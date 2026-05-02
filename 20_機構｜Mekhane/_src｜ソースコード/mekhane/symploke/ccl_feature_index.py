from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/モジュール] <- 20_機構｜Mekhane/symploke → CCL 特徴量インデックス
"""CCL 49d 特徴量による Code→Code 構造検索インデックス。

U⊣N 随伴の N の実装 — 名前を忘却した構造空間での直接近傍探索。
既存の text/structure 検索 (NL→Code) とは直交する。

テキスト embedding (3072d) は CCL テキストを言語空間に射影するが、
49d 特徴量ベクトルは構造そのもの (トークン分布・ネスト深度・AST ノード型・型フロー)
10: を直接保持する。

Z-score 正規化:
    生の 49d ベクトルは dim[0] (mean=0.902) が支配的で、コサイン類似度が
    median=0.98 に潰れる。構築時に各次元の mean/std を計算し、検索時に
    Z-score 正規化してからコサイン類似度を計算する。

使用法:
    from mekhane.symploke.ccl_feature_index import CCLFeatureIndex

    idx = CCLFeatureIndex()
    idx.load("/path/to/code_ccl_features.pkl")
    results = idx.find_similar_to("code_ingest.py", "python_to_ccl", k=10)
"""

# PURPOSE: CCL 49d 特徴量による構造検索インデックス


import ast
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np


# PURPOSE: 構造類似検索の結果
@dataclass
class SimilarResult:
    """Code→Code 構造検索の結果。"""

    score: float  # コサイン類似度 ∈ [-1.0, 1.0] (通常 0〜1)
    function_name: str
    file_path: str
    line_start: int
    ccl_expr: str  # CCL 式
    metadata: dict


# PURPOSE: 49d 特徴量インデックス
class CCLFeatureIndex:
    """CCL 49d 特徴量の直接コサイン検索インデックス。

    ccl_features(29d) + ccl_structural_counts(12d) + ccl_type_features(8d) = 49d で
    コード間の構造的類似度を直接計算する。

    NL→Code (text/structure) とは独立。
    Code→Code の構造検索を提供する。
    """

    DIMENSION = 49  # ccl_features(29d) + ccl_structural_counts(12d) + ccl_type_features(8d)

    def __init__(self) -> None:
        self._vectors: list[np.ndarray] = []
        self._metadata: list[dict] = []
        self._loaded = False
        # Z-score 正規化パラメータ (構築時に計算)
        self._mean: Optional[np.ndarray] = None
        self._std: Optional[np.ndarray] = None
        # 正規化済みベクトル行列 (検索時のキャッシュ)
        self._matrix_z: Optional[np.ndarray] = None

    @property
    def count(self) -> int:
        """インデックス内のベクトル数。"""
        return len(self._vectors)

    # ================================================================
    # Z-score 正規化
    # ================================================================

    # PURPOSE: 構築時に全ベクトルから正規化統計を計算
    def _compute_normalization(self) -> None:
        """全ベクトルから Z-score 正規化パラメータを計算する。

        各次元の mean/std を求め、std=0 の死次元は自動除外される。
        正規化済みベクトル行列 (_matrix_z) も事前計算する。
        """
        if not self._vectors:
            return

        raw = np.vstack(self._vectors)  # (N, 49)
        self._mean = np.mean(raw, axis=0)  # (49,)
        self._std = np.std(raw, axis=0)    # (49,)
        # std=0 の次元はゼロ除算回避 (正規化後もゼロのまま)
        self._std = np.where(self._std > 1e-10, self._std, 1.0)

        # 正規化済み行列を事前計算
        self._matrix_z = (raw - self._mean) / self._std  # (N, 49)
        # L2 正規化 (コサイン類似度用)
        norms = np.linalg.norm(self._matrix_z, axis=1, keepdims=True)
        norms = np.where(norms > 0, norms, 1.0)
        self._matrix_z = self._matrix_z / norms

    # PURPOSE: クエリベクトルを Z-score + L2 正規化
    def _normalize_query(self, query_features: list[float]) -> np.ndarray:
        """クエリベクトルを構築時の統計で Z-score 正規化する。"""
        query = np.array(query_features, dtype=np.float32)
        if self._mean is not None and self._std is not None:
            query = (query - self._mean) / self._std
        norm = np.linalg.norm(query)
        if norm > 0:
            query = query / norm
        return query

    # ================================================================
    # 構築
    # ================================================================

    # PURPOSE: code.pkl から ccl_expr を使って 49d インデックスを再構築
    def build_from_code_pkl(self, code_pkl_path: str) -> int:
        """既存の code.pkl から ccl_expr を使って 49d インデックスを構築する。

        code.pkl の各 Document の metadata["ccl_expr"] からリアルタイムに
        ccl_feature_vector を再計算する。metadata に保存された旧 ccl_features
        は次元数が変わっている可能性があるため依存しない。

        Args:
            code_pkl_path: code.pkl のパス

        Returns:
            構築されたエントリ数
        """
        from mekhane.symploke.adapters.vector_store import VectorStore
        from mekhane.symploke.code_ingest import (
            ccl_features, ccl_structural_counts, ccl_type_features,
        )

        store = VectorStore()
        store.load(code_pkl_path)

        self._vectors = []
        self._metadata = []
        skipped = 0

        for idx in range(store.count()):
            meta = store.get_metadata(idx)
            if meta is None:
                continue

            # ccl_expr からリアルタイムに 49d を再計算
            ccl_expr = meta.get("ccl_expr", "")
            if not ccl_expr:
                skipped += 1
                continue

            cf = ccl_features(ccl_expr)
            sc = ccl_structural_counts(ccl_expr)
            tf = ccl_type_features(ccl_expr)
            features = cf + [float(x) for x in sc] + tf

            if len(features) != self.DIMENSION:
                skipped += 1
                continue

            vec = np.array(features, dtype=np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm

            self._vectors.append(vec)
            self._metadata.append({
                "function_name": meta.get("function_name", ""),
                "file_path": meta.get("file_path", ""),
                "line_start": meta.get("line_start", 0),
                "ccl_expr": meta.get("ccl_expr", ""),
                "code_type": meta.get("code_type", ""),
                "ki_name": meta.get("ki_name", ""),
                "summary": meta.get("summary", ""),
            })

        if skipped:
            print(f"  ⚠️ {skipped} entries skipped (no ccl_expr)")
        self._loaded = True
        self._compute_normalization()
        return len(self._vectors)

    # PURPOSE: Document リストから直接構築 (インジェスト時用)
    def build_from_documents(self, docs: list) -> int:
        """Document リストから 49d インデックスを構築する。

        code_ingest.py のインジェストパイプラインから呼ばれる。

        Args:
            docs: Document リスト (metadata に ccl_features を含む)

        Returns:
            構築されたエントリ数
        """
        self._vectors = []
        self._metadata = []

        for doc in docs:
            features = doc.metadata.get("ccl_features")
            if features is None or len(features) != self.DIMENSION:
                continue

            vec = np.array(features, dtype=np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm

            self._vectors.append(vec)
            self._metadata.append({
                "function_name": doc.metadata.get("function_name", ""),
                "file_path": doc.metadata.get("file_path", ""),
                "line_start": doc.metadata.get("line_start", 0),
                "ccl_expr": doc.metadata.get("ccl_expr", ""),
                "code_type": doc.metadata.get("code_type", ""),
                "ki_name": doc.metadata.get("ki_name", ""),
                "summary": doc.metadata.get("summary", ""),
            })

        self._loaded = True
        self._compute_normalization()
        return len(self._vectors)

    # ================================================================
    # 検索
    # ================================================================

    # PURPOSE: 49d コサイン類似度で近傍検索
    def search_similar(
        self,
        query_features: list[float],
        k: int = 10,
        exclude_self: bool = False,
        self_file: str = "",
        self_func: str = "",
    ) -> list[SimilarResult]:
        """49d 特徴量ベクトルで構造的に類似した関数を検索する。

        Args:
            query_features: 49d の特徴量ベクトル
            k: 返す件数
            exclude_self: 自分自身を除外するか
            self_file: 除外対象のファイルパス
            self_func: 除外対象の関数名

        Returns:
            SimilarResult のリスト (score 降順)
        """
        if not self._loaded or not self._vectors:
            return []

        # クエリを Z-score + L2 正規化
        query = self._normalize_query(query_features)

        # 一括コサイン類似度 (Z-score 正規化済み行列を使用)
        if self._matrix_z is not None:
            scores = self._matrix_z @ query  # (N,)
        else:
            # フォールバック (正規化統計なし)
            matrix = np.vstack(self._vectors)
            scores = matrix @ query

        # ソート
        sorted_indices = np.argsort(scores)[::-1]

        results = []
        for idx in sorted_indices:
            if len(results) >= k:
                break

            meta = self._metadata[idx]

            # 自己除外
            if exclude_self:
                if (meta["file_path"] == self_file and
                        meta["function_name"] == self_func):
                    continue

            results.append(SimilarResult(
                score=float(scores[idx]),
                function_name=meta["function_name"],
                file_path=meta["file_path"],
                line_start=meta["line_start"],
                ccl_expr=meta["ccl_expr"],
                metadata=meta,
            ))

        return results

    # PURPOSE: ファイルパス + 関数名から構造類似検索
    def find_similar_to(
        self,
        file_path: str,
        func_name: str,
        k: int = 10,
    ) -> list[SimilarResult]:
        """指定した関数と構造的に類似した関数を検索する。

        ファイルを AST 解析し、対象関数の ccl_feature_vector を計算して検索。

        Args:
            file_path: Python ファイルのパス
            func_name: 関数名
            k: 返す件数

        Returns:
            SimilarResult のリスト (score 降順、自分自身は除外)
        """
        # ファイルから対象関数の AST ノードを取得
        target_path = Path(file_path)
        if not target_path.exists():
            return []

        try:
            source = target_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:  # noqa: BLE001
            return []

        # 対象関数を探す
        target_node = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == func_name:
                    target_node = node
                    break

        if target_node is None:
            return []

        # 特徴量を計算
        from mekhane.symploke.code_ingest import ccl_feature_vector
        features = ccl_feature_vector(target_node)

        return self.search_similar(
            query_features=features,
            k=k,
            exclude_self=True,
            self_file=str(target_path),
            self_func=func_name,
        )

    # ================================================================
    # 永続化
    # ================================================================

    # PURPOSE: pkl に保存
    def save(self, path: str) -> None:
        """49d インデックスを pkl に保存する。"""
        data = {
            "dimension": self.DIMENSION,
            "vectors": self._vectors,
            "metadata": self._metadata,
            # Z-score 正規化パラメータ
            "mean": self._mean,
            "std": self._std,
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)

    # PURPOSE: pkl から読込
    def load(self, path: str) -> None:
        """49d インデックスを pkl から読み込む。"""
        with open(path, "rb") as f:
            data = pickle.load(f)

        dim = data.get("dimension", 0)
        if dim != self.DIMENSION:
            raise ValueError(
                f"次元数不一致: 期待={self.DIMENSION}, 実際={dim}"
            )

        self._vectors = data["vectors"]
        self._metadata = data["metadata"]
        self._loaded = True

        # Z-score 正規化パラメータを復元 (v2 以降)
        self._mean = data.get("mean")
        self._std = data.get("std")

        if self._mean is not None and self._std is not None:
            # 正規化済み行列を事前計算
            raw = np.vstack(self._vectors)
            z = (raw - self._mean) / self._std
            norms = np.linalg.norm(z, axis=1, keepdims=True)
            norms = np.where(norms > 0, norms, 1.0)
            self._matrix_z = z / norms
        else:
            # v1 互換: 正規化統計がない場合は構築時に計算
            self._compute_normalization()
