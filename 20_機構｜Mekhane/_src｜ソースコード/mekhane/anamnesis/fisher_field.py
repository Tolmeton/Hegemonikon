from __future__ import annotations
"""Fisher Field — 場の Fisher 情報行列を構築する。

PROOF: F2 自動分類の基盤モジュール。
PhantasiaField (embedding 場) から Fisher 情報行列を構築し、
固有分解で分類軸を演繹的に導出する。

理論的基盤:
  - axiom_hierarchy.md §Euporía 感度理論:
    7座標 = Fisher 情報行列の固有ベクトル (sloppy universality)
  - linkage_hyphe.md §3.3:
    ρ_MB(x) = 1 - I(I;E|B) / (I(I;E) + ε) — MB 密度
  - Possati (2025): KSG estimator による MB 密度の近似

設計:
  1. 場から全 embedding を取得 (3072次元)
  2. k-NN で各点の ρ_MB 勾配を推定
  3. 勾配の外積和 → Fisher 情報行列 G (3072×3072)
  4. 上位固有値のみ計算 (scipy.sparse.linalg.eigsh)
  5. Sloppy spectrum の gap 検出 → 有効軸数 k の自然決定

依存:
  - mekhane.anamnesis.phantasia_field.PhantasiaField
  - numpy, scipy
"""


import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

log = logging.getLogger(__name__)


@dataclass
class FieldAxes:
    """場の固有分解結果を保持する。

    属性:
        eigenvectors: 固有ベクトル (3072 × k の配列)
        eigenvalues: 固有値 (k 個の配列、降順)
        k: 有効軸数 (sloppy gap で自動決定)
        gap_index: 最大 gap の位置
        sloppy_ratio: log₁₀(λ_max / λ_min)
        computed_at: 計算日時 (ISO8601)
        total_points: 計算に使ったデータ点数
    """

    eigenvectors: np.ndarray  # (3072, k)
    eigenvalues: np.ndarray  # (k,)
    k: int
    gap_index: int = 0
    sloppy_ratio: float = 0.0
    computed_at: str = ""
    total_points: int = 0


class FisherField:
    """場の Fisher 情報行列を構築・固有分解するエンジン。

    Usage:
        fisher = FisherField(hyphe_field)
        axes = fisher.compute_axes(k_neighbors=10, k_max_axes=50)
        # axes.eigenvectors: (3072, k) — k 個の分類軸
        # axes.eigenvalues: (k,) — 各軸の重要度
    """

    # PURPOSE: PhantasiaField との結合
    def __init__(self, hyphe_field: Optional["PhantasiaField"] = None):
        """FisherField を初期化する。

        Args:
            hyphe_field: embedding 場。None の場合はデフォルト構成で生成。
        """
        self._field = hyphe_field

    # PURPOSE: PhantasiaField の遅延初期化
    def _get_field(self) -> "PhantasiaField":
        """PhantasiaField を遅延初期化して返す。"""
        if self._field is None:
            from mekhane.anamnesis.phantasia_field import PhantasiaField
            self._field = PhantasiaField()
        return self._field

    # PURPOSE: 場から全 embedding を取得
    def get_all_embeddings(
        self,
        source_filter: Optional[str] = None,
        session_filter: Optional[str] = None,
    ) -> tuple[np.ndarray, list[dict]]:
        """場から全 embedding をメタデータ付きで取得する。

        GnosisIndex の filter_to_pandas() で全レコードを取得。

        Args:
            source_filter: ソースでフィルタ (例: "session")
            session_filter: セッション ID でフィルタ

        Returns:
            (embeddings, metadata) のタプル
            - embeddings: (N, 3072) の numpy 配列
            - metadata: 各チャンクのメタデータのリスト
        """
        field = self._get_field()
        index = field._get_index()

        # Backend から pandas dataframe を直接取得
        try:
            df = index.filter_to_pandas()
        except Exception as e:  # noqa: BLE001
            log.error(f"[FisherField] 全 embedding 取得失敗: {e}")
            return np.array([]), []

        # フィルタ適用
        if source_filter and "source" in df.columns:
            df = df[df["source"] == source_filter]
        if session_filter and "session_id" in df.columns:
            df = df[df["session_id"] == session_filter]

        if df.empty:
            log.warning("[FisherField] embedding が空")
            return np.array([]), []

        # embedding 列を抽出 (ベクトル列名は "vector")
        vec_col = "vector"
        if vec_col not in df.columns:
            # 別名を試行
            vec_candidates = [c for c in df.columns if "vec" in c.lower() or "embed" in c.lower()]
            if vec_candidates:
                vec_col = vec_candidates[0]
            else:
                log.error(f"[FisherField] ベクトル列が見つからない: {list(df.columns)}")
                return np.array([]), []

        embeddings = np.array(df[vec_col].tolist(), dtype=np.float32)
        metadata = df.drop(columns=[vec_col]).to_dict("records")

        log.info(f"[FisherField] {len(embeddings)} 点の embedding を取得 ({embeddings.shape[1]}次元)")
        return embeddings, metadata

    # PURPOSE: フォールバック用の embedding 取得
    def _fallback_get_embeddings(
        self, index, source_filter: Optional[str] = None,
    ) -> tuple[np.ndarray, list[dict]]:
        """テーブル直接アクセスが失敗した場合のフォールバック。"""
        log.warning("[FisherField] フォールバック: 空ベクトル検索で全レコード取得")
        try:
            # ゼロベクトルで全件取得 (距離順)
            results = index.search(
                query=" ",  # 空文字列は拒否されるためスペース
                limit=100000,
                search_type="vector",
            )
            if not results:
                return np.array([]), []

            embeddings = np.array(
                [r["vector"] for r in results if "vector" in r],
                dtype=np.float32,
            )
            metadata = [
                {k: v for k, v in r.items() if k != "vector"}
                for r in results
            ]
            return embeddings, metadata
        except Exception as e:  # noqa: BLE001
            log.error(f"[FisherField] フォールバックも失敗: {e}")
            return np.array([]), []

    # PURPOSE: セッション別の embedding centroid を計算
    def get_session_centroids(
        self,
        source_filter: Optional[str] = None,
    ) -> dict[str, np.ndarray]:
        """セッション別の centroid (重心) を計算する。

        Returns:
            {session_id: centroid_vector (3072,)} の辞書
        """
        embeddings, metadata = self.get_all_embeddings(source_filter=source_filter)
        if len(embeddings) == 0:
            return {}

        # セッション ID ごとにグループ化
        session_groups = defaultdict(list)
        for i, m in enumerate(metadata):
            sid = m.get("session_id") or m.get("session")
            if not sid:
                # url または primary_key にファイルパスが入る事が多い
                url = m.get("url", "")
                if url:
                    sid = Path(url).stem
                else:
                    sid = m.get("primary_key", "unknown")
                    # primary_key が chunk_1 のようになっている場合は削る
                    if ":" in sid:
                        sid = sid.split(":")[0]

            session_groups[sid].append(i)

        # 各セッションの centroid を計算
        centroids = {}
        for sid, indices in session_groups.items():
            session_embeddings = embeddings[indices]
            centroids[sid] = session_embeddings.mean(axis=0)

        log.info(f"[FisherField] {len(centroids)} セッションの centroid を計算")
        return centroids

    # PURPOSE: ρ_MB を k-NN で計算
    @staticmethod
    def compute_rho_knn(
        embeddings: np.ndarray,
        k: int = 10,
    ) -> np.ndarray:
        """k-NN 密度推定で各点の ρ_MB を計算する。

        ρ_MB(x) ≈ k / (V_d · r_k(x)^d)
        ここで r_k(x) は x の k-近傍距離、V_d は d 次元超球体積。

        高次元では r_k の比率が重要 (絶対値は発散する)。
        正規化: ρ(x) = k / (r_k(x)^d) を [0, 1] にスケール。

        Args:
            embeddings: (N, d) の embedding 配列
            k: 近傍数

        Returns:
            (N,) の密度値配列 (0 = 低密度, 1 = 高密度)
        """
        n, d = embeddings.shape
        if n <= k + 1:
            log.warning(f"[FisherField] データ点 {n} <= k+1={k+1}: 一様密度を返す")
            return np.full(n, 0.5, dtype=np.float32)

        r_k = np.zeros(n, dtype=np.float32)
        batch_size = 1000
        norm_emb = np.sum(embeddings**2, axis=1)
        
        for i in range(0, n, batch_size):
            end = min(i + batch_size, n)
            A = embeddings[i:end]
            
            # ||a - b||^2 = ||a||^2 + ||b||^2 - 2<a, b>
            dist_sq = A @ embeddings.T
            dist_sq *= -2
            dist_sq += norm_emb
            dist_sq += np.sum(A**2, axis=1, keepdims=True)
            dist_sq = np.maximum(dist_sq, 0.0)
            
            # argpartition で小さい方から k+1 個を取得
            idx = np.argpartition(dist_sq, k+1, axis=1)[:, :k+1]
            
            # 最も遠い (k+1番目) 距離を取得
            top_dists = np.take_along_axis(dist_sq, idx, axis=1)
            kth_dist_sq = np.max(top_dists, axis=1)
            r_k[i:end] = np.sqrt(kth_dist_sq)

        # ρ ∝ 1/r_k^d → 高次元では log 空間で扱う
        # 正規化のため rank-based
        log_rk = np.log(r_k + 1e-10)
        # 小さい r_k = 高密度 → 反転
        rho = 1.0 - (np.argsort(np.argsort(log_rk)) / (n - 1))

        return rho.astype(np.float32)

    # PURPOSE: Fisher 情報行列を構築 (核心アルゴリズム)
    @staticmethod
    def compute_fisher_matrix(
        embeddings: np.ndarray,
        k: int = 10,
        rho: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """場の Fisher 情報行列を構築する。

        G_ij = (1/N) Σ_x (∂ρ/∂x_i)(∂ρ/∂x_j)

        ∂ρ/∂x_i は k-NN 近傍の有限差分で近似:
          ∂ρ/∂x_i ≈ Σ_{j∈N(x)} (ρ_j - ρ_x)(x_j - x)_i / ||x_j - x||²

        3072次元で直接計算。ANN で近傍探索を高速化。

        Args:
            embeddings: (N, d) の embedding 配列
            k: 近傍数
            rho: 事前計算された密度値 (None → 内部で計算)

        Returns:
            (d, d) の Fisher 情報行列
        """
        n, d = embeddings.shape
        log.info(f"[FisherField] Fisher 行列構築開始: {n} 点 × {d} 次元, k={k}")
        t0 = time.time()

        if rho is None:
            rho = FisherField.compute_rho_knn(embeddings, k=k)

        # メモリ効率: G をバッチで逐次更新
        G = np.zeros((d, d), dtype=np.float64)
        batch_size = 1000
        norm_emb = np.sum(embeddings**2, axis=1)
        
        for i in range(0, n, batch_size):
            end = min(i + batch_size, n)
            A = embeddings[i:end]
            
            dist_sq = A @ embeddings.T
            dist_sq *= -2
            dist_sq += norm_emb
            dist_sq += np.sum(A**2, axis=1, keepdims=True)
            dist_sq = np.maximum(dist_sq, 0.0)
            
            idx = np.argpartition(dist_sq, k+1, axis=1)[:, :k+1]
            
            batch_grads = []
            
            for j in range(end - i):
                global_i = i + j
                neighbors = idx[j]
                
                # 自分自身を除外
                neighbors = neighbors[neighbors != global_i]
                if len(neighbors) > k:
                    neighbors = neighbors[:k]
                
                if len(neighbors) == 0:
                    continue
                    
                rho_i = rho[global_i]
                rho_j = rho[neighbors]
                
                delta = embeddings[neighbors].astype(np.float64) - embeddings[global_i].astype(np.float64)
                
                n_dist_sq = dist_sq[j, neighbors]
                n_dist_sq = np.maximum(n_dist_sq, 1e-10)
                
                weights = (rho_j - rho_i) / n_dist_sq
                
                grad_rho = np.sum(delta * weights[:, np.newaxis], axis=0)
                grad_rho /= k
                batch_grads.append(grad_rho)
                
            if batch_grads:
                bg = np.array(batch_grads, dtype=np.float32)  # (batch_size, D)
                G += bg.T @ bg

            # 進捗ログ (1000点ごと)
            if (i + 1) % 1000 == 0:
                elapsed = time.time() - t0
                log.info(
                    f"[FisherField] Fisher 行列構築: {i+1}/{n} "
                    f"({elapsed:.1f}s, {(i+1)/elapsed:.0f} 点/秒)"
                )

        G /= n

        elapsed = time.time() - t0
        log.info(f"[FisherField] Fisher 行列構築完了: {elapsed:.1f}s")

        return G

    # PURPOSE: 固有分解 + sloppy gap 検出
    @staticmethod
    def eigen_decompose(
        G: np.ndarray,
        k_max: int = 50,
    ) -> FieldAxes:
        """Fisher 行列を固有分解し、sloppy gap で有効軸数を決定する。

        scipy.sparse.linalg.eigsh で上位 k_max 個のみ計算。
        log₁₀(λ_i) - log₁₀(λ_{i+1}) の最大 gap で k を自然決定。

        Args:
            G: (d, d) の Fisher 情報行列 (対称)
            k_max: 計算する最大固有値数

        Returns:
            FieldAxes — 固有ベクトル・固有値・有効軸数
        """
        from scipy.sparse.linalg import eigsh
        from datetime import datetime, timezone

        d = G.shape[0]
        k_max = min(k_max, d - 1)

        log.info(f"[FisherField] 固有分解開始: {d}×{d} 行列, 上位 {k_max} 個")
        t0 = time.time()

        eigenvalues, eigenvectors = eigsh(G, k=k_max, which="LM")

        # 降順にソート
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # 負の固有値を除外 (数値誤差)
        positive_mask = eigenvalues > 1e-12
        eigenvalues = eigenvalues[positive_mask]
        eigenvectors = eigenvectors[:, positive_mask]

        if len(eigenvalues) < 2:
            log.warning("[FisherField] 有効な固有値が 2 未満")
            return FieldAxes(
                eigenvectors=eigenvectors,
                eigenvalues=eigenvalues,
                k=len(eigenvalues),
                computed_at=datetime.now(timezone.utc).isoformat(),
            )

        # Sloppy spectrum gap 検出
        log_λ = np.log10(eigenvalues + 1e-20)
        gaps = np.abs(np.diff(log_λ))
        gap_index = int(np.argmax(gaps))
        k_axes = gap_index + 1  # gap の前までが有意な軸

        # k が 1 以下は不自然 → 最低 2 軸
        k_axes = max(k_axes, 2)

        sloppy_ratio = float(log_λ[0] - log_λ[-1])

        elapsed = time.time() - t0
        log.info(
            f"[FisherField] 固有分解完了: {elapsed:.1f}s, "
            f"k={k_axes} 軸 (gap@{gap_index}), "
            f"sloppy_ratio={sloppy_ratio:.2f}"
        )

        # スペクトルログ (上位 10 軸)
        for i in range(min(10, len(eigenvalues))):
            log.info(
                f"  λ_{i}: {eigenvalues[i]:.6e} "
                f"(log₁₀={log_λ[i]:.2f})"
                f"{' ← gap' if i == gap_index else ''}"
            )

        return FieldAxes(
            eigenvectors=eigenvectors[:, :k_axes],
            eigenvalues=eigenvalues[:k_axes],
            k=k_axes,
            gap_index=gap_index,
            sloppy_ratio=sloppy_ratio,
            computed_at=datetime.now(timezone.utc).isoformat(),
            total_points=G.shape[0],
        )

    # PURPOSE: 場の固有軸を計算する統合メソッド
    def compute_axes(
        self,
        k_neighbors: int = 10,
        k_max_axes: int = 50,
        source_filter: Optional[str] = None,
        use_centroids: bool = False,
    ) -> FieldAxes:
        """場から分類軸を演繹的に導出する。

        溶解済みの embedding から Fisher 情報行列を構築し固有分解する。
        使用モード:
          - use_centroids=False: 全チャンクの embedding を使用 (高精度、重い)
          - use_centroids=True: セッション centroid のみ使用 (高速、粗い)

        Args:
            k_neighbors: k-NN の近傍数
            k_max_axes: 計算する最大軸数
            source_filter: ソースでフィルタ
            use_centroids: セッション centroid を使うか

        Returns:
            FieldAxes — 固有ベクトル・固有値・有効軸数
        """
        if use_centroids:
            centroids = self.get_session_centroids(source_filter=source_filter)
            if not centroids:
                raise ValueError("セッション centroid がありません")
            embeddings = np.array(list(centroids.values()), dtype=np.float32)
            log.info(f"[FisherField] centroid モード: {len(embeddings)} セッション")
        else:
            embeddings, _ = self.get_all_embeddings(source_filter=source_filter)
            if len(embeddings) == 0:
                raise ValueError("embedding がありません")

        # k_neighbors をデータサイズに適応
        k = min(k_neighbors, len(embeddings) - 1)
        if k < 2:
            raise ValueError(f"データ点が少なすぎます: {len(embeddings)} (最低 3 点必要)")

        # 計算コスト爆発を防ぐため最大 5000 点にサンプリング
        max_points = 5000
        if len(embeddings) > max_points:
            log.info(f"[FisherField] データ点が多すぎます ({len(embeddings)} > {max_points})。ランダムサンプリングします。")
            np.random.seed(42)
            indices = np.random.choice(len(embeddings), max_points, replace=False)
            sampled_embeddings = embeddings[indices]
        else:
            sampled_embeddings = embeddings

        # Fisher 行列構築
        G = self.compute_fisher_matrix(sampled_embeddings, k=k)

        # 固有分解
        k_max = min(k_max_axes, len(embeddings) - 1)
        axes = self.eigen_decompose(G, k_max=k_max)
        axes.total_points = len(embeddings)

        return axes

    # PURPOSE: セッションを固有軸に射影
    def project_session(
        self,
        session_id: str,
        axes: FieldAxes,
    ) -> Optional[np.ndarray]:
        """セッションの centroid を固有軸空間に射影する。

        Args:
            session_id: セッション ID
            axes: compute_axes() で得た固有軸

        Returns:
            (k,) の座標ベクトル。セッションが見つからなければ None。
        """
        centroids = self.get_session_centroids()
        if session_id not in centroids:
            log.warning(f"[FisherField] セッション {session_id} が見つかりません")
            return None

        centroid = centroids[session_id]
        # 固有軸への射影: centroid (3072,) @ eigenvectors (3072, k) → (k,)
        coords = centroid @ axes.eigenvectors
        return coords

    # PURPOSE: 全セッションを一括射影
    def project_all_sessions(
        self,
        axes: FieldAxes,
        source_filter: Optional[str] = None,
    ) -> dict[str, np.ndarray]:
        """全セッションの centroid を固有軸空間に一括射影する。

        Returns:
            {session_id: coords (k,)} の辞書
        """
        centroids = self.get_session_centroids(source_filter=source_filter)
        projected = {}

        for sid, centroid in centroids.items():
            coords = centroid @ axes.eigenvectors
            projected[sid] = coords

        log.info(f"[FisherField] {len(projected)} セッションを {axes.k} 次元に射影")
        return projected
