"""
SWE-bench Phase C: H3 (FBR) と H4 (OOR) の実装と弁別力テスト
忘却論 Paper V への布石 / Phase B の Null Result を受けたパラダイムシフト

Usage:
    python swe_bench_phase_c.py --data swebench_lite_with_results.jsonl --trajectories swebench_lite_real_traj.jsonl --output results_phase_c
"""

import argparse
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

def extract_action_state(step: dict) -> str:
    """actionフィールドからコマンドの動詞部分と対象を抽出する。"""
    action = step.get("action", "")
    if not action:
        return "none"
    
    parts = action.strip().split()
    if not parts:
        return "none"
        
    verb = parts[0].lower()
    
    # 引数があれば状態空間に含める（ただし長すぎる場合は切り詰める）
    target = ""
    if len(parts) > 1:
        target = parts[1].split('/')[-1] # パスの場合はファイル名のみ
        target = target[:20] # 状態空間の爆発を防ぐため20文字制限
        
    return f"{verb}_{target}" if target else verb

def compute_aste(trajectory: list[dict]) -> float:
    """H3: Action-Space Transition Entropy (ASTE) / 初回被弾復元力 FBR
    初回エラー以降の行動遷移（動詞+対象のバイグラム）のエントロピーを計算。
    """
    error_idx = -1
    for i, obs in enumerate(trajectory):
        cont_lower = str(obs.get("observation", obs.get("content", ""))).lower()
        # 単純な 'traceback' 部分一致による誤爆を防ぐため、Pythonのエラー出力に特有のフレーズで判定
        if "traceback (most recent call last)" in cont_lower or "syntaxerror:" in cont_lower or "nameerror:" in cont_lower or "typeerror:" in cont_lower or "attributeerror:" in cont_lower or "assertionerror:" in cont_lower:
            error_idx = i
            break
            
    if error_idx == -1 or len(trajectory) - error_idx < 3:
        return np.nan
        
    post_error_steps = trajectory[error_idx:]
    states = [extract_action_state(step) for step in post_error_steps]
    
    # 遷移バイグラムの生成
    transitions = [f"{states[i]}->{states[i+1]}" for i in range(len(states)-1)]
    if not transitions:
        return 0.0
        
    # 遷移確率分布
    unique_trans, counts = np.unique(transitions, return_counts=True)
    probs = counts / len(transitions)
    
    # Shannon Entropy
    entropy = -np.sum(probs * np.log2(probs))
    return entropy

def compute_oor(trajectory: list[dict], min_obs_len: int = 200) -> float:
    """H4: Observation Omission Rate (OOR) / 観測無視率
    観測が一定長以上の場合、次のthoughtにおける観測語彙の非対称引用率の反転を計算。
    """
    omission_rates = []
    
    # word tokenizer (英字4文字以上の単語を抽出)
    word_pattern = re.compile(r'\b[a-zA-Z]{4,}\b')
    
    for i in range(len(trajectory) - 1):
        obs_text = str(trajectory[i].get("observation", trajectory[i].get("content", "")))
        if len(obs_text) < min_obs_len:
            continue
            
        next_thought = str(trajectory[i+1].get("thought", trajectory[i+1].get("content", "")))
        
        obs_words = set(word_pattern.findall(obs_text.lower()))
        thought_words = set(word_pattern.findall(next_thought.lower()))
        
        if len(thought_words) == 0:
            continue
            
        # 思考に含まれる単語のうち、観測にも含まれていた単語の割合（非対称な引用率）
        intersection = len(obs_words & thought_words)
        citation_rate = intersection / len(thought_words)
        
        # 観測無視率 = 1 - 引用率
        omission_rates.append(1.0 - citation_rate)
        
    if not omission_rates:
        return np.nan
        
    return float(np.mean(omission_rates))

def analyze_metrics(df: pd.DataFrame) -> dict:
    """M-1, M-4, M-5 相当の弁別力テスト"""
    results = {}
    try:
        import pingouin as pg
        
        # H3: ASTE と Success の相関
        df_aste = df.dropna(subset=["aste"])
        if len(df_aste) > 5:
            corr_aste = pg.corr(df_aste["aste"], df_aste["success"])
            results["H3_r"] = round(corr_aste["r"].iloc[0] if hasattr(corr_aste["r"], "iloc") else corr_aste["r"], 4)
            results["H3_p"] = round(corr_aste["p_val"].iloc[0] if hasattr(corr_aste["p_val"], "iloc") else corr_aste["p_val"], 6)
            results["H3_bf10"] = corr_aste["BF10"].iloc[0] if hasattr(corr_aste["BF10"], "iloc") else corr_aste["BF10"]
            results["H3_n"] = len(df_aste)
            
        # H4: OOR と Success の相関
        df_oor = df.dropna(subset=["oor"])
        if len(df_oor) > 5:
            corr_oor = pg.corr(df_oor["oor"], df_oor["success"])
            results["H4_r"] = round(corr_oor["r"].iloc[0] if hasattr(corr_oor["r"], "iloc") else corr_oor["r"], 4)
            results["H4_p"] = round(corr_oor["p_val"].iloc[0] if hasattr(corr_oor["p_val"], "iloc") else corr_oor["p_val"], 6)
            results["H4_bf10"] = corr_oor["BF10"].iloc[0] if hasattr(corr_oor["BF10"], "iloc") else corr_oor["BF10"]
            results["H4_n"] = len(df_oor)
            
    except ImportError:
        results["error"] = "pingouin not found"

    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--trajectories", required=True)
    parser.add_argument("--output", default="results_phase_c")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading data from {args.data}...")
    instances = []
    with open(args.data, encoding="utf-8") as f:
        for line in f:
            instances.append(json.loads(line.strip()))
            
    print(f"Loading trajectories from {args.trajectories}...")
    trajectories = {}
    with open(args.trajectories, encoding="utf-8") as f:
        for line in f:
            traj = json.loads(line.strip())
            tid = traj.get("instance_id", "")
            trajectories[tid] = traj.get("trajectory", [])

    records = []
    for inst in instances:
        iid = inst.get("instance_id", "")
        traj = trajectories.get(iid, [])
        
        aste = compute_aste(traj)
        oor = compute_oor(traj)
        
        success = float(inst.get("resolved", inst.get("success", 0)))
        
        records.append({
            "instance_id": iid,
            "success": success,
            "aste": aste,
            "oor": oor
        })

    df = pd.DataFrame(records)
    
    print(f"\n{'='*60}")
    print(f"SWE-bench Phase C: H3(ASTE/FBR) & H4(OOR) Verification")
    print(f"{'='*60}")
    print(f"Total instances: {len(df)}")
    print(f"Valid ASTE (H3): {df['aste'].notna().sum()}")
    print(f"Valid OOR  (H4): {df['oor'].notna().sum()}")
    
    results = analyze_metrics(df)
    
    print("\n--- H3: Action-Space Transition Entropy (First Blow Resilience) ---")
    print(f"  r      : {results.get('H3_r', 'N/A')}")
    print(f"  p-value: {results.get('H3_p', 'N/A')}")
    print(f"  BF10   : {results.get('H3_bf10', 'N/A')} (N={results.get('H3_n', 'N/A')})")
    try:
        if float(results.get("H3_bf10", 0)) > 3:
            print("  ✓ BF10 > 3: Substantial evidence that ASTE correlates with success.")
        elif float(results.get("H3_bf10", 0)) < 0.33:
            print("  ⚠️ BF10 < 0.33: Substantial evidence for NO correlation.")
        else:
            print("  ⚠️ Anecdotal evidence.")
    except Exception:
        pass

    print("\n--- H4: Observation Omission Rate (OOR) ---")
    print(f"  r      : {results.get('H4_r', 'N/A')}")
    print(f"  p-value: {results.get('H4_p', 'N/A')}")
    print(f"  BF10   : {results.get('H4_bf10', 'N/A')} (N={results.get('H4_n', 'N/A')})")
    try:
        if float(results.get("H4_bf10", 0)) > 3:
            print("  ✓ BF10 > 3: Substantial evidence that OOR correlates with success.")
        elif float(results.get("H4_bf10", 0)) < 0.33:
            print("  ⚠️ BF10 < 0.33: Substantial evidence for NO correlation.")
        else:
            print("  ⚠️ Anecdotal evidence.")
    except Exception:
        pass
        
    df.to_csv(output_dir / "phase_c_metrics.csv", index=False)
    with open(output_dir / "phase_c_analysis.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved to {output_dir}/")

if __name__ == "__main__":
    main()
