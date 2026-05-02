from __future__ import annotations
# PROOF: mekhane/periskope/fallback_controller.py
# PURPOSE: 信号不足時の段階的フォールバック (Progressive Relaxation) コントローラ
"""
Periskopē Fallback Controller — Phase 1.9

信号が弱い（ニッチ領域）検索で結果が不足する場合に、
段階的に検索感度を上げて再探索する3段階フォールバック機構。

Stage 1: 閾値緩和 — relevance_threshold を下げて pre_rerank_results を再フィルタ
Stage 2: ソース展開 — 学術系ソースの差集合を追加検索
Stage 3: 隣接ドメイン — LLM で隣接概念を生成し個別検索

設計変更履歴:
  v1 → v2: /exe 批判的吟味により Stage 3 (クエリ分解) を Phase 2.5 に統合。
            W-1 (Adaptive Depth 抑制)、W-3 (ソース差集合) を反映。
"""


import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mekhane.periskope.engine import PeriskopeEngine
    from mekhane.periskope.models import ProgressCallback, SearchResult

logger = logging.getLogger(__name__)


@dataclass
class FallbackResult:
    """フォールバック実行結果。"""

    # 累積された検索結果
    search_results: list[SearchResult] = field(default_factory=list)
    # ソース別カウント (累積)
    source_counts: dict[str, int] = field(default_factory=dict)
    # 実行した段階名のリスト
    stages_executed: list[str] = field(default_factory=list)
    # Stage 3 で生成した隣接概念
    adjacent_concepts: list[str] = field(default_factory=list)


def _min_results_for_depth(depth: int, config: dict) -> int:
    """depth 別の最小結果数閾値を返す。"""
    fallback_cfg = config.get("fallback", {})
    thresholds = fallback_cfg.get("min_results_by_depth", {1: 1, 2: 3, 3: 5})
    return thresholds.get(depth, thresholds.get(2, 3))


def _has_enough(results: list, depth: int, config: dict) -> bool:
    """結果が十分かどうかを判定する。"""
    return len(results) >= _min_results_for_depth(depth, config)


async def _stage1_threshold_relaxation(
    initial_results: list[SearchResult],
    config: dict,
) -> list[SearchResult]:
    """Stage 1: 閾値緩和。

    pre_rerank_results を緩い閾値で再フィルタし、
    厳しいフィルタで落とされた結果を復活させる。
    """
    fallback_cfg = config.get("fallback", {})
    relaxed_threshold = fallback_cfg.get("relaxed_relevance_threshold", 0.15)

    recovered = [
        r for r in initial_results
        if r.relevance >= relaxed_threshold
    ]

    # フォールバック経由であることをメタデータに記録
    for r in recovered:
        r.metadata["fallback_stage"] = "threshold_relaxation"

    logger.info(
        "Stage 1 (閾値緩和): threshold=%.2f → %d 件復活 (元 %d 件)",
        relaxed_threshold, len(recovered), len(initial_results),
    )
    return recovered


async def _stage2_source_expansion(
    engine: PeriskopeEngine,
    query: str,
    already_searched: set[str],
    config: dict,
) -> tuple[list[SearchResult], dict[str, int]]:
    """Stage 2: ソース展開。

    学術系ソースのうち、まだ検索していないものだけを追加検索する。
    W-3 対処: already_searched との差集合で重複排除。
    """
    fallback_cfg = config.get("fallback", {})
    academic_sources = set(fallback_cfg.get("academic_sources", [
        "semantic_scholar", "gnosis", "gemini_search",
    ]))

    # W-3: 未検索ソースのみ
    new_sources = academic_sources - already_searched
    if not new_sources:
        logger.info("Stage 2 (ソース展開): 追加すべきソースなし (全て検索済み)")
        return [], {}

    logger.info(
        "Stage 2 (ソース展開): %s を追加検索 (既存: %s)",
        new_sources, already_searched,
    )

    # engine._phase_search を再利用して追加ソースのみ検索
    results, counts = await engine._phase_search(query, new_sources)

    # フォールバック経由であることをメタデータに記録
    for r in results:
        r.metadata["fallback_stage"] = "source_expansion"

    logger.info("Stage 2 (ソース展開): %d 件取得", len(results))
    return results, counts


async def _stage3_adjacent_domain(
    engine: PeriskopeEngine,
    query: str,
    enabled_sources: set[str],
    config: dict,
) -> tuple[list[SearchResult], dict[str, int], list[str]]:
    """Stage 3: 隣接ドメイン展開。

    LLM で元のクエリから「隣接する概念」を生成し、
    各概念を個別に検索して交差点を合成する。
    """
    fallback_cfg = config.get("fallback", {})
    adj_config = fallback_cfg.get("adjacent_domain", {})
    max_concepts = adj_config.get("max_concepts", 3)

    # LLM で隣接概念を生成
    concepts = await _generate_adjacent_concepts(
        engine, query, max_concepts, config,
    )

    if not concepts:
        logger.warning("Stage 3 (隣接ドメイン): 隣接概念の生成に失敗")
        return [], {}, []

    logger.info(
        "Stage 3 (隣接ドメイン): %d 概念生成 → %s",
        len(concepts), concepts,
    )

    # 各概念を個別検索
    all_results: list[SearchResult] = []
    all_counts: dict[str, int] = {}

    for concept in concepts:
        try:
            results, counts = await engine._phase_search(
                concept, enabled_sources,
            )
            for r in results:
                r.metadata["fallback_stage"] = "adjacent_domain"
                r.metadata["adjacent_concept"] = concept
            all_results.extend(results)
            for src, cnt in counts.items():
                all_counts[src] = all_counts.get(src, 0) + cnt
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "Stage 3: 概念 %r の検索失敗: %s", concept, e,
            )

    logger.info("Stage 3 (隣接ドメイン): 合計 %d 件取得", len(all_results))
    return all_results, all_counts, concepts


async def _generate_adjacent_concepts(
    engine: PeriskopeEngine,
    query: str,
    max_concepts: int,
    config: dict,
) -> list[str]:
    """LLM を使って元のクエリから隣接概念を生成する。"""
    fallback_cfg = config.get("fallback", {})
    adj_config = fallback_cfg.get("adjacent_domain", {})
    model = adj_config.get("model", "gemini-3-flash-preview")

    prompt = f"""以下の研究クエリに対して、直接的には一致しないが
理論的に密接に関連する「隣接概念」を{max_concepts}つ生成してください。

各概念は検索クエリとして使える簡潔な英語フレーズ（5-10語）にしてください。
元のクエリと同じ用語を単に言い換えるのではなく、
異なる分野や異なる視点からの接続点を見つけてください。

研究クエリ: {query}

出力形式（各行に1つ、番号なし、説明なし）:
"""

    try:
        # engine が持つ cortex client を使用
        if hasattr(engine, "cortex") and engine.cortex:
            response = await engine.cortex.generate(
                prompt, model=model,
            )
        elif hasattr(engine, "gemini_search") and hasattr(engine.gemini_search, "cortex"):
            response = await engine.gemini_search.cortex.generate(
                prompt, model=model,
            )
        else:
            logger.warning("Stage 3: LLM クライアントが利用不可")
            return []

        # レスポンスをパースして概念リストに
        lines = [
            line.strip()
            for line in response.strip().split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]
        return lines[:max_concepts]

    except Exception as e:  # noqa: BLE001
        logger.warning("Stage 3: 隣接概念の生成に失敗: %s", e)
        return []


async def execute_fallback(
    engine: PeriskopeEngine,
    query: str,
    initial_results: list[SearchResult],
    enabled_sources: set[str],
    depth: int,
    config: dict,
    progress_callback: ProgressCallback | None = None,
) -> FallbackResult:
    """段階的フォールバックを実行する。

    各段階は前段階の結果を累積し、
    十分な結果が集まった時点で早期リターンする。

    Args:
        engine: PeriskopeEngine インスタンス (_phase_search の再利用)
        query: 検索クエリ
        initial_results: フィルタ前の pre_rerank_results
        enabled_sources: 有効なソースの集合
        depth: 検索深度 (1-3)
        config: 設定辞書
        progress_callback: 進捗通知コールバック

    Returns:
        FallbackResult: 累積された結果
    """
    from mekhane.periskope.models import ProgressEvent

    fallback_cfg = config.get("fallback", {})
    if not fallback_cfg.get("enabled", True):
        logger.info("Fallback: 無効化されています")
        return FallbackResult()

    max_stages = fallback_cfg.get("max_stages", 3)
    result = FallbackResult()

    def _notify(phase: str, **detail: Any) -> None:
        if progress_callback:
            progress_callback(ProgressEvent(phase=phase, **detail))

    # ── Stage 1: 閾値緩和 ──
    if max_stages >= 1:
        _notify("fallback_stage1_start", label="閾値緩和")
        recovered = await _stage1_threshold_relaxation(initial_results, config)
        result.search_results.extend(recovered)
        result.stages_executed.append("threshold_relaxation")
        _notify("fallback_stage1_done", label="閾値緩和",
                detail={"recovered": len(recovered)})

        if _has_enough(result.search_results, depth, config):
            logger.info("Fallback: Stage 1 で十分な結果 (%d 件)", len(result.search_results))
            return result

    # ── Stage 2: ソース展開 ──
    if max_stages >= 2:
        _notify("fallback_stage2_start", label="ソース展開")
        expanded, counts = await _stage2_source_expansion(
            engine, query, enabled_sources, config,
        )
        result.search_results.extend(expanded)
        for src, cnt in counts.items():
            result.source_counts[src] = result.source_counts.get(src, 0) + cnt
        result.stages_executed.append("source_expansion")
        _notify("fallback_stage2_done", label="ソース展開",
                detail={"expanded": len(expanded)})

        if _has_enough(result.search_results, depth, config):
            logger.info("Fallback: Stage 2 で十分な結果 (%d 件)", len(result.search_results))
            return result

    # ── Stage 3: 隣接ドメイン ──
    if max_stages >= 3:
        _notify("fallback_stage3_start", label="隣接ドメイン展開")
        adjacent_results, adj_counts, concepts = await _stage3_adjacent_domain(
            engine, query, enabled_sources, config,
        )
        result.search_results.extend(adjacent_results)
        for src, cnt in adj_counts.items():
            result.source_counts[src] = result.source_counts.get(src, 0) + cnt
        result.adjacent_concepts = concepts
        result.stages_executed.append("adjacent_domain")
        _notify("fallback_stage3_done", label="隣接ドメイン展開",
                detail={"results": len(adjacent_results), "concepts": concepts})

    logger.info(
        "Fallback 完了: %d 件, stages=%s",
        len(result.search_results), result.stages_executed,
    )
    return result
