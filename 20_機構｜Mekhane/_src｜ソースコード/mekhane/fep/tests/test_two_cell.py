#!/usr/bin/env python3
# PROOF: mekhane/fep/tests/test_two_cell.py
# PURPOSE: fep モジュールの two_cell に対するテスト
"""Tests for two_cell.py — L3+L4 Weak 2-category structure (v5.4)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from mekhane.fep.two_cell import (
    HigherCell,
    Associator,
    PoiesisSpace,
    get_poiesis_space,
    get_all_spaces,
    get_tribe_spaces,
    count_cells,
    verify_pentagon,
    verify_triangle_identity,
    verify_composition_laws,
    verify_coherence,
    build_associator,
    describe_space,
    describe_summary,
    # Legacy aliases
    TwoCell,
    get_derivative_space,
    get_series_spaces,
    count_two_cells,
    verify_all,
)

import unittest
import warnings


# PURPOSE: Test suite validating HigherCell correctness
class TestHigherCell(unittest.TestCase):
    """Test HigherCell data structure."""

    def test_label(self):
        cell = HigherCell(source="V01", target="V04", level=1)
        assert cell.label == "V01 → V04"

    def test_identity_label(self):
        cell = HigherCell(source="V01", target="V01", level=1, is_identity=True)
        assert cell.label == "id(V01)"

    def test_custom_label(self):
        cell = HigherCell(source="V01", target="V04", level=1, label_text="/noe >> /ene")
        assert cell.label == "/noe >> /ene"

    def test_compose_valid(self):
        a = HigherCell(source="V01", target="V04", level=1)
        b = HigherCell(source="V04", target="V18", level=1)
        result = a.compose(b)
        assert result is not None
        assert result.source == "V01"
        assert result.target == "V18"

    def test_compose_identity_left(self):
        id_cell = HigherCell(source="V01", target="V01", level=1, is_identity=True)
        cell = HigherCell(source="V01", target="V04", level=1)
        result = id_cell.compose(cell)
        assert result is not None
        assert result.source == "V01"
        assert result.target == "V04"

    def test_compose_identity_right(self):
        cell = HigherCell(source="V01", target="V04", level=1)
        id_cell = HigherCell(source="V04", target="V04", level=1, is_identity=True)
        result = cell.compose(id_cell)
        assert result is not None
        assert result.source == "V01"
        assert result.target == "V04"

    def test_compose_incompatible(self):
        a = HigherCell(source="V01", target="V04", level=1)
        b = HigherCell(source="V18", target="V24", level=1)
        result = a.compose(b)
        assert result is None

    def test_compose_different_levels(self):
        a = HigherCell(source="V01", target="V04", level=1)
        b = HigherCell(source="V04", target="V18", level=2)
        result = a.compose(b)
        assert result is None

    def test_session_id_propagation(self):
        a = HigherCell(source="V01", target="V04", level=1, session_id="sess-001")
        b = HigherCell(source="V04", target="V18", level=1)
        result = a.compose(b)
        assert result is not None
        assert result.session_id == "sess-001"

    def test_compose_associativity(self):
        a = HigherCell(source="V01", target="V04", level=1)
        b = HigherCell(source="V04", target="V18", level=1)
        c = HigherCell(source="V18", target="V24", level=1)
        left = a.compose(b)
        assert left is not None
        left_result = left.compose(c)
        right = b.compose(c)
        assert right is not None
        right_result = a.compose(right)
        assert left_result is not None
        assert right_result is not None
        assert left_result.source == right_result.source == "V01"
        assert left_result.target == right_result.target == "V24"


# PURPOSE: Test suite validating Associator correctness
class TestAssociator(unittest.TestCase):
    """Test Associator structure."""

    def test_basic_associator(self):
        a = Associator(f="/noe", g="/ele", h="/ene")
        assert "α(/noe,/ele,/ene)" in a.label
        assert a.left_associated == "(/noe>>/ele)>>/ene"
        assert a.right_associated == "/noe>>(/ele>>/ene)"
        assert a.is_nontrivial

    def test_auto_magnitude_same_tribe(self):
        a = Associator(f="/noe", g="/bou", h="/zet")  # all Ousia
        assert a.magnitude == 0.2

    def test_auto_magnitude_cross_tribe(self):
        a = Associator(f="/noe", g="/ele", h="/ath")  # Ousia, Orexis, Chronos
        assert a.magnitude == 0.8

    def test_explicit_magnitude(self):
        a = Associator(f="/noe", g="/ele", h="/ene", magnitude=0.42)
        assert a.magnitude == 0.42

    def test_trivial_associator(self):
        a = Associator(f="/noe", g="/ele", h="/ene", magnitude=0.0)
        assert not a.is_nontrivial

    def test_build_associator_valid(self):
        a = build_associator("/noe", "/ele", "/ene")
        assert a is not None
        assert a.f == "/noe"

    def test_build_associator_invalid(self):
        a = build_associator("/noe", "/invalid", "/ene")
        assert a is None

    def test_temporal_shift(self):
        a = Associator(f="/noe", g="/ele", h="/ene", magnitude=1.0, session_id="sess-001")
        a2 = a.temporal_shift(new_magnitude=0.3, new_session_id="sess-050")
        assert a2.magnitude == 0.3
        assert a2.session_id == "sess-050"
        assert a.magnitude == 1.0  # original unchanged

    def test_expertise_pattern(self):
        """Novice → Expert: associator magnitude decreases."""
        novice = Associator(f="/noe", g="/ele", h="/ene", magnitude=1.0, session_id="sess-001")
        intermediate = novice.temporal_shift(0.6, "sess-025")
        expert = intermediate.temporal_shift(0.1, "sess-100")
        assert novice.magnitude > intermediate.magnitude > expert.magnitude
        assert expert.is_nontrivial


# PURPOSE: Test suite validating composition laws
class TestCompositionLaws(unittest.TestCase):
    """Test verify_composition_laws."""

    def test_composition_laws_pass(self):
        violations = verify_composition_laws()
        assert violations == [], f"Composition law violations: {violations}"


# PURPOSE: Test suite validating PoiesisSpace correctness
class TestPoiesisSpace(unittest.TestCase):
    """Test PoiesisSpace structure."""

    def test_v01_space(self):
        space = get_poiesis_space("V01")
        assert space is not None
        assert space.verb_name == "Noēsis"
        assert space.verb_ja == "理解"
        assert space.ccl_cmd == "/noe"
        assert space.tribe == "Ousia"

    def test_lookup_by_ccl(self):
        space = get_poiesis_space("/ele")
        assert space is not None
        assert space.verb_id == "V18"
        assert space.verb_name == "Elenchos"

    def test_unknown_verb(self):
        space = get_poiesis_space("V99")
        assert space is None

    def test_one_cell_to(self):
        v01 = get_poiesis_space("V01")
        v04 = get_poiesis_space("V04")
        assert v01 is not None and v04 is not None
        cell = v01.one_cell_to(v04)
        assert cell.source == "V01"
        assert cell.target == "V04"
        assert cell.level == 1
        assert "/noe >> /ene" in cell.label

    def test_native_poles(self):
        space = get_poiesis_space("V01")
        assert space is not None
        poles = space.native_poles
        assert poles["Flow"] == "I"
        assert poles["Strategy"] == "E"
        assert len(poles) == 2

    def test_native_poles_v18(self):
        space = get_poiesis_space("/ele")
        assert space is not None
        poles = space.native_poles
        assert poles["Flow"] == "I"
        assert poles["Valence"] == "-"

    def test_all_axes(self):
        axes = PoiesisSpace.all_axes()
        assert len(axes) == 6
        assert axes[0] == ("Flow", "I", "A")

    def test_compose_triple(self):
        a = get_poiesis_space("V01")
        b = get_poiesis_space("V18")
        c = get_poiesis_space("V24")
        assert a and b and c
        f, g, assoc = PoiesisSpace.compose_triple(a, b, c)
        assert f.source == "V01"
        assert f.target == "V18"
        assert g.source == "V18"
        assert g.target == "V24"
        assert assoc.f == "/noe"
        assert assoc.g == "/ele"
        assert assoc.h == "/par"
        assert assoc.magnitude == 0.8  # 3 tribes


# PURPOSE: Test suite validating registry correctness
class TestRegistry(unittest.TestCase):
    """Test the 48-Poiesis registry (v5.4)."""

    def test_all_spaces_count(self):
        spaces = get_all_spaces()
        assert len(spaces) == 48

    def test_tribe_counts(self):
        for tribe in ["Ousia", "Methodos", "Krisis", "Diástasis", "Orexis", "Chronos"]:
            spaces = get_tribe_spaces(tribe)
            assert len(spaces) == 8, f"Tribe {tribe} has {len(spaces)} verbs, expected 8"

    def test_count_cells(self):
        stats = count_cells()
        assert stats["zero_cells"] == 48
        assert stats["one_cells"] == 48 * 47

    def test_verify_all(self):
        results = verify_all()
        assert len(results) == 48
        for verb_id, violations in results.items():
            assert violations == [], f"{verb_id} has violations: {violations}"


# PURPOSE: Test suite validating pentagon identity
class TestPentagon(unittest.TestCase):
    """Test pentagon identity verification."""

    def test_pentagon_valid(self):
        violations = verify_pentagon("/noe", "/ele", "/ene", "/ath")
        assert violations == []

    def test_pentagon_invalid(self):
        violations = verify_pentagon("/noe", "/invalid", "/ene", "/ath")
        assert len(violations) > 0


# PURPOSE: Test suite validating triangle identity
class TestTriangleIdentity(unittest.TestCase):
    """Test triangle identity verification."""

    def test_triangle_valid(self):
        violations = verify_triangle_identity("/noe", "/ele")
        assert violations == []

    def test_triangle_invalid(self):
        violations = verify_triangle_identity("/noe", "/invalid")
        assert len(violations) > 0


# PURPOSE: Test suite validating overall coherence
class TestCoherence(unittest.TestCase):
    """Test full L3 coherence verification."""

    def test_verify_coherence(self):
        res = verify_coherence()
        # Coherence should be valid across representative samples
        assert res["is_coherent"], f"Coherence failed: {res['pentagon_violations']} {res['triangle_violations']}"
        assert len(res["pentagon_violations"]) == 0 # type: ignore
        assert len(res["triangle_violations"]) == 0 # type: ignore
        assert res["n_pentagon_checked"] > 0 # type: ignore
        assert res["n_triangle_checked"] > 0 # type: ignore


# PURPOSE: Test suite validating display functions
class TestDisplay(unittest.TestCase):
    """Test display functions."""

    def test_describe_space(self):
        space = get_poiesis_space("V01")
        assert space is not None
        desc = describe_space(space)
        assert "Noēsis" in desc
        assert "/noe" in desc

    def test_describe_summary(self):
        summary = describe_summary()
        assert "L3" in summary
        assert "48" in summary


# PURPOSE: Test suite validating backward compatibility
class TestLegacy(unittest.TestCase):
    """Test legacy aliases for backward compatibility."""

    def test_twocell_alias(self):
        cell = TwoCell(source="V01", target="V04", level=1)
        assert cell.label == "V01 → V04"

    def test_derivative_space_legacy(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            space = get_derivative_space("O1")
            assert space is not None
            assert space.verb_id == "V01"

    def test_series_spaces_legacy(self):
        spaces = get_series_spaces("Tel")
        assert len(spaces) == 8

    def test_count_two_cells_legacy(self):
        stats = count_two_cells()
        assert stats["zero_cells"] == 48
        assert "total" in stats
        assert "identity" in stats
        assert "non_identity" in stats

    def test_derivative_space_deprecation_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            space = get_derivative_space("S1")
            assert space is not None
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "positional" in str(w[0].message)

    def test_derivative_space_no_warning_for_o_series(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            space = get_derivative_space("O1")
            assert space is not None
            assert space.verb_id == "V01"
            assert len(w) == 0


if __name__ == "__main__":
    unittest.main()
