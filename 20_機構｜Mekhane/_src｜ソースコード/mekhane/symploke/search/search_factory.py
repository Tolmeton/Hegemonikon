# PROOF: [L2/インフラ] <- mekhane/symploke/search/search_factory.py A0→検索エンジン提供が必要→search_factory が担う
"""
SearchEngine Factory (Singleton Cache)

遅延インポートと各ソースのインデックス初期化を隠蔽し、
指定されたソースを持つ SearchEngine インスタンスを提供する。

G1 解消: ソースセットごとにキャッシュし、同一構成の SearchEngine は再利用する。
"""

import logging
from typing import Dict, List, Tuple

from .engine import SearchEngine

logger = logging.getLogger("hegemonikon.symploke.search_factory")

# Singleton cache: frozenset(sources) → SearchEngine
_engine_cache: Dict[frozenset, SearchEngine] = {}


# PURPOSE: SearchEngine のファクトリ関数 (シングルトンキャッシュ付き)
def get_search_engine(sources: List[str]) -> Tuple[SearchEngine, List[str]]:
    """
    指定ソースに対応する DomainIndex を登録した SearchEngine を返す。
    同一ソースセットの2回目以降はキャッシュから返す (G1 解消)。
    初期化に失敗したソースは errors リストで返す (G5 解消)。

    Args:
        sources: 検索対象ソース名のリスト (例: ["handoff", "gnosis"])

    Returns:
        (SearchEngine インスタンス, 初期化失敗ソースのリスト)
    """
    source_key = frozenset(sources)

    if source_key in _engine_cache:
        return _engine_cache[source_key], []

    engine = SearchEngine()
    errors: List[str] = []

    from ..adapters.vector_store import VectorStore
    from ..indices import (
        ChronosIndex,
        SophiaIndex,
        KairosIndex,
        HandoffIndex,
    )
    from ..indices.doxa import DoxaIndex
    from ..indices.gnosis_bridge import GnosisBridge

    domain_classes = {
        "gnosis": GnosisBridge,  # FAISS backend (610 papers) — GnosisIndex は stub
        "chronos": ChronosIndex,
        "sophia": SophiaIndex,
        "kairos": KairosIndex,
        "handoff": HandoffIndex,
        "doxa": DoxaIndex,
    }

    for source in sources:
        IndexClass = domain_classes.get(source)
        if not IndexClass:
            continue
        try:
            if source == "gnosis":
                # GnosisBridge は adapter 不要 (FAISS backend を自己管理)
                index = GnosisBridge()
            else:
                adapter = VectorStore()
                index = IndexClass(adapter, source, dimension=0)
                index.initialize()
            engine.register(index)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to initialize %s index: %s", source, exc)
            errors.append(source)

    _engine_cache[source_key] = engine
    return engine, errors


# PURPOSE: キャッシュのクリア (テスト用)
def clear_cache() -> None:
    """SearchEngine キャッシュをクリアする (テスト / ホットリロード用)。"""
    _engine_cache.clear()
