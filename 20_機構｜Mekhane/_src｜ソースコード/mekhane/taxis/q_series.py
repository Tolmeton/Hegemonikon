from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/taxis/q_series.py
# PURPOSE: Q-series (循環規則) — K₆ 上の反対称テンソル場
"""
Q-series Module — K₆ 上の循環方向を定義する反対称テンソル場。

X-series (G_{ij}) が「結合の強さ」を定義するのに対し、
Q-series (Q_{ij}) は「循環の方向」を定義する。

K₆ の 15辺に (G_{ij}, Q_{ij}) の二重パラメータが載る:
  G = 対称 (平衡的結合強度)
  Q = 反対称 (非平衡的循環強度)

理論的根拠:
- circulation_taxis.md v1.2.0 — 15辺の定義・3群分類
- circulation_theorem.md — 循環幾何定理 (ω-不変性, Schur 分解)
- axiom_hierarchy.md §Basis — Helmholtz 分解 f = (Γ + Q)∇φ

導出チェーン:
  FEP → NESS → Helmholtz B = A + Q
    → K₆ の各辺に Q_{ij} (反対称成分) を割り当て
      → Schur 分解 → 3回転面 (ω₁, ω₂, ω₃)
"""


from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# 定数: 6修飾座標の名前とインデックス
# ---------------------------------------------------------------------------

# PURPOSE: K₆ の頂点ラベル (6修飾座標)
COORDINATES = ("Value", "Function", "Precision", "Scale", "Valence", "Temporality")

# PURPOSE: 座標名 → 行列インデックス
COORD_INDEX = {name: i for i, name in enumerate(COORDINATES)}

# PURPOSE: 一意な略称テーブル (衝突回避: Value≠Valence)
_COORD_ABBR: dict[str, str] = {
    "Value": "Val",
    "Function": "Fun",
    "Precision": "Pre",
    "Scale": "Sca",
    "Valence": "Vle",
    "Temporality": "Tem",
}
_ABBR_TO_FULL: dict[str, str] = {v: k for k, v in _COORD_ABBR.items()}


# ---------------------------------------------------------------------------
# QEdge — K₆ の 1辺
# ---------------------------------------------------------------------------

# PURPOSE: Q-series 辺の群分類
class QGroup(Enum):
    """Q辺の3群分類 (circulation_taxis.md)。

    群 I:  d2×d2 間 (3本) — Stoicheia が直接定義
    群 II: d2×d3 間 (9本) — 座標間の結合
    群 III: d3×d3 間 (3本) — 弱い結合、強い方向バイアス
    """
    GROUP_I = "d2×d2"
    GROUP_II = "d2×d3"
    GROUP_III = "d3×d3"


# PURPOSE: K₆ の1辺のデータ構造
@dataclass(frozen=True)
class QEdge:
    """Q-series の 1辺。K₆ グラフの反対称成分。

    Q_{ij} > 0: i→j 方向が優勢
    Q_{ij} < 0: j→i 方向が優勢
    Q_{ij} ≈ 0: 双方向均衡 (健全な状態)

    反対称性: Q_{ij} = -Q_{ji}
    """
    coord_i: str           # 始点座標名
    coord_j: str           # 終点座標名
    value: float           # Q_{ij} の値 (正=i→j優勢, 負=j→i優勢)
    group: QGroup          # 群分類
    edge_id: int           # Q1〜Q15
    description: str = ""  # 循環の認知的意味
    description_ja: str = ""  # 日本語説明

    @property
    def key(self) -> str:
        """辺キー: 例 'Val→Pre'"""
        return f"{_COORD_ABBR[self.coord_i]}→{_COORD_ABBR[self.coord_j]}"

    @property
    def magnitude(self) -> float:
        """循環の強度 (絶対値)"""
        return abs(self.value)

    @property
    def is_stagnant(self, threshold: float = 0.7) -> bool:
        """固着リスクがあるか"""
        return self.magnitude > threshold


# ---------------------------------------------------------------------------
# Anti-Timidity 対応テーブル
# ---------------------------------------------------------------------------

# PURPOSE: Anti-Timidity と Q辺の対応 (circulation_taxis.md §運用規則)
ANTI_TIMIDITY_MAP: dict[str, dict[str, str]] = {
    "T-1": {
        "edge_id": "Q15",
        "fixation": "Vl→Te",
        "description": "/bye 提案禁止: 否定感情→過去回避の固着",
    },
    "T-3": {
        "edge_id": "Q9",
        "fixation": "Fu→Te",
        "description": "先延ばし禁止: Exploit→過去固着",
    },
    "T-4": {
        "edge_id": "Q8",
        "fixation": "Vl→Fu (逆方向)",
        "description": "保守的選択禁止: 恐怖→Exploit固着",
    },
    "T-6": {
        "edge_id": "Q13",
        "fixation": "Sc→Vl",
        "description": "尻込み禁止: Macro→否定の情動固着",
    },
}


# ---------------------------------------------------------------------------
# CirculationDiagnosis — 診断結果
# ---------------------------------------------------------------------------

# PURPOSE: 循環診断の結果
@dataclass(frozen=True)
class CirculationDiagnosis:
    """特定の Q辺に対する循環診断結果。"""
    edge: QEdge
    dominant_direction: str        # "i→j" / "j→i" / "balanced"
    magnitude: float               # |Q_{ij}|
    stagnation_risk: bool          # |Q| > threshold か
    anti_timidity_ref: Optional[str] = None  # T-1, T-3 等


# ---------------------------------------------------------------------------
# 理論的 Q₀ 定数 (from_theory のデフォルト値)
# ---------------------------------------------------------------------------

# PURPOSE: circulation_taxis.md の定義 + Stoicheia Γ/Q から演繹した理論値
# 符号の決定根拠:
#   Stoicheia の随伴対:
#     S-I:  Γ=Value,     Q=Precision → Va→Pr が自然方向 (知覚→精度)
#     S-II: Γ=Function,  Q=Flow      → Fu が Flow の駆動源
#     S-III: Γ=Precision, Q=Value    → Pr→Va は S-I の逆方向
#
#   d2×d3 間: 理論的根拠の強さで ±0.5〜±0.8
#   d3×d3 間: 弱い結合 ±0.3 (AuDHD のドーパミン変動で振幅変動)
_THEORY_Q0: list[dict] = [
    # --- 群 I: d2×d2 間 (3本) ---
    {
        "id": 1, "i": "Value", "j": "Precision",
        "value": 0.8, "group": QGroup.GROUP_I,
        "desc": "Inner goals drive certainty production",
        "desc_ja": "内的目標が確信の生産を駆動",
    },
    {
        "id": 2, "i": "Value", "j": "Function",
        "value": 0.6, "group": QGroup.GROUP_I,
        "desc": "Purpose selects strategy",
        "desc_ja": "目的が探索/活用の戦略を選択",
    },
    {
        "id": 3, "i": "Function", "j": "Precision",
        "value": 0.7, "group": QGroup.GROUP_I,
        "desc": "Strategy determines certainty requirements",
        "desc_ja": "Explore は低精度容認、Exploit は高精度要求",
    },
    # --- 群 II: d2×d3 間 (9本) ---
    {
        "id": 4, "i": "Value", "j": "Scale",
        "value": 0.5, "group": QGroup.GROUP_II,
        "desc": "Internal goals set observation granularity",
        "desc_ja": "内的目標が観測粒度を設定",
    },
    {
        "id": 5, "i": "Value", "j": "Valence",
        "value": 0.6, "group": QGroup.GROUP_II,
        "desc": "Goal alignment generates positive valence",
        "desc_ja": "目標整合が肯定感を生成",
    },
    {
        "id": 6, "i": "Value", "j": "Temporality",
        "value": 0.5, "group": QGroup.GROUP_II,
        "desc": "Purpose sets temporal horizon",
        "desc_ja": "目的が時間的射程を設定",
    },
    {
        "id": 7, "i": "Function", "j": "Scale",
        "value": 0.5, "group": QGroup.GROUP_II,
        "desc": "Explore demands macro view, exploit demands micro",
        "desc_ja": "探索は巨視、活用は微視を要求",
    },
    {
        "id": 8, "i": "Function", "j": "Valence",
        "value": -0.5, "group": QGroup.GROUP_II,
        "desc": "Fear drives exploit fixation (Anti-Timidity T-4)",
        "desc_ja": "恐怖が Exploit 固着を駆動 (T-4)",
    },
    {
        "id": 9, "i": "Function", "j": "Temporality",
        "value": 0.6, "group": QGroup.GROUP_II,
        "desc": "Strategy consumes temporal resources",
        "desc_ja": "探索は未来志向、活用は過去参照",
    },
    {
        "id": 10, "i": "Precision", "j": "Scale",
        "value": 0.5, "group": QGroup.GROUP_II,
        "desc": "Certainty constrains observation scope",
        "desc_ja": "高確信→視野狭窄、低確信→広域探索",
    },
    {
        "id": 11, "i": "Precision", "j": "Valence",
        "value": 0.5, "group": QGroup.GROUP_II,
        "desc": "Certainty generates emotional state",
        "desc_ja": "高確信→安心(+)、低確信→不安(-)",
    },
    {
        "id": 12, "i": "Precision", "j": "Temporality",
        "value": 0.4, "group": QGroup.GROUP_II,
        "desc": "Certainty stabilizes temporal orientation",
        "desc_ja": "高確信→持続的行動、低確信→過去参照",
    },
    # --- 群 III: d3×d3 間 (3本) ---
    {
        "id": 13, "i": "Scale", "j": "Valence",
        "value": 0.3, "group": QGroup.GROUP_III,
        "desc": "Size perception drives emotional response (T-6 shirking)",
        "desc_ja": "Macro→圧倒感(-)、Micro→達成感(+) (T-6 尻込み)",
    },
    {
        "id": 14, "i": "Scale", "j": "Temporality",
        "value": 0.3, "group": QGroup.GROUP_III,
        "desc": "Spatial granularity drives temporal horizon",
        "desc_ja": "Macro→長期、Micro→短期",
    },
    {
        "id": 15, "i": "Valence", "j": "Temporality",
        "value": 0.3, "group": QGroup.GROUP_III,
        "desc": "Emotion drives temporal direction (rumination, Anti-Timidity T-1)",
        "desc_ja": "肯定→未来志向、否定→過去回顧 (反芻, T-1)",
    },
]
assert len(_THEORY_Q0) == 15, f"15辺の定義が必要、現在 {len(_THEORY_Q0)} 辺"


# ---------------------------------------------------------------------------
# QMatrix — 6×6 反対称行列
# ---------------------------------------------------------------------------

# PURPOSE: Q-series 全体を保持する行列クラス
@dataclass
class QMatrix:
    """6×6 反対称行列。K₆ の 15辺の Q 値を保持。

    反対称性: Q + Q^T = 0 (対角は 0)
    """
    edges: list[QEdge] = field(default_factory=list)
    _matrix: np.ndarray = field(default=None, repr=False)

    def __post_init__(self):
        """辺リストから行列を構築。"""
        if self._matrix is None:
            self._matrix = np.zeros((6, 6))
            for edge in self.edges:
                i = COORD_INDEX[edge.coord_i]
                j = COORD_INDEX[edge.coord_j]
                self._matrix[i, j] = edge.value
                self._matrix[j, i] = -edge.value  # 反対称

    @property
    def matrix(self) -> np.ndarray:
        """6×6 反対称行列を返す。"""
        return self._matrix.copy()

    @property
    def is_antisymmetric(self) -> bool:
        """反対称性の検証: Q + Q^T = 0。"""
        return np.allclose(self._matrix + self._matrix.T, 0)

    # --- Static Factory Methods ---

    @staticmethod
    def from_theory() -> QMatrix:
        """(a) 理論的構成: circulation_taxis.md の Q₀ を内蔵定数から構築。

        Stoicheia の Γ/Q 随伴対から符号を演繹的に決定。
        日常使用のデフォルト。
        """
        edges = []
        for spec in _THEORY_Q0:
            edge = QEdge(
                coord_i=spec["i"],
                coord_j=spec["j"],
                value=spec["value"],
                group=spec["group"],
                edge_id=spec["id"],
                description=spec["desc"],
                description_ja=spec["desc_ja"],
            )
            edges.append(edge)
        return QMatrix(edges=edges)

    @staticmethod
    def from_manual(edge_values: dict[str, float]) -> QMatrix:
        """(c) 手動設定: 15辺を直接指定。

        Args:
            edge_values: {"Va→Pr": 0.8, "Va→Fu": -0.5, ...}
                キーは "XX→YY" 形式 (座標名の先頭2文字)

        Returns:
            QMatrix
        """
        edges = []
        edge_id = 1
        for key, value in edge_values.items():
            parts = key.split("→")
            if len(parts) != 2:
                raise ValueError(f"辺キーは 'XXX→YYY' 形式: {key}")
            coord_i = _ABBR_TO_FULL.get(parts[0])
            coord_j = _ABBR_TO_FULL.get(parts[1])
            if coord_i is None or coord_j is None:
                raise ValueError(f"未知の座標略称: {key}")

            # 群分類を自動判定
            d_i = _get_d(coord_i)
            d_j = _get_d(coord_j)
            if d_i == 2 and d_j == 2:
                group = QGroup.GROUP_I
            elif d_i == 3 and d_j == 3:
                group = QGroup.GROUP_III
            else:
                group = QGroup.GROUP_II

            edges.append(QEdge(
                coord_i=coord_i,
                coord_j=coord_j,
                value=value,
                group=group,
                edge_id=edge_id,
            ))
            edge_id += 1

        return QMatrix(edges=edges)

    @staticmethod
    def from_counts(transition_counts: dict[str, dict[str, int]]) -> QMatrix:
        """(b) セッションデータ推定: WF 遷移頻度から反対称成分を抽出。

        Args:
            transition_counts: {coord_i: {coord_j: count}}
                例: {"Value": {"Precision": 15, "Function": 8}, ...}

        Returns:
            QMatrix (反対称成分のみ)
        """
        # 遷移行列を構築
        n = len(COORDINATES)
        T = np.zeros((n, n))
        for ci, targets in transition_counts.items():
            if ci not in COORD_INDEX:
                continue
            i = COORD_INDEX[ci]
            for cj, count in targets.items():
                if cj not in COORD_INDEX:
                    continue
                j = COORD_INDEX[cj]
                T[i, j] = count

        # 行正規化 → 遷移確率
        row_sums = T.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # ゼロ除算防止
        P = T / row_sums

        # 反対称成分を抽出: Q = (P - P^T) / 2
        Q = (P - P.T) / 2

        # QEdge リストを構築
        edges = []
        edge_id = 1
        for i in range(n):
            for j in range(i + 1, n):
                ci = COORDINATES[i]
                cj = COORDINATES[j]
                d_i = _get_d(ci)
                d_j = _get_d(cj)
                if d_i == 2 and d_j == 2:
                    group = QGroup.GROUP_I
                elif d_i == 3 and d_j == 3:
                    group = QGroup.GROUP_III
                else:
                    group = QGroup.GROUP_II

                edges.append(QEdge(
                    coord_i=ci,
                    coord_j=cj,
                    value=float(Q[i, j]),
                    group=group,
                    edge_id=edge_id,
                    description=f"Estimated from {int(T[i,j])}/{int(T[j,i])} transitions",
                    description_ja=f"遷移 {int(T[i,j])}/{int(T[j,i])} から推定",
                ))
                edge_id += 1

        return QMatrix(edges=edges)

    # --- 診断関数 ---

    def get_edge(self, key: str) -> Optional[QEdge]:
        """辺キーで QEdge を取得。

        Args:
            key: "Va→Pr" 等の形式

        Returns:
            QEdge or None
        """
        for edge in self.edges:
            if edge.key == key:
                return edge
        return None

    def get_edge_by_id(self, edge_id: int) -> Optional[QEdge]:
        """Q番号 (1-15) で QEdge を取得。"""
        for edge in self.edges:
            if edge.edge_id == edge_id:
                return edge
        return None

    def diagnose(self, key: str, threshold: float = 0.7) -> Optional[CirculationDiagnosis]:
        """特定辺の循環方向と固着リスクを診断。

        Args:
            key: "Va→Pr" 等
            threshold: 固着リスク閾値 (デフォルト 0.7)

        Returns:
            CirculationDiagnosis or None
        """
        edge = self.get_edge(key)
        if edge is None:
            return None

        magnitude = edge.magnitude
        if edge.value > 0.05:
            direction = f"{edge.coord_i}→{edge.coord_j}"
        elif edge.value < -0.05:
            direction = f"{edge.coord_j}→{edge.coord_i}"
        else:
            direction = "balanced"

        stagnation = magnitude > threshold

        # Anti-Timidity 対応を検索
        at_ref = None
        for t_key, t_info in ANTI_TIMIDITY_MAP.items():
            if t_info["edge_id"] == f"Q{edge.edge_id}":
                at_ref = t_key
                break

        return CirculationDiagnosis(
            edge=edge,
            dominant_direction=direction,
            magnitude=magnitude,
            stagnation_risk=stagnation,
            anti_timidity_ref=at_ref,
        )

    def diagnose_all(self, threshold: float = 0.7) -> list[CirculationDiagnosis]:
        """全15辺の循環診断。"""
        results = []
        for edge in self.edges:
            diag = self.diagnose(edge.key, threshold)
            if diag is not None:
                results.append(diag)
        return results

    def stagnation_risks(self, threshold: float = 0.7) -> list[QEdge]:
        """固着リスクのある辺を返す。"""
        return [e for e in self.edges if e.magnitude > threshold]

    def anti_timidity_map(self) -> dict[str, CirculationDiagnosis]:
        """Anti-Timidity T-1〜T-6 と Q辺の対応関係を返す。"""
        result = {}
        for t_key, t_info in ANTI_TIMIDITY_MAP.items():
            edge = self.get_edge_by_id(int(t_info["edge_id"][1:]))
            if edge is not None:
                diag = self.diagnose(edge.key)
                if diag is not None:
                    result[t_key] = diag
        return result

    # --- Schur 分解 ---

    def schur_decomposition(self) -> dict:
        """Schur 分解: 反対称行列 → 3回転面 (ω₁, ω₂, ω₃)。

        H1 条件 (ブロック間結合 ≲ 回転周波数の ~10%) 下でのみ
        3回転面と 3ブロック (s, π, ω) の対応が成立。

        Returns:
            dict with:
              - eigenvalues: 固有値 (純虚数ペア)
              - frequencies: [ω₁, ω₂, ω₃] (回転周波数)
              - rotation_planes: 回転面の情報
              - pfaffian: Pfaffian 値 (非零なら非退化)
        """
        from scipy.linalg import schur

        Q = self._matrix

        # Schur 分解
        T_schur, U = schur(Q, output="complex")

        # 固有値抽出 (反対称行列は純虚数固有値)
        eigenvalues = np.diag(T_schur)

        # 回転周波数 = 固有値の虚部の正のもの
        imag_parts = np.sort(np.abs(eigenvalues.imag))[::-1]
        # 3つの正の固有値 (6次元反対称行列 → 3組の ±iω)
        frequencies = []
        seen = set()
        for val in imag_parts:
            rounded = round(val, 10)
            if rounded > 0 and rounded not in seen:
                frequencies.append(rounded)
                seen.add(rounded)
            if len(frequencies) == 3:
                break

        # 退化チェック (0に近い周波数があるか)
        while len(frequencies) < 3:
            frequencies.append(0.0)

        # Pfaffian 計算 (6×6 反対称行列)
        pfaffian = _compute_pfaffian_6x6(Q)

        return {
            "eigenvalues": eigenvalues.tolist(),
            "frequencies": sorted(frequencies, reverse=True),
            "pfaffian": pfaffian,
            "is_nondegenerate": abs(pfaffian) > 1e-10,
            "schur_form": T_schur,
            "unitary": U,
        }

    def check_h1_condition(self, epsilon: float = 0.1) -> dict:
        """H1 条件のチェック: ブロック間結合 ≲ 回転周波数の ~10%。

        Args:
            epsilon: 許容閾値 (デフォルト 0.1 = 10%)

        Returns:
            dict with h1_satisfied, coupling_ratio, details
        """
        result = self.schur_decomposition()
        freqs = result["frequencies"]

        if len(freqs) < 3 or min(freqs) == 0:
            return {
                "h1_satisfied": False,
                "reason": "退化固有値 (ω=0) が存在",
                "frequencies": freqs,
            }

        # ブロック間結合の推定 (off-diagonal elements の norm)
        # 群 I, II, III 間の結合強度を評価
        group_edges = {QGroup.GROUP_I: [], QGroup.GROUP_II: [], QGroup.GROUP_III: []}
        for edge in self.edges:
            group_edges[edge.group].append(edge.value)

        # 群間の平均絶対値
        inter_group_coupling = 0.0
        for g, vals in group_edges.items():
            if vals:
                inter_group_coupling += np.mean(np.abs(vals))
        inter_group_coupling /= len(group_edges)

        min_freq = min(freqs)
        ratio = inter_group_coupling / min_freq if min_freq > 0 else float("inf")

        return {
            "h1_satisfied": ratio < epsilon,
            "coupling_ratio": ratio,
            "threshold": epsilon,
            "frequencies": freqs,
            "inter_group_coupling": inter_group_coupling,
        }

    # --- 表示 ---

    def format_table(self) -> str:
        """全15辺を Markdown テーブルで表示。"""
        lines = [
            "| Q# | 辺 | 群 | Q値 | 方向 | 説明 |",
            "|:---|:---|:---|:----|:-----|:-----|",
        ]
        for edge in sorted(self.edges, key=lambda e: e.edge_id):
            direction = "→" if edge.value > 0.05 else ("←" if edge.value < -0.05 else "↔")
            lines.append(
                f"| Q{edge.edge_id} | {edge.key} | {edge.group.value} "
                f"| {edge.value:+.2f} | {direction} | {edge.description_ja or edge.description} |"
            )
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"QMatrix(edges={len(self.edges)}, antisymmetric={self.is_antisymmetric})"


# ---------------------------------------------------------------------------
# Internal Utilities
# ---------------------------------------------------------------------------

# PURPOSE: 座標名から d 値を取得
def _get_d(coord: str) -> int:
    """座標の d 値 (構成距離) を返す。"""
    d_map = {
        "Value": 2, "Function": 2, "Precision": 2,
        "Scale": 3, "Valence": 3, "Temporality": 3,
    }
    return d_map.get(coord, -1)


# PURPOSE: 6×6 反対称行列の Pfaffian を計算
def _compute_pfaffian_6x6(Q: np.ndarray) -> float:
    """6×6 反対称行列の Pfaffian を計算する。

    Pf(Q) = ε_{i₁j₁i₂j₂i₃j₃} Q_{i₁j₁} Q_{i₂j₂} Q_{i₃j₃} / (2^3 × 3!)

    Pf² = det(Q) なので det(Q) ≥ 0 なら Pf = √det(Q)。
    """
    det_Q = np.linalg.det(Q)
    # 反対称行列の det は常に ≥ 0 (偶数次元)
    if det_Q < 0:
        det_Q = 0.0  # 数値誤差の処理
    return float(np.sqrt(abs(det_Q)))
