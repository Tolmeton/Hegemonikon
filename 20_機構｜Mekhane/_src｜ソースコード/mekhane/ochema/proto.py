from __future__ import annotations

from typing import Any
# PROOF: [L2/インフラ] <- mekhane/ochema/ v8 proto 定義一元管理。unit test + CLI + MCP で検証済み
# PURPOSE: Antigravity LS の ConnectRPC proto 定義を一元管理する
# REASON: scripts/ (実験) と ochema/ (正式) が同じ v8 proto 知識を共有し、
#         Creator が proto を更新するとき 1 箇所だけ変えれば済むようにする
"""Antigravity Language Server — Proto Definitions (v8).

LS の ConnectRPC JSON エンドポイント、ペイロード構造、モデル定数を定義。
Cortex API リバースエンジニアリングの成果を集約する単一ソース。

WARNING: ToS グレーゾーン。実験用途限定。公開禁止。
"""



# --- RPC Endpoints ---

RPC_BASE = "exa.language_server_pb.LanguageServerService"

# Core 4-Step Flow
RPC_START_CASCADE = f"{RPC_BASE}/StartCascade"
RPC_SEND_MESSAGE = f"{RPC_BASE}/SendUserCascadeMessage"
RPC_GET_TRAJECTORIES = f"{RPC_BASE}/GetAllCascadeTrajectories"
RPC_GET_STEPS = f"{RPC_BASE}/GetCascadeTrajectorySteps"

# Status & Config
RPC_GET_STATUS = f"{RPC_BASE}/GetUserStatus"
RPC_MODEL_CONFIG = f"{RPC_BASE}/GetCascadeModelConfigData"
RPC_EXPERIMENT_STATUS = f"{RPC_BASE}/GetStaticExperimentStatus"
RPC_USER_MEMORIES = f"{RPC_BASE}/GetUserMemories"


# --- IDE Metadata (v8) ---

IDE_METADATA = {
    "ideName": "antigravity",
    "ideVersion": "1.107.0",
    "extensionVersion": "0.2.0",
}

# CortexTrajectorySource enum (from extension.js proto3)
#   0=UNSPECIFIED, 1=CASCADE_CLIENT, 2=EXPLAIN_PROBLEM,
#   12=INTERACTIVE_CASCADE (IDE default), 15=SDK
SOURCE_INTERACTIVE_CASCADE = 12

# v8: trajectoryType (必須)
TRAJECTORY_TYPE = 17


# --- Model Constants ---

DEFAULT_MODEL = "MODEL_PLACEHOLDER_M35"

# Human-friendly aliases → proto enum
# SOURCE: list_models.py 2026-03-27 LS GetUserStatus から取得
MODEL_ALIASES = {
    # Claude
    "claude-sonnet": "MODEL_PLACEHOLDER_M35",        # Claude Sonnet 4.6 (Thinking)
    "claude-opus": "MODEL_PLACEHOLDER_M26",           # Claude Opus 4.6 (Thinking)
    # Gemini
    "gemini-pro": "MODEL_PLACEHOLDER_M37",            # Gemini 3.1 Pro (High)
    "gemini-pro-low": "MODEL_PLACEHOLDER_M36",        # Gemini 3.1 Pro (Low)
    "gemini-flash": "MODEL_PLACEHOLDER_M47",          # Gemini 3 Flash
    # GPT
    "gpt-oss": "MODEL_OPENAI_GPT_OSS_120B_MEDIUM",   # GPT-OSS 120B (Medium)
    # 旧 enum (後方互換)
    "gemini-3.1-pro-preview": "MODEL_PLACEHOLDER_M37",
    "gemini-3-flash-preview": "MODEL_PLACEHOLDER_M47",
}

# Timing
DEFAULT_TIMEOUT = 120  # seconds
POLL_INTERVAL = 1.0  # seconds


# --- Payload Builders (v8) ---

# PURPOSE: StartCascade RPC のペイロードを構築する。
def build_start_cascade() -> dict:
    """StartCascade ペイロードを構築する。

    v8: metadata + trajectoryType:17 が必須。
    これがないと trajectory が生成されない。
    """
    return {
        "metadata": IDE_METADATA.copy(),
        "source": SOURCE_INTERACTIVE_CASCADE,
        "trajectoryType": TRAJECTORY_TYPE,
    }


# PURPOSE: SendUserCascadeMessage RPC のペイロードを v8 仕様で構築する。
def build_send_message(cascade_id: str, text: str, model: str) -> dict:
    """SendUserCascadeMessage ペイロードを構築する。

    v8 実証済み curl 構造に準拠:
    - items: トップレベルに直接配置
    - plannerTypeConfig: {conversational: {}}
    - requestedModel: {model: "MODEL_..."} (proto enum 形式)
    """
    return {
        "cascadeId": cascade_id,
        "items": [{"text": text}],
        "cascadeConfig": {
            "plannerConfig": {
                "plannerTypeConfig": {"conversational": {}},
                "requestedModel": {"model": model},
            },
        },
    }


# --- CascadePlannerConfig Protobuf Field Map (LS binary strings 復元) ---
# SOURCE: strings language_server_linux_x64 | grep 'CascadePlannerConfig'
# フィールド番号は Go struct タグ `protobuf:"...,N,..."` から抽出。
PLANNER_CONFIG_FIELDS = {
    "conversational": 2,           # oneof plannerTypeConfig
    "no_tool_explanation": 7,      # bool (oneof)
    "max_output_tokens": 8,        # varint ⭐
    "plan_model": 12,              # bytes/string
    "truncation_threshold_tokens": 14,  # varint ⭐
    "requested_model": 15,         # bytes/string (message)
    "ephemeral_messages_config": 21,    # message
    "show_all_errors": 25,         # bool
    "google": 26,                  # oneof plannerTypeConfig
    "retry_config": 30,            # message
    "step_string_converter_config": 31,  # message
    "knowledge_config": 32,        # message
    "no_tool_summary": 33,         # bool (oneof)
    "thinking_level": 35,          # varint/enum ⭐
    "cider": 36,                   # oneof plannerTypeConfig
    "no_wait_for_previous_tools": 37,   # bool (oneof)
    "custom_agent": 39,            # oneof plannerTypeConfig
    "custom_agent_config_absolute_uri": 40,  # string (oneof)
    "prompt_section_customization_config": 41,  # message
    "customization_config": 42,    # message
}

CASCADE_CONFIG_FIELDS = {
    "planner_config": 1,           # message
    "checkpoint_config": 2,        # message
    "executor_config": 3,          # message
    "trajectory_conversion_config": 4,  # message
    "apply_model_default_override": 6,  # bool (oneof)
    "split_dynamic_prompt_sections": 8,  # bool (oneof)
    "message_config": 9,           # message
    "conversation_history_config": 111,  # message (oneof)
}


# PURPOSE: パラメータ制御付き SendUserCascadeMessage ペイロードを構築する。
def build_send_message_with_params(
    cascade_id: str,
    text: str,
    model: str,
    *,
    max_output_tokens: int | None = None,
    thinking_level: int | None = None,
    truncation_threshold_tokens: int | None = None,
    show_all_errors: bool | None = None,
    no_tool_summary: bool | None = None,
    no_tool_explanation: bool | None = None,
    no_wait_for_previous_tools: bool | None = None,
) -> dict:
    """パラメータ制御付き SendUserCascadeMessage ペイロードを構築する。

    LS バイナリ strings から復元した protobuf フィールド番号を使い、
    ConnectRPC JSON 形式で CascadePlannerConfig にフィールドを注入する。

    ConnectRPC は JSON-to-Protobuf マッピングを行うため、
    フィールド名は camelCase でもスネークケースでも受理される。

    Args:
        cascade_id: StartCascade で取得した cascade ID
        text: ユーザーメッセージ
        model: モデル enum (e.g., MODEL_PLACEHOLDER_M35)
        max_output_tokens: 最大出力トークン数 (field 8)
        thinking_level: 思考レベル enum 値 (field 35)
        truncation_threshold_tokens: コンテキスト切り詰め閾値 (field 14)
        show_all_errors: 全エラーを表示するか (field 25)
        no_tool_summary: ツール概要を省略するか (field 33)
        no_tool_explanation: ツール説明を省略するか (field 7)
        no_wait_for_previous_tools: 前のツールを待たないか (field 37)
    """
    # 基本構造 (v8 実証済み)
    planner_config: dict = {
        "plannerTypeConfig": {"conversational": {}},
        "requestedModel": {"model": model},
    }

    # パラメータ注入 (JSON field name = camelCase protobuf name)
    if max_output_tokens is not None:
        planner_config["maxOutputTokens"] = max_output_tokens
    if thinking_level is not None:
        planner_config["thinkingLevel"] = thinking_level
    if truncation_threshold_tokens is not None:
        planner_config["truncationThresholdTokens"] = truncation_threshold_tokens
    if show_all_errors is not None:
        planner_config["showAllErrors"] = show_all_errors
    if no_tool_summary is not None:
        planner_config["noToolSummary"] = no_tool_summary
    if no_tool_explanation is not None:
        planner_config["noToolExplanation"] = no_tool_explanation
    if no_wait_for_previous_tools is not None:
        planner_config["noWaitForPreviousTools"] = no_wait_for_previous_tools

    return {
        "cascadeId": cascade_id,
        "items": [{"text": text}],
        "cascadeConfig": {
            "plannerConfig": planner_config,
        },
    }


# PURPOSE: GetUserStatus RPC のペイロードを構築する。
def build_get_status() -> dict:
    """GetUserStatus ペイロードを構築する。"""
    return {
        "metadata": {
            "ideName": "antigravity",
            "extensionName": "antigravity",
            "locale": "en",
        },
    }


# PURPOSE: GetCascadeTrajectorySteps RPC のペイロードを構築する。
def build_get_steps(cascade_id: str, trajectory_id: str) -> dict:
    """GetCascadeTrajectorySteps ペイロードを構築する。"""
    return {
        "cascadeId": cascade_id,
        "trajectoryId": trajectory_id,
    }


# --- Response Parsing Helpers ---

# Step types
STEP_TYPE_PLANNER = "CORTEX_STEP_TYPE_PLANNER_RESPONSE"
STEP_STATUS_DONE = "CORTEX_STEP_STATUS_DONE"

# Turn states that unambiguously mean the assistant turn finished (no empty string).
TURN_STATES_DONE_EXPLICIT = (
    "TURN_STATE_WAITING_FOR_USER",
    "TURN_STATE_COMPLETED",
    "TURN_STATE_IDLE",
    "TURN_STATE_DONE",
)

# Backward-compat name: 旧コードは "" を完了扱いしていたが、空 turnState は推論中と区別できず
# 空本文で早期 return する原因になる。cascade_turn_complete() を使うこと。
TURN_STATES_DONE = TURN_STATES_DONE_EXPLICIT

# stopReason があれば「本文が空でも」ターン終端とみなせる値 (LS 実装差異の吸収)
STOP_REASONS_TERMINAL = frozenset(
    {
        "STOP_REASON_END_TURN",
        "STOP_REASON_MAX_TOKENS",
        "STOP_REASON_STOP_SEQUENCE",
        "END_TURN",
        "STOP",
    }
)


def _coerce_planner_text(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, dict):
        return (
            str(val.get("text") or val.get("content") or val.get("response") or "")
            .strip()
        )
    return str(val).strip()


# PURPOSE: カスケードのターンが完了したか (ポーリング終了条件)。
def cascade_turn_complete(
    turn_state: str,
    steps: list,
    min_planner_count: int,
) -> bool:
    """最後の PLANNER ステップが DONE かつ、turnState / 本文 / stopReason で完了とみなせるか。

    旧: TURN_STATES_DONE に空文字が含まれ、GetSteps が turnState 未設定のまま
    返すと応答本文なしで完了扱いになることがあった。
    """
    planner_steps = [s for s in steps if s.get("type") == STEP_TYPE_PLANNER]
    if len(planner_steps) < min_planner_count:
        return False
    last = planner_steps[-1]
    if last.get("status") != STEP_STATUS_DONE:
        return False

    done_count = sum(
        1 for s in planner_steps if s.get("status") == STEP_STATUS_DONE
    )
    if done_count < min_planner_count:
        return False

    parsed = extract_planner_response(last)
    ts = (turn_state or "").strip()

    if ts in TURN_STATES_DONE_EXPLICIT:
        return True

    if ts == "":
        if (parsed.get("text") or "").strip():
            return True
        sr = (parsed.get("stop_reason") or "").strip()
        if sr in STOP_REASONS_TERMINAL:
            return True
        return False

    return False


# PURPOSE: PLANNER_RESPONSE ステップから text/thinking/model を抽出する。
def extract_planner_response(step: dict) -> dict:
    """PLANNER_RESPONSE ステップからテキスト・thinking・model を抽出する。

    v8: generatorModel は step.metadata に格納 (fallback: plannerResponse)
    v9+: response 以外のキーに本文が入る場合のフォールバックあり

    Returns:
        {text, thinking, model, token_usage, status}
    """
    pr = step.get("plannerResponse")
    if not isinstance(pr, dict):
        pr = {}
    step_metadata = step.get("metadata", {})

    # v8: model location migration
    model = step_metadata.get("generatorModel", "")
    if not model:
        model = pr.get("generatorModel", "")  # fallback

    text = _coerce_planner_text(
        pr.get("response")
        or pr.get("modifiedResponse")
        or pr.get("finalResponse")
        or pr.get("content")
        or pr.get("text")
    )
    if not text:
        am = pr.get("assistantMessage") or pr.get("message")
        if isinstance(am, dict):
            text = _coerce_planner_text(am.get("content") or am.get("text"))
        elif isinstance(am, str):
            text = am.strip()

    return {
        "text": text,
        "thinking": pr.get("thinking", "") or "",
        "thinking_signature": pr.get("thinkingSignature", ""),
        "thinking_duration": pr.get("thinkingDuration", ""),
        "stop_reason": pr.get("stopReason", ""),
        "message_id": pr.get("messageId", ""),
        "model": model,
        "token_usage": pr.get("tokenUsage", {}),
        "status": step.get("status", ""),
    }


# PURPOSE: モデルエイリアスを proto enum に解決する。
def resolve_model(name: str) -> str:
    """モデルエイリアスを proto enum に解決する。"""
    if name in MODEL_ALIASES:
        return MODEL_ALIASES[name]
    if name.startswith("MODEL_"):
        return name
    # Fuzzy match
    lower = name.lower()
    for alias, model_id in MODEL_ALIASES.items():
        if lower in alias:
            return model_id
    return name  # Pass through, let the API validate
