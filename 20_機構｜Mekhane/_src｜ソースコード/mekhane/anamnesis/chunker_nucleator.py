from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/anamnesis/chunker_nucleator.py
"""PROOF: [L2/インフラ] このファイルは存在しなければならない

P3 → 場⊣結晶パイプラインが必要
   → セッションログの意味的チャンキングが必要
   → Nucleator アルゴリズム (linkage_hyphe.md §3-§8) が担う
   → chunker_nucleator.py が production 実装

Q.E.D.

---

Nucleator — Hyphē Session Chunker (production 版)

PURPOSE: PoC (60_Peira/06_HyphēPoC/hyphe_chunker.py) から昇格。
  sys.path ハックを撤廃し、核心アルゴリズムを直接内蔵する。

理論→実装マッピング:
  ρ_MB (§3.3)  → 隣接ステップの cosine similarity (proxy)
  τ (§3.4)     → 類似度閾値 (統計的戦略: μ(ρ) - 1.5σ(ρ))
  L(c) (§3.6)  → Drift + EFE 2項分解 (epistemic + pragmatic)
  F (§3 Write) → 短チャンク merge (発散)
  G (§3 Read)  → 低 coherence 再分割 (収束)
  Fix(G∘F)     → 境界が不変になるまで反復

検証: 130実験 (13セッション × 5τ × 2モード) で G∘F 収束率 100%。
"""


import math
import logging
from dataclasses import dataclass, field as dc_field
from typing import Optional

logger = logging.getLogger(__name__)


# ── データ構造 ──────────────────────────────────────────────────────

@dataclass
class Step:
    """セッションログの1ステップ (意味的段落単位)。"""
    index: int
    text: str
    tools: list[str] = dc_field(default_factory=list)

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def line_count(self) -> int:
        return self.text.count("\n") + 1


@dataclass
class PrecisionResult:
    """チャンクの精度計算結果 (v1.0)。

    kNN 密度ベース、multilayer (浅↔深 cos sim)、ensemble (RSA 行相関)
    の 3 信号を統合した precision 値を構造化して保持する。
    """
    knn: float           # L1: k-NN 密度ベース precision
    multilayer: float    # L2: bge-m3 浅↔深 cos sim (0.0 if unavailable)
    ensemble: float      # L3: RSA 行相関 (0.0 if unavailable)
    integrated: float    # 統合値 (w * best + (1-w) * knn)
    gate_label: str      # "high" / "mid" / "low"

    @property
    def recompute_ratio(self) -> float:
        """precision → 再計算率 (連続値)。

        CacheBlend HKVD 原理の同型: precision が低いほど再処理が必要。
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
    precision_ml: float = 0.0        # multilayer precision: 浅↔深 cos sim
    precision_ensemble: float = 0.0  # ensemble precision: RSA 行相関
    precision_result: "PrecisionResult | None" = None  # 構造化 precision 結果
    topic: str = ""                  # 推定トピック名

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
class ChunkingResult:
    """チャンク化の最終結果。"""
    session_id: str
    chunks: list[Chunk]
    iterations: int = 0              # G∘F 反復回数
    converged: bool = False          # Fix 到達したか
    similarity_trace: list[float] = dc_field(default_factory=list)
    tau: float = 0.0                 # 使用した τ
    metrics: dict = dc_field(default_factory=dict)


# ── ベクトル演算 ─────────────────────────────────────────────────────

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


# ── 類似度トレース ───────────────────────────────────────────────────

def compute_similarity_trace(
    embeddings: list[list[float]],
    mode: str = "pairwise",
    k: int = 5,
) -> list[float]:
    """ステップ間の類似度トレースを計算。

    mode:
      'pairwise' — 隣接 (i, i+1) のみ。1次マルコフ仮定。
      'knn'      — 前後 k ステップの平均類似度。非線形テキスト対応。

    返り値: 長さ = len(embeddings) - 1
    """
    if len(embeddings) < 2:
        return []

    normed = [_l2_normalize(e) for e in embeddings]

    if mode == "knn":
        return _compute_knn_trace(normed, k=k)

    # pairwise (デフォルト)
    return [
        _cosine_similarity(normed[i], normed[i + 1])
        for i in range(len(normed) - 1)
    ]


def _compute_knn_trace(normed: list[list[float]], k: int = 5) -> list[float]:
    """k-nearest 類似度トレース。

    各遷移 (i, i+1) について、前後 k ステップ間の窓の
    平均類似度を計算。1次マルコフ仮定を緩和。
    """
    n = len(normed)
    similarities = []

    for i in range(n - 1):
        left_window = range(max(0, i - k + 1), i + 1)
        right_window = range(i + 1, min(n, i + k + 1))

        cross_sims = [
            _cosine_similarity(normed[li], normed[ri])
            for li in left_window
            for ri in right_window
        ]

        sim = sum(cross_sims) / len(cross_sims) if cross_sims else 0.0
        similarities.append(sim)

    return similarities


# ── 境界検出 ─────────────────────────────────────────────────────────

def detect_boundaries(similarities: list[float], tau: float = 0.7) -> list[int]:
    """類似度が τ を下回るインデックスを境界として返す。

    linkage_hyphe.md §3.4: τ = 自律性出現の臨界密度
    """
    return [i for i, sim in enumerate(similarities) if sim < tau]


def compute_adaptive_tau(similarities: list[float], k: float = 1.5) -> float:
    """統計的 τ 決定: μ(ρ) - kσ(ρ)。

    linkage_hyphe.md §8: uninformative prior に近い統計的戦略。
    G∘F の事後的補正があるため精密な τ_init は不要。

    Args:
        similarities: 類似度トレース
        k: σ の係数 (デフォルト 1.5 で有意な逸脱)

    Returns:
        τ 値。0.5 以上 0.9 以下にクランプ。
    """
    if not similarities:
        return 0.70  # デフォルト

    n = len(similarities)
    mu = sum(similarities) / n
    variance = sum((s - mu) ** 2 for s in similarities) / n
    sigma = math.sqrt(variance)

    tau = mu - k * sigma
    return max(0.5, min(0.9, tau))


def steps_to_chunks(steps: list[Step], boundaries: list[int]) -> list[Chunk]:
    """ステップ列と境界リストからチャンクを生成。"""
    if not steps:
        return []

    bounds = sorted(set(boundaries))
    chunks = []
    chunk_id = 0
    start = 0

    for b in bounds:
        end = b + 1
        if end > start and end <= len(steps):
            chunks.append(Chunk(chunk_id=chunk_id, steps=steps[start:end]))
            chunk_id += 1
            start = end

    if start < len(steps):
        chunks.append(Chunk(chunk_id=chunk_id, steps=steps[start:]))

    return chunks


# ── G∘F 反復 ─────────────────────────────────────────────────────────

def _merge_small_chunks(chunks: list[Chunk], min_steps: int = 2) -> list[Chunk]:
    """F 操作: 短すぎるチャンクを隣接チャンクに merge (発散 → 結合)。"""
    if len(chunks) <= 1:
        return chunks

    merged = []
    i = 0
    while i < len(chunks):
        current = chunks[i]
        if len(current) < min_steps and i + 1 < len(chunks):
            next_chunk = chunks[i + 1]
            combined = Chunk(
                chunk_id=current.chunk_id,
                steps=current.steps + next_chunk.steps,
            )
            merged.append(combined)
            i += 2
        elif len(current) < min_steps and merged:
            merged[-1] = Chunk(
                chunk_id=merged[-1].chunk_id,
                steps=merged[-1].steps + current.steps,
            )
            i += 1
        else:
            merged.append(current)
            i += 1

    return merged


def _recursive_split(
    chunk: Chunk,
    embeddings: list[list[float]],
    tau: float,
    min_steps: int,
) -> list[Chunk]:
    """1つのチャンクを τ 未満の全箇所で再帰的に分割する。"""
    if len(chunk) < min_steps * 2:
        return [chunk]

    step_indices = [s.index for s in chunk.steps]
    chunk_embeddings = [embeddings[idx] for idx in step_indices]
    internal_sims = compute_similarity_trace(chunk_embeddings)

    if not internal_sims:
        return [chunk]

    min_sim = min(internal_sims)
    min_idx = internal_sims.index(min_sim)

    if min_sim >= tau:
        return [chunk]
    if min_idx < min_steps - 1 or (len(chunk) - min_idx - 1) < min_steps:
        return [chunk]

    split_point = min_idx + 1
    chunk_a = Chunk(chunk_id=chunk.chunk_id, steps=chunk.steps[:split_point])
    chunk_b = Chunk(chunk_id=chunk.chunk_id + 1, steps=chunk.steps[split_point:])

    left = _recursive_split(chunk_a, embeddings, tau, min_steps)
    right = _recursive_split(chunk_b, embeddings, tau, min_steps)

    return left + right


def _split_incoherent_chunks(
    chunks: list[Chunk],
    embeddings: list[list[float]],
    tau: float = 0.7,
    min_steps: int = 2,
) -> list[Chunk]:
    """G 操作: 低 coherence チャンクを再帰的に再分割 (収束 → 蒸留)。"""
    result = []
    for chunk in chunks:
        result.extend(_recursive_split(chunk, embeddings, tau, min_steps))
    return result


def _renumber_chunks(chunks: list[Chunk]) -> list[Chunk]:
    """チャンク ID を連番に振り直す。"""
    for i, chunk in enumerate(chunks):
        chunk.chunk_id = i
    return chunks


def _extract_boundaries(chunks: list[Chunk]) -> list[int]:
    """チャンク列から境界インデックスを抽出。"""
    return [chunk.steps[-1].index for chunk in chunks if chunk.steps]


def gf_iterate(
    chunks: list[Chunk],
    embeddings: list[list[float]],
    tau: float = 0.7,
    min_steps: int = 2,
    max_iterations: int = 10,
) -> tuple[list[Chunk], int, bool]:
    """G∘F を反復して Fix(G∘F) に収束させる。

    linkage_hyphe.md §3: Fix(G∘F) = リンクを足して蒸留しても変わらない
    130実験で G∘F 収束率 100% (§8.5)。

    Returns: (chunks, iterations, converged)
    """
    prev_boundaries = _extract_boundaries(chunks)

    for iteration in range(max_iterations):
        # F: merge (発散)
        chunks = _merge_small_chunks(chunks, min_steps=min_steps)
        # G: split (収束)
        chunks = _split_incoherent_chunks(chunks, embeddings, tau=tau, min_steps=min_steps)
        chunks = _renumber_chunks(chunks)

        current_boundaries = _extract_boundaries(chunks)
        if current_boundaries == prev_boundaries:
            return chunks, iteration + 1, True

        prev_boundaries = current_boundaries

    return chunks, max_iterations, False


# ── L(c) メトリクス計算 ──────────────────────────────────────────────

def _compute_knn_density(normed: list[list[float]], k: int = 5) -> list[float]:
    """各ステップの k-NN 密度を計算。ρ_i = kNN の平均類似度。"""
    n = len(normed)
    if n <= 1:
        return [1.0] * n

    effective_k = min(k, n - 1)
    densities = []
    for i in range(n):
        sims = sorted(
            [_cosine_similarity(normed[i], normed[j]) for j in range(n) if j != i],
            reverse=True,
        )
        densities.append(sum(sims[:effective_k]) / effective_k)

    return densities


def _compute_epistemic_density(
    normed: list[list[float]],
    step_indices: list[int],
    k: int = 5,
) -> float:
    """I_epistemic = チャンクによる密度場の変形量。

    linkage_hyphe.md §3.6: KL[P(world|c) ‖ P(world)] の proxy。
    返り値: ∈ [0, 1]。密度差が大きいほど epistemic value が高い。
    """
    n = len(normed)
    if n <= 1:
        return 0.0

    densities = _compute_knn_density(normed, k=k)

    step_set = set(step_indices)
    rho_in_vals = [densities[i] for i in step_indices if i < n]
    rho_out_vals = [densities[i] for i in range(n) if i not in step_set]

    if not rho_in_vals or not rho_out_vals:
        return 0.0

    rho_in = sum(rho_in_vals) / len(rho_in_vals)
    rho_out = sum(rho_out_vals) / len(rho_out_vals)

    denom = max(rho_in, rho_out, 1e-8)
    return min(1.0, abs(rho_in - rho_out) / denom)


def compute_lambda_schedule(tau: float) -> tuple[float, float]:
    """τ に応じて λ₁, λ₂ を調整する。

    linkage_hyphe.md §3.5: λ(ρ) = a + b·exp(-β·ρ)
    高τ → λ₂ (EFE) を上げる / 低τ → λ₁ (Drift) を上げる
    """
    t = max(0.0, min(1.0, (tau - 0.6) / 0.2))
    lambda1 = round(0.7 - 0.4 * t, 4)
    lambda2 = round(0.3 + 0.4 * t, 4)
    return lambda1, lambda2


def compute_chunk_metrics(
    chunks: list[Chunk],
    embeddings: list[list[float]],
    similarities: list[float],
    lambda1: float = 0.5,
    lambda2: float = 0.5,
    alpha: float = 0.5,
    edges: Optional[dict[str, list[tuple[str, float]]]] = None,
    use_density_epistemic: bool = True,
    per_step_sims: list[float] | None = None,
    ml_weight: float = 0.4,
    ensemble_precisions: list[float] | None = None,
    ensemble_weight: float = 0.5,
) -> list[Chunk]:
    """各チャンクの品質メトリクスを計算。

    linkage_hyphe.md §3.6:
      L(c) = λ₁ · Drift  +  λ₂ · (-EFE(c))
      EFE(c) = α · I_epistemic + (1-α) · I_pragmatic

    v1.0 追加: 3パス precision 計算 (kNN → quantile → ensemble 統合)
      per_step_sims: multilayer precision 用の浅↔深 cos sim (None で無効)
      ensemble_precisions: チャンクごとの ensemble precision (None で無効)
      ensemble_weight: ensemble 統合時の重み (デフォルト 0.5)
    """
    normed = [_l2_normalize(e) for e in embeddings]

    # 密度キャッシュ: 全ステップの k-NN 密度を1回だけ計算 (O(n²d))
    _density_cache: list[float] | None = None
    if use_density_epistemic and len(normed) > 3:
        _k = min(5, len(normed) - 1)
        _density_cache = _compute_knn_density(normed, k=_k)

    # P(world) の proxy
    dim = len(normed[0]) if normed else 0
    global_centroid = [0.0] * dim
    if normed:
        for vec in normed:
            for d in range(dim):
                global_centroid[d] += vec[d]
        global_centroid = [c / len(normed) for c in global_centroid]

    # edges ベース max_degree
    max_degree = 0.0
    if edges:
        for edge_list in edges.values():
            degree_w = sum(w for _, w in edge_list)
            if degree_w > max_degree:
                max_degree = degree_w

    # --- Pass 1: Coherence, Drift, EFE, rho_eff ---
    for chunk in chunks:
        if not chunk.steps:
            continue

        step_indices = [s.index for s in chunk.steps]

        # Coherence
        if len(step_indices) >= 2:
            chunk_sims = [
                similarities[idx] for idx in step_indices[:-1]
                if idx < len(similarities)
            ]
            chunk.coherence = sum(chunk_sims) / len(chunk_sims) if chunk_sims else 1.0
        else:
            chunk.coherence = 1.0

        # Boundary Novelty
        last_idx = step_indices[-1]
        chunk.boundary_novelty = (1.0 - similarities[last_idx]) if last_idx < len(similarities) else 0.0

        # Drift (centroid variance)
        if len(step_indices) >= 2:
            cc = [0.0] * dim
            for idx in step_indices:
                for d in range(dim):
                    cc[d] += normed[idx][d]
            cc = [c / len(step_indices) for c in cc]

            distances_sq = [
                sum((normed[idx][d] - cc[d]) ** 2 for d in range(dim))
                for idx in step_indices
            ]
            chunk.drift = min(1.0, sum(distances_sq) / len(distances_sq) / 2.0)
            chunk_centroid = cc
        else:
            chunk_centroid = normed[step_indices[0]] if step_indices else global_centroid
            chunk.drift = 0.0

        # I_epistemic
        if use_density_epistemic and len(normed) > 3:
            chunk.epistemic = _compute_epistemic_density(
                normed, step_indices, k=min(5, len(normed) - 1),
            )
        else:
            if global_centroid and chunk_centroid:
                chunk.epistemic = 1.0 - _cosine_similarity(chunk_centroid, global_centroid)
            else:
                chunk.epistemic = 0.0

        # I_pragmatic
        chunk_id_str = str(chunk.chunk_id)
        if edges and chunk_id_str in edges:
            degree_weighted = sum(w for _, w in edges[chunk_id_str])
            chunk.pragmatic = degree_weighted / max_degree if max_degree > 0 else 0.0
        else:
            chunk.pragmatic = chunk.boundary_novelty

        # EFE
        chunk.efe = alpha * chunk.epistemic + (1.0 - alpha) * chunk.pragmatic

        # rho_eff (統合有効密度) — Pass 2 の quantile 正規化入力
        if _density_cache and step_indices:
            rho_vals = [_density_cache[i] for i in step_indices if i < len(_density_cache)]
            rho_mean = sum(rho_vals) / len(rho_vals) if rho_vals else 0.0
        else:
            rho_mean = 0.5  # フォールバック: 中間値
        # 統合有効密度: 密度 × 一貫性 × 安定性
        chunk._rho_eff = rho_mean * chunk.coherence * (1.0 - chunk.drift)  # type: ignore[attr-defined]

    # --- Pass 2: Precision (k-NN) = quantile 正規化 rho_eff ---
    # rank-based (quantile) normalization: precision_knn = rank(rho_eff) / (n - 1)
    rho_effs = [c._rho_eff for c in chunks if hasattr(c, '_rho_eff')]  # type: ignore[attr-defined]
    precision_knn_vals: list[float] = []
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
            for k_idx in range(i, j):
                ranks[sorted_rhos[k_idx][0]] = avg_rank
            i = j
        n_rho = len(rho_effs)
        chunk_idx = 0
        for chunk in chunks:
            if hasattr(chunk, '_rho_eff'):
                p_knn = ranks[chunk_idx] / (n_rho - 1) if n_rho > 1 else 0.5
                precision_knn_vals.append(p_knn)
                chunk_idx += 1
                del chunk._rho_eff  # type: ignore[attr-defined]
    else:
        for chunk in chunks:
            if hasattr(chunk, '_rho_eff'):
                precision_knn_vals.append(0.5)
                del chunk._rho_eff  # type: ignore[attr-defined]

    # --- Pass 3: precision_ml / ensemble + 統合 precision + PrecisionResult ---
    # 優先順位: ensemble > multilayer > kNN のみ
    has_ml = per_step_sims is not None and len(per_step_sims) > 0
    has_ensemble = ensemble_precisions is not None and len(ensemble_precisions) > 0

    if has_ml and per_step_sims is not None:
        s_min = min(per_step_sims)
        s_max = max(per_step_sims)
        s_range = s_max - s_min
    else:
        s_min = s_max = s_range = 0.0

    for ci, chunk in enumerate(chunks):
        if not chunk.steps:
            continue

        # k-NN precision (ベースライン)
        p_knn = precision_knn_vals[ci] if ci < len(precision_knn_vals) else 0.5

        # multilayer precision (浅↔深 cos sim)
        if has_ml and per_step_sims is not None:
            step_indices = [s.index for s in chunk.steps]
            sims = [per_step_sims[idx] for idx in step_indices if idx < len(per_step_sims)]
            if sims and s_range > 1e-9:
                mean_sim = sum(sims) / len(sims)
                chunk.precision_ml = max(0.0, min(1.0, (mean_sim - s_min) / s_range))
            else:
                chunk.precision_ml = 0.5
        else:
            chunk.precision_ml = 0.0

        # ensemble precision (RSA 行相関)
        if has_ensemble and ensemble_precisions is not None and ci < len(ensemble_precisions):
            chunk.precision_ensemble = ensemble_precisions[ci]
        else:
            chunk.precision_ensemble = 0.0

        # 統合 precision: 最良信号との加重平均
        if has_ensemble and ensemble_precisions is not None and ci < len(ensemble_precisions):
            chunk.precision = ensemble_weight * chunk.precision_ensemble + (1.0 - ensemble_weight) * p_knn
        elif has_ml:
            chunk.precision = ml_weight * chunk.precision_ml + (1.0 - ml_weight) * p_knn
        else:
            chunk.precision = p_knn

        # PrecisionResult を生成
        chunk.precision_result = PrecisionResult(
            knn=p_knn,
            multilayer=chunk.precision_ml,
            ensemble=chunk.precision_ensemble,
            integrated=chunk.precision,
            gate_label="mid",  # 暫定: precision_gate で後から上書き
        )

    # --- L(c) 統合損失 ---
    for chunk in chunks:
        if chunk.steps:
            chunk.loss = lambda1 * chunk.drift + lambda2 * (-chunk.efe)

    return chunks


# ── AY (Presheaf Representability) ───────────────────────────────────

# PURPOSE: precision が追加する「射」の数を定量化する。
#   AY = |Hom(L(K), −)| - |Hom(K, −)|
#   L(K) = precision-annotated chunks, K = bare chunks
#   AY > 0 ⟺ precision が non-trivial (定数でない)
#   理論根拠: linkage_hyphe.md §4, compute_ay_v2.py
#   PROOF: kalon.md §6 — 展開可能性 (Generative) の定量化
def compute_ay(
    chunks: list[Chunk],
    lambda1: float = 0.5,
    lambda2: float = 0.5,
) -> dict:
    """セッションレベルの AY (Presheaf Representability) を計算する。

    AY は precision の「付加価値」を4つの観点で測定:
    1. 構造的 AY: precision が生む弁別可能な状態数
    2. 情報論的 AY: precision の Shannon エントロピー
    3. 実効的 AY: precision による λ schedule への影響量
    4. 品質シグナル性: precision と coherence/drift の相関

    Args:
        chunks: compute_chunk_metrics() で処理済みのチャンクリスト
        lambda1: Drift 項の重み (Approach 3 で使用)
        lambda2: EFE 項の重み (Approach 3 で使用)

    Returns:
        dict: AY 指標を含む辞書
          - ay_structural: int — 追加射の数
          - ay_ratio: float — 射の増加率
          - ay_info: float — Shannon エントロピー (bits)
          - ay_effective: float — Σ|dL| (precision による loss 変動の総量)
          - ay_positive: bool — AY > 0 か
          - unique_precisions: int — ユニークな precision 値の数
          - discriminability: float — unique / n
          - corr_precision_coherence: float — precision-coherence 相関
          - corr_precision_drift: float — precision-drift 相関
          - lambda_recommendation: dict — 次回セッション向け λ 推奨
              - lambda1: float — 推奨 λ₁ (Drift 重み)
              - lambda2: float — 推奨 λ₂ (EFE 重み)
              - reason: str — 推奨理由
    """
    valid = [c for c in chunks if c.steps]
    n = len(valid)
    if n == 0:
        return {
            "ay_structural": 0, "ay_ratio": 0.0, "ay_info": 0.0,
            "ay_effective": 0.0, "ay_positive": False,
            "unique_precisions": 0, "discriminability": 0.0,
            "corr_precision_coherence": 0.0,
            "corr_precision_drift": 0.0,
            "lambda_recommendation": {
                "lambda1": 0.5, "lambda2": 0.5,
                "reason": "データ不足: チャンクなし",
            },
        }

    precisions = [c.precision for c in valid]

    # Approach 1: 構造的 AY (弁別可能性)
    # Hom(K, −) = n (bare K: 各チャンクから同一型への射1つ)
    # Hom(L(K), −) = n + unique_p (フィルタ射) + C(unique_p, 2) (比較射)
    unique_p = len(set(round(p, 6) for p in precisions))
    hom_k = n
    filter_morphisms = unique_p
    compare_morphisms = unique_p * (unique_p - 1) // 2
    hom_lk = n + filter_morphisms + compare_morphisms
    ay_structural = hom_lk - hom_k
    ay_ratio = ay_structural / hom_k if hom_k > 0 else 0.0

    # Approach 2: 情報論的 AY (Shannon エントロピー)
    # H(K) = 0 (bare chunks = 弁別不能)
    # H(L(K)) = precision 分布のエントロピー > 0
    n_bins = 10
    hist = [0] * n_bins
    for p in precisions:
        hist[min(int(p * n_bins), n_bins - 1)] += 1
    probs = [h / n for h in hist if h > 0]
    ay_info = -sum(p_i * math.log2(p_i) for p_i in probs) if probs else 0.0

    # Approach 3: 実効的 AY (λ direct impact)
    # precision による λ schedule への直接影響を計算 (compute_ay_v2 準拠)
    delta_factor = 0.1
    total_abs_dl = 0.0
    for c in valid:
        p = c.precision
        dl1 = -delta_factor * (p - 0.5)
        dl2 = +delta_factor * (p - 0.5)
        loss_base = lambda1 * c.drift + lambda2 * (-c.efe)
        loss_adj = (lambda1 + dl1) * c.drift + (lambda2 + dl2) * (-c.efe)
        total_abs_dl += abs(loss_base - loss_adj)

    # Approach 4: 品質シグナル性 (precision vs coherence/drift 相関)
    coherences = [c.coherence for c in valid]
    drifts = [c.drift for c in valid]
    corr_pc = _pearson_r(precisions, coherences) if n >= 2 else 0.0
    corr_pd = _pearson_r(precisions, drifts) if n >= 2 else 0.0

    discriminability = unique_p / n if n > 0 else 0.0

    # λ 推奨: precision の影響度と相関パターンから次回 λ を調整
    # ay_effective が大きい → precision の影響が強い → precision に従う方向に λ を調整
    # corr_pd < 0 → precision が高いチャンクほど drift が低い → λ1 (drift) を下げてよい
    # corr_pd > 0 → precision が高いチャンクほど drift が高い → λ1 (drift) を上げるべき
    rec_lambda1 = 0.5
    rec_lambda2 = 0.5
    reason = "デフォルト: 十分な信号なし"
    if total_abs_dl > 0.01 and n >= 3:
        # precision が drift と負相関 → drift 項を下げても安全
        if corr_pd < -0.3:
            rec_lambda1 = round(max(0.2, lambda1 - 0.1), 4)
            rec_lambda2 = round(min(0.8, lambda2 + 0.1), 4)
            reason = f"precision-drift 負相関 ({corr_pd:.2f}): λ₁↓ λ₂↑"
        # precision が drift と正相関 → drift 項を上げて補正
        elif corr_pd > 0.3:
            rec_lambda1 = round(min(0.8, lambda1 + 0.1), 4)
            rec_lambda2 = round(max(0.2, lambda2 - 0.1), 4)
            reason = f"precision-drift 正相関 ({corr_pd:.2f}): λ₁↑ λ₂↓"
        else:
            rec_lambda1 = lambda1
            rec_lambda2 = lambda2
            reason = f"precision-drift 弱相関 ({corr_pd:.2f}): 現行 λ 維持"

    return {
        "ay_structural": ay_structural,
        "ay_ratio": round(ay_ratio, 4),
        "ay_info": round(ay_info, 4),
        "ay_effective": round(total_abs_dl, 6),
        "ay_positive": ay_structural > 0,
        "unique_precisions": unique_p,
        "discriminability": round(discriminability, 4),
        "corr_precision_coherence": round(corr_pc, 4),
        "corr_precision_drift": round(corr_pd, 4),
        "lambda_recommendation": {
            "lambda1": rec_lambda1,
            "lambda2": rec_lambda2,
            "reason": reason,
        },
    }


def _pearson_r(xs: list[float], ys: list[float]) -> float:
    """2系列のピアソン相関係数を計算。"""
    n = len(xs)
    if n < 2:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / n
    var_x = sum((x - mean_x) ** 2 for x in xs) / n
    var_y = sum((y - mean_y) ** 2 for y in ys) / n
    denom = (var_x * var_y) ** 0.5
    return cov / denom if denom > 1e-12 else 0.0


# ── τ 動的決定 ───────────────────────────────────────────────────────

def compute_tau_from_entropy(
    issues: list[dict],
    tau_base: float = 0.7,
    alpha: float = 0.3,
    tau_min: float = 0.3,
    tau_max: float = 0.9,
) -> float:
    """consistency_log の severity エントロピーから τ を動的に決定する。

    H(severity) = -Σ p(s) log₂ p(s)
    H が高い (多様な問題) → τ を下げる (より細かくチャンク)
    """
    if not issues:
        return max(tau_min, min(tau_max, tau_base))

    severity_levels = ("low", "medium", "high", "critical")
    counts: dict[str, int] = {s: 0 for s in severity_levels}
    for issue in issues:
        sev = issue.get("severity", "medium")
        counts[sev if sev in counts else "medium"] += 1

    total = sum(counts.values())
    if total == 0:
        return max(tau_min, min(tau_max, tau_base))

    h = -sum(
        (c / total) * math.log2(c / total)
        for c in counts.values() if c > 0
    )

    h_max = math.log2(len(severity_levels))
    h_normalized = h / h_max if h_max > 0 else 0.0

    tau = tau_base * (1.0 - alpha * h_normalized)
    return max(tau_min, min(tau_max, tau))


# ── メイン API ───────────────────────────────────────────────────────

def chunk_session(
    steps: list[Step],
    embeddings: list[list[float]],
    session_id: str = "",
    tau: float | str = 0.70,
    min_steps: int = 2,
    max_iterations: int = 10,
    sim_mode: str = "pairwise",
    sim_k: int = 3,
    edges: Optional[dict[str, list[tuple[str, float]]]] = None,
    auto_lambda: bool = True,
    per_step_sims: list[float] | None = None,
    ml_weight: float = 0.4,
    ensemble_precisions: list[float] | None = None,
    ensemble_weight: float = 0.5,
) -> ChunkingResult:
    """セッションログをチャンク化するメインエントリポイント。

    NucleatorChunker から呼ばれる低レベル API。

    Args:
        steps: 意味的段落に分割済みのステップ列
        embeddings: 各ステップの embedding ベクトル
        session_id: セッション識別子
        tau: 境界検出閾値 (float) or "auto" (統計的決定)
        min_steps: チャンクの最小ステップ数
        max_iterations: G∘F 最大反復回数
        sim_mode: 類似度計算モード ("pairwise" or "knn")
        sim_k: knn モードの k 値
        edges: knowledge_edges マッピング (chunk_id → [(to_id, weight)])
        auto_lambda: True で τ 依存 λ スケジュールを使用
        per_step_sims: multilayer precision 用ステップごと浅↔深 cos sim
        ml_weight: multilayer 統合時の重み (デフォルト 0.4)
        ensemble_precisions: チャンクごとの ensemble precision
        ensemble_weight: ensemble 統合時の重み (デフォルト 0.5)
    """
    if len(steps) != len(embeddings):
        raise ValueError(
            f"steps ({len(steps)}) と embeddings ({len(embeddings)}) の長さが不一致"
        )

    if not steps:
        return ChunkingResult(session_id=session_id, chunks=[], converged=True)

    # 類似度トレース
    similarities = compute_similarity_trace(embeddings, mode=sim_mode, k=sim_k)

    # τ 解決
    if tau == "auto":
        effective_tau = compute_adaptive_tau(similarities)
    else:
        effective_tau = float(tau)

    # 境界検出 → 初期チャンク
    boundaries = detect_boundaries(similarities, tau=effective_tau)
    chunks = steps_to_chunks(steps, boundaries)

    # G∘F 反復
    chunks, iterations, converged = gf_iterate(
        chunks, embeddings,
        tau=effective_tau, min_steps=min_steps, max_iterations=max_iterations,
    )

    # L(c) + precision 計算
    if auto_lambda:
        lambda1, lambda2 = compute_lambda_schedule(effective_tau)
    else:
        lambda1, lambda2 = 0.5, 0.5

    chunks = compute_chunk_metrics(
        chunks, embeddings, similarities,
        lambda1=lambda1, lambda2=lambda2,
        edges=edges,
        per_step_sims=per_step_sims,
        ml_weight=ml_weight,
        ensemble_precisions=ensemble_precisions,
        ensemble_weight=ensemble_weight,
    )

    # AY (Presheaf Representability) 計算
    ay_metrics = compute_ay(chunks, lambda1=lambda1, lambda2=lambda2)

    # 統計情報
    n = len(chunks) if chunks else 1
    base_metrics = {
        "total_steps": len(steps),
        "num_chunks": len(chunks),
        "mean_chunk_size": round(sum(len(c) for c in chunks) / n, 1),
        "mean_coherence": round(sum(c.coherence for c in chunks) / n, 3),
        "mean_drift": round(sum(c.drift for c in chunks) / n, 3),
        "mean_efe": round(sum(c.efe for c in chunks) / n, 4),
        "mean_loss": round(sum(c.loss for c in chunks) / n, 4),
        "converged": converged,
        "iterations": iterations,
        "tau": round(effective_tau, 4),
    }
    base_metrics["ay"] = ay_metrics

    return ChunkingResult(
        session_id=session_id,
        chunks=chunks,
        iterations=iterations,
        converged=converged,
        similarity_trace=similarities,
        tau=effective_tau,
        metrics=base_metrics,
    )
