from __future__ import annotations
# PROOF: model_defaults — 全モジュールが参照するモデル名の唯一の真実
# PURPOSE: モデル世代交代時に1ファイルの変更で全体を更新可能にする
"""
Hegemonikón Model Defaults — モデル名の唯一の真実源 (Single Source of Truth)

全モジュールはここからインポートしてデフォルトモデルを参照する。
モデル世代が変わった時、このファイルだけを変更すれば全体に伝播する。

使い方:
    from mekhane.ochema.model_defaults import FLASH, PRO

    client = CortexClient(model=FLASH)
    # or
    def my_func(model: str = FLASH):
        ...

現行モデル基準 (2026-02 時点):
    Google:    Gemini 3.1 Pro (最高性能), Gemini 3 Flash (高速)
    Anthropic: Claude Opus 4.6 (最高性能), Claude Sonnet 4.6 (高速)
"""

# ─── Google Gemini ────────────────────────────────────────────
FLASH = "gemini-3-flash-preview"       # 高速推論。日常タスク、軽量処理
PRO = "gemini-3.1-pro-preview"         # 最高性能。深い推論、コード生成

# ─── Anthropic Claude ─────────────────────────────────────────
OPUS = "claude-opus-4-20250514"        # 最高性能。深い分析、長文
SONNET = "claude-sonnet-4-20250514"    # 高速・高品質。日常タスク

# ─── Vertex AI (ADC 認証) ─────────────────────────────────────
VERTEX_OPUS = "claude-opus-4-6@latest"
VERTEX_SONNET = "claude-sonnet-4-6@latest"

# ─── 用途別エイリアス ─────────────────────────────────────────
DEFAULT = FLASH           # 汎用デフォルト (コスト最適)
QUALITY = PRO             # 品質重視タスク
WF_EXECUTION = PRO        # WF 実行 (hermeneus)
LIGHTWEIGHT = FLASH       # 軽量処理 (監査、圧縮等)

# ─── フォールバックチェーン (429 CAPACITY_EXHAUSTED 時) ────────
# MODEL_CAPACITY_EXHAUSTED 時にモデルを降格して再試行する順序。
# RATE_LIMIT_EXCEEDED はアカウントローテーションで対処 (cortex_api.py)。
MODEL_FALLBACK_CHAIN: dict[str, list[str]] = {
    PRO: [FLASH],                                                   # 3.1-pro → 3-flash
    "gemini-3-pro-preview": [FLASH],                                # 3-pro → 3-flash
    "gemini-3.1-pro-preview_vertex": ["gemini-3-flash-preview_vertex"],
    "gemini-3-pro-preview_vertex": ["gemini-3-flash-preview_vertex"],
}

# ─── Circuit Breaker (絶対タイムアウト) ─────────────────────
# リトライ + フォールバック全体の wall-clock 制限。
# これを超えたら即座に CortexAPIError を raise し、Hang を防ぐ。
CIRCUIT_BREAKER_TIMEOUT = 90.0       # ask() 全体 (リトライ + モデルフォールバック)
CIRCUIT_BREAKER_TIMEOUT_STREAM = 120.0  # ask_stream() (ストリーミングは接続確立まで時間がかかる)

# ─── Context Window Sizes (トークン数) ─────────────────────
# 各モデルの最大コンテキストウィンドウ。
# Agent Guard (context_window.py) が参照し、warn/block 判定に使用。
# 情報源: 各プロバイダの公式ドキュメント (2026-03 時点)
MODEL_CONTEXT_WINDOWS: dict[str, int] = {
    # Gemini
    FLASH: 1_000_000,
    PRO: 1_000_000,
    "gemini-3-flash-preview_vertex": 1_000_000,
    "gemini-3.1-pro-preview_vertex": 1_000_000,
    # Claude (via Anthropic API)
    OPUS: 200_000,
    SONNET: 200_000,
    # Claude (via Vertex AI)
    VERTEX_OPUS: 200_000,
    VERTEX_SONNET: 200_000,
}

DEFAULT_CONTEXT_WINDOW = 128_000  # 未知のモデルのフォールバック


def get_context_window(model: str) -> int:
    """モデルのコンテキストウィンドウサイズを返す。未知のモデルは DEFAULT_CONTEXT_WINDOW。"""
    return MODEL_CONTEXT_WINDOWS.get(model, DEFAULT_CONTEXT_WINDOW)

