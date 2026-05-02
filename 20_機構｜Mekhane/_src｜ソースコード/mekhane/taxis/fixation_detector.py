from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/taxis/fixation_detector.py
# PURPOSE: Q3 固着パターン自動検知 — テキスト表層の停止ワードを Q辺にマッピング
"""
固着パターン検出器 (Fixation Detector)

Hóros の停止ワード (⛔) を Q-series の辺 (循環方向) に対応付け、
テキスト内での出現頻度から「どの座標間が固着しているか」を構造的に検出する。

Q3 Phase (a): テキスト表層検出
- scan_text(): テキスト走査 → FixationHit リスト
- score_fixation(): ヒット → パターン別スコア
- detect_fixation(): 統合関数 → FixationReport

設計根拠:
- circulation_taxis.md §運用規則: Anti-Timidity ↔ Q辺 対応
- horos-hub.md §BRD: B20 逃避衝動の停止ワード
- horos-N07.md: ⛔ 停止ワード定義
"""


import re
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# データ構造
# ---------------------------------------------------------------------------

# PURPOSE: 固着パターンの定義
@dataclass(frozen=True)
class FixationPattern:
    """1つの固着パターン定義。

    Q辺と停止ワード群を対応付ける。
    """
    pattern_id: str          # "shirk", "procrastinate" 等
    q_edge_id: int           # Q番号 (1-15)
    name: str                # パターン名 (日本語)
    name_en: str             # パターン名 (英語)
    keywords: tuple[str, ...] # 停止ワード群
    nomos_ref: str           # 関連 Nomos 参照
    description: str = ""    # 説明


# PURPOSE: テキスト走査のヒット (1件)
@dataclass(frozen=True)
class FixationHit:
    """停止ワードの出現1件。"""
    pattern_id: str          # どのパターンに該当するか
    keyword: str             # マッチした停止ワード
    position: int            # テキスト内の位置 (文字インデックス)
    context: str             # 前後の文脈 (±30文字)


# PURPOSE: 固着検出の最終レポート
@dataclass
class FixationReport:
    """固着検出の統合結果。"""
    total_hits: int                          # 総ヒット数
    pattern_scores: dict[str, float]         # パターン別スコア
    hits: list[FixationHit]                  # 全ヒットリスト
    alerts: list[str]                        # 閾値超過パターンの名前
    dominant_pattern: Optional[str] = None   # 最高スコアのパターン
    max_score: float = 0.0                   # 最高スコア
    text_length: int = 0                     # 入力テキスト長

    @property
    def has_fixation(self) -> bool:
        """固着が検出されたか"""
        return len(self.alerts) > 0

    @property
    def summary(self) -> str:
        """通知用サマリ文字列"""
        if not self.has_fixation:
            return "固着パターンは検出されませんでした。"
        parts = []
        for alert in self.alerts:
            score = self.pattern_scores.get(alert, 0.0)
            pattern = FIXATION_PATTERNS.get(alert)
            name = pattern.name if pattern else alert
            parts.append(f"• {name}: スコア {score:.2f}")
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# 固着パターン定義 (停止ワード → Q辺)
# ---------------------------------------------------------------------------

# PURPOSE: Hóros 停止ワードを Q-series 辺にマッピング
# SOURCE: horos-hub.md §BRD, horos-N07/N08, circulation_taxis.md §運用規則
FIXATION_PATTERNS: dict[str, FixationPattern] = {
    "shirk": FixationPattern(
        pattern_id="shirk",
        q_edge_id=13,
        name="尻込み (T-6)",
        name_en="Shirking",
        keywords=(
            "大きすぎる", "複雑", "難しい", "大変そう", "膨大",
            "大きなタスク", "量が多い", "網羅は困難",
        ),
        nomos_ref="N-8 θ8.5",
        description="Q13 Sc→Vl: Macro→否定情動の固着。タスク規模への尻込み。",
    ),
    "procrastinate": FixationPattern(
        pattern_id="procrastinate",
        q_edge_id=9,
        name="先延ばし (T-3)",
        name_en="Procrastination",
        keywords=(
            "次のセッション", "後で", "次回に", "後でやりましょう",
            "次セッション", "明日",
        ),
        nomos_ref="N-8 θ8.4",
        description="Q9 Fu→Te: Exploit→過去固着。今できることの先延ばし。",
    ),
    "ruminate": FixationPattern(
        pattern_id="ruminate",
        q_edge_id=15,
        name="反芻",
        name_en="Rumination",
        keywords=(
            "前にも失敗", "また同じ", "もう一回やれば",
            "前回も", "繰り返し",
        ),
        nomos_ref="N-6 θ6.2",
        description="Q15 Vl→Te: 否定感情→過去回避の固着。同じ失敗パターンの反復。",
    ),
    "conserve": FixationPattern(
        pattern_id="conserve",
        q_edge_id=8,
        name="保守化 (T-4)",
        name_en="Conservatism",
        keywords=(
            "安全な方", "リスクが", "保守的に", "無難",
            "安全策", "慎重に",
        ),
        nomos_ref="N-7 θ7.6",
        description="Q8 Vl→Fu: 恐怖→Exploit固着。安全な選択肢への偏向。",
    ),
    "skip_read": FixationPattern(
        pattern_id="skip_read",
        q_edge_id=1,
        name="読み飛ばし",
        name_en="Skip Reading",
        keywords=(
            "知っている", "覚えている", "たぶん", "確か",
            "前に見た", "既に取得済み", "全文読みは不要",
            "要約で十分",
        ),
        nomos_ref="N-1 θ1.1",
        description="Q1 Val→Pre: prior 過信。確認を怠る循環の固着。",
    ),
    "impossible": FixationPattern(
        pattern_id="impossible",
        q_edge_id=3,
        name="不可能断定",
        name_en="Impossibility Claim",
        keywords=(
            "できない", "不可能", "困難", "現実的でない",
            "無理", "手動では",
        ),
        nomos_ref="N-3 SFBT",
        description="Q3 Fun→Pre: 探索→確信の短絡。SFBT なしの不可能断定。",
    ),
}


# ---------------------------------------------------------------------------
# 検出関数
# ---------------------------------------------------------------------------

# PURPOSE: テキスト内の停止ワードを走査
def scan_text(text: str) -> list[FixationHit]:
    """テキストを走査し、停止ワードの出現箇所を返す。

    Args:
        text: 走査対象テキスト

    Returns:
        FixationHit のリスト (出現順)
    """
    if not text:
        return []

    hits: list[FixationHit] = []

    for pattern_id, pattern in FIXATION_PATTERNS.items():
        for keyword in pattern.keywords:
            # 全出現を検索
            start = 0
            while True:
                pos = text.find(keyword, start)
                if pos == -1:
                    break

                # 前後30文字の文脈を抽出
                ctx_start = max(0, pos - 30)
                ctx_end = min(len(text), pos + len(keyword) + 30)
                context = text[ctx_start:ctx_end]

                hits.append(FixationHit(
                    pattern_id=pattern_id,
                    keyword=keyword,
                    position=pos,
                    context=context,
                ))
                start = pos + len(keyword)

    # 出現位置順にソート
    hits.sort(key=lambda h: h.position)
    return hits


# PURPOSE: ヒットからパターン別スコアを算出
def score_fixation(hits: list[FixationHit], text_length: int = 1) -> dict[str, float]:
    """パターン別の固着スコアを算出。

    スコア = ヒット数 / max(1, テキスト長 / 200)
    テキスト200文字あたり1回の出現で 1.0。

    Args:
        hits: FixationHit のリスト
        text_length: 入力テキストの文字数

    Returns:
        {pattern_id: score} の辞書
    """
    # テキスト長に基づく正規化係数
    normalizer = max(1, text_length / 200)

    counts: dict[str, int] = {}
    for hit in hits:
        counts[hit.pattern_id] = counts.get(hit.pattern_id, 0) + 1

    scores: dict[str, float] = {}
    for pattern_id in FIXATION_PATTERNS:
        count = counts.get(pattern_id, 0)
        scores[pattern_id] = count / normalizer

    return scores


# PURPOSE: テキスト → 固着検出の統合関数
def detect_fixation(text: str, threshold: float = 0.3) -> FixationReport:
    """テキストから固着パターンを検出する統合関数。

    1. scan_text() で停止ワードを走査
    2. score_fixation() でパターン別スコアを算出
    3. 閾値超過パターンを alerts に収集
    4. FixationReport を返す

    Args:
        text: 走査対象テキスト
        threshold: 固着アラートの閾値 (デフォルト 0.3)

    Returns:
        FixationReport
    """
    if not text:
        return FixationReport(
            total_hits=0,
            pattern_scores={p: 0.0 for p in FIXATION_PATTERNS},
            hits=[],
            alerts=[],
            text_length=0,
        )

    hits = scan_text(text)
    scores = score_fixation(hits, text_length=len(text))

    # 閾値超過パターン
    alerts = [pid for pid, score in scores.items() if score >= threshold]

    # 最高スコアのパターン
    max_score = 0.0
    dominant = None
    for pid, score in scores.items():
        if score > max_score:
            max_score = score
            dominant = pid

    return FixationReport(
        total_hits=len(hits),
        pattern_scores=scores,
        hits=hits,
        alerts=alerts,
        dominant_pattern=dominant,
        max_score=max_score,
        text_length=len(text),
    )


# PURPOSE: フォーマット済み診断レポート (Markdown)
def format_report(report: FixationReport) -> str:
    """FixationReport を Markdown テーブルにフォーマット。"""
    lines = [
        "## 🔄 固着パターン検出レポート\n",
        f"- **テキスト長**: {report.text_length} 文字",
        f"- **総ヒット数**: {report.total_hits}",
        f"- **固着検出**: {'⚠️ あり' if report.has_fixation else '✅ なし'}",
    ]

    if report.dominant_pattern:
        pattern = FIXATION_PATTERNS.get(report.dominant_pattern)
        name = pattern.name if pattern else report.dominant_pattern
        lines.append(f"- **支配的パターン**: {name} (スコア {report.max_score:.2f})")

    lines.append("")
    lines.append("| パターン | Q辺 | スコア | 状態 |")
    lines.append("|:---------|:-----|:-------|:-----|")

    for pid, pattern in FIXATION_PATTERNS.items():
        score = report.pattern_scores.get(pid, 0.0)
        status = "⚠️ 固着" if pid in report.alerts else "✅ 正常"
        lines.append(f"| {pattern.name} | Q{pattern.q_edge_id} | {score:.2f} | {status} |")

    if report.hits:
        lines.append("")
        lines.append("### ヒット詳細")
        for hit in report.hits[:10]:  # 最大10件表示
            pattern = FIXATION_PATTERNS.get(hit.pattern_id)
            pname = pattern.name if pattern else hit.pattern_id
            lines.append(f"- **{pname}**: 「{hit.keyword}」 @ pos {hit.position}")

    return "\n".join(lines)
