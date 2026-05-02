from __future__ import annotations
#!/usr/bin/env python3
# PROOF: mekhane/basanos/l2/cli.py
# PURPOSE: basanos モジュールのコマンドラインインターフェース (cli)
# PURPOSE: Basanos L2 問い生成 CLI — deficit 検出→問い生成→優先度表示
# REASON: 全 deficit factory を統合実行し、HGK の構造的ズレを対話的に発見する
"""Basanos L2 CLI: Structural deficit detection and question generation.

Usage:
    python -m mekhane.basanos.l2.cli scan              # Full scan
    python -m mekhane.basanos.l2.cli scan --type eta    # η deficit only
    python -m mekhane.basanos.l2.cli scan --type epsilon  # ε deficit only
    python -m mekhane.basanos.l2.cli scan --type delta  # Δε/Δt only
    python -m mekhane.basanos.l2.cli questions           # Generate questions
"""


import argparse
import sys
from pathlib import Path
from typing import Optional

from mekhane.basanos.l2.models import Deficit, DeficitType
from mekhane.basanos.l2.g_struct import GStruct
from mekhane.basanos.l2.deficit_factories import (
    EtaDeficitFactory,
    EpsilonDeficitFactory,
    DeltaDeficitFactory,
)
from mekhane.paths import HGK_ROOT
from mekhane.basanos.l2.history import record_scan, load_history, get_trend
from mekhane.basanos.l2.resolver import Resolver, print_resolutions


# ANSI colors
# PURPOSE: [L2-auto] C のクラス定義
class C:
    """ANSI color codes."""

    BOLD = "\033[1m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    DIM = "\033[2m"
    RESET = "\033[0m"


# PURPOSE: [L2-auto] _fetch_gnosis_keywords の関数定義
def _fetch_gnosis_keywords() -> list[tuple[str, list[str]]]:
    """Fetch paper keywords from Gnōsis knowledge base.

    Returns list of (paper_title, keywords) tuples.
    Returns empty list if Gnōsis is unavailable.
    """
    import subprocess as sp
    import json

    try:
        # Query gnosis for recent papers' keywords
        result = sp.run(
            [
                sys.executable,
                "-c",
                (
                    "import json, sys; sys.path.insert(0, '.'); "
                    "from mekhane.gnosis.kb import KnowledgeBase; "
                    "kb = KnowledgeBase(); "
                    "papers = kb.list_papers(limit=20); "
                    "out = [(p.title, p.keywords) for p in papers if p.keywords]; "
                    "print(json.dumps(out))"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(detect_project_root()),
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout.strip())
    except (sp.TimeoutExpired, OSError, json.JSONDecodeError, Exception):  # noqa: BLE001
        pass

    # Fallback: try gnosis MCP search for core topics
    try:
        result = sp.run(
            [
                sys.executable,
                "-m", "mekhane.gnosis.cli",
                "topics",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(detect_project_root()),
        )
        if result.returncode == 0 and result.stdout.strip():
            # Parse topics output into keyword pairs
            topics = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
            return [(t, t.split()) for t in topics[:10]]
    except (sp.TimeoutExpired, OSError, Exception):  # noqa: BLE001
        pass

    return []


# PURPOSE: [L2-auto] detect_project_root の関数定義
def detect_project_root() -> Path:
    """Find project root by looking for kernel/ directory."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "kernel").is_dir():
            return current
        current = current.parent
    # Fallback
    return HGK_ROOT


# PURPOSE: [L2-auto] scan_deficits の関数定義
def scan_deficits(
    project_root: Path,
    deficit_type: Optional[str] = None,
    since: str = "HEAD~5",
) -> list[Deficit]:
    """Run deficit factories and return all detected deficits."""
    kernel_root = project_root / "kernel"
    g_struct = GStruct(kernel_root)
    deficits: list[Deficit] = []

    # η deficit
    if deficit_type in (None, "eta"):
        eta_factory = EtaDeficitFactory(g_struct, project_root)
        print(f"{C.DIM}  scanning η deficits (external vs HGK)...{C.RESET}")

        # Try Gnōsis integration for paper keywords
        gnosis_keywords = _fetch_gnosis_keywords()
        if gnosis_keywords:
            for title, keywords in gnosis_keywords:
                deficits.extend(eta_factory.detect(keywords, title))
        else:
            # Fallback: detect series coverage gaps
            concepts = g_struct.scan_all()
            series_coverage = {c.series for c in concepts if c.series != "?"}
            expected = {"O", "S", "H", "P", "K", "A"}
            missing = expected - series_coverage
            for s in missing:
                deficits.append(
                    Deficit(
                        type=DeficitType.ETA,
                        severity=0.7,
                        source="kernel/",
                        target=f"{s}-series",
                        description=f"{s}-series の kernel/ 定義が見つからない",
                        evidence=[f"検出された series: {sorted(series_coverage)}"],
                        suggested_action=f"kernel/{s.lower()}*.md を確認",
                    )
                )

    # ε deficit
    if deficit_type in (None, "epsilon"):
        print(f"{C.DIM}  scanning ε deficits (impl + justification)...{C.RESET}")
        eps_factory = EpsilonDeficitFactory(g_struct, project_root)
        deficits.extend(eps_factory.detect_impl_deficits())

        # ε-just: check kernel claims against Gnōsis papers
        gnosis_kw_pairs = _fetch_gnosis_keywords()
        if gnosis_kw_pairs:
            all_keywords: set[str] = set()
            for _title, keywords in gnosis_kw_pairs:
                all_keywords.update(kw.lower() for kw in keywords)
            if all_keywords:
                deficits.extend(
                    eps_factory.detect_justification_deficits(all_keywords)
                )

    # Δε/Δt deficit
    if deficit_type in (None, "delta"):
        print(f"{C.DIM}  scanning Δε/Δt deficits (git changes)...{C.RESET}")
        delta_factory = DeltaDeficitFactory(project_root)
        deficits.extend(delta_factory.detect(since=since))

    # Sort by severity (highest first)
    deficits.sort(key=lambda d: d.severity, reverse=True)
    return deficits


# PURPOSE: [L2-auto] print_deficits の関数定義
def print_deficits(deficits: list[Deficit]) -> None:
    """Display deficits in a formatted table."""
    if not deficits:
        print(f"\n{C.GREEN}✅ ズレなし — 構造的整合性が保たれています{C.RESET}")
        return

    print(f"\n{C.BOLD}━━━ Basanos L2: 構造的差分レポート ━━━{C.RESET}\n")

    type_colors = {
        DeficitType.ETA: C.CYAN,
        DeficitType.EPSILON_IMPL: C.YELLOW,
        DeficitType.EPSILON_JUST: C.RED,
        DeficitType.DELTA: C.DIM,
    }

    for i, d in enumerate(deficits, 1):
        color = type_colors.get(d.type, C.RESET)
        severity_bar = "█" * int(d.severity * 10) + "░" * (10 - int(d.severity * 10))
        print(f"  {C.BOLD}{i:2d}.{C.RESET} [{color}{d.type.value}{C.RESET}] {severity_bar} {d.severity:.1f}")
        print(f"      {d.description}")
        if d.suggested_action:
            print(f"      {C.DIM}→ {d.suggested_action}{C.RESET}")
        print()

    print(f"{C.BOLD}合計: {len(deficits)} 件{C.RESET}")
    print(f"  η: {sum(1 for d in deficits if d.type == DeficitType.ETA)}")
    print(f"  ε-impl: {sum(1 for d in deficits if d.type == DeficitType.EPSILON_IMPL)}")
    print(f"  ε-just: {sum(1 for d in deficits if d.type == DeficitType.EPSILON_JUST)}")
    print(f"  Δε/Δt: {sum(1 for d in deficits if d.type == DeficitType.DELTA)}")


# PURPOSE: [L2-auto] print_questions の関数定義
def print_questions(deficits: list[Deficit], limit: int = 10) -> None:
    """Generate and display questions from deficits."""
    questions = [d.to_question() for d in deficits]
    questions.sort(key=lambda q: q.priority, reverse=True)

    if not questions:
        print(f"\n{C.GREEN}✅ 問いなし{C.RESET}")
        return

    print(f"\n{C.BOLD}━━━ Basanos L2: 問い一覧 (上位 {min(limit, len(questions))}) ━━━{C.RESET}\n")

    for i, q in enumerate(questions[:limit], 1):
        priority_icon = "🔴" if q.priority >= 0.7 else "🟡" if q.priority >= 0.4 else "🟢"
        print(f"  {priority_icon} {C.BOLD}Q{i}{C.RESET}: {q.text}")
        print(f"     {C.DIM}[{q.deficit.type.value}] priority={q.priority:.1f}{C.RESET}")
        print()


# PURPOSE: [L2-auto] main の関数定義
def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="basanos-l2",
        description="Basanos L2: 構造的差分検出 & 問い生成",
    )
    subparsers = parser.add_subparsers(dest="command")

    # scan command
    scan_parser = subparsers.add_parser("scan", help="deficit をスキャン")
    scan_parser.add_argument(
        "--type",
        choices=["eta", "epsilon", "delta"],
        help="特定の deficit タイプのみスキャン",
    )
    scan_parser.add_argument(
        "--since",
        default="HEAD~5",
        help="Δε/Δt の git 範囲 (default: HEAD~5)",
    )

    # questions command
    q_parser = subparsers.add_parser("questions", help="問いを生成")
    q_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="表示する問いの最大数 (default: 10)",
    )
    q_parser.add_argument(
        "--type",
        choices=["eta", "epsilon", "delta"],
        help="特定の deficit タイプのみ",
    )

    # history command
    hist_parser = subparsers.add_parser("history", help="deficit 履歴を表示")
    hist_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="表示するレコード数 (default: 10)",
    )
    hist_parser.add_argument(
        "--trend",
        action="store_true",
        help="トレンドサマリーを表示",
    )

    # resolve command (F4: L3)
    res_parser = subparsers.add_parser("resolve", help="deficit の解決策を自動提案")
    res_parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="提案する解決策の最大数 (default: 5)",
    )
    res_parser.add_argument(
        "--type",
        choices=["eta", "epsilon", "delta"],
        help="特定の deficit タイプのみ",
    )

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    project_root = detect_project_root()
    print(f"{C.DIM}project: {project_root}{C.RESET}")

    if args.command == "scan":
        deficits = scan_deficits(
            project_root,
            deficit_type=args.type,
            since=getattr(args, "since", "HEAD~5"),
        )
        print_deficits(deficits)
        # F8: auto-record to history
        hpath = record_scan(deficits, scan_type=args.type or "full")
        print(f"{C.DIM}📝 履歴記録: {hpath}{C.RESET}")

    elif args.command == "questions":
        deficits = scan_deficits(
            project_root,
            deficit_type=getattr(args, "type", None),
        )
        print_questions(deficits, limit=getattr(args, "limit", 10))

    elif args.command == "history":
        if getattr(args, "trend", False):
            trend = get_trend()
            icon = {"improving": "📉", "worsening": "📈", "stable": "➡️"}.get(trend["direction"], "❓")
            print(f"\n{C.BOLD}━━━ Basanos L2: トレンド ━━━{C.RESET}")
            print(f"  {icon} {trend['direction']}  (現在: {trend['current']}, 前回: {trend['previous']}, Δ: {trend['delta']:+d})")
            print(f"  sparkline: {trend.get('sparkline', '')}  (直近 {trend.get('window', 0)} 回)")
        else:
            records = load_history(limit=getattr(args, "limit", 10))
            if not records:
                print(f"\n{C.DIM}履歴なし{C.RESET}")
            else:
                print(f"\n{C.BOLD}━━━ Basanos L2: 履歴 (直近 {len(records)} 件) ━━━{C.RESET}\n")
                for r in records:
                    ts = r.get("timestamp", "?")[:19].replace("T", " ")
                    total = r.get("total", 0)
                    by_type = r.get("by_type", {})
                    type_str = " ".join(f"{k}:{v}" for k, v in by_type.items())
                    color = C.GREEN if total == 0 else C.YELLOW if total <= 5 else C.RED
                    print(f"  {C.DIM}{ts}{C.RESET}  {color}{total:3d}{C.RESET} 件  [{type_str}]")

    elif args.command == "resolve":
        deficits = scan_deficits(
            project_root,
            deficit_type=getattr(args, "type", None),
        )
        resolver = Resolver(project_root)
        resolutions = resolver.resolve_batch(
            deficits,
            max_resolutions=getattr(args, "limit", 5),
        )
        print_resolutions(resolutions)

    return 0


if __name__ == "__main__":
    sys.exit(main())
