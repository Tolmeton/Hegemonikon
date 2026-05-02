# PROOF: [L2/インフラ] <- mekhane/mneme/trace_point.py A0→GEPA trace / lesson データ構造
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional

TraceType = Literal["TOOL_CALL", "DECISION", "ERROR", "CORRECTION", "REFLECTION"]


@dataclass
class TracePoint:
    id: str
    type: TraceType
    timestamp: str
    context: dict = field(default_factory=dict)
    content: dict = field(default_factory=dict)
    signals: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> TracePoint:
        return cls(**json.loads(json_str))


@dataclass
class FeedbackScore:
    decision_id: str
    score: float
    feedback_text: str


@dataclass
class Lesson:
    id: str
    lesson_text: str
    context_types: list[str] = field(default_factory=list)
    effectiveness: dict[str, float] = field(default_factory=dict)
    source_decisions: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    dominated_by: Optional[str] = None
