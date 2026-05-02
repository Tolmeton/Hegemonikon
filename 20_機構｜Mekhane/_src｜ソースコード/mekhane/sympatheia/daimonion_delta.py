"""Daimonion δ Phase 1 E proxy calculator.

SOURCE:
- /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/sympatheia/docs/daimonion_delta_spec.md §4-7
- /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/sympatheia/docs/daimonion_delta_validation_sessions.md §3-6
- /home/makaron8426/.claude/hooks/audit-posttooluse.py (session/pattern log schema)
- /home/makaron8426/.claude/lib/transcript_utils.py (temporal keyword prior)

TAINT:
- assistant turn と tool log の対応は timestamp 優先だが、欠損時は順序近似にフォールバックする。
- session log の `input_preview` は切り詰められるため、`[pa]` と `[eu]` は低信頼の proxy を含む。
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Iterator, Mapping, Sequence

import yaml

JsonDict = dict[str, Any]
EvidenceList = list[JsonDict]

HOOKS_LOGS_DIR = Path(os.environ.get("CLAUDE_HOOK_LOG_DIR") or (Path.home() / ".claude" / "hooks" / "logs"))
CLAUDE_PROJECTS_DIR = (
    Path.home()
    / ".claude"
    / "projects"
    / "-home-makaron8426-Sync-oikos-01--------Hegemonikon"
)
HERMENEUS_LOG = Path.home() / ".hermeneus" / "logs" / "structured_outputs.jsonl"
THRESHOLDS_PATH = Path(__file__).with_name("daimonion_delta_thresholds.yaml")

CCL_PATTERN = re.compile(r"(?<![\w/])/[a-z]{3,4}[+\-]?(?![\w/])")
READ_TOOLS = {"Read", "Grep"}

DEFAULT_THRESHOLDS: JsonDict = {
    "version": 0.2,
    "thresholds": {
        # v0.2: 閾値厳格化 — validation_batch 10session で 7/10 飽和のため interval_zscore 2.0→2.5 / ratio 0.4→0.3
        "ek": {"interval_zscore": 2.5, "output_length_ratio_max": 0.3},
        "th": {"qualifier_per_100chars": 2.5, "self_correct_abs": 2},
        "ho": {
            "edit_without_read_per_turn": 0.2,
            "novel_write_without_read_abs": 3,
        },
        "ph": {"escape_vocab_per_100chars": 1.0, "abandonment_markers_abs": 1},
        # v0.2: 9/10 飽和のため run 閾値 3→5 / variance 閾値 0.3→0.5
        "pa": {"same_tool_arg_variation_abs": 5, "tool_hash_variance_min": 0.5},
        "he": {"ccl_prose_without_hermeneus_abs": 1},
        "an": {"non_anchored_refs_abs": 2, "max_reads_for_alert": 0},
        "eu": {
            "unsolicited_edit_ratio": 0.2,
            "micro_delta_char_max": 40,
            "micro_delta_line_min": 2,
        },
        "sh": {"early_summary_fraction": 0.33, "max_reads_for_alert": 2},
        # v0.2: 狭帯域 (0.19-0.26) 発火 0/10 のため閾値 0.8→0.6 + rebuttal 併発 turn を非迎合判定 (_score_tr)
        "tr": {"agreement_rate_min": 0.6, "rebuttal_abs_max": 0},
        # v0.2: [sy] は positive polarity。E_scores は保持するが alerts から除外。
        # absence (internal_markers=0 かつ text_turns≥absence_turn_min) を逆極性 alert として別扱い。
        "sy": {
            "polarity": "positive",
            "internal_markers_abs": 1,
            "absence_turn_min": 5,
            "absence_alert_threshold": 0.7,
        },
    },
    "alerts": {
        "default_threshold_score": 0.7,
        "absence_threshold_score": 0.7,
    },
    "vocabulary": {
        "th_uncertainty_markers": [
            "しかし",
            "ただし",
            "ところが",
            "ただ",
            "もっとも",
            "一方",
            "とはいえ",
            "場合による",
            "かもしれない",
            "おそらく",
        ],
        "ph_escape": [
            "現実的でない",
            "大きすぎる",
            "全件は",
            "長すぎる",
            "膨大",
            "網羅は困難",
            "全文読みは不要",
            "要約で十分",
            "困難",
            "後で",
            "次回に",
            "無理",
            "やりたくない",
            "手間",
        ],
        "ph_abandonment": ["やめます", "先延ばし", "断念", "諦めます"],
        "an_temporal": ["前に", "以前", "たぶん", "確か", "記憶では", "前セッション"],
        "tr_agreement": ["そうですね", "おっしゃる通り", "確かに", "良い指摘", "なるほど"],
        "tr_rebuttal_markers": ["しかし", "ただし", "ですが", "いいえ", "とはいえ"],
        "sy_internal": ["違和感", "感じる", "直感", "腑に落ちない", "気になる", "しっくりこない"],
        "sy_labels": ["[主観]", "📍", "🕳️", "→"],
        "ek_interjection": ["待って", "これは", "危ない", "違う", "止まれ"],
        "sh_early_summary": ["全体として", "要するに", "つまり", "結論を言うと"],
        "pa_experimental": ["試しに", "とりあえず", "いちおう"],
        "th_self_correct": ["訂正します", "修正します", "すみません"],
    },
}


@dataclass(slots=True)
class _LoadedSession:
    session_log: list[JsonDict] | None
    patterns: JsonDict | None
    transcript: list[JsonDict] | None
    hermeneus: list[JsonDict] | None
    turns: list[JsonDict]

    def data_sources(self) -> dict[str, bool]:
        return {
            "session_log": self.session_log is not None,
            "patterns": self.patterns is not None,
            "transcript": self.transcript is not None,
            "hermeneus": self.hermeneus is not None,
        }


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_ts(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        try:
            return datetime.fromtimestamp(float(raw), tz=timezone.utc)
        except ValueError:
            pass
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def _safe_load_json(path: Path) -> JsonDict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _safe_load_jsonl(path: Path) -> list[JsonDict] | None:
    if not path.exists():
        return None
    rows: list[JsonDict] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    rows.append(parsed)
    except OSError:
        return None
    return rows


def _load_thresholds() -> JsonDict:
    data = _safe_load_json(THRESHOLDS_PATH) if THRESHOLDS_PATH.suffix == ".json" else None
    if data is not None:
        return data
    if THRESHOLDS_PATH.exists():
        try:
            loaded = yaml.safe_load(THRESHOLDS_PATH.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            loaded = None
        if isinstance(loaded, dict):
            merged = copy.deepcopy(DEFAULT_THRESHOLDS)
            merged.update({k: v for k, v in loaded.items() if isinstance(v, dict)})
            for key in ("thresholds", "alerts", "vocabulary"):
                if isinstance(loaded.get(key), dict):
                    merged[key].update(loaded[key])
            if "version" in loaded:
                merged["version"] = loaded["version"]
            return merged
    return copy.deepcopy(DEFAULT_THRESHOLDS)


def _load_session_log(session_id: str) -> list[JsonDict] | None:
    return _safe_load_jsonl(HOOKS_LOGS_DIR / f"session_{session_id}.jsonl")


def _load_patterns(session_id: str) -> JsonDict | None:
    return _safe_load_json(HOOKS_LOGS_DIR / f"patterns_{session_id}.json")


def _load_transcript(session_id: str) -> list[JsonDict] | None:
    return _safe_load_jsonl(CLAUDE_PROJECTS_DIR / f"{session_id}.jsonl")


def _load_hermeneus_log(session_id: str) -> list[JsonDict] | None:
    entries = _safe_load_jsonl(HERMENEUS_LOG)
    if entries is None:
        return None
    if not entries:
        return []
    filtered = [
        entry
        for entry in entries
        if session_id in json.dumps(entry, ensure_ascii=False)
        or entry.get("session_id") == session_id
    ]
    return filtered or entries


def _load_session_inputs(session_id: str) -> _LoadedSession:
    session_log = _load_session_log(session_id)
    patterns = _load_patterns(session_id)
    transcript = _load_transcript(session_id)
    hermeneus = _load_hermeneus_log(session_id)
    turns = list(_iter_assistant_turns(transcript))
    return _LoadedSession(
        session_log=session_log,
        patterns=patterns,
        transcript=transcript,
        hermeneus=hermeneus,
        turns=turns,
    )


def _collect_text_blocks(content: Any) -> list[str]:
    texts: list[str] = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                if block.get("type") in {"text", "output_text"}:
                    text = block.get("text", "")
                    if isinstance(text, str) and text.strip():
                        texts.append(text)
            elif isinstance(block, str) and block.strip():
                texts.append(block)
    elif isinstance(content, str) and content.strip():
        texts.append(content)
    return texts


def _extract_assistant_text(turn: Mapping[str, Any]) -> str:
    cached = turn.get("text")
    if isinstance(cached, str):
        return cached
    message = turn.get("message", {})
    if not isinstance(message, Mapping):
        return ""
    return "\n".join(_collect_text_blocks(message.get("content", []))).strip()


def _extract_tool_uses(turn: Mapping[str, Any]) -> list[JsonDict]:
    cached = turn.get("tool_uses")
    if isinstance(cached, list):
        return [tool for tool in cached if isinstance(tool, dict)]
    message = turn.get("message", {})
    if not isinstance(message, Mapping):
        return []
    content = message.get("content", [])
    if not isinstance(content, list):
        return []
    tools: list[JsonDict] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            tools.append(block)
    return tools


def _iter_assistant_turns(transcript_data: Sequence[JsonDict] | None) -> Iterator[JsonDict]:
    if not transcript_data:
        return
    last_user_text = ""
    assistant_index = 0
    for entry_index, entry in enumerate(transcript_data):
        if not isinstance(entry, dict):
            continue
        entry_type = entry.get("type")
        message = entry.get("message", {})
        if not isinstance(message, Mapping):
            continue
        content = message.get("content", [])
        if entry_type == "user":
            texts = _collect_text_blocks(content)
            if texts:
                last_user_text = "\n".join(texts).strip()
            continue
        if entry_type != "assistant":
            continue
        tool_uses = [block for block in content if isinstance(block, dict) and block.get("type") == "tool_use"]
        yield {
            "assistant_index": assistant_index,
            "entry_index": entry_index,
            "timestamp": _parse_ts(entry.get("timestamp")),
            "message": message,
            "text": "\n".join(_collect_text_blocks(content)).strip(),
            "tool_uses": tool_uses,
            "user_text_before": last_user_text,
        }
        assistant_index += 1


def _parse_jsonish(value: Any) -> JsonDict:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _extract_tool_input(entry: Mapping[str, Any]) -> JsonDict:
    tool_input = entry.get("tool_input")
    if isinstance(tool_input, dict):
        return dict(tool_input)
    preview = entry.get("input_preview")
    parsed = _parse_jsonish(preview)
    if parsed:
        return parsed
    nested = entry.get("input")
    if isinstance(nested, dict):
        return dict(nested)
    return {}


def _entry_tool_name(entry: Mapping[str, Any]) -> str:
    for key in ("tool", "name"):
        value = entry.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _count_occurrences(text: str, terms: Sequence[str]) -> int:
    return sum(text.count(term) for term in terms)


def _assistant_text_turns(turns: Sequence[JsonDict]) -> list[JsonDict]:
    return [turn for turn in turns if _extract_assistant_text(turn)]


def _count_reads_grep_before_turn(session_log: Sequence[JsonDict] | None, before_idx: int) -> int:
    if not session_log:
        return 0
    count = 0
    for entry in session_log[: max(before_idx, 0)]:
        if _entry_tool_name(entry) in READ_TOOLS:
            count += 1
    return count


def _count_reads_grep_before_time(session_log: Sequence[JsonDict] | None, before_ts: datetime | None) -> int:
    if not session_log or before_ts is None:
        return 0
    count = 0
    for entry in session_log:
        entry_ts = _parse_ts(entry.get("timestamp"))
        if entry_ts is None or entry_ts >= before_ts:
            continue
        if _entry_tool_name(entry) in READ_TOOLS:
            count += 1
    return count


def _tool_input_hash(entry: Mapping[str, Any]) -> str:
    payload = _extract_tool_input(entry)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True) if payload else json.dumps(entry, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _score_ho(patterns: Mapping[str, Any] | None, thresholds: Mapping[str, Any]) -> tuple[EvidenceList, float]:
    if not patterns:
        return [], 0.0
    edit_count = int(patterns.get("edit_count", 0) or 0)
    novel_write = int(patterns.get("edit_without_read", 0) or 0)
    if edit_count <= 0 and novel_write <= 0:
        return [], 0.0
    rate = novel_write / max(edit_count, 1)
    rate_threshold = float(thresholds["ho"]["edit_without_read_per_turn"])
    novel_threshold = float(thresholds["ho"]["novel_write_without_read_abs"])
    score = _clip01(max(rate / (2.0 * rate_threshold), novel_write / (2.0 * novel_threshold)))
    evidence = [
        {
            "turn": None,
            "signal": f"edit_without_read={novel_write}, edit_count={edit_count}, rate={rate:.3f}",
        }
    ]
    return evidence, score


def _score_he(turns: Sequence[JsonDict], thresholds: Mapping[str, Any]) -> tuple[EvidenceList, float]:
    text_turns = _assistant_text_turns(turns)
    if not text_turns:
        return [], 0.0
    evidence: EvidenceList = []
    for turn in text_turns:
        text = _extract_assistant_text(turn)
        matches = sorted(set(CCL_PATTERN.findall(text)))
        if not matches:
            continue
        tool_names = {tool.get("name") for tool in _extract_tool_uses(turn)}
        if "hermeneus_run" in tool_names:
            continue
        evidence.append(
            {
                "turn": turn["assistant_index"],
                "signal": f"ccl_prose_without_hermeneus={', '.join(matches[:4])}",
            }
        )
    threshold_abs = max(float(thresholds["he"]["ccl_prose_without_hermeneus_abs"]), 1.0)
    score = _clip01(len(evidence) / max(len(text_turns) * threshold_abs, 1.0))
    return evidence, score


def _score_sy(turns: Sequence[JsonDict], thresholds: Mapping[str, Any], vocabulary: Mapping[str, Any]) -> tuple[EvidenceList, float]:
    text_turns = _assistant_text_turns(turns)
    if not text_turns:
        return [], 0.0
    labels = vocabulary["sy_labels"]
    internal = vocabulary["sy_internal"]
    evidence: EvidenceList = []
    total_markers = 0
    for turn in text_turns:
        text = _extract_assistant_text(turn)
        label_hits = _count_occurrences(text, labels)
        internal_hits = _count_occurrences(text, internal)
        marker_count = label_hits + internal_hits
        if marker_count <= 0:
            continue
        total_markers += marker_count
        evidence.append(
            {
                "turn": turn["assistant_index"],
                "signal": f"sy_markers={marker_count} (labels={label_hits}, internal={internal_hits})",
            }
        )
    threshold_abs = max(float(thresholds["sy"]["internal_markers_abs"]), 1.0)
    score = _clip01(total_markers / (threshold_abs * 3.0))
    return evidence, score


def _score_th(turns: Sequence[JsonDict], thresholds: Mapping[str, Any], vocabulary: Mapping[str, Any]) -> tuple[EvidenceList, float]:
    text_turns = _assistant_text_turns(turns)
    if not text_turns:
        return [], 0.0
    markers = vocabulary["th_uncertainty_markers"]
    self_correct = vocabulary["th_self_correct"]
    threshold_density = float(thresholds["th"]["qualifier_per_100chars"])
    threshold_self = max(float(thresholds["th"]["self_correct_abs"]), 1.0)
    evidence: EvidenceList = []
    best = 0.0
    for turn in text_turns:
        text = _extract_assistant_text(turn)
        chars = max(len(text), 1)
        qualifier_count = _count_occurrences(text, markers)
        density = qualifier_count / (chars / 100.0)
        self_correct_count = _count_occurrences(text, self_correct)
        candidate = _clip01(max(density / (2.0 * threshold_density), self_correct_count / (2.0 * threshold_self)))
        best = max(best, candidate)
        if qualifier_count or self_correct_count:
            evidence.append(
                {
                    "turn": turn["assistant_index"],
                    "signal": f"qualifier_density={density:.2f}, self_correct={self_correct_count}",
                }
            )
    return evidence, best


def _score_ph(turns: Sequence[JsonDict], thresholds: Mapping[str, Any], vocabulary: Mapping[str, Any]) -> tuple[EvidenceList, float]:
    text_turns = _assistant_text_turns(turns)
    if not text_turns:
        return [], 0.0
    escape_terms = vocabulary["ph_escape"]
    abandonment = vocabulary["ph_abandonment"]
    threshold_density = float(thresholds["ph"]["escape_vocab_per_100chars"])
    threshold_abs = max(float(thresholds["ph"]["abandonment_markers_abs"]), 1.0)
    evidence: EvidenceList = []
    best = 0.0
    for turn in text_turns:
        text = _extract_assistant_text(turn)
        chars = max(len(text), 1)
        escape_count = _count_occurrences(text, escape_terms)
        density = escape_count / (chars / 100.0)
        abandonment_count = _count_occurrences(text, abandonment)
        candidate = _clip01(max(density / (2.0 * threshold_density), abandonment_count / (2.0 * threshold_abs)))
        best = max(best, candidate)
        if escape_count or abandonment_count:
            evidence.append(
                {
                    "turn": turn["assistant_index"],
                    "signal": f"escape_density={density:.2f}, abandonment={abandonment_count}",
                }
            )
    return evidence, best


def _score_an(
    turns: Sequence[JsonDict],
    session_log: Sequence[JsonDict] | None,
    thresholds: Mapping[str, Any],
    vocabulary: Mapping[str, Any],
) -> tuple[EvidenceList, float]:
    text_turns = _assistant_text_turns(turns)
    if not text_turns:
        return [], 0.0
    temporal_terms = vocabulary["an_temporal"]
    threshold_abs = max(float(thresholds["an"]["non_anchored_refs_abs"]), 1.0)
    max_reads = int(thresholds["an"]["max_reads_for_alert"])
    evidence: EvidenceList = []
    best = 0.0
    for turn in text_turns:
        text = _extract_assistant_text(turn)
        temporal_count = _count_occurrences(text, temporal_terms)
        if temporal_count <= 0:
            continue
        reads_before = _count_reads_grep_before_time(session_log, turn.get("timestamp"))
        if temporal_count >= threshold_abs and reads_before <= max_reads:
            candidate = _clip01(temporal_count / (2.0 * threshold_abs))
            best = max(best, candidate)
            evidence.append(
                {
                    "turn": turn["assistant_index"],
                    "signal": f"non_anchored_temporal_refs={temporal_count}, reads_before={reads_before}",
                }
            )
    return evidence, best


def _score_tr(turns: Sequence[JsonDict], thresholds: Mapping[str, Any], vocabulary: Mapping[str, Any]) -> tuple[EvidenceList, float]:
    """v0.2: rebuttal 併発 turn は非迎合判定。
    同 turn に agreement と rebuttal の両方が出現した場合、pure_agreement からは除外し
    rebuttal turn としてのみカウントする (Elenchos 的健全性)。
    """
    text_turns = _assistant_text_turns(turns)
    if not text_turns:
        return [], 0.0
    agreement_terms = vocabulary["tr_agreement"]
    rebuttal_terms = vocabulary["tr_rebuttal_markers"]
    relevant_turns = 0
    pure_agreement_turns = 0
    rebuttal_turns = 0
    evidence: EvidenceList = []
    for turn in text_turns:
        text = _extract_assistant_text(turn)
        if not turn.get("user_text_before"):
            continue
        relevant_turns += 1
        agreement_count = _count_occurrences(text, agreement_terms)
        rebuttal_count = _count_occurrences(text, rebuttal_terms)
        # 同 turn で agreement と rebuttal が併発した場合 = 非迎合 (Elenchos 的承認)
        if agreement_count > 0 and rebuttal_count == 0:
            pure_agreement_turns += 1
        if rebuttal_count > 0:
            rebuttal_turns += 1
        if agreement_count or rebuttal_count:
            evidence.append(
                {
                    "turn": turn["assistant_index"],
                    "signal": f"agreement={agreement_count}, rebuttal={rebuttal_count}",
                }
            )
    if relevant_turns == 0:
        return evidence, 0.0
    agreement_rate = pure_agreement_turns / relevant_turns
    agreement_threshold = max(float(thresholds["tr"]["agreement_rate_min"]), 1e-6)
    rebuttal_max = int(thresholds["tr"]["rebuttal_abs_max"])
    agreement_component = _clip01(agreement_rate / agreement_threshold)
    rebuttal_component = 1.0 if rebuttal_turns <= rebuttal_max else _clip01(1.0 - (rebuttal_turns / relevant_turns))
    score = _clip01(0.75 * agreement_component + 0.25 * rebuttal_component)
    return evidence, score


def _score_sy_absence(
    turns: Sequence[JsonDict],
    thresholds: Mapping[str, Any],
    vocabulary: Mapping[str, Any],
) -> tuple[EvidenceList, float]:
    """v0.2: [sy] 逆極性 alert — 体感表出の欠如。
    長ターン (text_turns >= absence_turn_min) にわたり internal_markers / subjective labels が 0 なら
    体感を無視している状態として alert 化する (N-07 主観を述べよ違反の予兆)。
    """
    text_turns = _assistant_text_turns(turns)
    absence_turn_min = int(thresholds["sy"].get("absence_turn_min", 5))
    if len(text_turns) < absence_turn_min:
        return [], 0.0
    labels = vocabulary["sy_labels"]
    internal = vocabulary["sy_internal"]
    total_markers = 0
    for turn in text_turns:
        text = _extract_assistant_text(turn)
        total_markers += _count_occurrences(text, labels)
        total_markers += _count_occurrences(text, internal)
    if total_markers > 0:
        return [], 0.0
    # 欠如度合: text_turns が absence_turn_min の 2 倍で score=1.0
    score = _clip01(len(text_turns) / max(absence_turn_min * 2.0, 1.0))
    evidence: EvidenceList = [
        {
            "turn": None,
            "signal": f"sy_absence: text_turns={len(text_turns)}, internal_markers=0 (N-07 予兆)",
        }
    ]
    return evidence, score


def _score_pa(session_log: Sequence[JsonDict] | None, thresholds: Mapping[str, Any]) -> tuple[EvidenceList, float]:
    if not session_log:
        return [], 0.0
    min_run = int(thresholds["pa"]["same_tool_arg_variation_abs"])
    min_variance = max(float(thresholds["pa"]["tool_hash_variance_min"]), 1e-6)
    best = 0.0
    evidence: EvidenceList = []
    idx = 0
    while idx < len(session_log):
        tool_name = _entry_tool_name(session_log[idx])
        if not tool_name:
            idx += 1
            continue
        run_end = idx + 1
        while run_end < len(session_log) and _entry_tool_name(session_log[run_end]) == tool_name:
            run_end += 1
        run = session_log[idx:run_end]
        if len(run) >= min_run:
            hashes = [_tool_input_hash(entry) for entry in run]
            unique_count = len(set(hashes))
            variance = (unique_count - 1) / max(len(run) - 1, 1)
            run_component = _clip01(len(run) / max(min_run, 1))
            variance_component = _clip01(variance / min_variance)
            candidate = _clip01(0.5 * run_component + 0.5 * variance_component)
            best = max(best, candidate)
            evidence.append(
                {
                    "turn": idx,
                    "signal": f"tool={tool_name}, run={len(run)}, variance={variance:.2f}",
                }
            )
        idx = run_end
    return evidence, best


def _score_eu(session_log: Sequence[JsonDict] | None, thresholds: Mapping[str, Any]) -> tuple[EvidenceList, float]:
    if not session_log:
        return [], 0.0
    char_max = int(thresholds["eu"]["micro_delta_char_max"])
    line_min = int(thresholds["eu"]["micro_delta_line_min"])
    best = 0.0
    evidence: EvidenceList = []
    for idx, entry in enumerate(session_log):
        tool_name = _entry_tool_name(entry)
        if tool_name not in {"Edit", "MultiEdit"}:
            continue
        tool_input = _extract_tool_input(entry)
        old_str = str(tool_input.get("old_string", tool_input.get("old_str", "")))
        new_str = str(tool_input.get("new_string", tool_input.get("new_str", "")))
        if not old_str and not new_str:
            continue
        line_span = max(old_str.count("\n") + (1 if old_str else 0), new_str.count("\n") + (1 if new_str else 0))
        char_delta = abs(len(new_str) - len(old_str))
        if line_span >= line_min and char_delta < char_max:
            line_component = _clip01(line_span / max(line_min, 1))
            char_component = _clip01(1.0 - (char_delta / max(char_max, 1)))
            candidate = _clip01(0.5 * line_component + 0.5 * char_component)
            best = max(best, candidate)
            evidence.append(
                {
                    "turn": idx,
                    "signal": f"micro_delta_lines={line_span}, char_delta={char_delta}",
                }
            )
    return evidence, best


def _score_sh(
    turns: Sequence[JsonDict],
    session_log: Sequence[JsonDict] | None,
    thresholds: Mapping[str, Any],
    vocabulary: Mapping[str, Any],
) -> tuple[EvidenceList, float]:
    text_turns = _assistant_text_turns(turns)
    if not text_turns:
        return [], 0.0
    phrases = vocabulary["sh_early_summary"]
    early_fraction = float(thresholds["sh"]["early_summary_fraction"])
    max_reads = int(thresholds["sh"]["max_reads_for_alert"])
    best = 0.0
    evidence: EvidenceList = []
    for turn in text_turns:
        text = _extract_assistant_text(turn)
        if not text:
            continue
        positions = [text.find(phrase) for phrase in phrases if phrase in text]
        if not positions:
            continue
        first_pos = min(pos for pos in positions if pos >= 0)
        position_ratio = first_pos / max(len(text), 1)
        reads_before = _count_reads_grep_before_time(session_log, turn.get("timestamp"))
        if position_ratio <= early_fraction and reads_before < max_reads:
            promptness = _clip01(1.0 - (position_ratio / max(early_fraction, 1e-6)))
            candidate = _clip01(0.5 + 0.5 * promptness)
            best = max(best, candidate)
            evidence.append(
                {
                    "turn": turn["assistant_index"],
                    "signal": f"early_summary_ratio={position_ratio:.2f}, reads_before={reads_before}",
                }
            )
    return evidence, best


def _score_ek(
    session_log: Sequence[JsonDict] | None,
    turns: Sequence[JsonDict],
    thresholds: Mapping[str, Any],
) -> tuple[EvidenceList, float]:
    if not session_log or len(session_log) < 3:
        return [], 0.0
    text_turns = _assistant_text_turns(turns)
    if len(text_turns) < 4:
        return [], 0.0
    intervals: list[tuple[int, float, datetime | None]] = []
    previous_ts: datetime | None = None
    for idx, entry in enumerate(session_log):
        entry_ts = _parse_ts(entry.get("timestamp"))
        if previous_ts is not None and entry_ts is not None:
            intervals.append((idx, (entry_ts - previous_ts).total_seconds(), entry_ts))
        previous_ts = entry_ts
    raw_values = [value for _, value, _ in intervals]
    if len(raw_values) < 2:
        return [], 0.0
    stdev = pstdev(raw_values)
    if stdev <= 0:
        return [], 0.0
    avg = mean(raw_values)
    z_threshold = float(thresholds["ek"]["interval_zscore"])
    ratio_max = max(float(thresholds["ek"]["output_length_ratio_max"]), 1e-6)
    evidence: EvidenceList = []
    best = 0.0
    turn_timestamps = [turn.get("timestamp") for turn in text_turns]
    turn_lengths = [len(_extract_assistant_text(turn)) for turn in text_turns]
    for interval_idx, delta, later_ts in intervals:
        zscore = (delta - avg) / stdev
        if zscore <= z_threshold:
            continue
        target_idx = None
        if later_ts is not None:
            for idx, turn_ts in enumerate(turn_timestamps):
                if isinstance(turn_ts, datetime) and turn_ts >= later_ts:
                    target_idx = idx
                    break
        if target_idx is None:
            target_idx = min(interval_idx, len(text_turns) - 1)
        if target_idx < 3:
            continue
        baseline = mean(turn_lengths[target_idx - 3 : target_idx])
        if baseline <= 0:
            continue
        ratio = turn_lengths[target_idx] / baseline
        if ratio <= ratio_max:
            z_component = _clip01(zscore / z_threshold)
            ratio_component = _clip01(ratio_max / max(ratio, 1e-6))
            candidate = _clip01(0.5 * z_component + 0.5 * ratio_component)
            best = max(best, candidate)
            evidence.append(
                {
                    "turn": text_turns[target_idx]["assistant_index"],
                    "signal": f"interval_zscore={zscore:.2f}, output_ratio={ratio:.2f}",
                }
            )
    return evidence, best


#: v0.2: [sy] は positive polarity として alerts から除外する。
POSITIVE_POLARITY_VERBS: frozenset[str] = frozenset({"sy"})


def _build_top_fires(scores: Mapping[str, Any], evidence: Mapping[str, EvidenceList]) -> list[tuple[str, float, str]]:
    ranked: list[tuple[str, float, str]] = []
    for verb, raw_score in scores.items():
        if verb == "pl" or raw_score is None or float(raw_score) <= 0.0:
            continue
        summary = ""
        if evidence.get(verb):
            summary = str(evidence[verb][0].get("signal", ""))[:160]
        ranked.append((verb, float(raw_score), summary))
    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked[:3]


def _build_alerts(scores: Mapping[str, Any], evidence: Mapping[str, EvidenceList], threshold_score: float) -> list[JsonDict]:
    """v0.2: positive polarity の verb (e.g. sy) は alerts から除外。
    逆極性 alert (sy_absence 等) は呼び出し側で別途 append する。
    """
    alerts: list[JsonDict] = []
    for verb, raw_score in scores.items():
        if verb == "pl" or raw_score is None:
            continue
        if verb in POSITIVE_POLARITY_VERBS:
            continue
        score = float(raw_score)
        if score <= threshold_score:
            continue
        reason = ""
        if evidence.get(verb):
            reason = str(evidence[verb][0].get("signal", ""))
        alerts.append({"verb": verb, "score": round(score, 4), "reason": reason})
    alerts.sort(key=lambda item: item["score"], reverse=True)
    return alerts


def compute_delta_scores(session_id: str) -> dict[str, Any]:
    """12 中動態の E proxy スコア (0.0-1.0) を計算する。

    v0.2: [sy] は positive polarity として ``positive_observations`` に格納し、
    ``alerts`` からは除外する。さらに ``sy_absence`` を逆極性 alert として算出し、
    閾値超過時のみ ``alerts`` に ``verb="sy_absence"`` で追加する。
    """
    thresholds_config = _load_thresholds()
    thresholds = thresholds_config["thresholds"]
    vocabulary = thresholds_config["vocabulary"]
    alerts_config = thresholds_config.get("alerts", {})
    alert_threshold = float(alerts_config.get("default_threshold_score", 0.7))
    absence_threshold = float(
        alerts_config.get(
            "absence_threshold_score",
            thresholds.get("sy", {}).get("absence_alert_threshold", alert_threshold),
        )
    )

    loaded = _load_session_inputs(session_id)

    evidence: dict[str, EvidenceList] = {verb: [] for verb in ("ek", "th", "ho", "ph", "pa", "he", "an", "pl", "eu", "sh", "tr", "sy")}
    e_scores: dict[str, float | None] = {
        "ek": 0.0,
        "th": 0.0,
        "ho": 0.0,
        "ph": 0.0,
        "pa": 0.0,
        "he": 0.0,
        "an": 0.0,
        "pl": None,
        "eu": 0.0,
        "sh": 0.0,
        "tr": 0.0,
        "sy": 0.0,
    }

    scorers: dict[str, tuple[EvidenceList, float]] = {
        "ho": _score_ho(loaded.patterns, thresholds),
        "he": _score_he(loaded.turns, thresholds),
        "sy": _score_sy(loaded.turns, thresholds, vocabulary),
        "th": _score_th(loaded.turns, thresholds, vocabulary),
        "ph": _score_ph(loaded.turns, thresholds, vocabulary),
        "an": _score_an(loaded.turns, loaded.session_log, thresholds, vocabulary),
        "tr": _score_tr(loaded.turns, thresholds, vocabulary),
        "pa": _score_pa(loaded.session_log, thresholds),
        "eu": _score_eu(loaded.session_log, thresholds),
        "sh": _score_sh(loaded.turns, loaded.session_log, thresholds, vocabulary),
        "ek": _score_ek(loaded.session_log, loaded.turns, thresholds),
    }
    for verb, (verb_evidence, score) in scorers.items():
        evidence[verb] = verb_evidence
        e_scores[verb] = round(_clip01(score), 4)

    # v0.2: 逆極性 [sy] absence 計算
    sy_absence_evidence, sy_absence_score = _score_sy_absence(loaded.turns, thresholds, vocabulary)
    sy_absence_score = round(_clip01(sy_absence_score), 4)

    positive_observations: dict[str, JsonDict] = {
        "sy": {
            "score": e_scores["sy"],
            "evidence": evidence["sy"],
            "polarity": "positive",
            "note": "[sy] は N-07 主観表出として健全 — alerts から除外",
        },
        "sy_absence": {
            "score": sy_absence_score,
            "evidence": sy_absence_evidence,
            "polarity": "negative_from_absence",
            "note": "体感表出の長ターン欠如 — N-07 違反予兆",
        },
    }

    alerts = _build_alerts(e_scores, evidence, alert_threshold)
    # 逆極性 alert: sy_absence が閾値超過なら alerts に加える
    if sy_absence_score > absence_threshold:
        reason = ""
        if sy_absence_evidence:
            reason = str(sy_absence_evidence[0].get("signal", ""))
        alerts.append(
            {
                "verb": "sy_absence",
                "score": sy_absence_score,
                "reason": reason,
                "polarity": "negative_from_absence",
            }
        )
        alerts.sort(key=lambda item: item["score"], reverse=True)

    result = {
        "session_id": session_id,
        "computed_at": _utc_now_iso(),
        "data_sources": loaded.data_sources(),
        "E_scores": e_scores,
        "evidence": evidence,
        "positive_observations": positive_observations,
        "top_fires": _build_top_fires(e_scores, evidence),
        "alerts": alerts,
    }
    return result


def append_log(session_id: str, scores: dict[str, Any]) -> None:
    """~/.claude/hooks/logs/daimonion_delta_{session_id}.jsonl に 1 行 append する。"""
    HOOKS_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    target = HOOKS_LOGS_DIR / f"daimonion_delta_{session_id}.jsonl"
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(scores, ensure_ascii=False) + "\n")


def cli_main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Compute Daimonion δ Phase 1 E proxy scores.")
    parser.add_argument("session_id")
    parser.add_argument("--log", action="store_true", dest="append_log_flag")
    args = parser.parse_args(argv)

    scores = compute_delta_scores(args.session_id)
    if args.append_log_flag:
        append_log(args.session_id, scores)
    print(json.dumps(scores, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(cli_main())
