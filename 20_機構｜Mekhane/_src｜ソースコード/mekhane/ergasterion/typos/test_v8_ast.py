#!/usr/bin/env python3
# PROOF: mekhane/ergasterion/typos/test_v8_ast.py
# PURPOSE: ergasterion モジュールの v8_ast に対するテスト
"""Tests for v8 AST pipeline (v8_tokenizer → v8_ast → v8_compiler).

Validates the full AST-based parsing pipeline introduced in RFC v0.4.
"""

import sys
import time
import unittest
from pathlib import Path

# Allow running directly
sys.path.insert(0, str(Path(__file__).parent))

from v8_ast import V8Document, V8Node
from v8_tokenizer import V8Tokenizer, V8ParseError
from v8_compiler import V8Compiler


class TestV8AST(unittest.TestCase):
    """Test v8_ast.py data structures."""

    def test_node_inline(self):
        """V8Node with value is inline."""
        n = V8Node(kind="role", value="Expert", line=1)
        self.assertTrue(n.is_inline)
        self.assertFalse(n.has_children)

    def test_node_block(self):
        """V8Node with text_lines is a block."""
        n = V8Node(kind="constraints", text_lines=["- A", "- B"], line=2)
        self.assertFalse(n.is_inline)
        self.assertEqual(n.text_content, "- A\n- B")

    def test_node_nested(self):
        """V8Node with children is nested."""
        child = V8Node(kind="constraints", text_lines=["- X"], line=3)
        parent = V8Node(kind="if", condition='env == "prod"', children=[child], line=2)
        self.assertTrue(parent.has_children)
        self.assertEqual(parent.find_first("constraints"), child)
        self.assertEqual(parent.find_children("constraints"), [child])

    def test_document_meta(self):
        """V8Document exposes meta via properties."""
        doc = V8Document(
            meta={"prompt": "test", "syntax": "v8", "depth": "L2", "target": "xml"},
        )
        self.assertEqual(doc.name, "test")
        self.assertEqual(doc.syntax_version, "v8")
        self.assertEqual(doc.depth, "L2")
        self.assertEqual(doc.target, "xml")

    def test_document_find(self):
        """V8Document.find_nodes / find_first_node works."""
        n1 = V8Node(kind="role", value="A", line=1)
        n2 = V8Node(kind="goal", value="B", line=2)
        n3 = V8Node(kind="role", value="C", line=3)
        doc = V8Document(root_nodes=[n1, n2, n3])
        self.assertEqual(len(doc.find_nodes("role")), 2)
        self.assertEqual(doc.find_first_node("goal"), n2)
        self.assertIsNone(doc.find_first_node("missing"))


class TestV8Tokenizer(unittest.TestCase):
    """Test v8_tokenizer.py parsing."""

    def test_meta_parsing(self):
        """#prompt, #syntax, #target, #depth are parsed as meta."""
        content = """\
#prompt tokenizer_test
#syntax: v8
#target: xml
#depth: L2

<:role: Expert :>
"""
        doc = V8Tokenizer(content).tokenize()
        self.assertEqual(doc.name, "tokenizer_test")
        self.assertEqual(doc.syntax_version, "v8")
        self.assertEqual(doc.target, "xml")
        self.assertEqual(doc.depth, "L2")

    def test_inline_directive(self):
        """<:role: Expert :> produces an inline V8Node."""
        content = """\
#prompt inline_test
#syntax: v8

<:role: Expert :>
"""
        doc = V8Tokenizer(content).tokenize()
        role_node = doc.find_first_node("role")
        self.assertIsNotNone(role_node)
        self.assertTrue(role_node.is_inline)
        self.assertEqual(role_node.value, "Expert")

    def test_block_directive(self):
        """<:constraints:\n...\n:> produces a block V8Node."""
        content = """\
#prompt block_test
#syntax: v8

<:constraints:
  - Rule one
  - Rule two
:>
"""
        doc = V8Tokenizer(content).tokenize()
        node = doc.find_first_node("constraints")
        self.assertIsNotNone(node)
        self.assertFalse(node.is_inline)
        self.assertGreaterEqual(len(node.text_lines), 2)

    def test_named_close(self):
        """/constraints:> closes the matching block."""
        content = """\
#prompt named_test
#syntax: v8

<:constraints:
  - Deep constraint
/constraints:>
"""
        doc = V8Tokenizer(content).tokenize()
        node = doc.find_first_node("constraints")
        self.assertIsNotNone(node)
        self.assertEqual(node.close_tag, "/constraints:>")

    def test_code_block_protection(self):
        """<: and :> inside ``` are ignored (RFC v0.4)."""
        content = """\
#prompt code_test
#syntax: v8

<:format:
  ```json
  {"key": "<:value:>", "end": ":>"}
  ```
:>
"""
        doc = V8Tokenizer(content).tokenize()
        node = doc.find_first_node("format")
        self.assertIsNotNone(node)
        # The code block content should be preserved raw
        text = node.text_content
        self.assertIn("<:value:>", text)
        self.assertIn(":>", text)

    def test_nested_if(self):
        """<:if cond: ... :> creates a nested structure."""
        content = """\
#prompt if_test
#syntax: v8

<:if env == "prod":
  <:constraints:
    - Production only
  :>
:>
"""
        doc = V8Tokenizer(content).tokenize()
        if_node = doc.find_first_node("if")
        self.assertIsNotNone(if_node)
        self.assertEqual(if_node.condition, 'env == "prod"')
        self.assertTrue(if_node.has_children)
        self.assertEqual(len(if_node.find_children("constraints")), 1)

    def test_multiple_directives(self):
        """Multiple top-level directives are all captured."""
        content = """\
#prompt multi_test
#syntax: v8

<:role: Expert :>
<:goal: Do things :>
<:constraints:
  - A
  - B
:>
"""
        doc = V8Tokenizer(content).tokenize()
        self.assertEqual(len(doc.root_nodes), 3)
        self.assertIsNotNone(doc.find_first_node("role"))
        self.assertIsNotNone(doc.find_first_node("goal"))
        self.assertIsNotNone(doc.find_first_node("constraints"))


class TestV8Compiler(unittest.TestCase):
    """Test v8_compiler.py AST → Prompt conversion."""

    def _make_prompt(self, content: str):
        """Helper: tokenize + compile to Prompt."""
        doc = V8Tokenizer(content).tokenize()
        return V8Compiler(doc).compile()

    def test_basic_compile(self):
        """Basic directives compile to Prompt fields."""
        prompt = self._make_prompt("""\
#prompt basic
#syntax: v8

<:role: Senior Developer :>
<:goal: Write clean code :>
""")
        self.assertEqual(prompt.name, "basic")
        self.assertEqual(prompt.blocks.get("@role"), "Senior Developer")
        self.assertEqual(prompt.blocks.get("@goal"), "Write clean code")

    def test_constraints_compile(self):
        """Constraints block compiles to list."""
        prompt = self._make_prompt("""\
#prompt constr
#syntax: v8

<:role: Tester :>
<:constraints:
  - Rule A
  - Rule B
  - Rule C
:>
""")
        self.assertEqual(len(prompt.blocks.get("@spec", [])), 3)
        self.assertIn("Rule A", prompt.blocks.get("@spec", []))

    def test_tools_compile(self):
        """Tools block compiles to dict."""
        prompt = self._make_prompt("""\
#prompt tools
#syntax: v8

<:role: Dev :>
<:tools:
  - search: Find files
  - edit: Modify code
:>
""")
        self.assertIn("search", prompt.blocks.get("@data", {}))
        self.assertEqual(prompt.blocks.get("@data", {})["edit"], "Modify code")

    def test_examples_compile(self):
        """Examples block compiles to list of dicts."""
        prompt = self._make_prompt("""\
#prompt examples
#syntax: v8

<:role: Demo :>
<:examples:
  - input: hello
    output: world
:>
""")
        self.assertGreaterEqual(len(prompt.blocks.get("@case", [])), 1)

    def test_generic_blocks(self):
        """Unknown directives go to prompt.blocks."""
        prompt = self._make_prompt("""\
#prompt generic
#syntax: v8

<:role: Agent :>
<:intent:
  Understand the system deeply
:>
""")
        self.assertIn("@intent", prompt.blocks)

    def test_target_and_depth(self):
        """#target and #depth flow through to Prompt."""
        prompt = self._make_prompt("""\
#prompt meta
#syntax: v8
#target: xml
#depth: L2

<:role: Meta tester :>
""")
        self.assertEqual(prompt.target, "xml")
        self.assertEqual(prompt.depth, "L2")

    def test_compile_output(self):
        """Compiled prompt produces non-empty output."""
        prompt = self._make_prompt("""\
#prompt output
#syntax: v8

<:role: Compiler :>
<:goal: Generate clean output :>
<:constraints:
  - Be concise
:>
""")
        output = prompt.compile()
        self.assertIn("Compiler", output)
        self.assertIn("Generate clean output", output)

    def test_roundtrip_v8_ast(self):
        """v8 content → tokenize → compile → Prompt fields match."""
        content = """\
#prompt roundtrip
#syntax: v8
#target: typos

<:role: Roundtrip Tester :>
<:goal: Verify AST pipeline integrity :>
<:constraints:
  - Accuracy first
  - Speed second
:>
<:format:
  JSON output with clear structure
:>
"""
        prompt = self._make_prompt(content)
        self.assertEqual(prompt.name, "roundtrip")
        self.assertEqual(prompt.blocks.get("@role"), "Roundtrip Tester")
        self.assertEqual(prompt.blocks.get("@goal"), "Verify AST pipeline integrity")
        self.assertEqual(len(prompt.blocks.get("@spec", [])), 2)
        self.assertIn("JSON", prompt.blocks.get("@format", ""))


class TestV8ASTPerformance(unittest.TestCase):
    """Performance benchmarks for the AST pipeline."""

    def test_large_document_performance(self):
        """700+ line document tokenizes + compiles in < 1 second."""
        lines = ["#prompt perf_ast", "#syntax: v8", ""]
        lines.append("<:role: Benchmark Subject :>")
        lines.append("<:goal: Parse efficiently :>")
        lines.append("")

        # 60 constraints
        lines.append("<:constraints:")
        for i in range(60):
            lines.append(f"  - Constraint {i}: quality metric {i}")
        lines.append(":>")
        lines.append("")

        # 80 generic blocks × 7 lines each = 560 lines
        for i in range(80):
            lines.append(f"<:block_{i}:")
            for k in range(5):
                lines.append(f"  Content line {k} of block {i}")
            lines.append(":>")
            lines.append("")

        # Tools
        lines.append("<:tools:")
        for i in range(20):
            lines.append(f"  - tool_{i}: Description {i}")
        lines.append(":>")

        content = "\n".join(lines)
        self.assertGreater(len(lines), 700)

        start = time.monotonic()
        doc = V8Tokenizer(content).tokenize()
        prompt = V8Compiler(doc).compile()
        elapsed = time.monotonic() - start

        self.assertEqual(prompt.name, "perf_ast")
        self.assertEqual(prompt.blocks.get("@role"), "Benchmark Subject")
        self.assertEqual(len(prompt.blocks.get("@spec", [])), 60)
        self.assertEqual(len(prompt.blocks.get("@data", {})), 20)
        self.assertLess(elapsed, 1.0, f"AST pipeline took {elapsed:.3f}s")


if __name__ == "__main__":
    unittest.main(verbosity=2)
