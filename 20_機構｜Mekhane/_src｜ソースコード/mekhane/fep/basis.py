from __future__ import annotations
# PROOF: [L2/FEP] <- mekhane/fep/basis.py
# PURPOSE: Basis (βάσις) — Helmholtz 分解 (Γ⊣Q) と 12 数学的演算子の定義
"""
Basis Layer — Helmholtz Decomposition and 12 Mathematical Operators

axiom_hierarchy.md v4.2 で定義された Basis (d=0) 層の
コード上の表現。Basis は FEP/NESS の定理であり、
7 座標 (d=1〜3) が「立つ土台」。体系核 32 に数えない。

導出チェーン:
    FEP → NESS (Non-Equilibrium Steady State)
      → Fokker-Planck 方程式
        → Helmholtz 分解: f = (Γ + Q)∇φ
          Γ = gradient (dissipative) — VFE 最小化
          Q = solenoidal (conservative) — 等 VFE 面上の探索

12 演算子 = Basis (Γ/Q) × 6 修飾座標
  → 12 演算子 × Flow (I/A) = 24 認知動詞の変分多様体上の実装

理論的根拠:
- Friston 2019 (arXiv:1906.10184): A particular kind of FEP
- axiom_hierarchy.md v4.2 §Basis
"""


from dataclasses import dataclass
from enum import Enum
from mekhane.fep.coordinates import (
    COORDINATE_SPECS,
    MODIFYING_COORDINATES,
    CoordinateSpec,
    coordinates_by_d,
    get_d_value,
)


# ---------------------------------------------------------------------------
# Helmholtz Decomposition (Basis)
# ---------------------------------------------------------------------------

# PURPOSE: Helmholtz 分解の 2 成分
class HelmholtzComponent(Enum):
    """Helmholtz 分解の 2 成分 (Γ⊣Q 随伴対)"""
    GRADIENT = "Γ"       # dissipative: VFE 最小化、定常状態への駆動
    SOLENOIDAL = "Q"     # conservative: 確率保存的循環、等確率面上の探索


# PURPOSE: Basis (βάσις) のデータ構造
@dataclass(frozen=True)
class Basis:
    """Basis (βάσις) — FEP の d=0 層。

    FEP が動力学系に適用されたときの動的実現 (dynamical realization)。
    追加仮定ゼロで導出される定理であり、独立実体ではない。
    体系核 32 には数えない (体系核外)。

    構造的役割: 7 座標が「立つ土台」。認知座標ではなく、
    座標系が成立する前提条件。岩石も Helmholtz 分解を持つ。
    """
    gradient: str = "Γ"      # dissipative component
    solenoidal: str = "Q"    # conservative component
    d_value: int = 0         # 構成距離 = 0 (追加仮定ゼロ)

    @property
    def adjunction_pair(self) -> tuple[str, str]:
        """Γ⊣Q 随伴対を返す。"""
        return (self.gradient, self.solenoidal)


# Singleton — 体系内で唯一
BASIS = Basis()




# ---------------------------------------------------------------------------
# 12 数学的演算子 (Basis × 6 修飾座標)
# ---------------------------------------------------------------------------

# PURPOSE: Basis × 座標方向の演算子 (変分多様体上の操作)
@dataclass(frozen=True)
class HelmholtzOperator:
    """12 数学的演算子の 1 つ。

    Basis (Γ/Q) × 6 修飾座標 = 変分多様体上の操作。
    認知動詞ではなく、動詞の数学的実装基盤。

    12 演算子 × Flow (I/A) = 24 認知動詞 (Poiesis) への橋渡し。
    """
    coordinate: str              # 修飾座標名 (Value, Function, ...)
    component: HelmholtzComponent  # Γ (gradient) or Q (solenoidal)
    description: str             # 操作の数学的意味
    description_ja: str          # 日本語説明

    @property
    def name(self) -> str:
        """演算子名: 例 'Γ_Value', 'Q_Function'"""
        return f"{self.component.value}_{self.coordinate}"

    @property
    def is_gradient(self) -> bool:
        return self.component == HelmholtzComponent.GRADIENT

    @property
    def is_solenoidal(self) -> bool:
        return self.component == HelmholtzComponent.SOLENOIDAL


# PURPOSE: 12 演算子の定義テーブル (axiom_hierarchy.md v4.2 §Basis)
HELMHOLTZ_OPERATORS: list[HelmholtzOperator] = [
    # --- Γ 列 (gradient / 最適化) ---
    HelmholtzOperator(
        coordinate="Value",
        component=HelmholtzComponent.GRADIENT,
        description="Gradient descent on expected free energy (pragmatic continuous exploitation)",
        description_ja="内的目的(E/P)に向けた期待自由エネルギー勾配の降下",
    ),
    HelmholtzOperator(
        coordinate="Function",
        component=HelmholtzComponent.GRADIENT,
        description="Convergence of policy distribution towards exploiting known optimal states",
        description_ja="既知の最適状態を活用するための政策分布の収束（Exploit偏重）",
    ),
    HelmholtzOperator(
        coordinate="Precision",
        component=HelmholtzComponent.GRADIENT,
        description="Optimization of precision weights, collapsing uncertainty (δ -> Dirac)",
        description_ja="精度重みの最適化による不確実性の崩壊と確信(C)の形成",
    ),
    HelmholtzOperator(
        coordinate="Scale",
        component=HelmholtzComponent.GRADIENT,
        description="Localization of inference into micro-scale, reducing representation scope",
        description_ja="推論を局所的な微視的(Mi)スケールに収束させる最適化",
    ),
    HelmholtzOperator(
        coordinate="Valence",
        component=HelmholtzComponent.GRADIENT,
        description="Gradient descent towards positively valenced (attractor) steady states",
        description_ja="肯定的な価値(引力)に向かって状態を駆動する勾配流",
    ),
    HelmholtzOperator(
        coordinate="Temporality",
        component=HelmholtzComponent.GRADIENT,
        description="Teleological prediction optimization directed toward the future states",
        description_ja="望ましい未来の状態に向けた予測モデルの目的論的最適化",
    ),

    # --- Q 列 (solenoidal / 探索) ---
    HelmholtzOperator(
        coordinate="Value",
        component=HelmholtzComponent.SOLENOIDAL,
        description="Isoprobability circulation along Value axis (epistemic foraging)",
        description_ja="Value 方向の等確率循環 (認識的探索)",
    ),
    HelmholtzOperator(
        coordinate="Function",
        component=HelmholtzComponent.SOLENOIDAL,
        description="Isoprobability circulation along Function axis (exploration variance)",
        description_ja="Function 方向の等確率循環 (探索分散)",
    ),
    HelmholtzOperator(
        coordinate="Precision",
        component=HelmholtzComponent.SOLENOIDAL,
        description="Isoprobability circulation along Precision axis (uncertainty maintenance)",
        description_ja="Precision 方向の等確率循環 (不確実性保持)",
    ),
    HelmholtzOperator(
        coordinate="Scale",
        component=HelmholtzComponent.SOLENOIDAL,
        description="Isoprobability circulation along Scale axis (macro-scale divergence)",
        description_ja="Scale 方向の等確率循環 (巨視的発散)",
    ),
    HelmholtzOperator(
        coordinate="Valence",
        component=HelmholtzComponent.SOLENOIDAL,
        description="Isoprobability circulation along Valence axis (negative divergence)",
        description_ja="Valence 方向の等確率循環 (負の反発・発散)",
    ),
    HelmholtzOperator(
        coordinate="Temporality",
        component=HelmholtzComponent.SOLENOIDAL,
        description="Isoprobability circulation along Temporality axis (past-directed archaeology)",
        description_ja="Temporality 方向の等確率循環 (過去指向の再構築)",
    ),
]
assert len(HELMHOLTZ_OPERATORS) == 12, f"Expected 12 operators, got {len(HELMHOLTZ_OPERATORS)}"


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

# PURPOSE: 座標名と成分で演算子を取得
def get_operator(
    coordinate: str,
    component: HelmholtzComponent | str,
) -> Optional[HelmholtzOperator]:
    """座標名と Helmholtz 成分から演算子を検索する。

    Args:
        coordinate: 修飾座標名 (Value, Function, Precision, Scale, Valence, Temporality)
        component: HelmholtzComponent or "Γ"/"Q"/"gradient"/"solenoidal"

    Returns:
        HelmholtzOperator or None
    """
    if isinstance(component, str):
        component = _parse_component(component)

    for op in HELMHOLTZ_OPERATORS:
        if op.coordinate == coordinate and op.component == component:
            return op
    return None


# PURPOSE: Γ 列 (gradient) の 6 演算子を取得
def gradient_operators() -> list[HelmholtzOperator]:
    """Γ 列 (gradient / 最適化) の 6 演算子を返す。"""
    return [op for op in HELMHOLTZ_OPERATORS if op.is_gradient]


# PURPOSE: Q 列 (solenoidal) の 6 演算子を取得
def solenoidal_operators() -> list[HelmholtzOperator]:
    """Q 列 (solenoidal / 保存的循環) の 6 演算子を返す。"""
    return [op for op in HELMHOLTZ_OPERATORS if op.is_solenoidal]





# PURPOSE: 12 演算子と 24 動詞 (Poiesis) の対応関係を表示
def format_operator_table() -> str:
    """12 演算子テーブルを Markdown 形式で返す。"""
    lines = [
        "| 演算子 | 座標 | 成分 | 説明 |",
        "|:-------|:-----|:-----|:-----|",
    ]
    for op in HELMHOLTZ_OPERATORS:
        comp_label = "Γ (gradient)" if op.is_gradient else "Q (solenoidal)"
        lines.append(f"| `{op.name}` | {op.coordinate} | {comp_label} | {op.description_ja} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helmholtz Score (H_s = Γ/(Γ+Q))
# ---------------------------------------------------------------------------

# PURPOSE: 統一 Helmholtz Score の計算
@dataclass(frozen=True)
class HelmholtzScore:
    """統一 Helmholtz Score — Γ/Q 比の正規化。

    H_s = Γ / (Γ + Q)  ∈ [0, 1]
    - H_s → 1: Exploitation (収束・最適化優先)
    - H_s → 0: Exploration (循環・探索優先)
    - H_s ≈ 0.5: バランス状態

    各モジュールが独自の方法で Γ/Q の生値を計算し、
    この関数で正規化することで、体系全体で統一的な解釈が可能になる。
    """
    gamma: float      # Γ (gradient) 成分の生値
    q: float          # Q (solenoidal) 成分の生値
    score: float      # H_s = Γ / (Γ + Q) ∈ [0, 1]


def helmholtz_score(gamma: float, q: float) -> HelmholtzScore:
    """Helmholtz Score を計算する。

    H_s = Γ / (Γ + Q)

    Args:
        gamma: Γ (gradient/最適化) 成分。0 以上。
        q: Q (solenoidal/探索) 成分。0 以上。

    Returns:
        HelmholtzScore(gamma, q, score)

    Raises:
        ValueError: Γ < 0 or Q < 0

    Examples:
        # derivative_selector: oscillation_score → Q, convergence → Γ
        hs = helmholtz_score(gamma=0.8, q=0.2)
        assert hs.score == 0.8  # 強い最適化モード

        # periskope: coherence → Γ, entropy → Q
        hs = helmholtz_score(gamma=0.3, q=0.7)
        assert hs.score == 0.3  # 強い探索モード
    """
    if gamma < 0 or q < 0:
        raise ValueError(f"Γ and Q must be non-negative: Γ={gamma}, Q={q}")

    total = gamma + q
    if total == 0:
        # 両方ゼロ → バランス状態
        score = 0.5
    else:
        score = gamma / total

    return HelmholtzScore(gamma=gamma, q=q, score=score)


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _parse_component(s: str) -> HelmholtzComponent:
    """文字列から HelmholtzComponent を解決する。"""
    mapping = {
        "Γ": HelmholtzComponent.GRADIENT,
        "gamma": HelmholtzComponent.GRADIENT,
        "gradient": HelmholtzComponent.GRADIENT,
        "Q": HelmholtzComponent.SOLENOIDAL,
        "solenoidal": HelmholtzComponent.SOLENOIDAL,
    }
    if s in mapping:
        return mapping[s]
    raise ValueError(f"Unknown Helmholtz component: {s!r}. Use Γ/Q/gradient/solenoidal")


# ---------------------------------------------------------------------------
# Precision Dynamics — Proietti H₁ (γ/γ' 特殊化)
# ---------------------------------------------------------------------------
# 理論的根拠:
#   - Proietti, Parr, Tessari, Friston, Pezzulo (2025)
#     "Active inference and cognitive control"
#   - axiom_hierarchy.md v4.2.2 §P₃
#   - pei_gamma_hs_hypothesis_2026-03-15.md (ODE v2, MC 20/20)
#
# H₁ 仮説: γ/γ' は Precision 座標の Γ_Prec/Q_Prec の内部構造。
#   γ  → Γ_Precision: 精度重みの最適化 → 確信(C)形成 → habit 化
#   γ' → Q_Precision: surprise 駆動の不確実性保持 → deliberation
#
# H₂ (H_s 全体の動的調整) との関係: H₁ は H₂ の Precision 軸射影。
# 包含関係であり排他的ではない。

# PURPOSE: Precision 座標内の γ/γ' 動態 (Proietti H₁ 特殊化)
@dataclass(frozen=True)
class PrecisionDynamics:
    """Precision 座標の γ/γ' 動態状態。

    Proietti (2025) の γ (habitual precision) / γ' (meta-cognitive control)
    を Helmholtz 演算子 Γ_Precision / Q_Precision の内部構造として型化。

    γ  → Γ_Precision: 精度重みの最適化 (δ→Dirac: 確信形成)
    γ' → Q_Precision: 等確率循環 (不確実性保持: surprise 駆動)

    H_s_precision = γ / (γ + γ') ∈ [0, 1]
      → 1: habit (Γ_Precision 優位)
      → 0: deliberation (Q_Precision 優位)
    """
    gamma: float            # γ: habitual precision 強度 (Γ_Precision 成分)
    gamma_prime: float      # γ': meta-cognitive control signal (Q_Precision 成分)
    surprise: float         # Bayesian surprise (γ' の駆動入力)
    h_s_precision: float    # Precision 軸の局所 Helmholtz Score


# PURPOSE: Precision 軸の局所 Helmholtz Score を計算
def precision_helmholtz_score(gamma: float, gamma_prime: float) -> HelmholtzScore:
    """Precision 座標内の Helmholtz Score を計算する。

    γ (habitual precision) → Γ_Precision 成分
    γ' (meta-cognitive control) → Q_Precision 成分

    H_s_prec = γ / (γ + γ')

    pei 実験 (MC 20/20) で検証済みの構造的対応:
      corr(H_s, γ') = -0.845 ± 0.020
      corr(γ', surprise[t-1]) = 0.987

    Args:
        gamma: γ (habitual precision) 成分。0 以上。
        gamma_prime: γ' (meta-cognitive control) 成分。0 以上。

    Returns:
        HelmholtzScore(gamma=γ, q=γ', score=H_s_prec)

    Examples:
        # 習慣化状態: γ >> γ'
        hs = precision_helmholtz_score(gamma=0.99, gamma_prime=0.01)
        assert hs.score > 0.95  # habit 領域

        # deliberation 状態: γ' が上昇
        hs = precision_helmholtz_score(gamma=0.5, gamma_prime=0.8)
        assert hs.score < 0.5  # deliberation 領域
    """
    return helmholtz_score(gamma=gamma, q=gamma_prime)


# PURPOSE: Precision 動態の ODE 更新 (pei v2 パラメータ)
@dataclass(frozen=True)
class PrecisionDynamicsParams:
    """Precision 動態の ODE パラメータ。

    pei 実験 v2 (MC 20 seeds, 100% 支持) のデフォルト値。
    感度分析 (OAT × MC5 = 350 sim) で γ' gain/decay は全範囲で頑健。
    """
    # Γ_Precision (γ 学習)
    gamma_learning_rate: float = 0.05   # γ の学習速度
    gamma_decay_rate: float = 0.01      # γ の減衰速度

    # Q_Precision (γ' 応答)
    gamma_prime_gain: float = 0.5       # surprise → γ' のゲイン
    gamma_prime_decay: float = 0.3      # γ' の減衰速度
    gamma_prime_max: float = 0.8        # γ' の上限

    # Q 成分
    q_base: float = 0.1                 # Q のベース値
    q_decay_rate: float = 0.05          # Q の減衰速度


# デフォルトパラメータ (pei v2 検証済み)
DEFAULT_PRECISION_PARAMS = PrecisionDynamicsParams()


def update_precision_dynamics(
    current: PrecisionDynamics,
    reward: float,
    surprise: float,
    params: PrecisionDynamicsParams | None = None,
) -> PrecisionDynamics:
    """Precision 動態を 1 ステップ更新する。

    ODE 離散化 (pei v2):
      dΓ/dt = reward × learning_rate - Γ × decay_rate
      dγ'/dt = surprise × gain - γ' × decay
      Q ← q_base + γ' × (1 - q_decay)

    Args:
        current: 現在の PrecisionDynamics 状態
        reward: 報酬信号 (0 or 1)。γ の学習を駆動
        surprise: Bayesian surprise。γ' を駆動
        params: ODE パラメータ (None → デフォルト)

    Returns:
        更新後の PrecisionDynamics
    """
    if params is None:
        params = DEFAULT_PRECISION_PARAMS

    # --- Γ_Precision (γ 学習) ---
    # 報酬があれば γ を増加、なければ減衰
    new_gamma = max(0.0, (
        current.gamma
        + reward * params.gamma_learning_rate
        - current.gamma * params.gamma_decay_rate
    ))

    # --- Q_Precision (γ' 応答) ---
    # surprise に比例して γ' を増加、時定数で減衰
    new_gamma_prime = min(params.gamma_prime_max, max(0.0, (
        current.gamma_prime
        + surprise * params.gamma_prime_gain
        - current.gamma_prime * params.gamma_prime_decay
    )))

    # --- H_s_precision ---
    hs = precision_helmholtz_score(new_gamma, new_gamma_prime)

    return PrecisionDynamics(
        gamma=new_gamma,
        gamma_prime=new_gamma_prime,
        surprise=surprise,
        h_s_precision=hs.score,
    )


def simulate_precision_trajectory(
    n_trials: int = 300,
    context_switch_at: int = 150,
    params: PrecisionDynamicsParams | None = None,
    seed: int | None = None,
) -> list[PrecisionDynamics]:
    """Proietti-style の Precision 動態軌道を生成する。

    Phase 1 (0..switch): 報酬あり → γ 学習 → H_s → 1 (habit)
    Phase 2 (switch..end): context switch → surprise スパイク → γ' 応答

    pei v2 で MC 20/20 支持済み。

    Args:
        n_trials: 試行数 (デフォルト 300)
        context_switch_at: 文脈切替の試行番号 (デフォルト 150)
        params: ODE パラメータ (None → デフォルト)
        seed: 乱数シード (None → 決定論的)

    Returns:
        PrecisionDynamics のリスト (長さ n_trials)
    """
    import random as _random

    if params is None:
        params = DEFAULT_PRECISION_PARAMS
    if seed is not None:
        _random.seed(seed)

    trajectory: list[PrecisionDynamics] = []
    state = PrecisionDynamics(
        gamma=0.1,
        gamma_prime=0.2,
        surprise=0.0,
        h_s_precision=0.333,
    )

    for t in range(n_trials):
        # Phase 1: 報酬あり、surprise 低い
        if t < context_switch_at:
            reward = 1.0
            surprise = 0.05 if seed is None else max(0.0, 0.05 + _random.gauss(0, 0.02))
        else:
            # Phase 2: context switch → 報酬減少、surprise 増加
            steps_after = t - context_switch_at
            # surprise は switch 直後に急増し徐々に減衰
            base_surprise = 0.8 * (0.9 ** steps_after) if steps_after < 50 else 0.05
            surprise = base_surprise if seed is None else max(0.0, base_surprise + _random.gauss(0, 0.05))
            # 報酬は context-dependent (Phase 2 では低い)
            reward = 0.2

        state = update_precision_dynamics(state, reward=reward, surprise=surprise, params=params)
        trajectory.append(state)

    return trajectory
