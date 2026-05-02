# PROOF: [L2/テスト] <- mekhane/ergasterion/typos/test_v8.py S2→v8 AST パイプラインのテストが必要→test_v8 が担う
"""Typos v8 AST パイプライン専用テスト.

テスト対象:
  - V8Tokenizer: テキスト → V8Document (AST)
  - V8Compiler: V8Document → Prompt
  - 統合: テキスト → Prompt (parse() 経由)
"""

import unittest
from pathlib import Path

from mekhane.ergasterion.typos.v8_ast import V8Node, V8Document
from mekhane.ergasterion.typos.v8_tokenizer import V8Tokenizer, V8ParseError
from mekhane.ergasterion.typos.v8_compiler import V8Compiler


class TestV8Tokenizer(unittest.TestCase):
    """V8Tokenizer のユニットテスト。"""

    def test_inline_directive(self):
        """<:name: value :> がインラインノードになる。"""
        doc = V8Tokenizer("#prompt test\n#syntax: v8\n\n<:role: Expert :>").tokenize()
        self.assertEqual(doc.name, "test")
        self.assertEqual(len(doc.root_nodes), 1)
        node = doc.root_nodes[0]
        self.assertEqual(node.kind, "role")
        self.assertEqual(node.value, "Expert")
        self.assertTrue(node.is_inline)

    def test_block_directive(self):
        """複数行ブロックが text_lines を持つ。"""
        doc = V8Tokenizer(
            "#prompt test\n#syntax: v8\n\n"
            "<:constraints:\n  - itemA\n  - itemB\n:>"
        ).tokenize()
        self.assertEqual(len(doc.root_nodes), 1)
        node = doc.root_nodes[0]
        self.assertEqual(node.kind, "constraints")
        self.assertEqual(len(node.text_lines), 2)
        self.assertIn("itemA", node.text_lines[0])

    def test_named_close_tag(self):
        """/name:> で名前付き閉じタグが機能する。"""
        doc = V8Tokenizer(
            "#prompt test\n#syntax: v8\n\n"
            "<:constraints:\n  - item1\n/constraints:>"
        ).tokenize()
        node = doc.root_nodes[0]
        self.assertEqual(node.close_tag, "/constraints:>")

    def test_nested_blocks(self):
        """ネストされたブロックが children になる。"""
        doc = V8Tokenizer(
            "#prompt test\n#syntax: v8\n\n"
            "<:rubric:\n  <:dimension:\n    name: accuracy\n  /dimension:>\n/rubric:>"
        ).tokenize()
        rubric = doc.root_nodes[0]
        self.assertEqual(rubric.kind, "rubric")
        self.assertEqual(len(rubric.children), 1)
        dim = rubric.children[0]
        self.assertEqual(dim.kind, "dimension")

    def test_if_else_group(self):
        """<:if ... <:else: .../if:> が正しくグループ化される。"""
        doc = V8Tokenizer(
            "#prompt test\n#syntax: v8\n\n"
            "<:if env == \"prod\":\n"
            "  <:constraints:\n    - strict\n  :>\n"
            "<:else:\n"
            "  <:constraints:\n    - lenient\n  :>\n"
            "/if:>"
        ).tokenize()
        if_node = doc.root_nodes[0]
        self.assertEqual(if_node.kind, "if")
        self.assertEqual(if_node.condition, 'env == "prod"')
        # children: constraints (direct) + else node
        self.assertEqual(len(if_node.children), 2)
        self.assertEqual(if_node.children[0].kind, "constraints")
        self.assertEqual(if_node.children[1].kind, "else")

    def test_code_block_protection(self):
        """``` 内の <: :> はパースされない。"""
        doc = V8Tokenizer(
            "#prompt test\n#syntax: v8\n\n"
            "<:format:\n  ```json\n  <:fake: inside :>\n  ```\n/format:>"
        ).tokenize()
        fmt = doc.root_nodes[0]
        self.assertEqual(fmt.kind, "format")
        self.assertEqual(len(fmt.children), 0)  # <:fake: は無視
        self.assertTrue(any("<:fake:" in l for l in fmt.text_lines))

    def test_unclosed_block_error(self):
        """閉じ忘れが V8ParseError を発生させる。"""
        with self.assertRaises(V8ParseError):
            V8Tokenizer(
                "#prompt test\n#syntax: v8\n\n<:constraints:\n  - item\n"
            ).tokenize()

    def test_mismatched_named_close_error(self):
        """名前不一致の /name:> が V8ParseError を発生させる。"""
        with self.assertRaises(V8ParseError):
            V8Tokenizer(
                "#prompt test\n#syntax: v8\n\n<:constraints:\n  - item\n/format:>"
            ).tokenize()


class TestV8Compiler(unittest.TestCase):
    """V8Compiler のユニットテスト。"""

    def _compile(self, text: str):
        doc = V8Tokenizer(text).tokenize()
        return V8Compiler(doc).compile()

    def test_compile_basic_fields(self):
        """role, goal, format がコンパイルされる。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:role: Expert :>\n"
            "<:goal: Do things :>\n"
            "<:format: JSON :>"
        )
        self.assertEqual(p.blocks.get("@role"), "Expert")
        self.assertEqual(p.blocks.get("@goal"), "Do things")
        self.assertEqual(p.blocks.get("@format"), "JSON")

    def test_compile_constraints_list(self):
        """constraints のリスト項目がパースされる。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:constraints:\n  - A\n  - B\n  - C\n:>"
        )
        self.assertEqual(p.blocks.get("@spec", []), ["A", "B", "C"])

    def test_compile_rubric_with_dimension(self):
        """rubric の dimension ノードがコンパイルされる。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:rubric:\n"
            "  <:dimension:\n"
            "    name: accuracy\n"
            "    description: How accurate\n"
            "    scale: 1-5\n"
            "  /dimension:>\n"
            "/rubric:>"
        )
        self.assertIn("@schema", p.blocks)
        self.assertEqual(len(p.blocks.get("@schema").dimensions), 1)
        dim = p.blocks.get("@schema").dimensions[0]
        self.assertEqual(dim.name, "accuracy")
        self.assertEqual(dim.scale, "1-5")

    def test_compile_if_else_conditions(self):
        """if/else が Condition として再帰コンパイルされる。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:if env == \"prod\":\n"
            "  <:constraints:\n    - strict\n  :>\n"
            "<:else:\n"
            "  <:constraints:\n    - lenient\n  :>\n"
            "/if:>"
        )
        self.assertEqual(len(p.conditions), 1)
        c = p.conditions[0]
        self.assertEqual(c.variable, "env")
        self.assertEqual(c.operator, "==")
        self.assertEqual(c.value, "prod")
        # if_content は展開された Prompt dict
        self.assertIn("blocks", c.if_content)
        self.assertIn("@spec", c.if_content["blocks"])
        self.assertIn("strict", c.if_content["blocks"]["@spec"])
        self.assertIn("blocks", c.else_content)
        self.assertIn("@spec", c.else_content["blocks"])
        self.assertIn("lenient", c.else_content["blocks"]["@spec"])

    def test_compile_examples(self):
        """examples の input/output がコンパイルされる。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:examples:\n"
            "  <:example:\n"
            "    <:input: hello :>\n"
            "    <:output: world :>\n"
            "  /example:>\n"
            "/examples:>"
        )
        self.assertEqual(len(p.blocks.get("@case", [])), 1)
        self.assertEqual(p.blocks.get("@case", [])[0]["input"], "hello")
        self.assertEqual(p.blocks.get("@case", [])[0]["output"], "world")

    def test_compile_generic_blocks(self):
        """未知のディレクティブが blocks に格納される。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:unknown: Background info :>"
        )
        self.assertIn("@unknown", p.blocks)
        self.assertEqual(p.blocks["@unknown"], "Background info")


class TestV8Integration(unittest.TestCase):
    """PromptLangParser 経由の統合テスト。"""

    def test_parse_via_parser(self):
        """PromptLangParser.parse() が v8 AST パイプラインを使う。"""
        from mekhane.ergasterion.typos.typos import PromptLangParser
        content = (
            "#prompt test-v8-integration\n#syntax: v8\n\n"
            "<:role: Tester :>\n"
            "<:constraints:\n  - Rule1\n:>"
        )
        p = PromptLangParser(content).parse()
        self.assertEqual(p.name, "test-v8-integration")
        self.assertEqual(p.blocks.get("@role"), "Tester")
        self.assertEqual(p.blocks.get("@spec", []), ["Rule1"])
        self.assertEqual(p.syntax_version, "v8")

    def test_demo_v8_full_parse(self):
        """demo_v8.prompt の完全パース。"""
        from mekhane.ergasterion.typos.typos import PromptLangParser
        demo = Path(__file__).parent / "demo_v8.prompt"
        if not demo.exists():
            self.skipTest("demo_v8.prompt not found")
        content = demo.read_text()
        p = PromptLangParser(content).parse()
        self.assertEqual(p.name, "demo-v8-test")
        self.assertEqual(p.syntax_version, "v8")
        self.assertIsNotNone(p.blocks.get("@role"))
        self.assertEqual(len(p.blocks.get("@spec", [])), 3)
        # schema (Which族) は L3 のみ有効。demo_v8 は L2 なのでスキップされる
        self.assertIsNone(p.blocks.get("@schema"))
        self.assertEqual(len(p.conditions), 1)
        self.assertEqual(len(p.blocks.get("@case", [])), 1)


class TestDepthLevelSystem(unittest.TestCase):
    """深度レベルシステム (L0-L3) のテスト。"""

    def _compile_with_depth(self, depth: str, body: str) -> dict:
        """指定深度で body をコンパイルし blocks を返す。"""
        src = f"#prompt test\n#syntax: v8\n#depth: {depth}\n\n{body}"
        doc = V8Tokenizer(src).tokenize()
        prompt = V8Compiler(doc).compile()
        return prompt.blocks

    def test_l0_skips_v7_directives(self):
        """L0 では V7 ディレクティブがスキップされる。"""
        body = "<:role: Expert :>\n<:spec:\n  - rule1\n:>\n<:intent:\n  why\n:>"
        blocks = self._compile_with_depth("L0", body)
        # role は V7 外なので常に有効
        self.assertIn("@role", blocks)
        # spec, intent は V7 ディレクティブ → L0 ではスキップ
        self.assertNotIn("@spec", blocks)
        self.assertNotIn("@intent", blocks)

    def test_l1_allows_why_and_how(self):
        """L1 では Why族・How族は有効、When族はスキップ。"""
        body = (
            "<:role: Expert :>\n"
            "<:spec:\n  - rule1\n:>\n"       # How族 → 有効
            "<:intent:\n  why\n:>\n"          # Why族 → 有効
            "<:fact:\n  some fact\n:>"         # When族 → L1 ではスキップ
        )
        blocks = self._compile_with_depth("L1", body)
        self.assertIn("@spec", blocks)
        self.assertIn("@intent", blocks)
        self.assertNotIn("@fact", blocks)

    def test_l2_allows_salience_and_context(self):
        """L2 では How-much族・Where族も有効、Which族はスキップ。"""
        body = (
            "<:step:\n  - step1\n:>\n"        # Where族 → 有効
            "<:focus:\n  - focus1\n:>\n"       # How-much族 → 有効
            "<:data:\n  key: value\n:>\n"      # Which族 → L2 ではスキップ
        )
        blocks = self._compile_with_depth("L2", body)
        self.assertIn("@step", blocks)
        self.assertIn("@focus", blocks)
        self.assertNotIn("@data", blocks)

    def test_l3_allows_all(self):
        """L3 では全24種が有効。"""
        body = (
            "<:fact:\n  some fact\n:>\n"       # When族
            "<:data:\n  key: value\n:>\n"      # Which族
            "<:spec:\n  - rule1\n:>\n"         # How族
        )
        blocks = self._compile_with_depth("L3", body)
        self.assertIn("@fact", blocks)
        self.assertIn("@data", blocks)
        self.assertIn("@spec", blocks)

    def test_default_depth_is_l3(self):
        """depth 未指定時はデフォルト L3 (全開放)。"""
        src = "#prompt test\n#syntax: v8\n\n<:fact:\n  a fact\n:>"
        doc = V8Tokenizer(src).tokenize()
        prompt = V8Compiler(doc).compile()
        self.assertIn("@fact", prompt.blocks)

    def test_legacy_spec_allowed_at_l0_via_mapping(self):
        """L0 でも role は常に有効 (V7 外)。"""
        body = "<:role: Expert :>"
        blocks = self._compile_with_depth("L0", body)
        self.assertIn("@role", blocks)
        self.assertEqual(blocks["@role"], "Expert")


class TestV8Identifiers(unittest.TestCase):
    """v8.4 識別子ディレクティブのテスト。"""

    def test_identifier_inline_hyphen(self):
        """S-01a ハイフン形式のインライン識別子。"""
        doc = V8Tokenizer(
            "#prompt test\n#syntax: v8\n\n<:S-01a: 仮説α :>"
        ).tokenize()
        node = doc.root_nodes[0]
        self.assertEqual(node.kind, "S-01a")
        self.assertEqual(node.prefix, "S")
        self.assertEqual(node.address, "01a")
        self.assertEqual(node.value, "仮説α")
        self.assertTrue(node.is_identifier)

    def test_identifier_inline_bracket(self):
        """S[01a] ブラケット形式 (ハイフン省略)。"""
        doc = V8Tokenizer(
            "#prompt test\n#syntax: v8\n\n<:S[01a]: 仮説β :>"
        ).tokenize()
        node = doc.root_nodes[0]
        self.assertEqual(node.kind, "S[01a]")
        self.assertEqual(node.prefix, "S")
        self.assertEqual(node.address, "01a")

    def test_identifier_inline_hyphen_bracket(self):
        """S-[01a] ハイフン + ブラケット併用。"""
        doc = V8Tokenizer(
            "#prompt test\n#syntax: v8\n\n<:S-[01a]: 仮説γ :>"
        ).tokenize()
        node = doc.root_nodes[0]
        self.assertEqual(node.kind, "S-[01a]")
        self.assertEqual(node.prefix, "S")
        self.assertEqual(node.address, "01a")

    def test_identifier_hierarchical(self):
        """S-01a.02 階層アドレス。"""
        doc = V8Tokenizer(
            "#prompt test\n#syntax: v8\n\n<:S-01a.02: 詳細 :>"
        ).tokenize()
        node = doc.root_nodes[0]
        self.assertEqual(node.prefix, "S")
        self.assertEqual(node.address, "01a.02")

    def test_identifier_block(self):
        """S-01a ブロック形式。"""
        doc = V8Tokenizer(
            "#prompt test\n#syntax: v8\n\n"
            "<:S-01a:\n  仮説の内容\n:>"
        ).tokenize()
        node = doc.root_nodes[0]
        self.assertEqual(node.kind, "S-01a")
        self.assertEqual(node.prefix, "S")
        self.assertEqual(node.address, "01a")
        self.assertIn("仮説の内容", node.text_lines[0])

    def test_identifier_named_close(self):
        """識別子の名前付き閉じタグ。"""
        doc = V8Tokenizer(
            "#prompt test\n#syntax: v8\n\n"
            "<:S-01a:\n  内容\n/S-01a:>"
        ).tokenize()
        node = doc.root_nodes[0]
        self.assertEqual(node.kind, "S-01a")
        self.assertEqual(node.close_tag, "/S-01a:>")

    def test_identifier_backward_compat(self):
        """従来のディレクティブは識別子にならない。"""
        doc = V8Tokenizer(
            "#prompt test\n#syntax: v8\n\n<:role: Expert :>"
        ).tokenize()
        node = doc.root_nodes[0]
        self.assertEqual(node.kind, "role")
        self.assertIsNone(node.prefix)
        self.assertIsNone(node.address)
        self.assertFalse(node.is_identifier)

    def test_flow_directive_parse(self):
        """<:flow:> ディレクティブの CCL 構造演算子パース。"""
        doc = V8Tokenizer(
            "#prompt test\n#syntax: v8\n\n"
            "<:flow: [S-01a,S-01b]>>S-02>>S-03 :>"
        ).tokenize()
        prompt = V8Compiler(doc).compile()
        flow = prompt.blocks.get("@flow")
        self.assertIsNotNone(flow)
        self.assertEqual(len(flow["stages"]), 3)
        # 第1段階: [S-01a, S-01b] = 並列グループ
        self.assertTrue(flow["stages"][0]["parallel"])
        self.assertEqual(flow["stages"][0]["nodes"], ["S-01a", "S-01b"])
        # 第2段階: S-02 = 単独
        self.assertFalse(flow["stages"][1]["parallel"])
        self.assertEqual(flow["stages"][1]["nodes"], ["S-02"])
        # 第3段階: S-03 = 単独
        self.assertFalse(flow["stages"][2]["parallel"])

    def test_identifier_compile_grouped(self):
        """識別子ノードが @id:S にグループ化される。"""
        doc = V8Tokenizer(
            "#prompt test\n#syntax: v8\n\n"
            "<:S-01a: 仮説α :>\n"
            "<:S-01b: 仮説β :>\n"
            "<:S-02: 統合 :>"
        ).tokenize()
        prompt = V8Compiler(doc).compile()
        group = prompt.blocks.get("@id:S")
        self.assertIsNotNone(group)
        self.assertEqual(len(group), 3)
        self.assertEqual(group[0]["address"], "01a")
        self.assertEqual(group[0]["content"], "仮説α")
        self.assertEqual(group[2]["address"], "02")

    def test_flow_with_parallel_operator(self):
        """* 並列演算子のパース。"""
        doc = V8Tokenizer(
            "#prompt test\n#syntax: v8\n\n"
            "<:flow: S-01a*S-01b>>S-02 :>"
        ).tokenize()
        prompt = V8Compiler(doc).compile()
        flow = prompt.blocks.get("@flow")
        self.assertEqual(len(flow["stages"]), 2)
        self.assertTrue(flow["stages"][0]["parallel"])
        self.assertEqual(flow["stages"][0]["nodes"], ["S-01a", "S-01b"])


if __name__ == "__main__":
    unittest.main()
