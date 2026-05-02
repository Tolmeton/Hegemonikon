from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/prokataskeve/intent_classifier.py
"""
IntentClassifier — Intent classification, goal extraction, template matching.

Contains:
  - classify_intent (Noēsis, I×E) — L1
  - extract_goal (Boulēsis, I×P) — L2
  - match_template (Synagōgē, I×Exploit) — L2
"""

import asyncio
import json
import logging
import re
from typing import Any

from mekhane.mcp.prokataskeve.models import (
    Domain,
    Entity,
    EntityType,
    GoalExtraction,
    IntentClassification,
    IntentType,
    TemplateMatch,
)

logger = logging.getLogger(__name__)


# =============================================================================
# L1: classify_intent (Noēsis)
# =============================================================================


# PURPOSE: L1 意図分類 (Noēsis, I×E — 世界像を認識目的で更新する)
async def classify_intent(
    text: str,
    entities: list[Entity],
) -> IntentClassification:
    """L1 Classify the intent and domain of the input.

    Uses Gemini Flash for fast classification.
    Falls back to heuristic classification on LLM failure.
    """
    # Heuristic pre-check (skip LLM if obvious)
    ccl_entities = [e for e in entities if e.type == EntityType.CCL]
    if ccl_entities:
        return IntentClassification(
            intent=IntentType.WORKFLOW,
            domain=Domain.OPS,
            confidence=0.95,
            reasoning=f"CCL expression detected: {ccl_entities[0].value}",
        )

    # Heuristic keywords
    text_lower = text.lower()
    if any(kw in text_lower for kw in ["バグ", "エラー", "error", "bug", "traceback", "exception"]):
        return IntentClassification(
            intent=IntentType.DEBUG,
            domain=Domain.ENGINEERING,
            confidence=0.8,
            reasoning="Debug keywords detected",
        )
    if any(kw in text_lower for kw in ["検索", "調べ", "search", "research", "論文", "paper"]):
        return IntentClassification(
            intent=IntentType.SEARCH,
            domain=Domain.ACADEMIC if "論文" in text or "paper" in text_lower else Domain.GENERAL,
            confidence=0.7,
            reasoning="Search keywords detected",
        )
    if any(kw in text_lower for kw in ["コード", "実装", "作って", "作成", "implement", "create", "build"]):
        return IntentClassification(
            intent=IntentType.CODE,
            domain=Domain.ENGINEERING,
            confidence=0.7,
            reasoning="Code/build keywords detected",
        )
    if any(kw in text_lower for kw in ["レビュー", "review", "チェック", "check", "監査", "audit"]):
        return IntentClassification(
            intent=IntentType.REVIEW,
            domain=Domain.ENGINEERING,
            confidence=0.7,
            reasoning="Review keywords detected",
        )

    # Workflow patterns (non-CCL): 実行、デプロイ、起動、ビルド
    if any(kw in text_lower for kw in ["実行", "deploy", "デプロイ", "起動", "ビルド", "build", "run"]):
        return IntentClassification(
            intent=IntentType.WORKFLOW,
            domain=Domain.OPS,
            confidence=0.65,
            reasoning="Workflow/ops keywords detected",
        )

    # Discuss patterns: 日本語の相談・説明・質問
    if any(kw in text_lower for kw in [
        "教えて", "説明", "とは", "って何", "どう思う", "意見",
        "相談", "について", "違い", "比較",
        "explain", "what is", "how to", "why",
    ]):
        return IntentClassification(
            intent=IntentType.DISCUSS,
            domain=Domain.GENERAL,
            confidence=0.65,
            reasoning="Discussion/question keywords detected",
        )

    # Try LLM classification (Fallback)
    try:
        from mekhane.mcp.prokataskeve.cortex_singleton import get_cortex
        client = get_cortex()
        if client is None:
            raise RuntimeError("CortexClient unavailable")

        prompt = (
            "Classify the intent and domain of the user input.\n"
            "Intent options: search, code, discuss, debug, review, workflow\n"
            "Domain options: academic, engineering, ops, general\n\n"
            "Examples:\n"
            "Q: FEPの論文探して\n"
            'A: {"intent": "search", "domain": "academic", "reasoning": "user wants to find papers"}\n'
            "Q: このエラーなんで？ Traceback...\n"
            'A: {"intent": "debug", "domain": "engineering", "reasoning": "traceback indicates an error"}\n\n'
            f"Input: {text[:500]}\n\n"
            'Reply strictly in valid JSON format: {"intent": "...", "domain": "...", "reasoning": "..."}'
        )
        response = await asyncio.to_thread(
            client.chat, message=prompt, model="gemini-3-flash-preview", timeout=5.0,
        )
        data = json.loads(response.text.strip().removeprefix("```json").removesuffix("```").strip())
        intent_str = str(data.get("intent", "discuss"))
        domain_str = str(data.get("domain", "general"))
        reasoning_str = str(data.get("reasoning", "LLM classified"))

        try:
            intent_val = IntentType(intent_str)
        except ValueError:
            intent_val = IntentType.DISCUSS

        try:
            domain_val = Domain(domain_str)
        except ValueError:
            domain_val = Domain.GENERAL

        return IntentClassification(
            intent=intent_val,
            domain=domain_val,
            confidence=0.85,
            reasoning=reasoning_str,
        )
    except Exception as e:  # noqa: BLE001
        logger.debug("LLM intent classification failed, using heuristic: %s", e)

    # Fallback: discuss
    return IntentClassification(
        intent=IntentType.DISCUSS,
        domain=Domain.GENERAL,
        confidence=0.3,
        reasoning="No specific keywords detected, defaulting to discuss",
    )


# =============================================================================
# L2: extract_goal (Boulēsis)
# =============================================================================


# Template for goal extraction
_GOAL_EXTRACTION_PROMPT = (
    "Extract the user's goal from this input as structured JSON.\n\n"
    "Fields:\n"
    '  action: What the user wants to do (e.g., "fix", "search", "create", "review", "explain", "analyze")\n'
    '  target: What the action applies to (e.g., "bug", "paper", "class", "test", "performance")\n'
    '  constraints: List of constraints or requirements (e.g., ["within 1s", "in Python"])\n\n'
    "Examples:\n"
    "Input: このバグを直して。テストも追加して。\n"
    'Output: {"action": "fix", "target": "bug", "constraints": ["add tests"]}\n\n'
    "Input: FEPに関する最新の論文を5件探して\n"
    'Output: {"action": "search", "target": "FEP papers", "constraints": ["latest", "5 papers"]}\n\n'
    "Input: {input}\n\n"
    "Reply strictly in valid JSON: "
    '{"action": "...", "target": "...", "constraints": [...]}'
)


# PURPOSE: L2 目的抽出 (Boulēsis, I×P — 実用目的で世界像を更新する)
async def extract_goal(
    text: str,
    intent: IntentClassification,
) -> GoalExtraction:
    """L2 Extract structured goal from input text.

    Complements classify_intent (which answers "what kind of task")
    by answering "what specifically does the user want done".
    """
    # Fast path: workflow intent has goal embedded in CCL
    if intent.intent == IntentType.WORKFLOW:
        return GoalExtraction(
            action="execute", target="workflow", confidence=0.9,
        )

    # Try LLM extraction
    try:
        from mekhane.mcp.prokataskeve.cortex_singleton import get_cortex
        client = get_cortex()
        if client is None:
            raise RuntimeError("CortexClient unavailable")

        prompt = _GOAL_EXTRACTION_PROMPT.replace("{input}", text[:500])
        response = await asyncio.to_thread(
            client.chat, message=prompt, model="gemini-3-flash-preview", timeout=5.0,
        )
        data = json.loads(response.text.strip().removeprefix("```json").removesuffix("```").strip())
        return GoalExtraction(
            action=str(data.get("action", "unknown")),
            target=str(data.get("target", "unknown")),
            constraints=[str(c) for c in data.get("constraints", [])],
            confidence=0.8,
        )
    except Exception as e:  # noqa: BLE001
        logger.debug("Goal extraction LLM failed: %s", e)

    # Heuristic fallback
    action_map = {
        IntentType.DEBUG: "fix",
        IntentType.SEARCH: "search",
        IntentType.CODE: "create",
        IntentType.REVIEW: "review",
        IntentType.DISCUSS: "discuss",
    }
    return GoalExtraction(
        action=action_map.get(intent.intent, "unknown"),
        target="unspecified",
        confidence=0.3,
    )


# =============================================================================
# L2: match_template (Synagōgē)
# =============================================================================


# Known task templates
_TEMPLATES = [
    {
        "id": "ccl_execute",
        "name": "CCL ワークフロー実行",
        "pattern": re.compile(r'/[a-z]{2,4}[+\-]'),
        "params_extract": lambda t: {"ccl": re.search(r'/[a-z]{2,4}[+\-]*', t).group()},  # type: ignore[union-attr]
    },
    {
        "id": "paper_search",
        "name": "論文検索",
        "pattern": re.compile(r'(?:論文|paper|研究).*(?:検索|探|search|find)', re.IGNORECASE),
        "params_extract": lambda t: {"query": t},
    },
    {
        "id": "code_review",
        "name": "コードレビュー",
        "pattern": re.compile(r'(?:レビュー|review|チェック|check).*(?:コード|code|ファイル|file)', re.IGNORECASE),
        "params_extract": lambda t: {},
    },
    {
        "id": "bug_fix",
        "name": "バグ修正",
        "pattern": re.compile(r'(?:バグ|bug|エラー|error).*(?:直|fix|修正|resolve)', re.IGNORECASE),
        "params_extract": lambda t: {},
    },
    {
        "id": "deep_research",
        "name": "Deep Research",
        "pattern": re.compile(r'(?:調べ|リサーチ|research|investigate|深く)', re.IGNORECASE),
        "params_extract": lambda t: {"query": t},
    },
]


# PURPOSE: L2 テンプレートマッチ (Synagōgē, I×Exploit — 既知パターンに照合する)
def match_template(
    text: str,
    intent: IntentClassification,
) -> TemplateMatch | None:
    """L2 Match input against known task templates.

    Returns the best matching template, or None if no match.
    Rule-based only — no LLM required.
    """
    for tmpl in _TEMPLATES:
        if tmpl["pattern"].search(text):
            try:
                params = tmpl["params_extract"](text)
            except Exception:  # noqa: BLE001
                params = {}
            return TemplateMatch(
                template_id=tmpl["id"],
                template_name=tmpl["name"],
                confidence=0.8,
                params=params,
            )

    return None
