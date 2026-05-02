# PROOF: [L2/テスト] <- mekhane/fep/tests/test_krisis_adjunction.py
"""
PROOF: [L2/テスト] このファイルは存在しなければならない

A0 → Krisis族の随伴 (K⊣E, P⊣D) が正しく動作する必要がある
   → krisis_adjunction_builder と KRISIS_ADJUNCTIONS の検証
   → test_krisis_adjunction.py が担う

Q.E.D.
"""

import pytest

from mekhane.fep.category import (
    Adjunction,
    KRISIS_ADJUNCTIONS,
    KRISIS_WF_TO_ADJUNCTION,
)
from mekhane.fep.krisis_adjunction_builder import (
    build_krisis_adjunction,
    describe_krisis_pair,
    get_adjunction_for_wf,
    get_adjoint_role,
    KRISIS_PAIR_METADATA,
)


# =============================================================================
# Registry Tests
# =============================================================================


# PURPOSE: KRISIS_ADJUNCTIONS レジストリの検証
class TestKrisisAdjunctionRegistry:
    """KRISIS_ADJUNCTIONS レジストリの検証"""

    # PURPOSE: Verify both pairs registered
    def test_both_pairs_registered(self):
        """K⊣E と P⊣D の両方が登録されている"""
        assert "K⊣E" in KRISIS_ADJUNCTIONS
        assert "P⊣D" in KRISIS_ADJUNCTIONS
        assert len(KRISIS_ADJUNCTIONS) == 2

    # PURPOSE: Verify K⊣E template fields
    def test_ke_template(self):
        """K⊣E のテンプレートが正しい"""
        ke = KRISIS_ADJUNCTIONS["K⊣E"]
        assert isinstance(ke, Adjunction)
        assert ke.left_name == "kat"
        assert ke.right_name == "epo"
        assert ke.source_category == "Evidence"
        assert ke.target_category == "Commitment"

    # PURPOSE: Verify P⊣D template fields
    def test_pd_template(self):
        """P⊣D のテンプレートが正しい"""
        pd = KRISIS_ADJUNCTIONS["P⊣D"]
        assert isinstance(pd, Adjunction)
        assert pd.left_name == "pai"
        assert pd.right_name == "dok"
        assert pd.source_category == "Confidence"
        assert pd.target_category == "ResourceAllocation"

    # PURPOSE: Verify WF to adjunction mapping
    def test_wf_mapping(self):
        """全4つの WF が正しいペアにマッピングされている"""
        assert KRISIS_WF_TO_ADJUNCTION["kat"] == "K⊣E"
        assert KRISIS_WF_TO_ADJUNCTION["epo"] == "K⊣E"
        assert KRISIS_WF_TO_ADJUNCTION["pai"] == "P⊣D"
        assert KRISIS_WF_TO_ADJUNCTION["dok"] == "P⊣D"
        assert len(KRISIS_WF_TO_ADJUNCTION) == 4

    # PURPOSE: Verify metadata exists for both pairs
    def test_metadata_complete(self):
        """メタデータが両ペアに対して完全に存在する"""
        for pair in ["K⊣E", "P⊣D"]:
            meta = KRISIS_PAIR_METADATA[pair]
            assert "name" in meta
            assert "axis" in meta
            assert "fep" in meta
            assert "algebra" in meta


# =============================================================================
# Builder Tests
# =============================================================================


# PURPOSE: build_krisis_adjunction の検証
class TestBuildKrisisAdjunction:
    """build_krisis_adjunction の検証"""

    # PURPOSE: Verify build with empty output
    def test_build_empty_output(self):
        """空の出力でもビルドできる（η=0, ε=0）"""
        adj = build_krisis_adjunction("K⊣E")
        assert isinstance(adj, Adjunction)
        assert adj.left_name == "kat"
        assert adj.right_name == "epo"
        assert adj.eta_quality == 0.0
        assert adj.epsilon_precision == 0.0
        assert adj.drift == 1.0  # 1 - ε

    # PURPOSE: Verify build with rich output
    def test_build_with_rich_output(self):
        """Source と根拠を含む出力で η > 0"""
        output = """
        Phase 0: 命題の定義
        [CHECKPOINT PHASE 0/4]
        Phase 1: 根拠の三角測量 (SOURCE: view_file)
        [CHECKPOINT PHASE 1/4]
        Phase 2: 反証の試み
        [CHECKPOINT PHASE 2/4]
        Phase 3: 撤回条件: APIレスポンスが500ms超
        [CHECKPOINT PHASE 3/4]
        📌 判定: [確信] 85%
        $goal = テスト
        """
        adj = build_krisis_adjunction("K⊣E", left_output=output)
        assert adj.eta_quality > 0.0
        assert adj.epsilon_precision > 0.0
        assert adj.drift < 1.0

    # PURPOSE: Verify unknown pair raises ValueError
    def test_unknown_pair_raises(self):
        """不明なペア名で ValueError"""
        with pytest.raises(ValueError, match="Unknown Krisis adjunction pair"):
            build_krisis_adjunction("X⊣Y")

    # PURPOSE: Verify drift formula
    def test_drift_formula(self):
        """drift = 1 - ε が正しく計算される"""
        adj = build_krisis_adjunction("P⊣D")
        assert adj.drift == pytest.approx(1.0 - adj.epsilon_precision)

# =============================================================================
# η Computation Tests (WF-Specific Rubrics)
# =============================================================================


# PURPOSE: compute_wf_eta の WF 固有ルーブリック検証
class TestComputeWfEta:
    """η 計算の WF 固有ルーブリック検証"""

    def test_kat_high_quality(self):
        """/kat: SOURCE多数 + 反証品質HIGHで高η"""
        from mekhane.fep.krisis_adjunction_builder import compute_wf_eta
        output = """
        [CHECKPOINT PHASE 0/4]
        根拠1: (SOURCE: view_file L42)
        根拠2: (SOURCE: test 実行)
        根拠3: (TAINT: 推論)
        [CHECKPOINT PHASE 1/4]
        反証試行の品質: [HIGH]
        [CHECKPOINT PHASE 2/4]
        [CHECKPOINT PHASE 3/4]
        """
        eta = compute_wf_eta("kat", output)
        assert eta > 0.7  # 0.3 (checkpoint) + 0.2 (source 2/3) + 0.4 (HIGH)

    def test_kat_low_quality(self):
        """/kat: マーカーなしで低η"""
        from mekhane.fep.krisis_adjunction_builder import compute_wf_eta
        eta = compute_wf_eta("kat", "これはテキストです")
        assert eta < 0.2

    def test_epo_with_procrastination(self):
        """/epo: 先延ばしスコアが低いほど高η"""
        from mekhane.fep.krisis_adjunction_builder import compute_wf_eta
        output = """
        [CHECKPOINT PHASE 0/4]
        [CHECKPOINT PHASE 1/4]
        トリガー条件: Xが判明したとき
        タイムボックス: 3日以内
        先延ばしスコア: 1/5
        [CHECKPOINT PHASE 2/4]
        [CHECKPOINT PHASE 3/4]
        """
        eta = compute_wf_eta("epo", output)
        assert eta > 0.7

    def test_unknown_wf(self):
        """未知WFでη=0"""
        from mekhane.fep.krisis_adjunction_builder import compute_wf_eta
        assert compute_wf_eta("unknown", "anything") == 0.0


# =============================================================================
# ε Computation Tests (WF-Specific Rubrics)
# =============================================================================


# PURPOSE: compute_wf_epsilon の WF 固有ルーブリック検証
class TestComputeWfEpsilon:
    """ε 計算の WF 固有ルーブリック検証"""

    def test_kat_confidence_extraction(self):
        """/kat: 確信度パーセンテージ抽出"""
        from mekhane.fep.krisis_adjunction_builder import compute_wf_epsilon
        output = "📌 判定: [確信] 85%"
        eps = compute_wf_epsilon("kat", output)
        assert eps == pytest.approx(0.85)

    def test_kat_label_fallback(self):
        """/kat: パーセンテージなしでN-10 ラベルフォールバック"""
        from mekhane.fep.krisis_adjunction_builder import compute_wf_epsilon
        assert compute_wf_epsilon("kat", "[推定]") == pytest.approx(0.65)

    def test_epo_hypothesis_distribution(self):
        """/epo: 仮説分布の最大値抽出"""
        from mekhane.fep.krisis_adjunction_builder import compute_wf_epsilon
        output = "H1=30%, H2=50%, H3=20%"
        eps = compute_wf_epsilon("epo", output)
        assert eps == pytest.approx(0.5)

    def test_dok_default_low(self):
        """/dok: デフォルトで低ε"""
        from mekhane.fep.krisis_adjunction_builder import compute_wf_epsilon
        eps = compute_wf_epsilon("dok", "打診行動を実行")
        assert eps == pytest.approx(0.2)


# =============================================================================
# Lookup Tests
# =============================================================================


# PURPOSE: get_adjunction_for_wf の検証
class TestWfLookup:
    """WF → Adjunction ルックアップの検証"""

    # PURPOSE: Verify Krisis WFs
    def test_krisis_wfs(self):
        """Krisis WF は正しいペアを返す"""
        assert get_adjunction_for_wf("kat") == "K⊣E"
        assert get_adjunction_for_wf("epo") == "K⊣E"
        assert get_adjunction_for_wf("pai") == "P⊣D"
        assert get_adjunction_for_wf("dok") == "P⊣D"

    # PURPOSE: Verify non-Krisis WFs
    def test_non_krisis_wf(self):
        """Krisis 以外の WF は None を返す"""
        assert get_adjunction_for_wf("noe") is None
        assert get_adjunction_for_wf("bou") is None

    # PURPOSE: Verify adjoint role
    def test_adjoint_role(self):
        """left/right の判定が正しい"""
        assert get_adjoint_role("kat") == "left"
        assert get_adjoint_role("epo") == "right"
        assert get_adjoint_role("pai") == "left"
        assert get_adjoint_role("dok") == "right"
        assert get_adjoint_role("noe") is None


# =============================================================================
# Display Tests
# =============================================================================


# PURPOSE: describe_krisis_pair の検証
class TestDescribe:
    """表示関数の検証"""

    # PURPOSE: Verify describe output
    def test_describe_ke(self):
        """K⊣E の記述にペア名が含まれる"""
        text = describe_krisis_pair("K⊣E")
        assert "Katalēpsis" in text
        assert "Epochē" in text
        assert "kat" in text
        assert "epo" in text

    # PURPOSE: Verify describe with custom adjunction
    def test_describe_with_adj(self):
        """カスタム Adjunction を渡すと η/ε が反映される"""
        adj = Adjunction(
            left_name="kat", right_name="epo",
            source_category="Evidence", target_category="Commitment",
            eta_quality=0.9, epsilon_precision=0.8,
        )
        text = describe_krisis_pair("K⊣E", adj)
        assert "0.90" in text  # η
        assert "0.80" in text  # ε
        assert "faithful" in text.lower()

    # PURPOSE: Verify unknown pair
    def test_describe_unknown(self):
        """不明なペアでもエラーなし"""
        text = describe_krisis_pair("X⊣Y")
        assert "Unknown" in text


# =============================================================================
# Integration Points Tests (New Features)
# =============================================================================

from mekhane.fep.krisis_adjunction_builder import (
    detect_drift,
    compute_adjunction_from_execution,
    format_adjunction_section,
    propose_dual_wf,
    check_krisis_adjunction_health,
)


class TestDriftDetection:
    """detect_drift の検証"""
    def test_drift_detected(self):
        """/kat 実行時に [再構成] コンテキストがあれば Drift 判定"""
        context = "これは不明な点が多い未決定の探索です。"
        result = detect_drift("kat", context)
        assert result is not None
        assert "/epo" in result["warning"]

        context = "これは確実に向かう決定事項です。 確信度: 90%"
        result = detect_drift("kat", context)
        assert result is None

    def test_non_krisis_wf(self):
        result = detect_drift("noe", "context")
        assert result is None


class TestComputeAdjunctionFromExecution:
    """compute_adjunction_from_execution の検証"""
    def test_compute_metrics(self):
        """実行後に出力からメトリクスが計算される"""
        output = "[CHECKPOINT PHASE 0/4]\n$goal = test"
        metrics = compute_adjunction_from_execution("kat", output)
        assert metrics is not None
        assert "adjunction" in metrics
        assert metrics["pair_name"] == "K⊣E"
        assert "section" in metrics


class TestFormatAdjunctionSection:
    """format_adjunction_section の検証"""
    def test_format_section(self):
        """文字列がフォーマットされる"""
        context = "[CHECKPOINT PHASE 0/4]\n$goal = test"
        from mekhane.fep.category import Adjunction
        adj = Adjunction("kat", "epo", "Evidence", "Commitment", eta_quality=0.5, epsilon_precision=0.4)
        section = format_adjunction_section("K⊣E", adj)
        assert "Katalēpsis ⊣ Epochē" in section
        assert "η" in section


class TestProposeDualWf:
    """propose_dual_wf の検証"""
    def test_proposal_generation(self):
        """双対または移行の提案が生成される"""
        proposal = propose_dual_wf("kat")
        assert proposal is not None
        assert ("Epochē" in proposal) or ("P⊣D" in proposal)

    def test_non_krisis_proposal(self):
        """Krisis 非対応なら None"""
        assert propose_dual_wf("noe") is None


class TestHealthCheck:
    """check_krisis_adjunction_health の検証"""
    def test_health_check(self):
        """ヘルス情報リストを返す"""
        health_data = check_krisis_adjunction_health()
        assert isinstance(health_data, list)
        assert len(health_data) == 2  # K⊣E and P⊣D
        assert health_data[0][0] == "Adjunction K⊣E"
        assert health_data[1][0] == "Adjunction P⊣D"
