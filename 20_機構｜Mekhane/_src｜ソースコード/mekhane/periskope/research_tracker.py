# PROOF: mekhane/periskope/research_tracker.py
# PURPOSE: periskope モジュールの research_tracker
"""Periskopē research tracking — /sop.track の永続化バックエンド.

調査テーマの進捗を YAML ファイルで管理する。
"""
import datetime
import yaml
from pathlib import Path
from dataclasses import dataclass, field, asdict


from mekhane.paths import OUTPUTS_DIR

TRACK_DIR = OUTPUTS_DIR / "research"


# PURPOSE: [L2-auto] ResearchTopic のクラス定義
@dataclass
class ResearchTopic:
    """調査テーマの進捗管理."""
    theme: str
    created: str = ""
    updated: str = ""
    completed: list[str] = field(default_factory=list)
    in_progress: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    depth_history: list[dict] = field(default_factory=list)  # [{depth, query, date, score}]

    # PURPOSE: [L2-auto] progress の関数定義
    @property
    def progress(self) -> float:
        """進捗率 (0.0-1.0)."""
        total = len(self.completed) + len(self.in_progress) + len(self.pending)
        if total == 0:
            return 0.0
        return len(self.completed) / total

    # PURPOSE: [L2-auto] progress_percent の関数定義
    @property
    def progress_percent(self) -> int:
        return int(self.progress * 100)


# PURPOSE: [L2-auto] _track_path の関数定義
def _track_path(theme_slug: str) -> Path:
    """テーマ名から YAML パスを生成."""
    return TRACK_DIR / f"track_{theme_slug}.yaml"


# PURPOSE: [L2-auto] _slugify の関数定義
def _slugify(theme: str) -> str:
    """テーマ名を slug に変換."""
    import re
    slug = re.sub(r'[^\w\s-]', '', theme.lower())
    slug = re.sub(r'[\s_]+', '-', slug).strip('-')
    return slug[:60]


# PURPOSE: [L2-auto] load_track の関数定義
def load_track(theme: str) -> ResearchTopic | None:
    """テーマの進捗をロード."""
    slug = _slugify(theme)
    path = _track_path(slug)
    if not path.exists():
        return None
    with open(path) as f:
        data = yaml.safe_load(f)
    return ResearchTopic(**data)


# PURPOSE: [L2-auto] save_track の関数定義
def save_track(topic: ResearchTopic) -> Path:
    """テーマの進捗を保存."""
    TRACK_DIR.mkdir(parents=True, exist_ok=True)
    slug = _slugify(topic.theme)
    path = _track_path(slug)
    topic.updated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    if not topic.created:
        topic.created = topic.updated
    with open(path, "w") as f:
        yaml.dump(asdict(topic), f, allow_unicode=True, default_flow_style=False)
    return path


# PURPOSE: [L2-auto] create_track の関数定義
def create_track(
    theme: str,
    topics: list[str] | None = None,
) -> ResearchTopic:
    """新しい調査テーマを作成."""
    topic = ResearchTopic(
        theme=theme,
        pending=list(topics) if topics else [],
    )
    save_track(topic)
    return topic


# PURPOSE: [L2-auto] update_progress の関数定義
def update_progress(
    theme: str,
    completed: list[str] | None = None,
    in_progress: list[str] | None = None,
    pending: list[str] | None = None,
    next_actions: list[str] | None = None,
) -> ResearchTopic:
    """進捗を更新."""
    topic = load_track(theme) or ResearchTopic(theme=theme)
    if completed:
        for item in completed:
            if item not in topic.completed:
                topic.completed.append(item)
            # Remove from in_progress/pending
            topic.in_progress = [x for x in topic.in_progress if x != item]
            topic.pending = [x for x in topic.pending if x != item]
    if in_progress:
        for item in in_progress:
            if item not in topic.in_progress:
                topic.in_progress.append(item)
            topic.pending = [x for x in topic.pending if x != item]
    if pending:
        for item in pending:
            if item not in topic.pending and item not in topic.completed and item not in topic.in_progress:
                topic.pending.append(item)
    if next_actions is not None:
        topic.next_actions = next_actions
    save_track(topic)
    return topic


# PURPOSE: [L2-auto] log_research_run の関数定義
def log_research_run(
    theme: str,
    query: str,
    depth: int,
    score: float | None = None,
) -> ResearchTopic:
    """調査実行を記録."""
    topic = load_track(theme) or ResearchTopic(theme=theme)
    topic.depth_history.append({
        "depth": depth,
        "query": query,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "score": score,
    })
    save_track(topic)
    return topic


# PURPOSE: [L2-auto] list_tracks の関数定義
def list_tracks() -> list[ResearchTopic]:
    """全調査テーマを一覧."""
    if not TRACK_DIR.exists():
        return []
    tracks = []
    for path in sorted(TRACK_DIR.glob("track_*.yaml")):
        with open(path) as f:
            data = yaml.safe_load(f)
        if data:
            tracks.append(ResearchTopic(**data))
    return tracks


# PURPOSE: [L2-auto] format_status の関数定義
def format_status(topic: ResearchTopic) -> str:
    """テーマの進捗を表形式で出力."""
    lines = [
        f"# 調査進捗: {topic.theme}",
        f"",
        f"| 項目 | 内容 |",
        f"|:-----|:-----|",
        f"| テーマ | {topic.theme} |",
        f"| 進捗率 | {topic.progress_percent}% |",
        f"| 完了 | {', '.join(topic.completed) or '—'} |",
        f"| 進行中 | {', '.join(topic.in_progress) or '—'} |",
        f"| 未着手 | {', '.join(topic.pending) or '—'} |",
        f"| 次のアクション | {', '.join(topic.next_actions) or '—'} |",
    ]
    if topic.depth_history:
        lines.append("")
        lines.append("## 調査履歴")
        lines.append("")
        lines.append("| 日時 | クエリ | Depth | Score |")
        lines.append("|:-----|:------|:------|------:|")
        for h in topic.depth_history[-5:]:  # Last 5
            score_str = f"{h['score']:.0%}" if h.get('score') is not None else "—"
            lines.append(f"| {h['date']} | {h['query'][:40]} | L{h['depth']} | {score_str} |")
    return "\n".join(lines)


# PURPOSE: [L2-auto] format_dashboard の関数定義
def format_dashboard() -> str:
    """H7: 全テーマ横断ダッシュボード — スコア推移表示."""
    tracks = list_tracks()
    if not tracks:
        return "調査テーマはまだありません。"

    lines = [
        "# 調査ダッシュボード",
        "",
        "## テーマ一覧",
        "",
        "| テーマ | 進捗 | 調査回数 | 平均スコア | 最新スコア | 更新日 |",
        "|:------|-----:|--------:|---------:|---------:|:------|",
    ]

    all_history = []
    for t in tracks:
        runs = len(t.depth_history)
        scores = [h["score"] for h in t.depth_history if h.get("score") is not None]
        avg = sum(scores) / len(scores) if scores else 0
        latest = scores[-1] if scores else 0
        lines.append(
            f"| {t.theme[:40]} | {t.progress_percent}% | {runs} | "
            f"{avg:.0%} | {latest:.0%} | {t.updated} |"
        )
        all_history.extend(t.depth_history)

    # Global score trend (last 10 runs across all themes)
    if all_history:
        sorted_history = sorted(all_history, key=lambda h: h.get("date", ""))
        recent = sorted_history[-10:]
        lines.append("")
        lines.append("## スコア推移 (直近10件)")
        lines.append("")
        lines.append("| 日時 | クエリ | Depth | Score |")
        lines.append("|:-----|:------|:------|------:|")
        for h in recent:
            score_str = f"{h['score']:.0%}" if h.get("score") is not None else "—"
            lines.append(
                f"| {h.get('date', '?')} | {h.get('query', '?')[:35]} | "
                f"L{h.get('depth', '?')} | {score_str} |"
            )

    return "\n".join(lines)
