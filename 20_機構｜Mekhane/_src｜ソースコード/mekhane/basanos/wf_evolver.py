# PROOF: [L1/定理] <- mekhane/basanos/wf_evolver.py /noe+ autoresearch 分析 L0 prototype
"""
WFEvolver — WF/RULES の進化的最適化エンジン (L0 + L1)

autoresearch パターンの HGK 転用:
- train.py → WF .md files
- val_bpb → wf_quality_score (0.0-1.0)
- results.tsv → wf_evolution_log.jsonl
- keep/discard → score 比較

Phase C: TrendAnalyzer パターンの WF 拡張
  WFProfile = FileProfile と同構造。品質指標は issue 数ではなく構造スコア。
  WFTrendAnalyzer = TrendAnalyzer と同パターン。daily_reviews → wf_reviews。

Phase B (将来): LLM-as-Mutator
  ochema で変異体生成 → hermeneus execute で検証 → keep/discard。

設計原則:
- TrendAnalyzer と同じ: 空データでもクラッシュしない (graceful degradation)
- 合成データでテスト可能 (fixture first)
- 既存インフラを再利用 (paths.py, OUTPUTS_DIR)
"""

import hashlib
import json
import logging
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)

from mekhane.paths import OUTPUTS_DIR, WORKFLOWS_DIR

WF_REVIEWS_DIR = OUTPUTS_DIR / "wf_reviews"
WF_EVOLUTION_LOG = OUTPUTS_DIR / "wf_evolution_log.jsonl"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WFProfile — FileProfile の WF 版
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# PURPOSE: [L2] WFProfile — WF ファイルの品質履歴プロファイル
@dataclass
class WFProfile:
    """WF ファイルの品質履歴プロファイル。FileProfile と同構造。

    FEP 解釈: WF の品質スコアが低下 = 予測誤差が蓄積。
    改善が必要な WF を特定し、進化的最適化の対象にする。
    """

    path: str
    quality_scores: List[float] = field(default_factory=list)  # 日次品質スコア
    first_seen: str = ""
    last_seen: str = ""
    days_tracked: int = 0

    # PURPOSE: [L2] quality — 直近の品質スコア
    @property
    def quality(self) -> float:
        """直近の品質スコア (0.0-1.0)。データなしは 0.0。"""
        if not self.quality_scores:
            return 0.0
        return self.quality_scores[-1]

    # PURPOSE: [L2] trend — 品質の変化傾向
    @property
    def trend(self) -> float:
        """品質の変化傾向。正=改善、負=劣化。線形回帰の傾き。"""
        if len(self.quality_scores) < 2:
            return 0.0

        n = len(self.quality_scores)
        x_mean = (n - 1) / 2.0
        y_mean = sum(self.quality_scores) / n

        numerator = sum(
            (i - x_mean) * (s - y_mean)
            for i, s in enumerate(self.quality_scores)
        )
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0
        return round(numerator / denominator, 4)

    # PURPOSE: [L2] needs_evolution — 進化的最適化の対象かどうか
    @property
    def needs_evolution(self) -> bool:
        """品質が低い or 劣化傾向 → 進化対象。データなしは対象外。"""
        if not self.quality_scores:
            return False
        return self.quality < 0.7 or self.trend < -0.05


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WFQualityScorer — WF の品質を数値化
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# PURPOSE: [L2] WFQualityScorer — WF ファイルの品質をスカラー化
class WFQualityScorer:
    """WF ファイルの品質を 0.0-1.0 のスカラーで数値化。

    autoresearch の val_bpb に相当する品質指標。
    L0 = 構文+構造のみ (LLM 不要)。

    スコア構成:
    - frontmatter (0.30): YAML frontmatter の存在+構造
    - sections (0.25): Markdown section の構造完全性
    - content_density (0.20): 行数の妥当性+内容密度
    - formatting (0.15): Markdown 形式の健全性
    - hash_consistency (0.10): 内容の一意性 (空ファイル検出)
    """

    WEIGHTS = {
        "frontmatter": 0.30,
        "sections": 0.25,
        "content_density": 0.20,
        "formatting": 0.15,
        "hash_consistency": 0.10,
    }

    # PURPOSE: [L2] score — 総合品質スコア
    def score(self, content: str) -> float:
        """総合品質スコア (0.0-1.0)。"""
        if not content or not content.strip():
            return 0.0

        scores = {
            "frontmatter": self.score_frontmatter(content),
            "sections": self.score_sections(content),
            "content_density": self.score_content_density(content),
            "formatting": self.score_formatting(content),
            "hash_consistency": self.score_hash_consistency(content),
        }

        total = sum(
            scores[k] * self.WEIGHTS[k]
            for k in self.WEIGHTS
        )
        return round(min(1.0, max(0.0, total)), 3)

    # PURPOSE: [L2] score_detail — 各項目のスコアを返す
    def score_detail(self, content: str) -> Dict[str, float]:
        """各品質項目のスコアを返す。"""
        if not content or not content.strip():
            return {k: 0.0 for k in self.WEIGHTS}

        return {
            "frontmatter": round(self.score_frontmatter(content), 3),
            "sections": round(self.score_sections(content), 3),
            "content_density": round(self.score_content_density(content), 3),
            "formatting": round(self.score_formatting(content), 3),
            "hash_consistency": round(self.score_hash_consistency(content), 3),
        }

    # PURPOSE: [L2] score_frontmatter — YAML frontmatter チェック
    def score_frontmatter(self, content: str) -> float:
        """YAML frontmatter の品質。"""
        score = 0.0

        # Frontmatter exists?
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                score += 0.4  # frontmatter exists
                try:
                    fm = yaml.safe_load(parts[1])
                    if isinstance(fm, dict):
                        score += 0.2  # valid YAML
                        if "description" in fm:
                            score += 0.2  # has description
                        if "version" in fm or "hegemonikon" in fm:
                            score += 0.2  # has metadata
                except yaml.YAMLError:
                    pass  # Invalid YAML → only 0.4
        return min(1.0, score)

    # PURPOSE: [L2] score_sections — Markdown section 構造チェック
    def score_sections(self, content: str) -> float:
        """Markdown の section 構造の完全性。"""
        lines = content.split("\n")
        headings = [l for l in lines if l.startswith("#")]

        if not headings:
            return 0.2  # No headings at all → minimal

        score = 0.3  # At least some headings

        # h1 exists?
        h1 = [h for h in headings if h.startswith("# ") and not h.startswith("##")]
        if h1:
            score += 0.2

        # h2+ exists (structured document)?
        h2 = [h for h in headings if h.startswith("## ")]
        if len(h2) >= 2:
            score += 0.3

        # Heading hierarchy is consistent (no h4 without h3)?
        levels = []
        for h in headings:
            level = len(h) - len(h.lstrip("#"))
            levels.append(level)

        if levels:
            # Check for gaps (e.g., h1 → h4 without h2/h3)
            gaps = sum(1 for i in range(1, len(levels)) if levels[i] - levels[i-1] > 1)
            if gaps == 0:
                score += 0.2

        return min(1.0, score)

    # PURPOSE: [L2] score_content_density — 内容密度
    def score_content_density(self, content: str) -> float:
        """行数と内容密度の妥当性。"""
        lines = content.strip().split("\n")
        total = len(lines)

        if total < 5:
            return 0.1  # Too short
        if total < 20:
            return 0.4  # Short but functional

        # Non-empty lines ratio
        non_empty = sum(1 for l in lines if l.strip())
        density = non_empty / total if total > 0 else 0

        score = 0.5  # Base for adequate length

        if density > 0.5:
            score += 0.2  # Good density
        if density > 0.7:
            score += 0.1  # Very good density

        # Excessive length penalty (>1000 lines)
        if total > 1000:
            score -= 0.2

        # Has actual content (not just headings/metadata)
        content_lines = [l for l in lines if l.strip() and not l.startswith("#") and not l.startswith("---")]
        if len(content_lines) > 10:
            score += 0.2

        return min(1.0, max(0.0, score))

    # PURPOSE: [L2] score_formatting — Markdown 形式の健全性
    def score_formatting(self, content: str) -> float:
        """Markdown 形式の健全性チェック。"""
        lines = content.split("\n")
        score = 0.6  # Base — most WFs are well-formatted

        # Check for common formatting issues
        issues = 0

        # Triple+ blank lines
        blank_streak = 0
        for line in lines:
            if not line.strip():
                blank_streak += 1
                if blank_streak >= 3:
                    issues += 1
            else:
                blank_streak = 0

        # Unclosed code blocks
        code_block_count = content.count("```")
        if code_block_count % 2 != 0:
            issues += 2  # Major issue

        # Broken links (][) without preceding []
        broken_links = len(re.findall(r'\]\s+\(', content))
        issues += broken_links

        # Score adjustment
        if issues == 0:
            score = 1.0
        else:
            score = max(0.1, score - 0.15 * issues)

        return min(1.0, score)

    # PURPOSE: [L2] score_hash_consistency — 空/重複ファイル検出
    def score_hash_consistency(self, content: str) -> float:
        """内容の一意性。空/テンプレートのみのファイルを検出。"""
        stripped = content.strip()
        if not stripped:
            return 0.0

        # Very short content (< 50 chars) is likely a stub
        if len(stripped) < 50:
            return 0.3

        # Check for template-only content
        if stripped.count("TODO") > 3 or stripped.count("TBD") > 3:
            return 0.4

        return 1.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WFTrendAnalyzer — TrendAnalyzer の WF 版
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# PURPOSE: [L2] WFTrendAnalyzer — WF 品質のトレンド分析
class WFTrendAnalyzer:
    """WF ファイルの品質をトレンド分析する。TrendAnalyzer の WF 版。

    Usage:
        analyzer = WFTrendAnalyzer()
        report = analyzer.scan_workflows()  # 全 WF をスキャン → レポート保存
        profiles = analyzer.wf_profiles()
        weak = analyzer.weak_workflows(threshold=0.7)
    """

    # PURPOSE: [L2] __init__
    def __init__(
        self,
        wf_dir: Path = WORKFLOWS_DIR,
        reviews_dir: Path = WF_REVIEWS_DIR,
        days: int = 14,
    ):
        self.wf_dir = wf_dir
        self.reviews_dir = reviews_dir
        self.days = days
        self.scorer = WFQualityScorer()
        self._reviews: Optional[List[dict]] = None

    # PURPOSE: [L2] scan_workflows — 全 WF をスキャンしてスコア
    def scan_workflows(self) -> Dict[str, float]:
        """WORKFLOWS_DIR 以下の全 .md ファイルをスコアリング。

        Returns:
            {relative_path: quality_score}
        """
        results: Dict[str, float] = {}

        if not self.wf_dir.exists():
            logger.warning(f"Workflow directory not found: {self.wf_dir}")
            return results

        for md_file in sorted(self.wf_dir.rglob("*.md")):
            try:
                content = md_file.read_text("utf-8")
                rel_path = str(md_file.relative_to(self.wf_dir))
                score = self.scorer.score(content)
                results[rel_path] = score
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Failed to score {md_file}: {e}")

        logger.info(f"Scanned {len(results)} WF files")
        return results

    # PURPOSE: [L2] save_review — スキャン結果を日次レポートとして保存
    def save_review(self, scores: Optional[Dict[str, float]] = None) -> Path:
        """スキャン結果を wf_reviews/YYYY-MM-DD.json に保存。"""
        if scores is None:
            scores = self.scan_workflows()

        self.reviews_dir.mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        review_file = self.reviews_dir / f"{today}.json"

        review = {
            "timestamp": datetime.now().isoformat(),
            "wf_count": len(scores),
            "scores": scores,
            "mean_score": round(sum(scores.values()) / max(len(scores), 1), 3),
            "weak_wfs": [
                k for k, v in scores.items() if v < 0.7
            ],
        }

        # Append mode (like DailyReviewPipeline)
        if review_file.exists():
            existing = json.loads(review_file.read_text("utf-8"))
            if isinstance(existing, list):
                existing.append(review)
            else:
                existing = [existing, review]
            review_file.write_text(
                json.dumps(existing, ensure_ascii=False, indent=2), "utf-8"
            )
        else:
            review_file.write_text(
                json.dumps(review, ensure_ascii=False, indent=2), "utf-8"
            )

        logger.info(f"WF review saved: {review_file}")
        return review_file

    # PURPOSE: [L2] load_reviews — 過去N日分のレビューを読込
    def load_reviews(self) -> List[dict]:
        """wf_reviews/ から過去N日分のレビューを読み込む。"""
        if self._reviews is not None:
            return self._reviews

        reviews = []
        if not self.reviews_dir.exists():
            self._reviews = reviews
            return reviews

        cutoff = datetime.now() - timedelta(days=self.days)

        for json_file in sorted(self.reviews_dir.glob("*.json")):
            try:
                date_str = json_file.stem
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date < cutoff:
                    continue

                data = json.loads(json_file.read_text("utf-8"))
                if isinstance(data, dict):
                    data = [data]

                for review in data:
                    review["_date"] = date_str
                    reviews.append(review)

            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Skipping {json_file}: {e}")

        self._reviews = reviews
        logger.info(f"Loaded {len(reviews)} WF reviews")
        return reviews

    # PURPOSE: [L2] wf_profiles — WF 別のプロファイルを集計
    def wf_profiles(self) -> Dict[str, WFProfile]:
        """WF 別の品質プロファイルを集計。"""
        reviews = self.load_reviews()
        profiles: Dict[str, WFProfile] = {}

        for review in reviews:
            date = review.get("_date", "")
            scores = review.get("scores", {})

            for wf_path, score in scores.items():
                if wf_path not in profiles:
                    profiles[wf_path] = WFProfile(
                        path=wf_path,
                        first_seen=date,
                    )

                p = profiles[wf_path]
                p.quality_scores.append(score)
                p.last_seen = max(p.last_seen, date) if p.last_seen else date
                p.days_tracked += 1

        return profiles

    # PURPOSE: [L2] weak_workflows — 品質が低い WF を返す
    def weak_workflows(self, threshold: float = 0.7) -> List[WFProfile]:
        """品質スコア < threshold の WF をスコア昇順で返す。"""
        profiles = self.wf_profiles()
        weak = [p for p in profiles.values() if p.quality < threshold]
        return sorted(weak, key=lambda p: p.quality)

    # PURPOSE: [L2] improving_workflows — 改善傾向の WF
    def improving_workflows(self) -> List[WFProfile]:
        """品質が改善傾向にある WF を返す。"""
        profiles = self.wf_profiles()
        return [p for p in profiles.values() if p.trend > 0.05]

    # PURPOSE: [L2] declining_workflows — 劣化傾向の WF
    def declining_workflows(self) -> List[WFProfile]:
        """品質が劣化傾向にある WF を返す。"""
        profiles = self.wf_profiles()
        return [p for p in profiles.values() if p.trend < -0.05]

    # PURPOSE: [L2] log_evolution — 進化ログを JSONL に追記
    def log_evolution(
        self,
        wf_path: str,
        original_score: float,
        mutated_score: float,
        mutation_type: str,
        kept: bool,
        log_file: Path = WF_EVOLUTION_LOG,
    ) -> None:
        """autoresearch の results.tsv に相当する進化ログ。"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "wf_path": wf_path,
            "original_score": original_score,
            "mutated_score": mutated_score,
            "mutation_type": mutation_type,
            "delta": round(mutated_score - original_score, 4),
            "kept": kept,
        }

        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # PURPOSE: [L2] summary — トレンド分析の要約
    def summary(self) -> str:
        """分析結果の要約テキスト。"""
        reviews = self.load_reviews()
        if not reviews:
            return "📊 WF Trend Analysis: No data available yet."

        profiles = self.wf_profiles()
        weak = self.weak_workflows()
        improving = self.improving_workflows()
        declining = self.declining_workflows()

        # Latest mean score
        latest = reviews[-1] if reviews else {}
        mean = latest.get("mean_score", 0)

        lines = [
            f"📊 WF Trend Analysis ({len(reviews)} reviews, {len(profiles)} WFs tracked)",
            f"   Mean quality: {mean:.2f}",
        ]

        if weak:
            lines.append(f"   ⚠️ Weak WFs ({len(weak)}):")
            for p in weak[:5]:
                lines.append(f"      {p.path} (quality={p.quality:.2f})")

        if declining:
            lines.append(f"   📉 Declining ({len(declining)}):")
            for p in declining[:3]:
                lines.append(f"      {p.path} (trend={p.trend:+.3f})")

        if improving:
            lines.append(f"   📈 Improving ({len(improving)}):")
            for p in improving[:3]:
                lines.append(f"      {p.path} (trend={p.trend:+.3f})")

        return "\n".join(lines)

    # PURPOSE: [L2] evolve — autoresearch ループ (Phase B)
    def evolve(
        self,
        wf_path: str,
        wf_content: str,
        mutation_types: Optional[List[str]] = None,
        log_file: Path = WF_EVOLUTION_LOG,
    ) -> List[Dict[str, Any]]:
        """autoresearch パターンの進化ループ。

        1. 元の WF をスコアリング
        2. 各 mutation_type で変異体を生成 (WFMutator)
        3. 変異体をスコアリング
        4. スコアが改善した変異体を kept=True でログ
        5. 結果を返す

        注意: LLM 呼出は行わない (WFMutator.mutate は同期呼出)。
        LLM 呼出は呼び出し側が ochema 経由で行い、結果を渡す。

        Args:
            wf_path: WF のパス (ログ用)
            wf_content: 元の WF テキスト
            mutation_types: 試す変異タイプのリスト
            log_file: 進化ログの出力先

        Returns:
            各変異体の結果リスト
        """
        if mutation_types is None:
            mutation_types = list(WFMutator.STRATEGIES.keys())

        original_score = self.scorer.score(wf_content)
        results = []

        for mt in mutation_types:
            prompt = WFMutator.build_prompt(wf_content, mt)
            results.append({
                "wf_path": wf_path,
                "mutation_type": mt,
                "original_score": original_score,
                "prompt": prompt,
                "mutated_content": None,  # 呼出側が LLM で埋める
                "mutated_score": None,
                "kept": None,
            })

        return results

    # PURPOSE: [L2] evaluate_mutation — 変異体を評価してログ
    def evaluate_mutation(
        self,
        result: Dict[str, Any],
        mutated_content: str,
        log_file: Path = WF_EVOLUTION_LOG,
    ) -> Dict[str, Any]:
        """LLM が埋めた変異体を評価し、keep/discard を決定。

        Args:
            result: evolve() が返した結果 dict
            mutated_content: LLM が生成した変異 WF テキスト
            log_file: ログファイル

        Returns:
            更新された結果 dict
        """
        mutated_score = self.scorer.score(mutated_content)
        kept = mutated_score > result["original_score"]

        result["mutated_content"] = mutated_content
        result["mutated_score"] = mutated_score
        result["kept"] = kept

        self.log_evolution(
            wf_path=result["wf_path"],
            original_score=result["original_score"],
            mutated_score=mutated_score,
            mutation_type=result["mutation_type"],
            kept=kept,
            log_file=log_file,
        )

        return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WFMutator — LLM ベースの WF 変異体生成 (Phase B)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# PURPOSE: [L2] WFMutator — autoresearch の「train.py 変更」に対応
class WFMutator:
    """WF テキストの変異プロンプトを生成する。

    autoresearch では agent が train.py を直接書き換える。
    HGK では LLM (ochema 経由) にプロンプトを渡し、変異 WF を生成させる。

    WFMutator 自体は LLM を呼ばない。プロンプトを構築するだけ。
    実際の LLM 呼出は呼び出し側 (Claude/Gemini) が ochema MCP 経由で行う。
    """

    STRATEGIES = {
        "clarify": {
            "description": "曖昧なステップを具体化する",
            "instruction": (
                "以下の WF を改善してください。曖昧な指示を具体的にし、"
                "各ステップに明確な完了条件を追加してください。"
                "WF の構造 (frontmatter, headings) は維持してください。"
            ),
        },
        "restructure": {
            "description": "セクション構造を改善する",
            "instruction": (
                "以下の WF のセクション構造を改善してください。"
                "論理的な順序に並び替え、不足しているセクション (前提条件, 出力形式 等) を追加し、"
                "frontmatter の description を改善してください。"
            ),
        },
        "densify": {
            "description": "情報密度を高める",
            "instruction": (
                "以下の WF の情報密度を高めてください。"
                "冗長な文を削除し、箇条書きを活用し、"
                "同じ情報量をより少ない行数で表現してください。"
                "ただし、重要な情報は削除しないでください。"
            ),
        },
        "decompose": {
            "description": "大きなステップを分割する",
            "instruction": (
                "以下の WF の大きなステップを、より小さく実行可能な単位に分割してください。"
                "各ステップは1つのアクションだけを記述し、"
                "ツール呼出がある場合は明示してください。"
            ),
        },
        "strengthen": {
            "description": "品質チェックポイントを追加する",
            "instruction": (
                "以下の WF に品質チェックポイントを追加してください。"
                "各主要ステップの後に検証手順を入れ、"
                "失敗時のフォールバック手順も記述してください。"
            ),
        },
    }

    @classmethod
    def build_prompt(cls, wf_content: str, strategy: str) -> str:
        """変異プロンプトを構築する。

        Args:
            wf_content: 元の WF テキスト
            strategy: 変異戦略名 (clarify, restructure, etc.)

        Returns:
            LLM に渡すプロンプト文字列
        """
        if strategy not in cls.STRATEGIES:
            raise ValueError(
                f"Unknown strategy: {strategy}. "
                f"Available: {list(cls.STRATEGIES.keys())}"
            )

        info = cls.STRATEGIES[strategy]

        return (
            f"{info['instruction']}\n\n"
            f"--- 元の WF ---\n"
            f"{wf_content}\n"
            f"--- /元の WF ---\n\n"
            f"改善した WF のみを出力してください。説明は不要です。"
            f"frontmatter (---) から始めてください。"
        )

    @classmethod
    def available_strategies(cls) -> Dict[str, str]:
        """利用可能な変異戦略の一覧。"""
        return {k: v["description"] for k, v in cls.STRATEGIES.items()}
