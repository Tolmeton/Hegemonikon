#!/usr/bin/env python3
# PROOF: [L1/テスト] <- mekhane/mcp/tests/test_prokataskeve_l2l3l4.py
"""
Test for V-001 Prokataskeve (Tier 2 Package) - L2/L3/L4 Modules.

Covers:
  - consistency_checker.py (L3)
  - hypothesis_generator.py (L3)
  - pattern_injector.py (L2)
  - predictor.py (L4)
  - pipeline.py (Integration)
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

from mekhane.mcp.prokataskeve.models import IntentType, Domain, IntentClassification, ContextSummary
from mekhane.mcp.prokataskeve.consistency_checker import detect_contradiction, suggest_fix
from mekhane.mcp.prokataskeve.hypothesis_generator import generate_hyde
from mekhane.mcp.prokataskeve.pattern_injector import inject_few_shot
from mekhane.mcp.prokataskeve.predictor import predict_next, prefetch
from mekhane.mcp.prokataskeve.pipeline import PreprocessPipeline, PreprocessResult

class TestConsistencyChecker:
    @patch('mekhane.mcp.prokataskeve.consistency_checker.asyncio.to_thread')
    @patch('mekhane.mcp.prokataskeve.cortex_singleton.get_cortex')
    def test_detect_contradiction(self, mock_get_cortex, mock_to_thread):
        async def _impl():
            mock_cortex = MagicMock()
            mock_get_cortex.return_value = mock_cortex

            mock_response = MagicMock()
            mock_response.text = '[{"description": "Found bug", "span_a": "A", "span_b": "B", "severity": "medium"}]'
            mock_to_thread.return_value = mock_response

            context = ContextSummary(summary_text="Previous info")
            issues = await detect_contradiction("Current text", context)
            assert len(issues) == 1
            assert issues[0].severity == "medium"
        asyncio.run(_impl())

    @patch('mekhane.mcp.prokataskeve.consistency_checker.asyncio.to_thread')
    @patch('mekhane.mcp.prokataskeve.cortex_singleton.get_cortex')
    def test_suggest_fix(self, mock_get_cortex, mock_to_thread):
        async def _impl():
            mock_cortex = MagicMock()
            mock_get_cortex.return_value = mock_cortex

            mock_response = MagicMock()
            mock_response.text = '[{"issue_type": "contradiction", "original": "A", "suggestion": "Fix A", "action": "ask"}]'
            mock_to_thread.return_value = mock_response

            # Need to provide some issues
            from mekhane.mcp.prokataskeve.models import Contradiction
            issues = [Contradiction("Found bug", "A", "B", "medium")]
            fixes = suggest_fix(issues, [])
            assert len(fixes) == 1
            assert fixes[0].suggestion == "軽微な矛盾: Found bug"
        asyncio.run(_impl())

class TestHypothesisGenerator:
    @patch('mekhane.mcp.prokataskeve.hypothesis_generator.asyncio.to_thread')
    @patch('mekhane.mcp.prokataskeve.cortex_singleton.get_cortex')
    def test_generate_hyde(self, mock_get_cortex, mock_to_thread):
        async def _impl():
            mock_cortex = MagicMock()
            mock_get_cortex.return_value = mock_cortex

            mock_response = MagicMock()
            mock_response.text = "This is a hypothetical passage about the query."
            mock_to_thread.return_value = mock_response

            intent = IntentClassification(intent=IntentType.SEARCH, domain=Domain.ENGINEERING)
            query = "Find FEP implementation"
            passage = await generate_hyde(query, intent)
            assert "hypothetical passage" in passage
        asyncio.run(_impl())

    def test_generate_hyde_skip_non_search(self):
        async def _impl():
            intent = IntentClassification(intent=IntentType.CODE, domain=Domain.ENGINEERING)
            query = "Find FEP implementation"
            passage = await generate_hyde(query, intent)
            assert passage is None
        asyncio.run(_impl())

class TestPatternInjector:
    @patch('mekhane.mneme.search.search_all')
    def test_inject_few_shot(self, mock_search_all):
        async def _impl():
            mock_search_all.return_value = []
            intent = IntentClassification(intent=IntentType.CODE, domain=Domain.ENGINEERING)
            examples = await inject_few_shot("test query", intent)
            assert isinstance(examples, list)
        asyncio.run(_impl())

class TestPredictor:
    @patch('mekhane.mcp.prokataskeve.predictor.asyncio.to_thread')
    @patch('mekhane.mcp.prokataskeve.cortex_singleton.get_cortex')
    def test_predict_next(self, mock_get_cortex, mock_to_thread):
        async def _impl():
            mock_cortex = MagicMock()
            mock_get_cortex.return_value = mock_cortex

            mock_response = MagicMock()
            mock_response.text = '["FEP scaling", "scale logic", "pipeline.py"]'
            mock_to_thread.return_value = mock_response

            context = ContextSummary()
            intent = IntentClassification(intent=IntentType.SEARCH, domain=Domain.ENGINEERING)
            prediction = await predict_next("test scaling", intent, context)
            assert isinstance(prediction, list)
            assert "FEP scaling" in prediction
        asyncio.run(_impl())

class TestPipeline:
    def test_pipeline_instantiation(self):
        async def _impl():
            pipeline = PreprocessPipeline()
            assert pipeline is not None
            # Pipeline has no state, runs strictly functional pipeline through run() method
        asyncio.run(_impl())


# =============================================================================
# v4 Structurizer Parser Tests
# =============================================================================

from mekhane.mcp.prokataskeve.structurizer import parse_structured_output
from mekhane.mcp.prokataskeve.models import StructuredBlock, StructureResult, TraceEntry
import asyncio


class TestParseStructuredOutputV4:
    """v4 Týpos プロンプトの出力パーサーテスト。"""

    # テスト用の v4 Markdown 出力
    V4_MARKDOWN = (
        "**サマリ: 2タスク + 1構想**\n\n"
        "- **A-1** [指示] API エンドポイントの実装 [priority: 1] [独立]\n"
        "  <:voice: 技術的に確信 :>\n"
        "  [→WF: /tek — 既知手法の適用で確実に実装]\n"
        "- **A-2** [提案] テストの追加 [priority: 2] [依存: A-1]\n"
        "  [→WF: /pei]\n"
        "- **B-1** [仮説 40%] 入力前処理 MCP 構想 [HELD]\n"
        "  <:voice: まだ仮説段階、検証必要 :>\n\n"
        "| 原文 | ブロック |\n"
        "| --- | --- |\n"
        "| APIを実装して | A-1 |\n"
        "| テストも書いて | A-2 |\n"
        "| 入力前処理を考えたい | B-1 [条件] |\n"
    )

    def test_summary_extraction(self):
        """サマリ行が正しくパースされること。"""
        result = parse_structured_output(self.V4_MARKDOWN)
        assert isinstance(result, StructureResult)
        assert result.summary == "2タスク + 1構想"

    def test_block_count_and_ids(self):
        """3ブロック (A-1, A-2, B-1) が正しく抽出されること。"""
        result = parse_structured_output(self.V4_MARKDOWN)
        assert len(result.blocks) == 3
        ids = [b.block_id for b in result.blocks]
        assert "A-1" in ids
        assert "A-2" in ids
        assert "B-1" in ids

    def test_priority_and_held(self):
        """priority と HELD フラグが正しく抽出されること。"""
        result = parse_structured_output(self.V4_MARKDOWN)
        blocks = {b.block_id: b for b in result.blocks}

        assert blocks["A-1"].priority == 1
        assert blocks["A-2"].priority == 2
        assert blocks["B-1"].is_held is True
        assert blocks["A-1"].is_held is False

    def test_wf_rationale_separation(self):
        """WF 名と根拠が正しく分離されること。"""
        result = parse_structured_output(self.V4_MARKDOWN)
        blocks = {b.block_id: b for b in result.blocks}

        assert blocks["A-1"].suggested_wf == "/tek"
        assert blocks["A-1"].wf_rationale == "既知手法の適用で確実に実装"
        # 根拠なしの場合
        assert blocks["A-2"].suggested_wf == "/pei"
        assert blocks["A-2"].wf_rationale == ""

    def test_dependencies_and_voice(self):
        """依存関係と voice が正しく抽出されること。"""
        result = parse_structured_output(self.V4_MARKDOWN)
        blocks = {b.block_id: b for b in result.blocks}

        assert blocks["A-2"].dependencies == ["A-1"]
        assert blocks["A-1"].dependencies == []  # [独立] は空リスト
        assert "技術的に確信" in blocks["A-1"].voice

    def test_traceability_table(self):
        """トレーサビリティ表が正しくパースされること。"""
        result = parse_structured_output(self.V4_MARKDOWN)
        assert len(result.traceability) >= 3
        originals = [t.original for t in result.traceability]
        assert "APIを実装して" in originals

    def test_confidence_extraction(self):
        """トーンから確信度が正しく抽出されること。"""
        result = parse_structured_output(self.V4_MARKDOWN)
        blocks = {b.block_id: b for b in result.blocks}

        assert blocks["A-1"].confidence == 0.9   # [指示] → 0.9
        assert blocks["A-2"].confidence == 0.7   # [提案] → 0.7
        assert blocks["B-1"].confidence == 0.4   # [仮説 40%] → 0.4

    def test_fallback_on_empty(self):
        """パース不能時にフォールバックが返ること。"""
        result = parse_structured_output("ただのテキスト、構造なし")
        assert isinstance(result, StructureResult)
        assert len(result.blocks) == 1
        assert result.blocks[0].block_id == "A-1"

    def test_json_format_with_v4_fields(self):
        """JSON 形式でも v4 フィールドがパースされること。"""
        import json as json_mod
        data = {
            "blocks": [
                {
                    "id": "A-1",
                    "series": "A",
                    "tone": "指示",
                    "content": "テスト用ブロック",
                    "confidence": 0.9,
                    "priority": 1,
                    "wf": "/tek",
                    "wf_rationale": "確実な実装のため",
                    "is_held": False,
                }
            ],
            "summary": "1タスク",
            "traceability": [
                {"original": "テストして", "block_id": "A-1"}
            ],
        }
        raw = json_mod.dumps(data, ensure_ascii=False)
        result = parse_structured_output(raw)

        assert result.summary == "1タスク"
        assert len(result.blocks) == 1
        assert result.blocks[0].priority == 1
        assert result.blocks[0].suggested_wf == "/tek"
        assert result.blocks[0].wf_rationale == "確実な実装のため"
        assert len(result.traceability) == 1
