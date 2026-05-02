# PROOF: [L2/テスト] <- mekhane/fep/tests/test_basis.py
# PURPOSE: Basis (Γ⊣Q) と 12 数学的演算子のテスト
"""Tests for mekhane.fep.basis — Helmholtz decomposition and 12 operators."""

import pytest
from mekhane.fep.basis import (
    Basis,
    BASIS,
    HelmholtzComponent,
    HelmholtzOperator,
    CoordinateSpec,
    COORDINATE_SPECS,
    HELMHOLTZ_OPERATORS,
    MODIFYING_COORDINATES,
    get_operator,
    gradient_operators,
    solenoidal_operators,
    get_d_value,
    coordinates_by_d,
    format_operator_table,
)


# ---------------------------------------------------------------------------
# Basis
# ---------------------------------------------------------------------------

# PURPOSE: Basis の基本構造テスト
class TestBasis:
    """Basis (βάσις) の基本構造テスト"""

    def test_basis_singleton(self):
        """BASIS は d=0, Γ⊣Q を持つ。"""
        assert BASIS.d_value == 0
        assert BASIS.gradient == "Γ"
        assert BASIS.solenoidal == "Q"

    def test_adjunction_pair(self):
        """随伴対 (Γ, Q) を返す。"""
        assert BASIS.adjunction_pair == ("Γ", "Q")

    def test_basis_is_frozen(self):
        """Basis は immutable。"""
        with pytest.raises(AttributeError):
            BASIS.d_value = 1  # type: ignore


# ---------------------------------------------------------------------------
# Coordinates
# ---------------------------------------------------------------------------

# PURPOSE: 座標系テスト
class TestCoordinates:
    """座標系 (v4.2 d 値)"""

    def test_seven_coordinates(self):
        """7 座標が定義されている。"""
        assert len(COORDINATE_SPECS) == 7

    def test_six_modifying_coordinates(self):
        """修飾座標は Flow を除いた 6 つ。"""
        assert len(MODIFYING_COORDINATES) == 6
        assert "Flow" not in MODIFYING_COORDINATES

    def test_d_values_v42(self):
        """d 値が axiom_hierarchy.md v4.2 と一致。"""
        assert get_d_value("Basis") == 0
        assert get_d_value("Flow") == 1
        assert get_d_value("Value") == 2
        assert get_d_value("Function") == 2
        assert get_d_value("Precision") == 2
        assert get_d_value("Scale") == 3
        assert get_d_value("Valence") == 3
        assert get_d_value("Temporality") == 3

    def test_d_value_distribution(self):
        """d 値の分布: 1 + 3 + 3 = 7。"""
        groups = coordinates_by_d()
        assert groups[0] == ["Basis"]       # 体系核外
        assert len(groups[1]) == 1          # Flow のみ
        assert len(groups[2]) == 3          # Value, Function, Precision
        assert len(groups[3]) == 3          # Scale, Valence, Temporality

    def test_unknown_coordinate_raises(self):
        """未知の座標名で KeyError。"""
        with pytest.raises(KeyError):
            get_d_value("NonExistent")

    def test_coordinate_has_opposition(self):
        """各座標は対立極を持つ。"""
        for name, spec in COORDINATE_SPECS.items():
            assert len(spec.opposition) == 2, f"{name} has no opposition pair"


# ---------------------------------------------------------------------------
# 12 Operators
# ---------------------------------------------------------------------------

# PURPOSE: 12 演算子テスト
class TestHelmholtzOperators:
    """12 数学的演算子 (Basis × 6 修飾座標)"""

    def test_twelve_operators(self):
        """演算子は正確に 12 個。"""
        assert len(HELMHOLTZ_OPERATORS) == 12

    def test_six_gradient_six_solenoidal(self):
        """Γ 列 6 + Q 列 6 = 12。"""
        gammas = gradient_operators()
        qs = solenoidal_operators()
        assert len(gammas) == 6
        assert len(qs) == 6

    def test_all_coordinates_covered(self):
        """6 修飾座標すべてが Γ/Q 両方でカバーされている。"""
        for coord in MODIFYING_COORDINATES:
            g_op = get_operator(coord, HelmholtzComponent.GRADIENT)
            q_op = get_operator(coord, HelmholtzComponent.SOLENOIDAL)
            assert g_op is not None, f"Missing Γ_{coord}"
            assert q_op is not None, f"Missing Q_{coord}"

    def test_operator_name_format(self):
        """演算子名は 'Γ_座標' or 'Q_座標' 形式。"""
        for op in HELMHOLTZ_OPERATORS:
            assert op.name.startswith("Γ_") or op.name.startswith("Q_")

    def test_get_operator_by_string(self):
        """文字列で成分を指定して検索できる。"""
        op = get_operator("Value", "gradient")
        assert op is not None
        assert op.coordinate == "Value"
        assert op.is_gradient

        op2 = get_operator("Function", "Q")
        assert op2 is not None
        assert op2.is_solenoidal

    def test_get_operator_returns_none_for_invalid(self):
        """存在しない組み合わせで None。"""
        assert get_operator("Flow", HelmholtzComponent.GRADIENT) is None
        assert get_operator("NonExistent", "gradient") is None

    def test_operator_has_descriptions(self):
        """各演算子は英語・日本語の説明を持つ。"""
        for op in HELMHOLTZ_OPERATORS:
            assert len(op.description) > 0
            assert len(op.description_ja) > 0


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

# PURPOSE: テーブル出力テスト
class TestFormatting:
    """Markdown テーブル出力"""

    def test_format_operator_table(self):
        """Markdown テーブルが 12+2 行 (ヘッダ含む)。"""
        table = format_operator_table()
        lines = table.strip().split("\n")
        assert len(lines) == 14  # header + separator + 12 rows

    def test_table_contains_all_operators(self):
        """テーブルに全演算子名が含まれる。"""
        table = format_operator_table()
        for op in HELMHOLTZ_OPERATORS:
            assert op.name in table
