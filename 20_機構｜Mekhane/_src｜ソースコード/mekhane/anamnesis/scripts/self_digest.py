from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/ユーティリティ] <- mekhane/anamnesis/scripts/self_digest.py
# PURPOSE: Phantazein 自己消化スクリプト — セッション記録を場に溶解する自己消化ループ
"""
Phantazein Self-Digestion — 自己消化パイプライン

phantazein.db の IDE セッション記録 (artifacts テーブル) を
PhantasiaPipeline.dissolve() で場に投入し、
自分自身の知識を蓄積する自己消化ループを構築する。

理論的背景:
  F: Session → Field (左随伴 = 溶解)
  G: Field → Crystal (右随伴 = 結晶化)
  Self-Digestion = F(Phantazein) → 自分自身のセッションを場の素材にする

Usage:
  # dry-run (DB に書き込まない、統計のみ出力)
  python3 -m mekhane.anamnesis.scripts.self_digest --dry-run

  # 実行 (場に溶解)
  python3 -m mekhane.anamnesis.scripts.self_digest

  # 特定セッション
  python3 -m mekhane.anamnesis.scripts.self_digest --session-id abc123

  # 検証クエリ付き
  python3 -m mekhane.anamnesis.scripts.self_digest --verify "FEP と能動推論"
"""


import argparse
import json
import logging
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

log = logging.getLogger("hegemonikon.self_digest")

# ── HGK ディレクトリ定数 ──────────────────────────────────────────────

_HGK_ROOT = Path(__file__).resolve().parents[5]  # scripts → anamnesis → mekhane → _src → 20_Mekhane → HGK root
_DEFAULT_DB_PATH = _HGK_ROOT / "30_記憶｜Mneme" / "05_状態｜State" / "phantazein.db"
_DEFAULT_DB_DIR = _HGK_ROOT / "30_記憶｜Mneme" / "04_知識｜Gnosis" / "lance_db"


# ── データモデル ──────────────────────────────────────────────────────

@dataclass
class SessionRecord:
    """消化対象のセッションレコード。"""
    session_id: str
    title: str
    dir_path: str
    artifact_count: int
    total_text_size: int  # バイト
    artifacts: list[dict]  # {filename, summary, size_bytes, artifact_type}


@dataclass
class DigestStats:
    """自己消化の統計。"""
    sessions_scanned: int = 0
    sessions_digested: int = 0
    sessions_skipped: int = 0
    total_artifacts: int = 0
    total_text_chars: int = 0
    total_chunks_dissolved: int = 0
    elapsed_seconds: float = 0.0
    errors: list[str] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    def summary_lines(self) -> list[str]:
        """統計サマリーを行リストで返す。"""
        lines = [
            "═══ Phantazein Self-Digestion 結果 ═══",
            f"  セッション数     : {self.sessions_scanned} (消化: {self.sessions_digested}, スキップ: {self.sessions_skipped})",
            f"  アーティファクト数: {self.total_artifacts}",
            f"  テキスト総量     : {self.total_text_chars:,} chars",
            f"  溶解チャンク数   : {self.total_chunks_dissolved}",
            f"  所要時間         : {self.elapsed_seconds:.1f}s",
        ]
        if self.errors:
            lines.append(f"  エラー数         : {len(self.errors)}")
            for e in self.errors[:5]:
                lines.append(f"    ⚠ {e}")
        return lines


# ── セッション読み出し ────────────────────────────────────────────────

def load_sessions(
    db_path: Path,
    session_id: Optional[str] = None,
    min_artifact_count: int = 1,
) -> list[SessionRecord]:
    """phantazein.db から IDE セッションと artifacts を読み出す。

    Args:
        db_path: phantazein.db のパス
        session_id: 特定セッション ID (None = 全セッション)
        min_artifact_count: 最小 artifact 数 (これ未満はスキップ)

    Returns:
        SessionRecord のリスト
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        # セッション一覧取得
        if session_id:
            session_rows = conn.execute(
                "SELECT * FROM ide_sessions WHERE id = ?",
                (session_id,),
            ).fetchall()
        else:
            session_rows = conn.execute(
                "SELECT * FROM ide_sessions WHERE artifact_count >= ? ORDER BY created_at DESC",
                (min_artifact_count,),
            ).fetchall()

        records = []
        for srow in session_rows:
            sid = srow["id"]
            # アーティファクトを取得
            art_rows = conn.execute(
                "SELECT filename, artifact_type, summary, size_bytes FROM artifacts WHERE session_id = ? ORDER BY filename",
                (sid,),
            ).fetchall()

            artifacts = [dict(a) for a in art_rows]
            total_size = sum(a.get("size_bytes", 0) for a in artifacts)

            records.append(SessionRecord(
                session_id=sid,
                title=srow["title"] or "",
                dir_path=srow["dir_path"] or "",
                artifact_count=len(artifacts),
                total_text_size=total_size,
                artifacts=artifacts,
            ))

        return records
    finally:
        conn.close()

    return records


# ── アーティファクトのテキスト読み出し ────────────────────────────────

def read_artifact_text(session: SessionRecord) -> str:
    """セッションの全アーティファクトからテキストを構築する。

    1. dir_path が存在する場合、実ファイルを読む
    2. 実ファイルがない場合、summary をフォールバックとして使う

    Returns:
        結合されたテキスト
    """
    parts: list[str] = []

    # セッションヘッダ
    header = f"# Session: {session.title or session.session_id}\n"
    header += f"Session ID: {session.session_id}\n\n"
    parts.append(header)

    dir_path = Path(session.dir_path) if session.dir_path else None

    for art in session.artifacts:
        filename = art.get("filename", "")
        summary = art.get("summary", "")
        artifact_type = art.get("artifact_type", "other")

        # 実ファイルを試みる
        file_text = None
        if dir_path and filename:
            filepath = dir_path / filename
            if filepath.exists() and filepath.is_file():
                try:
                    file_text = filepath.read_text(encoding="utf-8")
                except Exception as e:  # noqa: BLE001
                    log.warning(f"ファイル読み込み失敗: {filepath}: {e}")

        # テキスト構築
        section_header = f"## {filename} ({artifact_type})\n\n"
        if file_text:
            parts.append(section_header + file_text + "\n\n")
        elif summary:
            parts.append(section_header + summary + "\n\n")
        # テキストも summary もない場合はスキップ

    return "".join(parts)


# ── 自己消化実行 ──────────────────────────────────────────────────────

def run_self_digest(
    db_path: Path = _DEFAULT_DB_PATH,
    db_dir: Path = _DEFAULT_DB_DIR,
    session_id: Optional[str] = None,
    dry_run: bool = True,
    min_text_chars: int = 100,
    verify_query: Optional[str] = None,
) -> DigestStats:
    """自己消化パイプラインを実行する。

    Args:
        db_path: phantazein.db のパス
        db_dir: GnosisIndex ディレクトリ
        session_id: 特定セッション (None = 全セッション)
        dry_run: True の場合 DB に書き込まない (統計のみ)
        min_text_chars: 最小テキスト長 (これ未満はスキップ)
        verify_query: 検証クエリ (消化後に recrystallize を実行)

    Returns:
        DigestStats: 消化統計
    """
    stats = DigestStats()
    start_time = time.monotonic()

    # セッション読み出し
    log.info(f"📖 phantazein.db からセッション読み出し: {db_path}")
    sessions = load_sessions(db_path, session_id=session_id)
    stats.sessions_scanned = len(sessions)
    log.info(f"  → {len(sessions)} セッション発見")

    if not sessions:
        log.warning("消化対象のセッションなし")
        stats.elapsed_seconds = time.monotonic() - start_time
        return stats

    # PhantasiaPipeline 初期化 (dry-run でなければ)
    pipeline = None
    if not dry_run:
        try:
            from mekhane.anamnesis.phantasia_field import PhantasiaField
            from mekhane.anamnesis.phantasia_pipeline import PhantasiaPipeline

            field = PhantasiaField(
                db_path=str(db_dir),
                chunker_mode="markdown",
            )
            pipeline = PhantasiaPipeline(field)
            log.info(f"✅ PhantasiaPipeline 初期化完了 (db_dir={db_dir})")
        except Exception as e:  # noqa: BLE001
            log.error(f"❌ Pipeline 初期化失敗: {e}")
            stats.errors.append(f"Pipeline init: {e}")
            stats.elapsed_seconds = time.monotonic() - start_time
            return stats

    # セッション毎に溶解
    for i, session in enumerate(sessions, 1):
        log.info(f"[{i}/{len(sessions)}] Session: {session.title or session.session_id} ({session.artifact_count} artifacts)")

        # テキスト読み出し
        text = read_artifact_text(session)
        text_chars = len(text)
        stats.total_artifacts += session.artifact_count
        stats.total_text_chars += text_chars

        if text_chars < min_text_chars:
            log.info(f"  → スキップ (テキスト {text_chars} chars < {min_text_chars})")
            stats.sessions_skipped += 1
            continue

        if dry_run:
            log.info(f"  → [DRY-RUN] {text_chars:,} chars, {session.artifact_count} artifacts")
            stats.sessions_digested += 1
            continue

        # 溶解実行
        try:
            result = pipeline.dissolve(
                text=text,
                session_id=session.session_id,
                source="session",
                title=session.title or f"Session {session.session_id}",
                trigger="self_digest",
            )
            if result.success:
                stats.total_chunks_dissolved += result.chunks_count
                stats.sessions_digested += 1
                log.info(f"  → ✅ {result.chunks_count} chunks ({result.elapsed_ms:.0f}ms)")
            else:
                stats.sessions_skipped += 1
                stats.errors.append(f"Session {session.session_id}: {result.error}")
                log.warning(f"  → ⚠ 溶解失敗: {result.error}")
        except Exception as e:  # noqa: BLE001
            stats.sessions_skipped += 1
            stats.errors.append(f"Session {session.session_id}: {e}")
            log.error(f"  → ❌ 例外: {e}")

    stats.elapsed_seconds = time.monotonic() - start_time

    # 検証クエリ
    if verify_query and pipeline and not dry_run:
        log.info(f"\n🔍 検証クエリ: '{verify_query}'")
        try:
            rcr_result = pipeline.recrystallize(verify_query)
            log.info(f"  → {len(rcr_result.crystals)} crystals found ({rcr_result.elapsed_ms:.0f}ms)")
            for j, crystal in enumerate(rcr_result.crystals[:5], 1):
                log.info(f"  [{j}] score={crystal.score:.3f} | {crystal.title or crystal.source} | {crystal.content[:80]}...")
        except Exception as e:  # noqa: BLE001
            log.error(f"  → ❌ 検証クエリ失敗: {e}")
            stats.errors.append(f"Verify: {e}")

    return stats


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    """CLI エントリポイント。"""
    parser = argparse.ArgumentParser(
        description="Phantazein Self-Digestion — セッション記録を場に溶解",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  # dry-run (統計のみ)
  python3 -m mekhane.anamnesis.scripts.self_digest --dry-run

  # 実行
  python3 -m mekhane.anamnesis.scripts.self_digest --execute

  # 特定セッション + 検証クエリ
  python3 -m mekhane.anamnesis.scripts.self_digest --execute --session-id abc123 --verify "FEP"
        """,
    )
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="統計のみ出力、DB に書き込まない (デフォルト)")
    parser.add_argument("--execute", action="store_true",
                        help="実際に場に溶解する")
    parser.add_argument("--session-id", type=str, default=None,
                        help="特定のセッション ID のみ消化")
    parser.add_argument("--db-path", type=str, default=None,
                        help="phantazein.db のパス")
    parser.add_argument("--db-dir", "--lance-dir", type=str, default=None,
                        dest="db_dir",
                        help="GnosisIndex ディレクトリ")
    parser.add_argument("--min-chars", type=int, default=100,
                        help="最小テキスト長 (デフォルト: 100)")
    parser.add_argument("--verify", type=str, default=None,
                        help="消化後の検証クエリ")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="詳細ログ出力")

    args = parser.parse_args()

    # ログ設定
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
    )

    # dry-run vs execute
    dry_run = not args.execute

    # パス解決
    db_path = Path(args.db_path) if args.db_path else _DEFAULT_DB_PATH
    db_dir = Path(args.db_dir) if args.db_dir else _DEFAULT_DB_DIR

    # DB 存在チェック
    if not db_path.exists():
        log.error(f"❌ phantazein.db が見つかりません: {db_path}")
        sys.exit(1)

    mode_label = "🔴 EXECUTE" if not dry_run else "🟡 DRY-RUN"
    log.info(f"═══ Phantazein Self-Digestion [{mode_label}] ═══")
    log.info(f"  DB     : {db_path}")
    log.info(f"  DB dir : {db_dir}")
    log.info(f"  Session: {args.session_id or 'ALL'}")
    log.info("")

    # 実行
    stats = run_self_digest(
        db_path=db_path,
        db_dir=db_dir,
        session_id=args.session_id,
        dry_run=dry_run,
        min_text_chars=args.min_chars,
        verify_query=args.verify,
    )

    # 統計出力
    log.info("")
    for line in stats.summary_lines():
        log.info(line)

    # 終了コード
    if stats.errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
