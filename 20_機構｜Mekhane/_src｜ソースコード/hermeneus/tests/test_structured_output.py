import pytest
from jsonschema import ValidationError
from hermeneus.src.macro_executor import _extract_structured_meta, ExecutionContext
from hermeneus.src.schemas import get_schema

class TestStructuredOutput:
    
    def test_extract_valid_json(self):
        """正しい JSON ブロックが抽出・パースできるか"""
        text = """思考過程...
```json
{
  "findings": ["発見A", "発見B"],
  "confidence": 0.8,
  "summary": "テスト成功"
}
```
"""
        clean, meta = _extract_structured_meta(text)
        assert "思考過程..." in clean
        assert "```json" not in clean
        assert meta["confidence"] == 0.8
        assert len(meta["findings"]) == 2

    def test_extract_invalid_schema(self):
        """スキーマを満たさない JSON の場合でも抽出はされる (現状はログ警告のみで返す方針)"""
        text = """
```json
{
  "confidence": "これは数値じゃない"
}
```
"""
        clean, meta = _extract_structured_meta(text)
        # Phase 1 の段階ではエラーで落とさず、抽出したものをそのまま返す仕様にしている
        assert meta["confidence"] == "これは数値じゃない"

    def test_extract_no_json(self):
        """JSON ブロックが存在しない場合"""
        text = "普通にテキストだけが返ってきた場合。"
        clean, meta = _extract_structured_meta(text)
        assert clean == text
        assert meta == {}

    def test_execution_context_push_structured(self):
        """ExecutionContext.push_structured で構造化データが蓄積されるか"""
        ctx = ExecutionContext()
        meta1 = {
            "findings": ["F1"],
            "confidence": 0.5,
            "summary": "Sum1"
        }
        ctx.push_structured("output1", "step1", meta1)
        
        assert ctx.structured["findings"] == ["F1"]
        assert ctx.structured["confidence"] == 0.5
        assert ctx.structured["phase_summary"]["step1"] == "Sum1"
        
        meta2 = {
            "findings": ["F2"],
            "open_questions": ["Q1"],
            "confidence": 0.9,
            "summary": "Sum2"
        }
        ctx.push_structured("output2", "step2", meta2)
        
        assert ctx.structured["findings"] == ["F1", "F2"]  # 追記される
        assert ctx.structured["open_questions"] == ["Q1"]
        assert ctx.structured["confidence"] == 0.9  # 上書きされる
        assert ctx.structured["phase_summary"]["step2"] == "Sum2"
        
    def test_get_schema(self):
        schema = get_schema("_default")
        assert "findings" in schema["properties"]
        assert "confidence" in schema["required"]
