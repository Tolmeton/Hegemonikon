# PROOF: [L2/インフラ] <- mekhane/mcp/gateway_tools/_utils.py A0→Gateway共有ユーティリティ
# PURPOSE: gateway_tools/ 全ドメインファイルが共有する定数、設定、トレース機能を提供。
#          hgk_gateway.py への逆インポート依存を完全解消する DI 深化の核。
"""Gateway tools shared utilities.

hgk_gateway.py から分離されたユーティリティ群。
gateway_tools/ 内のドメインファイルはここからインポートする。
hgk_gateway.py 本体は FastMCP + OAuth + 起動ロジックのみを保持する。
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


# =============================================================================
# Path Constants — paths.py が Single Source of Truth
# =============================================================================

try:
    from mekhane.paths import (
        HGK_ROOT as PROJECT_ROOT,
        MNEME_DIR,
        SESSIONS_DIR,
        HANDOFF_DIR,
        ARTIFACTS_DIR,
        INCOMING_DIR,
        PROCESSED_DIR,
    )
    _MNEME_DIR = MNEME_DIR  # backward compat alias for _trace_tool_call
except ImportError:
    # Fallback for standalone execution
    PROJECT_ROOT = Path(__file__).resolve().parents[3]
    _MNEME_DIR = Path(os.getenv("HGK_MNEME", str(MNEME_DIR)))
    MNEME_DIR = PROJECT_ROOT / "30_記憶｜Mneme"
    _MNEME_RECORDS = MNEME_DIR / "01_記録｜Records"
    SESSIONS_DIR = _MNEME_RECORDS / "b_対話｜sessions"
    HANDOFF_DIR = _MNEME_RECORDS / "a_引継｜handoff"
    ARTIFACTS_DIR = _MNEME_RECORDS / "d_成果物｜artifacts"
    INCOMING_DIR = MNEME_DIR / "incoming"
    PROCESSED_DIR = MNEME_DIR / "processed"

DOXA_DIR = ARTIFACTS_DIR
SOP_OUTPUT_DIR = MNEME_DIR / "workflows"
IDEA_DIR = MNEME_DIR / "ideas"

# Cowork
_COWORK_DIR = _MNEME_DIR / "cowork"
_COWORK_ARCHIVE = _COWORK_DIR / "_archive"
_COWORK_MAX_ACTIVE = 5  # 最新 N 件を保持


# =============================================================================
# Gateway URL (env → Tailscale auto-detect → fallback)
# =============================================================================

GATEWAY_PORT = int(os.getenv("HGK_GATEWAY_PORT", "8765"))

_env_url = os.getenv("HGK_GATEWAY_URL")
if _env_url:
    _GATEWAY_URL = _env_url
else:
    _GATEWAY_URL = f"http://localhost:{GATEWAY_PORT}"


# =============================================================================
# Policy Loader
# =============================================================================

def _load_policy() -> dict:
    """gateway_policy.yaml を読み込み、ポリシー辞書を返す。"""
    try:
        import yaml
    except ImportError:
        return {"version": "0.0", "defaults": {"max_input_size": 10000}, "tools": {}, "security": {}, "trace": {"enabled": False}}

    policy_path = Path(__file__).parent.parent / "gateway_policy.yaml"
    if not policy_path.exists():
        return {"version": "0.0", "defaults": {"max_input_size": 10000}, "tools": {}, "security": {}, "trace": {"enabled": False}}

    try:
        with open(policy_path, "r", encoding="utf-8") as f:
            policy = yaml.safe_load(f)
        return policy
    except Exception:  # noqa: BLE001
        return {"version": "0.0", "defaults": {"max_input_size": 10000}, "tools": {}, "security": {}, "trace": {"enabled": False}}


POLICY = _load_policy()


def _get_policy(tool_name: str, key: str, default=None):
    """ポリシーからツール固有の値を取得。なければ defaults → default の順。"""
    tool_policy = POLICY.get("tools", {}).get(tool_name, {})
    if key in tool_policy:
        return tool_policy[key]
    defaults = POLICY.get("defaults", {})
    if key in defaults:
        return defaults[key]
    return default


# =============================================================================
# Trace Logger
# =============================================================================

def _trace_tool_call(
    tool_name: str,
    input_size: int,
    duration_ms: float,
    success: bool,
) -> None:
    """ツール呼び出しをトレースログに記録する。"""
    trace_config = POLICY.get("trace", {})
    if not trace_config.get("enabled", False):
        return

    from datetime import timezone

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tool": tool_name,
        "input_size": input_size,
        "duration_ms": round(duration_ms, 1),
        "success": success,
    }

    trace_filename = trace_config.get("output", "gateway_trace.jsonl")
    trace_path = _MNEME_DIR / trace_filename

    try:
        _MNEME_DIR.mkdir(parents=True, exist_ok=True)

        max_mb = trace_config.get("max_file_size_mb", 10)
        if trace_path.exists() and trace_path.stat().st_size > max_mb * 1024 * 1024:
            rotated = trace_path.with_suffix(f".{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")
            trace_path.rename(rotated)

        with open(trace_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Trace log failed: {e}", file=sys.stderr)


def _estimate_input_size(*args: Any, **kwargs: Any) -> int:
    """ツール引数から入力サイズ (文字数) を推定する。"""
    total = 0
    for a in args:
        if isinstance(a, str):
            total += len(a)
    for v in kwargs.values():
        if isinstance(v, str):
            total += len(v)
    return total


def _traced(fn):
    """ツール関数にトレースを自動付与するデコレータ (sync/async 両対応)。"""
    import functools
    import asyncio
    import inspect

    if inspect.iscoroutinefunction(fn):
        @functools.wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            _start = time.time()
            input_size = _estimate_input_size(*args, **kwargs)
            try:
                result = await fn(*args, **kwargs)
                _trace_tool_call(fn.__name__, input_size, (time.time() - _start) * 1000, True)
                return result
            except Exception:  # noqa: BLE001
                _trace_tool_call(fn.__name__, input_size, (time.time() - _start) * 1000, False)
                raise
        return async_wrapper
    else:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _start = time.time()
            input_size = _estimate_input_size(*args, **kwargs)
            try:
                result = fn(*args, **kwargs)
                _trace_tool_call(fn.__name__, input_size, (time.time() - _start) * 1000, True)
                return result
            except Exception:  # noqa: BLE001
                _trace_tool_call(fn.__name__, input_size, (time.time() - _start) * 1000, False)
                raise
        return wrapper


# =============================================================================
# Shared Mutable State (ochema domain)
# =============================================================================

_ASK_RATE_LIMIT = 5
_ASK_RATE_WINDOW = 60  # seconds
_ask_timestamps: list[float] = []

_MAX_CHAT_SESSIONS = 5
_chat_sessions: dict[str, object] = {}
