# PROOF: [L2/互換] <- mekhane/anamnesis/hyphe_field.py
"""後方互換シム: hyphe_field → phantasia_field

Phantasia (旧 Hyphē) に名前変更されたが、既存の import パスを維持する。
新規コードは mekhane.anamnesis.phantasia_field を直接使うこと。
"""
from mekhane.anamnesis.phantasia_field import PhantasiaField as HypheField  # noqa: F401

__all__ = ["HypheField"]
