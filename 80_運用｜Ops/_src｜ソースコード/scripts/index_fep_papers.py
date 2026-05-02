#!/usr/bin/env python3
# PROOF: [L3/ユーティリティ] <- scripts/ O4→収集した論文をGnōsisに投入
# PURPOSE: collected_papers.json → Gnōsis FAISS インデックスへの投入
"""
FEP Papers → Gnōsis Indexer
=============================

collect_fep_papers.py で収集した論文を Gnōsis (FAISS) に投入する。
GnosisIndex.add_papers() の dedupe 機構を活用。

既存テーブルのスキーマ:
    primary_key, title, source, abstract, content, authors,
    doi, arxiv_id, url, citations, vector

Usage:
    # ドライラン（変換のみ、投入しない）
    python scripts/index_fep_papers.py --dry-run

    # 本番実行
    python scripts/index_fep_papers.py

    # 投入後にインデックス統計を表示
    python scripts/index_fep_papers.py --stats
"""

import sys
import json
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mekhane.anamnesis.index import GnosisIndex, Embedder
from mekhane.anamnesis.models.paper import Paper

# 入力ファイル
COLLECTED_FILE = PROJECT_ROOT / "data" / "fep_papers" / "collected_papers.json"


def build_papers(collected: list[dict]) -> list[Paper]:
    """collected_papers.json → Paper オブジェクトのリストに変換"""
    papers: list[Paper] = []
    skipped = 0

    for entry in collected:
        abstract = entry.get("abstract") or ""
        if len(abstract) < 20:
            skipped += 1
            continue

        paper_id = entry.get("paper_id", "")
        doi = entry.get("doi") or ""
        arxiv_id = entry.get("arxiv_id") or ""
        authors = entry.get("authors", [])
        title = entry.get("title", "")

        # source_id: DOI > arXiv > paper_id
        source_id = doi or arxiv_id or paper_id

        paper = Paper(
            id=paper_id,
            source="semantic_scholar",
            source_id=source_id,
            title=title,
            abstract=abstract[:2000],
            content=f"{title} {abstract[:1000]}",
            authors=", ".join(authors[:10]) if authors else "",
            doi=doi,
            arxiv_id=arxiv_id,
            url=entry.get("url", ""),
            citations=entry.get("citation_count", 0) or 0,
        )
        papers.append(paper)

    print(f"  変換: {len(papers)} papers (abstract 不足で {skipped} skip)")
    return papers


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Papers → Gnōsis Indexer (FAISS)")
    parser.add_argument("--dry-run", action="store_true", help="変換のみ、投入しない")
    parser.add_argument("--stats", action="store_true", help="投入後に統計表示")
    parser.add_argument("--input", type=str, default=None, help="入力 JSON ファイルパス")
    args = parser.parse_args()

    input_file = Path(args.input) if args.input else COLLECTED_FILE
    if not input_file.exists():
        print(f"❌ {input_file} が見つかりません。先に collect スクリプトを実行してください。")
        sys.exit(1)

    # 読み込み
    collected = json.loads(input_file.read_text())
    print(f"📂 読込: {len(collected)} papers from {input_file.name}")

    # Paper オブジェクト構築
    papers = build_papers(collected)

    if args.dry_run:
        print(f"\n🔍 DRY RUN — 投入しません")
        print(f"\n  サンプル (top 5):")
        for p in papers[:5]:
            print(f"    {p.citations:>5}c | {p.title[:60]}")
            print(f"      Key: {p.primary_key}")
            print(f"      Abstract: {p.abstract[:80]}...")
        return

    if not papers:
        print("  ✅ 変換対象なし。終了。")
        return

    # GnosisIndex 経由で投入 (dedupe=True で重複排除)
    index = GnosisIndex()
    print(f"\n🚀 投入中... ({len(papers)} papers, dedupe=True)")
    added = index.add_papers(papers, dedupe=True)
    print(f"\n✅ 投入完了: {added} papers added to Gnōsis")

    # 統計
    if args.stats or True:
        stats = index.stats()
        print(f"\n📊 Gnōsis Index Stats:")
        for k, v in stats.items():
            print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
