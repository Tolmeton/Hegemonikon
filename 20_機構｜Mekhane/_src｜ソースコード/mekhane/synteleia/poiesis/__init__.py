# PROOF: [L2/インフラ] <- mekhane/synteleia/poiesis/__init__.py Poiēsis 生成層パッケージ
"""
Poiēsis (ποίησις) — 生成層 [非推奨]

⚠️ このパッケージは非推奨。mekhane.synteleia.nomoi を使用してください。
旧3エージェント → 12法 (Nomoi) エージェントに移行:
  OusiaAgent  → N01SourceAgent (S-I × P1)
  SchemaAgent → N05ProbeAgent (S-II × P1)
  HormeAgent  → N07VoiceAgent (S-II × P3)
"""

import warnings as _warnings

_warnings.warn(
    "mekhane.synteleia.poiesis は非推奨です。"
    " mekhane.synteleia.nomoi を使用してください。"
    " 詳細: synteleia_design.md §後方互換性",
    DeprecationWarning,
    stacklevel=2,
)

from .ousia_agent import OusiaAgent
from .schema_agent import SchemaAgent
from .horme_agent import HormeAgent

__all__ = ["OusiaAgent", "SchemaAgent", "HormeAgent"]
