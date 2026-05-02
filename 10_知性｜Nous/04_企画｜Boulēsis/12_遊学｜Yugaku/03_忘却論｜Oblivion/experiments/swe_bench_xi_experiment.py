#!/usr/bin/env python3
"""
SWE-bench Trajectory 分析 — 選択的忘却定理の検証
Paper II §5.3: Corr(Ξ, P) > 0

操作化:
  各 trajectory の observation ターン (role="user") の文字数列 {L₁, ..., L_T} を抽出し:
    Ξ_CV = σ(L) / μ(L)        # 変動係数 (不均一度)
    Ξ_Gini = Gini(L)           # Gini 係数 (不均一度)
  P = target (成功/失敗) との Point-Biserial 相関で検証。

データセット: nebius/SWE-agent-trajectories (80,036件)
"""

import json
import sys
import warnings
from collections import defaultdict

import numpy as np
from scipy import stats

warnings.filterwarnings("ignore")


def gini_coefficient(x: np.ndarray) -> float:
    """Gini 係数を計算。0=完全均一、1=完全不均一。"""
    if len(x) == 0 or np.sum(x) == 0:
        return 0.0
    x = np.sort(x)
    n = len(x)
    # 標準公式: G = (2 * Σ i*x_i) / (n * Σ x_i) - (n+1)/n
    index = np.arange(1, n + 1)
    return (2 * np.sum(index * x)) / (n * np.sum(x)) - (n + 1) / n


def extract_observation_lengths(trajectory: list | str) -> list[int]:
    """trajectory から observation ターンの文字数列を抽出。

    HF データセット形式: trajectory はパース済みリスト。
    各要素は {role, text, mask, cutoff_date, system_prompt}。
    SWE-agent では observation (環境出力) = role が "user" または
    assistant でないターン。text フィールドに内容がある。
    """
    # パース済みリストの場合はそのまま、文字列の場合は JSON パース
    if isinstance(trajectory, str):
        try:
            turns = json.loads(trajectory)
        except (json.JSONDecodeError, TypeError):
            return []
    elif isinstance(trajectory, list):
        turns = trajectory
    else:
        return []

    lengths = []
    for turn in turns:
        if not isinstance(turn, dict):
            continue
        role = turn.get("role", "")
        # observation = 環境からの応答 (assistant 以外, system 以外)
        # SWE-agent: role="user" が observation、role="assistant" が action
        if role not in ("assistant", "system"):
            text = turn.get("text", "") or turn.get("content", "")
            if isinstance(text, str) and len(text) > 0:
                lengths.append(len(text))
    return lengths


def compute_xi(lengths: list[int]) -> dict:
    """Ξ_CV と Ξ_Gini を計算。"""
    arr = np.array(lengths, dtype=float)
    mu = np.mean(arr)
    sigma = np.std(arr, ddof=1) if len(arr) > 1 else 0.0

    xi_cv = sigma / mu if mu > 0 else 0.0
    xi_gini = gini_coefficient(arr)

    return {
        "xi_cv": xi_cv,
        "xi_gini": xi_gini,
        "n_turns": len(arr),
        "mean_len": mu,
        "std_len": sigma,
    }


def main():
    N_SAMPLES = 500  # §5.3 で指定
    MIN_TURNS = 3    # observation が3ターン以上

    P = lambda *a, **k: print(*a, **k, flush=True)
    P("=" * 60)
    P("SWE-bench Trajectory 分析 — 選択的忘却定理の検証")
    P("Paper II §5.3: Corr(Ξ, P) > 0")
    P("=" * 60)

    # Phase 1: データ取得
    P("\n[Phase 1] データ取得 (streaming)...")
    try:
        from datasets import load_dataset
    except ImportError:
        P("ERROR: datasets ライブラリが必要。pip install datasets")
        sys.exit(1)

    P("  データセット接続中...")
    ds = load_dataset(
        "nebius/SWE-agent-trajectories",
        streaming=True,
        split="train",
    )
    P("  接続完了。サンプル収集開始...")

    # データ収集
    results = []
    n_processed = 0
    n_errors = 0
    n_filtered = 0  # T < MIN_TURNS でフィルタ

    for i, row in enumerate(ds):
        if len(results) >= N_SAMPLES:
            break

        n_processed += 1

        # trajectory パース
        lengths = extract_observation_lengths(row.get("trajectory", ""))
        if len(lengths) < MIN_TURNS:
            n_filtered += 1
            continue

        target = row.get("target", None)
        if target is None:
            n_errors += 1
            continue

        xi = compute_xi(lengths)
        xi["target"] = bool(target)
        xi["model"] = row.get("model_name", "unknown")
        xi["instance_id"] = row.get("instance_id", "")
        results.append(xi)

        if len(results) % 50 == 0:
            P(f"  ... {len(results)}/{N_SAMPLES} サンプル収集 (検索: {n_processed}件)")

    P(f"\n  完了: {len(results)} サンプル (処理: {n_processed}, フィルタ: {n_filtered}, エラー: {n_errors})")

    if len(results) < 30:
        P("ERROR: サンプル数が不足 (< 30)。中断。")
        sys.exit(1)

    # Phase 2: Ξ 計算結果の要約
    P("\n[Phase 2] Ξ 計算結果")
    xi_cv = np.array([r["xi_cv"] for r in results])
    xi_gini = np.array([r["xi_gini"] for r in results])
    targets = np.array([r["target"] for r in results], dtype=bool)

    success = targets
    failure = ~targets

    P(f"  成功群: n={success.sum()}, Ξ_CV={xi_cv[success].mean():.4f}±{xi_cv[success].std():.4f}")
    P(f"  失敗群: n={failure.sum()}, Ξ_CV={xi_cv[failure].mean():.4f}±{xi_cv[failure].std():.4f}")
    P(f"  成功群: Ξ_Gini={xi_gini[success].mean():.4f}±{xi_gini[success].std():.4f}")
    P(f"  失敗群: Ξ_Gini={xi_gini[failure].mean():.4f}±{xi_gini[failure].std():.4f}")

    # Phase 3: 統計検定
    P("\n[Phase 3] 統計検定")

    # Point-Biserial 相関
    r_cv, p_cv = stats.pointbiserialr(targets.astype(int), xi_cv)
    r_gini, p_gini = stats.pointbiserialr(targets.astype(int), xi_gini)

    P(f"  Point-Biserial (Ξ_CV, target):  r={r_cv:.4f}, p={p_cv:.4e}")
    P(f"  Point-Biserial (Ξ_Gini, target): r={r_gini:.4f}, p={p_gini:.4e}")

    # Mann-Whitney U (ノンパラメトリック)
    u_cv, p_mw_cv = stats.mannwhitneyu(xi_cv[success], xi_cv[failure], alternative="greater")
    u_gini, p_mw_gini = stats.mannwhitneyu(xi_gini[success], xi_gini[failure], alternative="greater")

    # 効果量 r = Z / √N
    n_total = len(results)
    z_cv = stats.norm.ppf(1 - p_mw_cv) if p_mw_cv < 1 else 0
    z_gini = stats.norm.ppf(1 - p_mw_gini) if p_mw_gini < 1 else 0
    effect_cv = z_cv / np.sqrt(n_total)
    effect_gini = z_gini / np.sqrt(n_total)

    P(f"  Mann-Whitney U (Ξ_CV, H1: success > failure):  U={u_cv:.0f}, p={p_mw_cv:.4e}, r={effect_cv:.4f}")
    P(f"  Mann-Whitney U (Ξ_Gini, H1: success > failure): U={u_gini:.0f}, p={p_mw_gini:.4e}, r={effect_gini:.4f}")

    # Phase 4: 判定
    P("\n[Phase 4] 選択的忘却定理の検証結果")
    P("=" * 60)

    verdict_cv = "支持" if r_cv > 0 and p_cv < 0.05 else "棄却" if r_cv <= 0 else "不確定 (p≥0.05)"
    verdict_gini = "支持" if r_gini > 0 and p_gini < 0.05 else "棄却" if r_gini <= 0 else "不確定 (p≥0.05)"

    P(f"  Ξ_CV:   Corr={r_cv:+.4f}, p={p_cv:.4e} → {verdict_cv}")
    P(f"  Ξ_Gini: Corr={r_gini:+.4f}, p={p_gini:.4e} → {verdict_gini}")

    # 結果テーブル出力 (Paper II 追記用)
    P("\n" + "=" * 60)
    P("Paper II §5.3 追記用テーブル:")
    P("=" * 60)
    P(f"| 指標 | r (Point-Biserial) | p 値 | Mann-Whitney p | 効果量 r | 判定 |")
    P(f"|:-----|:-------------------|:-----|:---------------|:---------|:-----|")
    P(f"| Ξ_CV | {r_cv:+.4f} | {p_cv:.2e} | {p_mw_cv:.2e} | {effect_cv:.4f} | {verdict_cv} |")
    P(f"| Ξ_Gini | {r_gini:+.4f} | {p_gini:.2e} | {p_mw_gini:.2e} | {effect_gini:.4f} | {verdict_gini} |")

    P(f"\nN={len(results)} (成功: {success.sum()}, 失敗: {failure.sum()})")
    P(f"フィルタ: T ≥ {MIN_TURNS} observation ターン")

    # モデル別の内訳
    P("\n--- モデル別内訳 ---")
    model_counts = defaultdict(lambda: {"success": 0, "failure": 0})
    for r in results:
        key = "success" if r["target"] else "failure"
        model_counts[r["model"]][key] += 1

    for model, counts in sorted(model_counts.items(), key=lambda x: sum(x[1].values()), reverse=True)[:10]:
        total = counts["success"] + counts["failure"]
        rate = counts["success"] / total if total > 0 else 0
        P(f"  {model}: n={total}, 成功率={rate:.1%}")


if __name__ == "__main__":
    main()
