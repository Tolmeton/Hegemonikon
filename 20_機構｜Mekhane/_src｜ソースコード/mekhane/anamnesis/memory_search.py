#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/anamnesis/
"""
PROOF: [L2/インフラ]

P3 → 記憶の横断検索が必要
   → 意味記憶+エピソード記憶の統合
   → memory_search が担う

Q.E.D.

---

統合長期記憶検索 API — M8 Anamnēsis
====================================

意味記憶（ベクトル検索）とエピソード記憶（FTS 検索）を
GnosisIndex ファサード経由で統合した検索 API。

Usage:
    python memory_search.py "query"           # ハイブリッド検索
    python memory_search.py --vector "query"  # ベクトル検索のみ
    python memory_search.py --fts "query"     # FTS 検索のみ
"""

import sys
from pathlib import Path
from typing import Optional


# PURPOSE: GnosisIndex を遅延ロードで取得
def _get_index(table_name: str = "gnosis"):
    """GnosisIndex を取得する。"""
    from mekhane.anamnesis.index import GnosisIndex

    return GnosisIndex(table_name=table_name)


# PURPOSE: FTS 検索（GnosisIndex 経由）
def search_fts(query: str, limit: int = 3) -> str:
    """GnosisIndex 経由の全文検索。"""
    try:
        idx = _get_index()
        results = idx.search_fts(query, k=limit)
        if not results:
            return "  (該当なし)"
        lines = []
        for r in results:
            title = r.get("title", r.get("filename", "?"))
            preview = r.get("content_preview", r.get("text", ""))[:200]
            lines.append(f"  [{title}] {preview}")
        return "\n".join(lines)
    except Exception as e:  # noqa: BLE001
        return f"[ERROR] FTS search failed: {e}"


# PURPOSE: ベクトル検索（GnosisIndex 経由）
def search_vector(query: str, limit: int = 3,
                  embedder=None) -> str:
    """GnosisIndex 経由のベクトル検索。

    embedder が None の場合は FTS にフォールバック。
    """
    try:
        if embedder is None:
            # エンベッダ未指定 → FTS で代替
            return search_fts(query, limit)
        idx = _get_index()
        query_vector = embedder(query)
        results = idx.search(query, query_vector=query_vector, k=limit)
        if not results:
            return "  (該当なし)"
        lines = []
        for r in results:
            title = r.get("title", r.get("filename", "?"))
            score = r.get("_distance", "?")
            lines.append(f"  [{title}] (score: {score})")
        return "\n".join(lines)
    except Exception as e:  # noqa: BLE001
        return f"[ERROR] Vector search failed: {e}"


# PURPOSE: モジュール検索（GnosisIndex 経由）
def search_modules(query: str, limit: int = 3) -> str:
    """GnosisIndex の dev_modules テーブルを検索。"""
    try:
        idx = _get_index(table_name="dev_modules")
        if not idx.table_exists():
            return "  (モジュールインデックス未構築)"
        results = idx.search_fts(query, k=limit)
        if not results:
            return "  (該当なし)"
        lines = []
        for r in results:
            title = r.get("title", r.get("filename", "?"))
            cat = r.get("category", "?")
            lines.append(f"  [{title}] (category: {cat})")
        return "\n".join(lines)
    except Exception as e:  # noqa: BLE001
        return f"[ERROR] Module search failed: {e}"


# PURPOSE: ハイブリッド検索（全ソースを実行）
def hybrid_search(query: str) -> str:
    """ハイブリッド検索（全ソースを実行）"""
    output = []

    output.append("[Hegemonikon] M8 Anamnēsis — 統合長期記憶検索")
    output.append(f"  クエリ: {query}")
    output.append("")

    # FTS 検索（エピソード記憶）
    output.append("=== エピソード記憶（FTS）===")
    fts_result = search_fts(query)
    output.append(fts_result)

    # ベクトル検索（意味記憶）
    output.append("\n=== 意味記憶（ベクトル検索）===")
    vector_result = search_vector(query)
    output.append(vector_result)

    # モジュール検索（開発用モジュール）
    output.append("\n=== 開発用モジュール ===")
    module_result = search_modules(query)
    output.append(module_result)

    return "\n".join(output)


# PURPOSE: CLI エントリポイント — 知識基盤の直接実行
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    mode = "hybrid"
    query_start = 1

    if sys.argv[1] == "--vector":
        mode = "vector"
        query_start = 2
    elif sys.argv[1] == "--fts":
        mode = "fts"
        query_start = 2

    query = " ".join(sys.argv[query_start:])

    if not query:
        print("Error: No query provided")
        sys.exit(1)

    if mode == "vector":
        print(search_vector(query))
    elif mode == "fts":
        print(search_fts(query))
    else:
        print(hybrid_search(query))


if __name__ == "__main__":
    main()
