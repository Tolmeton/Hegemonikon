#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/anamnesis/constants.py
# PURPOSE: Embedding モデル定数の Single Source of Truth
"""
Embedding モデル定数。

全モジュール (anamnesis, symploke, periskope, api) はここからモデル名と次元を取得する。
モデル切替はこのファイルのみ変更すればよい。

移行ログ:
  - 2026-03-15: gemini-embedding-001 (3072d) → gemini-embedding-2-preview (3072d)
                4x 入力トークン (8192), マルチモーダル対応
"""

# ── Embedding モデル ──────────────────────────────────────────
# 現行モデル (全モジュールで使用)
EMBED_MODEL: str = "gemini-embedding-2-preview"
EMBED_DIM: int = 3072

# モデル → 最大次元マッピング
MODEL_MAX_DIMS: dict[str, int] = {
    "gemini-embedding-2-preview": 3072,
    "gemini-embedding-001": 3072,
    "text-embedding-005": 768,
    "text-embedding-004": 768,
}

# ── 旧モデル (移行参考) ───────────────────────────────────────
LEGACY_EMBED_MODEL: str = "gemini-embedding-001"
LEGACY_EMBED_DIM: int = 3072
