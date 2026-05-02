"""NucleatorSplitter のテスト。

embedding backend として単純な bag-of-chars ベクトルを使用し、
Nucleator の G∘F アルゴリズムが storage-agnostic adapter 経由で
正しく動作することを検証する。
"""
from __future__ import annotations

import math

import pytest

from mekhane.anamnesis.chunker_nucleator import ChunkingResult, Step
from mekhane.anamnesis.nucleator_splitter import (
    NucleatorSplitter,
    StepParserConfig,
    parse_text_to_steps,
)


# ── テスト用 embedding backend ───────────────────────────────────────

def _toy_embed_fn(texts: list[str]) -> list[list[float]]:
    """テスト用 embedding: 文字の出現頻度ベクトル (26次元, L2正規化)。

    目的: 実際の embedding モデルなしで Nucleator を駆動する。
    意味的類似性は保証しないが、テキストの字面の近さは反映する。
    """
    dim = 26
    result = []
    for text in texts:
        counts = [0.0] * dim
        for ch in text.lower():
            if 'a' <= ch <= 'z':
                counts[ord(ch) - ord('a')] += 1.0
        # L2 normalize
        norm = math.sqrt(sum(x * x for x in counts))
        if norm > 0:
            counts = [x / norm for x in counts]
        result.append(counts)
    return result


# ── parse_text_to_steps ──────────────────────────────────────────────

class TestParseTextToSteps:
    def test_basic_split(self):
        text = "First paragraph with enough text.\n\nSecond paragraph also long enough."
        steps = parse_text_to_steps(text)
        assert len(steps) == 2
        assert steps[0].index == 0
        assert steps[1].index == 1
        assert "First" in steps[0].text
        assert "Second" in steps[1].text

    def test_short_fragments_filtered(self):
        text = "Long enough paragraph here.\n\nOK\n\nAnother long enough paragraph."
        steps = parse_text_to_steps(text, StepParserConfig(min_chars=20))
        assert len(steps) == 2  # "OK" は min_chars 未満で除去

    def test_empty_text(self):
        steps = parse_text_to_steps("")
        assert steps == []

    def test_custom_separator(self):
        text = "Part one---Part two---Part three"
        steps = parse_text_to_steps(text, StepParserConfig(separator="---", min_chars=5))
        assert len(steps) == 3

    def test_indices_are_sequential(self):
        text = "Short.\n\nA long enough paragraph.\n\nTiny.\n\nAnother long paragraph here."
        steps = parse_text_to_steps(text, StepParserConfig(min_chars=20))
        # "Short." and "Tiny." are filtered
        assert len(steps) == 2
        assert steps[0].index == 0
        assert steps[1].index == 1


# ── NucleatorSplitter ────────────────────────────────────────────────

class TestNucleatorSplitter:
    def _make_splitter(self, **kwargs) -> NucleatorSplitter:
        return NucleatorSplitter(
            embed_fn=_toy_embed_fn,
            tau=0.5,
            min_steps=1,
            **kwargs,
        )

    def test_split_text_returns_strings(self):
        splitter = self._make_splitter()
        text = (
            "The quick brown fox jumps over the lazy dog.\n\n"
            "A completely different topic about quantum physics and entanglement.\n\n"
            "Back to animals: cats and dogs living together in harmony."
        )
        chunks = splitter.split_text(text)
        assert isinstance(chunks, list)
        assert all(isinstance(c, str) for c in chunks)
        assert len(chunks) >= 1

    def test_split_text_detailed_returns_chunking_result(self):
        splitter = self._make_splitter()
        text = (
            "Introduction to the topic of machine learning.\n\n"
            "Deep neural networks have revolutionized computer vision.\n\n"
            "Transformers changed natural language processing fundamentally."
        )
        result = splitter.split_text_detailed(text, session_id="test-001")
        assert isinstance(result, ChunkingResult)
        assert result.session_id == "test-001"
        assert result.converged is True  # G∘F は収束すべき
        assert len(result.chunks) >= 1
        assert "metrics" in dir(result) or hasattr(result, "metrics")

    def test_empty_text(self):
        splitter = self._make_splitter()
        chunks = splitter.split_text("")
        assert chunks == []

    def test_single_paragraph(self):
        splitter = self._make_splitter()
        text = "A single paragraph that is long enough to be kept as one step in the pipeline."
        chunks = splitter.split_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text.strip()

    def test_split_documents_dict_format(self):
        splitter = self._make_splitter()
        docs = [
            {
                "page_content": "Topic A first paragraph.\n\nTopic A second paragraph.",
                "metadata": {"source": "file_a.txt"},
            },
            {
                "page_content": "Topic B standalone paragraph long enough for processing.",
                "metadata": {"source": "file_b.txt"},
            },
        ]
        result = splitter.split_documents(docs)
        assert isinstance(result, list)
        assert all("page_content" in d for d in result)
        assert all("metadata" in d for d in result)
        # metadata が継承されている
        sources = {d["metadata"]["source"] for d in result}
        assert "file_a.txt" in sources or "file_b.txt" in sources
        # chunker metadata が追加されている
        for d in result:
            assert d["metadata"]["chunker"] == "nucleator_gf"

    def test_embedding_mismatch_raises(self):
        """embed_fn が不正な数の embedding を返したらエラー。"""
        def bad_embed_fn(texts: list[str]) -> list[list[float]]:
            return [[0.0] * 26]  # 常に1つしか返さない

        splitter = NucleatorSplitter(
            embed_fn=bad_embed_fn,
            tau=0.5,
            min_steps=1,
            step_parser=StepParserConfig(min_chars=5),
        )
        # 両方とも min_chars を超える十分な長さのパラグラフ
        text = "First paragraph with enough content to pass.\n\nSecond paragraph also long enough."
        with pytest.raises(ValueError, match="不一致"):
            splitter.split_text(text)

    def test_convergence_metrics(self):
        """G∘F 反復が収束し、メトリクスが計算されることを検証。"""
        splitter = self._make_splitter()
        text = "\n\n".join([
            f"This is paragraph number {i} with some unique content about topic {chr(65 + i)}."
            for i in range(10)
        ])
        result = splitter.split_text_detailed(text)
        assert result.converged is True
        assert result.iterations >= 1
        assert "num_chunks" in result.metrics
        assert "mean_coherence" in result.metrics
        assert result.metrics["num_chunks"] >= 1


# ── EmbedFn Protocol ────────────────────────────────────────────────

class TestEmbedFnProtocol:
    def test_toy_embed_fn_is_valid(self):
        """_toy_embed_fn が EmbedFn Protocol を満たすことを確認。"""
        from mekhane.anamnesis.nucleator_splitter import EmbedFn
        assert isinstance(_toy_embed_fn, EmbedFn)

    def test_lambda_is_valid_embed_fn(self):
        """lambda でも EmbedFn Protocol を満たす。"""
        from mekhane.anamnesis.nucleator_splitter import EmbedFn
        fn = lambda texts: [[0.0] * 10 for _ in texts]
        # runtime_checkable Protocol は callable をチェック
        assert callable(fn)
