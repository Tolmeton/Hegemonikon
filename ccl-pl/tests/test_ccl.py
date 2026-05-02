# CCL-PL テストスイート
"""
pytest テスト: パーサー、トランスパイラ、executor、hgk-stdlib
"""

import pytest
from ccl.parser.core import CCLParser
from ccl.parser.ast import (
    Workflow, Sequence, Fusion, Oscillation, Lambda,
    FnDef, FnCall, RawExpr, LetBinding,
)
from ccl.transpiler import CCLTranspiler
from ccl.executor import CCLExecutor
from ccl.optimizer import ASTOptimizer


# =============================================================================
# パーサーテスト
# =============================================================================

class TestParser:
    """CCL パーサーのテスト"""

    def setup_method(self):
        self.parser = CCLParser()

    def test_simple_workflow(self):
        """単一ワークフロー /noe"""
        ast = self.parser.parse("/noe")
        assert isinstance(ast, Workflow)
        assert ast.id == "noe"

    def test_workflow_with_modifier(self):
        """/noe+ → DEEPEN 修飾子"""
        ast = self.parser.parse("/noe+")
        assert isinstance(ast, Workflow)
        assert ast.id == "noe"
        assert len(ast.operators) == 1

    def test_sequence(self):
        """/noe_/dia → Sequence"""
        ast = self.parser.parse("/noe_/dia")
        assert isinstance(ast, Sequence)
        assert len(ast.steps) == 2

    def test_fusion(self):
        """/noe*/dia → Fusion"""
        ast = self.parser.parse("/noe*/dia")
        assert isinstance(ast, Fusion)

    def test_oscillation(self):
        """/ske~/sag → Oscillation"""
        ast = self.parser.parse("/ske~/sag")
        assert isinstance(ast, Oscillation)

    def test_convergent_oscillation(self):
        """/ske~*/sag → 収束振動"""
        ast = self.parser.parse("/ske~*/sag")
        assert isinstance(ast, Oscillation)
        assert ast.convergent is True

    def test_lambda_with_arithmetic(self):
        """L:[x]{x * 2} → Lambda + RawExpr (算術の * が CCL 融合とならない)"""
        ast = self.parser.parse("L:[x]{x * 2}")
        assert isinstance(ast, Lambda)
        assert isinstance(ast.body, RawExpr)
        assert ast.body.code == "x * 2"

    def test_lambda_with_ccl_body(self):
        """L:[wf]{/noe+} → Lambda + Workflow (CCL パターンあり)"""
        ast = self.parser.parse("L:[wf]{/noe+}")
        assert isinstance(ast, Lambda)
        assert isinstance(ast.body, Workflow)

    def test_fn_def(self):
        """fn add(a, b) { a + b } → FnDef + RawExpr"""
        ast = self.parser.parse("fn add(a, b) { a + b }")
        assert isinstance(ast, FnDef)
        assert ast.name == "add"
        assert ast.params == ["a", "b"]
        assert isinstance(ast.body, RawExpr)

    def test_fn_call(self):
        """add(3, 4) → FnCall"""
        ast = self.parser.parse("add(3, 4)")
        assert isinstance(ast, FnCall)
        assert ast.name == "add"
        assert len(ast.args) == 2

    def test_let_binding(self):
        """let x = /noe+ → LetBinding"""
        ast = self.parser.parse("let x = /noe+")
        assert isinstance(ast, LetBinding)
        assert ast.name == "x"

    def test_bracket_modifiers(self):
        """/noe[Va:E,Pr:C]+ → ブラケット修飾子"""
        ast = self.parser.parse("/noe[Va:E,Pr:C]+")
        assert isinstance(ast, Workflow)
        assert ast.modifiers.get("Va") == "E"
        assert ast.modifiers.get("Pr") == "C"


# =============================================================================
# トランスパイラテスト
# =============================================================================

class TestTranspiler:
    """CCL トランスパイラのテスト"""

    def setup_method(self):
        self.parser = CCLParser()
        self.transpiler = CCLTranspiler()

    def _transpile(self, ccl: str) -> str:
        ast = self.parser.parse(ccl)
        return self.transpiler.transpile(ast, include_header=False)

    def test_simple_workflow(self):
        result = self._transpile("/noe")
        assert "noe()" in result

    def test_sequence(self):
        result = self._transpile("/noe+_/dia")
        assert "noe(" in result
        assert "dia(" in result

    def test_fusion_uses_merge(self):
        result = self._transpile("/noe*/dia")
        assert "merge(" in result

    def test_fn_def_generates_def(self):
        result = self._transpile("fn add(a, b) { a + b }")
        assert "def add(a, b):" in result
        assert "return a + b" in result

    def test_fn_call_generates_call(self):
        result = self._transpile("add(3, 4)")
        assert "add(3, 4)" in result

    def test_lambda_preserves_arithmetic(self):
        result = self._transpile("L:[x]{x * 2}")
        assert "x * 2" in result


# =============================================================================
# Executor テスト
# =============================================================================

class TestExecutor:
    """CCL 実行エンジンのテスト"""

    def setup_method(self):
        self.exe = CCLExecutor()

    def test_fn_def_and_call(self):
        """fn 定義 → 呼出"""
        self.exe.execute("fn add(a, b) { a + b }")
        result = self.exe.execute("add(3, 4)")
        assert result == 7

    def test_lambda_arithmetic(self):
        """Lambda 内の算術が正しく動く"""
        self.exe.execute("let double = L:[x]{x * 2}")
        fn = self.exe._globals.get("double")
        assert callable(fn)
        assert fn(21) == 42

    def test_multiline_file(self):
        """複数文の逐次実行"""
        source = """
        fn greet(name) { "Hello, " + name }
        greet("World")
        """
        result = self.exe.execute(source)
        assert result == "Hello, World"

    def test_comment_skip(self):
        """コメント行がスキップされる"""
        result = self.exe.execute("# コメント\n# もう一つ\n")
        assert result is None

    def test_prelude_functions(self):
        """prelude の関数が使える"""
        assert "add" in self.exe._globals
        assert "print" in self.exe._globals


# =============================================================================
# hgk-stdlib テスト
# =============================================================================

class TestHgkStdlib:
    """hgk-stdlib のテスト"""

    def test_import_all(self):
        """全関数がインポートできる"""
        from ccl.stdlib.hgk import __all__
        assert len(__all__) >= 26  # 24関数 + 2メタ

    def test_telos(self):
        from ccl.stdlib.hgk import recognize, explore
        r = recognize("test")
        assert r["type"] == "insight"
        e = explore("hypothesis")
        assert e["type"] == "discovery"

    def test_methodos(self):
        from ccl.stdlib.hgk import diverge_strategy, converge_strategy
        d = diverge_strategy("problem")
        assert d["type"] == "hypotheses"
        c = converge_strategy(d)
        assert c["type"] == "best"

    def test_krisis(self):
        from ccl.stdlib.hgk import commit, suspend
        c = commit("evidence")
        assert c["type"] == "decision"
        s = suspend("ambiguous")
        assert s["type"] == "options"

    def test_diastasis(self):
        from ccl.stdlib.hgk import analyze_detail, overview
        a = analyze_detail("complex object")
        assert a["type"] == "components"
        o = overview("system")
        assert o["type"] == "map"

    def test_orexis(self):
        from ccl.stdlib.hgk import affirm, critique
        a = affirm("good")
        assert a["type"] == "confidence"
        c = critique("claim")
        assert c["type"] == "issues"

    def test_chronos(self):
        from ccl.stdlib.hgk import recall, forecast
        r = recall("past event")
        assert r["type"] == "memory"
        f = forecast("current state")
        assert f["type"] == "prediction"

    def test_adjoint_pairs(self):
        """随伴対が12個ある"""
        from ccl.stdlib.hgk import ALL_ADJOINT_PAIRS
        assert len(ALL_ADJOINT_PAIRS) == 12

    def test_verb_map(self):
        """/verb → 関数のマッピングが完全"""
        from ccl.stdlib.hgk import VERB_MAP
        assert len(VERB_MAP) >= 24  # I/A 24 + S極
        assert "noe" in VERB_MAP
        assert "par" in VERB_MAP


# =============================================================================
# Extension テスト
# =============================================================================

class TestExtension:
    """Extension ローダーと use 統合のテスト"""

    def test_extension_loader_ccl_file(self):
        """ccl-ext-math/basic.ccl から関数をロードできる"""
        from pathlib import Path
        from ccl.extension import ExtensionLoader

        loader = ExtensionLoader()
        # ccl-pl/ ディレクトリを検索パスに追加
        ccl_pl_dir = Path(__file__).parent.parent
        loader.add_search_path(ccl_pl_dir)

        ext = loader.load("math.basic")
        assert "double" in ext.functions
        assert "halve" in ext.functions
        assert "square" in ext.functions
        assert ext.functions["double"](21) == 42
        assert ext.functions["halve"](84) == 42.0
        assert ext.functions["square"](6) == 36

    def test_extension_adjoint_pairs(self):
        """Extension から随伴対がロードされる"""
        from pathlib import Path
        from ccl.extension import ExtensionLoader

        loader = ExtensionLoader()
        ccl_pl_dir = Path(__file__).parent.parent
        loader.add_search_path(ccl_pl_dir)

        ext = loader.load("math.basic")
        assert ("double", "halve") in ext.adjoint_pairs
        assert ("negate", "negate") in ext.adjoint_pairs

    def test_extension_python_fallback(self):
        """Python stdlib フォールバックで hgk.telos がロードされる"""
        from ccl.extension import ExtensionLoader

        loader = ExtensionLoader()
        ext = loader.load("hgk.telos")
        assert "recognize" in ext.functions
        assert "intend" in ext.functions
        result = ext.functions["recognize"]("test")
        assert result["type"] == "insight"

    def test_use_in_executor(self):
        """Executor で use math.basic → 関数が使える"""
        import os
        from pathlib import Path

        exe = CCLExecutor()
        ccl_pl_dir = Path(__file__).parent.parent
        exe._ext_loader.add_search_path(ccl_pl_dir)

        exe.execute("use math.basic")
        result = exe.execute("double(21)")
        assert result == 42

    def test_use_adjoint_registered(self):
        """use した Extension の随伴対が Optimizer に登録される"""
        from pathlib import Path

        exe = CCLExecutor()
        ccl_pl_dir = Path(__file__).parent.parent
        exe._ext_loader.add_search_path(ccl_pl_dir)

        exe.execute("use math.basic")
        pairs = exe._globals.get("__ccl_adjoint_pairs__", [])
        assert ("double", "halve") in pairs

    def test_extension_python_bridge_local_file_module(self, tmp_path):
        """hyphenated local extension dir の Python bridge が解決される"""
        from ccl.extension import ExtensionLoader

        ext_dir = tmp_path / "ccl-ext-sample"
        ext_dir.mkdir()
        (ext_dir / "core.ccl").write_text(
            'extension sample {\n    fn triple(x) -> python("ccl-ext-sample.core.triple")\n}\n',
            encoding="utf-8",
        )
        (ext_dir / "core.py").write_text(
            "def triple(x):\n    return x * 3\n",
            encoding="utf-8",
        )

        loader = ExtensionLoader([tmp_path])
        ext = loader.load("sample.core")

        assert ext.functions["triple"](14) == 42

    def test_extension_loader_entry_point_root(self, monkeypatch, tmp_path):
        """entry point が公開した root から extension をロードできる"""
        from ccl.extension import ENTRY_POINT_GROUP, ExtensionLoader

        root = tmp_path / "pkg_root"
        ext_dir = root / "ccl-ext-demo" / "nested"
        ext_dir.mkdir(parents=True)
        (ext_dir / "core.ccl").write_text(
            'extension demo.nested {\n    fn meaning() { 42 }\n}\n',
            encoding="utf-8",
        )

        class FakeEntryPoint:
            def load(self):
                return lambda: root

        class FakeEntryPoints(list):
            def select(self, *, group=None, **kwargs):
                if group == ENTRY_POINT_GROUP:
                    return self
                return []

        monkeypatch.setattr(
            "ccl.extension.importlib.metadata.entry_points",
            lambda: FakeEntryPoints([FakeEntryPoint()]),
        )

        loader = ExtensionLoader()
        ext = loader.load("demo.nested.core")

        assert ext.functions["meaning"]() == 42


class TestOptimizer:
    """AST optimizer の随伴縮約テスト"""

    def test_optimizer_folds_composed_cross_extension_adjoints(self):
        """(F2∘F1) ⊣ (G1∘G2) の round-trip を内側から相殺できる"""
        optimizer = ASTOptimizer()
        optimizer.register_adjoint_pairs([
            ("normalize", "denormalize"),
            ("project", "inflate"),
        ])

        ast = FnCall(
            name="denormalize",
            args=[
                FnCall(
                    name="inflate",
                    args=[
                        FnCall(
                            name="project",
                            args=[
                                FnCall(name="normalize", args=[RawExpr(code="x")]),
                            ],
                        ),
                    ],
                ),
            ],
        )

        result = optimizer.optimize(ast)

        assert isinstance(result, RawExpr)
        assert result.code == "x"
        assert optimizer.stats["optimizations_applied"] == 2
