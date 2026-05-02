from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import yaml

from mekhane.peira.hermes_ttsi_probe import (
    build_value_deltas,
    main,
    parse_hermes_skill,
    run_probe,
)


def _write_skill(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# CI Safety Skill",
                "",
                "Use this skill when you need to verify tests and document decisions.",
                "",
                "## Trigger",
                "- Run before commit when a workflow changes",
                "",
                "## Steps",
                "1. Run tests and verify the result.",
                "2. Document the decision in a report artifact.",
                "",
                "## Guardrails",
                "- Do not skip validation.",
            ]
        ),
        encoding="utf-8",
    )


def _write_values(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "version": "1.0.0",
                "values": {
                    "core_principles": {
                        "zero_entropy": {"weight": 1.0, "description": "clarity"},
                        "hyperengineering": {"weight": 0.9, "description": "automation"},
                        "japanese_first": {"weight": 0.95, "description": "jp"},
                    },
                    "development_priorities": {
                        "test_before_commit": {"weight": 0.85, "description": "tests"},
                        "incremental_changes": {"weight": 0.8, "description": "small steps"},
                        "document_decisions": {"weight": 0.75, "description": "docs"},
                    },
                },
                "meta": {"last_updated": "2026-01-27T14:52:00+09:00", "update_count": 1},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_patterns_template(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({"schema": {"example": [{"pattern": "foo", "message": "bar"}]}}),
        encoding="utf-8",
    )


def _write_a_base(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    matrix = np.arange(14 * 48, dtype=np.float64).reshape(14, 48)
    np.save(path, np.array([matrix], dtype=object), allow_pickle=True)


def test_parse_hermes_skill_extracts_core_fields(tmp_path: Path):
    skill_path = tmp_path / ".hermes" / "skills" / "ci-safety" / "SKILL.md"
    _write_skill(skill_path)

    snapshot = parse_hermes_skill(skill_path)

    assert snapshot.skill_id == "ci-safety"
    assert snapshot.title == "CI Safety Skill"
    assert "verify tests" in snapshot.summary.lower()
    assert snapshot.trigger_text.startswith("Run before commit")
    assert snapshot.steps[0].startswith("Run tests")
    assert snapshot.guardrails == ["Do not skip validation."]
    assert len(snapshot.raw_text_hash) == 64


def test_build_value_deltas_only_touches_known_keys(tmp_path: Path):
    skill_path = tmp_path / ".hermes" / "skills" / "ci-safety" / "SKILL.md"
    values_path = tmp_path / "values.json"
    _write_skill(skill_path)
    _write_values(values_path)

    snapshot = parse_hermes_skill(skill_path)
    deltas = build_value_deltas(snapshot, json.loads(values_path.read_text(encoding="utf-8")))

    touched = {(delta.group, delta.key) for delta in deltas}
    assert ("development_priorities", "test_before_commit") in touched
    assert ("development_priorities", "document_decisions") in touched
    assert all(-0.05 <= delta.delta <= 0.05 for delta in deltas)


def test_run_probe_writes_shadow_bundle(tmp_path: Path):
    hermes_home = tmp_path / ".hermes"
    values_path = tmp_path / "runtime" / "values.json"
    patterns_path = tmp_path / "template" / "patterns.yaml"
    a_base = tmp_path / "fep" / "learned_A.npy"
    shadow_root = tmp_path / "artifacts" / "pei_hermes_ttsi_probe_test"
    report_path = tmp_path / "artifacts" / "pei_hermes_ttsi_probe_test.md"

    _write_skill(hermes_home / "skills" / "ci-safety" / "SKILL.md")
    _write_values(values_path)
    _write_patterns_template(patterns_path)
    _write_a_base(a_base)

    run = run_probe(
        hermes_home=hermes_home,
        shadow_root=shadow_root,
        report_path=report_path,
        values_live_path=values_path,
        patterns_template_path=patterns_path,
        a_base_path=a_base,
        skill_limit=None,
    )

    assert run.exit_code == 0
    assert Path(run.patterns_path).exists()
    assert Path(run.values_path).exists()
    assert Path(run.learned_a_path).exists()
    assert Path(run.manifest_path).exists()
    assert Path(run.report_path).exists()

    manifest = json.loads(Path(run.manifest_path).read_text(encoding="utf-8"))
    assert manifest["run"]["gate_pass_count"] == 1
    assert manifest["bundles"][0]["gate_decision"] == "shadow_pass"

    values_shadow = json.loads(Path(run.values_path).read_text(encoding="utf-8"))
    assert values_shadow["values"]["development_priorities"]["test_before_commit"]["weight"] > 0.85

    patterns_shadow = yaml.safe_load(Path(run.patterns_path).read_text(encoding="utf-8"))
    assert patterns_shadow["candidates"][0]["id"] == "ci-safety"


def test_main_writes_missing_input_report_without_shadow_bundle(tmp_path: Path, monkeypatch):
    report_path = tmp_path / "artifacts" / "pei_missing_input.md"
    shadow_root = tmp_path / "artifacts" / "pei_missing_input"
    hermes_home = tmp_path / ".hermes"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "hermes_ttsi_probe.py",
            "--hermes-home",
            str(hermes_home),
            "--report",
            str(report_path),
            "--shadow-root",
            str(shadow_root),
        ],
    )

    exit_code = main()

    assert exit_code == 1
    assert report_path.exists()
    assert "missing_input" in report_path.read_text(encoding="utf-8")
    assert not shadow_root.exists()
