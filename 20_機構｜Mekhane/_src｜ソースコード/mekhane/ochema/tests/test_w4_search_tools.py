#!/usr/bin/env python3
# PROOF: [L2/テスト] <- mekhane/ochema/tests/ W4 Tool Search テスト
# PURPOSE: search_tools メタツール、カテゴリフィルタ、プリセットの動作検証
"""
W4: Ochema Tool Search (Category-based Lazy Loading) Tests

Tests:
- Category tagging on HGK tools
- get_tools_by_category / get_tools_by_preset
- search_extended_tools (free-text)
- execute_search_tools integration
- SEARCH_TOOLS_DEFINITION structure
"""

from __future__ import annotations
from mekhane.ochema.tools import (
    SEARCH_TOOLS_DEFINITION,
    HGK_CATEGORIES,
    get_tools_by_category,
    get_tools_by_preset,
    search_extended_tools,
    execute_search_tools,
)
from mekhane.ochema.hgk_tools import HGK_TOOL_DEFINITIONS


class TestCategoryTags:
    """All HGK tools must have a valid category tag."""

    def test_all_tools_have_category(self):
        for t in HGK_TOOL_DEFINITIONS:
            assert "category" in t, f"Tool {t['name']} missing category"

    def test_all_categories_valid(self):
        for t in HGK_TOOL_DEFINITIONS:
            cat = t["category"]
            assert cat in HGK_CATEGORIES, (
                f"Tool {t['name']} has invalid category '{cat}'. "
                f"Valid: {HGK_CATEGORIES}"
            )

    def test_category_distribution(self):
        """Each category should have at least one tool."""
        cats_found = {t["category"] for t in HGK_TOOL_DEFINITIONS}
        assert cats_found == HGK_CATEGORIES


class TestGetToolsByCategory:
    def test_knowledge_category(self):
        tools = get_tools_by_category("knowledge")
        assert len(tools) > 0
        names = {t["name"] for t in tools}
        assert "hgk_pks_search" in names
        assert "hgk_search" in names

    def test_digest_category(self):
        tools = get_tools_by_category("digest")
        names = {t["name"] for t in tools}
        assert "hgk_digest_check" in names
        assert "hgk_digest_run" in names

    def test_all_category(self):
        tools = get_tools_by_category("all")
        assert len(tools) == len(HGK_TOOL_DEFINITIONS)

    def test_invalid_category(self):
        tools = get_tools_by_category("nonexistent")
        assert tools == []


class TestGetToolsByPreset:
    def test_research_preset(self):
        tools = get_tools_by_preset("research")
        names = {t["name"] for t in tools}
        assert "hgk_paper_search" in names
        assert "hgk_pks_search" in names

    def test_digest_preset(self):
        tools = get_tools_by_preset("digest")
        names = {t["name"] for t in tools}
        assert len(names) == 5
        assert "hgk_digest_check" in names

    def test_session_preset(self):
        tools = get_tools_by_preset("session")
        names = {t["name"] for t in tools}
        assert "hgk_handoff_read" in names

    def test_invalid_preset(self):
        tools = get_tools_by_preset("nonexistent")
        assert tools == []


class TestSearchExtendedTools:
    def test_search_by_name_fragment(self):
        results = search_extended_tools("paper")
        names = {t["name"] for t in results}
        assert "hgk_paper_search" in names

    def test_search_by_description(self):
        results = search_extended_tools("handoff")
        names = {t["name"] for t in results}
        assert "hgk_handoff_read" in names

    def test_search_by_category(self):
        results = search_extended_tools("digest")
        assert len(results) >= 5  # All digest tools

    def test_search_no_match(self):
        results = search_extended_tools("zzz_nonexistent_zzz")
        assert results == []


class TestExecuteSearchTools:
    def test_preset_loads_tools(self):
        result = execute_search_tools({"preset": "research"})
        assert "output" in result
        assert "loaded_tools" in result
        assert len(result["loaded_tools"]) > 0
        # loaded_tools should not contain 'category' key
        for t in result["loaded_tools"]:
            assert "category" not in t
            assert "name" in t

    def test_category_loads_tools(self):
        result = execute_search_tools({"category": "ccl"})
        assert len(result["loaded_tools"]) == 2
        names = {t["name"] for t in result["loaded_tools"]}
        assert "hgk_ccl_execute" in names

    def test_query_loads_tools(self):
        result = execute_search_tools({"query": "session"})
        assert len(result["loaded_tools"]) >= 2

    def test_empty_args_lists_options(self):
        result = execute_search_tools({})
        assert "categories" in result["output"].lower()
        assert "presets" in result["output"].lower()
        assert result["loaded_tools"] == []


class TestSearchToolsDefinition:
    """SEARCH_TOOLS_DEFINITION must be a valid Gemini tool definition."""

    def test_has_required_fields(self):
        assert "name" in SEARCH_TOOLS_DEFINITION
        assert "description" in SEARCH_TOOLS_DEFINITION
        assert "parameters" in SEARCH_TOOLS_DEFINITION

    def test_name_is_search_tools(self):
        assert SEARCH_TOOLS_DEFINITION["name"] == "search_tools"

    def test_has_category_param(self):
        props = SEARCH_TOOLS_DEFINITION["parameters"]["properties"]
        assert "category" in props

    def test_has_preset_param(self):
        props = SEARCH_TOOLS_DEFINITION["parameters"]["properties"]
        assert "preset" in props

    def test_has_query_param(self):
        props = SEARCH_TOOLS_DEFINITION["parameters"]["properties"]
        assert "query" in props
