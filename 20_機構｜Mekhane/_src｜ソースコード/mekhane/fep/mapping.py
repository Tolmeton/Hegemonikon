from __future__ import annotations
# PROOF: [L2/FEP] <- mekhane/fep/mapping.py
# PURPOSE: 12 Helmholtz 演算子から 48 認知操作 (36 Poiesis + 12 H-series) へのマッピング (Level A)
"""
Poiesis Mapping Layer (Level A) — v5.4 K₄柱モデル対応

Smithe et al. 2023 / Spisak & Friston 2025 の枠組みに従い、
Basis (Γ⊣Q) と 6 修飾座標からなる 12 の Helmholtz 演算子が、
どのように 48 の認知操作に展開されるかを定義する。

構成規則 (The Generation Rule — v5.4 K₄柱モデル):
    Afferent×Efferent の4象限すべてが等価な体系核となる。
    36 Poiesis = Flow(S/I/A) × 6 修飾座標 × 2 極 (Γ/Q)
    12 H-series = Flow(S∩A) (中動態) × 6 修飾座標 × 2 極
    48 認知操作 = 36 Poiesis + 12 H-series (体系核57の一部)

    1. 各修飾座標について、Γ と Q の演算子が存在する。
    2. Γ (Gradient): VFE を最小化する最適化成分
    3. Q (Solenoidal): 構造を探索・移動する循環成分
    4. Flow(S/I/A) の三値を掛ける:
       - I × Γ = 内的最適化 (信念の収束) [T1/T2]
       - I × Q = 内的探索 (仮説空間の拡張) [T1/T2]
       - A × Γ = 外的最適化 (合目的的な行動) [T3/T4]
       - A × Q = 外的探索 (能動的サンプリング) [T3/T4]
       - S × Γ = 知覚的最適化 (知覚入力の精度向上) [T5/T6]
       - S × Q = 知覚的探索 (感覚走査) [T5/T6]

    これにより、1 つの座標 (例: Value) に対して 6 つの動詞が生成される。
    6 座標 × 6 極 = 36 動詞 (Poiesis)

Γ/Q 極性割り当ての根拠 (axiom_hierarchy.md L97-100 との照合済み):
    一貫した原理: Γ = 収束・最適化・確定方向、Q = 発散・探索・保留方向

    座標          Γ に対応する極    Q に対応する極    根拠
    Value         P (実用)         E (認識)         目的収束 vs 知識探索
    Function      Exploit (活用)   Explore (探索)    既知活用 vs 未知探索
    Precision     C (確信)         U (留保)          不確実性崩壊 vs エントロピー維持
    Scale         Mi (局所)        Ma (広域)         微視的収束 vs 巨視的発散
    Valence       + (肯定)         - (批判)          引力点収束 vs 斥力循環
    Temporality   Future (未来)    Past (過去)       目標最適化 vs 蓄積再循環
"""


from dataclasses import dataclass

from .basis import HelmholtzComponent, HelmholtzOperator, get_operator


# ---------------------------------------------------------------------------
# PoiesisVerb — 認知動詞定義
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PoiesisVerb:
    """Poiesis (動詞層) の 1 要素を表す。"""
    ccl_name: str           # e.g., "noe"
    greek_name: str         # e.g., "Noēsis"
    japanese_name: str      # e.g., "理解する"
    coordinate: str         # 属する修飾座標 (e.g., "Value")
    flow_pole: str          # "I" (Inference) or "A" (Action)
    helmholtz_component: HelmholtzComponent  # Γ or Q

    @property
    def operator(self) -> HelmholtzOperator:
        """対応する Helmholtz 演算子を取得する。"""
        op = get_operator(self.coordinate, self.helmholtz_component)
        if op is None:
            raise RuntimeError(f"Missing operator for {self.coordinate} {self.helmholtz_component}")
        return op


# ---------------------------------------------------------------------------
# Mappings by Series (Coordinate)
# ---------------------------------------------------------------------------

# PURPOSE: 36 Poiesis 動詞の辞書。キーは CCL 名 (e.g., "noe") — v5.4: S極12動詞追加を継承
POIESIS_VERBS: dict[str, PoiesisVerb] = {
    # 1. Telos 族 (Value × Flow)
    # E(認識) ↔ P(実用) にマップされる。
    # 認識(E) は探索的・循環的(Q), 実用(P) は収束的・最適化的(Γ)
    "noe": PoiesisVerb(
        ccl_name="noe", greek_name="Noēsis", japanese_name="理解する",
        coordinate="Value", flow_pole="I", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),
    "bou": PoiesisVerb(
        ccl_name="bou", greek_name="Boulēsis", japanese_name="意志する",
        coordinate="Value", flow_pole="I", helmholtz_component=HelmholtzComponent.GRADIENT
    ),
    "zet": PoiesisVerb(
        ccl_name="zet", greek_name="Zētēsis", japanese_name="探求する",
        coordinate="Value", flow_pole="A", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),
    "ene": PoiesisVerb(
        ccl_name="ene", greek_name="Energeia", japanese_name="実行する",
        coordinate="Value", flow_pole="A", helmholtz_component=HelmholtzComponent.GRADIENT
    ),

    # 2. Methodos 族 (Function × Flow)
    # Explore(探索) ↔ Exploit(活用) にマップされる。
    # Explore = Q, Exploit = Γ
    "ske": PoiesisVerb(
        ccl_name="ske", greek_name="Skepsis", japanese_name="発散する",
        coordinate="Function", flow_pole="I", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),
    "sag": PoiesisVerb(
        ccl_name="sag", greek_name="Synagōgē", japanese_name="収束する",
        coordinate="Function", flow_pole="I", helmholtz_component=HelmholtzComponent.GRADIENT
    ),
    "pei": PoiesisVerb(
        ccl_name="pei", greek_name="Peira", japanese_name="実験する",
        coordinate="Function", flow_pole="A", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),
    "tek": PoiesisVerb(
        ccl_name="tek", greek_name="Tekhnē", japanese_name="適用する",
        coordinate="Function", flow_pole="A", helmholtz_component=HelmholtzComponent.GRADIENT
    ),

    # 3. Krisis 族 (Precision × Flow)
    # U(留保) ↔ C(確信) にマップされる。
    # 留保(U) = Q, 確信(C) = Γ
    "epo": PoiesisVerb(
        ccl_name="epo", greek_name="Epochē", japanese_name="留保する",
        coordinate="Precision", flow_pole="I", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),
    "kat": PoiesisVerb(
        ccl_name="kat", greek_name="Katalēpsis", japanese_name="確定する",
        coordinate="Precision", flow_pole="I", helmholtz_component=HelmholtzComponent.GRADIENT
    ),
    "dok": PoiesisVerb(
        ccl_name="dok", greek_name="Dokimasia", japanese_name="打診する",
        coordinate="Precision", flow_pole="A", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),
    "pai": PoiesisVerb(
        ccl_name="pai", greek_name="Proairesis", japanese_name="決断する",
        coordinate="Precision", flow_pole="A", helmholtz_component=HelmholtzComponent.GRADIENT
    ),

    # 4. Diástasis 族 (Scale × Flow)
    # Mi(局所) ↔ Ma(広域) にマップされる。
    # 局所(Mi) = Γ, 広域(Ma) = Q  ※ Scaleの解釈: 大きく動くことはQ、局所収束はΓ
    "lys": PoiesisVerb(
        ccl_name="lys", greek_name="Analysis", japanese_name="詳細分析する",
        coordinate="Scale", flow_pole="I", helmholtz_component=HelmholtzComponent.GRADIENT
    ),
    "ops": PoiesisVerb(
        ccl_name="ops", greek_name="Synopsis", japanese_name="俯瞰する",
        coordinate="Scale", flow_pole="I", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),
    "akr": PoiesisVerb(
        ccl_name="akr", greek_name="Akribeia", japanese_name="精密操作する",
        coordinate="Scale", flow_pole="A", helmholtz_component=HelmholtzComponent.GRADIENT
    ),
    "ark": PoiesisVerb(
        ccl_name="ark", greek_name="Architektonikē", japanese_name="全体展開する",
        coordinate="Scale", flow_pole="A", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),

    # 5. Orexis 族 (Valence × Flow)
    # -(批判) ↔ +(推進) にマップされる。
    # -(批判/回避) = Q, +(推進/肯定) = Γ
    "ele": PoiesisVerb(
        ccl_name="ele", greek_name="Elenchos", japanese_name="批判する",
        coordinate="Valence", flow_pole="I", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),
    "beb": PoiesisVerb(
        ccl_name="beb", greek_name="Bebaiōsis", japanese_name="肯定する",
        coordinate="Valence", flow_pole="I", helmholtz_component=HelmholtzComponent.GRADIENT
    ),
    "dio": PoiesisVerb(
        ccl_name="dio", greek_name="Diorthōsis", japanese_name="是正する",
        coordinate="Valence", flow_pole="A", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),
    "kop": PoiesisVerb(
        ccl_name="kop", greek_name="Prokopē", japanese_name="推進する",
        coordinate="Valence", flow_pole="A", helmholtz_component=HelmholtzComponent.GRADIENT
    ),

    # 6. Chronos 族 (Temporality × Flow)
    # Past(過去) ↔ Future(未来) にマップされる。
    # 過去(Past) = Q (既存状態の循環・再構築), 未来(Future) = Γ (目的状態への最適化)
    "hyp": PoiesisVerb(
        ccl_name="hyp", greek_name="Hypomnēsis", japanese_name="想起する",
        coordinate="Temporality", flow_pole="I", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),
    "prm": PoiesisVerb(
        ccl_name="prm", greek_name="Promētheia", japanese_name="予見する",
        coordinate="Temporality", flow_pole="I", helmholtz_component=HelmholtzComponent.GRADIENT
    ),
    "ath": PoiesisVerb(
        ccl_name="ath", greek_name="Anatheōrēsis", japanese_name="省みる",
        coordinate="Temporality", flow_pole="A", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),
    "par": PoiesisVerb(
        ccl_name="par", greek_name="Proparaskeuē", japanese_name="仕掛ける",
        coordinate="Temporality", flow_pole="A", helmholtz_component=HelmholtzComponent.GRADIENT
    ),

    # --- v5.0 S極動詞 (T5-T6): Flow=S (Sensory/Afferent) ---
    # 知覚はする、行為はしない。φ_SI パイプラインの入力端。

    # 7. Telos 族 S極
    "the": PoiesisVerb(
        ccl_name="the", greek_name="Theōria", japanese_name="観照する",
        coordinate="Value", flow_pole="S", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),
    "ant": PoiesisVerb(
        ccl_name="ant", greek_name="Antilepsis", japanese_name="検知する",
        coordinate="Value", flow_pole="S", helmholtz_component=HelmholtzComponent.GRADIENT
    ),

    # 8. Methodos 族 S極
    "ere": PoiesisVerb(
        ccl_name="ere", greek_name="Ereuna", japanese_name="探知する",
        coordinate="Function", flow_pole="S", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),
    "agn": PoiesisVerb(
        ccl_name="agn", greek_name="Anagnōsis", japanese_name="参照する",
        coordinate="Function", flow_pole="S", helmholtz_component=HelmholtzComponent.GRADIENT
    ),

    # 9. Krisis 族 S極
    "sap": PoiesisVerb(
        ccl_name="sap", greek_name="Saphēneia", japanese_name="精読する",
        coordinate="Precision", flow_pole="S", helmholtz_component=HelmholtzComponent.GRADIENT
    ),
    "ski": PoiesisVerb(
        ccl_name="ski", greek_name="Skiagraphia", japanese_name="走査する",
        coordinate="Precision", flow_pole="S", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),

    # 10. Diástasis 族 S極
    "prs": PoiesisVerb(
        ccl_name="prs", greek_name="Prosochē", japanese_name="注視する",
        coordinate="Scale", flow_pole="S", helmholtz_component=HelmholtzComponent.GRADIENT
    ),
    "per": PoiesisVerb(
        ccl_name="per", greek_name="Perioptē", japanese_name="一覧する",
        coordinate="Scale", flow_pole="S", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),

    # 11. Orexis 族 S極
    "apo": PoiesisVerb(
        ccl_name="apo", greek_name="Apodochē", japanese_name="傾聴する",
        coordinate="Valence", flow_pole="S", helmholtz_component=HelmholtzComponent.GRADIENT
    ),
    "exe": PoiesisVerb(
        ccl_name="exe", greek_name="Exetasis", japanese_name="吟味する",
        coordinate="Valence", flow_pole="S", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),

    # 12. Chronos 族 S極
    "his": PoiesisVerb(
        ccl_name="his", greek_name="Historiā", japanese_name="回顧する",
        coordinate="Temporality", flow_pole="S", helmholtz_component=HelmholtzComponent.SOLENOIDAL
    ),
    "prg": PoiesisVerb(
        ccl_name="prg", greek_name="Prognōsis", japanese_name="予感する",
        coordinate="Temporality", flow_pole="S", helmholtz_component=HelmholtzComponent.GRADIENT
    ),
}
assert len(POIESIS_VERBS) == 36, f"Expected 36 Poiesis verbs (v5.0+), but got {len(POIESIS_VERBS)}"


# ---------------------------------------------------------------------------
# H-series — 中動態 (being) の 12 前動詞 (v5.1)
# ---------------------------------------------------------------------------
# PURPOSE: φ_SA (反射弧) × 6修飾座標 × 2極。μ を迂回して「起きている」状態。
# Poiesis = doing (能動態) に対し H-series = being (中動態)。
# L3 では Poiesis と同じ 0-cell だが、doing/being の区別は Hom 空間の Drift で捕捉 (v5.4)。

@dataclass(frozen=True)
class HSeriesVerb:
    """H-series (中動態) の 1 要素。being 状態を表す。"""
    bracket_name: str        # e.g., "[tr]"
    greek_name: str          # e.g., "Tropos"
    japanese_name: str       # e.g., "向き"
    coordinate: str          # 属する修飾座標
    pole: str                # 極1 or 極2

HSERIES_VERBS: dict[str, HSeriesVerb] = {
    # Telos 族 H-series
    "tr": HSeriesVerb(bracket_name="[tr]", greek_name="Tropos", japanese_name="向き",
                      coordinate="Value", pole="E"),
    "sy": HSeriesVerb(bracket_name="[sy]", greek_name="Synaisthēsis", japanese_name="共感覚",
                      coordinate="Value", pole="P"),
    # Methodos 族 H-series
    "pa": HSeriesVerb(bracket_name="[pa]", greek_name="Pathos", japanese_name="受容",
                      coordinate="Function", pole="E"),
    "he": HSeriesVerb(bracket_name="[he]", greek_name="Hexis", japanese_name="習慣態",
                      coordinate="Function", pole="P"),
    # Krisis 族 H-series
    "ek": HSeriesVerb(bracket_name="[ek]", greek_name="Ektasis", japanese_name="伸張",
                      coordinate="Precision", pole="U"),
    "th": HSeriesVerb(bracket_name="[th]", greek_name="Thixis", japanese_name="接触",
                      coordinate="Precision", pole="C"),
    # Diástasis 族 H-series
    "eu": HSeriesVerb(bracket_name="[eu]", greek_name="Eurythmia", japanese_name="均整",
                      coordinate="Scale", pole="Mi"),
    "sh": HSeriesVerb(bracket_name="[sh]", greek_name="Schēma", japanese_name="形態",
                      coordinate="Scale", pole="Ma"),
    # Orexis 族 H-series
    "ho": HSeriesVerb(bracket_name="[ho]", greek_name="Hormē", japanese_name="衝動",
                      coordinate="Valence", pole="+"),
    "ph": HSeriesVerb(bracket_name="[ph]", greek_name="Phobos", japanese_name="忌避",
                      coordinate="Valence", pole="-"),
    # Chronos 族 H-series
    "an": HSeriesVerb(bracket_name="[an]", greek_name="Anamnēsis", japanese_name="追想",
                      coordinate="Temporality", pole="Past"),
    "pl": HSeriesVerb(bracket_name="[pl]", greek_name="Plērophoria", japanese_name="充溢",
                      coordinate="Temporality", pole="Future"),
}
assert len(HSERIES_VERBS) == 12, f"Expected 12 H-series verbs, but got {len(HSERIES_VERBS)}"

# 全 48 認知操作 (v5.4: K₄柱モデル)
# Poiesis (36) + H-series (12) = L3 の 48 0-cell (全体で体系核)
ALL_COGNITIVE_OPS_COUNT = len(POIESIS_VERBS) + len(HSERIES_VERBS)
assert ALL_COGNITIVE_OPS_COUNT == 48, f"Expected 48 cognitive ops, but got {ALL_COGNITIVE_OPS_COUNT}"


# ---------------------------------------------------------------------------
# Mapping Utilities
# ---------------------------------------------------------------------------

# PURPOSE: CCL 名から PoiesisVerb を取得
def get_poiesis_verb(ccl_name: str) -> PoiesisVerb | None:
    """CCL 名（例: 'noe'）から PoiesisVerb 定義を取得する。"""
    ccl_name = ccl_name.lower().replace("/", "")
    return POIESIS_VERBS.get(ccl_name)


# PURPOSE: 演算子と Flow 極性から生成される動詞を特定
def map_to_verb(operator: HelmholtzOperator, flow_pole: str) -> PoiesisVerb | None:
    """Helmholtz 演算子と Flow 極性 (I or A) から、対応する動詞を取得する。"""
    for verb in POIESIS_VERBS.values():
        if (verb.coordinate == operator.coordinate and
            verb.helmholtz_component == operator.component and
            verb.flow_pole == flow_pole):
            return verb
    return None


# PURPOSE: WF 実行パイプラインに Helmholtz コンテキストを注入する
@dataclass(frozen=True)
class HelmholtzContext:
    """WF 実行時の Helmholtz コンテキスト。

    各認知動詞が持つ数学的性質を、ランタイムで参照可能にする。
    Γ (gradient/最適化) か Q (solenoidal/探索) かで、
    モジュールの挙動パラメータを自動調整する基盤。
    """
    ccl_name: str                    # CCL 名 (e.g., "noe")
    coordinate: str                  # 修飾座標 (e.g., "Value")
    flow_pole: str                   # "I" (Inference) or "A" (Action)
    is_gradient: bool                # Γ 成分 = True → 最適化/収束モード
    is_solenoidal: bool              # Q 成分 = True → 探索/循環モード
    description_ja: str              # 演算子の数学的意味 (日本語)
    helmholtz_score: float | None = None  # H_s = Γ/(Γ+Q) (外部から注入)


def verb_helmholtz_context(
    ccl_name: str,
    helmholtz_score: float | None = None,
) -> HelmholtzContext | None:
    """CCL 名から Helmholtz コンテキストを生成する。

    WF 実行パイプラインの各ステップで呼び出し、
    実行中の動詞に対応する Helmholtz 演算子の Γ/Q 成分を取得する。

    Args:
        ccl_name: CCL 動詞名 (e.g., "noe", "/ene", "ske")
        helmholtz_score: 外部から注入する H_s = Γ/(Γ+Q) スコア (0-1)
            None の場合、Γ/Q 成分から理論値を設定

    Returns:
        HelmholtzContext or None (未知の動詞名)

    Usage:
        ctx = verb_helmholtz_context("noe")
        if ctx and ctx.is_solenoidal:
            # 探索モード: 結論への収束を急がない
            temperature = 0.8
        elif ctx and ctx.is_gradient:
            # 最適化モード: 確実に収束させる
            temperature = 0.3
    """
    verb = get_poiesis_verb(ccl_name)
    if verb is None:
        return None

    op = verb.operator

    # H_s が未指定の場合、Γ/Q 成分から理論値を設定
    if helmholtz_score is None:
        helmholtz_score = 1.0 if op.is_gradient else 0.0

    return HelmholtzContext(
        ccl_name=verb.ccl_name,
        coordinate=op.coordinate,
        flow_pole=verb.flow_pole,
        is_gradient=op.is_gradient,
        is_solenoidal=op.is_solenoidal,
        description_ja=op.description_ja,
        helmholtz_score=helmholtz_score,
    )


# ---------------------------------------------------------------------------
# P5: Derivative Recommendation → Helmholtz Enrichment
# ---------------------------------------------------------------------------

# Theorem code → CCL verb name mapping
# Each theorem is one of the 36 verbs (v5.0+). The Series letter maps to a coordinate:
#   O=Value, S=Function, H=Valence, P=Precision, K=Temporality, A=Scale
# The number maps to position in the quartet (I-pole Q, I-pole Γ, A-pole Q, A-pole Γ)
_SERIES_COORDINATE: dict[str, str] = {
    "O": "Value", "S": "Function", "H": "Valence",
    "P": "Precision", "K": "Temporality", "A": "Scale",
}
# Position 1-6 maps to (flow_pole, component) — v5.0+: S極追加
#   1: I,Q(solenoidal)  2: I,Γ(gradient)  3: A,Q(solenoidal)  4: A,Γ(gradient)
#   5: S,Q(solenoidal)  6: S,Γ(gradient)
_POSITION_SPEC: dict[int, tuple[str, HelmholtzComponent]] = {
    1: ("I", HelmholtzComponent.SOLENOIDAL),
    2: ("I", HelmholtzComponent.GRADIENT),
    3: ("A", HelmholtzComponent.SOLENOIDAL),
    4: ("A", HelmholtzComponent.GRADIENT),
    5: ("S", HelmholtzComponent.SOLENOIDAL),
    6: ("S", HelmholtzComponent.GRADIENT),
}


def _theorem_to_verb(theorem: str) -> PoiesisVerb | None:
    """Theorem code (e.g., 'O1', 'S3') → PoiesisVerb.

    Uses Series→coordinate and position→(flow_pole, component) to find
    the matching verb in POIESIS_VERBS.
    """
    if len(theorem) < 2:
        return None
    series_letter = theorem[0]
    try:
        position = int(theorem[1])
    except (ValueError, IndexError):
        return None

    coord = _SERIES_COORDINATE.get(series_letter)
    spec = _POSITION_SPEC.get(position)
    if coord is None or spec is None:
        return None

    flow_pole, component = spec
    for verb in POIESIS_VERBS.values():
        if (verb.coordinate == coord and
            verb.flow_pole == flow_pole and
            verb.helmholtz_component == component):
            return verb
    return None


@dataclass(frozen=True)
class EnrichedRecommendation:
    """DerivativeRecommendation + Helmholtz context.

    P5: derivative_selector の出力を Helmholtz コンテキストで装飾する。
    confidence は H_s に変換され、Γ/Q 情報と共にダウンストリームへ渡る。
    """
    theorem: str
    derivative: str
    confidence: float
    rationale: str
    alternatives: list[str]
    # Helmholtz enrichment
    helmholtz: HelmholtzContext | None
    helmholtz_adjusted_confidence: float  # confidence × H_s 方向加重


# PURPOSE: DerivativeRecommendation を Helmholtz コンテキストで装飾する
def enrich_with_helmholtz(
    theorem: str,
    derivative: str,
    confidence: float,
    rationale: str = "",
    alternatives: list[str] | None = None,
) -> EnrichedRecommendation:
    """DerivativeRecommendation の出力を Helmholtz で装飾する。

    theorem code (O1, S2, ...) → CCL verb → verb_helmholtz_context() で
    Γ/Q コンテキストを取得し、confidence を H_s で方向加重する。

    方向加重ロジック:
    - Γ 成分 (最適化/収束): adjusted = confidence × 1.0 (そのまま)
      → 高 confidence をそのまま信頼
    - Q 成分 (探索/循環): adjusted = confidence × 0.7 + 0.15
      → confidence を緩和し、下限を保証 (探索は低 confidence でも進める)

    Args:
        theorem: Theorem code (e.g., "O1", "S2")
        derivative: Selected derivative code (e.g., "nous", "comp")
        confidence: Keyword-based confidence (0.0-1.0)
        rationale: Selection rationale text
        alternatives: Alternative derivative codes

    Returns:
        EnrichedRecommendation with Helmholtz context and adjusted confidence
    """
    verb = _theorem_to_verb(theorem)
    h_ctx = verb_helmholtz_context(verb.ccl_name) if verb else None

    if h_ctx is not None and h_ctx.is_gradient:
        # Γ: 収束モード — confidence をそのまま活かす
        adjusted = confidence
    elif h_ctx is not None and h_ctx.is_solenoidal:
        # Q: 探索モード — confidence を緩和、下限 0.15
        adjusted = confidence * 0.7 + 0.15
    else:
        adjusted = confidence

    return EnrichedRecommendation(
        theorem=theorem,
        derivative=derivative,
        confidence=confidence,
        rationale=rationale,
        alternatives=alternatives or [],
        helmholtz=h_ctx,
        helmholtz_adjusted_confidence=round(adjusted, 4),
    )


# ---------------------------------------------------------------------------
# P6: Helmholtz Parameter Adjuster
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HelmholtzParams:
    """Helmholtz-adjusted execution parameters.

    H_s に基づいてダウンストリームモジュールのパラメータを自動調整する。
    """
    temperature: float      # LLM temperature (0.1-1.0)
    num_candidates: int     # 候補生成数 (1-5)
    exploration_weight: float  # EFE の epistemic 項の重み (0.0-1.0)
    convergence_threshold: float  # 収束判定の閾値 (0.0-1.0)
    mode: str               # "exploit" | "explore" | "balanced"


# PURPOSE: H_s から実行パラメータを自動調整する
def helmholtz_adjust(h_ctx: HelmholtzContext | None) -> HelmholtzParams:
    """HelmholtzContext からモジュールパラメータを自動調整する。

    Γ/Q 分解に基づき、最適化/探索のバランスに応じた実行パラメータを返す。

    H_s | mode     | temperature | candidates | exploration | convergence
    ----|----------|-------------|------------|-------------|------------
    1.0 | exploit  | 0.2         | 1          | 0.0         | 0.9
    0.5 | balanced | 0.5         | 3          | 0.5         | 0.5
    0.0 | explore  | 0.8         | 5          | 1.0         | 0.1

    Args:
        h_ctx: HelmholtzContext (None → balanced default)

    Returns:
        HelmholtzParams with adjusted values
    """
    if h_ctx is None or h_ctx.helmholtz_score is None:
        h_s = 0.5  # balanced default
    else:
        h_s = h_ctx.helmholtz_score

    # Linear interpolation between explore (h_s=0) and exploit (h_s=1)
    temperature = round(0.8 - 0.6 * h_s, 2)       # 0.8 → 0.2
    num_candidates = max(1, round(5 - 4 * h_s))     # 5 → 1
    exploration_weight = round(1.0 - h_s, 2)         # 1.0 → 0.0
    convergence_threshold = round(0.1 + 0.8 * h_s, 2)  # 0.1 → 0.9

    if h_s >= 0.7:
        mode = "exploit"
    elif h_s <= 0.3:
        mode = "explore"
    else:
        mode = "balanced"

    return HelmholtzParams(
        temperature=temperature,
        num_candidates=num_candidates,
        exploration_weight=exploration_weight,
        convergence_threshold=convergence_threshold,
        mode=mode,
    )


__all__ = [
    "PoiesisVerb",
    "POIESIS_VERBS",
    "HSeriesVerb",
    "HSERIES_VERBS",
    "ALL_COGNITIVE_OPS_COUNT",
    "HelmholtzContext",
    "EnrichedRecommendation",
    "HelmholtzParams",
    "get_poiesis_verb",
    "map_to_verb",
    "verb_helmholtz_context",
    "enrich_with_helmholtz",
    "helmholtz_adjust",
]

