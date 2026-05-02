from __future__ import annotations
# PROOF: [L2/FEP] <- mekhane/fep/coordinates.py
# PURPOSE: 認知座標系の Single Source of Truth (SSoT)
"""
Coordinate Registry — 7 認知座標の正規定義

axiom_hierarchy.md v4.2 で定義された 7 座標の d 値・対立極・問いを
体系全体の共有オントロジーとして提供する。

全ての座標参照はこのモジュールを経由すること (SSoT 原則)。
他モジュール (basis.py, attractor.py, fisher_metric.py 等) は
ここからインポートする。

構成距離 (d-value):
    d=0: Basis (体系核外, FEP/NESS 定理) → basis.py で定義
    d=1: Flow (Basis + Markov Blanket 仮定)
    d=2: Value, Function, Precision (VFE/EFE 分解)
    d=3: Scale, Valence, Temporality (階層的生成モデル)
"""


from dataclasses import dataclass


# ---------------------------------------------------------------------------
# CoordinateSpec — 座標仕様
# ---------------------------------------------------------------------------

# PURPOSE: 各認知座標の構成距離 d と対立極を定義
@dataclass(frozen=True)
class CoordinateSpec:
    """認知座標の仕様 (axiom_hierarchy.md v4.2)"""
    name: str               # 座標名 (英語)
    name_ja: str             # 座標名 (日本語)
    d_value: int             # 構成距離 (v4.2: Basis=0, Flow=1, ...)
    question: str            # 対応する問い
    opposition: tuple[str, str]  # 対立極


# ---------------------------------------------------------------------------
# COORDINATE_SPECS — 7 座標の正規定義 (v4.2: +1 シフト済み)
# ---------------------------------------------------------------------------

# PURPOSE: 体系全体の共有オントロジー — 全ファイルがここを参照する
COORDINATE_SPECS: dict[str, CoordinateSpec] = {
    "Flow": CoordinateSpec(
        name="Flow", name_ja="流れ", d_value=1,
        question="Who",
        opposition=("I (推論)", "A (行動)"),
    ),
    "Value": CoordinateSpec(
        name="Value", name_ja="価値", d_value=2,
        question="Why",
        opposition=("E (認識)", "P (実用)"),
    ),
    "Function": CoordinateSpec(
        name="Function", name_ja="機能", d_value=2,
        question="How",
        opposition=("Explore", "Exploit"),
    ),
    "Precision": CoordinateSpec(
        name="Precision", name_ja="精度", d_value=2,
        question="How much",
        opposition=("C (確信)", "U (留保)"),
    ),
    "Scale": CoordinateSpec(
        name="Scale", name_ja="尺度", d_value=3,
        question="Where",
        opposition=("Mi (微視)", "Ma (巨視)"),
    ),
    "Valence": CoordinateSpec(
        name="Valence", name_ja="傾向", d_value=3,
        question="Which",
        opposition=("+", "-"),
    ),
    "Temporality": CoordinateSpec(
        name="Temporality", name_ja="時間性", d_value=3,
        question="When",
        opposition=("Past (過去)", "Future (未来)"),
    ),
}

# 6 修飾座標 = Flow を除外した座標 (Basis × 6 = 12 演算子を生成)
MODIFYING_COORDINATES: list[str] = [
    k for k, v in COORDINATE_SPECS.items() if k != "Flow"
]
assert len(MODIFYING_COORDINATES) == 6, (
    f"Expected 6 modifying coordinates, got {len(MODIFYING_COORDINATES)}"
)


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

# PURPOSE: 座標 → d 値を返す
def get_d_value(coordinate_name: str) -> int:
    """座標名から構成距離 d を返す (v4.2).

    "Basis" → 0, "Flow" → 1, "Value" → 2, etc.

    Raises:
        KeyError: 未知の座標名
    """
    if coordinate_name == "Basis":
        return 0
    spec = COORDINATE_SPECS[coordinate_name]
    return spec.d_value


# PURPOSE: d 値でグループ化した座標リストを返す
def coordinates_by_d() -> dict[int, list[str]]:
    """d 値でグループ化した座標リストを返す.

    Returns:
        {0: ["Basis"], 1: ["Flow"], 2: ["Value", "Function", "Precision"],
         3: ["Scale", "Valence", "Temporality"]}
    """
    groups: dict[int, list[str]] = {0: ["Basis"]}
    for name, spec in COORDINATE_SPECS.items():
        groups.setdefault(spec.d_value, []).append(name)
    return groups


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "CoordinateSpec",
    "COORDINATE_SPECS",
    "MODIFYING_COORDINATES",
    "get_d_value",
    "coordinates_by_d",
]
