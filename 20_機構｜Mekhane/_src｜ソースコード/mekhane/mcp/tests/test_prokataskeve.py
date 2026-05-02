#!/usr/bin/env python3
# PROOF: [L1/テスト] <- mekhane/mcp/tests/
"""
Test for V-001 Prokataskeve (Tier 2 Package) - L0/L1 Modules.

Covers:
  - input_analyzer.py
  - intent_classifier.py (L1 rules)
  - query_transformer.py (L1 rules)
  - context_resolver.py (L1 rules)
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

# Mock mekhane.mneme to bypass __getattr__ before imports that use it
import types
mock_mneme = types.ModuleType("mekhane.mneme")
mock_search = types.ModuleType("mekhane.mneme.search")
mock_search.search_all = AsyncMock(return_value=[{"id": "KI1", "title": "KI1 Title", "score": 0.9}])
mock_mneme.search = mock_search

import mekhane
original_getattr = getattr(mekhane, "__getattr__", None)
def fake_getattr(name):
    if name == "mneme":
        return mock_mneme
    if original_getattr:
        return original_getattr(name)
    raise AttributeError(name)

mekhane.__getattr__ = fake_getattr
sys.modules["mekhane.mneme"] = mock_mneme
sys.modules["mekhane.mneme.search"] = mock_search

# Now we can import the modules
from mekhane.mcp.prokataskeve.input_analyzer import normalize, extract_entities, extract_certain, detect_ambiguity
from mekhane.mcp.prokataskeve.models import EntityType, IntentType, Domain, Entity, IntentClassification
from mekhane.mcp.prokataskeve.intent_classifier import classify_intent, extract_goal, match_template
from mekhane.mcp.prokataskeve.query_transformer import rewrite_query, diversify_query
from mekhane.mcp.prokataskeve.context_resolver import resolve_references, integrate_context, recall_past
import mekhane.mcp.prokataskeve.cortex_singleton
import asyncio

class TestInputAnalyzer:
    def test_normalize_fullwidth(self):
        assert normalize("ＡＢＣ　１２３") == "ABC 123"
        assert normalize("テスト　入力") == "テスト 入力"

    def test_normalize_whitespaces(self):
        assert normalize("a    b\t\tc") == "a b c"
        assert normalize("  strip  ") == "strip"

    def test_normalize_newlines(self):
        text = "line1\n\n\nline2"
        assert normalize(text) == "line1\n\nline2"

    def test_extract_entities_ccl(self):
        entities = extract_entities("実行して /noe+")
        ccl_entities = [e for e in entities if e.type == EntityType.CCL]
        assert len(ccl_entities) == 1
        assert ccl_entities[0].value == "/noe+"

    def test_extract_entities_macro_ccl(self):
        entities = extract_entities("実行して /noe+ >> /bou-")
        ccl_entities = [e for e in entities if e.type == EntityType.CCL]
        assert len(ccl_entities) == 1
        assert ccl_entities[0].value == "/noe+ >> /bou-"

    def test_extract_entities_path_and_url(self):
        text = "Check /etc/hosts and https://example.com"
        entities = extract_entities(text)
        assert any(e.type == EntityType.PATH and e.value == "/etc/hosts" for e in entities)
        assert any(e.type == EntityType.URL and e.value == "https://example.com" for e in entities)

    def test_extract_entities_quoted_and_code(self):
        text = "これは 「引用」 です。 `code` もあります。"
        entities = extract_entities(text)
        assert any(e.type == EntityType.QUOTED and e.value == "「引用」" for e in entities)
        assert any(e.type == EntityType.CODE_BLOCK and e.value == "`code`" for e in entities)

    def test_extract_certain(self):
        text = "引用: 「重要データ」"
        entities = extract_entities(text)
        certain_spans = extract_certain(text, entities)
        assert len(certain_spans) == 1
        assert certain_spans[0].text == "「重要データ」"

    def test_detect_ambiguity_implicit_target(self):
        text = "これを削除して"
        ambiguities = detect_ambiguity(text, [], resolved_refs={})
        assert len(ambiguities) == 1
        assert "これ" in ambiguities[0].text

class TestIntentClassifier:
    @patch('mekhane.mcp.prokataskeve.cortex_singleton.get_cortex')
    def test_classify_intent_mock(self, mock_get_cortex):
        async def _impl():
            mock_cortex = MagicMock()
            mock_response = MagicMock()
            mock_response.text = '{"intent": "search", "domain": "engineering", "confidence": 0.9, "reasoning": "test"}'
            mock_cortex.chat.return_value = mock_response
            mock_get_cortex.return_value = mock_cortex

            res = await classify_intent("architecture document", [])
            assert res.intent == IntentType.SEARCH
            assert res.domain == Domain.ENGINEERING
        asyncio.run(_impl())

    def test_classify_intent_fallback(self):
        async def _impl():
            with patch('mekhane.mcp.prokataskeve.cortex_singleton.get_cortex', return_value=None):
                res = await classify_intent("python コードを直して", [])
                assert res.intent == IntentType.CODE
                assert res.domain == Domain.ENGINEERING
        asyncio.run(_impl())

    def test_match_template(self):
        intent = IntentClassification(intent=IntentType.REVIEW, domain=Domain.ENGINEERING)
        # Assuming code check matches code_review or similar heuristic
        match = match_template("コードをチェックして", intent)

class TestQueryTransformer:
    def test_rewrite_query_intent_sharpening(self):
        async def _impl():
            with patch('mekhane.periskope.query_expander.get_expander', side_effect=ImportError):
                intent = IntentClassification(intent=IntentType.SEARCH, domain=Domain.GENERAL)
                queries = await rewrite_query("FEP について 調べて", intent)
                assert "FEP 調べて" not in queries
                assert "FEP" in queries or any("FEP" == q for q in queries)
        asyncio.run(_impl())

    @patch('mekhane.mcp.prokataskeve.cortex_singleton.get_cortex')
    def test_diversify_query(self, mock_get_cortex):
        async def _impl():
            mock_cortex = MagicMock()
            mock_response = MagicMock()
            mock_response.text = '["FEP history", "variational inference"]'
            mock_cortex.chat.return_value = mock_response
            mock_get_cortex.return_value = mock_cortex

            res = await diversify_query("FEP", ["FEP"])
            assert "FEP history" in res
        asyncio.run(_impl())

class TestContextResolver:
    def test_resolve_references_without_state(self):
        refs = resolve_references("これを それの 前の ログ")
        assert "これ" in refs
        assert refs["これ"] == "[unresolved:demonstrative]"

    def test_resolve_references_with_state(self):
        state = {"last_topic": "FEP_test", "last_file": "test.py"}
        refs = resolve_references("さっきの 問題", session_state=state)
        assert "さっきの" in refs
        assert refs["さっきの"] == "test.py"

    def test_integrate_context(self):
        async def _impl():
            state = {"topic": "AI", "active_files": ["main.py"]}
            res = await integrate_context("query", session_state=state, resolved_refs={"これ": "main.py"})
            assert "main.py" in res.active_files
            assert "KI1 Title" in res.related_kis
            assert "トピック: AI" in res.summary_text
            assert "main.py" in res.summary_text
        asyncio.run(_impl())
