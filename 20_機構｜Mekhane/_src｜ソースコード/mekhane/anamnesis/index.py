# PROOF: [L2/インフラ] <- mekhane/anamnesis/index.py
"""
PROOF: [L2/インフラ] このファイルは存在しなければならない

P3 → 記憶の永続化が必要
   → 論文のセマンティック索引が必要
   → index.py が担う

Q.E.D.

---

Gnōsis Index - StorageBackend 抽象化 + 重複排除

デフォルトバックエンド: FAISS (faiss-cpu)
代替: NumPy (brute-force)
"""

import os
import sys
import threading
from pathlib import Path
from typing import Optional
from mekhane.anamnesis.embedder_mixin import EmbedderMixin

from mekhane.anamnesis.models.paper import Paper
from mekhane.paths import GNOSIS_DB_DIR

# Paths
MODELS_DIR = (
    Path(__file__).parent.parent / "models" / "bge-small"
)  # forge/models/bge-small




# Windows UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass  # TODO: Add proper error handling


# PURPOSE: Text embedding (Vertex AI exclusively)
class Embedder(EmbedderMixin):
    """Text embedding using VertexEmbedder.

    Strategy:
      1. Always use VertexEmbedder (constants.EMBED_MODEL).
      2. bge-m3 / sentence-transformers fallback has been completely purged.

    Singleton: Same (model_name, dimension) key returns cached instance.
    """

    _instances: dict[tuple, "Embedder"] = {}
    _lock = threading.Lock()

    # PURPOSE: [L2-auto] 内部処理: new__ (thread-safe singleton)
    def __new__(cls, force_cpu: bool = False, model_name: str | None = None, dimension: int | None = None):
        from mekhane.anamnesis.constants import EMBED_MODEL, EMBED_DIM
        if model_name is None:
            model_name = EMBED_MODEL
        if dimension is None:
            dimension = EMBED_DIM
        key = (model_name, dimension)
        with cls._lock:
            if key in cls._instances:
                return cls._instances[key]
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[key] = instance
            return instance

    # PURPOSE: [L2-auto] 初期化: init__
    def __init__(self, force_cpu: bool = False, model_name: str | None = None, dimension: int | None = None):
        from mekhane.anamnesis.constants import EMBED_MODEL, EMBED_DIM
        if model_name is None:
            model_name = EMBED_MODEL
        if dimension is None:
            dimension = EMBED_DIM
        with self._lock:
            if self._initialized:
                return
            self._initialized = True

        self.model_name = model_name
        self._dimension = dimension
        self._use_gpu = False  # API based
        self._is_onnx_fallback = False
        self._embedder = None
        
        try:
            from mekhane.anamnesis.vertex_embedder import VertexEmbedder
            self._embedder = VertexEmbedder(model_name=model_name, dimension=dimension)
            print(f"[Embedder] Using VertexEmbedder ({model_name}, dim={dimension})")
        except Exception as e:  # noqa: BLE001
            print(f"[Embedder] ERROR: VertexEmbedder initialization failed: {e}")
            self._dimension_mismatch = True

    # embed() は EmbedderMixin から継承 (embed_batch([text])[0])

    # similarity_batch, novelty, pairwise_novelty は EmbedderMixin から継承

    # PURPOSE: GPU embedding via Vertex API.
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self._embedder is None:
            raise RuntimeError("Embedder not initialized (Vertex AI failed)")
        return self._embedder.embed_batch(texts)


# PURPOSE: Gnōsis論文インデックス
class GnosisIndex:
    """Gnōsis 論文・チャンクインデックス (StorageBackend 抽象化)

    デフォルト: FAISS (faiss-cpu)
    代替: NumPy (brute-force)
    """

    TABLE_NAME = "knowledge"

    # PURPOSE: GnosisIndex の構成と依存関係の初期化
    def __init__(self, db_dir: Optional[Path] = None, backend: str = "faiss", **kwargs):
        self.db_dir = db_dir or GNOSIS_DB_DIR
        self.db_dir.mkdir(parents=True, exist_ok=True)

        # StorageBackend の初期化
        self._backend = self._create_backend(backend, self.db_dir)
        self._backend_name = backend

        self.embedder: Optional[Embedder] = None
        self._primary_key_cache: set[str] = set()

    @staticmethod
    def _create_backend(backend_name: str, storage_dir: Path):
        """Backend インスタンスを生成する。"""
        if backend_name == "faiss":
            from mekhane.anamnesis.backends.faiss_backend import FAISSBackend
            return FAISSBackend(storage_dir, table_name=GnosisIndex.TABLE_NAME)
        elif backend_name == "numpy":
            from mekhane.anamnesis.backends.numpy_backend import NumpyBackend
            return NumpyBackend(storage_dir, table_name=GnosisIndex.TABLE_NAME)
        else:
            raise ValueError(f"Unknown backend: {backend_name}. Use 'faiss' or 'numpy'")

    # PURPOSE: テーブル存在チェック (StorageBackend 委譲)
    def _table_exists(self) -> bool:
        """TABLE_NAME が DB に存在するか"""
        return self._backend.exists()

    # PURPOSE: テーブル次元に適合する Embedder を返す (次元安全)
    _get_embedder_in_progress = False  # 循環参照防御フラグ

    def _get_embedder(self):
        """テーブル次元に適合する Embedder を返す。
        """
        import logging
        log = logging.getLogger(__name__)

        # Detect table dimension (StorageBackend 委譲)
        table_dim = self._backend.get_vector_dimension() if self._table_exists() else None

        # Default dimension for new tables
        from mekhane.anamnesis.constants import EMBED_DIM
        target_dim = table_dim or EMBED_DIM

        # Try app.state embedder first (API server context)
        # 循環参照防御: server.py._preload() → _get_embedder() → import server.app
        # _preload 中は app.state.embedder が未設定なので問題ないが、
        # 再帰呼び出しを明示的にブロックして安全を保証する。
        if not GnosisIndex._get_embedder_in_progress:
            try:
                from mekhane.api.server import app
                if hasattr(app.state, "embedder") and app.state.embedder is not None:
                    embedder = app.state.embedder
                    embedder_dim = getattr(embedder, '_dimension', None)
                    # If dimensions match or no table yet, use it
                    if table_dim is None or embedder_dim == table_dim:
                        return embedder
                    # Dimension mismatch — fall through to select correct one
                    log.warning(
                        f"app.state.embedder dim={embedder_dim} != table dim={table_dim}, "
                        f"selecting dimension-compatible embedder"
                    )
            except (ImportError, RuntimeError):
                pass  # Not in API server context

        # Always use VertexEmbedder indirectly via Embedder wrapper
        GnosisIndex._get_embedder_in_progress = True
        try:
            from mekhane.anamnesis.constants import EMBED_MODEL
            embedder = Embedder(model_name=EMBED_MODEL, dimension=target_dim)
            if table_dim is not None and getattr(embedder, '_dimension', target_dim) != table_dim:
                log.warning(
                    f"[GnosisIndex] VertexEmbedder dim {getattr(embedder, '_dimension', target_dim)} != table dim {table_dim}. "
                    f"FTS-only fallback will be used."
                )
                embedder._dimension_mismatch = True
                embedder._table_dim = table_dim
            return embedder
        finally:
            GnosisIndex._get_embedder_in_progress = False
    # PURPOSE: 既存primary_keyとtitleをキャッシュ
    def _load_primary_keys(self):
        """既存primary_keyとtitleをキャッシュ"""
        if not self._table_exists():
            return

        try:
            df = self._backend.to_pandas()
            if "primary_key" in df.columns:
                self._primary_key_cache = set(df["primary_key"].tolist())
            # Title cache: normalized_title -> primary_key
            self._title_cache: dict[str, str] = {}
            if "title" in df.columns and "primary_key" in df.columns:
                for _, row in df.iterrows():
                    norm = self._normalize_title(row.get("title", ""))
                    if norm:
                        self._title_cache[norm] = row["primary_key"]
        except Exception:  # noqa: BLE001
            pass  # Intentional: table may be empty or have no primary_key column

    # PURPOSE: [L2-auto] _normalize_title の関数定義
    @staticmethod
    # PURPOSE: [L2-auto] タイトルの正規化: 小文字化 + 非英数字除去でファジーマッチ。
    def _normalize_title(title: str) -> str:
        """タイトルの正規化: 小文字化 + 非英数字除去でファジーマッチ。"""
        import re
        return re.sub(r'[^a-z0-9]', '', title.lower().strip())

    # PURPOSE: 論文をインデックスに追加
    def add_papers(self, papers: list[Paper], dedupe: bool = True) -> int:
        """
        論文をインデックスに追加

        Args:
            papers: 追加する論文リスト
            dedupe: 重複排除を行うか

        Returns:
            追加された論文数
        """
        if not papers:
            return 0

        embedder = self._get_embedder()

        # Guard: dimension mismatch → ingest 拒否 (3072d テーブルに 1024d を混在させない)
        if getattr(embedder, '_dimension_mismatch', False):
            import logging
            log = logging.getLogger(__name__)
            table_dim = getattr(embedder, '_table_dim', '?')
            emb_dim = getattr(embedder, '_dimension', '?')
            log.error(
                f"[GnosisIndex] ⛔ Ingest blocked: embedder dim={emb_dim} ≠ table dim={table_dim}. "
                f"Vertex AI を復旧するか、reindex_gnosis.py でテーブルを再構築してください。"
            )
            return 0

        # 重複排除: primary_key + title fuzzy match
        if dedupe:
            self._load_primary_keys()
            title_cache = getattr(self, '_title_cache', {})
            new_papers = []
            for p in papers:
                # Check 1: primary_key exact match
                if p.primary_key in self._primary_key_cache:
                    continue
                # Check 2: normalized title match (cross-source dedup)
                norm_title = self._normalize_title(p.title)
                if norm_title and norm_title in title_cache:
                    # Same paper from different source — skip
                    continue
                new_papers.append(p)
                self._primary_key_cache.add(p.primary_key)
                if norm_title:
                    title_cache[norm_title] = p.primary_key
            papers = new_papers

        if not papers:
            print("[GnosisIndex] No new papers to add (all duplicates)")
            return 0

        # 埋め込み生成
        data = []
        BATCH_SIZE = 32

        for i in range(0, len(papers), BATCH_SIZE):
            batch_papers = papers[i : i + BATCH_SIZE]
            texts = [p.embedding_text for p in batch_papers]
            vectors = embedder.embed_batch(texts)

            for paper, vector in zip(batch_papers, vectors):
                record = paper.to_dict()
                record["vector"] = vector
                data.append(record)

            print(f"  Processed {min(i + BATCH_SIZE, len(papers))}/{len(papers)}...")

        # Backend に追加 (スキーマフィルタリング付き)
        if self._table_exists():
            schema_fields = self._backend.schema_fields()
            filtered_data = [
                {k: v for k, v in record.items() if k in schema_fields}
                for record in data
            ]
            self._backend.add(filtered_data)
        else:
            self._backend.create(data)

        print(f"[GnosisIndex] Added {len(data)} papers")
        return len(data)

    # PURPOSE: セマンティック検索 (ハイブリッド対応)
    def search(
        self,
        query: str,
        k: int = 10,
        source_filter: str | None = None,
        precision_weights: dict[str, float] | None = None,
        hybrid: bool = False,
        hybrid_weight: float = 0.7,
    ) -> list[dict]:
        """
        セマンティック検索 (Vector + オプション FTS ハイブリッド)

        Args:
            query: 検索クエリ
            k: 取得件数
            source_filter: ソースフィルタ (例: "arxiv", "session", "handoff")
            precision_weights: ソース別の精度加重 π (例: {"arxiv": 1.5, "session": 0.8})
                高い π = そのソースからの結果をより重視する
            hybrid: True でハイブリッド検索 (Vector + Full-Text) を有効化
            hybrid_weight: ベクトル検索の重み (0.0=FTS only, 1.0=Vector only)

        Returns:
            検索結果のリスト (precision_weights 指定時は weighted_score 付き)
        """
        if not self._table_exists():
            print("[GnosisIndex] No papers indexed yet")
            return []

        embedder = self._get_embedder()
        
        # Dimension mismatch graceful degradation
        if getattr(embedder, '_dimension_mismatch', False):
            import logging
            log = logging.getLogger(__name__)
            log.warning("[GnosisIndex] ⚠️ Dimension mismatch → FTS-only mode fallback")
            fetch_k = k * 3 if precision_weights else k
            filter_expr = f"source = '{source_filter}'" if source_filter else None
            results = self._backend.search_fts(query, fetch_k, filter_expr)
            
            # F4: Precision-weighted re-ranking
            if precision_weights and results:
                for r in results:
                    source = r.get("source", "unknown")
                    pi = precision_weights.get(source, 1.0)
                    distance = r.get("_distance", 1.0)
                    similarity = 1.0 / (1.0 + distance)
                    r["weighted_score"] = similarity * pi
                results.sort(key=lambda r: r["weighted_score"], reverse=True)
            return results[:k]

        query_vector = embedder.embed(query)

        # Dimension safety check for other cases
        embedder_dim = getattr(embedder, '_dimension', len(query_vector))
        table_dim = self._backend.get_vector_dimension()
        if table_dim and table_dim != embedder_dim:
            print(
                f"[GnosisIndex] ⚠️ Dimension mismatch: "
                f"table={table_dim}d, embedder={embedder_dim}d "
                f"({getattr(embedder, 'model_name', 'unknown')}). Cannot search.",
                flush=True,
            )
            return []

        # Fetch more results when using precision weights to allow re-ranking
        fetch_k = k * 3 if precision_weights else k

        # フィルタ式を構築
        filter_expr = f"source = '{source_filter}'" if source_filter else None

        # Hybrid search: combine vector + full-text search
        if hybrid:
            vec_results = self._backend.search_vector(query_vector, fetch_k * 2, filter_expr)
            fts_results = self._backend.search_fts(query, fetch_k * 2, filter_expr)
            if not fts_results:
                results = vec_results[:fetch_k]
            else:
                results = self._merge_rrf(
                    vec_results, fts_results,
                    vec_weight=hybrid_weight,
                    fts_weight=1.0 - hybrid_weight,
                    k=fetch_k,
                )
        else:
            results = self._backend.search_vector(query_vector, fetch_k, filter_expr)

        # F4: Precision-weighted re-ranking
        if precision_weights and results:
            for r in results:
                source = r.get("source", "unknown")
                pi = precision_weights.get(source, 1.0)
                distance = r.get("_distance", 1.0)
                # similarity = 1 / (1 + distance), then scale by π
                similarity = 1.0 / (1.0 + distance)
                r["weighted_score"] = similarity * pi
            results.sort(key=lambda r: r["weighted_score"], reverse=True)
            results = results[:k]

        return results[:k]

    # _search_vector / _search_hybrid / _search_fts は Backend に委譲済み (上記 search() 参照)

    @staticmethod
    def _merge_rrf(
        vec_results: list[dict],
        fts_results: list[dict],
        vec_weight: float,
        fts_weight: float,
        k: int,
        rrf_k: int = 60,
    ) -> list[dict]:
        """Merge results using Reciprocal Rank Fusion (RRF).

        RRF score = Σ weight / (rrf_k + rank)
        """
        scores: dict[str, float] = {}
        result_map: dict[str, dict] = {}

        # Score vector results
        for rank, r in enumerate(vec_results):
            pk = r.get("primary_key", str(rank))
            scores[pk] = scores.get(pk, 0.0) + vec_weight / (rrf_k + rank + 1)
            result_map[pk] = r

        # Score FTS results
        for rank, r in enumerate(fts_results):
            pk = r.get("primary_key", f"fts_{rank}")
            scores[pk] = scores.get(pk, 0.0) + fts_weight / (rrf_k + rank + 1)
            if pk not in result_map:
                result_map[pk] = r

        # Sort by combined score
        sorted_keys = sorted(scores.keys(), key=lambda pk: scores[pk], reverse=True)

        merged = []
        for pk in sorted_keys[:k]:
            result = result_map[pk]
            result["_rrf_score"] = scores[pk]
            merged.append(result)

        return merged

    # PURPOSE: インデックス統計
    def stats(self) -> dict:
        """インデックス統計"""
        if not self._table_exists():
            return {"total": 0, "sources": {}}

        df = self._backend.to_pandas()

        sources = df["source"].value_counts().to_dict() if "source" in df.columns else {}

        return {
            "total": len(df),
            "sources": sources,
            "unique_dois": df["doi"].notna().sum() if "doi" in df.columns else 0,
            "unique_arxiv": df["arxiv_id"].notna().sum() if "arxiv_id" in df.columns else 0,
        }

    # PURPOSE: primary_keyで論文取得
    def get_by_primary_key(self, primary_key: str) -> Optional[dict]:
        """primary_keyで論文取得"""
        if not self._table_exists():
            return None

        try:
            # FTS で primary_key を検索 (フィルタ式として使用)
            results = self._backend.search_fts(
                primary_key, k=1,
                filter_expr=f"primary_key = '{primary_key}'",
            )
            if results:
                return results[0]
            # フォールバック: 全データから検索
            for record in self._backend.to_list():
                if record.get("primary_key") == primary_key:
                    return record
            return None
        except Exception:  # noqa: BLE001
            return None  # Intentional: query may fail on malformed key or empty table

    # PURPOSE: FTS インデックスを構築 (ハイブリッド検索用)
    def build_fts_index(self, fields: list[str] | None = None, replace: bool = True) -> bool:
        """FTS (Full-Text Search) インデックスを構築する。

        build_fts_index をサポートする Backend のみ有効。FAISS/NumPy では no-op (キーワードマッチで代替)。

        Args:
            fields: FTS 対象フィールド (デフォルト: ["title", "abstract"])
            replace: 既存 FTS インデックスを置換するか

        Returns:
            True if successful, False otherwise
        """
        if not self._table_exists():
            print("[FTS] テーブルが存在しません")
            return False

        if fields is None:
            fields = ["title", "abstract"]

        # build_fts_index をサポートする Backend のみ FTS 構築
        if hasattr(self._backend, 'build_fts_index'):
            return self._backend.build_fts_index(fields, replace)

        # FAISS/NumPy は FTS 不要 (search_fts でキーワードマッチ)
        print(f"[FTS] ℹ️ {self._backend_name} backend — FTS は search_fts() 内蔵")
        return True

    # PURPOSE: 指定ソースのレコードを削除 (再インデックス用)
    def drop_source(self, source: str) -> int:
        """指定ソースのレコードをすべて削除する。

        再インデックス時に古いレコードを除去するために使用。
        チャンキング対応前のレコードを削除して再投入する際に便利。

        Args:
            source: 削除対象のソース名 (例: "handoff", "rom")

        Returns:
            削除されたレコード数
        """
        if not self._table_exists():
            return 0

        try:
            deleted = self._backend.delete(f"source = '{source}'")

            if deleted == 0:
                print(f"[Drop] source='{source}' のレコードはありません")
                return 0

            # Clear primary key cache
            self._primary_key_cache.clear()

            print(f"[Drop] ✅ source='{source}' の {deleted} 件を削除")
            return deleted
        except Exception as e:  # noqa: BLE001
            print(f"[Drop] ❌ 削除失敗: {e}")
            return 0

    # ── スキーマ拡張 (F2 マイグレーション) ────────────────────────

    # Hyphē + F2 拡張フィールド定義
    HYPHE_F2_COLUMNS: dict[str, object] = {
        # Hyphē フィールド
        "content": "",
        "chunk_index": 0,
        "parent_id": "",
        "section_title": "",
        "precision": 0.5,
        "density": 0.0,
        "session_id": "",
        "project_id": "",
        "metadata_json": "{}",
        # F2 分類フィールド
        "cluster_label": "",
        "f2_tags": "",
        "f2_confidence": 0.0,
    }

    # PURPOSE: スキーマに Hyphē + F2 フィールドを追加
    def migrate_schema(self) -> int:
        """テーブルに Hyphē + F2 拡張フィールドを追加する。

        既存テーブルに欠損カラムがあればデフォルト値で埋めて再作成する。
        全カラムが揃っていれば何もしない (冪等)。

        Returns:
            マイグレーションされたレコード数 (変更不要なら 0)
        """
        if not hasattr(self._backend, 'migrate_schema'):
            import logging
            logging.getLogger(__name__).warning(
                f"[GnosisIndex] {self._backend_name} backend は migrate_schema 未対応"
            )
            return 0

        return self._backend.migrate_schema(self.HYPHE_F2_COLUMNS)

    # PURPOSE: F2 分類結果をインデックスに書き戻す
    def update_f2_fields(
        self,
        classifications: list[dict],
    ) -> int:
        """F2 分類結果を既存レコードに書き戻す。

        FieldClassifier の出力 (session_id, cluster_label, tags, confidence) を
        該当する session_id のレコード群に反映する。

        Args:
            classifications: [{"session_id": str, "cluster_label": str,
                              "tags": list[str], "confidence": float}, ...]

        Returns:
            更新されたレコード数
        """
        if not self._table_exists():
            return 0

        # スキーマにF2フィールドがあるか確認
        fields = self._backend.schema_fields()
        if "cluster_label" not in fields:
            print("[GnosisIndex] ⚠️ cluster_label カラムがありません。migrate_schema() を先に実行してください")
            return 0

        # session_id → classification のマッピング
        cls_map = {c["session_id"]: c for c in classifications}
        if not cls_map:
            return 0

        # 全レコード読み出し → 該当レコードを更新
        records = self._backend.to_list()
        updated = 0

        for record in records:
            sid = record.get("session_id", "")
            if sid and sid in cls_map:
                c = cls_map[sid]
                record["cluster_label"] = c.get("cluster_label", "")
                record["f2_tags"] = ", ".join(c.get("tags", []))
                record["f2_confidence"] = c.get("confidence", 0.0)
                updated += 1

        if updated == 0:
            return 0

        # バッチ更新: 全削除 → 再投入
        self._backend.delete("true")
        self._backend.add(records)

        print(f"[GnosisIndex] ✅ F2 分類を {updated} レコードに反映")
        return updated

    # ── Hyphē Field 拡張 ──────────────────────────────────────

    # PURPOSE: チャンクを場に溶解 (F: Source → Field)
    def add_chunks(
        self,
        chunks: list[dict],
        source: str = "session",
        session_id: str = "",
        project_id: str = "",
        dedupe: bool = True,
    ) -> int:
        """チャンクを embedding 付きでインデックスに投入する。

        chunker.chunk() の出力 ({id, parent_id, text, section_title, chunk_index, ...})
        を受け取り、embedding を生成してテーブルに追加する。

        Args:
            chunks: chunker.chunk() の出力リスト
            source: データソース種別 ("session", "handoff", "rom", "ki")
            session_id: 関連セッション ID
            project_id: 関連プロジェクト ID
            dedupe: 重複排除を行うか (primary_key ベース)

        Returns:
            追加されたチャンク数
        """
        if not chunks:
            return 0

        embedder = self._get_embedder()

        # 次元不一致ガード
        if getattr(embedder, '_dimension_mismatch', False):
            import logging
            log = logging.getLogger(__name__)
            log.error("[GnosisIndex] ⛔ add_chunks blocked: dimension mismatch")
            return 0

        # 重複排除
        if dedupe:
            self._load_primary_keys()
            new_chunks = [
                c for c in chunks
                if c.get("id", "") not in self._primary_key_cache
            ]
            chunks = new_chunks

        if not chunks:
            print("[GnosisIndex] No new chunks to add (all duplicates)")
            return 0

        # Embedding 生成
        data = []
        BATCH_SIZE = 32
        texts = [c["text"] for c in chunks]

        for i in range(0, len(texts), BATCH_SIZE):
            batch_texts = texts[i:i + BATCH_SIZE]
            batch_chunks = chunks[i:i + BATCH_SIZE]
            vectors = embedder.embed_batch(batch_texts)

            for chunk, vector in zip(batch_chunks, vectors):
                import json
                # チャンク固有メタデータ (coherence, drift, efe) を metadata_json に格納
                extra_meta = {}
                for key in ("coherence", "drift", "efe"):
                    if key in chunk:
                        extra_meta[key] = chunk[key]

                record = {
                    "id": chunk["id"],
                    "primary_key": chunk["id"],
                    "source": source,
                    "source_id": chunk.get("parent_id", ""),
                    "title": chunk.get("section_title", ""),
                    "abstract": "",  # 論文用フィールド (チャンクでは未使用)
                    "authors": "",
                    "published": "",
                    "url": "",
                    "pdf_url": "",
                    "citations": 0,
                    "categories": "",
                    "venue": "",
                    "collected_at": "",
                    "doi": "",
                    "arxiv_id": "",
                    "vector": vector,
                    # Hyphē 拡張フィールド
                    "content": chunk["text"],
                    "chunk_index": chunk.get("chunk_index", 0),
                    "parent_id": chunk.get("parent_id", ""),
                    "section_title": chunk.get("section_title", ""),
                    "precision": chunk.get("precision", 0.5),
                    "density": chunk.get("density", 0.0),
                    "session_id": session_id,
                    "project_id": project_id,
                    "metadata_json": json.dumps(extra_meta, ensure_ascii=False) if extra_meta else "{}",
                    # F2 分類フィールド (FieldClassifier が後から書き戻す)
                    "cluster_label": "",
                    "f2_tags": "",
                    "f2_confidence": 0.0,
                }
                data.append(record)
                self._primary_key_cache.add(chunk["id"])

            print(f"  Dissolved {min(i + BATCH_SIZE, len(texts))}/{len(texts)} chunks...")

        # Backend に追加
        if self._table_exists():
            schema_fields = self._backend.schema_fields()
            data_fields = set(data[0].keys()) if data else set()
            missing_fields = data_fields - schema_fields - {"vector"}

            # スキーマに足りないフィールドがあれば自動マイグレーション
            if missing_fields and hasattr(self._backend, 'migrate_schema'):
                new_cols = {k: v for k, v in self.HYPHE_F2_COLUMNS.items() if k in missing_fields}
                if new_cols:
                    import logging
                    logging.getLogger(__name__).info(
                        f"[GnosisIndex] Auto-migrate: adding {list(new_cols.keys())}"
                    )
                    self._backend.migrate_schema(new_cols)
                    schema_fields = self._backend.schema_fields()

            filtered_data = [
                {k: v for k, v in record.items() if k in schema_fields}
                for record in data
            ]
            self._backend.add(filtered_data)
        else:
            self._backend.create(data)

        print(f"[GnosisIndex] ✅ Dissolved {len(data)} chunks (source={source})")
        return len(data)

    # PURPOSE: k-NN 密度推定で ρ_MB を再計算 (NumPy 演算)
    def update_density(self, k: int = 10) -> int:
        """全チャンクの density (ρ_MB) を k-NN 密度推定で再計算する。

        ストレージからベクトルを NumPy に取り出し、k-NN 距離の平均逆数で密度を推定。
        結果は [0, 1] に正規化してストレージに書き戻す。

        Args:
            k: 近傍数 (デフォルト 10)

        Returns:
            更新されたレコード数
        """
        if not self._table_exists():
            return 0

        import numpy as np

        df = self._backend.to_pandas()

        if len(df) < 2:
            return 0

        # ベクトル取得
        vectors = np.array(df["vector"].tolist())
        n = len(vectors)
        effective_k = min(k, n - 1)

        if effective_k < 1:
            return 0

        # k-NN 距離計算 (コサイン距離)
        # 正規化
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        normalized = vectors / norms

        # コサイン類似度行列
        sim_matrix = normalized @ normalized.T
        np.fill_diagonal(sim_matrix, -np.inf)  # 自分自身を除外

        # k-NN の平均類似度 → 密度推定
        densities = np.zeros(n)
        for i in range(n):
            top_k_indices = np.argsort(sim_matrix[i])[-effective_k:]
            densities[i] = np.mean(sim_matrix[i][top_k_indices])

        # [0, 1] に正規化 (min-max)
        d_min, d_max = densities.min(), densities.max()
        if d_max > d_min:
            densities = (densities - d_min) / (d_max - d_min)
        else:
            densities = np.full(n, 0.5)

        # density フィールドがスキーマにあるか確認
        if "density" not in self._backend.schema_fields():
            print("[GnosisIndex] ⚠️ density フィールドがスキーマにありません。新しいテーブルで再作成が必要です")
            return 0

        # バッチ更新: 全レコードを削除して再投入
        records = self._backend.to_list()
        for i, record in enumerate(records):
            record["density"] = float(densities[i])

        self._backend.delete("true")  # 全削除
        self._backend.add(records)

        print(f"[GnosisIndex] ✅ Updated density for {n} records (k={effective_k})")
        return n

    # ── Facade API (外部ファイル向け) ──────────────────────────

    # PURPOSE: 全 primary_key の集合を返す (dedupe 用)
    def list_primary_keys(self) -> set[str]:
        """全 primary_key の集合を返す。

        session_indexer 等で重複排除チェックに使用。
        Backend の to_pandas() を使い、primary_key カラムを抽出する。

        Returns:
            primary_key の集合。テーブル未存在時は空集合。
        """
        if not self._table_exists():
            return set()

        try:
            df = self._backend.to_pandas()
            if "primary_key" in df.columns:
                return set(df["primary_key"].dropna().tolist())
            return set()
        except Exception:  # noqa: BLE001
            return set()

    # PURPOSE: フィルタ付き DataFrame 取得 (ダッシュボード・集計用)
    def filter_to_pandas(self, filter_expr: Optional[str] = None) -> "pd.DataFrame":
        """フィルタ条件を満たすレコードを pandas DataFrame で返す。

        cli.py のダッシュボードや gnosis_chat の集計で使用。
        filter_expr が None の場合は全レコードを返す。

        Args:
            filter_expr: フィルタ式 (例: "source = 'export'")。
                        None の場合は全レコード。

        Returns:
            pandas DataFrame。テーブル未存在時は空 DataFrame。
        """
        import pandas as pd

        if not self._table_exists():
            return pd.DataFrame()

        try:
            df = self._backend.to_pandas()
            if filter_expr is None:
                return df

            # 簡易フィルタ: "field = 'value'" をパース
            import re
            match = re.match(r"(\w+)\s*=\s*'([^']*)'", filter_expr.strip())
            if match:
                field, value = match.groups()
                if field in df.columns:
                    return df[df[field] == value]
            return df
        except Exception:  # noqa: BLE001
            return pd.DataFrame()

    # PURPOSE: レコードを直接追加 (embedding 済みデータ用)
    def add_records(self, records: list[dict]) -> int:
        """embedding 済みのレコードを直接追加する。

        session_indexer 等で embedding を独自生成した後に使用。
        スキーマフィルタリングを自動適用する。

        Args:
            records: vector フィールドを含むレコードのリスト

        Returns:
            追加されたレコード数
        """
        if not records:
            return 0

        if self._table_exists():
            schema_fields = self._backend.schema_fields()
            filtered = [
                {k: v for k, v in r.items() if k in schema_fields}
                for r in records
            ]
            self._backend.add(filtered)
        else:
            self._backend.create(records)

        return len(records)

    # PURPOSE: テーブル存在確認の公開版 (proactive_push 等用)
    def table_exists(self) -> bool:
        """テーブルが存在するか (公開 API)。

        外部コードが index._table_exists() の代わりに使う。

        Returns:
            テーブルが存在すれば True。
        """
        return self._table_exists()

    # PURPOSE: Backend の公開アクセサ (テスト用)
    @property
    def backend(self):
        """StorageBackend インスタンスへの読取専用アクセス。"""
        return self._backend
