# hgk-stdlib: Methodos 族
"""
HGK Standard Library: Methodos 族

関数マッピング:
    /ske (発散)  → diverge_strategy  : Space → [Hypothesis]
    /sag (収束)  → converge_strategy : [Hypothesis] → Best
    /pei (実験)  → experiment        : Hypothesis → Evidence
    /tek (適用)  → apply_technique   : Method → Result

随伴対:
    diverge_strategy ⊣ experiment   (Skepsis ⊣ Peira)
    converge_strategy ⊣ apply_technique (Synagōgē ⊣ Tekhnē)
"""

from typing import Any


def diverge_strategy(state: Any = None, *, detail_level: int = 2) -> Any:
    """発散 (/ske) — 仮説空間を拡げ、前提を破壊する"""
    if state is None:
        return {"action": "diverge_strategy", "detail": detail_level}
    return {"diverged": state, "detail": detail_level, "type": "hypotheses"}


def converge_strategy(state: Any = None, *, detail_level: int = 2) -> Any:
    """収束 (/sag) — 仮説空間の Limit として最適構造を抽出する"""
    if state is None:
        return {"action": "converge_strategy", "detail": detail_level}
    return {"converged": state, "detail": detail_level, "type": "best"}


def experiment(state: Any = None, *, detail_level: int = 2) -> Any:
    """実験 (/pei) — 未知領域で情報を集め、仮説を検証する"""
    if state is None:
        return {"action": "experiment", "detail": detail_level}
    return {"experimented": state, "detail": detail_level, "type": "evidence"}


def apply_technique(state: Any = None, *, detail_level: int = 2) -> Any:
    """適用 (/tek) — 既知の手法を使って確実に成果を出す"""
    if state is None:
        return {"action": "apply_technique", "detail": detail_level}
    return {"applied": state, "detail": detail_level, "type": "result"}


ADJOINT_PAIRS = [
    ("diverge_strategy", "experiment"),       # Skepsis ⊣ Peira
    ("converge_strategy", "apply_technique"), # Synagōgē ⊣ Tekhnē
]
