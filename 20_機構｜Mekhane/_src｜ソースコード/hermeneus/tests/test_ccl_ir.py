# PROOF: [L2/テスト] <- hermeneus/tests/ CCL IR テスト
"""
CCL IR (中間表現) テスト

P2: ast_to_ir 変換、CCLIRNode 属性、CCLIR コンテナ機能のテスト。
10 ケース以上をカバー。
"""

import pytest
from hermeneus.src.parser import CCLParser
from hermeneus.src.ccl_ir import (
    ast_to_ir,
    CCLIR,
    CCLIRNode,
    BindingTime,
    _depth_from_workflow,
    _classify_binding_time,
    _reset_counter,
)
from hermeneus.src.ccl_ast import (
    Workflow, Sequence, Fusion, Oscillation, ForLoop, IfCondition,
    MacroRef, OpenEnd, OpType, Condition, TaggedBlock,
    ConvergenceLoop, Pipeline, Parallel, Group, WhileLoop,
)


# ヘルパー: CCL 式を parse → IR に変換
def _ccl_to_ir(ccl_expr: str) -> CCLIR:
    """CCL 式を parse → IR に変換するヘルパー。"""
    parser = CCLParser()
    ast = parser.parse(ccl_expr)
    return ast_to_ir(ast, ccl_expr=ccl_expr)


# =============================================================================
# T1: 単一ワークフロー
# =============================================================================

class TestSingleWorkflow:
    """単一 WF の IR 変換テスト。"""

    def test_noe_plus_depth_3(self):
        """'/noe+' → depth_discrete=3, BindingTime.STATIC"""
        ir = _ccl_to_ir("/noe+")
        assert ir.root.wf_id == "noe"
        assert ir.root.depth_discrete == 3
        assert ir.root.binding_time == BindingTime.STATIC
        assert ir.root.ast_type == "Workflow"

    def test_bou_minus_depth_1(self):
        """'/bou-' → depth_discrete=1"""
        ir = _ccl_to_ir("/bou-")
        assert ir.root.wf_id == "bou"
        assert ir.root.depth_discrete == 1

    def test_ene_default_depth_2(self):
        """'/ene' → depth_discrete=2 (デフォルト)"""
        ir = _ccl_to_ir("/ene")
        assert ir.root.depth_discrete == 2

    def test_max_depth_property(self):
        """CCLIR.max_depth は全ノードの最大深度。"""
        ir = _ccl_to_ir("/noe+")
        assert ir.max_depth == 3


# =============================================================================
# T2: シーケンス (Sequence)
# =============================================================================

class TestSequence:
    """シーケンスの IR 変換テスト。"""

    def test_sequence_children(self):
        """'/noe+_/dia-' → 2子ノード"""
        ir = _ccl_to_ir("/noe+_/dia-")
        assert ir.root.ast_type == "Sequence"
        assert len(ir.root.children) == 2
        assert ir.root.children[0].wf_id == "noe"
        assert ir.root.children[1].wf_id == "dia"

    def test_sequence_depth_propagation(self):
        """シーケンスの深度は子の最大値。"""
        ir = _ccl_to_ir("/noe+_/dia-")
        assert ir.root.depth_discrete == 3  # max(3, 1)

    def test_sequence_all_static(self):
        """全子が STATIC → シーケンスも STATIC。"""
        ir = _ccl_to_ir("/noe_/bou")
        assert ir.root.binding_time == BindingTime.STATIC


# =============================================================================
# T3: 融合 (Fusion)
# =============================================================================

class TestFusion:
    """融合の IR 変換テスト。"""

    def test_fusion_children(self):
        """'/noe+*/dia-' → Fusion, 2子ノード"""
        ir = _ccl_to_ir("/noe+*/dia-")
        assert ir.root.ast_type == "Fusion"
        assert len(ir.root.children) == 2
        assert ir.root.depth_discrete == 3  # max(3, 1)

    def test_fusion_static_propagation(self):
        """両子が STATIC → Fusion も STATIC。"""
        ir = _ccl_to_ir("/noe*/dia")
        assert ir.root.binding_time == BindingTime.STATIC


# =============================================================================
# T4: 振動 (Oscillation)
# =============================================================================

class TestOscillation:
    """振動の IR 変換テスト。"""

    def test_oscillation_dynamic(self):
        """振動は常に DYNAMIC。"""
        ir = _ccl_to_ir("/noe+~/dia+")
        assert ir.root.ast_type == "Oscillation"
        assert ir.root.binding_time == BindingTime.DYNAMIC

    def test_convergent_oscillation(self):
        """'~*' 収束振動。"""
        ir = _ccl_to_ir("/noe+~*/dia+")
        assert ir.root.ast_type == "Oscillation"


# =============================================================================
# T5: 制御構文 (ForLoop, IfCondition)
# =============================================================================

class TestControlFlow:
    """制御構文の IR 変換テスト。"""

    def test_for_loop_dynamic(self):
        """ForLoop は DYNAMIC。"""
        ir = _ccl_to_ir("F:[×3]{/noe+}")
        assert ir.root.ast_type == "ForLoop"
        assert ir.root.binding_time == BindingTime.DYNAMIC
        assert ir.root.metadata.get("iterations") == 3
        assert len(ir.root.children) == 1
        assert ir.root.children[0].wf_id == "noe"

    def test_if_condition_dynamic(self):
        """IfCondition は DYNAMIC。"""
        ir = _ccl_to_ir("I:[V[]>0.5]{/noe+}")
        assert ir.root.ast_type == "IfCondition"
        assert ir.root.binding_time == BindingTime.DYNAMIC


# =============================================================================
# T6: CCLIR コンテナ機能
# =============================================================================

class TestCCLIRContainer:
    """CCLIR コンテナのテスト。"""

    def test_all_nodes_populated(self):
        """all_nodes はフラットリストとして全ノードを含む。"""
        ir = _ccl_to_ir("/noe+_/dia-_/bou")
        # Sequence (1) + 3 Workflows = 4 ノード
        assert len(ir.all_nodes) == 4

    def test_workflow_nodes_filter(self):
        """workflow_nodes は WF ノードのみ返す。"""
        ir = _ccl_to_ir("/noe+_/dia-")
        wf_nodes = ir.workflow_nodes
        assert len(wf_nodes) == 2
        assert all(n.wf_id is not None for n in wf_nodes)

    def test_ccl_expr_stored(self):
        """元の CCL 式が保存されている。"""
        ir = _ccl_to_ir("/noe+")
        assert ir.ccl_expr == "/noe+"


# =============================================================================
# T7: Precision 伝搬
# =============================================================================

class TestPrecisionPropagation:
    """precision_ml 伝搬テスト。"""

    def test_default_none(self):
        """Phase 1: precision_ml は全て None。"""
        ir = _ccl_to_ir("/noe+")
        assert ir.root.precision_ml is None
        assert ir.global_precision_ml is None

    def test_propagate_precision(self):
        """propagate_precision で全ノードに伝搬される。"""
        ir = _ccl_to_ir("/noe+_/dia-")
        ir.propagate_precision(precision_ml=0.75, coherence=0.9, drift=0.1)
        assert ir.global_precision_ml == 0.75
        for node in ir.all_nodes:
            assert node.precision_ml == 0.75
            assert node.coherence == 0.9
            assert node.drift == 0.1

    def test_propagate_no_overwrite(self):
        """既に値を持つノードは上書きしない。"""
        ir = _ccl_to_ir("/noe+_/dia-")
        ir.all_nodes[0].precision_ml = 0.5  # 手動設定
        ir.propagate_precision(precision_ml=0.8)
        assert ir.all_nodes[0].precision_ml == 0.5  # 上書きされない
        # 未設定ノードには伝搬
        for node in ir.all_nodes[1:]:
            assert node.precision_ml == 0.8


# =============================================================================
# T8: effective_depth (precision_ml 有無による分岐)
# =============================================================================

class TestEffectiveDepth:
    """effective_depth プロパティのテスト。"""

    def test_no_precision_returns_discrete(self):
        """precision_ml=None → depth_discrete をそのまま返す。"""
        ir = _ccl_to_ir("/noe+")
        assert ir.root.effective_depth == 3.0

    def test_high_precision_reduces_depth(self):
        """precision_ml=1.0 → depth を1段下げる (exploit)。"""
        ir = _ccl_to_ir("/noe+")
        ir.root.precision_ml = 1.0
        # 加算式: 3 + (1 - 2×1.0) = 3 - 1 = 2.0
        assert ir.root.effective_depth == 2.0

    def test_low_precision_increases_depth(self):
        """precision_ml=0.0 → depth を1段上げる (explore)。"""
        ir = _ccl_to_ir("/ene")  # depth_discrete = 2
        ir.root.precision_ml = 0.0
        # 加算式: 2 + (1 - 2×0.0) = 2 + 1 = 3.0
        assert ir.root.effective_depth == 3.0

    def test_mid_precision_maintains_depth(self):
        """precision_ml=0.5 → 深度据え置き (中立)。"""
        ir = _ccl_to_ir("/ene")  # depth_discrete = 2
        ir.root.precision_ml = 0.5
        # 加算式: 2 + (1 - 2×0.5) = 2 + 0 = 2.0
        assert ir.root.effective_depth == 2.0


# =============================================================================
# T9: format_tree (デバッグ出力)
# =============================================================================

class TestFormatTree:
    """IR ツリー表示テスト。"""

    def test_format_tree_single(self):
        """単一ノードの表示。"""
        ir = _ccl_to_ir("/noe+")
        tree = ir.format_tree()
        assert "noe" in tree
        assert "d=3" in tree
        assert "STATIC" in tree

    def test_format_tree_nested(self):
        """ネストしたツリーの表示。"""
        ir = _ccl_to_ir("/noe+_/dia-")
        tree = ir.format_tree()
        lines = tree.strip().split("\n")
        assert len(lines) == 3  # Sequence + 2 WF


# =============================================================================
# T10: マクロ参照・末端ノード
# =============================================================================

class TestEdgeCases:
    """エッジケースのテスト。"""

    def test_macro_ref(self):
        """'@think' → MacroRef, STATIC。"""
        ir = _ccl_to_ir("@think")
        assert ir.root.ast_type == "MacroRef"
        assert ir.root.binding_time == BindingTime.STATIC
        assert ir.root.metadata.get("macro_name") == "think"

    def test_tagged_block(self):
        """'V:{/noe+}' → TaggedBlock, tag='V'。"""
        ir = _ccl_to_ir("V:{/noe+}")
        assert ir.root.ast_type == "TaggedBlock"
        assert ir.root.metadata.get("tag") == "V"
        assert len(ir.root.children) == 1
        assert ir.root.children[0].wf_id == "noe"

    def test_convergence_loop(self):
        """/noe+ ~> V[]<0.3 → ConvergenceLoop, DYNAMIC。"""
        ir = _ccl_to_ir("/noe+>>V[]<0.3")
        assert ir.root.ast_type == "ConvergenceLoop"
        assert ir.root.binding_time == BindingTime.DYNAMIC

    def test_pipeline(self):
        """/noe+&>/dia- → Pipeline。"""
        ir = _ccl_to_ir("/noe+&>/dia-")
        assert ir.root.ast_type == "Pipeline"
        assert len(ir.root.children) == 2

    def test_group_with_modifier(self):
        """'(/noe_/dia)+' → Group, depth=3。"""
        ir = _ccl_to_ir("(/noe_/dia)+")
        assert ir.root.ast_type == "Group"
        assert ir.root.depth_discrete == 3  # + で上書き


# =============================================================================
# T9: Morphism (>*, <*, *>, >%, <<)
# =============================================================================

class TestMorphismIR:
    """Morphism の IR 変換テスト。"""

    def test_oplax_basic(self):
        """/noe+<*/dia+ → Morphism, children=2, direction=oplax"""
        ir = _ccl_to_ir("/noe+<*/dia+")
        assert ir.root.ast_type == "Morphism"
        assert len(ir.root.children) == 2
        assert ir.root.metadata["direction"] == "oplax"
        # depth は子の最大値
        assert ir.root.depth_discrete == 3

    def test_lax_basic(self):
        """/noe+>*/dia → Morphism, direction=lax, depth=max(3,2)=3"""
        ir = _ccl_to_ir("/noe+>*/dia")
        assert ir.root.ast_type == "Morphism"
        assert ir.root.metadata["direction"] == "lax"
        assert ir.root.depth_discrete == 3

    def test_morphism_binding_time(self):
        """静的な source + target → STATIC"""
        ir = _ccl_to_ir("/noe>*/dia")
        assert ir.root.binding_time == BindingTime.STATIC

    def test_morphism_in_all_nodes(self):
        """/noe<*/dia → all_nodes に3ノード: Morphism + Workflow×2"""
        ir = _ccl_to_ir("/noe<*/dia")
        assert len(ir.all_nodes) == 3
        types = {n.ast_type for n in ir.all_nodes}
        assert "Morphism" in types
        assert "Workflow" in types


# =============================================================================
# T10: Adjunction (||, |>, <|)
# =============================================================================

class TestAdjunctionIR:
    """Adjunction の IR 変換テスト。"""

    def test_adjunction_declaration(self):
        """/noe+||/dia+ → Adjunction, children=2"""
        ir = _ccl_to_ir("/noe+||/dia+")
        assert ir.root.ast_type == "Adjunction"
        assert len(ir.root.children) == 2

    def test_adjunction_binding_time(self):
        """静的な随伴宣言 → STATIC"""
        ir = _ccl_to_ir("/noe||/dia")
        assert ir.root.binding_time == BindingTime.STATIC
