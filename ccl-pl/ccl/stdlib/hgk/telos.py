# hgk-stdlib: Telos 族 — 認知動詞の PL 向けラッピング
"""
HGK Standard Library: Telos 族

認知動詞を汎用関数名で提供する。

使い方:
    use hgk.telos  (将来の import 構文)
    現在: from ccl.stdlib.hgk.telos import *

関数マッピング:
    /noe (認識)  → recognize   : State → Insight
    /bou (意志)  → intend      : Insight → Goal
    /zet (探求)  → explore     : Goal → Discovery
    /ene (実行)  → execute_plan: Plan → Result
    /the (観照)  → observe     : World → Percept
    /ant (検知)  → detect      : State → Delta

随伴対:
    recognize ⊣ explore  (Noēsis ⊣ Zētēsis)
    intend ⊣ execute_plan (Boulēsis ⊣ Energeia)
"""

from typing import Any, Optional


def recognize(state: Any = None, *, detail_level: int = 2) -> Any:
    """認識 (/noe) — 内部の信念を透徹し構造の核を見通す

    圏論: F (左随伴, 展開) — 情報を構造化して認識する
    随伴対: recognize ⊣ explore
    """
    if state is None:
        return {"action": "recognize", "detail": detail_level}
    return {"recognized": state, "detail": detail_level, "type": "insight"}


def intend(state: Any = None, *, detail_level: int = 2) -> Any:
    """意志 (/bou) — 何を望むかを明確化する

    圏論: H型自然変換 (recognize ↔ intend)
    随伴対: intend ⊣ execute_plan
    """
    if state is None:
        return {"action": "intend", "detail": detail_level}
    return {"intended": state, "detail": detail_level, "type": "goal"}


def explore(state: Any = None, *, detail_level: int = 2) -> Any:
    """探求 (/zet) — 何を問うべきかを発見する

    圏論: G∘F の F 成分 — 可能性空間を展開する
    随伴対: recognize ⊣ explore
    """
    if state is None:
        return {"action": "explore", "detail": detail_level}
    return {"explored": state, "detail": detail_level, "type": "discovery"}


def execute_plan(state: Any = None, *, detail_level: int = 2) -> Any:
    """実行 (/ene) — 意志を現実に具現化する

    圏論: G (右随伴, 収束) — 計画を実行に移す
    随伴対: intend ⊣ execute_plan
    """
    if state is None:
        return {"action": "execute", "detail": detail_level}
    return {"executed": state, "detail": detail_level, "type": "result"}


def observe(state: Any = None, *, detail_level: int = 2) -> Any:
    """観照 (/the) — 対象を先入観なく受容的に観照する

    圏論: S象限 (知覚的, φ_SI パイプライン入力端)
    """
    if state is None:
        return {"action": "observe", "detail": detail_level}
    return {"observed": state, "detail": detail_level, "type": "percept"}


def detect(state: Any = None, *, detail_level: int = 2) -> Any:
    """検知 (/ant) — 環境の変化・異変を検知する

    圏論: S象限 (知覚的, prior との差分検出)
    """
    if state is None:
        return {"action": "detect", "detail": detail_level}
    return {"detected": state, "detail": detail_level, "type": "delta"}


# 随伴対の登録 (ランタイムに注入)
ADJOINT_PAIRS = [
    ("recognize", "explore"),       # Noēsis ⊣ Zētēsis
    ("intend", "execute_plan"),     # Boulēsis ⊣ Energeia
]
