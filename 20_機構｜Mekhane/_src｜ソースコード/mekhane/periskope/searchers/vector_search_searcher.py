from __future__ import annotations
# PROOF: mekhane/periskope/searchers/vector_search_searcher.py
# PURPOSE: periskope モジュールの vector_search_searcher
"""
Vertex AI Vector Search (Matching Engine) Searcher for Periskopē.
Provides low-latency ANN search for internal high-volume knowledge (Papers, etc.).
Hydrates skeletal results from Gnōsis primary store.
"""


import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any


from mekhane.periskope.models import SearchResult, SearchSource

logger = logging.getLogger(__name__)

#from mekhane.periskope.searchers.base import Searcher, SearchResult
from mekhane.paths import GNOSIS_DB_DIR

DB_URI = GNOSIS_DB_DIR


class VectorSearchSearcher:
    """Vertex AI Vector Search (Matching Engine) API Client.

    ANN search returns doc IDs + similarity scores.
    Hydration fills title/snippet/content from Gnōsis primary store.
    """

    def __init__(
        self,
        project: str = "",
        location: str = "us-central1",
        index_endpoint_id: str = "",
        deployed_index_id: str = "periskope_deployed_idx",
        embedder: Any = None,
        credentials_file: str = "",
    ) -> None:
        self.project = project
        self.location = location
        self.index_endpoint_id = index_endpoint_id
        self.deployed_index_id = deployed_index_id
        self.enabled = bool(self.project and self.index_endpoint_id)
        self.embedder = embedder
        self.credentials_file = credentials_file
        self._endpoint_cache = None
        self._gnosis_backend = None  # 遅延ロード Gnōsis FAISSBackend

    @property
    def available(self) -> bool:
        """Indicates if the searcher is configured and ready."""
        return self.enabled

    def _get_endpoint(self):
        if self._endpoint_cache is None:
            from google.cloud import aiplatform

            # SA 鍵認証 > ADC フォールバック
            credentials = None
            if self.credentials_file and os.path.isfile(self.credentials_file):
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_file,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )
                logger.info("VVS: SA key auth: %s", self.credentials_file)

            aiplatform.init(
                project=self.project,
                location=self.location,
                credentials=credentials,
            )
            self._endpoint_cache = aiplatform.MatchingEngineIndexEndpoint(
                index_endpoint_name=self.index_endpoint_id
            )
        return self._endpoint_cache

    def _get_gnosis_backend(self):
        """遅延ロードで GnosisIndex の FAISSBackend を取得する。"""
        if self._gnosis_backend is None:
            try:
                from mekhane.anamnesis.index import GnosisIndex
                index = GnosisIndex()
                if index._table_exists():
                    self._gnosis_backend = index._backend
                    logger.info("VVS: Gnōsis hydration backend loaded (FAISS)")
                else:
                    logger.warning("VVS: Gnōsis index not found")
            except Exception as e:  # noqa: BLE001
                logger.warning("VVS: Gnōsis hydration unavailable: %s", e)
        return self._gnosis_backend

    def _hydrate_results(self, results: list[SearchResult]) -> list[SearchResult]:
        """Fill skeletal VVS results with content from Gnōsis.

        Looks up each doc_id in the Gnōsis knowledge table and populates
        title, snippet (abstract), content, url, and metadata.
        """
        backend = self._get_gnosis_backend()
        if backend is None:
            return results

        # バッチ lookup: 全 doc_id を収集
        doc_id_map: dict[str, SearchResult] = {}
        for r in results:
            # vvs://doc_id URL から doc_id を抽出
            if r.url and r.url.startswith("vvs://"):
                doc_id = r.url[6:]  # "vvs://" を除去
                doc_id_map[doc_id] = r

        if not doc_id_map:
            return results

        try:
            # FAISSBackend のメタデータから primary_key で照合
            backend._load()
            for idx, meta in backend._metadata.items():
                pk = str(meta.get("primary_key", ""))
                if pk not in doc_id_map:
                    continue

                r = doc_id_map[pk]
                title = str(meta.get("title", ""))
                abstract = str(meta.get("abstract", ""))
                content = str(meta.get("content", ""))
                url = str(meta.get("url", ""))
                source_name = str(meta.get("source", ""))

                # Hydrate the result
                r.title = title or r.title
                r.snippet = abstract[:500] if abstract else content[:500]
                r.content = content or abstract
                if url and url != "nan":
                    r.url = url  # vvs:// を実 URL に置換
                r.metadata["vvs_doc_id"] = pk
                r.metadata["vvs_source"] = source_name

                # authors/doi があれば追加
                authors = meta.get("authors", "")
                if authors and str(authors) != "nan":
                    r.metadata["authors"] = str(authors)
                doi = meta.get("doi", "")
                if doi and str(doi) != "nan":
                    r.metadata["doi"] = str(doi)

            hydrated = sum(1 for r in results if r.snippet)
            logger.info("VVS: Hydrated %d/%d results from Gnōsis", hydrated, len(results))

        except Exception as e:  # noqa: BLE001
            logger.warning("VVS: Hydration failed (results returned as skeletal): %s", e)

        return results

    async def search(
        self,
        query: str,
        max_results: int = 10,
        source_filter: str | None = None,
    ) -> list[SearchResult]:
        if not self.enabled or self.embedder is None:
            return []

        # 1. Embed query
        start_t = time.perf_counter()
        try:
            query_emb = await asyncio.to_thread(self.embedder.embed, query)
        except Exception as e:  # noqa: BLE001
            logger.error("VVS: Embedding failed: %s", e)
            return []

        # 2. Build filters
        numeric_restricts = []
        string_restricts = []
        if source_filter:
            from google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint import Namespace
            string_restricts.append(
                Namespace(name="source", allow_tokens=[source_filter])
            )

        # 3. Query Vector Search
        try:
            endpoint = self._get_endpoint()
            fn_kwargs: dict = {
                "deployed_index_id": self.deployed_index_id,
                "queries": [query_emb],
                "num_neighbors": max_results,
            }
            if string_restricts:
                fn_kwargs["string_restricts"] = string_restricts
            response = await asyncio.to_thread(
                endpoint.find_neighbors,
                **fn_kwargs,
            )

            if not response or not response[0]:
                return []

            matches = response[0]
            results = []

            for match in matches:
                doc_id = match.id
                relevance = match.distance

                res = SearchResult(
                    url=f"vvs://{doc_id}",
                    title=f"[VVS] {doc_id}",
                    snippet="",
                    relevance=relevance,
                    source=SearchSource.VECTOR_SEARCH_ANN,
                )
                results.append(res)

            # 4. Hydrate from Gnōsis
            results = await asyncio.to_thread(self._hydrate_results, results)

            elapsed = time.perf_counter() - start_t
            logger.info("VVS: Found %d results in %.2f s (hydrated)", len(results), elapsed)
            return results

        except Exception as e:  # noqa: BLE001
            logger.error("VVS: Search failed: %s", e)
            return []
