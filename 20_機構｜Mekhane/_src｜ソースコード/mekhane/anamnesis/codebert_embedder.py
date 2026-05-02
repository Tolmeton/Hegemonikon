from __future__ import annotations
# PROOF: mekhane/anamnesis/codebert_embedder.py
# PURPOSE: CodeBERT ベースの embedder — CCL 構造を高精度で保持
"""CodeBertEmbedder — microsoft/codebert-base を使用した コード特化 embedder。

Sweep 実験結果:
  CodeBERT:       ρ=0.507 (CCL 文字列距離 ρ=0.521 にほぼ匹敵)
  VertexEmbedder: ρ=0.245 (構造情報を 53% 喪失)

EmbedderMixin を継承し、embed_batch() のみを実装。
GPU が利用可能な場合は自動で CUDA を使用。

Usage:
    embedder = CodeBertEmbedder()
    vecs = embedder.embed_batch(["_ >> fn >> I:[ok]{_ >> pred}", "_ >> fn"])
"""


import logging
from typing import Optional

import numpy as np

from mekhane.anamnesis.embedder_mixin import EmbedderMixin

logger = logging.getLogger(__name__)

# CodeBERT の出力次元
CODEBERT_DIM = 768
# モデル名
CODEBERT_MODEL = "microsoft/codebert-base"


class CodeBertEmbedder(EmbedderMixin):
    """CodeBERT (microsoft/codebert-base) を使用した embedder。

    CCL 式の構造的距離を embedding 空間上で高精度に保持する。
    768 次元の dense embedding を生成。

    embed_batch() が唯一のプリミティブ。
    similarity, novelty 等は EmbedderMixin から継承。
    """

    def __init__(
        self,
        model_name: str = CODEBERT_MODEL,
        max_length: int = 512,
        batch_size: int = 32,
        device: Optional[str] = None,
    ):
        """初期化。

        Args:
            model_name: HuggingFace モデル名。
            max_length: トークン最大長。CCL 式は通常短いので 512 で十分。
            batch_size: バッチサイズ。
            device: 'cuda', 'cpu', None (自動検出)。
        """
        self._model_name = model_name
        self._max_length = max_length
        self._batch_size = batch_size
        self._tokenizer = None
        self._model = None
        self._device = device
        self._dimension = CODEBERT_DIM

    def _ensure_loaded(self):
        """遅延ロード — 初回 embed_batch 呼出時にモデルを読み込む。"""
        if self._model is not None:
            return

        try:
            import torch
            from transformers import AutoModel, AutoTokenizer
        except ImportError as e:
            raise RuntimeError(
                "CodeBertEmbedder requires torch and transformers. "
                "Install with: pip install torch transformers"
            ) from e

        # デバイス自動検出
        if self._device is None:
            self._device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(
            "CodeBertEmbedder loading %s on %s",
            self._model_name, self._device,
        )

        self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        self._model = AutoModel.from_pretrained(self._model_name)
        self._model.to(self._device)
        self._model.eval()

        logger.info(
            "CodeBertEmbedder ready: %s, %dd, device=%s",
            self._model_name, self._dimension, self._device,
        )

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """テキストのバッチを embedding に変換。

        [CLS] トークンの hidden state を使用 (CodeBERT の pooled output)。
        入力は L2 正規化しない — EmbedderMixin の derived methods が正規化する。

        Args:
            texts: CCL 式またはテキストのリスト。

        Returns:
            list of 768d float vectors.
        """
        import torch

        self._ensure_loaded()

        all_embeddings = []

        for i in range(0, len(texts), self._batch_size):
            batch_texts = texts[i:i + self._batch_size]
            inputs = self._tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=self._max_length,
                return_tensors="pt",
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self._model(**inputs)

            # [CLS] トークンの hidden state (バッチ x 768)
            cls_embeddings = outputs.last_hidden_state[:, 0, :]
            all_embeddings.extend(cls_embeddings.cpu().numpy().tolist())

        return all_embeddings

    @property
    def dimension(self) -> int:
        """Embedding 次元数。"""
        return self._dimension
