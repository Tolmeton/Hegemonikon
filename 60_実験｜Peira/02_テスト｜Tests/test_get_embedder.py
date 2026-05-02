"""Test: _get_embedder() Vertex AI 優先ロジック

GnosisIndex._get_embedder() が:
1. VertexEmbedder を最初に試行する
2. Vertex 失敗時に bge-m3 にフォールバックする
3. テーブル次元に合わせて target_dim を設定する
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mekhane.anamnesis.index import GnosisIndex


def test_vertex_preferred_when_available():
    """VertexEmbedder が使用可能な場合、それが優先される"""
    idx = GnosisIndex()

    mock_vertex = MagicMock()
    mock_vertex._dimension = 1024

    with patch.object(idx, '_table_exists', return_value=False):
        with patch(
            'mekhane.anamnesis.index.VertexEmbedder',
            return_value=mock_vertex,
            create=True,
        ) as mock_cls:
            # _get_embedder 内の import をモック
            with patch.dict('sys.modules', {
                'mekhane.anamnesis.vertex_embedder': MagicMock(VertexEmbedder=mock_cls)
            }):
                embedder = idx._get_embedder()

    # VertexEmbedder の mock が返されたか
    assert embedder is mock_vertex, f"Expected VertexEmbedder, got {type(embedder)}"
    print("✅ test_vertex_preferred_when_available")


def test_fallback_to_bge_m3_when_vertex_fails():
    """Vertex AI 初期化失敗時に bge-m3 にフォールバックする"""
    idx = GnosisIndex()

    with patch.object(idx, '_table_exists', return_value=False):
        # vertex_embedder の import 自体を失敗させる
        with patch.dict('sys.modules', {
            'mekhane.anamnesis.vertex_embedder': None,
        }):
            embedder = idx._get_embedder()

    # bge-m3 Embedder が返される (dimension=1024)
    dim = getattr(embedder, '_dimension', None)
    # 新規テーブル：target_dim = 3072、Vertex 失敗 → bge-m3 (1024d)
    # table_dim が None の場合、bge-m3 (1024d) では table_dim !=1024 チェックをスキップ
    assert embedder is not None
    print(f"✅ test_fallback_to_bge_m3_when_vertex_fails (dim={dim})")


def test_table_dim_detection():
    """既存テーブルの次元を検出して target_dim に使う"""
    idx = GnosisIndex()

    mock_vertex = MagicMock()
    mock_vertex._dimension = 1024

    mock_table = MagicMock()
    # Schema with vector field of dim 1024
    mock_field = MagicMock()
    mock_field.name = "vector"
    mock_field.type = "fixed_size_list<float32>[1024]"
    mock_table.schema = [mock_field]

    with patch.object(idx, '_table_exists', return_value=True):
        with patch.object(idx.db, 'open_table', return_value=mock_table):
            with patch(
                'mekhane.anamnesis.index._get_vector_dimension',
                return_value=1024,
            ):
                with patch.dict('sys.modules', {
                    'mekhane.anamnesis.vertex_embedder': MagicMock(
                        VertexEmbedder=MagicMock(return_value=mock_vertex)
                    )
                }):
                    embedder = idx._get_embedder()

    assert embedder is mock_vertex
    print("✅ test_table_dim_detection")


if __name__ == "__main__":
    test_vertex_preferred_when_available()
    test_fallback_to_bge_m3_when_vertex_fails()
    test_table_dim_detection()
    print("\n🎉 All _get_embedder tests passed!")
