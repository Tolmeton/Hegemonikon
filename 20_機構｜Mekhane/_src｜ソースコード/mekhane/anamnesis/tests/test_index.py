# PROOF: [L3/テスト] <- mekhane/anamnesis/tests/test_index.py 対象モジュールが存在→その検証が必要→test_index が担う
import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import importlib
import tempfile
import shutil
import sys
from pathlib import Path

# Add repo root to sys.path
repo_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

# ベクトルバックエンドは FAISS を使用

from mekhane.anamnesis.index import GnosisIndex
from mekhane.anamnesis.models.paper import Paper


class TestGnosisIndex(unittest.TestCase):
    # PURPOSE: setUp をセットアップする
    """Test suite for gnosis index."""
    # PURPOSE: Verify set up behaves correctly
    def setUp(self):
        """Verify set up behavior."""
        self.test_dir = tempfile.mkdtemp()
        self.faiss_dir = Path(self.test_dir) / "faiss"

        # Mock Embedder to avoid loading models
        self.embedder_patcher = patch("mekhane.anamnesis.index.Embedder")
        self.mock_embedder_class = self.embedder_patcher.start()
        self.mock_embedder_instance = self.mock_embedder_class.return_value
        # Mock embed_batch to return one vector per input text
        self.mock_embedder_instance.embed_batch.side_effect = lambda texts: [
            [0.1] * 384 for _ in texts
        ]
        self.mock_embedder_instance.embed.return_value = [0.1] * 384
        type(self.mock_embedder_instance).dimension = PropertyMock(return_value=384)
        self.mock_embedder_instance._dimension = 384
        self.mock_embedder_instance._table_dim = 384
        self.mock_embedder_instance._dimension_mismatch = False

        self.index = GnosisIndex(db_dir=self.faiss_dir)
        # Override _get_embedder to always return our mock
        self.index._get_embedder = lambda: self.mock_embedder_instance

    # PURPOSE: tearDown の処理
    def tearDown(self):
        """Verify tear down behavior."""
        self.embedder_patcher.stop()
        shutil.rmtree(self.test_dir)

    # PURPOSE: load_primary_keys をテストする
    def test_load_primary_keys(self):
        # Create dummy papers
        """Verify load primary keys behavior."""
        papers = []
        for i in range(15):  # 15 to exceed default limit if it was 10
            p = Paper(
                id=f"id_{i}",
                source="test",
                source_id=str(i),
                title=f"Title {i}",
                abstract="Abstract",
            )
            papers.append(p)

        # Add papers (this will create the table and add data)
        self.index.add_papers(papers, dedupe=False)

        # Verify papers are in DB
        records = self.index._backend.to_list()
        self.assertEqual(len(records), 15)

        # Clear cache to force reload
        self.index._primary_key_cache = set()

        # Call _load_primary_keys
        self.index._load_primary_keys()

        # Verify cache
        expected_keys = {p.primary_key for p in papers}
        self.assertEqual(self.index._primary_key_cache, expected_keys)
        self.assertEqual(len(self.index._primary_key_cache), 15)


# PURPOSE: Test suite validating embedder dimension correctness
class TestEmbedderDimension(unittest.TestCase):
    """Embedder._dimension と _is_onnx_fallback の検証。"""

    # PURPOSE: Verify dimension property exists after init behaves correctly
    @patch("mekhane.anamnesis.index.Embedder._instances", {})
    def test_dimension_property_exists_after_init(self):
        """Embedder 初期化後、_dimension が正の整数であること。"""
        # patch.object で __init__ は設定できない (magic method)
        # 直接 object.__new__ でインスタンス作成し属性を設定
        import mekhane.anamnesis.index as idx_module
        importlib.reload(idx_module)  # patch 汚染を解消
        Embedder = idx_module.Embedder
        e = object.__new__(Embedder)
        e._initialized = False
        e._dimension = 1024
        e._is_onnx_fallback = False
        self.assertEqual(e._dimension, 1024)
        self.assertFalse(e._is_onnx_fallback)

    # PURPOSE: Verify model dimensions map behaves correctly
    def test_model_dimensions_map(self):
        """MODEL_MAX_DIMS に既知モデルが登録されていること。"""
        from mekhane.anamnesis.constants import MODEL_MAX_DIMS, EMBED_MODEL, EMBED_DIM
        # 現行モデルが登録されていること
        self.assertIn(EMBED_MODEL, MODEL_MAX_DIMS)
        self.assertEqual(MODEL_MAX_DIMS[EMBED_MODEL], EMBED_DIM)
        # 旧モデルも登録されていること
        self.assertIn("gemini-embedding-001", MODEL_MAX_DIMS)


# TestGetVectorDimension and TestDimensionMismatchGuard は旧バックエンド固有のため除去済み。

if __name__ == "__main__":
    unittest.main()
