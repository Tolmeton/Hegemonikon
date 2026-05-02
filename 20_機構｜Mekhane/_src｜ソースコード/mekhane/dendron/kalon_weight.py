from __future__ import annotations
# PROOF: [L2/コア] <- mekhane/dendron/kalon_weight.py
# PURPOSE: Fisher 固有値 λ に基づく stiffness 重み付けで、check issue の修正優先順を決定する
"""
Kalon Weight — Stiffness ランキング (Layer 1)

FEP の Fisher 情報行列の固有分解に基づき、Dendron の check 結果に
stiffness 重みを付与する。stiff な違反ほど先に直すべき。

理論的根拠:
- axiom_hierarchy.md §C-2: d 値 = 1/λ (固有値の逆数) = sloppiness
  - d=0: λ → ∞ (最 stiff) — 物理法則そのもの
  - d=1: λ = 大 — 推論⊣行動の崩壊は即座に検出
  - d=2: λ = 中 — VFE/EFE の偏りは検出可能
  - d=3: λ = 小 (sloppy) — 偏りが見えにくい

- kalon.md §6: Kalon = Fix(G∘F)
  - G = Dendron check (存在誤差の検出)
  - F = 開発者の修正 (発散→新しいコード)
  - stiff な方向の誤差を先に解消 → Fix への最短経路
"""


from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .models import CheckResult, ProofStatus


# ─── 座標と d 値テーブル ──────────────────────────────

# PURPOSE: FEP 座標の列挙（axiom_hierarchy.md §C-2 から演繹）
class FEPCoordinate(Enum):
    """FEP の 7+1 座標。d 値は追加仮定の数。"""
    HELMHOLTZ = "Helmholtz"   # d=0, λ → ∞
    FLOW = "Flow"             # d=1, λ = 大
    VALUE = "Value"           # d=2, λ = 中
    FUNCTION = "Function"     # d=2, λ = 中
    PRECISION = "Precision"   # d=2, λ = 中
    TEMPORALITY = "Temporality"  # d=2, λ = 中
    SCALE = "Scale"           # d=3, λ = 小
    VALENCE = "Valence"       # d=3, λ = 小


# PURPOSE: 各座標の d 値と stiffness 重みの正規テーブル
# stiffness = 1 / (d + 1) — d=0 が最も stiff (1.0)、d=3 が最も sloppy (0.25)
D_VALUE_TABLE: dict[FEPCoordinate, int] = {
    FEPCoordinate.HELMHOLTZ: 0,
    FEPCoordinate.FLOW: 1,
    FEPCoordinate.VALUE: 2,
    FEPCoordinate.FUNCTION: 2,
    FEPCoordinate.PRECISION: 2,
    FEPCoordinate.TEMPORALITY: 2,
    FEPCoordinate.SCALE: 3,
    FEPCoordinate.VALENCE: 3,
}

# PURPOSE: d 値 → stiffness 重み (1/(d+1) で正規化)
STIFFNESS_TABLE: dict[FEPCoordinate, float] = {
    coord: 1.0 / (d + 1) for coord, d in D_VALUE_TABLE.items()
}


# ─── Dendron check_type → FEP 座標マッピング ──────────────────

# PURPOSE: Dendron の check 種別から FEP 座標への射影
# 理論的根拠は implementation_plan.md に記載
CHECK_TYPE_TO_COORDINATE: dict[str, FEPCoordinate] = {
    # PROOF レベル — 存在証明は体系の公理的基盤 (Helmholtz = d=0)
    "L1_missing": FEPCoordinate.HELMHOLTZ,    # PROOF 欠落 = 存在未証明 → 公理レベル
    "L1_invalid": FEPCoordinate.HELMHOLTZ,    # PROOF 不正 = 存在証明の破損 → 公理レベル
    "L1_orphan": FEPCoordinate.FLOW,          # 親参照なし → 接続崩壊
    # L2 PURPOSE
    "L2_missing": FEPCoordinate.FUNCTION,     # 関数の目的不明 → 機能の不明確
    "L2_weak": FEPCoordinate.FUNCTION,        # WHAT vs WHY → 機能の精度
    # L3 Variable
    "L3_type_missing": FEPCoordinate.PRECISION,  # 型ヒント欠落 → 精度不足
    "L3_short_name": FEPCoordinate.PRECISION,    # 短い変数名 → 精度不足
    # EPT Matrix
    "nf2_missing": FEPCoordinate.VALUE,       # NF2 構造欠落 → 内部/外部区分
    "nf3_weak": FEPCoordinate.FUNCTION,       # NF3 関数NF違反 → 機能直交性
    "bcnf_weak": FEPCoordinate.FLOW,          # BCNF 不可欠性違反 → 全体接続
    # MECE
    "me_violation": FEPCoordinate.VALENCE,    # 排他性違反 → 概念の+/-
    "ce_violation": FEPCoordinate.TEMPORALITY, # 網羅性違反 → 時間的完全性
    "bcnf_deletable": FEPCoordinate.FLOW,     # 削除可能 → 全体接続
    # R-axis
    "reason_missing": FEPCoordinate.TEMPORALITY,  # REASON 欠落 → 経緯(時間)の欠損
    "reason_nf3": FEPCoordinate.VALENCE,          # 親子重複 → 概念の重複
    "reason_bcnf": FEPCoordinate.VALENCE,         # トートロジー → 概念の自明性
}


# ─── 重み付き Issue ──────────────────────────────

# PURPOSE: stiffness 重み付きの issue を表現する
@dataclass
class WeightedIssue:
    """stiffness 重みを持つ Dendron issue。

    weight が大きいほど先に直すべき (= stiff な方向の誤差)。
    """
    check_type: str
    coordinate: FEPCoordinate
    d_value: int
    stiffness: float
    path: str
    detail: str
    severity: str = "warning"  # "error" / "warning" / "info"

    # PURPOSE: stiffness × severity による総合重みを返す
    @property
    def weight(self) -> float:
        """総合重み = stiffness × severity_multiplier"""
        multiplier = {"error": 3.0, "warning": 1.0, "info": 0.5}
        return self.stiffness * multiplier.get(self.severity, 1.0)


# ─── レイヤー別 issue 収集ヘルパー ──────────────────────────────

# PURPOSE: L1 (PROOF) レイヤーの issue を収集する
def _collect_l1_issues(result: CheckResult) -> List[WeightedIssue]:
    """PROOF 欠落・無効・孤立の issue を収集する。"""
    issues: List[WeightedIssue] = []
    for fp in result.file_proofs:
        if fp.status == ProofStatus.MISSING:
            issues.append(_make_issue("L1_missing", str(fp.path), "PROOF ヘッダー欠落", "error"))
        elif fp.status == ProofStatus.INVALID:
            issues.append(_make_issue("L1_invalid", str(fp.path), "PROOF ヘッダー不正", "error"))
        elif fp.status == ProofStatus.ORPHAN:
            issues.append(_make_issue("L1_orphan", str(fp.path), "親参照なし (ORPHAN)", "warning"))
    return issues


# PURPOSE: L2 (PURPOSE) レイヤーの issue を収集する
def _collect_l2_issues(result: CheckResult) -> List[WeightedIssue]:
    """PURPOSE 欠落・弱い issue を収集する。"""
    issues: List[WeightedIssue] = []
    for fp in result.function_proofs:
        if fp.status == ProofStatus.MISSING:
            issues.append(_make_issue(
                "L2_missing", str(fp.path),
                f"PURPOSE 欠落: {fp.name} (L{fp.line_number})", "warning"
            ))
        elif fp.status == ProofStatus.WEAK:
            issues.append(_make_issue(
                "L2_weak", str(fp.path),
                f"PURPOSE が WHAT: {fp.name} (L{fp.line_number})", "info"
            ))
    return issues


# PURPOSE: L3 (Variable) レイヤーの issue を収集する
def _collect_l3_issues(result: CheckResult) -> List[WeightedIssue]:
    """型ヒント欠落・短い変数名の issue を収集する。"""
    issues: List[WeightedIssue] = []
    for vp in result.variable_proofs:
        if vp.check_type == "short_name":
            issues.append(_make_issue(
                "L3_short_name", str(vp.path),
                f"短い変数名: {vp.name} (L{vp.line_number})", "info"
            ))
    if result.signatures_missing_hints > 0:
        issues.append(_make_issue(
            "L3_type_missing", "<aggregate>",
            f"型ヒント欠落: {result.signatures_missing_hints} 個", "warning"
        ))
    return issues


# PURPOSE: EPT (NF2/NF3/BCNF) レイヤーの issue を収集する
def _collect_ept_issues(result: CheckResult) -> List[WeightedIssue]:
    """NF2 構造欠落・NF3 違反・BCNF 違反の issue を収集する。"""
    issues: List[WeightedIssue] = []
    for sp in result.structure_proofs:
        if sp.status == ProofStatus.MISSING:
            issues.append(_make_issue("nf2_missing", str(sp.path), f"NF2 構造欠落: {sp.name}", "warning"))
    for fnp in result.function_nf_proofs:
        if fnp.status == ProofStatus.WEAK:
            issues.append(_make_issue("nf3_weak", str(fnp.path), f"NF3 違反: {fnp.name} ({fnp.check_type})", "warning"))
    for vp in result.verification_proofs:
        if vp.status in (ProofStatus.WEAK, ProofStatus.MISSING):
            issues.append(_make_issue("bcnf_weak", str(vp.path), f"BCNF 違反: {vp.name} ({vp.check_type})", "warning"))
    return issues


# PURPOSE: MECE レイヤーの issue を収集する
def _collect_mece_issues(result: CheckResult) -> List[WeightedIssue]:
    """ME/CE 違反と削除可能候補の issue を収集する。"""
    issues: List[WeightedIssue] = []
    for mi in result.mece_issues:
        if mi.issue_type.startswith("me_"):
            issues.append(_make_issue("me_violation", str(mi.parent_path), f"ME 違反: {mi.suggestion or mi.issue_type}", mi.severity))
        elif mi.issue_type.startswith("ce_"):
            issues.append(_make_issue("ce_violation", str(mi.parent_path), f"CE 違反: {mi.suggestion or mi.issue_type}", mi.severity))
        elif mi.issue_type == "bcnf_deletable":
            issues.append(_make_issue("bcnf_deletable", str(mi.parent_path), f"削除可能: {mi.suggestion or mi.issue_type}", mi.severity))
    return issues


# PURPOSE: R-axis (REASON) レイヤーの issue を収集する
def _collect_reason_issues(result: CheckResult) -> List[WeightedIssue]:
    """REASON 親子重複・トートロジーの issue を収集する。"""
    issues: List[WeightedIssue] = []
    if result.reason_nf3_issues > 0:
        issues.append(_make_issue("reason_nf3", "<aggregate>", f"REASON 親子重複: {result.reason_nf3_issues} 件", "info"))
    if result.reason_bcnf_issues > 0:
        issues.append(_make_issue("reason_bcnf", "<aggregate>", f"REASON トートロジー: {result.reason_bcnf_issues} 件", "info"))
    return issues


# ─── メイン関数 ──────────────────────────────

# PURPOSE: CheckResult から全 issue を抽出し、stiffness 重みでランキングする
def weight_issues(result: CheckResult) -> List[WeightedIssue]:
    """CheckResult の全 issue に stiffness 重みを付与し、降順でソートする。

    Args:
        result: Dendron checker.check() の結果

    Returns:
        WeightedIssue のリスト (weight 降順)
    """
    issues: List[WeightedIssue] = []
    issues.extend(_collect_l1_issues(result))
    issues.extend(_collect_l2_issues(result))
    issues.extend(_collect_l3_issues(result))
    issues.extend(_collect_ept_issues(result))
    issues.extend(_collect_mece_issues(result))
    issues.extend(_collect_reason_issues(result))
    issues.sort(key=lambda x: x.weight, reverse=True)
    return issues


# PURPOSE: CheckResult から Kalon スナップショット指標を計算する (Layer 2 への橋渡し)
@dataclass
class KalonSnapshot:
    """1回の check 結果の Kalon 指標スナップショット。

    Layer 2 (kalon_convergence.py) の入力。
    知覚の質 = 複合指標で収束を判定する。
    """
    coverage: float              # PROOF カバレッジ率
    ept_score: int               # EPT Matrix の OK 数
    ept_total: int               # EPT Matrix の合計数
    ept_ratio: float             # ept_score / ept_total (0-1)
    weighted_issue_count: int    # 重み付き issue の総数
    total_stiffness: float       # 全 issue の stiffness 合計 (低いほど良い)
    top_stiff_issues: List[str]  # Top-5 issue の概要

    # ─── quality_score 重み定数 ──────────────────────────────
    # 理論的根拠:
    #   coverage (PROOF 網羅率) と ept_ratio (EPT 合格率) は
    #   それぞれ「存在の完全性」と「正規化の品質」を測定する独立指標。
    #   stiffness は issue の深刻度の総和であり、上記2指標に含まれない
    #   残存リスクを補完する。3指標での重みは均等ではなく、
    #   存在証明 (coverage) と品質検証 (ept) を同等、stiffness を補助とする。
    #   sigmoid の分母 20.0 は典型的なプロジェクトの stiffness 上界 (~50) の
    #   中央付近で 0.5 となるよう設定。
    W_COVERAGE: float = 0.4
    W_EPT: float = 0.4
    W_STIFFNESS: float = 0.2
    STIFFNESS_SIGMOID_SCALE: float = 20.0

    # PURPOSE: 単一の正規化された品質スコアを計算する (0.0-1.0, 高いほど良い)
    @property
    def quality_score(self) -> float:
        """複合品質スコア = W_COVERAGE×coverage + W_EPT×ept_ratio + W_STIFFNESS×(1 - normalized_stiffness)

        知覚の質:
        - coverage: 構造的完全性 (PROOF の網羅率)
        - ept_ratio: 正規化品質 (EPT の合格率)
        - stiffness: 残存 issue の深刻度 (反転: 低いほど良い)
        """
        normalized_stiffness = 1.0 / (1.0 + self.total_stiffness / self.STIFFNESS_SIGMOID_SCALE)
        return (
            self.W_COVERAGE * (self.coverage / 100.0)
            + self.W_EPT * self.ept_ratio
            + self.W_STIFFNESS * normalized_stiffness
        )


# PURPOSE: CheckResult から KalonSnapshot を生成する
def make_snapshot(result: CheckResult, weighted_issues: Optional[List[WeightedIssue]] = None) -> KalonSnapshot:
    """CheckResult + WeightedIssue リストから KalonSnapshot を生成する。

    Args:
        result: Dendron check 結果
        weighted_issues: weight_issues() の結果。None なら内部で計算

    Returns:
        KalonSnapshot
    """
    if weighted_issues is None:
        weighted_issues = weight_issues(result)

    ept_score = result.structure_ok + result.function_nf_ok + result.verification_ok
    ept_total = (
        result.total_structure_checks
        + result.total_function_nf_checks
        + result.total_verification_checks
    )
    # 検証なし (ept_total=0) は「合格」ではなく「未知」= 0.0
    ept_ratio = ept_score / ept_total if ept_total > 0 else 0.0

    total_stiffness = sum(i.weight for i in weighted_issues)
    top_5 = [f"[{i.coordinate.value} d={i.d_value}] {i.detail}" for i in weighted_issues[:5]]

    return KalonSnapshot(
        coverage=result.coverage,
        ept_score=ept_score,
        ept_total=ept_total,
        ept_ratio=ept_ratio,
        weighted_issue_count=len(weighted_issues),
        total_stiffness=total_stiffness,
        top_stiff_issues=top_5,
    )


# ─── ヘルパー ──────────────────────────────

# PURPOSE: check_type から WeightedIssue を構築するヘルパー
def _make_issue(
    check_type: str, path: str, detail: str, severity: str = "warning"
) -> WeightedIssue:
    """check_type → FEPCoordinate → d値 → stiffness の変換を行う。"""
    coord = CHECK_TYPE_TO_COORDINATE.get(check_type, FEPCoordinate.SCALE)
    d = D_VALUE_TABLE[coord]
    stiffness = STIFFNESS_TABLE[coord]
    return WeightedIssue(
        check_type=check_type,
        coordinate=coord,
        d_value=d,
        stiffness=stiffness,
        path=path,
        detail=detail,
        severity=severity,
    )
