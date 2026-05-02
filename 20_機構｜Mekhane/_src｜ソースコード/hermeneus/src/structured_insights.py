# PROOF: [L2/Phase2] <- hermeneus/src/structured_insights.py Downstream Consumer for Structured Outputs
"""
Hermēneus Structured Insights — JSONL ログの品質トレンド分析

structured_output の JSONL ログ (~/.hermeneus/logs/structured_outputs.jsonl) を
消費し、WF 実行の品質トレンドを可視化する downstream consumer。

- WF 別の平均確信度トレンド
- findings / open_questions の頻度分析
- fit_level の分布追跡
- 時系列での品質変化検出

Origin: 2026-03-01 Structured Outputs Naturalization (/fit*/ele)
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


# =============================================================================
# Constants
# =============================================================================

JSONL_PATH = Path.home() / ".hermeneus" / "logs" / "structured_outputs.jsonl"


# =============================================================================
# Data Types
# =============================================================================

# PURPOSE: 個別エントリの型安全なラッパー
@dataclass
class StructuredEntry:
    """JSONL の1行を型安全に扱うラッパー"""
    timestamp: datetime
    ccl: str
    model: str
    account: str
    structured_output: Dict[str, Any]

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Optional["StructuredEntry"]:
        """辞書からエントリを生成。不正データは None を返す。"""
        try:
            ts = datetime.fromisoformat(d["timestamp"])
            return cls(
                timestamp=ts,
                ccl=d.get("ccl", ""),
                model=d.get("model", ""),
                account=d.get("account", ""),
                structured_output=d.get("structured_output", {}),
            )
        except (KeyError, ValueError, TypeError):
            return None

    @property
    def wf_id(self) -> str:
        """CCL から WF ID を抽出 (e.g., '/noe+' → 'noe')"""
        return self.ccl.strip().lstrip("/@").rstrip("+-^~*").split("_")[0]

    @property
    def confidence(self) -> Optional[float]:
        """structured_output から confidence を取得"""
        return self.structured_output.get("confidence")

    @property
    def findings(self) -> List[str]:
        return self.structured_output.get("findings", [])

    @property
    def open_questions(self) -> List[str]:
        return self.structured_output.get("open_questions", [])

    @property
    def fit_level(self) -> Optional[str]:
        return self.structured_output.get("fit_level")


# PURPOSE: トレンド分析結果
@dataclass
class InsightReport:
    """品質トレンド分析レポート"""
    total_entries: int = 0
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    # WF 別の実行回数
    wf_counts: Dict[str, int] = field(default_factory=dict)

    # WF 別の平均確信度
    wf_avg_confidence: Dict[str, float] = field(default_factory=dict)

    # Fit Level 分布
    fit_distribution: Dict[str, int] = field(default_factory=dict)

    # 頻出する findings
    top_findings: List[tuple] = field(default_factory=list)

    # 頻出する open_questions
    top_questions: List[tuple] = field(default_factory=list)

    # モデル別実行回数
    model_counts: Dict[str, int] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """分析結果を Markdown 形式で出力"""
        if self.total_entries == 0:
            return "📭 構造化出力ログにエントリがありません。"

        period = ""
        if self.period_start and self.period_end:
            period = f"**期間**: {self.period_start.strftime('%Y-%m-%d %H:%M')} ～ {self.period_end.strftime('%Y-%m-%d %H:%M')}"

        lines = [
            "## 📊 Structured Output 品質トレンド",
            "",
            f"**総エントリ数**: {self.total_entries}",
            period,
            "",
        ]

        # WF 別実行回数 + 確信度
        if self.wf_counts:
            lines.append("### WF 別サマリー")
            lines.append("")
            lines.append("| WF | 実行回数 | 平均確信度 |")
            lines.append("|:---|--------:|----------:|")
            for wf, count in sorted(self.wf_counts.items(), key=lambda x: -x[1]):
                conf = self.wf_avg_confidence.get(wf)
                conf_str = f"{conf:.0%}" if conf is not None else "—"
                lines.append(f"| /{wf} | {count} | {conf_str} |")
            lines.append("")

        # Fit Level 分布
        if self.fit_distribution:
            lines.append("### Fit Level 分布")
            lines.append("")
            emoji = {"superficial": "🔴", "absorbed": "🟡", "naturalized": "🟢"}
            for level, count in sorted(self.fit_distribution.items(), key=lambda x: -x[1]):
                e = emoji.get(level, "⚪")
                lines.append(f"- {e} **{level}**: {count}件")
            lines.append("")

        # 頻出 findings
        if self.top_findings:
            lines.append("### 頻出 Findings (Top 5)")
            lines.append("")
            for finding, count in self.top_findings[:5]:
                lines.append(f"- ({count}回) {finding[:80]}")
            lines.append("")

        # 未解決の問い
        if self.top_questions:
            lines.append("### 未解決の問い (Top 5)")
            lines.append("")
            for q, count in self.top_questions[:5]:
                lines.append(f"- ({count}回) {q[:80]}")
            lines.append("")

        # モデル別
        if self.model_counts:
            lines.append("### モデル別実行回数")
            lines.append("")
            for model, count in sorted(self.model_counts.items(), key=lambda x: -x[1]):
                lines.append(f"- `{model}`: {count}回")

        return "\n".join(lines)


# =============================================================================
# Core Analysis
# =============================================================================

# PURPOSE: JSONL ファイルからエントリを読み込む
def load_entries(
    jsonl_path: Optional[Path] = None,
    since: Optional[datetime] = None,
    wf_filter: Optional[str] = None,
) -> List[StructuredEntry]:
    """JSONL ファイルからエントリを読み込む。

    Args:
        jsonl_path: JSONL ファイルのパス (デフォルト: ~/.hermeneus/logs/structured_outputs.jsonl)
        since: この日時以降のエントリのみ取得
        wf_filter: 特定の WF ID でフィルタ (e.g., 'noe', 'fit')

    Returns:
        StructuredEntry のリスト
    """
    path = jsonl_path or JSONL_PATH
    if not path.exists():
        return []

    entries: List[StructuredEntry] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                entry = StructuredEntry.from_dict(data)
                if entry is None:
                    continue
                if since and entry.timestamp < since:
                    continue
                if wf_filter and entry.wf_id != wf_filter.lstrip("/@").rstrip("+-^~*"):
                    continue
                entries.append(entry)
            except json.JSONDecodeError:
                continue

    return entries


# PURPOSE: エントリ群から品質トレンドを分析する
def analyze(
    entries: Optional[List[StructuredEntry]] = None,
    since: Optional[datetime] = None,
    wf_filter: Optional[str] = None,
    jsonl_path: Optional[Path] = None,
) -> InsightReport:
    """エントリ群から品質トレンドを分析する。

    Args:
        entries: 分析対象のエントリ (省略時は JSONL から読み込み)
        since: この日時以降のエントリのみ (entries 省略時に有効)
        wf_filter: 特定の WF ID でフィルタ
        jsonl_path: JSONL ファイルのパス

    Returns:
        InsightReport
    """
    if entries is None:
        entries = load_entries(jsonl_path=jsonl_path, since=since, wf_filter=wf_filter)

    report = InsightReport(total_entries=len(entries))

    if not entries:
        return report

    report.period_start = min(e.timestamp for e in entries)
    report.period_end = max(e.timestamp for e in entries)

    # WF 別集計
    wf_confidences: Dict[str, List[float]] = defaultdict(list)
    wf_counter: Counter = Counter()
    model_counter: Counter = Counter()
    fit_counter: Counter = Counter()
    findings_counter: Counter = Counter()
    questions_counter: Counter = Counter()

    for entry in entries:
        wf_counter[entry.wf_id] += 1
        model_counter[entry.model] += 1

        if entry.confidence is not None:
            wf_confidences[entry.wf_id].append(entry.confidence)

        if entry.fit_level:
            fit_counter[entry.fit_level] += 1

        for f in entry.findings:
            findings_counter[f] += 1
        for q in entry.open_questions:
            questions_counter[q] += 1

    report.wf_counts = dict(wf_counter)
    report.model_counts = dict(model_counter)
    report.fit_distribution = dict(fit_counter)
    report.top_findings = findings_counter.most_common(10)
    report.top_questions = questions_counter.most_common(10)

    # 平均確信度
    for wf_id, confs in wf_confidences.items():
        report.wf_avg_confidence[wf_id] = sum(confs) / len(confs) if confs else 0.0

    return report


# =============================================================================
# Convenience Functions
# =============================================================================

# PURPOSE: 直近N日間のトレンドを取得 (CLI / MCP 用)
def get_insights(days: int = 7, wf_filter: Optional[str] = None) -> str:
    """直近 N 日間の品質トレンドを Markdown で返す。

    Args:
        days: 分析対象の日数 (デフォルト: 7)
        wf_filter: 特定の WF ID でフィルタ

    Returns:
        Markdown 形式のレポート
    """
    since = datetime.now() - timedelta(days=days)
    report = analyze(since=since, wf_filter=wf_filter)
    return report.to_markdown()


# PURPOSE: schemas.py への依存を持つ検証関数 — 消したら壊れる
def validate_entry_schema(entry: StructuredEntry) -> List[str]:
    """エントリの structured_output がスキーマに適合しているか検証する。

    schemas.py の get_schema() を使用してバリデーションを行い、
    不足フィールドや型不一致を検出する。

    Returns:
        エラーメッセージのリスト (空ならバリデーション成功)
    """
    from hermeneus.src.schemas import get_schema

    schema = get_schema(entry.wf_id)
    errors: List[str] = []

    required = schema.get("required", [])
    properties = schema.get("properties", {})
    output = entry.structured_output

    # required フィールドの存在チェック
    for field_name in required:
        if field_name not in output:
            errors.append(f"Missing required field: {field_name}")

    # 型チェック (簡易)
    type_map = {"string": str, "number": (int, float), "integer": int, "array": list, "object": dict}
    for field_name, field_def in properties.items():
        if field_name in output:
            expected_type = type_map.get(field_def.get("type", ""))
            if expected_type and not isinstance(output[field_name], expected_type):
                errors.append(
                    f"Type mismatch for {field_name}: expected {field_def['type']}, "
                    f"got {type(output[field_name]).__name__}"
                )

    return errors
