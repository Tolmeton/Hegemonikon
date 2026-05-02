#!/usr/bin/env python3
# PROOF: mekhane/fep/tests/test_coherence_calculator.py
# PURPOSE: fep モジュールの coherence_calculator に対するテスト
"""Tests for coherence_calculator.py — H型自然変換の品質計測

H型 (極反転) での本質保存度 κ を検証する。
"""

import pytest

from mekhane.fep.coherence_calculator import (
    CoherenceResult,
    compute_coherence,
    describe_coherence,
    _extract_key_concepts,
)


# PURPOSE: キー概念抽出のテスト
class TestExtractKeyConcepts:
    """キー概念抽出の正確性を検証。"""

    # PURPOSE: 見出しと太字を抽出できることを検証
    def test_headers_and_bold(self):
        """見出しと太字を概念として抽出する。"""
        text = "## 圏論\n\n**随伴関手**の定義。\n\n## ガロア接続"
        concepts = _extract_key_concepts(text)
        assert "圏論" in concepts
        assert "随伴関手" in concepts
        assert "ガロア接続" in concepts

    # PURPOSE: フォールバック (長い単語) を検証
    def test_fallback_long_words(self):
        """見出し/太字がない場合、長い単語をフォールバック。"""
        text = "this is a simple test with some longer_words and patterns"
        concepts = _extract_key_concepts(text)
        assert len(concepts) > 0

    # PURPOSE: 空テキストのフォールバックを検証
    def test_empty_text(self):
        """空テキストは空リスト。"""
        concepts = _extract_key_concepts("")
        assert concepts == []


# PURPOSE: bidirectional coherence 計算のテスト
class TestComputeCoherence:
    """双方向 TF-IDF coherence の正確性を検証。"""

    # PURPOSE: 同一テキストで κ ≈ 1.0 を検証
    def test_identical_texts(self):
        """同一テキスト → κ ≈ 1.0。"""
        text = "圏論における随伴関手の定義と性質について。ガロア接続は前順序圏の特殊ケース。" * 3
        result = compute_coherence(text, text, method="bidirectional")
        assert result.kappa > 0.9
        assert result.method == "bidirectional"

    # PURPOSE: 完全に異なるテキストで κ が低いことを検証
    def test_completely_different_texts(self):
        """完全に異なるテキスト → κ が低い。"""
        t1 = "圏論における随伴関手の定義と性質を確認した。前順序圏のガロア接続について議論。" * 3
        t2 = "Python のウェブフレームワーク Django について。REST API の設計パターン。" * 3
        result = compute_coherence(t1, t2, method="bidirectional")
        assert result.kappa < 0.5
        assert result.transformed_count > 0

    # PURPOSE: 部分的重複で中間値を検証
    def test_partial_overlap(self):
        """部分的重複 → 中間の κ。"""
        t1 = ("## 圏論の基本\n\n**関手**と**自然変換**の定義。"
              "\n\n一般的な数学の議論。線形代数の復習。")
        t2 = ("## 圏論の応用\n\n**関手**の応用例。"
              "\n\nプログラミングでのモナドの実装。")
        result = compute_coherence(t1, t2, method="bidirectional")
        assert 0.01 < result.kappa < 0.95

    # PURPOSE: 空テキストのエッジケースを検証
    def test_empty_texts(self):
        """両方空 → κ = 1.0。"""
        result = compute_coherence("", "")
        assert result.kappa == 1.0

    # PURPOSE: 片方空テキストのエッジケースを検証
    def test_one_empty(self):
        """片方空 → κ = 0.0。"""
        result = compute_coherence("圏論の基本概念について。" * 5, "")
        assert result.kappa == 0.0


# PURPOSE: concept 法 coherence のテスト
class TestConceptCoherence:
    """概念出現率法の正確性を検証。"""

    # PURPOSE: 共有概念がある場合を検証
    def test_shared_concepts(self):
        """共有概念 → κ > 0。"""
        t1 = "## 圏論\n\n**随伴関手**の定義"
        t2 = "## 圏論の応用\n\n**随伴関手**をプログラミングで使う"
        result = compute_coherence(t1, t2, method="concept")
        assert result.kappa > 0.0
        assert result.method == "concept"
        assert result.preserved_count > 0

    # PURPOSE: 共有概念がない場合を検証
    def test_no_shared_concepts(self):
        """共有概念なし → κ = 0.0。"""
        t1 = "## 圏論\n\n**関手**の定義"
        t2 = "## 料理\n\n**パスタ**の作り方"
        result = compute_coherence(t1, t2, method="concept")
        assert result.kappa == 0.0


# PURPOSE: CoherenceResult プロパティのテスト
class TestCoherenceResultProperties:
    """CoherenceResult のプロパティ検証。"""

    # PURPOSE: loss_rate の計算を検証
    def test_loss_rate(self):
        """loss_rate = 1 - κ。"""
        result = CoherenceResult(kappa=0.7, method="bidirectional")
        assert result.loss_rate == pytest.approx(0.3)

    # PURPOSE: カウントプロパティを検証
    def test_counts(self):
        """preserved_count と transformed_count。"""
        result = CoherenceResult(
            kappa=0.5,
            method="bidirectional",
            preserved_cores=["a", "b"],
            transformed_cores=["c"],
        )
        assert result.preserved_count == 2
        assert result.transformed_count == 1


# PURPOSE: describe_coherence のテスト
class TestDescribeCoherence:
    """人間可読出力の検証。"""

    # PURPOSE: 高 coherence の表示を検証
    def test_high_coherence(self):
        """κ ≥ 0.7 → 🟢。"""
        result = CoherenceResult(
            kappa=0.85,
            method="bidirectional",
            forward_rate=0.9,
            backward_rate=0.8,
            preserved_cores=["圏論", "関手"],
        )
        desc = describe_coherence(result)
        assert "🟢" in desc
        assert "85.0%" in desc

    # PURPOSE: 低 coherence の表示を検証
    def test_low_coherence(self):
        """κ < 0.4 → 🔴。"""
        result = CoherenceResult(
            kappa=0.2,
            method="concept",
            forward_rate=0.1,
            backward_rate=0.3,
            transformed_cores=["失われた概念"],
        )
        desc = describe_coherence(result)
        assert "🔴" in desc
        assert "🔀" in desc
        assert "失われた概念" in desc


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
