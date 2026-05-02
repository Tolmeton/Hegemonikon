# PROOF: [L2/テスト] <- mekhane/ergasterion/digestor/tests/test_selector_quality.py selector品質改善の検証
"""
Digestor Selector 品質テスト

3層防御 (v3) の効果を検証する。
- MockPaper による単体テスト (デフォルト)
- --live フラグで arXiv API 実環境テスト

Usage:
    python -m pytest mekhane/ergasterion/digestor/tests/test_selector_quality.py -v
    python mekhane/ergasterion/digestor/tests/test_selector_quality.py --live
"""

import sys
from dataclasses import dataclass, field
from typing import Optional

import pytest


# ─── Mock Paper ───────────────────────────────────────────

# PURPOSE: Test suite validating mock paper correctness
@dataclass
class MockPaper:
    """テスト用の軽量 Paper"""
    id: str
    title: str
    abstract: str = ""
    source: str = "arxiv"
    categories: list = field(default_factory=list)
    published: Optional[str] = None
    url: Optional[str] = None


# ─── テストデータ ─────────────────────────────────────────

# 明らかに無関係な論文 (層1で排除されるべき)
IRRELEVANT_PAPERS = [
    MockPaper(
        id="dark1",
        title="Dark Matter Distribution in Galaxy Clusters",
        abstract="We study the spatial distribution of dark matter halos "
                 "using N-body simulations. Gravitational lensing effects.",
        categories=["astro-ph.CO"],
    ),
    MockPaper(
        id="chem1",
        title="Synthesis of Novel Organic Compounds for Drug Delivery",
        abstract="We report the synthesis of a new class of organic molecules "
                 "with pharmaceutical applications in targeted cancer therapy.",
        categories=["chem-ph"],
    ),
    MockPaper(
        id="bio1",
        title="Genome-Wide Association Study of Diabetes Risk Factors",
        abstract="A comprehensive GWAS analysis of genetic variants associated "
                 "with type 2 diabetes mellitus in East Asian populations.",
        categories=["q-bio.GN"],
    ),
    MockPaper(
        id="math1",
        title="Prime Number Distribution in Arithmetic Progressions",
        abstract="We prove new bounds on the distribution of primes in "
                 "arithmetic progressions using sieve methods.",
        categories=["math.NT"],
    ),
]

# 関連する論文 (通過すべき)
RELEVANT_PAPERS = [
    MockPaper(
        id="ai1",
        title="Self-Reflective Agents: Metacognition in Large Language Models",
        abstract="We propose a framework for metacognitive self-reflection "
                 "in LLM-based autonomous agents. Our approach uses chain-of-thought "
                 "prompting for improved reasoning and decision making capabilities "
                 "with transformer architectures and attention mechanisms.",
        categories=["cs.AI", "cs.CL"],
    ),
    MockPaper(
        id="fep1",
        title="Active Inference and Free Energy Minimization in Artificial Agents",
        abstract="We formalize active inference using variational free energy "
                 "principle and Bayesian inference for autonomous planning in "
                 "AI agents. The framework connects predictive coding with "
                 "reinforcement learning for cognitive control.",
        categories=["cs.AI", "stat.ML"],
    ),
    MockPaper(
        id="cot1",
        title="Improving Chain-of-Thought Reasoning with Self-Consistency",
        abstract="We present a method for enhancing chain-of-thought reasoning "
                 "in large language models through self-consistency decoding. "
                 "Our approach improves reasoning accuracy and inference quality.",
        categories=["cs.CL"],
    ),
    MockPaper(
        id="stoic1",
        title="Stoic Philosophy and Rational Agent Decision Making",
        abstract="We explore connections between Stoic hegemonikon (ruling faculty) "
                 "and modern AI agent architectures. Virtue ethics provides a "
                 "framework for autonomous agent decision making and moral reasoning.",
        categories=["cs.AI"],
    ),
]

# 境界線上の論文 (カテゴリは許可だがドメイン適合度は中程度)
BORDERLINE_PAPERS = [
    MockPaper(
        id="border1",
        title="Neural Networks for Particle Physics Event Classification",
        abstract="Deep learning applied to high-energy physics experiments. "
                 "We use neural networks and machine learning for event detection.",
        categories=["hep-ex", "cs.LG"],
    ),
]


# ═══════════════════════════════════════════════════════════
# 層1: arXiv カテゴリフィルタ テスト
# ═══════════════════════════════════════════════════════════

# PURPOSE: Test suite validating category filter correctness
class TestCategoryFilter:
    """層1: arXiv カテゴリフィルタの検証"""

    # PURPOSE: Verify irrelevant papers rejected behaves correctly
    def test_irrelevant_papers_rejected(self):
        """無関係分野は全て除外される"""
        from mekhane.ergasterion.digestor.selector import _is_relevant_domain

        for paper in IRRELEVANT_PAPERS:
            assert not _is_relevant_domain(paper), (
                f"{paper.id} ({paper.categories}) should be rejected"
            )

    # PURPOSE: Verify relevant papers accepted behaves correctly
    def test_relevant_papers_accepted(self):
        """関連分野は全て通過する"""
        from mekhane.ergasterion.digestor.selector import _is_relevant_domain

        for paper in RELEVANT_PAPERS:
            assert _is_relevant_domain(paper), (
                f"{paper.id} ({paper.categories}) should be accepted"
            )

    # PURPOSE: Verify no category passes behaves correctly
    def test_no_category_passes(self):
        """カテゴリなしは通す (偽陽性 > 偽陰性)"""
        from mekhane.ergasterion.digestor.selector import _is_relevant_domain

        paper = MockPaper(id="nocat", title="Unknown Source Paper", categories=[])
        assert _is_relevant_domain(paper)

    # PURPOSE: Verify borderline cs lg passes behaves correctly
    def test_borderline_cs_lg_passes(self):
        """cs.LG を持つ論文は通過する"""
        from mekhane.ergasterion.digestor.selector import _is_relevant_domain

        for paper in BORDERLINE_PAPERS:
            assert _is_relevant_domain(paper), (
                f"{paper.id} with cs.LG should pass"
            )


# ═══════════════════════════════════════════════════════════
# 層3: ドメインキーワード テスト
# ═══════════════════════════════════════════════════════════

# PURPOSE: Test suite validating domain relevance correctness
class TestDomainRelevance:
    """層3: ドメインキーワード適合度の検証"""

    # PURPOSE: Verify irrelevant low score behaves correctly
    def test_irrelevant_low_score(self):
        """無関連論文はドメイン適合度が低い"""
        from mekhane.ergasterion.digestor.selector import _domain_relevance

        for paper in IRRELEVANT_PAPERS:
            score = _domain_relevance(paper)
            assert score < 0.34, (
                f"{paper.id} domain_relevance={score:.2f} should be < 0.34"
            )

    # PURPOSE: Verify relevant high score behaves correctly
    def test_relevant_high_score(self):
        """関連論文はドメイン適合度が高い"""
        from mekhane.ergasterion.digestor.selector import _domain_relevance

        for paper in RELEVANT_PAPERS:
            score = _domain_relevance(paper)
            assert score >= 0.67, (
                f"{paper.id} domain_relevance={score:.2f} should be >= 0.67"
            )


# ═══════════════════════════════════════════════════════════
# 統合テスト: select_candidates (keyword mode)
# ═══════════════════════════════════════════════════════════

# PURPOSE: Test suite validating select candidates integration correctness
class TestSelectCandidatesIntegration:
    """統合テスト: keyword モードでの候補選定"""

    # PURPOSE: Verify irrelevant never selected behaves correctly
    def test_irrelevant_never_selected(self):
        """無関係論文は候補に選ばれない"""
        from mekhane.ergasterion.digestor.selector import DigestorSelector

        selector = DigestorSelector(mode="keyword")
        candidates = selector.select_candidates(
            IRRELEVANT_PAPERS, min_score=0.0
        )
        assert len(candidates) == 0, (
            f"Irrelevant papers should produce 0 candidates, got {len(candidates)}: "
            f"{[c.paper.id for c in candidates]}"
        )

    # PURPOSE: Verify mixed only relevant selected behaves correctly
    def test_mixed_only_relevant_selected(self):
        """混合リストから関連論文のみが選ばれる"""
        from mekhane.ergasterion.digestor.selector import DigestorSelector

        all_papers = IRRELEVANT_PAPERS + RELEVANT_PAPERS
        selector = DigestorSelector(mode="keyword")
        candidates = selector.select_candidates(all_papers, min_score=0.0)

        selected_ids = {c.paper.id for c in candidates}
        irrelevant_ids = {p.id for p in IRRELEVANT_PAPERS}

        # 無関連が混入していないか
        leaked = selected_ids & irrelevant_ids
        assert len(leaked) == 0, (
            f"Irrelevant papers leaked into candidates: {leaked}"
        )


# ═══════════════════════════════════════════════════════════
# Live テスト (--live フラグで実行)
# ═══════════════════════════════════════════════════════════

# PURPOSE: Verify run live test behaves correctly
def run_live_test():
    """実 arXiv API で候補を再生成して品質を確認"""
    print("=" * 60)
    print("🔬 Digestor Live Quality Test")
    print("=" * 60)

    from mekhane.ergasterion.digestor.selector import (
        DigestorSelector,
        _is_relevant_domain,
        _domain_relevance,
    )
    from mekhane.ergasterion.digestor.pipeline import DigestorPipeline

    pipeline = DigestorPipeline()
    print("\n[1] Fetching papers from arXiv...")
    papers = pipeline._fetch_from_gnosis(max_papers=30)
    print(f"    Fetched: {len(papers)} papers")

    # 層1 フィルタ適用前後の比較
    before = len(papers)
    filtered = [p for p in papers if _is_relevant_domain(p)]
    after = len(filtered)
    rejected = before - after
    print(f"\n[2] Category Filter: {before} → {after} ({rejected} rejected)")

    for p in papers:
        if not _is_relevant_domain(p):
            cats = getattr(p, "categories", [])
            print(f"    ❌ {p.title[:60]}... ({', '.join(cats)})")

    # 候補選定
    print(f"\n[3] Selecting candidates (keyword mode)...")
    selector = DigestorSelector(mode="keyword")
    candidates = selector.select_candidates(filtered, min_score=0.0)

    print(f"    Candidates: {len(candidates)}")
    for i, c in enumerate(candidates, 1):
        dr = _domain_relevance(c.paper)
        cats = getattr(c.paper, "categories", [])
        print(f"    {i}. [{c.score:.2f}] (domain={dr:.2f}) {c.paper.title[:55]}...")
        print(f"       Topics: {', '.join(c.matched_topics)} | Cat: {', '.join(cats)}")

    # 品質サマリ
    print(f"\n{'=' * 60}")
    print(f"📊 Quality Summary")
    print(f"    Total fetched:    {before}")
    print(f"    Category filter:  -{rejected}")
    print(f"    Candidates:       {len(candidates)}")
    if candidates:
        avg_score = sum(c.score for c in candidates) / len(candidates)
        avg_domain = sum(_domain_relevance(c.paper) for c in candidates) / len(candidates)
        print(f"    Avg score:        {avg_score:.2f}")
        print(f"    Avg domain_rel:   {avg_domain:.2f}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    if "--live" in sys.argv:
        run_live_test()
    else:
        pytest.main([__file__, "-v"])
