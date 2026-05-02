from __future__ import annotations
# PROOF: mekhane/periskope/cognition/phi0_query_fortifier.py
# PURPOSE: 全クエリを調査依頼書形式に自動構造化するセーフティネット
"""
Φ0 Query Fortifier — 全クエリ構造化

環境強制アーキテクチャ:
  第1層: MCP ツール定義の description で「調査依頼書形式」を誘導
  第2層 (本モジュール): research_brief が渡されなかった全クエリを LLM で構造化

参照: templates.md, tek_research_brief_*.md (7件の実例から抽出した6要素)
"""


import logging

logger = logging.getLogger(__name__)




async def fortify_query(query: str, known_context: str = "") -> str:
    """素のクエリを「調査依頼書」形式に構造化する。

    Gemini Flash を使用して、文脈のない素のクエリ (キーワード羅列含む) を
    構造化された調査依頼プロンプトに変換する。

    research_brief が渡されていない全てのクエリに適用される。
    文脈のないクエリは意図のないクエリ — 構造化が VFE を下げる。

    Args:
        query: 素のクエリ (キーワード羅列 or 構造不足の自然文)
        known_context: 既知のコンテキスト (あれば)

    Returns:
        構造化されたクエリ (失敗時は元のクエリをそのまま返す)
    """
    from mekhane.periskope.prompts import load_prompt
    from mekhane.periskope.cognition._llm import llm_ask
    from mekhane.ochema.model_defaults import FLASH

    # プロンプトテンプレートをロード
    template = load_prompt("phi0_query_fortify.typos")
    if not template:
        # Typos コンパイル失敗時のフォールバック
        template = _FALLBACK_PROMPT

    # プロンプト構築
    prompt = template.replace("{query}", query)
    if known_context:
        prompt = prompt.replace("{known_context}", known_context)
    else:
        prompt = prompt.replace("{known_context}", "(なし)")

    try:
        fortified = await llm_ask(
            prompt,
            model=FLASH,
            max_tokens=512,
            timeout=30.0,
            pipeline="periskope",
        )
        if fortified and len(fortified) > len(query):
            logger.info("🔧 Query structured → investigation request")
            logger.debug("  Original: %s", query[:100])
            logger.debug("  Structured: %s", fortified[:200])
            return fortified.strip()
        else:
            logger.warning("Query structuring produced shorter result, keeping original")
            return query
    except Exception as e:  # noqa: BLE001
        logger.warning("Query structuring failed: %s — keeping original", e)
        return query


# Typos コンパイル失敗時のフォールバックプロンプト
_FALLBACK_PROMPT = """以下の検索クエリを、外部AIへの「調査依頼プロンプト」に構造化してください。

元のクエリ: {query}
既知のコンテキスト: {known_context}

出力形式（自然文で）:
1. 背景: なぜこの調査が必要か（クエリから推測）
2. 具体的な問い: 何を知りたいか（番号付き）
3. 既知情報: 既に知っていること
4. 期待する証拠の種類
5. 制約: 不要な方向

構造化後のプロンプトのみを出力してください（説明不要）。"""
