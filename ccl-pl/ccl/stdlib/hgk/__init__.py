# hgk-stdlib — HGK 認知動詞の PL 向け標準ライブラリ
"""
CCL-PL の標準ライブラリ: HGK 認知動詞を汎用関数名で提供する。

6族 × 4動詞 (I/A 象限) = 24 関数 + 12 随伴対。

使い方:
    from ccl.stdlib.hgk import *

    # 認識 → 意志 → 実行
    insight = recognize(data)
    goal = intend(insight)
    result = execute_plan(goal)
"""

from ccl.stdlib.hgk.telos import (
    recognize, intend, explore, execute_plan, observe, detect,
)
from ccl.stdlib.hgk.methodos import (
    diverge_strategy, converge_strategy, experiment, apply_technique,
)
from ccl.stdlib.hgk.krisis import (
    commit, suspend, decide, probe,
)
from ccl.stdlib.hgk.diastasis import (
    analyze_detail, overview, refine, orchestrate,
)
from ccl.stdlib.hgk.orexis import (
    affirm, critique, advance, correct,
)
from ccl.stdlib.hgk.chronos import (
    recall, forecast, reflect, prepare,
)

# 全随伴対を集約
ALL_ADJOINT_PAIRS = []
from ccl.stdlib.hgk import telos, methodos, krisis, diastasis, orexis, chronos
for mod in [telos, methodos, krisis, diastasis, orexis, chronos]:
    ALL_ADJOINT_PAIRS.extend(mod.ADJOINT_PAIRS)

# /verb → 関数名のマッピング
VERB_MAP = {
    # Telos
    "noe": recognize, "bou": intend, "zet": explore, "ene": execute_plan,
    "the": observe, "ant": detect,
    # Methodos
    "ske": diverge_strategy, "sag": converge_strategy,
    "pei": experiment, "tek": apply_technique,
    # Krisis
    "kat": commit, "epo": suspend, "pai": decide, "dok": probe,
    # Diástasis
    "lys": analyze_detail, "ops": overview, "akr": refine, "arh": orchestrate,
    # Orexis
    "beb": affirm, "ele": critique, "kop": advance, "dio": correct,
    # Chronos
    "hyp": recall, "prm": forecast, "ath": reflect, "par": prepare,
}

__all__ = [
    # Telos
    "recognize", "intend", "explore", "execute_plan", "observe", "detect",
    # Methodos
    "diverge_strategy", "converge_strategy", "experiment", "apply_technique",
    # Krisis
    "commit", "suspend", "decide", "probe",
    # Diástasis
    "analyze_detail", "overview", "refine", "orchestrate",
    # Orexis
    "affirm", "critique", "advance", "correct",
    # Chronos
    "recall", "forecast", "reflect", "prepare",
    # Meta
    "ALL_ADJOINT_PAIRS", "VERB_MAP",
]
