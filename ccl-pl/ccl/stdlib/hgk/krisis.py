# hgk-stdlib: Krisis 族
"""
HGK Standard Library: Krisis 族

関数マッピング:
    /kat (確定) → commit      : Evidence → Decision
    /epo (留保) → suspend     : Evidence → [Options]
    /pai (決断) → decide      : Options → Choice
    /dok (打診) → probe       : Hypothesis → Feedback

随伴対:
    commit ⊣ decide     (Katalēpsis ⊣ Proairesis)
    suspend ⊣ probe     (Epochē ⊣ Dokimasia)
"""

from typing import Any


def commit(state: Any = None, *, detail_level: int = 2) -> Any:
    """確定 (/kat) — 信念を固定しコミットする"""
    if state is None:
        return {"action": "commit", "detail": detail_level}
    return {"committed": state, "detail": detail_level, "type": "decision"}


def suspend(state: Any = None, *, detail_level: int = 2) -> Any:
    """留保 (/epo) — 判断を開いて複数可能性を保持する"""
    if state is None:
        return {"action": "suspend", "detail": detail_level}
    return {"suspended": state, "detail": detail_level, "type": "options"}


def decide(state: Any = None, *, detail_level: int = 2) -> Any:
    """決断 (/pai) — 確信を持って資源を投入する"""
    if state is None:
        return {"action": "decide", "detail": detail_level}
    return {"decided": state, "detail": detail_level, "type": "choice"}


def probe(state: Any = None, *, detail_level: int = 2) -> Any:
    """打診 (/dok) — 小さく一歩を打って反応を見る"""
    if state is None:
        return {"action": "probe", "detail": detail_level}
    return {"probed": state, "detail": detail_level, "type": "feedback"}


ADJOINT_PAIRS = [
    ("commit", "decide"),    # Katalēpsis ⊣ Proairesis
    ("suspend", "probe"),    # Epochē ⊣ Dokimasia
]
