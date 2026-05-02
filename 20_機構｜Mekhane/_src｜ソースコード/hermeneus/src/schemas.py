# PROOF: [L2/Phase2] <- hermeneus/src/schemas.py Structured Output Schema Definitions
"""
Hermēneus JSON Schema Definitions

WF 実行結果の構造化メタデータを定義する。
LLM プロバイダの Structured Outputs 機能 (Gemini responseSchema 等) と
連携し、型安全な出力を実現する。

Origin: 2026-03-01 Structured Outputs Integration
Naturalized: 2026-03-01 /fit*/ele → opt-in + provider 抽象化
"""

import copy
from typing import Dict, Any, Optional


# =============================================================================
# Core Schemas
# =============================================================================

# PURPOSE: 全 WF 共通のメタデータスキーマ
# macro_executor.py の _extract_structured_meta() と互換性を保つ
WF_META_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {"type": "string"},
            "description": "The main findings or insights from this execution step.",
        },
        "decisions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Any decisions made or conclusions reached.",
        },
        "open_questions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Questions that remain unanswered or require further investigation.",
        },
        "blind_spots": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Potential blind spots or biases identified in the execution.",
        },
        "confidence": {
            "type": "number",
            "description": "Confidence score for the output (0.0 to 1.0).",
        },
        "summary": {
            "type": "string",
            "description": "A concise 1-line summary of the execution result.",
        },
    },
    "required": ["findings", "confidence", "summary"],
}


# PURPOSE: WF_META_SCHEMA を継承し、固有フィールドを追加したスキーマを生成
def _extend_schema(extra_properties: Dict[str, Any],
                   extra_required: Optional[list] = None) -> Dict[str, Any]:
    """WF_META_SCHEMA を継承し、固有フィールドを追加したスキーマを生成する。"""
    schema = copy.deepcopy(WF_META_SCHEMA)
    schema["properties"].update(extra_properties)
    if extra_required:
        schema["required"] = list(set(schema["required"]) | set(extra_required))
    return schema


# =============================================================================
# WF 別固有スキーマ
# =============================================================================

# /pis (H2 Pistis) — 確信度評価 (メタデータ抽出向き: JSON 強制が適切)
_PIS_SCHEMA = _extend_schema({
    "confidence_breakdown": {
        "type": "object",
        "properties": {
            "evidence": {"type": "number", "description": "Evidence strength (0-1)"},
            "coherence": {"type": "number", "description": "Internal coherence (0-1)"},
            "coverage": {"type": "number", "description": "Coverage of domain (0-1)"},
        },
        "description": "Breakdown of confidence assessment.",
    },
    "risks": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Identified risks or failure modes.",
    },
})

# /fit — Fit 判定 (判定結果の構造化に適する)
_FIT_SCHEMA = _extend_schema({
    "fit_level": {
        "type": "string",
        "enum": ["superficial", "absorbed", "naturalized"],
        "description": "Fit level: superficial (red), absorbed (yellow), naturalized (green).",
    },
    "boundary_signals": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Remaining boundary signals (naming, duplication, etc).",
    },
    "empowerment_score": {
        "type": "integer",
        "description": "System empowerment score (-2 to 5).",
    },
    "break_test": {
        "type": "string",
        "description": "What breaks if removed? (nothing / tests / system).",
    },
}, extra_required=["fit_level"])

# /ene (O4 Energeia) — 行為・実行 (実行結果の記録に適する)
_ENE_SCHEMA = _extend_schema({
    "actions_taken": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Concrete actions executed.",
    },
    "artifacts_created": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Files or artifacts created/modified.",
    },
})

# /dia (A2 Krisis) — 判定・批評 (メタデータ抽出専用: LLM 応答は自然言語)
_DIA_SCHEMA = _extend_schema({
    "verdict": {
        "type": "string",
        "enum": ["accept", "reject", "conditional"],
        "description": "Final judgment: accept, reject, or conditional.",
    },
    "objections": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Counter-arguments or objections raised.",
    },
    "conditions": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Conditions for acceptance (if conditional).",
    },
}, extra_required=["verdict"])

# /noe (O1 Noēsis) — 深い認識・直観 (メタデータ抽出専用: LLM 応答は自然言語)
_NOE_SCHEMA = _extend_schema({
    "essence": {
        "type": "string",
        "description": "The essential insight or deep understanding reached.",
    },
    "abstractions": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Abstract concepts or patterns identified.",
    },
}, extra_required=["essence"])

# /zet (O3 Zētēsis) — 探求・問い (メタデータ抽出専用: LLM 応答は自然言語)
_ZET_SCHEMA = _extend_schema({
    "questions": {
        "type": "array",
        "items": {"type": "string"},
        "description": "The core questions discovered through inquiry.",
    },
    "assumptions_challenged": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Assumptions that were questioned or overturned.",
    },
}, extra_required=["questions"])


# =============================================================================
# Schema Registry — opt-in 方式
# =============================================================================

# PURPOSE: 全スキーマのレジストリ (参照・後処理用)
_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "_default": WF_META_SCHEMA,
    "noe": _NOE_SCHEMA,
    "dia": _DIA_SCHEMA,
    "zet": _ZET_SCHEMA,
    "pis": _PIS_SCHEMA,
    "fit": _FIT_SCHEMA,
    "ene": _ENE_SCHEMA,
}

# PURPOSE: LLM API に response_schema として渡してよい WF のセット
# 分析系 WF (/noe, /dia, /zet) は自然言語出力が本質であり、
# JSON 強制は出力品質を犠牲にするため除外する。
# メタデータ抽出・判定結果の構造化が主目的の WF のみ opt-in。
_STRUCTURED_OUTPUT_ENABLED: set[str] = {
    "pis",   # 確信度評価 — 数値・分類の構造化が本質
    "fit",   # Fit 判定 — 判定レベルの構造化が本質
    "ene",   # 行為・実行 — 成果物リストの構造化が有用
}


# =============================================================================
# Public API
# =============================================================================

# PURPOSE: WF ID に対応する JSON Schema を取得する (参照用)
def get_schema(wf_id: str) -> Dict[str, Any]:
    """WF ID に対応する JSON Schema を取得する。

    全 WF のスキーマを返す (参照・後処理・テスト用)。
    LLM API への送信可否は is_structured_enabled() で判定する。

    Args:
        wf_id: ワークフローID (e.g., 'noe', 'dia', '/fit+')

    Returns:
        JSON Schema オブジェクト
    """
    clean_id = wf_id.lstrip("/@").rstrip("+-^~*")
    return _SCHEMAS.get(clean_id, _SCHEMAS["_default"])


# PURPOSE: 指定 WF が Structured Output (LLM API への schema 送信) に対応しているか
def is_structured_enabled(wf_id: str) -> bool:
    """指定 WF が Structured Output に opt-in しているかを返す。

    分析系 WF (/noe, /dia, /zet) は自然言語出力が本質のため False。
    """
    clean_id = wf_id.lstrip("/@").rstrip("+-^~*")
    return clean_id in _STRUCTURED_OUTPUT_ENABLED


# PURPOSE: LLM プロバイダ用のスキーマに変換する (provider 抽象化)
def to_provider_schema(wf_id: str, provider: str = "gemini") -> Optional[Dict[str, Any]]:
    """LLM プロバイダ用のスキーマに変換する。

    opt-in されていない WF の場合は None を返す。
    provider ごとのフォーマット差異を吸収する。

    Args:
        wf_id: ワークフローID
        provider: LLM プロバイダ ('gemini', 'claude', etc.)

    Returns:
        プロバイダ互換の schema dict。opt-in 外なら None。
    """
    if not is_structured_enabled(wf_id):
        return None

    schema = copy.deepcopy(get_schema(wf_id))

    if provider == "gemini":
        # Gemini の generateContent API は responseSchema をそのまま受け入れる
        return schema
    elif provider == "claude":
        # Claude の tool_use は将来対応 (現時点で None)
        return None
    else:
        return None


# PURPOSE: 後方互換性のためのエイリアス (deprecation 予定)
def to_gemini_schema(wf_id: str) -> Optional[Dict[str, Any]]:
    """Gemini API の response_schema 形式に変換する。

    後方互換性のために残す。新規コードは to_provider_schema() を使うこと。
    """
    return to_provider_schema(wf_id, provider="gemini")


# PURPOSE: 登録済みスキーマの一覧を返す
def list_schemas() -> Dict[str, list]:
    """登録済みスキーマの一覧を返す。"""
    return {
        wf_id: list(schema.get("properties", {}).keys())
        for wf_id, schema in _SCHEMAS.items()
    }
