# PROOF: mekhane/agent_guard/tool_loop.py
# PURPOSE: agent_guard モジュールの tool_loop
"""
Tool Loop Guard

エージェントが同じツールを無限に呼び出す「ツールループ」を検出してブロックする機構。
OpenClaw の T-03 を移植。
"""
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

# Constants matching OpenClaw's DEFAULT_LOOP_DETECTION_CONFIG
TOOL_CALL_HISTORY_SIZE = 30
WARNING_THRESHOLD = 10
CRITICAL_THRESHOLD = 20
GLOBAL_CIRCUIT_BREAKER_THRESHOLD = 30


@dataclass
class ToolLoopDetectorsConfig:
    generic_repeat: bool = True
    known_poll_no_progress: bool = True
    ping_pong: bool = True


@dataclass
class ToolLoopConfig:
    enabled: bool = True
    history_size: int = TOOL_CALL_HISTORY_SIZE
    warning_threshold: int = WARNING_THRESHOLD
    critical_threshold: int = CRITICAL_THRESHOLD
    global_circuit_breaker_threshold: int = GLOBAL_CIRCUIT_BREAKER_THRESHOLD
    detectors: ToolLoopDetectorsConfig = field(default_factory=ToolLoopDetectorsConfig)

    def __post_init__(self):
        # 閾値の整合性を担保
        if self.critical_threshold <= self.warning_threshold:
            self.critical_threshold = self.warning_threshold + 1
        if self.global_circuit_breaker_threshold <= self.critical_threshold:
            self.global_circuit_breaker_threshold = self.critical_threshold + 1


@dataclass
class ToolCallRecord:
    tool_name: str
    args_hash: str
    timestamp: float
    tool_call_id: Optional[str] = None
    result_hash: Optional[str] = None


@dataclass
class LoopDetectionResult:
    stuck: bool
    level: Optional[Literal["warning", "critical"]] = None
    detector: Optional[Literal["generic_repeat", "known_poll_no_progress", "global_circuit_breaker", "ping_pong"]] = None
    count: int = 0
    message: str = ""
    paired_tool_name: Optional[str] = None
    warning_key: Optional[str] = None


def _stable_stringify(value: Any) -> str:
    """JSON化可能な値を決定論的に文字列化する"""
    if value is None or not isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(_stable_stringify(v) for v in value) + "]"
    
    obj_dict = value
    sorted_keys = sorted(obj_dict.keys())
    return "{" + ",".join(f"{json.dumps(k)}:{_stable_stringify(obj_dict[k])}" for k in sorted_keys) + "}"


def _stable_stringify_fallback(value: Any) -> str:
    try:
        return _stable_stringify(value)
    except Exception:  # noqa: BLE001
        if value is None:
            return "None"
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        if isinstance(value, Exception):
            return f"{type(value).__name__}:{str(value)}"
        return repr(value)


def _digest_stable(value: Any) -> str:
    serialized = _stable_stringify_fallback(value)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def hash_tool_call(tool_name: str, params: Any) -> str:
    """ツール名と引数の安定ハッシュを生成"""
    return f"{tool_name}:{_digest_stable(params)}"


def hash_tool_outcome(tool_name: str, params: Any, result: Any, error: Any) -> Optional[str]:
    """ツールの実行結果の安定ハッシュを生成"""
    if error is not None:
        # Error hashing
        err_str = str(error) if isinstance(error, Exception) else _stable_stringify_fallback(error)
        return f"error:{_digest_stable(err_str)}"
    
    if not isinstance(result, dict):
        return _digest_stable(result) if result is not None else None

    details = result.get("details", {}) if isinstance(result.get("details"), dict) else {}
    # extract_text_content
    text = ""
    if isinstance(result.get("content"), list):
        text_parts = [
            c["text"] for c in result["content"] 
            if isinstance(c, dict) and c.get("type") == "text" and isinstance(c.get("text"), str)
        ]
        text = "\n".join(text_parts).strip()
        
    return _digest_stable({"details": details, "text": text})


def is_known_poll_tool_call(tool_name: str, params: Any) -> bool:
    """進行状況が変わらないポーリング呼び出しかどうかを判定"""
    if tool_name == "command_status":
        return True
    if tool_name == "process" and isinstance(params, dict):
        action = params.get("action")
        return action in ("poll", "log")
    return False


def _get_no_progress_streak(history: List[ToolCallRecord], tool_name: str, args_hash: str) -> tuple[int, Optional[str]]:
    """同じツールと引数で、結果が変わらない (no progress) 連続回数"""
    streak = 0
    latest_result_hash = None

    for record in reversed(history):
        if record.tool_name != tool_name or record.args_hash != args_hash:
            # 他のツールの呼び出しが間に挟まってもリセットしない (OpenClaw の continue ロジック)
            # いや、OpenClaw は対象ツールの呼び出しまでは continue して、対象の連続性を見る
            continue
        
        if record.result_hash is None or record.result_hash == "":
            continue # まだ結果がないものはスキップ
            
        if latest_result_hash is None:
            latest_result_hash = record.result_hash
            streak = 1
            continue
            
        if record.result_hash != latest_result_hash:
            break # 結果が変わった = 進捗があった
            
        streak += 1

    return streak, latest_result_hash


def _get_ping_pong_streak(history: List[ToolCallRecord], current_signature: str) -> tuple[int, Optional[str], Optional[str], bool]:
    """A -> B -> A -> B のような交互呼び出しの反復を検出"""
    if not history:
        return 0, None, None, False
        
    last = history[-1]
    
    other_signature = None
    other_tool_name = None
    for call in reversed(history[:-1]):
        if call.args_hash != last.args_hash:
            other_signature = call.args_hash
            other_tool_name = call.tool_name
            break
            
    if not other_signature or not other_tool_name:
        return 0, None, None, False
        
    alternating_tail_count = 0
    for call in reversed(history):
        expected = last.args_hash if alternating_tail_count % 2 == 0 else other_signature
        if call.args_hash != expected:
            break
        alternating_tail_count += 1
        
    if alternating_tail_count < 2:
        return 0, None, None, False
        
    expected_current_signature = other_signature
    if current_signature != expected_current_signature:
        return 0, None, None, False
        
    # Check no-progress evidence
    tail_start = max(0, len(history) - alternating_tail_count)
    first_hash_a = None
    first_hash_b = None
    no_progress_evidence = True
    
    for call in history[tail_start:]:
        if not call.result_hash:
            no_progress_evidence = False
            break
            
        if call.args_hash == last.args_hash:
            if first_hash_a is None:
                first_hash_a = call.result_hash
            elif first_hash_a != call.result_hash:
                no_progress_evidence = False
                break
            continue
            
        if call.args_hash == other_signature:
            if first_hash_b is None:
                first_hash_b = call.result_hash
            elif first_hash_b != call.result_hash:
                no_progress_evidence = False
                break
            continue
            
        no_progress_evidence = False
        break
        
    if first_hash_a is None or first_hash_b is None:
        no_progress_evidence = False

    return alternating_tail_count + 1, last.tool_name, last.args_hash, no_progress_evidence


def _canonical_pair_key(sig_a: str, sig_b: str) -> str:
    return "|".join(sorted([sig_a, sig_b]))


def detect_tool_call_loop(
    history: List[ToolCallRecord],
    tool_name: str,
    params: Any,
    config: Optional[ToolLoopConfig] = None
) -> LoopDetectionResult:
    """ツールループを検出し、stuck かどうかを判定する"""
    cfg = config or ToolLoopConfig()
    if not cfg.enabled:
        return LoopDetectionResult(stuck=False)

    history = history or []
    current_hash = hash_tool_call(tool_name, params)
    no_progress_streak, latest_result_hash = _get_no_progress_streak(history, tool_name, current_hash)
    known_poll_tool = is_known_poll_tool_call(tool_name, params)
    ping_pong_count, paired_tool_name, paired_signature, pp_no_progress = _get_ping_pong_streak(history, current_hash)

    # 1. Global Circuit Breaker (最優先)
    if no_progress_streak >= cfg.global_circuit_breaker_threshold:
        return LoopDetectionResult(
            stuck=True,
            level="critical",
            detector="global_circuit_breaker",
            count=no_progress_streak,
            message=f"CRITICAL: {tool_name} has repeated identical no-progress outcomes {no_progress_streak} times. Session execution blocked by global circuit breaker to prevent runaway loops.",
            warning_key=f"global:{tool_name}:{current_hash}:{latest_result_hash or 'none'}"
        )

    # 2. Known Poll No Progress - Critical
    if known_poll_tool and cfg.detectors.known_poll_no_progress and no_progress_streak >= cfg.critical_threshold:
        return LoopDetectionResult(
            stuck=True,
            level="critical",
            detector="known_poll_no_progress",
            count=no_progress_streak,
            message=f"CRITICAL: Called {tool_name} with identical arguments and no progress {no_progress_streak} times. This appears to be a stuck polling loop. Session execution blocked to prevent resource waste.",
            warning_key=f"poll:{tool_name}:{current_hash}:{latest_result_hash or 'none'}"
        )

    # 3. Known Poll No Progress - Warning
    if known_poll_tool and cfg.detectors.known_poll_no_progress and no_progress_streak >= cfg.warning_threshold:
        return LoopDetectionResult(
            stuck=True,
            level="warning",
            detector="known_poll_no_progress",
            count=no_progress_streak,
            message=f"WARNING: You have called {tool_name} {no_progress_streak} times with identical arguments and no progress. Stop polling and either (1) increase wait time between checks, or (2) report the task as failed if the process is stuck.",
            warning_key=f"poll:{tool_name}:{current_hash}:{latest_result_hash or 'none'}"
        )

    ping_pong_warning_key = (
        f"pingpong:{_canonical_pair_key(current_hash, paired_signature)}"
        if paired_signature else f"pingpong:{tool_name}:{current_hash}"
    )

    # 4. Ping-Pong Loop - Critical
    if cfg.detectors.ping_pong and ping_pong_count >= cfg.critical_threshold and pp_no_progress:
        return LoopDetectionResult(
            stuck=True,
            level="critical",
            detector="ping_pong",
            count=ping_pong_count,
            message=f"CRITICAL: You are alternating between repeated tool-call patterns ({ping_pong_count} consecutive calls) with no progress. This appears to be a stuck ping-pong loop. Session execution blocked to prevent resource waste.",
            paired_tool_name=paired_tool_name,
            warning_key=ping_pong_warning_key
        )

    # 5. Ping-Pong Loop - Warning
    if cfg.detectors.ping_pong and ping_pong_count >= cfg.warning_threshold:
        return LoopDetectionResult(
            stuck=True,
            level="warning",
            detector="ping_pong",
            count=ping_pong_count,
            message=f"WARNING: You are alternating between repeated tool-call patterns ({ping_pong_count} consecutive calls). This looks like a ping-pong loop; stop retrying and report the task as failed.",
            paired_tool_name=paired_tool_name,
            warning_key=ping_pong_warning_key
        )

    # 6. Generic Repeat - Warning
    recent_count = sum(1 for h in history if h.tool_name == tool_name and h.args_hash == current_hash)
    if not known_poll_tool and cfg.detectors.generic_repeat and recent_count >= cfg.warning_threshold:
        return LoopDetectionResult(
            stuck=True,
            level="warning",
            detector="generic_repeat",
            count=recent_count,
            message=f"WARNING: You have called {tool_name} {recent_count} times with identical arguments. If this is not making progress, stop retrying and report the task as failed.",
            warning_key=f"generic:{tool_name}:{current_hash}"
        )

    return LoopDetectionResult(stuck=False)


def record_tool_call(
    history: List[ToolCallRecord],
    tool_name: str,
    params: Any,
    timestamp: float,
    tool_call_id: Optional[str] = None,
    config: Optional[ToolLoopConfig] = None
) -> None:
    """ツール呼び出しを記録する"""
    cfg = config or ToolLoopConfig()
    record = ToolCallRecord(
        tool_name=tool_name,
        args_hash=hash_tool_call(tool_name, params),
        timestamp=timestamp,
        tool_call_id=tool_call_id
    )
    history.append(record)
    
    if len(history) > cfg.history_size:
        history.pop(0)


def record_tool_outcome(
    history: List[ToolCallRecord],
    tool_name: str,
    params: Any,
    result: Any = None,
    error: Any = None,
    tool_call_id: Optional[str] = None,
    config: Optional[ToolLoopConfig] = None
) -> None:
    """ツールの実行結果を記録し、no-progress判定に使用する"""
    cfg = config or ToolLoopConfig()
    result_hash = hash_tool_outcome(tool_name, params, result, error)
    if not result_hash:
        return
        
    args_hash = hash_tool_call(tool_name, params)
    matched = False
    
    for call in reversed(history):
        if tool_call_id and call.tool_call_id != tool_call_id:
            continue
        if call.tool_name != tool_name or call.args_hash != args_hash:
            continue
        if call.result_hash is not None:
            continue
            
        call.result_hash = result_hash
        matched = True
        break
        
    if not matched:
        import time
        history.append(ToolCallRecord(
            tool_name=tool_name,
            args_hash=args_hash,
            timestamp=time.time(),
            tool_call_id=tool_call_id,
            result_hash=result_hash
        ))
        
    excess = len(history) - cfg.history_size
    if excess > 0:
        del history[:excess]

