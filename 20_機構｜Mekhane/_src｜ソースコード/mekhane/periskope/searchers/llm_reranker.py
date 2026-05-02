from __future__ import annotations
# PROOF: mekhane/periskope/searchers/llm_reranker.py
# PURPOSE: periskope モジュールの llm_reranker
"""
LLM Cascade Reranker for Periskopē.

Architecture:
  Stage 0: Vertex Embedding Rerank (existing _rerank_results, free, fast)
  Stage 1: LLM Flash Bulk Score (Gemini Flash, many items per prompt)
  Stage 2: LLM Pro Precision Score (Gemini Pro, few items per prompt, L2+ only)
  Alt:      Cohere Rerank (rerank-v3.5, second opinion / fallback)

Prompt Design:
  - Source: Týpos .prompt ファイル (periskope_reranker.prompt)
  - Archetype: Precision (正確性・再現性が勝利条件)
  - Scoring Rubric: 3軸評価 (Relevance, Specificity, Authority)
  - Output: JSON array with per-dimension raw scores → Python 側で加重計算
  - Pre-Mortem: LLM が全部 0.7-0.9 に寄せる「平均化バイアス」を Rubric で抑制
"""


import asyncio
import dataclasses
import json
import logging
import os
import pathlib
import time

from mekhane.periskope.models import SearchResult

logger = logging.getLogger(__name__)

# ━━━ Týpos .prompt からプロンプトをロード ━━━
# SOURCE: mekhane/ergasterion/typos/prompts/periskope_reranker.prompt

_PROMPT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "ergasterion" / "typos" / "prompts"
_PROMPT_FILE = _PROMPT_DIR / "periskope_reranker.prompt"


def _load_system_instruction() -> str:
    """Týpos .prompt ファイルからシステム命令をコンパイルする。"""
    try:
        from mekhane.ergasterion.typos.typos import parse_file
        pf = parse_file(str(_PROMPT_FILE))
        compiled = pf.compile(format="markdown")
        return compiled
    except Exception as e:  # noqa: BLE001
        logger.warning("Týpos prompt load failed, using fallback: %s", e)
        return _FALLBACK_SYSTEM_INSTRUCTION


# Týpos ロード失敗時のフォールバック (最小限)
_FALLBACK_SYSTEM_INSTRUCTION = """\
You are a search result relevance evaluator.
Score each result on 3 axes (0.0-1.0):
- r (relevance): Does this result directly address the query?
- sp (specificity): Does it provide concrete, actionable information?
- au (authority): Is the source credible? (judge from URL/domain)
Output ONLY a JSON array: [{"id": 0, "r": 0.9, "sp": 0.8, "au": 0.7}, ...]
Use the FULL range. Irrelevant results MUST score below 0.2."""

_SCORE_PROMPT = """\
Query: "{query}"

Results to evaluate:
{items_text}
Score each result on 3 axes. Output a JSON array:
[{{"id": 0, "r": 0.9, "sp": 0.8, "au": 0.7}}, ...]

Fields: id (int), r (relevance 0.0-1.0), sp (specificity 0.0-1.0), au (authority 0.0-1.0).
JSON only, no other text."""


class LLMReranker:
    """LLM Cascade Reranker with Cohere fallback.

    Pipeline:
      existing Vertex Embedding rerank → Flash bulk score → Pro precision score
                                         ↕ (fallback)
                                     Cohere Rerank 3.5
    """

    def __init__(self, config: dict, cortex=None) -> None:
        llm_cfg = config.get("llm_rerank", {})
        self.enabled = llm_cfg.get("enabled", False)
        self.flash_model = llm_cfg.get("flash_model", "gemini-3.1-pro-preview")
        self.pro_model = llm_cfg.get("pro_model", "gemini-3.1-pro-preview")
        self.batch_size_by_depth: dict[int, int] = {
            int(k): int(v)
            for k, v in llm_cfg.get("batch_size_by_depth", {1: 30, 2: 15, 3: 5}).items()
        }
        self.top_k: int = llm_cfg.get("top_k", 30)
        self.top_n: int = llm_cfg.get("top_n", 10)

        # 3軸加重 (Python 側計算。LLM は素点のみ返す)
        weights = llm_cfg.get("score_weights", {})
        self._w_r: float = weights.get("relevance", 0.50)
        self._w_sp: float = weights.get("specificity", 0.30)
        self._w_au: float = weights.get("authority", 0.20)

        # Týpos プロンプト (lazy load)
        self._system_instruction: str | None = None
        self.fallback: bool = llm_cfg.get("fallback_on_error", True)

        # Depth-dependent timeout: L1=30s, L2=60s, L3=no limit (None)
        self.timeout_by_depth: dict[int, float | None] = {
            1: 30.0, 2: 60.0, 3: None,
        }

        # Cohere Rerank (second opinion)
        cohere_cfg = llm_cfg.get("cohere", {})
        self.cohere_enabled: bool = cohere_cfg.get("enabled", False)
        self.cohere_model: str = cohere_cfg.get("model", "rerank-v3.5")
        self.cohere_top_n: int = cohere_cfg.get("top_n", 10)

        self._cortex = cortex  # Shared CortexClient (injected from engine)
        self._cohere_client = None

    # ━━━ Cortex (Gemini) client ━━━

    def _get_cortex(self):
        """Lazy-load CortexClient."""
        if self._cortex is None:
            from mekhane.ochema.cortex_client import CortexClient
            try:
                from mekhane.ochema.account_router import get_account_for
                account = get_account_for("periskope")
            except Exception:  # noqa: BLE001
                account = "default"
            self._cortex = CortexClient(max_tokens=65536, account=account)
        return self._cortex

    # ━━━ Cohere client ━━━

    def _get_cohere(self):
        """Lazy-load Cohere client."""
        if self._cohere_client is None:
            import cohere
            api_key = os.environ.get("COHERE_API_KEY", "")
            self._cohere_client = cohere.ClientV2(api_key=api_key)
        return self._cohere_client

    # ━━━ Main rerank entry ━━━

    async def rerank(
        self, query: str, results: list[SearchResult], depth: int = 2
    ) -> list[SearchResult]:
        """Run the full reranking cascade."""
        if not self.enabled or not results:
            return results

        try:
            # Stage 1: Flash bulk score
            batch_size = self.batch_size_by_depth.get(depth, 15)
            timeout = self.timeout_by_depth.get(depth, 60.0)
            logger.info(
                "W8 Stage 1: Flash bulk scoring %d results (batch=%d, timeout=%s)",
                len(results), batch_size, timeout,
            )
            flash_scored = await self._bulk_score(query, results, batch_size, self.flash_model, timeout)
            flash_scored.sort(key=lambda x: x.relevance, reverse=True)
            top_k_results = flash_scored[:self.top_k]
            remaining_flash = flash_scored[self.top_k:]

            # Stage 2: Pro precision score (L2+ only)
            if depth >= 2 and len(top_k_results) > 0:
                pro_batch = min(5, batch_size)
                logger.info(
                    "W8 Stage 2: Pro precision scoring top %d results (batch=%d, timeout=%s)",
                    len(top_k_results), pro_batch, timeout,
                )
                pro_scored = await self._bulk_score(query, top_k_results, pro_batch, self.pro_model, timeout)
                pro_scored.sort(key=lambda x: x.relevance, reverse=True)
                final = pro_scored + remaining_flash
            else:
                final = flash_scored

            # Stage 3: Score normalization (min-max rescaling)
            # LLM の「平均化バイアス」を打破: 全結果が 0.3-0.5 に集中する問題を解消
            # min-max で [0.0, 1.0] に再スケーリングし、relevance_threshold フィルタを有効化
            if len(final) >= 3:
                scores = [r.relevance for r in final]
                s_min, s_max = min(scores), max(scores)
                spread = s_max - s_min
                if spread > 0.01:  # 全て同じスコアでなければ正規化
                    final = [
                        dataclasses.replace(r, relevance=(r.relevance - s_min) / spread)
                        for r in final
                    ]
                    final.sort(key=lambda x: x.relevance, reverse=True)
                    logger.info(
                        "W8 Stage 3: Score normalized [%.2f-%.2f] → [0.00-1.00]",
                        s_min, s_max,
                    )

            logger.info("W8: LLM cascade complete, %d results", len(final))
            return final

        except Exception as e:  # noqa: BLE001
            logger.warning("W8: LLM cascade failed (%s), trying Cohere fallback", e)
            if self.cohere_enabled:
                return await self._cohere_rerank(query, results)
            if self.fallback:
                # 全フォールバック時は、元の結果をそのまま返す（切り詰めない）
                return results
            raise

    # ━━━ Cohere Rerank (second opinion / fallback) ━━━

    async def _cohere_rerank(
        self, query: str, results: list[SearchResult]
    ) -> list[SearchResult]:
        """Rerank via Cohere Rerank API (second opinion)."""
        try:
            co = self._get_cohere()
            documents = [
                f"{r.title}\n{(r.content or r.snippet or '')[:1000]}"
                for r in results
            ]
            response = await asyncio.to_thread(
                co.rerank,
                model=self.cohere_model,
                query=query,
                documents=documents,
                top_n=self.cohere_top_n,
            )

            reranked_indices = set()
            reranked = []
            for item in response.results:
                idx = item.index
                reranked_indices.add(idx)
                new_r = dataclasses.replace(
                    results[idx],
                    relevance=item.relevance_score,
                )
                reranked.append(new_r)

            # スコアリングの対象外となった結果を後方に結合 (切り詰め防止)
            for i, r in enumerate(results):
                if i not in reranked_indices:
                    reranked.append(r)

            logger.info("W8 Cohere: Reranked %d → %d results, total appended: %d", 
                        len(results), len(reranked_indices), len(reranked))
            return reranked

        except Exception as e:  # noqa: BLE001
            logger.warning("W8 Cohere rerank failed: %s", e)
            if self.fallback:
                return results
            raise

    # ━━━ LLM Bulk Scoring ━━━

    async def _bulk_score(
        self, query: str, results: list[SearchResult], batch_size: int, model: str,
        timeout: float | None = 60.0,
    ) -> list[SearchResult]:
        """Score results in parallel batches via LLM."""
        chunks = [results[i:i + batch_size] for i in range(0, len(results), batch_size)]
        tasks = [self._score_chunk(query, chunk, model, timeout) for chunk in chunks]
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

        scored = []
        for i, res in enumerate(chunk_results):
            if isinstance(res, Exception):
                logger.warning("W8 chunk %d/%d failed (%s): %s", i + 1, len(chunks), model, res)
                scored.extend(chunks[i])
            else:
                scored.extend(res)
        return scored

    async def _score_chunk(
        self, query: str, chunk: list[SearchResult], model: str,
        timeout: float | None = 60.0,
    ) -> list[SearchResult]:
        """Score a single chunk via LLM with /mek+ crafted rubric prompt."""
        cortex = self._get_cortex()

        items_text = ""
        for i, r in enumerate(chunk):
            snippet = (r.content or r.snippet or "")[:1000]
            source_tag = r.source.value if r.source else "unknown"
            url_tag = f"\n{r.url}" if r.url else ""
            items_text += f"[{i}] ({source_tag}) {r.title}{url_tag}\n{snippet}\n\n"

        prompt = _SCORE_PROMPT.format(query=query, items_text=items_text)

        # timeout=None means no limit (L3 deep mode)
        chat_timeout = timeout if timeout is not None else 300.0
        # Týpos プロンプトを lazy load
        if self._system_instruction is None:
            self._system_instruction = _load_system_instruction()

        response = await asyncio.to_thread(
            cortex.chat,
            message=prompt,
            model=model,
            system_instruction=self._system_instruction,
            timeout=chat_timeout,
        )

        # Parse JSON (strip markdown fences if present)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        scores_data = json.loads(text)

        score_map: dict[int, float] = {}
        dim_map: dict[int, dict[str, float]] = {}  # 3-dimensional scores per item
        if isinstance(scores_data, list):
            for item in scores_data:
                if isinstance(item, dict) and "id" in item:
                    item_id = int(item["id"])
                    # 3軸素点を抽出
                    dims: dict[str, float] = {}
                    for key in ("r", "sp", "au"):
                        if key in item:
                            dims[key] = max(0.0, min(1.0, float(item[key])))
                    if dims:
                        dim_map[item_id] = dims
                    # Python 側で加重計算 (LLM に暗算させない)
                    r_val = dims.get("r", 0.0)
                    sp_val = dims.get("sp", 0.0)
                    au_val = dims.get("au", 0.0)
                    composite = (
                        self._w_r * r_val
                        + self._w_sp * sp_val
                        + self._w_au * au_val
                    )
                    score_map[item_id] = max(0.0, min(1.0, composite))

        # DEBUG: LLM 生スコア分布ログ (プロンプト品質診断用)
        if score_map:
            vals = list(score_map.values())
            logger.info(
                "W8 chunk scores: n=%d min=%.3f max=%.3f mean=%.3f spread=%.3f | dims=%s",
                len(vals), min(vals), max(vals),
                sum(vals) / len(vals), max(vals) - min(vals),
                {i: dim_map.get(i, {}) for i in sorted(dim_map)[:3]},
            )

        scored_chunk = []
        for i, r in enumerate(chunk):
            if i in score_map:
                new_meta = dict(r.metadata) if r.metadata else {}
                if i in dim_map:
                    new_meta["llm_scores"] = dim_map[i]
                scored_chunk.append(dataclasses.replace(
                    r, relevance=score_map[i], metadata=new_meta,
                ))
            else:
                scored_chunk.append(r)
        return scored_chunk
