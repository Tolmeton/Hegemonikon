"""Hyphē Session Log Chunker — 理論実証 PoC v0.5.

PURPOSE: linkage_hyphe.md §3-§3.6 の Hyphē 理論に基づき、
セッションログを意味的チャンクに自動分割する。

理論→実装マッピング:
  ρ_MB (§3.3)  → 隣接ステップの cosine similarity (proxy)
  τ (§3.4)     → 類似度閾値 (§3.4a: φ(ρ) でスケール変換)
  L(c) (§3.6)  → Drift + EFE 2項分解 (epistemic + pragmatic)
  F (§3 Write) → 短チャンク merge (発散)
  G (§3 Read)  → 低 coherence 再分割 (収束)
  Fix(G∘F)     → 境界が不変になるまで反復
  precision    → λ(ρ) の逆像: 1 - λ(ρ) (§3.5 + Stoll2026 N3)

PROOF: linkage_hyphe.md §3.6
  L(c) = λ₁·‖G∘F(c)-c‖² + λ₂·(-EFE(c))
  EFE(c) = α·I_epistemic(c) + (1-α)·I_pragmatic(c)

  v0.4 改善 (EFE 精度向上):
    I_epistemic: cos proxy → k-NN 密度差分 Δρ (KL の高次近似)
    I_pragmatic: boundary_novelty → knowledge_edges degree×weight (AY 直接計測)
    λ₁, λ₂: 固定 0.5 → τ 依存スケジュール (§3.5 λ(ρ) モデル整合)

  v0.5 追加 (precision gradient):
    precision(ρ) = 1 - λ(ρ) = 1 - (a + b·exp(-β·ρ))
    Stoll2026 N3: embedding 層の深度 ∝ precision (浅い=explore, 深い=exploit)
    λ₁, λ₂ を precision-aware に微調整

  v0.9 追加 (multilayer precision):
    precision_ml: bge-m3 浅層↔深層 cos sim ベースの独立精度信号
    coherence と独立 (r=-0.27, N=13), k-NN とは条件付き相関
    統合 precision = w * precision_knn + (1-w) * precision_ml
"""

from __future__ import annotations

import heapq
import logging
import math

import numpy as np
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ── データ構造 ──────────────────────────────────────────────────────

@dataclass
class Step:
    """セッションログの1ステップ (## 🤖 Assistant/Claude 区切り)。"""
    index: int
    text: str
    tools: list[str] = field(default_factory=list)

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def line_count(self) -> int:
        return self.text.count("\n") + 1


@dataclass
class Chunk:
    """意味的チャンク — 連続する Step のグループ。"""
    chunk_id: int
    steps: list[Step]
    coherence: float = 0.0           # チャンク内平均類似度
    boundary_novelty: float = 0.0    # 境界での novelty
    drift: float = 0.0               # L(c) Drift 項 = centroid variance
    epistemic: float = 0.0           # I_epistemic = surprise (§3.6 EFE 第1項)
    pragmatic: float = 0.0           # I_pragmatic = boundary contrast (§3.6 EFE 第2項)
    efe: float = 0.0                 # EFE(c) = α·epistemic + (1-α)·pragmatic
    loss: float = 0.0                # L(c) = λ₁·drift + λ₂·(-EFE)
    precision: float = 0.0           # 統合 precision (k-NN + multilayer/ensemble)
    precision_ml: float = 0.0        # multilayer precision: bge-m3 浅↔深 cos sim (v0.9)
    precision_ensemble: float = 0.0  # ensemble precision: Qwen3×Gemini RSA (v1.0)
    precision_result: "PrecisionResult | None" = None  # 構造化 precision 結果 (v1.0)
    topic: str = ""                   # 推定トピック名

    @property
    def step_range(self) -> tuple[int, int]:
        """(開始step index, 終了step index)。"""
        if not self.steps:
            return (0, 0)
        return (self.steps[0].index, self.steps[-1].index)

    @property
    def text(self) -> str:
        """全ステップのテキストを結合。"""
        return "\n\n".join(s.text for s in self.steps)

    def __len__(self) -> int:
        return len(self.steps)


@dataclass
class PrecisionResult:
    """チャンクの precision 計算結果 (CacheBlend HKVD 原理の同型対応)。

    3層パイプライン:
      L1 kNN: ρ_eff quantile 正規化 (ベースライン)
      L2 multilayer: bge-m3 浅↔深 cos sim (v0.9 互換)
      L3 ensemble: Qwen3 × Gemini RSA 行相関 (v1.0 主力)

    CacheBlend との対応 (同型であって同一ではない):
      KV deviation ≅ 1 - precision (cross-attention 不足度)
      HKVD tokens ≅ low-precision chunks (集中的処理が必要)
      gradual filtering ≅ ensemble RSA (複数信号源の統計的集約)

    PROOF: implementation_plan.md §Hyphē × CacheBlend 設計思想
    """
    knn: float           # L1: ρ_eff quantile 正規化 [0, 1]
    multilayer: float    # L2: bge-m3 浅↔深 (0.0 if unavailable)
    ensemble: float      # L3: RSA 行相関 (0.0 if unavailable)
    integrated: float    # 統合値 (w * best + (1-w) * knn)
    gate_label: str      # "high" / "mid" / "low"

    @property
    def recompute_ratio(self) -> float:
        """precision → 再計算率 (連続値)。

        CacheBlend HKVD 原理の同型: precision が低いほど再処理が必要。
        数値は Hyphē 実験で校正。CacheBlend の r*=15% は直接適用しない。
        """
        return 1.0 - self.integrated

    @property
    def layers_available(self) -> int:
        """利用可能な precision 層数 (1-3)。"""
        count = 1  # kNN は常に利用可能
        if self.multilayer > 0.0:
            count += 1
        if self.ensemble > 0.0:
            count += 1
        return count


@dataclass
class LambdaNormalizationMeta:
    """λ計算の正規化メタデータ。cross-session 比較用。

    compute_lambda_schedule が使用した正規化パラメータを記録する。
    異なるセッション間で λ 値を比較する際に、このメタデータを
    normalize_lambda_cross_session に渡すことで再正規化が可能。
    """
    tau_raw: float              # クリップ前の元 τ 値
    tau_min: float = 0.6        # 使用した正規化範囲の下限
    tau_max: float = 0.8        # 使用した正規化範囲の上限
    precision: float | None = None  # precision 修飾に使われた値 (None = 未使用)
    lambda1: float = 0.5        # 計算結果 λ₁
    lambda2: float = 0.5        # 計算結果 λ₂


@dataclass
class ChunkingResult:
    """チャンク化の最終結果。"""
    session_id: str
    chunks: list[Chunk]
    iterations: int = 0              # G∘F 反復回数
    converged: bool = False          # Fix 到達したか
    similarity_trace: list[float] = field(default_factory=list)  # 隣接類似度列
    tau: float = 0.0                 # 使用した τ
    metrics: dict = field(default_factory=dict)
    lambda_meta: LambdaNormalizationMeta | None = None  # cross-session 比較用メタデータ


# ── パーサー ────────────────────────────────────────────────────────

# 🤖 Assistant / Claude のマーカーパターン (conv/ は Claude を使用)
_STEP_PATTERN = re.compile(r"^## 🤖 (?:Assistant|Claude)", re.MULTILINE)


def parse_session(text: str) -> list[Step]:
    """セッションログを Step に分割する。

    ## 🤖 Assistant/Claude マーカーで区切り、
    各ブロックをテキスト + ツール情報として抽出。
    """
    # ヘッダー部分 (最初の ## 🤖 Assistant/Claude の前) をスキップ
    splits = _STEP_PATTERN.split(text)

    steps = []
    # splits[0] はヘッダー。splits[1:] が各ステップ
    for i, block in enumerate(splits[1:], start=0):
        # 先頭の "()\n\n" 部分を除去
        block = re.sub(r"^\s*\([^)]*\)\s*\n*", "", block).strip()
        if not block:
            continue

        # ツール使用の検出
        tools = re.findall(r"🔧 `([^`]+)`", block)

        steps.append(Step(index=i, text=block, tools=tools))

    return steps


def parse_session_file(path: Path) -> tuple[str, list[Step]]:
    """ファイルからセッションを読み込む。session_id と Step[] を返す。"""
    text = path.read_text(encoding="utf-8")
    # session_id をファイル名から抽出 (session_XXXXX_YYYY.md → XXXXX)
    match = re.search(r"session_([a-f0-9]{8})", path.name)
    session_id = match.group(1) if match else path.stem
    return session_id, parse_session(text)


# ── 類似度計算 ──────────────────────────────────────────────────────

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """2ベクトルの cosine similarity。L2 正規化済み前提。"""
    dot = sum(x * y for x, y in zip(a, b))
    return max(0.0, min(1.0, dot))


def _l2_normalize(vec: list[float]) -> list[float]:
    """L2 正規化。"""
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return vec
    return [x / norm for x in vec]


def compute_similarity_trace(
    embeddings: list[list[float]],
    mode: str = "pairwise",
    k: int = 5,
) -> list[float]:
    """ステップ間の類似度トレースを計算。

    mode:
      'pairwise' — 隣接 (i, i+1) のみ。1次マルコフ仮定。
      'knn'      — 前後 k ステップの平均類似度。非線形テキスト対応。

    返り値: similarities[i] = step_i と step_{i+1} 間の類似度 (pairwise)
            または step_i の近傍平均類似度 (knn)。
            長さ = len(embeddings) - 1
    """
    if len(embeddings) < 2:
        return []

    # L2 正規化
    normed = [_l2_normalize(e) for e in embeddings]

    if mode == "knn":
        return _compute_knn_trace(normed, k=k)

    # pairwise (デフォルト)
    similarities = []
    for i in range(len(normed) - 1):
        sim = _cosine_similarity(normed[i], normed[i + 1])
        similarities.append(sim)

    return similarities


def _compute_knn_trace(
    normed: list[list[float]],
    k: int = 5,
) -> list[float]:
    """k-nearest 類似度トレース。

    各遷移 (i, i+1) について、step_i の前後 k ステップと
    step_{i+1} の前後 k ステップの間の平均類似度を計算。
    1次マルコフ仮定を緩和し、非線形テキストの境界検出を改善。

    理論: Nucleator §8 残存課題 #1 への対応。
    局所窓 [i-k, i+k] 内の平均類似度が急落する箇所 = 構造的境界。
    """
    n = len(normed)
    similarities = []

    for i in range(n - 1):
        # step_i 側の窓: [max(0, i-k+1), i]
        # step_{i+1} 側の窓: [i+1, min(n-1, i+k)]
        left_window = range(max(0, i - k + 1), i + 1)
        right_window = range(i + 1, min(n, i + k + 1))

        # 左窓と右窓の全ペア類似度の平均
        cross_sims = []
        for li in left_window:
            for ri in right_window:
                cross_sims.append(_cosine_similarity(normed[li], normed[ri]))

        sim = sum(cross_sims) / len(cross_sims) if cross_sims else 0.0
        similarities.append(sim)

    return similarities


# ── 境界検出 (???izer の回答) ────────────────────────────────────────

def detect_boundaries(
    similarities: list[float],
    tau: float = 0.7,
) -> list[int]:
    """類似度が τ を下回るインデックスを境界として返す。

    similarities[i] = sim(step_i, step_{i+1})
    返り値: 境界インデックス (step_{boundary} と step_{boundary+1} の間が切れる)

    linkage_hyphe.md §3.4: τ = 自律性出現の臨界密度
    ここでは ρ_MB の proxy として cosine similarity を使用。
    τ を下回る = MB 境界が存在 = チャンクの切れ目。
    """
    boundaries = []
    for i, sim in enumerate(similarities):
        if sim < tau:
            boundaries.append(i)
    return boundaries


def steps_to_chunks(
    steps: list[Step],
    boundaries: list[int],
) -> list[Chunk]:
    """ステップ列と境界リストからチャンクを生成。

    boundaries[k] = i は step_i と step_{i+1} の間に境界があることを示す。
    """
    if not steps:
        return []

    # 境界をソートして重複排除
    bounds = sorted(set(boundaries))

    chunks = []
    chunk_id = 0
    start = 0

    for b in bounds:
        # step[start] ... step[b] が1チャンク
        end = b + 1
        if end > start and end <= len(steps):
            chunks.append(Chunk(
                chunk_id=chunk_id,
                steps=steps[start:end],
            ))
            chunk_id += 1
            start = end

    # 残りのステップ
    if start < len(steps):
        chunks.append(Chunk(
            chunk_id=chunk_id,
            steps=steps[start:],
        ))

    return chunks


# ── G∘F 反復 ────────────────────────────────────────────────────────

def _merge_small_chunks(
    chunks: list[Chunk],
    min_steps: int = 2,
) -> list[Chunk]:
    """F 操作: 短すぎるチャンクを隣接チャンクに merge (発散 → 結合)。

    linkage_hyphe.md §3: F(K) = リンク追加 (index_op)
    ここでは「小さすぎるセグメントを隣接に統合」で近似。
    """
    if len(chunks) <= 1:
        return chunks

    merged = []
    i = 0
    while i < len(chunks):
        current = chunks[i]
        # 短すぎるチャンクは次のチャンクに merge
        if len(current) < min_steps and i + 1 < len(chunks):
            next_chunk = chunks[i + 1]
            combined = Chunk(
                chunk_id=current.chunk_id,
                steps=current.steps + next_chunk.steps,
            )
            merged.append(combined)
            i += 2  # 次のも消費
        elif len(current) < min_steps and merged:
            # 最後のチャンクが短い場合は前に merge
            merged[-1] = Chunk(
                chunk_id=merged[-1].chunk_id,
                steps=merged[-1].steps + current.steps,
            )
            i += 1
        else:
            merged.append(current)
            i += 1

    return merged


def _split_incoherent_chunks(
    chunks: list[Chunk],
    embeddings: list[list[float]],
    tau: float = 0.7,
    min_steps: int = 2,
) -> list[Chunk]:
    """G 操作: 低 coherence チャンクを再帰的に再分割 (収束 → 蒸留)。

    linkage_hyphe.md §3: G(K) = 有用部分に蒸留 (search-distill)
    チャンク内の連続類似度が τ を下回る**全箇所**で分割。
    v2: 1箇所のみ → 全箇所に改善 (G∘F 積極化)。
    """
    result = []
    for chunk in chunks:
        sub_chunks = _recursive_split(chunk, embeddings, tau, min_steps)
        result.extend(sub_chunks)
    return result


def _recursive_split(
    chunk: Chunk,
    embeddings: list[list[float]],
    tau: float,
    min_steps: int,
) -> list[Chunk]:
    """1つのチャンクを τ 未満の全箇所で再帰的に分割する。"""
    if len(chunk) < min_steps * 2:
        return [chunk]

    # チャンク内の隣接類似度を計算
    step_indices = [s.index for s in chunk.steps]
    chunk_embeddings = [embeddings[idx] for idx in step_indices]
    internal_sims = compute_similarity_trace(chunk_embeddings)

    if not internal_sims:
        return [chunk]

    # τ 未満の最低類似度箇所を探す
    min_sim = min(internal_sims)
    min_idx = internal_sims.index(min_sim)

    # 分割条件: τ未満 かつ 両側が min_steps 以上
    if min_sim >= tau:
        return [chunk]
    if min_idx < min_steps - 1 or (len(chunk) - min_idx - 1) < min_steps:
        return [chunk]

    # 分割
    split_point = min_idx + 1
    chunk_a = Chunk(
        chunk_id=chunk.chunk_id,
        steps=chunk.steps[:split_point],
    )
    chunk_b = Chunk(
        chunk_id=chunk.chunk_id + 1,
        steps=chunk.steps[split_point:],
    )

    # 再帰的に各半分をさらに分割
    left = _recursive_split(chunk_a, embeddings, tau, min_steps)
    right = _recursive_split(chunk_b, embeddings, tau, min_steps)

    return left + right


def _renumber_chunks(chunks: list[Chunk]) -> list[Chunk]:
    """チャンク ID を連番に振り直す。"""
    for i, chunk in enumerate(chunks):
        chunk.chunk_id = i
    return chunks


def gf_iterate(
    chunks: list[Chunk],
    embeddings: list[list[float]],
    tau: float = 0.7,
    min_steps: int = 2,
    max_iterations: int = 10,
) -> tuple[list[Chunk], int, bool]:
    """G∘F を反復して Fix(G∘F) に収束させる。

    linkage_hyphe.md §3: Fix(G∘F) = リンクを足して蒸留しても変わらない
    = 全ての有用な境界が存在し、全ての境界が有用

    Returns: (chunks, iterations, converged)
    """
    prev_boundaries = _extract_boundaries(chunks)

    for iteration in range(max_iterations):
        # F: merge small chunks (発散 → 結合)
        chunks = _merge_small_chunks(chunks, min_steps=min_steps)
        # G: split incoherent chunks (収束 → 蒸留)
        chunks = _split_incoherent_chunks(chunks, embeddings, tau=tau, min_steps=min_steps)
        chunks = _renumber_chunks(chunks)

        # Fix 判定: 境界が変化しなければ停止
        current_boundaries = _extract_boundaries(chunks)
        if current_boundaries == prev_boundaries:
            return chunks, iteration + 1, True

        prev_boundaries = current_boundaries

    return chunks, max_iterations, False


def _extract_boundaries(chunks: list[Chunk]) -> list[int]:
    """チャンク列から境界インデックスを抽出。"""
    boundaries = []
    for chunk in chunks:
        if chunk.steps:
            boundaries.append(chunk.steps[-1].index)
    return boundaries


# ── PCA 次元削減 (precision 計算用) ─────────────────────────────────


def _pca_reduce(
    embeddings: list[list[float]],
    n_components: int = 16,
) -> list[list[float]]:
    """PCA で embedding を低次元に射影 (precision 用密度計算の前処理)。

    FEP 根拠: 高次元 embedding の anisotropy を排除し、
    有効成分のみで k-NN 密度を計算することで precision の弁別力を回復する。

    Gram matrix ベース: n×n (ステップ数 ≈ 50) なので d×d (768²) より効率的。
    O(n²d + n³) — n << d の場合に最適。

    Args:
        embeddings: L2 正規化済み embedding のリスト (n × d)
        n_components: 射影先の次元数

    Returns:
        射影済み embedding のリスト (n × n_components)
    """
    n = len(embeddings)
    if n <= 1 or n_components <= 0:
        return embeddings

    # n_components は n を超えない
    k = min(n_components, n)

    # numpy 配列に変換
    X = np.array(embeddings, dtype=np.float64)  # (n, d)

    # 平均中心化
    mean = X.mean(axis=0)
    X_centered = X - mean

    # Gram matrix: K = X_centered @ X_centered.T  (n × n)
    K = X_centered @ X_centered.T

    # 固有値分解 (対称行列 → eigh)
    eigenvalues, eigenvectors = np.linalg.eigh(K)

    # eigh は昇順 → 降順に反転
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    # 上位 k 成分を選択
    # 主成分 = X_centered.T @ eigenvectors[:, :k] / sqrt(eigenvalues[:k])
    # 射影 = X_centered @ 主成分 = eigenvectors[:, :k] * sqrt(eigenvalues[:k])
    # ただし表現としては eigenvectors[:, :k] だけで距離構造を保存
    selected = eigenvectors[:, :k]  # (n, k)

    # 固有値でスケーリング (分散を保存)
    scale = np.sqrt(np.maximum(eigenvalues[:k], 0.0))
    projected = selected * scale  # (n, k)

    logger.debug(
        "PCA: %d → %d dim, 説明率 %.1f%%",
        X.shape[1], k,
        100.0 * eigenvalues[:k].sum() / max(eigenvalues.sum(), 1e-12),
    )

    return projected.tolist()


# ── L(c) 計算 (Drift + EFE 2項分解) ────────────────────────────────


def _compute_knn_density(
    normed: list[list[float]],
    k: int = 5,
) -> list[float]:
    """各ステップの k-NN 密度を計算。

    ρ_i = (1/k) · Σ_{j ∈ kNN(i)} cos(i, j)
    密度が高い = 近傍に似たステップが多い = MB 内部。

    返り値: len(normed) の密度リスト ∈ [0, 1]
    """
    n = len(normed)
    if n <= k:
        # ステップ数が k 以下 → 全ペアの平均を返す
        if n <= 1:
            return [1.0] * n
        densities = []
        for i in range(n):
            sims = [
                _cosine_similarity(normed[i], normed[j])
                for j in range(n) if j != i
            ]
            densities.append(sum(sims) / len(sims))
        return densities

    densities = []
    for i in range(n):
        # 全ステップとの類似度を計算し、上位 k 個の平均
        # heapq.nlargest は O(n log k) — ソートの O(n log n) より効率的
        sims = [
            _cosine_similarity(normed[i], normed[j])
            for j in range(n) if j != i
        ]
        top_k = heapq.nlargest(k, sims)
        densities.append(sum(top_k) / len(top_k))

    return densities


def _compute_epistemic_density(
    normed: list[list[float]],
    step_indices: list[int],
    k: int = 5,
    *,
    precomputed_densities: list[float] | None = None,
) -> float:
    """I_epistemic = チャンクによる密度場の変形量。

    linkage_hyphe.md §3.6: KL[P(world|c) ‖ P(world)] の proxy。
    「c を読むとモデルが変わるか」を密度差分で測定。

    1. 全ステップの k-NN 密度 ρ_i を計算
    2. チャンク内ステップの平均密度 ρ_in を計算
    3. チャンク外ステップの平均密度 ρ_out を計算
    4. epistemic = |ρ_in - ρ_out| / max(ρ_in, ρ_out, ε)
       密度が大きく異なる → 情報量が高い (surprise)

    返り値: ∈ [0, 1]。密度差が大きいほど epistemic value が高い。
    """
    n = len(normed)
    if n <= 1:
        return 0.0

    densities = precomputed_densities or _compute_knn_density(normed, k=k)

    # チャンク内/外の密度平均
    step_set = set(step_indices)
    rho_in_vals = [densities[i] for i in step_indices if i < n]
    rho_out_vals = [densities[i] for i in range(n) if i not in step_set]

    if not rho_in_vals or not rho_out_vals:
        return 0.0

    rho_in = sum(rho_in_vals) / len(rho_in_vals)
    rho_out = sum(rho_out_vals) / len(rho_out_vals)

    # 正規化された密度差分
    denom = max(rho_in, rho_out, 1e-8)
    epistemic = abs(rho_in - rho_out) / denom

    return min(1.0, epistemic)


def compute_lambda_schedule(
    tau: float,
    precision: float | None = None,
    *,
    tau_min: float = 0.6,
    tau_max: float = 0.8,
) -> tuple[float, float, LambdaNormalizationMeta]:
    """τ (および precision) に応じて λ₁, λ₂ を調整する。

    linkage_hyphe.md §3.5: λ(ρ) = a + b·exp(-β·ρ)
    高τ → Drift は自動的に小さい → λ₂ (EFE) を上げる
    低τ → Drift が支配的 → λ₁ (Drift) を上げる

    v0.5: precision が渡された場合、precision-aware 微調整を適用:
      高 precision → λ₂ (EFE) をさらに重視 (構造安定 → 展開可能性を評価)
      低 precision → λ₁ (Drift) をさらに重視 (構造不安定 → 収束を優先)

    v0.9: cross-session 比較用の LambdaNormalizationMeta を返す。
      tau_min, tau_max で正規化範囲をオーバーライド可能。

    τ ∈ [tau_min, tau_max] を λ₁ ∈ [0.7, 0.3] にマップ。
    返り値: (lambda1, lambda2, LambdaNormalizationMeta)
    """
    tau_raw = tau
    # τ を [tau_min, tau_max] → [0, 1] に正規化
    span = tau_max - tau_min
    if span <= 0:
        span = 0.2  # フォールバック: デフォルト幅
    t = (tau - tau_min) / span
    t = max(0.0, min(1.0, t))

    lambda1 = 0.7 - 0.4 * t  # 0.7 → 0.3
    lambda2 = 0.3 + 0.4 * t  # 0.3 → 0.7

    # precision-aware 微調整 (v0.5)
    # precision ∈ [0, 1] で λ₂ を最大 ±0.1 調整
    if precision is not None:
        p = max(0.0, min(1.0, precision))
        adjustment = 0.1 * (2.0 * p - 1.0)  # p=0 → -0.1, p=0.5 → 0, p=1 → +0.1
        lambda1 = max(0.1, lambda1 - adjustment)
        lambda2 = max(0.1, lambda2 + adjustment)
        # 合計を 1.0 に正規化
        total = lambda1 + lambda2
        lambda1 /= total
        lambda2 /= total

    l1 = round(lambda1, 4)
    l2 = round(lambda2, 4)
    meta = LambdaNormalizationMeta(
        tau_raw=tau_raw,
        tau_min=tau_min,
        tau_max=tau_max,
        precision=precision,
        lambda1=l1,
        lambda2=l2,
    )
    return l1, l2, meta


def normalize_lambda_cross_session(
    meta_a: LambdaNormalizationMeta,
    meta_b: LambdaNormalizationMeta,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """2セッションのλメタデータから共通正規化されたλ値を再計算する。

    両セッションの tau_raw を統合した範囲 [min(a,b), max(a,b)] で
    compute_lambda_schedule を再呼出しし、比較可能な λ を算出する。

    Returns:
        ((a_lambda1, a_lambda2), (b_lambda1, b_lambda2))
        共通正規化されたλペア
    """
    # 統合正規化範囲
    unified_min = min(meta_a.tau_min, meta_b.tau_min,
                      meta_a.tau_raw, meta_b.tau_raw)
    unified_max = max(meta_a.tau_max, meta_b.tau_max,
                      meta_a.tau_raw, meta_b.tau_raw)

    # 再計算 (各セッションの precision を維持)
    a_l1, a_l2, _ = compute_lambda_schedule(
        meta_a.tau_raw, precision=meta_a.precision,
        tau_min=unified_min, tau_max=unified_max,
    )
    b_l1, b_l2, _ = compute_lambda_schedule(
        meta_b.tau_raw, precision=meta_b.precision,
        tau_min=unified_min, tau_max=unified_max,
    )

    return (a_l1, a_l2), (b_l1, b_l2)



def compute_precision_gradient(
    density: float,
    a: float = 0.3,
    b: float = 0.7,
    beta: float = 5.0,
) -> float:
    """ρ_MB (k-NN 密度) から λ schedule 用の precision を算出する。

    linkage_hyphe.md §3.5: λ(ρ) = a + b·exp(-β·ρ)
    precision(ρ) = 1 - λ(ρ) = 1 - a - b·exp(-β·ρ)

    ⚠ この関数は compute_lambda_schedule 専用。
    チャンクの precision メトリクスには使わないこと。
    チャンク precision は min-max 正規化済み rho_eff を直接使用する
    (compute_chunk_metrics Pass 2 参照)。

    理由: exp(-β·ρ) は β=5.0 で ρ>0.6 に飽和し、
    勾配が 0.024 に低下して弁別力を喪失する。
    rho_eff の min-max 正規化が precision の操作的定義として十分。

    Args:
        density: チャンクの平均 k-NN 密度 ∈ [0, 1]
        a: ρ→∞ での λ の漸近値 (< 1)。デフォルト 0.3
        b: 振幅。デフォルト 0.7
        beta: MB 境界の鋭さパラメータ。デフォルト 5.0

    Returns:
        precision ∈ [0, 1]。密度が高いほど precision が高い。
    """
    # λ(ρ) = a + b·exp(-β·ρ)
    lam = a + b * math.exp(-beta * density)
    # precision = 1 - λ(ρ)
    precision = 1.0 - lam
    # clamp to [0, 1] — ρ ≤ τ では precision ≤ 0 になりうる
    return max(0.0, min(1.0, precision))


def _compute_global_centroid(
    normed: list[list[float]],
) -> list[float]:
    """全ステップの平均 embedding (global centroid)。P(world) の proxy。"""
    if not normed:
        return []
    dim = len(normed[0])
    centroid = [0.0] * dim
    for vec in normed:
        for d in range(dim):
            centroid[d] += vec[d]
    return [c / len(normed) for c in centroid]


def _compute_chunk_centroid(
    normed: list[list[float]],
    step_indices: list[int],
) -> list[float]:
    """チャンク内ステップの平均 embedding (chunk centroid)。"""
    dim = len(normed[step_indices[0]])
    centroid = [0.0] * dim
    for idx in step_indices:
        for d in range(dim):
            centroid[d] += normed[idx][d]
    return [c / len(step_indices) for c in centroid]


def compute_chunk_metrics(
    chunks: list[Chunk],
    embeddings: list[list[float]],
    similarities: list[float],
    lambda1: float = 0.5,
    lambda2: float = 0.5,
    alpha: float = 0.5,
    edges: Optional[dict[str, list[tuple[str, float]]]] = None,
    use_density_epistemic: bool = True,
    pca_dim: int | None = None,
    per_step_sims: list[float] | None = None,
    ml_weight: float = 0.4,
    ensemble_precisions: list[float] | None = None,
    ensemble_weight: float = 0.5,
) -> list[Chunk]:
    """各チャンクの品質メトリクスを計算。

    linkage_hyphe.md §3.6:
      L(c) = λ₁ · Drift  +  λ₂ · (-EFE(c))
      EFE(c) = α · I_epistemic + (1-α) · I_pragmatic

    v0.4 改善:
      I_epistemic: k-NN 密度差分 Δρ (cos proxy fallback 付き)
      I_pragmatic: knowledge_edges degree×weight (boundary_novelty fallback 付き)
      λ₁, λ₂: compute_lambda_schedule() による τ 依存調整

    Args:
      edges: チャンク ID → [(接続先 ID, weight)] のマッピング。
             None の場合は boundary_novelty にフォールバック。
      use_density_epistemic: True で密度ベース epistemic を使用。
             False または step 数不足時は cos proxy にフォールバック。

    追加メトリクス:
      coherence  = チャンク内の隣接ステップ平均類似度
      boundary_novelty = 境界での novelty (1 - similarity)
    """
    normed = [_l2_normalize(e) for e in embeddings]

    # PCA 次元削減: precision 用の密度計算のみに適用
    # 境界検出・coherence・drift は原空間の normed を使用
    if pca_dim is not None and pca_dim > 0 and len(normed) > 1:
        normed_pca = _pca_reduce(normed, n_components=pca_dim)
    else:
        normed_pca = normed

    # 密度キャッシュ: 全ステップの k-NN 密度を1回だけ計算 (O(n²d))
    # PCA 射影後の空間で密度を計算し、anisotropy による飽和を回避
    _density_cache: list[float] | None = None
    if use_density_epistemic and len(normed_pca) > 3:
        _k = min(5, len(normed_pca) - 1)
        _density_cache = _compute_knn_density(normed_pca, k=_k)

    # P(world) の proxy — 全ステップの global centroid
    global_centroid = _compute_global_centroid(normed)

    # I_pragmatic の edges ベース: max_degree を先に計算
    max_degree = 0.0
    if edges:
        for chunk_id_key, edge_list in edges.items():
            degree_w = sum(w for _, w in edge_list)
            if degree_w > max_degree:
                max_degree = degree_w

    for chunk in chunks:
        if not chunk.steps:
            continue

        step_indices = [s.index for s in chunk.steps]

        # --- Coherence (チャンク内平均類似度) ---
        if len(step_indices) >= 2:
            chunk_sims = []
            for i in range(len(step_indices) - 1):
                idx_a, idx_b = step_indices[i], step_indices[i + 1]
                if idx_a < len(similarities):
                    chunk_sims.append(similarities[idx_a])
            chunk.coherence = sum(chunk_sims) / len(chunk_sims) if chunk_sims else 1.0
        else:
            chunk.coherence = 1.0

        # --- Boundary Novelty (境界での不連続性) ---
        last_step_idx = step_indices[-1]
        if last_step_idx < len(similarities):
            chunk.boundary_novelty = 1.0 - similarities[last_step_idx]
        else:
            chunk.boundary_novelty = 0.0  # 最後のチャンクには後続がない

        # --- Drift (L(c) Drift 項) ---
        # centroid からの平均距離² = チャンクの不安定性 (高いほど悪い)
        if len(step_indices) >= 2:
            chunk_centroid = _compute_chunk_centroid(normed, step_indices)

            # centroid からの各ステップの L2 距離
            dim = len(chunk_centroid)
            distances_sq = []
            for idx in step_indices:
                dist_sq = sum(
                    (normed[idx][d] - chunk_centroid[d]) ** 2 for d in range(dim)
                )
                distances_sq.append(dist_sq)

            mean_dist_sq = sum(distances_sq) / len(distances_sq)
            # drift = 平均距離² (0〜2 の範囲を 0〜1 に正規化)
            chunk.drift = min(1.0, mean_dist_sq / 2.0)
        else:
            chunk_centroid = normed[step_indices[0]] if step_indices else global_centroid
            chunk.drift = 0.0

        # --- I_epistemic (surprise) ---
        # v0.4: k-NN 密度差分 → cos proxy フォールバック
        # 密度はキャッシュ済み (_density_cache) を使い O(1) で参照
        if use_density_epistemic and len(normed) > 3:
            chunk.epistemic = _compute_epistemic_density(
                normed, step_indices, k=min(5, len(normed) - 1),
                precomputed_densities=_density_cache,
            )
        else:
            # cos proxy フォールバック (v0.3 互換)
            if global_centroid:
                sim_to_global = _cosine_similarity(chunk_centroid, global_centroid)
                chunk.epistemic = 1.0 - sim_to_global
            else:
                chunk.epistemic = 0.0

        # --- I_pragmatic (展開可能性) ---
        # v0.4: knowledge_edges degree×weight → boundary_novelty フォールバック
        chunk_id_str = str(chunk.chunk_id)
        if edges and chunk_id_str in edges:
            # degree_weighted = Σ weight for all edges from/to chunk_id
            degree_weighted = sum(w for _, w in edges[chunk_id_str])
            chunk.pragmatic = degree_weighted / max_degree if max_degree > 0 else 0.0
        else:
            # boundary_novelty フォールバック (v0.3 互換)
            chunk.pragmatic = chunk.boundary_novelty

        # --- Precision (v0.7 — min-max 正規化 rho_eff 直接使用) ---
        # v0.5-v0.6 の問題: compute_precision_gradient の exp(-β·ρ) が
        # ρ>0.6 で飽和し precision range ≈ 0.001 に圧縮されていた。
        # v0.7: exp 変換を廃止。min-max 正規化済み rho_eff をそのまま precision とする。
        #   rho_eff = ρ_mean × coh × (1 - drift)  (統合有効密度)
        #   precision = min-max(rho_eff) ∈ [0, 1]
        #   FEP 根拠: precision は MB 内の相対的精度。
        #     rho_eff 自体が「密度 × 一貫性 × 安定性」= precision の操作的定義。
        #     非線形変換は λ schedule 用であり、precision 計測には不要。
        if _density_cache and step_indices:
            rho_vals = [_density_cache[i] for i in step_indices if i < len(_density_cache)]
            rho_mean = sum(rho_vals) / len(rho_vals) if rho_vals else 0.0
        else:
            rho_mean = 0.5  # フォールバック: 中間値
        # 統合有効密度: 3 信号の積
        rho_eff = rho_mean * chunk.coherence * (1.0 - chunk.drift)
        chunk._rho_eff = rho_eff  # Pass 2 用に一時保存

        # --- EFE = α·epistemic + (1-α)·pragmatic ---
        chunk.efe = alpha * chunk.epistemic + (1.0 - alpha) * chunk.pragmatic

    # --- Pass 2: Precision (k-NN) = quantile 正規化 rho_eff (v0.8) ---
    # v0.7 の min-max 正規化は rho_eff の狭い値域 (e.g. 0.55-0.58) を
    # 0→1 に引き伸ばし、外れ値が端に固定される U字型分布を生む。
    # v0.8: rank-based (quantile) normalization に変更。
    #   precision_knn = rank(rho_eff) / (n - 1)
    #   FEP 根拠: precision は MB 内の相対精度 (= 順位)。
    rho_effs = [c._rho_eff for c in chunks if hasattr(c, '_rho_eff')]
    precision_knn_vals = []  # Pass 3 で使用
    if len(rho_effs) >= 2:
        # 昇順ソートでランクを割り当て (同値は平均ランク)
        sorted_rhos = sorted(enumerate(rho_effs), key=lambda x: x[1])
        ranks = [0.0] * len(rho_effs)
        i = 0
        while i < len(sorted_rhos):
            j = i
            while j < len(sorted_rhos) and abs(sorted_rhos[j][1] - sorted_rhos[i][1]) < 1e-12:
                j += 1
            avg_rank = sum(range(i, j)) / (j - i)
            for k in range(i, j):
                ranks[sorted_rhos[k][0]] = avg_rank
            i = j
        n_rho = len(rho_effs)
        chunk_idx = 0
        for chunk in chunks:
            if hasattr(chunk, '_rho_eff'):
                p_knn = ranks[chunk_idx] / (n_rho - 1) if n_rho > 1 else 0.5
                precision_knn_vals.append(p_knn)
                chunk_idx += 1
                del chunk._rho_eff
    else:
        for chunk in chunks:
            if hasattr(chunk, '_rho_eff'):
                precision_knn_vals.append(0.5)
                del chunk._rho_eff

    # --- Pass 3: precision_ml (multilayer) / ensemble + 統合 precision (v1.0) ---
    # v0.9: per_step_sims (bge-m3 浅↔深 cos sim) → precision_ml
    # v1.0: ensemble_precisions (Qwen3×Gemini RSA) → precision_ensemble
    # 優先順位: ensemble > multilayer > kNN のみ
    # 統合: w * best_signal + (1-w) * precision_knn
    has_ml = per_step_sims is not None and len(per_step_sims) > 0
    has_ensemble = ensemble_precisions is not None and len(ensemble_precisions) > 0

    if has_ml:
        # セッション全体の min-max を計算
        s_min = min(per_step_sims)
        s_max = max(per_step_sims)
        s_range = s_max - s_min

    for ci, chunk in enumerate(chunks):
        if not chunk.steps:
            continue
        # k-NN precision (ベースライン)
        p_knn = precision_knn_vals[ci] if ci < len(precision_knn_vals) else 0.5

        # multilayer precision (bge-m3 浅↔深)
        if has_ml:
            step_indices = [s.index for s in chunk.steps]
            sims = [per_step_sims[idx] for idx in step_indices if idx < len(per_step_sims)]
            if sims and s_range > 1e-9:
                mean_sim = sum(sims) / len(sims)
                chunk.precision_ml = max(0.0, min(1.0, (mean_sim - s_min) / s_range))
            else:
                chunk.precision_ml = 0.5
        else:
            chunk.precision_ml = 0.0

        # ensemble precision (Qwen3×Gemini RSA)
        if has_ensemble and ci < len(ensemble_precisions):
            chunk.precision_ensemble = ensemble_precisions[ci]
        else:
            chunk.precision_ensemble = 0.0

        # 統合 precision: 最良信号との加重平均
        if has_ensemble and ci < len(ensemble_precisions):
            # v1.0: ensemble が利用可能 → ensemble × weight + kNN × (1-weight)
            chunk.precision = ensemble_weight * chunk.precision_ensemble + (1.0 - ensemble_weight) * p_knn
        elif has_ml:
            # v0.9 互換: multilayer × weight + kNN × (1-weight)
            chunk.precision = ml_weight * chunk.precision_ml + (1.0 - ml_weight) * p_knn
        else:
            # kNN のみ (後方互換)
            chunk.precision = p_knn

        # PrecisionResult を生成 (v1.0)
        # gate_label は暫定 "mid" — 閾値 (theta_high, theta_low) は実験で決定後に設定
        chunk.precision_result = PrecisionResult(
            knn=p_knn,
            multilayer=chunk.precision_ml,
            ensemble=chunk.precision_ensemble,
            integrated=chunk.precision,
            gate_label="mid",  # 暫定: precision_gate で後から上書き
        )

    # --- L(c) 統合損失 ---
    # L(c) = λ₁·drift + λ₂·(-EFE)
    for chunk in chunks:
        if chunk.steps:
            chunk.loss = lambda1 * chunk.drift + lambda2 * (-chunk.efe)

    return chunks


# ── AY: Presheaf Representability Difference ─────────────────────────


# PURPOSE: precision が追加する「射」の数を定量化する。
#   AY = |Hom(L(K), −)| - |Hom(K, −)|
#   L(K) = precision-annotated chunks, K = bare chunks
#   AY > 0 ⟺ precision が non-trivial (定数でない)
#   理論根拠: linkage_hyphe.md §4, compute_ay_v2.py
#   PROOF: kalon.md §6 — 展開可能性 (Generative) の定量化
def compute_ay(chunks: list["Chunk"]) -> dict:
    """セッションレベルの AY (Presheaf Representability) を計算する。

    AY は precision の「付加価値」を3つの観点で測定:
    1. 構造的 AY: precision が生む弁別可能な状態数
    2. 情報論的 AY: precision のShannon エントロピー
    3. 実効的 AY: precision による λ schedule への影響量

    Args:
        chunks: compute_chunk_metrics() で処理済みのチャンクリスト

    Returns:
        dict: AY 指標を含む辞書
          - ay_structural: int — 追加射の数
          - ay_ratio: float — 射の増加率
          - ay_info: float — Shannon エントロピー (bits)
          - ay_effective: float — Σ|dL| (precision による loss 変動の総量)
          - ay_positive: bool — AY > 0 か
          - unique_precisions: int — ユニークな precision 値の数
          - discriminability: float — unique / n
    """
    import math as _math

    valid = [c for c in chunks if c.steps]
    n = len(valid)
    if n == 0:
        return {"ay_structural": 0, "ay_ratio": 0.0, "ay_info": 0.0,
                "ay_effective": 0.0, "ay_positive": False,
                "unique_precisions": 0, "discriminability": 0.0}

    precisions = [c.precision for c in valid]

    # Approach 1: 構造的 AY (弁別可能性)
    unique_p = len(set(round(p, 6) for p in precisions))
    hom_k = n  # bare K: 各チャンクから1射
    filter_morphisms = unique_p
    compare_morphisms = unique_p * (unique_p - 1) // 2
    hom_lk = n + filter_morphisms + compare_morphisms
    ay_structural = hom_lk - hom_k
    ay_ratio = ay_structural / hom_k if hom_k > 0 else 0.0

    # Approach 2: 情報論的 AY (Shannon エントロピー)
    n_bins = 10
    hist = [0] * n_bins
    for p in precisions:
        hist[min(int(p * n_bins), n_bins - 1)] += 1
    probs = [h / n for h in hist if h > 0]
    ay_info = -sum(p_i * _math.log2(p_i) for p_i in probs) if probs else 0.0

    # Approach 3: 実効的 AY (λ impact)
    delta = 0.1
    ay_effective = 0.0
    for c in valid:
        p = c.precision
        dl = delta * abs(p - 0.5) * (abs(c.drift) + abs(c.efe))
        ay_effective += dl

    discriminability = unique_p / n if n > 0 else 0.0

    return {
        "ay_structural": ay_structural,
        "ay_ratio": round(ay_ratio, 4),
        "ay_info": round(ay_info, 4),
        "ay_effective": round(ay_effective, 6),
        "ay_positive": ay_structural > 0,
        "unique_precisions": unique_p,
        "discriminability": round(discriminability, 4),
    }


# ── τ 動的決定 (Motherbrain consistency_log → Hyphē τ) ─────────────


# PURPOSE: consistency_log の severity エントロピーから τ を動的に決定する
#   FEP 根拠: τ = 精度パラメータ π の操作化
#   issue 蓄積量 ∝ ρ の低さ → τ を下げる (より細かくチャンク)
#   PROOF: linkage_hyphe.md §3.4 — τ は precision setting 問題
def compute_tau_from_entropy(
    issues: list[dict],
    tau_base: float = 0.7,
    alpha: float = 0.3,
    tau_min: float = 0.3,
    tau_max: float = 0.9,
) -> float:
    """consistency_log の severity エントロピーから τ を動的に決定する。

    Args:
        issues: phantazein_store.get_recent_issues() の戻り値。
                各 dict に "severity" キー (low/medium/high/critical) を含む。
        tau_base: 基準 τ 値 (issue なし時のデフォルト)。
        alpha: エントロピー感度係数。α が大きいほど τ の変動幅が大きい。
        tau_min: τ の下限 (過度な分割防止)。
        tau_max: τ の上限。

    Returns:
        動的に決定された τ 値。

    理論:
        H(severity) = -Σ p(s) log₂ p(s)
        H_max = log₂(4) = 2.0 (4カテゴリ)
        H_normalized = H / H_max ∈ [0, 1]
        τ = clamp(τ_base × (1 - α × H_normalized), τ_min, τ_max)

        H が高い (severity が均等に分散 = 多様な問題) → τ を下げる
        H が低い (severity が偏る or issue なし) → τ を維持
    """
    if not issues:
        # issue なし = 健全 → τ_base をそのまま返す
        return max(tau_min, min(tau_max, tau_base))

    # severity カテゴリの頻度集計
    severity_levels = ("low", "medium", "high", "critical")
    counts: dict[str, int] = {s: 0 for s in severity_levels}
    for issue in issues:
        sev = issue.get("severity", "medium")
        if sev in counts:
            counts[sev] += 1
        else:
            counts["medium"] += 1  # 未知の severity → medium にフォールバック

    total = sum(counts.values())
    if total == 0:
        return max(tau_min, min(tau_max, tau_base))

    # Shannon エントロピー計算
    h = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total
            h -= p * math.log2(p)

    # 正規化 (H_max = log₂(4) = 2.0)
    h_max = math.log2(len(severity_levels))  # 2.0
    h_normalized = h / h_max if h_max > 0 else 0.0

    # τ 変換: エントロピーが高いほど τ を下げる
    tau = tau_base * (1.0 - alpha * h_normalized)

    # クランプ
    tau = max(tau_min, min(tau_max, tau))

    logger.info(
        "τ 動的決定: H=%.3f, H_norm=%.3f, τ=%.3f (base=%.3f, α=%.2f)",
        h, h_normalized, tau, tau_base, alpha,
    )
    return tau


# ── メイン API ──────────────────────────────────────────────────────

def chunk_session(
    steps: list[Step],
    embeddings: list[list[float]],
    tau: float = 0.7,
    min_steps: int = 2,
    max_iterations: int = 10,
    sim_mode: str = "pairwise",
    sim_k: int = 3,
    edges: Optional[dict[str, list[tuple[str, float]]]] = None,
    auto_lambda: bool = True,
    pca_dim: int | None = None,
    per_step_sims: list[float] | None = None,
    ml_weight: float = 0.4,
    ensemble_precisions: list[float] | None = None,
    ensemble_weight: float = 0.5,
) -> ChunkingResult:
    """セッションログをチャンク化するメインエントリポイント。

    Args:
        steps: パース済みのステップ列
        embeddings: 各ステップの embedding ベクトル
        tau: 境界検出の閾値 (理論の τ に対応)
        min_steps: チャンクの最小ステップ数
        max_iterations: G∘F 最大反復回数
        sim_mode: 類似度計算モード ("pairwise" or "knn")
        sim_k: knn モードの k 値 (デフォルト 3)

        edges: knowledge_edges のマッピング (chunk_id → [(to_id, weight)])。
            None の場合は boundary_novelty にフォールバック。
        auto_lambda: True で τ に応じた λ₁, λ₂ を自動計算 (v0.4)。

    Returns:
        ChunkingResult with chunks, metrics, convergence info
    """
    if len(steps) != len(embeddings):
        raise ValueError(
            f"steps ({len(steps)}) と embeddings ({len(embeddings)}) の長さが不一致"
        )

    if not steps:
        return ChunkingResult(session_id="", chunks=[], converged=True)

    # Phase 3: 類似度トレースと境界検出
    similarities = compute_similarity_trace(embeddings, mode=sim_mode, k=sim_k)
    boundaries = detect_boundaries(similarities, tau=tau)

    # 初期チャンク生成
    chunks = steps_to_chunks(steps, boundaries)

    # Phase 4: G∘F 反復
    chunks, iterations, converged = gf_iterate(
        chunks, embeddings,
        tau=tau, min_steps=min_steps, max_iterations=max_iterations,
    )

    # Phase 5: L(c) 計算 (Drift + EFE 2項分解)
    # v0.4: τ 依存 λ スケジュール
    # v0.5: precision-aware 微調整は compute_chunk_metrics 後に再計算
    lambda_meta = None
    if auto_lambda:
        lambda1, lambda2, lambda_meta = compute_lambda_schedule(tau)
    else:
        lambda1, lambda2 = 0.5, 0.5
    chunks = compute_chunk_metrics(
        chunks, embeddings, similarities,
        lambda1=lambda1, lambda2=lambda2,
        edges=edges,
        pca_dim=pca_dim,
        per_step_sims=per_step_sims,
        ml_weight=ml_weight,
        ensemble_precisions=ensemble_precisions,
        ensemble_weight=ensemble_weight,
    )

    # v0.7: Precision-aware λ 再計算
    # compute_chunk_metrics で各チャンクの precision が計算された後、
    # チャンクごとに λ₁, λ₂ を precision で微調整し loss を更新する。
    # 高 precision (p > 0.5) → EFE 重視 / 低 precision (p < 0.5) → drift 重視
    if auto_lambda:
        for chunk in chunks:
            if chunk.steps and chunk.precision is not None:
                pa_lam1, pa_lam2, _ = compute_lambda_schedule(tau, precision=chunk.precision)
                chunk.loss = pa_lam1 * chunk.drift + pa_lam2 * (-chunk.efe)

    # 統計情報
    n = len(chunks) if chunks else 1
    mean_drift = sum(c.drift for c in chunks) / n
    mean_coherence = sum(c.coherence for c in chunks) / n
    mean_size = sum(len(c) for c in chunks) / n
    mean_epistemic = sum(c.epistemic for c in chunks) / n
    mean_pragmatic = sum(c.pragmatic for c in chunks) / n
    mean_efe = sum(c.efe for c in chunks) / n
    mean_loss = sum(c.loss for c in chunks) / n
    mean_precision = sum(c.precision for c in chunks) / n
    mean_precision_ml = sum(c.precision_ml for c in chunks) / n
    mean_precision_ens = sum(c.precision_ensemble for c in chunks) / n

    # 分散 (弁別力の指標)
    drift_var = sum((c.drift - mean_drift) ** 2 for c in chunks) / n if n > 1 else 0.0
    epi_var = sum((c.epistemic - mean_epistemic) ** 2 for c in chunks) / n if n > 1 else 0.0
    prag_var = sum((c.pragmatic - mean_pragmatic) ** 2 for c in chunks) / n if n > 1 else 0.0
    efe_var = sum((c.efe - mean_efe) ** 2 for c in chunks) / n if n > 1 else 0.0
    precision_var = sum((c.precision - mean_precision) ** 2 for c in chunks) / n if n > 1 else 0.0
    precision_ml_var = sum((c.precision_ml - mean_precision_ml) ** 2 for c in chunks) / n if n > 1 else 0.0
    precision_ens_var = sum((c.precision_ensemble - mean_precision_ens) ** 2 for c in chunks) / n if n > 1 else 0.0
    loss_var = sum((c.loss - mean_loss) ** 2 for c in chunks) / n if n > 1 else 0.0

    return ChunkingResult(
        session_id="",
        chunks=chunks,
        iterations=iterations,
        converged=converged,
        similarity_trace=similarities,
        tau=tau,
        metrics={
            "total_steps": len(steps),
            "num_chunks": len(chunks),
            "mean_chunk_size": round(mean_size, 1),
            "mean_coherence": round(mean_coherence, 3),
            "mean_drift": round(mean_drift, 3),
            "mean_epistemic": round(mean_epistemic, 4),
            "mean_pragmatic": round(mean_pragmatic, 4),
            "mean_efe": round(mean_efe, 4),
            "mean_loss": round(mean_loss, 4),
            "drift_var": round(drift_var, 6),
            "epistemic_var": round(epi_var, 6),
            "pragmatic_var": round(prag_var, 6),
            "efe_var": round(efe_var, 6),
            "loss_var": round(loss_var, 6),
            "mean_precision": round(mean_precision, 4),
            "precision_var": round(precision_var, 6),
            "mean_precision_ml": round(mean_precision_ml, 4),
            "precision_ml_var": round(precision_ml_var, 6),
            "converged": converged,
            "iterations": iterations,
        },
        lambda_meta=lambda_meta,
    )
