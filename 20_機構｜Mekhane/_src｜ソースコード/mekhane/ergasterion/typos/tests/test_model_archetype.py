# PROOF: mekhane/ergasterion/typos/tests/test_model_archetype.py
# PURPOSE: ergasterion モジュールの model_archetype に対するテスト
import os
import pytest
from mekhane.ergasterion.typos.typos import Prompt, PromptLangParser

def test_gemini_xml_wrapping():
    content = """#prompt test_gemini
@role:
  You are a test assistant.
@constraints:
  - Do this.
  - Do that.
"""
    parser = PromptLangParser(content)
    prompt = parser.parse()
    compiled = prompt.compile(model="gemini")
    
    # Gemini archetype wraps role in <role> and constraints in <instructions>
    assert "<role>\nYou are a test assistant.\n</role>" in compiled
    assert "<instructions>\n- Do this.\n- Do that.\n</instructions>" in compiled
    # simple task thinking hint
    assert "Think silently for simple tasks." in compiled

def test_claude_contract_style():
    content = """#prompt test_claude
@role:
  You are a Claude test assistant.
@constraints:
  - Do this.
  - Never do that.
  - Avoid hallucination.
"""
    parser = PromptLangParser(content)
    prompt = parser.parse()
    compiled = prompt.compile(model="claude")
    
    # Claude archetype uses prose role, no thinking hint
    assert "You are a Claude test assistant." in compiled
    assert "<role>" not in compiled
    assert "Think silently" not in compiled
    # Contract-style: positive → MUST, negative → MUST NOT
    assert "**MUST**: Do this." in compiled
    assert "**MUST NOT**: Never do that." in compiled
    assert "**MUST NOT**: Avoid hallucination." in compiled

def test_openai_cot_hint():
    content = """#prompt test_openai
@role:
  You are an OpenAI test assistant.
@constraints:
  - Do this.
  - Do that too.
"""
    parser = PromptLangParser(content)
    prompt = parser.parse()
    compiled = prompt.compile(model="openai")
    
    # OpenAI doesn't wrap role in xml
    assert "You are an OpenAI test assistant." in compiled
    assert "<role>" not in compiled
    # Explicit numbered constraints
    assert "1. Do this." in compiled
    assert "2. Do that too." in compiled
    assert "Strictly follow ALL constraints" in compiled
    # CoT hint
    assert "Let's think step by step" in compiled
    # JSON format hint
    assert "Response Format" in compiled
    assert "valid JSON" in compiled

def test_claude_negation_detection():
    """Test that various negation patterns are correctly detected."""
    content = """#prompt test_neg
@role:
  Test
@constraints:
  - Do not generate fake data.
  - Don't repeat yourself.
  - Write clearly.
"""
    parser = PromptLangParser(content)
    prompt = parser.parse()
    compiled = prompt.compile(model="claude")
    
    assert "**MUST NOT**: Do not generate fake data." in compiled
    assert "**MUST NOT**: Don't repeat yourself." in compiled
    assert "**MUST**: Write clearly." in compiled

def test_auto_detection():
    # Detect Gemini
    prompt_gemini = Prompt(name="test")
    assert prompt_gemini._detect_model("Gemini 1.5 Pro を使って回答してください。") == "gemini"
    
    # Detect Claude
    prompt_claude = Prompt(name="test")
    assert prompt_claude._detect_model("Claude 3 Opus 向けにプロンプトを作成。") == "claude"
    
    # Detect OpenAI
    prompt_openai = Prompt(name="test")
    assert prompt_openai._detect_model("gpt-4o を想定して出力して。") == "openai"
    
    # Detect default/fallback (None when not detected, handled by default logic)
    prompt_default = Prompt(name="test")
    assert prompt_default._detect_model("一般的なLLM用タスク。") is None

def test_archetype_yaml_loading():
    # Calling internal method
    gemini_config = Prompt._load_archetype("gemini")
    assert gemini_config is not None
    assert gemini_config["role_format"] == "xml"
    assert "instructions" in gemini_config["xml_tags"]
    
    claude_config = Prompt._load_archetype("claude")
    assert claude_config is not None
    assert claude_config["constraint_style"] == "contract"
    
    openai_config = Prompt._load_archetype("openai")
    assert openai_config is not None
    assert openai_config["instruction_format"] == "json"
    assert openai_config["constraint_style"] == "explicit"
    
    unknown = Prompt._load_archetype("unknown_model")
    assert unknown is None
