from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ergasterion/tekhne/ A0→プロンプト品質の深掘り分析が必要→deep_engineが担う
"""
Deep Engine — Pro × 20次元プロンプト品質深掘り分析

Sweep Engine が検出した上位 N 件の issues を、
Gemini Pro で深掘り分析し、具体的な改善案を生成する。

Architecture:
  SweepReport.top_issues(n=20)
    → 20 deep-analysis prompts
    → CortexClient.ask_batch (gemini-3.1-pro-preview)
    → DeepReport (具体的改善案 + 優先順位)

Usage:
  from sweep_engine import SweepEngine
  from deep_engine import DeepEngine

  sweep = SweepEngine()
  sweep_report = sweep.sweep("prompt.skill.md")

  deep = DeepEngine()
  deep_report = deep.analyze(sweep_report.top_issues(n=20), "prompt.skill.md")

FEP mapping: Function axiom Exploit — 重要な問題を深く掘り下げる
"""


import json
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from mekhane.ochema.model_defaults import FLASH

logger = logging.getLogger(__name__)

# Project root for imports
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# === Data Structures ===


# PURPOSE: [L2-auto] DeepFix のクラス定義
@dataclass
class DeepFix:
    """A concrete fix for an issue."""

    original: str  # the problematic text/pattern
    replacement: str  # suggested replacement
    rationale: str  # why this fix helps
    confidence: float = 0.0  # 0.0-1.0


# PURPOSE: [L2-auto] DeepAnalysis のクラス定義
@dataclass
class DeepAnalysis:
    """Deep analysis of a single issue."""

    issue_id: str  # e.g. "Security-O1"
    severity: str  # re-assessed severity
    root_cause: str  # why this is a problem
    impact: str  # what happens if not fixed
    fixes: list[DeepFix] = field(default_factory=list)
    related_issues: list[str] = field(default_factory=list)
    priority_score: float = 0.0  # 0.0-1.0 (computed from severity + fixability)

    # PURPOSE: [L2-auto] has_actionable_fix の関数定義
    @property
    def has_actionable_fix(self) -> bool:
        return len(self.fixes) > 0 and any(f.replacement for f in self.fixes)


# PURPOSE: [L2-auto] DeepReport のクラス定義
@dataclass
class DeepReport:
    """Result of deep analysis on top issues."""

    filepath: str
    analyses: list[DeepAnalysis] = field(default_factory=list)
    errors: int = 0
    total_issues: int = 0
    elapsed_seconds: float = 0.0

    # PURPOSE: [L2-auto] prioritized の関数定義
    def prioritized(self) -> list[DeepAnalysis]:
        """Return analyses sorted by priority (highest first)."""
        return sorted(
            self.analyses, key=lambda a: a.priority_score, reverse=True
        )

    # PURPOSE: [L2-auto] actionable の関数定義
    def actionable(self) -> list[DeepAnalysis]:
        """Return only analyses with concrete fixes."""
        return [a for a in self.prioritized() if a.has_actionable_fix]

    # PURPOSE: [L2-auto] summary の関数定義
    def summary(self) -> str:
        """Human-readable summary."""
        lines = [
            f"{'=' * 60}",
            f"🔬 Deep Analysis Report: {self.filepath}",
            f"{'=' * 60}",
            f"  Issues analyzed: {self.total_issues}",
            f"  Analyses completed: {len(self.analyses)}",
            f"  Actionable fixes: {len(self.actionable())}",
            f"  Errors: {self.errors}",
            f"  Elapsed: {self.elapsed_seconds:.1f}s",
        ]

        if self.analyses:
            lines.append("")
            lines.append("  Prioritized Issues:")
            for i, analysis in enumerate(self.prioritized()[:10], 1):
                fix_count = len(analysis.fixes)
                actionable = "✅" if analysis.has_actionable_fix else "❌"
                sev_icon = {
                    "critical": "🔴",
                    "major": "🟠",
                    "minor": "🟡",
                    "info": "🔵",
                }.get(analysis.severity, "⚪")
                lines.append(
                    f"    {i:2d}. {sev_icon} [{analysis.issue_id}] "
                    f"P={analysis.priority_score:.2f} "
                    f"Fixes={fix_count} {actionable}"
                )
                lines.append(f"        Root cause: {analysis.root_cause[:60]}")

        lines.append(f"{'=' * 60}")
        return "\n".join(lines)

    # PURPOSE: [L2-auto] to_dict の関数定義
    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "filepath": self.filepath,
            "total_issues": self.total_issues,
            "analyses_count": len(self.analyses),
            "actionable_count": len(self.actionable()),
            "errors": self.errors,
            "elapsed_seconds": self.elapsed_seconds,
            "analyses": [
                {
                    "issue_id": a.issue_id,
                    "severity": a.severity,
                    "priority_score": a.priority_score,
                    "root_cause": a.root_cause,
                    "impact": a.impact,
                    "fixes": [
                        {
                            "original": f.original,
                            "replacement": f.replacement,
                            "rationale": f.rationale,
                            "confidence": f.confidence,
                        }
                        for f in a.fixes
                    ],
                    "related_issues": a.related_issues,
                }
                for a in self.prioritized()
            ],
        }


# === Response Parser ===


# PURPOSE: [L2-auto] _parse_deep_response の関数定義
def _parse_deep_response(response_text: str, issue_id: str) -> Optional[DeepAnalysis]:
    """Parse a Pro model deep analysis response."""
    text = response_text.strip()

    # Try JSON parse
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            fixes = []
            for fix_data in data.get("fixes", []):
                if isinstance(fix_data, dict):
                    fixes.append(
                        DeepFix(
                            original=fix_data.get("original", ""),
                            replacement=fix_data.get("replacement", ""),
                            rationale=fix_data.get("rationale", ""),
                            confidence=float(fix_data.get("confidence", 0.5)),
                        )
                    )

            severity = data.get("severity", "info").lower()
            severity_weight = {
                "critical": 1.0,
                "major": 0.75,
                "minor": 0.5,
                "info": 0.25,
            }.get(severity, 0.25)

            fix_quality = min(1.0, len(fixes) * 0.3) if fixes else 0.0
            priority = severity_weight * 0.6 + fix_quality * 0.4

            return DeepAnalysis(
                issue_id=issue_id,
                severity=severity,
                root_cause=data.get("root_cause", ""),
                impact=data.get("impact", ""),
                fixes=fixes,
                related_issues=data.get("related_issues", []),
                priority_score=priority,
            )
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: text-based extraction
    if len(text) > 100:
        return DeepAnalysis(
            issue_id=issue_id,
            severity="info",
            root_cause=text[:300],
            impact="",
            fixes=[],
            priority_score=0.1,
        )

    return None


# === Deep Engine ===


# PURPOSE: [L2-auto] DeepEngine のクラス定義
class DeepEngine:
    """Pro × 20 Core deep analysis engine.

    Takes top issues from SweepReport and performs deep analysis
    using Gemini Pro for detailed root cause analysis and fix generation.

    Usage:
        engine = DeepEngine()
        report = engine.analyze(sweep_issues, "path/to/prompt.skill.md")
        for fix in report.actionable():
            print(fix.summary())
    """

    DEFAULT_MODEL = "gemini-3.1-pro-preview"
    DEFAULT_DELAY = 1.0  # Pro has tighter rate limits

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        delay: float = DEFAULT_DELAY,
    ):
        self.model = model
        self.delay = delay
        self._client = None

    # PURPOSE: [L2-auto] _get_client の関数定義
    def _get_client(self):
        """Lazy-load CortexClient."""
        if self._client is None:
            from mekhane.ochema.cortex_client import CortexClient
            try:
                from mekhane.ochema.account_router import get_account_for
                account = get_account_for("batch")
            except Exception:  # noqa: BLE001
                account = "default"
            self._client = CortexClient(model=self.model, temperature=0.2, max_tokens=2048, account=account)
        return self._client

    # PURPOSE: [L2-auto] analyze の関数定義
    def analyze(
        self,
        issues: list,  # list[SweepIssue]
        filepath: str,
        max_issues: int = 20,
    ) -> DeepReport:
        """Run deep analysis on a list of issues.

        Args:
            issues: SweepIssues from SweepReport.top_issues()
            filepath: Path to the original prompt file
            max_issues: Maximum issues to analyze (default: 20)

        Returns:
            DeepReport with detailed analyses and fixes
        """
        start_time = time.time()
        issues = issues[:max_issues]

        # Read original content
        content = Path(filepath).read_text(encoding="utf-8")
        if len(content) > 6000:
            content = content[:6000] + "\n\n[... truncated ...]"

        logger.info("Deep: analyzing %d issues for %s", len(issues), filepath)

        system_instruction = (
            "You are an expert prompt engineer performing deep analysis. "
            "For each issue, provide:\n"
            "1. Root cause analysis (why this is a problem)\n"
            "2. Impact assessment (what happens if not fixed)\n"
            "3. Concrete fixes (original text → replacement)\n"
            "4. Related issues that might be connected\n\n"
            "Respond in JSON format:\n"
            "{\n"
            '  "severity": "critical|major|minor|info",\n'
            '  "root_cause": "...",\n'
            '  "impact": "...",\n'
            '  "fixes": [\n'
            '    {"original": "text to find", "replacement": "better text", '
            '"rationale": "why", "confidence": 0.0-1.0}\n'
            "  ],\n"
            '  "related_issues": ["issue_id1", "issue_id2"]\n'
            "}"
        )

        tasks = []
        for issue in issues:
            prompt = (
                f"## Issue to Analyze\n\n"
                f"- Perspective: {issue.perspective_id}\n"
                f"- Domain: {issue.domain}\n"
                f"- Axis: {issue.axis}\n"
                f"- Current Severity: {issue.severity}\n"
                f"- Description: {issue.description}\n\n"
                f"## Original Prompt Content\n\n{content}"
            )
            tasks.append({"prompt": prompt})

        # Execute
        client = self._get_client()
        report = DeepReport(
            filepath=filepath,
            total_issues=len(issues),
        )

        try:
            responses = client.ask_batch(
                tasks,
                default_model=self.model,
                default_system_instruction=system_instruction,
                delay=self.delay,
            )

            for resp, issue in zip(responses, issues):
                if resp.text.startswith("[ERROR]"):
                    report.errors += 1
                    continue

                analysis = _parse_deep_response(resp.text, issue.perspective_id)
                if analysis:
                    report.analyses.append(analysis)

        except Exception as e:  # noqa: BLE001
            logger.error("Deep analysis failed: %s", e)
            report.errors = len(issues)

        report.elapsed_seconds = time.time() - start_time
        return report


# === CLI ===


# PURPOSE: [L2-auto] main の関数定義
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Deep Engine — Pro × 20 Core Deep Analysis"
    )
    parser.add_argument("filepath", help="Path to prompt file")
    parser.add_argument(
        "--issues-json",
        help="JSON file with pre-extracted issues (from sweep --json)",
    )
    parser.add_argument(
        "--model",
        default=DeepEngine.DEFAULT_MODEL,
        help=f"Gemini model (default: {DeepEngine.DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=20,
        help="Max issues to analyze (default: 20)",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    if not Path(args.filepath).exists():
        print(f"Error: {args.filepath} not found", file=sys.stderr)
        sys.exit(1)

    # Load issues
    if args.issues_json:
        with open(args.issues_json) as f:
            data = json.load(f)

        from sweep_engine import SweepIssue
        issues = [
            SweepIssue(
                perspective_id=i["perspective_id"],
                domain=i["domain"],
                axis=i["axis"],
                severity=i["severity"],
                description=i["description"],
                recommendation=i.get("recommendation", ""),
            )
            for i in data.get("issues", data) if isinstance(i, dict)
        ]
    else:
        # Run sweep first
        print("🔍 Running sweep first (no --issues-json provided)...")
        from sweep_engine import SweepEngine
        sweep = SweepEngine(model=FLASH)
        sweep_report = sweep.sweep(args.filepath)
        issues = sweep_report.top_issues(n=args.max)
        print(f"   Found {len(issues)} top issues")
        print()

    engine = DeepEngine(model=args.model)
    report = engine.analyze(issues, args.filepath, max_issues=args.max)

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(report.summary())

        actionable = report.actionable()
        if actionable:
            print()
            print(f"🔧 Actionable Fixes ({len(actionable)}):")
            print("-" * 60)
            for i, analysis in enumerate(actionable, 1):
                print(f"\n  {i}. [{analysis.issue_id}] (P={analysis.priority_score:.2f})")
                print(f"     Root: {analysis.root_cause[:60]}")
                for fix in analysis.fixes[:3]:
                    print(f"     ✏️  '{fix.original[:40]}' → '{fix.replacement[:40]}'")
                    print(f"        {fix.rationale[:60]}")


if __name__ == "__main__":
    main()
