#!/usr/bin/env python3
"""bulk_dissolve_md.py — HGK プロジェクト内の全 .md / .typos を PhantasiaField に溶解する

PURPOSE: ROM / handoff / Nous / Mekhane / kernel 等の全マークダウンを
  PhantasiaField.dissolve() 経由で統一意味場 (GnosisIndex) に溶解する。
  Claude が検索でトークンをかけずに情報にアクセスできるようにする。

参考: dissolve_sessions.py (sys.path 解決 + 溶解ループの基本パターン)

使い方:
  python bulk_dissolve_md.py --dry-run           # ファイル数・source 別分布のみ表示
  python bulk_dissolve_md.py --max 3              # 最初の 3 件だけ溶解
  python bulk_dissolve_md.py --root <path>        # 特定サブディレクトリのみ
  python bulk_dissolve_md.py --resume             # 進捗 JSON から再開
  python bulk_dissolve_md.py                      # 全件溶解 (未処理のみ)
  python bulk_dissolve_md.py --force-replace --source-only rom        # ROM だけ削除→再溶解
  python bulk_dissolve_md.py --force-replace --source-only rom --dry-run  # 削除予定数のみ表示
  python bulk_dissolve_md.py --force-replace --source-only rom --yes  # 確認プロンプト skip
"""

import argparse
import json
import os
import subprocess
import sys
import time
import signal
from datetime import datetime, timezone
from pathlib import Path

# ── sys.path 解決 (dissolve_sessions.py から流用) ─────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _find_src_dir() -> str:
    hgk_root = os.environ.get("HGK_ROOT", "")
    if hgk_root:
        candidate = os.path.join(hgk_root, "20_機構｜Mekhane", "_src｜ソースコード")
        if os.path.isdir(candidate):
            return candidate
    hgk_root_guess = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
    for dirname in os.listdir(hgk_root_guess):
        if dirname.startswith("20_") and "Mekhane" in dirname:
            for subdir in os.listdir(os.path.join(hgk_root_guess, dirname)):
                if subdir.startswith("_src"):
                    candidate = os.path.join(hgk_root_guess, dirname, subdir)
                    if os.path.isdir(os.path.join(candidate, "mekhane")):
                        return candidate
    return os.path.normpath(
        os.path.join(SCRIPT_DIR, "..", "..", "20_機構｜Mekhane", "_src｜ソースコード")
    )


SRC_DIR = _find_src_dir()
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


# ── 設定 ─────────────────────────────────────────────────────────

HGK_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
PROGRESS_PATH = Path.home() / ".claude" / "hooks" / "logs" / "bulk_dissolve_progress.json"

EXCLUDE_PATTERNS = [
    "/.git/", "/.venv/", "/.stversions/", "/.tmp/", "/.tmp_index_export/",
    "/.codex_tmp/", "/.pytest_cache/", "/node_modules/", "/__pycache__/",
    "/90_保管庫｜Archive/",
    "/.claude/worktrees/",
]

EXTENSIONS = (".md", ".typos")


# ── ユーティリティ ──────────────────────────────────────────────

def _classify_source(path: Path) -> str:
    s = str(path)
    if "00_核心｜Kernel/" in s:
        return "kernel"
    if "30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff/" in s:
        return "handoff"
    if "30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/" in s:
        return "rom"
    if "30_記憶｜Mneme/01_記録｜Records/d_成果物｜artifacts/" in s:
        return "doxa"
    if "30_記憶｜Mneme/01_記録｜Records/b_対話｜sessions/" in s:
        return "session"
    return "sophia"


def _classify_project(path: Path) -> str:
    s = str(path)
    if "/10_知性｜Nous/" in s:
        return "nous"
    if "/20_機構｜Mekhane/" in s:
        return "mekhane"
    if "/30_記憶｜Mneme/" in s:
        return "mneme"
    if "/40_作品｜Poiema/" in s:
        return "poiema"
    if "/60_実験｜Peira/" in s:
        return "peira"
    if "/80_運用｜Ops/" in s:
        return "ops"
    if "/00_核心｜Kernel/" in s:
        return "kernel"
    return ""


def _extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()[:200]
    return fallback


def _is_excluded(path: Path) -> bool:
    s = str(path)
    return any(pat in s for pat in EXCLUDE_PATTERNS)


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _walk_targets(root: Path) -> list[Path]:
    """対象ディレクトリから .md/.typos を再帰収集する。"""
    results: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # 除外パターンを含むサブディレクトリは入らない
        if _is_excluded(Path(dirpath + "/")):
            dirnames[:] = []
            continue
        # 除外 dirname を in-place で削除
        dirnames[:] = [
            d for d in dirnames
            if not _is_excluded(Path(os.path.join(dirpath, d) + "/"))
        ]
        for fname in filenames:
            if fname.endswith(EXTENSIONS):
                p = Path(os.path.join(dirpath, fname))
                if not _is_excluded(p):
                    results.append(p)
    return sorted(results)


def _load_existing_paths() -> set[str]:
    """既存 FAISS metadata から既溶解パス集合を構築する (dedup キー)。

    GnosisIndex.add_chunks は `url` を空にし `parent_id` にパスを入れる経路と、
    逆に `url` にパスを入れる古い経路が混在している。両方を dedup キーとして拾う。
    """
    from mekhane.anamnesis.index import GnosisIndex
    idx = GnosisIndex()
    backend = idx._backend
    backend._load()
    paths: set[str] = set()
    for rec in backend._metadata.values():
        for key in ("url", "parent_id", "source_id"):
            v = rec.get(key)
            if v:
                paths.add(v)
    return paths


def _load_path_record_counts() -> tuple[dict[str, int], dict[str, int]]:
    """各ファイルパスに対する url-match / parent_id-match の件数を返す。

    Returns:
        (url_counts, parent_counts)
        url_counts[path]    = url == path のレコード数
        parent_counts[path] = parent_id == path のレコード数
    """
    from mekhane.anamnesis.index import GnosisIndex
    idx = GnosisIndex()
    backend = idx._backend
    backend._load()
    url_counts: dict[str, int] = {}
    parent_counts: dict[str, int] = {}
    for rec in backend._metadata.values():
        u = rec.get("url")
        if u:
            url_counts[u] = url_counts.get(u, 0) + 1
        p = rec.get("parent_id")
        if p:
            parent_counts[p] = parent_counts.get(p, 0) + 1
    return url_counts, parent_counts


def _delete_existing_records(backend, file_path: str) -> tuple[int, int]:
    """指定パスに紐づくレガシー (url=path) と既存 new (parent_id=path) を削除する。

    Args:
        backend: GnosisIndex._backend (FAISSBackend 等)
        file_path: 対象ファイルの絶対パス文字列

    Returns:
        (n_legacy, n_new) 削除件数のタプル
    """
    # FAISSBackend._match_filter は "field = 'value'" のシングルクォート形式のみ対応
    # value 中に ' が含まれる場合は安全側で削除をスキップ (現状そういう path はない)
    if "'" in file_path:
        return (0, 0)
    n_legacy = backend.delete(f"url = '{file_path}'")
    n_new = backend.delete(f"parent_id = '{file_path}'")
    return (n_legacy, n_new)


def _load_progress() -> dict:
    if not PROGRESS_PATH.exists():
        return {}
    try:
        with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_progress(progress: dict) -> None:
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = PROGRESS_PATH.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    tmp.replace(PROGRESS_PATH)


def _dissolve_with_retry(field, text, source, session_id, project_id,
                         title, parent_id, max_retries: int = 5) -> int:
    """dissolve を exponential backoff で retry する。"""
    delay = 2.0
    for attempt in range(max_retries):
        try:
            return field.dissolve(
                text=text,
                source=source,
                session_id=session_id,
                project_id=project_id,
                title=title,
                parent_id=parent_id,
                dedupe=True,
            )
        except Exception as e:
            msg = str(e).lower()
            retryable = any(tok in msg for tok in ("rate", "503", "429", "timeout", "unavailable"))
            if not retryable or attempt == max_retries - 1:
                raise
            print(f"    ⏳ retry {attempt+1}/{max_retries} after {delay:.1f}s ({e})")
            time.sleep(delay)
            delay *= 2
    return 0


# ── Post-dissolve sync (Symploke Kairos/Sophia 即時反映) ────────

def _post_dissolve_sync(project_root: Path) -> None:
    """bulk_dissolve 完了後、Symploke Kairos/Sophia インデックスを同期する。

    subprocess で既存の kairos_ingest.py / sophia_ingest.py を直接呼ぶ。
    既存の systemd service (hgk-symploke-refresh.service) と同じ呼出パターン。
    失敗は non-fatal (bulk dissolve 結果を無効化しない)。
    """
    python_bin = project_root / ".venv" / "bin" / "python"
    src_dir = project_root / "20_機構｜Mekhane" / "_src｜ソースコード"
    kairos_script = src_dir / "mekhane" / "symploke" / "kairos_ingest.py"
    sophia_script = src_dir / "mekhane" / "symploke" / "sophia_ingest.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_dir)

    print("\n🔗 Post-dissolve sync: Symploke Kairos/Sophia...")
    for script, extra_args in [(kairos_script, ["--all"]), (sophia_script, [])]:
        try:
            result = subprocess.run(
                [str(python_bin), str(script)] + extra_args,
                env=env, cwd=str(project_root),
                timeout=1800,
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                print(f"  ✅ {script.name}")
            else:
                err_tail = (result.stderr or "")[:200]
                print(f"  ⚠️ {script.name} exit={result.returncode}: {err_tail}")
        except Exception as e:
            print(f"  ⚠️ {script.name} failed: {e} (non-fatal)")
    print("🔗 Post-sync complete")


# ── メインロジック ──────────────────────────────────────────────

def cmd_run(args) -> int:
    root = Path(args.root) if args.root else Path(HGK_ROOT)
    if not root.exists():
        print(f"❌ root が見つかりません: {root}", file=sys.stderr)
        return 1

    # --source-only パース ("rom,handoff" → {"rom","handoff"}; 空 = 全 source)
    source_filter: set[str] = set()
    if getattr(args, "source_only", ""):
        source_filter = {s.strip() for s in args.source_only.split(",") if s.strip()}

    force_replace: bool = bool(getattr(args, "force_replace", False))
    auto_yes: bool = bool(getattr(args, "yes", False))

    print(f"🔍 走査中: {root}")
    all_files_raw = _walk_targets(root)

    # source filter 適用 (--source-only)
    if source_filter:
        all_files = [p for p in all_files_raw if _classify_source(p) in source_filter]
        print(f"📌 --source-only={','.join(sorted(source_filter))} 適用: "
              f"{len(all_files_raw):,} → {len(all_files):,} 件")
    else:
        all_files = all_files_raw

    total_size = sum(p.stat().st_size for p in all_files)

    # source 別分布
    by_source: dict[str, int] = {}
    for p in all_files:
        s = _classify_source(p)
        by_source[s] = by_source.get(s, 0) + 1

    print("📦 FAISS metadata ロード中...")
    if force_replace:
        # --force-replace: 既存削除モード。url / parent_id 別の件数を取得
        try:
            url_counts, parent_counts = _load_path_record_counts()
        except Exception as e:
            print(f"⚠️ metadata ロード失敗: {e} — 削除件数を 0 とみなす")
            url_counts, parent_counts = {}, {}
        existing_paths: set[str] = set()  # force-replace では skip 判定無効
    else:
        # 通常モード: 既存パス集合で dedup
        try:
            existing_paths = _load_existing_paths()
        except Exception as e:
            print(f"⚠️ metadata ロード失敗: {e} — 全件 fresh とみなす")
            existing_paths = set()
        url_counts, parent_counts = {}, {}

    # 対象ファイルを skip / todo に分類
    todo: list[Path] = []
    skipped_existing = 0
    for p in all_files:
        if not force_replace and str(p) in existing_paths:
            skipped_existing += 1
        else:
            todo.append(p)

    # dry-run / 通常実行ヘッダ
    print()
    if args.dry_run:
        header = "=== Bulk Dissolve Dry-Run (force-replace) ===" if force_replace \
                 else "=== Bulk Dissolve Dry-Run ==="
    else:
        header = "=== Bulk Dissolve (force-replace) ===" if force_replace \
                 else "=== Bulk Dissolve ==="
    print(header)
    print(f"Root: {root}")
    if source_filter:
        print(f"Source filter: {','.join(sorted(source_filter))}")
    print(f"Target files: {len(all_files):,}")
    for s in sorted(by_source):
        print(f"  {s}: {by_source[s]:,}")
    print(f"Total size: {_format_size(total_size)}")

    # 削除予定件数 (force-replace 時のみ)
    deletion_url_total = 0
    deletion_parent_total = 0
    if force_replace:
        for p in todo:
            sp = str(p)
            deletion_url_total += url_counts.get(sp, 0)
            deletion_parent_total += parent_counts.get(sp, 0)
        deletion_total = deletion_url_total + deletion_parent_total
        print(f"Existing records to delete: {deletion_total:,}")
        print(f"  by url match: {deletion_url_total:,}")
        print(f"  by parent_id match: {deletion_parent_total:,}")
        print(f"To dissolve (after deletion): {len(todo):,} files")
    else:
        print(f"Already in DB (by path): {skipped_existing:,}")
        print(f"To dissolve: {len(todo):,}")

    if args.dry_run:
        est_chunks = len(todo) * 8  # ざっくり 1ファイル 8 chunks 想定
        est_dissolve_min = len(todo) * 3 / 60  # ざっくり 1ファイル 3 秒
        if force_replace:
            # 削除は record 1件あたり ~10ms, _save() がボトルネック (1ファイル 2 calls × ~50ms)
            est_delete_min = len(todo) * 0.1 / 60
            print(f"Estimated chunks: ~{est_chunks:,}")
            print(f"Estimated time: ~{est_delete_min:.1f} min (deletion) "
                  f"+ ~{est_dissolve_min:.0f} min (dissolve) "
                  f"= ~{est_delete_min + est_dissolve_min:.0f} min")
        else:
            print(f"Estimated chunks: ~{est_chunks:,}")
            print(f"Estimated time: ~{est_dissolve_min:.0f} min (rough)")
        return 0

    if args.max and args.max > 0:
        todo = todo[: args.max]
        print(f"(--max {args.max} 適用: {len(todo)} 件に制限)")

    if not todo:
        print("✅ 処理対象なし")
        return 0

    # --force-replace の安全確認 (大量削除の場合)
    if force_replace and not auto_yes and len(todo) >= 50:
        print()
        print(f"⚠️ --force-replace で {len(todo):,} 件のファイルを削除→再溶解します")
        try:
            ans = input("続行しますか？ [y/N]: ").strip().lower()
        except EOFError:
            ans = ""
        if ans not in ("y", "yes"):
            print("🛑 中止")
            return 1

    # resume 処理
    progress = _load_progress() if args.resume else {}
    processed_paths = {e.get("path") for e in progress.get("processed", [])
                       if e.get("status") in ("ok", "skip")}
    if args.resume and processed_paths:
        before = len(todo)
        todo = [p for p in todo if str(p) not in processed_paths]
        print(f"(--resume: {before - len(todo)} 件を済みとしてスキップ)")

    if not progress:
        progress = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "total_files": len(todo),
            "processed": [],
            "failed_files": [],
        }

    # 溶解開始
    print("\n⚙️ PhantasiaField を初期化中...")
    from mekhane.anamnesis.phantasia_field import PhantasiaField
    field = PhantasiaField(chunker_mode="nucleator")

    # --force-replace で削除に使う backend を取得 (PhantasiaField と同じ index を共有)
    delete_backend = None
    if force_replace:
        try:
            from mekhane.anamnesis.index import GnosisIndex
            delete_backend = GnosisIndex()._backend
            delete_backend._load()
        except Exception as e:
            # 偏差5 修正: silent downgrade 廃止。
            # backend 取得失敗時に force_replace=False に降格すると、
            # 全削除予定のものが通常 dissolve に降格し重複 chunks を生む。
            # → fail-fast: stderr に理由を出して abort する。
            print(
                f"❌ delete backend 取得失敗: {e}\n"
                "   --force-replace 指定時は legacy chunks の削除が必須のため、"
                "重複投入を避けるため abort します。\n"
                "   対処: backend (GnosisIndex) の初期化問題を解決してから再実行してください。",
                file=sys.stderr,
            )
            sys.exit(1)

    print("🔥 溶解開始...\n")
    start = time.time()
    total_chunks = 0
    ok_count = 0
    skip_count = 0
    err_count = 0
    total_deleted = 0

    # Ctrl+C で graceful flush
    interrupted = {"flag": False}

    def _sigint(_signum, _frame):
        interrupted["flag"] = True
        print("\n⚠️ 中断シグナル受信 — 現在のファイル完了後に停止します")

    signal.signal(signal.SIGINT, _sigint)

    for i, path in enumerate(todo, 1):
        source = _classify_source(path)
        project_id = _classify_project(path)

        try:
            text = path.read_text(encoding="utf-8")
        except Exception as e:
            err_count += 1
            progress["processed"].append({
                "path": str(path), "chunks": 0, "deleted": 0, "status": "error",
                "error": f"read failed: {e}",
            })
            progress["failed_files"].append(str(path))
            _save_progress(progress)
            print(f"[{i}/{len(todo)}] ❌ {path.name} → read error: {e}")
            if interrupted["flag"]:
                break
            continue

        if not text.strip():
            skip_count += 1
            progress["processed"].append({
                "path": str(path), "chunks": 0, "deleted": 0, "status": "skip",
                "error": "empty",
            })
            _save_progress(progress)
            if i % 10 == 0:
                print(f"[{i}/{len(todo)}] ⏭️ {path.name} → empty (skip)")
            if interrupted["flag"]:
                break
            continue

        # --force-replace: dissolve 直前にレガシー (url=path) と既存 new (parent_id=path) を削除
        n_deleted = 0
        delete_error: str = ""
        if force_replace and delete_backend is not None:
            try:
                n_legacy, n_new = _delete_existing_records(delete_backend, str(path))
                n_deleted = n_legacy + n_new
                total_deleted += n_deleted
            except Exception as e:
                delete_error = str(e)
                err_count += 1
                progress["processed"].append({
                    "path": str(path), "chunks": 0, "deleted": 0, "status": "error",
                    "error": f"delete failed: {e}",
                })
                progress["failed_files"].append(str(path))
                _save_progress(progress)
                print(f"[{i}/{len(todo)}] ❌ {path.name} → delete error: {e}")
                if interrupted["flag"]:
                    break
                continue

        title = _extract_title(text, path.stem)

        try:
            n_chunks = _dissolve_with_retry(
                field,
                text=text,
                source=source,
                session_id="",
                project_id=project_id,
                title=title,
                parent_id=str(path),
            )
            if n_chunks > 0:
                ok_count += 1
                total_chunks += n_chunks
                status = "ok"
            else:
                skip_count += 1
                status = "skip"
            progress["processed"].append({
                "path": str(path), "chunks": n_chunks, "deleted": n_deleted, "status": status,
            })
            if i % 10 == 0 or n_chunks == 0 or (force_replace and n_deleted > 0):
                rel = str(path).replace(str(root), ".")
                del_tag = f" (-{n_deleted} legacy)" if force_replace and n_deleted else ""
                print(f"[{i}/{len(todo)}] {'✅' if status == 'ok' else '⏭️'} "
                      f"...{rel[-60:]} → {n_chunks} chunks{del_tag} (source={source})")
        except Exception as e:
            err_count += 1
            progress["processed"].append({
                "path": str(path), "chunks": 0, "deleted": n_deleted, "status": "error",
                "error": str(e),
            })
            progress["failed_files"].append(str(path))
            print(f"[{i}/{len(todo)}] ❌ {path.name} → {e}")

        _save_progress(progress)

        if interrupted["flag"]:
            print(f"\n🛑 中断: {i}/{len(todo)} 件処理済")
            break

    elapsed = time.time() - start
    print(f"\n📊 Bulk Dissolve 結果 ({elapsed:.1f}秒):")
    print(f"   溶解 OK: {ok_count}")
    print(f"   スキップ: {skip_count}")
    print(f"   エラー: {err_count}")
    print(f"   総チャンク: {total_chunks:,}")
    print(f"   進捗 JSON: {PROGRESS_PATH}")

    # Post-dissolve sync (Symploke Kairos/Sophia)
    skip_sync: bool = bool(getattr(args, "skip_sync", False))
    if not args.dry_run and not skip_sync and ok_count > 0:
        try:
            _post_dissolve_sync(Path(HGK_ROOT))
        except Exception as e:
            print(f"⚠️ post-dissolve sync aborted: {e} (non-fatal)")
    return 0 if err_count == 0 else 2


def main():
    parser = argparse.ArgumentParser(
        description="HGK プロジェクトの .md / .typos を PhantasiaField に一括溶解",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="溶解せず対象ファイル数・source 分布のみ表示")
    parser.add_argument("--max", type=int, default=0,
                        help="最大溶解件数 (0=全件)")
    parser.add_argument("--root", type=str, default="",
                        help="走査開始ディレクトリ (デフォルト: HGK プロジェクトルート)")
    parser.add_argument("--resume", action="store_true",
                        help="進捗 JSON から再開 (処理済みはスキップ)")
    parser.add_argument("--force-replace", dest="force_replace",
                        action="store_true",
                        help="既存レコード (url=path / parent_id=path) を削除してから再溶解")
    parser.add_argument("--source-only", dest="source_only", type=str, default="",
                        help="source 種別フィルタ (カンマ区切り。例: rom / rom,handoff)")
    parser.add_argument("--yes", "-y", dest="yes", action="store_true",
                        help="--force-replace で 50 件以上の確認プロンプトを skip")
    parser.add_argument("--skip-sync", dest="skip_sync", action="store_true",
                        help="post-dissolve sync (Symploke Kairos/Sophia) をスキップ")
    args = parser.parse_args()
    return cmd_run(args)


if __name__ == "__main__":
    sys.exit(main())
