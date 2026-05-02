# PROOF: [L2/テスト] <- mekhane/peira/hgk_health.py health 契約の分離を固定

from __future__ import annotations

from mekhane.mcp.hub_config import get_backend_required_probe
from mekhane.peira.hgk_health import (
    HealthItem,
    HealthReport,
    get_health_item_contract,
    serialize_health_item,
)


def test_health_report_splits_blockers_and_degradations() -> None:
    report = HealthReport(
        timestamp="2026-04-18T00:00:00",
        effective_profile="full",
        items=[
            HealthItem("HGK Backend (Digestor)", "error", "not ready"),
            HealthItem("Dendron L1", "warn", "coverage low"),
            HealthItem("Theorem Activity", "ok", "healthy"),
        ],
    )

    assert report.ready is False
    assert report.status == "blocked"
    assert [item.name for item in report.blockers] == ["HGK Backend (Digestor)"]
    assert [item.name for item in report.degradations] == ["Dendron L1"]

    payload = report.to_dict()
    assert payload["ready"] is False
    assert payload["status"] == "blocked"
    assert payload["blockers"][0]["blocking"] is True
    assert payload["degradations"][0]["category"] == "quality"


def test_blocking_warn_is_degradation_not_stop() -> None:
    report = HealthReport(
        timestamp="2026-04-18T00:00:00",
        effective_profile="full",
        items=[
            HealthItem("HGK Backend (Digestor)", "warn", "liveness only"),
            HealthItem("Theorem Activity", "ok", "healthy"),
        ],
    )

    assert report.ready is True
    assert report.status == "degraded"
    assert report.blockers == []
    assert [item.name for item in report.degradations] == ["HGK Backend (Digestor)"]


def test_health_item_contract_serialization_adds_category_and_blocking() -> None:
    item = HealthItem("Hermēneus MCP", "ok", "running")
    payload = serialize_health_item(item)

    assert payload["category"] == "service"
    assert payload["blocking"] is True
    assert get_health_item_contract("unknown-item") == {"category": "quality", "blocking": False}


def test_backend_required_probe_contracts_exist_for_core_backends() -> None:
    xmcp_probe = get_backend_required_probe("xmcp")
    ochema_probe = get_backend_required_probe("ochema")
    notebooklm_probe = get_backend_required_probe("notebooklm")

    assert xmcp_probe["mode"] == "call"
    assert xmcp_probe["tool"] == "getUsersMe"
    assert xmcp_probe["contract"] == "user_context_read"

    assert ochema_probe["blocking"] is True
    assert ochema_probe["tool"] == "ask"

    assert notebooklm_probe["mode"] == "call"
    assert notebooklm_probe["tool"] == "notebook_list"
    assert notebooklm_probe["contract"] == "external_rag"
