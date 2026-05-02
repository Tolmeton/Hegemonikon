from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/fep/ X型双対の tension (τ) を計算する
"""
Tension Calculator — X型双対の生成的緊張計測

Origin: CategoryEngine v4.1 (2026-03-11)
Mathematical Basis: τ ∈ {low, medium, high} — X型対角の生成性

X型双対 = 対角線上の完全対極ペア (例: Noēsis ↔ Energeia)
対極のテキスト間の「生成的緊張」を計測する。

良い X型対話は:
    1. 十分な divergence (独自の語彙空間がある)
    2. 意味のある convergence (共有する核心がある)
    3. この二つの緊張から新しい洞察が生まれる

Design symmetry:
    drift_calculator:      source + compressed → DriftResult (情報損失)
    coherence_calculator:  text_t1 + text_t2  → CoherenceResult (本質保存)
    tension_calculator:    text_t1 + text_t4  → TensionResult (生成的緊張)
"""


import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from mekhane.fep.drift_calculator import (
    _build_vocabulary,
    _char_ngrams,
    _cosine_similarity,
    _idf_weights,
    _normalize_text,
    _split_into_chunks,
    _tfidf_vector,
)


# =============================================================================
# TensionResult — 「対極の緊張から何が生まれるか」
# =============================================================================


# PURPOSE: X型双対の生成的緊張を表す統一的インターフェース
@dataclass
class TensionResult:
    """X型双対 (対角線) の生成的緊張計測結果。

    Category-theoretic interpretation:
        divergence = T1 と T4 の語彙空間の非重複度
        convergence = 共有核心の深さ
        τ = 発散と収束の緊張から生まれる生成性
        novel_terms = T1∩T4 にはない T1∪T4 の固有概念
    """

    level: str  # "low", "medium", "high"
    divergence: float  # 発散度 ∈ [0, 1]. 語彙の非重複率
    convergence: float  # 収束度 ∈ [0, 1]. 共有核心の類似度
    method: str  # "tfidf" or "concept"
    unique_to_t1: List[str] = field(default_factory=list)
    unique_to_t4: List[str] = field(default_factory=list)
    shared_concepts: List[str] = field(default_factory=list)
    tension_score: float = 0.0  # τ ∈ [0, 1]. 生成的緊張の定量値

    # PURPOSE: τスコアを返す (level の定量版)
    @property
    def tau(self) -> float:
        """τ ∈ [0, 1]. 生成的緊張の定量値。"""
        return self.tension_score

    # PURPOSE: T1 固有概念の数を返す
    @property
    def unique_t1_count(self) -> int:
        return len(self.unique_to_t1)

    # PURPOSE: T4 固有概念の数を返す
    @property
    def unique_t4_count(self) -> int:
        return len(self.unique_to_t4)

    # PURPOSE: 共有概念の数を返す
    @property
    def shared_count(self) -> int:
        return len(self.shared_concepts)


# =============================================================================
# キー概念抽出 (coherence_calculator と同一ロジック)
# =============================================================================


# PURPOSE: テキストからキー概念を抽出する
def _extract_key_concepts(text: str) -> Set[str]:
    """テキストからキー概念を抽出し Set で返す。

    Markdown の見出しと太字をキー概念として扱う。
    見つからない場合は長い単語をフォールバックとして使用。
    """
    headers = re.findall(r'^#{1,4}\s+(.+)$', text, re.MULTILINE)
    bold = re.findall(r'\*\*(.+?)\*\*', text)
    concepts = set(h.strip().lower() for h in headers + bold if h.strip())

    if not concepts:
        words = set(re.findall(r'\b\w{4,}\b', _normalize_text(text)))
        concepts = set(sorted(words)[:30])

    return concepts


# =============================================================================
# Tension 計算: TF-IDF 法
# =============================================================================


# PURPOSE: X型双対の tension を計算する
def compute_tension(
    text_t1: str,
    text_t4: str,
    *,
    method: str = "tfidf",
    ngram_sizes: Tuple[int, ...] = (2, 3),
) -> TensionResult:
    """X型双対の生成的緊張 (τ) を計算する。

    Category-theoretic interpretation:
        T1 と T4 は対角線上の完全対極
        良い緊張 = 十分な発散 + 意味のある収束
        τ = f(divergence, convergence)
        divergence のみ高い → 無関係 (τ = low)
        convergence のみ高い → 同一 (τ = low)
        両方適度 → 生成的緊張 (τ = high)

    Args:
        text_t1: T1 側のテキスト (例: Noēsis の出力)
        text_t4: T4 側のテキスト (例: Energeia の出力)
        method: "tfidf" (TF-IDF) or "concept" (概念集合)
        ngram_sizes: 文字 n-gram のサイズ

    Returns:
        TensionResult with τ level, 発散度, 収束度, 固有/共有概念
    """
    if method == "concept":
        return _compute_concept_tension(text_t1, text_t4)
    return _compute_tfidf_tension(text_t1, text_t4, ngram_sizes)


# PURPOSE: TF-IDF で tension を計算する
def _compute_tfidf_tension(
    text_t1: str,
    text_t4: str,
    ngram_sizes: Tuple[int, ...],
) -> TensionResult:
    """TF-IDF cosine similarity による tension 計算。

    全体の cosine similarity で convergence を測り、
    チャンク単位の非一致率で divergence を測る。
    """
    chunks_t1 = _split_into_chunks(text_t1)
    chunks_t4 = _split_into_chunks(text_t4)

    # エッジケース
    if not chunks_t1 and not chunks_t4:
        return TensionResult(
            level="low", divergence=0.0, convergence=1.0,
            method="tfidf", tension_score=0.0,
        )
    if not chunks_t1 or not chunks_t4:
        return TensionResult(
            level="low", divergence=1.0, convergence=0.0,
            method="tfidf", tension_score=0.0,
        )

    # 共通語彙構築
    all_docs = chunks_t1 + chunks_t4
    vocabulary = _build_vocabulary(all_docs, ngram_sizes)

    if not vocabulary:
        return TensionResult(
            level="low", divergence=0.5, convergence=0.5,
            method="tfidf", tension_score=0.0,
        )

    # IDF 計算
    idf = _idf_weights(all_docs, vocabulary, ngram_sizes)

    # 全体テキストの TF-IDF ベクトル → convergence
    vec_t1 = _tfidf_vector(text_t1, vocabulary, idf, ngram_sizes)
    vec_t4 = _tfidf_vector(text_t4, vocabulary, idf, ngram_sizes)
    global_sim = _cosine_similarity(vec_t1, vec_t4)
    convergence = round(global_sim, 3)

    # チャンク単位のクロス類似度 → divergence
    t4_vectors = [
        _tfidf_vector(chunk, vocabulary, idf, ngram_sizes)
        for chunk in chunks_t4
    ]

    low_match_count = 0
    for src_chunk in chunks_t1:
        src_vector = _tfidf_vector(src_chunk, vocabulary, idf, ngram_sizes)
        max_sim = max(
            _cosine_similarity(src_vector, tgt_vec)
            for tgt_vec in t4_vectors
        )
        if max_sim < 0.3:
            low_match_count += 1

    divergence = round(low_match_count / len(chunks_t1), 3) if chunks_t1 else 0.0

    # 概念レベルの固有/共有分析
    concepts_t1 = _extract_key_concepts(text_t1)
    concepts_t4 = _extract_key_concepts(text_t4)
    shared = sorted(concepts_t1 & concepts_t4)
    unique_t1 = sorted(concepts_t1 - concepts_t4)
    unique_t4 = sorted(concepts_t4 - concepts_t1)

    # τ = 生成的緊張 = divergence と convergence の幾何平均
    # 両方が適度に高いときに τ が最大になる
    tension_score = round(2.0 * divergence * convergence / (divergence + convergence), 3) \
        if (divergence + convergence) > 0 else 0.0

    # レベル判定
    level = _classify_tension(tension_score)

    return TensionResult(
        level=level,
        divergence=divergence,
        convergence=convergence,
        method="tfidf",
        unique_to_t1=unique_t1[:10],
        unique_to_t4=unique_t4[:10],
        shared_concepts=shared[:10],
        tension_score=max(0.0, min(1.0, tension_score)),
    )


# =============================================================================
# Tension 計算: 概念集合法 (軽量フォールバック)
# =============================================================================


# PURPOSE: キー概念の集合演算で tension を計算する
def _compute_concept_tension(
    text_t1: str,
    text_t4: str,
) -> TensionResult:
    """キー概念の集合演算による tension 計算 (軽量)。

    divergence = |T1△T4| / |T1∪T4| (対称差)
    convergence = |T1∩T4| / |T1∪T4| (Jaccard 類似度)
    """
    concepts_t1 = _extract_key_concepts(text_t1)
    concepts_t4 = _extract_key_concepts(text_t4)

    # エッジケース
    if not concepts_t1 and not concepts_t4:
        return TensionResult(
            level="low", divergence=0.0, convergence=1.0,
            method="concept", tension_score=0.0,
        )

    union = concepts_t1 | concepts_t4
    if not union:
        return TensionResult(
            level="low", divergence=0.0, convergence=0.0,
            method="concept", tension_score=0.0,
        )

    shared = concepts_t1 & concepts_t4
    symmetric_diff = concepts_t1 ^ concepts_t4

    divergence = round(len(symmetric_diff) / len(union), 3)
    convergence = round(len(shared) / len(union), 3)

    # τ = 調和平均
    tension_score = round(2.0 * divergence * convergence / (divergence + convergence), 3) \
        if (divergence + convergence) > 0 else 0.0

    level = _classify_tension(tension_score)

    return TensionResult(
        level=level,
        divergence=divergence,
        convergence=convergence,
        method="concept",
        unique_to_t1=sorted(concepts_t1 - concepts_t4)[:10],
        unique_to_t4=sorted(concepts_t4 - concepts_t1)[:10],
        shared_concepts=sorted(shared)[:10],
        tension_score=max(0.0, min(1.0, tension_score)),
    )


# =============================================================================
# ユーティリティ
# =============================================================================


# PURPOSE: τスコアからレベルを判定する
def _classify_tension(score: float) -> str:
    """τスコアから low/medium/high を判定。

    幾何学的閾値:
        low < 0.2: 対極間に緊張がない (無関係 or 同一)
        0.2 ≤ medium < 0.5: 適度な緊張
        high ≥ 0.5: 強い生成的緊張
    """
    if score >= 0.5:
        return "high"
    elif score >= 0.2:
        return "medium"
    return "low"


# =============================================================================
# 表示 (drift_calculator.describe_drift と対称)
# =============================================================================


# PURPOSE: tension の人間可読な説明を生成する
def describe_tension(result: TensionResult) -> str:
    """人間可読な tension 計測結果。

    drift_calculator.describe_drift() と対称。
    """
    level_emoji = {"low": "🔵", "medium": "🟡", "high": "⚡"}
    emoji = level_emoji.get(result.level, "🔵")

    lines = [
        f"⚡ Tension Measurement (method: {result.method})",
        f"  τ (tension):   {result.tension_score:.1%} [{result.level}]",
        f"  Divergence:    {result.divergence:.1%}",
        f"  Convergence:   {result.convergence:.1%}",
        f"  Unique to T1:  {result.unique_t1_count} concepts",
        f"  Unique to T4:  {result.unique_t4_count} concepts",
        f"  Shared:        {result.shared_count} concepts",
    ]

    # レベル表示
    if result.level == "high":
        lines.append(f"  {emoji} High tension — strong generative potential")
    elif result.level == "medium":
        lines.append(f"  {emoji} Moderate tension — some generative potential")
    else:
        lines.append(f"  {emoji} Low tension — weak generative potential")

    # 共有概念
    if result.shared_concepts:
        lines.append("")
        lines.append("  Shared core concepts:")
        for concept in result.shared_concepts[:5]:
            lines.append(f"    🔗 {concept}")

    # T1 固有
    if result.unique_to_t1:
        lines.append("")
        lines.append("  Unique to T1:")
        for concept in result.unique_to_t1[:5]:
            lines.append(f"    ◀ {concept}")

    # T4 固有
    if result.unique_to_t4:
        lines.append("")
        lines.append("  Unique to T4:")
        for concept in result.unique_to_t4[:5]:
            lines.append(f"    ▶ {concept}")

    return "\n".join(lines)


# =============================================================================
# CLI エントリポイント
# =============================================================================


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) < 3:
        print("Usage: python tension_calculator.py <text_t1_file> <text_t4_file>")
        print("Example: python tension_calculator.py noesis_output.md energeia_output.md")
        sys.exit(1)

    t1_path = Path(sys.argv[1])
    t4_path = Path(sys.argv[2])

    if not t1_path.exists() or not t4_path.exists():
        print("Error: file not found")
        sys.exit(1)

    t1_text = t1_path.read_text(encoding="utf-8")
    t4_text = t4_path.read_text(encoding="utf-8")

    result = compute_tension(t1_text, t4_text)
    print(describe_tension(result))
