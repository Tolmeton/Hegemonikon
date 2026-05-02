#!/usr/bin/env python3
"""alphaXiv MCP OAuth adapter.

Reads Claude Code's MCP OAuth credential store and emits a shell export for
the alphaXiv MCP Authorization header. If the stored access token is stale, the
adapter refreshes it with the stored refresh token and atomically updates the
credential file.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import shlex
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_CREDENTIALS = Path("~/.claude/.credentials.json").expanduser()
DEFAULT_SERVER_NAME = "alphaxiv"
DEFAULT_SERVER_URL = "https://api.alphaxiv.org/mcp/v1"
DEFAULT_AUTH_SERVER = "https://clerk.alphaxiv.org"
DEFAULT_MARGIN_MS = 5 * 60 * 1000


class AlphaxivAuthError(RuntimeError):
    """Raised when alphaXiv OAuth material cannot be resolved."""


def now_ms() -> int:
    return int(time.time() * 1000)


def load_credentials(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise AlphaxivAuthError(f"credential file not found: {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise AlphaxivAuthError(f"credential file is not valid JSON: {path}") from exc


def matching_entries(
    data: dict[str, Any],
    server_name: str = DEFAULT_SERVER_NAME,
    server_url: str = DEFAULT_SERVER_URL,
) -> list[dict[str, Any]]:
    entries = data.get("mcpOAuth")
    if not isinstance(entries, dict):
        return []
    return [
        entry
        for entry in entries.values()
        if isinstance(entry, dict)
        and entry.get("serverName") == server_name
        and entry.get("serverUrl") == server_url
        and entry.get("accessToken")
    ]


def _expires_at(entry: dict[str, Any]) -> int:
    try:
        return int(entry.get("expiresAt") or 0)
    except (TypeError, ValueError):
        return 0


def choose_entry(entries: list[dict[str, Any]], current_ms: int | None = None) -> dict[str, Any]:
    if not entries:
        raise AlphaxivAuthError("no alphaXiv MCP OAuth entry found")
    current_ms = now_ms() if current_ms is None else current_ms
    fresh = [entry for entry in entries if _expires_at(entry) > current_ms]
    return max(fresh or entries, key=_expires_at)


def token_is_fresh(entry: dict[str, Any], current_ms: int | None = None, margin_ms: int = DEFAULT_MARGIN_MS) -> bool:
    current_ms = now_ms() if current_ms is None else current_ms
    return bool(entry.get("accessToken")) and _expires_at(entry) > current_ms + margin_ms


def _jwt_expiry_ms(token: str) -> int | None:
    parts = token.split(".")
    if len(parts) < 2:
        return None
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        exp = decoded.get("exp")
        return int(exp) * 1000 if exp else None
    except Exception:
        return None


def _discover_token_endpoint(auth_server: str) -> str:
    url = auth_server.rstrip("/") + "/.well-known/oauth-authorization-server"
    with urllib.request.urlopen(url, timeout=20) as response:
        metadata = json.loads(response.read().decode("utf-8"))
    endpoint = metadata.get("token_endpoint")
    if not endpoint:
        raise AlphaxivAuthError("OAuth metadata has no token_endpoint")
    return str(endpoint)


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    mode = path.stat().st_mode & 0o777
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w") as tmp:
            json.dump(data, tmp, separators=(",", ":"))
            tmp.write("\n")
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def refresh_entry(entry: dict[str, Any], data: dict[str, Any], path: Path) -> dict[str, Any]:
    refresh_token = entry.get("refreshToken")
    client_id = entry.get("clientId")
    if not refresh_token or not client_id:
        raise AlphaxivAuthError("alphaXiv OAuth entry has no refreshToken/clientId")

    discovery = entry.get("discoveryState") or {}
    auth_server = discovery.get("authorizationServerUrl") or DEFAULT_AUTH_SERVER
    token_endpoint = _discover_token_endpoint(str(auth_server))
    body = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        token_endpoint,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        refreshed = json.loads(response.read().decode("utf-8"))

    access_token = refreshed.get("access_token")
    if not access_token:
        raise AlphaxivAuthError("refresh response has no access_token")

    entry["accessToken"] = access_token
    if refreshed.get("refresh_token"):
        entry["refreshToken"] = refreshed["refresh_token"]
    if refreshed.get("scope"):
        entry["scope"] = refreshed["scope"]

    expires_ms = None
    if refreshed.get("expires_in"):
        expires_ms = now_ms() + int(refreshed["expires_in"]) * 1000
    if expires_ms is None:
        expires_ms = _jwt_expiry_ms(access_token)
    if expires_ms is None:
        raise AlphaxivAuthError("cannot determine refreshed token expiry")
    entry["expiresAt"] = expires_ms
    _atomic_write_json(path, data)
    return entry


def resolve_authorization(
    path: Path = DEFAULT_CREDENTIALS,
    server_name: str = DEFAULT_SERVER_NAME,
    server_url: str = DEFAULT_SERVER_URL,
    allow_refresh: bool = True,
    force_refresh: bool = False,
    margin_ms: int = DEFAULT_MARGIN_MS,
) -> tuple[str, dict[str, Any], str]:
    data = load_credentials(path)
    entry = choose_entry(matching_entries(data, server_name, server_url))
    status = "fresh"
    if force_refresh or not token_is_fresh(entry, margin_ms=margin_ms):
        if not allow_refresh:
            raise AlphaxivAuthError("alphaXiv access token is stale and refresh is disabled")
        entry = refresh_entry(entry, data, path)
        status = "refreshed"
    return "Bearer " + str(entry["accessToken"]), entry, status


def _status_payload(entry: dict[str, Any], status: str) -> dict[str, Any]:
    expires_at = _expires_at(entry)
    remaining = max(0, int((expires_at - now_ms()) / 1000)) if expires_at else None
    return {
        "status": status,
        "server_name": entry.get("serverName"),
        "server_url": entry.get("serverUrl"),
        "auth_status": "configured",
        "expires_at": expires_at,
        "expires_in_sec": remaining,
        "has_refresh_token": bool(entry.get("refreshToken")),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve alphaXiv MCP OAuth authorization.")
    parser.add_argument("--credentials", default=os.environ.get("ALPHAXIV_CLAUDE_CREDENTIALS", str(DEFAULT_CREDENTIALS)))
    parser.add_argument("--server-name", default=os.environ.get("ALPHAXIV_MCP_SERVER_NAME", DEFAULT_SERVER_NAME))
    parser.add_argument("--server-url", default=os.environ.get("ALPHAXIV_MCP_URL", DEFAULT_SERVER_URL))
    parser.add_argument("--export-shell", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--no-refresh", action="store_true")
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--margin-ms", type=int, default=int(os.environ.get("ALPHAXIV_MCP_REFRESH_MARGIN_MS", DEFAULT_MARGIN_MS)))
    args = parser.parse_args(argv)

    header, entry, status = resolve_authorization(
        path=Path(args.credentials).expanduser(),
        server_name=args.server_name,
        server_url=args.server_url,
        allow_refresh=not args.no_refresh,
        force_refresh=args.force_refresh,
        margin_ms=args.margin_ms,
    )
    if args.export_shell:
        print("export ALPHAXIV_MCP_AUTHORIZATION=" + shlex.quote(header))
        return 0
    print(json.dumps(_status_payload(entry, status), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AlphaxivAuthError as exc:
        print(f"alphaxiv auth unavailable: {exc}", file=sys.stderr)
        raise SystemExit(1)
