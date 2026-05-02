"""
SWE-bench 追実験: nebius/SWE-agent-trajectories から Ξ を計算し P との相関を検証

データソース: https://huggingface.co/datasets/nebius/SWE-agent-trajectories
  - 80,036 trajectories (SWE-agent による GitHub issue 解決試行)
  - columns: instance_id, model_name, target (bool), trajectory (JSON list), patch, ...

理論的対応:
  - Ξ = Var(λ_1, ..., λ_T) where λ_t = observation t の相対情報量
  - P = target (bool: 1=成功, 0=失敗)
  - 選択的忘却定理: Corr(Ξ, P) > 0

使い方:
  pip install datasets
  python swe_bench_xi_experiment.py --n_samples 500 --output results.json
"""
import json
import numpy as np
from scipy import stats
import argparse
from pathlib import Path
import sys


def compute_xi_from_trajectory(trajectory: list) -> dict:
    """
    Trajectory から Ξ (忘却の不均一度) を計算する。
    
    trajectory: [{role: str, content: str}, ...]
      - role="user"/"tool" → observation (環境からの入力)
      - role="ai"/"assistant" → action (エージェントの出力)
      - role="system" → システムプロンプト (除外)
    
    Ξ の操作化 (v2 — CV ベース):
      各 observation turn の文字数 L_t (= 情報量の proxy) から:
      - Ξ_CV  = std(L) / mean(L)  — 変動係数 (スケール不変な不均一度)
      - Ξ_Gini = Gini(L)          — 文字数分布の不均一度
      
      直感: observation の情報量が均一 → Ξ ≈ 0 (等方的)
            一部の observation が支配的 → Ξ > 0 (異方的)
    
    v1 (relative_info の Var) は T が大きいと 1/T² に縮退するため廃止。
    """
    obs_lengths = []
    action_lengths = []
    
    for entry in trajectory:
        if not isinstance(entry, dict):
            continue
        
        role = entry.get("role", "")
        # nebius/SWE-agent-trajectories はテキストを "text" フィールドに格納
        # (汎用の "content" ではない)
        content = entry.get("text", "") or entry.get("content", "") or ""
        
        # content がリスト形式の場合の処理
        if isinstance(content, list):
            content = " ".join(
                item.get("text", str(item)) if isinstance(item, dict) else str(item)
                for item in content
            )
        
        if not isinstance(content, str):
            content = str(content) if content else ""
        
        if role in ("user", "tool"):
            obs_lengths.append(len(content))
        elif role in ("ai", "assistant"):
            action_lengths.append(len(content))
        # role="system" は除外
    
    T = len(obs_lengths)
    if T == 0:
        return {"xi_cv": 0.0, "xi_gini": 0.0, "n_obs_turns": 0, "n_action_turns": 0, "total_turns": 0}
    
    a = np.array(obs_lengths, dtype=float)
    mean_len = np.mean(a)
    total_obs_chars = int(np.sum(a))
    total_action_chars = sum(action_lengths)
    
    if mean_len < 1e-10:
        return {"xi_cv": 0.0, "xi_gini": 0.0, "n_obs_turns": T, "n_action_turns": len(action_lengths), "total_turns": T + len(action_lengths)}
    
    # Ξ_CV: 変動係数 (std / mean) — スケール不変な不均一度
    xi_cv = float(np.std(a) / mean_len)
    
    # Ξ_Gini: Gini 係数 (文字数分布の不均一度)
    sorted_a = np.sort(a)
    n = len(sorted_a)
    index = np.arange(1, n + 1)
    xi_gini = float((2 * np.sum(index * sorted_a) - (n + 1) * np.sum(sorted_a)) / (n * np.sum(sorted_a) + 1e-10))
    
    # エントロピー比 (1.0 = 完全均一、0 に近いほど不均一)
    relative_info = a / np.sum(a)
    info_entropy = float(-np.sum(relative_info * np.log(relative_info + 1e-10)))
    max_entropy = float(np.log(T)) if T > 1 else 0.0
    
    # 行動比率
    action_ratio = total_action_chars / (total_obs_chars + total_action_chars + 1e-10)
    
    return {
        "xi_cv": xi_cv,
        "xi_gini": xi_gini,
        "n_obs_turns": T,
        "n_action_turns": len(action_lengths),
        "total_turns": T + len(action_lengths),
        "total_obs_chars": total_obs_chars,
        "total_action_chars": total_action_chars,
        "action_ratio": action_ratio,
        "info_entropy": info_entropy,
        "max_entropy": max_entropy,
        "entropy_ratio": info_entropy / max_entropy if max_entropy > 0 else 0.0,
        "mean_obs_len": float(mean_len),
        "max_obs_len": int(np.max(a)),
        "min_obs_len": int(np.min(a)),
    }


def run_experiment(n_samples: int = 500, output_path: str = None, seed: int = 42):
    """
    nebius/SWE-agent-trajectories から n_samples 件をサンプリングし、
    Ξ-P 相関を検証する。
    """
    try:
        from datasets import load_dataset
    except ImportError:
        print("❌ datasets ライブラリが未インストール:")
        print("   pip install datasets")
        sys.exit(1)
    
    print(f"📥 nebius/SWE-agent-trajectories をロード中...")
    ds = load_dataset("nebius/SWE-agent-trajectories", split="train", streaming=True)
    
    print(f"🧪 {n_samples} 件をサンプリングして Ξ を計算中...")
    np.random.seed(seed)
    
    results = []
    errors = 0
    
    for i, example in enumerate(ds):
        if len(results) >= n_samples:
            break
        
        try:
            # trajectory を取得
            trajectory = example.get("trajectory", [])
            if isinstance(trajectory, str):
                trajectory = json.loads(trajectory)
            
            if not trajectory or len(trajectory) < 3:
                # 短すぎる trajectory はスキップ
                continue
            
            # Ξ を計算
            xi_result = compute_xi_from_trajectory(trajectory)
            
            # メタデータを追加
            xi_result["instance_id"] = example.get("instance_id", "")
            xi_result["model_name"] = example.get("model_name", "")
            xi_result["target"] = 1 if example.get("target", False) else 0  # P = 成功/失敗
            xi_result["completion_status"] = example.get("completion_status", "")
            
            results.append(xi_result)
            
            if len(results) % 100 == 0:
                print(f"  進捗: {len(results)}/{n_samples} (エラー: {errors})")
                
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  ⚠️ エラー: {e}")
    
    print(f"\n✅ {len(results)} 件の trajectory を処理 (エラー: {errors})")
    
    if len(results) < 10:
        print("❌ サンプル数が不十分")
        return
    
    # 統計分析
    xi_cv = np.array([r["xi_cv"] for r in results])
    xi_gini = np.array([r["xi_gini"] for r in results])
    P = np.array([r["target"] for r in results])
    n_turns = np.array([r["total_turns"] for r in results])
    entropy_ratio = np.array([r.get("entropy_ratio", 0) for r in results])
    
    print(f"\n{'='*60}")
    print(f"SWE-bench Ξ-P 相関分析 (N={len(results)})")
    print(f"{'='*60}")
    
    # 基本統計
    n_success = int(P.sum())
    n_fail = len(P) - n_success
    print(f"\n📊 基本統計:")
    print(f"  成功率: {n_success}/{len(P)} ({100*n_success/len(P):.1f}%)")
    print(f"  Ξ_CV   mean: {np.mean(xi_cv):.4f} (std: {np.std(xi_cv):.4f})")
    print(f"  Ξ_Gini mean: {np.mean(xi_gini):.4f} (std: {np.std(xi_gini):.4f})")
    print(f"  Turns  mean: {np.mean(n_turns):.1f} (std: {np.std(n_turns):.1f})")
    
    # Ξ-P 相関 (Point-Biserial correlation: 二値 P に対する連続変数 Ξ の相関)
    print(f"\n🔬 Ξ-P 相関 (選択的忘却定理の検証):")
    
    # Point-biserial (= P が二値の場合の Pearson r)
    r_cv, p_cv = stats.pointbiserialr(P, xi_cv)
    r_gini, p_gini = stats.pointbiserialr(P, xi_gini)
    r_entropy, p_entropy = stats.pointbiserialr(P, entropy_ratio)
    r_turns, p_turns = stats.pointbiserialr(P, n_turns)
    
    print(f"  Corr(Ξ_CV,   P) = {r_cv:+.4f}  (p={p_cv:.2e})  {'✅' if r_cv > 0 and p_cv < 0.05 else '❌'}")
    print(f"  Corr(Ξ_Gini, P) = {r_gini:+.4f}  (p={p_gini:.2e})  {'✅' if r_gini > 0 and p_gini < 0.05 else '❌'}")
    print(f"  Corr(H_ratio, P) = {r_entropy:+.4f}  (p={p_entropy:.2e})")
    print(f"  Corr(N_turns, P) = {r_turns:+.4f}  (p={p_turns:.2e})")
    
    # 成功群 vs 失敗群の比較
    xi_success = xi_cv[P == 1]
    xi_fail = xi_cv[P == 0]
    
    if len(xi_success) > 1 and len(xi_fail) > 1:
        t_stat, t_p = stats.ttest_ind(xi_success, xi_fail)
        d = (np.mean(xi_success) - np.mean(xi_fail)) / np.sqrt(
            (np.var(xi_success) + np.var(xi_fail)) / 2 + 1e-10
        )
        print(f"\n📈 群間比較 (Ξ_CV):")
        print(f"  成功群: mean={np.mean(xi_success):.4f} (N={len(xi_success)})")
        print(f"  失敗群: mean={np.mean(xi_fail):.4f} (N={len(xi_fail)})")
        print(f"  t-test: t={t_stat:.3f}, p={t_p:.2e}")
        print(f"  Cohen's d: {d:.3f}")
    
    # Gini の群間比較
    gini_success = xi_gini[P == 1]
    gini_fail = xi_gini[P == 0]
    
    if len(gini_success) > 1 and len(gini_fail) > 1:
        t_stat_g, t_p_g = stats.ttest_ind(gini_success, gini_fail)
        d_g = (np.mean(gini_success) - np.mean(gini_fail)) / np.sqrt(
            (np.var(gini_success) + np.var(gini_fail)) / 2 + 1e-10
        )
        print(f"\n📈 群間比較 (Ξ_Gini):")
        print(f"  成功群: mean={np.mean(gini_success):.4f} (N={len(gini_success)})")
        print(f"  失敗群: mean={np.mean(gini_fail):.4f} (N={len(gini_fail)})")
        print(f"  t-test: t={t_stat_g:.3f}, p={t_p_g:.2e}")
        print(f"  Cohen's d: {d_g:.3f}")
    
    # ターン数の群間比較
    turns_success = n_turns[P == 1]
    turns_fail = n_turns[P == 0]
    
    if len(turns_success) > 1 and len(turns_fail) > 1:
        print(f"\n📈 群間比較 (N_turns):")
        print(f"  成功群: mean={np.mean(turns_success):.1f} (N={len(turns_success)})")
        print(f"  失敗群: mean={np.mean(turns_fail):.1f} (N={len(turns_fail)})")
    
    print(f"\n{'='*60}")
    
    # 理論的解釈
    print(f"\n📝 理論的解釈:")
    if r_cv > 0 and p_cv < 0.05:
        print(f"  ✅ Ξ_CV-P 正の相関 → 選択的忘却定理を支持")
        print(f"     異方的忘却 (Ξ > 0) を持つ trajectory はタスク成功率が高い")
    elif r_cv < 0 and p_cv < 0.05:
        print(f"  ⚠️ Ξ_CV-P 負の相関 → 統制実験の random_selective パターンと同型の可能性")
        print(f"     SWE-agent の忘却パターンが「方向なき不均一性」を示す可能性")
    else:
        print(f"  ❓ 有意な相関なし → 追加分析が必要 (交絡変数の候補: ターン数, タスク難易度)")
    
    if r_gini > 0 and p_gini < 0.05:
        print(f"  ✅ Ξ_Gini-P 正の相関 → 不均一性がタスク成功に寄与")
    elif r_gini < 0 and p_gini < 0.05:
        print(f"  ⚠️ Ξ_Gini-P 負の相関 → 統制実験結果 (r=-0.43) と整合")
        print(f"     「方向なき不均一性」仮説を支持")
    
    # 結果保存
    if output_path:
        output = {
            "experiment": "swe_bench_xi_p_correlation",
            "n_samples": len(results),
            "n_success": n_success,
            "n_fail": n_fail,
            "statistics": {
                "xi_cv_p_corr": {"r": float(r_cv), "p": float(p_cv)},
                "xi_gini_p_corr": {"r": float(r_gini), "p": float(p_gini)},
                "entropy_p_corr": {"r": float(r_entropy), "p": float(p_entropy)},
                "turns_p_corr": {"r": float(r_turns), "p": float(p_turns)},
            },
            "results": results[:100],  # 最初の 100 件のみ保存 (容量制限)
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\n💾 結果を {output_path} に保存")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SWE-bench trajectory から Ξ-P 相関を検証")
    parser.add_argument("--n_samples", type=int, default=500, help="分析する trajectory 数")
    parser.add_argument("--output", default=None, help="結果 JSON の出力先")
    parser.add_argument("--seed", type=int, default=42, help="乱数シード")
    
    args = parser.parse_args()
    run_experiment(args.n_samples, args.output, args.seed)
