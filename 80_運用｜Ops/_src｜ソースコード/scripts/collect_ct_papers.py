#!/usr/bin/env python3
# PROOF: [L3/ユーティリティ] <- scripts/ O4→圏論×AI論文のバッチ収集
# PURPOSE: Semantic Scholar API で圏論関連論文を体系的に収集
"""
Category Theory Papers Collector
==================================

10カテゴリで圏論×AI/ソフトウェア/認知科学の論文を収集する。

Usage:
    # ドライラン
    python scripts/collect_ct_papers.py --dry-run --stats

    # 本番収集
    python scripts/collect_ct_papers.py

    # 特定カテゴリのみ
    python scripts/collect_ct_papers.py --category "applied_ct"
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from collections import Counter

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mekhane.pks.semantic_scholar import SemanticScholarClient, Paper

# Output
OUTPUT_DIR = PROJECT_ROOT / "data" / "ct_papers"
COLLECTED_FILE = OUTPUT_DIR / "collected_papers.json"
STATS_FILE = OUTPUT_DIR / "collection_stats.json"

# 10 categories — queries use same format as FEP collector
CATEGORIES: dict[str, list[dict]] = {
    "ct_ml_foundations": [
        {"query": "category theory machine learning foundations", "limit": 40},
        {"query": "categorical foundations deep learning", "limit": 30},
        {"query": "functorial machine learning", "limit": 30},
    ],
    "ct_type_theory": [
        {"query": "category theory type theory programming languages", "limit": 30},
        {"query": "categorical semantics programming", "limit": 20},
        {"query": "dependent type theory categorical", "limit": 20},
    ],
    "adjoint_functors": [
        {"query": "adjoint functor application software", "limit": 40},
        {"query": "adjunction category theory computation", "limit": 30},
        {"query": "Galois connection application lattice", "limit": 30},
    ],
    "ct_cognitive": [
        {"query": "category theory cognitive science", "limit": 30},
        {"query": "categorical perception cognition", "limit": 20},
        {"query": "compositional cognition category theory", "limit": 20},
    ],
    "ct_software": [
        {"query": "category theory software engineering compositional", "limit": 30},
        {"query": "categorical design patterns programming", "limit": 20},
        {"query": "monad software engineering practical", "limit": 20},
    ],
    "galois_enriched": [
        {"query": "Galois connection abstract interpretation", "limit": 30},
        {"query": "enriched category theory applications", "limit": 20},
        {"query": "fuzzy logic enriched categories", "limit": 20},
    ],
    "ct_nlp": [
        {"query": "category theory natural language processing", "limit": 30},
        {"query": "compositional distributional semantics categorical", "limit": 20},
        {"query": "DisCoCat categorical linguistics", "limit": 20},
    ],
    "applied_ct": [
        {"query": "applied category theory ACT", "limit": 40},
        {"query": "applied category theory systems", "limit": 30},
        {"query": "categorical systems theory David Spivak", "limit": 20},
    ],
    "ct_fep": [
        {"query": "category theory free energy principle", "limit": 30},
        {"query": "categorical active inference Bayesian", "limit": 20},
        {"query": "functorial Bayesian inference", "limit": 20},
    ],
    "ct_latest": [
        {"query": "category theory artificial intelligence 2024", "limit": 30, "year": (2024, 2026)},
        {"query": "categorical machine learning 2025", "limit": 20, "year": (2024, 2026)},
        {"query": "compositional AI category theory", "limit": 20},
    ],
}


def collect_category(
    client: SemanticScholarClient,
    category: str,
    queries: list[dict],
    existing_ids: set[str],
) -> list[Paper]:
    """1カテゴリ分の論文を収集"""
    category_papers: list[Paper] = []

    for q in queries:
        query_text = q["query"]
        limit = q.get("limit", 20)
        year_range = q.get("year")

        print(f"\n  📚 Query: '{query_text}' (limit={limit})")
        papers = client.search(query_text, limit=limit, year_range=year_range)

        new_count = 0
        for p in papers:
            if p.paper_id not in existing_ids:
                category_papers.append(p)
                existing_ids.add(p.paper_id)
                new_count += 1

        print(f"     → {len(papers)} found, {new_count} new")

    return category_papers


def collect_all(
    categories: list[str] | None = None,
    dry_run: bool = True,
) -> dict:
    """全カテゴリの論文を収集"""
    client = SemanticScholarClient()

    # 既存データの読み込み
    existing_papers: list[dict] = []
    existing_ids: set[str] = set()
    if COLLECTED_FILE.exists():
        existing_papers = json.loads(COLLECTED_FILE.read_text())
        existing_ids = {p["paper_id"] for p in existing_papers}
        print(f"📂 既存データ: {len(existing_papers)} papers")

    # 対象カテゴリ
    target_categories = categories or list(CATEGORIES.keys())

    all_new_papers: list[Paper] = []
    category_stats: dict[str, int] = {}

    for cat in target_categories:
        if cat not in CATEGORIES:
            print(f"⚠️  Unknown category: {cat}")
            continue

        queries = CATEGORIES[cat]
        print(f"\n{'='*60}")
        print(f"📂 Category: {cat} ({len(queries)} queries)")
        print(f"{'='*60}")

        papers = collect_category(client, cat, queries, existing_ids)
        all_new_papers.extend(papers)
        category_stats[cat] = len(papers)

    # 統計
    total_with_abstract = sum(1 for p in all_new_papers if p.has_abstract)
    year_dist = Counter(p.year for p in all_new_papers if p.year)

    stats = {
        "timestamp": datetime.now().isoformat(),
        "new_papers": len(all_new_papers),
        "existing_papers": len(existing_papers),
        "total_papers": len(existing_papers) + len(all_new_papers),
        "with_abstract": total_with_abstract,
        "without_abstract": len(all_new_papers) - total_with_abstract,
        "category_stats": category_stats,
        "year_distribution": dict(sorted(year_dist.items())),
        "api_requests": client._total_requests,
        "authenticated": client.authenticated,
        "dry_run": dry_run,
    }

    print(f"\n{'='*60}")
    print(f"📊 Collection Summary")
    print(f"{'='*60}")
    print(f"  新規: {stats['new_papers']} papers")
    print(f"  既存: {stats['existing_papers']} papers")
    print(f"  合計: {stats['total_papers']} papers")
    print(f"  Abstract あり: {stats['with_abstract']}")
    print(f"  Abstract なし: {stats['without_abstract']}")
    print(f"  API requests: {stats['api_requests']}")
    print(f"\n  Year distribution:")
    for year, count in sorted(year_dist.items()):
        bar = "█" * min(count, 50)
        print(f"    {year}: {count:>3} {bar}")

    # 保存
    if not dry_run:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # 新規論文を追加して保存
        all_paper_dicts = existing_papers + [p.to_dict() for p in all_new_papers]
        COLLECTED_FILE.write_text(
            json.dumps(all_paper_dicts, indent=2, ensure_ascii=False)
        )
        print(f"\n  💾 Saved to {COLLECTED_FILE}")

        # 統計を保存
        STATS_FILE.write_text(json.dumps(stats, indent=2, ensure_ascii=False))
        print(f"  📊 Stats saved to {STATS_FILE}")
    else:
        print(f"\n  🔍 DRY RUN — データは保存されません")

    return stats


def show_stats():
    """収集済みデータの統計を表示"""
    if not COLLECTED_FILE.exists():
        print("❌ No collected data found")
        return

    papers = json.loads(COLLECTED_FILE.read_text())
    year_dist = Counter(p.get("year") for p in papers if p.get("year"))
    abstract_count = sum(1 for p in papers if p.get("abstract") and len(p["abstract"]) > 20)

    print(f"\n📊 CT Literature Collection Stats")
    print(f"{'='*50}")
    print(f"  Total papers: {len(papers)}")
    print(f"  With abstract: {abstract_count}")
    print(f"  Without abstract: {len(papers) - abstract_count}")

    print(f"\n  Top cited:")
    by_cite = sorted(papers, key=lambda p: p.get("citation_count", 0), reverse=True)
    for p in by_cite[:10]:
        print(f"    {p.get('citation_count', 0):>5}c | [{p.get('year')}] {p.get('title', '')[:60]}")

    print(f"\n  Year distribution:")
    for year, count in sorted(year_dist.items()):
        bar = "█" * min(count, 50)
        print(f"    {year}: {count:>3} {bar}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="CT Literature Collector")
    parser.add_argument("--dry-run", action="store_true", default=False, help="収集のみ、保存しない")
    parser.add_argument("--category", type=str, default=None, help="特定カテゴリのみ")
    parser.add_argument("--stats", action="store_true", help="統計表示")
    args = parser.parse_args()

    if args.stats:
        show_stats()
        return

    categories_list = [args.category] if args.category else None
    collect_all(categories=categories_list, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
