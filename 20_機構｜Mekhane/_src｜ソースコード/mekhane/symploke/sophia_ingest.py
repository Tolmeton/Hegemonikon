#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/ A0→知識管理が必要→sophia_ingest が担う
"""
Sophia Ingest - Knowledge Items を Sophia インデックスに自動投入

Usage:
    python sophia_ingest.py                    # 全KIを投入
    python sophia_ingest.py --dry-run          # パースのみ
"""

from mekhane.paths import (
    MNEME_STATE, HGK_ROOT, EPISTEME_DIR, KERNEL_DIR, NOUS_DIR, MEKHANE_DIR, MNEME_DIR,
    BOULESIS_DIR, HYLE_DIR, OPS_DIR, MNEME_RECORDS, MNEME_BELIEFS,
)
import sys
import os
import json
import argparse
from pathlib import Path

# プロジェクトルートを PATH に追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# .env から API キーを読み込む (VertexEmbedder が GOOGLE_API_KEY_* を参照)
try:
    from mekhane.paths import ensure_env
    ensure_env()
except ImportError:
    pass  # mekhane.paths 未インストール — システム環境変数に依存

from mekhane.symploke.indices import Document

# 複数 KI ソースディレクトリ (順にスキャン)
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_HOME = Path.home()

# スキャン対象ディレクトリ (KI 構造 — metadata.json + artifacts/)
# 優先度: env override > Nous KI > Antigravity KI > brain > legacy
DEFAULT_KNOWLEDGE_DIRS: list[Path] = [
    EPISTEME_DIR / "B_知識項目｜KnowledgeItems",              # Nous KI (正規パス)
    _HOME / ".gemini" / "antigravity" / "knowledge",          # Antigravity IDE KIs
    _HOME / ".gemini" / "antigravity" / "brain",              # IDE セッションアーティファクト
    MNEME_STATE / "knowledge",                                 # mneme KIs (旧パス)
    _PROJECT_ROOT / "kernel" / "knowledge",                    # legacy kernel KIs
]

# 汎用ドキュメントディレクトリ (parse_generic_documents でスキャン)
# KI 構造ではなく、直接 .md ファイルを再帰的にパースする
GENERIC_DOCUMENT_DIRS: list[tuple[Path, str]] = [
    # --- 既存 ---
    (KERNEL_DIR, "kernel"),                                      # 公理・定理の根幹
    (NOUS_DIR / "01_制約｜Constraints", "horos"),                 # Hóros, CCL 定義
    (NOUS_DIR / "02_手順｜Procedures", "workflow"),               # WF, Skills, Macros
    (NOUS_DIR / "03_知識｜Epistēmē", "episteme"),                # KI, ドキュメント
    (MEKHANE_DIR, "mekhane_doc"),                                 # モジュール docs
    (MNEME_DIR / "01_記録｜Records" / "d_成果物｜artifacts", "artifact"),  # セッション成果物
    # --- v1.2 拡張: 全ギャップ追加 ---
    (BOULESIS_DIR, "boulesis"),                                   # Sprint/計画/PRD
    (HYLE_DIR, "hyle"),                                           # テンプレート・素材
    (MNEME_RECORDS / "c_ROM｜rom", "rom"),                        # ROM 蒸留コンテキスト
    (MNEME_RECORDS / "b_対話｜sessions", "session"),              # 対話ログ
    (MNEME_RECORDS / "e_レビュー｜reviews", "review"),            # レビュー記録
    (OPS_DIR, "ops_doc"),                                         # 運用ドキュメント
    (MNEME_RECORDS / "g_実行痕跡｜traces", "trace"),              # WF 実行痕跡
    (MNEME_BELIEFS, "belief"),                                     # 信念・エピソード記憶
]

# _src, キャッシュ等の除外パターン
_EXCLUDE_DIRS = {
    "_src｜ソースコード", "_src", "__pycache__", ".git", "node_modules",
    "90_保管庫｜Archive", "09_保管｜Archeia", ".system_generated",
    ".obsidian", ".stversions", "archive",
}

# If HGK_KNOWLEDGE_DIR is set, use ONLY that directory (backwards compat)
_env_knowledge_dir = os.environ.get("HGK_KNOWLEDGE_DIR")
if _env_knowledge_dir:
    KNOWLEDGE_DIRS = [Path(_env_knowledge_dir)]
else:
    KNOWLEDGE_DIRS = [d for d in DEFAULT_KNOWLEDGE_DIRS if d.exists()]


# PURPOSE: Parse a KI directory into Documents
def parse_ki_directory(ki_path: Path) -> list[Document]:
    """Parse a KI directory into Documents.

    Note: Uses rglob to capture nested .md files in subdirectories.
    """
    docs = []

    # Read metadata.json
    metadata_file = ki_path / "metadata.json"
    if not metadata_file.exists():
        return docs

    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    ki_name = metadata.get("name", ki_path.name)
    summary = metadata.get("summary", "")

    # Read artifact files (including nested directories)
    artifacts_dir = ki_path / "artifacts"
    if artifacts_dir.exists():
        for artifact_file in artifacts_dir.rglob("*.md"):  # Changed: glob -> rglob
            content = artifact_file.read_text(encoding="utf-8")

            # Use relative path from artifacts_dir as part of ID
            rel_path = artifact_file.relative_to(artifacts_dir)
            doc_id = (
                f"ki-{ki_path.name}-{str(rel_path.with_suffix('')).replace('/', '-')}"
            )

            doc = Document(
                id=doc_id,
                content=f"{ki_name}\n\n{summary}\n\n{content[:1500]}",  # Combine for context
                metadata={
                    "type": "knowledge_item",
                    "ki_name": ki_name,
                    "summary": summary[:200],
                    "artifact": artifact_file.name,
                    "file_path": str(artifact_file),
                    "subdir": (
                        str(rel_path.parent) if rel_path.parent != Path(".") else None
                    ),
                },
            )
            docs.append(doc)

    # If no artifacts, create doc from summary
    if not docs and summary:
        docs.append(
            Document(
                id=f"ki-{ki_path.name}",
                content=f"{ki_name}\n\n{summary}",
                metadata={
                    "type": "knowledge_item",
                    "ki_name": ki_name,
                    "summary": summary[:200],
                },
            )
        )

    return docs


# PURPOSE: brain セッション内の .md アーティファクトを Document に変換
def parse_brain_session(session_path: Path) -> list[Document]:
    """brain セッションの .md アーティファクトを Document に変換。

    .system_generated/ 配下は除外し、直下の .md ファイルのみをパースする。
    """
    docs = []
    session_id = session_path.name[:8]  # UUID の先頭8文字

    for md_file in session_path.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:  # noqa: BLE001
            continue
        if not content.strip():
            continue

        # 先頭行からタイトルを抽出 (# Title 形式)
        title = md_file.stem
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                title = stripped[2:].strip()
                break

        doc = Document(
            id=f"brain-{session_id}-{md_file.stem}",
            content=f"{title}\n\n{content[:2000]}",
            metadata={
                "type": "brain_artifact",
                "ki_name": f"[Session {session_id}] {title}",
                "summary": content[:200].replace("\n", " ").strip(),
                "session_id": session_path.name,
                "artifact": md_file.name,
                "file_path": str(md_file),
            },
        )
        docs.append(doc)
    return docs


# PURPOSE: 汎用 .md ドキュメントを Document に変換 (KI 構造不要)
def parse_generic_documents(dir_path: Path, doc_type: str) -> list[Document]:
    """汎用 .md ドキュメントを Document に変換。

    KI 構造 (metadata.json + artifacts/) を前提とせず、
    指定ディレクトリ内の全 .md ファイルを再帰的にパースする。
    _src/, __pycache__/, .git/ 等は除外。

    Args:
        dir_path: スキャン対象ディレクトリ
        doc_type: metadata の type フィールド値 (kernel, horos, workflow 等)

    Returns:
        Document のリスト
    """
    docs = []
    if not dir_path.exists():
        return docs

    for md_file in sorted(dir_path.rglob("*.md")):
        # 除外ディレクトリチェック
        parts = set(md_file.relative_to(dir_path).parts)
        if parts & _EXCLUDE_DIRS:
            continue

        try:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:  # noqa: BLE001
            continue
        if not content.strip():
            continue

        # 先頭行からタイトルを抽出 (# Title 形式)
        title = md_file.stem
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                title = stripped[2:].strip()
                break

        # ディレクトリ内の相対パスで一意な ID を生成
        rel_path = md_file.relative_to(dir_path)
        doc_id = f"doc-{doc_type}-{str(rel_path.with_suffix('')).replace('/', '-').replace(' ', '_')}"

        doc = Document(
            id=doc_id,
            content=f"{title}\n\n{content[:2000]}",
            metadata={
                "type": "generic_doc",
                "doc_type": doc_type,
                "title": title,
                "file_path": str(md_file),
                "ki_name": f"[{doc_type}] {title}",
                "summary": content[:200].replace("\n", " ").strip(),
            },
        )
        docs.append(doc)

    return docs


# PURPOSE: KI + brain + 汎用ドキュメントの全 Document を統合返却
def get_all_documents() -> list[Document]:
    """KI ディレクトリ、brain セッション、汎用ドキュメントの全 Document を統合返却。

    各 KNOWLEDGE_DIRS を走査し、brain ディレクトリは parse_brain_session()、
    それ以外は parse_ki_directory() でパースする。
    加えて GENERIC_DOCUMENT_DIRS を parse_generic_documents() でパースする。
    """
    docs = []
    seen_paths: set[Path] = set()

    # 1. KI + brain ディレクトリ (既存)
    for knowledge_dir in KNOWLEDGE_DIRS:
        if not knowledge_dir.exists():
            continue

        # brain ディレクトリの判定
        is_brain = knowledge_dir.name == "brain"

        for subdir in sorted(knowledge_dir.iterdir()):
            if not subdir.is_dir():
                continue
            resolved = subdir.resolve()
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)

            if is_brain:
                docs.extend(parse_brain_session(subdir))
            else:
                docs.extend(parse_ki_directory(subdir))

    # 2. 汎用ドキュメントディレクトリ (新規)
    for dir_path, doc_type in GENERIC_DOCUMENT_DIRS:
        resolved = dir_path.resolve()
        if resolved in seen_paths:
            continue
        seen_paths.add(resolved)
        generic_docs = parse_generic_documents(dir_path, doc_type)
        docs.extend(generic_docs)

    return docs


# PURPOSE: Get all KI directories from all configured sources
def get_ki_directories() -> list[Path]:
    """Get all KI directories from all configured knowledge sources.

    Scans KNOWLEDGE_DIRS (multiple paths) and returns all subdirectories
    that could contain KI data. Deduplicates by resolved path.
    """
    seen: set[Path] = set()
    dirs: list[Path] = []

    for knowledge_dir in KNOWLEDGE_DIRS:
        if not knowledge_dir.exists():
            continue
        for d in knowledge_dir.iterdir():
            if d.is_dir():
                resolved = d.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    dirs.append(d)

    return sorted(dirs)


# PURPOSE: Ingest documents to Sophia index using real embeddings (returns count)
def ingest_to_sophia(docs: list[Document], save_path: str = None) -> int:
    """Ingest documents to Sophia index using VertexEmbedder (3072d).

    Args:
        docs: Documents to ingest
        save_path: If provided, save the index to this path after ingestion
    """
    from mekhane.symploke.adapters.vector_store import VectorStore
    from mekhane.symploke.indices.sophia import SophiaIndex
    from mekhane.symploke.embedder_factory import get_embed_fn, get_dimension

    adapter = VectorStore()
    dim = get_dimension()
    embed_fn = get_embed_fn()
    index = SophiaIndex(adapter, "sophia", dimension=dim, embed_fn=embed_fn)
    index.initialize()

    count = index.ingest(docs)
    print(f"Ingested {count} documents to Sophia (VertexEmbedder, {dim}d)")

    if save_path:
        adapter.save(save_path)
        print(f"💾 Saved index to: {save_path}")

    return count


# PURPOSE: Sophia 差分インデックス — 変更ファイルのみ re-embed
def incremental_rebuild_sophia(index_path: str = None) -> dict:
    """manifest ベースの差分インデックス更新。

    1. 既存 pkl の manifest (file_path → mtime) を読み込む
    2. 現在のファイルスキャンで mtime を比較
    3. 変更/新規ファイルのみ re-embed、削除ファイルを除去
    4. manifest を更新して保存

    Returns:
        dict: {added: int, updated: int, deleted: int, unchanged: int, total: int}
    """
    from mekhane.symploke.adapters.vector_store import VectorStore
    from mekhane.symploke.indices.sophia import SophiaIndex
    from mekhane.symploke.embedder_factory import get_embed_fn, get_dimension

    if index_path is None:
        index_path = str(DEFAULT_INDEX_PATH)

    adapter = VectorStore()
    stats = {"added": 0, "updated": 0, "deleted": 0, "unchanged": 0, "total": 0}

    # 1. pkl ロード → manifest 取得
    old_manifest: dict[str, float] = {}
    if Path(index_path).exists():
        old_manifest = adapter.load(index_path) or {}
    else:
        # pkl なし → フル再構築
        print("📦 No existing index — full rebuild")
        all_docs = get_all_documents()
        ingest_to_sophia(all_docs, save_path=index_path)
        # manifest を構築して保存し直す
        new_manifest = _build_sophia_manifest()
        adapter.save(index_path, manifest=new_manifest)
        stats["added"] = len(all_docs)
        stats["total"] = len(all_docs)
        return stats

    # 2. 現在のファイル mtime スキャン
    current_manifest = _build_sophia_manifest()

    # 3. 差分計算
    old_files = set(old_manifest.keys())
    current_files = set(current_manifest.keys())

    deleted_files = old_files - current_files
    new_files = current_files - old_files
    common_files = old_files & current_files
    modified_files = {
        f for f in common_files
        if current_manifest[f] != old_manifest[f]
    }
    unchanged_files = common_files - modified_files

    stats["deleted"] = len(deleted_files)
    stats["added"] = len(new_files)
    stats["updated"] = len(modified_files)
    stats["unchanged"] = len(unchanged_files)

    if not deleted_files and not new_files and not modified_files:
        print("✅ Sophia index is up-to-date (0 changes)")
        stats["total"] = adapter.count()
        return stats

    print(f"📊 Sophia diff: +{len(new_files)} new, ~{len(modified_files)} modified, -{len(deleted_files)} deleted, ={len(unchanged_files)} unchanged")

    # 4a. 削除: deleted + modified のエントリを除去
    files_to_remove = deleted_files | modified_files
    for fp in files_to_remove:
        adapter.delete_by_source(fp)

    # 4b. 追加: new + modified のファイルを Document 化して embed
    files_to_add = new_files | modified_files
    if files_to_add:
        # 対象ファイルの Document 生成
        new_docs = _docs_for_files(files_to_add)
        if new_docs:
            dim = get_dimension()
            embed_fn = get_embed_fn()

            # 個別 embed して追加
            import numpy as np
            for doc in new_docs:
                try:
                    vec = embed_fn(doc.content)
                    meta = {**doc.metadata, "source": doc.metadata.get("file_path", ""), "doc_id": doc.id}
                    adapter.add_vectors(np.array([vec]), metadata=[meta])
                except Exception as e:  # noqa: BLE001
                    print(f"  ⚠️ Embed error for {doc.id}: {e}")

            print(f"  ✅ Added/updated {len(new_docs)} documents")

    # 5. manifest 更新して保存
    adapter.save(index_path, manifest=current_manifest)
    stats["total"] = adapter.count()
    print(f"💾 Saved ({stats['total']} vectors)")
    return stats


# PURPOSE: Sophia 用の manifest (全対象ファイルの mtime) を構築
def _build_sophia_manifest() -> dict[str, float]:
    """Sophia 対象ファイル全体の file_path → mtime マッピングを返す。"""
    manifest: dict[str, float] = {}

    # KI ディレクトリ
    for knowledge_dir in KNOWLEDGE_DIRS:
        if not knowledge_dir.exists():
            continue
        for md_file in knowledge_dir.rglob("*.md"):
            parts = set(md_file.relative_to(knowledge_dir).parts)
            if parts & _EXCLUDE_DIRS:
                continue
            fp = str(md_file)
            try:
                manifest[fp] = md_file.stat().st_mtime
            except OSError:
                pass

    # 汎用ドキュメント
    for dir_path, _ in GENERIC_DOCUMENT_DIRS:
        if not dir_path.exists():
            continue
        for md_file in dir_path.rglob("*.md"):
            parts = set(md_file.relative_to(dir_path).parts)
            if parts & _EXCLUDE_DIRS:
                continue
            fp = str(md_file)
            if fp not in manifest:
                try:
                    manifest[fp] = md_file.stat().st_mtime
                except OSError:
                    pass

    return manifest


# PURPOSE: 指定ファイルパスに属する Document のみ生成
def _docs_for_files(file_paths: set[str]) -> list[Document]:
    """指定ファイルパスに対応する Document のみを生成する。"""
    all_docs = get_all_documents()
    return [
        d for d in all_docs
        if d.metadata.get("file_path", "") in file_paths
    ]


# PURPOSE: Load a previously saved Sophia index
def load_sophia_index(load_path: str):
    """Load a previously saved Sophia index."""
    from mekhane.symploke.adapters.vector_store import VectorStore

    adapter = VectorStore()
    adapter.load(load_path)
    print(f"📂 Loaded index from: {load_path} ({adapter.count()} vectors)")
    return adapter


# PURPOSE: Search using a loaded adapter directly
def search_loaded_index(adapter, query: str, top_k: int = 5):
    """Search using a loaded adapter directly."""
    from mekhane.symploke.embedder_factory import get_embed_fn
    
    # Encode query using the centralized embedder
    embed_fn = get_embed_fn()
    query_vec = embed_fn(query)
    
    results = adapter.search(query_vec, k=top_k)
    return results


# Configurable via env — defaults to mneme indices
from mekhane.paths import INDEX_DIR
DEFAULT_INDEX_PATH = Path(
    os.environ.get(
        "HGK_SOPHIA_INDEX",
        str(INDEX_DIR / "sophia.pkl"),
    )
)


# PURPOSE: /boot 統合 API: コンテキストに基づいて関連 KI を自動プッシュ
def get_boot_ki(context: str = None, mode: str = "standard") -> dict:
    """
    /boot 統合 API: コンテキストに基づいて関連 KI を自動プッシュ

    Args:
        context: 現在のセッションコンテキスト（Handoff の主題や目的など）
        mode: "fast" (0件), "standard" (3件), "detailed" (5件)

    Returns:
        dict: {
            "ki_items": List[dict],  # 関連 KI リスト
            "count": int
        }
    """
    # モードによる件数
    top_k = {"fast": 0, "standard": 3, "detailed": 5}.get(mode, 3)

    if top_k == 0 or not context:
        return {"ki_items": [], "count": 0}

    # インデックス読み込み
    if not DEFAULT_INDEX_PATH.exists():
        return {"ki_items": [], "count": 0}

    adapter = load_sophia_index(str(DEFAULT_INDEX_PATH))

    # 検索
    results = search_loaded_index(adapter, context, top_k=top_k)

    # 結果を整形
    ki_items = []
    for r in results:
        ki_items.append(
            {
                "ki_name": r.metadata.get("ki_name", "Unknown"),
                "summary": r.metadata.get("summary", ""),
                "artifact": r.metadata.get("artifact", ""),
                "score": r.score,
                "file_path": r.metadata.get("file_path", ""),
            }
        )

    return {"ki_items": ki_items, "count": len(ki_items)}


# PURPOSE: /boot 用の KI 出力フォーマット
def format_ki_output(result: dict) -> str:
    """
    /boot 用の KI 出力フォーマット
    """
    if not result["ki_items"]:
        return "📚 関連する知識: なし"

    lines = [f"📚 今日関連しそうな知識 ({result['count']}件):"]

    for item in result["ki_items"]:
        ki_name = item["ki_name"]
        summary = (
            item["summary"][:60] + "..."
            if len(item["summary"]) > 60
            else item["summary"]
        )
        lines.append(f"  • [{ki_name}] {summary}")

    return "\n".join(lines)


# PURPOSE: main の処理
def main():
    parser = argparse.ArgumentParser(description="Ingest KIs to Sophia index")
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse only, don't ingest"
    )
    parser.add_argument(
        "--save", action="store_true", help="Save index after ingestion (default: True)"
    )
    parser.add_argument(
        "--no-save", action="store_true", help="Don't save index after ingestion"
    )
    parser.add_argument(
        "--load", action="store_true", help="Load existing index and show stats"
    )
    parser.add_argument("--search", type=str, help="Search query (requires --load)")
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Only ingest new/modified KIs (diff mode)",
    )
    args = parser.parse_args()

    # Ensure index directory exists
    DEFAULT_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Load mode
    if args.load:
        if not DEFAULT_INDEX_PATH.exists():
            print(f"❌ Index not found: {DEFAULT_INDEX_PATH}")
            return
        adapter = load_sophia_index(str(DEFAULT_INDEX_PATH))

        if args.search:
            results = search_loaded_index(adapter, args.search, top_k=5)
            print(f"\n=== Search: {args.search} ===")
            for r in results:
                print(f"Score: {r.score:.3f} | {r.metadata.get('doc_id', 'N/A')}")
                print(f"  KI: {r.metadata.get('ki_name', 'N/A')}")
                print(f"  Summary: {r.metadata.get('summary', 'N/A')[:80]}...")
                print()
        return

    # Ingest mode — KI + brain を統合パース
    all_docs = get_all_documents()
    ki_count = sum(1 for d in all_docs if d.metadata.get("type") == "knowledge_item")
    brain_count = sum(1 for d in all_docs if d.metadata.get("type") == "brain_artifact")
    generic_count = sum(1 for d in all_docs if d.metadata.get("type") == "generic_doc")
    print(f"Found {len(all_docs)} documents (KI: {ki_count}, Brain: {brain_count}, Generic: {generic_count})")

    # 汎用ドキュメントの内訳
    if generic_count > 0:
        from collections import Counter
        type_counts = Counter(d.metadata.get("doc_type", "?") for d in all_docs if d.metadata.get("type") == "generic_doc")
        print(f"  Generic breakdown: {dict(type_counts)}")

    for doc in all_docs:
        print(f"  → {doc.id}")

    print(f"\nTotal: {len(all_docs)} documents")

    # Incremental mode: filter out existing docs
    if args.incremental and DEFAULT_INDEX_PATH.exists():
        adapter = load_sophia_index(str(DEFAULT_INDEX_PATH))
        existing_count = adapter.count()

        # Get existing doc IDs from adapter metadata
        existing_ids = set()
        if existing_count > 0:
            # Use a broad search to get all existing docs
            dummy_vec = adapter.encode([""])[0]
            existing_results = adapter.search(dummy_vec, k=existing_count)
            existing_ids = {r.metadata.get("doc_id", "") for r in existing_results}

        # Filter to only new docs
        new_docs = [d for d in all_docs if d.id not in existing_ids]
        skipped = len(all_docs) - len(new_docs)

        print(
            f"\n[Incremental] Existing: {len(existing_ids)}, New: {len(new_docs)}, Skipped: {skipped}"
        )

        if not new_docs:
            print("No new documents to ingest.")
            return

        all_docs = new_docs

    if args.dry_run:
        print("\n[Dry run] Would ingest documents")
        return

    # Save by default unless --no-save
    save_path = None if args.no_save else str(DEFAULT_INDEX_PATH)
    ingest_to_sophia(all_docs, save_path=save_path)
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
