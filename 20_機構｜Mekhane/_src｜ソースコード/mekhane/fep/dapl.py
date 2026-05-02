from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/fep/ A0→dirty adapterの設計を体系化する必要→dapl が担う
"""
DAPL — Dirty Adapter Pattern Language v1

理論と現実の接続点で発生する「汚い妥協」を体系化する。
Hegemonikón の FEP 層で使われる dirty adapter を登録・管理・TTL 追跡する。

Origin: /zet+ Q18 (2026-02-08)
Insight: DAPL の3パターンは FEP の3戦略と同型である。

    FEP Strategy           DAPL Pattern            操作
    ─────────────          ──────────────          ──────────
    Perceptual inference   Ensemble               多重推定 → max/mean
    Precision weighting    PenaltyMultiplier       信頼度減衰 → ×係数
    Active inference       DefensiveFallback       環境介入 → try/except

設計時に4つを決める:
    1. Pattern: Ensemble | PenaltyMultiplier | DefensiveFallback
    2. TTL: この adapter はいつ clean に交換するか
    3. Upgrade Path: clean 版のインターフェース
    4. Silent Failure Risk: LOW | MEDIUM | HIGH

Usage:
    from mekhane.fep.dapl import DAPL_REGISTRY, check_ttl, list_adapters
    expired = check_ttl()  # TTL 超過の adapter を返す
"""


from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import List


# PURPOSE: DAPL パターン分類 — FEP 戦略と同型
class DAPLPattern(Enum):
    """Dirty adapter pattern taxonomy, isomorphic to FEP strategies."""

    ENSEMBLE = "Ensemble"
    # FEP analog: Perceptual inference (多重予測)
    # 操作: 複数の不完全な推定器の楽観的合成
    # 例: max(seq_ratio, jaccard)

    PENALTY_MULTIPLIER = "PenaltyMultiplier"
    # FEP analog: Precision weighting (感覚精度の調整)
    # 操作: 信頼できない入力に減衰係数を掛ける
    # 例: ε_raw × fill_ratio

    DEFENSIVE_FALLBACK = "DefensiveFallback"
    # FEP analog: Active inference (環境への介入)
    # 操作: 不正入力を静かに無視する
    # 例: try: float(x) except: skip


# PURPOSE: Silent failure のリスクレベル
class SilentFailureRisk(Enum):
    """Silent failure risk level — determines TTL urgency."""

    LOW = "LOW"        # max は安全側に倒れる → 12ヶ月
    MEDIUM = "MEDIUM"  # ハードコード定数がある → 6ヶ月
    HIGH = "HIGH"      # 有効入力を捨てる可能性 → 3ヶ月 + logging 義務


# PURPOSE: 個別の dirty adapter の登録情報
@dataclass
class DirtyAdapter:
    """A registered dirty adapter with TTL and upgrade path.

    設計原則: 「正確な答えを出すな。壊れない答えを出せ。」
    """

    id: str                              # 一意識別子
    pattern: DAPLPattern                 # パターン分類
    location: str                        # ファイル:関数
    description: str                     # 何をしているか (1行)
    fep_analog: str                      # FEP のどの戦略と同型か
    created: date                        # 作成日
    ttl_months: int                      # TTL (月)
    upgrade_path: str                    # clean 版への移行方法
    silent_failure_risk: SilentFailureRisk
    notes: str = ""                      # 補足

    # PURPOSE: dapl の expires 処理を実行する
    @property
    def expires(self) -> date:
        """TTL 満了日。"""
        return self.created + timedelta(days=self.ttl_months * 30)

    # PURPOSE: dapl の is expired 処理を実行する
    @property
    def is_expired(self) -> bool:
        """TTL を超過しているか。"""
        return date.today() > self.expires

    # PURPOSE: dapl の days remaining 処理を実行する
    @property
    def days_remaining(self) -> int:
        """残り日数 (負 = 超過)。"""
        return (self.expires - date.today()).days


# =============================================================================
# Registry — 登録済み dirty adapter
# =============================================================================

# PURPOSE: 全 dirty adapter の登録簿
DAPL_REGISTRY: List[DirtyAdapter] = [
    DirtyAdapter(
        id="bigram_jaccard",
        pattern=DAPLPattern.ENSEMBLE,
        location="cone_builder.py:compute_dispersion",
        description="SequenceMatcher + bigram Jaccard の max で日本語 V を改善",
        fep_analog="Perceptual inference — 多重予測で予測誤差を抑制",
        created=date(2026, 2, 8),
        ttl_months=12,
        upgrade_path="similarity 関数を semantic embedding (cosine) に差し替え",
        silent_failure_risk=SilentFailureRisk.LOW,
        notes="max は安全側 (類似度が高い方を採用) に倒れる",
    ),
    DirtyAdapter(
        id="fill_penalty",
        pattern=DAPLPattern.PENALTY_MULTIPLIER,
        location="boot_integration.py:postcheck_boot_report",
        description="ε を FILL 残存率で割り引き、テンプレート見出しの誤マッチを減衰",
        fep_analog="Precision weighting — 入力の信頼性が低いとき精度を下げる",
        created=date(2026, 2, 8),
        ttl_months=6,
        upgrade_path="FILL マーカーを構造的にパースし、セクション単位で ε 計算",
        silent_failure_risk=SilentFailureRisk.MEDIUM,
        notes="estimated_total_fills=25 がハードコード。テンプレート変更で陳腐化",
    ),
    DirtyAdapter(
        id="pw_defensive",
        pattern=DAPLPattern.DEFENSIVE_FALLBACK,
        location="cone_builder.py:_parse_pw",
        description="不正な float 値を logging.warning + スキップ (cleaned from silent pass)",
        fep_analog="Active inference — 予測不能な入力を記録した上で無視",
        created=date(2026, 2, 8),
        ttl_months=12,  # cleaned: silent→logging で TTL 延長
        upgrade_path="parse_error count を戻り値に含め、呼び出し側で判断可能にする",
        silent_failure_risk=SilentFailureRisk.LOW,  # cleaned: HIGH→LOW
        notes="2026-02-08 clean化: silent pass→logging.warning。リスク LOW に降格",
    ),
]


# =============================================================================
# Query API
# =============================================================================


# PURPOSE: TTL 超過の adapter を返す
def check_ttl() -> List[DirtyAdapter]:
    """Return adapters whose TTL has expired."""
    return [a for a in DAPL_REGISTRY if a.is_expired]


# PURPOSE: パターン別に adapter を取得
def by_pattern(pattern: DAPLPattern) -> List[DirtyAdapter]:
    """Filter adapters by pattern type."""
    return [a for a in DAPL_REGISTRY if a.pattern == pattern]


# PURPOSE: リスクレベル別に adapter を取得
def by_risk(risk: SilentFailureRisk) -> List[DirtyAdapter]:
    """Filter adapters by silent failure risk."""
    return [a for a in DAPL_REGISTRY if a.silent_failure_risk == risk]


# PURPOSE: 全 adapter の一覧を表示
def list_adapters() -> str:
    """Format all registered adapters for display."""
    lines = [f"DAPL Registry — {len(DAPL_REGISTRY)} adapters"]
    lines.append("=" * 60)

    for a in DAPL_REGISTRY:
        status = "⚠️ EXPIRED" if a.is_expired else f"✅ {a.days_remaining}d remaining"
        risk_icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}[a.silent_failure_risk.value]
        lines.append(f"\n{risk_icon} [{a.id}] ({a.pattern.value})")
        lines.append(f"   📍 {a.location}")
        lines.append(f"   📝 {a.description}")
        lines.append(f"   🧬 FEP: {a.fep_analog}")
        lines.append(f"   ⏰ TTL: {a.ttl_months}mo — {status}")
        lines.append(f"   🔄 Upgrade: {a.upgrade_path}")

    expired = check_ttl()
    if expired:
        lines.append(f"\n🚨 {len(expired)} adapter(s) past TTL!")

    return "\n".join(lines)


# PURPOSE: 新しい adapter を設計するためのガイド
def design_guide(what: str) -> str:
    """Guided questions for designing a new dirty adapter.

    Args:
        what: 何を adapter で橋渡しするか (1行)
    """
    return f"""
DAPL Design Guide — "{what}"
{'=' * 50}

1. この adapter は何を推定しているか？
   → 複数の不完全な推定がある     → Ensemble
   → 入力の信頼度が不明           → PenaltyMultiplier
   → 入力が壊れている可能性がある → DefensiveFallback

2. Silent failure のリスクは？
   → LOW (安全側に倒れる)    → TTL 12ヶ月
   → MEDIUM (定数がある)     → TTL 6ヶ月
   → HIGH (入力を捨てる)     → TTL 3ヶ月 + logging 義務

3. Clean 版のインターフェースは？
   → 同じ関数シグネチャで実装だけ差し替え可能にする

4. FEP のどの戦略と同型か？
   → Perceptual inference (予測の精度を上げる)
   → Precision weighting (入力の信頼性を調整する)
   → Active inference (入力自体を変える)

共通原則: 「正確な答えを出すな。壊れない答えを出せ。」
"""


if __name__ == "__main__":
    print(list_adapters())
