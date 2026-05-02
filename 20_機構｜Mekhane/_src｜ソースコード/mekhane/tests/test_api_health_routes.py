# PROOF: [L2/テスト] <- mekhane/api/server.py + api/routes/status.py health 語彙分離を固定

from __future__ import annotations

from contextlib import asynccontextmanager

import pytest

pytest.importorskip("fastapi", reason="fastapi not installed (see requirements.txt)")
from fastapi.testclient import TestClient

from mekhane.peira.hgk_health import HealthItem, HealthReport


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    import mekhane.api.server as server
    from mekhane.api import API_PREFIX
    from mekhane.api.routes.status import router as status_router
    import mekhane.peira.hgk_health as health_module

    @asynccontextmanager
    async def noop_lifespan(_app):
        yield

    def register_only_status(app):
        app.include_router(status_router, prefix=API_PREFIX)

    def fake_report(_backend_check_mode: str = "http") -> HealthReport:
        return HealthReport(
            timestamp="2026-04-18T00:00:00",
            effective_profile="full",
            items=[
                HealthItem("HGK Backend (Digestor)", "error", "not ready"),
                HealthItem("Dendron L1", "warn", "coverage low"),
                HealthItem("Theorem Activity", "ok", "healthy"),
            ],
        )

    monkeypatch.setattr(server, "_lifespan", noop_lifespan)
    monkeypatch.setattr(server, "_register_routers", register_only_status)
    monkeypatch.setattr(health_module, "run_health_check", fake_report)

    return TestClient(server.create_app())


def test_root_healthz_is_liveness_only(client: TestClient) -> None:
    res = client.get("/healthz")

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "uptime_seconds" in body


def test_root_readyz_exposes_blockers_and_degradations(client: TestClient) -> None:
    res = client.get("/readyz")

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "blocked"
    assert body["ready"] is False
    assert body["blockers"] == ["HGK Backend (Digestor)"]
    assert body["degradations"] == ["Dendron L1"]


def test_status_capability_returns_enriched_contract_report(client: TestClient) -> None:
    res = client.get("/api/status/capability")

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "blocked"
    assert body["ready"] is False
    assert body["effective_profile"] == "full"
    assert body["items"][0]["category"] == "service"
    assert body["items"][0]["blocking"] is True


def test_status_readyz_returns_summary_only(client: TestClient) -> None:
    res = client.get("/api/status/readyz")

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "blocked"
    assert body["ready"] is False
    assert body["blockers"][0]["name"] == "HGK Backend (Digestor)"
    assert body["degradations"][0]["name"] == "Dendron L1"
