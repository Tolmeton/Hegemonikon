#!/usr/bin/env python3
# PROOF: [L2/運用] <- scripts/
# PURPOSE: Gnōsis 知識の能動的活用 — WF/タスクに関連する学術知見を自動提示
"""
gnosis_advisor.py — Gnōsis 知識アドバイザー

セッション中に関連知識を自動提示し、学術知見の活用機会を増やす。
/boot 時に日次トピックを表示、WF 実行時にコンテキスト検索を実行する。

Usage:
    python scripts/gnosis_advisor.py --daily              # /boot 用日次トピック
    python scripts/gnosis_advisor.py --query "自由エネルギー原理"  # クエリ検索
    python scripts/gnosis_advisor.py --wf noe             # WF 関連知識
    python scripts/gnosis_advisor.py --topics             # トピック一覧
"""

import sys
import argparse
import subprocess
from pathlib import Path
from typing import Optional

# ============================================================
# Config
# ============================================================

PROJECT_ROOT = Path(__file__).parent.parent
CLI_PATH = PROJECT_ROOT / "mekhane" / "anamnesis" / "cli.py"
PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"

# WF → 検索クエリ のマッピング
# 各 WF に対して最も関連する学術トピックを定義
WF_TOPICS = {
    # Telos (目的)
    "noe": ["metacognition self-monitoring", "intuition cognitive science"],
    "bou": ["motivation goal-setting willpower", "intrinsic motivation"],
    "zet": ["inquiry-based learning question generation", "Socratic method"],
    "ene": ["action implementation intention", "behavior change"],
    # Schema (様態)
    "met": ["measurement scale cognitive", "psychometrics"],
    "mek": ["method design systematic", "design patterns"],
    "sta": ["evaluation criteria benchmark", "assessment framework"],
    "pra": ["practical wisdom phronesis", "applied ethics"],
    # Krisis (傾向)
    "pro": ["first impressions priming", "System 1 thinking"],
    "pis": ["epistemic confidence calibration", "Bayesian reasoning"],
    "ore": ["desire motivation hedonic", "value alignment"],
    "dox": ["belief revision update", "Bayesian belief"],
    # Akribeia (精密)
    "pat": ["emotion regulation meta-emotion", "affective forecasting"],
    "dia": ["critical evaluation adversarial thinking", "epistemic humility"],
    "gno": ["maxim principle extraction", "heuristics"],
    "epi": ["justified true belief epistemology", "knowledge formation"],
    # Chronos (時間)
    "sop": ["research methodology survey", "systematic review"],
    "chr": ["temporal cognition time perception", "deadline effect"],
    "tel": ["teleological purpose means-ends", "goal hierarchy"],
    "euk": ["opportunity recognition timing", "decision timing"],
    # Meta
    "boot": ["session initialization priming", "cognitive warm-up"],
    "bye": ["knowledge transfer handoff", "organizational memory"],
    "ax": ["category theory universal property", "mathematical structures"],
}

# 高優先度ソース（学術系を優先）
PRIORITY_SOURCES = ["arxiv", "research", "ki", "kernel"]


# ============================================================
# Search Functions
# ============================================================

def _run_cli_search(
    query: str,
    limit: int = 3,
    source: Optional[str] = None,
) -> str:
    """cli.py search を実行して結果を返す。"""
    cmd = [
        str(PYTHON), str(CLI_PATH), "search", query,
        "--limit", str(limit),
    ]
    if source:
        cmd.extend(["--source", source])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
            env={"PYTHONPATH": str(PROJECT_ROOT), "PATH": "/usr/bin:/bin"},
        )
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return f"Error: {e}"


def search_for_wf(wf_name: str, limit: int = 2) -> str:
    """WF に関連する学術知識を検索。"""
    topics = WF_TOPICS.get(wf_name)
    if not topics:
        return f"⚠️ WF '{wf_name}' に対するトピック定義がありません"

    results = []
    for topic in topics[:2]:  # 最大2トピック
        for source in PRIORITY_SOURCES[:2]:  # arxiv, research を優先
            output = _run_cli_search(topic, limit=limit, source=source)
            if "Found" in output and "0 results" not in output:
                results.append(f"🔍 [{source}] {topic}")
                # タイトル行のみ抽出
                for line in output.split("\n"):
                    if line.strip().startswith("[") and "]" in line:
                        title = line.split("]", 1)[1].strip()
                        if title:
                            results.append(f"  📄 {title}")
                    elif "URL:" in line:
                        url = line.split("URL:", 1)[1].strip()
                        results.append(f"     → {url}")
                break  # 最初にヒットしたソースで十分

    if not results:
        return f"📚 WF '{wf_name}': 関連する学術知識が見つかりませんでした"

    header = f"📚 /{wf_name} 関連知識 ({len(results)} hits)"
    return "\n".join([header, ""] + results)


def daily_topics() -> str:
    """日次トピック: /boot 用のランダムな知識ハイライト。"""
    lines = [
        "📚 Gnōsis 日次ハイライト",
        "",
    ]

    # 各優先ソースから1件ずつ
    queries = [
        ("metacognition LLM", "arxiv"),
        ("free energy principle", "research"),
        ("cognitive control", "ki"),
    ]

    for query, source in queries:
        output = _run_cli_search(query, limit=1, source=source)
        if "Found" in output and "0 results" not in output:
            for line in output.split("\n"):
                if line.strip().startswith("[1]"):
                    title = line.split("]", 1)[1].strip()
                    lines.append(f"  📄 [{source}] {title}")
                    break

    if len(lines) <= 2:
        lines.append("  （ヒットなし — Gnōsis インデックスを確認してください）")

    return "\n".join(lines)


def list_topics() -> str:
    """WF → トピック マッピング一覧。"""
    lines = ["📋 WF × Gnōsis トピックマッピング", ""]
    for wf, topics in sorted(WF_TOPICS.items()):
        topics_str = " | ".join(topics[:2])
        lines.append(f"  /{wf}: {topics_str}")
    return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Gnōsis 知識アドバイザー — WF/タスクに関連する学術知見を自動提示"
    )
    parser.add_argument("--daily", action="store_true", help="/boot 用日次トピック")
    parser.add_argument("--query", type=str, help="フリーテキスト検索")
    parser.add_argument("--wf", type=str, help="WF 名で関連知識を検索")
    parser.add_argument("--topics", action="store_true", help="トピック一覧表示")
    parser.add_argument("--limit", type=int, default=2, help="結果数")
    parser.add_argument("--source", type=str, help="ソースフィルタ")
    args = parser.parse_args()

    if args.topics:
        print(list_topics())
    elif args.daily:
        print(daily_topics())
    elif args.wf:
        print(search_for_wf(args.wf, limit=args.limit))
    elif args.query:
        if args.source:
            print(_run_cli_search(args.query, limit=args.limit, source=args.source))
        else:
            # 学術系ソースを優先して検索
            for source in PRIORITY_SOURCES:
                output = _run_cli_search(args.query, limit=args.limit, source=source)
                if "Found" in output and "0 results" not in output:
                    print(f"📚 Source: {source}")
                    print(output)
                    break
            else:
                # フォールバック: 全ソース検索
                print(_run_cli_search(args.query, limit=args.limit))
    else:
        parser.print_help()

    sys.exit(0)


if __name__ == "__main__":
    main()
