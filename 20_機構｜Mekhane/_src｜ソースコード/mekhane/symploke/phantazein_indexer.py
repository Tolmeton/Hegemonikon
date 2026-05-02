#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/phantazein_indexer.py
# PURPOSE: .gemini/brain/ と Mneme を走査し、セッション・アーティファクト・Handoff・ROM を DB に格納する
"""
Phantazein Indexer — ファイルシステム → DB 同期エンジン

走査対象:
  1. .gemini/antigravity/brain/{uuid}/ → ide_sessions + artifacts
  2. 30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff/ → handoffs
  3. 30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/ → roms

機能:
  - full_sync(): 全量走査 (初回 or リビルド)
  - incremental_sync(): 差分走査 (mtime ベース)
"""

import json
import logging
import os
import re
import yaml
import time
from pathlib import Path
from typing import Optional

from mekhane.symploke.phantazein_store import PhantazeinStore, get_store

logger = logging.getLogger("hegemonikon.phantazein.indexer")

# ── 定数 ────────────────────────────────────────────────────

# 標準アーティファクト (is_standard = True)
STANDARD_ARTIFACTS = {"task.md", "implementation_plan.md", "walkthrough.md"}

# アーティファクトタイプの推定 (ファイル名 → artifact_type)
ARTIFACT_TYPE_MAP = {
    "task.md": "task",
    "implementation_plan.md": "impl_plan",
    "walkthrough.md": "walkthrough",
}

# UUID v4 パターン (セッションディレクトリ名の検証)
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)

# Handoff ファイル名から日時を抽出するパターン
HANDOFF_DATE_PATTERN = re.compile(
    r"handoff_(\d{4}-\d{2}-\d{2})_(\d{4})"
)

# ROM ファイル名からトピックを抽出するパターン
ROM_TOPIC_PATTERN = re.compile(
    r"rom_\d{4}-\d{2}-\d{2}_(.+)\.md$"
)

# Handoff 内の session_id 抽出パターン (型 B: 末尾)
SESSION_FOOTER_PATTERN = re.compile(
    r"\*Session:\s*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\*"
)

# Handoff 内の session_id 抽出パターン (型 C: blockquote)
SESSION_BLOCKQUOTE_PATTERN = re.compile(
    r">\s*\*{0,2}Session\*{0,2}:\s*`?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})`?"
)


# ── パス解決 ─────────────────────────────────────────────────


# PURPOSE: IDE セッションのベースディレクトリを取得する
def _get_brain_dir() -> Path:
    """IDE セッションの格納ディレクトリを返す。"""
    brain = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain.exists():
        return brain
    # フォールバック: 環境変数
    env_path = os.getenv("HGK_BRAIN_DIR")
    if env_path:
        return Path(env_path)
    return brain


# PURPOSE: Handoff ディレクトリを取得する
def _get_handoff_dir() -> Path:
    """Handoff の格納ディレクトリを返す。"""
    from mekhane.paths import HANDOFF_DIR
    return HANDOFF_DIR


# PURPOSE: ROM ディレクトリを取得する
def _get_rom_dir() -> Path:
    """ROM の格納ディレクトリを返す。"""
    from mekhane.paths import ROM_DIR
    return ROM_DIR


# ── ヘルパー ─────────────────────────────────────────────────


# PURPOSE: セッションディレクトリの task.md 等から人間可読なタイトルを抽出する
def _extract_title(session_dir: Path) -> str:
    """task.md → implementation_plan.md → walkthrough.md の順で最初の # ヘッダーを返す。

    見つからなければ空文字列を返す。
    """
    # 優先順位つきのファイル名
    candidates = ["task.md", "implementation_plan.md", "walkthrough.md"]
    for filename in candidates:
        filepath = session_dir / filename
        if not filepath.exists():
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line.startswith("# "):
                        return line.lstrip("#").strip()
        except (UnicodeDecodeError, OSError):
            continue
    return ""


# ── スキャナ ─────────────────────────────────────────────────


# PURPOSE: セッションディレクトリからメタデータを読取り DB に格納する
def _scan_session(session_dir: Path, store: PhantazeinStore) -> int:
    """1つのセッションディレクトリを走査し、DB に格納する。

    Returns:
        アーティファクト数
    """
    session_id = session_dir.name
    if not UUID_PATTERN.match(session_id):
        return 0

    # アーティファクト一覧 (*.md のうち .metadata.json / .resolved を除外)
    artifact_files = [
        f for f in session_dir.iterdir()
        if f.is_file()
        and f.suffix == ".md"
        and not f.name.endswith(".metadata.json")
        and ".resolved" not in f.name
    ]

    # セッション作成日時の推定 (最古のファイルの mtime)
    file_mtimes = [f.stat().st_mtime for f in session_dir.iterdir() if f.is_file()]
    created_at = min(file_mtimes) if file_mtimes else session_dir.stat().st_mtime
    updated_at = max(file_mtimes) if file_mtimes else session_dir.stat().st_mtime

    # タイトル抽出: task.md の最初の # ヘッダーから取得
    title = _extract_title(session_dir)

    # セッション登録
    store.upsert_ide_session(
        session_id=session_id,
        title=title,
        created_at=created_at,
        updated_at=updated_at,
        dir_path=str(session_dir),
        artifact_count=len(artifact_files),
    )

    # 各アーティファクトを登録
    for art_file in artifact_files:
        filename = art_file.name
        is_standard = filename in STANDARD_ARTIFACTS
        artifact_type = ARTIFACT_TYPE_MAP.get(filename, "other")

        # メタデータファイルを読む (存在すれば)
        meta_path = session_dir / f"{filename}.metadata.json"
        summary = ""
        version = 1
        art_updated_at = art_file.stat().st_mtime
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                summary = meta.get("summary", "")
                version = int(meta.get("version", 1))
                # artifactType マッピング
                raw_type = meta.get("artifactType", "")
                if "IMPLEMENTATION_PLAN" in raw_type:
                    artifact_type = "impl_plan"
                elif "WALKTHROUGH" in raw_type:
                    artifact_type = "walkthrough"
                elif "TASK" in raw_type:
                    artifact_type = "task"
            except (json.JSONDecodeError, ValueError):
                pass

        store.upsert_artifact(
            session_id=session_id,
            filename=filename,
            artifact_type=artifact_type,
            summary=summary,
            size_bytes=art_file.stat().st_size,
            created_at=art_file.stat().st_mtime,
            updated_at=art_updated_at,
            version=version,
            is_standard=is_standard,
        )

    return len(artifact_files)


# PURPOSE: Handoff ファイルの内容からメタデータを抽出する
def _parse_handoff_content(text: str) -> dict:
    """Handoff ファイルの内容を解析し、構造化メタデータを返す。

    4 フォーマットに対応:
      A: v2 YAML code block (```yaml ... session_handoff: ...```)
      B: 末尾 *Session: {uuid}*
      C: Blockquote > **Session**: `{uuid}`
      D: session_id なし (フォールバック)

    Returns:
        {
            "session_id": str | None,
            "project": str | None,
            "workspace": str | None,
            "handoff_version": str | None,
            "title": str | None,
        }
    """
    result: dict = {
        "session_id": None,
        "project": None,
        "workspace": None,
        "handoff_version": None,
        "title": None,
    }

    # --- タイトル抽出 (先頭の # ヘッダー、コードブロック内はスキップ) ---
    in_code_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if stripped.startswith("#"):
            result["title"] = stripped.lstrip("#").strip()
            break

    # --- 型 A: YAML code block パース ---
    yaml_match = re.search(r"```ya?ml\s*\n(.*?)```", text, re.DOTALL)
    if yaml_match:
        yaml_text = yaml_match.group(1)
        try:
            parsed = yaml.safe_load(yaml_text)
            if isinstance(parsed, dict):
                # session_handoff ラッパーの有無
                sh = parsed.get("session_handoff", parsed)
                if isinstance(sh, dict):
                    result["session_id"] = sh.get("session_id")
                    result["project"] = sh.get("project")
                    result["workspace"] = sh.get("workspace")
                    result["handoff_version"] = str(sh.get("version", "")) or None
                    if result["session_id"]:
                        return result  # 型 A は最優先。他のパターンはスキップ
        except (yaml.YAMLError, AttributeError):
            pass

    # --- 型 B: 末尾 *Session: uuid* ---
    m = SESSION_FOOTER_PATTERN.search(text)
    if m:
        result["session_id"] = m.group(1)
        return result

    # --- 型 C: Blockquote > **Session**: uuid ---
    m = SESSION_BLOCKQUOTE_PATTERN.search(text)
    if m:
        result["session_id"] = m.group(1)
        return result

    # --- 型 D: session_id なし ---
    return result


# PURPOSE: Handoff ディレクトリを走査し DB に格納する
def _scan_handoffs(handoff_dir: Path, store: PhantazeinStore) -> int:
    """Handoff ファイルを走査し、メタデータをパースして DB に格納する。

    Returns:
        スキャンした Handoff 数
    """
    if not handoff_dir.exists():
        logger.warning("Handoff ディレクトリが見つからない: %s", handoff_dir)
        return 0

    count = 0
    for f in handoff_dir.iterdir():
        if not f.is_file() or not f.name.startswith("handoff_"):
            continue

        # ファイル全文を読み取り、メタデータを抽出
        text = ""
        try:
            with open(f, "r", encoding="utf-8") as fh:
                text = fh.read()
        except (UnicodeDecodeError, OSError):
            pass

        meta = _parse_handoff_content(text) if text else {}

        store.upsert_handoff(
            filename=f.name,
            filepath=str(f),
            created_at=f.stat().st_mtime,
            size_bytes=f.stat().st_size,
            title=meta.get("title", "") or "",
            session_id=meta.get("session_id"),
            project_name=meta.get("project"),
            handoff_version=meta.get("handoff_version"),
        )
        count += 1

    return count


# PURPOSE: ROM ディレクトリを走査し DB に格納する
def _scan_roms(rom_dir: Path, store: PhantazeinStore) -> int:
    """ROM ファイルを走査し、DB に格納する。

    Returns:
        スキャンした ROM 数
    """
    if not rom_dir.exists():
        logger.warning("ROM ディレクトリが見つからない: %s", rom_dir)
        return 0

    count = 0
    for f in rom_dir.iterdir():
        if not f.is_file() or not f.name.startswith("rom_"):
            continue

        # トピック抽出 (ファイル名から)
        topic = ""
        m = ROM_TOPIC_PATTERN.search(f.name)
        if m:
            topic = m.group(1).replace("_", " ")

        store.upsert_rom(
            filename=f.name,
            filepath=str(f),
            created_at=f.stat().st_mtime,
            size_bytes=f.stat().st_size,
            topic=topic,
        )
        count += 1

    return count

# ── セッション紐づけ (S2) ─────────────────────────────────────

# ファイル名日時パターン
_FNAME_DATE_PATTERNS = [
    # handoff_2026-03-12_2234.md / handoff_2026-03-12_215852_desc.md
    re.compile(r"(?:handoff|rom)[_-](\d{4})-(\d{2})-(\d{2})[_-](\d{2})(\d{2})(?:(\d{2}))?[_.]?"),
    # handoff_20260312_desc.md / rom_20260312_desc.md
    re.compile(r"(?:handoff|rom)[_-](\d{4})(\d{2})(\d{2})[_.]?"),
]


# PURPOSE: ファイル名から作成日時を epoch に変換する
def _parse_filename_datetime(filename: str) -> float | None:
    """Handoff/ROM のファイル名から日時をパースして epoch を返す。

    対応パターン:
      - handoff_2026-03-12_2234.md → 2026-03-12 22:34:00
      - handoff_2026-03-12_215852_syncthing-setup.md → 2026-03-12 21:58:52
      - handoff_20260312_session_restore.md → 2026-03-12 12:00:00
      - rom_2026-03-12_2234.md → 同上

    Returns:
        epoch float or None
    """
    from datetime import datetime, timezone, timedelta

    jst = timezone(timedelta(hours=9))

    for pat in _FNAME_DATE_PATTERNS:
        m = pat.search(filename)
        if not m:
            continue
        groups = m.groups()
        year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
        if len(groups) >= 5 and groups[3] is not None:
            hour, minute = int(groups[3]), int(groups[4])
            second = int(groups[5]) if len(groups) >= 6 and groups[5] is not None else 0
        else:
            # 日付のみ → 正午とする
            hour, minute, second = 12, 0, 0
        try:
            dt = datetime(year, month, day, hour, minute, second, tzinfo=jst)
            return dt.timestamp()
        except ValueError:
            continue
    return None


# PURPOSE: 未紐づけの Handoff/ROM を日時近接でセッションに紐づける
def _link_to_sessions(store: PhantazeinStore) -> tuple[int, int]:
    """session_id が NULL の Handoff/ROM を find_closest_session で紐づける。

    ファイル名から日時をパースし、取得できた場合はそれを優先。
    取得できない場合は mtime (created_at) にフォールバック。

    Returns:
        (linked_handoffs, linked_roms) のタプル
    """
    linked_h = 0
    linked_r = 0

    # Handoff の紐づけ
    unlinked_handoffs = store._conn.execute(
        "SELECT filename, created_at FROM handoffs WHERE session_id IS NULL"
    ).fetchall()
    for row in unlinked_handoffs:
        ts = _parse_filename_datetime(row["filename"]) or row["created_at"]
        session_id = store.find_closest_session(ts)
        if session_id:
            store.link_handoff_to_session(row["filename"], session_id)
            linked_h += 1

    # ROM の紐づけ
    unlinked_roms = store._conn.execute(
        "SELECT filename, created_at FROM roms WHERE session_id IS NULL"
    ).fetchall()
    for row in unlinked_roms:
        ts = _parse_filename_datetime(row["filename"]) or row["created_at"]
        session_id = store.find_closest_session(ts)
        if session_id:
            store.link_rom_to_session(row["filename"], session_id)
            linked_r += 1

    if linked_h or linked_r:
        logger.info("Linked %d handoffs, %d ROMs to sessions", linked_h, linked_r)
    return linked_h, linked_r


# ── η/ε 連鎖構築 ─────────────────────────────────────────────


# PURPOSE: Handoff から η/ε 連鎖を構築する
def _build_chains(store: PhantazeinStore) -> int:
    """session_id を持つ Handoff から η/ε 連鎖を構築する。

    ε (生成): Handoff 内から抽出した session_id がその Handoff を生んだ Session
    η (消費): 時系列で次に開始された Session がその Handoff を消費した Session

    Returns:
        構築した連鎖数
    """
    # session_id を持つ全 Handoff を時系列順で取得 (project_name も含む)
    handoffs_with_session = store._conn.execute(
        """
        SELECT id, filename, session_id, created_at, project_name
        FROM handoffs
        WHERE session_id IS NOT NULL
        ORDER BY created_at ASC
        """
    ).fetchall()

    if not handoffs_with_session:
        return 0

    # 全セッションを時系列順で取得 (η の候補特定用)
    all_sessions = store._conn.execute(
        "SELECT id, created_at FROM ide_sessions ORDER BY created_at ASC"
    ).fetchall()

    # セッション開始時刻のソート済みリスト
    session_starts = [(row["id"], row["created_at"]) for row in all_sessions]

    # セッション→プロジェクト名のマッピング (project_name フィルタ用)
    # Handoff の project_name から、同プロジェクトのセッション集合を構築
    session_project_map: dict[str, set[str]] = {}
    for hrow in handoffs_with_session:
        if hrow["project_name"] and hrow["session_id"]:
            session_project_map.setdefault(hrow["project_name"], set()).add(hrow["session_id"])

    chain_count = 0
    for hrow in handoffs_with_session:
        handoff_id = hrow["id"]
        source_session_id = hrow["session_id"]   # ε
        handoff_created = hrow["created_at"]
        project_name = hrow["project_name"]

        # η: Handoff 作成後に最初に開始されたセッションを探す
        # プロジェクトフィルタ: 同一プロジェクトのセッションを優先
        target_session_id = None
        project_sessions = session_project_map.get(project_name, set()) if project_name else set()

        # 1st pass: 同プロジェクト内で時系列的に次のセッションを探す
        if project_sessions:
            for sid, s_created in session_starts:
                if s_created > handoff_created and sid != source_session_id and sid in project_sessions:
                    target_session_id = sid
                    break

        # 2nd pass: プロジェクトフィルタで見つからなければ全セッションからフォールバック
        if target_session_id is None:
            for sid, s_created in session_starts:
                if s_created > handoff_created and sid != source_session_id:
                    target_session_id = sid
                    break

        store.record_chain(
            handoff_id=handoff_id,
            source_session_id=source_session_id,
            target_session_id=target_session_id,
        )
        chain_count += 1

    logger.info("Built %d η/ε chains", chain_count)
    return chain_count


# ── プロジェクト走査・マッチング (Phase 3) ─────────────────


# PURPOSE: ディレクトリ構造からプロジェクトを自動登録する
def _scan_projects(store: PhantazeinStore) -> int:
    """Boulēsis/Poiema/External のサブディレクトリを projects テーブルに登録する。

    プロジェクト ID の命名規則:
        boulesis/{dir_name}  — 企画プロジェクト
        poiema/{dir_name}    — 作品プロジェクト
        external/{dir_name}  — 外部 OSS プロジェクト

    Returns:
        登録/更新したプロジェクト数
    """
    from mekhane.paths import BOULESIS_DIR, POIEMA_DIR, EXTERNAL_DIR

    # (カテゴリ prefix, ディレクトリ Path) のペア
    sources = [
        ("boulesis", BOULESIS_DIR),
        ("poiema", POIEMA_DIR),
        ("external", EXTERNAL_DIR),
    ]

    count = 0
    for prefix, base_dir in sources:
        if not base_dir.is_dir():
            continue
        for child in sorted(base_dir.iterdir()):
            if not child.is_dir():
                continue
            # ディレクトリ名をそのまま name に使う (例: "01_美論｜Kalon")
            dir_name = child.name
            project_id = f"{prefix}/{dir_name}"
            store.upsert_project(
                project_id=project_id,
                name=dir_name,
                dir_path=str(child),
            )
            count += 1

    logger.info("Scanned %d projects from directory structure", count)
    return count


# PURPOSE: Handoff タイトル/ファイル名からプロジェクトをマッチングする
def _match_handoffs_to_projects(store: PhantazeinStore) -> int:
    """project_id が未設定の Handoff に対し、タイトル/ファイル名にプロジェクト名キーワードが
    含まれていれば project_id を設定する。

    マッチングロジック:
        1. projects テーブルから全プロジェクトを取得
        2. 各プロジェクト名からキーワードを抽出 (日本語部分と英語部分)
        3. project_id が NULL の Handoff を走査し、タイトル/ファイル名に
           キーワードが含まれていれば project_id を設定

    Returns:
        マッチした Handoff 数
    """
    all_projects = store.get_all_projects()
    if not all_projects:
        return 0

    # プロジェクト名からキーワードを抽出
    # 例: "01_美論｜Kalon" → ["kalon", "美論"]
    # 例: "openclaw" → ["openclaw"]
    project_keywords: list[tuple[str, list[str]]] = []
    for proj in all_projects:
        pid = proj["id"]
        name = proj["name"]
        keywords = _extract_project_keywords(name)
        if keywords:
            project_keywords.append((pid, keywords))

    if not project_keywords:
        return 0

    # project_id が未設定の Handoff を取得
    unmatched = store._conn.execute(
        """
        SELECT id, filename, title
        FROM handoffs
        WHERE project_id IS NULL OR project_id = ''
        """
    ).fetchall()

    matched = 0
    for row in unmatched:
        hid = row["id"]
        # タイトルとファイル名を結合して検索対象にする (小文字化)
        search_text = f"{row['title'] or ''} {row['filename'] or ''}".lower()

        best_match = _find_best_project_match(search_text, project_keywords)
        if best_match:
            store.update_handoff_project(hid, best_match)
            matched += 1

    logger.info("Matched %d handoffs to projects (out of %d unmatched)", matched, len(unmatched))
    return matched


def _extract_project_keywords(dir_name: str) -> list[str]:
    """ディレクトリ名からマッチング用キーワードを抽出する。

    命名パターン:
        "01_美論｜Kalon" → ["kalon", "美論"]
        "openclaw" → ["openclaw"]
        "B_活用｜Praxis" → ["praxis", "活用"]
        "deer-flow" → ["deer-flow", "deerflow"]

    Returns:
        小文字化されたキーワードのリスト
    """
    keywords = []

    # "01_美論｜Kalon" → 数字プレフィックスを除去 → "美論｜Kalon"
    # パターン: 数字+アンダースコアのプレフィックス or 英字+アンダースコアのプレフィックス
    cleaned = re.sub(r'^[0-9A-Z]+_', '', dir_name)

    # "|" または "｜" で分割
    parts = re.split(r'[|｜]', cleaned)
    for part in parts:
        part = part.strip()
        if part:
            keywords.append(part.lower())

    # ハイフン付き名前の場合、ハイフンなし版も追加 (例: "deer-flow" → "deerflow")
    for kw in list(keywords):
        if '-' in kw:
            keywords.append(kw.replace('-', ''))

    return keywords


def _find_best_project_match(
    search_text: str,
    project_keywords: list[tuple[str, list[str]]],
) -> Optional[str]:
    """検索テキストに最もマッチするプロジェクトの ID を返す。

    マッチング優先度:
        1. 最も長いキーワードが一致したプロジェクトを優先 (短い偽陽性を防ぐ)
        2. 同じ長さなら最初に見つかった方

    Returns:
        マッチしたプロジェクト ID、なければ None
    """
    best_pid = None
    best_len = 0

    for pid, keywords in project_keywords:
        for kw in keywords:
            if len(kw) < 3:
                # 短すぎるキーワードは偽陽性リスクが高い → スキップ
                continue
            if kw in search_text:
                if len(kw) > best_len:
                    best_len = len(kw)
                    best_pid = pid

    return best_pid


# ── 公開 API ─────────────────────────────────────────────────


# PURPOSE: 全量走査を実行する
def full_sync(store: Optional[PhantazeinStore] = None) -> dict:
    """全データソースを走査し、DB に格納する。

    Returns:
        走査結果のサマリー dict
    """
    if store is None:
        store = get_store()

    start = time.time()
    results = {
        "projects": 0,
        "sessions": 0,
        "total_artifacts": 0,
        "handoffs": 0,
        "roms": 0,
        "linked_handoffs": 0,
        "linked_roms": 0,
        "chains": 0,
        "matched_projects": 0,
        "duration_sec": 0.0,
    }

    # 0.5. プロジェクト走査 (Phase 3: ディレクトリ構造から自動登録)
    results["projects"] = _scan_projects(store)

    # 1. IDE セッション走査
    brain_dir = _get_brain_dir()
    if brain_dir.exists():
        for session_dir in brain_dir.iterdir():
            if session_dir.is_dir() and UUID_PATTERN.match(session_dir.name):
                art_count = _scan_session(session_dir, store)
                results["sessions"] += 1
                results["total_artifacts"] += art_count
    logger.info(
        "IDE sessions scanned: %d sessions, %d artifacts",
        results["sessions"], results["total_artifacts"]
    )

    # 2. Handoff 走査 (Phase 2: YAML パース統合)
    handoff_dir = _get_handoff_dir()
    results["handoffs"] = _scan_handoffs(handoff_dir, store)
    logger.info("Handoffs scanned: %d", results["handoffs"])

    # 3. ROM 走査
    rom_dir = _get_rom_dir()
    results["roms"] = _scan_roms(rom_dir, store)
    logger.info("ROMs scanned: %d", results["roms"])

    # 4. Handoff/ROM → セッション紐づけ (S2: 日時近接フォールバック)
    linked_h, linked_r = _link_to_sessions(store)
    results["linked_handoffs"] = linked_h
    results["linked_roms"] = linked_r

    # 5. η/ε 連鎖構築 (Phase 2)
    results["chains"] = _build_chains(store)

    # 5.5. Handoff → Project マッチング (Phase 3: キーワードマッチ)
    results["matched_projects"] = _match_handoffs_to_projects(store)

    results["duration_sec"] = round(time.time() - start, 2)
    logger.info(
        "Full sync completed in %.2fs (projects=%d, chains=%d, matched=%d)",
        results["duration_sec"], results["projects"],
        results["chains"], results["matched_projects"]
    )
    return results


# PURPOSE: 差分走査を実行する (mtime ベース)
def incremental_sync(
    since: Optional[float] = None,
    store: Optional[PhantazeinStore] = None,
) -> dict:
    """最終更新時刻以降に変更されたファイルのみ走査する。

    Args:
        since: Unix timestamp。省略時は直近24時間。

    Returns:
        走査結果のサマリー dict
    """
    if store is None:
        store = get_store()
    if since is None:
        since = time.time() - 86400  # 直近24時間

    start = time.time()
    results = {
        "sessions": 0,
        "total_artifacts": 0,
        "handoffs": 0,
        "roms": 0,
        "chains": 0,
        "duration_sec": 0.0,
        "mode": "incremental",
        "since": since,
    }

    # 1. IDE セッション (更新されたもののみ)
    brain_dir = _get_brain_dir()
    if brain_dir.exists():
        for session_dir in brain_dir.iterdir():
            if not session_dir.is_dir() or not UUID_PATTERN.match(session_dir.name):
                continue
            # ディレクトリ内のいずれかのファイルが since 以降に更新されているか
            has_recent = any(
                f.stat().st_mtime > since
                for f in session_dir.iterdir()
                if f.is_file()
            )
            if has_recent:
                art_count = _scan_session(session_dir, store)
                results["sessions"] += 1
                results["total_artifacts"] += art_count

    # 2. Handoff (since 以降に更新されたもの — Phase 2: YAML パース統合)
    handoff_dir = _get_handoff_dir()
    if handoff_dir.exists():
        for f in handoff_dir.iterdir():
            if f.is_file() and f.name.startswith("handoff_") and f.stat().st_mtime > since:
                text = ""
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        text = fh.read()
                except (UnicodeDecodeError, OSError):
                    pass

                meta = _parse_handoff_content(text) if text else {}
                store.upsert_handoff(
                    filename=f.name, filepath=str(f),
                    created_at=f.stat().st_mtime, size_bytes=f.stat().st_size,
                    title=meta.get("title", "") or "",
                    session_id=meta.get("session_id"),
                    project_name=meta.get("project"),
                    handoff_version=meta.get("handoff_version"),
                )
                results["handoffs"] += 1

    # 3. ROM (since 以降に更新されたもの)
    rom_dir = _get_rom_dir()
    if rom_dir.exists():
        for f in rom_dir.iterdir():
            if f.is_file() and f.name.startswith("rom_") and f.stat().st_mtime > since:
                topic = ""
                m = ROM_TOPIC_PATTERN.search(f.name)
                if m:
                    topic = m.group(1).replace("_", " ")
                store.upsert_rom(
                    filename=f.name, filepath=str(f),
                    created_at=f.stat().st_mtime, size_bytes=f.stat().st_size, topic=topic,
                )
                results["roms"] += 1

    # 4. η/ε 連鎖構築 (Phase 2)
    if results["handoffs"] > 0:
        results["chains"] = _build_chains(store)

    results["duration_sec"] = round(time.time() - start, 2)
    logger.info("Incremental sync completed in %.2fs (chains=%d)", results["duration_sec"], results.get("chains", 0))
    return results
