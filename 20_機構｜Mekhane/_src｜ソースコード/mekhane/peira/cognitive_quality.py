#!/usr/bin/env python3
# PROOF: [L2/検証] <- A0→認知品質の定量測定が必要→n=1でもデータで語る
"""
Cognitive Quality Dashboard — 認知品質ダッシュボード

Handoff ファイルから 4 指標を集計し、HGK の実用性を定量的に評価する。
外部レビュー (B-) の「実用性の未測定」批判に対する応答として実装。

指標:
  1. セッション品質スコア (★ レーティング)
  2. 生産性 (コミット数/セッション)
  3. BC 遵守率 (違反密度)
  4. 定理活用率 (直接使用定理数/24)

Usage:
    python3 cognitive_quality.py              # ダッシュボード
    python3 cognitive_quality.py --days 30    # 過去30日
    python3 cognitive_quality.py --json       # JSON 出力
    python3 cognitive_quality.py --trend      # 月次トレンド
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# --- Configuration ---

from mekhane.paths import HANDOFF_DIR
from mekhane.peira.theorem_activity import THEOREM_WORKFLOWS
from mekhane.symploke.handoff_files import list_handoff_files

# ★ レーティングのパターン
QUALITY_PATTERN = re.compile(r'[★☆]{3,5}|(\d(?:\.\d)?)/5')

# ★ を数値に変換
STAR_MAP = {
    "★★★★★": 5.0, "★★★★☆": 4.0, "★★★☆☆": 3.0,
    "★★☆☆☆": 2.0, "★☆☆☆☆": 1.0,
    # 4文字の場合
    "★★★★": 4.5, "★★★☆": 3.5, "★★☆☆": 2.5, "★☆☆☆": 1.5,
    # 3文字の場合
    "★★★": 3.0, "★★☆": 2.5, "★☆☆": 1.5,
}

# コミット数パターン
COMMIT_PATTERN = re.compile(
    r'(?:コミット|commit)[:\s]*(\d+)\s*(?:本|件|commits?)?',
    re.IGNORECASE
)

# BC 違反パターン
VIOLATION_PATTERN = re.compile(
    r'(?:(?:BC|N)-\d+\s*違反|違反.*(?:BC|N)-\d+|violation)',
    re.IGNORECASE
)


# PURPOSE: [L2-auto] Handoff ファイル名から日付を抽出
def parse_date(path: Path) -> Optional[datetime]:
    """Handoff ファイル名から日付を抽出"""
    patterns = [
        r'handoff_(\d{4}-\d{2}-\d{2})',
        r'handoff_(\d{8})',
        r'handoff_.*?(\d{4}-\d{2}-\d{2})',
    ]
    for pat in patterns:
        m = re.search(pat, path.stem)
        if m:
            date_str = m.group(1)
            try:
                if '-' in date_str:
                    return datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    return datetime.strptime(date_str, "%Y%m%d")
            except ValueError:
                continue
    return None


# PURPOSE: [L2-auto] ★ 文字列を数値に変換
def stars_to_score(text: str) -> Optional[float]:
    """★ 文字列を数値スコアに変換"""
    # 直接マッチ
    if text in STAR_MAP:
        return STAR_MAP[text]
    # N/5 形式
    m = re.match(r'(\d(?:\.\d)?)/5', text)
    if m:
        return float(m.group(1))
    # ★ の数を数える
    star_count = text.count('★')
    if star_count > 0:
        return min(float(star_count), 5.0)
    return None


# PURPOSE: [L2-auto] Handoff から品質データを抽出
def extract_quality(content: str) -> Optional[float]:
    """Handoff から品質レーティングを抽出"""
    # 品質行を探す
    for line in content.split('\n'):
        if '品質' in line or 'Quality' in line or '★' in line:
            # ★★★★☆ 形式
            star_match = re.search(r'[★☆]{3,5}', line)
            if star_match:
                return stars_to_score(star_match.group())
            # N/5 形式
            score_match = re.search(r'(\d(?:\.\d)?)\s*/\s*5', line)
            if score_match:
                return float(score_match.group(1))
    return None


# PURPOSE: [L2-auto] Handoff からコミット数を抽出
def extract_commits(content: str) -> int:
    """Handoff からコミット数を抽出"""
    total = 0
    for m in COMMIT_PATTERN.finditer(content):
        total = max(total, int(m.group(1)))
    return total


# PURPOSE: [L2-auto] Handoff から BC 違反を検出
def extract_violations(content: str) -> int:
    """Handoff から BC 違反の記載数を抽出"""
    return len(VIOLATION_PATTERN.findall(content))


# PURPOSE: [L2-auto] 全 Handoff を走査して指標を集計
def scan_all(days: Optional[int] = None) -> dict:
    """全 Handoff を走査して品質指標を集計"""
    cutoff = None
    if days:
        cutoff = datetime.now() - timedelta(days=days)

    all_files = list_handoff_files(HANDOFF_DIR)
    results = {
        "total": 0,
        "quality_scores": [],
        "commits": [],
        "violations": [],
        "by_month": defaultdict(lambda: {
            "scores": [], "commits": [], "violations": [], "count": 0
        }),
        "theorems_direct": Counter(),
    }

    # WF パターン (theorem_activity.py と同じ)
    all_wfs = list(THEOREM_WORKFLOWS.keys())
    wf_pattern = re.compile(
        r'(?:^|(?<=\s))/(' +
        '|'.join(sorted(all_wfs, key=len, reverse=True)) +
        r')([+\-]?)(?=\s|$|[,.\)}\]|])',
        re.MULTILINE
    )

    for f in all_files:
        fdate = parse_date(f)
        if cutoff and fdate and fdate < cutoff:
            continue

        content = f.read_text(errors="replace")
        results["total"] += 1

        month_key = fdate.strftime("%Y-%m") if fdate else "unknown"
        month = results["by_month"][month_key]
        month["count"] += 1

        # Quality score
        score = extract_quality(content)
        if score is not None:
            results["quality_scores"].append(score)
            month["scores"].append(score)

        # Commits
        commits = extract_commits(content)
        if commits > 0:
            results["commits"].append(commits)
            month["commits"].append(commits)

        # Violations
        violations = extract_violations(content)
        results["violations"].append(violations)
        month["violations"].append(violations)

        # Direct theorem usage
        for match in wf_pattern.finditer(content):
            results["theorems_direct"][match.group(1)] += 1

    return results


# PURPOSE: [L2-auto] トレンド矢印を計算
def trend_arrow(values: list, window: int = 3) -> str:
    """直近 window 件の平均 vs 全体平均で↑↓→を決定"""
    if len(values) < window + 1:
        return "—"
    recent = sum(values[-window:]) / window
    overall = sum(values) / len(values)
    diff = recent - overall
    if diff > 0.2:
        return "↑"
    elif diff < -0.2:
        return "↓"
    return "→"


# PURPOSE: [L2-auto] ダッシュボードを生成
def generate_dashboard(
    days: Optional[int] = None,
    as_json: bool = False,
    show_trend: bool = False,
) -> str:
    """認知品質ダッシュボードを生成"""
    data = scan_all(days)
    period = f"過去{days}日" if days else "全期間"

    # 指標計算
    scores = data["quality_scores"]
    avg_quality = sum(scores) / len(scores) if scores else 0.0
    star_display = "★" * int(avg_quality) + ("☆" if avg_quality % 1 >= 0.5 else "")
    if not star_display:
        star_display = "N/A"

    commits = data["commits"]
    avg_commits = sum(commits) / len(commits) if commits else 0.0

    violations = data["violations"]
    total_violations = sum(violations)
    sessions_with_violations = sum(1 for v in violations if v > 0)
    compliance_rate = (
        (1 - sessions_with_violations / data["total"]) * 100
        if data["total"] > 0 else 0
    )

    direct_used = sum(1 for c in data["theorems_direct"].values() if c > 0)
    coverage = direct_used / 24 * 100

    if as_json:
        return json.dumps({
            "period": period,
            "total_sessions": data["total"],
            "quality": {
                "average": round(avg_quality, 2),
                "count": len(scores),
                "trend": trend_arrow(scores),
            },
            "productivity": {
                "avg_commits": round(avg_commits, 1),
                "total_commits": sum(commits),
                "trend": trend_arrow(commits),
            },
            "compliance": {
                "rate": round(compliance_rate, 1),
                "total_violations": total_violations,
                "sessions_with_violations": sessions_with_violations,
            },
            "theorem_coverage": {
                "direct_used": direct_used,
                "total": 24,
                "rate": round(coverage, 1),
            },
        }, ensure_ascii=False, indent=2)

    # --- Dashboard ---
    lines = []
    lines.append("╔══════════════════════════════════════════╗")
    lines.append("║  Cognitive Quality Dashboard             ║")
    lines.append(f"║  {datetime.now().strftime('%Y-%m-%d %H:%M')}  {period:>16}  ║")
    lines.append("╠══════════════════════════════════════════╣")
    lines.append(
        f"║  📊 Session Quality:  {star_display:<6} "
        f"({avg_quality:.1f}/5, n={len(scores)})"
    )
    lines.append(
        f"║  ⚡ Productivity:     "
        f"{avg_commits:.1f} commits/session "
        f"(total: {sum(commits)})"
    )
    lines.append(
        f"║  🛡️ BC Compliance:    "
        f"{compliance_rate:.0f}% "
        f"({total_violations} violations in "
        f"{sessions_with_violations}/{data['total']} sessions)"
    )
    lines.append(
        f"║  🧭 Theorem Coverage: "
        f"{coverage:.0f}% "
        f"({direct_used}/24 directly used)"
    )

    # Trend
    q_trend = trend_arrow(scores)
    p_trend = trend_arrow(commits)
    lines.append(
        f"║  📈 Trend:            "
        f"Quality {q_trend}  "
        f"Productivity {p_trend}"
    )
    lines.append("╚══════════════════════════════════════════╝")

    # Monthly trend (optional)
    if show_trend:
        lines.append("")
        lines.append("## 月次トレンド")
        lines.append("")
        lines.append(
            "| 月 | Sessions | Quality | Commits/S | Violations | Coverage |"
        )
        lines.append(
            "|:---|:---------|:--------|:----------|:-----------|:---------|"
        )
        for month_key in sorted(data["by_month"].keys()):
            m = data["by_month"][month_key]
            m_scores = m["scores"]
            m_commits = m["commits"]
            m_violations = m["violations"]
            avg_s = (
                f"{sum(m_scores) / len(m_scores):.1f}"
                if m_scores else "—"
            )
            avg_c = (
                f"{sum(m_commits) / len(m_commits):.1f}"
                if m_commits else "—"
            )
            total_v = sum(m_violations)
            lines.append(
                f"| {month_key} | {m['count']} | "
                f"{avg_s} | {avg_c} | "
                f"{total_v} | — |"
            )

    # Caveats
    lines.append("")
    lines.append("> **⚠️ 制限**: 全指標はプロキシ。")
    lines.append(
        "> ★ レーティングは Claude の自己評価。"
        "外部検証されていない。"
    )
    lines.append(
        "> n=1 問題は解決しないが、n=1 の内部データを"
        "可視化することに意味がある。"
    )

    return "\n".join(lines)


# PURPOSE: [L2-auto] 関数: main
def main():
    parser = argparse.ArgumentParser(
        description="認知品質ダッシュボード — Handoff から品質指標を集計"
    )
    parser.add_argument(
        "--days", type=int, default=None,
        help="過去N日間に限定 (default: 全期間)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="JSON 形式で出力"
    )
    parser.add_argument(
        "--trend", action="store_true",
        help="月次トレンドを表示"
    )
    args = parser.parse_args()

    report = generate_dashboard(
        days=args.days, as_json=args.json, show_trend=args.trend
    )
    print(report)


if __name__ == "__main__":
    main()
