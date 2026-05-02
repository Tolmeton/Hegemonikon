from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L3/弱2-圏] <- mekhane/fep/ A0→Poiesis間の合成は弱2-圏構造を持つ→two_cellが担う
"""
Two-Cell — Weak 2-Category Structure for v5.4 Poiesis (K₄柱モデル, 48 0-cell)

Origin: G1 of /bou category theory roadmap (2026-02-11)
Refactored: 2026-02-28 for v4.1 (24 Poiesis + Dokimasia parameters)
Extended: 2026-03-25 for v5.4 (48 cognitive operations: 36 Poiesis + 12 H-series)

L3 (weak 2-category / bicategory):
    - 0-cells: 48 cognitive operations (36 Poiesis + 12 H-series, v5.4 K₄柱モデル)
        - 36 Poiesis: Flow(S/I/A) × 6 coordinates × 2 poles
    - 1-cells: CCL >> pipelines between Poiesis
    - 2-cells: Relations between pipelines with same endpoints (associator)

L4 extension (Time → BiCat):
    - session_id field enables tracking associator evolution over time
    - Mneme (handoff + violations) provides time parameter

Design decision (2026-02-28):
    L4 = Time → BiCat (NOT Tricategory).
    The weak 2-category itself evolves over time via Mneme.
    3-cells are NOT static structure but temporal change of L3.

    "/ele+ で刺したら、Tricategory は棄却。Time→BiCat が正解。" — 2026-02-28

Design symmetry:
    drift_calculator:   source + compressed → DriftResult (L2: Hom value)
    two_cell:           poiesis + pipelines → PoiesisSpace (L3: 2-cells)
    cone_builder:       WF outputs → Cone (C0-C3)

L3 実存検証 (2026-02-28 /zet+ 実測):
    CCL 括弧構造はテンプレート展開のコンテキストを変える。
    (/noe >> /ele) >> /ene ≠ /noe >> (/ele >> /ene)
    → associator は装飾品ではない。入れ子が実行文脈を変える。
"""


import warnings
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# =============================================================================
# Core Data Structures
# =============================================================================


# PURPOSE: n-cell の統一的インターフェースを実現する (L3+L4 対応)
@dataclass
class HigherCell:
    """An n-cell in the weak 2-category (bicategory).

    In a weak 2-category (bicategory) for HGK v5.4:
        - 0-cells: 48 cognitive operations (36 Poiesis + 12 H-series)
        - 1-cells: CCL >> pipelines between cognitive operations
        - 2-cells: associators — relations between pipelines with same endpoints

    The weak (lax) nature means composition is associative
    only up to isomorphism, not strictly (strictification rejected).

    L4 extension: session_id tracks temporal evolution of associators.
    """

    source: str            # e.g., "V01" (0-cell or 1-cell source)
    target: str            # e.g., "V04" (0-cell or 1-cell target)
    level: int = 1         # 0=0-cell, 1=1-cell, 2=2-cell
    label_text: str = ""   # optional human-readable label
    is_identity: bool = False
    session_id: Optional[str] = None  # L4: time parameter for Time→BiCat

    # PURPOSE: 人間可読なラベルを返す
    @property
    def label(self) -> str:
        if self.label_text:
            return self.label_text
        if self.is_identity:
            return f"id({self.source})"
        return f"{self.source} → {self.target}"

    # PURPOSE: 2つの cell の垂直合成を行う
    def compose(self, other: "HigherCell") -> Optional["HigherCell"]:
        """Compose self with other (vertical composition).

        Returns None if composition is not possible (mismatched endpoints or levels).
        """
        if self.level != other.level:
            return None
        if self.target != other.source:
            return None

        return HigherCell(
            source=self.source,
            target=other.target,
            level=self.level,
            label_text=f"{self.label} ∘ {other.label}" if not (self.is_identity or other.is_identity) else "",
            is_identity=self.is_identity and other.is_identity,
            session_id=self.session_id or other.session_id,
        )


# PURPOSE: 弱2-圏の associator (2-cell) を表現する
@dataclass
class Associator:
    """An associator witnessing (f>>g)>>h ≅ f>>(g>>h).

    In a weak 2-category, composition is associative only up to isomorphism.
    The associator is the 2-cell witnessing this isomorphism.

    magnitude: how "far" from strict (0.0 = strict, 1.0 = maximally non-strict).
        -1 = auto-compute from coordinate distance.
        Auto-computation: same-tribe=0.2, 2-tribes=0.5, 3-tribes=0.8.

    L3 実存検証 (2026-02-28): CCL 括弧構造はテンプレート展開のコンテキストを変える。
    この magnitude は将来 hermeneus のテンプレート差分から実測計算できる (TODO)。
    """

    f: str  # first 1-cell (e.g., "/noe")
    g: str  # second 1-cell (e.g., "/ele")
    h: str  # third 1-cell (e.g., "/ene")
    magnitude: float = -1.0  # -1=auto-compute, 0.0=strict, 1.0=maximally non-strict
    session_id: Optional[str] = None  # L4: time parameter

    def __post_init__(self):
        """Auto-compute magnitude from coordinate distance if not explicitly set."""
        if self.magnitude < 0:
            self.magnitude = self._compute_magnitude()

    # PURPOSE: 座標距離に基づいて magnitude を自動計算する
    def _compute_magnitude(self) -> float:
        """Compute associator magnitude from coordinate distance of the 3 Poiesis.

        Magnitude = how much the nesting order matters.
        Same-tribe verbs → low magnitude (0.2).
        Cross-tribe verbs → high magnitude (context switch between domains).
        Identity insertion → magnitude 0.0.

        Future: replace with hermeneus template diff measurement.
        """
        if "id" in [self.f, self.g, self.h]:
            return 0.0

        def extract_cmds(c: str) -> List[str]:
            return [x.strip() for x in c.replace("(", "").replace(")", "").split(">>") if x.strip() != "id"]

        all_cmds = extract_cmds(self.f) + extract_cmds(self.g) + extract_cmds(self.h)
        spaces = [get_poiesis_space(cmd) for cmd in all_cmds]
        
        if not spaces or any(s is None for s in spaces):
            return 0.5  # unknown → neutral

        tribes = {s.tribe for s in spaces if s is not None}
        n_tribes = len(tribes)

        # Same tribe → low magnitude (0.2), two tribes → medium (0.5), three or more → high (0.8)
        if n_tribes == 1:
            return 0.2
        elif n_tribes == 2:
            return 0.5
        else:
            return 0.8

    # PURPOSE: associator のラベルを返す
    @property
    def label(self) -> str:
        return f"α({self.f},{self.g},{self.h})[{self.magnitude:.2f}]"

    # PURPOSE: left-associated の合成を表現
    @property
    def left_associated(self) -> str:
        """(f>>g)>>h — left-associated composition."""
        return f"({self.f}>>{self.g})>>{self.h}"

    # PURPOSE: right-associated の合成を表現
    @property
    def right_associated(self) -> str:
        """f>>(g>>h) — right-associated composition."""
        return f"{self.f}>>({self.g}>>{self.h})"

    # PURPOSE: associator が非自明かどうか (strictly > 0)
    @property
    def is_nontrivial(self) -> bool:
        """True if this associator is non-trivial (not the identity)."""
        return self.magnitude > 0.0

    # PURPOSE: 2つの associator の自然変換 (L4: 時間的変容)
    def temporal_shift(self, new_magnitude: float, new_session_id: str) -> "Associator":
        """Create a new associator with changed magnitude (L4: learning).

        This represents the temporal evolution of L3:
        F: T → BiCat maps each session to a bicategory with different associator magnitudes.
        """
        return Associator(
            f=self.f,
            g=self.g,
            h=self.h,
            magnitude=new_magnitude,
            session_id=new_session_id,
        )


# PURPOSE: v4.1 Poiesis (動詞) とその Dokimasia パラメータを表現する
@dataclass
class PoiesisSpace:
    """A Poiesis verb and its Dokimasia parameter space.

    Replaces legacy DerivativeSpace. Each Poiesis is a 0-cell in L3.
    """

    verb_id: str         # e.g., "V01"
    verb_name: str       # e.g., "Noēsis"
    verb_ja: str         # e.g., "理解"
    coordinates: str     # e.g., "I × E"
    ccl_cmd: str         # e.g., "/noe"
    tribe: str           # e.g., "Ousia" (族名)

    # PURPOSE: この Poiesis に固有の座標極を返す
    @property
    def native_poles(self) -> Dict[str, str]:
        """The coordinate poles that define this specific Poiesis.

        Parsed from the coordinates string (e.g., 'I × E' → {'Flow': 'I', 'Strategy': 'E'}).
        """
        _POLE_TO_AXIS = {
            "I": "Flow", "A": "Flow",
            "E": "Strategy", "P": "Strategy",
            "Explore": "Strategy", "Exploit": "Strategy",
            "C": "Precision", "U": "Precision",
            "Mi": "Scale", "Ma": "Scale",
            "+": "Valence", "-": "Valence",
            "Past": "Temporality", "Future": "Temporality",
        }
        poles: Dict[str, str] = {}
        parts = [p.strip() for p in self.coordinates.split("×")]
        for part in parts:
            axis = _POLE_TO_AXIS.get(part)
            if axis:
                poles[axis] = part
        return poles

    # PURPOSE: 全 Dokimasia パラメータ軸を返す (全動詞共通)
    @staticmethod
    def all_axes() -> List[Tuple[str, str, str]]:
        """All 6 Dokimasia parameter axes with (axis_name, pole_a, pole_b)."""
        return [
            ("Flow", "I", "A"),
            ("Strategy", "E", "P"),
            ("Precision", "C", "U"),
            ("Scale", "Mi", "Ma"),
            ("Valence", "+", "-"),
            ("Temporality", "Past", "Future"),
        ]

    # PURPOSE: この Poiesis の 0-cell としてのラベルを返す
    @property
    def zero_cell_label(self) -> str:
        return f"{self.verb_id} {self.verb_name}"

    # PURPOSE: 2つの CCL コマンド間の 1-cell を生成する
    def one_cell_to(self, other: "PoiesisSpace") -> HigherCell:
        """Create a 1-cell (CCL pipeline step) from this Poiesis to another."""
        return HigherCell(
            source=self.verb_id,
            target=other.verb_id,
            level=1,
            label_text=f"{self.ccl_cmd} >> {other.ccl_cmd}",
        )

    # PURPOSE: 3つの Poiesis から Associator を構成する (HigherCell → Associator ブリッジ)
    @staticmethod
    def compose_triple(
        a: "PoiesisSpace", b: "PoiesisSpace", c: "PoiesisSpace",
        session_id: Optional[str] = None,
    ) -> Tuple[HigherCell, HigherCell, Associator]:
        """Bridge HigherCell and Associator: create 1-cells and their associator.

        Returns:
            (f: a→b, g: b→c, associator: α_{f,g,...})
        """
        f = a.one_cell_to(b)
        g = b.one_cell_to(c)
        assoc = Associator(
            f=a.ccl_cmd,
            g=b.ccl_cmd,
            h=c.ccl_cmd,
            session_id=session_id,
        )
        return f, g, assoc


# =============================================================================
# 48 Poiesis Registry (v5.4 core — K₄柱モデル)
# =============================================================================

# Each entry: (verb_id, verb_name, verb_ja, coordinates, ccl_cmd, tribe)
_POIESIS_DATA: List[Tuple[str, str, str, str, str, str]] = [
    # Ousia 族 (Flow × Strategy) — 存在基盤
    ("V01", "Noēsis", "理解", "I × E", "/noe", "Ousia"),
    ("V02", "Boulēsis", "意志", "I × P", "/bou", "Ousia"),
    ("V03", "Zētēsis", "探求", "A × E", "/zet", "Ousia"),
    ("V04", "Energeia", "実行", "A × P", "/ene", "Ousia"),

    # Methodos 族 (Flow × Strategy, Schema level) — 方法
    ("V05", "Skepsis", "発散", "I × Explore", "/ske", "Methodos"),
    ("V06", "Synagōgē", "収束", "I × Exploit", "/sag", "Methodos"),
    ("V07", "Peira", "実験", "A × Explore", "/pei", "Methodos"),
    ("V08", "Tekhnē", "適用", "A × Exploit", "/tek", "Methodos"),

    # Krisis 族 (Flow × Precision) — 判断
    ("V09", "Katalēpsis", "確定", "I × C", "/kat", "Krisis"),
    ("V10", "Epochē", "留保", "I × U", "/epo", "Krisis"),
    ("V11", "Proairesis", "決断", "A × C", "/pai", "Krisis"),
    ("V12", "Dokimasia", "打診", "A × U", "/dok", "Krisis"),

    # Diástasis 族 (Flow × Scale) — 空間
    ("V13", "Analysis", "詳細分析", "I × Mi", "/lys", "Diástasis"),
    ("V14", "Synopsis", "俯瞰", "I × Ma", "/ops", "Diástasis"),
    ("V15", "Akribeia", "精密操作", "A × Mi", "/akr", "Diástasis"),
    ("V16", "Architektonikē", "全体設計", "A × Ma", "/arc", "Diástasis"),

    # Orexis 族 (Flow × Valence) — 欲求
    ("V17", "Bebaiōsis", "肯定", "I × +", "/beb", "Orexis"),
    ("V18", "Elenchos", "批判", "I × -", "/ele", "Orexis"),
    ("V19", "Prokopē", "推進", "A × +", "/kop", "Orexis"),
    ("V20", "Diorthōsis", "是正", "A × -", "/dio", "Orexis"),

    # Chronos 族 (Flow × Temporality) — 時間
    ("V21", "Hypomnēsis", "想起", "I × Past", "/hyp", "Chronos"),
    ("V22", "Promētheia", "予見", "I × Future", "/prm", "Chronos"),
    ("V23", "Anatheōrēsis", "省顧", "A × Past", "/ath", "Chronos"),
    ("V24", "Proparaskeuē", "仕掛", "A × Future", "/par", "Chronos"),

    # --- v5.0 S極動詞 (T5-T6): Flow=S (Sensory/Afferent) ---
    ("V25", "Theōria", "観照", "S × E", "/the", "Ousia"),
    ("V26", "Antilepsis", "検知", "S × P", "/ant", "Ousia"),
    ("V27", "Ereuna", "探知", "S × Explore", "/ere", "Methodos"),
    ("V28", "Anagnōsis", "参照", "S × Exploit", "/agn", "Methodos"),
    ("V29", "Saphēneia", "精読", "S × C", "/sap", "Krisis"),
    ("V30", "Skiagraphia", "走査", "S × U", "/ski", "Krisis"),
    ("V31", "Prosochē", "注視", "S × Mi", "/prs", "Diástasis"),
    ("V32", "Perioptē", "一覧", "S × Ma", "/per", "Diástasis"),
    ("V33", "Apodochē", "傾聴", "S × +", "/apo", "Orexis"),
    ("V34", "Exetasis", "吟味", "S × -", "/exe", "Orexis"),
    ("V35", "Historiā", "回顧", "S × Past", "/his", "Chronos"),
    ("V36", "Prognōsis", "予感", "S × Future", "/prg", "Chronos"),

    # --- v5.4 S∩A極動詞 (H-series): Flow=S∩A (being) ---
    ("H01", "Tropē", "向変", "S∩A × E", "[tr]", "Ousia"),
    ("H02", "Synaisthēsis", "体感", "S∩A × P", "[sy]", "Ousia"),
    ("H03", "Paidia", "遊戯", "S∩A × Explore", "[pa]", "Methodos"),
    ("H04", "Hexis", "習慣態", "S∩A × Exploit", "[he]", "Methodos"),
    ("H05", "Ekplēxis", "驚愕", "S∩A × C", "[ek]", "Krisis"),
    ("H06", "Thambos", "戸惑い", "S∩A × U", "[th]", "Krisis"),
    ("H07", "Euarmostia", "微調和", "S∩A × Mi", "[eu]", "Diástasis"),
    ("H08", "Synhorasis", "一望", "S∩A × Ma", "[sh]", "Diástasis"),
    ("H09", "Hormē", "衝動", "S∩A × +", "[ho]", "Orexis"),
    ("H10", "Phobos", "忌避", "S∩A × -", "[ph]", "Orexis"),
    ("H11", "Anamnēsis", "追想", "S∩A × Past", "[an]", "Chronos"),
    ("H12", "Prolepsis", "充溢", "S∩A × Future", "[pl]", "Chronos"),
]

# Tribe grouping (v5.4: 8動詞/族 = I極2 + A極2 + S極2 + S∩A極2)
_TRIBES = {
    "Ousia": ["V01", "V02", "V03", "V04", "V25", "V26", "H01", "H02"],
    "Methodos": ["V05", "V06", "V07", "V08", "V27", "V28", "H03", "H04"],
    "Krisis": ["V09", "V10", "V11", "V12", "V29", "V30", "H05", "H06"],
    "Diástasis": ["V13", "V14", "V15", "V16", "V31", "V32", "H07", "H08"],
    "Orexis": ["V17", "V18", "V19", "V20", "V33", "V34", "H09", "H10"],
    "Chronos": ["V21", "V22", "V23", "V24", "V35", "V36", "H11", "H12"],
}


# =============================================================================
# Lookup Functions
# =============================================================================


# PURPOSE: verb_id または ccl コマンドから PoiesisSpace を取得する
def get_poiesis_space(verb_id: str) -> Optional[PoiesisSpace]:
    """Get a PoiesisSpace by verb ID (e.g., 'V01') or CCL command (e.g., '/noe')."""
    for vid, name, ja, coords, ccl, tribe in _POIESIS_DATA:
        if vid == verb_id or ccl == verb_id:
            return PoiesisSpace(
                verb_id=vid,
                verb_name=name,
                verb_ja=ja,
                coordinates=coords,
                ccl_cmd=ccl,
                tribe=tribe,
            )
    return None


# PURPOSE: 全 PoiesisSpace を返す
def get_all_spaces() -> List[PoiesisSpace]:
    """Get all Poiesis spaces in this registry (48 verbs, v5.4)."""
    return [
        PoiesisSpace(vid, name, ja, coords, ccl, tribe)
        for vid, name, ja, coords, ccl, tribe in _POIESIS_DATA
    ]


# PURPOSE: 族名から PoiesisSpace を返す
def get_tribe_spaces(tribe: str) -> List[PoiesisSpace]:
    """Get Poiesis spaces belonging to a tribe."""
    verb_ids = _TRIBES.get(tribe, [])
    return [s for s in get_all_spaces() if s.verb_id in verb_ids]


# =============================================================================
# Associator Construction
# =============================================================================


# PURPOSE: 3つの CCL コマンドから Associator を構築する
def build_associator(
    f_cmd: str,
    g_cmd: str,
    h_cmd: str,
    magnitude: float = -1.0,
    session_id: Optional[str] = None,
) -> Optional[Associator]:
    """Build an associator from three CCL commands.

    Returns None if any command is unknown.
    """
    for term in [f_cmd, g_cmd, h_cmd]:
        for cmd in term.replace("(", "").replace(")", "").split(">>"):
            cmd = cmd.strip()
            if cmd != "id" and get_poiesis_space(cmd) is None:
                return None

    return Associator(
        f=f_cmd,
        g=g_cmd,
        h=h_cmd,
        magnitude=magnitude,
        session_id=session_id,
    )


# =============================================================================
# Statistics & Verification
# =============================================================================


# PURPOSE: 体系全体の統計を返す
def count_cells() -> Dict[str, int]:
    """Count cells across the system.

    Expected (v5.4):
        0-cells: 48 (one per Poiesis)
        1-cells: 48 × 47 = 2256 (all possible pipelines)
        Tribes: 6
    """
    spaces = get_all_spaces()
    n_zero_cells = len(spaces)
    n_one_cells = n_zero_cells * (n_zero_cells - 1)  # all ordered pairs
    n_tribes = len(_TRIBES)

    return {
        "zero_cells": n_zero_cells,
        "one_cells": n_one_cells,
        "tribes": n_tribes,
    }


# PURPOSE: pentagon identity を検証する (4つの 1-cell の合成)
def verify_pentagon(
    f_cmd: str, g_cmd: str, h_cmd: str, k_cmd: str
) -> List[str]:
    """Verify pentagon identity for four Poiesis pipeline steps.

    Construct HigherCells and verify that:
    Path 1: ((f∘g)∘h)∘k → compose left-to-right
    Path 2: f∘(g∘(h∘k)) → compose right-to-left
    Both must have the same source and target.

    Returns list of violations (empty if valid).
    """
    violations: List[str] = []

    # Resolve commands to Poiesis spaces
    spaces = []
    for cmd in [f_cmd, g_cmd, h_cmd, k_cmd]:
        s = get_poiesis_space(cmd)
        if s is None:
            violations.append(f"Unknown command: {cmd}")
            return violations
        spaces.append(s)

    a, b, c, d = spaces

    # Build 1-cells: f:a→b, g:b→c, h:c→d
    f = HigherCell(source=a.verb_id, target=b.verb_id, level=1)
    g = HigherCell(source=b.verb_id, target=c.verb_id, level=1)
    h = HigherCell(source=c.verb_id, target=d.verb_id, level=1)

    # Need a 5th object for the 4th morphism k:d→e
    all_spaces = get_all_spaces()
    used_ids = {s.verb_id for s in spaces}
    e_space = next((s for s in all_spaces if s.verb_id not in used_ids), None)
    if e_space is None:
        violations.append("Cannot find 5th Poiesis for pentagon")
        return violations

    k_cell = HigherCell(source=d.verb_id, target=e_space.verb_id, level=1)

    # Path 1 (left-associated): ((f∘g)∘h)∘k
    fg = f.compose(g)
    if fg is None:
        violations.append("f∘g composability fails")
        return violations
    fgh = fg.compose(h)
    if fgh is None:
        violations.append("(f∘g)∘h composability fails")
        return violations
    path1 = fgh.compose(k_cell)
    if path1 is None:
        violations.append("((f∘g)∘h)∘k composability fails")
        return violations

    # Path 2 (right-associated): f∘(g∘(h∘k))
    hk = h.compose(k_cell)
    if hk is None:
        violations.append("h∘k composability fails")
        return violations
    ghk = g.compose(hk)
    if ghk is None:
        violations.append("g∘(h∘k) composability fails")
        return violations
    path2 = f.compose(ghk)
    if path2 is None:
        violations.append("f∘(g∘(h∘k)) composability fails")
        return violations

    # Verify endpoints match (weak associativity at the 4-composition level)
    if path1.source != path2.source:
        violations.append(f"Pentagon source mismatch: {path1.source} ≠ {path2.source}")
    if path1.target != path2.target:
        violations.append(f"Pentagon target mismatch: {path1.target} ≠ {path2.target}")

    # Verify magnitude coherence (max magnitude across paths matches)
    # Path 1: α(f>>g, h, k) and α(f, g, h>>k)
    a1 = build_associator(f"{f_cmd}>>{g_cmd}", h_cmd, k_cmd)
    a2 = build_associator(f_cmd, g_cmd, f"{h_cmd}>>{k_cmd}")
    
    # Path 2: α(f, g, h)⊗id_k, α(f, g>>h, k), id_f⊗α(g, h, k)
    a3 = build_associator(f_cmd, g_cmd, h_cmd) 
    a4 = build_associator(f_cmd, f"{g_cmd}>>{h_cmd}", k_cmd)
    a5 = build_associator(g_cmd, h_cmd, k_cmd)

    assocs = [a1, a2, a3, a4, a5]
    if any(a is None for a in assocs):
        violations.append(f"Cannot build all associators for pentagon {f_cmd},{g_cmd},{h_cmd},{k_cmd}")
    else:
        # In a strict bicategory, path magnitudes should match (here using max to represent composition cost)
        path1_mag = max(a1.magnitude, a2.magnitude) # type: ignore
        path2_mag = max(a3.magnitude, a4.magnitude, a5.magnitude) # type: ignore
        if path1_mag != path2_mag:
            violations.append(f"Pentagon magnitude mismatch: Path1={path1_mag} ≠ Path2={path2_mag}")

    return violations


# PURPOSE: triangle identity を検証する (identity 1-cell の挿入)
def verify_triangle_identity(
    f_cmd: str, g_cmd: str
) -> List[str]:
    """Verify triangle identity: inserting identity between two 1-cells.

    In a bicategory, the triangle identity states:
        α_{f, id_B, g} composed with (id_f ⊗ λ_g) = (ρ_f ⊗ id_g)

    For HGK: inserting "do nothing" (identity Poiesis) into a pipeline
    should not break the associator structure. Concretely:

    1. Endpoint preservation: f >> id >> g has same endpoints as f >> g
    2. Identity transparency: the associator α(f, id, g) should have
       magnitude 0 (identity insertion is transparent)
    3. Composition law: id(A) ∘ f = f = f ∘ id(B)

    Returns list of violations (empty if valid).
    """
    violations: List[str] = []

    f_space = get_poiesis_space(f_cmd)
    g_space = get_poiesis_space(g_cmd)
    if f_space is None:
        violations.append(f"Unknown command: {f_cmd}")
        return violations
    if g_space is None:
        violations.append(f"Unknown command: {g_cmd}")
        return violations

    # 1-cell f: f_space → g_space
    f_cell = HigherCell(source=f_space.verb_id, target=g_space.verb_id, level=1)

    # Identity 1-cell at g_space (the "middle" point)
    id_b = HigherCell(
        source=g_space.verb_id, target=g_space.verb_id,
        level=1, is_identity=True,
    )

    # Need a third Poiesis for g: g_space → c_space
    all_spaces = get_all_spaces()
    used_ids = {f_space.verb_id, g_space.verb_id}
    c_space = next((s for s in all_spaces if s.verb_id not in used_ids), None)
    if c_space is None:
        violations.append("Cannot find 3rd Poiesis for triangle")
        return violations

    g_cell = HigherCell(source=g_space.verb_id, target=c_space.verb_id, level=1)

    # Check 1: f >> id_B composes correctly and equals f
    f_id = f_cell.compose(id_b)
    if f_id is None:
        violations.append(f"f ∘ id(B) composition fails for f={f_cmd}")
    elif f_id.source != f_cell.source or f_id.target != f_cell.target:
        violations.append(
            f"Right identity fails: ({f_cmd} → {g_cmd}) ∘ id({g_cmd}) "
            f"endpoints mismatch: {f_id.source}→{f_id.target} vs {f_cell.source}→{f_cell.target}"
        )

    # Check 2: id_B >> g composes correctly and equals g
    id_g = id_b.compose(g_cell)
    if id_g is None:
        violations.append(f"id(B) ∘ g composition fails for g={g_cmd}")
    elif id_g.source != g_cell.source or id_g.target != g_cell.target:
        violations.append(
            f"Left identity fails: id({g_cmd}) ∘ ({g_cmd} → {c_space.ccl_cmd}) "
            f"endpoints mismatch: {id_g.source}→{id_g.target} vs {g_cell.source}→{g_cell.target}"
        )

    # Check 3: f >> id >> g has same endpoints as f >> g
    if f_id is not None:
        f_id_g = f_id.compose(g_cell)
        f_g = f_cell.compose(
            HigherCell(source=g_space.verb_id, target=c_space.verb_id, level=1)
        )
        if f_id_g is not None and f_g is not None:
            if f_id_g.source != f_g.source or f_id_g.target != f_g.target:
                violations.append(
                    f"Triangle: f>>id>>g endpoints ≠ f>>g: "
                    f"{f_id_g.source}→{f_id_g.target} vs {f_g.source}→{f_g.target}"
                )

    # Check 4: Associator α(f, id, g) — identity insertion should be transparent
    # The associator for f >> id_B >> g should have structural transparency.
    # We verify this by using build_associator and asserting its computed magnitude is 0.
    assoc = build_associator(f_cmd, "id", g_cmd)
    if assoc is None:
        violations.append(f"Triangle: Could not build α({f_cmd}, id, {g_cmd})")
    elif assoc.is_nontrivial:
        violations.append(
            f"Triangle: α({f_cmd}, id, {g_cmd}) should be trivial (magnitude 0) "
            f"but got magnitude={assoc.magnitude}"
        )

    return violations


# PURPOSE: 全体の coherence を検証する (pentagon + triangle)
def verify_coherence() -> Dict[str, object]:
    """Verify full L3 bicategory coherence: pentagon + triangle identities.

    Runs representative samples across all tribe combinations.

    Returns:
        Dict with 'pentagon_violations', 'triangle_violations',
        'n_pentagon_checked', 'n_triangle_checked', 'is_coherent'.
    """
    pentagon_violations: List[str] = []
    triangle_violations: List[str] = []
    n_pentagon = 0
    n_triangle = 0

    # Representative sample: 1 verb per tribe
    tribe_reps = ["/noe", "/ske", "/kat", "/lys", "/beb", "/hyp"]

    # Pentagon: check all 4-tuples from representatives
    for i, f in enumerate(tribe_reps):
        for j, g in enumerate(tribe_reps):
            for k, h in enumerate(tribe_reps):
                for m, kk in enumerate(tribe_reps):
                    n_pentagon += 1
                    violations = verify_pentagon(f, g, h, kk)
                    pentagon_violations.extend(violations)

    # Triangle: check all 2-tuples from representatives
    for i, f in enumerate(tribe_reps):
        for j, g in enumerate(tribe_reps):
            n_triangle += 1
            violations = verify_triangle_identity(f, g)
            triangle_violations.extend(violations)

    return {
        "pentagon_violations": pentagon_violations,
        "triangle_violations": triangle_violations,
        "n_pentagon_checked": n_pentagon,
        "n_triangle_checked": n_triangle,
        "is_coherent": len(pentagon_violations) == 0 and len(triangle_violations) == 0,
    }


# PURPOSE: 1-cell の合成則と identity 則を検証する (全族横断)
def verify_composition_laws() -> List[str]:
    """Verify composition laws for 1-cells (cross-tribe sampling):
    1. Identity law: id(A) ∘ f = f = f ∘ id(B) for f: A→B
    2. Composability: (f ∘ g) is defined iff target(f) = source(g)
    3. Weak associativity: (f∘g)∘h ≅ f∘(g∘h) (same endpoints)
    """
    violations: List[str] = []
    spaces = get_all_spaces()

    # Cross-tribe sample: one verb from each of the 6 tribes
    sample_ids = ["V01", "V05", "V09", "V13", "V17", "V21"]
    sample = [s for s in spaces if s.verb_id in sample_ids]

    for s in sample:
        # Identity law
        id_cell = HigherCell(source=s.verb_id, target=s.verb_id, level=1, is_identity=True)
        for t in sample:
            if s.verb_id == t.verb_id:
                continue
            f = HigherCell(source=s.verb_id, target=t.verb_id, level=1)

            left_id = id_cell.compose(f)
            if left_id is None or left_id.source != f.source or left_id.target != f.target:
                violations.append(f"Left identity fails: id({s.verb_id}) ∘ {f.label}")

            right_id = f.compose(
                HigherCell(source=t.verb_id, target=t.verb_id, level=1, is_identity=True)
            )
            if right_id is None or right_id.source != f.source or right_id.target != f.target:
                violations.append(f"Right identity fails: {f.label} ∘ id({t.verb_id})")

    # Composability: target(f) ≠ source(g) → None
    f_nc = HigherCell(source="V01", target="V09", level=1)
    g_nc = HigherCell(source="V17", target="V21", level=1)
    result_nc = f_nc.compose(g_nc)
    if result_nc is not None:
        violations.append(f"Composability: V01→V09 ∘ V17→V21 should be None but got {result_nc.label}")

    # Weak associativity: Ousia → Krisis → Orexis → Chronos
    f = HigherCell(source="V01", target="V09", level=1)
    g = HigherCell(source="V09", target="V17", level=1)
    h_cell = HigherCell(source="V17", target="V21", level=1)

    fg = f.compose(g)
    if fg is None:
        violations.append("Cross-tribe f∘g composability fails")
    else:
        left = fg.compose(h_cell)
        if left is None:
            violations.append("Cross-tribe (f∘g)∘h composability fails")
        else:
            gh = g.compose(h_cell)
            if gh is None:
                violations.append("Cross-tribe g∘h composability fails")
            else:
                right = f.compose(gh)
                if right is None:
                    violations.append("Cross-tribe f∘(g∘h) composability fails")
                elif left.source != right.source or left.target != right.target:
                    violations.append(
                        f"Weak associativity fails cross-tribe: "
                        f"({f.label}∘{g.label})∘{h_cell.label} "
                        f"endpoints ≠ {f.label}∘({g.label}∘{h_cell.label})"
                    )

    return violations


# =============================================================================
# Display
# =============================================================================


# PURPOSE: 1つの PoiesisSpace を人間可読な形で記述する
def describe_space(space: PoiesisSpace) -> str:
    """Human-readable description of a Poiesis space."""
    lines = [
        f"  {space.verb_id} {space.verb_name} ({space.verb_ja})",
        f"    座標: {space.coordinates}",
        f"    CCL: {space.ccl_cmd}",
        f"    族: {space.tribe}",
    ]
    return "\n".join(lines)


# PURPOSE: 全体のサマリーを記述する
def describe_summary() -> str:
    """Summary of the entire L3 structure."""
    stats = count_cells()
    lines = [
        "=== L3 弱2-圏構造 (v4.1) ===",
        "",
        f"0-cells (Poiesis): {stats['zero_cells']}",
        f"1-cells (pipelines): {stats['one_cells']}",
        f"族 (Tribes): {stats['tribes']}",
        "",
        "族一覧:",
    ]
    for tribe, verb_ids in _TRIBES.items():
        spaces = [s for s in get_all_spaces() if s.verb_id in verb_ids]
        names = ", ".join(f"{s.ccl_cmd}" for s in spaces)
        lines.append(f"  {tribe}: {names}")

    return "\n".join(lines)


# =============================================================================
# Backward Compatibility — Legacy aliases (DEPRECATED)
# =============================================================================

# Legacy alias: TwoCell → HigherCell
TwoCell = HigherCell

# Legacy mapping: old theorem codes → new Poiesis IDs.
# NOTE: Only O-series (O1-O4) maps by semantic identity.
# S/H/P/K/A series mapped by POSITIONAL ORDER within their tribe,
# NOT by semantic equivalence. Old S1=Metron ≠ new V05=Skepsis.
_LEGACY_NAME_MAP: Dict[str, str] = {
    # O-series → Ousia: semantic match (same names)
    "O1": "V01",  # Noēsis → Noēsis ✓
    "O2": "V02",  # Boulēsis → Boulēsis ✓
    "O3": "V03",  # Zētēsis → Zētēsis ✓
    "O4": "V04",  # Energeia → Energeia ✓
    # S-series → Methodos: POSITIONAL (S1≠V05 semantically)
    "S1": "V05",  "S2": "V06",  "S3": "V07",  "S4": "V08",
    # H-series → Krisis: POSITIONAL
    "H1": "V09",  "H2": "V10",  "H3": "V11",  "H4": "V12",
    # P-series → Diástasis: POSITIONAL
    "P1": "V13",  "P2": "V14",  "P3": "V15",  "P4": "V16",
    # K-series → Orexis: POSITIONAL
    "K1": "V17",  "K2": "V18",  "K3": "V19",  "K4": "V20",
    # A-series → Chronos: POSITIONAL
    "A1": "V21",  "A2": "V22",  "A3": "V23",  "A4": "V24",
}


def get_derivative_space(theorem: str) -> Optional[PoiesisSpace]:
    """DEPRECATED: Map old theorem codes to new Poiesis IDs.

    WARNING: Only O-series (O1-O4) maps semantically.
    All other series map by positional order within tribe.
    """
    if theorem in _LEGACY_NAME_MAP and not theorem.startswith("O"):
        warnings.warn(
            f"get_derivative_space('{theorem}'): non-O-series mapping is positional, "
            f"not semantic. {theorem} maps to {_LEGACY_NAME_MAP[theorem]} by position only. "
            f"Use get_poiesis_space() with v4.1 verb IDs instead.",
            DeprecationWarning,
            stacklevel=2,
        )
    new_id = _LEGACY_NAME_MAP.get(theorem, theorem)
    return get_poiesis_space(new_id)


def get_series_spaces(series: str) -> List[PoiesisSpace]:
    """DEPRECATED: Map old series names to tribes."""
    _SERIES_TO_TRIBE = {
        "Tel": "Ousia", "Met": "Methodos", "Kri": "Krisis",
        "Dia": "Diástasis", "Ore": "Orexis", "Chr": "Chronos",
    }
    tribe = _SERIES_TO_TRIBE.get(series, series)
    return get_tribe_spaces(tribe)


def count_two_cells() -> Dict[str, int]:
    """DEPRECATED: Legacy alias for count_cells. Includes both old and new keys."""
    stats = count_cells()
    stats["total"] = stats["zero_cells"] + stats["one_cells"]
    stats["identity"] = stats["zero_cells"]
    stats["non_identity"] = stats["one_cells"]
    return stats


def verify_all() -> Dict[str, List[str]]:
    """Verify composition laws and structure for all Poiesis.

    Actually runs verify_composition_laws() and reports per-verb.
    """
    global_violations = verify_composition_laws()
    result: Dict[str, List[str]] = {}
    for s in get_all_spaces():
        verb_violations = [
            v for v in global_violations
            if s.verb_id in v or s.ccl_cmd in v
        ]
        result[s.verb_id] = verb_violations
    return result


# =============================================================================
# CLI
# =============================================================================


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        verb = sys.argv[1]
        space = get_poiesis_space(verb)
        if space:
            print(describe_space(space))
        else:
            print(f"Unknown verb: {verb}")
            sys.exit(1)
    else:
        print(describe_summary())
        print()
        for space in get_all_spaces():
            print(describe_space(space))
            print()
