# PROOF: mekhane/agent_guard/context_window.py
# PURPOSE: agent_guard モジュールの context_window
"""
Context Window Guard (T-02 移植)

エージェントの利用可能なコンテキストウィンドウサイズを評価し、
警告・ブロックの判定を行う。
"""

from dataclasses import dataclass
from typing import Literal, Optional

CONTEXT_WINDOW_HARD_MIN_TOKENS = 16_000
CONTEXT_WINDOW_WARN_BELOW_TOKENS = 32_000

ContextWindowSource = Literal["model", "config", "agent_cap", "default"]

@dataclass
class ContextWindowInfo:
    tokens: int
    source: ContextWindowSource

@dataclass
class ContextWindowGuardResult(ContextWindowInfo):
    should_warn: bool
    should_block: bool

def _normalize_positive_int(value: Optional[int]) -> Optional[int]:
    if value is None or not isinstance(value, (int, float)):
        return None
    try:
        val = int(value)
        return val if val > 0 else None
    except (ValueError, TypeError):
        return None

def resolve_context_window(
    provider: str,
    model_id: str,
    model_context_window: Optional[int] = None,
    default_tokens: int = 128_000,
    config: Optional[dict] = None,
) -> ContextWindowInfo:
    """
    複数ソースから最適なコンテキストウィンドウサイズを推論する。
    優先順位:
      1. config の capabilities/max_tokens など (Ochema defaults 対応)
      2. model_context_window 引数
      3. default_tokens 引数
    最終的に agent の token cap があればそれで制限する。
    """
    config = config or {}
    
    # Try out config definitions
    from_config = None
    if isinstance(config, dict) and "capabilities" in config:
        # Example Ochema defaults style
        capabilities = config.get("capabilities", {})
        if isinstance(capabilities, dict):
            from_config = _normalize_positive_int(capabilities.get("max_tokens"))

    from_model = _normalize_positive_int(model_context_window)
    
    if from_config:
        base_info = ContextWindowInfo(tokens=from_config, source="config")
    elif from_model:
        base_info = ContextWindowInfo(tokens=from_model, source="model")
    else:
        base_info = ContextWindowInfo(tokens=max(1, int(default_tokens)), source="default")
        
    cap_tokens = None
    if isinstance(config, dict) and "agent_cap" in config:
        cap_tokens = _normalize_positive_int(config.get("agent_cap"))
    
    if cap_tokens is not None and cap_tokens < base_info.tokens:
        return ContextWindowInfo(tokens=cap_tokens, source="agent_cap")
        
    return base_info

def evaluate_guard(
    info: ContextWindowInfo,
    warn_below_tokens: Optional[int] = None,
    hard_min_tokens: Optional[int] = None,
) -> ContextWindowGuardResult:
    """
    エージェントが安全に動作できるコンテキスト余裕があるか評価する。
    """
    warn_below = max(
        1, int(warn_below_tokens) if warn_below_tokens is not None else CONTEXT_WINDOW_WARN_BELOW_TOKENS
    )
    hard_min = max(
        1, int(hard_min_tokens) if hard_min_tokens is not None else CONTEXT_WINDOW_HARD_MIN_TOKENS
    )
    
    tokens = max(0, int(info.tokens))
    
    return ContextWindowGuardResult(
        tokens=tokens,
        source=info.source,
        should_warn=0 < tokens < warn_below,
        should_block=0 < tokens < hard_min,
    )


# ─── Ochema 統合用ヘルパー ─────────────────────────────────


def resolve_from_model(model: str) -> ContextWindowInfo:
    """model_defaults.py からコンテキストウィンドウを自動解決する。

    Usage:
        from mekhane.agent_guard.context_window import resolve_from_model, evaluate_guard
        info = resolve_from_model("gemini-3-flash-preview")
        result = evaluate_guard(info)
        if result.should_block:
            raise OchemaContextWindowError(...)
    """
    from mekhane.ochema.model_defaults import get_context_window
    tokens = get_context_window(model)
    return ContextWindowInfo(tokens=tokens, source="model")


def evaluate_guard_ratio(
    info: ContextWindowInfo,
    warn_ratio: float = 0.25,
    block_ratio: float = 0.125,
    reference_tokens: Optional[int] = None,
) -> ContextWindowGuardResult:
    """比率ベースの閾値評価。

    モデルのコンテキストウィンドウに対する比率で warn/block を判定する。
    reference_tokens が指定されない場合は info.tokens 自体を参照点とする。

    Args:
        info: 評価対象のコンテキストウィンドウ情報
        warn_ratio: この比率以下で WARNING (default: 25%)
        block_ratio: この比率以下で BLOCK (default: 12.5%)
        reference_tokens: 比較基準のトークン数 (省略時は info.tokens)
    """
    ref = reference_tokens if reference_tokens is not None else info.tokens
    if ref <= 0:
        return ContextWindowGuardResult(
            tokens=info.tokens,
            source=info.source,
            should_warn=True,
            should_block=True,
        )
    
    warn_threshold = int(ref * warn_ratio)
    block_threshold = int(ref * block_ratio)
    
    return evaluate_guard(info, warn_below_tokens=warn_threshold, hard_min_tokens=block_threshold)

