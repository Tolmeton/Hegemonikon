# PROOF: [L3/テスト] <- hermeneus/tests/test_forgetfulness_score.py 忘却スコアテスト
"""
Forgetfulness Score Unit Tests

Theorema Egregium Cognitionis (aletheia.md §6.1) の実験的検証。
S(e) が構文的操作のみで計算可能であることを実証する。

テスト設計:
    - 境界値: S=0.0 (完全), S=1.0 (完全忘却)
    - 部分明示: 1座標, 3座標
    - AST ノード型: PartialDiff, Sequence, Fusion, Oscillation, ForLoop
    - E2E: 文字列入力から診断生成まで
"""

import pytest
import sys
from pathlib import Path

# パッケージパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hermeneus.src.forgetfulness_score import (
    COORDINATES,
    COORDINATE_TO_U_PATTERN,
    extract_coordinates,
    forgetfulness_score,
    diagnose,
    score_ccl,
    Diagnosis,
    ScoreResult,
)
from hermeneus.src.parser import CCLParser

# テスト用パーサー
_parser = CCLParser()


def _parse(ccl: str):
    """テスト用ヘルパー: CCL をパースして AST を返す"""
    return _parser.parse(ccl)


# =============================================================================
# §1: 定数の検証
# =============================================================================

class TestConstants:
    """6座標とマッピングの整合性"""

    # PURPOSE: 6座標が正確に定義されている
    def test_coordinate_count(self):
        """C = {Va, Fu, Pr, Sc, Vl, Te} — |C| = 6"""
        assert len(COORDINATES) == 6
        assert COORDINATES == frozenset({"Va", "Fu", "Pr", "Sc", "Vl", "Te"})

    # PURPOSE: 全座標に U パターンマッピングが存在する
    def test_all_coordinates_have_mapping(self):
        """全座標に U パターンと候補 Nomoi が定義されている"""
        for coord in COORDINATES:
            assert coord in COORDINATE_TO_U_PATTERN
            u_name, desc, nomoi = COORDINATE_TO_U_PATTERN[coord]
            assert u_name.startswith("U_")
            assert len(desc) > 0
            assert len(nomoi) > 0


# =============================================================================
# §2: extract_coordinates — AST 走査
# =============================================================================

class TestExtractCoordinates:
    """AST 走査による座標収集"""

    # PURPOSE: 座標修飾子なしの Workflow → 空集合
    def test_workflow_no_modifiers(self):
        """/noe+ — 座標なし → 空集合"""
        ast = _parse("/noe+")
        coords = extract_coordinates(ast)
        assert coords == set()

    # PURPOSE: 1座標明示 → その座標のみ
    def test_workflow_one_modifier(self):
        """/noe[Pr:C]+ — Pr のみ"""
        ast = _parse("/noe[Pr:C]+")
        coords = extract_coordinates(ast)
        assert coords == {"Pr"}

    # PURPOSE: 3座標明示
    def test_workflow_three_modifiers(self):
        """/noe[Va:E, Pr:C, Sc:Mi]+ — 3座標"""
        ast = _parse("/noe[Va:E, Pr:C, Sc:Mi]+")
        coords = extract_coordinates(ast)
        assert coords == {"Va", "Pr", "Sc"}

    # PURPOSE: 全6座標明示 → 完全集合
    def test_workflow_all_modifiers(self):
        """/noe[Va:E, Fu:Explore, Pr:C, Sc:Mi, Vl:+, Te:Past]+ — 全座標"""
        ast = _parse("/noe[Va:E, Fu:Explore, Pr:C, Sc:Mi, Vl:+, Te:Past]+")
        coords = extract_coordinates(ast)
        assert coords == set(COORDINATES)

    # PURPOSE: PartialDiff ∂ の座標を認識
    def test_partial_diff_coordinate(self):
        """∂Pr/noe — ∂ の座標 Pr を認識"""
        ast = _parse("∂Pr/noe")
        coords = extract_coordinates(ast)
        assert "Pr" in coords

    # PURPOSE: Sequence — 2ノードの union
    def test_sequence_union(self):
        """/noe[Va:E]+_/bou[Fu:Exploit]+ — union({Va}, {Fu})"""
        ast = _parse("/noe[Va:E]+_/bou[Fu:Exploit]+")
        coords = extract_coordinates(ast)
        assert coords == {"Va", "Fu"}

    # PURPOSE: Fusion — 左右の union
    def test_fusion_union(self):
        """/noe[Pr:C]*/ele[Vl:-] — union({Pr}, {Vl})"""
        ast = _parse("/noe[Pr:C]*/ele[Vl:-]")
        coords = extract_coordinates(ast)
        assert coords == {"Pr", "Vl"}

    # PURPOSE: Oscillation (ネスト)
    def test_oscillation_nested(self):
        """(/noe[Va:E]+~*/bou[Te:Future]+) — union({Va}, {Te})"""
        ast = _parse("(/noe[Va:E]+~*/bou[Te:Future]+)")
        coords = extract_coordinates(ast)
        assert coords == {"Va", "Te"}

    # PURPOSE: ForLoop — body を走査
    def test_forloop_body(self):
        """F:[×3]{/noe[Sc:Mi]+} — body 内の座標"""
        ast = _parse("F:[×3]{/noe[Sc:Mi]+}")
        coords = extract_coordinates(ast)
        assert "Sc" in coords

    # PURPOSE: IfCondition — then/else 両方を走査
    def test_if_both_branches(self):
        """I:[V[]>0.5]{/noe[Va:E]+} E:{/bou[Fu:Explore]+} — 両分岐の union"""
        ast = _parse("I:[V[]>0.5]{/noe[Va:E]+} E:{/bou[Fu:Explore]+}")
        coords = extract_coordinates(ast)
        assert coords == {"Va", "Fu"}

    # PURPOSE: TaggedBlock — body を走査
    def test_tagged_block(self):
        """V:{/noe[Pr:U]+} — 検証ブロック内"""
        ast = _parse("V:{/noe[Pr:U]+}")
        coords = extract_coordinates(ast)
        assert "Pr" in coords

    # PURPOSE: Morphism — source/target 両方
    def test_morphism(self):
        """/noe[Va:E]+>>/bou[Te:Future]+ — 射の両端"""
        ast = _parse("/noe[Va:E]+>>/bou[Te:Future]+")
        # >> は ConvergenceLoop になるため、Sequence で代替
        # 実際は >> の右辺が Condition として解釈されるため、
        # Morphism テストには << を使用
        ast2 = _parse("/noe[Va:E]+<</bou[Te:Future]+")
        coords = extract_coordinates(ast2)
        assert "Va" in coords
        assert "Te" in coords


# =============================================================================
# §3: forgetfulness_score — S(e) 計算
# =============================================================================

class TestForgetfulnessScore:
    """S(e) の計算"""

    # PURPOSE: S(e) = 0.0 — 全座標明示 (完全な型付け)
    def test_score_zero(self):
        """全座標明示 → S = 0.0"""
        ast = _parse("/noe[Va:E, Fu:Explore, Pr:C, Sc:Mi, Vl:+, Te:Past]+")
        s = forgetfulness_score(ast)
        assert s == pytest.approx(0.0)

    # PURPOSE: S(e) = 1.0 — 座標なし (完全忘却)
    def test_score_one(self):
        """座標なし → S = 1.0"""
        ast = _parse("/noe+")
        s = forgetfulness_score(ast)
        assert s == pytest.approx(1.0)

    # PURPOSE: S(e) = 5/6 — 1座標明示
    def test_score_one_sixth(self):
        """1座標明示 → S = 5/6 ≈ 0.833"""
        ast = _parse("/noe[Pr:C]+")
        s = forgetfulness_score(ast)
        assert s == pytest.approx(5.0 / 6.0)

    # PURPOSE: S(e) = 3/6 = 0.5 — 3座標明示
    def test_score_half(self):
        """3座標明示 → S = 0.5"""
        ast = _parse("/noe[Va:E, Pr:C, Sc:Mi]+")
        s = forgetfulness_score(ast)
        assert s == pytest.approx(0.5)

    # PURPOSE: Sequence の union で座標が増える → S が下がる
    def test_sequence_reduces_score(self):
        """2ノードの union で S が下がる"""
        ast_single = _parse("/noe[Va:E]+")
        ast_seq = _parse("/noe[Va:E]+_/bou[Fu:Exploit]+")
        s1 = forgetfulness_score(ast_single)
        s2 = forgetfulness_score(ast_seq)
        assert s2 < s1  # union で座標が増える → S 低下

    # PURPOSE: ∂ の座標が S を下げる
    def test_partial_diff_reduces_score(self):
        """∂Pr/noe は /noe より S が低い"""
        ast_pd = _parse("∂Pr/noe")
        ast_plain = _parse("/noe")
        s_pd = forgetfulness_score(ast_pd)
        s_plain = forgetfulness_score(ast_plain)
        assert s_pd < s_plain

    # PURPOSE: S(e) の値域は [0.0, 1.0]
    def test_score_range(self):
        """S(e) は常に [0.0, 1.0] の範囲"""
        test_cases = [
            "/noe+", "/bou-", "/ene",
            "/noe[Va:E]+", "/noe[Va:E, Pr:C]+",
            "/noe[Va:E, Fu:Explore, Pr:C, Sc:Mi, Vl:+, Te:Past]+",
            "/noe+_/bou+_/ene+",
        ]
        parser = CCLParser()
        for ccl in test_cases:
            ast = parser.parse(ccl)
            s = forgetfulness_score(ast)
            assert 0.0 <= s <= 1.0, f"S({ccl}) = {s} は範囲外"


# =============================================================================
# §4: diagnose — 欠落診断
# =============================================================================

class TestDiagnose:
    """欠落座標の診断"""

    # PURPOSE: 全座標明示 → 診断なし
    def test_no_diagnosis_when_complete(self):
        """全座標明示 → 空リスト"""
        ast = _parse("/noe[Va:E, Fu:Explore, Pr:C, Sc:Mi, Vl:+, Te:Past]+")
        diag = diagnose(ast)
        assert diag == []

    # PURPOSE: 完全忘却 → 6つの診断
    def test_six_diagnoses_when_empty(self):
        """座標なし → 6つの診断"""
        ast = _parse("/noe+")
        diag = diagnose(ast)
        assert len(diag) == 6

    # PURPOSE: 1座標明示 → 5つの診断
    def test_five_diagnoses_when_one_present(self):
        """1座標明示 → 5つの診断"""
        ast = _parse("/noe[Va:E]+")
        diag = diagnose(ast)
        assert len(diag) == 5
        # Va は欠落していない
        coords_in_diag = {d.coordinate for d in diag}
        assert "Va" not in coords_in_diag

    # PURPOSE: 診断に U パターンと Nomoi が含まれる
    def test_diagnosis_contains_u_pattern(self):
        """各診断に U パターン名と候補 Nomoi がある"""
        ast = _parse("/noe+")
        diag = diagnose(ast)
        for d in diag:
            assert d.u_pattern.startswith("U_")
            assert len(d.candidate_nomoi) > 0
            assert len(d.description) > 0

    # PURPOSE: Pr 欠落 → U_precision + N-02, N-03, N-10
    def test_specific_diagnosis_pr(self):
        """Pr 欠落 → U_precision"""
        ast = _parse("/noe[Va:E, Fu:Explore, Sc:Mi, Vl:+, Te:Past]+")  # Pr のみ欠落
        diag = diagnose(ast)
        assert len(diag) == 1
        assert diag[0].coordinate == "Pr"
        assert diag[0].u_pattern == "U_precision"
        assert "N-02" in diag[0].candidate_nomoi


# =============================================================================
# §5: score_ccl — E2E テスト
# =============================================================================

class TestScoreCCL:
    """E2E: 文字列 → ScoreResult"""

    # PURPOSE: 基本的な E2E
    def test_e2e_basic(self):
        """/noe+ → ScoreResult"""
        result = score_ccl("/noe+")
        assert isinstance(result, ScoreResult)
        assert result.score == pytest.approx(1.0)
        assert result.present_coordinates == frozenset()
        assert result.missing_coordinates == frozenset(COORDINATES)
        assert len(result.diagnoses) == 6
        assert result.expression == "/noe+"

    # PURPOSE: 全座標明示の E2E
    def test_e2e_complete(self):
        """全座標 → S = 0.0"""
        result = score_ccl("/noe[Va:E, Fu:Explore, Pr:C, Sc:Mi, Vl:+, Te:Past]+")
        assert result.score == pytest.approx(0.0)
        assert len(result.diagnoses) == 0

    # PURPOSE: Sequence の E2E
    def test_e2e_sequence(self):
        """/noe[Va:E]+_/bou[Fu:Exploit]+ — 2座標"""
        result = score_ccl("/noe[Va:E]+_/bou[Fu:Exploit]+")
        assert result.score == pytest.approx(4.0 / 6.0)
        assert result.present_coordinates == frozenset({"Va", "Fu"})

    # PURPOSE: 複雑な式の E2E
    def test_e2e_complex(self):
        """(/noe[Va:E, Pr:C]+~*/bou[Te:Future]+) — 3座標"""
        result = score_ccl("(/noe[Va:E, Pr:C]+~*/bou[Te:Future]+)")
        assert result.score == pytest.approx(3.0 / 6.0)
        assert result.present_coordinates == frozenset({"Va", "Pr", "Te"})

    # PURPOSE: パーサーは寛容 — 不正入力も AST として解釈される
    def test_e2e_tolerant_parser(self):
        """パーサーは不正入力でもエラーを投げず AST を返す → S(e)=1.0 (座標修飾なし)"""
        result = score_ccl("not_a_ccl_expression!!!")
        assert isinstance(result, ScoreResult)
        # 座標修飾子がないので完全忘却
        assert result.score == pytest.approx(1.0)


# =============================================================================
# §6: Theorema Egregium Cognitionis — 計算可能性の実証
# =============================================================================

class TestTheoremVerification:
    """Theorema Egregium Cognitionis の核心検証:
    S(e) は構文的性質の検査であり、全域計算可能関数である。
    """

    # PURPOSE: S(e) は意味論に触れない — 同じ座標構成なら WF ID に関係なく同スコア
    def test_score_independent_of_semantics(self):
        """同じ座標構成なら WF ID が異なっても同スコア (構文的性質)"""
        s_noe = score_ccl("/noe[Va:E, Pr:C]+").score
        s_bou = score_ccl("/bou[Va:E, Pr:C]+").score
        s_ene = score_ccl("/ene[Va:E, Pr:C]+").score
        assert s_noe == pytest.approx(s_bou)
        assert s_bou == pytest.approx(s_ene)

    # PURPOSE: S(e) は単調 — 座標を追加すると S は減少 (または不変)
    def test_score_monotone(self):
        """座標追加 → S は非増加 (単調性)"""
        s0 = score_ccl("/noe+").score  # 0座標
        s1 = score_ccl("/noe[Va:E]+").score  # 1座標
        s2 = score_ccl("/noe[Va:E, Pr:C]+").score  # 2座標
        s3 = score_ccl("/noe[Va:E, Pr:C, Sc:Mi]+").score  # 3座標
        assert s0 >= s1 >= s2 >= s3

    # PURPOSE: S(e) は等式成立 — S(e)=0 ⟺ 全座標明示
    def test_zero_iff_complete(self):
        """S(e)=0 ⟺ 全座標が明示されている"""
        result = score_ccl("/noe[Va:E, Fu:Explore, Pr:C, Sc:Mi, Vl:+, Te:Past]+")
        assert result.score == 0.0
        assert result.missing_coordinates == frozenset()

    # PURPOSE: S(e) は等式成立 — S(e)=1 ⟺ 座標修飾子が皆無
    def test_one_iff_empty(self):
        """S(e)=1 ⟺ 座標修飾子が皆無"""
        result = score_ccl("/noe+")
        assert result.score == 1.0
        assert result.present_coordinates == frozenset()

    # PURPOSE: 実際の WF マクロに対する S(e) の計算 (実用性検証)
    def test_real_world_ccl_expressions(self):
        """実際の CCL 式に対する S(e) — 全て有限時間で停止"""
        # aletheia.md §6.1 の核心主張: 「任意の well-formed CCL 式に対して有限時間で停止する」
        real_expressions = [
            "/noe+",                          # 単純
            "/bou+_/ene+",                    # シーケンス
            "/noe+~*/dia+",                   # 収束振動 (旧構文)
            "F:[×3]{/noe+}",                  # FOR ループ
            "(/ske+*/sag+)",                  # グループ融合
            "/noe[Va:E]+_/bou[Fu:Exploit]+",  # 部分座標
        ]
        for expr in real_expressions:
            result = score_ccl(expr)
            assert 0.0 <= result.score <= 1.0, f"S({expr}) = {result.score}"
            assert isinstance(result.diagnoses, tuple)


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
