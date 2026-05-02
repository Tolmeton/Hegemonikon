#!/usr/bin/env python3
"""
Tests for fix_mcp_smell.py — MCP Tool Description Auto-Fixer

Tests:
  1. _detect_missing: smell detection logic
  2. generate_return_text: return text patterns
  3. generate_example_text: example text generation
  4. generate_error_text: error condition generation
  5. build_suffix: combined suffix building
  6. _insert_suffix: source code rewriting (ASCII)
  7. _insert_suffix: source code rewriting (Japanese UTF-8)
  8. apply_fixes: end-to-end dry_run vs apply
"""

import ast
import sys
import tempfile
import textwrap
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.fix_mcp_smell import (
    ToolInfo,
    _detect_missing,
    generate_return_text,
    generate_example_text,
    generate_error_text,
    build_suffix,
    _insert_suffix,
    apply_fixes,
    extract_tools_deep,
)


# ============ _detect_missing ============

def test_detect_missing_all():
    """Description with nothing → all 3 missing."""
    result = _detect_missing("Simply does something.")
    assert "missing_return" in result
    assert "missing_example" in result
    assert "missing_error" in result


def test_detect_missing_none():
    """Description with all elements → nothing missing."""
    result = _detect_missing(
        "Returns: a result. Example: foo() Errors if param is missing."
    )
    assert result == []


def test_detect_missing_partial():
    """Description with Returns but no Example/Error."""
    result = _detect_missing("Returns: something useful.")
    assert "missing_return" not in result
    assert "missing_example" in result
    assert "missing_error" in result


def test_detect_missing_japanese_example():
    """Japanese 例 counts as example."""
    result = _detect_missing("例: foo() をやる")
    assert "missing_example" not in result


# ============ generate_return_text ============

def test_return_text_ping():
    tool = ToolInfo("ping", "", {}, None, 0, 0)
    assert "pong" in generate_return_text(tool)


def test_return_text_search():
    tool = ToolInfo("periskope_search", "", {}, None, 0, 0)
    assert "matching results" in generate_return_text(tool)


def test_return_text_status():
    tool = ToolInfo("sympatheia_status", "", {}, None, 0, 0)
    assert "statistics" in generate_return_text(tool).lower() or "status" in generate_return_text(tool).lower()


def test_return_text_fallback():
    tool = ToolInfo("unknown_verb_xyz", "", {}, None, 0, 0)
    result = generate_return_text(tool)
    assert "Returns:" in result  # fallback still produces something


# ============ generate_example_text ============

def test_example_text_with_required():
    tool = ToolInfo(
        "paper_search", "", 
        {"properties": {"query": {"type": "string"}}, "required": ["query"]},
        None, 0, 0,
    )
    result = generate_example_text(tool)
    assert "paper_search(" in result
    assert "query=" in result


def test_example_text_no_params():
    tool = ToolInfo("ping", "", {}, None, 0, 0)
    result = generate_example_text(tool)
    assert "ping()" in result


# ============ generate_error_text ============

def test_error_text_with_required():
    tool = ToolInfo(
        "foo", "", {"required": ["bar", "baz"]}, None, 0, 0,
    )
    result = generate_error_text(tool)
    assert "bar" in result
    assert "baz" in result


def test_error_text_no_required():
    tool = ToolInfo("foo", "", {}, None, 0, 0)
    result = generate_error_text(tool)
    assert "invalid input" in result.lower() or "internal" in result.lower()


# ============ build_suffix ============

def test_build_suffix_all_missing():
    tool = ToolInfo("search_papers", "", {}, None, 0, 0, 
                    missing=["missing_return", "missing_example", "missing_error"])
    suffix = build_suffix(tool)
    assert "Returns:" in suffix
    assert "Example:" in suffix
    assert "Errors" in suffix


def test_build_suffix_nothing_missing():
    tool = ToolInfo("search_papers", "", {}, None, 0, 0, missing=[])
    suffix = build_suffix(tool)
    assert suffix == ""


# ============ _insert_suffix (ASCII) ============

def test_insert_suffix_simple_ascii():
    """Insert suffix into a simple ASCII string."""
    code = 'description="Hello world",'
    tree = ast.parse(f'Tool({code})')
    # Find the description keyword
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "description":
            desc_node = node.value
            break
    
    lines = [f'Tool({code})']
    result = _insert_suffix(lines, desc_node, "SUFFIX")
    assert result is True
    assert "SUFFIX" in lines[0]
    assert lines[0].endswith('",)')  # closing quote + trailing comma preserved


def test_insert_suffix_japanese():
    """Insert suffix into Japanese multi-line concatenated string."""
    code = textwrap.dedent('''\
        Tool(
            name="test",
            description=(
                "日本語の説明文。"
                "二行目の日本語。"
            ),
        )
    ''')
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "description":
            desc_node = node.value
            break
    
    lines = code.split("\n")
    result = _insert_suffix(lines, desc_node, "ADDED")
    assert result is True
    # The suffix should be inserted somewhere in the source
    joined = "\n".join(lines)
    assert "ADDED" in joined


# ============ apply_fixes (end-to-end) ============

def test_apply_fixes_dry_run():
    """Dry run should propose but not modify."""
    code = textwrap.dedent('''\
        from mcp.types import Tool
        tools = [
            Tool(
                name="my_tool",
                description="Does something.",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]
    ''')
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        filepath = Path(f.name)
    
    try:
        tools = extract_tools_deep(filepath)
        assert len(tools) == 1
        assert tools[0].missing  # should have missing elements
        
        changes = apply_fixes(filepath, tools, dry_run=True)
        assert len(changes) > 0
        assert all(not c["applied"] for c in changes)
        
        # File should be unchanged
        assert filepath.read_text() == code
    finally:
        filepath.unlink()


def test_apply_fixes_apply():
    """Apply should modify the file."""
    code = textwrap.dedent('''\
        from mcp.types import Tool
        tools = [
            Tool(
                name="my_search",
                description="Search for things.",
                inputSchema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            ),
        ]
    ''')
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        filepath = Path(f.name)
    
    try:
        tools = extract_tools_deep(filepath)
        changes = apply_fixes(filepath, tools, dry_run=False)
        assert len(changes) > 0
        assert any(c["applied"] for c in changes)
        
        # File should now contain Returns/Example/Errors
        new_content = filepath.read_text()
        assert "Returns:" in new_content
        assert "Example:" in new_content
        assert "Errors" in new_content
    finally:
        filepath.unlink()


def test_apply_fixes_japanese_multiline():
    """Apply should handle Japanese multi-line strings correctly."""
    code = textwrap.dedent('''\
        from mcp.types import Tool
        tools = [
            Tool(
                name="jp_tool",
                description=(
                    "日本語の説明文です。"
                    "これはテストの二行目。"
                ),
                inputSchema={"type": "object", "properties": {}},
            ),
        ]
    ''')
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        filepath = Path(f.name)
    
    try:
        tools = extract_tools_deep(filepath)
        assert len(tools) == 1
        
        changes = apply_fixes(filepath, tools, dry_run=False)
        assert any(c["applied"] for c in changes)
        
        new_content = filepath.read_text()
        assert "Returns:" in new_content
        
        # Verify the file is still valid Python
        ast.parse(new_content)
    finally:
        filepath.unlink()


# ============ Runner ============

if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
