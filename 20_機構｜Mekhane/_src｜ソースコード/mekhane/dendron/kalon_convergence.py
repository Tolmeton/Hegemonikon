from __future__ import annotations
# PROOF: [L2/コア] <- mekhane/dendron/kalon_convergence.py
# PURPOSE: check 結果の時系列から G∘F サイクルの収束を Bayesian Beta で判定する
"""
Kalon Convergence — 収束判定エンジン (Layer 2)

check 結果を JSONL で永続化し、時系列の変化から G∘F サイクルの
収束を Bayesian Beta モデルで判定する。

理論的根拠:
- kalon.md §6: Kalon = Fix(G∘F)
  - G = check (存在誤差の検出 = 収束操作)
  - F = 修正 (新コードの発散 = 発散操作)
  - Fix = G∘F の不動点 = check → 修正 → re-check のサイクルが安定

- kalon.md §6.3: Bayesian Beta モデル
  - α = successes + 1 (品質改善の回数)
  - β = failures + 1 (品質悪化の回数)
  - P(θ > 0.5 | α, β) > 0.95 → ◎ (収束 = Fix に到達)

知覚（前提）の質が運動の質を規定する:
  「改善/悪化」の判定に KalonSnapshot.quality_score (複合指標) を使用。
  単一指標 (issue count のみ) への妥協は知的欺瞞。
"""


import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import lgamma, exp, log
from pathlib import Path
from typing import List, Optional


# ─── 履歴エントリ ──────────────────────────────

# PURPOSE: 1回の check 結果を永続化する構造体
@dataclass
class HistoryEntry:
    """JSONL に保存される 1 行分のデータ。"""
    timestamp: str                # ISO 8601
    target: str                   # check 対象のパス
    quality_score: float          # KalonSnapshot.quality_score (0-1)
    coverage: float               # PROOF カバレッジ率
    ept_score: int                # EPT OK 数
    ept_total: int                # EPT 合計数
    ept_ratio: float              # ept_score / ept_total
    weighted_issue_count: int     # issue 総数
    total_stiffness: float        # stiffness 合計
    top_stiff_issues: List[str]   # Top-5 issue の概要


# ─── 収束判定結果 ──────────────────────────────

# PURPOSE: G∘F サイクルの収束判定結果を格納する
@dataclass
class KalonJudgment:
    """Kalon 収束判定の結果。

    verdict:
      ◎ = Fix(G∘F) に到達 (収束)
      ◯ = 許容 (改善傾向だが収束未確認)
      ✗ = 違和感 (悪化傾向または不安定)
    """
    verdict: str                   # "◎" / "◯" / "✗"
    alpha: int                     # Bayesian Beta: α (改善 + 1)
    beta: int                      # Bayesian Beta: β (悪化 + 1)
    convergence_probability: float # P(θ > 0.5 | α, β)
    history_length: int            # 履歴の長さ
    trend: str                     # "improving" / "stable" / "degrading"
    quality_scores: List[float]    # 品質スコアの時系列
    latest_score: float            # 最新の quality_score


# ─── 収束エンジン ──────────────────────────────

# PURPOSE: check 履歴の永続化と Bayesian 収束判定を行うエンジン
class KalonHistory:
    """Kalon 収束エンジン。

    JSONL ファイルに check 結果を蓄積し、
    Bayesian Beta で G∘F サイクルの収束を判定する。
    """

    # PURPOSE: 初期化。履歴ディレクトリを設定する
    def __init__(self, history_dir: Optional[Path] = None):
        """
        Args:
            history_dir: 履歴ファイルの保存先。
                         デフォルトは .dendron/ (check 対象のルート直下)
        """
        self._history_dir = history_dir

    # PURPOSE: check 結果を JSONL に追記する
    def save(
        self,
        target: Path,
        quality_score: float,
        coverage: float,
        ept_score: int,
        ept_total: int,
        ept_ratio: float,
        weighted_issue_count: int,
        total_stiffness: float,
        top_stiff_issues: List[str],
        timestamp: Optional[str] = None,
    ) -> Path:
        """check 結果を JSONL に追記する。

        Args:
            target: check 対象のパス
            その他: KalonSnapshot のフィールド

        Returns:
            保存先ファイルのパス
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        entry = HistoryEntry(
            timestamp=timestamp,
            target=str(target),
            quality_score=quality_score,
            coverage=coverage,
            ept_score=ept_score,
            ept_total=ept_total,
            ept_ratio=ept_ratio,
            weighted_issue_count=weighted_issue_count,
            total_stiffness=total_stiffness,
            top_stiff_issues=top_stiff_issues,
        )

        filepath = self._history_file(target)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

        return filepath

    # PURPOSE: JSONL から履歴を読み込む
    def load(self, target: Path) -> List[HistoryEntry]:
        """JSONL から履歴を読み込む。

        Args:
            target: check 対象のパス

        Returns:
            HistoryEntry のリスト (時系列順)
        """
        filepath = self._history_file(target)
        if not filepath.exists():
            return []

        entries: List[HistoryEntry] = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                entries.append(HistoryEntry(**data))

        return entries

    # PURPOSE: 履歴から G∘F の収束を判定する
    def judge_convergence(self, target: Path) -> KalonJudgment:
        """Bayesian Beta モデルで G∘F サイクルの収束を判定する。

        kalon.md §6.3 の操作的判定:
        1. G (check) → 変化するか? → する = ◯以下 / しない = 次へ
        2. F (修正) → 何が生まれるか? → 何もない = ✗ / 3つ以上 = ◎

        Bayesian Beta:
        - 連続する2回の check で quality_score が改善 → success
        - quality_score が悪化 → failure
        - P(θ > 0.5 | α, β) > 0.95 → ◎

        Returns:
            KalonJudgment
        """
        entries = self.load(target)
        quality_scores = [e.quality_score for e in entries]

        if len(entries) < 2:
            return KalonJudgment(
                verdict="◯",
                alpha=1,
                beta=1,
                convergence_probability=0.5,
                history_length=len(entries),
                trend="insufficient_data",
                quality_scores=quality_scores,
                latest_score=quality_scores[-1] if quality_scores else 0.0,
            )

        # 連続ペアの比較: quality_score の増減
        # IMPROVEMENT_THRESHOLD: 1% 未満の変化はノイズとみなし無視する
        # 理由: 浮動小数点誤差 (~1e-15) と本質的改善を区別するため
        IMPROVEMENT_THRESHOLD = 0.01
        successes = 0
        failures = 0
        for i in range(1, len(quality_scores)):
            if quality_scores[i] > quality_scores[i - 1] + IMPROVEMENT_THRESHOLD:
                successes += 1
            elif quality_scores[i] < quality_scores[i - 1] - IMPROVEMENT_THRESHOLD:
                failures += 1
            # 閾値内の変化はカウントしない (安定 or ノイズ)

        alpha = successes + 1
        beta_param = failures + 1

        # P(θ > 0.5 | α, β) = 1 - I(0.5; α, β) — 正則化不完全ベータ関数
        conv_prob = 1.0 - _regularized_incomplete_beta(0.5, alpha, beta_param)

        # トレンド判定
        if len(quality_scores) >= 3:
            recent = quality_scores[-3:]
            if recent[-1] > recent[0] + 0.01:
                trend = "improving"
            elif recent[-1] < recent[0] - 0.01:
                trend = "degrading"
            else:
                trend = "stable"
        else:
            trend = "improving" if successes > failures else "degrading"

        # 判定
        if conv_prob > 0.95 and len(entries) >= 3:
            verdict = "◎"
        elif conv_prob >= 0.5:
            verdict = "◯"
        else:
            verdict = "✗"

        return KalonJudgment(
            verdict=verdict,
            alpha=alpha,
            beta=beta_param,
            convergence_probability=conv_prob,
            history_length=len(entries),
            trend=trend,
            quality_scores=quality_scores,
            latest_score=quality_scores[-1],
        )

    # PURPOSE: 判定結果を人間に読めるレポートにフォーマットする
    @staticmethod
    def format_report(judgment: KalonJudgment) -> str:
        """判定結果のテキストレポート。"""
        lines = [
            "=" * 50,
            "Kalon 収束判定 (G∘F Convergence)",
            "=" * 50,
            "",
            f"判定: {judgment.verdict}  (P(θ>0.5) = {judgment.convergence_probability:.3f})",
            f"Bayesian Beta: α={judgment.alpha}, β={judgment.beta}",
            f"トレンド: {judgment.trend}",
            f"履歴: {judgment.history_length} 回の check",
            f"最新スコア: {judgment.latest_score:.3f}",
            "",
        ]

        if judgment.quality_scores:
            lines.append("品質スコア推移:")
            for i, score in enumerate(judgment.quality_scores):
                bar = "█" * int(score * 30)
                lines.append(f"  [{i+1:2d}] {score:.3f} {bar}")
            lines.append("")

        # 判定の解釈
        if judgment.verdict == "◎":
            lines.append("→ Fix(G∘F) に到達。check → 修正のサイクルが安定した。")
        elif judgment.verdict == "◯":
            lines.append("→ 改善傾向だが収束未確認。check → 修正を継続すべき。")
        else:
            lines.append("→ 悪化傾向または不安定。戦略の見直しが必要。")

        return "\n".join(lines)

    # ─── 内部ヘルパー ──────────────────────────────

    # PURPOSE: 履歴ファイルのパスを決定する（SHA256 で衝突を防止）
    def _history_file(self, target: Path) -> Path:
        """履歴 JSONL ファイルのパス。

        パス名を SHA256 ハッシュに変換して衝突を防止する。
        デバッグ用にパスの末尾コンポーネントも先頭に付ける。
        """
        if self._history_dir:
            base = self._history_dir
        else:
            base = Path(target) / ".dendron"
        # SHA256 で一意性を保証（replace ベースでは `/test/project` と `_test_project` が衝突する）
        target_str = str(target)
        path_hash = hashlib.sha256(target_str.encode("utf-8")).hexdigest()[:12]
        stem = Path(target_str).stem or "root"
        return base / f"kalon_history_{stem}_{path_hash}.jsonl"


# ─── Bayesian Beta ヘルパー ──────────────────────────────

# PURPOSE: 正則化不完全ベータ関数 I(x; a, b) を計算する (scipy 不要の実装)
def _regularized_incomplete_beta(x: float, a: int, b: int) -> float:
    """正則化不完全ベータ関数 I(x; a, b)。

    scipy.special.betainc の代替で、整数パラメータの場合に
    閉じた形で計算できる。numpy/scipy への依存を避ける。

    I(x; a, b) = Σ_{j=a}^{a+b-1} C(a+b-1, j) * x^j * (1-x)^(a+b-1-j)

    Args:
        x: 評価点 (0-1)
        a: α パラメータ (正整数)
        b: β パラメータ (正整数)

    Returns:
        I(x; a, b) ∈ [0, 1]
    """
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0

    # 整数の場合の閉じた形式: 二項級数
    n = a + b - 1
    total = 0.0
    for j in range(a, n + 1):
        log_binom = _log_binomial(n, j)
        log_term = log_binom + j * log(x) + (n - j) * log(1.0 - x)
        total += exp(log_term)

    return total


# PURPOSE: log(C(n, k)) を計算する (オーバーフロー対策)
def _log_binomial(n: int, k: int) -> float:
    """log(C(n, k)) = log(n!) - log(k!) - log((n-k)!)"""
    return lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1)
