#!/usr/bin/env python3
"""
E11: α-τ 対応の定量化 — Paper III の代数的相転移と Hyphē の結晶化閾値

PURPOSE:
  Paper III §1.1: α > 0 でのみ copy/del (Markov 圏公理) が well-defined。
  Hyphē: ρ_MB > τ でのみ結晶化が起きる。
  linkage_crystallization.md: 「α-τ の構造的対応」。

  本実験は τ を連続的に掃引し、以下を測定する:
  1. 秩序パラメータ: chunk 数, coherence, G∘F 収束
  2. 相転移特性: 臨界 τ_c の特定, 秩序パラメータの不連続/急変
  3. α_eff(τ) マッピング: FEP 対応表 (Paper I §6.5) に基づく有効 α

  α_eff の定義:
    Paper I §6.5: α → +1 = exploitation (data-faithful), α → -1 = exploration (prior-faithful)
    Hyphē: high τ → fine grain → more chunks → exploitation of structure
           low τ → coarse grain → fewer chunks → exploration (prior-faithful)
    α_eff(τ) = 2 * (coherence(τ) - coherence_min) / (coherence_max - coherence_min) - 1
    これにより α_eff ∈ [-1, +1] にマップされる。

SOURCE: PINAKAS_TASK T-001
"""

import json
import pickle
import sys
import numpy as np
from pathlib import Path

HGK_ROOT = Path.home() / "Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
POC_DIR = HGK_ROOT / "60_実験｜Peira/06_Hyphē実験｜HyphePoC"

sys.path.insert(0, str(POC_DIR))
sys.path.insert(0, str(HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"))

from hyphe_chunker import chunk_session, Step


def load_cache():
    with open(POC_DIR / "embedding_cache.pkl", "rb") as f:
        return pickle.load(f)


def load_results():
    return json.load(open(POC_DIR / "results.json", encoding="utf-8"))


def prepare_sessions(cache, results):
    """Cache から (steps, embeddings, sid) リストを構築。"""
    sessions = []
    for r in results:
        sid = r["session_id"]
        if sid not in cache:
            continue
        sess = cache[sid]
        embs = sess["embeddings"]
        steps_raw = sess.get("steps", [])
        steps = []
        for i, s in enumerate(steps_raw):
            if isinstance(s, Step):
                steps.append(s)
            elif isinstance(s, str):
                steps.append(Step(index=i, text=s))
            elif hasattr(s, "text"):
                steps.append(Step(index=i, text=s.text))
            else:
                steps.append(Step(index=i, text=str(s)))
        if len(steps) >= 2:
            sessions.append((steps, embs, sid))
    return sessions


def run_tau_sweep(sessions, tau_values):
    """全セッション × 全 τ で chunking を実行し結果を収集。"""
    results = {}

    for tau in tau_values:
        tau_key = f"{tau:.3f}"
        session_metrics = []

        for steps, embs, sid in sessions:
            try:
                result = chunk_session(
                    steps, embs, tau=tau, min_steps=2, max_iterations=10,
                    sim_mode="pairwise",
                )
                coherences = [c.coherence for c in result.chunks]
                precisions = [c.precision for c in result.chunks]
                chunk_sizes = [len(c) for c in result.chunks]

                session_metrics.append({
                    "sid": sid,
                    "num_chunks": len(result.chunks),
                    "mean_coherence": float(np.mean(coherences)) if coherences else 0.0,
                    "std_coherence": float(np.std(coherences)) if coherences else 0.0,
                    "mean_precision": float(np.mean(precisions)) if precisions else 0.0,
                    "converged": result.converged,
                    "iterations": result.iterations,
                    "mean_chunk_size": float(np.mean(chunk_sizes)) if chunk_sizes else 0.0,
                    "total_steps": sum(chunk_sizes),
                })
            except Exception as e:
                continue

        if session_metrics:
            n = len(session_metrics)
            results[tau_key] = {
                "tau": tau,
                "n_sessions": n,
                "mean_num_chunks": float(np.mean([m["num_chunks"] for m in session_metrics])),
                "std_num_chunks": float(np.std([m["num_chunks"] for m in session_metrics])),
                "mean_coherence": float(np.mean([m["mean_coherence"] for m in session_metrics])),
                "std_coherence": float(np.std([m["mean_coherence"] for m in session_metrics])),
                "mean_precision": float(np.mean([m["mean_precision"] for m in session_metrics])),
                "convergence_rate": float(np.mean([m["converged"] for m in session_metrics])),
                "mean_iterations": float(np.mean([m["iterations"] for m in session_metrics])),
                "mean_chunk_size": float(np.mean([m["mean_chunk_size"] for m in session_metrics])),
            }

    return results


def compute_alpha_eff(sweep_results):
    """τ → α_eff マッピングを計算。

    α_eff(τ) は coherence を [-1, +1] に正規化。
    Paper I §6.5: α → +1 = e-connection (exploitation), α → -1 = m-connection (exploration)
    """
    coherences = [r["mean_coherence"] for r in sweep_results.values()]
    c_min, c_max = min(coherences), max(coherences)
    c_range = c_max - c_min if c_max > c_min else 1e-10

    alpha_map = {}
    for tau_key, r in sweep_results.items():
        alpha_eff = 2 * (r["mean_coherence"] - c_min) / c_range - 1
        alpha_map[tau_key] = {
            "tau": r["tau"],
            "alpha_eff": float(alpha_eff),
            "coherence": r["mean_coherence"],
            "num_chunks": r["mean_num_chunks"],
            "precision": r["mean_precision"],
        }
    return alpha_map


def find_critical_tau(sweep_results):
    """秩序パラメータの最大変化率から臨界 τ_c を特定。"""
    taus = sorted(sweep_results.keys())
    if len(taus) < 3:
        return None

    # dN/dτ (chunk 数の変化率)
    tau_vals = [sweep_results[t]["tau"] for t in taus]
    n_chunks = [sweep_results[t]["mean_num_chunks"] for t in taus]
    coherences = [sweep_results[t]["mean_coherence"] for t in taus]

    # 数値微分
    dn_dtau = np.gradient(n_chunks, tau_vals)
    dc_dtau = np.gradient(coherences, tau_vals)

    # |dN/dτ| が最大の点 = 相転移点
    max_dn_idx = int(np.argmax(np.abs(dn_dtau)))
    max_dc_idx = int(np.argmax(np.abs(dc_dtau)))

    return {
        "tau_c_chunks": float(tau_vals[max_dn_idx]),
        "max_dn_dtau": float(dn_dtau[max_dn_idx]),
        "tau_c_coherence": float(tau_vals[max_dc_idx]),
        "max_dc_dtau": float(dc_dtau[max_dc_idx]),
    }


def main():
    print("=" * 70)
    print("E11: α-τ 対応の定量化")
    print("=" * 70)

    cache = load_cache()
    results_orig = load_results()
    sessions = prepare_sessions(cache, results_orig)
    print(f"Sessions: {len(sessions)}")

    # τ sweep: 0.50 ~ 0.95, step 0.01
    tau_values = [round(0.50 + i * 0.01, 3) for i in range(46)]
    print(f"τ range: {tau_values[0]} ~ {tau_values[-1]} ({len(tau_values)} points)")

    print("\n[Phase 1] Running τ sweep...")
    sweep = run_tau_sweep(sessions, tau_values)

    # Print sweep summary
    print(f"\n{'τ':>6} | {'chunks':>7} | {'coherence':>10} | {'precision':>10} | {'conv%':>6} | {'iter':>5}")
    print("-" * 60)
    for tau_key in sorted(sweep.keys()):
        r = sweep[tau_key]
        print(f"{r['tau']:6.3f} | {r['mean_num_chunks']:7.1f} | {r['mean_coherence']:10.4f} | {r['mean_precision']:10.4f} | {r['convergence_rate']:5.0%} | {r['mean_iterations']:5.1f}")

    # Phase 2: α_eff mapping
    print("\n[Phase 2] Computing α_eff(τ) mapping...")
    alpha_map = compute_alpha_eff(sweep)

    print(f"\n{'τ':>6} | {'α_eff':>7} | {'coherence':>10} | {'chunks':>7}")
    print("-" * 45)
    for tau_key in sorted(alpha_map.keys()):
        a = alpha_map[tau_key]
        print(f"{a['tau']:6.3f} | {a['alpha_eff']:+7.3f} | {a['coherence']:10.4f} | {a['num_chunks']:7.1f}")

    # Phase 3: Critical τ
    print("\n[Phase 3] Finding critical τ_c...")
    critical = find_critical_tau(sweep)
    if critical:
        print(f"  τ_c (max |dN/dτ|): {critical['tau_c_chunks']:.3f} (dN/dτ = {critical['max_dn_dtau']:.1f})")
        print(f"  τ_c (max |dC/dτ|): {critical['tau_c_coherence']:.3f} (dC/dτ = {critical['max_dc_dtau']:.4f})")

        # α_eff at critical point
        tau_c_key = f"{critical['tau_c_chunks']:.3f}"
        if tau_c_key in alpha_map:
            print(f"  α_eff(τ_c) = {alpha_map[tau_c_key]['alpha_eff']:+.3f}")
            print(f"  理論予測: α_eff(τ_c) ≈ 0 (Paper III の α = 0 臨界点)")

    # Phase 4: Paper III 対応の検証
    print("\n[Phase 4] Paper III 対応の検証")
    print("  Paper III: α > 0 → copy/del well-defined → Markov 圏公理成立")
    print("  Hyphē:    ρ > τ → 結晶化可能 → chunk が安定形成")

    # α > 0 region: τ < τ_c (more chunks, structured)
    # α < 0 region: τ > τ_c (few chunks, degenerate)
    if critical:
        tau_c = critical["tau_c_chunks"]
        above_c = [(k, v) for k, v in sweep.items() if v["tau"] > tau_c + 0.05]
        below_c = [(k, v) for k, v in sweep.items() if v["tau"] < tau_c - 0.05]

        if above_c and below_c:
            above_conv = np.mean([v["convergence_rate"] for _, v in above_c])
            below_conv = np.mean([v["convergence_rate"] for _, v in below_c])
            above_chunks = np.mean([v["mean_num_chunks"] for _, v in above_c])
            below_chunks = np.mean([v["mean_num_chunks"] for _, v in below_c])

            print(f"\n  τ < τ_c (α > 0 側): mean chunks = {below_chunks:.1f}, conv rate = {below_conv:.0%}")
            print(f"  τ > τ_c (α < 0 側): mean chunks = {above_chunks:.1f}, conv rate = {above_conv:.0%}")
            print(f"  → 結晶化可能領域と不可能領域の非対称性が {'確認' if below_chunks > above_chunks * 1.5 else '不明瞭'}")

    # Save
    output = {
        "experiment": "e11_alpha_tau_correspondence",
        "tau_sweep": sweep,
        "alpha_map": alpha_map,
        "critical_tau": critical,
    }
    out_path = POC_DIR / "e11_alpha_tau_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved: {out_path}")


if __name__ == "__main__":
    main()
