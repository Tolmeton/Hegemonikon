#!/usr/bin/env python3
"""CoT Search Chain threshold experiment.

Compare search quality at different saturation thresholds to find the
sweet spot where multi-round CoT actually improves results.

Usage:
    cd ~/oikos/01_ヘゲモニコン｜Hegemonikon
    PYTHONPATH=. CUDA_VISIBLE_DEVICES="" .venv/bin/python experiments/cot_threshold_experiment.py
"""
import asyncio
import json
import logging
import time
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("cot_experiment")

QUERY = "free energy principle active inference"
THRESHOLDS = [0.15, 0.05, 0.02]  # original, medium, aggressive


async def run_single(threshold: float) -> dict:
    """Run a single research pass with a given saturation threshold."""
    from mekhane.periskope.engine import PeriskopeEngine

    logger.info("=" * 60)
    logger.info("EXPERIMENT: threshold=%.3f", threshold)
    logger.info("=" * 60)

    engine = PeriskopeEngine(max_results_per_source=10, verify_citations=False)

    # Override the config for this run
    engine._config["iterative_deepening"]["saturation_threshold"] = threshold

    t0 = time.time()
    report = await engine.research(
        query=QUERY,
        depth=2,
        expand_query=True,
        auto_digest=False,
    )
    elapsed = time.time() - t0

    # Extract metrics
    qm = report.quality_metrics
    trace = getattr(engine, "_reasoning_trace", None)

    result = {
        "threshold": threshold,
        "elapsed_seconds": round(elapsed, 1),
        "total_results": len(report.search_results),
        "quality_score": round(qm.overall_score, 3) if qm else None,
        "ndcg": round(qm.ndcg_at_10, 3) if qm else None,
        "entropy": round(qm.source_entropy, 3) if qm else None,
        "coverage": round(qm.query_coverage, 3) if qm else None,
        "cot_iterations": len(trace.steps) if trace else 0,
        "final_confidence": round(trace.latest_confidence * 100) if trace and trace.steps else 0,
        "total_learned": sum(len(s.learned) for s in trace.steps) if trace else 0,
        "total_gaps": sum(len(s.gaps) for s in trace.steps) if trace else 0,
    }

    logger.info("RESULT: %s", json.dumps(result, indent=2))
    return result


async def main():
    results = []
    for th in THRESHOLDS:
        try:
            r = await run_single(th)
            results.append(r)
        except Exception as e:
            logger.error("Failed at threshold=%.3f: %s", th, e)
            import traceback
            traceback.print_exc()

    # Summary table
    print("\n" + "=" * 80)
    print("CoT Search Chain — Threshold Experiment Results")
    print("=" * 80)
    print(f"{'Threshold':>10} {'Iters':>6} {'Quality':>8} {'NDCG':>6} "
          f"{'Learned':>8} {'Gaps':>5} {'Conf%':>6} {'Time':>7}")
    print("-" * 80)
    for r in results:
        print(f"{r['threshold']:>10.3f} {r['cot_iterations']:>6} "
              f"{r['quality_score'] or 0:>8.3f} {r['ndcg'] or 0:>6.3f} "
              f"{r['total_learned']:>8} {r['total_gaps']:>5} "
              f"{r['final_confidence']:>5}% {r['elapsed_seconds']:>6.1f}s")

    # Save to JSONL
    out = Path(__file__).parent / "cot_threshold_results.jsonl"
    with open(out, "a") as f:
        for r in results:
            r["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nResults saved to: {out}")


if __name__ == "__main__":
    asyncio.run(main())
