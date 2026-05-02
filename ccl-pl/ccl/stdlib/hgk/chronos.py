# hgk-stdlib: Chronos 族
"""
HGK Standard Library: Chronos 族

関数マッピング:
    /hyp (想起)   → recall       : Key → Memory
    /prm (予見)   → forecast     : State → Prediction
    /ath (省察)   → reflect      : Action → Lesson
    /par (仕掛)   → prepare      : Goal → Setup

随伴対:
    recall ⊣ reflect       (Hypomnēsis ⊣ Anatheōrēsis)
    forecast ⊣ prepare     (Promētheia ⊣ Proparaskeuē)
"""

from typing import Any


def recall(state: Any = None, *, detail_level: int = 2) -> Any:
    """想起 (/hyp) — 過去の信念状態にアクセスする"""
    if state is None:
        return {"action": "recall", "detail": detail_level}
    return {"recalled": state, "detail": detail_level, "type": "memory"}


def forecast(state: Any = None, *, detail_level: int = 2) -> Any:
    """予見 (/prm) — 未来の状態を推論・予測する"""
    if state is None:
        return {"action": "forecast", "detail": detail_level}
    return {"forecast": state, "detail": detail_level, "type": "prediction"}


def reflect(state: Any = None, *, detail_level: int = 2) -> Any:
    """省察 (/ath) — 過去の行動を評価し教訓を抽出する"""
    if state is None:
        return {"action": "reflect", "detail": detail_level}
    return {"reflected": state, "detail": detail_level, "type": "lesson"}


def prepare(state: Any = None, *, detail_level: int = 2) -> Any:
    """仕掛 (/par) — 未来を形成するための先制行動をとる"""
    if state is None:
        return {"action": "prepare", "detail": detail_level}
    return {"prepared": state, "detail": detail_level, "type": "setup"}


ADJOINT_PAIRS = [
    ("recall", "reflect"),     # Hypomnēsis ⊣ Anatheōrēsis
    ("forecast", "prepare"),   # Promētheia ⊣ Proparaskeuē
]
