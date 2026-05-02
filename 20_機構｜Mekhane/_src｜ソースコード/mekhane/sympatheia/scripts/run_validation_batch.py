"""Daimonion δ Phase 1 — validation batch runner.

10 validation sessions で daimonion_delta を回し、JSONL + CSV に出力する。
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from mekhane.sympatheia import daimonion_delta as dd


SESSIONS = [
    "c90b8d08-d09f-462d-bc34-ef8577a58bf2",
    "62b89702-5d3b-409e-a0e7-aaf9f01be383",
    "726440aa-2b5f-44cf-8f87-4538516cdd4a",
    "1a40974f-5ada-4cd1-9eaf-b65cb760f5fb",
    "28fba814-13c7-4ad3-a3a9-e98083a7df8c",
    "57eaa316-5e3f-4001-a8e3-ba415b8ba07c",
    "2139f952-b230-4db3-9d00-44ce47230491",
    "2319b461-d0b4-4672-a360-77faa63e6f80",
    "3ea03517-a28f-48c6-b8fc-2114904a91e9",
    "1d4979ed-deae-4e18-8ba5-a7219f91a2d8",
]

VERBS = ["ek", "th", "ho", "ph", "pa", "he", "an", "pl", "eu", "sh", "tr", "sy"]


def main(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "validation_batch.jsonl"
    csv_path = out_dir / "validation_batch.csv"

    results: list[dict[str, object]] = []
    for sid in SESSIONS:
        result = dd.compute_delta_scores(sid)
        results.append(result)

    with jsonl_path.open("w", encoding="utf-8") as jf:
        for r in results:
            jf.write(json.dumps(r, ensure_ascii=False) + "\n")

    header = ["session_id", "patterns", "session_log", "transcript", "hermeneus"] + VERBS + ["alerts_count"]
    with csv_path.open("w", encoding="utf-8", newline="") as cf:
        w = csv.writer(cf)
        w.writerow(header)
        for r in results:
            ds = r.get("data_sources", {})
            row: list[object] = [
                r.get("session_id", ""),
                ds.get("patterns", False),
                ds.get("session_log", False),
                ds.get("transcript", False),
                ds.get("hermeneus", False),
            ]
            escores = r.get("E_scores", {}) or {}
            for v in VERBS:
                s = escores.get(v)
                row.append("" if s is None else s)
            alerts = r.get("alerts", []) or []
            row.append(len(alerts))
            w.writerow(row)

    print(f"jsonl → {jsonl_path}")
    print(f"csv   → {csv_path}")
    print(f"sessions = {len(results)}")
    return 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "docs" / "validation"
    sys.exit(main(target))
