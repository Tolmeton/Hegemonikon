#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/ A0→薄い観測圧縮が必要→phantazein_observation が担う
"""
Phantazein Observation Runtime — deterministic observation compression + packet rendering.

V1 方針:
- transcript mining は行わない
- LLM 圧縮を使わない
- hook / legacy artifacts / Pinakas / Handoff から薄い packet を組む
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from mekhane.paths import PINAKAS_DIR
from mekhane.symploke.kairos_ingest import get_handoff_files, parse_handoff

try:
    import yaml
except Exception:  # noqa: BLE001
    yaml = None


AUTO_INJECT_THRESHOLD = 0.75
BOOT_PACKET_LIMIT = 1600
FILE_PACKET_LIMIT = 700

_WHITESPACE_RE = re.compile(r"\s+")
_WARNING_RE = re.compile(
    r"(warning|error|failed|traceback|exception|denied|timeout|not found)",
    re.IGNORECASE,
)
_PINAKAS_BOARDS: tuple[tuple[str, str, set[str]], ...] = (
    ("task", "PINAKAS_TASK.yaml", {"open", "in_progress"}),
    ("question", "PINAKAS_QUESTION.yaml", {"open"}),
    ("seed", "PINAKAS_SEED.yaml", {"open"}),
    ("wish", "PINAKAS_WISH.yaml", {"open"}),
    ("whiteboard", "PINAKAS_WHITEBOARD.yaml", {"active"}),
)
_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2, "": 3}


@dataclass(slots=True)
class ObservationSpec:
    session_id: str
    source_kind: str
    source_ref: str
    observation_kind: str
    summary: str
    confidence: float
    project_id: str = ""
    tags: list[str] = field(default_factory=list)
    file_paths: list[str] = field(default_factory=list)
    links: list[tuple[str, str, float]] = field(default_factory=list)


def _collapse_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text or "").strip()


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict):
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))
        return " ".join(parts)
    if isinstance(value, dict):
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)
    return str(value)


def _shorten(text: str, limit: int = 220) -> str:
    clean = _collapse_whitespace(text)
    if len(clean) <= limit:
        return clean
    return clean[: max(0, limit - 1)].rstrip() + "…"


def _canonical_file_paths(paths: Iterable[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for raw in paths:
        raw = str(raw or "").strip()
        if not raw:
            continue
        try:
            path = str(Path(raw).expanduser().resolve(strict=False))
        except OSError:
            path = raw
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


def _extract_tool_paths(tool_input: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    for key in ("file_path", "path"):
        value = tool_input.get(key)
        if isinstance(value, str):
            candidates.append(value)
    paths = tool_input.get("paths")
    if isinstance(paths, list):
        candidates.extend(str(item) for item in paths if isinstance(item, str))
    return _canonical_file_paths(candidates)


def _tool_verb(tool_name: str) -> str:
    return {
        "Read": "Read",
        "Edit": "Edit",
        "Write": "Write",
        "MultiEdit": "MultiEdit",
        "Grep": "Grep",
        "Glob": "Glob",
        "Bash": "Bash",
    }.get(tool_name, tool_name or "Tool")


def tool_event_to_specs(event: dict[str, Any]) -> list[ObservationSpec]:
    session_id = str(event.get("session_id", "")).strip()
    if not session_id:
        return []
    project_id = str(event.get("project_id", "")).strip()

    tool_name = str(event.get("tool_name", "")).strip() or "unknown"
    tool_input = event.get("tool_input", {})
    if not isinstance(tool_input, dict):
        tool_input = {}

    source_ref = tool_name
    file_paths = _extract_tool_paths(tool_input)
    specs: list[ObservationSpec] = []

    if file_paths and tool_name in {"Read", "Edit", "Write", "MultiEdit"}:
        for file_path in file_paths:
            specs.append(
                ObservationSpec(
                    session_id=session_id,
                    project_id=project_id,
                    source_kind="tool_event",
                    source_ref=source_ref,
                    observation_kind="file_fact",
                    summary=f"{_tool_verb(tool_name)}: {file_path}",
                    confidence=0.8,
                    tags=[tool_name.lower()],
                    file_paths=[file_path],
                    links=[("file_path", file_path, 1.0)],
                )
            )

    output_text = _to_text(event.get("tool_output", ""))
    if output_text and _WARNING_RE.search(output_text):
        specs.append(
            ObservationSpec(
                session_id=session_id,
                project_id=project_id,
                source_kind="tool_event",
                source_ref=source_ref,
                observation_kind="warning",
                summary=_shorten(output_text, 220),
                confidence=0.5,
                tags=[tool_name.lower(), "tool_warning"],
                file_paths=file_paths,
                links=[("file_path", path, 0.5) for path in file_paths],
            )
        )

    return _dedupe_specs(specs)


def load_json_file(path_str: str) -> dict[str, Any]:
    path = Path(path_str)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def load_latest_handoff_summary() -> Optional[dict[str, str]]:
    files = get_handoff_files()
    if not files:
        return None

    latest = files[0]
    doc = parse_handoff(latest)
    primary_task = _collapse_whitespace(doc.metadata.get("primary_task", ""))
    if primary_task and primary_task != "Unknown":
        summary = primary_task
    else:
        summary = _first_meaningful_line(doc.content)

    if not summary:
        summary = latest.name

    return {
        "path": str(latest.resolve()),
        "title": latest.name,
        "summary": _shorten(summary, 240),
    }


def legacy_artifacts_to_specs(
    *,
    project_id: str = "",
    decision_log_path: str = "",
    context_pack_path: str = "",
    return_ticket_path: str = "",
) -> list[ObservationSpec]:
    decision_log = load_json_file(decision_log_path) if decision_log_path else {}
    context_pack = load_json_file(context_pack_path) if context_pack_path else {}
    return_ticket = load_json_file(return_ticket_path) if return_ticket_path else {}

    session_id = _resolve_artifact_session_id(decision_log, context_pack, return_ticket)
    if not session_id:
        return []

    goal = _collapse_whitespace(
        context_pack.get("goal", "")
        or _nested_get(return_ticket, "headers", "control", "goal", default="")
    )
    assistant_summary = _collapse_whitespace(decision_log.get("assistant_summary", ""))
    key_files = _canonical_file_paths(
        context_pack.get("key_files", []) or decision_log.get("self_impl_files", [])
    )
    warning_values = _string_list(
        decision_log.get("warnings", []),
        _nested_get(return_ticket, "next_task_context", "warnings", default=[]),
        return_ticket.get("unresolved", []),
    )
    open_questions = _string_list(context_pack.get("open_questions", []))

    specs: list[ObservationSpec] = []
    if goal:
        specs.append(
            ObservationSpec(
                session_id=session_id,
                project_id=project_id,
                source_kind="context_pack",
                source_ref=context_pack_path or return_ticket_path,
                observation_kind="decision",
                summary=goal,
                confidence=1.0,
                tags=["goal"],
                file_paths=key_files,
                links=_artifact_links(
                    decision_log_path=decision_log_path,
                    context_pack_path=context_pack_path,
                    return_ticket_path=return_ticket_path,
                    file_paths=key_files,
                ),
            )
        )

    if assistant_summary and assistant_summary != goal:
        specs.append(
            ObservationSpec(
                session_id=session_id,
                project_id=project_id,
                source_kind="decision_log",
                source_ref=decision_log_path,
                observation_kind="decision",
                summary=assistant_summary,
                confidence=1.0,
                tags=["assistant_summary"],
                file_paths=key_files,
                links=_artifact_links(
                    decision_log_path=decision_log_path,
                    return_ticket_path=return_ticket_path,
                    file_paths=key_files,
                ),
            )
        )

    for warning in warning_values:
        specs.append(
            ObservationSpec(
                session_id=session_id,
                project_id=project_id,
                source_kind="return_ticket",
                source_ref=return_ticket_path or decision_log_path,
                observation_kind="constraint",
                summary=warning,
                confidence=1.0,
                tags=["warning"],
                file_paths=key_files,
                links=_artifact_links(
                    decision_log_path=decision_log_path,
                    return_ticket_path=return_ticket_path,
                    file_paths=key_files,
                ),
            )
        )

    for question in open_questions:
        specs.append(
            ObservationSpec(
                session_id=session_id,
                project_id=project_id,
                source_kind="context_pack",
                source_ref=context_pack_path,
                observation_kind="todo",
                summary=question,
                confidence=1.0,
                tags=["open_question"],
                file_paths=key_files,
                links=_artifact_links(
                    context_pack_path=context_pack_path,
                    decision_log_path=decision_log_path,
                    file_paths=key_files,
                ),
            )
        )

    for file_path in key_files:
        specs.append(
            ObservationSpec(
                session_id=session_id,
                project_id=project_id,
                source_kind="context_pack",
                source_ref=context_pack_path or decision_log_path,
                observation_kind="file_fact",
                summary=f"Touched file: {file_path}",
                confidence=1.0,
                tags=["touched_file"],
                file_paths=[file_path],
                links=_artifact_links(
                    context_pack_path=context_pack_path,
                    decision_log_path=decision_log_path,
                    file_paths=[file_path],
                ),
            )
        )

    handoff = load_latest_handoff_summary()
    if handoff:
        specs.append(
            ObservationSpec(
                session_id=session_id,
                project_id=project_id,
                source_kind="handoff",
                source_ref=handoff["path"],
                observation_kind="handoff",
                summary=handoff["summary"],
                confidence=0.8,
                tags=["latest_handoff"],
                links=[("handoff_path", handoff["path"], 1.0)],
            )
        )

    return _dedupe_specs(specs)


def load_active_pinakas_items(limit: int = 8) -> list[dict[str, Any]]:
    if yaml is None:
        return []

    items: list[dict[str, Any]] = []
    for board_name, filename, active_statuses in _PINAKAS_BOARDS:
        board_path = PINAKAS_DIR / filename
        try:
            payload = yaml.safe_load(board_path.read_text(encoding="utf-8")) or {}
        except (FileNotFoundError, OSError):
            continue
        entries = payload.get("items", [])
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            status = str(entry.get("status", "")).strip()
            if status not in active_statuses:
                continue
            text = _collapse_whitespace(
                str(entry.get("text", "") or entry.get("title", "")).strip()
            )
            if not text:
                continue
            items.append(
                {
                    "board": board_name,
                    "id": str(entry.get("id", "")).strip(),
                    "text": text,
                    "status": status,
                    "priority": str(entry.get("priority", "")).strip().lower(),
                    "tags": [str(tag).strip() for tag in entry.get("tags", []) if str(tag).strip()],
                    "path": str(entry.get("path", "")).strip(),
                    "target": str(entry.get("target", "")).strip(),
                    "related_wb": str(entry.get("related_wb", "")).strip(),
                }
            )

    items.sort(
        key=lambda item: (
            _PRIORITY_RANK.get(item.get("priority", ""), 3),
            item.get("board", ""),
            item.get("id", ""),
        )
    )
    return items[:limit]


def matching_pinakas_items(file_path: str, limit: int = 3) -> list[dict[str, Any]]:
    target_path = str(Path(file_path).resolve(strict=False))
    target_name = Path(target_path).name.lower()
    matched: list[dict[str, Any]] = []
    for item in load_active_pinakas_items(limit=32):
        haystacks = [
            item.get("text", ""),
            item.get("path", ""),
            item.get("target", ""),
            item.get("related_wb", ""),
        ]
        joined = " ".join(haystacks).lower()
        if target_path.lower() in joined or target_name in joined:
            matched.append(item)
        if len(matched) >= limit:
            break
    return matched


def ingest_specs(store: Any, specs: list[ObservationSpec]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        row = store.upsert_observation(
            session_id=spec.session_id,
            project_id=spec.project_id,
            source_kind=spec.source_kind,
            source_ref=spec.source_ref,
            observation_kind=spec.observation_kind,
            summary=spec.summary,
            confidence=spec.confidence,
            tags=spec.tags,
            file_paths=spec.file_paths,
        )
        for link_type, link_ref, weight in spec.links:
            if link_ref:
                store.add_observation_link(
                    observation_id=row["id"],
                    link_type=link_type,
                    link_ref=link_ref,
                    weight=weight,
                )
        rows.append(row)
    return rows


def build_boot_packet(
    store: Any,
    session_id: str,
    *,
    project_id: str = "",
    previous_session_id: str = "",
) -> tuple[str, list[str]]:
    recent_decisions = _scoped_recent(
        store,
        limit=10,
        min_confidence=AUTO_INJECT_THRESHOLD,
        kinds=["decision"],
        project_id=project_id,
        previous_session_id=previous_session_id,
    )
    prev_goal = (
        next(
            (
                obs for obs in recent_decisions
                if "goal" in obs.get("tags", []) and obs.get("session_id") == previous_session_id
            ),
            None,
        )
        if previous_session_id
        else None
    )
    recent_project_goal = (
        None
        if prev_goal
        else next((obs for obs in recent_decisions if "goal" in obs.get("tags", [])), None)
    )
    decision_lines = [
        _shorten(obs["summary"], 180)
        for obs in recent_decisions
        if obs["id"] not in {(prev_goal or {}).get("id"), (recent_project_goal or {}).get("id")}
    ][:2]

    warnings = _scoped_recent(
        store,
        limit=4,
        min_confidence=AUTO_INJECT_THRESHOLD,
        kinds=["constraint", "warning"],
        project_id=project_id,
        previous_session_id=previous_session_id,
    )
    warning_lines = [_shorten(obs["summary"], 160) for obs in warnings[:3]]

    file_facts = _scoped_recent(
        store,
        limit=12,
        min_confidence=AUTO_INJECT_THRESHOLD,
        kinds=["file_fact"],
        project_id=project_id,
        previous_session_id=previous_session_id,
    )
    touched_files = _unique_preserve(
        path
        for obs in file_facts
        for path in obs.get("file_paths", [])
    )[:5]

    previous_handoff = _first_scoped_handoff(
        store,
        project_id=project_id,
        previous_session_id=previous_session_id,
    )
    recent_project_handoff = None
    if not previous_handoff:
        recent_handoffs = _scoped_recent(
            store,
            limit=2,
            min_confidence=AUTO_INJECT_THRESHOLD,
            kinds=["handoff"],
            project_id=project_id,
        )
        recent_project_handoff = recent_handoffs[0] if recent_handoffs else None

    top_observations = [
        obs
        for obs in _scoped_recent(
            store,
            limit=12,
            min_confidence=AUTO_INJECT_THRESHOLD,
            project_id=project_id,
            previous_session_id=previous_session_id,
        )
        if obs["observation_kind"] not in {"decision", "constraint", "warning", "file_fact", "handoff"}
    ][:3]

    sections = [
        ("prev_goal", [prev_goal["summary"]] if prev_goal else [], [prev_goal["id"]] if prev_goal else []),
        ("recent_project_goal", [recent_project_goal["summary"]] if recent_project_goal else [], [recent_project_goal["id"]] if recent_project_goal else []),
        (
            "latest_decisions",
            decision_lines,
            [
                obs["id"]
                for obs in recent_decisions
                if obs["id"] not in {(prev_goal or {}).get("id"), (recent_project_goal or {}).get("id")}
            ][:2],
        ),
        ("active_warnings", warning_lines, [obs["id"] for obs in warnings[:3]]),
        ("touched_files", touched_files, [obs["id"] for obs in file_facts[:5]]),
        ("active_pinakas", [_render_pinakas_item(item) for item in load_active_pinakas_items(limit=5)], []),
        (
            "previous_session_handoff",
            [previous_handoff["summary"]] if previous_handoff else [],
            [previous_handoff["id"]] if previous_handoff else [],
        ),
        (
            "recent_project_handoff",
            [recent_project_handoff["summary"]] if recent_project_handoff else [],
            [recent_project_handoff["id"]] if recent_project_handoff else [],
        ),
        ("top_observations", [_shorten(obs["summary"], 150) for obs in top_observations], [obs["id"] for obs in top_observations]),
    ]
    return _render_sections(sections, BOOT_PACKET_LIMIT)


def build_file_packet(
    store: Any,
    session_id: str,
    file_path: str,
    *,
    project_id: str = "",
    previous_session_id: str = "",
) -> tuple[str, list[str]]:
    canonical_path = str(Path(file_path).expanduser().resolve(strict=False))
    file_observations = store.get_linked_observations(
        link_type="file_path",
        link_ref=canonical_path,
        limit=4,
        min_confidence=AUTO_INJECT_THRESHOLD,
        kinds=["file_fact", "warning"],
        project_id=project_id or None,
    )
    decision_obs = store.get_linked_observations(
        link_type="file_path",
        link_ref=canonical_path,
        limit=2,
        min_confidence=AUTO_INJECT_THRESHOLD,
        kinds=["decision"],
        project_id=project_id or None,
    )
    handoff_obs = []
    if previous_session_id:
        handoff_obs = store.get_recent_observations(
            limit=1,
            min_confidence=AUTO_INJECT_THRESHOLD,
            kinds=["handoff"],
            session_id=previous_session_id,
            project_id=project_id or None,
        )
    pinakas_items = matching_pinakas_items(canonical_path, limit=3)

    sections = [
        ("file_observations", [_shorten(obs["summary"], 150) for obs in file_observations[:3]], [obs["id"] for obs in file_observations[:3]]),
        ("related_decision", [_shorten(obs["summary"], 150) for obs in decision_obs[:1]], [obs["id"] for obs in decision_obs[:1]]),
        ("previous_session_handoff", [_shorten(obs["summary"], 150) for obs in handoff_obs[:1]], [obs["id"] for obs in handoff_obs[:1]]),
        ("related_pinakas", [_render_pinakas_item(item) for item in pinakas_items], []),
    ]
    return _render_sections(sections, FILE_PACKET_LIMIT)


def _scoped_recent(
    store: Any,
    *,
    limit: int,
    min_confidence: float,
    kinds: Optional[list[str]] = None,
    project_id: str = "",
    previous_session_id: str = "",
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    if previous_session_id:
        rows.extend(
            store.get_recent_observations(
                limit=limit,
                min_confidence=min_confidence,
                kinds=kinds,
                session_id=previous_session_id,
                project_id=project_id or None,
            )
        )
    if project_id:
        rows.extend(
            store.get_recent_observations(
                limit=max(limit * 2, limit),
                min_confidence=min_confidence,
                kinds=kinds,
                project_id=project_id,
            )
        )
    elif not previous_session_id:
        rows.extend(
            store.get_recent_observations(
                limit=limit,
                min_confidence=min_confidence,
                kinds=kinds,
            )
        )
    scoped: list[dict[str, Any]] = []
    for row in rows:
        row_id = str(row.get("id", "")).strip()
        if row_id and row_id in seen:
            continue
        if row_id:
            seen.add(row_id)
        scoped.append(row)
        if len(scoped) >= limit:
            break
    return scoped


def _first_scoped_handoff(
    store: Any,
    *,
    project_id: str = "",
    previous_session_id: str = "",
) -> Optional[dict[str, Any]]:
    if previous_session_id:
        handoffs = store.get_recent_observations(
            limit=1,
            min_confidence=AUTO_INJECT_THRESHOLD,
            kinds=["handoff"],
            session_id=previous_session_id,
            project_id=project_id or None,
        )
        if handoffs:
            return handoffs[0]
    return None


def _dedupe_specs(specs: list[ObservationSpec]) -> list[ObservationSpec]:
    deduped: list[ObservationSpec] = []
    seen: set[tuple[str, str, str, str]] = set()
    for spec in specs:
        signature = (
            spec.session_id,
            spec.observation_kind,
            spec.source_ref,
            _collapse_whitespace(spec.summary),
        )
        if signature in seen or not spec.summary:
            continue
        seen.add(signature)
        spec.file_paths = _canonical_file_paths(spec.file_paths)
        deduped.append(spec)
    return deduped


def _resolve_artifact_session_id(
    decision_log: dict[str, Any],
    context_pack: dict[str, Any],
    return_ticket: dict[str, Any],
) -> str:
    candidates = [
        decision_log.get("session_id", ""),
        context_pack.get("session_id", ""),
        str(return_ticket.get("task_id", "")).replace("session-", "", 1),
    ]
    for candidate in candidates:
        text = str(candidate or "").strip()
        if text:
            return text
    return ""


def _string_list(*values: Any) -> list[str]:
    result: list[str] = []
    for value in values:
        if isinstance(value, list):
            for item in value:
                text = _collapse_whitespace(str(item))
                if text:
                    result.append(text)
        elif isinstance(value, str):
            text = _collapse_whitespace(value)
            if text:
                result.append(text)
    return _unique_preserve(result)


def _artifact_links(
    *,
    decision_log_path: str = "",
    context_pack_path: str = "",
    return_ticket_path: str = "",
    file_paths: Optional[list[str]] = None,
) -> list[tuple[str, str, float]]:
    links: list[tuple[str, str, float]] = []
    if decision_log_path:
        links.append(("decision_log", decision_log_path, 1.0))
    if context_pack_path:
        links.append(("context_pack", context_pack_path, 1.0))
    if return_ticket_path:
        links.append(("return_ticket", return_ticket_path, 1.0))
    for file_path in _canonical_file_paths(file_paths or []):
        links.append(("file_path", file_path, 1.0))
    return links


def _first_meaningful_line(text: str) -> str:
    for line in text.splitlines():
        clean = _collapse_whitespace(line)
        if clean and not clean.startswith("#"):
            return clean
    return ""


def _nested_get(payload: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def _render_pinakas_item(item: dict[str, Any]) -> str:
    item_id = item.get("id", "")
    board = item.get("board", "")
    priority = item.get("priority", "")
    text = item.get("text", "")
    prefix = f"{item_id} {board}"
    if priority:
        prefix += f" [{priority}]"
    return _shorten(f"{prefix}: {text}", 150)


def _render_sections(
    sections: list[tuple[str, list[str], list[str]]],
    limit: int,
) -> tuple[str, list[str]]:
    rendered_parts: list[str] = []
    observation_ids: list[str] = []
    for key, lines, ids in sections:
        block = _render_block(key, lines)
        if not block:
            continue
        candidate_parts = rendered_parts + [block]
        candidate = "\n\n".join(candidate_parts)
        if len(candidate) <= limit:
            rendered_parts = candidate_parts
            observation_ids.extend(ids)
            continue

        trimmed = _fit_block(key, lines, limit - len("\n\n".join(rendered_parts)) - (2 if rendered_parts else 0))
        if trimmed:
            rendered_parts.append(trimmed)
            observation_ids.extend(ids)
        break
    return "\n\n".join(rendered_parts), _unique_preserve(observation_ids)


def _render_block(key: str, lines: list[str]) -> str:
    normalized = [_collapse_whitespace(line) for line in lines if _collapse_whitespace(line)]
    if not normalized:
        return ""
    if len(normalized) == 1:
        return f"{key}: {normalized[0]}"
    bullets = "\n".join(f"- {line}" for line in normalized)
    return f"{key}:\n{bullets}"


def _fit_block(key: str, lines: list[str], available: int) -> str:
    if available <= len(key) + 3:
        return ""
    trimmed_lines: list[str] = []
    for line in lines:
        candidate = _render_block(key, trimmed_lines + [line])
        if len(candidate) > available:
            if not trimmed_lines:
                if available < len(key) + 10:
                    return ""
                return f"{key}: {_shorten(line, max(available - len(key) - 2, 8))}"
            break
        trimmed_lines.append(line)
    return _render_block(key, trimmed_lines)


def _unique_preserve(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result
