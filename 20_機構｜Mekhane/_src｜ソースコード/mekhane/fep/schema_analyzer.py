# PROOF: [L2/インフラ] <- mekhane/fep/schema_analyzer.py
"""
PROOF: [L1/定理] このファイルは存在しなければならない

A0 → 認知には戦略 (Schema) がある
   → S1, S3, S4 で尺度・基準・実践を分析
   → schema_analyzer が担う

Q.E.D.

---

S-series Methodos Analyzer — 戦略分析モジュール

Hegemonikón S-series (Methodos) 定理: S1 Metron, S3 Stathmos, S4 Praxis
FEP層での尺度・基準・実践の分析を担当。
(S2 Mekhanē は derivative_selector.py として既存)

Architecture:
- S1 Metron = 尺度・スケール (cont/disc/abst)
- S3 Stathmos = 基準・評価基準 (norm/empi/rela)
- S4 Praxis = 実践・価値実現 (prax/pois/temp)

References:
- /met, /sta, /pra ワークフロー
- FEP: 戦略 = 行動方策の選択
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum

# =============================================================================
# S1 Metron (尺度・スケール)
# =============================================================================


# PURPOSE: S1 Metron の派生モード
class MetronDerivative(Enum):
    """S1 Metron の派生モード"""

    CONTINUOUS = "cont"  # 連続量
    DISCRETE = "disc"  # 離散量
    ABSTRACT = "abst"  # 抽象度


# PURPOSE: スケールレベル
class ScaleLevel(Enum):
    """スケールレベル"""

    MICRO = "micro"  # 極小
    MESO = "meso"  # 中間
    MACRO = "macro"  # 広域


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: S1 Metron 評価結果
class MetronResult:
    """S1 Metron 評価結果

    Attributes:
        subject: 評価対象
        derivative: 派生モード
        scale: スケールレベル
        granularity: 粒度 (0.0 粗い - 1.0 細かい)
        recommendation: 推奨スケール
    """

    subject: str
    derivative: MetronDerivative
    scale: ScaleLevel
    granularity: float
    recommendation: str


# PURPOSE: S1 Metron: スケールを分析
def analyze_scale(
    subject: str,
    derivative: Optional[MetronDerivative] = None,
) -> MetronResult:
    """S1 Metron: スケールを分析

    Args:
        subject: 評価対象
        derivative: 派生モード

    Returns:
        MetronResult
    """
    subj_lower = subject.lower()

    # 派生自動推論
    if derivative is None:
        if any(w in subj_lower for w in ["連続", "流れ", "continuous", "flow"]):
            derivative = MetronDerivative.CONTINUOUS
        elif any(w in subj_lower for w in ["個数", "カウント", "discrete", "count"]):
            derivative = MetronDerivative.DISCRETE
        else:
            derivative = MetronDerivative.ABSTRACT

    # スケール推論
    if any(w in subj_lower for w in ["全体", "システム", "macro", "global"]):
        scale = ScaleLevel.MACRO
        granularity = 0.3
    elif any(w in subj_lower for w in ["部分", "モジュール", "meso", "module"]):
        scale = ScaleLevel.MESO
        granularity = 0.5
    else:
        scale = ScaleLevel.MICRO
        granularity = 0.8

    recommendation = f"{scale.value}スケールで{derivative.value}的に評価"

    return MetronResult(
        subject=subject,
        derivative=derivative,
        scale=scale,
        granularity=granularity,
        recommendation=recommendation,
    )


# =============================================================================
# S3 Stathmos (基準・評価基準)
# =============================================================================


# PURPOSE: S3 Stathmos の派生モード
class StathmosDerivative(Enum):
    """S3 Stathmos の派生モード"""

    NORMATIVE = "norm"  # 規範的基準
    EMPIRICAL = "empi"  # 経験的基準
    RELATIVE = "rela"  # 相対的基準


# PURPOSE: 基準の優先度
class CriterionPriority(Enum):
    """基準の優先度"""

    MUST = "must"  # 必須
    SHOULD = "should"  # 期待
    COULD = "could"  # 理想


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: S3 Stathmos 評価結果
class StathmosResult:
    """S3 Stathmos 評価結果

    Attributes:
        subject: 評価対象
        derivative: 派生モード
        criteria: 基準リスト (優先度付き)
        benchmark: ベンチマーク
    """

    subject: str
    derivative: StathmosDerivative
    criteria: Dict[CriterionPriority, List[str]]
    benchmark: str


# PURPOSE: S3 Stathmos: 評価基準を定義
def define_criteria(
    subject: str,
    must: Optional[List[str]] = None,
    should: Optional[List[str]] = None,
    could: Optional[List[str]] = None,
    derivative: Optional[StathmosDerivative] = None,
) -> StathmosResult:
    """S3 Stathmos: 評価基準を定義

    Args:
        subject: 評価対象
        must: 必須基準
        should: 期待基準
        could: 理想基準
        derivative: 派生モード

    Returns:
        StathmosResult
    """
    subj_lower = subject.lower()

    # 派生自動推論
    if derivative is None:
        if any(w in subj_lower for w in ["規則", "ルール", "rule", "standard"]):
            derivative = StathmosDerivative.NORMATIVE
        elif any(w in subj_lower for w in ["実験", "データ", "empirical", "test"]):
            derivative = StathmosDerivative.EMPIRICAL
        else:
            derivative = StathmosDerivative.RELATIVE

    criteria = {
        CriterionPriority.MUST: must or [],
        CriterionPriority.SHOULD: should or [],
        CriterionPriority.COULD: could or [],
    }

    # ベンチマーク生成
    total = sum(len(v) for v in criteria.values())
    benchmark = f"{total}基準 ({len(must or [])} must)"

    return StathmosResult(
        subject=subject,
        derivative=derivative,
        criteria=criteria,
        benchmark=benchmark,
    )


# =============================================================================
# S4 Praxis (実践・価値実現)
# =============================================================================


# PURPOSE: S4 Praxis の派生モード (Aristotle)
class PraxisDerivative(Enum):
    """S4 Praxis の派生モード (Aristotle)"""

    PRAXIS = "prax"  # 内在目的 (行為自体が目的)
    POIESIS = "pois"  # 外的産出 (成果物を作る)
    TEMPORAL = "temp"  # 時間構造 (いつ実行するか)


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: S4 Praxis 評価結果
class PraxisResult:
    """S4 Praxis 評価結果

    Attributes:
        action: 行動
        derivative: 派生モード
        value_type: 価値の種類
        realization_path: 実現経路
        intrinsic_value: 内在価値があるか
    """

    action: str
    derivative: PraxisDerivative
    value_type: str
    realization_path: List[str]
    intrinsic_value: bool


# PURPOSE: S4 Praxis: 実践を計画
def plan_praxis(
    action: str,
    derivative: Optional[PraxisDerivative] = None,
    steps: Optional[List[str]] = None,
) -> PraxisResult:
    """S4 Praxis: 実践を計画

    Args:
        action: 行動
        derivative: 派生モード
        steps: 実現ステップ

    Returns:
        PraxisResult
    """
    action_lower = action.lower()

    # 派生自動推論
    if derivative is None:
        if any(w in action_lower for w in ["学習", "成長", "learn", "practice"]):
            derivative = PraxisDerivative.PRAXIS
            intrinsic = True
        elif any(w in action_lower for w in ["作成", "構築", "build", "create"]):
            derivative = PraxisDerivative.POIESIS
            intrinsic = False
        else:
            derivative = PraxisDerivative.TEMPORAL
            intrinsic = False
    else:
        intrinsic = derivative == PraxisDerivative.PRAXIS

    # 価値タイプ
    value_type = {
        PraxisDerivative.PRAXIS: "内在的価値",
        PraxisDerivative.POIESIS: "外在的価値",
        PraxisDerivative.TEMPORAL: "時間的価値",
    }[derivative]

    return PraxisResult(
        action=action,
        derivative=derivative,
        value_type=value_type,
        realization_path=steps or [action],
        intrinsic_value=intrinsic,
    )


# =============================================================================
# Formatting
# =============================================================================


# PURPOSE: S1 Metron 結果をMarkdown形式でフォーマット
def format_metron_markdown(result: MetronResult) -> str:
    """S1 Metron 結果をMarkdown形式でフォーマット"""
    lines = [
        "┌─[S1 Metron スケール分析]────────────────────────────┐",
        f"│ 派生: {result.derivative.value}",
        f"│ 対象: {result.subject[:40]}",
        f"│ スケール: {result.scale.value}",
        f"│ 粒度: {result.granularity:.0%}",
        f"│ 推奨: {result.recommendation}",
        "└──────────────────────────────────────────────────┘",
    ]
    return "\n".join(lines)


# PURPOSE: S3 Stathmos 結果をMarkdown形式でフォーマット
def format_stathmos_markdown(result: StathmosResult) -> str:
    """S3 Stathmos 結果をMarkdown形式でフォーマット"""
    lines = [
        "┌─[S3 Stathmos 基準定義]──────────────────────────────┐",
        f"│ 派生: {result.derivative.value}",
        f"│ 対象: {result.subject[:40]}",
    ]
    for priority, items in result.criteria.items():
        if items:
            lines.append(f"│ {priority.value.upper()}: {', '.join(items[:3])}")
    lines.extend(
        [
            f"│ ベンチマーク: {result.benchmark}",
            "└──────────────────────────────────────────────────┘",
        ]
    )
    return "\n".join(lines)


# PURPOSE: S4 Praxis 結果をMarkdown形式でフォーマット
def format_praxis_markdown(result: PraxisResult) -> str:
    """S4 Praxis 結果をMarkdown形式でフォーマット"""
    intrinsic_emoji = "✨" if result.intrinsic_value else "📦"
    lines = [
        "┌─[S4 Praxis 実践計画]─────────────────────────────────┐",
        f"│ 派生: {result.derivative.value}",
        f"│ 行動: {result.action[:40]}",
        f"│ 価値: {intrinsic_emoji} {result.value_type}",
        f"│ 経路: {' → '.join(result.realization_path[:3])}",
        "└──────────────────────────────────────────────────┘",
    ]
    return "\n".join(lines)


# =============================================================================
# FEP Integration
# =============================================================================


# PURPOSE: FEP観察空間へのエンコード
def encode_schema_observation(
    metron: Optional[MetronResult] = None,
    stathmos: Optional[StathmosResult] = None,
    praxis: Optional[PraxisResult] = None,
) -> dict:
    """FEP観察空間へのエンコード"""
    context_clarity = 0.5
    urgency = 0.3
    confidence = 0.5

    # Metron: 粒度 → context_clarity
    if metron:
        context_clarity = metron.granularity

    # Stathmos: 基準数 → confidence
    if stathmos:
        total = sum(len(v) for v in stathmos.criteria.values())
        confidence = min(1.0, total * 0.15)

    # Praxis: 内在価値 → urgency (低urgency = 急がなくてよい)
    if praxis:
        urgency = 0.3 if praxis.intrinsic_value else 0.6

    return {
        "context_clarity": context_clarity,
        "urgency": urgency,
        "confidence": confidence,
    }
