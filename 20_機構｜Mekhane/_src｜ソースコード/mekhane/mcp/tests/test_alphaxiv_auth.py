#!/usr/bin/env python3
"""Tests for alphaXiv OAuth adapter."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


def _credential(access_token="tok", refresh_token="ref", expires_at=9_999_999_999_999):
    return {
        "mcpOAuth": {
            "alphaxiv|test": {
                "serverName": "alphaxiv",
                "serverUrl": "https://api.alphaxiv.org/mcp/v1",
                "accessToken": access_token,
                "refreshToken": refresh_token,
                "clientId": "client",
                "expiresAt": expires_at,
                "discoveryState": {"authorizationServerUrl": "https://clerk.alphaxiv.org"},
            }
        }
    }


def test_resolve_authorization_uses_fresh_credential(tmp_path):
    from mekhane.mcp.alphaxiv_auth import resolve_authorization

    path = tmp_path / "credentials.json"
    path.write_text(json.dumps(_credential(access_token="fresh-token")))

    header, entry, status = resolve_authorization(path=path, allow_refresh=False)

    assert header == "Bearer fresh-token"
    assert entry["serverName"] == "alphaxiv"
    assert status == "fresh"


def test_resolve_authorization_fails_closed_when_refresh_disabled(tmp_path):
    from mekhane.mcp.alphaxiv_auth import AlphaxivAuthError, resolve_authorization

    path = tmp_path / "credentials.json"
    path.write_text(json.dumps(_credential(expires_at=1)))

    with pytest.raises(AlphaxivAuthError, match="stale"):
        resolve_authorization(path=path, allow_refresh=False)


def test_export_shell_quotes_authorization(tmp_path, capsys):
    from mekhane.mcp.alphaxiv_auth import main

    path = tmp_path / "credentials.json"
    path.write_text(json.dumps(_credential(access_token="token with spaces")))

    assert main(["--credentials", str(path), "--export-shell", "--no-refresh"]) == 0

    out = capsys.readouterr().out.strip()
    assert out.startswith("export ALPHAXIV_MCP_AUTHORIZATION=")
    assert "Bearer token with spaces" in out
