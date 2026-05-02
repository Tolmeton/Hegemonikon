# PROOF: [L2/互換] <- mekhane/anamnesis/hyphe_pipeline.py
"""後方互換シム: hyphe_pipeline → phantasia_pipeline

Phantasia (旧 Hyphē) に名前変更されたが、既存の import パスを維持する。
新規コードは mekhane.anamnesis.phantasia_pipeline を直接使うこと。
"""
from mekhane.anamnesis.phantasia_pipeline import (  # noqa: F401
    PhantasiaPipeline as HyphePipeline,
    DissolveResult,
    Crystal,
    RecrystallizeResult,
    DistillResult,
)

__all__ = [
    "HyphePipeline",
    "DissolveResult",
    "Crystal",
    "RecrystallizeResult",
    "DistillResult",
]
