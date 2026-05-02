"""後方互換 shim — 旧パス scripts.bc_violation_logger を維持。
本体は mekhane.sympatheia.violation_logger に移動済み。
"""
import warnings

warnings.warn(
    "scripts.bc_violation_logger は非推奨です。"
    " mekhane.sympatheia.violation_logger を使用してください。",
    DeprecationWarning,
    stacklevel=2,
)

# 全公開シンボルを re-export
from mekhane.sympatheia.violation_logger import (  # noqa: F401,E402
    FeedbackEntry,
    log_entry,
    read_all_entries,
    filter_entries,
    compute_stats,
    compute_trend,
    format_dashboard,
    format_session_summary,
    format_bye_section,
    format_boot_summary,
    suggest_escalation,
    main,
    FEEDBACK_TYPES,
    PATTERN_NAMES,
    SEVERITY_ORDER,
    LOG_FILE,
)
