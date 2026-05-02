from __future__ import annotations
# PROOF: [L2/インフラ] <- hgk/api/tool_loop_guard.py Tool Loop Detection (OpenClaw 移植)
"""
Tool Loop Guard — エージェントのツール呼び出しループを検出・停止する安全装置。

Origin: OpenClaw src/agents/tool-loop-detection.ts (624行) を Python に移植。
Design: 4層検知器 (generic_repeat, known_poll_no_progress, ping_pong, global_circuit_breaker)
        + SHA-256 ハッシュベースのパターンマッチング + スライディングウィンドウ (デフォルト30)

HGK Context:
    - F6 Colony / F9 Agent 並列実行の暴走防止
    - N-4 (Proposal First) と連携し、ループ検出時に実行を中断
"""


import difflib
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Literal

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

HISTORY_SIZE = 30
WARNING_THRESHOLD = 10
CRITICAL_THRESHOLD = 20
CIRCUIT_BREAKER_THRESHOLD = 30

# HGK のツール名でポーリング系と判定されるもの
KNOWN_POLL_TOOLS = frozenset({
    "command_status",
    "read_terminal",
})

# ポーリング専用アクション (process ツール用)
KNOWN_POLL_ACTIONS = frozenset({"poll", "log"})

# 非決定的ツール — 実行のたびに出力が変わる (タイムスタンプ、乱数等を含む)。
# これらのツールではハッシュ完全一致ではなくソフトマッチング (difflib) で進捗を判定する。
NON_DETERMINISTIC_TOOLS = frozenset({
    "search_web",
    "read_url_content",
    "generate_image",
})

# ソフトマッチングの類似度閾値 — この値以上なら「実質同一」と判定
SOFT_MATCH_THRESHOLD = 0.95


# =============================================================================
# Types
# =============================================================================

# PURPOSE: ツール呼び出し履歴レコード
@dataclass
class ToolCallRecord:
    """単一のツール呼び出し記録。"""
    tool_name: str
    args_hash: str
    tool_call_id: str | None = None
    result_hash: str | None = None
    result_serialized: str | None = None  # ソフトマッチング用の生テキスト
    timestamp: float = field(default_factory=time.time)


# PURPOSE: ループ検出結果
@dataclass
class LoopDetectionResult:
    """ループ検出の結果。"""
    stuck: bool = False
    level: Literal["warning", "critical"] | None = None
    detector: str | None = None
    count: int = 0
    message: str = ""
    paired_tool_name: str | None = None
    warning_key: str | None = None


# PURPOSE: ループ検出設定
@dataclass
class LoopDetectionConfig:
    """ループ検出の設定。

    Design Decision:
        enabled=True (HGK) vs enabled=false (OpenClaw).
        OpenClaw はデフォルト無効 (opt-in) だが、HGK では Colony/Agent 実行時に
        常に暴走検出が必要なため、デフォルト有効 (opt-out) を選択。
        API ルーター統合時に Config で制御する想定。
    """
    enabled: bool = True
    history_size: int = HISTORY_SIZE
    warning_threshold: int = WARNING_THRESHOLD
    critical_threshold: int = CRITICAL_THRESHOLD
    circuit_breaker_threshold: int = CIRCUIT_BREAKER_THRESHOLD
    detect_generic_repeat: bool = True
    detect_poll_no_progress: bool = True
    detect_ping_pong: bool = True

    def __post_init__(self):
        # 閾値の単調増加を保証
        if self.critical_threshold <= self.warning_threshold:
            self.critical_threshold = self.warning_threshold + 1
        if self.circuit_breaker_threshold <= self.critical_threshold:
            self.circuit_breaker_threshold = self.critical_threshold + 1


# =============================================================================
# Hash Functions
# =============================================================================

# PURPOSE: 決定的な JSON 文字列化 (キーソート済み)
def _stable_stringify(value: Any) -> str:
    """オブジェクトをキーソート済み JSON 文字列に変換。

    OpenClaw の stableStringify() の Python 実装。
    json.dumps(sort_keys=True) で十分だが、
    型の不一致 (set, bytes 等) にも対応する。
    """
    try:
        return json.dumps(value, sort_keys=True, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)


# PURPOSE: SHA-256 ハッシュで同一性を高速判定
def _digest(value: Any) -> str:
    """値の SHA-256 ハッシュを返す。"""
    serialized = _stable_stringify(value)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


# PURPOSE: MCP content 配列からテキストを抽出 (OpenClaw extractTextContent 移植)
def _extract_text_content(result: Any) -> str:
    """MCP ToolResult の content 配列からテキスト部分を結合して返す。

    OpenClaw の extractTextContent() に対応。
    MCP 形式: {"content": [{"type": "text", "text": "..."}]}
    """
    if not isinstance(result, dict) or not isinstance(result.get("content"), list):
        return ""
    texts = []
    for entry in result["content"]:
        if (
            isinstance(entry, dict)
            and isinstance(entry.get("type"), str)
            and isinstance(entry.get("text"), str)
        ):
            texts.append(entry["text"])
    return "\n".join(texts).strip()


# PURPOSE: エラーを堅牢にフォーマット (OpenClaw formatErrorForHash 移植)
def _format_error_for_hash(error: Any) -> str:
    """エラー値をハッシュ用文字列に変換。型安全。"""
    if isinstance(error, Exception):
        return error.args[0] if error.args else type(error).__name__
    if isinstance(error, str):
        return error
    if isinstance(error, (int, float, bool)):
        return str(error)
    return _stable_stringify(error)


# PURPOSE: ポーリングツール判定 (OpenClaw isKnownPollToolCall 移植)
def _is_known_poll_tool(tool_name: str, params: Any) -> bool:
    """ツール名とパラメータからポーリングツールかどうかを判定。

    command_status は無条件でポーリング扱い。
    process ツールは action が poll/log の場合のみ。
    """
    if tool_name in KNOWN_POLL_TOOLS:
        return True
    if tool_name != "process" or not isinstance(params, dict):
        return False
    return params.get("action") in KNOWN_POLL_ACTIONS


# PURPOSE: ツール呼び出しのパターンハッシュ (ツール名+引数)
def hash_tool_call(tool_name: str, params: Any) -> str:
    """ツール名とパラメータからパターンハッシュを生成。"""
    return f"{tool_name}:{_digest(params)}"


# PURPOSE: ツール結果のハッシュ (進捗の有無を判定)
def hash_tool_outcome(
    tool_name: str,
    params: Any,
    result: Any = None,
    error: Any = None,
) -> str | None:
    """ツール結果からハッシュを生成。進捗の有無を判定するために使用。

    OpenClaw の hashToolOutcome() を忠実に移植:
    - エラー: _format_error_for_hash で堅牢にフォーマット
    - ポーリング (process poll/log): アクション固有フィールドのみ抽出
    - 一般ツール: details + text の2要素でハッシュ
    """
    if error is not None:
        return f"error:{_digest(_format_error_for_hash(error))}"

    if result is None:
        return None

    if not isinstance(result, dict):
        return _digest(result)

    details = result.get("details", {})
    if not isinstance(details, dict):
        details = {}
    text = _extract_text_content(result)

    # process ツールの poll/log アクションは固有フィールドのみ抽出
    if _is_known_poll_tool(tool_name, params) and tool_name == "process" and isinstance(params, dict):
        action = params.get("action")
        if action == "poll":
            return _digest({
                "action": action,
                "status": details.get("status"),
                "exitCode": details.get("exitCode"),
                "exitSignal": details.get("exitSignal"),
                "aggregated": details.get("aggregated"),
                "text": text,
            })
        if action == "log":
            return _digest({
                "action": action,
                "status": details.get("status"),
                "totalLines": details.get("totalLines"),
                "totalChars": details.get("totalChars"),
                "truncated": details.get("truncated"),
                "exitCode": details.get("exitCode"),
                "exitSignal": details.get("exitSignal"),
                "text": text,
            })

    # 一般ツール: details + text の構造でハッシュ (OpenClaw L226-229 と同一)
    return _digest({
        "details": details,
        "text": text,
    })


# =============================================================================
# Streak Detection (内部関数)
# =============================================================================

# PURPOSE: 2つのシリアライズ済みテキストのソフトマッチング (Entropy ベース進捗計測)
def _is_soft_match(text_a: str | None, text_b: str | None) -> bool:
    """2つのテキストが実質的に同一かどうかを判定。

    difflib.SequenceMatcher を使用し、ratio が SOFT_MATCH_THRESHOLD 以上なら
    「進捗なし」と判定。タイムスタンプや微小な乱数の差異を吸収する。
    """
    if text_a is None or text_b is None:
        return text_a == text_b
    if text_a == text_b:
        return True
    # 長すぎるテキストは先頭2000文字で比較 (パフォーマンス対策)
    a = text_a[:2000]
    b = text_b[:2000]
    return difflib.SequenceMatcher(None, a, b).ratio() >= SOFT_MATCH_THRESHOLD


# PURPOSE: 同一ツール+引数での「進捗なし」連続回数を計算
def _get_no_progress_streak(
    history: list[ToolCallRecord],
    tool_name: str,
    args_hash: str,
) -> tuple[int, str | None]:
    """結果ハッシュが同一のまま繰り返された回数を返す。

    非決定的ツール (NON_DETERMINISTIC_TOOLS) ではハッシュ完全一致ではなく
    difflib ソフトマッチングで「実質同一」を判定する。

    Returns:
        (streak_count, latest_result_hash)
    """
    streak = 0
    latest_hash: str | None = None
    latest_serialized: str | None = None
    use_soft_match = tool_name in NON_DETERMINISTIC_TOOLS

    for record in reversed(history):
        if record.tool_name != tool_name or record.args_hash != args_hash:
            continue
        if not record.result_hash:
            continue
        if latest_hash is None:
            latest_hash = record.result_hash
            latest_serialized = record.result_serialized
            streak = 1
            continue

        # 完全一致チェック (高速パス)
        if record.result_hash == latest_hash:
            streak += 1
            continue

        # ソフトマッチング (非決定的ツールのみ)
        if use_soft_match and _is_soft_match(record.result_serialized, latest_serialized):
            streak += 1
            continue

        break

    return streak, latest_hash


# PURPOSE: A↔B ツール交互呼び出しパターンを検出
def _get_ping_pong_streak(
    history: list[ToolCallRecord],
    current_signature: str,
) -> tuple[int, str | None, str | None, bool]:
    """交互呼び出しパターンの検出。

    Returns:
        (alternating_count, paired_tool_name, paired_signature, no_progress_evidence)
    """
    if not history:
        return 0, None, None, False

    last = history[-1]

    # 直近と異なるシグネチャを探す
    other_signature: str | None = None
    other_tool_name: str | None = None
    for record in reversed(history[:-1]):
        if record.args_hash != last.args_hash:
            other_signature = record.args_hash
            other_tool_name = record.tool_name
            break

    if not other_signature or not other_tool_name:
        return 0, None, None, False

    # 末尾からの交互パターン長を計算
    alternating_count = 0
    for record in reversed(history):
        expected = last.args_hash if alternating_count % 2 == 0 else other_signature
        if record.args_hash != expected:
            break
        alternating_count += 1

    if alternating_count < 2:
        return 0, None, None, False

    # 現在のシグネチャが交互パターンの次に期待されるものか確認
    if current_signature != other_signature:
        return 0, None, None, False

    # 進捗なし証拠の確認: 両サイドの結果ハッシュが全て同一か
    tail_start = max(0, len(history) - alternating_count)
    first_hash_a: str | None = None
    first_hash_b: str | None = None
    no_progress = True

    for record in history[tail_start:]:
        if not record.result_hash:
            no_progress = False
            break
        if record.args_hash == last.args_hash:
            if first_hash_a is None:
                first_hash_a = record.result_hash
            elif first_hash_a != record.result_hash:
                no_progress = False
                break
        elif record.args_hash == other_signature:
            if first_hash_b is None:
                first_hash_b = record.result_hash
            elif first_hash_b != record.result_hash:
                no_progress = False
                break
        else:
            no_progress = False
            break

    if not first_hash_a or not first_hash_b:
        no_progress = False

    return alternating_count + 1, last.tool_name, last.args_hash, no_progress


# PURPOSE: ping-pong ペアの正規化キー (OpenClaw canonicalPairKey 移植)
def _canonical_pair_key(signature_a: str, signature_b: str) -> str:
    """2つのシグネチャをソートして結合。ペアの順序に依存しない一意キーを生成。"""
    return "|".join(sorted([signature_a, signature_b]))


# =============================================================================
# Main Guard Class
# =============================================================================

# PURPOSE: ツール呼び出しループの検出・記録・統計を提供する安全装置
class ToolLoopGuard:
    """ツール呼び出しループを検出する安全装置。

    Usage:
        guard = ToolLoopGuard()

        # ツール呼び出し前にチェック
        result = guard.detect(tool_name="grep_search", params={"query": "foo"})
        if result.stuck:
            if result.level == "critical":
                raise RuntimeError(result.message)
            else:
                logger.warning(result.message)

        # ツール呼び出しを記録
        guard.record_call(tool_name="grep_search", params={"query": "foo"})

        # ツール結果を記録 (進捗判定用)
        guard.record_outcome(
            tool_name="grep_search",
            params={"query": "foo"},
            result={"output": "..."},
        )
    """

    def __init__(self, config: LoopDetectionConfig | None = None):
        self.config = config or LoopDetectionConfig()
        self._history: list[ToolCallRecord] = []

    @property
    def history(self) -> list[ToolCallRecord]:
        """現在の呼び出し履歴 (読み取り専用)。"""
        return self._history

    def reset(self) -> None:
        """履歴をクリア。"""
        self._history.clear()

    # ----- Recording -----

    def record_call(
        self,
        tool_name: str,
        params: Any,
        tool_call_id: str | None = None,
    ) -> None:
        """ツール呼び出しを履歴に記録 (呼び出し前)。"""
        self._history.append(ToolCallRecord(
            tool_name=tool_name,
            args_hash=hash_tool_call(tool_name, params),
            tool_call_id=tool_call_id,
        ))

        # スライディングウィンドウ
        if len(self._history) > self.config.history_size:
            self._history.pop(0)

    def record_outcome(
        self,
        tool_name: str,
        params: Any,
        result: Any = None,
        error: Any = None,
        tool_call_id: str | None = None,
    ) -> None:
        """ツール結果を履歴に記録 (呼び出し後)。"""
        result_hash = hash_tool_outcome(tool_name, params, result, error)
        if not result_hash:
            return

        # ソフトマッチング用のシリアライズ済みテキストを保存
        result_serialized: str | None = None
        if tool_name in NON_DETERMINISTIC_TOOLS:
            result_serialized = _stable_stringify(result)

        args_hash = hash_tool_call(tool_name, params)
        matched = False

        # 対応する呼び出しレコードを逆順で検索
        for record in reversed(self._history):
            if tool_call_id and record.tool_call_id != tool_call_id:
                continue
            if record.tool_name != tool_name or record.args_hash != args_hash:
                continue
            if record.result_hash is not None:
                continue
            record.result_hash = result_hash
            record.result_serialized = result_serialized
            matched = True
            break

        # 対応するレコードが見つからない場合は新規追加
        if not matched:
            self._history.append(ToolCallRecord(
                tool_name=tool_name,
                args_hash=args_hash,
                tool_call_id=tool_call_id,
                result_hash=result_hash,
                result_serialized=result_serialized,
            ))

        # スライディングウィンドウ
        if len(self._history) > self.config.history_size:
            excess = len(self._history) - self.config.history_size
            del self._history[:excess]

    # ----- Detection -----

    def detect(self, tool_name: str, params: Any) -> LoopDetectionResult:
        """ツール呼び出し前にループを検出する。

        4層検知器を優先順位順に評価:
        1. global_circuit_breaker (最優先)
        2. known_poll_no_progress (critical → warning)
        3. ping_pong (critical → warning)
        4. generic_repeat (warning のみ)
        """
        if not self.config.enabled:
            return LoopDetectionResult()

        current_hash = hash_tool_call(tool_name, params)
        no_progress_count, latest_result = _get_no_progress_streak(
            self._history, tool_name, current_hash,
        )
        is_poll = _is_known_poll_tool(tool_name, params)
        pp_count, pp_paired, pp_paired_sig, pp_no_progress = _get_ping_pong_streak(
            self._history, current_hash,
        )

        cfg = self.config

        # --- Layer 1: Global Circuit Breaker ---
        if no_progress_count >= cfg.circuit_breaker_threshold:
            msg = (
                f"CRITICAL: {tool_name} を同一引数・同一結果で "
                f"{no_progress_count} 回繰り返しました。"
                f"グローバルサーキットブレーカーにより実行を停止します。"
            )
            logger.error(msg)
            return LoopDetectionResult(
                stuck=True,
                level="critical",
                detector="global_circuit_breaker",
                count=no_progress_count,
                message=msg,
                warning_key=f"global:{tool_name}:{current_hash}:{latest_result or 'none'}",
            )

        # --- Layer 2: Known Poll No Progress ---
        if is_poll and cfg.detect_poll_no_progress:
            if no_progress_count >= cfg.critical_threshold:
                msg = (
                    f"CRITICAL: {tool_name} を同一引数・進捗なしで "
                    f"{no_progress_count} 回ポーリングしました。"
                    f"ポーリングループが停止しています。"
                )
                logger.error(msg)
                return LoopDetectionResult(
                    stuck=True,
                    level="critical",
                    detector="known_poll_no_progress",
                    count=no_progress_count,
                    message=msg,
                    warning_key=f"poll:{tool_name}:{current_hash}:{latest_result or 'none'}",
                )

            if no_progress_count >= cfg.warning_threshold:
                msg = (
                    f"WARNING: {tool_name} を同一引数で "
                    f"{no_progress_count} 回ポーリングしましたが進捗がありません。"
                    f"待機時間を増やすか、タスク失敗を報告してください。"
                )
                logger.warning(msg)
                return LoopDetectionResult(
                    stuck=True,
                    level="warning",
                    detector="known_poll_no_progress",
                    count=no_progress_count,
                    message=msg,
                    warning_key=f"poll:{tool_name}:{current_hash}:{latest_result or 'none'}",
                )

        # --- Layer 3: Ping-Pong ---
        # warningKey: canonicalPairKey でペア順序を安定化 (OpenClaw L435-437)
        pp_warning_key = (
            f"pingpong:{_canonical_pair_key(current_hash, pp_paired_sig)}"
            if pp_paired_sig
            else f"pingpong:{tool_name}:{current_hash}"
        )

        if cfg.detect_ping_pong and pp_count >= cfg.critical_threshold and pp_no_progress:
            msg = (
                f"CRITICAL: ツール呼び出しが交互パターンで "
                f"{pp_count} 回繰り返されています (進捗なし)。"
                f"Ping-pong ループを検出しました。実行を停止します。"
            )
            logger.error(msg)
            return LoopDetectionResult(
                stuck=True,
                level="critical",
                detector="ping_pong",
                count=pp_count,
                message=msg,
                paired_tool_name=pp_paired,
                warning_key=pp_warning_key,
            )

        if cfg.detect_ping_pong and pp_count >= cfg.warning_threshold:
            msg = (
                f"WARNING: ツール呼び出しが交互パターンで "
                f"{pp_count} 回繰り返されています。"
                f"Ping-pong ループの可能性があります。"
            )
            logger.warning(msg)
            return LoopDetectionResult(
                stuck=True,
                level="warning",
                detector="ping_pong",
                count=pp_count,
                message=msg,
                paired_tool_name=pp_paired,
                warning_key=pp_warning_key,
            )

        # --- Layer 4: Generic Repeat ---
        # Design: outcome (result_hash) が記録されている場合は
        # no_progress_streak で「進捗あり/なし」を判定する。
        # outcome がない場合 (record_call のみ) は args_hash 一致回数で判定。
        # これにより決定的ツールで結果が毎回異なる場合の誤検知を防ぎつつ、
        # outcome 未記録のケースでも従来通り検知できる。
        if not is_poll and cfg.detect_generic_repeat:
            # outcome が記録されたレコードがあるか確認
            has_outcomes = any(
                r.result_hash is not None
                for r in self._history
                if r.tool_name == tool_name and r.args_hash == current_hash
            )
            if has_outcomes:
                # 進捗ベース: 結果が変化していれば stuck ではない
                effective_count = no_progress_count
            else:
                # 回数ベース (従来互換): outcome なしでは単純に呼び出し回数
                effective_count = sum(
                    1 for r in self._history
                    if r.tool_name == tool_name and r.args_hash == current_hash
                )
            if effective_count >= cfg.warning_threshold:
                msg = (
                    f"WARNING: {tool_name} を同一引数で "
                    f"{effective_count} 回呼び出しました。"
                    f"進捗がなければ再試行を停止してください。"
                )
                logger.warning(msg)
                return LoopDetectionResult(
                    stuck=True,
                    level="warning",
                    detector="generic_repeat",
                    count=effective_count,
                    message=msg,
                    warning_key=f"generic:{tool_name}:{current_hash}",
                )

        return LoopDetectionResult()

    # ----- Statistics -----

    def get_stats(self) -> dict[str, Any]:
        """デバッグ/監視用の統計情報。"""
        patterns: dict[str, dict[str, Any]] = {}
        for record in self._history:
            key = record.args_hash
            if key in patterns:
                patterns[key]["count"] += 1
            else:
                patterns[key] = {"tool_name": record.tool_name, "count": 1}

        most_frequent = max(patterns.values(), key=lambda p: p["count"]) if patterns else None

        return {
            "total_calls": len(self._history),
            "unique_patterns": len(patterns),
            "most_frequent": most_frequent,
        }
