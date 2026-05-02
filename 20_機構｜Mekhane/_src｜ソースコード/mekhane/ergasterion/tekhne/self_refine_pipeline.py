from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ergasterion/tekhne/ A0→プロンプト自動改善が必要→self_refine_pipelineが担う
"""
Self-Refine Pipeline — プロンプトの品質を自動改善

6つのモード:
  1. 静的解析 (--mode static): prompt_quality_scorer による改善提案
  2. LLM Self-Refine (--mode llm): Hermēneus execute /dia- で批評→改善
  3. 両方 (--mode full): 静的 → LLM
  4. Sweep (--mode sweep): Flash × 480次元広域スキャン [NEW]
  5. Deep (--mode deep): Pro × 20次元深掘り分析 [NEW]
  6. Auto (--mode auto): Sweep → Deep → 改善案 [NEW]

Usage:
  # 静的解析のみ
  python self_refine_pipeline.py --input prompt.skill.md --mode static

  # Flash 480次元 Sweep
  python self_refine_pipeline.py --input prompt.skill.md --mode sweep

  # Auto (Sweep → Deep → 改善案)
  python self_refine_pipeline.py --input prompt.skill.md --mode auto
"""


import argparse
import json
import subprocess
import sys
from pathlib import Path
from mekhane.ochema.model_defaults import FLASH

# Import scorer
sys.path.insert(0, str(Path(__file__).parent))
from prompt_quality_scorer import format_report, score_prompt


# PURPOSE: self_refine_pipeline の static refine 処理を実行する
def static_refine(filepath: str, threshold: int = 80, max_iter: int = 3) -> dict:
    """
    Run static analysis refinement loop.
    Returns suggestions without modifying the file.
    """
    report = score_prompt(filepath)
    iterations = []

    iterations.append({
        "iteration": 0,
        "score": report.total,
        "grade": report.grade,
        "status": "initial",
    })

    print(format_report(report, verbose=True))

    if report.total >= threshold:
        print(f"\n✅ Score {report.total}/100 ≥ threshold {threshold}. No refinement needed.")
        return {
            "final_score": report.total,
            "iterations": iterations,
            "suggestions": [],
            "status": "pass",
        }

    # Collect all suggestions
    all_suggestions = []
    for dim_name, dim in [("Structure", report.structure),
                           ("Safety", report.safety),
                           ("Completeness", report.completeness),
                           ("Archetype Fit", report.archetype_fit)]:
        for s in dim.suggestions:
            all_suggestions.append({
                "dimension": dim_name,
                "suggestion": s,
                "impact": dim.max_score - dim.score,
            })

    # Sort by impact (highest first)
    all_suggestions.sort(key=lambda x: x["impact"], reverse=True)

    print(f"\n⚠️  Score {report.total}/100 < threshold {threshold}")
    print(f"\n📋 Improvement Plan ({len(all_suggestions)} items, sorted by impact):")
    for i, s in enumerate(all_suggestions, 1):
        print(f"  {i}. [{s['dimension']}] {s['suggestion']} (impact: ~{s['impact']}pt)")

    return {
        "final_score": report.total,
        "iterations": iterations,
        "suggestions": all_suggestions,
        "status": "needs_improvement",
    }


# PURPOSE: self_refine_pipeline の llm refine 処理を実行する
def llm_refine(filepath: str, threshold: int = 80) -> dict:
    """
    LLM-based refinement using Hermēneus execute /dia-.
    Generates a critique CCL expression and attempts execution.
    """
    content = Path(filepath).read_text(encoding="utf-8")
    report = score_prompt(filepath)

    if report.total >= threshold:
        print(f"\n✅ Score {report.total}/100 ≥ threshold {threshold}. LLM refine skipped.")
        return {"status": "pass", "score": report.total}

    # Build context for Hermēneus
    weak_dimensions = []
    for dim_name, dim in [("Structure", report.structure),
                           ("Safety", report.safety),
                           ("Completeness", report.completeness),
                           ("Archetype Fit", report.archetype_fit)]:
        if dim.normalized < 70:
            weak_dimensions.append(f"{dim_name} ({dim.normalized}/100)")

    context = (
        f"以下のプロンプトファイルの品質レビューを行え。\n"
        f"ファイル: {filepath}\n"
        f"現在スコア: {report.total}/100 (Grade: {report.grade})\n"
        f"弱い次元: {', '.join(weak_dimensions)}\n"
        f"検出 Archetype: {report.detected_archetype or 'N/A'}\n"
        f"検出フォーマット: {report.detected_format}\n\n"
        f"--- プロンプト内容 (先頭2000文字) ---\n"
        f"{content[:2000]}\n"
        f"--- ここまで ---\n\n"
        f"改善点を具体的に列挙し、修正案を提示せよ。"
    )

    # Try Hermēneus MCP execute
    print(f"\n🤖 LLM Self-Refine: Hermēneus execute /dia- を試行...")
    print(f"   Context: {len(context)} chars")
    print(f"   CCL: /dia-")

    try:
        # Use hermeneus CLI directly
        result = subprocess.run(
            [
                sys.executable, "-m", "hermeneus.src.cli",
                "execute", "/dia-",
                "--context", context,
                "--no-verify",
            ],
            capture_output=True, text=True, timeout=60,
            cwd=str(Path(__file__).parent.parent.parent.parent),
            env={**__import__("os").environ, "PYTHONPATH": str(Path(__file__).parent.parent.parent.parent)},
        )

        if result.returncode == 0:
            print(f"\n📝 Hermēneus /dia- 結果:")
            print(result.stdout[:3000])
            return {
                "status": "llm_critique_done",
                "score": report.total,
                "critique": result.stdout[:3000],
            }
        else:
            print(f"\n⚠️  Hermēneus 実行エラー: {result.stderr[:500]}")
            print("   → MCP 経由での実行を推奨: mcp_hermeneus_hermeneus_execute(ccl='/dia-', context=...)")
            return {
                "status": "llm_fallback",
                "score": report.total,
                "error": result.stderr[:500],
                "fallback_instruction": (
                    "Claude セッション内で以下を実行してください:\n"
                    f"  1. prompt_quality_scorer.py {filepath} -v でスコア確認\n"
                    f"  2. /dia- で批評\n"
                    f"  3. 改善を適用\n"
                    f"  4. 再スコアリング"
                ),
            }
    except subprocess.TimeoutExpired:
        print("\n⚠️  Hermēneus 実行タイムアウト (60s)")
        return {"status": "timeout", "score": report.total}
    except FileNotFoundError:
        print("\n⚠️  Hermēneus CLI が見つかりません")
        print("   → MCP 経由での実行を推奨")
        return {
            "status": "cli_not_found",
            "score": report.total,
            "fallback_instruction": (
                "MCP 経由で実行してください:\n"
                "  mcp_hermeneus_hermeneus_execute(ccl='/dia-', context='...')"
            ),
        }


# PURPOSE: self_refine_pipeline の full refine 処理を実行する
def full_refine(filepath: str, threshold: int = 80, max_iter: int = 3) -> dict:
    """Run static analysis first, then LLM refinement if needed."""
    print("=" * 60)
    print("Phase 1: Static Analysis")
    print("=" * 60)
    static_result = static_refine(filepath, threshold, max_iter)

    if static_result["status"] == "pass":
        return static_result

    print(f"\n{'=' * 60}")
    print("Phase 2: LLM Self-Refine")
    print("=" * 60)
    llm_result = llm_refine(filepath, threshold)

    return {
        "static": static_result,
        "llm": llm_result,
        "final_score": static_result["final_score"],
        "status": "full_refine_done",
    }


# PURPOSE: Sweep モード (Flash × 480次元) を実行する
def sweep_refine(filepath: str, **kwargs) -> dict:
    """Run Flash × 480 dimension sweep scan."""
    from sweep_engine import SweepEngine

    model = kwargs.get("model", FLASH)
    max_perspectives = kwargs.get("max_perspectives")
    domains = kwargs.get("domains")
    axes = kwargs.get("axes")

    engine = SweepEngine(model=model)
    report = engine.sweep(
        filepath,
        max_perspectives=max_perspectives,
        domains=domains,
        axes=axes,
    )

    print(report.summary())
    return report.to_dict()


# PURPOSE: Deep モード (Pro × 20次元) を実行する
def deep_refine(filepath: str, **kwargs) -> dict:
    """Run Pro × 20 core deep analysis."""
    from deep_engine import DeepEngine
    from sweep_engine import SweepEngine

    sweep_model = kwargs.get("sweep_model", FLASH)
    deep_model = kwargs.get("deep_model", "gemini-3.1-pro-preview")
    top_n = kwargs.get("top_n", 20)

    # Sweep first
    print("🔍 Phase 1: Sweep (Flash × 480)")
    sweep = SweepEngine(model=sweep_model)
    sweep_report = sweep.sweep(filepath)
    print(sweep_report.summary())

    # Deep analysis
    print(f"\n🔬 Phase 2: Deep (Pro × {top_n})")
    issues = sweep_report.top_issues(n=top_n)
    if not issues:
        print("  No issues found in sweep. Skip deep analysis.")
        return {"sweep": sweep_report.to_dict(), "deep": None, "status": "clean"}

    deep = DeepEngine(model=deep_model)
    deep_report = deep.analyze(issues, filepath, max_issues=top_n)
    print(deep_report.summary())

    return {
        "sweep": sweep_report.to_dict(),
        "deep": deep_report.to_dict(),
        "status": "deep_done",
    }


# PURPOSE: Auto モード (Sweep → Deep → 改善案) を実行する
def auto_refine(filepath: str, **kwargs) -> dict:
    """Full automatic pipeline: Sweep → Deep → Fixes."""
    result = deep_refine(filepath, **kwargs)

    if result.get("status") == "clean":
        return result

    deep_data = result.get("deep", {})
    if not deep_data:
        return result

    actionable = [
        a for a in deep_data.get("analyses", [])
        if any(f.get("replacement") for f in a.get("fixes", []))
    ]

    if actionable:
        print(f"\n🔧 Actionable Fixes: {len(actionable)}")
        print("-" * 60)
        for i, a in enumerate(actionable[:10], 1):
            print(f"  {i}. [{a['issue_id']}] P={a['priority_score']:.2f}")
            for fix in a.get("fixes", [])[:2]:
                if fix.get("replacement"):
                    print(f"     ✏️  '{fix['original'][:40]}' → '{fix['replacement'][:40]}'")

    result["actionable_count"] = len(actionable)
    result["status"] = "auto_done"
    return result


# PURPOSE: self_refine_pipeline の main 処理を実行する
def main():
    parser = argparse.ArgumentParser(description="Self-Refine Pipeline")
    parser.add_argument("--input", required=True, help="Input prompt file")
    parser.add_argument(
        "--mode",
        choices=["static", "llm", "full", "sweep", "deep", "auto"],
        default="full",
        help="Refinement mode (default: full)",
    )
    parser.add_argument("--threshold", type=int, default=80,
                        help="Quality threshold (default: 80)")
    parser.add_argument("--max-iterations", type=int, default=3,
                        help="Max static refinement iterations (default: 3)")
    parser.add_argument("--max-perspectives", type=int, default=None,
                        help="Max perspectives for sweep (for testing)")
    parser.add_argument("--top-n", type=int, default=20,
                        help="Top N issues for deep analysis (default: 20)")
    parser.add_argument("--sweep-model", default=FLASH,
                        help="Model for sweep (default: gemini-3-flash-preview)")
    parser.add_argument("--deep-model", default="gemini-3.1-pro-preview",
                        help="Model for deep (default: gemini-3.1-pro-preview)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    kwargs = {
        "model": args.sweep_model,
        "sweep_model": args.sweep_model,
        "deep_model": args.deep_model,
        "max_perspectives": args.max_perspectives,
        "top_n": args.top_n,
    }

    if args.mode == "static":
        result = static_refine(args.input, args.threshold, args.max_iterations)
    elif args.mode == "llm":
        result = llm_refine(args.input, args.threshold)
    elif args.mode == "full":
        result = full_refine(args.input, args.threshold, args.max_iterations)
    elif args.mode == "sweep":
        result = sweep_refine(args.input, **kwargs)
    elif args.mode == "deep":
        result = deep_refine(args.input, **kwargs)
    elif args.mode == "auto":
        result = auto_refine(args.input, **kwargs)
    else:
        result = full_refine(args.input, args.threshold, args.max_iterations)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
