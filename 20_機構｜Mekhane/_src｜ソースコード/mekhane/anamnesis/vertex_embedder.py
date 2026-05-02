#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/anamnesis/vertex_embedder.py
"""
PROOF: [L2/インフラ]

A0 → 埋め込みベクトル生成が必要
   → Gemini Embedding API で生成
   → vertex_embedder.py が担う

Q.E.D.

---

Vertex AI / Gemini Embedding — Developer API (API Key) ラッパー

サポートモデル:
  - gemini-embedding-2-preview: 最大 3072d, 8192 入力トークン, マルチモーダル
  - gemini-embedding-001: 最大 3072d (3072d 推奨)
  - text-embedding-005: 最大 768d
  - text-embedding-004: 最大 768d (legacy)

認証:
  環境変数から Google API Key を読み込み、ラウンドロビンで分散。
  GOOGLE_API_KEY           → デフォルト (makaron8426)
  GOOGLE_API_KEY_MOVEMENT  → movement
  GOOGLE_API_KEY_TOLMETON → Tolmeton
  etc.

旧 Vertex AI 方式 (ADC/SA + project + IAM) は廃止。
"""

import os
import logging
import itertools
import threading

from mekhane.anamnesis.embedder_mixin import EmbedderMixin

logger = logging.getLogger(__name__)


# --- API Key ラウンドロビン ---

_KEY_ENV_NAMES = [
    "GOOGLE_API_KEY_MOVEMENT",   # デフォルト (movement)
    "GOOGLE_API_KEY",            # makaron8426
    "GOOGLE_API_KEY_TOLMETON",
    "GOOGLE_API_KEY_RAIRAIXOXOXO",
    "GOOGLE_API_KEY_HRAIKI",
]


def _load_api_keys() -> list[str]:
    """環境変数から有効な API Key を収集。"""
    keys = []
    for name in _KEY_ENV_NAMES:
        val = os.getenv(name, "").strip()
        if val:
            keys.append(val)
    return keys


class VertexEmbedder(EmbedderMixin):
    """Gemini Embedding (Developer API) — API Key ラウンドロビン。

    後方互換のためクラス名は VertexEmbedder のまま。
    similarity / novelty / pairwise_novelty は EmbedderMixin から継承。
    """

    # Model → max dimension mapping (constants.py の MODEL_MAX_DIMS と同期)
    _MODEL_MAX_DIMS: dict[str, int] = {
        "gemini-embedding-2-preview": 3072,
        "gemini-embedding-001": 3072,
        "text-embedding-005": 768,
        "text-embedding-004": 768,
    }

    def __init__(
        self,
        model_name: str | None = None,
        dimension: int | None = None,
        credentials_file: str = "",  # 後方互換 (無視される)
    ):
        # デフォルト値は constants.py から取得
        from mekhane.anamnesis.constants import EMBED_MODEL, EMBED_DIM
        if model_name is None:
            model_name = EMBED_MODEL
        if dimension is None:
            dimension = EMBED_DIM
        self.model_name = model_name
        max_dim = self._MODEL_MAX_DIMS.get(model_name, 768)
        if dimension > max_dim:
            raise ValueError(
                f"[VertexEmbedder] {model_name} の最大次元は {max_dim}d です "
                f"({dimension}d は不可)。"
            )
        self._dimension = dimension
        self._use_gpu = False

        # --- API Key 収集 ---
        self._api_keys = _load_api_keys()
        if not self._api_keys:
            raise ValueError(
                "[VertexEmbedder] Google API Key が見つかりません。\n"
                "  .env に GOOGLE_API_KEY=AIzaSy... を設定してください。"
            )

        # ラウンドロビン用サイクラー (thread-safe)
        self._key_cycle = itertools.cycle(self._api_keys)
        self._key_lock = threading.Lock()

        # 初期クライアント作成 (最初のキーで)
        self._client = self._make_client(self._api_keys[0])

        logger.info(
            "[VertexEmbedder] initialized. model=%s, dim=%d, api_keys=%d, auth=API_KEY",
            model_name, self._dimension, len(self._api_keys),
        )

    def _make_client(self, api_key: str):
        """API Key で genai.Client を作成。"""
        from google import genai
        return genai.Client(api_key=api_key)

    def _next_client(self):
        """ラウンドロビンで次のクライアントを返す。"""
        with self._key_lock:
            key = next(self._key_cycle)
        return self._make_client(key)

    # embed() は EmbedderMixin から継承:
    #   embed(text) → embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """複数テキストの埋め込みベクトルをバッチ取得。

        API Key ラウンドロビン: バッチごとに異なるキーを並列使用。
        429 (quota exhausted) 時は次のキーにフォールオーバー。
        """
        from google.genai import types
        from concurrent.futures import ThreadPoolExecutor, as_completed

        BATCH_SIZE = 50  # Gemini API limit=100, 安全マージン確保
        config = types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=self._dimension,
        )

        # バッチ分割
        batches = []
        for i in range(0, len(texts), BATCH_SIZE):
            batches.append((i, texts[i: i + BATCH_SIZE]))

        if len(batches) <= 1:
            # 単一バッチ: 逐次実行 (オーバーヘッド回避)
            return self._embed_single_batch(batches[0][1], config) if batches else []

        # 複数バッチ: 並列実行 (max_workers = キー数)
        results: dict[int, list[list[float]]] = {}
        max_workers = min(len(self._api_keys), len(batches))

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {}
            for idx, batch_texts in batches:
                future = pool.submit(self._embed_single_batch, batch_texts, config)
                futures[future] = idx

            for future in as_completed(futures):
                idx = futures[future]
                results[idx] = future.result()  # raises if failed

        # 元の順序で結合
        all_embeddings: list[list[float]] = []
        for idx, _ in batches:
            all_embeddings.extend(results[idx])
        return all_embeddings

    def _embed_single_batch(
        self, texts: list[str], config
    ) -> list[list[float]]:
        """単一バッチの埋め込み取得 + 429 フォールオーバー。"""
        client = self._next_client()
        last_error = None

        for attempt in range(len(self._api_keys)):
            try:
                result = client.models.embed_content(
                    model=self.model_name,
                    contents=texts,
                    config=config,
                )
                return [e.values for e in result.embeddings]
            except Exception as e:  # noqa: BLE001
                last_error = e
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    logger.warning(
                        "[VertexEmbedder] Key exhausted (attempt %d/%d), rotating...",
                        attempt + 1, len(self._api_keys),
                    )
                    client = self._next_client()
                    continue
                raise

        logger.error("[VertexEmbedder] All keys exhausted: %s", last_error)
        raise last_error  # type: ignore[misc]
