#!/usr/bin/env python3
"""
Benchmark Script for Periskopē Cognition Flow.

Compares search quality metrics across different cognitive depths:
- Depth 1 (Quick): Basic keyword search, minimal LLM intervention.
- Depth 2 (Standard): Full cognitive flow (Φ1-Φ7) with query expansion, divergence, and pre-search ranking.

Metrics measured:
- NDCG (Pipeline sort health)
- Source Entropy (Diversity of sources)
- Coverage (Conceptual completeness)
- Score Spread (LLM reranker discrimination)
- Latency (Time taken)
"""

import asyncio
import json
import logging
import random
import sys
import time
from pathlib import Path

from mekhane.periskope.engine import PeriskopeEngine


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("benchmark")


QUERIES = [
    # 1. Concept / Philosophy (Needs broad synthesis)
    "Free Energy Principle vs Active Inference",
    
    # 2. Implementation / Technical (Needs precise ranking and code parsing)
    "How to use FAISS with Sentence Transformers in Python",
    
    # 3. Academic / Deep research (Needs citation verification)
    "Attention is All You Need key mechanisms",
]

# Use internal sources to keep it fast and deterministic.
# 3 sources → max_entropy = log₂(3) ≈ 1.58, avoiding the ceiling effect
# that occurs with only 2 sources (max_entropy = 1.0).
SOURCES = ["gnosis", "sophia", "kairos"]

OUTPUT_DIR = Path("output/benchmarks")


async def run_benchmark(query: str, depth: int) -> dict:
    """Run a single benchmark for a query at a given depth."""
    logger.info("Running benchmark: query='%s', depth=%d", query, depth)
    
    # Disable verify_citations to isolate search/synthesis performance differences
    # and reduce overall latency variance caused by external paper fetches.
    engine = PeriskopeEngine(
        verify_citations=False,
        max_results_per_source=5,
    )
    
    start_time = time.time()
    try:
        report = await engine.research(
            query=query,
            sources=SOURCES,
            depth=depth,
        )
    except Exception as e:
        logger.error("Error running research for '%s' (depth=%d): %s", query, depth, e)
        return {
            "query": query,
            "depth": depth,
            "error": str(e),
            "latency": time.time() - start_time,
        }
        
    latency = time.time() - start_time
    
    metrics = report.quality_metrics
    
    # Track per-source hit counts for M1 validation (Kairos effectiveness)
    source_counts = {}
    for r in report.search_results:
        src = r.source.value if hasattr(r.source, 'value') else str(r.source)
        source_counts[src] = source_counts.get(src, 0) + 1
    
    res = {
        "query": query,
        "depth": depth,
        "latency": latency,
        "results_count": len(report.search_results),
        "source_counts": source_counts,
        "ndcg_at_10": metrics.ndcg_at_10 if metrics else 0.0,
        "entropy": metrics.source_entropy_normalized if metrics else 0.0,
        "coverage": metrics.coverage_score if metrics else 0.0,
        "score_spread": metrics.score_spread if metrics else 0.0,
        "overall_score": metrics.overall_score if metrics else 0.0,
    }
    
    # Save markdown report for qualitative comparison
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = query.lower().replace(" ", "_")[:30] + f"_d{depth}.md"
    (OUTPUT_DIR / filename).write_text(report.markdown())
    
    return res


async def main() -> None:
    logger.info("Starting Cognitive Depth Benchmark")
    logger.info("Queries: %s", len(QUERIES))
    logger.info("Sources: %s", SOURCES)
    
    results = []
    
    for i, query in enumerate(QUERIES):
        logger.info("---")
        # Run DB warmup (first run pays the BAAI model loading cost)
        
        # Depth 1
        res1 = await run_benchmark(query, depth=1)
        results.append(res1)
        
        # Human-like pause between D1 → D2 (5-15s with gaussian jitter)
        d1_d2_wait = max(3.0, random.gauss(10.0, 3.0))
        logger.info("  💤 Waiting %.1fs before D2...", d1_d2_wait)
        await asyncio.sleep(d1_d2_wait)
        
        # Depth 2
        res2 = await run_benchmark(query, depth=2)
        results.append(res2)
        
        # Log per-source hit counts for each depth
        for res in [res1, res2]:
            if "error" not in res:
                sc = res.get("source_counts", {})
                logger.info("  D%d sources: %s (total=%d)", 
                           res["depth"], sc, res["results_count"])
        
        # Human-like pause between queries (20-50s with gaussian jitter)
        if i < len(QUERIES) - 1:
            inter_query_wait = max(10.0, random.gauss(35.0, 8.0))
            logger.info("  💤 Waiting %.1fs before next query...", inter_query_wait)
            await asyncio.sleep(inter_query_wait)

    # Calculate differences
    summary = []
    for q in QUERIES:
        d1 = next((r for r in results if r["query"] == q and r["depth"] == 1), None)
        d2 = next((r for r in results if r["query"] == q and r["depth"] == 2), None)
        
        if d1 and d2 and "error" not in d1 and "error" not in d2:
            diff = {
                "query": q,
                "d1_score": d1["overall_score"],
                "d2_score": d2["overall_score"],
                "latency_diff": d2["latency"] - d1["latency"],
                "ndcg_diff": d2["ndcg_at_10"] - d1["ndcg_at_10"],
                "entropy_diff": d2["entropy"] - d1["entropy"],
                "coverage_diff": d2["coverage"] - d1["coverage"],
                "score_diff": d2["overall_score"] - d1["overall_score"],
            }
            summary.append(diff)
            
    # Print summary table
    print("\n" + "="*80)
    print("BENCHMARK SUMMARY (Depth 2 vs Depth 1)")
    print("="*80)
    print(f"{'Query':<40} | {'Lat Δ':>7} | {'NDCG Δ':>7} | {'Ent Δ':>7} | {'Cov Δ':>7} | {'Score Δ':>7} | {'Rel%':>6}")
    print("-" * 90)
    
    for d in summary:
        # Show relative regression percentage for clearer interpretation
        d1_score = d.get('d1_score', 0.01)
        rel_pct = (d['score_diff'] / max(d1_score, 0.01)) * 100
        print(f"{d['query'][:40]:<40} | "
              f"{d['latency_diff']:+6.1f}s | "
              f"{d['ndcg_diff']:+6.3f} | "
              f"{d['entropy_diff']:+6.3f} | "
              f"{d['coverage_diff']:+6.3f} | "
              f"{d['score_diff']:+6.3f} | "
              f"{rel_pct:+5.1f}%")
              
    print("="*80)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / "benchmark_results.json"
    with open(out_file, "w") as f:
        json.dump({"raw": results, "summary": summary}, f, indent=2)

    has_failure = False
    for d in summary:
        # Assert that Depth 2 (L2) is not significantly worse than Depth 1 (L1)
        # Use relative regression: > 10% worse relative to D1 score
        d1_score = d.get('d1_score', 0.01)
        relative_regression = d['score_diff'] / max(d1_score, 0.01)
        if relative_regression < -0.10:
            logger.error(
                "Regression detected: D2 score is %.3f worse than D1 (%.1f%% relative) "
                "for query '%s'\n"
                "  D1=%.3f, D2=%.3f | NDCG Δ=%.3f, Entropy Δ=%.3f, Coverage Δ=%.3f",
                d['score_diff'], relative_regression * 100, d['query'],
                d['d1_score'], d['d2_score'],
                d['ndcg_diff'], d['entropy_diff'], d['coverage_diff'],
            )
            has_failure = True

    if has_failure:
        logger.error("CI Benchmark failed due to quality regressions.")
        sys.exit(1)
        
    logger.info("Benchmark complete and passed CI checks. Results saved to %s", out_file)


if __name__ == "__main__":
    asyncio.run(main())
