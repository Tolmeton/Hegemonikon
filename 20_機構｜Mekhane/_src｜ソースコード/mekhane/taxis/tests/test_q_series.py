#!/usr/bin/env python3
# PROOF: [L2/テスト] <- mekhane/taxis/tests/test_q_series.py
# PURPOSE: Q-series (循環規則) モジュールのテスト
"""Tests for mekhane.taxis.q_series — K₆ 反対称テンソル場。"""

import numpy as np
import pytest

from mekhane.taxis.q_series import (
    ANTI_TIMIDITY_MAP,
    COORD_INDEX,
    COORDINATES,
    CirculationDiagnosis,
    QEdge,
    QGroup,
    QMatrix,
    _compute_pfaffian_6x6,
    _get_d,
)


# ---------------------------------------------------------------------------
# QEdge
# ---------------------------------------------------------------------------

# PURPOSE: QEdge の基本構造テスト
class TestQEdge:
    """QEdge — K₆ の1辺"""

    def test_frozen(self):
        """QEdge は immutable。"""
        edge = QEdge(
            coord_i="Value", coord_j="Precision",
            value=0.8, group=QGroup.GROUP_I, edge_id=1,
        )
        with pytest.raises(AttributeError):
            edge.value = 0.5  # type: ignore

    def test_key_format(self):
        """辺キーは 'XXX→YYY' 形式。"""
        edge = QEdge(
            coord_i="Value", coord_j="Precision",
            value=0.8, group=QGroup.GROUP_I, edge_id=1,
        )
        assert edge.key == "Val→Pre"

    def test_magnitude(self):
        """magnitude は絶対値。"""
        edge = QEdge(
            coord_i="Function", coord_j="Valence",
            value=-0.5, group=QGroup.GROUP_II, edge_id=8,
        )
        assert edge.magnitude == 0.5

    def test_group_classification(self):
        """3群分類が正しい。"""
        assert QGroup.GROUP_I.value == "d2×d2"
        assert QGroup.GROUP_II.value == "d2×d3"
        assert QGroup.GROUP_III.value == "d3×d3"


# ---------------------------------------------------------------------------
# QMatrix — 基本
# ---------------------------------------------------------------------------

# PURPOSE: QMatrix の構築と反対称性テスト
class TestQMatrix:
    """QMatrix — 6×6 反対称行列"""

    def test_from_theory_has_15_edges(self):
        """理論的構成は正確に 15辺。"""
        qm = QMatrix.from_theory()
        assert len(qm.edges) == 15

    def test_from_theory_antisymmetric(self):
        """理論的構成の行列は反対称。"""
        qm = QMatrix.from_theory()
        assert qm.is_antisymmetric

    def test_from_theory_diagonal_is_zero(self):
        """対角は全てゼロ。"""
        qm = QMatrix.from_theory()
        M = qm.matrix
        for i in range(6):
            assert M[i, i] == 0.0

    def test_from_theory_symmetry(self):
        """Q_{ij} = -Q_{ji} が全辺で成立。"""
        qm = QMatrix.from_theory()
        M = qm.matrix
        for i in range(6):
            for j in range(6):
                assert np.isclose(M[i, j], -M[j, i])

    def test_from_theory_group_I_has_3_edges(self):
        """群 I (d2×d2) は 3辺。"""
        qm = QMatrix.from_theory()
        g1 = [e for e in qm.edges if e.group == QGroup.GROUP_I]
        assert len(g1) == 3

    def test_from_theory_group_II_has_9_edges(self):
        """群 II (d2×d3) は 9辺。"""
        qm = QMatrix.from_theory()
        g2 = [e for e in qm.edges if e.group == QGroup.GROUP_II]
        assert len(g2) == 9

    def test_from_theory_group_III_has_3_edges(self):
        """群 III (d3×d3) は 3辺。"""
        qm = QMatrix.from_theory()
        g3 = [e for e in qm.edges if e.group == QGroup.GROUP_III]
        assert len(g3) == 3

    def test_from_theory_edge_ids_1_to_15(self):
        """辺IDは Q1〜Q15。"""
        qm = QMatrix.from_theory()
        ids = sorted(e.edge_id for e in qm.edges)
        assert ids == list(range(1, 16))

    def test_matrix_shape(self):
        """行列は 6×6。"""
        qm = QMatrix.from_theory()
        assert qm.matrix.shape == (6, 6)


# ---------------------------------------------------------------------------
# QMatrix — from_manual
# ---------------------------------------------------------------------------

# PURPOSE: 手動構成のテスト
class TestQMatrixManual:
    """QMatrix.from_manual — 手動設定"""

    def test_manual_construction(self):
        """手動で辺を指定して構築できる。"""
        qm = QMatrix.from_manual({
            "Val→Pre": 1.0,
            "Val→Fun": -0.5,
            "Fun→Pre": 0.3,
        })
        assert len(qm.edges) == 3
        assert qm.is_antisymmetric

    def test_manual_value_preserved(self):
        """手動設定の値が保持される。"""
        qm = QMatrix.from_manual({"Val→Pre": 0.42})
        edge = qm.get_edge("Val→Pre")
        assert edge is not None
        assert edge.value == 0.42

    def test_manual_invalid_key_raises(self):
        """不正な辺キーで ValueError。"""
        with pytest.raises(ValueError):
            QMatrix.from_manual({"invalid": 0.5})

    def test_manual_unknown_coord_raises(self):
        """未知の座標略称で ValueError。"""
        with pytest.raises(ValueError):
            QMatrix.from_manual({"Xxx→Yyy": 0.5})

    def test_manual_group_auto_classification(self):
        """群分類が d 値から自動判定される。"""
        qm = QMatrix.from_manual({
            "Val→Fun": 0.5,  # d2×d2 → GROUP_I
            "Val→Sca": 0.3,  # d2×d3 → GROUP_II
            "Sca→Vle": 0.2,  # d3×d3 → GROUP_III
        })
        groups = {e.key: e.group for e in qm.edges}
        assert groups["Val→Fun"] == QGroup.GROUP_I
        assert groups["Val→Sca"] == QGroup.GROUP_II
        assert groups["Sca→Vle"] == QGroup.GROUP_III


# ---------------------------------------------------------------------------
# QMatrix — from_counts
# ---------------------------------------------------------------------------

# PURPOSE: セッションデータ推定のテスト
class TestQMatrixCounts:
    """QMatrix.from_counts — 遷移頻度からの推定"""

    def test_symmetric_counts_yield_zero_q(self):
        """対称的な遷移は Q ≈ 0 を生む。"""
        counts = {
            "Value": {"Precision": 10},
            "Precision": {"Value": 10},
        }
        qm = QMatrix.from_counts(counts)
        # Val→Pre の Q は ~0 (対称的な遷移)
        edge = qm.get_edge("Val→Pre")
        assert edge is not None
        assert abs(edge.value) < 0.01

    def test_asymmetric_counts_yield_nonzero_q(self):
        """非対称的な遷移は 非ゼロ Q を生む。"""
        # 複数の遷移先を含むデータ (行正規化後も非対称性が残る)
        counts = {
            "Value": {"Precision": 20, "Function": 5},
            "Precision": {"Value": 5, "Function": 10},
        }
        qm = QMatrix.from_counts(counts)
        edge = qm.get_edge("Val→Pre")
        assert edge is not None
        assert edge.value > 0  # Val→Pre が優勢

    def test_from_counts_antisymmetric(self):
        """推定結果は反対称。"""
        counts = {
            "Value": {"Precision": 15, "Function": 8},
            "Function": {"Value": 3, "Precision": 12},
            "Precision": {"Value": 5, "Function": 2},
        }
        qm = QMatrix.from_counts(counts)
        assert qm.is_antisymmetric

    def test_from_counts_has_15_edges(self):
        """推定結果は常に 15辺。"""
        counts = {"Value": {"Precision": 10}}
        qm = QMatrix.from_counts(counts)
        assert len(qm.edges) == 15


# ---------------------------------------------------------------------------
# CirculationDiagnosis
# ---------------------------------------------------------------------------

# PURPOSE: 循環診断テスト
class TestCirculationDiagnosis:
    """CirculationDiagnosis — 固着パターン検知"""

    def test_diagnose_positive_direction(self):
        """Q > 0 は i→j 方向。"""
        qm = QMatrix.from_theory()
        diag = qm.diagnose("Val→Pre")
        assert diag is not None
        assert "Value" in diag.dominant_direction
        assert "Precision" in diag.dominant_direction

    def test_diagnose_negative_direction(self):
        """Q < 0 は j→i 方向。"""
        qm = QMatrix.from_manual({"Val→Pre": -0.8})
        diag = qm.diagnose("Val→Pre")
        assert diag is not None
        assert "Precision" in diag.dominant_direction
        assert "Value" in diag.dominant_direction

    def test_diagnose_balanced(self):
        """|Q| < 0.05 は balanced。"""
        qm = QMatrix.from_manual({"Val→Pre": 0.01})
        diag = qm.diagnose("Val→Pre")
        assert diag is not None
        assert diag.dominant_direction == "balanced"

    def test_diagnose_stagnation_risk(self):
        """|Q| > threshold で固着リスク検出。"""
        qm = QMatrix.from_theory()
        diag = qm.diagnose("Val→Pre", threshold=0.5)  # Q1 = 0.8 > 0.5
        assert diag is not None
        assert diag.stagnation_risk is True

    def test_diagnose_no_stagnation(self):
        """|Q| < threshold で固着リスクなし。"""
        qm = QMatrix.from_theory()
        diag = qm.diagnose("Sca→Vle", threshold=0.5)  # Q13 = 0.3 < 0.5
        assert diag is not None
        assert diag.stagnation_risk is False

    def test_diagnose_all_returns_15(self):
        """diagnose_all は 15件の診断。"""
        qm = QMatrix.from_theory()
        results = qm.diagnose_all()
        assert len(results) == 15

    def test_stagnation_risks(self):
        """stagnation_risks は threshold 超えの辺。"""
        qm = QMatrix.from_theory()
        risks = qm.stagnation_risks(threshold=0.7)
        # Q1=0.8, Q3=0.7 → 少なくとも1つ
        assert len(risks) >= 1
        assert all(e.magnitude > 0.7 for e in risks)

    def test_diagnose_nonexistent_edge(self):
        """存在しない辺キーで None。"""
        qm = QMatrix.from_theory()
        assert qm.diagnose("Xxx→Yyy") is None


# ---------------------------------------------------------------------------
# Anti-Timidity
# ---------------------------------------------------------------------------

# PURPOSE: Anti-Timidity 対応テスト
class TestAntiTimidity:
    """Anti-Timidity T-1〜T-6 の Q辺対応"""

    def test_anti_timidity_map_defined(self):
        """ANTI_TIMIDITY_MAP に T-1, T-3, T-4, T-6 が定義。"""
        assert "T-1" in ANTI_TIMIDITY_MAP
        assert "T-3" in ANTI_TIMIDITY_MAP
        assert "T-4" in ANTI_TIMIDITY_MAP
        assert "T-6" in ANTI_TIMIDITY_MAP

    def test_t1_maps_to_q15(self):
        """T-1 → Q15 (Valence → Temporality)。"""
        assert ANTI_TIMIDITY_MAP["T-1"]["edge_id"] == "Q15"

    def test_t6_maps_to_q13(self):
        """T-6 → Q13 (Scale → Valence)。"""
        assert ANTI_TIMIDITY_MAP["T-6"]["edge_id"] == "Q13"

    def test_anti_timidity_diagnosis(self):
        """anti_timidity_map() が Anti-Timidity 対応辺の診断を返す。"""
        qm = QMatrix.from_theory()
        at_map = qm.anti_timidity_map()
        assert len(at_map) >= 4
        for t_key, diag in at_map.items():
            assert isinstance(diag, CirculationDiagnosis)
            assert diag.anti_timidity_ref == t_key


# ---------------------------------------------------------------------------
# Schur 分解
# ---------------------------------------------------------------------------

# PURPOSE: Schur 分解テスト
class TestSchurDecomposition:
    """Schur 分解: 3回転面"""

    def test_schur_returns_3_frequencies(self):
        """Schur 分解で 3回転周波数が得られる。"""
        qm = QMatrix.from_theory()
        result = qm.schur_decomposition()
        assert len(result["frequencies"]) == 3

    def test_schur_frequencies_nonnegative(self):
        """回転周波数は非負。"""
        qm = QMatrix.from_theory()
        result = qm.schur_decomposition()
        for freq in result["frequencies"]:
            assert freq >= 0

    def test_schur_pfaffian_nonzero(self):
        """理論的 Q₀ は非退化 (Pfaffian ≠ 0)。"""
        qm = QMatrix.from_theory()
        result = qm.schur_decomposition()
        assert result["is_nondegenerate"]

    def test_pfaffian_squared_equals_det(self):
        """Pf² = det(Q)。"""
        qm = QMatrix.from_theory()
        Q = qm.matrix
        pf = _compute_pfaffian_6x6(Q)
        det_Q = np.linalg.det(Q)
        assert np.isclose(pf ** 2, abs(det_Q), atol=1e-8)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

# PURPOSE: ユーティリティ関数のテスト
class TestUtilities:
    """内部ユーティリティ"""

    def test_coordinates_count(self):
        """座標は6つ。"""
        assert len(COORDINATES) == 6

    def test_coord_index_bijection(self):
        """COORD_INDEX はインデックスの全単射。"""
        assert len(COORD_INDEX) == 6
        assert set(COORD_INDEX.values()) == {0, 1, 2, 3, 4, 5}

    def test_get_d_values(self):
        """_get_d が正しい d 値を返す。"""
        assert _get_d("Value") == 2
        assert _get_d("Function") == 2
        assert _get_d("Precision") == 2
        assert _get_d("Scale") == 3
        assert _get_d("Valence") == 3
        assert _get_d("Temporality") == 3

    def test_get_edge_by_id(self):
        """get_edge_by_id で Q1〜Q15 を取得。"""
        qm = QMatrix.from_theory()
        for i in range(1, 16):
            edge = qm.get_edge_by_id(i)
            assert edge is not None
            assert edge.edge_id == i

    def test_format_table(self):
        """Markdown テーブルが 15+2 行 (ヘッダ含む)。"""
        qm = QMatrix.from_theory()
        table = qm.format_table()
        lines = table.strip().split("\n")
        assert len(lines) == 17  # header + separator + 15 rows
