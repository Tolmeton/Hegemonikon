# PROOF: [L2/インフラ] <- mekhane/symploke/indices/doxa.py A0→Doxa 検索が必要→doxa が担う
"""
Doxa Index - DomainIndex for Beliefs search

Beliefs/_global と _project の Doxa を自動投入し、
Symplokē の検索面に prior / belief 層を追加する。
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import re

import numpy as np

from .base import DomainIndex, SourceType, Document, IndexedResult
from ..adapters.base import VectorStoreAdapter
from mekhane.paths import INDEX_DIR, MNEME_BELIEFS


DOXA_INDEX_PATH = INDEX_DIR / "doxa.pkl"
DOXA_FAISS_PATH = DOXA_INDEX_PATH.with_suffix(".faiss")
DOXA_META_PATH = DOXA_INDEX_PATH.with_suffix(".meta")
DOXA_DIRS = [
    MNEME_BELIEFS / "_global",
    MNEME_BELIEFS / "_project",
]

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
ACTION_BLOCK_RE = re.compile(r"<:content action:\s*(.*?)\s*/content:>", re.DOTALL)
EVIDENCE_BLOCK_RE = re.compile(r"<:content evidence:\s*(.*?)\s*/content:>", re.DOTALL)
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{1,}|[一-龠々ぁ-んァ-ヶー]{2,}")


class DoxaIndex(DomainIndex):
    """
    Doxa: 信念 / prior のネイティブ DomainIndex

    Features:
        - Beliefs/_global, _project からの自動ロード
        - trigger / action / evidence を束ねた検索
        - confidence による関連度ブースト
        - 永続化インデックスのキャッシュ
    """

    # PURPOSE: 初期化
    def __init__(
        self,
        adapter: VectorStoreAdapter,
        name: str = "doxa",
        dimension: int = 0,  # 0 = adapter から自動検出
        embed_fn: Optional[callable] = None,
    ):
        super().__init__(adapter, name, dimension or 384)
        self._embed_fn = embed_fn
        self._doc_store: Dict[str, Document] = {}
        self._auto_dimension = dimension == 0

    @property
    def source_type(self) -> SourceType:
        return SourceType.DOXA

    def _hash_embed(self, text: str) -> np.ndarray:
        """埋め込み関数がない初回でも検索不能にしない deterministic fallback。"""
        vector = np.zeros(self._dimension, dtype=np.float32)
        for token in TOKEN_RE.findall(text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for offset in range(0, len(digest), 4):
                chunk = digest[offset: offset + 4]
                if len(chunk) < 4:
                    continue
                index = int.from_bytes(chunk, "big") % self._dimension
                sign = 1.0 if chunk[0] % 2 == 0 else -1.0
                vector[index] += sign
        if not np.any(vector):
            vector[0] = 1.0
        return vector

    def _embed(self, text: str) -> np.ndarray:
        """テキストをベクトル化。"""
        if self._embed_fn is not None:
            return np.asarray(self._embed_fn(text), dtype=np.float32)

        if hasattr(self._adapter, "encode"):
            try:
                vecs = self._adapter.encode([text])
                return np.asarray(vecs[0], dtype=np.float32)
            except Exception:  # noqa: BLE001
                pass

        return self._hash_embed(text)

    def _detect_dimension(self) -> int:
        """adapter / embed_fn から次元数を推定。無理なら fallback。"""
        if hasattr(self._adapter, "dimension") and self._adapter.dimension:
            return self._adapter.dimension
        if self._embed_fn is not None:
            sample = np.asarray(self._embed_fn("dimension-probe"), dtype=np.float32)
            return int(sample.shape[0])
        if hasattr(self._adapter, "encode"):
            try:
                sample = self._adapter.encode(["dimension-probe"])
                return int(sample.shape[1])
            except Exception:  # noqa: BLE001
                pass
        return 384

    def initialize(self) -> None:
        """auto-dimension + persistent index load + 初回 auto-ingest。"""
        if self._initialized:
            return

        if self._auto_dimension:
            self._dimension = self._detect_dimension()

        if DOXA_INDEX_PATH.exists() or (DOXA_FAISS_PATH.exists() and DOXA_META_PATH.exists()):
            try:
                self._adapter.load(str(DOXA_INDEX_PATH))
                self._initialized = True
                self._load_doc_store()
                return
            except Exception:  # noqa: BLE001
                pass

        self._adapter.create_index(dimension=self._dimension, index_name=self._name)
        self._initialized = True
        self._auto_ingest()

    def _list_doxa_files(self) -> list[Path]:
        """Beliefs/_global, _project 配下の doxa_*.typos 一覧。"""
        files: list[Path] = []
        for base_dir in DOXA_DIRS:
            if not base_dir.exists():
                continue
            files.extend(sorted(base_dir.rglob("doxa_*.typos")))
        return sorted(files)

    def _parse_scalar(self, value: str) -> object:
        stripped = value.strip()
        if stripped.startswith('"') and stripped.endswith('"'):
            return stripped[1:-1]
        if stripped.startswith("'") and stripped.endswith("'"):
            return stripped[1:-1]
        if re.fullmatch(r"-?\d+", stripped):
            return int(stripped)
        if re.fullmatch(r"-?\d+\.\d+", stripped):
            return float(stripped)
        return stripped

    def _parse_frontmatter(self, text: str) -> tuple[dict, str]:
        """frontmatter を dict 化し本文と分離する。"""
        match = FRONTMATTER_RE.match(text)
        if not match:
            raise ValueError("frontmatter がありません。")

        frontmatter: dict = {}
        for line in match.group(1).splitlines():
            stripped = line.strip()
            if not stripped or ":" not in stripped:
                continue
            key, value = stripped.split(":", 1)
            frontmatter[key.strip()] = self._parse_scalar(value)

        body = text[match.end():]
        return frontmatter, body

    def _extract_block(self, body: str, pattern: re.Pattern[str]) -> str:
        """Typos content block を抽出。"""
        match = pattern.search(body)
        if not match:
            return ""
        return match.group(1).strip()

    def _parse_doxa_file(self, path: Path) -> Optional[Document]:
        """単一 doxa ファイルを Document に変換。"""
        try:
            text = path.read_text(encoding="utf-8")
            frontmatter, body = self._parse_frontmatter(text)
        except Exception:  # noqa: BLE001
            return None

        belief_id = str(frontmatter.get("id", path.stem.removeprefix("doxa_")))
        scope = str(frontmatter.get("scope", "project"))
        trigger = str(frontmatter.get("trigger", ""))
        domain = str(frontmatter.get("domain", ""))
        confidence = float(frontmatter.get("confidence", 0.0) or 0.0)
        action_text = self._extract_block(body, ACTION_BLOCK_RE)
        evidence_text = self._extract_block(body, EVIDENCE_BLOCK_RE)

        content = "\n".join(
            part for part in [
                belief_id,
                trigger,
                action_text,
                domain,
                evidence_text,
            ]
            if part
        )

        doc_id = f"{scope}:{belief_id}"
        return Document(
            id=doc_id,
            content=content,
            metadata={
                "doc_id": doc_id,
                "belief_id": belief_id,
                "source": self.source_type.value,
                "scope": scope,
                "trigger": trigger,
                "domain": domain,
                "confidence": confidence,
                "action": action_text,
                "evidence": evidence_text,
                "file_path": str(path),
                "origin_session": frontmatter.get("origin_session", ""),
            },
        )

    def _load_doc_store(self) -> None:
        """検索結果表示用に現行 Doxa を再読込。"""
        self._doc_store = {}
        for path in self._list_doxa_files():
            document = self._parse_doxa_file(path)
            if document is not None:
                self._doc_store[document.id] = document

    def _auto_ingest(self) -> None:
        """初回起動時に全 Doxa を自動投入。"""
        documents: list[Document] = []
        for path in self._list_doxa_files():
            document = self._parse_doxa_file(path)
            if document is not None:
                documents.append(document)
        if not documents:
            return

        self.ingest(documents)
        DOXA_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._adapter.save(str(DOXA_INDEX_PATH))

    def ingest(self, documents: List[Document]) -> int:
        """Doxa をインジェスト。"""
        if not self._initialized:
            self.initialize()

        vectors = []
        metadata_list = []

        for doc in documents:
            if doc.embedding is not None:
                vector = np.asarray(doc.embedding, dtype=np.float32)
            else:
                vector = self._embed(doc.content)

            vectors.append(vector)
            metadata_list.append({
                "doc_id": doc.id,
                "source": self.source_type.value,
                **doc.metadata,
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
        domain: Optional[str] = None,
        scope: Optional[str] = None,
        min_confidence: Optional[float] = None,
        **kwargs,
    ) -> List[IndexedResult]:
        """Doxa を検索。confidence で score を乗算ブーストする。"""
        if not self._initialized:
            return []

        query_vec = self._embed(query)
        adapter_results = self._adapter.search(query_vec, k=k * 3)

        results: list[IndexedResult] = []
        for result in adapter_results:
            metadata = result.metadata
            belief_domain = metadata.get("domain", "")
            belief_scope = metadata.get("scope", "")
            confidence = float(metadata.get("confidence", 0.0) or 0.0)

            if domain and belief_domain != domain:
                continue
            if scope and belief_scope != scope:
                continue
            if min_confidence is not None and confidence < min_confidence:
                continue

            doc_id = metadata.get("doc_id", str(result.id))
            document = self._doc_store.get(doc_id)
            boosted_score = result.score * confidence
            results.append(
                IndexedResult(
                    doc_id=doc_id,
                    score=boosted_score,
                    source=self.source_type,
                    content=document.content if document else "",
                    metadata={
                        **metadata,
                        "title": metadata.get("belief_id", doc_id),
                    },
                )
            )

        results.sort(key=lambda item: item.score, reverse=True)
        return results[:k]
