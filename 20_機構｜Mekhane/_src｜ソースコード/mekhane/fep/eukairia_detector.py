# PROOF: [L1/定理] <- mekhane/fep/eukairia_detector.py
"""
PROOF: [L1/定理] このファイルは存在しなければならない

A0 → 認知には好機 (Eukairia) がある
   → K1 で「今がチャンスか」を判定
   → eukairia_detector が担う

Q.E.D.

---

K1 Eukairia Detector — 好機判定モジュール

Hegemonikón K-series (Chronos) 定理: K1 Eukairia
FEP層での機会検出とタイミング評価を担当。

Architecture:
- K1 Eukairia = 「今がチャンスか」の判定
- O4 Energeia が本モジュールを参照して好機を確認

References:
- /euk ワークフロー (好機判定)
- FEP: 機会 = 期待自由エネルギーが低い状態への遷移可能性
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


# PURPOSE: 機会窓の状態
class OpportunityWindow(Enum):
    """機会窓の状態"""

    WIDE = "wide"  # 広い: 時間的/条件的余裕あり
    NARROW = "narrow"  # 狭い: 限られた窓
    CLOSING = "closing"  # 閉じかけ: 急いで判断必要


# PURPOSE: 機会のスケール
class OpportunityScale(Enum):
    """機会のスケール"""

    MICRO = "micro"  # 局所的機会 (短期・小規模)
    MACRO = "macro"  # 大局的機会 (長期・大規模)


# PURPOSE: 好機判定結果
class OpportunityDecision(Enum):
    """好機判定結果"""

    GO = "go"  # 好機 — 行動せよ
    WAIT = "wait"  # 待機 — 条件改善を待て
    PASS = "pass"  # 見送り — この機会は取らない


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: 好機判定結果
class EukairiaResult:
    """好機判定結果

    Attributes:
        action: 判断対象の行動
        window: 機会窓の状態
        scale: 機会のスケール
        decision: 判定結果 (Go/Wait/Pass)
        confidence: 判定確信度 (0.0-1.0)
        rationale: 判定理由
        expected_return: 期待リターン (0.0-1.0)
        expected_risk: 期待リスク (0.0-1.0)
        opportunity_cost: 見送った場合の機会損失 (0.0-1.0)
        readiness_score: 準備度 (0.0-1.0)
        recommendation: 推奨アクション
        factors: 判定に影響した要因
    """

    action: str
    window: OpportunityWindow
    scale: OpportunityScale
    decision: OpportunityDecision
    confidence: float
    rationale: str
    expected_return: float
    expected_risk: float
    opportunity_cost: float
    readiness_score: float
    recommendation: str
    factors: List[str] = field(default_factory=list)

    # PURPOSE: eukairia_detector の should act 処理を実行する
    @property
    # PURPOSE: 今行動すべきか
    def should_act(self) -> bool:
        """今行動すべきか"""
        return self.decision == OpportunityDecision.GO

    # PURPOSE: eukairia_detector の should wait 処理を実行する
    @property
    # PURPOSE: 待機すべきか
    def should_wait(self) -> bool:
        """待機すべきか"""
        return self.decision == OpportunityDecision.WAIT

    # PURPOSE: eukairia_detector の net value 処理を実行する
    @property
    # PURPOSE: 純価値 (リターン - リスク)
    def net_value(self) -> float:
        """純価値 (リターン - リスク)"""
        return self.expected_return - self.expected_risk


# =============================================================================
# 好機評価パラメータ
# =============================================================================
# PURPOSE: 機会評価のコンテキスト


# PURPOSE: [L2-auto] OpportunityContext のクラス定義
@dataclass
class OpportunityContext:
    """機会評価のコンテキスト

    Attributes:
        environment_ready: 環境が整っているか (0.0-1.0)
        resources_available: リソースが利用可能か (0.0-1.0)
        skills_prepared: スキル/知識が準備できているか (0.0-1.0)
        timing_favorable: タイミングが良いか (0.0-1.0)
        competition_high: 競争が激しいか (True で不利)
        deadline_pressure: 期限からの圧力 (0.0-1.0)
    """

    environment_ready: float = 0.5
    resources_available: float = 0.5
    skills_prepared: float = 0.5
    timing_favorable: float = 0.5
    competition_high: bool = False
# PURPOSE: 準備度を計算
    deadline_pressure: float = 0.0


# PURPOSE: [L2-auto] _calculate_readiness の関数定義
def _calculate_readiness(ctx: OpportunityContext) -> float:
    """準備度を計算"""
    base = (
        ctx.environment_ready * 0.3
        + ctx.resources_available * 0.3
        + ctx.skills_prepared * 0.25
        + ctx.timing_favorable * 0.15
    )
    # 競争が激しい場合は減点
    if ctx.competition_high:
        base *= 0.8
# PURPOSE: 機会窓を評価
    return min(1.0, max(0.0, base))


# PURPOSE: [L2-auto] _calculate_window の関数定義
def _calculate_window(ctx: OpportunityContext) -> OpportunityWindow:
    """機会窓を評価"""
    if ctx.deadline_pressure >= 0.8:
        return OpportunityWindow.CLOSING
    elif ctx.timing_favorable >= 0.7 and ctx.deadline_pressure < 0.5:
        return OpportunityWindow.WIDE
    else:
# PURPOSE: 期待リターンを計算
        return OpportunityWindow.NARROW


# PURPOSE: [L2-auto] _calculate_return の関数定義
def _calculate_return(
    readiness: float,
    ctx: OpportunityContext,
    action_value: float = 0.5,
) -> float:
    """期待リターンを計算"""
    # 準備度 × 環境 × 行動価値
# PURPOSE: 期待リスクを計算
    return readiness * ctx.environment_ready * action_value * 1.5


# PURPOSE: [L2-auto] _calculate_risk の関数定義
def _calculate_risk(
    readiness: float,
    ctx: OpportunityContext,
) -> float:
    """期待リスクを計算"""
    # 準備不足 → 高リスク
    unpreparedness = 1.0 - readiness
    # 期限プレッシャー → 高リスク
    pressure_risk = ctx.deadline_pressure * 0.3
    # 競争 → 中リスク
    competition_risk = 0.2 if ctx.competition_high else 0.0

# PURPOSE: 見送った場合の機会損失を計算
    return min(1.0, unpreparedness * 0.5 + pressure_risk + competition_risk)


# PURPOSE: [L2-auto] _calculate_opportunity_cost の関数定義
def _calculate_opportunity_cost(
    window: OpportunityWindow,
    action_value: float = 0.5,
) -> float:
    """見送った場合の機会損失を計算"""
    window_factor = {
        OpportunityWindow.WIDE: 0.3,  # 後でも再挑戦可能
        OpportunityWindow.NARROW: 0.6,  # 逃すと痛い
        OpportunityWindow.CLOSING: 0.9,  # ほぼ最後のチャンス
    }
# PURPOSE: 判定と理由を生成
    return window_factor[window] * action_value


# PURPOSE: [L2-auto] _make_decision の関数定義
def _make_decision(
    expected_return: float,
    expected_risk: float,
    readiness: float,
    window: OpportunityWindow,
) -> tuple[OpportunityDecision, str]:
    """判定と理由を生成"""
    net = expected_return - expected_risk

    # GO条件: 純価値が正で、準備度が十分
    if net > 0.1 and readiness >= 0.6:
        decision = OpportunityDecision.GO
        rationale = f"純価値 {net:.0%} で準備度 {readiness:.0%} — 好機です"
    # WAIT条件: 純価値はあるが準備不足
    elif net > 0 and readiness < 0.6:
        decision = OpportunityDecision.WAIT
        rationale = f"純価値はあるが準備度 {readiness:.0%} — 条件改善を待つべき"
    # WAIT条件: 窓が広く、リスクが高め
    elif window == OpportunityWindow.WIDE and expected_risk > expected_return:
        decision = OpportunityDecision.WAIT
        rationale = "機会窓が広いため、より良い条件を待てます"
    # PASS条件: 純価値がマイナス
    elif net < 0:
        decision = OpportunityDecision.PASS
        rationale = (
            f"リスク ({expected_risk:.0%}) がリターン ({expected_return:.0%}) を上回る"
        )
    # GO条件: 窓が閉じかけで、純価値がゼロ以上
    elif window == OpportunityWindow.CLOSING and net >= 0:
        decision = OpportunityDecision.GO
        rationale = "機会窓が閉じかけ — 今行動しなければ機会を逃す"
    else:
        decision = OpportunityDecision.WAIT
        rationale = "条件が不十分 — 待機推奨"

# PURPOSE: 推奨アクションを生成
    return decision, rationale


# PURPOSE: [L2-auto] _generate_recommendation の関数定義
def _generate_recommendation(
    decision: OpportunityDecision, window: OpportunityWindow
) -> str:
    """推奨アクションを生成"""
    if decision == OpportunityDecision.GO:
        if window == OpportunityWindow.CLOSING:
            return "🚀 今すぐ行動開始 (/ene)"
        else:
            return "✅ 行動を開始 (/ene)"
    elif decision == OpportunityDecision.WAIT:
        return "⏸️ 条件改善を待つ (準備を進める)"
    else:  # PASS
        return "⛔ この機会は見送り (次を探す)"


# =============================================================================
# Public API
# PURPOSE: 好機を判定
# =============================================================================


# PURPOSE: [L2-auto] detect_opportunity の関数定義
def detect_opportunity(
    action: str,
    context: Optional[OpportunityContext] = None,
    action_value: float = 0.5,
    scale: OpportunityScale = OpportunityScale.MICRO,
) -> EukairiaResult:
    """好機を判定

    K1 Eukairia の中核関数。O4 Energeia から呼ばれ、
    行動開始前に好機かどうかを確認する。

    Args:
        action: 判断対象の行動
        context: 機会評価コンテキスト (None でデフォルト値)
        action_value: 行動の潜在価値 (0.0-1.0)
        scale: 機会のスケール

    Returns:
        EukairiaResult

    Example:
        >>> from mekhane.fep.eukairia_detector import detect_opportunity, OpportunityContext
        >>> ctx = OpportunityContext(
        ...     environment_ready=0.8,
        ...     resources_available=0.9,
        ...     skills_prepared=0.7,
        ...     timing_favorable=0.8,
        ... )
        >>> result = detect_opportunity("新機能をリリース", ctx, action_value=0.7)
        >>> result.decision
        OpportunityDecision.GO
    """
    ctx = context or OpportunityContext()

    # Step 1: 準備度計算
    readiness = _calculate_readiness(ctx)

    # Step 2: 機会窓評価
    window = _calculate_window(ctx)

    # Step 3: リスク/リターン分析
    expected_return = _calculate_return(readiness, ctx, action_value)
    expected_risk = _calculate_risk(readiness, ctx)
    opportunity_cost = _calculate_opportunity_cost(window, action_value)

    # Step 4: 判定
    decision, rationale = _make_decision(
        expected_return, expected_risk, readiness, window
    )

    # 推奨生成
    recommendation = _generate_recommendation(decision, window)

    # 判定確信度 (純価値の絶対値に基づく)
    net = abs(expected_return - expected_risk)
    confidence = min(1.0, 0.5 + net)

    # 影響要因リスト
    factors = []
    if ctx.environment_ready >= 0.7:
        factors.append("✅ 環境が整っている")
    elif ctx.environment_ready < 0.4:
        factors.append("⚠️ 環境が不十分")
    if ctx.resources_available >= 0.7:
        factors.append("✅ リソースが利用可能")
    if ctx.skills_prepared >= 0.7:
        factors.append("✅ スキル/知識が準備済み")
    elif ctx.skills_prepared < 0.4:
        factors.append("⚠️ 準備不足")
    if ctx.competition_high:
        factors.append("⚠️ 競争が激しい")
    if ctx.deadline_pressure >= 0.7:
        factors.append("⏰ 期限プレッシャーあり")

    return EukairiaResult(
        action=action,
        window=window,
        scale=scale,
        decision=decision,
        confidence=confidence,
        rationale=rationale,
        expected_return=expected_return,
        expected_risk=expected_risk,
        opportunity_cost=opportunity_cost,
        readiness_score=readiness,
        recommendation=recommendation,
        factors=factors,
# PURPOSE: 結果をMarkdown形式でフォーマット
    )


# PURPOSE: eukairia markdown を整形する
def format_eukairia_markdown(result: EukairiaResult) -> str:
    """結果をMarkdown形式でフォーマット"""
    decision_emoji = {
        OpportunityDecision.GO: "🚀",
        OpportunityDecision.WAIT: "⏸️",
        OpportunityDecision.PASS: "⛔",
    }
    window_text = {
        OpportunityWindow.WIDE: "広い",
        OpportunityWindow.NARROW: "狭い",
        OpportunityWindow.CLOSING: "閉じかけ",
    }

    lines = [
        "┌─[K1 Eukairia 好機判定]────────────────────────────┐",
        f"│ 対象: {result.action[:40]}",
        f"│ 機会窓: {window_text[result.window]} / スケール: {result.scale.value}",
        f"│ 判定: {decision_emoji[result.decision]} {result.decision.value.upper()}",
        f"│ 確信度: {result.confidence:.0%}",
        "│",
        f"│ 期待リターン: {result.expected_return:.0%}",
        f"│ 期待リスク: {result.expected_risk:.0%}",
        f"│ 機会損失: {result.opportunity_cost:.0%}",
        f"│ 準備度: {result.readiness_score:.0%}",
        "│",
        f"│ 理由: {result.rationale}",
    ]

    if result.factors:
        lines.append("│")
        lines.append("│ 要因:")
        for factor in result.factors[:4]:
            lines.append(f"│   {factor}")

    lines.extend(
        [
            "│",
            f"│ 推奨: {result.recommendation}",
            "└──────────────────────────────────────────────────┘",
        ]
    )

    return "\n".join(lines)
# PURPOSE: FEP観察空間へのエンコード


# FEP Integration
# PURPOSE: [L2-auto] encode_eukairia_observation の関数定義
def encode_eukairia_observation(result: EukairiaResult) -> dict:
    """FEP観察空間へのエンコード

    Returns:
        dict with context_clarity, urgency, confidence
    """
    # readiness を context_clarity にマップ
    context_clarity = result.readiness_score

    # 機会窓を urgency にマップ
    urgency_map = {
        OpportunityWindow.WIDE: 0.3,
        OpportunityWindow.NARROW: 0.6,
        OpportunityWindow.CLOSING: 0.9,
    }
    urgency = urgency_map[result.window]

    # 判定を confidence にマップ
    confidence = result.confidence

    return {
        "context_clarity": context_clarity,
        "urgency": urgency,
        "confidence": confidence,
    }
