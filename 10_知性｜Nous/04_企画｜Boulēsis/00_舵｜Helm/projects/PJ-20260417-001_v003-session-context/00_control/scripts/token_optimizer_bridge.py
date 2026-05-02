#!/usr/bin/env python3
"""Bridge token-optimizer telemetry into the session-context adjoint sidecar."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


SUPPORTED_FIELDS = {"checkpoint_summary", "quality_score", "archive_refs"}


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=True)


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _get_path(data: Any, dotted_path: str) -> Any:
    current = data
    for part in dotted_path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        return None
    return current


def _first_present(data: Any, *paths: str) -> Any:
    for dotted_path in paths:
        value = _get_path(data, dotted_path)
        if value not in (None, "", [], {}):
            return value
    return None


def _ensure_list(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return value
    return [value]


def _stringify_scalar(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _stringify_list(values: Any) -> list[str]:
    return [_stringify_scalar(item) for item in _ensure_list(values)]


def _digest_agent_state(agent_state: Any) -> str | None:
    if agent_state in (None, "", [], {}):
        return None
    if isinstance(agent_state, dict):
        pairs = []
        for key in sorted(agent_state):
            value = agent_state[key]
            if isinstance(value, (str, int, float, bool)) or value is None:
                pairs.append(f"{key}={value}")
            elif isinstance(value, list):
                pairs.append(f"{key}[{len(value)}]")
            elif isinstance(value, dict):
                pairs.append(f"{key}{{{len(value)}}}")
            else:
                pairs.append(f"{key}=<{type(value).__name__}>")
        digest = ", ".join(pairs)
        return digest[:400] if digest else None
    return _stringify_scalar(agent_state)[:400]


def _quality_band(score: int) -> str:
    if score >= 80:
        return "healthy"
    if score >= 60:
        return "watch"
    if score >= 40:
        return "degraded"
    return "critical"


def load_surface_schema(path: Path) -> dict[str, Any]:
    data = _load_yaml(path)
    included = set(_ensure_list(_get_path(data, "scope.included")))
    if not SUPPORTED_FIELDS.issubset(included):
        raise ValueError(
            "Surface schema is missing required supported fields: "
            f"{sorted(SUPPORTED_FIELDS - included)}"
        )
    return data


def map_measure_to_quality_score(measure: dict[str, Any], measured_at: str | None = None) -> dict[str, Any]:
    score = _first_present(
        measure,
        "score",
        "quality_score",
        "quality_estimate",
        "overall_score",
    )
    if score is None:
        raise ValueError("measure JSON does not contain a quality score")
    score_int = int(score)

    evidence: list[str] = []
    if _first_present(measure, "overhead_tokens", "metrics.overhead_tokens") not in (None, 0):
        evidence.append("overhead_tokens_detected")

    unused_candidates = _first_present(
        measure,
        "unused_skill_candidates",
        "quick_wins.unused_skill_candidates",
        "quick_win.unused_skills",
    )
    if unused_candidates not in (None, 0):
        evidence.append("unused_skill_surface_detected")

    if _first_present(measure, "top_offenders", "metrics.top_offenders"):
        evidence.append("top_offenders_recorded")

    if not evidence:
        evidence.append("score_only_import")

    quality_score: dict[str, Any] = {
        "score": score_int,
        "band": _first_present(measure, "band", "quality_band") or _quality_band(score_int),
        "measured_at": measured_at or _first_present(
            measure,
            "measured_at",
            "timestamp",
            "created_at",
        ) or _now_iso(),
        "evidence": evidence,
    }

    optional_map = {
        "context_fill_pct": ("context_fill_pct", "metrics.context_fill_pct", "overhead_pct"),
        "stale_reads": ("stale_reads", "metrics.stale_reads"),
        "bloated_results": ("bloated_results", "metrics.bloated_results"),
        "duplicates": ("duplicates", "metrics.duplicates"),
        "compaction_depth": ("compaction_depth", "metrics.compaction_depth"),
        "decision_density": ("decision_density", "metrics.decision_density"),
        "agent_efficiency": ("agent_efficiency", "metrics.agent_efficiency"),
    }
    for field, paths in optional_map.items():
        value = _first_present(measure, *paths)
        if value not in (None, "", [], {}):
            quality_score[field] = value

    return quality_score


def map_checkpoint_to_summary(
    checkpoint: dict[str, Any],
    source: str,
    checkpoint_id: str | None = None,
    captured_at: str | None = None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "checkpoint_id": _first_present(checkpoint, "checkpoint_id", "id") or checkpoint_id or "checkpoint-unknown",
        "source": source,
        "captured_at": _first_present(
            checkpoint,
            "captured_at",
            "timestamp",
            "created_at",
            "saved_at",
            "generated",
        ) or captured_at or _now_iso(),
        "active_task": _first_present(
            checkpoint,
            "active_task",
            "activeTask",
            "continuation.active_task",
            "current_task",
            "active_plan.title",
            "continuation_hint",
        ) or "unspecified",
        "key_decisions": _stringify_list(
            _first_present(checkpoint, "key_decisions", "decisions", "checkpoint.key_decisions")
        ),
        "modified_files": _stringify_list(
            _first_present(checkpoint, "modified_files", "changed_files", "checkpoint.modified_files")
        ),
        "recent_reads": _stringify_list(
            _first_present(checkpoint, "recent_reads", "recently_read_files", "checkpoint.recent_reads")
        ),
        "open_questions": _stringify_list(
            _first_present(checkpoint, "open_questions", "questions", "checkpoint.open_questions")
        ),
    }

    error_context = _first_present(checkpoint, "error_context", "errors", "recent_errors")
    if error_context not in (None, "", [], {}):
        summary["error_context"] = _stringify_list(error_context)

    agent_state_digest = _digest_agent_state(
        _first_present(checkpoint, "agent_state", "checkpoint.agent_state")
    )
    if agent_state_digest:
        summary["agent_state_digest"] = agent_state_digest

    continuation_hint = _first_present(
        checkpoint,
        "continuation_hint",
        "continuation.next_step",
        "continuation.summary",
    )
    if continuation_hint not in (None, "", [], {}):
        summary["continuation_hint"] = _stringify_scalar(continuation_hint)

    archived_refs = _first_present(
        checkpoint,
        "archived_result_refs",
        "archived_tool_results",
        "continuation.archived_result_refs",
    )
    if archived_refs not in (None, "", [], {}):
        summary["archived_result_refs"] = [
            item.get("ref_id", item.get("id", _stringify_scalar(item)))
            if isinstance(item, dict)
            else _stringify_scalar(item)
            for item in _ensure_list(archived_refs)
        ]

    return summary


def map_archive_refs(archive_payload: Any, default_origin: str = "token-optimizer") -> list[dict[str, Any]]:
    if isinstance(archive_payload, dict):
        items = _first_present(
            archive_payload,
            "archive_refs",
            "results",
            "items",
        )
        archive_items = _ensure_list(items if items is not None else archive_payload)
    else:
        archive_items = _ensure_list(archive_payload)

    refs: list[dict[str, Any]] = []
    for index, item in enumerate(archive_items, start=1):
        if isinstance(item, dict):
            ref = {
                "ref_id": item.get("ref_id") or item.get("id") or item.get("tool_use_id") or f"archive-{index}",
                "kind": item.get("kind") or item.get("type") or item.get("tool_name") or "tool_result",
                "origin": item.get("origin") or item.get("source") or item.get("archived_from") or default_origin,
                "summary": (
                    item.get("summary")
                    or item.get("title")
                    or item.get("description")
                    or (
                        f"{item.get('tool_name')} archived ({item.get('chars')} chars)"
                        if item.get("tool_name") and item.get("chars") not in (None, "")
                        else None
                    )
                    or f"archive ref {index}"
                ),
            }
            for optional in ("path", "size_bytes", "expand_hint", "linked_files"):
                if optional in item and item[optional] not in (None, "", [], {}):
                    ref[optional] = item[optional]
        else:
            ref = {
                "ref_id": f"archive-{index}",
                "kind": "opaque_ref",
                "origin": default_origin,
                "summary": _stringify_scalar(item),
            }
        refs.append(ref)
    return refs


def build_instance(
    schema: dict[str, Any],
    measure: dict[str, Any] | None,
    checkpoint: dict[str, Any] | None,
    archive_payload: Any,
    source_inputs: dict[str, str],
) -> dict[str, Any]:
    instance: dict[str, Any] = {
        "surface_id": schema["surface_id"],
        "surface_title": schema.get("title"),
        "status": "generated",
        "generated_at": _now_iso(),
        "generated_by": "token_optimizer_bridge.py",
        "canonicality": schema.get("canonicality"),
        "host_state_packet": schema.get("host_state_packet"),
        "source_inputs": source_inputs,
    }

    if checkpoint is not None:
        instance["checkpoint_summary"] = map_checkpoint_to_summary(
            checkpoint,
            source="token-optimizer",
            checkpoint_id=Path(source_inputs["checkpoint_json"]).stem if "checkpoint_json" in source_inputs else None,
        )
    if measure is not None:
        instance["quality_score"] = map_measure_to_quality_score(measure)
    if archive_payload is not None:
        instance["archive_refs"] = map_archive_refs(archive_payload)
    else:
        instance["archive_refs"] = []

    return instance


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", required=True, type=Path, help="Path to token_optimizer_adjoint_surface.yaml")
    parser.add_argument("--measure-json", type=Path, help="Path to token-optimizer measure JSON")
    parser.add_argument("--checkpoint-json", type=Path, help="Path to token-optimizer checkpoint JSON")
    parser.add_argument("--archive-json", type=Path, help="Path to token-optimizer archive refs JSON")
    parser.add_argument("--output", required=True, type=Path, help="Output YAML path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    schema = load_surface_schema(args.schema)

    measure = _load_json(args.measure_json) if args.measure_json else None
    checkpoint = _load_json(args.checkpoint_json) if args.checkpoint_json else None
    archive_payload = _load_json(args.archive_json) if args.archive_json else None

    source_inputs = {"schema": str(args.schema)}
    if args.measure_json:
        source_inputs["measure_json"] = str(args.measure_json)
    if args.checkpoint_json:
        source_inputs["checkpoint_json"] = str(args.checkpoint_json)
    if args.archive_json:
        source_inputs["archive_json"] = str(args.archive_json)

    instance = build_instance(schema, measure, checkpoint, archive_payload, source_inputs)
    _write_yaml(args.output, instance)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
