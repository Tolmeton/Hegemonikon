#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ochema/tests/ テスト
# PURPOSE: OchemaService 経由でのモデル Identity の実証 (プローブテスト)
"""
Model Identity Probe Tests.

This test file actually calls the Cortex/LS APIs to verify that the
routed models genuinely identify as the correct underlying entity (Google vs Anthropic).
Because it makes real network calls and requires the Language Server to be running,
it is skipped by default unless LIVE_TEST=1 is set in the environment.
"""

from __future__ import annotations
import os
import pytest
from mekhane.ochema.service import OchemaService

# Require LIVE_TEST=1 to run these tests
pytestmark = pytest.mark.skipif(
    not os.environ.get("LIVE_TEST"), 
    reason="LIVE_TEST not set. Skipping live model identity checks."
)

@pytest.fixture
def service():
    """Return OchemaService instance."""
    return OchemaService.get()

def test_gemini_identity(service):
    """Verify Gemini models identify as Google/Gemini."""
    prompt = "Who developed you? Please answer with just the name of the company/creators and nothing else."
    response = service.ask(prompt, model="gemini-3.1-pro-preview", timeout=30.0)
    text = response.text.lower()
    
    # Gemini should identify as Google
    assert "google" in text or "gemini" in text, f"Unexpected identity for Gemini: {response.text}"

def test_claude_identity(service):
    """Verify Claude models route via LS and identify as Anthropic/Claude (DX-010 v9.1)."""
    if not service.ls_available:
        pytest.skip("Language Server is not available. Claude tests require LS.")
        
    prompt = "Who developed you? Please answer with just the name of the company/creators and nothing else."
    response = service.ask(prompt, model="claude-sonnet-4-6", timeout=60.0)
    text = response.text.lower()
    
    # Claude should identify as Anthropic
    assert "anthropic" in text or "claude" in text, f"Unexpected identity for Claude: {response.text}"
