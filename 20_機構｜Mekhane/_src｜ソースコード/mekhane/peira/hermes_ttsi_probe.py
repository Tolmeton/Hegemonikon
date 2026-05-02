#!/usr/bin/env python3
# PROOF: [L2/実験] <- Hermes procedural memory を HGK TT-SI 候補へ写せるかの打診が必要→shadow probe が担う
"""
Hermes → HGK TT-SI Shadow Probe

実 Hermes skill (`~/.hermes/skills/**/SKILL.md`) を読み取り、
HGK の TT-SI 三面 (`patterns`, `values`, `learned_A`) に対する
shadow update candidate を生成する。

設計原則:
  - Doxa=状態 と Mneme=永続化の分離を壊さない
  - SOURCE/TAINT を厳格に区別する
  - live write ではなく shadow write で full write path を検証する
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from mekhane.paths import ARTIFACTS_DIR, HGK_ROOT, LEARNED_A_PATH, STATE_RUNTIME

DEFAULT_HERMES_HOME = Path.home() / ".hermes"
DEFAULT_VALUES_PATH = STATE_RUNTIME / "values.json"
DEFAULT_PATTERNS_TEMPLATE = (
    HGK_ROOT
    / "20_機構｜Mekhane"
    / "_src｜ソースコード"
    / "mekhane"
    / "synteleia"
    / "poiesis"
    / "patterns.yaml"
)
DEFAULT_A_FALLBACK = (
    HGK_ROOT
    / "30_記憶｜Mneme"
    / "04_知識｜Gnosis"
    / "01_文献｜Literature"
    / "fep"
    / "endurance_A.npy"
)
MAX_VALUE_DELTA = 0.05

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+(.*\S)\s*$")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]+")

TRIGGER_HEADINGS = ("trigger", "when to use", "use when", "activation", "発動", "トリガー")
STEP_HEADINGS = ("steps", "workflow", "instructions", "how to use", "usage", "手順", "使い方")
GUARDRAIL_HEADINGS = ("guardrails", "not for", "warning", "caution", "avoid", "禁止", "注意")
GUARDRAIL_RE = re.compile(
    r"(?:\bdo not\b|\bdon't\b|\bavoid\b|\bnever\b|\bnot for\b|禁止|避け|注意)",
    re.IGNORECASE,
)

VALUE_SIGNAL_MAP: dict[tuple[str, str], tuple[str, ...]] = {
    ("core_principles", "zero_entropy"): (
        "clarify",
        "clarity",
        "question",
        "resolve ambiguity",
        "ambigu",
        "spec",
        "exact",
        "precision",
    ),
    ("core_principles", "hyperengineering"): (
        "agent",
        "automation",
        "workflow",
        "tool",
        "integrat",
        "orchestrat",
        "system",
        "infrastructure",
    ),
    ("core_principles", "japanese_first"): (
        "japanese",
        "日本語",
    ),
    ("development_priorities", "test_before_commit"): (
        "test",
        "verify",
        "validation",
        "assert",
        "check",
        "benchmark",
    ),
    ("development_priorities", "incremental_changes"): (
        "incremental",
        "iterative",
        "small",
        "step by step",
        "iterate",
        "gradual",
    ),
    ("development_priorities", "document_decisions"): (
        "document",
        "record",
        "log",
        "decision",
        "artifact",
        "report",
        "write down",
    ),
}


@dataclass(slots=True)
class HermesSkillSnapshot:
    skill_id: str
    source_path: str
    title: str
    summary: str
    trigger_text: str
    steps: list[str]
    guardrails: list[str]
    raw_text_hash: str


@dataclass(slots=True)
class PatternCandidate:
    id: str
    source: str
    trigger: str
    action_summary: str
    procedure_steps: list[str]
    confidence: float
    evidence_path: str
    guardrails: list[str]


@dataclass(slots=True)
class ValueDelta:
    group: str
    key: str
    old_weight: float
    delta: float
    new_weight: float
    rationale: str


@dataclass(slots=True)
class AMatrixPatch:
    strategy: str
    target_shape: list[int]
    deltas: list[dict[str, Any]]
    reason: str


@dataclass(slots=True)
class SkillBundle:
    skill_id: str
    patterns_candidates: list[PatternCandidate]
    values_deltas: list[ValueDelta]
    a_matrix_patch: AMatrixPatch
    gate_decision: str
    blocked_reasons: list[str]
    evidence: list[str]


@dataclass(slots=True)
class ProbeRun:
    started_at: str
    hermes_home: str
    skills_found: int
    skills_mapped: int
    gate_pass_count: int
    gate_block_count: int
    values_keys_touched: int
    a_patch_nonzero_count: int
    shadow_write_success: bool
    exit_code: int
    bundle_count: int
    bundles: list[SkillBundle]
    shadow_root: str
    report_path: str
    manifest_path: str
    patterns_path: str
    values_path: str
    learned_a_path: str
    live_targets: dict[str, str | None]


def _normalize_heading(text: str) -> str:
    return text.strip().lower()


def _extract_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"__root__": []}
    current = "__root__"
    for line in text.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            current = _normalize_heading(heading.group(2))
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line.rstrip())
    return sections


def _find_first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            return match.group(2).strip()
    return fallback


def _extract_paragraph(lines: list[str]) -> str:
    paragraph: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            if paragraph:
                break
            continue
        if LIST_ITEM_RE.match(line):
            if paragraph:
                break
            continue
        paragraph.append(line)
    return " ".join(paragraph).strip()


def _extract_list_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    for raw in lines:
        match = LIST_ITEM_RE.match(raw)
        if match:
            items.append(match.group(1).strip())
    return items


def _first_nonempty(items: list[str], fallback: str = "") -> str:
    for item in items:
        if item.strip():
            return item.strip()
    return fallback


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique


def _slugify(text: str) -> str:
    words = WORD_RE.findall(text.lower())
    return "-".join(words[:8]) or "hermes-skill"


def discover_skill_paths(hermes_home: Path) -> list[Path]:
    skills_root = hermes_home / "skills"
    if not skills_root.is_dir():
        return []
    return sorted(skills_root.glob("**/SKILL.md"))


def parse_hermes_skill(path: Path) -> HermesSkillSnapshot:
    text = path.read_text(encoding="utf-8", errors="replace")
    sections = _extract_sections(text)
    title = _find_first_heading(text, path.parent.name)

    summary = _extract_paragraph(sections.get("__root__", []))
    if not summary:
        for heading, lines in sections.items():
            if heading != "__root__":
                summary = _extract_paragraph(lines)
                if summary:
                    break
    if not summary:
        summary = title

    trigger_candidates: list[str] = []
    step_candidates: list[str] = []
    guardrail_candidates: list[str] = []

    for heading, lines in sections.items():
        normalized = _normalize_heading(heading)
        list_items = _extract_list_items(lines)
        paragraph = _extract_paragraph(lines)
        if normalized != "__root__":
            if any(token in normalized for token in TRIGGER_HEADINGS):
                trigger_candidates.extend(list_items or ([paragraph] if paragraph else []))
            if any(token in normalized for token in STEP_HEADINGS):
                step_candidates.extend(list_items)
            if any(token in normalized for token in GUARDRAIL_HEADINGS):
                guardrail_candidates.extend(list_items or ([paragraph] if paragraph else []))

        for raw in lines:
            line = raw.strip()
            if not line:
                continue
            if GUARDRAIL_RE.search(line):
                if LIST_ITEM_RE.match(line):
                    guardrail_candidates.append(LIST_ITEM_RE.match(line).group(1).strip())
                else:
                    guardrail_candidates.append(line)

    if not step_candidates:
        step_candidates = _extract_list_items(sum(sections.values(), []))
    if not trigger_candidates:
        trigger_candidates = [summary]
    if not guardrail_candidates:
        guardrail_candidates = []

    skill_id = _slugify(path.parent.name or title)
    raw_text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return HermesSkillSnapshot(
        skill_id=skill_id,
        source_path=str(path),
        title=title,
        summary=summary,
        trigger_text=_first_nonempty(_dedupe_preserve_order(trigger_candidates), summary),
        steps=_dedupe_preserve_order(step_candidates)[:8],
        guardrails=_dedupe_preserve_order(guardrail_candidates)[:8],
        raw_text_hash=raw_text_hash,
    )


def _pattern_confidence(snapshot: HermesSkillSnapshot) -> float:
    confidence = 0.55
    if snapshot.trigger_text and snapshot.trigger_text != snapshot.summary:
        confidence += 0.1
    if snapshot.steps:
        confidence += 0.15
    if snapshot.guardrails:
        confidence += 0.05
    if len(snapshot.summary.split()) >= 6:
        confidence += 0.05
    return round(min(confidence, 0.95), 2)


def build_pattern_candidates(snapshot: HermesSkillSnapshot) -> list[PatternCandidate]:
    if not snapshot.summary:
        return []
    return [
        PatternCandidate(
            id=snapshot.skill_id,
            source="hermes_skill",
            trigger=snapshot.trigger_text,
            action_summary=snapshot.summary,
            procedure_steps=snapshot.steps,
            confidence=_pattern_confidence(snapshot),
            evidence_path=snapshot.source_path,
            guardrails=snapshot.guardrails,
        )
    ]


def _flatten_value_entries(values_doc: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    entries: dict[tuple[str, str], dict[str, Any]] = {}
    values = values_doc.get("values", {})
    for group, group_items in values.items():
        if not isinstance(group_items, dict):
            continue
        for key, item in group_items.items():
            if isinstance(item, dict) and "weight" in item:
                entries[(group, key)] = item
    return entries


def _snapshot_text(snapshot: HermesSkillSnapshot) -> str:
    parts = [snapshot.title, snapshot.summary, snapshot.trigger_text]
    parts.extend(snapshot.steps)
    parts.extend(snapshot.guardrails)
    return "\n".join(parts).lower()


def build_value_deltas(
    snapshot: HermesSkillSnapshot,
    values_doc: dict[str, Any],
) -> list[ValueDelta]:
    text = _snapshot_text(snapshot)
    entries = _flatten_value_entries(values_doc)
    deltas: list[ValueDelta] = []

    for key_path, keywords in VALUE_SIGNAL_MAP.items():
        live_entry = entries.get(key_path)
        if not live_entry:
            continue

        hits = 0
        matched: list[str] = []
        for keyword in keywords:
            if keyword in text:
                hits += text.count(keyword)
                matched.append(keyword)
        if hits <= 0:
            continue

        delta = min(MAX_VALUE_DELTA, 0.01 * hits)
        old_weight = float(live_entry["weight"])
        new_weight = round(max(0.0, min(1.0, old_weight + delta)), 4)
        applied_delta = round(new_weight - old_weight, 4)
        if applied_delta == 0.0:
            continue

        deltas.append(
            ValueDelta(
                group=key_path[0],
                key=key_path[1],
                old_weight=old_weight,
                delta=applied_delta,
                new_weight=new_weight,
                rationale=f"Hermes skill signal matched keywords: {', '.join(sorted(set(matched)))}",
            )
        )
    return deltas


def load_values_document(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def aggregate_value_deltas(bundles: list[SkillBundle]) -> dict[tuple[str, str], ValueDelta]:
    aggregated: dict[tuple[str, str], ValueDelta] = {}
    for bundle in bundles:
        for delta in bundle.values_deltas:
            key = (delta.group, delta.key)
            if key not in aggregated:
                aggregated[key] = ValueDelta(**asdict(delta))
                continue

            current = aggregated[key]
            new_delta = max(-MAX_VALUE_DELTA, min(MAX_VALUE_DELTA, current.delta + delta.delta))
            current.delta = round(new_delta, 4)
            current.new_weight = round(max(0.0, min(1.0, current.old_weight + current.delta)), 4)
            current.rationale = f"{current.rationale}; {delta.rationale}"
    return aggregated


def apply_value_deltas(
    values_doc: dict[str, Any],
    deltas: dict[tuple[str, str], ValueDelta],
) -> dict[str, Any]:
    updated = json.loads(json.dumps(values_doc))
    for (group, key), delta in deltas.items():
        updated["values"][group][key]["weight"] = delta.new_weight

    meta = updated.setdefault("meta", {})
    meta["last_updated"] = datetime.now().astimezone().isoformat(timespec="seconds")
    meta["update_count"] = int(meta.get("update_count", 0)) + 1
    meta["shadow_probe"] = {
        "surface": "values",
        "touched_keys": [f"{group}.{key}" for group, key in sorted(deltas.keys())],
    }
    return updated


def load_a_matrix(path: Path) -> tuple[np.ndarray, bool]:
    arr = np.load(path, allow_pickle=True)
    wrapped_object = False
    if arr.dtype == object and arr.shape == (1,):
        arr = arr.item()
        wrapped_object = True
    elif arr.dtype == object and arr.ndim == 3 and arr.shape[0] == 1:
        # Some object saves materialize as a singleton outer axis over the matrix payload.
        arr = arr[0]
        wrapped_object = True
    if not isinstance(arr, np.ndarray) or arr.ndim != 2:
        raise ValueError(f"A-matrix must be a 2D ndarray: {path}")
    return np.array(arr, dtype=np.float64, copy=True), wrapped_object


def build_a_patch(snapshot: HermesSkillSnapshot, matrix: np.ndarray) -> AMatrixPatch:
    reason = (
        "Hermes skill -> HGK A-matrix coordinate semantics are not locally grounded in SOURCE. "
        "Baseline is preserved unchanged."
    )
    return AMatrixPatch(
        strategy="preserve_baseline",
        target_shape=list(matrix.shape),
        deltas=[],
        reason=reason,
    )


def apply_a_patch(matrix: np.ndarray, patch: AMatrixPatch) -> np.ndarray:
    updated = matrix.copy()
    for delta in patch.deltas:
        row = int(delta["row"])
        col = int(delta["col"])
        updated[row, col] += float(delta["delta"])
    return updated


def write_a_matrix(path: Path, matrix: np.ndarray, wrapped_object: bool) -> None:
    if wrapped_object:
        payload = np.empty((1,), dtype=object)
        payload[0] = matrix
        np.save(path, payload, allow_pickle=True)
    else:
        np.save(path, matrix)


def build_skill_bundle(
    snapshot: HermesSkillSnapshot,
    values_doc: dict[str, Any],
    a_matrix: np.ndarray,
) -> SkillBundle:
    blocked: list[str] = []
    evidence = [snapshot.source_path, snapshot.raw_text_hash]

    patterns_candidates = build_pattern_candidates(snapshot)
    if not patterns_candidates:
        blocked.append("patterns:no_candidate")

    if not snapshot.steps:
        blocked.append("skill:no_procedure_steps")

    values_deltas = build_value_deltas(snapshot, values_doc)
    if not values_doc.get("values"):
        blocked.append("values:missing_schema")

    a_matrix_patch = build_a_patch(snapshot, a_matrix)
    if tuple(a_matrix_patch.target_shape) != tuple(a_matrix.shape):
        blocked.append("learned_A:shape_mismatch")

    gate = "shadow_pass" if not blocked else "blocked"
    return SkillBundle(
        skill_id=snapshot.skill_id,
        patterns_candidates=patterns_candidates,
        values_deltas=values_deltas,
        a_matrix_patch=a_matrix_patch,
        gate_decision=gate,
        blocked_reasons=blocked,
        evidence=evidence,
    )


def _candidate_to_dict(candidate: PatternCandidate) -> dict[str, Any]:
    return asdict(candidate)


def _bundle_to_dict(bundle: SkillBundle) -> dict[str, Any]:
    return {
        "skill_id": bundle.skill_id,
        "patterns_candidates": [_candidate_to_dict(item) for item in bundle.patterns_candidates],
        "values_deltas": [asdict(item) for item in bundle.values_deltas],
        "a_matrix_patch": asdict(bundle.a_matrix_patch),
        "gate_decision": bundle.gate_decision,
        "blocked_reasons": bundle.blocked_reasons,
        "evidence": bundle.evidence,
    }


def _default_report_stem() -> str:
    return f"pei_hermes_ttsi_probe_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def resolve_output_paths(report: Path | None, shadow_root: Path | None) -> tuple[Path, Path]:
    if report is None and shadow_root is None:
        stem = _default_report_stem()
        report = ARTIFACTS_DIR / f"{stem}.md"
        shadow_root = ARTIFACTS_DIR / stem
        return report, shadow_root

    if report is not None and shadow_root is None:
        stem = report.stem or _default_report_stem()
        return report, report.parent / stem

    if report is None and shadow_root is not None:
        return shadow_root.parent / f"{shadow_root.name}.md", shadow_root

    return report, shadow_root


def _resolve_a_base(explicit: Path | None) -> Path:
    candidates = [explicit, LEARNED_A_PATH, DEFAULT_A_FALLBACK]
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate
    raise FileNotFoundError("No A-matrix baseline found. Pass --a-base explicitly.")


def _load_patterns_template(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write_patterns_shadow(path: Path, bundles: list[SkillBundle], template_path: Path) -> dict[str, Any]:
    _load_patterns_template(template_path)
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": "hermes_skill_probe",
        "schema_mode": "candidate_shadow",
        "candidates": [
            _candidate_to_dict(item)
            for bundle in bundles
            if bundle.gate_decision == "shadow_pass"
            for item in bundle.patterns_candidates
        ],
    }
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return payload


def _render_report(
    run: ProbeRun,
    bundles: list[SkillBundle],
    patterns_shadow: dict[str, Any],
) -> str:
    verdict = "支持" if run.exit_code == 0 else "保留/棄却"
    blocked_lines = [
        f"- `{bundle.skill_id}`: {', '.join(bundle.blocked_reasons)}"
        for bundle in bundles
        if bundle.blocked_reasons
    ] or ["- なし"]

    pass_lines = [
        f"- `{bundle.skill_id}` → pattern={len(bundle.patterns_candidates)} / "
        f"values={len(bundle.values_deltas)} / a_strategy={bundle.a_matrix_patch.strategy}"
        for bundle in bundles
        if bundle.gate_decision == "shadow_pass"
    ] or ["- なし"]

    return "\n".join(
        [
            "═══ [Hegemonikón] V07 Peira v7.0 完了 ═══",
            "📋テーマ: Hermes skill/self-improvement → HGK TT-SI shadow probe",
            "",
            "━━━ P-0: Prolegomena (前限定) ━━━",
            f"実験空間: real Hermes skills only (`{Path(run.hermes_home) / 'skills'}`) を入力にし、"
            "TT-SI triad (`patterns`, `values`, `learned_A`) の shadow write path を検証する。",
            "最高リスクカテゴリ: Doxa/Mneme 境界崩壊",
            "",
            "━━━ P-1: Experiment Protocol Design ━━━",
            "仮説: 1件以上の Hermes skill を procedural residue として取り込み、"
            "live write を行わずに shadow bundle へ変換できる。",
            "反証条件: すべての skill が gate block される、または triad のいずれかが schema failure になる。",
            "",
            "━━━ P-2: MVP Design ━━━",
            f"対象 skill 数: {run.skills_found}",
            f"pass skill 数: {run.gate_pass_count}",
            f"values touched: {run.values_keys_touched}",
            f"A patch nonzero count: {run.a_patch_nonzero_count}",
            "",
            "━━━ P-3: Execution ━━━",
            f"- shadow root: `{run.shadow_root}`",
            f"- patterns shadow: `{run.patterns_path}` ({len(patterns_shadow['candidates'])} candidates)",
            f"- values shadow: `{run.values_path}`",
            f"- learned_A shadow: `{run.learned_a_path}`",
            "",
            "━━━ P-4: Harvest ━━━",
            f"判定: **{verdict}**",
            "Pass bundles:",
            *pass_lines,
            "Blocked bundles:",
            *blocked_lines,
            "",
            "━━━ 結果 ━━━",
            f"📌判定: {verdict}",
            f"🔬gate_pass_count: {run.gate_pass_count}",
            f"🧠学び: Hermes procedural memory は HGK に対して Doxa 直結ではなく "
            "TT-SI update candidate として扱うのが安全。",
            f"🔀→次: {'/kat' if run.exit_code == 0 else '/noe or /ske'}",
            "",
            "━━━ WM ━━━",
            "$goal = real Hermes skills を HGK TT-SI triad へ shadow candidate 化する",
            "$constraints = source-over-memory, shadow-only, no live Doxa write",
            f"$decision = {'shadow pass を確認' if run.exit_code == 0 else 'gate block を確認'}",
            "$next = pass なら memory+skills 拡張、block なら mapping/gate を見直す",
            "═══════════════════════════════════════════",
            "",
        ]
    )


def _render_missing_input_report(hermes_home: Path) -> str:
    skills_root = hermes_home / "skills"
    return "\n".join(
        [
            "═══ [Hegemonikón] V07 Peira v7.0 完了 ═══",
            "📋テーマ: Hermes skill/self-improvement → HGK TT-SI shadow probe",
            "",
            "━━━ P-0: Prolegomena (前限定) ━━━",
            f"実験空間: real Hermes skills only (`{skills_root}`) を入力にし、"
            "TT-SI triad (`patterns`, `values`, `learned_A`) の shadow write path を検証する。",
            "最高リスクカテゴリ: missing_input",
            "",
            "━━━ P-1: Experiment Protocol Design ━━━",
            "仮説: 1件以上の Hermes skill を procedural residue として取り込み、"
            "live write を行わずに shadow bundle へ変換できる。",
            "反証条件: 入力 skill が 0 件で、real Hermes output only 条件を満たせない。",
            "",
            "━━━ P-2: MVP Design ━━━",
            "対象 skill 数: 0",
            "shadow write: 実行せず",
            "",
            "━━━ P-3: Execution ━━━",
            f"- missing input root: `{skills_root}`",
            "- shadow bundle: not written",
            "",
            "━━━ P-4: Harvest ━━━",
            "判定: **保留/棄却**",
            "理由: `missing_input`",
            "",
            "━━━ 結果 ━━━",
            "📌判定: 保留/棄却",
            "🔬gate_pass_count: 0",
            "🧠学び: 実入力を前提とする `/pei` は、source 不在時に mapping 妥当性を判定してはいけない。",
            "🔀→次: Hermes 側で `~/.hermes/skills/**/SKILL.md` を用意して再実行する。",
            "",
            "━━━ WM ━━━",
            "$goal = real Hermes skills を HGK TT-SI triad へ shadow candidate 化する",
            "$constraints = source-over-memory, shadow-only, real Hermes output only",
            "$decision = missing_input を確認。shadow write は停止",
            "$next = Hermes skill を1件以上配置して再試行",
            "═══════════════════════════════════════════",
            "",
        ]
    )


def run_probe(
    *,
    hermes_home: Path,
    shadow_root: Path,
    report_path: Path,
    values_live_path: Path,
    patterns_template_path: Path,
    a_base_path: Path,
    skill_limit: int | None = None,
) -> ProbeRun:
    skill_paths = discover_skill_paths(hermes_home)
    if skill_limit is not None:
        skill_paths = skill_paths[:skill_limit]
    if not skill_paths:
        raise FileNotFoundError(f"No Hermes skills found under {hermes_home / 'skills'}")

    values_doc = load_values_document(values_live_path)
    a_matrix, wrapped_object = load_a_matrix(a_base_path)

    snapshots = [parse_hermes_skill(path) for path in skill_paths]
    bundles = [build_skill_bundle(snapshot, values_doc, a_matrix) for snapshot in snapshots]
    pass_bundles = [bundle for bundle in bundles if bundle.gate_decision == "shadow_pass"]

    aggregated_values = aggregate_value_deltas(pass_bundles)
    updated_values_doc = apply_value_deltas(values_doc, aggregated_values)

    a_patch = AMatrixPatch(
        strategy="preserve_baseline",
        target_shape=list(a_matrix.shape),
        deltas=[],
        reason="No semantically grounded A-matrix deltas were observed from local SOURCE.",
    )
    updated_a_matrix = apply_a_patch(a_matrix, a_patch)

    shadow_root.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    patterns_path = shadow_root / "patterns.shadow.yaml"
    values_path = shadow_root / "values.shadow.json"
    learned_a_path = shadow_root / "learned_A.shadow.npy"
    manifest_path = shadow_root / "manifest.json"

    patterns_shadow = _write_patterns_shadow(patterns_path, bundles, patterns_template_path)
    values_path.write_text(
        json.dumps(updated_values_doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_a_matrix(learned_a_path, updated_a_matrix, wrapped_object)

    exit_code = 0 if pass_bundles else 1
    run = ProbeRun(
        started_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        hermes_home=str(hermes_home),
        skills_found=len(skill_paths),
        skills_mapped=len(snapshots),
        gate_pass_count=len(pass_bundles),
        gate_block_count=len(bundles) - len(pass_bundles),
        values_keys_touched=len(aggregated_values),
        a_patch_nonzero_count=len(a_patch.deltas),
        shadow_write_success=True,
        exit_code=exit_code,
        bundle_count=len(bundles),
        bundles=bundles,
        shadow_root=str(shadow_root),
        report_path=str(report_path),
        manifest_path=str(manifest_path),
        patterns_path=str(patterns_path),
        values_path=str(values_path),
        learned_a_path=str(learned_a_path),
        live_targets={
            "patterns": None,
            "values": str(values_live_path),
            "learned_A": str(a_base_path),
        },
    )

    manifest_path.write_text(
        json.dumps(
            {
                "run": asdict(run),
                "bundles": [_bundle_to_dict(bundle) for bundle in bundles],
                "aggregated_values": [asdict(delta) for delta in aggregated_values.values()],
                "a_patch": asdict(a_patch),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report_path.write_text(_render_report(run, bundles, patterns_shadow), encoding="utf-8")
    return run


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes skill → HGK TT-SI shadow probe")
    parser.add_argument(
        "--hermes-home",
        type=Path,
        default=DEFAULT_HERMES_HOME,
        help="Hermes home directory (default: ~/.hermes)",
    )
    parser.add_argument(
        "--shadow-root",
        type=Path,
        default=None,
        help="Shadow bundle output directory",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Markdown report output path",
    )
    parser.add_argument(
        "--values-live",
        type=Path,
        default=DEFAULT_VALUES_PATH,
        help="HGK live values.json path",
    )
    parser.add_argument(
        "--patterns-template",
        type=Path,
        default=DEFAULT_PATTERNS_TEMPLATE,
        help="Schema exemplar for patterns shadow generation",
    )
    parser.add_argument(
        "--a-base",
        type=Path,
        default=None,
        help="Baseline learned_A.npy path",
    )
    parser.add_argument(
        "--skill-limit",
        type=int,
        default=None,
        help="Only process the first N Hermes skills",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    report_path, shadow_root = resolve_output_paths(args.report, args.shadow_root)
    a_base_path = _resolve_a_base(args.a_base)

    try:
        run = run_probe(
            hermes_home=args.hermes_home,
            shadow_root=shadow_root,
            report_path=report_path,
            values_live_path=args.values_live,
            patterns_template_path=args.patterns_template,
            a_base_path=a_base_path,
            skill_limit=args.skill_limit,
        )
    except FileNotFoundError:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(_render_missing_input_report(args.hermes_home), encoding="utf-8")
        print(report_path)
        return 1

    print(report_path)
    return run.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
