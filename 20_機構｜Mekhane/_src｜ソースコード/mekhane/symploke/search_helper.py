#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/ A0→知識管理が必要→search_helper が担う
"""
Symploke Search Helper - 統合検索の簡易インターフェース

Usage:
    python search_helper.py "query"              # 両源から検索
    python search_helper.py "query" --sophia     # Sophia のみ
    python search_helper.py "query" --kairos     # Kairos のみ
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mekhane.symploke.adapters.vector_store import VectorStore
from mekhane.paths import INDEX_DIR

SOPHIA_INDEX_PATH = INDEX_DIR / "sophia.pkl"
KAIROS_INDEX_PATH = INDEX_DIR / "kairos.pkl"


# PURPOSE: Load an adapter from a pickle file
def load_adapter(path: Path) -> VectorStore:
    """Load an adapter from a pickle file."""
    adapter = VectorStore()
    adapter.load(str(path))
    return adapter


# PURPOSE: Search using an adapter
def search_index(adapter: VectorStore, query: str, top_k: int = 5):
    """Search using an adapter with VertexEmbedder query encoding."""
    from mekhane.symploke.embedder_factory import get_embed_fn
    embed_fn = get_embed_fn()
    query_vec = embed_fn(query)
    return adapter.search(query_vec, k=top_k)


# PURPOSE: 統合検索: Sophia + Kairos を横断検索
def unified_search(query: str, sources: list[str] = None, top_k: int = 5):
    """
    統合検索: Sophia + Kairos を横断検索

    Args:
        query: 検索クエリ
        sources: ["sophia", "kairos"] または None (両方)
        top_k: 各源から取得する件数

    Returns:
        list of (source, result) tuples
    """
    sources = sources or ["sophia", "kairos"]
    all_results = []

    if "sophia" in sources and SOPHIA_INDEX_PATH.exists():
        sophia = load_adapter(SOPHIA_INDEX_PATH)
        results = search_index(sophia, query, top_k)
        for r in results:
            all_results.append(("sophia", r))

    if "kairos" in sources and KAIROS_INDEX_PATH.exists():
        kairos = load_adapter(KAIROS_INDEX_PATH)
        results = search_index(kairos, query, top_k)
        for r in results:
            all_results.append(("kairos", r))

    # スコア順でソート
    all_results.sort(key=lambda x: x[1].score, reverse=True)
    return all_results[: top_k * 2]


# PURPOSE: main の処理
def main():
    parser = argparse.ArgumentParser(description="Symploke unified search")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--sophia", action="store_true", help="Search Sophia only")
    parser.add_argument("--kairos", action="store_true", help="Search Kairos only")
    parser.add_argument(
        "--top-k", type=int, default=5, help="Number of results per source"
    )
    args = parser.parse_args()

    # Determine sources
    sources = []
    if args.sophia:
        sources.append("sophia")
    if args.kairos:
        sources.append("kairos")
    if not sources:
        sources = ["sophia", "kairos"]

    print(f"🔍 Search: {args.query}")
    print(f"   Sources: {', '.join(sources)}")
    print()

    results = unified_search(args.query, sources, args.top_k)

    if not results:
        print("No results found.")
        return

    print(f"=== Results ({len(results)}) ===")
    for source, r in results:
        if source == "sophia":
            label = r.metadata.get("ki_name", "N/A")
            detail = r.metadata.get("artifact", "")
        else:
            label = r.metadata.get("primary_task", "N/A")
            detail = r.metadata.get("timestamp", "")

        print(f"[{source}] {r.score:.3f} | {label}")
        if detail:
            print(f"         → {detail}")


if __name__ == "__main__":
    main()
