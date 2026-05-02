"""CCL contract compiler / validator tests."""

import pytest

from hermeneus.src.ccl_contracts import (
    compile_ccl_contract,
    validate_ccl_contract,
)


@pytest.mark.parametrize(
    "expr, expected_macro",
    [
        ("/ske", None),
        ("/ske>>/noe", None),
        ("@plan", "plan"),
        ("@search+", "search"),
        ("(/ske+*/sag+)", None),
        ("C:{/bou+~(/prm*/tek)_/m+~(/d*/k)_V:{/dia+}}", None),
        ("F:[×3]{@build}", "build"),
    ],
)
def test_compile_ccl_contract_examples(expr: str, expected_macro: str | None):
    contract = compile_ccl_contract(expr, invocation_mode="explicit")
    assert contract.normalized_ccl
    assert contract.expanded_ccl
    assert len(contract.obligations) > 0
    if expected_macro:
        assert expected_macro in contract.macro_names


def test_macro_sources_use_agents_workflows():
    contract = compile_ccl_contract("@plan", invocation_mode="explicit")
    assert "@plan" in contract.source_paths
    source_path = contract.source_paths["@plan"]
    assert ".agents" in source_path
    assert source_path.endswith("ccl-plan.md")


def test_validator_blocks_noncompliant_explicit_output():
    contract = compile_ccl_contract("/ske", invocation_mode="explicit")
    validation = validate_ccl_contract(contract, "短い要約だけ")
    assert validation.is_compliant is False
    assert "phase_0" in validation.unmet_requirements


def test_validator_accepts_minimal_structured_ske_output():
    contract = compile_ccl_contract("/ske", invocation_mode="explicit")
    output = """
派生選択: /ske.struct
Phase 0
[CHECKPOINT P-0/3]
Phase 0.5
[CHECKPOINT P-0.5/3]
Phase 1
[CHECKPOINT P-1/3]
Phase 2
[CHECKPOINT P-2/3]
orthogonality proof
T1 T2 T3
SkQS
"""
    validation = validate_ccl_contract(contract, output)
    assert validation.is_compliant is True
