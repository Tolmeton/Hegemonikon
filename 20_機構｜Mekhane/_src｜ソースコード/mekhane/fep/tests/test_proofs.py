# PROOF: [L2/テスト] <- mekhane/fep/tests/test_proofs.py
"""
PROOF: [L2/テスト] このファイルは存在しなければならない

proof ファイル (flow, d1, scale, temporality, valence, independence) の
計算的検証テスト。各 proof の run_*_proof() が正しい結果を返すことを確認する。

PURPOSE: /fit 未踏踏破 — proof ファイルの消去テストを実現し、
         🟡吸収 → 🟢馴化 への橋渡しをする。
"""

import pytest


# =============================================================================
# §1. Flow Proof (Step ①)
# =============================================================================


class TestFlowProof:
    """flow_proof.py の計算的検証テスト。"""

    def test_flow_derived(self):
        from mekhane.fep.flow_proof import run_flow_uniqueness_proof

        result = run_flow_uniqueness_proof()
        assert result["flow_derived"] is True

    def test_conditional_independence(self):
        from mekhane.fep.flow_proof import run_flow_uniqueness_proof

        result = run_flow_uniqueness_proof()
        assert result["conditional_independence"] is True

    def test_galois_notation(self):
        from mekhane.fep.flow_proof import run_flow_uniqueness_proof

        result = run_flow_uniqueness_proof()
        assert "I ⊣ A" in result["galois_notation"]


# =============================================================================
# §2. d1 Proof (Step ②)
# =============================================================================


class TestD1Proof:
    """d1_proof.py の計算的検証テスト。"""

    def test_efe_unique(self):
        from mekhane.fep.d1_proof import run_d1_uniqueness_proof

        result = run_d1_uniqueness_proof()
        assert result["efe_unique"] is True

    def test_fully_independent(self):
        from mekhane.fep.d1_proof import run_d1_uniqueness_proof

        result = run_d1_uniqueness_proof()
        assert result["fully_independent"] is True


# =============================================================================
# §3. Scale Proof (Step ③)
# =============================================================================


class TestScaleProof:
    """scale_proof.py の計算的検証テスト。"""

    def test_scale_derived(self):
        from mekhane.fep.scale_proof import run_scale_uniqueness_proof

        result = run_scale_uniqueness_proof()
        assert result["scale_derived"] is True

    def test_galois_notation(self):
        from mekhane.fep.scale_proof import run_scale_uniqueness_proof

        result = run_scale_uniqueness_proof()
        assert "Mi ⊣ Ma" in result["galois_notation"]


# =============================================================================
# §4. Temporality Proof (Step ④) — ARGUED level
# =============================================================================


class TestTemporalityProof:
    """temporality_proof.py の構造的検証テスト。

    NOTE: /ele+ で指摘された通り、verify 関数は True リテラル。
    テストは「構造が壊れていないこと」を検証する。
    ARGUED → PROVED への引き上げは verify 関数に実計算を導入する必要がある。
    """

    def test_temporality_derived(self):
        from mekhane.fep.temporality_proof import run_temporality_uniqueness_proof

        result = run_temporality_uniqueness_proof()
        assert result["temporality_derived"] is True

    def test_galois_notation(self):
        from mekhane.fep.temporality_proof import run_temporality_uniqueness_proof

        result = run_temporality_uniqueness_proof()
        assert "Past ⊣ Future" in result["galois_notation"]

    def test_no_circular_reasoning(self):
        from mekhane.fep.temporality_proof import run_temporality_uniqueness_proof

        result = run_temporality_uniqueness_proof()
        assert result["no_circular_reasoning"] is True

    def test_asymmetry_holds(self):
        from mekhane.fep.temporality_proof import run_temporality_uniqueness_proof

        result = run_temporality_uniqueness_proof()
        assert result["asymmetry_holds"] is True

    def test_scale_temporality_independent(self):
        from mekhane.fep.temporality_proof import run_temporality_uniqueness_proof

        result = run_temporality_uniqueness_proof()
        assert result["T_H_independent"] is True


# =============================================================================
# §5. Valence Proof (Step ⑤) — ARGUED level
# =============================================================================


class TestValenceProof:
    """valence_proof.py の構造的検証テスト。

    NOTE: /ele+ で指摘された通り、verify 関数は True リテラル。
    テストは「構造が壊れていないこと」を検証する。
    """

    def test_valence_derived(self):
        from mekhane.fep.valence_proof import run_valence_uniqueness_proof

        result = run_valence_uniqueness_proof()
        assert result["valence_derived"] is True

    def test_galois_notation(self):
        from mekhane.fep.valence_proof import run_valence_uniqueness_proof

        result = run_valence_uniqueness_proof()
        assert "+ ⊣ −" in result["galois_notation"]

    def test_sgn_exists(self):
        from mekhane.fep.valence_proof import run_valence_uniqueness_proof

        result = run_valence_uniqueness_proof()
        assert result["sgn_exists"] is True

    def test_interoception_not_required(self):
        from mekhane.fep.valence_proof import run_valence_uniqueness_proof

        result = run_valence_uniqueness_proof()
        assert result["interoception_not_required"] is True

    def test_precision_independent(self):
        from mekhane.fep.valence_proof import run_valence_uniqueness_proof

        result = run_valence_uniqueness_proof()
        assert result["precision_independent"] is True

    def test_zero_handling(self):
        from mekhane.fep.valence_proof import run_valence_uniqueness_proof

        result = run_valence_uniqueness_proof()
        assert result["zero_handling_consistent"] is True


# =============================================================================
# §6. Independence Proof (B'-3) — Condition-Verification Version
# =============================================================================


class TestIndependenceProof:
    """independence_proof.py の条件検証テスト (/ele+ 書き直し版)。

    旧版は同語反復 (定義に結論を埋め込み)。
    新版は C1-C3 の前提条件を検証してから Smithe 定理を適用する。
    """

    def test_c1_disjoint(self):
        from mekhane.fep.independence_proof import run_independence_proof

        result = run_independence_proof()
        assert result["c1_disjoint"] is True

    def test_c1_no_conflicts(self):
        from mekhane.fep.independence_proof import run_independence_proof

        result = run_independence_proof()
        assert result["c1_conflicts"] == []

    def test_c2_parallel_justified(self):
        from mekhane.fep.independence_proof import run_independence_proof

        result = run_independence_proof()
        assert result["c2_parallel_justified"] is True

    def test_c2_valence_temporality_noted(self):
        """Valence→Temporality の仮定依存が open issue として記録されている。"""
        from mekhane.fep.independence_proof import run_independence_proof

        result = run_independence_proof()
        assert result["c2_valence_temporality_noted"] is True

    def test_c3_kl_verified(self):
        from mekhane.fep.independence_proof import run_independence_proof

        result = run_independence_proof()
        assert result["c3_kl_verified"] is True

    def test_all_preconditions_met(self):
        from mekhane.fep.independence_proof import run_independence_proof

        result = run_independence_proof()
        assert result["all_preconditions_met"] is True

    def test_compositionality_applies(self):
        from mekhane.fep.independence_proof import run_independence_proof

        result = run_independence_proof()
        assert result["compositionality_applies"] is True

    def test_open_issue_documented(self):
        """open issue が空文字列ではないことを確認。"""
        from mekhane.fep.independence_proof import run_independence_proof

        result = run_independence_proof()
        assert len(result["open_issue"]) > 0

    def test_coordinates_count(self):
        from mekhane.fep.independence_proof import run_independence_proof

        result = run_independence_proof()
        assert result["coordinates_count"] == 7
