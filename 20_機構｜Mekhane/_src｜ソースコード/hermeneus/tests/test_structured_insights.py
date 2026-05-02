"""Tests for hermeneus.src.structured_insights — downstream consumer."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from hermeneus.src.structured_insights import (
    StructuredEntry,
    InsightReport,
    load_entries,
    analyze,
    validate_entry_schema,
)


# =============================================================================
# Fixtures
# =============================================================================

def _make_entry(wf="/pis+", confidence=0.85, findings=None, fit_level=None, model="gemini-3-flash"):
    """テスト用エントリを生成"""
    so = {
        "findings": findings or ["test finding"],
        "confidence": confidence,
        "summary": "test summary",
    }
    if fit_level:
        so["fit_level"] = fit_level
    return {
        "timestamp": datetime.now().isoformat(),
        "ccl": wf,
        "model": model,
        "account": "default",
        "structured_output": so,
    }


def _write_jsonl(entries, path):
    """エントリリストを JSONL に書き出す"""
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


# =============================================================================
# StructuredEntry
# =============================================================================

class TestStructuredEntry:
    def test_from_dict_valid(self):
        data = _make_entry()
        entry = StructuredEntry.from_dict(data)
        assert entry is not None
        assert entry.wf_id == "pis"
        assert entry.confidence == 0.85

    def test_from_dict_invalid(self):
        entry = StructuredEntry.from_dict({"bad": "data"})
        assert entry is None

    def test_wf_id_extraction(self):
        cases = [
            ("/noe+", "noe"),
            ("/dia-", "dia"),
            ("@fit*", "fit"),
            ("/ene", "ene"),
        ]
        for ccl, expected in cases:
            data = _make_entry(wf=ccl)
            entry = StructuredEntry.from_dict(data)
            assert entry.wf_id == expected, f"{ccl} → {entry.wf_id}, expected {expected}"

    def test_fit_level(self):
        data = _make_entry(fit_level="absorbed")
        entry = StructuredEntry.from_dict(data)
        assert entry.fit_level == "absorbed"


# =============================================================================
# load_entries
# =============================================================================

class TestLoadEntries:
    def test_load_from_file(self, tmp_path):
        entries = [_make_entry(), _make_entry(wf="/dia+", confidence=0.7)]
        jsonl = tmp_path / "test.jsonl"
        _write_jsonl(entries, jsonl)

        loaded = load_entries(jsonl_path=jsonl)
        assert len(loaded) == 2

    def test_load_empty_file(self, tmp_path):
        jsonl = tmp_path / "empty.jsonl"
        jsonl.touch()
        loaded = load_entries(jsonl_path=jsonl)
        assert len(loaded) == 0

    def test_load_nonexistent_file(self, tmp_path):
        loaded = load_entries(jsonl_path=tmp_path / "nonexistent.jsonl")
        assert len(loaded) == 0

    def test_wf_filter(self, tmp_path):
        entries = [_make_entry(wf="/pis+"), _make_entry(wf="/fit+")]
        jsonl = tmp_path / "test.jsonl"
        _write_jsonl(entries, jsonl)

        loaded = load_entries(jsonl_path=jsonl, wf_filter="pis")
        assert len(loaded) == 1
        assert loaded[0].wf_id == "pis"


# =============================================================================
# analyze
# =============================================================================

class TestAnalyze:
    def test_empty(self):
        report = analyze(entries=[])
        assert report.total_entries == 0

    def test_basic_analysis(self, tmp_path):
        entries = [
            _make_entry(wf="/pis+", confidence=0.8),
            _make_entry(wf="/pis+", confidence=0.9),
            _make_entry(wf="/fit+", confidence=0.6, fit_level="absorbed"),
        ]
        jsonl = tmp_path / "test.jsonl"
        _write_jsonl(entries, jsonl)

        report = analyze(jsonl_path=jsonl)
        assert report.total_entries == 3
        assert report.wf_counts.get("pis") == 2
        assert report.wf_counts.get("fit") == 1
        assert abs(report.wf_avg_confidence["pis"] - 0.85) < 0.01
        assert report.fit_distribution.get("absorbed") == 1

    def test_markdown_output(self, tmp_path):
        entries = [_make_entry()]
        jsonl = tmp_path / "test.jsonl"
        _write_jsonl(entries, jsonl)

        report = analyze(jsonl_path=jsonl)
        md = report.to_markdown()
        assert "品質トレンド" in md
        assert "/pis" in md


# =============================================================================
# validate_entry_schema
# =============================================================================

class TestValidateEntrySchema:
    def test_valid_entry(self):
        data = _make_entry(wf="/pis+")
        entry = StructuredEntry.from_dict(data)
        errors = validate_entry_schema(entry)
        assert len(errors) == 0

    def test_missing_required(self):
        data = _make_entry(wf="/pis+")
        del data["structured_output"]["findings"]
        entry = StructuredEntry.from_dict(data)
        errors = validate_entry_schema(entry)
        assert any("findings" in e for e in errors)

    def test_type_mismatch(self):
        data = _make_entry(wf="/pis+")
        data["structured_output"]["confidence"] = "not_a_number"
        entry = StructuredEntry.from_dict(data)
        errors = validate_entry_schema(entry)
        assert any("confidence" in e for e in errors)
