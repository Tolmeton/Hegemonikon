# PROOF: [L2/インフラ] <- mekhane/mneme/feedback_scorer.py A0→GEPA 目的関数 + 外部採点 (Gemini CLI)
from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any

from .trace_point import FeedbackScore, TracePoint

_TEXT_KW = {"text": True, "encoding": "utf-8", "errors": "replace"}


def extract_first_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object from raw CLI output (handles markdown fences / prose)."""
    stripped = (text or "").strip()
    if not stripped:
        raise ValueError("empty model output")

    try:
        val = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("no JSON object found in model output") from None
        val = json.loads(stripped[start : end + 1])

    if not isinstance(val, dict):
        raise TypeError("parsed JSON root must be an object")
    return val


def _gemini_env() -> dict[str, str]:
    """Match ochema/gemini_bridge gcloud isolation where possible."""
    return {
        **os.environ,
        "CLOUDSDK_CONFIG": "/dev/null",
        "GOOGLE_CLOUD_PROJECT": "",
        "GOOGLE_CLOUD_PROJECT_ID": "",
        "GCLOUD_PROJECT": "",
    }


def _run_gemini_cli(prompt: str, *, timeout: int = 300) -> str:
    gemini = shutil.which("gemini")
    if not gemini:
        raise FileNotFoundError("gemini CLI not found on PATH (expected executable name 'gemini')")

    result = subprocess.run(
        [gemini, "-p", prompt],
        capture_output=True,
        timeout=timeout,
        env=_gemini_env(),
        check=False,
        **_TEXT_KW,
    )
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if result.returncode != 0:
        msg = stderr or stdout or f"exit code {result.returncode}"
        raise RuntimeError(f"gemini CLI failed: {msg[:4000]}")
    return stdout


def score_objective(trace: TracePoint) -> float:
    """Deterministic heuristic score in ``[0, 1]`` from trace structure / signals."""
    sig = trace.signals or {}
    content = trace.content or {}

    if trace.type == "ERROR":
        return 0.05
    if trace.type == "CORRECTION":
        base = 0.45
    elif trace.type == "DECISION":
        base = 0.55
    elif trace.type == "REFLECTION":
        base = 0.6
    elif trace.type == "TOOL_CALL":
        base = 0.5
    else:
        base = 0.5

    if sig.get("tests_passed") is True:
        base += 0.2
    if sig.get("tests_passed") is False:
        base -= 0.25
    if sig.get("lint_clean") is True:
        base += 0.05
    if sig.get("lint_clean") is False:
        base -= 0.05

    err_n = sig.get("error_count")
    if isinstance(err_n, (int, float)):
        base -= 0.1 * min(float(err_n), 3.0)

    if content.get("risky") is True:
        base -= 0.1
    if content.get("reverted") is True:
        base -= 0.15

    return max(0.0, min(1.0, base))


def score_external(
    decision_id: str,
    trace: TracePoint,
    *,
    timeout: int = 300,
) -> FeedbackScore:
    """Use Gemini CLI to produce an external critique score for a single decision trace."""
    payload = {
        "decision_id": decision_id,
        "trace": trace.to_json(),
    }
    prompt = (
        "You are a rigorous retrospective reviewer (GEPA-style). "
        "Given the JSON payload of one agent decision trace, respond with ONE JSON object only, "
        "no markdown, keys exactly: "
        '{"score": <float between 0 and 1>, "feedback_text": "<concise critique>"}.\n\n'
        f"PAYLOAD:\n{json.dumps(payload, ensure_ascii=False)}"
    )

    raw = _run_gemini_cli(prompt, timeout=timeout)
    data = extract_first_json_object(raw)
    try:
        score = float(data["score"])
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"invalid score field in Gemini JSON: {data!r}") from e

    if score < 0.0 or score > 1.0:
        raise ValueError(f"score out of [0,1]: {score}")

    feedback = data.get("feedback_text")
    if not isinstance(feedback, str) or not feedback.strip():
        raise ValueError(f"invalid feedback_text in Gemini JSON: {data!r}")

    return FeedbackScore(decision_id=decision_id, score=score, feedback_text=feedback.strip())
