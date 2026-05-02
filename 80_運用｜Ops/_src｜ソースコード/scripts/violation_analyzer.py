#!/usr/bin/env python3
# PROOF: [L2/運用] <- scripts/
# PURPOSE: violations.md の自動分析 + /boot 用サマリー生成
"""
violation_analyzer.py — 違反パターン自動分析

violations.md から構造化エントリを読み込み、
パターン統計と傾向レポートを生成する。
/boot 時に呼び出して「過去の違反傾向」を想起させる。

Usage:
    python scripts/violation_analyzer.py                 # フルレポート
    python scripts/violation_analyzer.py --summary       # /boot 用サマリー
    python scripts/violation_analyzer.py --pattern skip_bias  # パターン別
    python scripts/violation_analyzer.py --since 7       # 直近N日
"""

import re
import sys
import argparse
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import yaml


# ============================================================
# Config
# ============================================================

VIOLATIONS_PATH = (
    Path(__file__).parent.parent / "nous" / "rules" /
    "behavioral_constraints" / "violations.md"
)

RETRACTION_EVENTS_PATH = (
    Path(__file__).parent.parent / "nous" / "rules" /
    "behavioral_constraints" / "retraction_events_raw.jsonl"
)

PATTERN_NAMES = {
    "skip_bias": "知っている→省略",
    "env_gap": "環境強制なし",
    "accuracy_vs_utility": "正確 ≠ 有用",
    "false_impossibility": "できない ≠ やっていない",
    "selective_omission": "勝手な省略",
    "stale_handoff": "古い情報を信じる",
    "preflight_waste": "確認が本番を消費",
    "shortcut": "短絡・手抜き",
    "overconfidence": "過信",
    "sycophancy": "迎合",
    "premature_completion": "生き急ぎ完了",
    "hallucination": "捏造・ハルシネーション",
    "retraction": "撤回・方向転換",
    "self_criticism": "自己批判・反省",
    "fact_correction": "事実の訂正・発見",
    "llm_limitation": "LLMの制約(コンテキスト等)",
    "ccl_bypass": "CCL 手書き偽装",
    "atomic_violation": "原子性違反",
    "laziness_deception": "怠惰欺瞞",
    "source_avoidance": "1次ソース回避",
    "uncategorized": "未分類",
}


# ============================================================
# Parser
# ============================================================

def parse_retraction_events(path: Optional[Path] = None) -> dict:
    """JSONLから撤回イベントをカテゴリ別に分類して返す。"""
    import json
    path = path or RETRACTION_EVENTS_PATH
    if not path.exists():
        return {"total": 0, "categories": {}}

    # Keyword-based classification (first match wins)
    _categories = {
        "hallucination": ["捏造", "ハルシネ", "hallucin", "存在しない", "実在しない",
                          "bge-m3", "嘘", "偽", "不正確", "誤認", "勝手な解釈"],
        "premature_completion": ["完了", "完成", "done", "修正済", "対応済", "終わり",
                                  "問題な", "premature", "生き急ぎ", "十分", "終了",
                                  "clear", "正常"],
        "selective_omission": ["省略", "見落", "漏れ", "抜け", "omit", "skip",
                                "忘れ", "不足", "欠け", "足りな", "端折",
                                "読み飛ば", "含まれていな", "削ってしまった", "削った"],
        "overconfidence": ["過信", "断定", "確実", "間違いない", "overconfid",
                           "浅かった", "急いだ", "安易", "時期尚早", "結論を出し", "早計", "軽率"],
        "self_criticism": ["判断ミス", "怠惰", "サボ", "怠け", "品質を落",
                           "申し訳", "私の怒り", "逃げ", "自分勝手", "舐め",
                           "欺瞞", "恥", "怠慢", "反省", "違反です", "違反を認",
                           "すみません", "ごめんなさい", "認めます", "弁明", "骨格を並べただけ", "パディング", "雑でした", "腰が引けて"],
        "sycophancy": ["迎合", "sycophancy", "期待に沿", "期待に応え"],
        "skip_bias": ["知っている", "わかった", "省略しよう", "skip_bias",
                      "読まず", "確認せず", "開かず"],
        "shortcut": ["手抜", "shortcut", "短絡", "近道"],
        "retraction": ["撤回", "方向転換", "やり直", "修正", "間違", "誤り", "訂正",
                       "再検討", "見直", "creatorの指摘は正し", "指摘は正当",
                       "結論を急", "bc-19違反", "反証", "指摘",
                       "creatorが正し", "おっしゃる通り", "ではなく",
                       "が正しい", "は正しかった", "エラー", "前回の分析",
                       "完全に理解した", "creatorは正しい", "直感が正しか", "弱いことを認め", "完全に正しい"],
        "fact_correction": ["判明", "発見", "特定する", "特定し", "確認する", "依頼"],
        "llm_limitation": ["サイズ制限", "コンテキスト"],
    }

    cat_counts: dict[str, int] = {}
    total = 0
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                total += 1
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                content = entry.get("content", "").lower()
                matched = False
                for cat, keywords in _categories.items():
                    if any(kw.lower() in content for kw in keywords):
                        cat_counts[cat] = cat_counts.get(cat, 0) + 1
                        matched = True
                        break
                if not matched:
                    cat_counts["uncategorized"] = cat_counts.get("uncategorized", 0) + 1
    except Exception:
        pass

    return {"total": total, "categories": cat_counts}

def parse_violations(path: Optional[Path] = None) -> list[dict]:
    """violations.md から YAML エントリを抽出する。"""
    path = path or VIOLATIONS_PATH
    if not path.exists():
        return []

    content = path.read_text(encoding="utf-8")

    # ```yaml ... ``` ブロックを全て抽出
    entries = []
    for match in re.finditer(r"```yaml\n(.+?)\n```", content, re.DOTALL):
        try:
            data = yaml.safe_load(match.group(1))
            if isinstance(data, dict) and "id" in data:
                entries.append(data)
        except yaml.YAMLError:
            continue

    return entries


# ============================================================
# Analysis
# ============================================================

def analyze(
    entries: list[dict],
    pattern_filter: Optional[str] = None,
    since_days: Optional[int] = None,
) -> dict:
    """違反エントリを分析して統計を返す。"""
    # フィルタリング
    filtered = entries

    if pattern_filter:
        filtered = [e for e in filtered if e.get("pattern") == pattern_filter]

    if since_days is not None:
        cutoff = datetime.now() - timedelta(days=since_days)
        filtered = [
            e for e in filtered
            if datetime.strptime(e.get("date", "2000-01-01"), "%Y-%m-%d") >= cutoff
        ]

    # 統計
    pattern_counts: Counter = Counter()
    for e in filtered:
        p = e.get("pattern", "unknown")
        if isinstance(p, list):
            pattern_counts.update(p)
        else:
            pattern_counts[str(p)] += 1
            
    bc_counts: Counter = Counter()
    for e in filtered:
        bcs = e.get("bc", [])
        if isinstance(bcs, list):
            bc_counts.update(bcs)
        else:
            bc_counts[str(bcs)] += 1

    severity_counts = Counter(e.get("severity", "unknown") for e in filtered)
    recurrence_count = sum(1 for e in filtered if e.get("recurrence"))

    return {
        "total": len(filtered),
        "patterns": dict(pattern_counts.most_common()),
        "bc_counts": dict(bc_counts.most_common()),
        "severity": dict(severity_counts),
        "recurrence": recurrence_count,
        "entries": filtered,
    }


# ============================================================
# Formatters
# ============================================================

def format_full_report(stats: dict) -> str:
    """フルレポートを生成。"""
    lines = [
        "📊 違反パターン分析レポート",
        f"   総件数: {stats['total']}",
        f"   再犯数: {stats['recurrence']}",
        "",
        "── パターン別 ──",
    ]

    for pattern, count in stats["patterns"].items():
        name = PATTERN_NAMES.get(pattern, pattern)
        lines.append(f"  {count}件  {name} ({pattern})")

    lines.append("")
    lines.append("── BC 別 ──")
    for bc, count in stats["bc_counts"].items():
        lines.append(f"  {count}件  {bc}")

    lines.append("")
    lines.append("── 深刻度 ──")
    for sev, count in stats["severity"].items():
        icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(sev, "⚪")
        lines.append(f"  {icon} {sev}: {count}件")

    # JSONL カテゴリ別内訳を追加
    retraction_data = parse_retraction_events()
    if retraction_data["total"] > 0:
        lines.append("")
        lines.append(f"── 撤回イベント (JSONL: {retraction_data['total']}件) ──")
        sorted_cats = sorted(
            retraction_data["categories"].items(),
            key=lambda x: x[1], reverse=True
        )
        for cat, count in sorted_cats:
            name = PATTERN_NAMES.get(cat, cat)
            pct = count / retraction_data["total"] * 100
            lines.append(f"  {count}件 ({pct:.0f}%)  {name}")

    return "\n".join(lines)


def format_boot_summary(stats: dict) -> str:
    """/boot 用の簡潔なサマリー。"""
    retraction_data = parse_retraction_events()

    lines = []
    
    # S-I (旧 BC-20) 戒め（恥の記録）の強制注入
    if retraction_data["total"] > 0:
        lines.append(f"🚨 恥の記録: 過去 {retraction_data['total']} 回、前言を撤回している。")
        
        # カテゴリ上位3つを表示
        cats = retraction_data["categories"]
        sorted_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)[:3]
        top_str = ", ".join(
            f"{PATTERN_NAMES.get(c, c)} {n}件"
            for c, n in sorted_cats
        )
        lines.append(f"   内訳上位: {top_str}")
        
        # premature_completion 専用警告
        pc_count = cats.get("premature_completion", 0)
        if pc_count > 0:
            lines.append(f"   ⚠️ 生き急ぎ (premature_completion): {pc_count}件。「完了」と思ったらまだ終わっていない。")
        lines.append("")

    if stats["total"] == 0:
        lines.append("✅ 違反記録なし")
        return "\n".join(lines)

    # 最頻出パターンを1つ
    top_pattern = max(stats["patterns"], key=stats["patterns"].get) if stats["patterns"] else None
    top_name = PATTERN_NAMES.get(top_pattern, top_pattern) if top_pattern else "不明"
    top_count = stats["patterns"].get(top_pattern, 0) if top_pattern else 0

    lines.append(f"⚠️ HGK 違反傾向 ({stats['total']}件中)")
    lines.append(f"  最頻出: {top_name} ({top_count}件)")

    if stats["recurrence"] > 0:
        lines.append(f"  🔴 再犯: {stats['recurrence']}件")

    # 直近の教訓
    if stats["entries"]:
        latest = stats["entries"][-1]
        lesson = latest.get("lesson", latest.get("summary", ""))
        lines.append(f"  最新教訓: {lesson}")

    return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="違反パターン自動分析 — /boot 用サマリー生成"
    )
    parser.add_argument("--summary", action="store_true", help="/boot 用簡潔サマリー")
    parser.add_argument("--pattern", type=str, help="パターンIDでフィルタ")
    parser.add_argument("--since", type=int, help="直近N日間")
    parser.add_argument("--json", action="store_true", help="JSON出力")
    parser.add_argument("--path", type=str, help="violations.md パス（デフォルト: 自動検出）")
    args = parser.parse_args()

    path = Path(args.path) if args.path else None
    entries = parse_violations(path)
    stats = analyze(entries, pattern_filter=args.pattern, since_days=args.since)

    if args.json:
        import json
        # entries は冗長なので除外
        output = {k: v for k, v in stats.items() if k != "entries"}
        print(json.dumps(output, ensure_ascii=False, indent=2))
    elif args.summary:
        print(format_boot_summary(stats))
    else:
        print(format_full_report(stats))

    sys.exit(0)


if __name__ == "__main__":
    main()
