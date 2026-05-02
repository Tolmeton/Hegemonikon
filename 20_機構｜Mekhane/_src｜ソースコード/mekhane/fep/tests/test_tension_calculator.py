#!/usr/bin/env python3
# PROOF: mekhane/fep/tests/test_tension_calculator.py
# PURPOSE: fep モジュールの tension_calculator に対するテスト
"""Tests for tension_calculator.py — X型双対の生成的緊張計測

X型 (対角線) での生成的緊張 τ を検証する。
"""

import pytest

from mekhane.fep.tension_calculator import (
    TensionResult,
    compute_tension,
    describe_tension,
    _classify_tension,
    _extract_key_concepts,
)


# PURPOSE: キー概念抽出のテスト
class TestExtractKeyConcepts:
    """キー概念抽出の正確性を検証。"""

    # PURPOSE: 見出しと太字を抽出できることを検証
    def test_headers_and_bold(self):
        """見出しと太字を概念 Set として抽出する。"""
        text = "## 圏論\n\n**随伴関手**の定義。\n\n## ガロア接続"
        concepts = _extract_key_concepts(text)
        assert "圏論" in concepts
        assert "随伴関手" in concepts
        assert "ガロア接続" in concepts
        assert isinstance(concepts, set)

    # PURPOSE: 空テキストで空集合を検証
    def test_empty_text(self):
        """空テキスト → 空集合。"""
        concepts = _extract_key_concepts("")
        assert len(concepts) == 0


# PURPOSE: tension レベル分類のテスト
class TestClassifyTension:
    """τスコアからレベル判定の正確性を検証。"""

    # PURPOSE: 高い τ → high を検証
    def test_high(self):
        assert _classify_tension(0.6) == "high"

    # PURPOSE: 中間 τ → medium を検証
    def test_medium(self):
        assert _classify_tension(0.3) == "medium"

    # PURPOSE: 低い τ → low を検証
    def test_low(self):
        assert _classify_tension(0.1) == "low"

    # PURPOSE: 境界値を検証
    def test_boundaries(self):
        assert _classify_tension(0.5) == "high"
        assert _classify_tension(0.2) == "medium"
        assert _classify_tension(0.0) == "low"


# PURPOSE: TF-IDF tension 計算のテスト
class TestComputeTension:
    """TF-IDF tension の正確性を検証。"""

    # PURPOSE: 同一テキストで τ = low を検証
    def test_identical_texts(self):
        """同一テキスト → divergence ≈ 0 → τ = low。"""
        text = "圏論における随伴関手の定義と性質について。ガロア接続は前順序圏の特殊ケース。" * 3
        result = compute_tension(text, text, method="tfidf")
        assert result.level == "low"
        assert result.divergence < 0.2

    # PURPOSE: 完全に異なるテキストで divergence が高いことを検証
    def test_completely_different_texts(self):
        """完全に異なるテキスト → divergence ≈ 1.0。"""
        t1 = "圏論における随伴関手の定義と性質を確認した。前順序圏のガロア接続について議論。" * 3
        t4 = "Python のウェブフレームワーク Django について。REST API の設計パターン。" * 3
        result = compute_tension(t1, t4, method="tfidf")
        assert result.divergence > 0.5
        assert result.unique_t1_count > 0 or result.unique_t4_count > 0

    # PURPOSE: 部分的重複でいろ平衡な緊張を検証
    def test_balanced_tension(self):
        """部分的重複 → τ > 0 (divergence と convergence の両方が存在)。"""
        t1 = ("## 圏論の理論\n\n**随伴関手**の数学的定義を確認した。"
              "\n\n抽象的な構造の分析。射の合成規則。")
        t4 = ("## 圏論の実装\n\n**随伴関手**をコードで実装した。"
              "\n\nPython のクラス設計。テストの実行結果。")
        result = compute_tension(t1, t4, method="tfidf")
        assert result.tension_score > 0.0
        assert result.shared_count > 0

    # PURPOSE: 空テキストのエッジケースを検証
    def test_empty_texts(self):
        """両方空 → τ = low, divergence = 0。"""
        result = compute_tension("", "")
        assert result.level == "low"
        assert result.tension_score == 0.0

    # PURPOSE: 片方空テキストのエッジケースを検証
    def test_one_empty(self):
        """片方空 → divergence = 1.0, convergence = 0。"""
        result = compute_tension("圏論の基本概念について。" * 5, "")
        assert result.divergence == 1.0
        assert result.convergence == 0.0
        assert result.level == "low"


# PURPOSE: concept 法 tension のテスト
class TestConceptTension:
    """概念集合法の正確性を検証。"""

    # PURPOSE: 完全共有で τ = low を検証
    def test_identical_concepts(self):
        """概念が完全一致 → divergence = 0 → τ = low。"""
        t1 = "## 圏論\n\n**関手**の定義"
        t4 = "## 圏論\n\n**関手**の実装"
        result = compute_tension(t1, t4, method="concept")
        assert result.divergence < 0.5  # 圏論と関手が共有

    # PURPOSE: 完全非共有で divergence 最大を検証
    def test_no_shared_concepts(self):
        """概念が完全不一致 → divergence = 1.0。"""
        t1 = "## 圏論\n\n**関手**の定義"
        t4 = "## 料理\n\n**パスタ**の作り方"
        result = compute_tension(t1, t4, method="concept")
        assert result.divergence == 1.0
        assert result.convergence == 0.0

    # PURPOSE: 部分共有で中間値を検証
    def test_partial_overlap(self):
        """部分共有 → 0 < divergence < 1, 0 < convergence < 1。"""
        t1 = "## 圏論\n\n**関手**と**自然変換**の定義"
        t4 = "## 圏論\n\n**モナド**と**関手**の応用"
        result = compute_tension(t1, t4, method="concept")
        assert 0.0 < result.divergence < 1.0
        assert 0.0 < result.convergence < 1.0


# PURPOSE: TensionResult プロパティのテスト
class TestTensionResultProperties:
    """TensionResult のプロパティ検証。"""

    # PURPOSE: tau プロパティを検証
    def test_tau_property(self):
        """tau = tension_score。"""
        result = TensionResult(
            level="medium", divergence=0.5, convergence=0.5,
            method="tfidf", tension_score=0.35,
        )
        assert result.tau == 0.35

    # PURPOSE: カウントプロパティを検証
    def test_counts(self):
        """unique/shared カウント。"""
        result = TensionResult(
            level="high", divergence=0.7, convergence=0.4,
            method="tfidf", tension_score=0.5,
            unique_to_t1=["a", "b"],
            unique_to_t4=["c"],
            shared_concepts=["d", "e", "f"],
        )
        assert result.unique_t1_count == 2
        assert result.unique_t4_count == 1
        assert result.shared_count == 3


# PURPOSE: describe_tension のテスト
class TestDescribeTension:
    """人間可読出力の検証。"""

    # PURPOSE: 高 tension の表示を検証
    def test_high_tension(self):
        """high → ⚡。"""
        result = TensionResult(
            level="high", divergence=0.6, convergence=0.5,
            method="tfidf", tension_score=0.55,
            shared_concepts=["圏論"],
            unique_to_t1=["理論"],
            unique_to_t4=["実装"],
        )
        desc = describe_tension(result)
        assert "⚡" in desc
        assert "55.0%" in desc
        assert "🔗" in desc
        assert "圏論" in desc

    # PURPOSE: 低 tension の表示を検証
    def test_low_tension(self):
        """low → 🔵。"""
        result = TensionResult(
            level="low", divergence=0.1, convergence=0.1,
            method="concept", tension_score=0.1,
        )
        desc = describe_tension(result)
        assert "🔵" in desc
        assert "Low tension" in desc


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
