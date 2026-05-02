"""Phase alpha scaffold for the Phantasia Field wiki layer.

This module keeps the Phase alpha scope intentionally narrow:

- `crystallize_pages()` emits minimal Markdown wiki pages from raw field chunks.
- `lint()` supports structural checks that do not require an LLM.
- contradiction and missing-concept detection are deferred to Phase beta.

The clustering path prefers chunk embeddings from `field._get_storage().filter_to_pandas()`.
If embeddings are not accessible from that DataFrame, clustering falls back to `parent_id`
grouping so the scaffold remains usable with storage backends that expose metadata only.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import pickle as _pickle
import shutil
import tempfile
import time
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import md5
from itertools import combinations
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mekhane.anamnesis.wiki_schema import WikiPage

if TYPE_CHECKING:
    from mekhane.anamnesis.link_graph import LinkGraph
    from mekhane.anamnesis.phantasia_field import PhantasiaField
    from mekhane.symploke.phantazein_store import PhantazeinStore

log = logging.getLogger(__name__)

_ALLOWED_OPERATIONS = {
    "orphan",
    "contradiction",
    "staleness",
    "missing",
    "cross-ref-gap",
}


def _resolve_storage_backend(preferred: str = "faiss") -> str:
    """Fall back to the NumPy backend when faiss is unavailable."""
    if preferred != "faiss":
        return preferred
    try:
        import faiss  # noqa: F401
    except ImportError:
        return "numpy"
    return preferred


@dataclass
class OrphanReport:
    cluster_id: str
    reason: str
    in_degree: int
    knn_density: float


@dataclass
class StalenessReport:
    cluster_id: str
    source_path: str
    source_mtime: float
    wiki_mtime: float


@dataclass
class CrossRefGapReport:
    cluster_a: str
    cluster_b: str
    cosine_similarity: float


@dataclass
class ContradictionReport:
    cluster_a: str
    cluster_b: str
    cosine_distance: float
    llm_verdict: str = ""


@dataclass
class MissingReport:
    keyword: str
    tfidf_score: float
    nearest_cluster_id: str


@dataclass
class LintResult:
    operations_run: list[str]
    orphans: list[OrphanReport] = field(default_factory=list)
    staleness: list[StalenessReport] = field(default_factory=list)
    cross_ref_gaps: list[CrossRefGapReport] = field(default_factory=list)
    contradictions: list[ContradictionReport] = field(default_factory=list)
    missing: list[MissingReport] = field(default_factory=list)
    consistency_log_inserts: int = 0
    dry_run: bool = False


class WikiLayer:
    """Persist and lint markdown wiki pages derived from the Phantasia Field."""

    def __init__(
        self,
        phantasia_field: "PhantasiaField",
        wiki_root: Path,
        link_graph: "LinkGraph | None" = None,
        *,
        min_knn_density: float = 0.3,
        use_snapshot: bool = True,
    ):
        self.field = phantasia_field
        self.wiki_root = Path(wiki_root)
        self.link_graph = link_graph
        self.min_knn_density = float(min_knn_density)
        self.use_snapshot = bool(use_snapshot)
        self._store = None

    def _get_store(self) -> "PhantazeinStore":
        """Lazy init PhantazeinStore."""
        if self._store is None:
            from mekhane.symploke.phantazein_store import PhantazeinStore

            self._store = PhantazeinStore()
        return self._store

    @staticmethod
    def _member_id(record: dict[str, Any], fallback_index: int) -> str:
        """Return a stable chunk member identifier for a storage record."""
        for key in ("chunk_id", "primary_key", "id"):
            value = record.get(key)
            if value not in (None, ""):
                return str(value)
        return f"row_{fallback_index}"

    @staticmethod
    def _coerce_float(value: Any, default: float = 0.0) -> float:
        """Convert values to floats without raising on malformed data."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _coerce_vector(value: Any) -> list[float] | None:
        """Convert storage vector payloads into a float list."""
        if value is None:
            return None
        if hasattr(value, "tolist"):
            value = value.tolist()
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return None
        if isinstance(value, tuple):
            value = list(value)
        if not isinstance(value, list):
            return None
        try:
            return [float(item) for item in value]
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_vector(vector: list[float]) -> list[float]:
        """L2-normalize a dense embedding vector."""
        norm = math.sqrt(sum(component * component for component in vector))
        if norm == 0.0:
            return vector
        return [component / norm for component in vector]

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        """Compute cosine similarity for normalized vectors."""
        if not left or not right or len(left) != len(right):
            return 0.0
        return sum(a * b for a, b in zip(left, right))

    def _load_storage_records(self) -> list[dict[str, Any]]:
        """Load raw chunk records from the underlying storage backend."""
        storage = self.field._get_storage()
        df = storage.filter_to_pandas()
        if hasattr(df, "to_dict"):
            return list(df.to_dict("records"))
        return []

    def _build_record_map(self) -> dict[str, dict[str, Any]]:
        """Map chunk identifiers back to raw storage records."""
        record_map: dict[str, dict[str, Any]] = {}
        for index, record in enumerate(self._load_storage_records()):
            member_id = self._member_id(record, index)
            record_map[member_id] = record
            for key in ("primary_key", "id", "chunk_id"):
                value = record.get(key)
                if value not in (None, ""):
                    record_map.setdefault(str(value), record)
        return record_map

    @staticmethod
    def _resolve_faiss_backend(storage: Any) -> tuple[str, Any] | None:
        """Locate a FAISS-style backend on `storage`, regardless of attr name.

        GnosisIndex stores its backend on `_backend`; tests sometimes attach a
        public `backend`. Either path is acceptable as long as the object has the
        FAISS-style `_storage_dir` + `_table_name` attributes that the snapshot
        and clustering paths rely on.

        Returns:
            (attr_name, backend) so the caller can restore via the same slot.
            None when no FAISS-style backend is reachable.
        """
        for attr in ("backend", "_backend"):
            candidate = getattr(storage, attr, None)
            if candidate is None:
                continue
            if hasattr(candidate, "_storage_dir") and hasattr(candidate, "_table_name"):
                return attr, candidate
        return None

    def _create_snapshot(self) -> Path | None:
        """Atomically copy {table}.faiss + {table}.meta.pkl to a temp dir.

        Returns None if use_snapshot=False or backend doesn't support it.
        Waits for source mtimes to settle (max 5 × 100 ms) before copying so we
        don't pick up a half-flushed write from an active producer. Retries up
        to 3x on OSError or unpickling failure (truncated pickle from an
        in-flight writer).
        """
        if not self.use_snapshot:
            return None
        try:
            storage = self.field._get_storage()
        except Exception:
            return None
        resolved = self._resolve_faiss_backend(storage)
        if resolved is None:
            return None
        _, backend = resolved
        storage_dir = getattr(backend, "_storage_dir", None)
        table_name = getattr(backend, "_table_name", None)
        if storage_dir is None or table_name is None:
            return None
        src_index = Path(storage_dir) / f"{table_name}.faiss"
        src_meta = Path(storage_dir) / f"{table_name}.meta.pkl"
        if not src_index.exists() or not src_meta.exists():
            return None
        # Wait for mtime to stabilize: an active writer often touches the meta
        # file twice in quick succession (write_index → pickle.dump). If the
        # timestamps move between samples we delay before copying.
        for _ in range(5):
            mtime_a = (src_index.stat().st_mtime, src_meta.stat().st_mtime)
            time.sleep(0.1)
            mtime_b = (src_index.stat().st_mtime, src_meta.stat().st_mtime)
            if mtime_a == mtime_b:
                break
        snap_dir = Path(tempfile.gettempdir()) / f"wiki_snapshot_{uuid.uuid4().hex[:8]}"
        snap_dir.mkdir(parents=True, exist_ok=True)
        last_err: Exception | None = None
        for _ in range(3):
            try:
                shutil.copy2(src_index, snap_dir / src_index.name)
                shutil.copy2(src_meta, snap_dir / src_meta.name)
                with open(snap_dir / src_meta.name, "rb") as f:
                    _pickle.load(f)
                return snap_dir
            except (OSError, _pickle.UnpicklingError, EOFError) as exc:
                last_err = exc
                time.sleep(0.2)
        log.warning("WikiLayer: snapshot failed after 3 attempts: %s", last_err)
        shutil.rmtree(snap_dir, ignore_errors=True)
        return None

    def _cleanup_snapshot(self, snap_dir: Path | None) -> None:
        if snap_dir is None:
            return
        shutil.rmtree(snap_dir, ignore_errors=True)

    def _swap_backend_to_snapshot(self, snap_dir: Path):
        """Monkey-patch the storage's FAISS backend to read from snapshot dir.

        Returns a (storage, attr_name, original_backend) tuple for restoration,
        or None if no swappable FAISS backend was found. Single-process only —
        not thread-safe.
        """
        try:
            storage = self.field._get_storage()
        except Exception:
            return None
        # Locate which attribute actually holds a FAISS-style backend so we can
        # restore it to the same slot later.
        attr_name = None
        orig = None
        for candidate_attr in ("_backend", "backend"):
            candidate = getattr(storage, candidate_attr, None)
            if candidate is None:
                continue
            if hasattr(candidate, "_storage_dir") and hasattr(candidate, "_table_name"):
                attr_name = candidate_attr
                orig = candidate
                break
        if orig is None or attr_name is None:
            return None
        table_name = getattr(orig, "_table_name", None)
        if table_name is None:
            return None
        from mekhane.anamnesis.backends.faiss_backend import FAISSBackend
        snap_backend = FAISSBackend(snap_dir, table_name=table_name)
        setattr(storage, attr_name, snap_backend)
        return (storage, attr_name, orig)

    def _restore_backend(self, original) -> None:
        """Restore the original backend after a snapshot-backed operation.

        Accepts the tuple returned by `_swap_backend_to_snapshot`. The legacy
        plain-backend form is kept for backward compatibility with older
        callers / tests.
        """
        if original is None:
            return
        if isinstance(original, tuple) and len(original) == 3:
            storage, attr_name, orig_backend = original
            try:
                setattr(storage, attr_name, orig_backend)
            except Exception:
                pass
            return
        # Legacy: original is a backend object — try the historical _backend slot.
        try:
            storage = self.field._get_storage()
        except Exception:
            return
        try:
            setattr(storage, "_backend", original)
        except Exception:
            pass

    # Aliases retained for tests / callers that prefer the snapshot-state idiom.
    def _activate_snapshot_backend(self, snap_dir: Path | None):
        if snap_dir is None:
            return None
        return self._swap_backend_to_snapshot(snap_dir)

    def _restore_snapshot_backend(self, state) -> None:
        self._restore_backend(state)

    def _cluster_by_parent(self, records: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        """Fallback clustering by `parent_id` when embeddings are unavailable."""
        buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for index, record in enumerate(records):
            parent_id = str(record.get("parent_id") or "").strip()
            key = parent_id or self._member_id(record, index)
            buckets[key].append(record)
        return list(buckets.values())

    def _cluster_records_inmemory(
        self,
        records: list[dict[str, Any]],
        k_neighbors: int,
        similarity_threshold: float = 0.7,
    ) -> list[list[dict[str, Any]]]:
        """Cluster records by k-NN connected components, with parent fallback."""
        if not records:
            return []
        if len(records) == 1:
            return [records]

        normed_vectors: list[list[float]] = []
        for record in records:
            vector = self._coerce_vector(record.get("vector"))
            if vector is None:
                log.info("WikiLayer clustering fallback: vector column unavailable, using parent_id groups")
                return self._cluster_by_parent(records)
            normed_vectors.append(self._normalize_vector(vector))

        adjacency = [set() for _ in records]
        effective_k = max(1, min(k_neighbors, len(records) - 1))
        for index, anchor in enumerate(normed_vectors):
            scored_neighbors: list[tuple[float, int]] = []
            for other_index, candidate in enumerate(normed_vectors):
                if index == other_index:
                    continue
                similarity = self._cosine_similarity(anchor, candidate)
                scored_neighbors.append((similarity, other_index))
            scored_neighbors.sort(key=lambda item: item[0], reverse=True)
            for similarity, neighbor_index in scored_neighbors[:effective_k]:
                if similarity < similarity_threshold:
                    continue
                adjacency[index].add(neighbor_index)
                adjacency[neighbor_index].add(index)

        visited: set[int] = set()
        clusters: list[list[dict[str, Any]]] = []
        for index in range(len(records)):
            if index in visited:
                continue
            stack = [index]
            component: list[int] = []
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                component.append(current)
                stack.extend(neighbor for neighbor in adjacency[current] if neighbor not in visited)
            clusters.append([records[item] for item in sorted(component)])
        return clusters

    def _cluster_records(
        self,
        records: list[dict[str, Any]],
        k_neighbors: int,
        similarity_threshold: float = 0.7,
    ) -> list[list[dict[str, Any]]]:
        """Cluster records via FAISS top-k when available, else in-memory fallback.

        The FAISS path is preferred whenever ``faiss`` is importable — it does
        not require the storage backend to expose a FAISSBackend, since we build
        a temporary ``IndexFlatIP`` over the supplied vectors. The historical
        gating on ``getattr(storage, "backend", None)`` silently fell back to
        the O(N²) in-memory path on real corpora (GnosisIndex exposes
        ``_backend``, not ``backend``), which was the root cause of the 5-min
        crystallize stall.
        """
        if not records or len(records) == 1:
            return self._cluster_records_inmemory(records, k_neighbors, similarity_threshold)
        if len(records) < 32:
            log.info("WikiLayer clustering: in-memory path (N=%d, k=%d)", len(records), k_neighbors)
            return self._cluster_records_inmemory(records, k_neighbors, similarity_threshold)

        try:
            import faiss
            import numpy as np
        except ImportError:
            log.info("WikiLayer clustering: in-memory path (N=%d, k=%d)", len(records), k_neighbors)
            return self._cluster_records_inmemory(records, k_neighbors, similarity_threshold)

        normed_vectors: list[list[float]] = []
        for record in records:
            vector = self._coerce_vector(record.get("vector"))
            if vector is None:
                log.info("WikiLayer clustering fallback: vector column unavailable, using parent_id groups")
                return self._cluster_by_parent(records)
            normed_vectors.append(self._normalize_vector(vector))

        log.info("WikiLayer clustering: faiss path (N=%d, k=%d)", len(records), k_neighbors)
        arr = np.asarray(normed_vectors, dtype="float32")
        dim = arr.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(arr)
        effective_k = max(1, min(k_neighbors, len(records) - 1))
        search_k = effective_k + 1
        sims, idxs = index.search(arr, search_k)
        adjacency: list[set[int]] = [set() for _ in records]
        for i in range(len(records)):
            for sim, j in zip(sims[i], idxs[i]):
                if j == i or j < 0:
                    continue
                if sim < similarity_threshold:
                    continue
                adjacency[i].add(int(j))
                adjacency[int(j)].add(i)

        visited: set[int] = set()
        clusters: list[list[dict[str, Any]]] = []
        for i in range(len(records)):
            if i in visited:
                continue
            stack = [i]
            comp: list[int] = []
            while stack:
                cur = stack.pop()
                if cur in visited:
                    continue
                visited.add(cur)
                comp.append(cur)
                stack.extend(n for n in adjacency[cur] if n not in visited)
            clusters.append([records[k] for k in sorted(comp)])
        return clusters

    @staticmethod
    def _select_representative(cluster: list[dict[str, Any]]) -> dict[str, Any]:
        """Pick the densest chunk as the representative for a cluster."""
        return max(cluster, key=lambda record: WikiLayer._coerce_float(record.get("density"), 0.0))

    def _page_path(self, page: WikiPage) -> Path:
        """Return the filesystem path for a wiki page."""
        source_type = page.source_types[0] if page.source_types else "unknown"
        return self.wiki_root / source_type / f"{page.cluster_id}.md"

    def _load_pages(self) -> list[tuple[Path, WikiPage]]:
        """Load all wiki pages currently present on disk."""
        if not self.wiki_root.exists():
            return []
        pages: list[tuple[Path, WikiPage]] = []
        for page_path in sorted(self.wiki_root.rglob("*.md")):
            try:
                text = page_path.read_text(encoding="utf-8")
                pages.append((page_path, WikiPage.from_markdown(text)))
            except Exception as exc:  # noqa: BLE001
                log.warning("Skipping unreadable wiki page %s: %s", page_path, exc)
        return pages

    def _resolve_source_path(self, record: dict[str, Any]) -> Path | None:
        """Resolve `parent_id` to a real file path when it is path-like."""
        parent_id = str(record.get("parent_id") or "").strip()
        if not parent_id:
            return None
        candidate = Path(parent_id).expanduser()
        if candidate.exists():
            return candidate.resolve()
        return None

    def _source_node_ids(self, page: WikiPage, record_map: dict[str, dict[str, Any]]) -> set[str]:
        """Resolve source-file node identifiers for a wiki page."""
        if self.link_graph is None:
            return set()

        node_ids: set[str] = set()
        for member in page.members:
            record = record_map.get(member)
            if record is None:
                continue
            parent_id = str(record.get("parent_id") or "").strip()
            if not parent_id:
                continue
            for candidate in (Path(parent_id).stem, parent_id):
                if candidate in self.link_graph.nodes:
                    node_ids.add(candidate)
                    break
        return node_ids

    def _has_explicit_edge(self, left_nodes: set[str], right_nodes: set[str]) -> bool:
        """Return whether any explicit graph edge already connects two node sets."""
        if self.link_graph is None:
            return False
        for node_id in left_nodes:
            node = self.link_graph.nodes.get(node_id)
            if node is None:
                continue
            neighbors = set(node.out_links) | set(node.in_links)
            if neighbors & right_nodes:
                return True
        return False

    def _cluster_density_details(
        self,
        page: WikiPage,
        record_map: dict[str, dict[str, Any]],
    ) -> tuple[float, bool]:
        """Estimate cluster density and whether it came from stored density values.

        Returns:
            (density, from_stored) where from_stored=True means the value came
            from non-zero stored density fields, False means it was computed
            from member-vector neighborhoods (semantic kNN density). When all
            stored densities are 0.0 (the real-corpus case), they are treated
            as absent so we fall through to the semantic computation.
        """
        density_values: list[float] = []
        vectors: list[list[float]] = []
        for member in page.members:
            record = record_map.get(member)
            if record is None:
                continue
            density = record.get("density")
            density_float = self._coerce_float(density, 0.0) if density not in (None, "") else None
            # Stored density of 0.0 across the entire corpus is the
            # uninitialized state — fall through to vector-based density.
            if density_float is not None and density_float > 0.0:
                density_values.append(density_float)
                continue
            vector = self._coerce_vector(record.get("vector"))
            if vector is not None:
                vectors.append(self._normalize_vector(vector))

        if density_values:
            return sum(density_values) / len(density_values), True

        if vectors:
            from mekhane.anamnesis.chunker_nucleator import _compute_knn_density

            densities = _compute_knn_density(vectors, k=min(5, len(vectors)))
            if densities:
                return sum(densities) / len(densities), False

        return 1.0, False

    def _cluster_density(self, page: WikiPage, record_map: dict[str, dict[str, Any]]) -> float:
        """Estimate cluster density from stored density values or member vectors."""
        density, _ = self._cluster_density_details(page, record_map)
        return density

    def _stored_density_for(self, page: WikiPage, record_map: dict[str, dict[str, Any]]) -> float | None:
        """Return averaged stored density (not kNN-computed) for a page, or None if absent.

        A density of exactly 0.0 is treated as "uninitialized" rather than
        "valid measurement" — see `_cluster_density_details` for rationale.
        """
        values: list[float] = []
        for member in page.members:
            record = record_map.get(member)
            if record is None:
                continue
            density = record.get("density")
            if density not in (None, ""):
                value = self._coerce_float(density, 0.0)
                if value > 0.0:
                    values.append(value)
        if not values:
            return None
        return sum(values) / len(values)

    def _page_centroid_vector(
        self,
        page: WikiPage,
        record_map: dict[str, dict[str, Any]],
    ) -> list[float] | None:
        """Mean-pool member vectors and L2-normalize → cluster centroid.

        Returns None when no member vector is recoverable from `record_map`.
        """
        member_vectors: list[list[float]] = []
        for member in page.members:
            record = record_map.get(member)
            if record is None:
                continue
            vector = self._coerce_vector(record.get("vector"))
            if vector is not None:
                member_vectors.append(vector)
        if not member_vectors:
            return None
        dim = len(member_vectors[0])
        centroid = [0.0] * dim
        for vec in member_vectors:
            if len(vec) != dim:
                continue
            for i, val in enumerate(vec):
                centroid[i] += val
        return self._normalize_vector(centroid)

    def _build_inferred_linkgraph(
        self,
        pages: list[tuple[Path, WikiPage]],
        record_map: dict[str, dict[str, Any]],
        k: int = 10,
        similarity_threshold: float = 0.5,
    ) -> tuple[dict[str, dict[str, Any]], dict[str, float]]:
        """Build a cluster-level link graph from FAISS k-NN topology.

        For each page, compute a centroid vector (mean of member vectors,
        L2-normalized). Connect cluster A → cluster B if cosine(A, B) ≥
        `similarity_threshold` and B is among A's top-k neighbors.

        Returns:
            (graph, density_by_cluster) where:
            - graph[cluster_id] = {"in_links": [...], "out_links": [...]}
            - density_by_cluster[cluster_id] = mean cosine similarity to its
              k nearest neighbors (semantic density signal)
        """
        graph: dict[str, dict[str, Any]] = {}
        density_by_cluster: dict[str, float] = {}

        cluster_ids: list[str] = []
        centroids: list[list[float]] = []
        for _, page in pages:
            centroid = self._page_centroid_vector(page, record_map)
            if centroid is None:
                graph[page.cluster_id] = {"in_links": [], "out_links": []}
                density_by_cluster[page.cluster_id] = 1.0
                continue
            cluster_ids.append(page.cluster_id)
            centroids.append(centroid)
            graph.setdefault(page.cluster_id, {"in_links": [], "out_links": []})

        if not centroids:
            return graph, density_by_cluster

        try:
            import faiss
            import numpy as np
        except ImportError:
            # Fallback: pure-python pairwise — only feasible for tiny page sets.
            for i, anchor_id in enumerate(cluster_ids):
                sims = []
                for j, other_id in enumerate(cluster_ids):
                    if i == j:
                        continue
                    s = self._cosine_similarity(centroids[i], centroids[j])
                    sims.append((s, other_id))
                sims.sort(key=lambda x: x[0], reverse=True)
                top = sims[: max(1, min(k, len(sims)))]
                density_by_cluster[anchor_id] = (
                    sum(s for s, _ in top) / len(top) if top else 1.0
                )
                for s, other_id in top:
                    if s < similarity_threshold:
                        continue
                    graph[anchor_id]["out_links"].append(other_id)
                    graph[other_id]["in_links"].append(anchor_id)
            return graph, density_by_cluster

        arr = np.asarray(centroids, dtype="float32")
        n, dim = arr.shape
        index = faiss.IndexFlatIP(dim)
        index.add(arr)
        effective_k = max(1, min(k, n - 1))
        search_k = effective_k + 1
        sims, idxs = index.search(arr, search_k)
        for i, anchor_id in enumerate(cluster_ids):
            top: list[tuple[float, str]] = []
            for sim, j in zip(sims[i], idxs[i]):
                if j == i or j < 0:
                    continue
                top.append((float(sim), cluster_ids[int(j)]))
                if len(top) >= effective_k:
                    break
            density_by_cluster[anchor_id] = (
                sum(s for s, _ in top) / len(top) if top else 1.0
            )
            for sim, other_id in top:
                if sim < similarity_threshold:
                    continue
                graph[anchor_id]["out_links"].append(other_id)
                graph[other_id]["in_links"].append(anchor_id)
        return graph, density_by_cluster

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed representative texts using the storage embedder when available."""
        storage = self.field._get_storage()
        if hasattr(storage, "_get_embedder"):
            embedder = storage._get_embedder()
        else:
            from mekhane.anamnesis.index import Embedder

            embedder = Embedder()
        return embedder.embed_batch(texts)

    def crystallize_pages(
        self,
        source_filter: str | None = None,
        no_llm: bool = True,
        k_neighbors: int = 10,
    ) -> list[WikiPage]:
        """Crystallize raw chunks into minimal wiki pages.

        Phase alpha only supports deterministic page generation. If embeddings are visible
        through `filter_to_pandas()`, records are grouped by greedy connected-components over
        top-k cosine neighbors. If embeddings are absent, clusters fall back to `parent_id`.
        """
        snap_dir = self._create_snapshot()
        orig_backend = None
        try:
            if snap_dir is not None:
                orig_backend = self._swap_backend_to_snapshot(snap_dir)
            if not no_llm:
                raise NotImplementedError("LLM page generation deferred to Phase β")

            storage = self.field._get_storage()
            df = storage.filter_to_pandas()
            if source_filter:
                if "source" in getattr(df, "columns", []):
                    df = df[df["source"] == source_filter]
                else:
                    log.warning("source_filter=%s requested but `source` column is unavailable", source_filter)

            records = list(df.to_dict("records")) if hasattr(df, "to_dict") else []
            if not records:
                return []

            clusters = self._cluster_records(records, k_neighbors=k_neighbors, similarity_threshold=0.7)
            now = datetime.now(timezone.utc)
            pages: list[WikiPage] = []
            for cluster in clusters:
                member_ids = [
                    self._member_id(record, index)
                    for index, record in enumerate(cluster)
                ]
                representative = self._select_representative(cluster)
                representative_text = str(representative.get("content") or "")
                source_types = list(
                    dict.fromkeys(
                        str(record.get("source") or "unknown")
                        for record in cluster
                    )
                )
                cluster_hash = md5("||".join(sorted(member_ids)).encode("utf-8")).hexdigest()[:12]
                page = WikiPage(
                    cluster_id=f"cluster_{cluster_hash}",
                    members=member_ids,
                    source_types=source_types,
                    representative_text=representative_text,
                    title=" ".join(representative_text.split())[:80],
                    created_at=now,
                    last_updated=now,
                    in_degree=0,
                    out_degree=0,
                )
                page_path = self._page_path(page)
                page_path.parent.mkdir(parents=True, exist_ok=True)
                page_path.write_text(page.to_markdown(), encoding="utf-8")
                pages.append(page)
            return pages
        finally:
            if orig_backend is not None:
                self._restore_backend(orig_backend)
            self._cleanup_snapshot(snap_dir)

    def lint(
        self,
        operations: list[str],
        llm_budget: int = 0,
        dry_run: bool = False,
    ) -> LintResult:
        """Run selected lint operations and optionally persist them into `consistency_log`."""
        snap_dir = self._create_snapshot()
        orig_backend = None
        try:
            if snap_dir is not None:
                orig_backend = self._swap_backend_to_snapshot(snap_dir)
            normalized_operations = [operation.strip() for operation in operations if operation.strip()]
            unknown_operations = sorted(set(normalized_operations) - _ALLOWED_OPERATIONS)
            if unknown_operations:
                raise ValueError(f"Unknown wiki lint operations: {', '.join(unknown_operations)}")

            result = LintResult(operations_run=[], dry_run=dry_run)
            for operation in normalized_operations:
                if operation == "orphan":
                    result.orphans = self._detect_orphan()
                elif operation == "staleness":
                    result.staleness = self._detect_staleness()
                elif operation == "cross-ref-gap":
                    result.cross_ref_gaps = self._detect_cross_ref_gap()
                elif operation == "contradiction":
                    result.contradictions = self._detect_contradiction(llm_budget=llm_budget)
                elif operation == "missing":
                    result.missing = self._detect_missing()
                result.operations_run.append(operation)

            if not dry_run:
                self._write_to_consistency_log(result)
            return result
        finally:
            if orig_backend is not None:
                self._restore_backend(orig_backend)
            self._cleanup_snapshot(snap_dir)

    def _detect_orphan(self) -> list[OrphanReport]:
        """Detect orphans with two signals:

        1. **in_degree** — primary: 0 incoming references means the cluster is
           topologically isolated.
        2. **knn_density** — secondary: even if a cluster has backlinks, very
           low semantic density to its neighbors suggests an outlier.

        ``link_graph`` resolution order:
        - explicit ``self.link_graph`` if provided
        - inferred cluster-level k-NN graph built from page centroids
          (FAISS-backed, semantic). Only when this also fails do we fall back
          to per-record stored density.
        """
        record_map = self._build_record_map()
        pages = self._load_pages()
        reports: list[OrphanReport] = []
        suppressed_singletons = 0

        inferred_graph: dict[str, dict[str, Any]] | None = None
        inferred_density: dict[str, float] = {}
        if self.link_graph is None and pages:
            try:
                inferred_graph, inferred_density = self._build_inferred_linkgraph(
                    pages, record_map
                )
                log.info(
                    "WikiLayer orphan: inferred cluster k-NN graph for %d pages",
                    len(pages),
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("WikiLayer orphan: inferred graph build failed: %s", exc)
                inferred_graph = None

        for _, page in pages:
            in_degree = 0
            if self.link_graph is not None:
                node = self.link_graph.nodes.get(page.cluster_id)
                in_degree = len(node.in_links) if node is not None else 0
            elif inferred_graph is not None:
                node = inferred_graph.get(page.cluster_id)
                in_degree = len(node["in_links"]) if node is not None else 0

            # Prefer inferred semantic density when available, else fall back
            # to stored-density / vector-based per-cluster computation.
            if inferred_graph is not None and page.cluster_id in inferred_density:
                knn_density = inferred_density[page.cluster_id]
            else:
                knn_density = self._cluster_density(page, record_map)
            is_singleton = len(page.members) <= 1

            if self.link_graph is not None:
                if in_degree == 0:
                    reports.append(
                        OrphanReport(
                            cluster_id=page.cluster_id,
                            reason="in_degree=0",
                            in_degree=in_degree,
                            knn_density=knn_density,
                        )
                    )
                elif knn_density < self.min_knn_density:
                    reports.append(
                        OrphanReport(
                            cluster_id=page.cluster_id,
                            reason="low_knn_density_with_backlinks",
                            in_degree=in_degree,
                            knn_density=knn_density,
                        )
                    )
            elif inferred_graph is not None:
                # Inferred graph: in_degree=0 means no semantically-similar
                # neighbor exists in the *current* page set. Combine with
                # density: only flag when both signals agree.
                #
                # Override signal: when chunks carry an explicit non-zero
                # stored density, honor it directly. The inferred density
                # defaults to 1.0 for clusters whose centroids could not be
                # built (no vectors), which would otherwise mask a real
                # low-density measurement persisted on the chunk records.
                stored_density = self._stored_density_for(page, record_map)
                if stored_density is not None and stored_density < self.min_knn_density:
                    reports.append(
                        OrphanReport(
                            cluster_id=page.cluster_id,
                            reason="low_knn_density",
                            in_degree=in_degree,
                            knn_density=stored_density,
                        )
                    )
                elif in_degree == 0 and knn_density < self.min_knn_density:
                    reports.append(
                        OrphanReport(
                            cluster_id=page.cluster_id,
                            reason="inferred_isolated",
                            in_degree=in_degree,
                            knn_density=knn_density,
                        )
                    )
                elif knn_density < self.min_knn_density and not is_singleton:
                    reports.append(
                        OrphanReport(
                            cluster_id=page.cluster_id,
                            reason="low_knn_density",
                            in_degree=in_degree,
                            knn_density=knn_density,
                        )
                    )
            else:
                if is_singleton:
                    stored_density = self._stored_density_for(page, record_map)
                    if stored_density is not None and stored_density < self.min_knn_density:
                        reports.append(
                            OrphanReport(
                                cluster_id=page.cluster_id,
                                reason="low_knn_density",
                                in_degree=in_degree,
                                knn_density=knn_density,
                            )
                        )
                    else:
                        suppressed_singletons += 1
                elif knn_density < self.min_knn_density:
                    reports.append(
                        OrphanReport(
                            cluster_id=page.cluster_id,
                            reason="low_knn_density",
                            in_degree=in_degree,
                            knn_density=knn_density,
                        )
                    )
        if suppressed_singletons:
            log.warning(
                "WikiLayer: LinkGraph not provided; skipped orphan detection for %d singleton clusters",
                suppressed_singletons,
            )
        return reports

    def _detect_staleness(self) -> list[StalenessReport]:
        """Detect wiki pages whose underlying source files are newer than the page."""
        record_map = self._build_record_map()
        reports: list[StalenessReport] = []
        for wiki_path, page in self._load_pages():
            wiki_mtime = wiki_path.stat().st_mtime
            seen_sources: set[Path] = set()
            for member in page.members:
                record = record_map.get(member)
                if record is None:
                    continue
                source_path = self._resolve_source_path(record)
                if source_path is None or source_path in seen_sources:
                    continue
                seen_sources.add(source_path)
                try:
                    source_mtime = source_path.stat().st_mtime
                except OSError:
                    continue
                if source_mtime > wiki_mtime:
                    reports.append(
                        StalenessReport(
                            cluster_id=page.cluster_id,
                            source_path=str(source_path),
                            source_mtime=source_mtime,
                            wiki_mtime=wiki_mtime,
                        )
                    )
        return reports

    def _detect_cross_ref_gap(
        self,
        similarity_threshold: float = 0.7,
        top_k: int = 10,
    ) -> list[CrossRefGapReport]:
        """Detect semantically similar clusters that lack explicit source links.

        Phase α-2.2 optimization — swap two costs simultaneously:

        1. **Drop the re-embedding step.** The previous implementation sent
           every page's ``representative_text`` through ``_embed_texts``
           (Vertex API round-trip) even though the member chunks already
           carried dense vectors. We now reuse ``_page_centroid_vector`` which
           mean-pools stored member vectors — no external call, no network
           cost, and the centroid is a stable representation of the cluster.
        2. **Replace the exhaustive N×N FAISS search with a top-k search.**
           The old ``index.search(sub, sub.shape[0])`` materialized the full
           similarity matrix (O(N²) results to iterate). We now request only
           the top-``top_k`` neighbors per cluster — an exact inner product
           search on L2-normalized centroids remains cosine — but the per-
           cluster result set is bounded. Asymptotic cost drops from O(N²)
           to O(N × top_k) on the post-index iteration, and FAISS itself
           runs a single BLAS matmul over N×N at index build + top-k
           selection — still far cheaper than the Python-level pair
           enumeration on real corpora.

        Semantic shift (documented): before, *every* cross-cluster pair above
        the threshold was reported; now we only report pairs that appear in
        the mutual top-k neighborhood. For tight thresholds (e.g. 0.85) the
        two behaviors coincide because high-similarity neighbors are already
        the top ones. For very loose thresholds on large corpora the new
        version may report fewer gaps, which is the intended behavior —
        reviewing 5,000+ weak gaps is not actionable feedback anyway.

        The pure-Python fallback (used when ``faiss`` / ``numpy`` are absent)
        preserves the same top-k semantics via per-anchor partial sort.
        """
        if self.link_graph is None:
            log.info("Skipping cross-ref gap detection because no LinkGraph was supplied")
            return []

        pages = self._load_pages()
        if len(pages) < 2:
            return []

        record_map = self._build_record_map()

        # Centroids built from stored member vectors — no embedder call.
        # Pages whose members carry no recoverable vector get None and are
        # skipped (same behavior as the old embedder-mismatch exit).
        centroids: list[list[float] | None] = [
            self._page_centroid_vector(page, record_map) for _, page in pages
        ]

        # Pre-resolve per-page source nodes once (was re-resolved per pair before).
        node_ids_by_index: list[set[str]] = [
            self._source_node_ids(page, record_map) for _, page in pages
        ]

        # A page is a candidate only if it has (a) a centroid and (b) at
        # least one source node (without source nodes, no edge can be
        # asserted or denied, so the page cannot produce a gap report).
        candidate_indices = [
            i
            for i in range(len(pages))
            if centroids[i] is not None and node_ids_by_index[i]
        ]
        if len(candidate_indices) < 2:
            return []

        reports: list[CrossRefGapReport] = []
        seen_pairs: set[tuple[int, int]] = set()
        pair_iter = self._cross_ref_gap_pairs(
            centroids,
            candidate_indices,
            similarity_threshold,
            top_k,
        )
        for left_index, right_index, similarity in pair_iter:
            ordered = (left_index, right_index) if left_index < right_index else (right_index, left_index)
            if ordered in seen_pairs:
                continue
            seen_pairs.add(ordered)
            left_nodes = node_ids_by_index[ordered[0]]
            right_nodes = node_ids_by_index[ordered[1]]
            if left_nodes & right_nodes:
                continue
            if self._has_explicit_edge(left_nodes, right_nodes):
                continue
            left_page = pages[ordered[0]][1]
            right_page = pages[ordered[1]][1]
            reports.append(
                CrossRefGapReport(
                    cluster_a=left_page.cluster_id,
                    cluster_b=right_page.cluster_id,
                    cosine_similarity=similarity,
                )
            )
        return reports

    def _cross_ref_gap_pairs(
        self,
        centroids: list[list[float] | None],
        candidate_indices: list[int],
        similarity_threshold: float,
        top_k: int,
    ):
        """Yield (i, j, similarity) pairs restricted to the mutual top-k.

        FAISS path (IndexFlatIP over centroids, top-k) is preferred. Falls
        back to a pure-Python per-anchor partial sort when faiss/numpy are
        unavailable — same top-k semantics, slower constants.

        Each unordered pair (i, j) may be yielded from either anchor side —
        the caller deduplicates via ``seen_pairs``.
        """
        try:
            import faiss
            import numpy as np
        except ImportError:
            faiss = None  # type: ignore[assignment]
            np = None  # type: ignore[assignment]

        if faiss is not None and np is not None:
            sub = np.asarray(
                [centroids[i] for i in candidate_indices],
                dtype="float32",
            )
            n_cand = sub.shape[0]
            dim = int(sub.shape[1])
            index = faiss.IndexFlatIP(dim)
            index.add(sub)
            # +1 so we can discard the self-hit without shrinking the neighborhood.
            search_k = max(1, min(top_k + 1, n_cand))
            sims, idxs = index.search(sub, search_k)
            log.info(
                "WikiLayer cross_ref_gap: faiss top-k path (candidates=%d, dim=%d, k=%d)",
                n_cand,
                dim,
                search_k,
            )
            for local_i in range(n_cand):
                anchor = candidate_indices[local_i]
                for sim, local_j in zip(sims[local_i], idxs[local_i]):
                    if local_j < 0 or int(local_j) == local_i:
                        continue
                    neighbor = candidate_indices[int(local_j)]
                    sim_f = float(sim)
                    if sim_f < similarity_threshold:
                        continue
                    yield anchor, neighbor, sim_f
            return

        # Pure-Python fallback: per-anchor partial sort → same top-k semantics.
        log.info(
            "WikiLayer cross_ref_gap: fallback top-k path (candidates=%d, k=%d)",
            len(candidate_indices),
            top_k,
        )
        for local_i, anchor in enumerate(candidate_indices):
            anchor_vec = centroids[anchor]
            if anchor_vec is None:
                continue
            scored: list[tuple[float, int]] = []
            for local_j, neighbor in enumerate(candidate_indices):
                if local_j == local_i:
                    continue
                neighbor_vec = centroids[neighbor]
                if neighbor_vec is None:
                    continue
                scored.append(
                    (self._cosine_similarity(anchor_vec, neighbor_vec), neighbor)
                )
            scored.sort(key=lambda item: item[0], reverse=True)
            for sim, neighbor in scored[:top_k]:
                if sim < similarity_threshold:
                    continue
                yield anchor, neighbor, sim

    def _detect_contradiction(self, llm_budget: int) -> list[ContradictionReport]:
        raise NotImplementedError("LLM contradiction detection deferred to Phase β")

    def _detect_missing(self) -> list[MissingReport]:
        raise NotImplementedError("TF-IDF gap detection deferred to Phase β")

    def _write_to_consistency_log(self, result: LintResult) -> None:
        """Persist lint findings into the shared `consistency_log` table."""
        severity_by_kind = {
            "orphan": "low",
            "staleness": "medium",
            "cross_ref_gap": "low",
            "contradiction": "high",
            "missing": "medium",
        }
        report_groups = [
            ("orphan", result.orphans),
            ("staleness", result.staleness),
            ("cross_ref_gap", result.cross_ref_gaps),
            ("contradiction", result.contradictions),
            ("missing", result.missing),
        ]

        store = self._get_store()
        for kind, reports in report_groups:
            for report in reports:
                details = json.dumps(asdict(report), ensure_ascii=False, sort_keys=True)
                if kind == "orphan":
                    summary = f"{report.cluster_id} {report.reason}"
                elif kind == "staleness":
                    summary = f"{report.cluster_id} newer than {Path(report.source_path).name}"
                elif kind == "cross_ref_gap":
                    summary = f"{report.cluster_a} ↔ {report.cluster_b}"
                elif kind == "contradiction":
                    summary = f"{report.cluster_a} ↔ {report.cluster_b}"
                else:
                    summary = f"{report.keyword} near {report.nearest_cluster_id}"

                store.log_consistency_issue(
                    session_id="wiki_layer_lint",
                    issue=f"[wiki/{kind}] {summary}",
                    severity=severity_by_kind[kind],
                    details=details,
                )
                result.consistency_log_inserts += 1


def main():
    parser = argparse.ArgumentParser(prog="wiki_layer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_cryst = sub.add_parser("crystallize")
    p_cryst.add_argument("--source-filter", default=None)
    p_cryst.add_argument("--no-llm", action="store_true", default=True)
    p_cryst.add_argument("--k-neighbors", type=int, default=10)
    p_cryst.add_argument(
        "--wiki-root",
        default=None,
        help="Override wiki root path",
    )

    p_lint = sub.add_parser("lint")
    p_lint.add_argument(
        "--operations",
        required=True,
        help="Comma-separated: orphan,staleness,cross-ref-gap,contradiction,missing",
    )
    p_lint.add_argument("--llm-budget", type=int, default=0)
    p_lint.add_argument(
        "--no-write",
        action="store_true",
        default=False,
        help="Detection のみ実行、consistency_log への書き込みをスキップ (read-only mode)",
    )
    p_lint.add_argument("--wiki-root", default=None)

    args = parser.parse_args()

    from mekhane.anamnesis.phantasia_field import PhantasiaField

    default_wiki_root = (
        Path(__file__).resolve().parents[3]
        / "30_記憶｜Mneme" / "01_記録｜Records" / "e_wiki｜wiki"
    )
    wiki_root = Path(args.wiki_root) if args.wiki_root else default_wiki_root

    field = PhantasiaField(backend=_resolve_storage_backend())
    layer = WikiLayer(field, wiki_root)

    if args.cmd == "crystallize":
        pages = layer.crystallize_pages(
            source_filter=args.source_filter,
            no_llm=args.no_llm,
            k_neighbors=args.k_neighbors,
        )
        print(f"Crystallized {len(pages)} pages → {wiki_root}")
    elif args.cmd == "lint":
        ops = [op.strip() for op in args.operations.split(",")]
        result = layer.lint(ops, llm_budget=args.llm_budget, dry_run=args.no_write)
        label = "[DRY-RUN] Lint result" if result.dry_run else "Lint result"
        print(f"{label}: {result.operations_run}")
        print(f"  orphans: {len(result.orphans)}")
        print(f"  staleness: {len(result.staleness)}")
        print(f"  cross-ref gaps: {len(result.cross_ref_gaps)}")
        print(f"  contradictions: {len(result.contradictions)}")
        print(f"  missing: {len(result.missing)}")
        print(f"  consistency_log inserts: {result.consistency_log_inserts}")


if __name__ == "__main__":
    main()
