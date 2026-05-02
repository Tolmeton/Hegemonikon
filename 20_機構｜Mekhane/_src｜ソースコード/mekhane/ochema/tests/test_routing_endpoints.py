# PROOF: [L2/インフラ] <- mekhane/ochema/tests/test_routing_endpoints.py
# PURPOSE: ランタイムルーティング API (/v1/routing) の契約固定

from __future__ import annotations

import os

import pytest

pytest.importorskip("fastapi", reason="fastapi not installed (see requirements.txt)")
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("HGK_OPENAI_COMPAT_TOKEN", "test-secret-token")
    from mekhane.ochema.openai_compat_server import (
        _ENV_HAIKU_BACKEND,
        _ENV_OPUS_BACKEND,
        _ENV_SONNET_BACKEND,
        create_app,
    )

    monkeypatch.delenv(_ENV_OPUS_BACKEND, raising=False)
    monkeypatch.delenv(_ENV_SONNET_BACKEND, raising=False)
    monkeypatch.delenv(_ENV_HAIKU_BACKEND, raising=False)
    return TestClient(create_app())


def test_routing_requires_bearer(client: TestClient) -> None:
    r = client.get("/v1/routing")
    assert r.status_code == 401


def test_routing_get_returns_defaults(client: TestClient) -> None:
    from mekhane.ochema.openai_compat_server import (
        _DEFAULT_HAIKU_SPEC,
        _DEFAULT_OPUS_SPEC,
        _DEFAULT_SONNET_SPEC,
    )

    r = client.get(
        "/v1/routing",
        headers={"Authorization": "Bearer test-secret-token"},
    )

    assert r.status_code == 200
    body = r.json()
    assert body == {
        "slots": {
            "opus": {
                "current": _DEFAULT_OPUS_SPEC,
                "default": _DEFAULT_OPUS_SPEC,
                "is_default": True,
            },
            "sonnet": {
                "current": _DEFAULT_SONNET_SPEC,
                "default": _DEFAULT_SONNET_SPEC,
                "is_default": True,
            },
            "haiku": {
                "current": _DEFAULT_HAIKU_SPEC,
                "default": _DEFAULT_HAIKU_SPEC,
                "is_default": True,
            },
        }
    }


def test_routing_put_updates_selected_slots(client: TestClient) -> None:
    from mekhane.ochema.openai_compat_server import (
        _DEFAULT_HAIKU_SPEC,
        _DEFAULT_OPUS_SPEC,
        _DEFAULT_SONNET_SPEC,
        _ENV_HAIKU_BACKEND,
        _ENV_OPUS_BACKEND,
        _ENV_SONNET_BACKEND,
    )

    r = client.put(
        "/v1/routing",
        headers={"Authorization": "Bearer test-secret-token"},
        json={
            "opus": "ls:claude-opus",
            "haiku": "gemini_cli:gemini-3.1-pro-preview",
        },
    )

    assert r.status_code == 200
    body = r.json()
    assert body["before"] == {
        "opus": {
            "current": _DEFAULT_OPUS_SPEC,
            "default": _DEFAULT_OPUS_SPEC,
            "is_default": True,
        },
        "sonnet": {
            "current": _DEFAULT_SONNET_SPEC,
            "default": _DEFAULT_SONNET_SPEC,
            "is_default": True,
        },
        "haiku": {
            "current": _DEFAULT_HAIKU_SPEC,
            "default": _DEFAULT_HAIKU_SPEC,
            "is_default": True,
        },
    }
    assert body["after"] == {
        "opus": {
            "current": "ls:claude-opus",
            "default": _DEFAULT_OPUS_SPEC,
            "is_default": False,
        },
        "sonnet": {
            "current": _DEFAULT_SONNET_SPEC,
            "default": _DEFAULT_SONNET_SPEC,
            "is_default": True,
        },
        "haiku": {
            "current": "gemini_cli:gemini-3.1-pro-preview",
            "default": _DEFAULT_HAIKU_SPEC,
            "is_default": False,
        },
    }
    assert os.environ[_ENV_OPUS_BACKEND] == "ls:claude-opus"
    assert os.environ[_ENV_HAIKU_BACKEND] == "gemini_cli:gemini-3.1-pro-preview"
    assert _ENV_SONNET_BACKEND not in os.environ


def test_routing_put_rejects_invalid_spec(client: TestClient) -> None:
    from mekhane.ochema.openai_compat_server import _ENV_OPUS_BACKEND

    r = client.put(
        "/v1/routing",
        headers={"Authorization": "Bearer test-secret-token"},
        json={"opus": "unknown_route:claude-opus"},
    )

    assert r.status_code == 400
    assert "Unknown route in backend spec" in r.json()["detail"]
    assert _ENV_OPUS_BACKEND not in os.environ


def test_routing_delete_resets_slots(client: TestClient) -> None:
    from mekhane.ochema.openai_compat_server import (
        _DEFAULT_HAIKU_SPEC,
        _DEFAULT_OPUS_SPEC,
        _DEFAULT_SONNET_SPEC,
        _ENV_HAIKU_BACKEND,
        _ENV_OPUS_BACKEND,
        _ENV_SONNET_BACKEND,
    )

    update = client.put(
        "/v1/routing",
        headers={"Authorization": "Bearer test-secret-token"},
        json={
            "opus": "ls:claude-opus",
            "sonnet": "cli_agent_smart:analysis",
            "haiku": "gemini_cli:gemini-3.1-pro",
        },
    )
    assert update.status_code == 200

    r = client.delete(
        "/v1/routing",
        headers={"Authorization": "Bearer test-secret-token"},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["after"] == {
        "opus": {
            "current": _DEFAULT_OPUS_SPEC,
            "default": _DEFAULT_OPUS_SPEC,
            "is_default": True,
        },
        "sonnet": {
            "current": _DEFAULT_SONNET_SPEC,
            "default": _DEFAULT_SONNET_SPEC,
            "is_default": True,
        },
        "haiku": {
            "current": _DEFAULT_HAIKU_SPEC,
            "default": _DEFAULT_HAIKU_SPEC,
            "is_default": True,
        },
    }
    assert _ENV_OPUS_BACKEND not in os.environ
    assert _ENV_SONNET_BACKEND not in os.environ
    assert _ENV_HAIKU_BACKEND not in os.environ
