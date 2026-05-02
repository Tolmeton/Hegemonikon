#!/usr/bin/env python3
"""
SWE-bench Trajectory 分析 — 選択的忘却定理の検証 (PyArrow バッチ版)
Paper II §5.3: Corr(Ξ, P) > 0

PyArrow iter_batches でメモリ効率的に処理。
"""

import sys
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

warnings.filterwarnings("ignore")

CACHE_FILE = Path("/tmp/swe_bench_cache/0000.parquet")
PARQUET_URL = (
    "https://huggingface.co/datasets/nebius/SWE-agent-trajectories/"
    "resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet"
)
N_SAMPLES = 500
MIN_TURNS = 3
BATCH_SIZE = 50  # バッチサイズを小さく

P = lambda *a, **k: print(*a, **k, flush=True)


def ensure_parquet() -> Path:
    """Parquet をDL (キャッシュあり)。"""
    if CACHE_FILE.exists() and CACHE_FILE.stat().st_size > 1_000_000:
        return CACHE_FILE
    import requests
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    P("  ダウンロード中...")
    resp = requests.get(PARQUET_URL, stream=True, timeout=120)
    resp.raise_for_status()
    with open(CACHE_FILE, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
    P(f"  完了: {CACHE_FILE.stat().st_size / 1e6:.1f} MB")
    return CACHE_FILE


def gini(x: np.ndarray) -> float:
    if len(x) == 0 or np.sum(x) == 0:
        return 0.0
    x = np.sort(x)
    n = len(x)
    idx = np.arange(1, n + 1)
    return float((2 * np.sum(idx * x)) / (n * np.sum(x)) - (n + 1) / n)


def obs_lengths(trajectory: list) -> list[int]:
    """observation ターンの文字数列。"""
    lengths = []
    for t in trajectory:
        if not isinstance(t, dict):
            continue
        role = t.get("role", "")
        if role in ("assistant", "system"):
            continue
        text = t.get("text") or ""
        if text:
            lengths.append(len(text))
    return lengths


def compute_xi(lengths: list[int]) -> dict:
    arr = np.array(lengths, dtype=float)
    mu = float(np.mean(arr))
    sigma = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    return {
        "xi_cv": sigma / mu if mu > 0 else 0.0,
        "xi_gini": gini(arr),
        "n_turns": len(arr),
        "mean_len": mu,
    }


def main():
    P("=" * 60)
    P("SWE-bench Trajectory — 選択的忘却定理の検証")
    P("=" * 60)

    pq_path = ensure_parquet()
    P(f"  Parquet: {pq_path.stat().st_size / 1e6:.1f} MB")

    import pyarrow.parquet as pq

    pf = pq.ParquetFile(str(pq_path))
    P(f"  行数: {pf.metadata.num_rows}")

    results = []
    n_filtered = 0
    n_total_rows = 0
    debug_done = False

    for batch in pf.iter_batches(
        batch_size=BATCH_SIZE,
        columns=["trajectory", "target", "model_name", "instance_id"],
    ):
        if len(results) >= N_SAMPLES:
            break

        # バッチを Python native に変換
        rows = batch.to_pylist()

        for row in rows:
            if len(results) >= N_SAMPLES:
                break
            n_total_rows += 1

            traj = row.get("trajectory")
            if traj is None:
                n_filtered += 1
                continue

            # デバッグ: 最初の行の構造を出力
            if not debug_done:
                P(f"  [debug] trajectory type: {type(traj).__name__}, len: {len(traj)}")
                if traj and len(traj) > 0:
                    t0 = traj[0]
                    P(f"  [debug] turn[0] type: {type(t0).__name__}")
                    if isinstance(t0, dict):
                        P(f"  [debug] keys: {list(t0.keys())}")
                        roles = set(t.get("role", "") for t in traj if isinstance(t, dict))
                        P(f"  [debug] roles: {roles}")
                debug_done = True

            lengths = obs_lengths(traj)
            if len(lengths) < MIN_TURNS:
                n_filtered += 1
                continue

            target = row.get("target")
            if target is None:
                continue

            xi = compute_xi(lengths)
            xi["target"] = bool(target)
            xi["model"] = row.get("model_name", "unknown")
            xi["instance_id"] = row.get("instance_id", "")
            results.append(xi)

        if len(results) % 100 < BATCH_SIZE and len(results) > 0:
            P(f"  {len(results)}/{N_SAMPLES} サンプル (処理: {n_total_rows})")

    P(f"\n  完了: {len(results)} サンプル (処理: {n_total_rows}, フィルタ: {n_filtered})")

    if len(results) < 30:
        P(f"ERROR: サンプル数が不足 ({len(results)} < 30)")
        sys.exit(1)

    # === 統計検定 ===
    P("\n[統計検定]")
    xi_cv = np.array([r["xi_cv"] for r in results])
    xi_gini = np.array([r["xi_gini"] for r in results])
    targets = np.array([r["target"] for r in results], dtype=bool)
    success, failure = targets, ~targets

    P(f"  成功: n={success.sum()}, Ξ_CV={xi_cv[success].mean():.4f}±{xi_cv[success].std():.4f}")
    P(f"  失敗: n={failure.sum()}, Ξ_CV={xi_cv[failure].mean():.4f}±{xi_cv[failure].std():.4f}")
    P(f"  成功: Ξ_Gini={xi_gini[success].mean():.4f}±{xi_gini[success].std():.4f}")
    P(f"  失敗: Ξ_Gini={xi_gini[failure].mean():.4f}±{xi_gini[failure].std():.4f}")

    r_cv, p_cv = stats.pointbiserialr(targets.astype(int), xi_cv)
    r_gini, p_gini = stats.pointbiserialr(targets.astype(int), xi_gini)
    P(f"  PB (Ξ_CV):  r={r_cv:.4f}, p={p_cv:.4e}")
    P(f"  PB (Ξ_Gini): r={r_gini:.4f}, p={p_gini:.4e}")

    u_cv, p_mw_cv = stats.mannwhitneyu(xi_cv[success], xi_cv[failure], alternative="greater")
    u_gini, p_mw_gini = stats.mannwhitneyu(xi_gini[success], xi_gini[failure], alternative="greater")
    n = len(results)
    z_cv = stats.norm.ppf(1 - p_mw_cv) if p_mw_cv < 1 else 0
    z_gini = stats.norm.ppf(1 - p_mw_gini) if p_mw_gini < 1 else 0
    eff_cv = z_cv / np.sqrt(n)
    eff_gini = z_gini / np.sqrt(n)
    P(f"  MW (Ξ_CV):  U={u_cv:.0f}, p={p_mw_cv:.4e}, r={eff_cv:.4f}")
    P(f"  MW (Ξ_Gini): U={u_gini:.0f}, p={p_mw_gini:.4e}, r={eff_gini:.4f}")

    # 判定
    v_cv = "支持" if r_cv > 0 and p_cv < 0.05 else "棄却" if r_cv <= 0 else "不確定"
    v_gini = "支持" if r_gini > 0 and p_gini < 0.05 else "棄却" if r_gini <= 0 else "不確定"

    P(f"\n{'='*60}")
    P("Paper II §5.3 追記用テーブル:")
    P("| 指標 | r_PB | p | MW_p | 効果量 | 判定 |")
    P("|:-----|:-----|:--|:-----|:-------|:-----|")
    P(f"| Ξ_CV | {r_cv:+.4f} | {p_cv:.2e} | {p_mw_cv:.2e} | {eff_cv:.4f} | {v_cv} |")
    P(f"| Ξ_Gini | {r_gini:+.4f} | {p_gini:.2e} | {p_mw_gini:.2e} | {eff_gini:.4f} | {v_gini} |")
    P(f"\nN={n} (成功: {success.sum()}, 失敗: {failure.sum()})")

    P("\n--- モデル別 ---")
    mc: dict[str, dict[str, int]] = defaultdict(lambda: {"s": 0, "f": 0})
    for r in results:
        mc[r["model"]]["s" if r["target"] else "f"] += 1
    for m, c in sorted(mc.items(), key=lambda x: x[1]["s"] + x[1]["f"], reverse=True)[:10]:
        t = c["s"] + c["f"]
        P(f"  {m}: n={t}, 成功率={c['s']/t:.0%}")


if __name__ == "__main__":
    main()
