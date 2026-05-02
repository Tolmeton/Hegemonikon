from __future__ import annotations
# PROOF: [L2/FEP] <- mekhane/fep/theorem_recommender.py
# PURPOSE: Underused theorem activation — keyword-based suggestion for all 24 theorems
"""
Theorem Recommender

24 theorems x keyword table for auto-suggestion.
Tracks usage frequency and generates "Today's Theorem" for /boot.

Extends attractor_advisor.py's _suggest_k_theorems() to cover all 6 Series.
"""


import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from mekhane.paths import MNEME_RECORDS


# ---------------------------------------------------------------------------
# Keyword Tables — All 24 theorems mapped to natural language triggers
# ---------------------------------------------------------------------------

# Each entry: series, theorem_id, name, greek, command, question, keywords
THEOREM_KEYWORDS: list[dict] = [
    # --- O-series (Telos) ---
    {"series": "O", "id": "O1", "name": "Noēsis", "command": "/noe",
     "question": "本質は何か？",
     "keywords": ["本質", "なぜ", "根本", "原理", "哲学", "理解",
                  "essence", "why", "fundamental", "principle", "understand"]},
    {"series": "O", "id": "O2", "name": "Boulēsis", "command": "/bou",
     "question": "何を望むか？",
     "keywords": ["望む", "意志", "目的", "ゴール", "ビジョン", "したい",
                  "want", "will", "goal", "vision", "desire"]},
    {"series": "O", "id": "O3", "name": "Zētēsis", "command": "/zet",
     "question": "何を問うべきか？",
     "keywords": ["問い", "疑問", "探求", "調べる", "不明", "なんで",
                  "question", "inquiry", "investigate", "unknown"]},
    {"series": "O", "id": "O4", "name": "Energeia", "command": "/ene",
     "question": "どう実現するか？",
     "keywords": ["実装", "作る", "やる", "実行", "コード", "ビルド",
                  "implement", "build", "execute", "code", "create"]},

    # --- S-series (Methodos) ---
    {"series": "S", "id": "S1", "name": "Metron", "command": "/met",
     "question": "何を測るべきか？",
     "keywords": ["測定", "指標", "メトリクス", "KPI", "数値", "計量", "パフォーマンス",
                  "measure", "metric", "benchmark", "performance", "quantify"]},
    {"series": "S", "id": "S2", "name": "Mekhanē", "command": "/mek",
     "question": "どの方法で？",
     "keywords": ["方法", "手段", "ツール", "フレームワーク", "やり方", "スキル", "手順",
                  "method", "tool", "framework", "how-to", "approach", "procedure"]},
    {"series": "S", "id": "S3", "name": "Stathmos", "command": "/sta",
     "question": "品質はどう計量する？",
     "keywords": ["品質", "基準", "レビュー", "評価基準", "良い悪い", "テスト", "検査",
                  "quality", "standard", "review", "criteria", "assessment", "inspect"]},
    {"series": "S", "id": "S4", "name": "Praxis", "command": "/pra",
     "question": "実践でどう適用する？",
     "keywords": ["実践", "運用", "デプロイ", "現場", "使う", "適用", "ワークフロー",
                  "practice", "deploy", "apply", "workflow", "production", "operationalize"]},

    # --- H-series (Krisis) ---
    {"series": "H", "id": "H1", "name": "Propatheia", "command": "/pro",
     "question": "第一印象は？",
     "keywords": ["直感", "感覚", "印象", "気になる", "違和感", "好き嫌い",
                  "intuition", "feeling", "impression", "gut", "vibe"]},
    {"series": "H", "id": "H2", "name": "Pistis", "command": "/pis",
     "question": "どれくらい確か？",
     "keywords": ["確信", "信頼", "根拠", "エビデンス", "データ", "証拠",
                  "confidence", "trust", "evidence", "data", "proof", "reliable"]},
    {"series": "H", "id": "H3", "name": "Orexis", "command": "/ore",
     "question": "何を欲しているか？",
     "keywords": ["欲求", "優先", "トレードオフ", "選好", "価値", "重視",
                  "preference", "priority", "trade-off", "value", "desire"]},
    {"series": "H", "id": "H4", "name": "Doxa", "command": "/dox",
     "question": "何を信じているか？",
     "keywords": ["信念", "前提", "仮定", "思い込み", "パラダイム", "世界観",
                  "belief", "assumption", "paradigm", "worldview", "premise"]},

    # --- P-series (Diástasis) ---
    {"series": "P", "id": "P1", "name": "Khōra", "command": "/kho",
     "question": "どの空間で？",
     "keywords": ["空間", "場所", "スコープ", "境界", "範囲", "領域", "ディレクトリ",
                  "space", "scope", "boundary", "domain", "area", "directory", "architecture"]},
    {"series": "P", "id": "P2", "name": "Hodos", "command": "/hod",
     "question": "どの経路で？",
     "keywords": ["経路", "パス", "段階", "ステップ", "ロードマップ", "マイルストーン",
                  "path", "route", "step", "roadmap", "milestone", "phase"]},
    {"series": "P", "id": "P3", "name": "Trokhia", "command": "/tro",
     "question": "どのパターンで？",
     "keywords": ["パターン", "軌道", "サイクル", "繰り返し", "ループ", "傾向", "トレンド",
                  "pattern", "trajectory", "cycle", "loop", "trend", "recurring"]},
    {"series": "P", "id": "P4", "name": "Tekhnē", "command": "/tek",
     "question": "どの技術で？",
     "keywords": ["技術", "技法", "テクノロジー", "言語", "ライブラリ", "スタック", "Python", "Rust",
                  "technology", "technique", "stack", "library", "language", "toolchain"]},

    # --- K-series (Chronos) — current v3.5: 4 theorems ---
    {"series": "K", "id": "K1", "name": "Eukairia", "command": "/euk",
     "question": "今が好機か？",
     "keywords": ["今", "タイミング", "好機", "チャンス", "待つ", "今すぐ", "後で",
                  "timing", "opportunity", "now", "later", "window"]},
    {"series": "K", "id": "K2", "name": "Chronos", "command": "/chr",
     "question": "時間をどう配置する？",
     "keywords": ["時間", "期限", "スケジュール", "いつ", "期日", "締め切り", "見積もり",
                  "time", "deadline", "schedule", "when", "estimate", "calendar"]},
    {"series": "K", "id": "K3", "name": "Telos", "command": "/tel",
     "question": "目的に合っているか？",
     "keywords": ["目的", "意図", "ミッション", "合っている", "整合", "方向性",
                  "purpose", "intent", "mission", "align", "direction", "objective"]},
    {"series": "K", "id": "K4", "name": "Sophia", "command": "/sop",
     "question": "過去の知恵は？",
     "keywords": ["知恵", "経験", "教訓", "過去", "学んだ", "前回", "歴史",
                  "wisdom", "experience", "lesson", "history", "learned", "precedent"]},

    # --- A-series (Orexis) ---
    {"series": "A", "id": "A1", "name": "Pathos", "command": "/pat",
     "question": "何が感じられるか？",
     "keywords": ["感情", "共感", "痛み", "喜び", "ユーザー体験", "UX",
                  "emotion", "empathy", "pain", "joy", "user experience", "UX"]},
    {"series": "A", "id": "A2", "name": "Krisis", "command": "/dia",
     "question": "判断は妥当か？",
     "keywords": ["判断", "評価", "レビュー", "批判", "判定", "妥当",
                  "judgment", "evaluate", "review", "critique", "assess", "valid"]},
    {"series": "A", "id": "A3", "name": "Gnōmē", "command": "/gno",
     "question": "経験的判断は？",
     "keywords": ["経験則", "勘", "ベストプラクティス", "定石", "常識", "慣例",
                  "heuristic", "best practice", "convention", "common sense", "rule of thumb"]},
    {"series": "A", "id": "A4", "name": "Epistēmē", "command": "/epi",
     "question": "確実に知っていることは？",
     "keywords": ["知識", "確実", "証明", "論文", "研究", "学術", "エビデンス",
                  "knowledge", "certain", "proven", "research", "academic", "evidence"]},
]


# ---------------------------------------------------------------------------
# Usage Tracker
# ---------------------------------------------------------------------------

_USAGE_FILE = MNEME_RECORDS / "e_ログ_logs" / "theorem_usage.jsonl"


# PURPOSE: [L2-auto] TheoremUsage のクラス定義
@dataclass
class TheoremUsage:
    """A single usage record."""
    theorem_id: str
    timestamp: str
    context: str = ""


# PURPOSE: [L2-auto] _load_usage_counts の関数定義
def _load_usage_counts() -> dict[str, int]:
    """Load usage counts from JSONL file."""
    counts: dict[str, int] = {t["id"]: 0 for t in THEOREM_KEYWORDS}
    if not _USAGE_FILE.exists():
        return counts
    try:
        for line in _USAGE_FILE.read_text().strip().split("\n"):
            if line:
                record = json.loads(line)
                tid = record.get("theorem_id", "")
                if tid in counts:
                    counts[tid] += 1
    except Exception:  # noqa: BLE001
        pass
    return counts


# PURPOSE: [L2-auto] record_usage の関数定義
def record_usage(theorem_id: str, context: str = "") -> None:
    """Record a theorem usage event."""
    _USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "theorem_id": theorem_id,
        "timestamp": datetime.now().isoformat(),
        "context": context[:100],
    }
    with open(_USAGE_FILE, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Keyword Matcher
# ---------------------------------------------------------------------------

# PURPOSE: [L2-auto] TheoremSuggestion のクラス定義
@dataclass
class TheoremSuggestion:
    """A suggested theorem with score and reason."""
    theorem_id: str
    name: str
    series: str
    command: str
    question: str
    score: float
    matched_keywords: list[str] = field(default_factory=list)


# PURPOSE: [L2-auto] suggest_theorems の関数定義
def suggest_theorems(
    user_input: str,
    max_results: int = 3,
    exclude_series: Optional[list[str]] = None,
) -> list[TheoremSuggestion]:
    """Keyword-match user input against all 24 theorem keyword tables.

    Args:
        user_input: Task description or natural language input.
        max_results: Maximum number of suggestions.
        exclude_series: Series to exclude (e.g., ["O", "A"] if already used).

    Returns:
        Sorted list of TheoremSuggestion (highest score first).
    """
    input_lower = user_input.lower()
    exclude = set(exclude_series or [])
    suggestions: list[TheoremSuggestion] = []

    for t in THEOREM_KEYWORDS:
        if t["series"] in exclude:
            continue
        matched = [kw for kw in t["keywords"] if kw.lower() in input_lower]
        if matched:
            suggestions.append(TheoremSuggestion(
                theorem_id=t["id"],
                name=t["name"],
                series=t["series"],
                command=t["command"],
                question=t["question"],
                score=len(matched),
                matched_keywords=matched,
            ))

    suggestions.sort(key=lambda x: x.score, reverse=True)
    return suggestions[:max_results]


# ---------------------------------------------------------------------------
# Today's Theorem — for /boot integration
# ---------------------------------------------------------------------------

# PURPOSE: [L2-auto] todays_theorem の関数定義
def todays_theorem(n: int = 2) -> list[dict]:
    """Select n underused theorems for today's session.

    Strategy:
    1. Load usage counts
    2. Pick from the least-used theorems
    3. Prefer different Series for diversity
    4. Add a connection prompt

    Returns:
        List of {"id", "name", "series", "command", "question", "usage_count", "prompt"}
    """
    counts = _load_usage_counts()

    # Sort by usage count (ascending = least used first)
    ranked = sorted(THEOREM_KEYWORDS, key=lambda t: counts.get(t["id"], 0))

    selected: list[dict] = []
    seen_series: set[str] = set()

    for t in ranked:
        if len(selected) >= n:
            break
        # Prefer diversity: one theorem per Series
        if t["series"] in seen_series and len(selected) < n - 1:
            continue

        usage = counts.get(t["id"], 0)
        prompt = _generate_connection_prompt(t)

        selected.append({
            "id": t["id"],
            "name": t["name"],
            "series": t["series"],
            "command": t["command"],
            "question": t["question"],
            "usage_count": usage,
            "prompt": prompt,
        })
        seen_series.add(t["series"])

    return selected


# PURPOSE: [L2-auto] _generate_connection_prompt の関数定義
def _generate_connection_prompt(theorem: dict) -> str:
    """Generate a prompt to connect the theorem to today's work."""
    prompts = {
        "S1": "作業の品質をどう計量していますか？ 測定なき改善は幻想です。",
        "S2": "今使っている方法を選んだ理由は？ 他の方法を3つ挙げられますか？",
        "S3": "「良い」の基準は明示されていますか？ 暗黙の基準は危険です。",
        "S4": "理論を実践に変換するとき、何が失われていますか？",
        "P1": "作業空間の境界は意識していますか？ スコープクリープは起きていませんか？",
        "P2": "A→B の経路は1本ですか？ 代替経路を検討しましたか？",
        "P3": "今の作業パターンは最初に決めたものですか？ 軌道修正の必要は？",
        "P4": "選んだ技術は問題に適していますか？ 道具に合わせて問題を変形していませんか？",
        "K1": "今がこの作業の好機である理由は？ 後でやる方が良い可能性は？",
        "K2": "この作業にどれくらいの時間を割くべきですか？ 上限を決めていますか？",
        "K3": "この作業は最終目的にどう繋がりますか？ 手段の目的化は起きていませんか？",
        "K4": "過去の類似経験から何を学べますか？ 同じ失敗を繰り返していませんか？",
        "A1": "ユーザーはこの変更をどう感じますか？ 技術的正しさ ≠ ユーザー体験の良さ。",
        "A3": "経験則と論理的根拠のどちらに依存していますか？ 勘は言語化すべきです。",
        "A4": "「知っている」と「思っている」を区別していますか？ 知識の境界はどこですか？",
    }
    default = f"「{theorem['question']}」— この問いを今日の作業に当てはめてみてください。"
    return prompts.get(theorem["id"], default)


# ---------------------------------------------------------------------------
# Usage Summary
# ---------------------------------------------------------------------------

# PURPOSE: [L2-auto] usage_summary の関数定義
def usage_summary() -> dict:
    """Generate a usage summary for dashboard display.

    Returns:
        {"total": N, "by_series": {S: N}, "by_theorem": {tid: N},
         "unused": [tid, ...], "most_used": [(tid, N), ...]}
    """
    counts = _load_usage_counts()
    total = sum(counts.values())

    by_series: dict[str, int] = {}
    for t in THEOREM_KEYWORDS:
        s = t["series"]
        by_series[s] = by_series.get(s, 0) + counts.get(t["id"], 0)

    unused = [tid for tid, c in counts.items() if c == 0]
    most_used = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total": total,
        "by_series": by_series,
        "by_theorem": counts,
        "unused": unused,
        "unused_count": len(unused),
        "most_used": most_used,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

# PURPOSE: [L2-auto] main の関数定義
def main() -> None:
    """CLI: python -m mekhane.fep.theorem_recommender [suggest|today|summary] [input]"""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m mekhane.fep.theorem_recommender suggest <text>")
        print("  python -m mekhane.fep.theorem_recommender today")
        print("  python -m mekhane.fep.theorem_recommender summary")
        sys.exit(1)

    action = sys.argv[1]

    if action == "suggest":
        text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "何をすべきか"
        results = suggest_theorems(text, max_results=5)
        print(f"\n入力: {text}")
        print("=" * 50)
        for s in results:
            print(f"  {s.theorem_id} {s.name} ({s.command}) — {s.question}")
            print(f"    Score: {s.score}, Matched: {s.matched_keywords}")
        if not results:
            print("  (マッチなし)")

    elif action == "today":
        theorems = todays_theorem(n=2)
        print("\n💡 今日の定理提案")
        print("=" * 50)
        for t in theorems:
            print(f"  {t['id']} {t['name']} ({t['command']}) — 使用回数: {t['usage_count']}")
            print(f"    {t['prompt']}")

    elif action == "summary":
        s = usage_summary()
        print("\n📊 定理使用サマリー")
        print("=" * 50)
        print(f"  Total: {s['total']}")
        print(f"  By Series: {s['by_series']}")
        print(f"  Unused: {s['unused_count']}/24 ({', '.join(s['unused'])})")
        print(f"  Most used: {s['most_used']}")

    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
