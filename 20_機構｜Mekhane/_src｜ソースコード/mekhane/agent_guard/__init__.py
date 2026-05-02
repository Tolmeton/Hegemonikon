"""
Agent Guard パッケージ

エージェントの安全な実行を監視・保護するためのモジュール群。

Context Window Guard: コンテキストウィンドウサイズの解決と閾値判定。
Compaction Utilities: トークン推定・履歴分割・閾値判定 (Context Rot 防止)。
Apothēkē: Lossless Eviction — 対話を Týpos ナレッジ化し KI として永続化。
Tool Loop Detection: 4検出器によるツールループ検出 (T-03 OpenClaw 移植)。
Tool Policy Pipeline: ツール名の allow/deny フィルタリング。
Session Write Lock: file-based exclusive lock (T-15 OpenClaw 移植)。
"""

from .context_window import (
    ContextWindowInfo,
    ContextWindowSource,
    ContextWindowGuardResult,
    resolve_context_window,
    resolve_from_model,
    evaluate_guard,
    evaluate_guard_ratio,
    CONTEXT_WINDOW_HARD_MIN_TOKENS,
    CONTEXT_WINDOW_WARN_BELOW_TOKENS,
)

from .compaction import (
    estimate_tokens,
    estimate_history_tokens,
    summarize_history,
    needs_compaction,
    SAFETY_MARGIN,
)

from .tool_policy import (
    DenyEntry,
    PolicyResult,
    PolicyStep,
    ToolPolicy,
    apply_pipeline,
    apply_policy,
    build_steps_from_yaml,
    normalize_tool_name,
)

from .tool_loop import (
    ToolCallRecord,
    ToolLoopConfig,
    ToolLoopDetectorsConfig,
    LoopDetectionResult,
    detect_tool_call_loop,
    hash_tool_call,
    hash_tool_outcome,
    is_known_poll_tool_call,
    record_tool_call,
    record_tool_outcome,
)

__all__ = [
    # Context Window Guard
    "ContextWindowInfo",
    "ContextWindowSource",
    "ContextWindowGuardResult",
    "resolve_context_window",
    "resolve_from_model",
    "evaluate_guard",
    "evaluate_guard_ratio",
    "CONTEXT_WINDOW_HARD_MIN_TOKENS",
    "CONTEXT_WINDOW_WARN_BELOW_TOKENS",
    # Compaction Utilities
    "estimate_tokens",
    "estimate_history_tokens",
    "summarize_history",
    "needs_compaction",
    "SAFETY_MARGIN",
    # Tool Policy Pipeline (T-14)
    "DenyEntry",
    "PolicyResult",
    "PolicyStep",
    "ToolPolicy",
    "apply_pipeline",
    "apply_policy",
    "build_steps_from_yaml",
    "normalize_tool_name",
    # Tool Loop Detection (T-03)
    "ToolCallRecord",
    "ToolLoopConfig",
    "ToolLoopDetectorsConfig",
    "LoopDetectionResult",
    "detect_tool_call_loop",
    "hash_tool_call",
    "hash_tool_outcome",
    "is_known_poll_tool_call",
    "record_tool_call",
    "record_tool_outcome",
]
