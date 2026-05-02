# PROOF: [L2/インフラ] <- mekhane/ochema/types.py 共有型定義
# PURPOSE: Ochēma モジュール間で共有される型定義。循環依存を防ぐための独立モジュール。
"""Ochēma shared types — LLMResponse and constants.

This module provides shared type definitions used across
the Ochēma package (service.py, cortex_client.py, etc).
"""
from __future__ import annotations
from typing import Any


from dataclasses import dataclass, field


# PURPOSE: [L2-auto] LLMResponse のクラス定義
@dataclass
class LLMResponse:
    """LLM からの応答を保持する。"""
    text: str = ""
    thinking: str = ""
    thinking_signature: str = ""
    thinking_duration: str = ""
    stop_reason: str = ""
    message_id: str = ""
    model: str = ""
    token_usage: dict = field(default_factory=dict)
    cascade_id: str = ""
    trajectory_id: str = ""
    raw_steps: list = field(default_factory=list)
    step_count: int = 0  # total steps seen (for multi-turn offset)
    parsed: Any = None  # Parsed Pydantic model when response_model is used

