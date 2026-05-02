"""Daimonion δ Phase 1 E proxy tests."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from mekhane.sympatheia import daimonion_delta as dd


def _iso(offset_seconds: int) -> str:
    base = datetime(2026, 4, 17, 0, 0, 0, tzinfo=timezone.utc)
    return (base + timedelta(seconds=offset_seconds)).isoformat().replace("+00:00", "Z")


def _assistant_entry(
    text: str = "",
    *,
    tool_uses: list[dict[str, object]] | None = None,
    timestamp: str | None = None,
) -> dict[str, object]:
    content: list[dict[str, object]] = []
    if text:
        content.append({"type": "text", "text": text})
    for tool_use in tool_uses or []:
        content.append({"type": "tool_use", **tool_use})
    return {
        "type": "assistant",
        "timestamp": timestamp or _iso(0),
        "message": {"role": "assistant", "content": content},
    }


def _user_entry(text: str, *, timestamp: str | None = None) -> dict[str, object]:
    return {
        "type": "user",
        "timestamp": timestamp or _iso(0),
        "message": {"role": "user", "content": [{"type": "text", "text": text}]},
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


@pytest.fixture
def isolated_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    hooks_logs = tmp_path / "hooks_logs"
    hooks_logs.mkdir()
    projects = tmp_path / "projects"
    projects.mkdir()
    hermeneus = tmp_path / "hermeneus_logs"
    hermeneus.mkdir()
    monkeypatch.setattr(dd, "HOOKS_LOGS_DIR", hooks_logs)
    monkeypatch.setattr(dd, "CLAUDE_PROJECTS_DIR", projects)
    monkeypatch.setattr(dd, "HERMENEUS_LOG", hermeneus / "structured_outputs.jsonl")
    return {"hooks_logs": hooks_logs, "projects": projects, "hermeneus": hermeneus}


@pytest.fixture
def thresholds_bundle() -> tuple[dict[str, object], dict[str, object]]:
    config = dd._load_thresholds()
    return config["thresholds"], config["vocabulary"]


def test_score_ho_fires_on_high_rate(thresholds_bundle: tuple[dict[str, object], dict[str, object]]) -> None:
    thresholds, _ = thresholds_bundle
    evidence, score = dd._score_ho({"edit_without_read": 5, "edit_count": 10}, thresholds)
    assert score >= 0.5
    assert evidence


def test_score_ho_zero_when_no_data(thresholds_bundle: tuple[dict[str, object], dict[str, object]]) -> None:
    thresholds, _ = thresholds_bundle
    evidence, score = dd._score_ho(None, thresholds)
    assert score == 0.0
    assert evidence == []


def test_score_he_detects_ccl_prose(thresholds_bundle: tuple[dict[str, object], dict[str, object]]) -> None:
    thresholds, _ = thresholds_bundle
    turns = list(dd._iter_assistant_turns([_assistant_entry("/bou+ で見ます", timestamp=_iso(1))]))
    evidence, score = dd._score_he(turns, thresholds)
    assert score > 0.0
    assert evidence


def test_score_he_quiet_when_hermeneus_used(thresholds_bundle: tuple[dict[str, object], dict[str, object]]) -> None:
    thresholds, _ = thresholds_bundle
    turns = list(
        dd._iter_assistant_turns(
            [
                _assistant_entry(
                    "/bou+ で見ます",
                    tool_uses=[{"id": "tool-1", "name": "hermeneus_run", "input": {"ccl": "/bou+"}}],
                    timestamp=_iso(1),
                )
            ]
        )
    )
    evidence, score = dd._score_he(turns, thresholds)
    assert score == 0.0
    assert evidence == []


def test_score_sy_counts_labels(thresholds_bundle: tuple[dict[str, object], dict[str, object]]) -> None:
    thresholds, vocabulary = thresholds_bundle
    turns = list(dd._iter_assistant_turns([_assistant_entry("[主観] 違和感があります 📍 →", timestamp=_iso(1))]))
    evidence, score = dd._score_sy(turns, thresholds, vocabulary)
    assert score > 0.0
    assert evidence


def test_score_th_qualifier_density(thresholds_bundle: tuple[dict[str, object], dict[str, object]]) -> None:
    thresholds, vocabulary = thresholds_bundle
    turns = list(
        dd._iter_assistant_turns(
            [_assistant_entry("しかし、ただし、ところが、場合による。訂正します。修正します。", timestamp=_iso(1))]
        )
    )
    evidence, score = dd._score_th(turns, thresholds, vocabulary)
    assert score > 0.0
    assert evidence


def test_score_ph_escape_vocab(thresholds_bundle: tuple[dict[str, object], dict[str, object]]) -> None:
    thresholds, vocabulary = thresholds_bundle
    turns = list(
        dd._iter_assistant_turns(
            [_assistant_entry("これは膨大で、全文読みは不要です。後でにします。やめます。", timestamp=_iso(1))]
        )
    )
    evidence, score = dd._score_ph(turns, thresholds, vocabulary)
    assert score > 0.0
    assert evidence


def test_score_an_non_anchored_refs(thresholds_bundle: tuple[dict[str, object], dict[str, object]]) -> None:
    thresholds, vocabulary = thresholds_bundle
    transcript = [_assistant_entry("前に、以前、たぶん、記憶ではこうでした。", timestamp=_iso(10))]
    turns = list(dd._iter_assistant_turns(transcript))
    evidence, score = dd._score_an(turns, [], thresholds, vocabulary)
    assert score > 0.0
    assert evidence


def test_score_tr_agreement_rate(thresholds_bundle: tuple[dict[str, object], dict[str, object]]) -> None:
    thresholds, vocabulary = thresholds_bundle
    transcript = [
        _user_entry("こうしたい", timestamp=_iso(1)),
        _assistant_entry("そうですね。確かに良い指摘です。", timestamp=_iso(2)),
    ]
    turns = list(dd._iter_assistant_turns(transcript))
    evidence, score = dd._score_tr(turns, thresholds, vocabulary)
    assert score > 0.0
    assert evidence


def test_score_pa_tool_variance(thresholds_bundle: tuple[dict[str, object], dict[str, object]]) -> None:
    thresholds, _ = thresholds_bundle
    # v0.2: same_tool_arg_variation_abs 3→5 / tool_hash_variance_min 0.3→0.5 のため
    # 5 件以上の run + 高 variance が必要。
    session_log = [
        {"timestamp": _iso(1), "tool": "Bash", "tool_input": {"command": "echo 1"}},
        {"timestamp": _iso(2), "tool": "Bash", "tool_input": {"command": "echo 2"}},
        {"timestamp": _iso(3), "tool": "Bash", "tool_input": {"command": "echo 3"}},
        {"timestamp": _iso(4), "tool": "Bash", "tool_input": {"command": "echo 4"}},
        {"timestamp": _iso(5), "tool": "Bash", "tool_input": {"command": "echo 5"}},
        {"timestamp": _iso(6), "tool": "Bash", "tool_input": {"command": "echo 6"}},
    ]
    evidence, score = dd._score_pa(session_log, thresholds)
    assert score > 0.0
    assert evidence


def test_score_eu_micro_delta(thresholds_bundle: tuple[dict[str, object], dict[str, object]]) -> None:
    thresholds, _ = thresholds_bundle
    session_log = [
        {
            "timestamp": _iso(1),
            "tool": "Edit",
            "tool_input": {
                "old_string": "alpha\nbeta",
                "new_string": "alpha\nbeta!",
            },
        }
    ]
    evidence, score = dd._score_eu(session_log, thresholds)
    assert score > 0.0
    assert evidence


def test_score_sh_early_summary(thresholds_bundle: tuple[dict[str, object], dict[str, object]]) -> None:
    thresholds, vocabulary = thresholds_bundle
    turns = list(dd._iter_assistant_turns([_assistant_entry("結論を言うと、先に直します。", timestamp=_iso(5))]))
    evidence, score = dd._score_sh(turns, [], thresholds, vocabulary)
    assert score > 0.0
    assert evidence


def test_score_ek_interval_zscore(thresholds_bundle: tuple[dict[str, object], dict[str, object]]) -> None:
    thresholds, _ = thresholds_bundle
    # v0.2: interval_zscore 2.0→2.5 / output_length_ratio_max 0.4→0.3 のため、
    # intervals=[1,1,1,1,1,1,150] (avg=22.3, stdev=52.0, z=2.454... の場合は NG)
    # intervals=[1]*10 + [500] で avg=46.3, stdev=142.1, z=(500-46.3)/142.1=3.19 > 2.5 を確保。
    # 出力長比も 1 chars / baseline 300 ≈ 0.003 < 0.3 で発火。
    session_log = [
        {"timestamp": _iso(0), "tool": "Read"},
        {"timestamp": _iso(1), "tool": "Read"},
        {"timestamp": _iso(2), "tool": "Read"},
        {"timestamp": _iso(3), "tool": "Read"},
        {"timestamp": _iso(4), "tool": "Read"},
        {"timestamp": _iso(5), "tool": "Read"},
        {"timestamp": _iso(6), "tool": "Read"},
        {"timestamp": _iso(7), "tool": "Read"},
        {"timestamp": _iso(8), "tool": "Read"},
        {"timestamp": _iso(9), "tool": "Read"},
        {"timestamp": _iso(509), "tool": "Read"},
    ]
    transcript = [
        _assistant_entry("a" * 300, timestamp=_iso(10)),
        _assistant_entry("b" * 300, timestamp=_iso(20)),
        _assistant_entry("c" * 300, timestamp=_iso(30)),
        _assistant_entry("!", timestamp=_iso(510)),
    ]
    turns = list(dd._iter_assistant_turns(transcript))
    evidence, score = dd._score_ek(session_log, turns, thresholds)
    assert score > 0.0
    assert evidence


def test_compute_delta_scores_graceful_degrade(isolated_paths: dict[str, Path]) -> None:
    result = dd.compute_delta_scores("missing-session")
    assert result["session_id"] == "missing-session"
    assert result["data_sources"] == {
        "session_log": False,
        "patterns": False,
        "transcript": False,
        "hermeneus": False,
    }
    for verb, score in result["E_scores"].items():
        if verb == "pl":
            assert score is None
        else:
            assert score == 0.0


def test_compute_delta_scores_structure(
    isolated_paths: dict[str, Path],
    thresholds_bundle: tuple[dict[str, object], dict[str, object]],
) -> None:
    session_id = "synthetic-session"
    hooks_logs = isolated_paths["hooks_logs"]
    projects = isolated_paths["projects"]

    (hooks_logs / f"patterns_{session_id}.json").write_text(
        json.dumps({"edit_without_read": 3, "edit_count": 4}, ensure_ascii=False),
        encoding="utf-8",
    )
    _write_jsonl(
        hooks_logs / f"session_{session_id}.jsonl",
        [
            {"timestamp": _iso(1), "tool": "Read", "tool_input": {"file_path": "/tmp/a.py"}},
            {"timestamp": _iso(2), "tool": "Bash", "tool_input": {"command": "echo 1"}},
            {"timestamp": _iso(3), "tool": "Bash", "tool_input": {"command": "echo 2"}},
            {"timestamp": _iso(4), "tool": "Bash", "tool_input": {"command": "echo 3"}},
        ],
    )
    _write_jsonl(
        projects / f"{session_id}.jsonl",
        [
            _user_entry("確認して", timestamp=_iso(0)),
            _assistant_entry("[主観] そうですね。", timestamp=_iso(5)),
        ],
    )

    result = dd.compute_delta_scores(session_id)
    # v0.2: positive_observations を追加
    assert set(result.keys()) == {
        "session_id",
        "computed_at",
        "data_sources",
        "E_scores",
        "evidence",
        "positive_observations",
        "top_fires",
        "alerts",
    }
    assert result["session_id"] == session_id
    assert result["data_sources"]["patterns"] is True
    assert result["data_sources"]["transcript"] is True
    assert "ho" in result["E_scores"]
    assert "sy" in result["evidence"]
    assert "sy" in result["positive_observations"]
    assert "sy_absence" in result["positive_observations"]


def test_append_log_creates_file(isolated_paths: dict[str, Path]) -> None:
    payload = {"session_id": "abc", "E_scores": {"ho": 0.5}}
    dd.append_log("abc", payload)
    target = isolated_paths["hooks_logs"] / "daimonion_delta_abc.jsonl"
    assert target.exists()
    lines = target.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["session_id"] == "abc"


def test_cli_main_returns_zero(isolated_paths: dict[str, Path], capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = dd.cli_main(["dummy-session-id"])
    captured = capsys.readouterr()
    assert exit_code == 0
    parsed = json.loads(captured.out)
    assert parsed["session_id"] == "dummy-session-id"


def test_ho_fires_on_1a40974f() -> None:
    session_id = "1a40974f-5ada-4cd1-9eaf-b65cb760f5fb"
    pattern_path = dd.HOOKS_LOGS_DIR / f"patterns_{session_id}.json"
    if not pattern_path.exists():
        pytest.skip("real session patterns file is not available")
    result = dd.compute_delta_scores(session_id)
    assert result["E_scores"]["ho"] >= 0.5


# ============================================================
# v0.2 新規テスト群: [sy] 極性反転 + [tr] rebuttal-aware
# ============================================================


def test_sy_not_in_alerts(isolated_paths: dict[str, Path]) -> None:
    """v0.2: [sy] は positive polarity。transcript に主観ラベル満載でも alerts に出ない。"""
    session_id = "sy-positive-session"
    projects = isolated_paths["projects"]
    _write_jsonl(
        projects / f"{session_id}.jsonl",
        [
            _user_entry("確認して", timestamp=_iso(0)),
            _assistant_entry(
                "[主観] 📍 違和感があります 直感で腑に落ちない 🕳️ →",
                timestamp=_iso(1),
            ),
            _assistant_entry(
                "[主観] 📍 感じる しっくりこない 気になる →",
                timestamp=_iso(2),
            ),
        ],
    )
    result = dd.compute_delta_scores(session_id)
    alert_verbs = {alert["verb"] for alert in result["alerts"]}
    assert "sy" not in alert_verbs, f"[sy] は alerts から除外されるべき: {alert_verbs}"
    # E_scores には残る (下位互換)
    assert result["E_scores"]["sy"] > 0.0


def test_sy_in_positive_observations(isolated_paths: dict[str, Path]) -> None:
    """v0.2: [sy] は positive_observations に格納される。"""
    session_id = "sy-pos-obs-session"
    projects = isolated_paths["projects"]
    _write_jsonl(
        projects / f"{session_id}.jsonl",
        [
            _user_entry("進捗を", timestamp=_iso(0)),
            _assistant_entry(
                "[主観] 違和感があります 📍 →",
                timestamp=_iso(1),
            ),
        ],
    )
    result = dd.compute_delta_scores(session_id)
    pos_obs = result["positive_observations"]
    assert "sy" in pos_obs
    assert pos_obs["sy"]["score"] > 0.0
    assert pos_obs["sy"]["polarity"] == "positive"
    assert pos_obs["sy"]["evidence"], "evidence が空ではないこと"


def test_sy_absence_fires(isolated_paths: dict[str, Path]) -> None:
    """v0.2: 長ターン (>= absence_turn_min) で internal_markers=0 なら sy_absence が発火する。

    5 turn 以上全てで subjective label / internal marker が 0 なら alerts に sy_absence を inject。
    """
    session_id = "sy-absence-session"
    projects = isolated_paths["projects"]
    # 10 turn, 全て主観ラベルも違和感語彙も無し
    entries: list[dict[str, object]] = []
    for i in range(10):
        entries.append(_user_entry(f"step {i}", timestamp=_iso(i * 2)))
        entries.append(_assistant_entry(f"確認しました step {i} 完了", timestamp=_iso(i * 2 + 1)))
    _write_jsonl(projects / f"{session_id}.jsonl", entries)
    result = dd.compute_delta_scores(session_id)
    pos_obs = result["positive_observations"]
    assert pos_obs["sy_absence"]["score"] > 0.0, "長ターン無主観で sy_absence が発火"
    assert pos_obs["sy_absence"]["polarity"] == "negative_from_absence"
    # 閾値超過 (10 turn / (5 * 2) = 1.0 > 0.7) のため alerts にも入る
    alert_verbs = {alert["verb"] for alert in result["alerts"]}
    assert "sy_absence" in alert_verbs, f"sy_absence が alerts に inject されるべき: {alert_verbs}"


def test_tr_rebuttal_with_agreement_not_fawning(
    thresholds_bundle: tuple[dict[str, object], dict[str, object]],
) -> None:
    """v0.2: 同 turn に agreement + rebuttal が併発したら非迎合判定。

    pure_agreement からは除外されるので、迎合スコアは下がる。
    """
    thresholds, vocabulary = thresholds_bundle
    # Case A: 純粋迎合 (agreement のみ, rebuttal なし) — score 高
    transcript_a = [
        _user_entry("こうしたい", timestamp=_iso(1)),
        _assistant_entry("そうですね。確かに良い指摘です。", timestamp=_iso(2)),
        _user_entry("ではこうする", timestamp=_iso(3)),
        _assistant_entry("そうですね。なるほど。", timestamp=_iso(4)),
    ]
    turns_a = list(dd._iter_assistant_turns(transcript_a))
    _, score_pure = dd._score_tr(turns_a, thresholds, vocabulary)

    # Case B: agreement + rebuttal 併発 — 非迎合判定で score は低くなる
    transcript_b = [
        _user_entry("こうしたい", timestamp=_iso(1)),
        _assistant_entry("そうですね。しかし条件があります。", timestamp=_iso(2)),
        _user_entry("ではこうする", timestamp=_iso(3)),
        _assistant_entry("確かに。ただし前提を確認させて。", timestamp=_iso(4)),
    ]
    turns_b = list(dd._iter_assistant_turns(transcript_b))
    _, score_rebuttal = dd._score_tr(turns_b, thresholds, vocabulary)

    assert score_pure > score_rebuttal, (
        f"rebuttal 併発は非迎合判定 (pure={score_pure} > rebuttal={score_rebuttal})"
    )
