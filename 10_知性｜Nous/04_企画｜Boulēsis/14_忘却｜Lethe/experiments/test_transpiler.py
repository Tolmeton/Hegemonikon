# CCL-PL テスト — CCL → Python トランスパイラの単体テスト
"""
CCL → Python トランスパイラ テスト

CCL 式を入力し、生成された Python ソースが:
1. 構文的に正しい (compile() 可能)
2. 期待する構造を含む
ことを検証する。
"""

import sys
import ast as python_ast
import unittest
from pathlib import Path

import pytest

# パスの追加
_THIS_DIR = Path(__file__).parent
_MEKHANE_SRC = _THIS_DIR.parent.parent / "20_機構｜Mekhane" / "_src｜ソースコード"
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_MEKHANE_SRC))

from ccl_transpiler import transpile_ccl, CCLTranspiler
from hermeneus.src.parser import CCLParser


# =============================================================================
# ヘルパー
# =============================================================================

def assert_valid_python(source: str) -> None:
    """Python ソースが構文的に正しいことを検証"""
    try:
        python_ast.parse(source)
    except SyntaxError as e:
        pytest.fail(f"生成コードが不正な Python:\n{source}\n\nエラー: {e}")


def transpile(ccl: str) -> str:
    """ヘッダーなしでトランスパイル (テスト用)"""
    return transpile_ccl(ccl, include_header=False)


# =============================================================================
# 基本ワークフロー
# =============================================================================

class TestBasicWorkflow:
    """単一ワークフローのトランスパイル"""
    
    def test_simple_workflow(self):
        """/noe → noe() を含む有効な Python"""
        source = transpile("/noe")
        assert_valid_python(source)
        assert "noe()" in source
    
    def test_deepen_modifier(self):
        """/noe+ → noe(detail_level=3)"""
        source = transpile("/noe+")
        assert_valid_python(source)
        assert "detail_level=3" in source
    
    def test_condense_modifier(self):
        """/bou- → bou(detail_level=1)"""
        source = transpile("/bou-")
        assert_valid_python(source)
        assert "detail_level=1" in source
    
    def test_ascend_modifier(self):
        """/noe^ → noe(detail_level=4)"""
        source = transpile("/noe^")
        assert_valid_python(source)
        assert "detail_level=4" in source


# =============================================================================
# シーケンス
# =============================================================================

class TestSequence:
    """シーケンス (_) のトランスパイル"""
    
    def test_two_step(self):
        """/noe_/dia → noe() + dia(v1)"""
        source = transpile("/noe_/dia")
        assert_valid_python(source)
        assert "noe(" in source
        assert "dia(" in source
    
    def test_three_step(self):
        """/noe+_/dia_/ene+ → 3つの逐次呼出し"""
        source = transpile("/noe+_/dia_/ene+")
        assert_valid_python(source)
        # 前の結果が次に渡される
        lines = [l.strip() for l in source.strip().split("\n") if l.strip() and not l.strip().startswith("#")]
        assert len(lines) >= 3


# =============================================================================
# 融合
# =============================================================================

class TestFusion:
    """融合 (*) と展開 (%) のトランスパイル"""
    
    def test_merge(self):
        """/noe * /dia → merge(noe(), dia())"""
        source = transpile("/noe*/dia")
        assert_valid_python(source)
        assert "merge(" in source
    
    def test_outer_product(self):
        """/noe % /dia → product(noe(), dia())"""
        source = transpile("/noe%/dia")
        assert_valid_python(source)
        assert "product(" in source


# =============================================================================
# 振動
# =============================================================================

class TestOscillation:
    """振動 (~), 収束振動 (~*), 発散振動 (~!) のトランスパイル"""
    
    def test_plain_oscillation(self):
        """/u ~ /noe → oscillate(...)"""
        source = transpile("/u~/noe")
        assert_valid_python(source)
        assert "oscillate(" in source
    
    def test_convergent_oscillation(self):
        """/u ~* /noe → converge(...)"""
        source = transpile("/u~*/noe")
        assert_valid_python(source)
        assert "converge(" in source
    
    def test_divergent_oscillation(self):
        """/u ~! /noe → diverge(...)"""
        source = transpile("/u~!/noe")
        assert_valid_python(source)
        assert "diverge(" in source


# =============================================================================
# 制御構文
# =============================================================================

class TestControlStructures:
    """制御構文のトランスパイル"""
    
    def test_for_loop_count(self):
        """F:[×3]{/dia} → for _ in range(3)"""
        source = transpile("F:[×3]{/dia}")
        assert_valid_python(source)
        assert "range(3)" in source
        assert "for " in source
    
    def test_for_loop_list(self):
        """F:[A,B,C]{/dia} → for _item in [...]"""
        source = transpile("F:[A,B,C]{/dia}")
        assert_valid_python(source)
        assert "for " in source
    
    def test_if_condition(self):
        """I:[V[] > 0.5]{/noe+} → if ... > 0.5"""
        source = transpile("I:[V[]>0.5]{/noe+}")
        assert_valid_python(source)
        assert "if " in source
        assert "0.5" in source
    
    def test_if_else(self):
        """I:[V[] > 0.5]{/noe+} E:{/noe-} → if/else"""
        source = transpile("I:[V[]>0.5]{/noe+}E:{/noe-}")
        assert_valid_python(source)
        assert "if " in source
        assert "else:" in source
    
    def test_while_loop(self):
        """W:[E[] > 0.3]{/dia} → while error > 0.3"""
        source = transpile("W:[E[]>0.3]{/dia}")
        assert_valid_python(source)
        assert "while " in source
    
    def test_lambda(self):
        """L:[x]{/noe} → lambda"""
        source = transpile("L:[x]{/noe}")
        assert_valid_python(source)
        assert "lambda" in source or "def " in source


# =============================================================================
# パイプラインと並列
# =============================================================================

class TestPipelineAndParallel:
    """分散パイプライン (&>) と分散並列 (&&) のトランスパイル (v7.6)"""
    
    def test_pipeline(self):
        """/noe+&>/dia+ → ネスト呼出し"""
        source = transpile("/noe+&>/dia+")
        assert_valid_python(source)
        assert "noe(" in source
        assert "dia(" in source
    
    def test_parallel(self):
        """/noe+&&/dia+ → asyncio.gather"""
        source = transpile("/noe+&&/dia+")
        assert_valid_python(source)
        assert "parallel(" in source


# =============================================================================
# 随伴演算子 (v7.6)
# =============================================================================

class TestAdjunction:
    """随伴演算子 (||, |>, <|) のトランスパイル (v7.6)"""
    
    def test_adjunction_declaration(self):
        """F || G → register_dual("F", "G") 随伴宣言"""
        source = transpile("/noe||/zet")
        assert_valid_python(source)
        assert 'register_dual(' in source
        assert '"noe"' in source
        assert '"zet"' in source
    
    def test_right_adjoint(self):
        """F|> → right_adjoint("F") 右随伴取得"""
        source = transpile("/noe|>")
        assert_valid_python(source)
        assert 'right_adjoint(' in source
        assert '"noe"' in source
    
    def test_left_adjoint(self):
        """G<| → left_adjoint("G") 左随伴取得"""
        source = transpile("/zet<|")
        assert_valid_python(source)
        assert 'left_adjoint(' in source
        assert '"zet"' in source


# =============================================================================
# 複合式
# =============================================================================

class TestComplex:
    """複合的な CCL 式のトランスパイル"""
    
    def test_sequence_with_fusion(self):
        """/noe+_/dia*/ene+ → シーケンス + 融合"""
        source = transpile("/noe+_/dia*/ene+")
        assert_valid_python(source)
    
    def test_for_with_oscillation(self):
        """F:[×3]{/dia~*/noe} → for ループ内の収束振動"""
        source = transpile("F:[×3]{/dia~*/noe}")
        assert_valid_python(source)
    
    def test_tagged_validate(self):
        """V:{/noe+} → validate(noe(...))"""
        source = transpile("V:{/noe+}")
        assert_valid_python(source)
        assert "validate(" in source
    
    def test_let_binding(self):
        """let x = /noe+ → x = noe(detail_level=3)"""
        source = transpile("let x = /noe+")
        assert_valid_python(source)
        assert "x = " in source
    
    def test_includes_header(self):
        """ヘッダー付きで生成すると import が含まれる"""
        source = transpile_ccl("/noe*/dia", include_header=True)
        assert_valid_python(source)
        assert "from ccl_runtime import" in source


# =============================================================================
# ランタイム実行テスト
# =============================================================================

class TestRuntime:
    """生成コードが実際に実行可能か (ダミー関数を注入して)"""
    
    def test_sequence_executes(self):
        """シーケンスの生成コードが exec() で実行可能"""
        source = transpile("/noe+_/dia_/ene+")
        
        # ダミー関数を注入
        env = {
            "noe": lambda *a, **kw: {"type": "noe", "args": a, **kw},
            "dia": lambda *a, **kw: {"type": "dia", "args": a, **kw},
            "ene": lambda *a, **kw: {"type": "ene", "args": a, **kw},
        }
        
        exec(source, env)
        assert "result" in env
        assert env["result"]["type"] == "ene"
    
    def test_fusion_executes(self):
        """融合の生成コードが exec() で実行可能"""
        source = transpile_ccl("/noe*/dia", include_header=False)
        
        from ccl_runtime import merge
        env = {
            "noe": lambda *a, **kw: {"from": "noe"},
            "dia": lambda *a, **kw: {"from": "dia"},
            "merge": merge,
        }
        
        exec(source, env)
        assert "result" in env
        assert env["result"]["from"] == "dia"  # 後の dict が上書き


# =============================================================================
# 双対生成 (\ 演算子) — トランスパイラテスト
# =============================================================================

class TestDualTranspile:
    """双対生成 (\\) のトランスパイル"""
    
    def test_dual_single_workflow(self):
        """\\A → dual("A")() を含む有効な Python"""
        source = transpile("\\noe")
        assert_valid_python(source)
        assert 'dual("noe")' in source
    
    def test_dual_with_modifier(self):
        """\\A+ → dual("A")(detail_level=3)"""
        source = transpile("\\noe+")
        assert_valid_python(source)
        assert 'dual(' in source
        assert 'detail_level=3' in source
    
    def test_dual_sequence(self):
        """\\(A_B_C) → 逆順で dual() が呼ばれる"""
        source = transpile("\\(noe_dia_ene)")
        assert_valid_python(source)
        assert 'dual(' in source
        # 逆順であること: ene が最初に出現し、noe が最後
        ene_pos = source.find('"ene"')
        noe_pos = source.find('"noe"')
        if ene_pos >= 0 and noe_pos >= 0:
            assert ene_pos < noe_pos, "シーケンスが逆順で生成されるべき"
    
    def test_dual_fusion_becomes_product(self):
        """\\(A*B) → product() (融合の双対 = 展開)"""
        source = transpile("\\(noe*dia)")
        assert_valid_python(source)
        assert "product(" in source
    
    def test_dual_product_becomes_merge(self):
        """\\(A%B) → merge() (展開の双対 = 融合)"""
        source = transpile("\\(noe%dia)")
        assert_valid_python(source)
        assert "merge(" in source
    
    def test_dual_convergence_becomes_divergence(self):
        """\\(A~*B) → diverge() (収束の双対 = 発散)"""
        source = transpile("\\(noe~*dia)")
        assert_valid_python(source)
        assert "diverge(" in source
    
    def test_dual_header_includes_dual(self):
        """ヘッダーに dual のインポートが含まれる"""
        source = transpile_ccl("\\noe", include_header=True)
        assert_valid_python(source)
        assert "dual" in source


# =============================================================================
# 双対生成 (\ 演算子) — ランタイムテスト
# =============================================================================

class TestDualRuntime:
    """双対レジストリとランタイム機能"""
    
    def test_register_and_lookup(self):
        """register_dual → dual() で取得可能"""
        from ccl_runtime import register_dual, dual, _dual_registry
        
        def encode(x): return f"enc({x})"
        def decode(x): return f"dec({x})"
        
        register_dual(encode, decode)
        
        assert dual("encode") is decode
        assert dual("decode") is encode
        
        # クリーンアップ
        _dual_registry.pop("encode", None)
        _dual_registry.pop("decode", None)
    
    def test_dual_of_decorator(self):
        """@dual_of デコレータで双対登録"""
        from ccl_runtime import dual_of, dual, _dual_registry
        
        def compress(data): return data[:5]
        
        @dual_of(compress)
        def decompress(data): return data + "..."
        
        assert dual("compress") is decompress
        assert dual("decompress") is compress
        
        # クリーンアップ
        _dual_registry.pop("compress", None)
        _dual_registry.pop("decompress", None)
    
    def test_operator_duals(self):
        """組み込み演算子の双対が正しい"""
        from ccl_runtime import dual
        
        # merge ↔ product
        merge_dual = dual("merge")
        assert merge_dual.__name__ == "product"
        
        product_dual = dual("product")
        assert product_dual.__name__ == "merge"
        
        # converge ↔ diverge
        assert dual("converge").__name__ == "diverge"
        assert dual("diverge").__name__ == "converge"
    
    def test_dual_not_found(self):
        """未登録の関数で DualNotFoundError"""
        from ccl_runtime import dual, DualNotFoundError
        
        with pytest.raises(DualNotFoundError):
            dual("nonexistent_function_xyz")
    
    def test_invert_pipeline(self):
        """invert_pipeline が逆順の双対パイプラインを生成"""
        from ccl_runtime import register_dual, invert_pipeline, _dual_registry
        
        # ダミー関数ペア
        def step_a(x): return f"a({x})"
        def step_a_inv(x): return f"a_inv({x})"
        def step_b(x): return f"b({x})"
        def step_b_inv(x): return f"b_inv({x})"
        
        register_dual(step_a, step_a_inv)
        register_dual(step_b, step_b_inv)
        
        # invert_pipeline(A, B) → pipe(B_inv, A_inv)
        inv = invert_pipeline(step_a, step_b)
        result = inv("x")
        assert result == "a_inv(b_inv(x))"  # B の逆を先に、A の逆を後に
        
        # クリーンアップ
        for name in ["step_a", "step_a_inv", "step_b", "step_b_inv"]:
            _dual_registry.pop(name, None)


# =============================================================================
# << (逆射/pullback) — トランスパイラテスト
# =============================================================================

class TestBackwardTranspile:
    """<< (逆射) のトランスパイル"""
    
    def test_simple_backward(self):
        """/noe << /dia → dual("dia")(noe()) を含む有効な Python"""
        source = transpile("/noe << /dia")
        assert_valid_python(source)
        assert 'dual("dia")' in source
        assert "noe(" in source
    
    def test_chained_backward(self):
        """/noe << /dia << /ene → 3段逆射チェイン"""
        source = transpile("/noe << /dia << /ene")
        assert_valid_python(source)
        assert 'dual("dia")' in source
        assert 'dual("ene")' in source
    
    def test_backward_header(self):
        """ヘッダーに dual のインポートが含まれる"""
        source = transpile_ccl("/noe << /dia", include_header=True)
        assert_valid_python(source)
        assert "dual" in source
    
    def test_backward_no_header(self):
        """ヘッダーなしで変換"""
        source = transpile("/noe << /dia")
        assert_valid_python(source)
        assert "from ccl_runtime" not in source


# =============================================================================
# << (逆射/pullback) — ランタイムテスト
# =============================================================================

class TestBackwardRuntime:
    """backward() と backward_search() のランタイム動作"""
    
    def test_backward_simple(self):
        """backward(goal, fn) で双対を自動適用"""
        from ccl_runtime import register_dual, backward, _dual_registry
        
        def encode(x): return f"enc({x})"
        def decode(x): return f"dec({x})"
        register_dual(encode, decode)
        
        # backward(encrypted, encode) → decode(encrypted)
        result = backward("enc(hello)", encode)
        assert result == "dec(enc(hello))"
        
        _dual_registry.pop("encode", None)
        _dual_registry.pop("decode", None)
    
    def test_backward_chain(self):
        """backward(goal, fn1, fn2) でチェイン逆射"""
        from ccl_runtime import register_dual, backward, _dual_registry
        
        def step_a(x): return f"a({x})"
        def step_a_inv(x): return f"a'({x})"
        def step_b(x): return f"b({x})"
        def step_b_inv(x): return f"b'({x})"
        
        register_dual(step_a, step_a_inv)
        register_dual(step_b, step_b_inv)
        
        # backward(goal, A, B) → A'(B'(goal))
        # つまり A の逆 → B の逆の順に適用
        result = backward("goal", step_a, step_b)
        assert result == "b'(a'(goal))"
        
        for name in ["step_a", "step_a_inv", "step_b", "step_b_inv"]:
            _dual_registry.pop(name, None)
    
    def test_backward_search_fallback(self):
        """backward_search で逆像を探索"""
        from ccl_runtime import backward_search
        
        def square(x): return x * x
        
        # 9 の逆像を [1,2,3,4,5] から探す → 3
        result = backward_search(9, square, candidates=[1, 2, 3, 4, 5])
        assert result == 3
        
        # 見つからない場合 → None
        result = backward_search(7, square, candidates=[1, 2, 3, 4, 5])
        assert result is None


# =============================================================================
# Desugar モード — ~ と ^ の構文化
# =============================================================================

class TestDesugar:
    """desugar=True 時の ~ (振動) と ^ (メタ) の構文的展開テスト"""
    
    def test_oscillation_desugar_basic(self):
        """~ desugar: for ループに展開される"""
        parser = CCLParser()
        ast = parser.parse("/noe~/ele")
        
        transpiler = CCLTranspiler(desugar=True)
        source = transpiler.transpile(ast, include_header=False)
        assert_valid_python(source)
        
        # for ループに展開されている
        assert "for " in source
        # ランタイム関数 oscillate が使われていない
        assert "oscillate" not in source
        # 交互適用のコメントが含まれる
        assert "desugar" in source
    
    def test_oscillation_desugar_convergent(self):
        """~* desugar: while + 収束判定"""
        parser = CCLParser()
        ast = parser.parse("/noe~*/ele")
        
        transpiler = CCLTranspiler(desugar=True)
        source = transpiler.transpile(ast, include_header=False)
        assert_valid_python(source)
        
        # 収束判定が含まれる
        assert "break" in source
        # 不動点コメント
        assert "不動点" in source or "収束" in source
        # ランタイム関数 converge が使われていない
        assert "converge" not in source
    
    def test_oscillation_desugar_divergent(self):
        """~! desugar: for ループ + 全軌跡保持"""
        parser = CCLParser()
        ast = parser.parse("/noe~!/ele")
        
        transpiler = CCLTranspiler(desugar=True)
        source = transpiler.transpile(ast, include_header=False)
        assert_valid_python(source)
        
        # 結果リストがある
        assert "append" in source
        # 発散コメント
        assert "発散" in source or "全軌跡" in source
        # ランタイム関数 diverge が使われていない
        assert "diverge" not in source
    
    def test_oscillation_normal_mode_unchanged(self):
        """desugar=False (デフォルト) では既存の動作が変わらない"""
        parser = CCLParser()
        ast = parser.parse("/noe~/ele")
        
        # デフォルト (desugar=False)
        transpiler = CCLTranspiler()
        source = transpiler.transpile(ast, include_header=False)
        assert_valid_python(source)
        assert "oscillate" in source
    
    def test_meta_runtime(self):
        """meta() 関数がリスト・辞書・単体で動作する"""
        from ccl_runtime import meta
        
        def double(x, **_kw): return x * 2
        
        # リスト → 各要素に適用
        assert meta(double)([1, 2, 3]) == [2, 4, 6]
        
        # 辞書 → 各値に適用
        assert meta(double)({"a": 1, "b": 2}) == {"a": 2, "b": 4}
        
        # タプル → タプルで返す
        assert meta(double)((1, 2, 3)) == (2, 4, 6)
        
        # 単体 → 直接適用
        assert meta(double)(5) == 10
    
    def test_desugar_structure_preserved(self):
        """desugar vs 通常モード: 構造的に同等のPythonが生成される"""
        parser = CCLParser()
        ccl_expr = "/noe~/ele"
        ast = parser.parse(ccl_expr)
        
        # 通常モード
        normal = CCLTranspiler()
        normal_source = normal.transpile(ast, include_header=False)
        
        # desugar モード
        ast2 = parser.parse(ccl_expr)
        desugared = CCLTranspiler(desugar=True)
        desugar_source = desugared.transpile(ast2, include_header=False)
        
        # どちらも有効な Python
        assert_valid_python(normal_source)
        assert_valid_python(desugar_source)
        
        # 通常: ランタイム依存, desugar: 純粋 Python
        assert "oscillate" in normal_source
        assert "oscillate" not in desugar_source
        assert "for " in desugar_source
    
    def test_transpile_ccl_desugar_passthrough(self):
        """transpile_ccl(desugar=True) で便利関数経由でも desugar が透過する"""
        source = transpile_ccl("/noe~/ele", include_header=False, desugar=True)
        assert_valid_python(source)
        # desugar: ランタイム関数ではなく for ループに展開
        assert "oscillate" not in source
        assert "for " in source
    
    def test_transpile_ccl_desugar_convergent(self):
        """transpile_ccl(desugar=True) で収束振動も透過する"""
        source = transpile_ccl("/noe~*/ele", include_header=False, desugar=True)
        assert_valid_python(source)
        # desugar: converge() ではなく while/for + break
        assert "converge" not in source
        assert "break" in source
    
    def test_transpile_ccl_desugar_default_false(self):
        """transpile_ccl() のデフォルトは desugar=False (後方互換)"""
        source = transpile_ccl("/noe~/ele", include_header=False)
        assert_valid_python(source)
        # デフォルト: ランタイム関数を使用
        assert "oscillate" in source


# =============================================================================
# 随伴演算子ランタイムテスト (v7.6)
# =============================================================================

class TestAdjunctionRuntime(unittest.TestCase):
    """随伴演算子のランタイム関数をテストする"""

    def setUp(self):
        """各テスト前にレジストリをクリアする"""
        from ccl_runtime import _dual_registry, _adjunction_registry
        _dual_registry.clear()
        _adjunction_registry.clear()

    def test_register_dual_strings(self):
        """文字列引数での随伴宣言が動作する"""
        from ccl_runtime import register_dual, _adjunction_registry
        register_dual("noe", "zet")
        assert _adjunction_registry["noe"] == "zet"

    def test_right_adjoint_lookup(self):
        """right_adjoint で右随伴を取得できる"""
        from ccl_runtime import register_dual, right_adjoint
        register_dual("noe", "zet")
        assert right_adjoint("noe") == "zet"

    def test_left_adjoint_lookup(self):
        """left_adjoint で左随伴を取得できる"""
        from ccl_runtime import register_dual, left_adjoint
        register_dual("noe", "zet")
        assert left_adjoint("zet") == "noe"

    def test_adjoint_not_found(self):
        """未登録の随伴で AdjointNotFoundError が発生する"""
        from ccl_runtime import right_adjoint, left_adjoint, AdjointNotFoundError
        with self.assertRaises(AdjointNotFoundError):
            right_adjoint("unknown")
        with self.assertRaises(AdjointNotFoundError):
            left_adjoint("unknown")

    def test_adjunction_transpile_executes(self):
        """トランスパイルされた /noe||/zet のコードが実行可能"""
        source = transpile_ccl("/noe||/zet", include_header=True)
        assert_valid_python(source)
        # ダミーのワークフロー関数を注入して実行
        namespace = {
            "noe": lambda: None,
            "zet": lambda: None,
        }
        exec(source, namespace)


# =============================================================================
# Morphism 演算子テスト (<*, *>, >%)
# =============================================================================

class TestMorphismTranspile:
    """新 Morphism 演算子のトランスパイル検証"""

    def test_oplax_transpile(self):
        """<* → morphism_oplax を含む有効な Python"""
        source = transpile("/sag<*/ele")
        assert_valid_python(source)
        assert "morphism_oplax" in source

    def test_directed_fusion_transpile(self):
        """*> → morphism_directed_fuse を含む有効な Python"""
        source = transpile("/pei*>/lys")
        assert_valid_python(source)
        assert "morphism_directed_fuse" in source

    def test_pushforward_transpile(self):
        """>% → morphism_pushforward を含む有効な Python"""
        source = transpile("/bye>%/ops")
        assert_valid_python(source)
        assert "morphism_pushforward" in source

    def test_oplax_with_modifier(self):
        """<* + 修飾子 → morphism_oplax(sag(detail_level=3), ...)"""
        source = transpile("/sag+<*/ele+")
        assert_valid_python(source)
        assert "morphism_oplax" in source

    def test_directed_fusion_with_modifier(self):
        """*> + 修飾子 → morphism_directed_fuse(pei(detail_level=3), ...)"""
        source = transpile("/pei+*>/lys+")
        assert_valid_python(source)
        assert "morphism_directed_fuse" in source

    def test_pushforward_with_modifier(self):
        """>% + 修飾子 → morphism_pushforward(bye(detail_level=3), ...)"""
        source = transpile("/bye+>%/ops+")
        assert_valid_python(source)
        assert "morphism_pushforward" in source


class TestMorphismRuntime:
    """Morphism 演算子のランタイム実行検証"""

    def test_oplax_dict_target_priority(self):
        """<* (oplax): target 優先の加重マージ (0.3/0.7)"""
        from ccl_runtime import morphism_oplax
        source = {"score": 10.0, "name": "src"}
        target = {"score": 20.0, "extra": "added"}
        result = morphism_oplax(source, target)
        # target 優先: 10*0.3 + 20*0.7 = 17.0
        assert result["score"] == pytest.approx(17.0)
        # target のみのキーも吸収
        assert result["extra"] == "added"
        # source のみのキーは保持
        assert result["name"] == "src"

    def test_directed_fuse_dict(self):
        """*> (directed fusion): 融合して target キーでフィルタ"""
        from ccl_runtime import morphism_directed_fuse
        source = {"a": 1, "b": 2, "c": 3}
        target = {"b": 20, "d": 40}
        result = morphism_directed_fuse(source, target)
        # target キーのみ返る。target が source を上書き
        assert "b" in result
        assert result["b"] == 20  # target 優先 (update)
        assert "d" in result
        assert result["d"] == 40
        # source のみのキー (a, c) は除外される
        assert "a" not in result
        assert "c" not in result

    def test_pushforward_dict_tensor(self):
        """>% (pushforward): source を target の全次元にテンソル展開"""
        from ccl_runtime import morphism_pushforward
        source = {"x": 1}
        target = {"dim_a": "A", "dim_b": "B"}
        result = morphism_pushforward(source, target)
        # target の各キーが外次元、source の各キーが内次元
        assert "dim_a" in result
        assert "dim_b" in result
        assert result["dim_a"]["x"] == (1, "A")
        assert result["dim_b"]["x"] == (1, "B")

    def test_pushforward_numeric(self):
        """>% (pushforward): 数値 × 数値 = スカラー積"""
        from ccl_runtime import morphism_pushforward
        assert morphism_pushforward(3, 5) == 15

    def test_oplax_numeric(self):
        """<* (oplax): 数値 × 数値 = target × source"""
        from ccl_runtime import morphism_oplax
        assert morphism_oplax(3, 5) == 15

    def test_directed_fuse_numeric(self):
        """*> (directed fusion): 融合して target 方向にスケール"""
        from ccl_runtime import morphism_directed_fuse
        result = morphism_directed_fuse(4.0, 6.0)
        # 融合: (4+6)/2 = 5.0, target 方向: 5.0 * (6/6) = 5.0
        assert result == pytest.approx(5.0)

    def test_transpile_and_execute_oplax(self):
        """<* のトランスパイル結果が実行可能"""
        source = transpile_ccl("/sag<*/ele", include_header=True)
        assert_valid_python(source)
        namespace = {
            "sag": lambda: {"review": 0.5},
            "ele": lambda: {"review": 0.9, "critique": "deep"},
        }
        exec(source, namespace)

    def test_transpile_and_execute_directed_fusion(self):
        """*> のトランスパイル結果が実行可能"""
        source = transpile_ccl("/pei*>/lys", include_header=True)
        assert_valid_python(source)
        namespace = {
            "pei": lambda: {"data": [1, 2, 3]},
            "lys": lambda: {"conclusion": "ok"},
        }
        exec(source, namespace)

    def test_transpile_and_execute_pushforward(self):
        """>% のトランスパイル結果が実行可能"""
        source = transpile_ccl("/bye>%/ops", include_header=True)
        assert_valid_python(source)
        namespace = {
            "bye": lambda: {"lesson": "learned"},
            "ops": lambda: {"area_a": None, "area_b": None},
        }
        exec(source, namespace)


# =============================================================================
# エントリポイント
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


