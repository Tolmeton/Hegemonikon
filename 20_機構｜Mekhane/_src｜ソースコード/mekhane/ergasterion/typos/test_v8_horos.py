# PROOF: [L2/テスト] <- mekhane/ergasterion/typos/test_v8_horos.py
"""Typos v8.2 Hóros 拡張ディレクティブのテスト。

テスト対象:
  P1: step/focus/highlight (リスト型), scope (構造化辞書), intent (テキスト)
  P2: context の YAML 風構文サポート
  P3: elif コンパイル
"""

import unittest

from mekhane.ergasterion.typos.v8_tokenizer import V8Tokenizer
from mekhane.ergasterion.typos.v8_compiler import V8Compiler


class TestHorosDirectives(unittest.TestCase):
    """P1: Hóros 拡張ディレクティブの型安全コンパイル。"""

    def _compile(self, text: str):
        doc = V8Tokenizer(text).tokenize()
        return V8Compiler(doc).compile()

    def test_step_list(self):
        """step がリストとしてコンパイルされる。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:role: Agent :>\n"
            "<:step:\n"
            "  - view_file で確認\n"
            "  - 出力形式を検証\n"
            "  - 📖 参照ラベル付与\n"
            ":>"
        )
        steps = p.blocks.get("@step", [])
        self.assertEqual(len(steps), 3)
        self.assertIn("view_file", steps[0])
        self.assertIn("📖", steps[2])

    def test_focus_list(self):
        """focus がリストとしてコンパイルされる。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:role: Agent :>\n"
            "<:focus:\n"
            "  - 「知っている」感覚 → view_file したか？\n"
            "  - 「たぶん」 → SOURCE がないのでは？\n"
            ":>"
        )
        focus = p.blocks.get("@focus", [])
        self.assertEqual(len(focus), 2)
        self.assertIn("知っている", focus[0])

    def test_highlight_list(self):
        """highlight がリストとしてコンパイルされる。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:role: Agent :>\n"
            "<:highlight:\n"
            "  - 確信の強さと正確さは無相関\n"
            "  - view_file のコスト < 推測のリスク\n"
            ":>"
        )
        hl = p.blocks.get("@highlight", [])
        self.assertEqual(len(hl), 2)

    def test_highlight_freetext_fallback(self):
        """highlight にリスト項目がない場合、テキスト全体が1要素になる。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:role: Agent :>\n"
            "<:highlight:\n"
            "  確信の強さと正確さは無相関\n"
            ":>"
        )
        hl = p.blocks.get("@highlight", [])
        self.assertEqual(len(hl), 1)
        self.assertIn("無相関", hl[0])

    def test_scope_structured(self):
        """scope が3区間辞書 (triggered/not_triggered/gray_zone) にコンパイルされる。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:role: Agent :>\n"
            "<:scope:\n"
            "  発動条件:\n"
            "  - WF 実行前に view_file\n"
            "  - HGK 独自概念への言及\n"
            "  非発動条件:\n"
            "  - 直前5ターン内の自作ファイル\n"
            "  グレーゾーン:\n"
            "  - 10ターン以上前の自作ファイル\n"
            ":>"
        )
        scope = p.blocks.get("@scope", {})
        self.assertIsInstance(scope, dict)
        self.assertEqual(len(scope["triggered"]), 2)
        self.assertEqual(len(scope["not_triggered"]), 1)
        self.assertEqual(len(scope["gray_zone"]), 1)
        self.assertIn("view_file", scope["triggered"][0])

    def test_scope_english_labels(self):
        """scope が英語ラベルでも動作する。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:role: Agent :>\n"
            "<:scope:\n"
            "  triggered:\n"
            "  - API calls\n"
            "  not_triggered:\n"
            "  - Simple math\n"
            ":>"
        )
        scope = p.blocks.get("@scope", {})
        self.assertEqual(len(scope["triggered"]), 1)
        self.assertEqual(len(scope["not_triggered"]), 1)

    def test_intent_text(self):
        """intent がテキストとしてコンパイルされる。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:role: Agent :>\n"
            "<:intent:\n"
            "  N-1 が無い世界: LLM は RLHF により確信を持って答えることに最適化されている。\n"
            "  確認すれば数秒で済むことを推測で進む。\n"
            ":>"
        )
        intent = p.blocks.get("@intent", "")
        self.assertIn("N-1", intent)
        self.assertIn("RLHF", intent)

    def test_intent_inline(self):
        """intent のインライン形式。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:role: Agent :>\n"
            "<:intent: 精度最適化 — prior の精度を下げ感覚入力を上げる :>"
        )
        intent = p.blocks.get("@intent", "")
        self.assertIn("精度最適化", intent)


class TestContextYAML(unittest.TestCase):
    """P2: Context ブロックの YAML 風構文サポート。"""

    def _compile(self, text: str):
        doc = V8Tokenizer(text).tokenize()
        return V8Compiler(doc).compile()

    def test_bracket_format(self):
        """既存のブラケット形式が動作する (回帰確認)。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:role: Agent :>\n"
            "<:context:\n"
            "  - [file] horos-hub.md (priority: CRITICAL)\n"
            "  - [knowledge] 体系構造\n"
            ":>"
        )
        ctx = p.blocks.get("@context", [])
        self.assertEqual(len(ctx), 2)
        self.assertEqual(ctx[0].ref_type, "file")
        self.assertEqual(ctx[0].priority, "CRITICAL")
        self.assertEqual(ctx[1].ref_type, "knowledge")
        self.assertEqual(ctx[1].priority, "MEDIUM")

    def test_yaml_format_with_priority(self):
        """YAML 風形式 (- file: path + priority: X) が動作する。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:role: Agent :>\n"
            "<:context:\n"
            "  - file: nous/workflows/ccl/ccl-plan.md\n"
            "    priority: HIGH\n"
            ":>"
        )
        ctx = p.blocks.get("@context", [])
        self.assertEqual(len(ctx), 1)
        self.assertEqual(ctx[0].ref_type, "file")
        self.assertIn("ccl-plan.md", ctx[0].path)
        self.assertEqual(ctx[0].priority, "HIGH")

    def test_yaml_format_without_priority(self):
        """YAML 風形式で priority 省略時に MEDIUM がデフォルト。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:role: Agent :>\n"
            "<:context:\n"
            "  - file: some/path.md\n"
            ":>"
        )
        ctx = p.blocks.get("@context", [])
        self.assertEqual(len(ctx), 1)
        self.assertEqual(ctx[0].ref_type, "file")
        self.assertEqual(ctx[0].priority, "MEDIUM")

    def test_mixed_formats(self):
        """ブラケット形式と YAML 形式の混在。"""
        p = self._compile(
            "#prompt test\n#syntax: v8\n\n"
            "<:role: Agent :>\n"
            "<:context:\n"
            "  - [file] horos-hub.md (priority: CRITICAL)\n"
            "  - knowledge: 体系構造\n"
            "    priority: LOW\n"
            ":>"
        )
        ctx = p.blocks.get("@context", [])
        self.assertEqual(len(ctx), 2)
        self.assertEqual(ctx[0].ref_type, "file")
        self.assertEqual(ctx[0].priority, "CRITICAL")
        self.assertEqual(ctx[1].ref_type, "knowledge")
        self.assertEqual(ctx[1].priority, "LOW")


class TestElifCompile(unittest.TestCase):
    """P3: elif コンパイル。"""

    def _compile(self, text: str):
        doc = V8Tokenizer(text).tokenize()
        return V8Compiler(doc).compile()

    def test_elif_basic(self):
        """if/elif/else がそれぞれ Condition として生成される。"""
        p = self._compile(
            '#prompt test\n#syntax: v8\n\n'
            '<:role: Agent :>\n'
            '<:if env == "prod":\n'
            '  <:constraints:\n    - strict\n  :>\n'
            '<:elif env == "staging":\n'
            '  <:constraints:\n    - moderate\n  :>\n'
            '<:else:\n'
            '  <:constraints:\n    - lenient\n  :>\n'
            '/if:>'
        )
        # if + elif = 2 conditions
        self.assertEqual(len(p.conditions), 2)
        # 最初の condition: env == prod
        c0 = p.conditions[0]
        self.assertEqual(c0.variable, "env")
        self.assertEqual(c0.value, "prod")
        self.assertIn("strict", str(c0.if_content))
        # 2番目の condition: env == staging (elif)
        c1 = p.conditions[1]
        self.assertEqual(c1.variable, "env")
        self.assertEqual(c1.value, "staging")
        self.assertIn("moderate", str(c1.if_content))


if __name__ == "__main__":
    unittest.main()
