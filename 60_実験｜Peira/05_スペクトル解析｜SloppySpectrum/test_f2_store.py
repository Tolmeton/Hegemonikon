#!/usr/bin/env python3
# PROOF: [L2/テスト] <- mekhane/symploke/motherbrain_store.py
# PURPOSE: F2 DB Schema (field_axes + session_classifications) の統合テスト
"""
F2 Store テスト — FieldAxes / SessionClassification の CRUD + エッジケース

テスト対象:
  - FieldAxes: 保存・復元 (BLOB ヘッダ付き新形式 + 旧形式フォールバック)
  - SessionClassification: CRUD, バッチ保存, UPSERT, フィルタ, サマリ
  - エッジケース: k=1 最小軸, float32 入力, ISO8601 computed_at 保持
"""

import json
import struct
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "20_機構｜Mekhane" / "_src｜ソースコード"))

from mekhane.symploke.motherbrain_store import MotherbrainStore
from mekhane.anamnesis.fisher_field import FieldAxes
from mekhane.symploke.field_classifier import ClassificationResult


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def store(tmp_path):
    """一時 DB を使う MotherbrainStore を提供"""
    db_path = tmp_path / "test_f2.db"
    s = MotherbrainStore(db_path)
    yield s
    s.close()


@pytest.fixture
def sample_axes():
    """標準的な FieldAxes (3×2, float64)"""
    return FieldAxes(
        eigenvectors=np.array([
            [1.0, 0.0],
            [0.0, 1.0],
            [0.5, 0.5],
        ], dtype=np.float64),
        eigenvalues=np.array([2.5, 1.2], dtype=np.float64),
        k=2,
        gap_index=1,
        sloppy_ratio=0.75,
        computed_at=datetime.now(timezone.utc).isoformat(),
        total_points=100,
    )


@pytest.fixture
def sample_results():
    """3つの ClassificationResult"""
    return [
        ClassificationResult(
            session_id="sess_001",
            cluster_id=0,
            cluster_label="cluster_A",
            coords=np.array([1.5, -0.5]),
            tags=["tag1", "tag2"],
            confidence=0.9,
        ),
        ClassificationResult(
            session_id="sess_002",
            cluster_id=1,
            cluster_label="cluster_B",
            coords=np.array([-1.5, 2.5]),
            tags=["tag3"],
            confidence=0.8,
        ),
        ClassificationResult(
            session_id="sess_003",
            cluster_id=0,
            cluster_label="cluster_A",
            coords=np.array([1.2, -0.1]),
            tags=["tag1"],
            confidence=0.85,
        ),
    ]


# ── FieldAxes テスト ──────────────────────────────────────

class TestFieldAxes:
    """FieldAxes の保存・復元テスト"""

    def test_save_and_load_roundtrip(self, store, sample_axes):
        """保存→復元で eigenvectors/eigenvalues が完全一致"""
        axes_id = store.save_field_axes(sample_axes, source_filter="test")
        assert axes_id > 0

        loaded = store.load_field_axes(axes_id)
        assert loaded is not None
        assert np.allclose(loaded.eigenvectors, sample_axes.eigenvectors)
        assert np.allclose(loaded.eigenvalues, sample_axes.eigenvalues)
        assert loaded.k == sample_axes.k
        assert loaded.gap_index == sample_axes.gap_index
        assert loaded.total_points == sample_axes.total_points

    def test_computed_at_preserved(self, store, sample_axes):
        """E1 修正: computed_at (ISO8601 str) が保存→復元で保持される"""
        original_ts = sample_axes.computed_at
        axes_id = store.save_field_axes(sample_axes)
        loaded = store.load_field_axes(axes_id)
        assert loaded is not None
        # ISO8601 文字列がそのまま保存されていること
        assert loaded.computed_at == original_ts

    def test_blob_header_shape_recovery(self, store, sample_axes):
        """E2 修正: BLOB ヘッダから正しい shape (d, k) が復元される"""
        axes_id = store.save_field_axes(sample_axes)
        loaded = store.load_field_axes(axes_id)
        assert loaded is not None
        assert loaded.eigenvectors.shape == sample_axes.eigenvectors.shape

    def test_float32_input_stored_as_float64(self, store):
        """E2 修正: float32 入力が float64 として正しく保存・復元される"""
        axes_f32 = FieldAxes(
            eigenvectors=np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
            eigenvalues=np.array([3.0, 1.0], dtype=np.float64),
            k=2,
            computed_at=datetime.now(timezone.utc).isoformat(),
        )
        axes_id = store.save_field_axes(axes_f32)
        loaded = store.load_field_axes(axes_id)
        assert loaded is not None
        # float32 → float64 に変換されて保存
        assert loaded.eigenvectors.dtype == np.float64
        assert np.allclose(loaded.eigenvectors, axes_f32.eigenvectors.astype(np.float64))

    def test_k1_minimal_axes(self, store):
        """エッジケース: k=1 (最小軸数) の保存・復元"""
        axes_k1 = FieldAxes(
            eigenvectors=np.array([[1.0], [0.5], [0.3]], dtype=np.float64),
            eigenvalues=np.array([5.0], dtype=np.float64),
            k=1,
            gap_index=0,
            sloppy_ratio=0.0,
            computed_at=datetime.now(timezone.utc).isoformat(),
            total_points=10,
        )
        axes_id = store.save_field_axes(axes_k1)
        loaded = store.load_field_axes(axes_id)
        assert loaded is not None
        assert loaded.eigenvectors.shape == (3, 1)
        assert np.allclose(loaded.eigenvectors, axes_k1.eigenvectors)

    def test_get_latest_field_axes(self, store, sample_axes):
        """get_latest_field_axes が最新のレコードを返す"""
        axes_id = store.save_field_axes(sample_axes, source_filter="test", use_centroids=True)
        latest = store.get_latest_field_axes()
        assert latest is not None
        assert latest["id"] == axes_id
        assert latest["source_filter"] == "test"
        assert latest["use_centroids"] == 1

    def test_load_nonexistent_returns_none(self, store):
        """存在しない axes_id は None を返す"""
        assert store.load_field_axes(9999) is None

    def test_load_latest_when_empty_returns_none(self, store):
        """テーブルが空の場合 load_field_axes(None) は None を返す"""
        assert store.load_field_axes() is None


# ── SessionClassification テスト ──────────────────────────

class TestSessionClassification:
    """SessionClassification の CRUD テスト"""

    def test_batch_save_and_retrieve(self, store, sample_axes, sample_results):
        """バッチ保存→全件取得"""
        axes_id = store.save_field_axes(sample_axes)
        n = store.save_classifications_batch(sample_results, axes_id)
        assert n == 3

        all_sc = store.get_all_classifications(axes_id)
        assert len(all_sc) == 3

    def test_single_get_with_axes_id(self, store, sample_axes, sample_results):
        """特定の session_id + axes_id で 1件取得"""
        axes_id = store.save_field_axes(sample_axes)
        store.save_classifications_batch(sample_results, axes_id)

        sc = store.get_session_classification("sess_001", axes_id)
        assert sc is not None
        assert sc["cluster_label"] == "cluster_A"
        assert sc["confidence"] == 0.9
        assert json.loads(sc["tags_json"]) == ["tag1", "tag2"]

    def test_single_get_latest_axes(self, store, sample_axes, sample_results):
        """axes_id 省略時に最新の axes で取得"""
        axes_id = store.save_field_axes(sample_axes)
        store.save_classifications_batch(sample_results, axes_id)

        sc = store.get_session_classification("sess_002")
        assert sc is not None
        assert sc["axes_id"] == axes_id

    def test_filter_by_cluster_label(self, store, sample_axes, sample_results):
        """cluster_label でフィルタ"""
        axes_id = store.save_field_axes(sample_axes)
        store.save_classifications_batch(sample_results, axes_id)

        a_only = store.get_all_classifications(axes_id, cluster_label="cluster_A")
        assert len(a_only) == 2
        for r in a_only:
            assert r["cluster_label"] == "cluster_A"

    def test_summary(self, store, sample_axes, sample_results):
        """クラスタラベル別サマリ"""
        axes_id = store.save_field_axes(sample_axes)
        store.save_classifications_batch(sample_results, axes_id)

        summary = store.get_classification_summary(axes_id)
        assert len(summary) == 2
        a_sum = next(s for s in summary if s["cluster_label"] == "cluster_A")
        assert a_sum["count"] == 2

    def test_upsert_updates_existing(self, store, sample_axes, sample_results):
        """E3 修正: 同一 (session_id, axes_id) で UPSERT が機能"""
        axes_id = store.save_field_axes(sample_axes)
        store.save_classifications_batch(sample_results, axes_id)

        # sess_001 を更新
        updated = ClassificationResult(
            session_id="sess_001",
            cluster_id=0,
            cluster_label="cluster_A_mod",
            coords=np.array([1.5, -0.5]),
            tags=["tag1", "tag2", "tagX"],
            confidence=0.95,
        )
        store.save_classification(updated, axes_id)

        sc = store.get_session_classification("sess_001", axes_id)
        assert sc["cluster_label"] == "cluster_A_mod"
        assert sc["confidence"] == 0.95
        assert "tagX" in json.loads(sc["tags_json"])

    def test_get_nonexistent_session(self, store, sample_axes):
        """存在しないセッションは None"""
        axes_id = store.save_field_axes(sample_axes)
        assert store.get_session_classification("nonexistent", axes_id) is None

    def test_summary_empty_db(self, store):
        """空 DB でサマリは空リスト"""
        assert store.get_classification_summary() == []

    def test_all_classifications_empty_db(self, store):
        """空 DB で全件取得は空リスト"""
        assert store.get_all_classifications() == []


# ── E6: _get_latest_axes_id ヘルパーテスト ────────────────

class TestHelpers:

    def test_get_latest_axes_id_empty(self, store):
        """空 DB で _get_latest_axes_id は None"""
        assert store._get_latest_axes_id() is None

    def test_get_latest_axes_id_multiple(self, store, sample_axes):
        """複数 axes 保存時に最大 id を返す"""
        id1 = store.save_field_axes(sample_axes)
        id2 = store.save_field_axes(sample_axes)
        assert store._get_latest_axes_id() == id2
        assert id2 > id1
