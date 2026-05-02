#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/indices/ A0→Gnōsis への直接アクセスが必要
"""
Gnōsis Bridge — Anamnesis GnosisIndex を Symplokē DomainIndex として公開

27,432件の論文データを持つ GnosisIndex を、再エンベッドせずに
Symplokē SearchEngine の gnosis ソースとして使う。

Usage:
    bridge = GnosisBridge()
    engine.register(bridge)  # SearchEngine に登録
    results = engine.search("active inference", sources=["gnosis"])
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

from .base import DomainIndex, SourceType, IndexedResult, Document

# Anamnesis のパス解決
_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # hegemonikon/
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# PURPOSE: Gnōsis を Symplokē DomainIndex として公開するブリッジ
class GnosisBridge(DomainIndex):
    """Gnōsis を Symplokē DomainIndex として公開するブリッジ

    Anamnesis の GnosisIndex を内部で使い、
    Symplokē の DomainIndex インターフェースに変換する。

    特徴:
    - 再エンベッド不要 (GnosisIndex の既存ベクトルを直接使用)
    - 27,432件の論文データに即座にアクセス
    - adapter は使わず、GnosisIndex の search API を直接呼ぶ
    """

    # PURPOSE: Gnōsis ブリッジの初期化
    def __init__(self, db_dir: Optional[Path] = None):
        """
        Args:
            db_dir: Gnōsis DB ディレクトリ (None = デフォルト)
        """
        # DomainIndex.__init__ には adapter が必要だが、
        # このブリッジは adapter を使わないので None を渡す
        super().__init__(adapter=None, name="gnosis", dimension=3072)
        self._db_dir = db_dir
        self._lance_index = None
        self._initialized = True  # GnosisIndex は initialize 不要

    # PURPOSE: [L2-auto] source_type の関数定義
    @property
    def source_type(self) -> SourceType:
        return SourceType.GNOSIS

    # PURPOSE: GnosisIndex を遅延初期化
    def _get_lance_index(self):
        """GnosisIndex を遅延初期化"""
        if self._lance_index is None:
            # プロキシ回避
            for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
                os.environ.pop(key, None)
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"

            from mekhane.anamnesis.index import GnosisIndex as AnamnesisGnosisIndex
            self._lance_index = AnamnesisGnosisIndex(db_dir=self._db_dir)
        return self._lance_index

    # PURPOSE: Gnōsis 検索 → Symplokē IndexedResult 変換
    def search(self, query: str, k: int = 10, **kwargs) -> List[IndexedResult]:
        """Gnōsis 検索 → Symplokē IndexedResult 変換"""
        try:
            lance = self._get_lance_index()
            raw_results = lance.search(query, k=k)
        except Exception as e:  # noqa: BLE001
            print(f"[GnosisBridge] Search error: {e}", file=sys.stderr)
            return []

        results = []
        for r in raw_results:
            # _distance を 0-1 スコアに変換
            distance = r.get("_distance", float("inf"))
            score = max(0.0, 1.0 - (distance / 2.0))

            results.append(
                IndexedResult(
                    doc_id=r.get("doi", r.get("arxiv_id", str(hash(r.get("title", ""))))),
                    score=score,
                    source=SourceType.GNOSIS,
                    content=r.get("abstract", ""),
                    metadata={
                        "title": r.get("title", "Untitled"),
                        "authors": r.get("authors", ""),
                        "source": r.get("source", "unknown"),
                        "url": r.get("url", ""),
                        "citations": r.get("citations", 0),
                    },
                )
            )

        return results

    # PURPOSE: Gnōsis の論文数を返す
    def count(self) -> int:
        """Gnōsis の論文数を返す (stats() は to_pandas() で全ベクトル展開するため使わない)"""
        try:
            lance = self._get_lance_index()
            # FAISSBackend の ntotal を直接取得 (stats() は 5GB メモリ消費するため回避)
            backend = lance._backend
            backend._load()
            if backend._index is not None:
                return backend._index.ntotal
            return len(backend._metadata)
        except Exception:  # noqa: BLE001
            return 0

    # PURPOSE: ブリッジは ingest をサポートしない
    def ingest(self, documents: List[Document]) -> int:
        """ブリッジは ingest をサポートしない (Anamnesis 経由で追加)"""
        raise NotImplementedError(
            "GnosisBridge does not support ingest. "
            "Use Anamnesis GnosisIndex directly."
        )

    # PURPOSE: ブリッジは initialize 不要
    def initialize(self) -> None:
        """ブリッジは initialize 不要 (GnosisIndex は自己管理)"""
        self._initialized = True

    # PURPOSE: ブリッジは save/load 不要
    def save(self, path: str) -> None:
        pass

    # PURPOSE: [L2-auto] load の関数定義
    def load(self, path: str) -> None:
        self._initialized = True
