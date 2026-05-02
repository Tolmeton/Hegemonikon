# PROOF: mekhane/kube/tests/test_playwright_bridge.py
# PURPOSE: kube モジュールの playwright_bridge に対するテスト
"""
PlaywrightBridge テスト: CDP AXTree パース + ネスト変換を検証する。

消去テスト: playwright_bridge.py を消すとこのテストが壊れる。
"""
import pytest
from mekhane.kube.playwright_bridge import PlaywrightBridge, PageState, ActionResult


class TestBuildNestedTree:
    """CDP getFullAXTree のフラットリスト → ネストツリー変換のテスト"""

    def test_single_root(self):
        bridge = PlaywrightBridge.__new__(PlaywrightBridge)
        nodes = [
            {"nodeId": "1", "role": {"value": "WebArea"}, "name": {"value": "Page"},
             "childIds": [], "properties": []},
        ]
        tree = bridge._build_nested_tree(nodes)
        assert tree["role"] == "WebArea"
        assert tree["name"] == "Page"
        assert tree["children"] == []

    def test_nested_children(self):
        bridge = PlaywrightBridge.__new__(PlaywrightBridge)
        nodes = [
            {"nodeId": "1", "role": {"value": "WebArea"}, "name": {"value": "Page"},
             "childIds": ["2", "3"], "properties": []},
            {"nodeId": "2", "role": {"value": "button"}, "name": {"value": "Submit"},
             "childIds": [], "properties": []},
            {"nodeId": "3", "role": {"value": "textbox"}, "name": {"value": "Search"},
             "childIds": [], "properties": [
                 {"name": "value", "value": {"value": "hello"}},
             ]},
        ]
        tree = bridge._build_nested_tree(nodes)
        assert len(tree["children"]) == 2
        assert tree["children"][0]["role"] == "button"
        assert tree["children"][0]["name"] == "Submit"
        assert tree["children"][1]["value"] == "hello"

    def test_deep_nesting(self):
        bridge = PlaywrightBridge.__new__(PlaywrightBridge)
        nodes = [
            {"nodeId": "1", "role": {"value": "WebArea"}, "name": {"value": ""},
             "childIds": ["2"], "properties": []},
            {"nodeId": "2", "role": {"value": "main"}, "name": {"value": ""},
             "childIds": ["3"], "properties": []},
            {"nodeId": "3", "role": {"value": "heading"}, "name": {"value": "Title"},
             "childIds": [], "properties": []},
        ]
        tree = bridge._build_nested_tree(nodes)
        assert tree["children"][0]["children"][0]["name"] == "Title"

    def test_disabled_property(self):
        bridge = PlaywrightBridge.__new__(PlaywrightBridge)
        nodes = [
            {"nodeId": "1", "role": {"value": "button"}, "name": {"value": "OK"},
             "childIds": [], "properties": [
                 {"name": "disabled", "value": {"value": True}},
             ]},
        ]
        tree = bridge._build_nested_tree(nodes)
        assert tree["disabled"] is True

    def test_empty_nodes(self):
        bridge = PlaywrightBridge.__new__(PlaywrightBridge)
        tree = bridge._build_nested_tree([])
        assert tree == {}


class TestSerializeA11yTree:
    """Accessibility Tree のシリアライズテスト"""

    def test_basic_serialization(self):
        bridge = PlaywrightBridge.__new__(PlaywrightBridge)
        tree = {
            "role": "WebArea", "name": "Page",
            "value": None, "checked": None, "disabled": False,
            "children": [
                {"role": "button", "name": "Click me",
                 "value": None, "checked": None, "disabled": False,
                 "children": []},
            ],
        }
        text = bridge._serialize_a11y_tree(tree)
        assert "button" in text
        assert "Click me" in text


class TestCountInteractive:
    """インタラクティブ要素のカウントテスト"""

    def test_counts_interactive_roles(self):
        bridge = PlaywrightBridge.__new__(PlaywrightBridge)
        tree = {
            "role": "WebArea", "name": "", "value": None, "checked": None,
            "disabled": False,
            "children": [
                {"role": "button", "name": "A", "value": None, "checked": None,
                 "disabled": False, "children": []},
                {"role": "textbox", "name": "B", "value": None, "checked": None,
                 "disabled": False, "children": []},
                {"role": "link", "name": "C", "value": None, "checked": None,
                 "disabled": False, "children": []},
                {"role": "heading", "name": "D", "value": None, "checked": None,
                 "disabled": False, "children": []},
            ],
        }
        count = bridge._count_interactive(tree)
        assert count == 3  # button, textbox, link — heading は非 interactive


class TestPageState:
    """PageState データクラスのテスト"""

    def test_creation(self):
        state = PageState(url="https://x.com", title="X", snapshot="...", interactive_count=5)
        assert state.url == "https://x.com"
        assert state.interactive_count == 5

    def test_default_values(self):
        state = PageState(url="", title="", snapshot="", interactive_count=0)
        assert state.snapshot == ""


class TestActionResult:
    """ActionResult データクラスのテスト"""

    def test_success(self):
        r = ActionResult(success=True)
        assert r.success is True
        assert r.error is None

    def test_failure_with_error(self):
        r = ActionResult(success=False, error="timeout")
        assert r.success is False
        assert r.error == "timeout"
