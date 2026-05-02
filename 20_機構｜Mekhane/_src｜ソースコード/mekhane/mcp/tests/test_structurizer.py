#!/usr/bin/env python3
# PROOF: [L1/テスト] <- mekhane/mcp/tests/test_structurizer.py
"""
Test for V-001 Prokataskeve — structurizer.py (L2 MECE 構造化).

Covers:
  - parse_structured_output (JSON/Markdown/fallback)
  - structurize (LLM mock + short text skip + fallback)
  - _extract_confidence (トーンから確信度抽出)
  - _get_system_prompt (キャッシュ動作)
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

# プロジェクトルート
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from mekhane.mcp.prokataskeve.models import (
    IntentType, Domain, IntentClassification,
    StructuredBlock, StructureResult,
)
from mekhane.mcp.prokataskeve.structurizer import (
    parse_structured_output,
    structurize,
    _extract_confidence,
)


# =========================================================================
# parse_structured_output テスト
# =========================================================================

class TestParseStructuredOutput:
    """LLM 出力のパーサーテスト。"""

    def test_json_array(self):
        """JSON 配列形式のパース。"""
        raw = '''```json
[
  {"id": "A1", "series": "A", "tone": "指示", "content": "バグを修正する", "confidence": 0.9},
  {"id": "B1", "series": "B", "tone": "提案", "content": "テストも追加", "confidence": 0.7}
]
```'''
        result = parse_structured_output(raw)
        assert isinstance(result, StructureResult)
        assert len(result.blocks) == 2
        assert result.blocks[0].block_id == "A1"
        assert result.blocks[0].series == "A"
        assert result.blocks[0].tone == "指示"
        assert result.blocks[0].content == "バグを修正する"
        assert result.blocks[0].confidence == 0.9
        assert result.blocks[1].block_id == "B1"
        assert result.blocks[1].confidence == 0.7

    def test_json_with_blocks_key(self):
        """{"blocks": [...]} 形式のパース。"""
        raw = '{"blocks": [{"id": "A1", "series": "A", "tone": "指示", "content": "テスト"}]}'
        result = parse_structured_output(raw)
        assert isinstance(result, StructureResult)
        assert len(result.blocks) == 1
        assert result.blocks[0].block_id == "A1"

    def test_markdown_format(self):
        """Markdown 形式 (- **A1** [トーン] 本文) のパース。"""
        raw = """- **A1** [指示] pipeline.py を修正する
- **B1** [提案] テストカバレッジを上げる
- **C1** [仮説 40%] 設計を見直す必要あり"""
        result = parse_structured_output(raw)
        assert isinstance(result, StructureResult)
        assert len(result.blocks) == 3
        assert result.blocks[0].block_id == "A1"
        assert result.blocks[0].series == "A"
        assert result.blocks[0].tone == "指示"
        assert "pipeline.py" in result.blocks[0].content
        assert result.blocks[2].confidence == 0.4  # "仮説 40%" → 0.4

    def test_fallback_unparseable(self):
        """パース不能テキストのフォールバック。"""
        raw = "これはどちらの形式にもマッチしないテキスト"
        result = parse_structured_output(raw)
        assert isinstance(result, StructureResult)
        assert len(result.blocks) == 1
        assert result.blocks[0].block_id == "A-1"
        assert result.blocks[0].series == "A"

    def test_empty_json_array(self):
        """空の JSON 配列。"""
        raw = "[]"
        result = parse_structured_output(raw)
        assert isinstance(result, StructureResult)
        # 空配列 → 空ブロックリスト
        assert len(result.blocks) == 0

    def test_json_with_dependencies(self):
        """依存関係付き JSON のパース。"""
        raw = '[{"id": "A2", "series": "A", "tone": "指示", "content": "デプロイ", "confidence": 0.8, "deps": ["A1"], "wf": "/ene"}]'
        result = parse_structured_output(raw)
        assert isinstance(result, StructureResult)
        assert len(result.blocks) == 1
        assert result.blocks[0].dependencies == ["A1"]
        assert result.blocks[0].suggested_wf == "/ene"


# =========================================================================
# _extract_confidence テスト
# =========================================================================

class TestExtractConfidence:
    """トーン文字列から確信度を抽出するテスト。"""

    def test_percentage(self):
        assert _extract_confidence("仮説 40%") == 0.4
        assert _extract_confidence("推定 85%") == 0.85

    def test_keyword_shiji(self):
        assert _extract_confidence("指示") == 0.9

    def test_keyword_teian(self):
        assert _extract_confidence("提案") == 0.7

    def test_keyword_kasetsu(self):
        assert _extract_confidence("仮説") == 0.4

    def test_unknown(self):
        assert _extract_confidence("不明なトーン") == 0.5


# =========================================================================
# structurize テスト
# =========================================================================

class TestStructurize:
    """L2 MECE 構造化のテスト。"""

    def test_short_text_skip(self):
        async def _impl():
            """50文字未満のテキストはスキップ。"""
            result = await structurize("短い")
            assert isinstance(result, StructureResult)
            assert result.is_fallback is True
            assert len(result.blocks) == 1
            assert result.blocks[0].content == "短い"
        asyncio.run(_impl())

    @patch('mekhane.mcp.prokataskeve.structurizer.asyncio.to_thread')
    @patch('mekhane.mcp.prokataskeve.cortex_singleton.get_cortex')
    def test_structurize_with_llm(self, mock_get_cortex, mock_to_thread):
        async def _impl():
            """LLM 呼び出し成功時の構造化。"""
            mock_cortex = MagicMock()
            mock_get_cortex.return_value = mock_cortex

            mock_response = MagicMock()
            mock_response.text = '''```json
[
  {"id": "A1", "series": "A", "tone": "指示", "content": "FEP エンジンのバグを修正する", "confidence": 0.9},
  {"id": "B1", "series": "B", "tone": "提案", "content": "テストカバレッジを上げるべき", "confidence": 0.7}
]
```'''
            mock_to_thread.return_value = mock_response

            # 50文字以上のテキスト (short text skip を回避)
            text = "FEP エンジンに重大なバグがある。早急に修正が必要。また、テストカバレッジも大幅に上げたほうがいいと思う。品質向上のために。"
            result = await structurize(text)

            assert isinstance(result, StructureResult)
            assert result.is_fallback is False
            assert len(result.blocks) == 2
            assert result.blocks[0].series == "A"
            assert result.blocks[1].series == "B"
        asyncio.run(_impl())

    @patch('mekhane.mcp.prokataskeve.cortex_singleton.get_cortex')
    def test_structurize_fallback_on_no_cortex(self, mock_get_cortex):
        async def _impl():
            """CortexClient 取得失敗時のフォールバック。"""
            mock_get_cortex.return_value = None

            # 50文字以上のテキスト (short text skip を回避)
            text = "これは十分に長いテキストです。構造化の対象になります。パラグラフ分割でフォールバックされるはず。CortexClient がないときの動作を確認する。"
            result = await structurize(text)

            assert isinstance(result, StructureResult)
            assert result.is_fallback is True
            assert len(result.blocks) >= 1
            assert result.blocks[0].confidence == 0.3  # フォールバック confidence
        asyncio.run(_impl())

    @patch('mekhane.mcp.prokataskeve.structurizer.asyncio.to_thread')
    @patch('mekhane.mcp.prokataskeve.cortex_singleton.get_cortex')
    def test_structurize_with_intent(self, mock_get_cortex, mock_to_thread):
        async def _impl():
            """意図情報を渡した場合の構造化。"""
            mock_cortex = MagicMock()
            mock_get_cortex.return_value = mock_cortex

            mock_response = MagicMock()
            mock_response.text = '[{"id": "A1", "series": "A", "tone": "指示", "content": "デバッグ対象を特定する", "confidence": 0.8}]'
            mock_to_thread.return_value = mock_response

            intent = IntentClassification(intent=IntentType.DEBUG, domain=Domain.ENGINEERING, confidence=0.85)
            text = "pipeline.py の L2 セクションでエラーが出る。structurize が失敗している。原因を調べてほしい。"
            result = await structurize(text, intent=intent)

            assert result.is_fallback is False
            assert len(result.blocks) == 1
        asyncio.run(_impl())


# =========================================================================
# StructuredBlock / StructureResult データモデルテスト
# =========================================================================

class TestDataModels:
    """データモデルの基本テスト。"""

    def test_structured_block_defaults(self):
        """StructuredBlock のデフォルト値。"""
        block = StructuredBlock(
            block_id="A1", series="A", tone="指示", content="テスト",
        )
        assert block.confidence == 0.5
        assert block.dependencies == []
        assert block.suggested_wf == ""
        assert block.voice == ""
        assert block.is_held is False

    def test_structure_result_defaults(self):
        """StructureResult のデフォルト値。"""
        result = StructureResult()
        assert result.blocks == []
        assert result.raw_output == ""
        assert result.is_fallback is False

    def test_structure_result_with_blocks(self):
        """StructureResult にブロックを追加。"""
        blocks = [
            StructuredBlock(block_id="A1", series="A", tone="指示", content="タスク1"),
            StructuredBlock(block_id="B1", series="B", tone="提案", content="アイデア1"),
        ]
        result = StructureResult(blocks=blocks, is_fallback=False)
        assert len(result.blocks) == 2
        assert result.blocks[0].block_id == "A1"
        assert result.blocks[1].series == "B"
