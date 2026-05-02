import asyncio
import time
import argparse
import sys
from pathlib import Path
import json

from mekhane.periskope.engine import PeriskopeEngine, ResearchReport
from mekhane.periskope.models import SynthModel

# REASON: [auto] 関数 run_benchmark の実装が必要だったため
async def run_benchmark(query: str, sources: list[str], max_recursion: int, breadth: int, depth: int):
    """Run a single benchmark iteration and print summary stats."""
    
    # Configure the engine to override MAX_RECURSION
    # REASON: [auto] クラス BenchEngine の実装が必要だったため
    class BenchEngine(PeriskopeEngine):
        MAX_RECURSION = max_recursion
        
    engine = BenchEngine(verify_citations=False, synth_models=[SynthModel.GEMINI_FLASH]) # Use Flash to save cost/time

    print(f"\n--- Running: query='{query}', MAX_RECURSION={max_recursion}, breadth={breadth}, depth={depth} ---")
    start = time.monotonic()
    
    try:
        report = await engine.research(
            query=query,
            sources=sources,
            depth=depth,
            breadth=breadth,
            llm_rerank=False, # Disable to stabilize time/cost
            auto_digest=False,
        )
        
        elapsed = time.monotonic() - start
        
        # Calculate costs (LLM tokens + search results)
        search_count = len(report.search_results)
        synth_tokens = sum(s.token_count for s in report.synthesis) if report.synthesis else 0
        quality = report.quality_metrics.overall_score if report.quality_metrics else 0.0
        
        print(f"Elapsed: {elapsed:.2f}s")
        print(f"Search Results: {search_count}")
        print(f"Synthesis Tokens: {synth_tokens}")
        if report.quality_metrics:
            print(f"Quality: {report.quality_metrics.summary()}")
        else:
            print("Quality: None")
            
        return {
            "max_recursion": max_recursion,
            "breadth": breadth,
            "elapsed_sec": elapsed,
            "search_count": search_count,
            "synth_tokens": synth_tokens,
            "quality": quality,
        }
    except Exception as e:
        print(f"Error during research: {e}")
        return {
            "max_recursion": max_recursion,
            "breadth": breadth,
            "elapsed_sec": 0,
            "search_count": 0,
            "synth_tokens": 0,
            "quality": 0,
        }

# REASON: [auto] 関数 main の実装が必要だったため

async def main():
    parser = argparse.ArgumentParser(description="Benchmark Phi0.5 recursive deepening.")
    parser.add_argument("--query", type=str, default="Compare Active Inference and Reinforcement Learning for AGI", help="Compound query to test")
    parser.add_argument("--sources", type=str, default="tavily", help="Comma-separated sources")
    args = parser.parse_args()

    sources = args.sources.split(",")

    print(f"Benchmarking with query: '{args.query}' and sources: {sources}")
    
    # Scenario 1: Baseline L2 (no Φ0.5 because MAX_RECURSION=0)
    res_base = await run_benchmark(args.query, sources, max_recursion=0, breadth=3, depth=2)
    
    # Scenario 2: Legacy Φ0.5 (1 level only, breadth=2)
    res_legacy = await run_benchmark(args.query, sources, max_recursion=1, breadth=2, depth=2)
    
    # Scenario 3: Full recursive Φ0.5 (MAX_RECURSION=2, breadth=2)
    res_full = await run_benchmark(args.query, sources, max_recursion=2, breadth=2, depth=2)
    
    print("\n=== SUMMARY ===")
    print(f"{'Scenario':<15} | {'Time (s)':<10} | {'Results':<10} | {'Tokens':<10} | {'Quality':<10}")
    print("-" * 65)
    print(f"{'L2 Baseline':<15} | {res_base['elapsed_sec']:<10.2f} | {res_base['search_count']:<10} | {res_base['synth_tokens']:<10} | {res_base['quality']:<10.2f}")
    print(f"{'Φ0.5 Legacy (1)':<15} | {res_legacy['elapsed_sec']:<10.2f} | {res_legacy['search_count']:<10} | {res_legacy['synth_tokens']:<10} | {res_legacy['quality']:<10.2f}")
    print(f"{'Φ0.5 Recursive(2)':<15} | {res_full['elapsed_sec']:<10.2f} | {res_full['search_count']:<10} | {res_full['synth_tokens']:<10} | {res_full['quality']:<10.2f}")

if __name__ == "__main__":
    asyncio.run(main())
