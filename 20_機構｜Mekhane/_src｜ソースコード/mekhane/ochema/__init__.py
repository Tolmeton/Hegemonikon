from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ochema/ A0→外部LLM接続
# PURPOSE: Ochēma パッケージ初期化 — lazy import
"""
Ochēma package — Unified LLM Access Layer.

Exports:
    OchemaService     - Unified LLM service (always available)
    CortexClient      - Cortex API direct
    LLMResponse       - Response data class
"""



# PURPOSE: [L2-auto] __getattr__ の関数定義
def __getattr__(name: str):
    """Lazy import for all public symbols."""
    if name == "OchemaService":
        from mekhane.ochema.service import OchemaService
        return OchemaService
    if name == "CortexClient":
        from mekhane.ochema.cortex_client import CortexClient
        return CortexClient
    if name == "LLMResponse":
        from mekhane.ochema.types import LLMResponse
        return LLMResponse
    raise AttributeError(f"module 'mekhane.ochema' has no attribute {name!r}")


__all__ = ["CortexClient", "LLMResponse", "OchemaService"]
