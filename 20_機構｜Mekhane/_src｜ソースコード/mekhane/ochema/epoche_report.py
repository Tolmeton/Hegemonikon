# PROOF: [L2/インフラ] <- mekhane/ochema/epoche_report.py Krisis 系エポケ回収
# REASON: [auto] 初回実装 (2026-04-02)
# PURPOSE: ツールループが max_iterations で打ち切られたときの構造化レポート
"""Epoche report — structured handoff when the tool loop stops before natural completion.

max_iterations に到達した時点で何が起きているか:
- 最後のイテレーションのツールは **実行済み** (結果も取得済み)
- しかしモデルはその結果を **統合する機会がなかった**
- つまり「未解決」ではなく「統合保留 (pending synthesis)」
"""

from __future__ import annotations

import json
from typing import Any

from mekhane.ochema.types import LLMResponse


# REASON: [auto] 関数 build_max_iterations_epoche_response の実装が必要だったため
def build_max_iterations_epoche_response(
    *,
    max_iterations: int,
    last_tool_calls: list[dict[str, Any]],
    total_usage: dict[str, Any],
    model: str,
) -> LLMResponse:
    """max_iterations 到達時の ``LLMResponse`` を構築する。

    ``last_tool_calls`` は最後のイテレーションで実行されたツール呼出。
    これらはツール側では完了しているが、モデルがその結果を
    統合応答に反映する前にループが打ち切られた。
    """
    executed: list[dict[str, Any]] = []
    for fc in last_tool_calls or []:
        row: dict[str, Any] = {
            "name": fc.get("name", ""),
            "args": fc.get("args", {}),
        }
        if fc.get("id") is not None:
            row["id"] = fc["id"]
        executed.append(row)

    payload = {
        "epoche_report": {
            "reason": "max_iterations_reached",
            "max_iterations": max_iterations,
            "last_executed_tool_calls": executed,
            "synthesis_status": "pending",
            "recommended_next_actions": [
                "直近のツール結果を踏まえてフォローアップ指示を送り、会話を継続する。",
                "1ターンあたりのツール呼出を減らす、または max_iterations を増やす。",
            ],
        }
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    return LLMResponse(
        text=text,
        model=model,
        token_usage=total_usage,
        pending_synthesis=executed if executed else None,
    )


# REASON: [auto] 関数 build_max_iterations_epoche_response_claude の実装が必要だったため
def build_max_iterations_epoche_response_claude(
    *,
    max_iterations: int,
    last_tool_calls: list[dict[str, Any]],
    model: str,
) -> LLMResponse:
    """Claude テキスト経路用 (token_usage は空辞書)。"""
    return build_max_iterations_epoche_response(
        max_iterations=max_iterations,
        last_tool_calls=last_tool_calls,
        total_usage={},
        model=model,
    )
