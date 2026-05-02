from __future__ import annotations

from mekhane.ochema.task_routing import infer_task_class, resolve_cli_task_route


def test_infer_task_class_prefers_explicit_marker() -> None:
    assert infer_task_class("task_class: coding\nReview this plan.") == "coding"


def test_infer_task_class_detects_coding_from_prompt() -> None:
    assert infer_task_class("Please implement this patch and fix the bug.") == "coding"


def test_infer_task_class_detects_multimodal_heavy() -> None:
    assert infer_task_class("Scan this PDF and write a report.") == "multimodal_heavy"


def test_resolve_cli_task_route_analysis_maps_to_copilot_xhigh() -> None:
    decision = resolve_cli_task_route("task_class: analysis")
    assert decision.tool == "copilot"
    assert decision.bridge_model == "gpt-5.4:xhigh"
