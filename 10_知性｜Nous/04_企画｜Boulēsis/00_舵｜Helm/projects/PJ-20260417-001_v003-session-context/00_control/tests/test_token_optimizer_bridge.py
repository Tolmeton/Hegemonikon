from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


BRIDGE_PATH = Path(
    "/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/projects/PJ-20260417-001_v003-session-context/00_control/scripts/token_optimizer_bridge.py"
)


def load_bridge_module():
    spec = importlib.util.spec_from_file_location("token_optimizer_bridge", BRIDGE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TokenOptimizerBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = load_bridge_module()

    def test_map_measure_to_quality_score(self):
        measure = {
            "quality_estimate": 97,
            "overhead_tokens": 31208,
            "overhead_pct": 3.1,
            "unused_skill_candidates": 61,
            "top_offenders": ["skills"],
            "timestamp": "2026-04-20T00:00:00+09:00",
        }

        mapped = self.bridge.map_measure_to_quality_score(measure)

        self.assertEqual(mapped["score"], 97)
        self.assertEqual(mapped["band"], "healthy")
        self.assertEqual(mapped["context_fill_pct"], 3.1)
        self.assertIn("overhead_tokens_detected", mapped["evidence"])
        self.assertIn("unused_skill_surface_detected", mapped["evidence"])

    def test_map_checkpoint_to_summary(self):
        checkpoint = {
            "id": "ckpt-123",
            "generated": "2026-04-20T00:00:00+09:00",
            "active_task": "bridge sidecar fields",
            "key_decisions": ["keep canonical files unchanged"],
            "modified_files": ["a.py"],
            "recently_read_files": ["b.py"],
            "open_questions": ["generalize later?"],
            "agent_state": {"worker_count": 1, "mode": "bridge"},
            "continuation_hint": "reopen recent_reads after restore",
            "archived_tool_results": [{"ref_id": "arch-1"}],
        }

        mapped = self.bridge.map_checkpoint_to_summary(checkpoint, source="token-optimizer")

        self.assertEqual(mapped["checkpoint_id"], "ckpt-123")
        self.assertEqual(mapped["captured_at"], "2026-04-20T00:00:00+09:00")
        self.assertEqual(mapped["active_task"], "bridge sidecar fields")
        self.assertEqual(mapped["modified_files"], ["a.py"])
        self.assertEqual(mapped["recent_reads"], ["b.py"])
        self.assertEqual(mapped["archived_result_refs"], ["arch-1"])
        self.assertIn("mode=bridge", mapped["agent_state_digest"])

    def test_map_archive_refs_accepts_actual_token_optimizer_entry(self):
        entry = {
            "tool_name": "Read",
            "tool_use_id": "tokopt_readme_20260423",
            "chars": 54341,
            "original_chars": 54341,
            "tokens_est": 13585,
            "truncated": False,
            "timestamp": "2026-04-23T12:08:32.049123+00:00",
            "archived_from": "PostToolUse",
            "response": "x" * 5000,
        }

        mapped = self.bridge.map_archive_refs(entry)

        self.assertEqual(mapped[0]["ref_id"], "tokopt_readme_20260423")
        self.assertEqual(mapped[0]["kind"], "Read")
        self.assertEqual(mapped[0]["origin"], "PostToolUse")
        self.assertEqual(mapped[0]["summary"], "Read archived (54341 chars)")

    def test_cli_builds_instance_yaml(self):
        schema = {
            "surface_id": "ADJ-TO-001",
            "title": "token-optimizer adjoint surface for session-context",
            "canonicality": "noncanonical_sidecar",
            "host_state_packet": {
                "project_index": "/tmp/project_index.yaml",
                "decisions": "/tmp/decisions.md",
            },
            "scope": {
                "included": ["checkpoint_summary", "quality_score", "archive_refs"],
            },
        }
        measure = {"quality_estimate": 82}
        checkpoint = {
            "id": "ckpt-001",
            "active_task": "write bridge",
            "key_decisions": ["sidecar only"],
            "modified_files": [],
            "recent_reads": [],
            "open_questions": [],
        }
        archive_payload = [
            {
                "id": "arch-1",
                "type": "tool_result",
                "summary": "large output moved out",
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema_path = tmp / "schema.yaml"
            measure_path = tmp / "measure.json"
            checkpoint_path = tmp / "checkpoint.json"
            archive_path = tmp / "archive.json"
            output_path = tmp / "instance.yaml"

            schema_path.write_text(yaml.safe_dump(schema, sort_keys=False, allow_unicode=True), encoding="utf-8")
            measure_path.write_text(json.dumps(measure), encoding="utf-8")
            checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
            archive_path.write_text(json.dumps(archive_payload), encoding="utf-8")

            subprocess.run(
                [
                    "python3",
                    str(BRIDGE_PATH),
                    "--schema",
                    str(schema_path),
                    "--measure-json",
                    str(measure_path),
                    "--checkpoint-json",
                    str(checkpoint_path),
                    "--archive-json",
                    str(archive_path),
                    "--output",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            payload = yaml.safe_load(output_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["surface_id"], "ADJ-TO-001")
        self.assertEqual(payload["quality_score"]["score"], 82)
        self.assertEqual(payload["checkpoint_summary"]["checkpoint_id"], "ckpt-001")
        self.assertEqual(payload["checkpoint_summary"]["active_task"], "write bridge")
        self.assertEqual(payload["archive_refs"][0]["ref_id"], "arch-1")


if __name__ == "__main__":
    unittest.main()
