#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/ A0→知識管理が必要→handoff_search が担う
"""
Handoff & Conversation Search - /boot 時に関連 Handoff と会話ログを検索

Usage:
    python handoff_search.py "query"                # Similar handoffs + conversations
    python handoff_search.py --latest               # Show latest handoff
    python handoff_search.py --recent 3             # Show 3 most recent
"""

import sys
import argparse
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mekhane.symploke.kairos_ingest import (
    get_handoff_files,
    parse_handoff,
    parse_conversation,
)
from mekhane.symploke.adapters.vector_store import VectorStore
from mekhane.symploke.indices import Document

from mekhane.paths import INDEX_DIR

# Handoff インデックスの永続化パス
HANDOFF_INDEX_PATH = INDEX_DIR / "handoffs.pkl"
# 会話ログインデックスの永続化パス (Kairos と共有)
CONVERSATION_INDEX_PATH = INDEX_DIR / "kairos.pkl"


# PURPOSE: クエリ文字列を embedder_factory 経由で 1d ベクトル化（VectorStore.encode は model_name 必須のため廃止）
def _query_embedding_vector(query: str):
    """テキストを VectorStore.search 用の 1d float32 ベクトルに変換する。"""
    import numpy as np
    from mekhane.symploke.embedder_factory import get_embed_fn
    v = get_embed_fn()(query)
    arr = np.asarray(v, dtype=np.float32)
    if arr.ndim > 1:
        arr = arr.reshape(-1)
    return arr


# PURPOSE: Load handoffs as documents (遅延パース対応)
def load_handoffs(workspace: str = None, project: str = None, limit: int = None) -> List[Document]:
    """Load handoffs as documents.

    ファイルリストを先に取得し、limit でスライスしてからパースする。
    全件パースを避けるため、可能な限り limit を指定すること。

    Args:
        workspace: ワークスペースタグでフィルタ (None=全件)。
        project: プロジェクトタグでフィルタ (None=全件)。
        limit: パースする最大件数 (None=全件)。ファイルは日付降順。
    """
    files = get_handoff_files(workspace=workspace)
    if limit is not None:
        files = files[:limit]
    docs = [parse_handoff(f) for f in files]
    if project:
        docs = [d for d in docs if d.metadata.get("project") == project]
    return docs


# PURPOSE: Build and save handoff index
def build_handoff_index(docs: List[Document] = None) -> VectorStore:
    """Build and save handoff index using VertexEmbedder (3072d)."""
    from mekhane.symploke.embedder_factory import get_embedder, get_dimension

    if docs is None:
        docs = load_handoffs()

    if not docs:
        return None

    adapter = VectorStore()
    embedder = get_embedder()
    dim = get_dimension()

    # Encode all docs with VertexEmbedder
    texts = [d.content for d in docs]
    doc_vectors_list = embedder.embed_batch(texts)
    import numpy as np
    doc_vectors = np.array(doc_vectors_list, dtype=np.float32)

    # Create index
    adapter.create_index(dimension=dim)
    metadata = [
        {
            "doc_id": d.id,
            "idx": i,
            "primary_task": d.metadata.get("primary_task", ""),
            "file_path": d.metadata.get("file_path", ""),  # 遅延パース用
        }
        for i, d in enumerate(docs)
    ]
    adapter.add_vectors(doc_vectors, metadata=metadata)

    # Save
    HANDOFF_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    adapter.save(str(HANDOFF_INDEX_PATH))
    print(f"💾 Handoff index saved: {len(docs)} docs ({dim}d)")

    return adapter


# PURPOSE: Load saved handoff index
def load_handoff_index() -> VectorStore:
    """Load saved handoff index."""
    adapter = VectorStore()
    adapter.load(str(HANDOFF_INDEX_PATH))
    return adapter


# スコア調整設定
SCORE_BOOST = {
    "handoff": 0.08,  # 構造化された総括は価値が高い
    "conversation": 0.0,  # 生の会話は基準値
    "conversation_chunk": 0.0,  # チャンクも基準値
}


# PURPOSE: タイプに基づいてスコアを調整する。
def adjust_score(score: float, doc_type: str) -> float:
    """タイプに基づいてスコアを調整する。

    Handoff は構造化された総括なので、生の会話より価値が高いとみなす。
    時間減衰は実装しない（原則・洞察の価値は時間に依存しない）。
    """
    boost = SCORE_BOOST.get(doc_type, 0.0)
    return min(1.0, score + boost)


# PURPOSE: Handoff からキーワードを抽出（Proactive Recall 用）
def extract_keywords(doc: Document, max_keywords: int = 5) -> List[str]:
    """Handoff からキーワードを抽出（Proactive Recall 用）"""
    content = doc.content
    keywords = []

    # primary_task をキーワードとして抽出
    primary_task = doc.metadata.get("primary_task", "")
    if primary_task:
        keywords.append(primary_task)

    # 日本語の重要そうなキーワードを抽出（簡易版）
    import re

    # カタカナ語を抽出
    katakana = re.findall(r"[ァ-ヴー]{3,}", content)
    keywords.extend(katakana[:3])

    # 英語の重要そうな語を抽出
    english = re.findall(r"[A-Z][a-z]+(?:[A-Z][a-z]+)*", content)
    keywords.extend(english[:3])

    return list(set(keywords))[:max_keywords]


# PURPOSE: Search handoffs by semantic similarity using cached index
#   Kalon: インデックスが存在すれば全件パースを回避し、ヒットしたファイルだけパースする
def search_handoffs(query: str, top_k: int = 5, workspace: str = None, project: str = None) -> List[Tuple[Document, float]]:
    """Search handoffs by semantic similarity using cached index.

    インデックスが存在する場合は全件パースを行わず、
    インデックス検索でヒットしたファイルのみを遅延パースする。

    Args:
        query: 検索クエリ
        top_k: 返却件数
        workspace: ワークスペースタグでフィルタ (None=全件)。
        project: プロジェクトタグでフィルタ (None=全件)。
    """
    try:
        if HANDOFF_INDEX_PATH.exists():
            # インデックスが存在 → 全件パース不要
            adapter = load_handoff_index()
            query_vector = _query_embedding_vector(query)
            results = adapter.search(query_vector, k=top_k)

            # ヒットした file_path から遅延パース
            matched = []
            for r in results:
                file_path = r.metadata.get("file_path")
                if file_path and Path(file_path).exists():
                    doc = parse_handoff(Path(file_path))
                    matched.append((doc, r.score))
                else:
                    # file_path がメタデータにない旧インデックス → idx フォールバック
                    # この場合のみ全件パースが必要
                    docs = load_handoffs(workspace=workspace, project=project)
                    idx = r.metadata.get("idx", r.id)
                    if idx < len(docs):
                        matched.append((docs[idx], r.score))
                    break  # 旧形式なら以降も同じなので抜ける

            return matched
        else:
            # インデックスなし → ビルドして検索
            docs = load_handoffs(workspace=workspace, project=project)
            if not docs:
                return []
            adapter = build_handoff_index(docs)
            if adapter is None:
                # Embedder 初期化失敗 — 日付順フォールバック
                return [(d, 0.5) for d in docs[:top_k]]

            query_vector = _query_embedding_vector(query)
            results = adapter.search(query_vector, k=top_k)
            matched = []
            for r in results:
                idx = r.metadata.get("idx", r.id)
                if idx < len(docs):
                    matched.append((docs[idx], r.score))
            return matched
    except Exception:  # noqa: BLE001
        # Embedder/ベクトル検索が使えない場合は日付順で返す（遅延パース）
        docs = load_handoffs(workspace=workspace, project=project, limit=top_k)
        return [(d, 0.5) for d in docs]


# PURPOSE: /boot 統合 API: モードに応じた Handoff と会話ログを返す
def _parse_handoff_timestamp(doc: "Document") -> datetime:
    """Handoff の timestamp メタデータを datetime に変換する。

    パース不可の場合は file_path の mtime にフォールバック。
    """
    ts_str = doc.metadata.get("timestamp", "")
    # 標準形式: YYYY-MM-DDTHH:MM:SS
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(ts_str, fmt)
        except (ValueError, TypeError):
            continue
    # フォールバック: ファイルの mtime
    file_path = doc.metadata.get("file_path", "")
    if file_path and Path(file_path).exists():
        mtime = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mtime)
    # 最終フォールバック: 遠い過去
    return datetime(2000, 1, 1)


def get_boot_handoffs(mode: str = "standard", context: str = None, workspace: str = None, project: str = None) -> dict:
    """
    /boot 統合 API: モードに応じた Handoff と会話ログを返す

    時間窓ベース:
      - fast (/boot-): 最新1件のみ
      - standard (/boot): 24H 以内の全 Handoff
      - detailed (/boot+): 72H 以内の全 Handoff

    Args:
        mode: "fast" (/boot-), "standard" (/boot), "detailed" (/boot+)
        context: 現在のコンテキスト（検索クエリに使用）
        workspace: ワークスペースタグでフィルタ (None=全件)。例: "fm", "hgk"
        project: プロジェクトタグでフィルタ (None=全件)。例: "Ergon"

    Returns:
        dict: {
            "latest": Document,           # 最新の Handoff
            "related": List[Document],    # 時間窓内の Handoff (latest 除く)
            "conversations": List[Document],  # 関連する会話ログ
            "count": int                  # 関連件数 (handoff + conversation)
        }
    """
    # モードによる時間窓 (時間)
    time_window_hours = {
        "fast": 0,     # /boot- : 最新のみ
        "standard": 24,   # /boot  : 24H 以内の全 Handoff
        "detailed": 72,   # /boot+ : 72H 以内の全 Handoff
    }.get(mode, 24)

    conv_count = {
        "fast": 0,  # /boot- : なし
        "standard": 2,  # /boot  : 関連会話 2
        "detailed": 5,  # /boot+ : 関連会話 5
    }.get(mode, 2)

    # Kalon: ファイルリストを先に取得し、必要な分だけパースする
    from mekhane.symploke.kairos_ingest import _extract_date_from_filename
    files = get_handoff_files(workspace=workspace)
    if not files:
        return {"latest": None, "related": [], "conversations": [], "count": 0}

    # 最新1件は常にパース
    latest = parse_handoff(files[0])

    # 検索クエリ
    query = context or latest.metadata.get("primary_task", latest.content[:200])

    # 時間窓による Handoff フィルタ — ファイル名日付で事前フィルタし、パースは最小限に
    related = []
    if time_window_hours > 0:
        now = datetime.now()
        cutoff = now - timedelta(hours=time_window_hours)
        # ファイル名から日付を抽出して cutoff 以降のものだけパース
        for f in files[1:]:  # latest は除外
            file_dt = _extract_date_from_filename(f)
            if file_dt >= cutoff:
                related.append(parse_handoff(f))
            else:
                # 日付降順なので cutoff より古いものが出たら打ち切り
                break

    # 関連会話ログ検索 (Kairos Index を使用)
    conversations = []
    if conv_count > 0 and CONVERSATION_INDEX_PATH.exists():
        try:
            adapter = VectorStore()
            adapter.load(str(CONVERSATION_INDEX_PATH))
            query_vec = _query_embedding_vector(query)
            results = adapter.search(query_vec, k=conv_count)

            # ファイルパスからドキュメントを再構築
            for r in results:
                file_path = r.metadata.get("file_path")
                if file_path and Path(file_path).exists():
                    doc = parse_conversation(Path(file_path))
                    # スコア調整を適用
                    adjusted_score = adjust_score(r.score, "conversation")
                    doc.metadata["score"] = adjusted_score
                    doc.metadata["raw_score"] = r.score
                    conversations.append(doc)
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ Conversation search error: {e}")

    # Proactive Recall: 最新 Handoff からキーワードを抽出し、追加検索
    proactive_memories = []
    if mode == "detailed" and latest:
        keywords = extract_keywords(latest)
        if keywords and CONVERSATION_INDEX_PATH.exists():
            try:
                proactive_query = " ".join(keywords[:3])
                adapter = VectorStore()
                adapter.load(str(CONVERSATION_INDEX_PATH))
                query_vec = _query_embedding_vector(proactive_query)
                results = adapter.search(query_vec, k=3)

                for r in results:
                    file_path = r.metadata.get("file_path")
                    if file_path and Path(file_path).exists():
                        # 重複チェック
                        if not any(
                            c.metadata.get("file_path") == file_path
                            for c in conversations
                        ):
                            doc = parse_conversation(Path(file_path))
                            doc.metadata["score"] = adjust_score(
                                r.score, "conversation"
                            )
                            doc.metadata["proactive"] = (
                                True  # Proactive Recall でヒット
                            )
                            proactive_memories.append(doc)
            except Exception as e:  # noqa: BLE001
                pass  # TODO: Add proper error handling

    return {
        "latest": latest,
        "related": related,
        "conversations": conversations,
        "proactive": proactive_memories,  # NEW: Proactive Recall 結果
        "count": len(related) + len(conversations) + len(proactive_memories),
    }


# PURPOSE: /boot 用の出力フォーマット
def format_boot_output(result: dict, verbose: bool = False) -> str:
    """
    /boot 用の出力フォーマット
    """
    lines = []

    if result["latest"]:
        doc = result["latest"]
        lines.append("📋 最新 Handoff:")
        lines.append(f"  ID: {doc.id}")
        lines.append(f"  主題: {doc.metadata.get('primary_task', 'Unknown')}")
        lines.append(f"  時刻: {doc.metadata.get('timestamp', 'Unknown')}")
        if verbose:
            lines.append(f"  内容: {doc.content[:300]}...")
        lines.append("")

        # 🪐 随伴 (Adjunctions) の表示 — 永続メトリクスベース
        try:
            from mekhane.fep.krisis_metrics_store import format_boot_metrics
            boot_metrics = format_boot_metrics()
            lines.append("🪐 " + boot_metrics)
            lines.append("")
        except ImportError:
            pass

    if result.get("related"):
        lines.append(f"🔗 関連 Handoff ({len(result['related'])}件):")
        for doc in result["related"]:
            lines.append(f"  • {doc.metadata.get('primary_task', doc.id)}")
            lines.append(f"    時刻: {doc.metadata.get('timestamp', 'Unknown')}")
        lines.append("")

    # NEW: 会話ログ表示
    if result.get("conversations"):
        lines.append(f"💬 関連する過去の会話 ({len(result['conversations'])}件):")
        for doc in result["conversations"]:
            score = doc.metadata.get("score", 0)
            msg_count = doc.metadata.get("msg_count", 0)
            title = doc.metadata.get("title", doc.id)
            lines.append(f"  • {title} ({msg_count} msgs, score: {score:.2f})")
            lines.append(f"    ID: {doc.id}")
        lines.append("")

    # NEW: Proactive Recall 表示
    if result.get("proactive"):
        lines.append(f"🧠 自動浮上した記憶 ({len(result['proactive'])}件):")
        for doc in result["proactive"]:
            score = doc.metadata.get("score", 0)
            title = doc.metadata.get("title", doc.id)
            lines.append(f"  ✨ {title} (score: {score:.2f})")

    return "\n".join(lines)


# PURPOSE: Show N most recent handoffs (遅延パース)
def show_latest(n: int = 1):
    """Show N most recent handoffs.

    Kalon: ファイルリストをスライスしてからパースする。全件パースしない。
    """
    files = get_handoff_files()[:n]
    for f in files:
        doc = parse_handoff(f)
        print(f"\n{'='*60}")
        print(f"📄 {doc.id}")
        print(f"主題: {doc.metadata.get('primary_task', 'Unknown')}")
        print(f"時刻: {doc.metadata.get('timestamp', 'Unknown')}")
        print("-" * 60)
        print(doc.content[:500] + "..." if len(doc.content) > 500 else doc.content)


# PURPOSE: main の処理
def main():
    parser = argparse.ArgumentParser(description="Search handoffs for /boot")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--latest", action="store_true", help="Show latest handoff")
    parser.add_argument("--recent", type=int, help="Show N most recent handoffs")
    parser.add_argument("-k", type=int, default=3, help="Number of results")
    parser.add_argument(
        "--boot",
        choices=["fast", "standard", "detailed"],
        help="/boot mode: fast (-), standard, detailed (+)",
    )
    parser.add_argument("--context", type=str, help="Context for /boot search")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # /boot mode
    if args.boot:
        result = get_boot_handoffs(mode=args.boot, context=args.context)
        print(format_boot_output(result, verbose=args.verbose))
        return

    if args.latest:
        show_latest(1)
    elif args.recent:
        show_latest(args.recent)
    elif args.query:
        print(f'🔍 Searching: "{args.query}"\n')
        results = search_handoffs(args.query, top_k=args.k)

        if not results:
            print("No matching handoffs found.")
            return

        for doc, score in results:
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"📊 Score: {score:.3f}")
            print(f"📄 {doc.id}")
            print(f"主題: {doc.metadata.get('primary_task', 'Unknown')}")
            print(f"時刻: {doc.metadata.get('timestamp', 'Unknown')}")
            print()
    else:
        # Default: show latest
        show_latest(1)


if __name__ == "__main__":
    main()
