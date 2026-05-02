from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/fep/ H型自然変換の coherence (κ) を計算する
"""
Coherence Calculator — H型自然変換の品質計測

Origin: CategoryEngine v4.1 (2026-03-11)
Mathematical Basis: κ ∈ [0,1] — H型切替時の本質保存度

H型自然変換 = 同一 Flow 上での極反転 (例: Noēsis ↔ Boulēsis)
極を切り替えても「核心」が保存され、かつ切替で豊穣になるかを計測する。

κ(T1, T2) = (preservation_1→2 + preservation_2→1) / 2

ここで preservation = T1 のキー概念が T2 に出現する割合

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
# CoherenceResult — 「切り替えても本質が残るか」
# =============================================================================


# PURPOSE: H型自然変換の品質を表す統一的インターフェース
@dataclass
class CoherenceResult:
    """H型自然変換 (極反転) の品質計測結果。

    Category-theoretic interpretation:
        κ = 自然変換の「自然性」の定量化
        preserved_cores = η の像 (保存された核心概念)
        transformed_cores = 極反転で変容した概念
    """

    kappa: float  # κ ∈ [0, 1]. 0 = 完全喪失, 1 = 完全保存
    method: str  # "bidirectional" or "concept"
    preserved_cores: List[str] = field(default_factory=list)
    transformed_cores: List[str] = field(default_factory=list)
    forward_rate: float = 0.0  # T1→T2 保存率
    backward_rate: float = 0.0  # T2→T1 保存率
    concept_scores: Dict[str, float] = field(default_factory=dict)

    # PURPOSE: 非保存率を返す
    @property
    def loss_rate(self) -> float:
        """1 - κ. 切替で失われた本質の割合。"""
        return 1.0 - self.kappa

    # PURPOSE: 保存された核心の数を返す
    @property
    def preserved_count(self) -> int:
        return len(self.preserved_cores)

    # PURPOSE: 変容した核心の数を返す
    @property
    def transformed_count(self) -> int:
        return len(self.transformed_cores)


# =============================================================================
# キー概念抽出
# =============================================================================


# PURPOSE: テキストからキー概念 (見出し + 太字) を抽出する
def _extract_key_concepts(text: str) -> List[str]:
    """テキストからキー概念を抽出する。

    Markdown の見出しと太字をキー概念として扱う。
    見つからない場合は長い単語をフォールバックとして使用。
    """
    # 見出し
    headers = re.findall(r'^#{1,4}\s+(.+)$', text, re.MULTILINE)
    # 太字
    bold = re.findall(r'\*\*(.+?)\*\*', text)
    # 重複除去 (順序保持)
    concepts = list(dict.fromkeys(headers + bold))

    if not concepts:
        # フォールバック: 4文字以上の単語を概念として扱う
        words = set(re.findall(r'\b\w{4,}\b', _normalize_text(text)))
        concepts = sorted(words)[:30]

    return concepts


# =============================================================================
# Coherence 計算: 双方向 TF-IDF 法
# =============================================================================


# PURPOSE: H型自然変換の coherence を計算する
def compute_coherence(
    text_t1: str,
    text_t2: str,
    *,
    method: str = "bidirectional",
    threshold: float = 0.3,
    ngram_sizes: Tuple[int, ...] = (2, 3),
) -> CoherenceResult:
    """H型自然変換の coherence (κ) を計算する。

    Category-theoretic interpretation:
        T1 と T2 は同一 Flow 上の異なる極 (極反転)
        κ = 双方向の本質保存率の平均
        高い κ = 自然変換が「自然」(本質を保存している)

    Args:
        text_t1: T1 側のテキスト (例: Noēsis の出力)
        text_t2: T2 側のテキスト (例: Boulēsis の出力)
        method: "bidirectional" (TF-IDF双方向) or "concept" (概念出現率)
        threshold: 類似度閾値
        ngram_sizes: 文字 n-gram のサイズ

    Returns:
        CoherenceResult with κ, 保存された核心, 変容した核心
    """
    if method == "concept":
        return _compute_concept_coherence(text_t1, text_t2)
    return _compute_bidirectional_coherence(
        text_t1, text_t2, threshold, ngram_sizes
    )


# PURPOSE: TF-IDF 双方向での coherence を計算する
def _compute_bidirectional_coherence(
    text_t1: str,
    text_t2: str,
    threshold: float,
    ngram_sizes: Tuple[int, ...],
) -> CoherenceResult:
    """TF-IDF cosine similarity による双方向 coherence 計算。

    T1→T2 と T2→T1 の両方向で各チャンクの最大類似度を計算し、
    その平均を κ とする。
    """
    chunks_t1 = _split_into_chunks(text_t1)
    chunks_t2 = _split_into_chunks(text_t2)

    # エッジケース処理
    if not chunks_t1 and not chunks_t2:
        return CoherenceResult(kappa=1.0, method="bidirectional")
    if not chunks_t1 or not chunks_t2:
        return CoherenceResult(kappa=0.0, method="bidirectional")

    # 共通語彙構築
    all_docs = chunks_t1 + chunks_t2
    vocabulary = _build_vocabulary(all_docs, ngram_sizes)

    if not vocabulary:
        return CoherenceResult(kappa=0.5, method="bidirectional")

    # IDF 計算
    idf = _idf_weights(all_docs, vocabulary, ngram_sizes)

    # T1→T2 方向: T1 の各チャンクが T2 にどれだけ保存されるか
    forward_scores = _directional_similarity(
        chunks_t1, chunks_t2, vocabulary, idf, ngram_sizes
    )
    forward_rate = (
        sum(forward_scores.values()) / len(forward_scores)
        if forward_scores
        else 0.0
    )

    # T2→T1 方向: T2 の各チャンクが T1 にどれだけ反映されるか
    backward_scores = _directional_similarity(
        chunks_t2, chunks_t1, vocabulary, idf, ngram_sizes
    )
    backward_rate = (
        sum(backward_scores.values()) / len(backward_scores)
        if backward_scores
        else 0.0
    )

    # κ = 双方向平均
    kappa = round((forward_rate + backward_rate) / 2.0, 3)

    # 保存 vs 変容の分類
    preserved: List[str] = []
    transformed: List[str] = []
    for display, score in forward_scores.items():
        if score >= threshold:
            preserved.append(display)
        else:
            transformed.append(display)

    return CoherenceResult(
        kappa=max(0.0, min(1.0, kappa)),
        method="bidirectional",
        preserved_cores=preserved,
        transformed_cores=transformed,
        forward_rate=round(forward_rate, 3),
        backward_rate=round(backward_rate, 3),
        concept_scores=forward_scores,
    )


# PURPOSE: 片方向のチャンク類似度を計算する
def _directional_similarity(
    source_chunks: List[str],
    target_chunks: List[str],
    vocabulary: List[str],
    idf: List[float],
    ngram_sizes: Tuple[int, ...],
) -> Dict[str, float]:
    """source の各チャンクと target の最大類似度を返す。"""
    target_vectors = [
        _tfidf_vector(chunk, vocabulary, idf, ngram_sizes)
        for chunk in target_chunks
    ]

    scores: Dict[str, float] = {}
    for src_chunk in source_chunks:
        src_vector = _tfidf_vector(src_chunk, vocabulary, idf, ngram_sizes)
        max_sim = max(
            _cosine_similarity(src_vector, tgt_vec)
            for tgt_vec in target_vectors
        )
        # 表示用に truncate
        display = src_chunk[:80].replace('\n', ' ')
        if len(src_chunk) > 80:
            display += "..."
        scores[display] = round(max_sim, 3)

    return scores


# =============================================================================
# Coherence 計算: 概念出現率法 (軽量フォールバック)
# =============================================================================


# PURPOSE: キー概念の出現率で coherence を計算する
def _compute_concept_coherence(
    text_t1: str,
    text_t2: str,
) -> CoherenceResult:
    """キー概念の双方向出現率による coherence 計算 (軽量)。

    T1 のキー概念が T2 に出現する割合と、
    T2 のキー概念が T1 に出現する割合の平均。
    """
    concepts_t1 = _extract_key_concepts(text_t1)
    concepts_t2 = _extract_key_concepts(text_t2)

    if not concepts_t1 and not concepts_t2:
        return CoherenceResult(kappa=1.0, method="concept")
    if not concepts_t1 or not concepts_t2:
        return CoherenceResult(kappa=0.0, method="concept")

    t2_lower = text_t2.lower()
    t1_lower = text_t1.lower()

    # T1→T2 方向
    fwd_preserved: List[str] = []
    fwd_transformed: List[str] = []
    fwd_scores: Dict[str, float] = {}
    for concept in concepts_t1:
        if concept.lower() in t2_lower:
            fwd_preserved.append(concept)
            fwd_scores[concept] = 1.0
        else:
            fwd_transformed.append(concept)
            fwd_scores[concept] = 0.0

    forward_rate = len(fwd_preserved) / len(concepts_t1) if concepts_t1 else 0.0

    # T2→T1 方向
    bwd_count = sum(1 for c in concepts_t2 if c.lower() in t1_lower)
    backward_rate = bwd_count / len(concepts_t2) if concepts_t2 else 0.0

    kappa = round((forward_rate + backward_rate) / 2.0, 3)

    return CoherenceResult(
        kappa=max(0.0, min(1.0, kappa)),
        method="concept",
        preserved_cores=fwd_preserved,
        transformed_cores=fwd_transformed,
        forward_rate=round(forward_rate, 3),
        backward_rate=round(backward_rate, 3),
        concept_scores=fwd_scores,
    )


# =============================================================================
# 表示 (drift_calculator.describe_drift と対称)
# =============================================================================


# PURPOSE: coherence の人間可読な説明を生成する
def describe_coherence(result: CoherenceResult) -> str:
    """人間可読な coherence 計測結果。

    drift_calculator.describe_drift() と対称。
    """
    lines = [
        f"🔄 Coherence Measurement (method: {result.method})",
        f"  κ (coherence): {result.kappa:.1%}",
        f"  Forward rate:  {result.forward_rate:.1%} (T1→T2)",
        f"  Backward rate: {result.backward_rate:.1%} (T2→T1)",
        f"  Preserved:     {result.preserved_count} cores",
        f"  Transformed:   {result.transformed_count} cores",
    ]

    # κ レベル表示
    if result.kappa >= 0.7:
        lines.append("  🟢 High coherence — essence well preserved")
    elif result.kappa >= 0.4:
        lines.append("  🟡 Moderate coherence — partial preservation")
    else:
        lines.append("  🔴 Low coherence — significant essence loss")

    # 保存された核心
    if result.preserved_cores:
        lines.append("")
        lines.append("  Preserved cores:")
        for core in result.preserved_cores[:5]:
            lines.append(f"    ✅ {core}")

    # 変容した核心
    if result.transformed_cores:
        lines.append("")
        lines.append("  Transformed cores:")
        for core in result.transformed_cores[:5]:
            lines.append(f"    🔀 {core}")

    return "\n".join(lines)


# =============================================================================
# CLI エントリポイント
# =============================================================================


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) < 3:
        print("Usage: python coherence_calculator.py <text_t1_file> <text_t2_file>")
        print("Example: python coherence_calculator.py noesis_output.md boulesis_output.md")
        sys.exit(1)

    t1_path = Path(sys.argv[1])
    t2_path = Path(sys.argv[2])

    if not t1_path.exists() or not t2_path.exists():
        print("Error: file not found")
        sys.exit(1)

    t1_text = t1_path.read_text(encoding="utf-8")
    t2_text = t2_path.read_text(encoding="utf-8")

    result = compute_coherence(t1_text, t2_text)
    print(describe_coherence(result))
