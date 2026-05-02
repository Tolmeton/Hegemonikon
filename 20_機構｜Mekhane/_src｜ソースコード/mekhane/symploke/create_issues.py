#!/usr/bin/env python3
# PROOF: [L3/ユーティリティ] <- mekhane/symploke/ O4→レビュー結果からIssue生成が必要→create_issues が担う
"""
Jules Specialist レビュー結果 → GitHub Issue 自動作成 v1.0

完了したセッションの結果を取得し、重要な発見を GitHub Issue として起票する。

Usage:
  python create_issues.py --results /tmp/jules_test_*.json
  python create_issues.py --dir logs/specialist_daily --days 1
  python create_issues.py --results result.json --dry-run  # Issue 作成せず内容を表示

Requires:
  - gh CLI (GitHub CLI) がインストール・認証済み
  - JULES_API_KEY_01 環境変数（セッション結果取得用）
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import aiohttp
except ImportError:
    print("ERROR: aiohttp not installed. Run: pip install aiohttp")
    sys.exit(1)


# === 定数 ===
JULES_API_BASE = "https://jules.googleapis.com/v1alpha/sessions"
MIN_QUALITY_SCORE = 4  # この閾値以上の品質スコアで Issue を作成
REPO = os.getenv("JULES_REPO_SOURCE", "Tolmeton/Hegemonikon")


# PURPOSE: API キーを1つ取得
def get_api_key() -> str:
    """セッション確認用の API キーを取得"""
    for i in range(1, 20):
        key = os.getenv(f"JULES_API_KEY_{i:02d}")
        if key:
            return key
    raise RuntimeError("No API key found (JULES_API_KEY_01~19)")


# PURPOSE: セッション状態を取得
async def get_session(session_id: str, api_key: str) -> dict:
    """Jules セッションの状態と結果を取得"""
    headers = {"X-Goog-Api-Key": api_key}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{JULES_API_BASE}/{session_id}",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            return {"error": resp.status, "session_id": session_id}


# PURPOSE: 複数セッションをバッチ取得
async def fetch_sessions(session_ids: list[str], api_key: str) -> list[dict]:
    """複数セッションを並列で取得（rate limit 考慮）"""
    results = []
    for sid in session_ids:
        result = await get_session(sid, api_key)
        results.append(result)
        await asyncio.sleep(0.5)  # rate limit 対策
    return results


# PURPOSE: 結果ファイルからセッション情報を抽出
def extract_sessions(result_file: Path) -> list[dict]:
    """結果 JSON からセッション情報を抽出"""
    data = json.loads(result_file.read_text())
    sessions = []

    if "files" in data:
        for file_entry in data["files"]:
            target = file_entry.get("target_file", "unknown")
            for result in file_entry.get("results", []):
                if "session_id" in result:
                    sessions.append({
                        "session_id": result["session_id"],
                        "specialist_id": result.get("id", ""),
                        "specialist_name": result.get("name", ""),
                        "category": result.get("category", ""),
                        "archetype": result.get("archetype", ""),
                        "target_file": target,
                        "url": result.get("url", ""),
                    })
    elif "results" in data:
        target = data.get("target_file", "unknown")
        for result in data.get("results", []):
            if "session_id" in result:
                sessions.append({
                    "session_id": result["session_id"],
                    "specialist_id": result.get("id", ""),
                    "specialist_name": result.get("name", ""),
                    "category": result.get("category", ""),
                    "target_file": target,
                    "url": result.get("url", ""),
                })

    return sessions


# PURPOSE: diff の品質をスコアリング
def score_quality(changed_files: list[str], patch_text: str) -> tuple[int, list[str]]:
    """品質スコアを計算し、理由を返す

    スコア基準:
        +3: ソースコード (.py, .ts, .yml) を修正
        +2: バグ修正キーワード (fix, bug, missing, error)
        +2: セキュリティ関連 (security, vulnerability, injection)
        +1: 2ファイル以上の変更 (波及あり)
        +1: テスト関連の変更
        -2: reviews/*.md のみの変更 (レビュー出力のみ)
        -1: コメント/空白のみの変更

    Returns:
        (score, reasons)
    """
    score = 0
    reasons = []

    # ボイラープレート除外: Jules が定型的に変更するファイル
    boilerplate_patterns = (
        'reviews/',          # レビュー出力
        '_review.md',        # レビュー出力
        '.github/workflows', # CI 設定 (Jules が依存関係を追加する定型修正)
    )
    meaningful_files = [f for f in changed_files
                        if not any(bp in f for bp in boilerplate_patterns)]
    boilerplate_files = [f for f in changed_files if f not in meaningful_files]

    # 実ソースコード変更?
    source_exts = ('.py', '.ts', '.js', '.yml', '.yaml', '.toml', '.cfg')
    has_meaningful_source = any(f.endswith(source_exts) for f in meaningful_files)

    if not meaningful_files:
        # ボイラープレートのみ = 実質的な発見なし
        score -= 2
        reasons.append(f'boilerplate only ({len(boilerplate_files)} files)')
    elif has_meaningful_source:
        score += 4
        reasons.append(f'meaningful source change: {", ".join(meaningful_files[:3])}')

    # キーワード検出 (実コード部分のみ)
    # ボイラープレート部分の diff を除外
    patch_lower = patch_text.lower()
    bug_keywords = ['fix', 'bug', 'missing', 'error', 'broken', 'incorrect', 'wrong']
    security_keywords = ['security', 'vulnerability', 'injection', 'xss', 'csrf', 'auth']

    for kw in bug_keywords:
        if kw in patch_lower:
            score += 2
            reasons.append(f'bug keyword: {kw}')
            break

    for kw in security_keywords:
        if kw in patch_lower:
            score += 2
            reasons.append(f'security keyword: {kw}')
            break

    # 波及範囲 (ボイラープレート除外)
    if len(meaningful_files) >= 2:
        score += 1
        reasons.append(f'{len(meaningful_files)} meaningful files affected')

    # テスト関連
    if any('test' in f.lower() for f in meaningful_files):
        score += 1
        reasons.append('test-related')

    # コメント/空白のみ?
    meaningful_lines = [l for l in patch_text.split('\n')
                        if l.startswith('+') or l.startswith('-')]
    content_lines = [l for l in meaningful_lines
                     if l.strip() not in ('+', '-', '+ ', '- ')
                     and not l.strip().startswith(('+#', '-#', '+ #', '- #'))]
    if meaningful_lines and not content_lines:
        score -= 1
        reasons.append('comments/whitespace only')

    return score, reasons


# PURPOSE: セッション結果から Issue 本文を生成
def format_issue(session_info: dict, session_data: dict) -> dict | None:
    """セッション結果を GitHub Issue の title/body に変換

    Jules API レスポンス構造:
        state: "COMPLETED" | "FAILED" | ...
        outputs[].changeSet.gitPatch.unidiffPatch: diff テキスト
        url: セッション URL

    Returns:
        {"title": ..., "body": ..., "labels": [...]} or None (Issue 不要)
    """
    state = session_data.get("state", "UNKNOWN")

    # 完了していないセッションはスキップ
    if state != "COMPLETED":
        return None

    # diff を抽出
    outputs = session_data.get("outputs", [])
    patches = []
    changed_files = []
    for output in outputs:
        change_set = output.get("changeSet", {})
        git_patch = change_set.get("gitPatch", {})
        patch = git_patch.get("unidiffPatch", "")
        if patch:
            patches.append(patch)
            # diff からファイル名を抽出
            for line in patch.split("\n"):
                if line.startswith("diff --git"):
                    parts = line.split(" b/")
                    if len(parts) >= 2:
                        changed_files.append(parts[-1])

    # diff がないセッションはスキップ (= 変更なし = 指摘なし)
    if not patches:
        return None

    specialist = session_info.get("specialist_name", "Unknown")
    specialist_id = session_info.get("specialist_id", "")
    target = session_info.get("target_file", "unknown")
    category = session_info.get("category", "specialist-review")
    session_url = session_info.get("url", "")

    title = f"[Jules/{specialist_id}] {specialist}: {target}"

    body_lines = [
        "## 🔍 Specialist Review Result",
        "",
        "| Item | Value |",
        "|:-----|:------|",
        f"| **Specialist** | {specialist} (`{specialist_id}`) |",
        f"| **Category** | `{category}` |",
        f"| **Target** | `{target}` |",
        f"| **Session** | [{session_info.get('session_id', '')}]({session_url}) |",
        f"| **Changed files** | {len(changed_files)} |",
        "",
    ]

    # 変更ファイル一覧
    if changed_files:
        body_lines.extend(["## Changed Files", ""])
        for cf in changed_files[:15]:
            body_lines.append(f"- `{cf}`")
        if len(changed_files) > 15:
            body_lines.append(f"- ... and {len(changed_files) - 15} more")
        body_lines.append("")

    # 品質スコア
    full_patch = "\n".join(patches)
    quality_score, quality_reasons = score_quality(changed_files, full_patch)

    # 品質スコアを表示
    body_lines.extend([
        "## Quality",
        "",
        f"Score: **{quality_score}** (threshold: {MIN_QUALITY_SCORE})",
        f"Reasons: {', '.join(quality_reasons)}",
        "",
    ])

    # diff (最大2000文字まで)
    if len(full_patch) > 2000:
        full_patch = full_patch[:2000] + "\n... (truncated)"
    body_lines.extend([
        "## Diff",
        "",
        "```diff",
        full_patch,
        "```",
        "",
        "---",
        f"*Auto-generated by Jules Specialist Reviews at {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
    ])

    labels = ["jules-review", category]
    if changed_files:
        labels.append("has-changes")

    return {
        "title": title,
        "body": "\n".join(body_lines),
        "labels": labels,
        "quality_score": quality_score,
        "quality_reasons": quality_reasons,
    }


# PURPOSE: gh CLI で Issue を作成
def create_github_issue(title: str, body: str, labels: list[str], repo: str, dry_run: bool = False) -> str | None:
    """gh CLI で GitHub Issue を作成"""
    if dry_run:
        print(f"\n{'='*60}")
        print(f"[DRY RUN] Issue: {title}")
        print(f"Labels: {', '.join(labels)}")
        print(f"{'='*60}")
        print(body)
        print(f"{'='*60}\n")
        return None

    cmd = [
        "gh", "issue", "create",
        "--repo", repo,
        "--title", title,
        "--body", body,
    ]
    for label in labels:
        cmd.extend(["--label", label])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            url = result.stdout.strip()
            print(f"  ✓ Issue created: {url}")
            return url
        else:
            print(f"  ✗ Failed: {result.stderr.strip()}")
            return None
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"  ✗ Error: {e}")
        return None


# PURPOSE: メインエントリポイント
async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Jules → GitHub Issue Creator v1.0")
    parser.add_argument("--results", "-r", nargs="+", help="Result JSON file(s)")
    parser.add_argument("--dir", "-d", default="", help="Results directory")
    parser.add_argument("--days", type=int, default=1, help="Days back to scan")
    parser.add_argument("--repo", default=REPO, help=f"GitHub repo (default: {REPO})")
    parser.add_argument("--min-score", type=int, default=MIN_QUALITY_SCORE, help="Minimum quality score for Issue creation")
    parser.add_argument("--dry-run", action="store_true", help="Print issues without creating")
    parser.add_argument("--status-only", action="store_true", help="Only check session statuses")
    parser.add_argument("--show-all", action="store_true", help="Show all issues including low-quality ones")

    args = parser.parse_args()

    # 結果ファイル収集
    result_files = []
    if args.results:
        result_files = [Path(f) for f in args.results if Path(f).exists()]
    elif args.dir:
        from collect_results import find_result_files
        result_files = find_result_files(base_dir=args.dir, days_back=args.days)
    else:
        # デフォルト: logs/specialist_daily
        from collect_results import find_result_files
        result_files = find_result_files(days_back=args.days)

    if not result_files:
        print("No result files found.")
        return

    print(f"📁 Result files: {len(result_files)}")

    # セッション情報抽出
    all_sessions = []
    for rf in result_files:
        sessions = extract_sessions(rf)
        all_sessions.extend(sessions)

    if not all_sessions:
        print("No sessions found in result files.")
        return

    print(f"📋 Sessions found: {len(all_sessions)}")

    # API キー取得
    api_key = get_api_key()

    # セッション状態確認
    session_ids = [s["session_id"] for s in all_sessions]
    print(f"🔍 Checking {len(session_ids)} session(s)...")

    session_results = await fetch_sessions(session_ids, api_key)

    # 状態集計
    states = {}
    for sr in session_results:
        state = sr.get("state", sr.get("error", "UNKNOWN"))
        states[state] = states.get(state, 0) + 1

    print(f"\n📊 Session states:")
    for state, count in sorted(states.items(), key=lambda x: -x[1]):
        print(f"  {state}: {count}")

    if args.status_only:
        return

    # Issue 作成 (品質フィルタ)
    issues_created = 0
    issues_skipped = 0
    for session_info, session_data in zip(all_sessions, session_results):
        issue = format_issue(session_info, session_data)
        if not issue:
            continue

        score = issue["quality_score"]
        reasons = issue["quality_reasons"]

        if score < args.min_score:
            issues_skipped += 1
            if args.show_all:
                print(f"  ⏭ Skip (score={score}): {issue['title']}")
                print(f"    Reasons: {', '.join(reasons)}")
            continue

        url = create_github_issue(
            title=issue["title"],
            body=issue["body"],
            labels=issue["labels"],
            repo=args.repo,
            dry_run=args.dry_run,
        )
        if url or args.dry_run:
            issues_created += 1

    print(f"\n{'='*40}")
    print(f"Issues {'previewed' if args.dry_run else 'created'}: {issues_created}")
    print(f"Issues skipped (score < {args.min_score}): {issues_skipped}")
    print(f"{'='*40}")


if __name__ == "__main__":
    asyncio.run(main())
