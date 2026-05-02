# PROOF: [L2/テスト] <- hermeneus/tests/test_oblivion.py @oblivion 演算子テスト
"""
Lēthē Phase C — @oblivion 演算子テスト

テスト対象:
    1. パーサー: @oblivion[θ=...]{...} 構文の AST 変換
    2. LUT: φ 値の完全性と取得ロジック
    3. フィルタリング: should_skip / filter_steps_by_phi
    4. E2E: score_ccl_oblivion の 3 層スコアリング
"""

import pytest

from hermeneus.src.ccl_ast import OblivionBlock, Workflow, Morphism, Sequence
from hermeneus.src.parser import CCLParser, parse_ccl
from hermeneus.src.oblivion_lut import (
    PHI_LUT,
    PHI_DEFAULT,
    get_phi,
    should_skip,
    filter_steps_by_phi,
    verify_lut_coverage,
)
from hermeneus.src.forgetfulness_score import score_ccl_oblivion


# =============================================================================
# C1: AST ノードテスト
# =============================================================================


class TestOblivionBlockAST:
    """OblivionBlock AST ノードの基本テスト"""

    def test_create_oblivion_block(self):
        """OblivionBlock が正しく生成できる"""
        block = OblivionBlock(
            theta=0.3,
            body=Workflow(id="noe"),
            phi_scores={"noe": 0.15},
        )
        assert block.theta == 0.3
        assert isinstance(block.body, Workflow)
        assert block.phi_scores["noe"] == 0.15

    def test_default_phi_scores(self):
        """phi_scores のデフォルトは空辞書"""
        block = OblivionBlock(theta=0.5, body=Workflow(id="noe"))
        assert block.phi_scores == {}


# =============================================================================
# C2: パーサーテスト
# =============================================================================


class TestOblivionParser:
    """@oblivion 構文のパーステスト"""

    def setup_method(self):
        self.parser = CCLParser()

    def test_parse_oblivion_basic(self):
        """基本構文: @oblivion[θ=0.3]{/noe+}"""
        ast = self.parser.parse('@oblivion[θ=0.3]{/noe+}')
        assert isinstance(ast, OblivionBlock)
        assert ast.theta == 0.3
        assert isinstance(ast.body, Workflow)
        assert ast.body.id == "noe"

    def test_parse_oblivion_shorthand(self):
        """省略形: @oblivion[0.5]{/ske}"""
        ast = self.parser.parse('@oblivion[0.5]{/ske}')
        assert isinstance(ast, OblivionBlock)
        assert ast.theta == 0.5

    def test_parse_oblivion_with_morphism(self):
        """合成演算子込み: @oblivion[θ=0.3]{/noe+ >> /dia+}"""
        ast = self.parser.parse('@oblivion[θ=0.3]{/noe+ >> /dia+}')
        assert isinstance(ast, OblivionBlock)
        assert isinstance(ast.body, Morphism)
        assert ast.body.direction == "forward"

    def test_parse_oblivion_with_sequence(self):
        """シーケンス込み: @oblivion[θ=0.4]{/noe+_/dia+_/ene+}"""
        ast = self.parser.parse('@oblivion[θ=0.4]{/noe+_/dia+_/ene+}')
        assert isinstance(ast, OblivionBlock)
        assert isinstance(ast.body, Sequence)
        assert len(ast.body.steps) == 3

    def test_parse_oblivion_phi_injection(self):
        """φ が LUT から自動注入される"""
        ast = self.parser.parse('@oblivion[θ=0.3]{/noe+ >> /hyp+}')
        assert isinstance(ast, OblivionBlock)
        # noe と hyp の φ が注入されているはず
        assert "noe" in ast.phi_scores
        assert "hyp" in ast.phi_scores
        # noe (Telos) < hyp (Chronos)
        assert ast.phi_scores["noe"] < ast.phi_scores["hyp"]

    def test_parse_oblivion_theta_validation_low(self):
        """θ < 0 でエラー"""
        with pytest.raises(ValueError, match="out of range"):
            self.parser.parse('@oblivion[θ=-0.1]{/noe+}')

    def test_parse_oblivion_theta_validation_high(self):
        """θ > 1 でエラー"""
        with pytest.raises(ValueError, match="out of range"):
            self.parser.parse('@oblivion[θ=1.5]{/noe+}')

    def test_parse_oblivion_invalid_syntax(self):
        """不正な構文でエラー"""
        with pytest.raises(ValueError, match="@oblivion"):
            self.parser.parse('@oblivion{/noe+}')

    def test_parse_oblivion_theta_boundaries(self):
        """θ の境界値 (0.0 と 1.0) は有効"""
        ast0 = self.parser.parse('@oblivion[θ=0.0]{/noe+}')
        assert ast0.theta == 0.0
        ast1 = self.parser.parse('@oblivion[θ=1.0]{/noe+}')
        assert ast1.theta == 1.0


# =============================================================================
# C3: φ LUT テスト
# =============================================================================


class TestPhiLUT:
    """φ Look-Up Table のテスト"""

    # 24 基本 Poiesis 動詞
    BASIC_VERBS = {
        "noe", "bou", "zet", "ene",
        "ske", "sag", "pei", "tek",
        "kat", "epo", "pai", "dok",
        "lys", "ops", "akr", "arc",
        "beb", "ele", "kop", "dio",
        "hyp", "prm", "ath", "par",
    }

    def test_lut_covers_24_basic_verbs(self):
        """LUT に 24 基本動詞が全て含まれる"""
        for verb in self.BASIC_VERBS:
            assert verb in PHI_LUT, f"Missing verb: {verb}"

    def test_phi_range(self):
        """全 φ 値が [0.0, 1.0] の範囲内"""
        for verb, phi in PHI_LUT.items():
            assert 0.0 <= phi <= 1.0, f"{verb}: φ={phi} out of range"

    def test_get_phi_known(self):
        """既知の動詞の φ 取得"""
        assert get_phi("noe") == 0.15
        assert get_phi("hyp") == 0.55

    def test_get_phi_unknown(self):
        """未知の動詞はデフォルト値"""
        assert get_phi("nonexistent") == PHI_DEFAULT

    def test_telos_lower_than_chronos(self):
        """Telos 族は Chronos 族より低忘却"""
        telos_avg = sum(get_phi(v) for v in ["noe", "bou", "zet", "ene"]) / 4
        chronos_avg = sum(get_phi(v) for v in ["hyp", "prm", "ath", "par"]) / 4
        assert telos_avg < chronos_avg

    def test_should_skip_true(self):
        """φ > θ → 忘却"""
        # hyp (φ=0.55) > θ=0.3 → True
        assert should_skip("hyp", 0.3) is True

    def test_should_skip_false(self):
        """φ ≤ θ → 保持"""
        # noe (φ=0.15) ≤ θ=0.3 → False
        assert should_skip("noe", 0.3) is False

    def test_should_skip_equal(self):
        """φ = θ → 保持 (≤)"""
        # noe (φ=0.15) ≤ θ=0.15 → False
        assert should_skip("noe", 0.15) is False


# =============================================================================
# C3: フィルタリングテスト
# =============================================================================


class TestFilterSteps:
    """filter_steps_by_phi のテスト"""

    def test_filter_basic(self):
        """基本フィルタリング: φ > θ をスキップ"""
        steps = [
            Workflow(id="noe"),   # φ=0.15
            Workflow(id="hyp"),   # φ=0.55
            Workflow(id="bou"),   # φ=0.20
        ]
        result = filter_steps_by_phi(steps, theta=0.30)
        assert len(result) == 2
        assert result[0].id == "noe"
        assert result[1].id == "bou"

    def test_filter_none_skipped(self):
        """θ=1.0 → 全て保持"""
        steps = [Workflow(id="noe"), Workflow(id="hyp")]
        result = filter_steps_by_phi(steps, theta=1.0)
        assert len(result) == 2

    def test_filter_all_skipped(self):
        """θ=0.0 → boot/ax 以外は全て忘却"""
        steps = [Workflow(id="hyp"), Workflow(id="pei")]
        result = filter_steps_by_phi(steps, theta=0.0)
        assert len(result) == 0

    def test_filter_preserves_order(self):
        """フィルタ後の順序が保持される"""
        steps = [
            Workflow(id="noe"),   # φ=0.15 → 保持
            Workflow(id="hyp"),   # φ=0.55 → 忘却
            Workflow(id="ene"),   # φ=0.25 → 保持
            Workflow(id="pei"),   # φ=0.50 → 忘却
            Workflow(id="bou"),   # φ=0.20 → 保持
        ]
        result = filter_steps_by_phi(steps, theta=0.30)
        assert [s.id for s in result] == ["noe", "ene", "bou"]

    def test_filter_empty_list(self):
        """空リスト"""
        assert filter_steps_by_phi([], theta=0.5) == []


# =============================================================================
# C4: score_ccl_oblivion E2E テスト
# =============================================================================


class TestScoreCclOblivion:
    """score_ccl_oblivion の 3 層スコアリングテスト"""

    def test_basic_oblivion_scoring(self):
        """基本的な忘却スコアリング"""
        result = score_ccl_oblivion("/noe+", theta=0.5)
        assert result.theta == 0.5
        assert "noe" in result.phi_scores
        # noe (φ=0.15) ≤ 0.5 → 保持
        assert "noe" in result.retained_verbs
        assert "noe" not in result.skipped_verbs

    def test_mixed_retention_skipping(self):
        """保持と忘却が混在"""
        result = score_ccl_oblivion("/noe+_/hyp+_/bou+", theta=0.3)
        # noe (0.15) → 保持, hyp (0.55) → 忘却, bou (0.20) → 保持
        assert "noe" in result.retained_verbs
        assert "bou" in result.retained_verbs
        assert "hyp" in result.skipped_verbs

    def test_retention_ratio(self):
        """保持率の計算"""
        result = score_ccl_oblivion("/noe+_/hyp+_/bou+", theta=0.3)
        # 3 動詞中 2 保持 = 2/3 ≈ 0.667
        assert abs(result.retention_ratio - 2.0 / 3.0) < 0.01

    def test_implicit_result_included(self):
        """Layer 0+1 (既存) の結果が含まれる"""
        result = score_ccl_oblivion("/noe+", theta=0.5)
        assert result.implicit_result is not None
        assert hasattr(result.implicit_result, 'explicit')


# =============================================================================
# パーサー回帰テスト
# =============================================================================


class TestParserRegression:
    """@oblivion 追加後の既存パーサー機能回帰テスト"""

    def setup_method(self):
        self.parser = CCLParser()

    def test_basic_workflow_still_works(self):
        """基本 WF パースが壊れていない"""
        ast = self.parser.parse("/noe+")
        assert isinstance(ast, Workflow)

    def test_macro_ref_still_works(self):
        """@macro パースが壊れていない"""
        from hermeneus.src.ccl_ast import MacroRef
        ast = self.parser.parse("@think")
        assert isinstance(ast, MacroRef)

    def test_morphism_still_works(self):
        """>> 演算子が壊れていない"""
        ast = self.parser.parse("/noe+ >> /dia+")
        assert isinstance(ast, Morphism)

    def test_sequence_still_works(self):
        """_ 演算子が壊れていない"""
        ast = self.parser.parse("/noe+_/dia+_/ene+")
        assert isinstance(ast, Sequence)
