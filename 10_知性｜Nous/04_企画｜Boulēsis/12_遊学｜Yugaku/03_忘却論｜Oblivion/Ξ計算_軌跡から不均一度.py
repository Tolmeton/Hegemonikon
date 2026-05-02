"""
Phase α: JetBrains Complexity Trap trajectory から Ξ (忘却の不均一度) を計算

原典との対応 (drafts/incubator/legacy/力とは忘却である_v2.md §4.6e — Ξ 定義 v2):
  
  原典の理論的定義:
    Ξ(U) = spec(G) = (λ₁, ..., λ_d)  ← 忘却関手 U のグラム行列の固有値スペクトラム (1-cell)
    Θ = decat(Ξ) = -tr(log G)/d       ← Ξ からの脱圏論化 (0-cell)
    Var(Ξ) = Var(λ₁, ..., λ_d)        ← 不均一度 (力の存在条件)
    P = P(Ξ) where ∂P/∂Var(Ξ) > 0     ← 選択的忘却定理
  
  本スクリプトの操作化:
    agent の trajectory において、各 turn t の observation の「保持率」λ_t を計算し、
    これを Ξ の離散近似として使用する。
    
    λ_t ∈ [0, 1]:
      masking 条件: λ_t = 1 (保持) or 0 (マスク) → binary → Var(Ξ) ≈ 0
      summary 条件: λ_t = len(summary_covering_t) / len(original_t) → continuous → Var(Ξ) > 0
      raw 条件: λ_t = 1 ∀t → Var(Ξ) = 0
    
    Var(Ξ) = Var(λ_1, ..., λ_T) — 原典の Var(Ξ) の trajectory レベルの操作化

SWE-agent の trajectory 形式:
  - 各 trajectory は JSON で、per-turn の {role, content} を含む
  - role=user の content は observation (tool output)
  - role=assistant の content は action (reasoning + tool call)

使い方:
  python xi_from_trajectory.py --trajectory_dir <dir> --strategy <masking|summary|raw>
"""
import json
import os
import glob
import numpy as np
from scipy import stats
import argparse
from pathlib import Path


def compute_xi_from_masking_trajectory(trajectory: list, window_m: int = 10) -> dict:
    """
    Masking 条件: 最新 M turn の observation を保持、残りを破棄
    
    retention_ratio[t] = 1 if t >= T-M else 0
    → ほぼ均一 (step function) → Ξ ≈ 0
    """
    # observation turn を抽出
    obs_lengths = []
    for entry in trajectory:
        content = None
        if "observation" in entry:
            content = entry.get("observation", "")
        elif entry.get("role") in ("user", "tool"):
            content = entry.get("content", "")
            if isinstance(content, list):
                content = content[0].get("text", "") if content else ""
        
        if content is not None:
            obs_lengths.append(len(content))
    
    T = len(obs_lengths)
    if T == 0:
        return {"xi": 0.0, "n_turns": 0, "mean_retention": 0.0}
    
    # masking: 最新 M turn は保持率 1.0、残りは保持率 0.0
    # (placeholder の長さ / 元の長さ ≈ 0)
    retention = np.zeros(T)
    retention[max(0, T - window_m):] = 1.0
    
    xi = float(np.var(retention))
    return {
        "xi": xi,
        "n_turns": T,
        "mean_retention": float(np.mean(retention)),
        "retention_pattern": "binary_step",
    }


def compute_xi_from_summary_trajectory(trajectory: list, summary_entries: list = None) -> dict:
    """
    Summary 条件: LLM が生成した要約が、元の turns の情報を不均一に保持

    retention_ratio[t] = len(summary_covering_t) / len(original_turns_t)
    → 不均一 → Ξ > 0
    """
    obs_lengths = []
    for entry in trajectory:
        content = None
        if "observation" in entry:
            content = entry.get("observation", "")
        elif entry.get("role") in ("user", "tool"):
            content = entry.get("content", "")
            if isinstance(content, list):
                content = content[0].get("text", "") if content else ""
        
        if content is not None:
            obs_lengths.append(len(content))
    
    T = len(obs_lengths)
    if T == 0:
        return {"xi": 0.0, "n_turns": 0, "mean_retention": 0.0}
    
    total_obs_chars = sum(obs_lengths)
    if total_obs_chars == 0:
        return {"xi": 0.0, "n_turns": T, "mean_retention": 0.0}
    
    # 各 turn の相対的な情報量 (文字数比)
    relative_info = np.array(obs_lengths) / total_obs_chars
    
    # 情報量の分散 = 不均一度
    # 均一なら全 turn 同じ比率 → Var ≈ 0
    # 不均一なら一部の turn が情報量に支配的 → Var > 0
    xi = float(np.var(relative_info))
    
    return {
        "xi": xi,
        "n_turns": T,
        "mean_retention": float(np.mean(relative_info)),
        "retention_pattern": "continuous",
        "info_entropy": float(-np.sum(relative_info * np.log(relative_info + 1e-10))),
        "max_entropy": float(np.log(T)),
        "kl_from_uniform": float(np.log(T) + np.sum(relative_info * np.log(relative_info + 1e-10))),
    }


def compute_xi_from_raw_trajectory(trajectory: list) -> dict:
    """
    Raw 条件: 全保持 → retention = 1.0 everywhere → Ξ = 0
    """
    obs_count = sum(1 for e in trajectory if "observation" in e or e.get("role") in ("user", "tool"))
    return {
        "xi": 0.0,
        "n_turns": obs_count,
        "mean_retention": 1.0,
        "retention_pattern": "all_retained",
    }


def load_trajectory(filepath: str) -> list:
    """trajectory ファイルを読み込み、メッセージリストを返す"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # SWE-agent の trajectory 形式:
    # {"history": [...], "info": {...}} or directly [...]
    if isinstance(data, dict):
        if "history" in data:
            return data["history"]
        if "messages" in data:
            return data["messages"]
        if "trajectory" in data:
            return data["trajectory"]
    if isinstance(data, list):
        return data
    
    raise ValueError(f"不明な trajectory 形式: {filepath}")


def analyze_directory(trajectory_dir: str, strategy: str, window_m: int = 10) -> list:
    """ディレクトリ内の全 trajectory ファイルを走査し、Ξ を計算する"""
    # JSON or TRAJ ファイルを探索
    target_files = glob.glob(os.path.join(trajectory_dir, "**", "*.json"), recursive=True)
    target_files.extend(glob.glob(os.path.join(trajectory_dir, "**", "*.traj"), recursive=True))
    
    if not target_files:
        print(f"⚠️ {trajectory_dir} に trajectory ファイルが見つかりません")
        return []
    
    results = []
    for fp in target_files:
        try:
            print(f"Processing {fp}... ", end="", flush=True)
            traj = load_trajectory(fp)
            
            if strategy == "masking":
                xi_result = compute_xi_from_masking_trajectory(traj, window_m)
            elif strategy == "summary":
                xi_result = compute_xi_from_summary_trajectory(traj)
            elif strategy == "raw":
                xi_result = compute_xi_from_raw_trajectory(traj)
            else:
                raise ValueError(f"不明な strategy: {strategy}")
            
            xi_result["file"] = os.path.basename(fp)
            results.append(xi_result)
            print("Done", flush=True)
        except Exception as e:
            print(f"⚠️ {fp}: {e}")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JetBrains trajectory から Ξ を計算")
    parser.add_argument("--trajectory_dir", required=True, help="trajectory JSON のディレクトリ")
    parser.add_argument("--strategy", choices=["masking", "summary", "raw"], required=True)
    parser.add_argument("--window_m", type=int, default=10, help="masking の window サイズ")
    parser.add_argument("--output", default=None, help="結果の出力ファイル")
    
    args = parser.parse_args()
    
    results = analyze_directory(args.trajectory_dir, args.strategy, args.window_m)
    
    if not results:
        print("結果なし")
        exit(1)
    
    xi_values = [r["xi"] for r in results]
    print(f"\n{'='*50}")
    print(f"Strategy: {args.strategy}")
    print(f"N trajectories: {len(results)}")
    print(f"Ξ mean: {np.mean(xi_values):.6f}")
    print(f"Ξ std: {np.std(xi_values):.6f}")
    print(f"Ξ median: {np.median(xi_values):.6f}")
    print(f"{'='*50}")
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump({"strategy": args.strategy, "results": results}, f, indent=2)
        print(f"結果を {args.output} に保存")
