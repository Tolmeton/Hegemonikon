#!/usr/bin/env python3
"""export_sessions.py — IDE セッション一括エクスポートツール

PURPOSE: IDE を閉じるとセッションログが消失する問題への対策。
Language Server API 経由で全セッションの会話ログを Markdown/JSON でエクスポートする。

使い方:
  python export_sessions.py                    # 全セッションを Markdown でエクスポート
  python export_sessions.py --format json      # JSON でエクスポート
  python export_sessions.py --list             # セッション一覧のみ表示
  python export_sessions.py --since 2026-03-13 # 日付フィルタ
  python export_sessions.py --max 10           # 最大件数指定
  python export_sessions.py --output ./exports # 出力先指定
  python export_sessions.py --unlimited        # 文字数制限なし (全文取得)

依存: mekhane.ochema.antigravity_client (AntigravityClient)
"""

import argparse
import os
import sys
import time

# mekhane パッケージへのパス解決
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def _find_src_dir() -> str:
    """mekhane パッケージの _src ディレクトリを検出する。"""
    # 方法1: HGK_ROOT 環境変数
    hgk_root = os.environ.get("HGK_ROOT", "")
    if hgk_root:
        candidate = os.path.join(hgk_root, "20_機構｜Mekhane", "_src｜ソースコード")
        if os.path.isdir(candidate):
            return candidate

    # 方法2: スクリプトからの相対パス (80_運用｜Ops/_src｜ソースコード/scripts/ にいる前提)
    # → 3階層上が HGK_ROOT
    hgk_root_guess = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
    for dirname in os.listdir(hgk_root_guess):
        if dirname.startswith("20_") and "Mekhane" in dirname:
            for subdir in os.listdir(os.path.join(hgk_root_guess, dirname)):
                if subdir.startswith("_src"):
                    candidate = os.path.join(hgk_root_guess, dirname, subdir)
                    if os.path.isdir(os.path.join(candidate, "mekhane")):
                        return candidate

    # 方法3: フォールバック — 直接パス
    fallback = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "20_機構｜Mekhane", "_src｜ソースコード"))
    return fallback

SRC_DIR = _find_src_dir()
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


def print_progress(current: int, total: int, cascade_id: str) -> None:
    """進捗表示コールバック。"""
    pct = current * 100 // total if total > 0 else 0
    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
    print(f"\r  [{bar}] {current}/{total} ({pct}%) {cascade_id[:12]}...", end="", flush=True)


def cmd_list(client, args):
    """セッション一覧を表示する。"""
    sessions = client.session_info(limit=0)  # 全件取得
    if "error" in sessions:
        print(f"❌ エラー: {sessions['error']}", file=sys.stderr)
        return 1

    all_sessions = sessions.get("sessions", [])
    print(f"\n📋 全 {sessions.get('total', 0)} セッション\n")
    print(f"{'#':>3}  {'Modified':16}  {'Steps':>5}  {'ID':14}  Summary")
    print(f"{'─'*3}  {'─'*16}  {'─'*5}  {'─'*14}  {'─'*40}")

    for i, s in enumerate(all_sessions, 1):
        modified = s.get("modified", "")[:16]
        steps = s.get("step_count", 0)
        cid = s.get("cascade_id", "")[:14]
        summary = s.get("summary", "(none)")[:60]
        print(f"{i:>3}  {modified:16}  {steps:>5}  {cid:14}  {summary}")

    return 0


def cmd_export(client, args):
    """セッションをエクスポートする。"""
    import json as _json

    # デフォルト出力先
    output_dir = args.output
    if not output_dir:
        hgk_root = os.environ.get("HGK_ROOT", "")
        if hgk_root:
            output_dir = os.path.join(hgk_root, "30_記憶｜Mneme", "01_記録｜Records", "b_対話｜sessions", "conv")
        else:
            output_dir = os.path.expanduser("~/.gemini/antigravity/sessions")

    fmt = args.format or "markdown"
    max_sessions = args.max or 0
    since = args.since or None
    unlimited = args.unlimited

    print(f"\n🚀 セッションエクスポート開始")
    print(f"   出力先: {output_dir}")
    print(f"   形式: {fmt}")
    print(f"   制限: {'全件' if max_sessions == 0 else f'最大 {max_sessions} 件'}")
    if since:
        print(f"   日付フィルタ: {since} 以降")
    if unlimited:
        print(f"   文字数制限: なし (全文取得)")
    print()

    os.makedirs(output_dir, exist_ok=True)
    start_time = time.time()

    # セッション一覧を取得
    sessions = client.session_info(limit=0)  # 全件取得
    if "error" in sessions:
        print(f"\n❌ エラー: {sessions['error']}", file=sys.stderr)
        return 1

    all_sessions = sessions.get("sessions", [])
    total_found = len(all_sessions)

    # フィルタ: since
    if since:
        all_sessions = [s for s in all_sessions if s.get("modified", "") >= since]

    # フィルタ: max_sessions
    if max_sessions > 0:
        all_sessions = all_sessions[:max_sessions]

    exported = []
    skipped = 0
    errors = []

    for i, s in enumerate(all_sessions, 1):
        cid = s["cascade_id"]
        modified = s.get("modified", "")[:10]
        summary_short = s.get("summary", "(none)")[:50].replace("/", "_").replace(" ", "_")
        # 安全なファイル名生成
        safe_summary = "".join(c for c in summary_short if c.isalnum() or c in "_-.").rstrip("_")

        if fmt == "json":
            filename = f"{modified}_conv_{i}_{safe_summary}.json"
        else:
            filename = f"{modified}_conv_{i}_{safe_summary}.md"
        filepath = os.path.join(output_dir, filename)

        # 既にエクスポート済みチェック (cascade_id ベース)
        if os.path.exists(filepath):
            skipped += 1
            print_progress(i, len(all_sessions), cid)
            continue

        # 会話を取得 (unlimited = full=True)
        try:
            conv = client.session_read(cid, max_turns=200, full=unlimited)
        except Exception as e:
            errors.append(f"{cid[:12]}: {e}")
            continue

        if fmt == "json":
            # JSON エクスポート
            export_data = {
                "cascade_id": cid,
                "modified": s.get("modified", ""),
                "summary": s.get("summary", ""),
                "step_count": s.get("step_count", 0),
                "total_steps": conv.get("total_steps", 0),
                "total_turns": conv.get("total_turns", 0),
                "conversation": conv.get("conversation", []),
            }
            with open(filepath, "w", encoding="utf-8") as f:
                _json.dump(export_data, f, ensure_ascii=False, indent=2)
        else:
            # Markdown エクスポート
            lines = [
                f"# Session: {s.get('summary', '(none)')}",
                f"",
                f"- **Cascade ID**: `{cid}`",
                f"- **Modified**: {s.get('modified', '')}",
                f"- **Steps**: {conv.get('total_steps', 0)}",
                f"- **Turns**: {conv.get('total_turns', 0)}",
                f"- **Summary**: {conv.get('summary', '(none)')}",
                f"",
                f"---",
                f"",
            ]

            for turn in conv.get("conversation", []):
                role = turn.get("role", "")
                if role == "user":
                    lines.append(f"## 👤 User\n")
                    lines.append(turn.get("content", ""))
                    if turn.get("truncated"):
                        lines.append("\n> ⚠️ (truncated)")
                    lines.append("")
                elif role == "assistant":
                    model = turn.get("model", "")
                    lines.append(f"## 🤖 Assistant ({model})\n")
                    lines.append(turn.get("content", ""))
                    if turn.get("truncated"):
                        lines.append("\n> ⚠️ (truncated)")
                    lines.append("")
                elif role == "tool":
                    tool = turn.get("tool", "")
                    lines.append(f"- 🔧 `{tool}` ({turn.get('status', '')})")

            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

        exported.append(filepath)
        print_progress(i, len(all_sessions), cid)

    elapsed = time.time() - start_time
    print()  # 進捗バーの改行

    print(f"\n✅ エクスポート完了 ({elapsed:.1f}秒)")
    print(f"   検出: {total_found} セッション")
    print(f"   エクスポート: {len(exported)} ファイル")
    print(f"   スキップ: {skipped} (既存 or フィルタ外)")

    if errors:
        print(f"   ⚠️ エラー: {len(errors)} 件")
        for err in errors[:5]:
            print(f"      - {err}")

    if exported:
        print(f"\n📁 出力先: {output_dir}")
        for path in exported[:5]:
            size = os.path.getsize(path) if os.path.exists(path) else 0
            basename = os.path.basename(path)
            print(f"   📄 {basename} ({size:,} bytes)")
        if len(exported) > 5:
            print(f"   ... 他 {len(exported) - 5} ファイル")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="IDE セッション一括エクスポートツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python export_sessions.py --list             # 一覧表示
  python export_sessions.py                    # 全件 Markdown エクスポート
  python export_sessions.py --format json      # JSON エクスポート
  python export_sessions.py --since 2026-03-13 # 日付フィルタ
  python export_sessions.py --unlimited        # 全文取得 (truncate なし)
""",
    )
    parser.add_argument("--list", action="store_true", help="セッション一覧のみ表示")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="出力形式 (default: markdown)")
    parser.add_argument("--output", "-o", help="出力先ディレクトリ")
    parser.add_argument("--max", type=int, default=0, help="最大エクスポート数 (0=全件)")
    parser.add_argument("--since", help="この日付以降のセッションのみ (YYYY-MM-DD)")
    parser.add_argument("--unlimited", action="store_true", help="会話テキストの文字数制限を解除")
    parser.add_argument("--workspace", help="ワークスペースパスを明示指定")

    args = parser.parse_args()

    # AntigravityClient の初期化
    try:
        from mekhane.ochema.antigravity_client import AntigravityClient
    except ImportError:
        print("❌ mekhane パッケージが見つかりません。", file=sys.stderr)
        print(f"   検索パス: {SRC_DIR}", file=sys.stderr)
        return 1

    workspace = args.workspace
    if not workspace:
        # HGK_ROOT からワークスペースを推定
        workspace = os.environ.get(
            "HGK_ROOT",
            os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "..")),
        )

    try:
        client = AntigravityClient(workspace=workspace)
        print(f"✅ Language Server に接続しました (workspace: {workspace})")
    except RuntimeError as e:
        print(f"❌ Language Server に接続できません: {e}", file=sys.stderr)
        print("   IDE が起動しているか確認してください。", file=sys.stderr)
        return 1

    if args.list:
        return cmd_list(client, args)
    else:
        return cmd_export(client, args)


if __name__ == "__main__":
    sys.exit(main())
