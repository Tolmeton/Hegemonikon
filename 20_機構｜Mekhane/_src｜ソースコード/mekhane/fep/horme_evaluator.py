# PROOF: [L1/定理] <- mekhane/fep/horme_evaluator.py
"""
PROOF: [L1/定理] このファイルは存在しなければならない

A0 → 認知には衝動 (Hormē) がある
   → H1-H3 で前感情・確信・欲求を評価
   → horme_evaluator が担う

Q.E.D.

---

H-series Krisis Evaluator — 衝動評価モジュール

Hegemonikón H-series (Krisis) 定理: H1 Propatheia, H2 Pistis, H3 Orexis
FEP層での衝動・確信・欲求の評価を担当。
(H4 Doxa は anamnesis/vault.py として永続化層で分離済み)

Architecture:
- H1 Propatheia = 前感情・直感 (init/warn/draw)
- H2 Pistis = 確信度・信頼性 (high/med/low)
- H3 Orexis = 欲求傾向 (approach/avoid/neutral)

References:
- /pro, /pis, /ore ワークフロー
- FEP: 衝動 = 期待自由エネルギー勾配に沿った傾向
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

# =============================================================================
# H1 Propatheia (前感情・直感)
# =============================================================================


# PURPOSE: H1 Propatheia の派生モード
class PropatheiaDerivative(Enum):
    """H1 Propatheia の派生モード"""

    INIT = "init"  # 初期傾向（中立的）
    WARN = "warn"  # 警告傾向（注意喚起）
    DRAW = "draw"  # 吸引傾向（引き寄せ）


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: H1 Propatheia 評価結果
class PropatheiaResult:
    """H1 Propatheia 評価結果

    Attributes:
        stimulus: 刺激・対象
        derivative: 派生モード
        intensity: 強度 (0.0-1.0)
        valence: 情緒価 (-1.0 negative to 1.0 positive)
        description: 直感の言語化
    """

    stimulus: str
    derivative: PropatheiaDerivative
    intensity: float
    valence: float
    description: str

    # PURPOSE: horme_evaluator の is positive 処理を実行する
    @property
    # PURPOSE: 正の情緒価か
    def is_positive(self) -> bool:
        """正の情緒価か"""
        return self.valence > 0

    # PURPOSE: horme_evaluator の is significant 処理を実行する
    @property
    # PURPOSE: 有意な強度か
    def is_significant(self) -> bool:
        """有意な強度か"""
        return self.intensity >= 0.5
# PURPOSE: H1 Propatheia: 前感情を評価


# PURPOSE: [L2-auto] evaluate_propatheia の関数定義
def evaluate_propatheia(
    stimulus: str,
    initial_feeling: Optional[str] = None,
) -> PropatheiaResult:
    """H1 Propatheia: 前感情を評価

    Args:
        stimulus: 刺激・対象
        initial_feeling: 初期感覚の記述

    Returns:
        PropatheiaResult
    """
    # キーワードベースの派生・情緒価推論
    stimulus_lower = stimulus.lower()
    feeling_lower = (initial_feeling or "").lower()
    combined = stimulus_lower + " " + feeling_lower

    # 警告キーワード
    warn_keywords = [
        "危険",
        "リスク",
        "不安",
        "懸念",
        "danger",
        "risk",
        "concern",
        "worry",
    ]
    # 吸引キーワード
    draw_keywords = [
        "興味",
        "魅力",
        "可能性",
        "チャンス",
        "interest",
        "opportunity",
        "exciting",
    ]

    if any(w in combined for w in warn_keywords):
        derivative = PropatheiaDerivative.WARN
        valence = -0.3
        intensity = 0.7
    elif any(w in combined for w in draw_keywords):
        derivative = PropatheiaDerivative.DRAW
        valence = 0.5
        intensity = 0.6
    else:
        derivative = PropatheiaDerivative.INIT
        valence = 0.0
        intensity = 0.3

    description = initial_feeling or f"{stimulus} に対する初期反応"

    return PropatheiaResult(
        stimulus=stimulus,
        derivative=derivative,
        intensity=intensity,
        valence=valence,
        description=description,
    )


# =============================================================================
# H2 Pistis (確信度・信頼性)
# =============================================================================
# PURPOSE: H2 Pistis の派生モード


# PURPOSE: [L2-auto] PistisDerivative のクラス定義
class PistisDerivative(Enum):
    """H2 Pistis の派生モード"""

    HIGH = "high"  # 高確信度
    MEDIUM = "med"  # 中確信度
    LOW = "low"  # 低確信度

# PURPOSE: H2 Pistis 評価結果

# PURPOSE: [L2-auto] PistisResult のクラス定義
@dataclass
class PistisResult:
    """H2 Pistis 評価結果

    Attributes:
        belief: 信念・判断
        derivative: 派生モード
        confidence: 確信度 (0.0-1.0)
        evidence_count: 根拠の数
        counter_evidence_count: 反証の数
        justification: 確信の根拠
    """

    belief: str
    derivative: PistisDerivative
    confidence: float
    evidence_count: int
    counter_evidence_count: int
    justification: str

    # PURPOSE: horme_evaluator の net evidence 処理を実行する
    @property
    # PURPOSE: 正味の根拠数
    def net_evidence(self) -> int:
        """正味の根拠数"""
        return self.evidence_count - self.counter_evidence_count

    # PURPOSE: horme_evaluator の should trust 処理を実行する
    @property
    # PURPOSE: 信頼すべきか
    def should_trust(self) -> bool:
# PURPOSE: H2 Pistis: 確信度を評価
        """信頼すべきか"""
        return self.confidence >= 0.6 and self.derivative != PistisDerivative.LOW


# PURPOSE: evaluate pistis を計算する
def evaluate_pistis(
    belief: str,
    evidence: Optional[List[str]] = None,
    counter_evidence: Optional[List[str]] = None,
) -> PistisResult:
    """H2 Pistis: 確信度を評価

    Args:
        belief: 信念・判断
        evidence: 根拠リスト
        counter_evidence: 反証リスト

    Returns:
        PistisResult
    """
    ev = evidence or []
    cev = counter_evidence or []

    # 確信度計算
    ev_count = len(ev)
    cev_count = len(cev)

    if ev_count == 0 and cev_count == 0:
        confidence = 0.5
        derivative = PistisDerivative.MEDIUM
        justification = "根拠なし — 中立"
    elif ev_count > cev_count * 2:
        confidence = min(0.95, 0.6 + ev_count * 0.1)
        derivative = PistisDerivative.HIGH
        justification = f"{ev_count}件の根拠あり"
    elif cev_count > ev_count:
        confidence = max(0.1, 0.5 - cev_count * 0.1)
        derivative = PistisDerivative.LOW
        justification = f"反証 ({cev_count}件) が根拠 ({ev_count}件) を上回る"
    else:
        confidence = 0.5 + (ev_count - cev_count) * 0.05
        derivative = PistisDerivative.MEDIUM
        justification = f"根拠 {ev_count}件 vs 反証 {cev_count}件"

    return PistisResult(
        belief=belief,
        derivative=derivative,
        confidence=confidence,
        evidence_count=ev_count,
        counter_evidence_count=cev_count,
        justification=justification,
    )


# =============================================================================
# PURPOSE: H3 Orexis の派生モード
# H3 Orexis (欲求傾向)
# =============================================================================


# PURPOSE: [L2-auto] OrexisDerivative のクラス定義
class OrexisDerivative(Enum):
    """H3 Orexis の派生モード"""

    APPROACH = "approach"  # 接近傾向
    AVOID = "avoid"  # 回避傾向
# PURPOSE: H3 Orexis 評価結果
    NEUTRAL = "neutral"  # 中立傾向


# PURPOSE: の統一的インターフェースを実現する
@dataclass
class OrexisResult:
    """H3 Orexis 評価結果

    Attributes:
        target: 対象
        derivative: 派生モード
        desire_strength: 欲求強度 (0.0-1.0)
        aversion_strength: 回避強度 (0.0-1.0)
        net_tendency: 正味傾向 (-1.0 avoid to 1.0 approach)
        motivation: 動機の言語化
    """

    target: str
    derivative: OrexisDerivative
    desire_strength: float
    aversion_strength: float
    net_tendency: float
    motivation: str

    # PURPOSE: horme_evaluator の should pursue 処理を実行する
    @property
    # PURPOSE: 追求すべきか
# PURPOSE: H3 Orexis: 欲求傾向を評価
    def should_pursue(self) -> bool:
        """追求すべきか"""
        return self.net_tendency > 0.2


# PURPOSE: H3 Orexis: 欲求傾向を評価
def evaluate_orexis(
    target: str,
    benefits: Optional[List[str]] = None,
    costs: Optional[List[str]] = None,
) -> OrexisResult:
    """H3 Orexis: 欲求傾向を評価

    Args:
        target: 対象
        benefits: 利益・メリット
        costs: コスト・デメリット

    Returns:
        OrexisResult
    """
    ben = benefits or []
    cos = costs or []

    # 欲求強度 (利益ベース)
    desire = min(1.0, len(ben) * 0.2) if ben else 0.3

    # 回避強度 (コストベース)
    aversion = min(1.0, len(cos) * 0.2) if cos else 0.1

    # 正味傾向
    net = desire - aversion

    if net > 0.2:
        derivative = OrexisDerivative.APPROACH
        motivation = f"利益 ({len(ben)}件) がコスト ({len(cos)}件) を上回る"
    elif net < -0.2:
        derivative = OrexisDerivative.AVOID
        motivation = f"コスト ({len(cos)}件) が利益 ({len(ben)}件) を上回る"
    else:
        derivative = OrexisDerivative.NEUTRAL
        motivation = "利益とコストが均衡"

    return OrexisResult(
        target=target,
        derivative=derivative,
        desire_strength=desire,
        aversion_strength=aversion,
        net_tendency=net,
        motivation=motivation,
    )


# PURPOSE: H1 Propatheia 結果をMarkdown形式でフォーマット
# =============================================================================
# Formatting
# =============================================================================


# PURPOSE: H1 Propatheia 結果をMarkdown形式でフォーマット
def format_propatheia_markdown(result: PropatheiaResult) -> str:
    """H1 Propatheia 結果をMarkdown形式でフォーマット"""
    valence_emoji = (
        "🟢" if result.valence > 0 else ("🔴" if result.valence < 0 else "⚪")
    )
    lines = [
        "┌─[H1 Propatheia 前感情評価]─────────────────────────┐",
        f"│ 派生: {result.derivative.value}",
        f"│ 刺激: {result.stimulus[:40]}",
        f"│ 強度: {result.intensity:.0%}",
        f"│ 情緒価: {valence_emoji} {result.valence:+.2f}",
        f"│ 直感: {result.description}",
# PURPOSE: H2 Pistis 結果をMarkdown形式でフォーマット
        "└──────────────────────────────────────────────────┘",
    ]
    return "\n".join(lines)


# PURPOSE: H2 Pistis 結果をMarkdown形式でフォーマット
def format_pistis_markdown(result: PistisResult) -> str:
    """H2 Pistis 結果をMarkdown形式でフォーマット"""
    conf_emoji = (
        "🟢"
        if result.confidence >= 0.7
        else ("🟡" if result.confidence >= 0.4 else "🔴")
    )
    lines = [
        "┌─[H2 Pistis 確信度評価]──────────────────────────────┐",
        f"│ 派生: {result.derivative.value}",
        f"│ 信念: {result.belief[:40]}",
        f"│ 確信度: {conf_emoji} {result.confidence:.0%}",
        f"│ 根拠: {result.evidence_count} / 反証: {result.counter_evidence_count}",
        f"│ 評価: {result.justification}",
# PURPOSE: H3 Orexis 結果をMarkdown形式でフォーマット
        "└──────────────────────────────────────────────────┘",
    ]
    return "\n".join(lines)


# PURPOSE: H3 Orexis 結果をMarkdown形式でフォーマット
def format_orexis_markdown(result: OrexisResult) -> str:
    """H3 Orexis 結果をMarkdown形式でフォーマット"""
    tend_emoji = (
        "→"
        if result.net_tendency > 0.2
        else ("←" if result.net_tendency < -0.2 else "○")
    )
    lines = [
        "┌─[H3 Orexis 欲求傾向評価]────────────────────────────┐",
        f"│ 派生: {result.derivative.value}",
        f"│ 対象: {result.target[:40]}",
        f"│ 欲求: {result.desire_strength:.0%} / 回避: {result.aversion_strength:.0%}",
        f"│ 傾向: {tend_emoji} {result.net_tendency:+.2f}",
        f"│ 動機: {result.motivation}",
        "└──────────────────────────────────────────────────┘",
    ]
    return "\n".join(lines)


# PURPOSE: FEP観察空間へのエンコード
# =============================================================================
# FEP Integration
# =============================================================================


# PURPOSE: FEP観察空間へのエンコード
def encode_horme_observation(
    propatheia: Optional[PropatheiaResult] = None,
    pistis: Optional[PistisResult] = None,
    orexis: Optional[OrexisResult] = None,
) -> dict:
    """FEP観察空間へのエンコード

    H-series の衝動評価を FEP agent の観察形式に変換。

    Returns:
        dict with context_clarity, urgency, confidence
    """
    context_clarity = 0.5
    urgency = 0.3
    confidence = 0.5

    # Propatheia: 前感情 → urgency (警告は高urgency)
    if propatheia:
        if propatheia.derivative == PropatheiaDerivative.WARN:
            urgency = 0.8
        elif propatheia.derivative == PropatheiaDerivative.DRAW:
            urgency = 0.5
        else:
            urgency = 0.3

    # Pistis: 確信度 → confidence
    if pistis:
        confidence = pistis.confidence

    # Orexis: 欲求 → context_clarity (明確な傾向は高clarity)
    if orexis:
        context_clarity = 0.5 + abs(orexis.net_tendency) * 0.5

    return {
        "context_clarity": context_clarity,
        "urgency": urgency,
        "confidence": confidence,
    }
