# PROOF: [L2/インフラ] <- mekhane/ochema/phase0_middleware.py DeerFlow Phase 0 結合
# REASON: [auto] 初回実装 (2026-04-02)
# PURPOSE: ツールループにおける D1/D2/D7 の振る舞いを司るミドルウェア基盤
"""Phase 0 Middleware Chain for DeerFlow Adjoint Restart.

This module defines the middleware contract for tool loop interception
and recovery behaviors (Context-loss, Clarification, Dangling recovery).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from mekhane.agent_guard.compaction import (
    AnchorFact,
    detect_lost_anchors,
    extract_anchors,
    format_anchor_reinjection_message,
)


# REASON: [auto] クラス ClarificationCategory の実装が必要だったため
class ClarificationCategory(str, Enum):
    """D1: Clarification Interrupt のカテゴリ。"""
    MISSING_INFO = "missing_info"
    AMBIGUOUS_REQUIREMENT = "ambiguous_requirement"
    APPROACH_CHOICE = "approach_choice"
    RISK_CONFIRMATION = "risk_confirmation"
    SUGGESTION = "suggestion"


@dataclass(frozen=True)
# REASON: [auto] クラス MiddlewareAction の実装が必要だったため
class MiddlewareAction:
    """ミドルウェアの判定結果を表現する型。"""
    interrupt: bool
    reason: str | None = None
    clarification_category: ClarificationCategory | None = None
    interrupt_message: str | None = None


# REASON: [auto] クラス Phase0Middleware の実装が必要だったため
class Phase0Middleware:
    """ツールループの主要なフックポイントを定義する基本インターフェース。"""
    
    # REASON: [auto] 関数 before_loop の実装が必要だったため
    def before_loop(self, contents: list[dict[str, Any]]) -> None:
        """ループ開始前/各イテレーション開始前にコンテキストを検証する (D7用)。"""
        pass

# REASON: [auto] 関数 before_tool_call の実装が必要だったため
    def before_tool_call(self, tool_call: dict[str, Any]) -> MiddlewareAction:
        """ツール実行前に呼び出され、中断すべきか判定する (D1/D2予兆用)。"""
        return MiddlewareAction(interrupt=False)

# REASON: [auto] 関数 after_tool_result の実装が必要だったため
    def after_tool_result(self, tool_call: dict[str, Any], result: dict[str, Any]) -> None:
        """ツール実行後に結果を検証・記録する (D2回収状態更新用)。"""
        pass

# REASON: [auto] 関数 before_finalize の実装が必要だったため
    def before_finalize(self, contents: list[dict[str, Any]], unresolved_calls: list[dict[str, Any]]) -> None:
# REASON: [auto] クラス ChainMiddleware の実装が必要だったため
        """ループ終了時、または max_iterations 中断時に最終調整を行う (D2回収応答用)。"""
        pass


class ChainMiddleware(Phase0Middleware):
    """複数のミドルウェアを順次適用するチェイン。"""
    # REASON: [auto] クラスの初期化処理が必要だったため
    def __init__(self, middlewares: list[Phase0Middleware]):
        self.middlewares = middlewares

# REASON: [auto] 関数 before_loop の実装が必要だったため
    def before_loop(self, contents: list[dict[str, Any]]) -> None:
        for mw in self.middlewares:
            mw.before_loop(contents)

# REASON: [auto] 関数 before_tool_call の実装が必要だったため
    def before_tool_call(self, tool_call: dict[str, Any]) -> MiddlewareAction:
        for mw in self.middlewares:
            action = mw.before_tool_call(tool_call)
            if action.interrupt:
                return action
        return MiddlewareAction(interrupt=False)

# REASON: [auto] 関数 after_tool_result の実装が必要だったため
    def after_tool_result(self, tool_call: dict[str, Any], result: dict[str, Any]) -> None:
# REASON: [auto] D7: Context-loss detection
        for mw in self.middlewares:
            mw.after_tool_result(tool_call, result)

# REASON: [auto] 関数 before_finalize の実装が必要だったため
    def before_finalize(self, contents: list[dict[str, Any]], unresolved_calls: list[dict[str, Any]]) -> None:
        for mw in self.middlewares:
            mw.before_finalize(contents, unresolved_calls)


class D7ContextLossMiddleware(Phase0Middleware):
    """D7: Context-loss detection
    
    evictionによってコンテキストから重要なAnchorFactが消失していないかを
    検知し、消失していれば再注入する。
    """
    # REASON: [auto] クラスの初期化処理が必要だったため
    def __init__(self):
        self._last_anchors: list[AnchorFact] = []

# REASON: [auto] 関数 before_loop の実装が必要だったため
    def before_loop(self, contents: list[dict[str, Any]]) -> None:
        # Loop開始時に現在のanchorを抽出する
        # このメソッドはeviction前と後に呼ばれる想定
        if not self._last_anchors:
            self._last_anchors = extract_anchors(contents)
        else:
# REASON: [auto] クラス D1ClarificationMiddleware の実装が必要だったため
            lost = detect_lost_anchors(self._last_anchors, contents)
            if lost:
                msg = format_anchor_reinjection_message(lost)
                contents.append({
                    "role": "user",
                    "parts": [{"text": msg}],
                })
            # anchorsを更新
            self._last_anchors = extract_anchors(contents)


# REASON: [auto] クラス D1ClarificationMiddleware の実装が必要だったため
class D1ClarificationMiddleware(Phase0Middleware):
    """D1: Clarification 型付き中断
    
    ツール呼び出しの引数や名前に曖昧性が含まれている場合、
    実行を停止してユーザーに質問を返す。
    （今回は最小実装として、特定のルールやキーワードマッチ、または
    専用ツール呼び出しを検知して中断する）
    """
    # REASON: [auto] 関数 before_tool_call の実装が必要だったため
    def before_tool_call(self, tool_call: dict[str, Any]) -> MiddlewareAction:
        name = tool_call.get("name", "")
        # もしモデルが 'clarify' ツールなどを呼んだ場合、あるいは
        # argsに特定の曖昧性マーカーが含まれていた場合に中断する。
        # 今回の計画では "曖昧時に実行停止して質問" とあるので、
        # 簡易的に ask_clarification ツールの呼び出しをフックするか、
        # ツール呼び出し内に `missing_info` 等の文字列が含まれていれば中断する。
        
        args_str = str(tool_call.get("args", {})).lower()
        # Thambosルールと同じキーワードで中断をトリガー（最小実装）
        if "insufficient information" in args_str or "情報不足" in args_str:
            return MiddlewareAction(
                interrupt=True,
                reason="clarification_needed",
                clarification_category=ClarificationCategory.MISSING_INFO,
                interrupt_message="情報不足のため実行を中断し、明確化を求めます。"
            )
# REASON: [auto] クラス D2DanglingRecoveryMiddleware の実装が必要だったため
        # 他のカテゴリについても同様の最小実装
        if "contradictory requirements" in args_str or "矛盾する要件" in args_str:
            return MiddlewareAction(
                interrupt=True,
                reason="clarification_needed",
                clarification_category=ClarificationCategory.AMBIGUOUS_REQUIREMENT,
                interrupt_message="要件が曖昧または矛盾しているため実行を中断します。"
            )
            
        return MiddlewareAction(interrupt=False)


# REASON: [auto] クラス D2DanglingRecoveryMiddleware の実装が必要だったため
class D2DanglingRecoveryMiddleware(Phase0Middleware):
    """D2: DanglingToolCall 回収
    
    ループがmax_iterationsで打ち切られたり、予期せぬエラーで
    完了しなかったツール呼び出しを、安全にリカバリ可能な形で返す。
    """
    # REASON: [auto] 関数 before_finalize の実装が必要だったため
    def before_finalize(self, contents: list[dict[str, Any]], unresolved_calls: list[dict[str, Any]]) -> None:
        # unresolved_calls (pending_synthesis) の回収応答生成は
        # epoche_report.py 側で行われているが、Middlewareチェーンを通すため
        # ここでcontentsに回収マーカーを挿入するなどの調整を行う。
        pass
