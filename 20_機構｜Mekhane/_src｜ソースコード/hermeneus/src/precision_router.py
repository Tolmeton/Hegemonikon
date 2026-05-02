from __future__ import annotations
"""Precision-Aware Execution Router (Anchor Cosine Similarity + Ensemble RSA + ABPP).

PURPOSE: gemini-embedding-2-preview で入力テキストの embedding を取得し、
  「単純タスク」「複雑タスク」2つのアンカーとの cos sim 差で precision を算出。
  diff = cos(input, simple) - cos(input, complex)
    正 → 単純テキスト → exploit
    負 → 複雑テキスト → explore

  v4: Ensemble Precision — 複数モデル間のチャンク類似度行列の一致度 (RSA)
    Qwen3-Embedding-0.6B (ローカル) + Gemini (API) の cos sim 行列の Spearman 相関

  v5: ABPP (Anchor-Based Precision Profiling) — 化学的分離法アンサンブル
    3手法: Electrophoresis (重心偏差) + Chromatography (2極位置) + IEF v2 (4軸パターン)
    4軸: technical / procedural / conceptual / judgmental × precise / vague
    加重アンサンブル: E=0.2, C=0.3, I=0.5 (実験で最適化, Spearman ρ=+0.89, N=20)

設計原理 (FEP):
  exploit = 既知パターンに沿った行動 (Accuracy ≫ Complexity)
  explore = 新規情報の探索が必要 (epistemic value が高い)
  precision = 行動の選択にかける精度の重み

依存: google-genai (gemini-embedding-2-preview API)
  API Key なし環境では graceful fallback (precision=0.5)。
  v4 追加依存: torch, transformers (Qwen3 用。未インストール時は graceful fallback)

移行履歴:
  v1: bge-m3 浅層/深層 cos sim (2026-03 〜)
  v2: Matryoshka 4帯域エネルギー (2026-03-15 — 棄却: range=0.0098)
  v3: アンカー cos sim (2026-03-15 〜 — diff range=0.3506)
  v4: Ensemble RSA (2026-03-15 〜 — Pearson r mean=0.80, chunk prec range=0.09〜1.00)
  v5: ABPP (2026-03-15 〜 — 3手法アンサンブル, ρ=+0.89)
"""


import json
import logging
import math
import os
import statistics as _statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# === 定数 ===

# Gemini Embedding モデル
MODEL_NAME = "gemini-embedding-2-preview"
EMBED_DIM = 768  # 768d で十分な分離を実証済み

# アンカー embedding ファイル (同一ディレクトリ)
_ANCHOR_PATH = Path(__file__).parent / "anchor_embeddings.json"

# 実行戦略の閾値 (diff = sim_simple - sim_complex)
# 実測値: simple +0.04〜+0.22 / complex -0.03〜-0.13
# → ±0.02 で clean に分離
EXPLOIT_THRESHOLD = 0.02   # ≥ この値 → exploit
EXPLORE_THRESHOLD = -0.02  # < この値 → explore

# コンテキスト最小長 (文字数)
MIN_CONTEXT_LENGTH = 100


# Skill description ファイル (skills ディレクトリ — WF 後継)
_SKILL_DIR = Path(__file__).resolve().parents[4] / ".agents" / "skills"
# フォールバック: 旧 WF ディレクトリ
_WF_DIR_LEGACY = Path(__file__).resolve().parents[4] / ".agents" / "workflows"


# === データクラス ===

@dataclass(frozen=True)
class PrecisionResult:
    """precision 算出の全結果 (P6: linkage metrics 含む)。"""

    diff: float            # sim_simple - sim_complex (-1 ~ +1)
    sim_simple: float      # cos(embedding, anchor_simple)
    sim_complex: float     # cos(embedding, anchor_complex)
    embedding: list[float] # context の生 embedding (linkage 計算で再利用)


@dataclass(frozen=True)
class LinkageMetrics:
    """P6 Linkage 三量 (coherence / drift)。

    coherence/drift が None の場合は「未計測」を意味し、
    effective_depth に影響しない (#5 /ele+ → /dio 修正)。
    """

    coherence: Optional[float]  # WF 間の意味的一貫性 [0, 1] or None
    drift: Optional[float]      # context と WF 群の意味的距離 [0, 1] or None
    wf_ids: tuple[str, ...]     # 対象 WF ID 群
    reasoning: str              # 判断根拠


@dataclass(frozen=True)
class ExecutionStrategy:
    """Precision routing の結果。"""

    depth_level: int           # 1-3 (L1/L2/L3)
    search_budget: int         # Periskopē 検索回数 (0/1/3)
    gnosis_search: bool        # Gnōsis 検索の有無
    precision_ml: float        # 算出された precision 値 (diff: -1.0〜+1.0)
    confidence_threshold: float  # 確信度閾値
    reasoning: str             # 判断根拠 (1行)


# === Singleton Embed Client & Anchors ===

_embed_client: Optional[object] = None
_embed_client_attempted: bool = False
_anchor_simple: Optional[list[float]] = None
_anchor_complex: Optional[list[float]] = None


def _get_embed_client():
    """Gemini API Client の遅延取得。singleton パターン。

    環境変数 GOOGLE_API_KEY が未設定 / google-genai 未インストール時は None。
    """
    global _embed_client, _embed_client_attempted

    if _embed_client_attempted:
        return _embed_client

    _embed_client_attempted = True

    try:
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        if not api_key:
            # Hermeneus 固有の Key もチェック
            api_key = os.getenv("GOOGLE_API_KEY_MOVEMENT", "").strip()
        if not api_key:
            logger.info("  ⚠️ [precision_router] GOOGLE_API_KEY 未設定 → fallback")
            return None

        from google import genai
        _embed_client = genai.Client(api_key=api_key)
        logger.info(
            "  ✅ [precision_router] Gemini Embedding client 初期化完了: %s",
            MODEL_NAME,
        )
        return _embed_client

    except (ImportError, Exception) as e:  # noqa: BLE001
        logger.warning("  ⚠️ [precision_router] client 初期化失敗: %s", e)
        _embed_client = None
        return None


def _load_anchors() -> tuple[list[float], list[float]] | tuple[None, None]:
    """アンカー embedding をファイルから遅延ロード。"""
    global _anchor_simple, _anchor_complex

    if _anchor_simple is not None:
        return _anchor_simple, _anchor_complex

    try:
        with open(_ANCHOR_PATH) as f:
            data = json.load(f)
        _anchor_simple = data["simple"]
        _anchor_complex = data["complex"]
        logger.debug(
            "  📊 [precision_router] アンカー読み込み: simple=%dd, complex=%dd",
            len(_anchor_simple), len(_anchor_complex),
        )
        return _anchor_simple, _anchor_complex
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logger.warning("  ⚠️ [precision_router] アンカー読み込み失敗: %s", e)
        return None, None


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """2つのベクトルの cos sim を計算。"""
    n = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(n))
    norm_a = math.sqrt(sum(x * x for x in a[:n]))
    norm_b = math.sqrt(sum(x * x for x in b[:n]))
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    return dot / (norm_a * norm_b)


def compute_context_precision(text: str) -> PrecisionResult:
    """テキストの precision を アンカー cos sim 差から算出。

    diff = cos(input, simple_anchor) - cos(input, complex_anchor)
      正 → 単純テキスト → exploit 方向
      負 → 複雑テキスト → explore 方向

    Args:
        text: 対象テキスト (100文字以上推奨)

    Returns:
        PrecisionResult。API 非対応環境では中立値 (diff=0.0)。
    """
    _NEUTRAL = PrecisionResult(diff=0.0, sim_simple=0.0, sim_complex=0.0, embedding=[])

    if len(text) < MIN_CONTEXT_LENGTH:
        return _NEUTRAL

    client = _get_embed_client()
    if client is None:
        return _NEUTRAL

    anchor_s, anchor_c = _load_anchors()
    if anchor_s is None:
        return _NEUTRAL

    try:
        from google.genai import types

        config = types.EmbedContentConfig(
            task_type="SEMANTIC_SIMILARITY",
            output_dimensionality=EMBED_DIM,
        )

        # API 1回で embedding を取得
        result = client.models.embed_content(
            model=MODEL_NAME,
            contents=[text[:2000]],  # 安全マージン: 2000文字で打ち切り
            config=config,
        )

        if not result.embeddings:
            logger.warning("  ⚠️ [precision_router] embedding が空")
            return _NEUTRAL

        embedding = list(result.embeddings[0].values)

        # アンカーとの cos sim
        sim_simple = _cosine_similarity(embedding, anchor_s)
        sim_complex = _cosine_similarity(embedding, anchor_c)
        diff = max(-1.0, min(1.0, sim_simple - sim_complex))

        logger.debug(
            "  📊 [precision_router] sim_S=%.4f sim_C=%.4f diff=%.4f",
            sim_simple, sim_complex, diff,
        )

        return PrecisionResult(
            diff=diff,
            sim_simple=sim_simple,
            sim_complex=sim_complex,
            embedding=embedding,
        )

    except Exception as e:  # noqa: BLE001
        logger.warning("  ⚠️ [precision_router] precision 算出失敗: %s", e)
        return _NEUTRAL


def _load_wf_descriptions(wf_ids: list[str]) -> list[str]:
    """WF/Skill ID 群の description を frontmatter から読み取る。

    優先順位: .agents/skills/{id}/SKILL.md > .agents/workflows/{id}.md (レガシー)
    """
    descriptions = []
    for wf_id in wf_ids:
        # Skill パス (新): .agents/skills/{verb}/SKILL.md
        skill_path = _SKILL_DIR / wf_id / "SKILL.md"
        # レガシー WF パス: .agents/workflows/{verb}.md
        legacy_path = _WF_DIR_LEGACY / f"{wf_id}.md"

        target_path = skill_path if skill_path.exists() else (
            legacy_path if legacy_path.exists() else None
        )
        if target_path is None:
            continue
        try:
            text = target_path.read_text(encoding="utf-8")
            # YAML frontmatter の description を抽出 (簡易パーサー)
            if text.startswith("---"):
                end = text.find("---", 3)
                if end > 0:
                    front = text[3:end]
                    for line in front.splitlines():
                        if line.startswith("description:"):
                            desc = line[len("description:"):].strip().strip('"').strip("'")
                            if desc:
                                descriptions.append(desc)
                            break
        except OSError:
            continue
    return descriptions


def compute_linkage(
    context_embedding: list[float],
    wf_ids: list[str],
) -> LinkageMetrics:
    """P6: WF description embedding による coherence/drift 計算。

    coherence = WF 間の description embedding の平均 cos sim (WF 間一貫性)
    drift     = 1.0 - mean(cos(context, wf_description)) (context-WF 乖離)

    Args:
        context_embedding: context の embedding (compute_context_precision で取得済み)
        wf_ids: CCL 式内の WF ID リスト (例: ["noe", "ene"])

    Returns:
        LinkageMetrics。API 非対応時は中立値。
    """
    _NEUTRAL = LinkageMetrics(
        coherence=None, drift=None, wf_ids=tuple(wf_ids), reasoning="fallback"
    )

    if not wf_ids or not context_embedding:
        return _NEUTRAL

    # WF description を取得
    descriptions = _load_wf_descriptions(wf_ids)
    if not descriptions:
        return LinkageMetrics(
            coherence=None, drift=None, wf_ids=tuple(wf_ids),
            reasoning=f"WF description 未取得 ({len(wf_ids)} WFs)",
        )

    # WF description を batch embedding
    client = _get_embed_client()
    if client is None:
        return _NEUTRAL

    try:
        from google.genai import types

        config = types.EmbedContentConfig(
            task_type="SEMANTIC_SIMILARITY",
            output_dimensionality=EMBED_DIM,
        )

        result = client.models.embed_content(
            model=MODEL_NAME,
            contents=descriptions,
            config=config,
        )

        if not result.embeddings or len(result.embeddings) < len(descriptions):
            logger.warning("  ⚠️ [linkage] WF embedding 不足")
            return _NEUTRAL

        wf_embeddings = [list(e.values) for e in result.embeddings]

        # --- coherence: WF 間 cos sim の平均 ---
        if len(wf_embeddings) >= 2:
            pair_sims = []
            for i in range(len(wf_embeddings)):
                for j in range(i + 1, len(wf_embeddings)):
                    pair_sims.append(
                        _cosine_similarity(wf_embeddings[i], wf_embeddings[j])
                    )
            coherence = sum(pair_sims) / len(pair_sims)
        else:
            # WF 1つのみ → 自己一貫 = 1.0
            coherence = 1.0

        # --- drift: context と WF 群の平均距離 ---
        ctx_wf_sims = [
            _cosine_similarity(context_embedding, wf_emb)
            for wf_emb in wf_embeddings
        ]
        mean_ctx_wf_sim = sum(ctx_wf_sims) / len(ctx_wf_sims)
        drift = max(0.0, min(1.0, 1.0 - mean_ctx_wf_sim))

        # coherence もクランプ
        coherence = max(0.0, min(1.0, coherence))

        logger.debug(
            "  📊 [linkage] coherence=%.4f drift=%.4f wf_ids=%s",
            coherence, drift, wf_ids,
        )

        return LinkageMetrics(
            coherence=coherence,
            drift=drift,
            wf_ids=tuple(wf_ids),
            reasoning=(
                f"coherence={coherence:.3f} (pairs={len(wf_embeddings)}C2), "
                f"drift={drift:.3f} (ctx-wf mean_sim={mean_ctx_wf_sim:.3f})"
            ),
        )

    except Exception as e:  # noqa: BLE001
        logger.warning("  ⚠️ [linkage] linkage 算出失敗: %s", e)
        return _NEUTRAL


def route_execution(
    precision: float,
    ccl_depth: int,
    *,
    exploit_threshold: float = EXPLOIT_THRESHOLD,
    explore_threshold: float = EXPLORE_THRESHOLD,
) -> ExecutionStrategy:
    """Precision 値に基づいて実行戦略を決定。

    CCL の `+`/`-` 演算子は上限/下限として機能:
    - `+` (ccl_depth=3): precision が高くても L3 以下にはしない
    - `-` (ccl_depth=1): precision が低くても L1 以上にはしない

    Args:
        precision: diff 値 (-1.0〜+1.0)。正=単純, 負=複雑
        ccl_depth: CCL 演算子から推定した深度 (1/2/3)
        exploit_threshold: exploit 閾値 (デフォルト 0.02)
        explore_threshold: explore 閾値 (デフォルト -0.02)

    Returns:
        ExecutionStrategy
    """
    if precision >= exploit_threshold:
        # exploit: 単純テキスト。深度を上げない
        return ExecutionStrategy(
            depth_level=max(ccl_depth, 1),  # CCL 指定の下限を尊重
            search_budget=0,
            gnosis_search=False,
            precision_ml=precision,
            confidence_threshold=0.8,
            reasoning=f"exploit (diff={precision:.4f} ≥ {exploit_threshold})",
        )

    if precision < explore_threshold:
        # explore: 複雑テキスト。深度を L2 以上に引き上げ
        return ExecutionStrategy(
            depth_level=max(ccl_depth, 2),  # 最低 L2
            search_budget=3,
            gnosis_search=True,
            precision_ml=precision,
            confidence_threshold=0.5,
            reasoning=f"explore (diff={precision:.4f} < {explore_threshold})",
        )

    # balanced: CCL 指定をそのまま使用
    return ExecutionStrategy(
        depth_level=ccl_depth,
        search_budget=1,
        gnosis_search=True,
        precision_ml=precision,
        confidence_threshold=0.65,
        reasoning=f"balanced (diff={precision:.4f})",
    )


# ══════════════════════════════════════════════════════════════════════
# v4: Ensemble Precision (RSA — Representational Similarity Analysis)
# ══════════════════════════════════════════════════════════════════════
#
# 方法:
#   1. チャンクテキスト群を Qwen3 (ローカル) + Gemini (API) で embedding
#   2. 各モデル内でチャンク間 cos sim 行列 (N×N) を計算
#   3. 2行列の Spearman 相関 = Ensemble Precision (セッション全体)
#   4. 行ごとの Spearman 相関 = チャンク別 precision
#
# Pearson r mean=0.80 (5セッション実験, 2026-03-15)
# チャンク別 precision range=[0.09, 1.00] — genuine な弁別力あり


@dataclass(frozen=True)
class EnsemblePrecisionResult:
    """Ensemble Precision (v4) の結果。"""

    session_precision: float   # セッション全体の Spearman r
    chunk_precisions: list[float]  # チャンク別 Spearman r
    available: bool            # 両モデルが使用可能だったか


class EnsemblePrecisionCalculator:
    """Qwen3 + Gemini の RSA でチャンク別 precision を算出。

    PURPOSE: 複数モデル間の類似度構造の一致度をチャンク精度として使う。
      両モデルが「似ている」と判定するチャンク = 意味的に明確 = 高 precision。
      不一致 = 曖昧 or モデル固有解釈依存 = 低 precision。

    遅延初期化: Qwen3 のロードは重い (数秒) ため、初回の compute() 呼び出し時に初期化。
    graceful fallback: torch/transformers 未インストール → None → 0.5 fallback。
    """

    def __init__(self) -> None:
        self._qwen_model = None
        self._qwen_tokenizer = None
        self._qwen_attempted = False
        self._qwen_device = "cpu"

    def _init_qwen(self) -> bool:
        """Qwen3 モデルの遅延初期化。成功時 True。"""
        if self._qwen_attempted:
            return self._qwen_model is not None
        self._qwen_attempted = True

        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            model_name = "Qwen/Qwen3-Embedding-0.6B"
            logger.info("  🧠 [ensemble] Loading %s...", model_name)
            self._qwen_tokenizer = AutoTokenizer.from_pretrained(
                model_name, trust_remote_code=True
            )
            if self._qwen_tokenizer.pad_token is None:
                self._qwen_tokenizer.pad_token = self._qwen_tokenizer.eos_token
            self._qwen_model = AutoModel.from_pretrained(
                model_name, trust_remote_code=True, torch_dtype=torch.float32
            )
            self._qwen_model.eval()
            logger.info("  ✅ [ensemble] Qwen3 loaded (CPU)")
            return True
        except (ImportError, Exception) as e:  # noqa: BLE001
            logger.warning("  ⚠️ [ensemble] Qwen3 初期化失敗: %s", e)
            self._qwen_model = None
            return False

    def _embed_qwen(self, texts: list[str]) -> list[list[float]] | None:
        """Qwen3 で embedding を取得。"""
        if not self._init_qwen():
            return None

        import torch

        results = []
        for text in texts:
            inputs = self._qwen_tokenizer(
                text[:2000], return_tensors="pt",
                max_length=512, truncation=True, padding=True,
            )
            with torch.no_grad():
                outputs = self._qwen_model(**inputs)
            attn = inputs.get("attention_mask")
            if attn is not None:
                idx = int(attn.sum(dim=1)[0]) - 1
            else:
                idx = inputs["input_ids"].shape[1] - 1
            emb = outputs.last_hidden_state[0, idx, :].float().tolist()
            results.append(emb)
        return results

    def _embed_gemini(self, texts: list[str]) -> list[list[float]] | None:
        """Gemini API で embedding を取得。"""
        client = _get_embed_client()
        if client is None:
            return None

        try:
            results = []
            for text in texts:
                result = client.models.embed_content(
                    model=MODEL_NAME,
                    contents=text[:2000],
                )
                emb = list(result.embeddings[0].values)
                results.append(emb)
            return results
        except Exception as e:  # noqa: BLE001
            logger.warning("  ⚠️ [ensemble] Gemini embedding 失敗: %s", e)
            return None

    @staticmethod
    def _cos_sim_matrix(embeddings: list[list[float]]) -> list[list[float]]:
        """embedding リストから cos sim 行列を計算 (numpy 不要)。"""
        n = len(embeddings)
        # L2 正規化
        norms = []
        for emb in embeddings:
            norm = math.sqrt(sum(x * x for x in emb))
            norms.append([x / (norm + 1e-12) for x in emb])

        mat = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                mat[i][j] = sum(a * b for a, b in zip(norms[i], norms[j]))
        return mat

    @staticmethod
    def _spearmanr(x: list[float], y: list[float]) -> float:
        """Spearman 順位相関 (scipy 不要の簡易実装)。"""
        n = len(x)
        if n < 3:
            return 0.0

        # 順位変換
        def _rank(vals: list[float]) -> list[float]:
            indexed = sorted(range(n), key=lambda i: vals[i])
            ranks = [0.0] * n
            for rank_val, idx in enumerate(indexed):
                ranks[idx] = float(rank_val)
            return ranks

        rx = _rank(x)
        ry = _rank(y)

        # Pearson on ranks
        mean_rx = sum(rx) / n
        mean_ry = sum(ry) / n
        cov = sum((rx[i] - mean_rx) * (ry[i] - mean_ry) for i in range(n))
        std_rx = math.sqrt(sum((rx[i] - mean_rx) ** 2 for i in range(n)))
        std_ry = math.sqrt(sum((ry[i] - mean_ry) ** 2 for i in range(n)))
        if std_rx < 1e-12 or std_ry < 1e-12:
            return 0.0
        return cov / (std_rx * std_ry)

    def compute(self, chunk_texts: list[str]) -> EnsemblePrecisionResult:
        """チャンクテキスト群から Ensemble Precision を算出。

        Args:
            chunk_texts: チャンクのテキストリスト (4以上推奨)

        Returns:
            EnsemblePrecisionResult。モデル不使用時は fallback (precision=0.5)。
        """
        _FALLBACK = EnsemblePrecisionResult(
            session_precision=0.5,
            chunk_precisions=[0.5] * len(chunk_texts),
            available=False,
        )

        if len(chunk_texts) < 3:
            return _FALLBACK

        # 両モデルで embedding
        qwen_embs = self._embed_qwen(chunk_texts)
        gemini_embs = self._embed_gemini(chunk_texts)

        if qwen_embs is None or gemini_embs is None:
            return _FALLBACK

        # cos sim 行列
        qwen_sim = self._cos_sim_matrix(qwen_embs)
        gemini_sim = self._cos_sim_matrix(gemini_embs)

        n = len(chunk_texts)

        # 上三角ベクトル (セッション全体の相関)
        vec_q = []
        vec_g = []
        for i in range(n):
            for j in range(i + 1, n):
                vec_q.append(qwen_sim[i][j])
                vec_g.append(gemini_sim[i][j])

        session_r = self._spearmanr(vec_q, vec_g) if len(vec_q) >= 3 else 0.5

        # チャンク別 precision (行ごとの相関)
        chunk_precs = []
        for i in range(n):
            row_q = [qwen_sim[i][j] for j in range(n) if j != i]
            row_g = [gemini_sim[i][j] for j in range(n) if j != i]
            r = self._spearmanr(row_q, row_g) if len(row_q) >= 3 else 0.0
            # r ∈ [-1, 1] → [0, 1] に変換
            chunk_precs.append(max(0.0, min(1.0, (r + 1.0) / 2.0)))

        logger.info(
            "  📊 [ensemble] session_r=%.4f chunk_prec_mean=%.4f range=[%.4f, %.4f]",
            session_r,
            sum(chunk_precs) / max(len(chunk_precs), 1),
            min(chunk_precs) if chunk_precs else 0.0,
            max(chunk_precs) if chunk_precs else 0.0,
        )

        return EnsemblePrecisionResult(
            session_precision=session_r,
            chunk_precisions=chunk_precs,
            available=True,
        )


# Singleton
_ensemble_calculator: Optional[EnsemblePrecisionCalculator] = None


def compute_ensemble_chunk_precisions(
    chunk_texts: list[str],
) -> EnsemblePrecisionResult:
    """Ensemble Precision を算出する公開 API。

    precision_router の既存 API (compute_context_precision) と並行して使用可能。
    compute_context_precision は 1テキスト → 精度 (アンカー比較)。
    この関数は N テキスト群 → N チャンク別精度 (モデル間 RSA)。

    Args:
        chunk_texts: チャンクテキストのリスト

    Returns:
        EnsemblePrecisionResult (session_precision, chunk_precisions, available)
    """
    global _ensemble_calculator
    if _ensemble_calculator is None:
        _ensemble_calculator = EnsemblePrecisionCalculator()
    return _ensemble_calculator.compute(chunk_texts)


# ============================================================================
# v5: ABPP (Anchor-Based Precision Profiling) — 化学的分離法アンサンブル
# ============================================================================
#
# 3手法: Electrophoresis (重心偏差) + Chromatography (2極位置) + IEF v2 (4軸パターン)
# 4軸: technical / procedural / conceptual / judgmental × precise / vague
# 加重アンサンブル: E=0.2, C=0.3, I=0.5 (実験で最適化, Spearman ρ=+0.89, N=20)
# 用途: v3 (高速ルーティング) の精密版。多軸の精度プロファイルを提供。

# ABPP アンカー embedding ファイル (同一ディレクトリ)
_ABPP_ANCHOR_PATH = Path(__file__).parent / "abpp_anchors.json"

# IEF 4軸の定義
_IEF_AXES = [
    ("tech_precise", "tech_vague"),
    ("proc_precise", "proc_vague"),
    ("concept_precise", "concept_vague"),
    ("judge_precise", "judge_vague"),
]

# 軸の短縮名
_AXIS_SHORT_NAMES = ["tech", "proc", "concept", "judge"]


@dataclass(frozen=True)
class ABPPResult:
    """ABPP (Anchor-Based Precision Profiling) v5 の結果。

    3手法アンサンブルによるテキスト精度プロファイル。
    ensemble が最終的な精度スコア [0, 1]。
    axis_scores で軸別の詳細を提供。
    """

    electrophoresis: float     # 重心偏差スコア [0, 1]。depth < 2 では 0.0
    chromatography: float      # 2極位置スコア [0, 1]
    ief_score: float           # IEF 平均スコア [0, 1]。depth < 1 では 0.0
    ief_pattern: str           # IEF パターン ("----"=低精度, "++++"=高精度, "????"=未計算)
    ensemble: float            # 加重アンサンブル [0, 1]
    axis_scores: dict[str, float]  # 軸別スコア {"tech", "proc", "concept", "judge"} → [0,1]
    api_calls: int             # 消費した API 呼出回数


class ABPPCalculator:
    """ABPP 3手法アンサンブル計算器。

    化学的分離法のアナロジーでテキスト embedding の精度を測定する。
    - Electrophoresis: embedding 重心からの偏差 (高精度ほど偏差大)
    - Chromatography: simple/complex 2極間の位置 (simple 寄り = 高精度)
    - IEF v2: 4軸 (tech/proc/concept/judge) の precise/vague 差分プロファイル

    最適重み (v3 実験で最適化済み, N=20, ρ=+0.89):
        E=0.2, C=0.3, I=0.5
    """

    # アンサンブル重み
    W_ELECTRO = 0.2
    W_CHROM = 0.3
    W_IEF = 0.5

    def __init__(self) -> None:
        self._anchors: dict[str, list[float]] = {}
        self._anchors_loaded: bool = False


    def _ensure_anchors(self) -> bool:
        """アンカー embedding をロードする (遅延ロード)。

        Returns:
            True: ロード成功, False: ファイルなしまたは不完全
        """
        if self._anchors_loaded:
            return bool(self._anchors)

        self._anchors_loaded = True

        if not _ABPP_ANCHOR_PATH.exists():
            logger.warning("ABPP アンカーファイルが見つかりません: %s", _ABPP_ANCHOR_PATH)
            return False

        try:
            with open(_ABPP_ANCHOR_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 必須キーの検証
            required_keys = set()
            for p, v in _IEF_AXES:
                required_keys.add(p)
                required_keys.add(v)
            required_keys.add("simple")
            required_keys.add("complex")

            missing = required_keys - set(data.keys())
            if missing:
                logger.error("ABPP アンカーにキーが不足: %s", missing)
                return False

            self._anchors = data
            logger.info("ABPP アンカーをロード: %d キー", len(data))
            return True

        except (json.JSONDecodeError, IOError) as e:
            logger.error("ABPP アンカーのロード失敗: %s", e)
            return False

    def _get_embedding(self, text: str) -> Optional[list[float]]:
        """Gemini API でテキストの embedding を取得する。

        既存の _get_embed_client を再利用。
        """
        client = _get_embed_client()
        if client is None:
            return None

        try:
            from google.genai import types as _types
            result = client.models.embed_content(
                model=MODEL_NAME,
                contents=text.strip(),
                config=_types.EmbedContentConfig(
                    output_dimensionality=EMBED_DIM,
                ),
            )
            return result.embeddings[0].values
        except Exception as e:  # noqa: BLE001
            logger.error("ABPP embedding 取得失敗: %s", e)
            return None

    def _electrophoresis(self, embedding: list[float]) -> float:
        """電気泳動法: 全アンカー重心からの cos sim 偏差。

        高精度テキストは特定のアンカー群に強く引き寄せられるため、
        重心からの偏差 (cos sim のばらつき) が大きくなる。

        Returns:
            正規化されたスコア [0, 1]
        """
        # 全アンカーとの cos sim を計算
        sims = []
        for key, anchor_vec in self._anchors.items():
            sims.append(_cosine_similarity(embedding, anchor_vec))

        if not sims:
            return 0.0

        # 重心 (平均 cos sim) からの偏差
        mean_sim = _statistics.mean(sims)
        deviations = [(s - mean_sim) ** 2 for s in sims]
        std_dev = math.sqrt(_statistics.mean(deviations))

        # 正規化: N=20 実験で std_dev の 95th percentile ≈ 0.048
        # 0.05 を上限として [0, 1] に正規化 (P2: 根拠明示)
        normalized = min(std_dev / 0.05, 1.0)
        return normalized

    def _chromatography(self, embedding: list[float]) -> float:
        """クロマトグラフィー法: simple/complex 2極間の位置。

        v3 の compute_context_precision と同じ原理だが、
        [0, 1] に正規化して返す (v3 は [-1, +1] の diff)。

        Returns:
            正規化されたスコア [0, 1] (simple 寄り=高精度=1.0)
        """
        anchor_simple = self._anchors.get("simple", [])
        anchor_complex = self._anchors.get("complex", [])

        if not anchor_simple or not anchor_complex:
            return 0.5  # fallback

        sim_s = _cosine_similarity(embedding, anchor_simple)
        sim_c = _cosine_similarity(embedding, anchor_complex)

        # diff を [-1, +1] → [0, 1] に正規化
        diff = sim_s - sim_c
        return max(0.0, min(1.0, (diff + 1.0) / 2.0))

    def _ief(self, embedding: list[float]) -> tuple[float, str, list[float]]:
        """等電点電気泳動法 v2: 4軸パターン。

        4軸 (tech/proc/concept/judge) の precise/vague アンカーとの
        cos sim 差分からパターンを生成する。

        Returns:
            (正規化スコア [0, 1], パターン文字列 "+-+-" 等, 軸別 raw diffs)
        """
        diffs: list[float] = []
        for p_key, v_key in _IEF_AXES:
            anchor_p = self._anchors.get(p_key, [])
            anchor_v = self._anchors.get(v_key, [])
            if not anchor_p or not anchor_v:
                diffs.append(0.0)
                continue

            sim_p = _cosine_similarity(embedding, anchor_p)
            sim_v = _cosine_similarity(embedding, anchor_v)
            diffs.append(sim_p - sim_v)

        # パターン生成: 正 = +, 負 = -
        pattern = "".join("+" if d > 0 else "-" for d in diffs)

        # 平均差分を [0, 1] に正規化
        mean_diff = _statistics.mean(diffs) if diffs else 0.0
        # N=20 実験で mean_diff の range ≈ [-0.048, +0.052]
        # 0.05 を半幅として [0, 1] に正規化 (P2: 根拠明示)
        normalized = max(0.0, min(1.0, (mean_diff + 0.05) / 0.10))

        return normalized, pattern, diffs

    def _compute_ensemble(
        self, electro: float, chrom: float, ief: float
    ) -> float:
        """3手法の加重アンサンブルを算出する。

        Returns:
            加重平均スコア [0, 1]
        """
        return (
            self.W_ELECTRO * electro
            + self.W_CHROM * chrom
            + self.W_IEF * ief
        )

    def compute(self, text: str, depth: int = 2) -> ABPPResult:
        """テキストの ABPP 精度プロファイルを算出する。

        depth 別の手法選択:
            depth=0: Chromatography 単体 (最速, API 1回)
            depth=1: Chromatography + IEF (API 1回, アンカーは事前計算)
            depth=2: 全3手法 (API 1回, アンカーは事前計算)

        Args:
            text: 分析対象テキスト
            depth: 分析深度 (0/1/2)

        Returns:
            ABPPResult
        """
        # アンカーチェック
        if not self._ensure_anchors():
            logger.warning("ABPP アンカー未準備。fallback (ensemble=0.5)")
            return ABPPResult(
                electrophoresis=0.0, chromatography=0.5,
                ief_score=0.0, ief_pattern="????",
                ensemble=0.5,
                axis_scores={n: 0.5 for n in _AXIS_SHORT_NAMES},
                api_calls=0,
            )

        # テキストの embedding を取得 (API 1回)
        embedding = self._get_embedding(text)
        if embedding is None:
            logger.warning("ABPP embedding 取得失敗。fallback (ensemble=0.5)")
            return ABPPResult(
                electrophoresis=0.0, chromatography=0.5,
                ief_score=0.0, ief_pattern="????",
                ensemble=0.5,
                axis_scores={n: 0.5 for n in _AXIS_SHORT_NAMES},
                api_calls=0,
            )

        api_calls = 1  # テキスト embedding のみ (アンカーは事前計算)

        # --- 手法別計算 (depth で制御) ---

        # Chromatography (常に実行)
        chrom_score = self._chromatography(embedding)

        # IEF v2 (depth >= 1) — P3: diffs を再利用して axis_scores の二重計算を排除
        ief_diffs: list[float] = []
        if depth >= 1:
            ief_score, ief_pattern, ief_diffs = self._ief(embedding)
        else:
            ief_score = 0.0
            ief_pattern = "????"

        # Electrophoresis (depth >= 2)
        if depth >= 2:
            electro_score = self._electrophoresis(embedding)
        else:
            electro_score = 0.0

        # --- 軸別スコア (P3: _ief の diffs を再利用 / P4: depth=0 ではスキップ) ---
        if depth >= 1 and ief_diffs:
            # _ief が計算済みの diffs を正規化して axis_scores に変換
            axis_scores: dict[str, float] = {}
            for i, d in enumerate(ief_diffs):
                axis_scores[_AXIS_SHORT_NAMES[i]] = max(0.0, min(1.0, (d + 0.05) / 0.10))
        else:
            # depth=0: 軸別スコアは中立値 (P4: 不要な計算を排除)
            axis_scores = {n: 0.5 for n in _AXIS_SHORT_NAMES}

        # --- アンサンブル ---
        # depth に応じて重みを再配分
        if depth == 0:
            # クロマト単体
            ensemble = chrom_score
        elif depth == 1:
            # クロマト + IEF (E の重みを C と I に配分)
            w_c = self.W_CHROM + self.W_ELECTRO * (self.W_CHROM / (self.W_CHROM + self.W_IEF))
            w_i = self.W_IEF + self.W_ELECTRO * (self.W_IEF / (self.W_CHROM + self.W_IEF))
            ensemble = w_c * chrom_score + w_i * ief_score
        else:
            # 全3手法
            ensemble = self._compute_ensemble(electro_score, chrom_score, ief_score)

        return ABPPResult(
            electrophoresis=electro_score,
            chromatography=chrom_score,
            ief_score=ief_score,
            ief_pattern=ief_pattern,
            ensemble=ensemble,
            axis_scores=axis_scores,
            api_calls=api_calls,
        )


# ABPP Singleton
_abpp_calculator: Optional[ABPPCalculator] = None


def compute_abpp(text: str, depth: int = 2) -> ABPPResult:
    """ABPP 精度プロファイルの公開 API (singleton)。

    precision_router の既存 API と並行して使用可能:
      - compute_context_precision: 1テキスト → diff (v3 高速ルーティング)
      - compute_ensemble_chunk_precisions: N チャンク → RSA精度 (v4)
      - compute_abpp: 1テキスト → 多軸精度プロファイル (v5 精密診断)

    Args:
        text: 分析対象テキスト
        depth: 分析深度 (0=クロマト単体, 1=+IEF, 2=全3手法)

    Returns:
        ABPPResult (ensemble, axis_scores, ief_pattern 等)
    """
    global _abpp_calculator
    if _abpp_calculator is None:
        _abpp_calculator = ABPPCalculator()
    return _abpp_calculator.compute(text, depth=depth)
