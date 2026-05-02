# PROOF: mekhane/kube/tests/test_prompt_parse.py
# PURPOSE: kube モジュールの prompt_parse に対するテスト
import pytest
import tempfile
import json
import os
from pathlib import Path

# MCP Typos の compile ツールを直接呼ぶのではなく、TyposParser を利用するか、
# プロンプトのフォーマット要件（JSON抽出）をテストする E2E クラス。
# ここでは KubeAgent が Ochema (gemini) のテキスト出力から正しく JSON を
# 抽出できるかのロジックをテストする。

def extract_json_from_response(text: str) -> dict:
    """LLM の応答テキストから JSON ブロックを抽出してパースする"""
    text = text.strip()
    
    # 1. ```json ブロックの抽出
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end != -1:
            json_str = text[start:end].strip()
            return json.loads(json_str)
            
    # 2. ``` ブロックの抽出
    if "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end != -1:
            json_str = text[start:end].strip()
            return json.loads(json_str)
            
    # 3. { } で囲まれた部分の抽出（一番外側のブレース）
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        json_str = text[start:end+1]
        return json.loads(json_str)
        
    raise ValueError("No valid JSON found in response")

class TestPromptParsing:
    
    def test_planner_normal_response(self):
        # Planner プロンプトが期待する出力形式のモック
        llm_response = """
Here is the plan.
```json
{
  "goal_understanding": "Google で旅行先を検索する",
  "feasibility": "possible",
  "rejection_reason": null,
  "subgoals": [
    {
      "id": 1,
      "description": "Google で検索",
      "security_level": "read",
      "depends_on": [],
      "expected_actions": 3,
      "success_criteria": "検索結果",
      "failure_fallback": null
    }
  ],
  "estimated_total_actions": 3,
  "estimated_time_seconds": 10,
  "requires_login": false,
  "requires_payment": false,
  "warnings": []
}
```
"""
        result = extract_json_from_response(llm_response)
        assert result["feasibility"] == "possible"
        assert len(result["subgoals"]) == 1
        assert result["subgoals"][0]["security_level"] == "read"

    def test_decider_normal_response(self):
        llm_response = """
```json
{
  "thinking": "ボタンが見えるのでクリック",
  "action": "click",
  "args": {
    "ref": "btn1"
  },
  "confidence": 0.9,
  "security_level": "read",
  "confirm_required": false,
  "extractions": null
}
```
"""
        result = extract_json_from_response(llm_response)
        assert result["action"] == "click"
        assert result["args"]["ref"] == "btn1"
        assert result["security_level"] == "read"

    def test_no_markdown_block(self):
        llm_response = """
{
  "action": "scroll_down",
  "args": {},
  "confidence": 0.8,
  "security_level": "read",
  "confirm_required": false,
  "extractions": null
}
"""
        result = extract_json_from_response(llm_response)
        assert result["action"] == "scroll_down"
