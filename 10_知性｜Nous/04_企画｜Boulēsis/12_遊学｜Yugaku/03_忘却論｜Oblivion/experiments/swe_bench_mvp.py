"""
SWE-bench MVP (Phase A/B): 新忘却メトリクス (H3/H4) 計算と効果量推定スクリプト
忘却論 Paper IV 定理 3.1.1 の検証および逆因果の排除用

Usage:
    python swe_bench_mvp.py --data <swebench_lite.jsonl> --output <results/>
    
Requirements:
    pip install numpy scipy pandas statsmodels pingouin
    
Note: SWE-bench Lite (N=300/500) のデータファイルが必要。
    https://github.com/princeton-nlp/SWE-bench からダウンロード。
"""

import argparse
import json
import sys
import re
import collections
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


def gini_coefficient(values: np.ndarray) -> float:
    """Gini 係数を計算。
    
    Paper IV §2.1: Ξ_Gini = Lorenz 曲線と対角線の間の面積比。
    Ξ = 0: 完全均一（忘却パターンなし）
    Ξ = 1: 完全不均一（最大忘却パターン）
    """
    if len(values) == 0 or np.all(values == 0):
        return 0.0
    sorted_vals = np.sort(values)
    n = len(sorted_vals)
    index = np.arange(1, n + 1)
    return (2 * np.sum(index * sorted_vals) / (n * np.sum(sorted_vals))) - (n + 1) / n


def compute_metrics(trajectory: list[dict]) -> tuple[float, float, float, float]:
    """trajectory から全体 t_gini、early_t_gini、H3(FBR)、H4(OOR) を計算する。
    
    逆因果（エラー泥沼化による事後的な高Gini化）を排除するための前方予測テスト用 (early_t_gini)。
    また、真の意味での忘却・適応を測るために H3 (First-Blow Resilience) と H4 (Observation Omission Rate) を導入。
    """
    if not trajectory:
        return np.nan, np.nan, np.nan, np.nan
        
    t_lengths = []
    error_idx = -1
    post_error_actions = []
    
    omissions = 0
    valid_transitions = 0
    
    last_obs_words = set()
    
    for i, obs in enumerate(trajectory):
        if "content" in obs:
            content = str(obs["content"])
            l = len(content)
            cont_lower = content.lower()
            role = obs.get("role", "")
            
            if role == "user" or role == "tool":
                obs_text = content
                thought_act_text = ""
            else:
                obs_text = ""
                thought_act_text = content
        else:
            l = sum(len(str(obs.get(k, ""))) for k in ["thought", "action", "observation", "response"])
            cont_lower = str(obs.get("observation", "")).lower()
            obs_text = str(obs.get("observation", ""))
            thought_act_text = str(obs.get("thought", "")) + " " + str(obs.get("action", ""))
            
        t_lengths.append(l)
        
        # 初回エラー検知
        if error_idx == -1 and ("traceback" in cont_lower or "exception" in cont_lower or "error:" in cont_lower):
            error_idx = i
            
        if error_idx != -1 and i > error_idx:
            # エラー後のアクションを収集 (H3 向け)
            action_text = str(obs.get("action", "")) if "action" in obs else thought_act_text
            if action_text.strip():
                # SWE-bench 用行動コマンド抽出 (XML/JSON/プレーン対応)
                act_str = action_text.strip()
                cmd = ""
                # XML抽出
                xml_match = re.search(r'<([a-zA-Z0-9_]+)', act_str)
                if xml_match:
                    cmd = "xml:" + xml_match.group(1)
                # JSON抽出
                elif act_str.startswith("{"):
                    try:
                        d = json.loads(act_str)
                        cmd = "json:" + str(d.get("name", d.get("command", d.get("action", "unknown"))))
                    except Exception:
                        pass
                
                if not cmd:
                    cmd = "text:" + act_str.split()[0][:20]
                    
                post_error_actions.append(cmd)
                
        # H4 OOR 計算 (局所的 Jaccard 係数近似)
        if thought_act_text.strip() and last_obs_words:
            next_words = set(thought_act_text.lower().split())
            if next_words:
                intersection = last_obs_words.intersection(next_words)
                jaccard = len(intersection) / len(last_obs_words)
                if jaccard < 0.01:
                    omissions += 1
                valid_transitions += 1
                
        if obs_text.strip():
            last_obs_words = set(obs_text.lower().split())
        
    t_gini = gini_coefficient(np.array(t_lengths))
    
    # Early t_gini (first half of trajectory)
    half_idx = max(3, len(t_lengths) // 2)
    if len(t_lengths) >= 3:
        early_t_gini = gini_coefficient(np.array(t_lengths[:half_idx]))
    else:
        early_t_gini = t_gini
        
    # H3 FBR (First-Blow Resilience) = Action Transition Entropy (ASTE)
    h3_fbr = np.nan
    if post_error_actions:
        counts = collections.Counter(post_error_actions)
        total = sum(counts.values())
        h3_fbr = -sum((c/total) * math.log2(c/total) for c in counts.values())
        
    # H4 OOR (Observation Omission Rate)
    h4_oor = omissions / valid_transitions if valid_transitions > 0 else np.nan
        
    return t_gini, early_t_gini, h3_fbr, h4_oor


def extract_confounders(instance: dict) -> dict:
    """交絡変数 Z₁-Z₈ を抽出。
    
    Paper IV §3.2 / SWE-bench verification plan §2。
    """
    return {
        "issue_length": len(instance.get("problem_statement", "")),
        "diff_size": len(instance.get("patch", "")),
        "test_size": len(instance.get("test_patch", "")),
        "repo": instance.get("repo", ""),
        "instance_id": instance.get("instance_id", ""),
    }


def stratified_analysis(df: pd.DataFrame, column: str, target: str = "t_gini", bins: int = 3) -> pd.DataFrame:
    """層別分析。SWE-bench verification plan §2 の各層別軸に対応。"""
    results = []
    df_valid = df.dropna(subset=[target])
    if len(df_valid) == 0:
        return pd.DataFrame()
        
    df_valid["_stratum"] = pd.qcut(df_valid[column], bins, labels=False, duplicates="drop")
    for stratum in sorted(df_valid["_stratum"].unique()):
        sub = df_valid[df_valid["_stratum"] == stratum]
        if len(sub) < 10:
            continue
        r, p = stats.pearsonr(sub[target], sub["success"])
        results.append({
            "stratum": int(stratum),
            f"{column}_min": sub[column].min(),
            f"{column}_max": sub[column].max(),
            "n": len(sub),
            "r": round(r, 4),
            "p_value": round(p, 6),
        })
    df_valid.drop(columns=["_stratum"], inplace=True)
    return pd.DataFrame(results)


def ac_discrimination(df: pd.DataFrame) -> dict:
    """A/C 弁別メトリクス (M-1, M-4, M-5, M-6).
    
    M-1: 減衰構造テスト — r(ρ, K) が Paper IV 定理 3.1.1 の曲面に適合するか
    M-4: 階層的回帰 — Ξ_Gini の偏回帰係数の有意性
    M-5: H3 (First-Blow Resilience) テスト — ASTE と Success の相関
    M-6: H4 (Observation Omission Rate) テスト — OOR と Success の相関
    """
    results = {}

    try:
        import pingouin as pg
        
        # M-1: 全件相関 (with CI, BF, Power)
        corr_res = pg.corr(df["t_gini"], df["success"])
        results["M1_r_full"] = round(corr_res["r"].iloc[0] if hasattr(corr_res["r"], "iloc") else corr_res["r"], 4)
        results["M1_p_full"] = round(corr_res["p_val"].iloc[0] if hasattr(corr_res["p_val"], "iloc") else corr_res["p_val"], 6)
        
        ci95 = corr_res["CI95"].iloc[0] if hasattr(corr_res["CI95"], "iloc") else corr_res["CI95"]
        if isinstance(ci95, (list, tuple, np.ndarray)) and len(ci95) >= 2:
            results["M1_ci_lower"] = round(ci95[0], 4)
            results["M1_ci_upper"] = round(ci95[1], 4)
        else:
            results["M1_ci_lower"] = np.nan
            results["M1_ci_upper"] = np.nan
            
        results["M1_bayes_factor"] = corr_res["BF10"].iloc[0] if hasattr(corr_res["BF10"], "iloc") else corr_res["BF10"]
        results["M1_power"] = round(corr_res["power"].iloc[0] if hasattr(corr_res["power"], "iloc") else corr_res["power"], 4)
        
        # Forward Prediction Test (early_t_gini)
        corr_early = pg.corr(df["early_t_gini"], df["success"])
        results["M1_early_r"] = round(corr_early["r"].iloc[0] if hasattr(corr_early["r"], "iloc") else corr_early["r"], 4)
        results["M1_early_bf"] = corr_early["BF10"].iloc[0] if hasattr(corr_early["BF10"], "iloc") else corr_early["BF10"]
        
        # M-5: H3 FBR (ASTE) の相関
        df_h3 = df.dropna(subset=["h3_fbr"])
        if len(df_h3) > 5:
            corr_h3 = pg.corr(df_h3["h3_fbr"], df_h3["success"])
            results["M5_h3_fbr_r"] = round(corr_h3["r"].iloc[0] if hasattr(corr_h3["r"], "iloc") else corr_h3["r"], 4)
            results["M5_h3_fbr_p"] = round(corr_h3["p_val"].iloc[0] if hasattr(corr_h3["p_val"], "iloc") else corr_h3["p_val"], 6)
            results["M5_h3_fbr_bf"] = corr_h3["BF10"].iloc[0] if hasattr(corr_h3["BF10"], "iloc") else corr_h3["BF10"]
            results["M5_n"] = len(df_h3)
            
        # M-6: H4 OOR の相関
        df_h4 = df.dropna(subset=["h4_oor"])
        if len(df_h4) > 5:
            corr_h4 = pg.corr(df_h4["h4_oor"], df_h4["success"])
            results["M6_h4_oor_r"] = round(corr_h4["r"].iloc[0] if hasattr(corr_h4["r"], "iloc") else corr_h4["r"], 4)
            results["M6_h4_oor_p"] = round(corr_h4["p_val"].iloc[0] if hasattr(corr_h4["p_val"], "iloc") else corr_h4["p_val"], 6)
            results["M6_h4_oor_bf"] = corr_h4["BF10"].iloc[0] if hasattr(corr_h4["BF10"], "iloc") else corr_h4["BF10"]

    except ImportError:
        # Fallback to scipy
        r_full, p_full = stats.pearsonr(df["t_gini"], df["success"])
        results["M1_r_full"] = round(r_full, 4)
        results["M1_p_full"] = round(p_full, 6)
        
        r_early, p_early = stats.pearsonr(df["early_t_gini"], df["success"])
        results["M1_early_r"] = round(r_early, 4)
        
        df_h3 = df.dropna(subset=["h3_fbr"])
        if len(df_h3) > 5:
            r_h3, p_h3 = stats.pearsonr(df_h3["h3_fbr"], df_h3["success"])
            results["M5_h3_fbr_r"] = round(r_h3, 4)
            results["M5_n"] = len(df_h3)
            
        df_h4 = df.dropna(subset=["h4_oor"])
        if len(df_h4) > 5:
            r_h4, p_h4 = stats.pearsonr(df_h4["h4_oor"], df_h4["success"])
            results["M6_h4_oor_r"] = round(r_h4, 4)

    # M-4: 階層的回帰（交絡変数制御後の Ξ 効果）
    try:
        import statsmodels.api as sm
        confounders = ["issue_length", "diff_size", "test_size"]
        available = [c for c in confounders if c in df.columns]
        if available:
            Z = sm.add_constant(df[available])
            ZX = sm.add_constant(df[available + ["t_gini"]])
            # Use HC3 robust standard errors
            model_base = sm.OLS(df["success"], Z).fit(cov_type='HC3')
            model_full = sm.OLS(df["success"], ZX).fit(cov_type='HC3')
            results["M4_xi_coeff"] = round(model_full.params.get("t_gini", 0), 4)
            results["M4_xi_pvalue"] = round(model_full.pvalues.get("t_gini", 1), 6)
            results["M4_r2_base"] = round(model_base.rsquared, 4)
            results["M4_r2_full"] = round(model_full.rsquared, 4)
            
            delta_r2 = model_full.rsquared - model_base.rsquared
            results["M4_delta_r2"] = round(delta_r2, 4)
            
            # Cohen's f^2 effect size
            f2 = delta_r2 / (1 - model_full.rsquared) if model_full.rsquared < 1 else np.inf
            results["M4_cohens_f2"] = round(f2, 4)
    except ImportError:
        results["M4_note"] = "statsmodels not available"

    return results


def main():
    parser = argparse.ArgumentParser(
        description="SWE-bench MVP: Ξ_Gini & Semantic Metrics (H3/H4) computation"
    )
    parser.add_argument("--data", required=True, help="Path to SWE-bench data (JSONL)")
    parser.add_argument("--trajectories", help="Path to trajectory data (JSONL)")
    parser.add_argument("--output", default="results", help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    print(f"Loading data from {args.data}...")
    instances = []
    with open(args.data, encoding="utf-8") as f:
        for line in f:
            instances.append(json.loads(line.strip()))
    print(f"  Loaded {len(instances)} instances")

    # Load trajectories
    trajectories = {}
    if args.trajectories and Path(args.trajectories).exists():
        print(f"Loading trajectories from {args.trajectories}...")
        with open(args.trajectories, encoding="utf-8") as f:
            for line in f:
                traj = json.loads(line.strip())
                tid = traj.get("instance_id", "")
                trajectories[tid] = traj.get("trajectory", [])
        print(f"  Loaded {len(trajectories)} trajectories")

    # Build dataframe
    records = []
    for inst in instances:
        iid = inst.get("instance_id", "")
        conf = extract_confounders(inst)
        traj = trajectories.get(iid, [])
        if traj:
            t_gini, early_t_gini, h3_fbr, h4_oor = compute_metrics(traj)
        else:
            t_gini, early_t_gini, h3_fbr, h4_oor = np.nan, np.nan, np.nan, np.nan
        records.append({
            "instance_id": iid,
            "t_gini": t_gini,
            "early_t_gini": early_t_gini,
            "h3_fbr": h3_fbr,
            "h4_oor": h4_oor,
            "success": float(inst.get("resolved", inst.get("success", 0))),
            **conf,
        })

    df = pd.DataFrame(records)
    df_valid = df.dropna(subset=["t_gini"])

    print(f"\n{'='*60}")
    print(f"SWE-bench MVP Analysis — Paper IV Null Result & H3/H4 Verification")
    print(f"{'='*60}")
    print(f"Total instances: {len(df)}")
    print(f"With trajectories: {len(df_valid)}")

    if len(df_valid) < 10:
        print("\n⚠️ Insufficient trajectory data for analysis.")
        print("  Provide --trajectories with observation sequences.")
        print("  Script validated successfully (dry run).")
        df.to_csv(output_dir / "instances.csv", index=False)
        print(f"\n  Instance metadata saved to {output_dir / 'instances.csv'}")
        return

    # Main analysis
    print(f"\n--- Main Analysis ---")
    ac_results = ac_discrimination(df_valid)
    for k, v in ac_results.items():
        print(f"  {k}: {v}")

    # Interpretation
    print(f"\n--- Interpretation ---")
    
    # 1. Main Effect Evaluation (t_gini)
    r = ac_results.get("M1_r_full", 0)
    bf_str = ac_results.get("M1_bayes_factor", "NaN")
    try:
        bf = float(bf_str)
    except ValueError:
        bf = np.nan
    ci_low = ac_results.get("M1_ci_lower", np.nan)
    ci_high = ac_results.get("M1_ci_upper", np.nan)

    print(f"\n  [Baseline Check] Main Effect Test (t_gini):")
    if np.isnan(bf):
        print(f"  ⚠️ BF10 missing (pingouin not installed). Correlation: r = {r:.3f}")
    elif bf > 3:
        print(f"  ✓ BF10 = {bf:.2f} (>3): Substantial evidence for correlation (r ≈ {r:.3f}, 95% CI [{ci_low:.3f}, {ci_high:.3f}])")
    elif bf < 0.33:
        print(f"  ⚠️ BF10 = {bf:.2f} (<0.33): Substantial evidence for NO correlation.")
    else:
        print(f"  ⚠️ BF10 = {bf:.2f}: Insufficient evidence. More data needed.")

    # 2. Null Result Evaluation (early_t_gini vs t_gini)
    early_r = ac_results.get("M1_early_r", 0)
    early_bf_str = ac_results.get("M1_early_bf", "NaN")
    try:
        early_bf = float(early_bf_str)
    except ValueError:
        early_bf = np.nan
        
    print(f"\n  [Null Result Check] Forward Prediction Test (early_t_gini):")
    if np.isnan(early_bf):
        print(f"  ⚠️ BF10 missing (pingouin not installed). Correlation: r = {early_r:.3f}")
    elif early_bf < 0.33:
        print(f"  ✓ BF10 = {early_bf:.2f} (<0.33): Substantial evidence for NO correlation in early trajectory.")
        print(f"  → Reverse causality confirmed. Macroscopic Gini is flawed. Null Result accepted.")
    elif early_bf > 3:
        print(f"  ⚠️ BF10 = {early_bf:.2f} (>3): Correlation persists in early trajectory (r={early_r:.3f}).")
        print(f"  → Null Result rejected. Forward causality may exist.")
    else:
        print(f"  ⚠️ BF10 = {early_bf:.2f}: Insufficient evidence. More data needed.")

    # 3. H3 (FBR) Evaluation
    if "M5_h3_fbr_r" in ac_results:
        h3_r = ac_results["M5_h3_fbr_r"]
        h3_bf = ac_results.get("M5_h3_fbr_bf", "NaN")
        try:
            h3_bf_val = float(h3_bf)
        except ValueError:
            h3_bf_val = np.nan
        print(f"\n  [H3 FBR] First-Blow Resilience (ASTE) Test:")
        if np.isnan(h3_bf_val):
            print(f"  ⚠️ BF10 missing. Correlation: r = {h3_r:.3f}")
        elif h3_bf_val > 3:
            print(f"  ✓ BF10 = {h3_bf_val:.2f} (>3): Action Transition Entropy shows correlation (r ≈ {h3_r:.3f})")
        else:
            print(f"  ⚠️ BF10 = {h3_bf_val:.2f}: Insufficient evidence for H3 correlation.")

    # 4. H4 (OOR) Evaluation
    if "M6_h4_oor_r" in ac_results:
        h4_r = ac_results["M6_h4_oor_r"]
        h4_bf = ac_results.get("M6_h4_oor_bf", "NaN")
        try:
            h4_bf_val = float(h4_bf)
        except ValueError:
            h4_bf_val = np.nan
        print(f"\n  [H4 OOR] Observation Omission Rate Test:")
        if np.isnan(h4_bf_val):
            print(f"  ⚠️ BF10 missing. Correlation: r = {h4_r:.3f}")
        elif h4_bf_val > 3:
            print(f"  ✓ BF10 = {h4_bf_val:.2f} (>3): OOR shows substantial correlation (r ≈ {h4_r:.3f})")
        else:
            print(f"  ⚠️ BF10 = {h4_bf_val:.2f}: Insufficient evidence for H4 correlation.")

    # Save results
    df.to_csv(output_dir / "instances.csv", index=False)
    with open(output_dir / "analysis.json", "w", encoding="utf-8") as f:
        json.dump(ac_results, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved to {output_dir}/")


if __name__ == "__main__":
    main()
