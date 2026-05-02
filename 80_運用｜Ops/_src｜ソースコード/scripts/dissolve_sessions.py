#!/usr/bin/env python3
"""dissolve_sessions.py — エクスポート済みセッションログを Hyphē (Phantasia) に溶解する

PURPOSE: conv/ に蓄積された IDE セッション Markdown を
  PhantasiaPipeline.dissolve() 経由で GnosisIndex (FAISS) に投入する。
  NucleatorChunker で意味的チャンキング → Gemini Embedding 2 で embedding 生成 → 場に溶解。

使い方:
  python dissolve_sessions.py --dry-run               # 件数・サイズ確認のみ
  python dissolve_sessions.py --max 5                  # 最初の5件だけ溶解
  python dissolve_sessions.py                          # 全件溶解
  python dissolve_sessions.py --since 2026-03-05       # 日付フィルタ
  python dissolve_sessions.py --source-dir ./my_conv/  # 入力ディレクトリ指定
  python dissolve_sessions.py --stats                  # GnosisIndex の現在の統計表示

依存: mekhane.anamnesis.phantasia_pipeline, mekhane.anamnesis.phantasia_field
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path

# ── sys.path 解決 ──────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _find_src_dir() -> str:
    """mekhane パッケージの _src ディレクトリを検出する。"""
    # HGK_ROOT 環境変数
    hgk_root = os.environ.get("HGK_ROOT", "")
    if hgk_root:
        candidate = os.path.join(hgk_root, "20_機構｜Mekhane", "_src｜ソースコード")
        if os.path.isdir(candidate):
            return candidate

    # スクリプトからの相対パス (80_運用｜Ops/_src｜ソースコード/scripts/ にいる前提)
    hgk_root_guess = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
    for dirname in os.listdir(hgk_root_guess):
        if dirname.startswith("20_") and "Mekhane" in dirname:
            for subdir in os.listdir(os.path.join(hgk_root_guess, dirname)):
                if subdir.startswith("_src"):
                    candidate = os.path.join(hgk_root_guess, dirname, subdir)
                    if os.path.isdir(os.path.join(candidate, "mekhane")):
                        return candidate

    # フォールバック
    return os.path.normpath(
        os.path.join(SCRIPT_DIR, "..", "..", "20_機構｜Mekhane", "_src｜ソースコード")
    )


SRC_DIR = _find_src_dir()
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


# ── ユーティリティ ──────────────────────────────────────────────────

def _default_conv_dir() -> str:
    """デフォルトの conv/ ディレクトリを返す。"""
    hgk_root = os.environ.get("HGK_ROOT", "")
    if hgk_root:
        return os.path.join(
            hgk_root, "30_記憶｜Mneme", "01_記録｜Records",
            "b_対話｜sessions", "conv",
        )
    # スクリプトからの相対パス
    return os.path.normpath(
        os.path.join(
            SCRIPT_DIR, "..", "..", "..",
            "30_記憶｜Mneme", "01_記録｜Records",
            "b_対話｜sessions", "conv",
        )
    )


def _extract_session_id(filepath: str) -> str:
    """ファイル名からセッション ID を生成する。

    conv/ のファイルには cascade_id が入っていないため、
    ファイル名ベースの安定的な ID を生成する。
    """
    basename = os.path.basename(filepath)
    # 拡張子を除去し、日本語・特殊文字を含むファイル名をそのまま使う
    name = os.path.splitext(basename)[0]
    return f"conv:{name}"


def _extract_date_from_filename(filepath: str) -> str:
    """ファイル名から日付 (YYYY-MM-DD) を抽出する。"""
    basename = os.path.basename(filepath)
    match = re.match(r"(\d{4}-\d{2}-\d{2})", basename)
    return match.group(1) if match else ""


def _format_size(size_bytes: int) -> str:
    """バイト数を人間可読形式に変換。"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _print_progress(current: int, total: int, session_id: str) -> None:
    """進捗表示。"""
    pct = current * 100 // total if total > 0 else 0
    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
    short_id = session_id[:40] if len(session_id) > 40 else session_id
    print(f"\r  [{bar}] {current}/{total} ({pct}%) {short_id}", end="", flush=True)


# ── メインコマンド ──────────────────────────────────────────────────

def cmd_stats() -> int:
    """GnosisIndex の現在の統計を表示する。"""
    from mekhane.anamnesis.phantasia_field import PhantasiaField

    field = PhantasiaField(chunker_mode="nucleator")
    stats = field.stats()
    health = field.health()

    print("\n📊 Phantasia Field 統計:")
    print(f"   状態: {health.get('status', '?')}")
    print(f"   チャンク総数: {stats.get('total', 0):,}")
    print(f"   チャンカー: {health.get('chunker_mode', '?')}")

    sources = health.get("sources", {})
    if sources:
        print(f"   ソース別:")
        for src, count in sorted(sources.items()):
            print(f"     - {src}: {count:,}")

    return 0


def cmd_dissolve(args) -> int:
    """セッションログを溶解する。"""
    from mekhane.anamnesis.phantasia_field import PhantasiaField
    from mekhane.anamnesis.phantasia_pipeline import PhantasiaPipeline

    source_dir = args.source_dir or _default_conv_dir()

    if not os.path.isdir(source_dir):
        print(f"❌ ディレクトリが見つかりません: {source_dir}", file=sys.stderr)
        return 1

    # ファイル一覧を取得
    md_files = sorted([
        os.path.join(source_dir, f)
        for f in os.listdir(source_dir)
        if f.endswith(".md")
    ])

    if not md_files:
        print(f"⚠️ Markdown ファイルが見つかりません: {source_dir}")
        return 0

    # 日付フィルタ
    if args.since:
        md_files = [
            f for f in md_files
            if _extract_date_from_filename(f) >= args.since
        ]

    # 件数制限
    if args.max and args.max > 0:
        md_files = md_files[:args.max]

    # 統計を計算
    total_size = sum(os.path.getsize(f) for f in md_files)

    print(f"\n🧪 Hyphē 溶解パイプライン")
    print(f"   入力: {source_dir}")
    print(f"   対象: {len(md_files)} ファイル ({_format_size(total_size)})")
    print(f"   embedding: gemini-embedding-2-preview (3072d)")
    print(f"   chunker: nucleator (G∘F 収束)")
    if args.since:
        print(f"   日付フィルタ: {args.since} 以降")
    if args.max:
        print(f"   件数制限: 最大 {args.max} 件")
    print()

    # dry-run モード
    if args.dry_run:
        print("  📋 dry-run モード — 溶解は実行しません\n")
        print(f"  {'#':>4}  {'日付':10}  {'サイズ':>10}  ファイル名")
        print(f"  {'─'*4}  {'─'*10}  {'─'*10}  {'─'*40}")
        for i, f in enumerate(md_files[:30], 1):
            date = _extract_date_from_filename(f)
            size = _format_size(os.path.getsize(f))
            name = os.path.basename(f)[:60]
            print(f"  {i:>4}  {date:10}  {size:>10}  {name}")
        if len(md_files) > 30:
            print(f"  ... 他 {len(md_files) - 30} ファイル")
        print(f"\n  合計: {len(md_files)} ファイル ({_format_size(total_size)})")
        print(f"\n  💡 溶解するには --dry-run を外してください")
        return 0

    # PhantasiaPipeline 初期化
    print("  ⚙️ PhantasiaField を初期化中...")
    field = PhantasiaField(chunker_mode="nucleator")
    pipeline = PhantasiaPipeline(field=field)

    # 溶解実行
    print("  🔥 溶解開始...\n")
    start_time = time.time()
    dissolved = []
    skipped = []
    errors = []
    total_chunks = 0

    for i, filepath in enumerate(md_files, 1):
        session_id = _extract_session_id(filepath)
        _print_progress(i, len(md_files), session_id)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()

            if not text.strip():
                skipped.append(os.path.basename(filepath))
                continue

            result = pipeline.dissolve(
                text=text,
                session_id=session_id,
                source="session",
                title=os.path.basename(filepath),
                trigger="batch",
            )

            if result.success:
                dissolved.append({
                    "file": os.path.basename(filepath),
                    "chunks": result.chunks_count,
                    "elapsed_ms": result.elapsed_ms,
                })
                total_chunks += result.chunks_count
            elif result.chunks_count == 0 and not result.error:
                # 重複排除: 全チャンクが既に溶解済み
                skipped.append(os.path.basename(filepath))
            else:
                errors.append(f"{os.path.basename(filepath)}: {result.error}")

        except Exception as e:
            errors.append(f"{os.path.basename(filepath)}: {e}")

    elapsed = time.time() - start_time
    print()  # 進捗バーの改行

    # 結果レポート
    print(f"\n✅ 溶解完了 ({elapsed:.1f}秒)")
    print(f"   溶解: {len(dissolved)}/{len(md_files)} ファイル")
    print(f"   スキップ (重複): {len(skipped)} ファイル")
    print(f"   チャンク総数: {total_chunks:,}")
    print(f"   平均チャンク/ファイル: {total_chunks / len(dissolved):.1f}" if dissolved else "")
    print(f"   スループット: {total_size / elapsed / 1024:.1f} KB/s" if elapsed > 0 else "")

    if errors:
        print(f"\n   ⚠️ エラー: {len(errors)} 件")
        for err in errors[:10]:
            print(f"      - {err}")

    # 溶解後の場の統計
    try:
        health = field.health()
        print(f"\n📊 場の状態:")
        print(f"   状態: {health.get('status', '?')}")
        print(f"   チャンク総数: {health.get('total_chunks', 0):,}")
    except Exception:
        pass

    return 0


# ── エントリポイント ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="エクスポート済みセッションログを Hyphē (Phantasia) に溶解する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python dissolve_sessions.py --dry-run               # 事前確認
  python dissolve_sessions.py --max 5                  # 少量テスト
  python dissolve_sessions.py                          # 全件溶解
  python dissolve_sessions.py --since 2026-03-05       # 日付フィルタ
  python dissolve_sessions.py --stats                  # 場の統計表示
""",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="溶解せず件数・サイズのみ表示",
    )
    parser.add_argument(
        "--max", type=int, default=0,
        help="最大溶解数 (0=全件)",
    )
    parser.add_argument(
        "--since",
        help="この日付以降のファイルのみ (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--source-dir",
        help="入力ディレクトリ (デフォルト: conv/)",
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="GnosisIndex の統計を表示して終了",
    )

    args = parser.parse_args()

    if args.stats:
        return cmd_stats()
    else:
        return cmd_dissolve(args)


if __name__ == "__main__":
    sys.exit(main())
