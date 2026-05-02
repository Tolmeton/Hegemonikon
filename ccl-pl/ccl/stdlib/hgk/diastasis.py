# hgk-stdlib: Diástasis 族
"""
HGK Standard Library: Diástasis 族

関数マッピング:
    /lys (分析)   → analyze_detail : Object → Components
    /ops (俯瞰)   → overview       : System → Map
    /akr (精密)   → refine         : Draft → Precise
    /arh (全体)   → orchestrate    : Parts → Whole

随伴対:
    analyze_detail ⊣ refine       (Analysis ⊣ Akribeia)
    overview ⊣ orchestrate        (Synopsis ⊣ Architektonikē)
"""

from typing import Any


def analyze_detail(state: Any = None, *, detail_level: int = 2) -> Any:
    """分析 (/lys) — 局所的に深く推論する"""
    if state is None:
        return {"action": "analyze_detail", "detail": detail_level}
    return {"analyzed": state, "detail": detail_level, "type": "components"}


def overview(state: Any = None, *, detail_level: int = 2) -> Any:
    """俯瞰 (/ops) — 広域的に全体を推論する"""
    if state is None:
        return {"action": "overview", "detail": detail_level}
    return {"overview": state, "detail": detail_level, "type": "map"}


def refine(state: Any = None, *, detail_level: int = 2) -> Any:
    """精密 (/akr) — 局所的に正確に行動する"""
    if state is None:
        return {"action": "refine", "detail": detail_level}
    return {"refined": state, "detail": detail_level, "type": "precise"}


def orchestrate(state: Any = None, *, detail_level: int = 2) -> Any:
    """全体 (/arh) — 広域的に一斉に行動する"""
    if state is None:
        return {"action": "orchestrate", "detail": detail_level}
    return {"orchestrated": state, "detail": detail_level, "type": "whole"}


ADJOINT_PAIRS = [
    ("analyze_detail", "refine"),     # Analysis ⊣ Akribeia
    ("overview", "orchestrate"),       # Synopsis ⊣ Architektonikē
]
