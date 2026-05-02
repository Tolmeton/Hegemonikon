"""
Symphysis — 内部プロジェクト融合モジュール

PURPOSE: 複数の HGK 内部プロジェクト (CCL-IR, Dendron 等) の
  忘却関手を統合し、直交的な分析軸を提供する。

PROOF: Symphysis/ccl-ir_dendron/VISION.md
"""

from mekhane.symphysis.fusion import (
    FusionEntry,
    scan_file,
    scan_codebase,
    analyze_orthogonality,
    save_index,
    load_index,
    OrthogonalityResult,
)

__all__ = [
    "FusionEntry",
    "scan_file",
    "scan_codebase",
    "analyze_orthogonality",
    "save_index",
    "load_index",
    "OrthogonalityResult",
]
