#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/anamnesis/
"""
PROOF: [L2/インフラ]

P3 → セッションの振り返りが必要
   → 自動ナイトレビュー生成
   → night_review が担う

Q.E.D.

---

Night Review Generator - Hegemonikón M8 Anamnēsis
==================================================

セッション履歴からナイトレビューを自動生成する。

Usage:
    python -m mekhane.anamnesis.night_review generate           # 本日のレビュー
    python -m mekhane.anamnesis.night_review generate --all     # 全履歴遡及
    python -m mekhane.anamnesis.night_review list               # セッション一覧

Requirements:
    pip install google-genai python-dotenv
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

from mekhane.anamnesis.vault import VaultManager

# Load environment
from mekhane.paths import ensure_env
from mekhane.ochema.model_defaults import FLASH

try:
    from mekhane.paths import HANDOFF_DIR, HANDOFF_DIR as _HANDOFF_DIR
except ImportError:
    _HANDOFF_DIR = HANDOFF_DIR

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
BRAIN_DIR = Path.home() / ".gemini" / "antigravity" / "brain"
OUTPUT_DIR = _HANDOFF_DIR
ENV_FILE = PROJECT_ROOT / ".env"

# Load API key
ensure_env()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")  # 一元管理: GOOGLE_API_KEY を使用


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: セッション情報
class SessionInfo:
    """セッション情報"""

    session_id: str
    title: str
    objective: str
    created_at: Optional[str]
    modified_at: Optional[str]
    artifacts: List[Dict[str, Any]]


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: ナイトレビュー構造体
class NightReview:
    """ナイトレビュー構造体"""

    date: str
    summary: str  # 3-7行の変更サマリ
    learnings: List[str]  # 学び・気づき
    tasks: List[str]  # 明日に引き継ぐタスク候補
    sessions_processed: int
    generated_at: str


# PURPOSE: 単一のセッションディレクトリを処理するヘルパー関数。
def _process_session_dir(
    session_dir: Path, target_date: Optional[date]
) -> Optional[SessionInfo]:
    """
    単一のセッションディレクトリを処理するヘルパー関数。
    並列処理のために分離。
    """
    if not session_dir.is_dir():
        return None
    if session_dir.name.startswith("_"):
        return None

    session_id = session_dir.name

    # Find metadata files
    artifacts = []
    title = ""
    objective = ""
    created_at = None
    modified_at = None

    for md_file in session_dir.glob("*.md"):
        meta_file = session_dir / f"{md_file.name}.metadata.json"

        if not meta_file.exists():
            continue

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)

            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            artifact_updated = meta.get("updatedAt", "")

            # Track latest modification
            if artifact_updated:
                if modified_at is None or artifact_updated > modified_at:
                    modified_at = artifact_updated
                if created_at is None or artifact_updated < created_at:
                    created_at = artifact_updated

            artifacts.append(
                {
                    "type": meta.get("artifactType", "unknown"),
                    "summary": meta.get("summary", ""),
                    "content": content[:2000],
                    "updated_at": artifact_updated,
                }
            )

            # Extract title from implementation_plan or task
            if not title and "plan" in md_file.name.lower():
                lines = content.split("\n")
                for line in lines:
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break

        except Exception as e:  # noqa: BLE001
            print(f"Warning: Failed to read {meta_file}: {e}", file=sys.stderr)
            continue

    if not artifacts:
        return None

    # Filter by date if specified
    if target_date and modified_at:
        try:
            mod_date = datetime.fromisoformat(modified_at.replace("Z", "+00:00")).date()
            if mod_date != target_date:
                return None
        except Exception:  # noqa: BLE001
            pass  # TODO: Add proper error handling

    return SessionInfo(
        session_id=session_id,
        title=title or f"Session {session_id[:8]}",
        objective=objective,
        created_at=created_at,
        modified_at=modified_at,
        artifacts=artifacts,
    )


# PURPOSE: Antigravity brain からセッション情報を取得。
def get_sessions(target_date: Optional[date] = None) -> List[SessionInfo]:
    """
    Antigravity brain からセッション情報を取得。

    Args:
        target_date: 指定日のみ取得。Noneの場合は全件。
    """
    sessions = []

    # Use ProcessPoolExecutor to process sessions in parallel
    import concurrent.futures

    # Adjust max_workers based on the environment
    max_workers = min(32, (os.cpu_count() or 1) + 4)

    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_process_session_dir, p, target_date): p
            for p in BRAIN_DIR.iterdir()
        }

        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                if result:
                    sessions.append(result)
            except Exception as e:  # noqa: BLE001
                print(f"Error processing session: {e}", file=sys.stderr)

    # Sort by modified_at descending
    sessions.sort(key=lambda s: s.modified_at or "", reverse=True)

    return sessions


# PURPOSE: Gemini API用のプロンプトを生成
def generate_review_prompt(sessions: List[SessionInfo], target_date: date) -> str:
    """Gemini API用のプロンプトを生成"""

    session_summaries = []
    for s in sessions:
        artifact_list = "\n".join(
            [f"  - [{a['type']}] {a['summary'][:100]}..." for a in s.artifacts]
        )
        session_summaries.append(f"""
### {s.title}
- Session ID: {s.session_id[:8]}
- 更新日時: {s.modified_at}
- アーティファクト:
{artifact_list}
""")

    sessions_text = "\n".join(session_summaries)

    return f"""あなたは Hegemonikón スペースの振り返りアシスタントです。
以下のセッション情報に基づいて、{target_date.isoformat()} のナイトレビューを生成してください。

# セッション情報
{sessions_text}

# 出力フォーマット（厳密に従ってください）

## 今日の変更サマリ
（3〜7行で簡潔に。技術的な詳細よりも「何を達成したか」に焦点）

## 学び・気づき
- 気づき1（具体的に）
- 気づき2
- 気づき3

## 明日に引き継ぐタスク候補
- [ ] タスク1（アクション可能な形式で）
- [ ] タスク2
- [ ] タスク3

# 制約
- 日本語で出力
- 各セクションは簡潔に
- 推測や仮定は避け、提供された情報のみに基づく
"""


# PURPOSE: Gemini API を呼び出してレビューを生成
def call_gemini_api(prompt: str) -> str:
    """Gemini API を呼び出してレビューを生成"""

    if not GEMINI_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY not found. " "Set it in ~/oikos/01_ヘゲモニコン｜Hegemonikon/.env"
        )

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError(
            "google-genai not installed. " "Run: pip install google-genai"
        )

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=FLASH,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=1500,
        ),
    )

    return response.text


# PURPOSE: APIレスポンスを構造化
def parse_review_response(
    response_text: str, target_date: date, session_count: int
) -> NightReview:
    """APIレスポンスを構造化"""

    lines = response_text.strip().split("\n")

    summary_lines = []
    learnings = []
    tasks = []

    current_section = None

    for line in lines:
        line_stripped = line.strip()

        if "今日の変更サマリ" in line or "変更サマリ" in line:
            current_section = "summary"
            continue
        elif "学び" in line or "気づき" in line:
            current_section = "learnings"
            continue
        elif "タスク" in line or "引き継ぐ" in line:
            current_section = "tasks"
            continue

        if not line_stripped or line_stripped.startswith("#"):
            continue

        if current_section == "summary":
            summary_lines.append(line_stripped)
        elif current_section == "learnings":
            if line_stripped.startswith("- "):
                learnings.append(line_stripped[2:])
        elif current_section == "tasks":
            if line_stripped.startswith("- [ ] "):
                tasks.append(line_stripped[6:])
            elif line_stripped.startswith("- "):
                tasks.append(line_stripped[2:])

    return NightReview(
        date=target_date.isoformat(),
        summary="\n".join(summary_lines[:7]),
        learnings=learnings[:5],
        tasks=tasks[:5],
        sessions_processed=session_count,
        generated_at=datetime.now().isoformat(),
    )


# PURPOSE: レビューをファイルに保存
def save_review(review: NightReview) -> Path:
    """レビューをファイルに保存"""

    vault_root = OUTPUT_DIR.parent
    vault = VaultManager(vault_root)

    # Relative path from vault_root
    rel_dir = Path(OUTPUT_DIR.name)

    filename = f"review_{review.date}.md"
    rel_path = rel_dir / filename

    # MCP Tool Smell Check + Auto-Fix 連携
    mcp_smell_text = ""
    try:
        sys.path.append(str(PROJECT_ROOT))
        from scripts.check_mcp_smell import run_smell_check
        smell_report = run_smell_check()
        sys.path.pop()
        
        avg = smell_report["average_smells_per_server"]
        mcp_smell_text = f"## 🛠️ MCP Tool Smell Check\n\n- **Average Smells/Server**: {avg:.2f}\n"
        if avg > 0:
            mcp_smell_text += "\n### Details\n"
            for srv, smells in smell_report["details"].items():
                if smells:
                    mcp_smell_text += f"- **{srv}**:\n"
                    for s in smells:
                        mcp_smell_text += f"  - {s}\n"
            mcp_smell_text += "\n"

        # Auto-Fix dry-run report
        try:
            from scripts.fix_mcp_smell import run_fix
            fix_report = run_fix(dry_run=True)
            fixable = fix_report["total_fixed"]
            if fixable > 0:
                mcp_smell_text += f"### 🔧 Auto-Fixable: {fixable} descriptions\n"
                mcp_smell_text += "Run `python scripts/fix_mcp_smell.py --apply` to fix.\n\n"
        except Exception:  # noqa: BLE001
            pass  # fix report is optional
    except Exception as e:  # noqa: BLE001
        mcp_smell_text = f"## 🛠️ MCP Tool Smell Check\n\n- Error: {e}\n\n"

    content = f"""# 📋 Night Review ({review.date})

## 今日の変更サマリ

{review.summary}

## 学び・気づき

{chr(10).join(f'- {l}' for l in review.learnings)}

## 明日に引き継ぐタスク候補

{chr(10).join(f'- [ ] {t}' for t in review.tasks)}

{mcp_smell_text}
---
*Generated by Hegemonikón M8 Anamnēsis*
*Sessions processed: {review.sessions_processed}*
*Generated at: {review.generated_at}*
"""

    # Use VaultManager to write file (handles backup and atomic write)
    vault.write_file(rel_path, content)

    # Also save JSON for programmatic access
    json_filename = f"review_{review.date}.json"
    vault.write_json(rel_dir / json_filename, asdict(review))

    return vault_root / rel_path


# PURPOSE: ナイトレビューを生成。
def generate_night_review(
    target_date: Optional[date] = None,
    process_all: bool = False,
) -> NightReview:
    """
    ナイトレビューを生成。

    Args:
        target_date: レビュー対象日（デフォルト: 今日）
        process_all: 全履歴を遡及処理
    """

    if target_date is None:
        target_date = date.today()

    print(f"[Hegemonikon] M8 Anamnēsis - Night Review Generator")
    print(f"  Target: {target_date.isoformat()}")
    print(f"  Mode: {'All history' if process_all else 'Single day'}")

    # Get sessions
    sessions = get_sessions(None if process_all else target_date)

    if not sessions:
        print(f"  Warning: No sessions found for {target_date}")
        return NightReview(
            date=target_date.isoformat(),
            summary="本日の活動記録はありません。",
            learnings=[],
            tasks=[],
            sessions_processed=0,
            generated_at=datetime.now().isoformat(),
        )

    print(f"  Sessions found: {len(sessions)}")

    # Generate prompt
    prompt = generate_review_prompt(sessions, target_date)

    # Call API
    print("  Calling Gemini API...")
    response = call_gemini_api(prompt)

    # Parse response
    review = parse_review_response(response, target_date, len(sessions))

    # Save
    filepath = save_review(review)
    print(f"  Saved: {filepath}")

    return review


# PURPOSE: 全セッション一覧を表示
def list_sessions():
    """全セッション一覧を表示"""
    sessions = get_sessions()

    print(f"\n[Hegemonikon] Session List")
    print("=" * 60)
    print(f"Total: {len(sessions)} sessions\n")

    for s in sessions[:20]:  # Show first 20
        print(f"[{s.session_id[:8]}] {s.title}")
        print(f"    Modified: {s.modified_at}")
        print(f"    Artifacts: {len(s.artifacts)}")
        print()


# PURPOSE: CLI エントリポイント — 知識基盤の直接実行
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Night Review Generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate night review")
    gen_parser.add_argument("--date", type=str, help="Target date (YYYY-MM-DD)")
    gen_parser.add_argument("--all", action="store_true", help="Process all history")

    # list command
    subparsers.add_parser("list", help="List all sessions")

    args = parser.parse_args()

    if args.command == "generate":
        target = None
        if args.date:
            target = date.fromisoformat(args.date)

        review = generate_night_review(target, args.all)

        print("\n" + "=" * 60)
        print(f"# Night Review ({review.date})")
        print("=" * 60)
        print(f"\n{review.summary}\n")
        print("## 学び・気づき")
        for l in review.learnings:
            print(f"- {l}")
        print("\n## タスク候補")
        for t in review.tasks:
            print(f"- [ ] {t}")

    elif args.command == "list":
        list_sessions()


if __name__ == "__main__":
    main()
