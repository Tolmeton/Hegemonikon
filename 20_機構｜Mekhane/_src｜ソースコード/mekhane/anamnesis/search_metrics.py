from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/anamnesis/search_metrics.py
"""
PROOF: [L2/インフラ] このファイルは存在しなければならない

P3 → 検索品質の定量評価が必要
   → MRR / Recall@K による自動計算
   → search_metrics.py が担う

Q.E.D.

---

Anamnesis Search Quality Metrics

Usage:
    python mekhane/anamnesis/search_metrics.py --golden mekhane/anamnesis/golden_set.yaml
    python mekhane/anamnesis/cli.py bench
"""


import yaml
from pathlib import Path
from typing import Optional


def load_golden_set(path: str | Path) -> list[dict]:
    """YAML ゴールデンセットを読み込む"""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("queries", [])


def _match(result_key: str, expected_keys: list[str]) -> bool:
    """primary_key がゴールデンセットの期待値にマッチするか判定。
    期待値がプレフィクスの場合 (末尾が ':') はプレフィクスマッチ、
    それ以外は完全一致。
    """
    for ek in expected_keys:
        if ek.endswith(":"):
            if result_key.startswith(ek):
                return True
        else:
            if result_key == ek:
                return True
    return False


def reciprocal_rank(results: list[dict], expected_keys: list[str]) -> float:
    """単一クエリの Reciprocal Rank を計算。
    最初の正解の順位の逆数を返す。正解がなければ 0.0。
    """
    for i, r in enumerate(results):
        pk = r.get("primary_key", "")
        if _match(pk, expected_keys):
            return 1.0 / (i + 1)
    return 0.0


def recall_at_k(results: list[dict], expected_keys: list[str], k: int = 5) -> float:
    """上位 K 件中の正解率 (少なくとも1つマッチすれば 1.0)。"""
    top_k = results[:k]
    hits = sum(1 for r in top_k if _match(r.get("primary_key", ""), expected_keys))
    return min(hits / max(len(expected_keys), 1), 1.0)


def evaluate(
    golden_path: str | Path,
    hybrid: bool = False,
    expand: bool = False,
    backend: str = "faiss",
) -> dict:
    """ゴールデンセット全体で MRR と Recall@K を計算する。

    Returns:
        {
            "mrr": float,
            "recall_at_k": float,
            "per_query": [...],
            "mode": str,
            "total_queries": int,
        }
    """
    from mekhane.anamnesis.index import GnosisIndex

    golden = load_golden_set(golden_path)
    index = GnosisIndex(backend=backend)

    mode_label = "vector"
    if hybrid:
        mode_label = "hybrid"

    rr_sum = 0.0
    recall_sum = 0.0
    per_query = []

    for entry in golden:
        query = entry["query"]
        expected_keys = entry["expected_keys"]
        source_filter = entry.get("source_filter")
        k = entry.get("k", 10)

        results = index.search(
            query, k=k,
            source_filter=source_filter,
            hybrid=hybrid,
        )

        rr = reciprocal_rank(results, expected_keys)
        recall = recall_at_k(results, expected_keys, k=k)

        rr_sum += rr
        recall_sum += recall

        per_query.append({
            "query": query,
            "rr": rr,
            "recall": recall,
            "hits": len(results),
            "first_match_rank": next(
                (i + 1 for i, r in enumerate(results)
                 if _match(r.get("primary_key", ""), expected_keys)),
                None,
            ),
        })

    n = max(len(golden), 1)
    return {
        "mrr": rr_sum / n,
        "recall_at_k": recall_sum / n,
        "per_query": per_query,
        "mode": mode_label,
        "total_queries": len(golden),
    }


def format_report(result: dict) -> str:
    """評価結果をMarkdownレポートとして整形する"""
    lines = [
        f"## Search Quality Report ({result['mode']})",
        "",
        f"| Metric | Value |",
        f"|:-------|------:|",
        f"| **MRR** | {result['mrr']:.3f} |",
        f"| **Recall@K** | {result['recall_at_k']:.3f} |",
        f"| Queries | {result['total_queries']} |",
        "",
        "### Per-Query Breakdown",
        "",
        "| Query | RR | Recall | First Match | Hits |",
        "|:------|---:|-------:|:------------|-----:|",
    ]

    for pq in result["per_query"]:
        rank_str = str(pq["first_match_rank"]) if pq["first_match_rank"] else "—"
        lines.append(
            f"| {pq['query'][:30]} | {pq['rr']:.2f} | {pq['recall']:.2f} | {rank_str} | {pq['hits']} |"
        )

    return "\n".join(lines)


def compare_modes(golden_path: str | Path, backend: str = "faiss") -> str:
    """Vector-only と Hybrid の比較レポートを生成する"""
    vec_result = evaluate(golden_path, hybrid=False, backend=backend)
    hyb_result = evaluate(golden_path, hybrid=True, backend=backend)

    lines = [
        "# Anamnesis Search Benchmark",
        "",
        "## Mode Comparison",
        "",
        "| Metric | Vector | Hybrid | Δ |",
        "|:-------|-------:|-------:|--:|",
        f"| MRR | {vec_result['mrr']:.3f} | {hyb_result['mrr']:.3f} | {hyb_result['mrr'] - vec_result['mrr']:+.3f} |",
        f"| Recall@K | {vec_result['recall_at_k']:.3f} | {hyb_result['recall_at_k']:.3f} | {hyb_result['recall_at_k'] - vec_result['recall_at_k']:+.3f} |",
        "",
        format_report(vec_result),
        "",
        "---",
        "",
        format_report(hyb_result),
    ]

    return "\n".join(lines)
