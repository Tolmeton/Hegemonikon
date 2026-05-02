# PROOF: [L2/インフラ] <- mekhane/fep/state_spaces_v2.py
# PURPOSE: 48-state FEP Model (v2) — Series 統合状態空間
"""
PROOF: [L2/インフラ] このファイルは存在しなければならない

A0 → FEP Agent は Series を知るべき
   → Series を hidden state factor に組み込む
   → state_spaces_v2.py が 48-state model を定義する

Q.E.D.

---

State Spaces v2 for Hegemonikón Active Inference

Extends v1 by adding Series (T/M/K/D/O/C) as a 4th hidden state factor
and series-specific actions, enabling unified cognitive-content judgment.

v1: phantasia(2) × assent(2) × horme(2) = 8 states, 2 actions
v2: phantasia(2) × assent(2) × horme(2) × series(6) = 48 states, 7 actions
"""

from typing import Dict, List, Tuple

# Re-export v1 factors for compatibility
from .state_spaces import (
    PHANTASIA_STATES,
    ASSENT_STATES,
    HORME_STATES,
    PREFERENCES as V1_PREFERENCES,
)

# =============================================================================
# 4th Hidden State Factor: Series
# =============================================================================

SERIES_STATES: List[str] = ["T", "M", "K", "D", "O", "C"]

SERIES_NAMES: Dict[str, str] = {
    "T": "Telos (目的)",
    "M": "Methodos (方法)",
    "K": "Krisis (判断)",
    "D": "Diástasis (拡張)",
    "O": "Orexis (欲求)",
    "C": "Chronos (時間)",
}

# =============================================================================
# Expanded Observation Modalities
# =============================================================================

OBSERVATION_MODALITIES_V2: Dict[str, List[str]] = {
    # v1 modalities (unchanged)
    "context": ["ambiguous", "clear"],
    "urgency": ["low", "medium", "high"],
    "confidence": ["low", "medium", "high"],
    # NEW: Topic modality from Attractor
    "topic": ["T", "M", "K", "D", "O", "C"],
}

# =============================================================================
# Expanded Actions
# =============================================================================

ACTIONS_V2: List[str] = [
    "observe",   # 0: Epochē — 判断停止、観察モード
    "act_T",     # 1: T-series WF 実行 (Telos/目的)
    "act_M",     # 2: M-series WF 実行 (Methodos/方法)
    "act_K",     # 3: K-series WF 実行 (Krisis/判断)
    "act_D",     # 4: D-series WF 実行 (Diástasis/拡張)
    "act_O",     # 5: O-series WF 実行 (Orexis/欲求)
    "act_C",     # 6: C-series WF 実行 (Chronos/時間)
]

# Action → Series mapping
ACTION_TO_SERIES: Dict[str, str] = {
    "act_T": "T", "act_M": "M", "act_K": "K",
    "act_D": "D", "act_O": "O", "act_C": "C",
}

# =============================================================================
# Preference Vectors (C matrix)
# =============================================================================

PREFERENCES_V2: Dict[str, Dict[str, float]] = {
    **V1_PREFERENCES,
    "topic": {
        # Series を認識したら行動を促す — Epochē からの脱出誘因
        # 高い値 = Agent は topic signal に応答して act_X を選びたがる
        # 4.0: context の ambiguous(-2.0)/clear(+2.0) と同等のインパクト
        "T": 4.0, "M": 4.0, "K": 4.0,
        "D": 4.0, "O": 4.0, "C": 4.0,
    },
}

# =============================================================================
# Dimensions
# =============================================================================

NUM_STATES_V2 = (
    len(PHANTASIA_STATES)
    * len(ASSENT_STATES)
    * len(HORME_STATES)
    * len(SERIES_STATES)
)  # 2 × 2 × 2 × 6 = 48

NUM_OBS_V2 = sum(len(v) for v in OBSERVATION_MODALITIES_V2.values())  # 14

NUM_ACTIONS_V2 = len(ACTIONS_V2)  # 7


# =============================================================================
# Helper Functions
# =============================================================================


# PURPOSE: total hidden state dimension for v2 model の利用を可能にする
def get_state_dim_v2() -> int:
    """Return total hidden state dimension for v2 model."""
    return NUM_STATES_V2


# PURPOSE: observation dimensions for v2 model の利用を可能にする
def get_obs_dim_v2() -> Dict[str, int]:
    """Return observation dimensions for v2 model."""
    return {k: len(v) for k, v in OBSERVATION_MODALITIES_V2.items()}


# PURPOSE: Convert 4-factor state to flat index
def state_to_index_v2(
    phantasia: str, assent: str, horme: str, series: str
) -> int:
    """Convert 4-factor state to flat index.

    Order: phantasia × assent × horme × series (row-major)
    """
    p_idx = PHANTASIA_STATES.index(phantasia)
    a_idx = ASSENT_STATES.index(assent)
    h_idx = HORME_STATES.index(horme)
    s_idx = SERIES_STATES.index(series)

    a_size = len(ASSENT_STATES)
    h_size = len(HORME_STATES)
    s_size = len(SERIES_STATES)

    return (
        p_idx * a_size * h_size * s_size
        + a_idx * h_size * s_size
        + h_idx * s_size
        + s_idx
    )


# PURPOSE: Convert flat index to 4-factor state names
def index_to_state_v2(idx: int) -> Tuple[str, str, str, str]:
    """Convert flat index to 4-factor state names.

    Returns:
        (phantasia, assent, horme, series)
    """
    s_size = len(SERIES_STATES)
    h_size = len(HORME_STATES)
    a_size = len(ASSENT_STATES)

    s_idx = idx % s_size
    h_idx = (idx // s_size) % h_size
    a_idx = (idx // (s_size * h_size)) % a_size
    p_idx = idx // (s_size * h_size * a_size)

    return (
        PHANTASIA_STATES[p_idx],
        ASSENT_STATES[a_idx],
        HORME_STATES[h_idx],
        SERIES_STATES[s_idx],
    )


# PURPOSE: Convert action index to human-readable name
def action_name_v2(action_idx: int) -> str:
    """Convert action index to human-readable name."""
    if 0 <= action_idx < len(ACTIONS_V2):
        return ACTIONS_V2[action_idx]
    return f"unknown_{action_idx}"


# PURPOSE: Get the Series associated with an action (None for observe)
def action_to_series(action_idx: int) -> str | None:
    """Get the Series associated with an action (None for observe)."""
    name = action_name_v2(action_idx)
    return ACTION_TO_SERIES.get(name)
