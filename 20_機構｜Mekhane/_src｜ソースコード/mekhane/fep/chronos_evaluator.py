# PROOF: [L1/定理] <- mekhane/fep/chronos_evaluator.py
"""
PROOF: [L1/定理] このファイルは存在しなければならない

A0 → 認知には時間的制約がある
   → K2 Chronos で「いつまでに」を評価
   → chronos_evaluator が担う

Q.E.D.

---

K2 Chronos Evaluator — 時間制約評価モジュール

Hegemonikón K-series (Chronos) 定理: K2 Chronos
FEP層での時間制約評価とデッドライン管理を担当。

Architecture:
- K2 Chronos = 「いつまでに」の評価
- O4 Energeia が本モジュールを参照して時間制約を確認

References:
- /chr ワークフロー (時間配置)
- FEP: 時間的期待 = 期待自由エネルギーの時間割引
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
from datetime import datetime, timedelta
import re


# PURPOSE: 時間スケール
class TimeScale(Enum):
    """時間スケール"""

    IMMEDIATE = "immediate"  # 即時 (分〜時間): ≤ 24h
    SHORT = "short"  # 短期 (日〜週): ≤ 7d
    MEDIUM = "medium"  # 中期 (週〜月): ≤ 30d
    LONG = "long"  # 長期 (月〜年): > 30d


# PURPOSE: 確信度
class CertaintyLevel(Enum):
    """確信度"""

    CERTAIN = "C"  # 確実な期限 (固定)
    UNCERTAIN = "U"  # 不確実な見積もり (可変)


# PURPOSE: 余裕度 (期限までの相対時間)
class SlackLevel(Enum):
    """余裕度 (期限までの相対時間)"""

    AMPLE = "ample"  # 十分: 2x 以上の時間
    ADEQUATE = "adequate"  # 適切: 1-2x の時間
    TIGHT = "tight"  # 逼迫: 0.5-1x の時間
    OVERDUE = "overdue"  # 超過: 0.5x 未満 or 期限超過


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: 時間評価結果
class ChronosResult:
    """時間評価結果

    Attributes:
        task: 評価対象タスク
        deadline: デッドライン (datetime or None)
        deadline_str: デッドライン文字列 (相対/絶対)
        time_scale: 時間スケール
        certainty: 確信度
        slack: 余裕度
        urgency: 緊急度 (0.0-1.0)
        estimated_hours: 見積もり時間
        remaining_hours: 残り時間
        recommendation: 推奨アクション
        critical_path: クリティカルパス (依存タスク)
    """

    task: str
    deadline: Optional[datetime]
    deadline_str: str
    time_scale: TimeScale
    certainty: CertaintyLevel
    slack: SlackLevel
    urgency: float
    estimated_hours: float
    remaining_hours: Optional[float]
    recommendation: str
    critical_path: List[str] = field(default_factory=list)

    # PURPOSE: chronos_evaluator の is overdue 処理を実行する
    @property
    # PURPOSE: 期限超過か
    def is_overdue(self) -> bool:
        """期限超過か"""
        return self.slack == SlackLevel.OVERDUE

    # PURPOSE: chronos_evaluator の needs acceleration 処理を実行する
    @property
    # PURPOSE: 加速が必要か
    def needs_acceleration(self) -> bool:
        """加速が必要か"""
        return self.slack in (SlackLevel.TIGHT, SlackLevel.OVERDUE)


# =============================================================================
# 時間軸マッピング (urgency 値)
# =============================================================================

URGENCY_MAP = {
    "today": 1.0,  # ≤ 24h
    "3days": 0.8,  # ≤ 72h
    "week": 0.6,  # ≤ 7d
    "3weeks": 0.4,  # ≤ 21d
    "2months": 0.2,  # ≤ 60d
}
# PURPOSE: 期限文字列をパース


# PURPOSE: [L2-auto] _parse_deadline の関数定義
def _parse_deadline(
    deadline_str: str,
) -> tuple[Optional[datetime], TimeScale, CertaintyLevel]:
    """期限文字列をパース

    対応形式:
    - "2026-01-30" (ISO日付)
    - "tomorrow" / "明日"
    - "3 days" / "3日"
    - "next week" / "来週"
    - "end of month" / "月末"

    Returns:
        (deadline datetime, time_scale, certainty)
    """
    now = datetime.now()
    deadline_str_lower = deadline_str.lower().strip()

    # ISO日付形式
    iso_match = re.match(r"(\d{4})-(\d{2})-(\d{2})", deadline_str)
    if iso_match:
        year, month, day = map(int, iso_match.groups())
        deadline = datetime(year, month, day, 23, 59, 59)
        remaining = (deadline - now).total_seconds() / 3600
        if remaining <= 24:
            scale = TimeScale.IMMEDIATE
        elif remaining <= 168:  # 7d
            scale = TimeScale.SHORT
        elif remaining <= 720:  # 30d
            scale = TimeScale.MEDIUM
        else:
            scale = TimeScale.LONG
        return deadline, scale, CertaintyLevel.CERTAIN

    # 相対表現 (Japanese)
    jp_patterns = [
        (
            r"今日|本日",
            timedelta(hours=24),
            TimeScale.IMMEDIATE,
            CertaintyLevel.CERTAIN,
        ),
        (
            r"明日",
            timedelta(days=1, hours=23, minutes=59),
            TimeScale.IMMEDIATE,
            CertaintyLevel.CERTAIN,
        ),
        (r"今週|今週中", timedelta(days=7), TimeScale.SHORT, CertaintyLevel.UNCERTAIN),
        (r"来週", timedelta(days=14), TimeScale.SHORT, CertaintyLevel.UNCERTAIN),
        (
            r"月末|今月中",
            timedelta(days=30),
            TimeScale.MEDIUM,
            CertaintyLevel.UNCERTAIN,
        ),
        (r"(\d+)日", None, TimeScale.SHORT, CertaintyLevel.UNCERTAIN),
        (r"(\d+)週間", None, TimeScale.MEDIUM, CertaintyLevel.UNCERTAIN),
        (r"(\d+)ヶ月|(\d+)か月", None, TimeScale.LONG, CertaintyLevel.UNCERTAIN),
    ]

    for pattern, delta, scale, certainty in jp_patterns:
        match = re.search(pattern, deadline_str)
        if match:
            if delta:
                deadline = now + delta
            else:
                # 数値抽出
                groups = [g for g in match.groups() if g]
                if groups:
                    num = int(groups[0])
                    if "日" in pattern:
                        delta = timedelta(days=num)
                    elif "週" in pattern:
                        delta = timedelta(weeks=num)
                    elif "月" in pattern:
                        delta = timedelta(days=num * 30)
                    deadline = now + delta
                else:
                    deadline = None
            return deadline, scale, certainty

    # 英語表現
    en_patterns = [
        (r"today", timedelta(hours=24), TimeScale.IMMEDIATE, CertaintyLevel.CERTAIN),
        (
            r"tomorrow",
            timedelta(days=1, hours=23, minutes=59),
            TimeScale.IMMEDIATE,
            CertaintyLevel.CERTAIN,
        ),
        (r"this week", timedelta(days=7), TimeScale.SHORT, CertaintyLevel.UNCERTAIN),
        (r"next week", timedelta(days=14), TimeScale.SHORT, CertaintyLevel.UNCERTAIN),
        (r"(\d+)\s*days?", None, TimeScale.SHORT, CertaintyLevel.UNCERTAIN),
        (r"(\d+)\s*weeks?", None, TimeScale.MEDIUM, CertaintyLevel.UNCERTAIN),
        (r"(\d+)\s*months?", None, TimeScale.LONG, CertaintyLevel.UNCERTAIN),
    ]

    for pattern, delta, scale, certainty in en_patterns:
        match = re.search(pattern, deadline_str_lower)
        if match:
            if delta:
                deadline = now + delta
            else:
                groups = [g for g in match.groups() if g]
                if groups:
                    num = int(groups[0])
                    if "day" in pattern:
                        delta = timedelta(days=num)
                    elif "week" in pattern:
                        delta = timedelta(weeks=num)
                    elif "month" in pattern:
                        delta = timedelta(days=num * 30)
                    deadline = now + delta
                else:
                    deadline = None
            return deadline, scale, certainty

    # パース不可
    return None, TimeScale.MEDIUM, CertaintyLevel.UNCERTAIN
# PURPOSE: 残り時間から緊急度を計算


# PURPOSE: [L2-auto] _calculate_urgency の関数定義
def _calculate_urgency(remaining_hours: Optional[float]) -> float:
    """残り時間から緊急度を計算

    Args:
        remaining_hours: 残り時間 (時間)

    Returns:
        urgency (0.0-1.0)
    """
    if remaining_hours is None:
        return 0.3  # 不明時はデフォルト

    if remaining_hours <= 0:
        return 1.0
    elif remaining_hours <= 24:  # ≤ 1 day
        return 1.0
    elif remaining_hours <= 72:  # ≤ 3 days
        return 0.8
    elif remaining_hours <= 168:  # ≤ 1 week
        return 0.6
    elif remaining_hours <= 504:  # ≤ 3 weeks
        return 0.4
    elif remaining_hours <= 1440:  # ≤ 2 months
        return 0.2
    else:
        return 0.1
# PURPOSE: 余裕度を計算


# PURPOSE: [L2-auto] _calculate_slack の関数定義
def _calculate_slack(
    remaining_hours: Optional[float],
    estimated_hours: float,
) -> SlackLevel:
    """余裕度を計算

    Args:
        remaining_hours: 残り時間
        estimated_hours: 見積もり時間

    Returns:
        SlackLevel
    """
    if remaining_hours is None:
        return SlackLevel.ADEQUATE  # 不明時はデフォルト

    if remaining_hours <= 0:
        return SlackLevel.OVERDUE

    ratio = remaining_hours / max(estimated_hours, 1)

    if ratio >= 2.0:
        return SlackLevel.AMPLE
    elif ratio >= 1.0:
        return SlackLevel.ADEQUATE
    elif ratio >= 0.5:
        return SlackLevel.TIGHT
    else:
        return SlackLevel.OVERDUE
# PURPOSE: 余裕度と時間スケールから推奨を生成


# PURPOSE: [L2-auto] _generate_recommendation の関数定義
def _generate_recommendation(slack: SlackLevel, time_scale: TimeScale) -> str:
    """余裕度と時間スケールから推奨を生成"""
    if slack == SlackLevel.AMPLE:
        return "通常ペースで進行"
    elif slack == SlackLevel.ADEQUATE:
        return "計画通り実行"
    elif slack == SlackLevel.TIGHT:
        if time_scale == TimeScale.IMMEDIATE:
            return "⚠️ 即時着手必須"
        else:
            return "⚠️ 加速が必要"
    else:  # OVERDUE
        return "🛑 期限交渉 or スコープ縮小を検討"


# =============================================================================
# Public API
# =============================================================================
# PURPOSE: 時間制約を評価


# PURPOSE: [L2-auto] evaluate_time の関数定義
def evaluate_time(
    task: str,
    deadline_str: str,
    estimated_hours: float = 4.0,
    critical_path: Optional[List[str]] = None,
) -> ChronosResult:
    """時間制約を評価

    K2 Chronos の中核関数。O4 Energeia から呼ばれ、
    実行前に時間的余裕を確認する。

    Args:
        task: タスク名
        deadline_str: 期限文字列 (ISO日付 or 相対表現)
        estimated_hours: 見積もり時間 (時間)
        critical_path: クリティカルパス (依存タスク)

    Returns:
        ChronosResult

    Example:
        >>> from mekhane.fep.chronos_evaluator import evaluate_time
        >>> result = evaluate_time(
        ...     task="K2 Chronos を実装",
        ...     deadline_str="明日",
        ...     estimated_hours=2.0,
        ... )
        >>> result.slack
        SlackLevel.TIGHT
    """
    # Step 1: 期限パース
    deadline, time_scale, certainty = _parse_deadline(deadline_str)

    # Step 2: 残り時間計算
    if deadline:
        remaining_hours = (deadline - datetime.now()).total_seconds() / 3600
        if remaining_hours < 0:
            remaining_hours = 0
    else:
        remaining_hours = None

    # Step 3: 緊急度計算
    urgency = _calculate_urgency(remaining_hours)

    # Step 4: 余裕度計算
    slack = _calculate_slack(remaining_hours, estimated_hours)

    # Step 5: 推奨生成
    recommendation = _generate_recommendation(slack, time_scale)

    return ChronosResult(
        task=task,
        deadline=deadline,
        deadline_str=deadline_str,
        time_scale=time_scale,
        certainty=certainty,
        slack=slack,
        urgency=urgency,
        estimated_hours=estimated_hours,
        remaining_hours=remaining_hours,
        recommendation=recommendation,
        critical_path=critical_path or [],
    )
# PURPOSE: 結果をMarkdown形式でフォーマット


# PURPOSE: [L2-auto] format_chronos_markdown の関数定義
def format_chronos_markdown(result: ChronosResult) -> str:
    """結果をMarkdown形式でフォーマット"""
    slack_emoji = {
        SlackLevel.AMPLE: "🟢",
        SlackLevel.ADEQUATE: "🟡",
        SlackLevel.TIGHT: "🟠",
        SlackLevel.OVERDUE: "🔴",
    }

    deadline_display = (
        result.deadline.strftime("%Y-%m-%d %H:%M")
        if result.deadline
        else result.deadline_str
    )
    remaining_display = (
        f"{result.remaining_hours:.1f}h" if result.remaining_hours else "不明"
    )

    lines = [
        "┌─[K2 Chronos 時間評価]────────────────────────────┐",
        f"│ 対象: {result.task[:40]}",
        f"│ 期限: {deadline_display}",
        f"│ 時間軸: {result.time_scale.value}",
        f"│ 確信度: {result.certainty.value}",
        f"│ 残り: {remaining_display} / 見積: {result.estimated_hours}h",
        f"│ 余裕度: {slack_emoji[result.slack]} {result.slack.value.upper()}",
        f"│ 緊急度: {result.urgency:.0%}",
        "│",
        f"│ 推奨: {result.recommendation}",
    ]

    if result.critical_path:
        lines.append("│")
        lines.append("│ クリティカルパス:")
        for dep in result.critical_path[:3]:
            lines.append(f"│   → {dep}")

    lines.append("└──────────────────────────────────────────────────┘")

    return "\n".join(lines)

# PURPOSE: FEP観察空間へのエンコード

# FEP Integration
# PURPOSE: [L2-auto] encode_chronos_observation の関数定義
def encode_chronos_observation(result: ChronosResult) -> dict:
    """FEP観察空間へのエンコード

    Returns:
        dict with context_clarity, urgency, confidence
    """
    # certainty を context_clarity にマップ
    context_clarity = 0.9 if result.certainty == CertaintyLevel.CERTAIN else 0.5

    # urgency はそのまま
    urgency = result.urgency

    # slack を confidence にマップ
    confidence_map = {
        SlackLevel.AMPLE: 0.9,
        SlackLevel.ADEQUATE: 0.7,
        SlackLevel.TIGHT: 0.4,
        SlackLevel.OVERDUE: 0.1,
    }
    confidence = confidence_map[result.slack]

    return {
        "context_clarity": context_clarity,
        "urgency": urgency,
        "confidence": confidence,
    }
