# hgk-stdlib: Orexis 族
"""
HGK Standard Library: Orexis 族

関数マッピング:
    /beb (肯定) → affirm    : Evidence → Confidence
    /ele (批判) → critique   : Claim → [Issues]
    /kop (推進) → advance    : Progress → Next
    /dio (是正) → correct    : Problem → Fix

随伴対:
    affirm ⊣ advance   (Bebaiōsis ⊣ Prokopē)
    critique ⊣ correct  (Elenchos ⊣ Diorthōsis)
"""

from typing import Any


def affirm(state: Any = None, *, detail_level: int = 2) -> Any:
    """肯定 (/beb) — 信念を強化・承認する"""
    if state is None:
        return {"action": "affirm", "detail": detail_level}
    return {"affirmed": state, "detail": detail_level, "type": "confidence"}


def critique(state: Any = None, *, detail_level: int = 2) -> Any:
    """批判 (/ele) — 信念を問い直し問題を検知する"""
    if state is None:
        return {"action": "critique", "detail": detail_level}
    return {"critiqued": state, "detail": detail_level, "type": "issues"}


def advance(state: Any = None, *, detail_level: int = 2) -> Any:
    """推進 (/kop) — 成功方向をさらに前進させる"""
    if state is None:
        return {"action": "advance", "detail": detail_level}
    return {"advanced": state, "detail": detail_level, "type": "next"}


def correct(state: Any = None, *, detail_level: int = 2) -> Any:
    """是正 (/dio) — 問題を修正し方向を変える"""
    if state is None:
        return {"action": "correct", "detail": detail_level}
    return {"corrected": state, "detail": detail_level, "type": "fix"}


ADJOINT_PAIRS = [
    ("affirm", "advance"),   # Bebaiōsis ⊣ Prokopē
    ("critique", "correct"), # Elenchos ⊣ Diorthōsis
]
