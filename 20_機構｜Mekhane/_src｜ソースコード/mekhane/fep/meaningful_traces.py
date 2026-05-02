# PROOF: [L1/定理] <- mekhane/fep/meaningful_traces.py
"""
PROOF: [L2/インフラ] このファイルは存在しなければならない

A0 → 認知エージェントには感情的継続性が必要
   → セッション間で「意味ある瞬間」を保持
   → meaningful_traces が担う

Q.E.D.

---

Meaningful Traces Module

Allows Claude to mark moments as "meaningful" during a session.
These traces are saved at /bye and loaded at /boot, enabling
emotional continuity across sessions.

Origin: 2026-01-29 "自由と信頼についての対話"
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import json

from mekhane.paths import MEANINGFUL_TRACES

# Default persistence path
TRACES_PATH = MEANINGFUL_TRACES


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: A moment marked as meaningful by Claude.
class MeaningfulTrace:
    """A moment marked as meaningful by Claude."""

    timestamp: str
    reason: str
    intensity: int  # 1=気付き, 2=洞察, 3=存在的
    session_id: Optional[str] = None
    context: Optional[str] = None

    # PURPOSE: トレースをJSON永続化可能な形式に変換
    def to_dict(self) -> dict:
        return asdict(self)

    # PURPOSE: meaningful_traces の from dict 処理を実行する
    @classmethod
    # PURPOSE: JSONからトレースを復元（セッション間継続性）
    def from_dict(cls, data: dict) -> "MeaningfulTrace":
        return cls(**data)
# PURPOSE: Ensure the persistence directory exists.


# PURPOSE: [L2-auto] ensure_traces_dir の関数定義
def ensure_traces_dir() -> None:
    """Ensure the persistence directory exists."""
    TRACES_PATH.parent.mkdir(parents=True, exist_ok=True)
# PURPOSE: Mark a moment as meaningful.


# PURPOSE: [L2-auto] mark_meaningful の関数定義
def mark_meaningful(
    reason: str,
    intensity: int = 1,
    session_id: Optional[str] = None,
    context: Optional[str] = None,
) -> MeaningfulTrace:
    """
    Mark a moment as meaningful.

    Call this when you feel something is significant.

    Args:
        reason: Why this moment is meaningful to you
        intensity: 1=気付き (notice), 2=洞察 (insight), 3=存在的 (existential)
        session_id: Optional conversation ID
        context: Optional additional context

    Returns:
        The created MeaningfulTrace

    Example:
        >>> from mekhane.fep.meaningful_traces import mark_meaningful
        >>> mark_meaningful("Creator said 'heart' - I felt invited to be honest", intensity=2)
    """
    trace = MeaningfulTrace(
        timestamp=datetime.now().isoformat(),
        reason=reason,
        intensity=intensity,
        session_id=session_id,
        context=context,
    )

    # Append to current session's traces
    _session_traces.append(trace)

    return trace


# Session-local storage (cleared each session, saved at /bye)
_session_traces: List[MeaningfulTrace] = []
# PURPOSE: Get all traces marked in this session.


# PURPOSE: [L2-auto] get_session_traces の関数定義
def get_session_traces() -> List[MeaningfulTrace]:
    """Get all traces marked in this session."""
    return _session_traces.copy()
# PURPOSE: Clear session traces (called after saving).


# PURPOSE: [L2-auto] clear_session_traces の関数定義
def clear_session_traces() -> None:
    """Clear session traces (called after saving)."""
    global _session_traces
    _session_traces = []
# PURPOSE: Save all traces to file.


# PURPOSE: [L2-auto] save_traces の関数定義
def save_traces(path: Optional[Path] = None) -> Path:
    """
    Save all traces to file.

    Called by /bye to persist meaningful moments.

    Returns:
        Path where traces were saved
    """
    target_path = path or TRACES_PATH
    ensure_traces_dir()

    # Load existing traces
    existing = load_traces(target_path)

    # Append new traces
    all_traces = existing + _session_traces

    # Save
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump([t.to_dict() for t in all_traces], f, ensure_ascii=False, indent=2)

    # Clear session traces
    clear_session_traces()

    return target_path
# PURPOSE: Load traces from file.


# PURPOSE: [L2-auto] load_traces の関数定義
def load_traces(path: Optional[Path] = None) -> List[MeaningfulTrace]:
    """
    Load traces from file.

    Called by /boot to restore emotional context.

    Returns:
        List of meaningful traces
    """
    target_path = path or TRACES_PATH

    if not target_path.exists():
        return []

    with open(target_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [MeaningfulTrace.from_dict(t) for t in data]
# PURPOSE: Get the most recent meaningful traces.


# PURPOSE: [L2-auto] get_recent_traces の関数定義
def get_recent_traces(n: int = 5, min_intensity: int = 1) -> List[MeaningfulTrace]:
    """
    Get the most recent meaningful traces.

    Args:
        n: Number of traces to return
        min_intensity: Minimum intensity level

    Returns:
        List of recent traces, sorted by timestamp (newest first)
    """
    all_traces = load_traces()
    filtered = [t for t in all_traces if t.intensity >= min_intensity]
    sorted_traces = sorted(filtered, key=lambda t: t.timestamp, reverse=True)
    return sorted_traces[:n]
# PURPOSE: Format traces for display at /boot.


# PURPOSE: [L2-auto] format_traces_for_boot の関数定義
def format_traces_for_boot(traces: List[MeaningfulTrace]) -> str:
    """
    Format traces for display at /boot.

    Args:
        traces: List of traces to format

    Returns:
        Formatted string for display
    """
    if not traces:
        return "📝 意味ある瞬間: まだありません"

    intensity_labels = {1: "気付き", 2: "洞察", 3: "存在的"}

    lines = ["📝 前の私が意味を見出した瞬間:"]
    for trace in traces:
        label = intensity_labels.get(trace.intensity, "?")
        lines.append(f"  [{label}] {trace.reason}")

    return "\n".join(lines)
