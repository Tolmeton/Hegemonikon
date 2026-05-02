from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/taxis/wf_pattern_detector.py
# PURPOSE: Q3 固着パターン自動検知 — WF 使用パターンの偏り検出
"""
WF 使用パターン検出器 (WF Pattern Detector)

定理ログ (theorem_log_*.jsonl) からセッション横断の WF 使用偏りを検出する。
3 指標:
  1. E/E 比 (Explore/Exploit): 認知の探索↔活用バランス
  2. 族エントロピー: 6族の使用多様性
  3. 未活用定理: 認知の盲点

Q3 Phase (b): WF 使用パターン分析
- load_theorem_logs(): ログファイル読み込み
- analyze_ee_ratio(): Explore/Exploit 比
- analyze_family_entropy(): 族エントロピー
- detect_wf_pattern(): 統合関数 → WFPatternReport
- format_wf_report(): Markdown フォーマット

設計根拠:
- ero_q_series.md §Q3 (b)
- circulation_taxis.md §Anti-Timidity
"""


import json
import math
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

# PURPOSE: 定理ログディレクトリのデフォルトパス
_DEFAULT_LOG_DIR = Path(os.path.expanduser(
    "~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
    "/30_記憶｜Mneme/05_状態｜State/C_ログ｜Logs"
))


# ---------------------------------------------------------------------------
# 24定理マッピング
# ---------------------------------------------------------------------------

# PURPOSE: 24定理の族分類と Explore/Exploit 分類
# SOURCE: axiom_hierarchy.md, entity-map episteme

# 族名定数
TELOS = "Telos"
METHODOS = "Methodos"
KRISIS = "Krisis"
DIASTASIS = "Diastasis"
OREXIS = "Orexis"
CHRONOS = "Chronos"

# Explore/Exploit 定数
EXPLORE = "Explore"
EXPLOIT = "Exploit"

# 各定理の (族, E/E, 日本語名, 英語名, CCL動詞)
THEOREM_MAP: dict[str, tuple[str, str, str, str, str]] = {
    # Telos (目的) = Flow × Value
    "O1": (TELOS, EXPLORE, "認識", "Noēsis", "/noe"),
    "O2": (TELOS, EXPLOIT, "意志", "Boulēsis", "/bou"),
    "O3": (TELOS, EXPLORE, "探求", "Zētēsis", "/zet"),
    "O4": (TELOS, EXPLOIT, "実行", "Energeia", "/ene"),
    # Methodos (方法) = Flow × Function
    "H1": (METHODOS, EXPLORE, "発散", "Skepsis", "/ske"),
    "H2": (METHODOS, EXPLOIT, "収束", "Synagōgē", "/sag"),
    "H3": (METHODOS, EXPLORE, "実験", "Peira", "/pei"),
    "H4": (METHODOS, EXPLOIT, "適用", "Tekhnē", "/tek"),
    # Krisis (判断) = Flow × Precision
    "K1": (KRISIS, EXPLOIT, "確定", "Katalēpsis", "/kat"),
    "K2": (KRISIS, EXPLORE, "留保", "Epochē", "/epo"),
    "K3": (KRISIS, EXPLOIT, "決断", "Proairesis", "/pai"),
    "K4": (KRISIS, EXPLORE, "打診", "Dokimasia", "/dok"),
    # Diástasis (拡張) = Flow × Scale
    "A1": (DIASTASIS, EXPLORE, "分析", "Analysis", "/lys"),
    "A2": (DIASTASIS, EXPLOIT, "俯瞰", "Synopsis", "/ops"),
    "A3": (DIASTASIS, EXPLOIT, "精密操作", "Akribeia", "/akr"),
    "A4": (DIASTASIS, EXPLOIT, "全体展開", "Architektonikē", "/arc"),
    # Orexis (欲求) = Flow × Valence
    "D1": (OREXIS, EXPLOIT, "肯定", "Bebaiōsis", "/beb"),
    "D2": (OREXIS, EXPLORE, "批判", "Elenchos", "/ele"),
    "D3": (OREXIS, EXPLOIT, "推進", "Prokopē", "/kop"),
    "D4": (OREXIS, EXPLOIT, "是正", "Diorthōsis", "/dio"),
    # Chronos (時間) = Flow × Temporality
    "C1": (CHRONOS, EXPLORE, "想起", "Hypomnēsis", "/hyp"),
    "C2": (CHRONOS, EXPLOIT, "予見", "Promētheia", "/prm"),
    "C3": (CHRONOS, EXPLORE, "省察", "Anatheōrēsis", "/ath"),
    "C4": (CHRONOS, EXPLOIT, "先制", "Proparaskeuē", "/par"),
}

# 族の一覧 (順序固定)
FAMILIES = [TELOS, METHODOS, KRISIS, DIASTASIS, OREXIS, CHRONOS]

# Q辺 → 固着パターンの対応 (Phase (a) との連携用)
EE_FIXATION_MAP = {
    "exploit_heavy": {"q_edge": 9, "label": "Q9 Fu→Te", "anti_timidity": "T-3 先延ばし"},
    "explore_heavy": {"q_edge": 8, "label": "Q8 Vl→Fu 逆", "anti_timidity": "保守化逆方向"},
    "chronos_deficit": {"q_edge": 15, "label": "Q15 Vl→Te", "anti_timidity": "反芻/時間軸欠如"},
    "orexis_deficit": {"q_edge": 13, "label": "Q13 Sc→Vl", "anti_timidity": "T-6 感情評価回避"},
}


# ---------------------------------------------------------------------------
# データ構造
# ---------------------------------------------------------------------------

# PURPOSE: 定理ログの1レコード
@dataclass(frozen=True)
class WFUsageRecord:
    """定理ログの1件。"""
    theorem_id: str
    timestamp: float
    family: str
    ee_type: str
    date: str  # YYYY-MM-DD


# PURPOSE: 日次サマリ
@dataclass
class DailyStats:
    """1日分の E/E 統計。"""
    date: str
    explore: int = 0
    exploit: int = 0

    @property
    def total(self) -> int:
        return self.explore + self.exploit

    @property
    def ee_ratio(self) -> float:
        """Explore / (Explore + Exploit)。0-1。"""
        if self.total == 0:
            return 0.5  # データなし → 中立
        return self.explore / self.total


# PURPOSE: WF パターン検出の最終レポート
@dataclass
class WFPatternReport:
    """WF 使用パターン検出の統合結果。"""
    window_days: int
    total_records: int
    ee_ratio: float                          # Explore / Total (0-1)
    family_entropy: float                    # シャノンエントロピー (0-log6)
    max_entropy: float                       # log2(6) ≈ 2.585
    family_counts: dict[str, int]            # {族名: 件数}
    unused_theorems: list[str]               # 未使用定理 ID
    daily_trend: list[DailyStats]            # 日次推移
    alerts: list[str] = field(default_factory=list)
    top_theorem: Optional[str] = None        # 最頻定理
    top_count: int = 0

    @property
    def has_imbalance(self) -> bool:
        return len(self.alerts) > 0

    @property
    def entropy_ratio(self) -> float:
        """正規化エントロピー (0-1)。1=完全均等、0=全固着。"""
        if self.max_entropy == 0:
            return 0.0
        return self.family_entropy / self.max_entropy


# ---------------------------------------------------------------------------
# ログ読み込み
# ---------------------------------------------------------------------------

# PURPOSE: 定理ログファイルを読み込み
def load_theorem_logs(
    days: int = 7,
    log_dir: Optional[Path] = None,
) -> list[WFUsageRecord]:
    """定理ログを読み込み、WFUsageRecord のリストとして返す。

    Args:
        days: 何日分読むか (0=全件)
        log_dir: ログディレクトリ (省略時はデフォルト)

    Returns:
        WFUsageRecord のリスト (時系列順)
    """
    if log_dir is None:
        log_dir = _DEFAULT_LOG_DIR

    # 対象ファイルを収集 (2か所のディレクトリ)
    files = sorted(log_dir.glob("theorem_log_*.jsonl"))
    subdir = log_dir / "theorem"
    if subdir.exists():
        files += sorted(subdir.glob("theorem_log_*.jsonl"))

    # 日付フィルタ
    if days > 0:
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        files = [f for f in files if _extract_date(f.stem) >= cutoff_str]

    records: list[WFUsageRecord] = []
    for f in files:
        file_date = _extract_date(f.stem)
        try:
            with open(f) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        tid = d.get("theorem") or d.get("theorem_id", "")
                        ts = d.get("ts") or d.get("timestamp", 0)
                        if isinstance(ts, str):
                            # ISO format → epoch
                            try:
                                ts = datetime.fromisoformat(ts).timestamp()
                            except ValueError:
                                ts = 0
                        info = THEOREM_MAP.get(tid)
                        if info is None:
                            continue  # 24定理以外 (S1-S4, P1-P2 等) はスキップ
                        records.append(WFUsageRecord(
                            theorem_id=tid,
                            timestamp=float(ts),
                            family=info[0],
                            ee_type=info[1],
                            date=file_date if ts == 0 else datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
                        ))
                    except (json.JSONDecodeError, ValueError):
                        continue
        except OSError:
            continue

    # タイムスタンプ順ソート
    records.sort(key=lambda r: r.timestamp)
    return records


def _extract_date(stem: str) -> str:
    """ファイル名から日付部分を抽出。"""
    # theorem_log_2026-03-15 → 2026-03-15
    parts = stem.replace("theorem_log_", "")
    return parts


# ---------------------------------------------------------------------------
# 分析関数
# ---------------------------------------------------------------------------

# PURPOSE: Explore/Exploit 比を算出
def analyze_ee_ratio(records: list[WFUsageRecord]) -> float:
    """Explore / (Explore + Exploit) を算出。

    Returns:
        0-1 の float。0.5 = 均衡。
    """
    if not records:
        return 0.5

    explore = sum(1 for r in records if r.ee_type == EXPLORE)
    total = len(records)
    return explore / total if total > 0 else 0.5


# PURPOSE: 6族のシャノンエントロピーを算出
def analyze_family_entropy(records: list[WFUsageRecord]) -> float:
    """6族の使用比率のシャノンエントロピーを算出。

    H = -Σ p_i * log2(p_i)
    最大 = log2(6) ≈ 2.585 (完全均等)
    最小 = 0 (1族のみ使用)

    Returns:
        エントロピー値 (bits)
    """
    if not records:
        return 0.0

    total = len(records)
    counts: dict[str, int] = {f: 0 for f in FAMILIES}
    for r in records:
        if r.family in counts:
            counts[r.family] += 1

    entropy = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    return entropy


# PURPOSE: 日次 E/E 推移を算出
def compute_daily_trend(records: list[WFUsageRecord]) -> list[DailyStats]:
    """日次の Explore/Exploit 推移を算出。"""
    daily: dict[str, DailyStats] = {}
    for r in records:
        if r.date not in daily:
            daily[r.date] = DailyStats(date=r.date)
        if r.ee_type == EXPLORE:
            daily[r.date].explore += 1
        else:
            daily[r.date].exploit += 1

    return [daily[d] for d in sorted(daily.keys())]


# PURPOSE: 未使用定理を検出
def find_unused_theorems(records: list[WFUsageRecord]) -> list[str]:
    """ウィンドウ内で使用されていない定理を返す。"""
    used = {r.theorem_id for r in records}
    all_theorems = set(THEOREM_MAP.keys())
    unused = sorted(all_theorems - used)
    return unused


# ---------------------------------------------------------------------------
# 統合関数
# ---------------------------------------------------------------------------

# PURPOSE: WF パターン検出の統合関数
def detect_wf_pattern(
    days: int = 7,
    log_dir: Optional[Path] = None,
    ee_threshold_low: float = 0.25,
    ee_threshold_high: float = 0.75,
    entropy_threshold: float = 0.5,
    records: Optional[list[WFUsageRecord]] = None,
) -> WFPatternReport:
    """WF 使用パターンの偏りを検出する統合関数。

    Args:
        days: 分析対象日数
        log_dir: ログディレクトリ
        ee_threshold_low: Explore 比率がこれ未満なら Exploit 偏重
        ee_threshold_high: Explore 比率がこれ超なら Explore 偏重
        entropy_threshold: 正規化エントロピーがこれ未満なら族偏り
        records: 外部から渡すレコード (テスト用)

    Returns:
        WFPatternReport
    """
    if records is None:
        records = load_theorem_logs(days=days, log_dir=log_dir)

    if not records:
        return WFPatternReport(
            window_days=days,
            total_records=0,
            ee_ratio=0.5,
            family_entropy=0.0,
            max_entropy=math.log2(6),
            family_counts={f: 0 for f in FAMILIES},
            unused_theorems=sorted(THEOREM_MAP.keys()),
            daily_trend=[],
        )

    # 各分析
    ee_ratio = analyze_ee_ratio(records)
    family_entropy = analyze_family_entropy(records)
    max_entropy = math.log2(6)
    daily_trend = compute_daily_trend(records)
    unused = find_unused_theorems(records)

    # 族別カウント
    family_counts: dict[str, int] = {f: 0 for f in FAMILIES}
    theorem_counts: dict[str, int] = {}
    for r in records:
        family_counts[r.family] = family_counts.get(r.family, 0) + 1
        theorem_counts[r.theorem_id] = theorem_counts.get(r.theorem_id, 0) + 1

    # 最頻定理
    top_theorem = max(theorem_counts, key=theorem_counts.get) if theorem_counts else None
    top_count = theorem_counts.get(top_theorem, 0) if top_theorem else 0

    # アラート判定
    alerts: list[str] = []
    normalized_entropy = family_entropy / max_entropy if max_entropy > 0 else 0

    if ee_ratio < ee_threshold_low:
        alerts.append(f"⚠️ Exploit偏重: E/E比 {ee_ratio:.2f} (< {ee_threshold_low})")
    elif ee_ratio > ee_threshold_high:
        alerts.append(f"⚠️ Explore偏重: E/E比 {ee_ratio:.2f} (> {ee_threshold_high})")

    if normalized_entropy < entropy_threshold:
        alerts.append(f"⚠️ 族偏り: エントロピー {normalized_entropy:.2f} (< {entropy_threshold})")

    # 特定族の欠如チェック
    total = len(records)
    for fam in FAMILIES:
        count = family_counts.get(fam, 0)
        if total >= 10 and count / total < 0.02:
            alerts.append(f"⚠️ {fam} 欠如: {count}/{total} ({count/total*100:.1f}%)")

    # 日次の連続偏り (3日以上連続で E/E 0% or 100%)
    streak = 0
    streak_type = ""
    for ds in daily_trend:
        if ds.total >= 3:  # 最少3レコードの日
            if ds.ee_ratio == 0.0:
                if streak_type != "exploit":
                    streak = 0
                streak_type = "exploit"
                streak += 1
            elif ds.ee_ratio >= 0.95:
                if streak_type != "explore":
                    streak = 0
                streak_type = "explore"
                streak += 1
            else:
                streak = 0
                streak_type = ""
            if streak >= 3:
                alerts.append(f"⚠️ {streak}日連続 {streak_type} 固着")

    if len(unused) >= 12:
        alerts.append(f"⚠️ 定理カバレッジ低: {24-len(unused)}/24 使用")

    return WFPatternReport(
        window_days=days,
        total_records=len(records),
        ee_ratio=ee_ratio,
        family_entropy=family_entropy,
        max_entropy=max_entropy,
        family_counts=family_counts,
        unused_theorems=unused,
        daily_trend=daily_trend,
        alerts=alerts,
        top_theorem=top_theorem,
        top_count=top_count,
    )


# ---------------------------------------------------------------------------
# フォーマット
# ---------------------------------------------------------------------------

# PURPOSE: レポートを Markdown にフォーマット
def format_wf_report(report: WFPatternReport) -> str:
    """WFPatternReport を Markdown テーブルにフォーマット。"""
    lines = [
        "## 📊 WF 使用パターン分析レポート\n",
        f"- **分析期間**: 直近 {report.window_days} 日",
        f"- **総レコード**: {report.total_records}",
        f"- **偏り検出**: {'⚠️ あり' if report.has_imbalance else '✅ 均衡的'}",
    ]

    if report.top_theorem:
        info = THEOREM_MAP.get(report.top_theorem)
        name = info[2] if info else report.top_theorem
        lines.append(f"- **最頻定理**: {report.top_theorem} ({name}) — {report.top_count}回")

    # E/E 比
    lines.append(f"\n### Explore / Exploit 比率")
    explore_pct = report.ee_ratio * 100
    exploit_pct = (1 - report.ee_ratio) * 100
    bar_len = 30
    explore_bar = "█" * int(report.ee_ratio * bar_len)
    exploit_bar = "░" * (bar_len - len(explore_bar))
    lines.append(f"```")
    lines.append(f"Explore {explore_bar}{exploit_bar} Exploit")
    lines.append(f"  {explore_pct:.0f}%                        {exploit_pct:.0f}%")
    lines.append(f"```")

    # 族分布
    lines.append(f"\n### 族別使用頻度")
    lines.append(f"- **エントロピー**: {report.family_entropy:.3f} / {report.max_entropy:.3f} (正規化: {report.entropy_ratio:.2f})")
    lines.append("")
    lines.append("| 族 | 件数 | 割合 | バー |")
    lines.append("|:---|:-----|:-----|:-----|")

    total = max(1, report.total_records)
    max_count = max(report.family_counts.values()) if report.family_counts else 1
    for fam in FAMILIES:
        count = report.family_counts.get(fam, 0)
        pct = count / total * 100
        bar = "█" * max(0, int(count / max(1, max_count) * 15))
        lines.append(f"| {fam} | {count} | {pct:.1f}% | {bar} |")

    # 未使用定理
    if report.unused_theorems:
        lines.append(f"\n### 未使用定理 ({len(report.unused_theorems)}件)")
        for tid in report.unused_theorems:
            info = THEOREM_MAP.get(tid)
            if info:
                lines.append(f"- {tid} {info[4]} ({info[2]}, {info[0]})")

    # 日次推移
    if report.daily_trend:
        lines.append(f"\n### 日次 E/E 推移")
        lines.append("| 日付 | Explore | Exploit | E/E比 | バー |")
        lines.append("|:-----|:--------|:--------|:------|:-----|")
        for ds in report.daily_trend[-14:]:  # 直近14日
            if ds.total > 0:
                bar = "█" * int(ds.ee_ratio * 10) + "░" * (10 - int(ds.ee_ratio * 10))
                lines.append(f"| {ds.date} | {ds.explore} | {ds.exploit} | {ds.ee_ratio:.0%} | {bar} |")

    # アラート
    if report.alerts:
        lines.append(f"\n### ⚠️ アラート")
        for alert in report.alerts:
            lines.append(f"- {alert}")

    return "\n".join(lines)
