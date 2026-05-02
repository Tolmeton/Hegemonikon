from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/fep/ Krisis随伴のメトリクスをセッション間で永続化
"""
Krisis Metrics Store — η/ε メトリクスの永続化

Problem: Krisis 随伴の η/ε はセッション揮発性。次の /boot で参照できない。
Solution: JSONL ファイルに WF 実行ごとのメトリクスを追記保存し、/boot で読み込む。

Architecture:
    WF 実行 → compute_wf_eta/epsilon → save_metrics() → krisis_metrics.jsonl
    /boot → load_latest_metrics() → Boot レポート表示
"""


import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from mekhane.paths import MNEME_RECORDS

# PURPOSE: メトリクスファイルのデフォルトパス
METRICS_DIR = MNEME_RECORDS / "e_ログ_logs" / "metrics"
METRICS_FILE = METRICS_DIR / "krisis_metrics.jsonl"


# PURPOSE: メトリクスエントリの構造
def _make_entry(
    wf_id: str,
    pair_name: str,
    eta: float,
    epsilon: float,
    drift_type: Optional[str] = None,
    context_summary: str = "",
) -> Dict:
    """Create a metrics entry dict."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "wf_id": wf_id,
        "pair_name": pair_name,
        "eta": round(eta, 4),
        "epsilon": round(epsilon, 4),
        "drift": round(1.0 - epsilon, 4),
        "drift_type": drift_type,
        "context_summary": context_summary[:200],  # cap length
    }


# PURPOSE: メトリクスを JSONL に追記保存
def save_metrics(
    wf_id: str,
    pair_name: str,
    eta: float,
    epsilon: float,
    drift_type: Optional[str] = None,
    context_summary: str = "",
    metrics_file: Optional[Path] = None,
) -> Path:
    """Append a metrics entry to the JSONL file.

    Args:
        wf_id: e.g. "kat", "epo", "pai", "dok"
        pair_name: "K⊣E" or "P⊣D"
        eta: Quality score (0-1)
        epsilon: Precision score (0-1)
        drift_type: Optional drift type detected
        context_summary: Brief context description
        metrics_file: Override path (for testing)

    Returns:
        Path to the metrics file
    """
    target = metrics_file or METRICS_FILE
    target.parent.mkdir(parents=True, exist_ok=True)

    entry = _make_entry(wf_id, pair_name, eta, epsilon, drift_type, context_summary)
    with open(target, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return target


# PURPOSE: 直近 N 件のメトリクスを読み込む
def load_latest_metrics(
    n: int = 10,
    pair_name: Optional[str] = None,
    metrics_file: Optional[Path] = None,
) -> List[Dict]:
    """Load the latest N metrics entries.

    Args:
        n: Number of latest entries to return
        pair_name: Filter by pair name (optional)
        metrics_file: Override path (for testing)

    Returns:
        List of metric entries (newest first)
    """
    target = metrics_file or METRICS_FILE
    if not target.exists():
        return []

    entries = []
    with open(target, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if pair_name is None or entry.get("pair_name") == pair_name:
                    entries.append(entry)
            except json.JSONDecodeError:
                continue

    # Return newest first
    return entries[-n:][::-1]


# PURPOSE: ペアごとの集約メトリクスを計算
def aggregate_metrics(
    pair_name: str,
    n: int = 5,
    metrics_file: Optional[Path] = None,
) -> Dict:
    """Compute aggregate metrics for a pair.

    Args:
        pair_name: "K⊣E" or "P⊣D"
        n: Number of recent entries to aggregate
        metrics_file: Override path (for testing)

    Returns:
        Dict with avg_eta, avg_epsilon, avg_drift, count, trend
    """
    entries = load_latest_metrics(n=n, pair_name=pair_name, metrics_file=metrics_file)
    if not entries:
        return {
            "pair_name": pair_name,
            "avg_eta": 0.0,
            "avg_epsilon": 0.0,
            "avg_drift": 1.0,
            "count": 0,
            "trend": "no_data",
        }

    etas = [e["eta"] for e in entries]
    epsilons = [e["epsilon"] for e in entries]
    avg_eta = sum(etas) / len(etas)
    avg_epsilon = sum(epsilons) / len(epsilons)

    # Trend: compare first half vs second half
    if len(entries) >= 4:
        mid = len(entries) // 2
        first_half_eta = sum(etas[:mid]) / mid
        second_half_eta = sum(etas[mid:]) / (len(etas) - mid)
        if second_half_eta > first_half_eta + 0.05:
            trend = "improving"
        elif second_half_eta < first_half_eta - 0.05:
            trend = "degrading"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    return {
        "pair_name": pair_name,
        "avg_eta": round(avg_eta, 4),
        "avg_epsilon": round(avg_epsilon, 4),
        "avg_drift": round(1.0 - avg_epsilon, 4),
        "count": len(entries),
        "trend": trend,
    }


# PURPOSE: Boot レポート用のフォーマット済みメトリクスセクション
def format_boot_metrics(metrics_file: Optional[Path] = None) -> str:
    """Format Krisis adjunction metrics for /boot display.

    Returns a section ready to be inserted into the boot report.
    """
    ke = aggregate_metrics("K⊣E", metrics_file=metrics_file)
    pd = aggregate_metrics("P⊣D", metrics_file=metrics_file)

    if ke["count"] == 0 and pd["count"] == 0:
        return "  Krisis Adjunctions: データなし（WF未実行）"

    lines = ["  ⊣ Krisis Adjunctions (永続メトリクス):"]

    for agg in [ke, pd]:
        if agg["count"] == 0:
            lines.append(f"    {agg['pair_name']}: データなし")
            continue

        trend_icon = {"improving": "📈", "degrading": "📉", "stable": "→", "insufficient_data": "…", "no_data": "∅"}.get(agg["trend"], "?")
        faithful = "✅" if agg["avg_eta"] > 0.8 else "⚠️"
        lines.append(
            f"    {agg['pair_name']}: η={agg['avg_eta']:.2f} ε={agg['avg_epsilon']:.2f} "
            f"drift={agg['avg_drift']:.2f} {faithful} ({agg['count']}件, {trend_icon}{agg['trend']})"
        )

    return "\n".join(lines)
