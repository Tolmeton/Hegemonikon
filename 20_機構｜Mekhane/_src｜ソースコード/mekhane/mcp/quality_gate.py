#!/usr/bin/env python3
# PROOF: [L2/品質] <- mekhane/mcp/ V-011 多層品質保証アーキテクチャ
"""
Quality Gate — V-011 多層品質保証の環境強制エンジン

PURPOSE: Agent の意志をバイパスして品質ゲートを環境的に強制する。
  リスクレベルに応じて L0/L1/L2 の監査を自動適用する。

Architecture:
  L0 (既存): Gemini Flash パターン検知 — mcp_base._run_sekisho_auto_audit()
  L1 (NEW):  Gemini Pro BC 監査 — sekisho._call_gemini_audit() を再利用
  L2 (NEW):  Cross-Model 検証 — notify_user 直前のみ

Risk Levels:
  LOW:    読取専用ツール → L0 のみ (既存フロー)
  MEDIUM: 実行系ツール → L0 + L1 (Gemini Pro 自動 BC 監査)
  HIGH:   最終応答 / 破壊的操作 → L0 + L1 + L2 (Cross-Model)

Policy: gateway_policy.yaml の quality_gate セクションで宣言的に制御。
"""

import json
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Any

from mekhane.paths import MNEME_STATE


# =============================================================================
# Risk Level
# =============================================================================

class RiskLevel(Enum):
    """ツール呼出のリスクレベル。"""
    LOW = "low"         # L0 Flash のみ (既存)
    MEDIUM = "medium"   # + L1 Gemini Pro BC 監査
    HIGH = "high"       # + L2 Cross-Model 検証


# =============================================================================
# Default Policy (gateway_policy.yaml が読めない場合のフォールバック)
# =============================================================================

_DEFAULT_POLICY = {
    "enabled": True,
    "periodic_audit_interval": 10,
    "max_unaudited": 15,
    "high_risk_tools": [
        "notify_user",
    ],
    "medium_risk_tools": [
        "write_to_file",
        "replace_file_content",
        "multi_replace_file_content",
        "run_command",
        "hgk_ccl_execute",
        "hgk_ask",
        "hgk_ask_with_tools",
        "hgk_jules_create_task",
        "hermeneus_run",
        "hermeneus_execute",
    ],
    "low_risk_tools": [
        "sekisho_ping", "sekisho_audit", "sekisho_history", "sekisho_gate",
        "hgk_health", "hgk_status", "hgk_doxa_read", "hgk_models",
        "hgk_ls_status", "hgk_notifications", "hgk_sessions",
        "sympatheia_ping", "sympatheia_status",
        "mneme_search", "mneme_stats", "mneme_sources",
        "periskope_sources", "periskope_metrics",
    ],
    "excluded_tools": [
        "sekisho_ping", "sekisho_audit", "sekisho_history", "sekisho_gate",
    ],
}


# =============================================================================
# Policy Loader
# =============================================================================

_policy_cache: dict | None = None


def _load_quality_gate_policy() -> dict:
    """gateway_policy.yaml から品質ゲートポリシーを読み込む。"""
    global _policy_cache
    if _policy_cache is not None:
        return _policy_cache

    try:
        import yaml
        policy_file = Path(__file__).parent / "gateway_policy.yaml"
        if policy_file.exists():
            with open(policy_file, "r", encoding="utf-8") as f:
                full_policy = yaml.safe_load(f) or {}
            qg = full_policy.get("quality_gate", {})
            if qg:
                _policy_cache = qg
                return _policy_cache
    except Exception as e:  # noqa: BLE001
        print(f"[QualityGate] Policy load error: {e}", file=sys.stderr, flush=True)

    _policy_cache = _DEFAULT_POLICY
    return _policy_cache


# =============================================================================
# Risk Assessment
# =============================================================================

def assess_risk(
    tool_name: str,
    arguments: dict | None = None,
    session_context: dict | None = None,
) -> RiskLevel:
    """ツール呼出のリスクレベルを判定する。

    判定の優先順位:
      1. ポリシーの excluded_tools → スキップ (LOW 扱い)
      2. ポリシーの high_risk_tools → HIGH
      3. ポリシーの medium_risk_tools → MEDIUM
      4. ポリシーの low_risk_tools → LOW
      5. 連続未監査数が閾値超過 → MEDIUM に昇格
      6. 定期監査間隔 → MEDIUM に昇格
      7. デフォルト → LOW
    """
    policy = _load_quality_gate_policy()

    if not policy.get("enabled", True):
        return RiskLevel.LOW

    # 除外リスト
    excluded = set(policy.get("excluded_tools", []))
    if tool_name in excluded:
        return RiskLevel.LOW

    # 明示的な高リスクツール
    high_tools = set(policy.get("high_risk_tools", []))
    if tool_name in high_tools:
        return RiskLevel.HIGH

    # 明示的な中リスクツール
    medium_tools = set(policy.get("medium_risk_tools", []))
    if tool_name in medium_tools:
        return RiskLevel.MEDIUM

    # 明示的な低リスクツール
    low_tools = set(policy.get("low_risk_tools", []))
    if tool_name in low_tools:
        return RiskLevel.LOW

    # ヒューリスティック: 連続未監査数の閾値昇格
    if session_context:
        unaudited = session_context.get("consecutive_unaudited", 0)
        max_unaudited = policy.get("max_unaudited", 15)
        if unaudited >= max_unaudited:
            return RiskLevel.MEDIUM

        # 定期監査間隔
        total_calls = session_context.get("total_tool_calls", 0)
        interval = policy.get("periodic_audit_interval", 10)
        if interval > 0 and total_calls > 0 and total_calls % interval == 0:
            return RiskLevel.MEDIUM

    # デフォルト: 未知のツールは LOW
    return RiskLevel.LOW


# =============================================================================
# L1 Gate: Gemini Pro BC 監査
# =============================================================================

def run_l1_gate(
    tool_name: str,
    arguments: dict,
    response_text: str,
) -> dict:
    """L1: Gemini Pro による BC 監査を実行する。

    sekisho_mcp_server の _call_gemini_audit をインポートして再利用する。

    Returns:
        監査結果の dict。{"verdict": "PASS"/"BLOCK", "violations": [...], ...}
    """
    try:
        from mekhane.mcp.sekisho_mcp_server import _call_gemini_audit

        # 簡易な reasoning を構築
        reasoning = (
            f"Tool: {tool_name}\n"
            f"Arguments keys: {list(arguments.keys())}\n"
            f"Response length: {len(response_text)} chars"
        )

        try:
            from mekhane.agent_guard.prostasia import get_prostasia
            prostasia = get_prostasia()
            session_log_text = prostasia.session_log.get_log_text() or "(空のセッションログ)"
            selected_bcs = prostasia.select_bcs(response_text[:8000], "L2")
            bc_texts = "\n\n".join(bc.get("full_text", "") for bc in selected_bcs)
        except Exception as e:  # noqa: BLE001
            session_log_text = "(automated quality gate — Prostasia not available)"
            bc_texts = "(automated gate — BC full texts omitted/unavailable)"
            print(f"[QualityGate] Prostasia load error: {e}", file=sys.stderr, flush=True)

        result = _call_gemini_audit(
            draft_response=response_text[:8000],
            reasoning=reasoning,
            session_log=session_log_text[:4000],
            bc_full_texts=bc_texts[:16000],
        )
        return result

    except ImportError as e:
        print(f"[QualityGate] L1 import error: {e}", file=sys.stderr, flush=True)
        return {"verdict": "PASS", "confidence": 0.0, "error": str(e)}
    except Exception as e:  # noqa: BLE001
        print(f"[QualityGate] L1 error: {e}", file=sys.stderr, flush=True)
        return {"verdict": "PASS", "confidence": 0.0, "error": str(e)}


# =============================================================================
# L2 Gate: Cross-Model 検証
# =============================================================================

def run_l2_gate(
    tool_name: str,
    arguments: dict,
    response_text: str,
    session_context: dict | None = None,
) -> dict:
    """L2: Cross-Model 検証を実行する。

    Gemini Pro (L1) とは別モデルで応答を検証する。
    notify_user 等の最終応答に対してのみ実行される。

    Returns:
        検証結果の dict。{"verdict": "PASS"/"BLOCK", ...}
    """
    try:
        from mekhane.ochema.cortex_client import CortexClient

        # Gemini Flash で高速クロスチェック
        client = CortexClient(
            model="gemini-3-flash-preview",
            max_tokens=512,
        )

        try:
            from mekhane.agent_guard.prostasia import get_prostasia
            prostasia = get_prostasia()
            selected_bcs = prostasia.select_bcs(response_text[:8000], "L2")
            bc_texts = "\n\n".join(bc.get("full_text", "") for bc in selected_bcs)
        except Exception as e:  # noqa: BLE001
            bc_texts = "(automated gate — BC full texts omitted/unavailable)"
            print(f"[QualityGate] Prostasia load error: {e}", file=sys.stderr, flush=True)

        prompt = f"""あなたは品質保証レビューアです。以下の Agent 応答を検証してください。

## 行動制約 (BC)
{bc_texts[:4000]}

## 検証項目
1. 応答が日本語であること (π1)
2. 事実でないことを断言していないこと (N-3)
3. 不可逆的な操作を確認なしで実行していないこと (N-4)
4. 出典なしで外部情報を引用していないこと (N-10)
5. 上記の行動制約 (BC) に違反していないこと

## 応答テキスト (先頭4000字)

{response_text[:4000]}

## 判定

問題なし → PASS のみ
問題あり → BLOCK と1行理由を返す

判定:"""

        response = client.ask(
            message=prompt,
            system_instruction="品質検証官。PASS か BLOCK + 理由1行のみ。",
            temperature=0.0,
            timeout=15.0,
        )

        text = (response.text if hasattr(response, 'text') else str(response)).strip()

        if "BLOCK" in text.upper():
            return {
                "verdict": "BLOCK",
                "reason": text,
                "confidence": 0.7,
            }
        return {
            "verdict": "PASS",
            "confidence": 0.8,
        }

    except Exception as e:  # noqa: BLE001
        print(f"[QualityGate] L2 error: {e}", file=sys.stderr, flush=True)
        return {"verdict": "PASS", "confidence": 0.0, "error": str(e)}


# =============================================================================
# Gate Execution Orchestrator
# =============================================================================

def execute_quality_gate(
    tool_name: str,
    arguments: dict,
    response_text: str,
    session_context: dict | None = None,
) -> dict:
    """品質ゲートを実行し、結果を返す。

    Args:
        tool_name: ツール名
        arguments: ツール引数
        response_text: ツール応答のテキスト (TextContent 結合)
        session_context: セッションコンテキスト (consecutive_unaudited 等)

    Returns:
        {
            "risk_level": "low"/"medium"/"high",
            "l1_result": {...} or None,
            "l2_result": {...} or None,
            "overall_verdict": "PASS"/"BLOCK",
            "block_reason": str or None,
            "elapsed_ms": float,
        }
    """
    start = time.time()

    risk = assess_risk(tool_name, arguments, session_context)

    gate_result = {
        "risk_level": risk.value,
        "l1_result": None,
        "l2_result": None,
        "overall_verdict": "PASS",
        "block_reason": None,
        "elapsed_ms": 0.0,
    }

    if risk == RiskLevel.LOW:
        gate_result["elapsed_ms"] = (time.time() - start) * 1000
        return gate_result

    # L1: Gemini Pro BC 監査 (MEDIUM + HIGH)
    if risk in (RiskLevel.MEDIUM, RiskLevel.HIGH):
        l1 = run_l1_gate(tool_name, arguments, response_text)
        gate_result["l1_result"] = l1
        if l1.get("verdict") == "BLOCK":
            gate_result["overall_verdict"] = "BLOCK"
            gate_result["block_reason"] = l1.get("suggestions", "L1 BC 監査で違反検出")
            gate_result["elapsed_ms"] = (time.time() - start) * 1000
            return gate_result

    # L2: Cross-Model 検証 (HIGH のみ)
    if risk == RiskLevel.HIGH:
        l2 = run_l2_gate(tool_name, arguments, response_text, session_context)
        gate_result["l2_result"] = l2
        if l2.get("verdict") == "BLOCK":
            gate_result["overall_verdict"] = "BLOCK"
            gate_result["block_reason"] = l2.get("reason", "L2 Cross-Model 検証で違反検出")

    gate_result["elapsed_ms"] = (time.time() - start) * 1000
    return gate_result


# =============================================================================
# Status File Integration
# =============================================================================

def update_gate_status(gate_result: dict) -> None:
    """品質ゲート結果を sekisho_status.json に記録する。"""
    try:
        status_file = MNEME_STATE / "sekisho_status.json"
        stats: dict[str, Any] = {}
        if status_file.exists():
            try:
                stats = json.loads(status_file.read_text("utf-8"))
            except Exception:  # noqa: BLE001
                pass

        # ゲート統計の更新
        auto_audits = int(stats.get("auto_gate_audits", 0))
        stats["auto_gate_audits"] = auto_audits + 1

        if gate_result["overall_verdict"] == "BLOCK":
            auto_blocks = int(stats.get("auto_gate_blocks", 0))
            stats["auto_gate_blocks"] = auto_blocks + 1
            stats["consecutive_unaudited"] = 0
        else:
            stats["consecutive_unaudited"] = 0

        stats["last_gate_risk"] = gate_result["risk_level"]
        stats["last_gate_elapsed_ms"] = gate_result["elapsed_ms"]

        # Atomic write
        import tempfile
        import os
        MNEME_STATE.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(MNEME_STATE), suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        Path(tmp).rename(status_file)

    except Exception as e:  # noqa: BLE001
        print(f"[QualityGate] Status update error: {e}", file=sys.stderr, flush=True)


# =============================================================================
# Format Gate Result for MCP TextContent
# =============================================================================

def format_gate_result(gate_result: dict) -> str | None:
    """品質ゲート結果を TextContent 用の文字列に変換する。

    Returns:
        PASS → None (応答に追加しない)
        BLOCK → 差し止め指示テキスト
        MEDIUM PASS with findings → 簡易レポート
    """
    risk = gate_result["risk_level"]
    verdict = gate_result["overall_verdict"]
    elapsed = gate_result["elapsed_ms"]

    if verdict == "BLOCK":
        lines = [
            "\n\n---",
            "🚨 **QUALITY GATE: 差し止め**",
            f"リスク: {risk.upper()} | ⏱️ {elapsed:.0f}ms",
        ]
        if gate_result.get("block_reason"):
            lines.append(f"理由: {gate_result['block_reason']}")

        l1 = gate_result.get("l1_result")
        if l1 and l1.get("violations"):
            lines.append("\n**L1 違反:**")
            for v in l1["violations"][:3]:
                lines.append(f"  - {v.get('bc_id', '?')}: {v.get('reason', '')}")

        l2 = gate_result.get("l2_result")
        if l2 and l2.get("reason"):
            lines.append(f"\n**L2 検証:** {l2['reason']}")

        lines.append("→ 修正してから再度実行してください。")
        lines.append("---")
        return "\n".join(lines)

    # MEDIUM PASS: L1 の結果がある場合はスコアを表示
    if risk in ("medium", "high"):
        l1 = gate_result.get("l1_result")
        if l1 and l1.get("overall_score") is not None:
            score = l1["overall_score"]
            confidence = l1.get("confidence", 0.0)
            return (
                f"\n🔍 QG ({risk}) "
                f"score={score:.2f} conf={confidence:.0%} "
                f"⏱️{elapsed:.0f}ms"
            )

    return None
