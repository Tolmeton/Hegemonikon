from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/anamnesis/nucleator_splitter.py
"""PROOF: [L2/インフラ] このファイルは存在しなければならない

P3 → Nucleator アルゴリズムを外部エコシステムから利用可能にする
   → storage-agnostic な chunking interface が必要
   → NucleatorSplitter が LangChain / LlamaIndex / 任意の RAG パイプラインへの橋渡し
   → nucleator_splitter.py が adapter 実装

Q.E.D.

---

NucleatorSplitter — Storage-Agnostic Adapter for Nucleator Chunking

PURPOSE: chunker_nucleator.py の G∘F 不動点アルゴリズムを、
  LangChain TextSplitter プロトコルおよび任意の embedding backend から
  利用可能にする薄い adapter 層。

設計原則:
  1. chunker_nucleator.py に一切の変更を加えない
  2. LangChain は optional dependency (なくても動作する)
  3. embedding は Callable[[list[str]], list[list[float]]] を受け取る
  4. 入力: 生テキスト → 出力: テキストチャンクのリスト

理論的位置づけ:
  CKDF L3 (Nucleator) と L0 (embedding 格子) の間の射。
  Nucleator が storage-agnostic であることの operationalization。
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Callable, Protocol, runtime_checkable

from mekhane.anamnesis.chunker_nucleator import (
    Chunk,
    ChunkingResult,
    Step,
    chunk_session,
)

logger = logging.getLogger(__name__)


# ── Embedding Protocol ───────────────────────────────────────────────

@runtime_checkable
class EmbedFn(Protocol):
    """Embedding 関数のプロトコル。

    任意の embedding backend を受け入れる最小インターフェース。
    EmbedderMixin.embed_batch と同一シグネチャ。

    実装例:
      - mekhane.anamnesis.vertex_embedder.VertexEmbedder().embed_batch
      - sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2').encode
      - openai.embeddings.create のラッパー
      - chromadb.utils.embedding_functions のラッパー
    """

    def __call__(self, texts: list[str]) -> list[list[float]]:
        ...


# ── Text → Step パーサー ─────────────────────────────────────────────

@dataclass
class StepParserConfig:
    """テキストを Step 列に分割する設定。"""
    separator: str = "\n\n"
    min_chars: int = 20
    strip_whitespace: bool = True


def parse_text_to_steps(
    text: str,
    config: StepParserConfig | None = None,
) -> list[Step]:
    """生テキストを Step 列に分割。

    デフォルトは空行 (\\n\\n) で分割し、短すぎる断片を除去。
    MemPalace や LangChain のパイプラインから呼ぶ際の前処理。
    """
    cfg = config or StepParserConfig()
    raw_parts = text.split(cfg.separator)

    steps: list[Step] = []
    for i, part in enumerate(raw_parts):
        cleaned = part.strip() if cfg.strip_whitespace else part
        if len(cleaned) >= cfg.min_chars:
            steps.append(Step(index=len(steps), text=cleaned))

    return steps


# ── NucleatorSplitter (Standalone) ───────────────────────────────────

class NucleatorSplitter:
    """Nucleator G∘F 不動点チャンキングの storage-agnostic adapter。

    LangChain なしで動作するスタンドアロン版。
    LangChain 互換版は NucleatorTextSplitter を使用。

    使用例 (最小):
        from mekhane.anamnesis.nucleator_splitter import NucleatorSplitter

        splitter = NucleatorSplitter(embed_fn=my_embedder.embed_batch)
        chunks = splitter.split_text("長いテキスト...")
        # → ["チャンク1のテキスト", "チャンク2のテキスト", ...]

    使用例 (詳細結果):
        result = splitter.split_text_detailed("長いテキスト...")
        # → ChunkingResult (chunks, metrics, convergence info)
    """

    def __init__(
        self,
        embed_fn: Callable[[list[str]], list[list[float]]],
        *,
        tau: float | str = "auto",
        min_steps: int = 2,
        max_iterations: int = 10,
        sim_mode: str = "pairwise",
        sim_k: int = 3,
        auto_lambda: bool = True,
        step_parser: StepParserConfig | None = None,
    ) -> None:
        """初期化。

        Args:
            embed_fn: テキストリストを embedding ベクトルに変換する関数。
                      シグネチャ: (list[str]) -> list[list[float]]
            tau: 境界検出閾値。"auto" で統計的決定 (μ - 1.5σ)。
            min_steps: チャンクの最小ステップ数。
            max_iterations: G∘F 反復の上限。
            sim_mode: "pairwise" (1次マルコフ) or "knn" (非線形)。
            sim_k: knn モードの k 値。
            auto_lambda: True で τ 依存 λ スケジュール使用。
            step_parser: テキスト→Step 分割の設定。
        """
        self._embed_fn = embed_fn
        self._tau = tau
        self._min_steps = min_steps
        self._max_iterations = max_iterations
        self._sim_mode = sim_mode
        self._sim_k = sim_k
        self._auto_lambda = auto_lambda
        self._step_parser = step_parser or StepParserConfig()

    def split_text(self, text: str) -> list[str]:
        """テキストを Nucleator でチャンク分割し、テキストのリストを返す。

        LangChain TextSplitter.split_text() と同一シグネチャ。
        """
        result = self.split_text_detailed(text)
        return [chunk.text for chunk in result.chunks]

    def split_text_detailed(
        self,
        text: str,
        session_id: str = "",
    ) -> ChunkingResult:
        """テキストを Nucleator でチャンク分割し、全メトリクスを含む結果を返す。

        split_text() の詳細版。G∘F 収束情報、L(c) メトリクス、
        precision 値などを含む ChunkingResult を返す。
        """
        # 1. Text → Steps
        steps = parse_text_to_steps(text, self._step_parser)

        if not steps:
            return ChunkingResult(
                session_id=session_id, chunks=[], converged=True
            )

        # 2. Steps → Embeddings
        texts = [s.text for s in steps]
        embeddings = self._embed_fn(texts)

        if len(embeddings) != len(steps):
            raise ValueError(
                f"embed_fn が返した embedding 数 ({len(embeddings)}) と "
                f"step 数 ({len(steps)}) が不一致"
            )

        # 3. Nucleator chunk_session (G∘F 不動点)
        return chunk_session(
            steps=steps,
            embeddings=embeddings,
            session_id=session_id,
            tau=self._tau,
            min_steps=self._min_steps,
            max_iterations=self._max_iterations,
            sim_mode=self._sim_mode,
            sim_k=self._sim_k,
            auto_lambda=self._auto_lambda,
        )

    def split_documents(
        self,
        documents: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """ドキュメントリストを分割。LangChain Document 互換の dict 版。

        入力/出力: [{"page_content": str, "metadata": dict}, ...]
        各ドキュメントを個別にチャンク分割し、metadata を継承する。
        """
        result_docs: list[dict[str, Any]] = []

        for doc in documents:
            content = doc.get("page_content", "")
            metadata = doc.get("metadata", {})

            chunks = self.split_text(content)
            for i, chunk_text in enumerate(chunks):
                result_docs.append({
                    "page_content": chunk_text,
                    "metadata": {
                        **metadata,
                        "chunk_index": i,
                        "chunker": "nucleator_gf",
                    },
                })

        return result_docs


# ── LangChain TextSplitter Adapter (Optional) ────────────────────────

def _create_langchain_splitter_class():
    """LangChain TextSplitter サブクラスを動的に生成。

    langchain がインストールされていない場合は None を返す。
    モジュールロード時に langchain を要求しない設計。
    """
    try:
        from langchain_text_splitters import TextSplitter
    except ImportError:
        try:
            from langchain.text_splitter import TextSplitter
        except ImportError:
            return None

    class _NucleatorTextSplitter(TextSplitter):
        """LangChain TextSplitter プロトコル準拠の Nucleator adapter。

        使用例:
            from mekhane.anamnesis.nucleator_splitter import NucleatorTextSplitter

            splitter = NucleatorTextSplitter(embed_fn=embedder.embed_batch)
            docs = splitter.split_documents(documents)
        """

        def __init__(
            self,
            embed_fn: Callable[[list[str]], list[list[float]]],
            *,
            tau: float | str = "auto",
            min_steps: int = 2,
            max_iterations: int = 10,
            sim_mode: str = "pairwise",
            sim_k: int = 3,
            auto_lambda: bool = True,
            step_parser: StepParserConfig | None = None,
            **kwargs: Any,
        ) -> None:
            # TextSplitter の __init__ を呼ぶ
            # chunk_size/chunk_overlap は Nucleator では不使用だが
            # LangChain の型チェックを通すために渡す
            super().__init__(
                chunk_size=kwargs.pop("chunk_size", 1000),
                chunk_overlap=kwargs.pop("chunk_overlap", 0),
                **kwargs,
            )
            self._nucleator = NucleatorSplitter(
                embed_fn=embed_fn,
                tau=tau,
                min_steps=min_steps,
                max_iterations=max_iterations,
                sim_mode=sim_mode,
                sim_k=sim_k,
                auto_lambda=auto_lambda,
                step_parser=step_parser,
            )

        def split_text(self, text: str) -> list[str]:
            """TextSplitter プロトコル実装。"""
            return self._nucleator.split_text(text)

    return _NucleatorTextSplitter


# モジュールレベルで LangChain adapter を生成 (import 時に解決)
NucleatorTextSplitter = _create_langchain_splitter_class()
"""LangChain TextSplitter 互換クラス。

langchain がインストールされていない場合は None。
使用前に ``if NucleatorTextSplitter is not None:`` でチェック。
"""
