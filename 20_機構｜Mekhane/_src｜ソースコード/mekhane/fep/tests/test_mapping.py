# PROOF: [L2/テスト] <- mekhane/fep/tests/test_mapping.py
# PURPOSE: 12 Helmholtz 演算子と Flow が 36 Poiesis + 12 H-series に正確にマップされるかを検証
"""Tests for mekhane.fep.mapping."""

import pytest
from mekhane.fep.basis import HelmholtzComponent, get_operator, HELMHOLTZ_OPERATORS
from mekhane.fep.mapping import (
    POIESIS_VERBS, HSERIES_VERBS, ALL_COGNITIVE_OPS_COUNT,
    get_poiesis_verb, map_to_verb,
)


class TestPoiesisMapping:
    """Poiesis 動詞層へのマッピング (Level A) の構造的・意味的検証"""

    def test_36_verbs_manifest(self):
        """36 の Poiesis 動詞が漏れなく定義されている (v5.0+)。"""
        assert len(POIESIS_VERBS) == 36

    def test_all_ccl_names_unique(self):
        """CCL 名 (e.g. 'noe') に重複がない。"""
        ccl_names = [v.ccl_name for v in POIESIS_VERBS.values()]
        assert len(ccl_names) == len(set(ccl_names))

    def test_all_operators_combined_with_flow_produce_verbs(self):
        """12 演算子 × 2 Flow極端 ＝ 24 枠がすべて埋まっている。"""
        covered_verbs = set()
        for op in HELMHOLTZ_OPERATORS:
            for flow_pole in ("I", "A"):
                verb = map_to_verb(op, flow_pole)
                assert verb is not None, f"Mapping missing for {op.name} × {flow_pole}"
                covered_verbs.add(verb.ccl_name)
        assert len(covered_verbs) == 24

    def test_get_operator_works_from_verb(self):
        """PoiesisVerb インスタンスが元の演算子を正しく逆引きできる。"""
        for verb in POIESIS_VERBS.values():
            op = verb.operator
            assert op.coordinate == verb.coordinate
            assert op.component == verb.helmholtz_component

    def test_get_poiesis_verb_util(self):
        """get_poiesis_verb("xyz") などで取得できる。"""
        verb = get_poiesis_verb("noe")
        assert verb is not None
        assert verb.greek_name == "Noēsis"

        verb = get_poiesis_verb("/noe")
        assert verb is not None
        assert verb.greek_name == "Noēsis"

    def test_semantic_mapping_telos(self):
        """Telos族 (Value) の意味論的対応確認。
        I×E (Q) -> noe, I×P (Γ) -> bou
        A×E (Q) -> zet, A×P (Γ) -> ene
        """
        q_val = get_operator("Value", HelmholtzComponent.SOLENOIDAL)
        g_val = get_operator("Value", HelmholtzComponent.GRADIENT)

        assert map_to_verb(q_val, "I").ccl_name == "noe"
        assert map_to_verb(g_val, "I").ccl_name == "bou"
        assert map_to_verb(q_val, "A").ccl_name == "zet"
        assert map_to_verb(g_val, "A").ccl_name == "ene"

    def test_semantic_mapping_methodos(self):
        """Methodos族 (Function) の意味論的対応確認。
        I×Explore (Q) -> ske, I×Exploit (Γ) -> sag
        A×Explore (Q) -> pei, A×Exploit (Γ) -> tek
        """
        q_func = get_operator("Function", HelmholtzComponent.SOLENOIDAL)
        g_func = get_operator("Function", HelmholtzComponent.GRADIENT)

        assert map_to_verb(q_func, "I").ccl_name == "ske"
        assert map_to_verb(g_func, "I").ccl_name == "sag"
        assert map_to_verb(q_func, "A").ccl_name == "pei"
        assert map_to_verb(g_func, "A").ccl_name == "tek"

    def test_semantic_mapping_s_pole_telos(self):
        """Telos族 S極 (v5.0+) の意味論的対応確認。
        S×E (Q) -> the, S×P (Γ) -> ant
        """
        q_val = get_operator("Value", HelmholtzComponent.SOLENOIDAL)
        g_val = get_operator("Value", HelmholtzComponent.GRADIENT)

        assert map_to_verb(q_val, "S").ccl_name == "the"
        assert map_to_verb(g_val, "S").ccl_name == "ant"

    def test_s_pole_verbs_count(self):
        """S極動詞が12個存在する (v5.0+)。"""
        s_verbs = [v for v in POIESIS_VERBS.values() if v.flow_pole == "S"]
        assert len(s_verbs) == 12

    def test_hseries_manifest(self):
        """12 の H-series 動詞が定義されている (v5.1+)。"""
        assert len(HSERIES_VERBS) == 12

    def test_total_cognitive_ops(self):
        """48 認知操作 = 36 Poiesis + 12 H-series (v5.4)。"""
        assert ALL_COGNITIVE_OPS_COUNT == 48
