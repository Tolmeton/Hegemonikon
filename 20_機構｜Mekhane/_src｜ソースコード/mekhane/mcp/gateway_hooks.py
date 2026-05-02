# PROOF: [L2/Gateway] <- mekhane/mcp/ Gateway Prostasia + Sekisho フック
"""
Gateway Hooks — FastMCP サブクラスによる Prostasia/Sekisho 統合

PURPOSE: Gateway の全ツール呼出に対して:
  1. Prostasia: BC 全文を応答末尾に注入 (L1: 環境的強制)
  2. Sekisho: Gemini Flash による行動パターン自動監査 (L0+L1)

設計原則 (Kalon):
  - FastMCP.call_tool は public メソッド → サブクラスでオーバーライド
  - Private API (_tool_manager, _call_tool_handler) に依存しない
  - MCPBase.install_prostasia_hook と同じ効果を、継承で実現
  - ON/OFF は環境変数で制御可能

Architecture:
  hgk_gateway.py: FastMCP → HGKFastMCP に差し替え
  ↓
  HGKFastMCP.call_tool()
    ↓ super().call_tool()  — 元のツール実行
    ↓ _inject_prostasia()  — BC テキスト注入
    ↓ _run_sekisho()       — 自動監査 (非 fatal)
  ↓
  応答返却
"""

import os
import sys
import time
from pathlib import Path
from typing import Any, Sequence

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent


# =============================================================================
# Configuration
# =============================================================================

# 環境変数で ON/OFF 制御
PROSTASIA_ENABLED = os.getenv("HGK_PROSTASIA_ENABLED", "1") == "1"
SEKISHO_ENABLED = os.getenv("HGK_SEKISHO_ENABLED", "1") == "1"
QUALITY_GATE_ENABLED = os.getenv("HGK_QUALITY_GATE_ENABLED", "1") == "1"
PROKATASKEVE_ENABLED = os.getenv("HGK_PROKATASKEVE_ENABLED", "1") == "1"
TOOL_POLICY_ENABLED = os.getenv("HGK_TOOL_POLICY_ENABLED", "1") == "1"

# Sekisho 自動監査の最小ログ数 (起動直後はスキップ)
SEKISHO_MIN_LOG_ENTRIES = 3

# Sekisho のツール除外リスト (自己監査の再帰防止)
SEKISHO_EXCLUDED_TOOLS = frozenset({
    "sekisho_audit", "sekisho_ping", "sekisho_history",
    "sekisho_gate", "hgk_health", "hgk_gateway_health",
})

# Prokataskeve: テキスト引数を持つフィールド名 (前処理対象)
_PROKATASKEVE_TEXT_FIELDS = frozenset({
    "message", "query", "prompt", "ccl", "context",
    "draft_response", "reasoning", "text", "content",
    "task_description", "description", "details",
})

# Prokataskeve: 除外ツール (前処理不要 / 再帰防止)
_PROKATASKEVE_EXCLUDED_TOOLS = frozenset({
    "sekisho_audit", "sekisho_ping", "sekisho_history", "sekisho_gate",
    "hgk_health", "hgk_gateway_health",
    "prokataskeve_preprocess",  # 自己再帰防止
    "sympatheia_ping", "sympatheia_peira_health",
})

# Tool Policy: ポリシーキャッシュ (起動時に1回だけ読込)
_TOOL_POLICY_STEPS: list | None = None


# =============================================================================
# Tool Policy Integration (T-14 OpenClaw)
# =============================================================================

# PURPOSE: ツール名に対するポリシーチェック。deny なら理由文字列を返す
def _check_tool_policy(tool_name: str) -> str | None:
    """gateway_policy.yaml の tool_policy セクションでツール許可/拒否を判定する。"""
    global _TOOL_POLICY_STEPS

    try:
        from mekhane.agent_guard.tool_policy import (
            apply_pipeline, build_steps_from_yaml,
        )

        # ポリシーステップのキャッシュ (起動時に1回だけYAML読込)
        if _TOOL_POLICY_STEPS is None:
            import yaml
            policy_yaml = Path(__file__).parent / "gateway_policy.yaml"
            if policy_yaml.exists():
                with open(policy_yaml, encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                tool_policy_cfg = config.get("tool_policy", {})
                if tool_policy_cfg.get("enabled", False):
                    _TOOL_POLICY_STEPS = build_steps_from_yaml(tool_policy_cfg)
                else:
                    _TOOL_POLICY_STEPS = []
            else:
                _TOOL_POLICY_STEPS = []

        if not _TOOL_POLICY_STEPS:
            return None

        result = apply_pipeline([tool_name], _TOOL_POLICY_STEPS)
        if result.denied:
            return next(iter(result.denied.values()), "Policy denied")
        return None

    except ImportError:
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[Gateway/ToolPolicy] Error (non-fatal): {e}", file=sys.stderr, flush=True)
        return None



# =============================================================================
# Prokataskeve Integration (Pre-flight)
# =============================================================================

# PURPOSE: ツール実行前に引数内のテキストフィールドを正規化・前処理する
async def _apply_prokataskeve(
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """V-001/V-011 Prokataskeve Gateway Intercept.

    テキスト引数を持つツールに対して L0 前処理 (正規化 + エンティティ抽出)
    を自動適用する。ツール実行前に呼ばれる pre-flight フック。

    設計原則:
      - 元の arguments を変更しない (コピーを返す)
      - 短いテキスト (<10文字) はスキップ (オーバーヘッド削減)
      - 例外は全て握りつぶし、元の arguments をそのまま返す (Graceful Degradation)
      - L0 のみ実行 (L1 は LLM 呼び出しを含むため Gateway では重い)
    """
    if tool_name in _PROKATASKEVE_EXCLUDED_TOOLS:
        return arguments

    # テキストフィールドを探す
    text_fields = [
        (k, v) for k, v in arguments.items()
        if k in _PROKATASKEVE_TEXT_FIELDS and isinstance(v, str) and len(v) >= 10
    ]

    if not text_fields:
        return arguments

    try:
        from mekhane.mcp.prokataskeve import PreprocessPipeline, Depth

        pipeline = PreprocessPipeline()
        modified = dict(arguments)  # shallow copy

        for field_name, field_value in text_fields:
            result = await pipeline.run(field_value, depth=Depth.L0)
            # L0 正規化のみ適用 (normalized_text)
            if result.normalized_text != field_value:
                modified[field_name] = result.normalized_text

        return modified

    except ImportError:
        # prokataskeve が利用不可 (graceful degradation)
        return arguments
    except Exception as e:  # noqa: BLE001
        print(
            f"[Gateway/Prokataskeve] Error (non-fatal): {e}",
            file=sys.stderr, flush=True,
        )
        return arguments


# =============================================================================
# Prostasia Integration
# =============================================================================

# PURPOSE: BC テキストを取得してツール応答に注入する
def _inject_prostasia(
    tool_name: str,
    arguments: dict[str, Any],
    result: Sequence[Any],
) -> Sequence[Any]:
    """Prostasia BC テキストをツール応答の末尾に注入する。

    既存の inject_into_mcp_result() を再利用する。
    これにより bypass penalty, adaptive depth, status file 等の
    全機能が Gateway でも同一動作する。
    """
    try:
        from mekhane.agent_guard.prostasia import inject_into_mcp_result

        # inject_into_mcp_result は list を受け取って list を返す
        result_list = list(result)
        result_list = inject_into_mcp_result(
            result_list, tool_name, arguments, TextContent,
        )
        return result_list

    except ImportError:
        # Prostasia が利用不可 (graceful degradation)
        return result
    except Exception as e:  # noqa: BLE001
        print(f"[Gateway/Prostasia] Error (non-fatal): {e}", file=sys.stderr, flush=True)
        return result


# =============================================================================
# Sekisho Integration
# =============================================================================

# PURPOSE: Gemini Flash による行動パターン自動監査を実行する
def _run_sekisho(
    tool_name: str,
    arguments: dict[str, Any],
    result: Sequence[Any],
) -> Sequence[Any]:
    """Sekisho L0+L1 自動監査をツール応答に注入する。

    mcp_base.py の _run_sekisho_auto_audit() を再利用。
    """
    if tool_name in SEKISHO_EXCLUDED_TOOLS:
        return result

    try:
        from mekhane.mcp.mcp_base import _run_sekisho_auto_audit

        audit_text = _run_sekisho_auto_audit(
            server_name="hgk-gateway",
            tool_name=tool_name,
            arguments=arguments or {},
        )

        if not audit_text:
            return result

        result_list = list(result)
        result_list.append(TextContent(
            type="text",
            text=audit_text,
        ))
        return result_list

    except ImportError:
        return result
    except Exception as e:  # noqa: BLE001
        print(f"[Gateway/Sekisho] Error (non-fatal): {e}", file=sys.stderr, flush=True)
        return result


# =============================================================================
# Quality Gate Integration
# =============================================================================

# PURPOSE: V-011 品質ゲートを実行し、リスクレベルに応じて L1/L2 監査を自動適用する
def _run_quality_gate(
    tool_name: str,
    arguments: dict[str, Any],
    result: Sequence[Any],
) -> Sequence[Any]:
    """V-011 品質ゲート: リスク判定 → L1/L2 自動監査。"""
    if tool_name in SEKISHO_EXCLUDED_TOOLS:
        return result

    try:
        from mekhane.mcp.quality_gate import (
            assess_risk, execute_quality_gate,
            format_gate_result, update_gate_status,
            RiskLevel,
        )

        # セッションコンテキストの取得
        session_context = {}
        try:
            from mekhane.mcp.quality_gate import MNEME_STATE
            import json
            status_file = MNEME_STATE / "sekisho_status.json"
            if status_file.exists():
                session_context = json.loads(status_file.read_text("utf-8"))
        except Exception:  # noqa: BLE001
            pass

        # リスク判定 (LOW ならスキップ)
        risk = assess_risk(tool_name, arguments or {}, session_context)
        if risk == RiskLevel.LOW:
            return result

        # 応答テキストを結合
        response_text = ""
        for item in result:
            if hasattr(item, "text"):
                response_text += item.text + "\n"

        if not response_text.strip():
            return result

        # 品質ゲート実行
        gate_result = execute_quality_gate(
            tool_name, arguments or {}, response_text, session_context,
        )

        # ステータス更新
        update_gate_status(gate_result)

        # 結果をフォーマットして応答に注入
        formatted = format_gate_result(gate_result)
        if formatted:
            result_list = list(result)
            result_list.append(TextContent(
                type="text",
                text=formatted,
            ))
            return result_list

        return result

    except ImportError:
        return result
    except Exception as e:  # noqa: BLE001
        print(f"[Gateway/QualityGate] Error (non-fatal): {e}", file=sys.stderr, flush=True)
        return result


# =============================================================================
# HGKFastMCP — FastMCP サブクラス
# =============================================================================

# PURPOSE: FastMCP を継承し、call_tool に Prostasia + Sekisho + QualityGate フックを統合する
class HGKFastMCP(FastMCP):
    """Hegemonikón Gateway FastMCP — Prostasia/Sekisho 統合版。

    FastMCP の public メソッド call_tool をオーバーライドし、
    全ツール呼出に対して BC 注入と自動監査を実行する。

    Private API (_tool_manager, _call_tool_handler) には依存しない。
    """

    async def list_tools(self) -> list:
        """ツール一覧を返す際に outputSchema を除去する。

        MCP SDK v1.26.0+ は -> str 等の戻り値型アノテーションから
        outputSchema を自動生成する (structured output 機能)。
        しかし Claude.ai 2026-03 時点ではこの機能に非対応で
        "outputSchema defined but no structured output returned" エラーが出る。

        対策: list_tools の結果から outputSchema を None にクリアし、
        クライアントに structured output を期待させない。
        """
        tools = await super().list_tools()
        for tool in tools:
            tool.outputSchema = None
        return tools

    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> Any:
        """ツール呼出 + ポリシーチェック + Prokataskeve + Prostasia + Sekisho + QualityGate。

        FastMCP の call_tool は structured output 対応時に
        (unstructured_content, structured_content) タプルを返す。
        フックは unstructured 部分にのみ適用し、structured 部分は保持する。
        """

        # -1. Tool Policy: ツール許可チェック (deny なら即拒否)
        if TOOL_POLICY_ENABLED:
            denied_reason = _check_tool_policy(name)
            if denied_reason:
                return [TextContent(type="text", text=f"⛔ Tool denied: {denied_reason}")]

        # 0. Prokataskeve: 引数テキストの前処理 (Pre-flight)
        _pre_start = time.time()
        if PROKATASKEVE_ENABLED:
            arguments = await _apply_prokataskeve(name, arguments)
        _pre_elapsed_ms = (time.time() - _pre_start) * 1000

        # 1. 元のツール実行
        _start = time.time()
        result = await super().call_tool(name, arguments)
        _elapsed_ms = (time.time() - _start) * 1000

        # 1.5. Structured output タプルの分解
        # FastMCP が (unstructured, structured) タプルを返した場合、
        # フックは unstructured 部分にのみ適用し、最後にタプルに再組立する
        structured_content = None
        if isinstance(result, tuple) and len(result) == 2:
            unstructured_result, structured_content = result
        else:
            unstructured_result = result

        # 2. Prostasia: BC テキスト注入 (unstructured 部分のみ)
        if PROSTASIA_ENABLED:
            unstructured_result = _inject_prostasia(name, arguments, unstructured_result)

        # 3. Sekisho: 自動監査 (unstructured 部分のみ)
        if SEKISHO_ENABLED:
            unstructured_result = _run_sekisho(name, arguments, unstructured_result)

        # 4. Quality Gate: V-011 多層品質保証 (unstructured 部分のみ)
        if QUALITY_GATE_ENABLED:
            unstructured_result = _run_quality_gate(name, arguments, unstructured_result)

        # 5. ログ
        print(
            f"[Gateway] {name} ({_elapsed_ms:.0f}ms)"
            f" pre={_pre_elapsed_ms:.1f}ms"
            f" policy={'ON' if TOOL_POLICY_ENABLED else 'OFF'}"
            f" prokataskeve={'ON' if PROKATASKEVE_ENABLED else 'OFF'}"
            f" prostasia={'ON' if PROSTASIA_ENABLED else 'OFF'}"
            f" sekisho={'ON' if SEKISHO_ENABLED else 'OFF'}"
            f" qgate={'ON' if QUALITY_GATE_ENABLED else 'OFF'}",
            file=sys.stderr, flush=True,
        )

        # 6. 常に unstructured のみ返す (structured content は破棄)
        # MCP SDK v1.26.0 は -> str 等から structured output を自動生成するが、
        # Claude.ai 2026-03 時点では非対応。list_tools で outputSchema=None にしても
        # call_tool のレスポンスに structuredContent が含まれると問題になりうるため、
        # ここでも structured content を除外して二重に安全性を確保する。
        return unstructured_result

