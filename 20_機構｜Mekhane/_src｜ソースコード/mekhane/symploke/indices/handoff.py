# PROOF: [L2/インフラ] <- mekhane/symploke/indices/handoff.py A0→索引管理が必要→handoff が担う
"""
Handoff Index - DomainIndex for Handoff search

Native DomainIndex implementation for handoff data.
Uses VectorStore for vector search with cached/persistent index.
"""

from typing import List, Dict, Optional
from pathlib import Path
import numpy as np

from .base import DomainIndex, SourceType, Document, IndexedResult
from ..adapters.base import VectorStoreAdapter


from mekhane.paths import HANDOFF_DIR, INDEX_DIR

# Persistent index path
HANDOFF_INDEX_PATH = INDEX_DIR / "handoffs.pkl"


# PURPOSE: Handoff のネイティブ DomainIndex
class HandoffIndex(DomainIndex):
    """
    Handoff: セッション引き継ぎのネイティブ DomainIndex

    Features:
        - Handoff ファイルからの自動ロード
        - VectorStore によるベクトル検索
        - 永続化インデックスのキャッシュ

    Usage:
        adapter = VectorStore()
        handoff = HandoffIndex(adapter)
        handoff.initialize()
        results = handoff.search("previous session context", k=5)
    """

    # PURPOSE: 初期化
    def __init__(
        self,
        adapter: VectorStoreAdapter,
        name: str = "handoff",
        dimension: int = 0,  # 0 = auto-detect from adapter
        embed_fn: Optional[callable] = None,
    ):
        """
        Args:
            adapter: ベクトルストアアダプタ (VectorStore)
            name: インデックス名
            dimension: ベクトル次元数 (0 = adapter から自動検出)
            embed_fn: テキスト→ベクトル変換関数 (None = adapter.encode を使用)
        """
        # dimension=0 の場合、initialize 時に自動検出する
        super().__init__(adapter, name, dimension or 3072)
        self._embed_fn = embed_fn
        self._doc_store: Dict[str, Document] = {}
        self._auto_dimension = dimension == 0

    @property
    def source_type(self) -> SourceType:
        return SourceType.HANDOFF

    def _embed(self, text: str) -> np.ndarray:
        """テキストをベクトル化"""
        if self._embed_fn is not None:
            return self._embed_fn(text)
        # VectorStore.encode を使用
        if hasattr(self._adapter, "encode"):
            vecs = self._adapter.encode([text])
            return vecs[0]
        return np.random.randn(self._dimension).astype(np.float32)

    def _detect_dimension(self) -> int:
        """adapter から dimension を自動検出"""
        if hasattr(self._adapter, "dimension") and self._adapter.dimension:
            return self._adapter.dimension
        if hasattr(self._adapter, "encode"):
            test_vec = self._adapter.encode(["test"])
            return test_vec.shape[1]
        return 3072  # fallback

    def initialize(self) -> None:
        """Initialize with auto-dimension detection and persistent index load."""
        if self._initialized:
            return

        # Auto-detect dimension
        if self._auto_dimension:
            self._dimension = self._detect_dimension()

        # Try to load persistent index first
        if HANDOFF_INDEX_PATH.exists():
            try:
                self._adapter.load(str(HANDOFF_INDEX_PATH))
                self._initialized = True
                # Load docs for content retrieval
                self._load_doc_store()
                return
            except Exception:  # noqa: BLE001
                pass  # Fall through to fresh init

        # Fresh init with auto-ingestion
        self._adapter.create_index(
            dimension=self._dimension, index_name=self._name
        )
        self._initialized = True
        self._auto_ingest()

    def _load_doc_store(self) -> None:
        """Load handoff documents into doc_store for content retrieval."""
        from ..kairos_ingest import get_handoff_files, parse_handoff

        files = get_handoff_files()
        for f in files:
            doc = parse_handoff(f)
            self._doc_store[doc.id] = doc

    def _auto_ingest(self) -> None:
        """Auto-ingest all handoff files on first init."""
        from ..kairos_ingest import get_handoff_files, parse_handoff

        files = get_handoff_files()
        if not files:
            return

        docs = [parse_handoff(f) for f in files]
        self.ingest(docs)

        # Persist index
        HANDOFF_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._adapter.save(str(HANDOFF_INDEX_PATH))

    def ingest(self, documents: List[Document]) -> int:
        """
        Handoff をインジェスト

        Args:
            documents: Document のリスト

        Returns:
            追加されたドキュメント数
        """
        if not self._initialized:
            self.initialize()

        vectors = []
        metadata_list = []

        for doc in documents:
            if doc.embedding is not None:
                vec = np.array(doc.embedding, dtype=np.float32)
            else:
                vec = self._embed(doc.content)

            vectors.append(vec)
            metadata_list.append({
                "doc_id": doc.id,
                "source": self.source_type.value,
                "idx": len(self._doc_store),
                "primary_task": doc.metadata.get("primary_task", ""),
                "timestamp": doc.metadata.get("timestamp", ""),
                "file_path": doc.metadata.get("file_path", ""),
                **{k: v for k, v in doc.metadata.items()
                   if k not in ("primary_task", "timestamp", "file_path")},
            })
            self._doc_store[doc.id] = doc

        if vectors:
            vectors_array = np.stack(vectors)
            self._adapter.add_vectors(vectors_array, metadata=metadata_list)

        return len(documents)

    def search(
        self,
        query: str,
        k: int = 10,
        **kwargs
    ) -> List[IndexedResult]:
        """
        Handoff を検索

        Args:
            query: 検索クエリ
            k: 取得件数

        Returns:
            IndexedResult のリスト
        """
        if not self._initialized:
            return []

        query_vec = self._embed(query)
        adapter_results = self._adapter.search(query_vec, k=k)

        results = []
        for r in adapter_results:
            doc_id = r.metadata.get("doc_id", str(r.id))
            doc = self._doc_store.get(doc_id)

            # Title: primary_task → filename date → ID
            title = r.metadata.get("primary_task", "")
            if not title or title == "Unknown":
                fp = r.metadata.get("file_path", "")
                if fp:
                    fname = Path(fp).stem
                    parts = fname.replace("handoff_", "").split("_")
                    if len(parts) >= 2:
                        date_part = parts[0]
                        time_part = parts[1]
                        if len(time_part) == 4:
                            time_part = f"{time_part[:2]}:{time_part[2:]}"
                        title = f"Handoff {date_part} {time_part}"
                    else:
                        title = fname
                else:
                    title = doc_id

            results.append(
                IndexedResult(
                    doc_id=doc_id,
                    score=r.score,
                    source=self.source_type,
                    content=doc.content[:200] if doc else "",
                    metadata={
                        **r.metadata,
                        "title": title,
                    },
                )
            )

        return results[:k]
