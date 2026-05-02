# PROOF: [L2/インフラ] <- mekhane/mneme/reflective_diagnosis.py A0→/ath+ 診断 (Gemini CLI → JSON)
from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Sequence

from .feedback_scorer import _run_gemini_cli, extract_first_json_object
from .trace_point import FeedbackScore, TracePoint


def diagnose(
    traces: Sequence[TracePoint],
    scores: Sequence[FeedbackScore],
    *,
    timeout: int = 600,
) -> dict[str, Any]:
    """Run a structured retrospective diagnosis via Gemini CLI; returns parsed JSON object.

    Expected model keys (best-effort; extra keys preserved):
      - ``summary``: str
      - ``root_causes``: list[str]
      - ``counterfactuals``: list[str]
      - ``lessons``: list[dict]  (each may include lesson_text, if_then_rules, …)
      - ``risks``: list[str]
    """
    bundle = {
        "traces": [json.loads(t.to_json()) for t in traces],
        "scores": [asdict(s) for s in scores],
    }
    prompt = (
        "You are executing /ath+ (Anatheōrēsis) with GEPA flavour: causal retrospective, "
        "counterfactuals, and If-Then rules.\n"
        "Input is JSON with fields traces[] and scores[].\n"
        "Respond with ONE JSON object only (no markdown), using this schema:\n"
        "{\n"
        '  "summary": string,\n'
        '  "root_causes": string[],\n'
        '  "counterfactuals": string[],\n'
        '  "lessons": object[],\n'
        '  "risks": string[],\n'
        '  "if_then_rules": string[]\n'
        "}\n\n"
        f"INPUT:\n{json.dumps(bundle, ensure_ascii=False)}"
    )

    raw = _run_gemini_cli(prompt, timeout=timeout)
    return extract_first_json_object(raw)
