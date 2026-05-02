"""P5/P6 統合テスト: precision_router → IR 注入 + Linkage Metrics の検証。

P5: diff_to_precision_ml() のマッピングと、IR ツリー全体への precision 伝播。
P6: PrecisionResult / LinkageMetrics の構造、WF description 読取、coherence/drift 計算。
"""

import pytest

from hermeneus.src.parser import parse_ccl
from hermeneus.src.ccl_ir import ast_to_ir, diff_to_precision_ml, CCLIR
from hermeneus.src.precision_router import (
    PrecisionResult,
    LinkageMetrics,
    _cosine_similarity,
    _load_wf_descriptions,
)


# =============================================================================
# ヘルパー
# =============================================================================

def _ccl_to_ir(expr: str) -> CCLIR:
    """CCL 式 → IR 変換ヘルパー。"""
    ast = parse_ccl(expr)
    return ast_to_ir(ast, ccl_expr=expr)


# =============================================================================
# T1: diff_to_precision_ml マッピング (境界値テスト)
# =============================================================================

class TestDiffToPrecisionMl:
    """diff → precision_ml の線形マッピング検証。"""

    def test_positive_one(self):
        """diff=+1.0 → precision_ml=1.0 (exploit)。"""
        assert diff_to_precision_ml(1.0) == 1.0

    def test_negative_one(self):
        """diff=-1.0 → precision_ml=0.0 (explore)。"""
        assert diff_to_precision_ml(-1.0) == 0.0

    def test_zero(self):
        """diff=0.0 → precision_ml=0.5 (中立)。"""
        assert diff_to_precision_ml(0.0) == 0.5

    def test_typical_exploit(self):
        """diff=+0.22 (実測の exploit 上限付近)。"""
        result = diff_to_precision_ml(0.22)
        assert 0.6 < result < 0.65  # (0.22 + 1) / 2 = 0.61

    def test_typical_explore(self):
        """diff=-0.13 (実測の explore 付近)。"""
        result = diff_to_precision_ml(-0.13)
        assert 0.43 < result < 0.44  # (-0.13 + 1) / 2 = 0.435

    def test_clamp_above(self):
        """diff > 1.0 はクランプされる。"""
        assert diff_to_precision_ml(1.5) == 1.0

    def test_clamp_below(self):
        """diff < -1.0 はクランプされる。"""
        assert diff_to_precision_ml(-1.5) == 0.0


# =============================================================================
# T2: effective_depth の連続化 (precision 注入後)
# =============================================================================

class TestEffectiveDepthWithPrecision:
    """precision_ml 注入後の effective_depth が加算式で正しく計算されるか。"""

    def test_exploit_reduces_depth(self):
        """exploit (diff=+0.22) → depth 減少。"""
        ir = _ccl_to_ir("/noe+")  # depth_discrete = 3
        p_ml = diff_to_precision_ml(0.22)  # ≈ 0.61
        ir.propagate_precision(precision_ml=p_ml)
        # 加算式: 3 + (1 - 2×0.61) = 3 + (-0.22) = 2.78
        assert 2.7 < ir.root.effective_depth < 2.9

    def test_explore_increases_depth(self):
        """explore (diff=-0.13) → depth 増加。"""
        ir = _ccl_to_ir("/ene")  # depth_discrete = 2
        p_ml = diff_to_precision_ml(-0.13)  # ≈ 0.435
        ir.propagate_precision(precision_ml=p_ml)
        # 加算式: 2 + (1 - 2×0.435) = 2 + 0.13 = 2.13
        assert 2.1 < ir.root.effective_depth < 2.2

    def test_neutral_maintains_depth(self):
        """中立 (diff=0.0) → depth 据え置き。"""
        ir = _ccl_to_ir("/ene")  # depth_discrete = 2
        p_ml = diff_to_precision_ml(0.0)  # = 0.5
        ir.propagate_precision(precision_ml=p_ml)
        # 加算式: 2 + (1 - 2×0.5) = 2 + 0 = 2.0
        assert ir.root.effective_depth == 2.0


# =============================================================================
# T3: ツリー全体への伝播 (子ノード)
# =============================================================================

class TestPrecisionPropagationInTree:
    """precision_ml がツリー全体に伝播するか。"""

    def test_sequence_propagation(self):
        """Sequence の子ノードにも precision が伝播する。"""
        ir = _ccl_to_ir("/noe+_/ene+")  # Sequence → 2 children
        p_ml = diff_to_precision_ml(0.1)  # ≈ 0.55
        ir.propagate_precision(precision_ml=p_ml)

        # ルートに precision が設定されている
        assert ir.root.precision_ml is not None

        # 全子ノードにも伝播している
        for child in ir.root.children:
            assert child.precision_ml is not None
            assert child.precision_ml == ir.root.precision_ml

    def test_no_overwrite_existing(self):
        """既に precision が設定されている子ノードは上書きしない。"""
        ir = _ccl_to_ir("/noe+_/ene+")
        # 先に子ノードに precision を設定
        if ir.root.children:
            ir.root.children[0].precision_ml = 0.9

        # ルートから伝播
        p_ml = diff_to_precision_ml(0.0)  # 0.5
        ir.propagate_precision(precision_ml=p_ml)

        # 子ノード[0] は上書きされない
        assert ir.root.children[0].precision_ml == 0.9
        # 子ノード[1] には伝播される
        if len(ir.root.children) > 1:
            assert ir.root.children[1].precision_ml == p_ml


# =============================================================================
# T4: PrecisionResult 構造テスト (P6)
# =============================================================================

class TestPrecisionResult:
    """PrecisionResult dataclass の構造検証。"""

    def test_neutral_result(self):
        """中立値の PrecisionResult が正しく構成される。"""
        r = PrecisionResult(diff=0.0, sim_simple=0.0, sim_complex=0.0, embedding=[])
        assert r.diff == 0.0
        assert r.embedding == []

    def test_frozen(self):
        """frozen=True なので属性変更不可。"""
        r = PrecisionResult(diff=0.1, sim_simple=0.5, sim_complex=0.4, embedding=[1.0])
        with pytest.raises(AttributeError):
            r.diff = 0.2  # type: ignore

    def test_embedding_preserved(self):
        """embedding が保持される。"""
        emb = [0.1, 0.2, 0.3]
        r = PrecisionResult(diff=0.1, sim_simple=0.6, sim_complex=0.5, embedding=emb)
        assert r.embedding == emb
        assert len(r.embedding) == 3


# =============================================================================
# T5: LinkageMetrics 構造テスト (P6)
# =============================================================================

class TestLinkageMetrics:
    """LinkageMetrics dataclass の構造検証。"""

    def test_basic(self):
        """基本的な LinkageMetrics 構成。"""
        m = LinkageMetrics(coherence=0.8, drift=0.2, wf_ids=("noe", "ene"), reasoning="test")
        assert m.coherence == 0.8
        assert m.drift == 0.2
        assert m.wf_ids == ("noe", "ene")

    def test_frozen(self):
        """frozen=True で変更不可。"""
        m = LinkageMetrics(coherence=0.5, drift=0.5, wf_ids=(), reasoning="")
        with pytest.raises(AttributeError):
            m.coherence = 0.9  # type: ignore

    def test_none_values(self):
        """フォールバック時は None (#5 /dio 修正)。"""
        m = LinkageMetrics(coherence=None, drift=None, wf_ids=("noe",), reasoning="fallback")
        assert m.coherence is None
        assert m.drift is None


# =============================================================================
# T6: WF description 読取テスト (P6)
# =============================================================================

class TestWfDescriptions:
    """_load_wf_descriptions が WF ファイルの description を正しく読み取るか。"""

    def test_known_wf(self):
        """既知の WF (noe) の description が取得できる。"""
        descs = _load_wf_descriptions(["noe"])
        assert len(descs) == 1
        assert "Noēsis" in descs[0]

    def test_multiple_wfs(self):
        """複数 WF の description が取得できる。"""
        descs = _load_wf_descriptions(["noe", "ene", "bou"])
        assert len(descs) == 3

    def test_unknown_wf(self):
        """存在しない WF は空リスト。"""
        descs = _load_wf_descriptions(["nonexistent_wf_xyz"])
        assert len(descs) == 0


# =============================================================================
# T7: coherence/drift 手動計算テスト (P6)
# =============================================================================

class TestCoherenceDriftCalculation:
    """_cosine_similarity を使った coherence/drift のロジック検証。"""

    def test_identical_vectors_coherence(self):
        """同一ベクトル同士の cos sim = 1.0 → coherence = 1.0。"""
        v = [1.0, 0.0, 0.0]
        sim = _cosine_similarity(v, v)
        assert abs(sim - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        """直交ベクトルの cos sim = 0.0。"""
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]
        sim = _cosine_similarity(v1, v2)
        assert abs(sim) < 1e-6

    def test_drift_from_similarity(self):
        """drift = 1 - mean_sim。高 sim → 低 drift。"""
        # 同一ベクトルなら sim=1.0、drift=0.0
        v = [0.5, 0.5, 0.5]
        sim = _cosine_similarity(v, v)
        drift = 1.0 - sim
        assert abs(drift) < 1e-6

    def test_coherence_pair_average(self):
        """2 WF の coherence = 2 WF 間 cos sim。"""
        v1 = [1.0, 0.0]
        v2 = [0.707, 0.707]  # ≈ 45°
        sim = _cosine_similarity(v1, v2)
        # cos(45°) ≈ 0.707
        assert 0.69 < sim < 0.72


# =============================================================================
# T8: coherence/drift → IR 伝播テスト (P6)
# =============================================================================

class TestLinkagePropagationToIR:
    """coherence/drift が IR ノードに正しく伝播するか。"""

    def test_coherence_drift_propagation(self):
        """coherence と drift が全ノードに伝播する。"""
        ir = _ccl_to_ir("/noe+_/ene+")
        ir.propagate_precision(precision_ml=0.5, coherence=0.85, drift=0.15)

        assert ir.root.coherence == 0.85
        assert ir.root.drift == 0.15
        for child in ir.root.children:
            assert child.coherence == 0.85
            assert child.drift == 0.15

    def test_none_linkage_no_override(self):
        """coherence/drift=None の場合、既存値を上書きしない。"""
        ir = _ccl_to_ir("/noe+")
        # 先に coherence を設定
        ir.root.coherence = 0.9
        ir.propagate_precision(precision_ml=0.5, coherence=None, drift=None)
        # 上書きされない
        assert ir.root.coherence == 0.9


# =============================================================================
# T9: effective_depth linkage 補正テスト (#1 /dio 修正)
# =============================================================================

class TestEffectiveDepthLinkage:
    """effective_depth が coherence/drift を反映するか (#1 /ele+ → /dio)。"""

    def test_no_linkage_same_as_before(self):
        """linkage 未注入時は従来通り動く。"""
        ir = _ccl_to_ir("/noe")  # depth_discrete=2
        ir.propagate_precision(precision_ml=0.5, coherence=None, drift=None)
        # precision_ml=0.5 → シフト 0、depth=2 + 0 = 2.0
        assert abs(ir.root.effective_depth - 2.0) < 1e-6

    def test_high_drift_increases_depth(self):
        """高 drift → context-WF 乖離 → 深く。"""
        ir = _ccl_to_ir("/noe")  # depth_discrete=2
        ir.propagate_precision(precision_ml=0.5, coherence=1.0, drift=0.8)
        # base = 2.0 + 0.0 + 0.5*0.8 + 0.3*(1-1.0) = 2.4
        assert abs(ir.root.effective_depth - 2.4) < 1e-6

    def test_low_coherence_increases_depth(self):
        """低 coherence → WF 群バラバラ → 深く。"""
        ir = _ccl_to_ir("/noe")  # depth_discrete=2
        ir.propagate_precision(precision_ml=0.5, coherence=0.0, drift=0.0)
        # base = 2.0 + 0.0 + 0.0 + 0.3*(1-0.0) = 2.3
        assert abs(ir.root.effective_depth - 2.3) < 1e-6

    def test_both_linkage_combined(self):
        """両方の linkage が組み合わさる。"""
        ir = _ccl_to_ir("/noe")  # depth_discrete=2
        ir.propagate_precision(precision_ml=0.5, coherence=0.5, drift=0.6)
        # base = 2.0 + 0.0 + 0.5*0.6 + 0.3*(1-0.5) = 2.0 + 0.3 + 0.15 = 2.45
        assert abs(ir.root.effective_depth - 2.45) < 1e-6

    def test_clamp_upper_bound(self):
        """最大値 3.0 を超えない。"""
        ir = _ccl_to_ir("/noe+")  # depth_discrete=3
        ir.propagate_precision(precision_ml=0.0, coherence=0.0, drift=1.0)
        # base = 3 + 1.0 + 0.5 + 0.3 = 4.8 → clamp → 3.0
        assert ir.root.effective_depth == 3.0

