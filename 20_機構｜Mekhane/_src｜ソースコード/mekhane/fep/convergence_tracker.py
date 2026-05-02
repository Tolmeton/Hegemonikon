#!/usr/bin/env python3
# PROOF: [L3/機能] <- mekhane/fep/ FEP Agent と Attractor の統合追跡
"""
Convergence Tracker — Agent/Attractor 統合スコアの永続的追跡

PURPOSE: FEP Agent と Attractor の「統合的価値」を測定する。

Design: Convergence as Pushout (圏論的再定義)
  旧: Equalizer = 「同じか？」 → rate = Σ(agreements) / Σ(total)
  新: Pushout  = 「一緒に何を作れるか？」 → 3成分統合スコア

ConvergenceScore = agreement×w₁ + value_alignment×w₂ + complementarity×w₃
  - agreement:       Agent と Attractor が一致したか (旧来の指標)
  - value_alignment:  結果が良かったか (本質的指標)
  - complementarity:  不一致が価値を生んだか (新規指標)

Convergence proof (3-layer criteria, /noe+ designed):
  1. Statistical: pushout_score > 0.3 with sufficient data
  2. Categorical: disagreements classified as explore/exploit/error
  3. Temporal: trend != "degrading"
"""

import json
import math
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal

# Disagreement categories (/noe+ design)
DisagreementCategory = Literal["explore", "exploit", "error", "unknown"]

# Max records to retain (prevents unbounded JSON growth)
MAX_RECORDS = 500

# Configurable via environment variable; falls back to default
_DEFAULT_PATH = os.path.expanduser(
    "~/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/convergence.json"
)
CONVERGENCE_PATH = Path(
    os.environ.get("HGK_CONVERGENCE_PATH", _DEFAULT_PATH)
)

# Pushout weights (configurable)
W_AGREEMENT = 0.2
W_VALUE_ALIGNMENT = 0.5
W_COMPLEMENTARITY = 0.3


# PURPOSE: の統一的インターフェースを実現する
@dataclass
class ConvergenceScore:
    """普遍的 Convergence スコア — Pushout として定義.

    Agent と Attractor の判断を「統合」し、
    一致/不一致を超えた価値を測定する。
    """

    # 射 π₁: Agent → Score
    agent_series: Optional[str]
    agent_confidence: float = 0.0

    # 射 π₂: Attractor → Score
    attractor_series: Optional[str] = None
    attractor_similarity: float = 0.0

    # Pushout の同値類（統合判断）
    agreement: bool = False
    value_alignment: float = 0.5      # [0,1] 中立初期値, /bye で更新
    complementarity: float = 0.0      # [0,1] 不一致が有益だったか

    # PURPOSE: convergence_tracker の score 処理を実行する
    @property
    def score(self) -> float:
        """統合 convergence スコア [0, 1]."""
        return (
            (1.0 if self.agreement else 0.0) * W_AGREEMENT
            + self.value_alignment * W_VALUE_ALIGNMENT
            + self.complementarity * W_COMPLEMENTARITY
        )

    # PURPOSE: convergence_tracker の to dict 処理を実行する
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON storage."""
        d = asdict(self)
        d["score"] = round(self.score, 3)
        return d


# PURPOSE: [L2-auto] _compute_complementarity の関数定義
def _compute_complementarity(
    agent_series: Optional[str],
    attractor_series: Optional[str],
    category: DisagreementCategory,
) -> float:
    """不一致の補完性を推定.

    - explore: Agent が情報収集 → 高い補完性 (0.7)
    - exploit: 異なる Series で行動 → 中程度 (0.4)
    - error:   エラー → 低い (0.1)
    - unknown: 不明 → 中立 (0.3)
    """
    if agent_series == attractor_series:
        return 0.0  # 一致時は complementarity 不要
    return {
        "explore": 0.7,
        "exploit": 0.4,
        "error": 0.1,
        "unknown": 0.3,
    }.get(category, 0.3)


# PURPOSE: [L2-auto] _load_records の関数定義
def _load_records() -> List[Dict[str, Any]]:
    """Load convergence records from disk."""
    if not CONVERGENCE_PATH.exists():
        return []
    try:
        with open(CONVERGENCE_PATH, "r") as f:
            data = json.load(f)
        return data.get("records", [])
    except Exception:  # noqa: BLE001
        return []


# PURPOSE: [L2-auto] _save_records の関数定義
def _save_records(records: List[Dict[str, Any]]) -> None:
    """Save convergence records to disk."""
    CONVERGENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": 1,
        "updated_at": datetime.now().isoformat(),
        "records": records,
    }
    with open(CONVERGENCE_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# PURPOSE: convergence_tracker の classify disagreement 処理を実行する
def classify_disagreement(
    agent_series: Optional[str],
    attractor_series: Optional[str],
    agent_action: str = "",
) -> DisagreementCategory:
    """Classify why Agent and Attractor disagreed.

    Categories (/noe+ design):
    - explore: Agent chose observe, Attractor recommended a Series
              → Agent is gathering info, healthy divergence
    - exploit: Agent chose a different Series than Attractor
              → Both are acting but on different domains
    - error:   One returned None/invalid unexpectedly
    - unknown: Cannot determine category
    """
    if agent_series == attractor_series:
        return "unknown"  # agreement, not a disagreement

    # Agent observes while Attractor recommends → explore
    if agent_action == "observe" or agent_series is None:
        return "explore"

    # Both have a Series but different → exploit
    if agent_series and attractor_series:
        return "exploit"

    # Something None/invalid → error
    return "error"


# PURPOSE: convergence_tracker の record agreement 処理を実行する
def record_agreement(
    agent_series: Optional[str],
    attractor_series: Optional[str],
    agent_action: str = "",
    epsilon: Optional[Dict[str, float]] = None,
    agent_confidence: float = 0.0,
    attractor_similarity: float = 0.0,
) -> Dict[str, Any]:
    """Record a convergence event between Agent and Attractor.

    Args:
        agent_series: Series selected by FEP Agent (None = observe)
        attractor_series: Series recommended by Attractor
        agent_action: Action name (e.g. "act_T", "observe")
        epsilon: Current ε values (for correlation analysis)
        agent_confidence: Agent's belief confidence [0, 1]
        attractor_similarity: Attractor's embedding similarity [0, 1]

    Returns:
        Updated convergence summary
    """
    records = _load_records()
    agreed = agent_series == attractor_series

    # Disagreement category
    category: DisagreementCategory = "unknown"
    if not agreed:
        category = classify_disagreement(
            agent_series, attractor_series, agent_action
        )

    # Compute ConvergenceScore (pushout)
    comp = _compute_complementarity(agent_series, attractor_series, category)
    conv_score = ConvergenceScore(
        agent_series=agent_series,
        agent_confidence=agent_confidence,
        attractor_series=attractor_series,
        attractor_similarity=attractor_similarity,
        agreement=agreed,
        value_alignment=0.5,  # 中立初期値, /bye で後から更新
        complementarity=comp,
    )

    record = {
        "timestamp": datetime.now().isoformat(),
        "agent_series": agent_series,
        "attractor_series": attractor_series,
        "agent_action": agent_action,
        "agreed": agreed,
        "epsilon": epsilon,
        "convergence_score": conv_score.to_dict(),
    }

    if not agreed:
        record["disagreement_category"] = category

    records.append(record)

    # Truncate to MAX_RECORDS (keep most recent)
    if len(records) > MAX_RECORDS:
        records = records[-MAX_RECORDS:]

    _save_records(records)

    return convergence_summary(records)


# PURPOSE: [L2-auto] _binomial_p_value の関数定義
def _binomial_p_value(successes: int, trials: int, chance: float = 1/6) -> float:
    """Compute one-sided binomial test p-value (H0: rate <= chance).

    Pure Python implementation — no scipy dependency.
    P(X >= successes | n=trials, p=chance) using the survival function.
    """
    if trials == 0 or successes == 0:
        return 1.0

    # P(X >= k) = 1 - P(X < k) = 1 - Σ_{i=0}^{k-1} C(n,i) * p^i * (1-p)^(n-i)
    p_value = 0.0
    for i in range(successes):
        # log-space to avoid overflow
        log_pmf = (
            _log_comb(trials, i)
            + i * math.log(chance)
            + (trials - i) * math.log(1 - chance)
        )
        p_value += math.exp(log_pmf)

    return round(1.0 - p_value, 6)


# PURPOSE: [L2-auto] _log_comb の関数定義
def _log_comb(n: int, k: int) -> float:
    """log(C(n, k)) using lgamma for numerical stability."""
    if k < 0 or k > n:
        return float("-inf")
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


# PURPOSE: convergence_tracker の convergence summary 処理を実行する
def convergence_summary(
    records: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Compute convergence statistics.

    Returns:
        Dict with:
        - total: number of records
        - agreements: number of agreements
        - rate: agreement rate (0.0-1.0)
        - p_value: binomial test p-value (H0: rate <= 1/6)
        - converged: True if p < 0.05 AND trend != "degrading"
        - recent_rate: agreement rate of last 10 records
        - trend: "improving" | "stable" | "degrading"
        - disagreement_breakdown: {explore: N, exploit: N, error: N}
    """
    if records is None:
        records = _load_records()

    if not records:
        return {
            "total": 0,
            "agreements": 0,
            "rate": 0.0,
            "p_value": 1.0,
            "converged": False,
            "recent_rate": 0.0,
            "trend": "unknown",
            "disagreement_breakdown": {},
        }

    total = len(records)
    agreements = sum(1 for r in records if r.get("agreed"))
    rate = agreements / total if total > 0 else 0.0

    # Binomial test: H0: rate <= 1/6 (chance with 6 Series)
    p_value = _binomial_p_value(agreements, total, chance=1/6)

    # Recent window (last 10)
    recent = records[-10:]
    recent_agreements = sum(1 for r in recent if r.get("agreed"))
    recent_rate = recent_agreements / len(recent) if recent else 0.0

    # Trend: compare first half vs second half
    if total >= 6:
        mid = total // 2
        first_half = records[:mid]
        second_half = records[mid:]
        rate_1 = sum(1 for r in first_half if r.get("agreed")) / len(first_half)
        rate_2 = sum(1 for r in second_half if r.get("agreed")) / len(second_half)
        if rate_2 - rate_1 > 0.1:
            trend = "improving"
        elif rate_1 - rate_2 > 0.1:
            trend = "degrading"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    # Disagreement breakdown
    breakdown: Dict[str, int] = {}
    for r in records:
        if not r.get("agreed"):
            cat = r.get("disagreement_category", "unknown")
            breakdown[cat] = breakdown.get(cat, 0) + 1

    # Pushout score: 統合スコアの平均
    pushout_scores = []
    for r in records:
        cs = r.get("convergence_score")
        if cs and "score" in cs:
            pushout_scores.append(cs["score"])
    avg_pushout = (
        sum(pushout_scores) / len(pushout_scores) if pushout_scores else 0.0
    )
    recent_pushout_scores = [
        r.get("convergence_score", {}).get("score", 0.0)
        for r in recent
        if r.get("convergence_score")
    ]
    recent_pushout = (
        sum(recent_pushout_scores) / len(recent_pushout_scores)
        if recent_pushout_scores
        else 0.0
    )

    # Convergence: 3-layer criteria (pushout version)
    #   1. Pushout score > 0.3 (better than degenerate case)
    #   2. Temporal: trend != "degrading"
    #   3. Minimum data: total >= 10
    converged = avg_pushout > 0.3 and trend != "degrading" and total >= 10

    return {
        "total": total,
        "agreements": agreements,
        "rate": round(rate, 3),
        "p_value": p_value,
        "converged": converged,
        "recent_rate": round(recent_rate, 3),
        "trend": trend,
        "disagreement_breakdown": breakdown,
        # Pushout metrics
        "pushout_score": round(avg_pushout, 3),
        "recent_pushout": round(recent_pushout, 3),
    }


# PURPOSE: convergence を整形する
def format_convergence(summary: Optional[Dict[str, Any]] = None) -> str:
    """Format convergence summary for display."""
    if summary is None:
        summary = convergence_summary()

    if summary["total"] == 0:
        return "📊 Convergence: No data yet"

    icon = "✅" if summary["converged"] else "📊"
    trend_icon = {"improving": "↗", "stable": "→", "degrading": "↘"}.get(
        summary["trend"], "?"
    )

    pushout = summary.get("pushout_score", 0.0)
    recent_p = summary.get("recent_pushout", 0.0)

    base = (
        f"{icon} Convergence: pushout={pushout:.2f} "
        f"agree={summary['rate']*100:.0f}% "
        f"({summary['agreements']}/{summary['total']}) "
        f"recent_pushout={recent_p:.2f} {trend_icon}"
    )

    # Add disagreement breakdown if any
    bd = summary.get("disagreement_breakdown", {})
    if bd:
        parts = [f"{k}={v}" for k, v in sorted(bd.items())]
        base += f" disagree=[{', '.join(parts)}]"

    return base


# =============================================================================
# CLI — E2E 接続ポイント (2)
# =============================================================================

# PURPOSE: convergence_tracker の main 処理を実行する
def main():
    """Convergence Tracker CLI.

    Usage:
        python convergence_tracker.py                    # 現在の収束状態を表示
        python convergence_tracker.py --record T T act_T # 手動記録
        python convergence_tracker.py --json             # JSON 出力
    """
    import argparse

    parser = argparse.ArgumentParser(description="Convergence Tracker CLI")
    parser.add_argument(
        "--record", nargs=3, metavar=("AGENT", "ATTRACTOR", "ACTION"),
        help="Record agreement: AGENT_SERIES ATTRACTOR_SERIES ACTION",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.record:
        agent_s, attractor_s, action = args.record
        # "None" → None
        agent_s = None if agent_s.lower() == "none" else agent_s
        attractor_s = None if attractor_s.lower() == "none" else attractor_s
        summary = record_agreement(agent_s, attractor_s, agent_action=action)
        print(f"✅ Recorded: agent={agent_s} attractor={attractor_s} action={action}")
        if args.json:
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        else:
            print(format_convergence(summary))
    else:
        summary = convergence_summary()
        if args.json:
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        else:
            print(format_convergence(summary))


if __name__ == "__main__":
    main()
