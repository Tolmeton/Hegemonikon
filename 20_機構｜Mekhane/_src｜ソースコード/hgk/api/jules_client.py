from __future__ import annotations
#!/usr/bin/env python3
"""
Jules API Client — Async coding agent integration for HGK

Jules API (v1alpha) を叩いて、GitHub リポジトリ上で非同期コーディングタスクを実行する。
18本の API キーをラウンドロビンでローテーションし、レートリミットを分散。

Usage:
    client = JulesClient()
    sources = client.list_sources()
    session = client.create_session(prompt="Fix the bug", source="sources/github/owner/repo")
    status = client.get_session(session["id"])
"""

import os
import time
import logging
import requests
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)

JULES_API_BASE = "https://jules.googleapis.com/v1alpha"


@dataclass
class JulesClient:
    """Jules REST API client with key rotation."""

    _keys: list[str] = field(default_factory=list, repr=False)
    _key_idx: int = field(default=0, repr=False)
    _session: requests.Session = field(default_factory=requests.Session, repr=False)

    def __post_init__(self) -> None:
        # Collect all JULES_API_KEY_* from environment
        if not self._keys:
            keys: list[str] = []
            for i in range(1, 30):  # up to 29 keys
                k = os.environ.get(f"JULES_API_KEY_{i:02d}", "")
                if k:
                    keys.append(k)
            if not keys:
                # Fallback: single key
                single = os.environ.get("JULES_API_KEY", "")
                if single:
                    keys.append(single)
            self._keys = keys
            log.info(f"JulesClient: loaded {len(self._keys)} API key(s)")

    @property
    def available(self) -> bool:
        return len(self._keys) > 0

    def _next_key(self) -> str:
        if not self._keys:
            raise RuntimeError("No Jules API keys configured")
        key = self._keys[self._key_idx % len(self._keys)]
        self._key_idx += 1
        return key

    def _headers(self) -> dict[str, str]:
        return {
            "X-Goog-Api-Key": self._next_key(),
            "Content-Type": "application/json",
        }

    def _get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        url = f"{JULES_API_BASE}{path}"
        resp = self._session.get(url, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, body: dict | None = None) -> dict[str, Any]:
        url = f"{JULES_API_BASE}{path}"
        resp = self._session.post(url, headers=self._headers(), json=body or {}, timeout=60)
        resp.raise_for_status()
        return resp.json()

    # ── Sources ───────────────────────────────────────────────

    def list_sources(self) -> list[dict[str, Any]]:
        """List available GitHub sources (repos installed via Jules web app)."""
        data = self._get("/sources")
        return data.get("sources", [])

    # ── Sessions ──────────────────────────────────────────────

    def create_session(
        self,
        prompt: str,
        source: str,
        *,
        title: str = "",
        branch: str = "main",
        automation_mode: str = "AUTO_CREATE_PR",
        require_plan_approval: bool = False,
    ) -> dict[str, Any]:
        """Create a new Jules session (coding task).

        Args:
            prompt: Task description (e.g., "Fix the login bug in auth.py")
            source: Source identifier (e.g., "sources/github/owner/repo")
            title: Optional session title
            branch: Starting branch (default: main)
            automation_mode: AUTO_CREATE_PR | MANUAL
            require_plan_approval: If True, Jules pauses after planning for approval
        """
        body: dict[str, Any] = {
            "prompt": prompt,
            "sourceContext": {
                "source": source,
                "githubRepoContext": {
                    "startingBranch": branch,
                },
            },
            "automationMode": automation_mode,
            "requirePlanApproval": require_plan_approval,
        }
        if title:
            body["title"] = title
        return self._post("/sessions", body)

    def list_sessions(self, page_size: int = 20) -> list[dict[str, Any]]:
        """List recent Jules sessions."""
        data = self._get("/sessions", params={"pageSize": page_size})
        return data.get("sessions", [])

    def get_session(self, session_id: str) -> dict[str, Any]:
        """Get session details by ID."""
        return self._get(f"/sessions/{session_id}")

    def approve_plan(self, session_id: str) -> dict[str, Any]:
        """Approve a pending plan for a session."""
        return self._post(f"/sessions/{session_id}:approvePlan")

    def send_message(self, session_id: str, message: str) -> dict[str, Any]:
        """Send a follow-up message to an active session."""
        return self._post(f"/sessions/{session_id}:sendMessage", {"message": message})

    # ── Activities ────────────────────────────────────────────

    def list_activities(self, session_id: str, page_size: int = 50) -> list[dict[str, Any]]:
        """List activities (log entries) for a session."""
        data = self._get(
            f"/sessions/{session_id}/activities",
            params={"pageSize": page_size},
        )
        return data.get("activities", [])

    # ── Polling helper ────────────────────────────────────────

    def poll_session(
        self,
        session_id: str,
        interval: float = 5.0,
        max_wait: float = 600.0,
        callback: Any = None,
    ) -> dict[str, Any]:
        """Poll a session until completion or timeout.

        Args:
            session_id: The session to poll
            interval: Seconds between polls
            max_wait: Maximum total wait time
            callback: Optional callable(session_dict) called each poll

        Returns:
            Final session state
        """
        start = time.monotonic()
        while time.monotonic() - start < max_wait:
            session = self.get_session(session_id)
            state = session.get("state", "")
            if callback:
                callback(session)
            if state in ("COMPLETED", "FAILED", "CANCELLED"):
                return session
            time.sleep(interval)
        return self.get_session(session_id)  # final fetch


# Singleton
_jules: JulesClient | None = None


def get_jules_client() -> JulesClient:
    global _jules
    if _jules is None:
        _jules = JulesClient()
    return _jules
