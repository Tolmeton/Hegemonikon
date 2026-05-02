# PROOF: [L3/テスト] <- mekhane/symploke/tests/test_incremental_rebuild_manifest.py 差分更新の manifest 復旧が必要→回帰防止テストが担う
"""
Regression tests for incremental rebuild when only FAISS/meta files remain.
"""

from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class _FakeVectorStore:
    def __init__(self, count: int):
        self._count = count
        self.saved_manifest = None
        self.saved_path = None

    def load(self, path: str):
        self.loaded_path = path
        return {}

    def save(self, path: str, manifest=None) -> None:
        self.saved_path = path
        self.saved_manifest = manifest

    def count(self) -> int:
        return self._count

    def delete_by_source(self, _source: str) -> None:
        raise AssertionError("delete_by_source should not run during manifest bootstrap")


def test_incremental_rebuild_sophia_bootstraps_manifest_without_full_rebuild(monkeypatch, tmp_path):
    from mekhane.symploke import sophia_ingest

    fake_store = _FakeVectorStore(count=6139)
    index_path = tmp_path / "sophia.pkl"
    current_manifest = {str(tmp_path / "note.md"): 123.0}

    monkeypatch.setattr("mekhane.symploke.adapters.vector_store.VectorStore", lambda: fake_store)
    monkeypatch.setattr(sophia_ingest, "_build_sophia_manifest", lambda: current_manifest)
    monkeypatch.setattr(sophia_ingest, "get_all_documents", lambda: pytest.fail("full rebuild must not run"))
    monkeypatch.setattr(sophia_ingest, "ingest_to_sophia", lambda *args, **kwargs: pytest.fail("full rebuild must not run"))

    stats = sophia_ingest.incremental_rebuild_sophia(str(index_path))

    assert fake_store.saved_path == str(index_path)
    assert fake_store.saved_manifest == current_manifest
    assert stats == {"added": 0, "updated": 0, "deleted": 0, "unchanged": 1, "total": 6139}


def test_incremental_rebuild_code_bootstraps_manifest_without_full_rebuild(monkeypatch, tmp_path):
    from mekhane.symploke import code_ingest

    fake_store = _FakeVectorStore(count=31774)
    index_path = tmp_path / "code.pkl"
    current_manifest = {str(tmp_path / "module.py"): 456.0}

    monkeypatch.setattr("mekhane.symploke.adapters.vector_store.VectorStore", lambda: fake_store)
    monkeypatch.setattr(code_ingest, "_build_code_manifest", lambda: current_manifest)
    monkeypatch.setattr(code_ingest, "get_all_code_documents", lambda: pytest.fail("full rebuild must not run"))
    monkeypatch.setattr(code_ingest, "ingest_to_code", lambda *args, **kwargs: pytest.fail("full rebuild must not run"))

    stats = code_ingest.incremental_rebuild_code(str(index_path))

    assert fake_store.saved_path == str(index_path)
    assert fake_store.saved_manifest == current_manifest
    assert stats == {"added": 0, "updated": 0, "deleted": 0, "unchanged": 1, "total": 31774}
