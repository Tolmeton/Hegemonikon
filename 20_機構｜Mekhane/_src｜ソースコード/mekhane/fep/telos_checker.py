# PROOF: [L1/定理] <- mekhane/fep/telos_checker.py
"""
PROOF: [L1/定理] このファイルは存在しなければならない

A0 → 認知には目的 (Telos) がある
   → K3 で目的-行為整合を確認
   → telos_checker が担う

Q.E.D.

---

K3 Telos Checker — 目的-行為整合性評価モジュール

Hegemonikón K-series (Chronos) 定理: K3 Telos
FEP層での目的追跡と手段-目的入れ替わり検出を担当。

References:
- /tel ワークフロー (目的自問)
- O4 Energeia (本モジュールを参照して活動)
- FEP: 目的整合 = 期待自由エネルギー最小化の一形態
"""

from dataclasses import dataclass, field
from typing import List
from enum import Enum


# PURPOSE: 目的-行為の整合状態
class AlignmentStatus(Enum):
    """目的-行為の整合状態"""

    ALIGNED = "aligned"  # 整合している
    DRIFTING = "drifting"  # 軽微なズレあり
    MISALIGNED = "misaligned"  # 目的から逸脱
    INVERTED = "inverted"  # 手段と目的が入れ替わっている


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: Telos評価結果
class TelосResult:
    """Telos評価結果

    Attributes:
        status: 整合状態
        alignment_score: 整合度 (0.0-1.0)
        goal: 評価対象の目的
        action: 評価対象の行為
        rationale: 判定理由
        drift_indicators: ドリフト指標 (検出された場合)
        suggestions: 軌道修正提案
    """

    status: AlignmentStatus
    alignment_score: float
    goal: str
    action: str
    rationale: str
    drift_indicators: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    # PURPOSE: telos_checker の is aligned 処理を実行する
    @property
    # PURPOSE: 行為が目的に整合しているか
    def is_aligned(self) -> bool:
        """行為が目的に整合しているか"""
        return self.status in (AlignmentStatus.ALIGNED, AlignmentStatus.DRIFTING)

    # PURPOSE: telos_checker の needs correction 処理を実行する
    @property
    # PURPOSE: 軌道修正が必要か
    def needs_correction(self) -> bool:
        """軌道修正が必要か"""
        return self.status in (AlignmentStatus.MISALIGNED, AlignmentStatus.INVERTED)


# =============================================================================
# ドリフト検出パターン
# =============================================================================

DRIFT_PATTERNS = {
    "means_end_inversion": {
        "description": "手段が目的化している",
        "examples": [
            "ツールの改善自体が目的になっている",
            "プロセスの完璧さを追求しすぎている",
            "中間成果物にこだわりすぎている",
        ],
        "keywords": ["最適化", "完璧", "もっと良く", "改善", "リファクタ"],
    },
    "scope_creep": {
        "description": "スコープが拡大している",
        "examples": [
            "元の目的に関係ない機能を追加しようとしている",
            "「ついでに」という言葉が頻出",
        ],
        "keywords": ["ついでに", "せっかくだから", "将来的に", "いずれ"],
    },
    "perfectionism_trap": {
        "description": "完璧主義の罠",
        "examples": [
            "80%で十分なのに100%を目指している",
            "エッジケースにこだわりすぎている",
        ],
        "keywords": ["完璧", "全て", "全部", "100%", "網羅"],
    },
    "local_optimum": {
        "description": "局所最適に陥っている",
        "examples": [
            "細部の改善に注力して全体を見失っている",
            "短期的な成果を優先している",
        ],
        "keywords": ["とりあえず", "一旦", "今は", "後で"],
    },
}
# PURPOSE: 目的と行為からドリフトパターンを検出


# PURPOSE: [L2-auto] _detect_drift_patterns の関数定義
def _detect_drift_patterns(goal: str, action: str) -> List[str]:
    """目的と行為からドリフトパターンを検出

    Args:
        goal: 目的テキスト
        action: 行為テキスト

    Returns:
        検出されたドリフト指標のリスト
    """
    indicators = []
    combined = f"{goal} {action}".lower()

    for pattern_id, pattern in DRIFT_PATTERNS.items():
        for keyword in pattern["keywords"]:
            if keyword.lower() in combined:
                indicators.append(f"⚠️ {pattern['description']} ('{keyword}' 検出)")
                break  # 1パターン1検出

    return indicators
# PURPOSE: 整合度スコアを計算


# PURPOSE: [L2-auto] _calculate_alignment の関数定義
def _calculate_alignment(goal: str, action: str, drift_count: int) -> float:
    """整合度スコアを計算

    基本アルゴリズム:
    1. 基本スコア 0.8 からスタート
    2. ドリフト指標ごとに -0.15
    3. 目的と行為のキーワード重複で +0.1
    4. 最終スコアを 0.0-1.0 にクリップ
    """
    # 基本スコア
    score = 0.8

    # ドリフトによる減点
    score -= drift_count * 0.15

    # キーワード重複による加点 (簡易実装)
    goal_words = set(goal.lower().split())
    action_words = set(action.lower().split())
    overlap = goal_words & action_words
    if len(overlap) >= 2:
        score += 0.1

    # クリップ
    return max(0.0, min(1.0, score))
# PURPOSE: スコアとドリフト数から状態を決定


# PURPOSE: [L2-auto] _determine_status の関数定義
def _determine_status(score: float, drift_count: int) -> AlignmentStatus:
    """スコアとドリフト数から状態を決定"""
    if score >= 0.7 and drift_count == 0:
        return AlignmentStatus.ALIGNED
    elif score >= 0.5:
        return AlignmentStatus.DRIFTING
    elif drift_count >= 3:
        return AlignmentStatus.INVERTED
    else:
        return AlignmentStatus.MISALIGNED
# PURPOSE: 状態に応じた軌道修正提案を生成


# PURPOSE: [L2-auto] _generate_suggestions の関数定義
def _generate_suggestions(
    status: AlignmentStatus, drift_indicators: List[str]
) -> List[str]:
    """状態に応じた軌道修正提案を生成"""
    suggestions = []

    if status == AlignmentStatus.ALIGNED:
        suggestions.append("✅ このまま継続")
    elif status == AlignmentStatus.DRIFTING:
        suggestions.append("→ 元の目的を再確認 (/tel)")
        suggestions.append("→ 「なぜこれをやっているか」を自問")
    elif status == AlignmentStatus.MISALIGNED:
        suggestions.append("⚠️ 一度立ち止まり、目的を再定義 (/bou)")
        suggestions.append("⚠️ 現在の作業を中断して優先順位を見直す")
    elif status == AlignmentStatus.INVERTED:
        suggestions.append("🛑 手段と目的が入れ替わっています")
        suggestions.append("🛑 /noe で根本から問い直してください")
        suggestions.append("🛑 Creator との対話を推奨")

    return suggestions


# =============================================================================
# Public API
# =============================================================================
# PURPOSE: 目的と行為の整合性を評価


# PURPOSE: [L2-auto] check_alignment の関数定義
def check_alignment(goal: str, action: str) -> TelосResult:
    """目的と行為の整合性を評価

    K3 Telos の中核関数。O4 Energeia から呼ばれ、
    活動開始前に目的整合を確認する。

    Args:
        goal: 現在の目的・意図
        action: これから行おうとしている行為

    Returns:
        TelосResult: 評価結果

    Example:
        >>> from mekhane.fep.telos_checker import check_alignment
        >>> result = check_alignment(
        ...     goal="K3 Telos モジュールを実装する",
        ...     action="telos_checker.py を作成する"
        ... )
        >>> result.is_aligned
        True
        >>> result.alignment_score
        0.9
    """
    # Step 1: ドリフトパターン検出
    drift_indicators = _detect_drift_patterns(goal, action)

    # Step 2: 整合度スコア計算
    alignment_score = _calculate_alignment(goal, action, len(drift_indicators))

    # Step 3: 状態決定
    status = _determine_status(alignment_score, len(drift_indicators))

    # Step 4: 軌道修正提案生成
    suggestions = _generate_suggestions(status, drift_indicators)

    # Step 5: 判定理由生成
    if status == AlignmentStatus.ALIGNED:
        rationale = f"行為「{action[:30]}...」は目的に整合しています"
    elif status == AlignmentStatus.DRIFTING:
        rationale = f"軽微なドリフトを検出: {len(drift_indicators)}個の指標"
    else:
        rationale = f"目的から逸脱の可能性: {len(drift_indicators)}個のドリフト指標"

    return TelосResult(
        status=status,
        alignment_score=alignment_score,
        goal=goal,
        action=action,
        rationale=rationale,
        drift_indicators=drift_indicators,
        suggestions=suggestions,
    )
# PURPOSE: 結果をMarkdown形式でフォーマット


# PURPOSE: [L2-auto] format_telos_markdown の関数定義
def format_telos_markdown(result: TelосResult) -> str:
    """結果をMarkdown形式でフォーマット

    Args:
        result: TelосResult 評価結果

    Returns:
        Markdown文字列
    """
    status_emoji = {
        AlignmentStatus.ALIGNED: "✅",
        AlignmentStatus.DRIFTING: "⚠️",
        AlignmentStatus.MISALIGNED: "❌",
        AlignmentStatus.INVERTED: "🛑",
    }

    lines = [
        "┌─[K3 Telos 整合性評価]─────────────────────────┐",
        f"│ 状態: {status_emoji[result.status]} {result.status.value.upper()}",
        f"│ 整合度: {result.alignment_score:.0%}",
        f"│ 目的: {result.goal[:40]}...",
        f"│ 行為: {result.action[:40]}...",
        "│",
    ]

    if result.drift_indicators:
        lines.append("│ ドリフト指標:")
        for ind in result.drift_indicators[:3]:  # 最大3つ
            lines.append(f"│   {ind}")

    lines.append("│")
    lines.append("│ 提案:")
    for sug in result.suggestions[:3]:  # 最大3つ
        lines.append(f"│   {sug}")

    lines.append("└──────────────────────────────────────────────┘")

    return "\n".join(lines)

# PURPOSE: FEP観察空間へのエンコード

# For FEP integration: encode telos result into observation
# PURPOSE: [L2-auto] encode_telos_observation の関数定義
def encode_telos_observation(result: TelосResult) -> dict:
    """FEP観察空間へのエンコード

    TelосResult を FEP agent の観察形式に変換。
    state_spaces.py の encode_observation と連携。

    Returns:
        dict with context_clarity, urgency, confidence
    """
    # alignment_score を context_clarity にマップ
    context_clarity = result.alignment_score

    # ドリフト数を urgency にマップ (多いほど urgency 高)
    urgency = min(1.0, len(result.drift_indicators) * 0.3)

    # status を confidence にマップ
    confidence_map = {
        AlignmentStatus.ALIGNED: 0.9,
        AlignmentStatus.DRIFTING: 0.6,
        AlignmentStatus.MISALIGNED: 0.3,
        AlignmentStatus.INVERTED: 0.1,
    }
    confidence = confidence_map[result.status]

    return {
        "context_clarity": context_clarity,
        "urgency": urgency,
        "confidence": confidence,
    }
