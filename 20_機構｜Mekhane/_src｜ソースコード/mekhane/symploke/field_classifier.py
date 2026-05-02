from __future__ import annotations
"""Field Classifier — 場の固有軸空間でセッションを分類する。

PROOF: F2 自動分類のメインモジュール。
FisherField で導出された固有軸にセッションを射影し、
HDBSCAN でクラスタリング → タグを演繹的に導出する。

設計原則:
  - タグは LLM 生成ではなく座標値から決定論的に導出
  - クラスタ数は HDBSCAN が自動決定 (min_cluster_size のみ指定)
  - 冷起動時は Boulēsis PJ ドキュメントの centroid を seed として使用

依存:
  - mekhane.anamnesis.fisher_field (FisherField, FieldAxes)
  - hdbscan or sklearn.cluster.HDBSCAN
  - numpy
"""


import logging
import time
from dataclasses import dataclass, field as dataclass_field
from typing import Optional

import numpy as np

log = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """セッション分類結果。

    属性:
        session_id: セッション ID
        coords: 固有軸空間の座標値 (k 次元)
        cluster_id: HDBSCAN クラスタ ID (-1 = ノイズ)
        cluster_label: クラスタラベル (例: "PJ:hegemonikon")
        tags: 演繹されたタグのリスト
        confidence: 分類の確信度 (0-1)
    """

    session_id: str
    coords: np.ndarray
    cluster_id: int = -1
    cluster_label: str = ""
    tags: list[str] = dataclass_field(default_factory=list)
    confidence: float = 0.0


@dataclass
class ClusterInfo:
    """クラスタの情報。

    属性:
        cluster_id: クラスタ ID
        label: ラベル名
        centroid: クラスタ centroid (k 次元)
        member_count: メンバー数
        session_ids: 所属セッション ID のリスト
    """

    cluster_id: int
    label: str = ""
    centroid: Optional[np.ndarray] = None
    member_count: int = 0
    session_ids: list[str] = dataclass_field(default_factory=list)


class FieldClassifier:
    """場の固有軸空間でセッションを分類するエンジン。

    Usage:
        from mekhane.anamnesis.fisher_field import FisherField

        fisher = FisherField()
        axes = fisher.compute_axes()

        classifier = FieldClassifier(fisher)
        results = classifier.classify_all(axes)
        for r in results:
            print(f"{r.session_id}: {r.tags}")
    """

    # PURPOSE: 初期化
    def __init__(
        self,
        fisher_field: Optional["FisherField"] = None,
        min_cluster_size: int = 3,
        pj_seeds: Optional[dict[str, np.ndarray]] = None,
    ):
        """FieldClassifier を初期化する。

        Args:
            fisher_field: FisherField インスタンス (None → 内部で生成)
            min_cluster_size: HDBSCAN の最小クラスタサイズ
            pj_seeds: 冷起動用 PJ seed {name: centroid_embedding}
        """
        self._fisher = fisher_field
        self._min_cluster_size = min_cluster_size
        self._pj_seeds = pj_seeds or {}

    # PURPOSE: FisherField の遅延初期化
    def _get_fisher(self) -> "FisherField":
        """FisherField を遅延初期化して返す。"""
        if self._fisher is None:
            from mekhane.anamnesis.fisher_field import FisherField
            self._fisher = FisherField()
        return self._fisher

    # PURPOSE: HDBSCAN クラスタリング
    def cluster(
        self,
        projected: dict[str, np.ndarray],
        min_cluster_size: Optional[int] = None,
    ) -> tuple[dict[str, int], list[ClusterInfo]]:
        """固有軸空間の座標でクラスタリングする。

        Args:
            projected: {session_id: coords (k,)} の辞書
            min_cluster_size: HDBSCAN の最小クラスタサイズ

        Returns:
            (assignments, clusters) のタプル
            - assignments: {session_id: cluster_id}
            - clusters: ClusterInfo のリスト
        """
        if not projected:
            return {}, []

        min_cs = min_cluster_size or self._min_cluster_size
        session_ids = list(projected.keys())
        coords = np.array([projected[sid] for sid in session_ids])

        n = len(session_ids)
        log.info(f"[FieldClassifier] HDBSCAN 開始: {n} セッション, k={coords.shape[1]} 次元")

        # データが少ない場合のフォールバック
        if n < min_cs:
            log.warning(
                f"[FieldClassifier] データ点 ({n}) < min_cluster_size ({min_cs}): "
                "全て1クラスタに割り当て"
            )
            assignments = {sid: 0 for sid in session_ids}
            centroid = coords.mean(axis=0)
            clusters = [ClusterInfo(
                cluster_id=0,
                centroid=centroid,
                member_count=n,
                session_ids=session_ids,
            )]
            return assignments, clusters

        # HDBSCAN
        try:
            from sklearn.cluster import HDBSCAN as SkHDBSCAN
            clusterer = SkHDBSCAN(
                min_cluster_size=min_cs,
                min_samples=max(1, min_cs // 2),
                metric="euclidean",
            )
            labels = clusterer.fit_predict(coords)
        except ImportError:
            try:
                import hdbscan
                clusterer = hdbscan.HDBSCAN(
                    min_cluster_size=min_cs,
                    min_samples=max(1, min_cs // 2),
                    metric="euclidean",
                )
                labels = clusterer.fit_predict(coords)
            except ImportError:
                log.warning("[FieldClassifier] HDBSCAN 未インストール: k-means にフォールバック")
                return self._fallback_kmeans(session_ids, coords)

        # 結果を整理
        assignments = {sid: int(label) for sid, label in zip(session_ids, labels)}
        unique_labels = set(labels)
        unique_labels.discard(-1)  # ノイズを除く

        clusters = []
        for cid in sorted(unique_labels):
            mask = labels == cid
            member_ids = [sid for sid, m in zip(session_ids, mask) if m]
            centroid = coords[mask].mean(axis=0)
            clusters.append(ClusterInfo(
                cluster_id=int(cid),
                centroid=centroid,
                member_count=int(mask.sum()),
                session_ids=member_ids,
            ))

        noise_count = int((labels == -1).sum())
        log.info(
            f"[FieldClassifier] HDBSCAN 完了: "
            f"{len(clusters)} クラスタ, {noise_count} ノイズ"
        )

        return assignments, clusters

    # PURPOSE: k-means フォールバック
    def _fallback_kmeans(
        self,
        session_ids: list[str],
        coords: np.ndarray,
    ) -> tuple[dict[str, int], list[ClusterInfo]]:
        """HDBSCAN が使えない場合の k-means フォールバック。"""
        from sklearn.cluster import KMeans

        # クラスタ数を概算 (√(n/2) のヒューリスティック)
        n = len(session_ids)
        k = max(2, min(12, int(np.sqrt(n / 2))))

        kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = kmeans.fit_predict(coords)

        assignments = {sid: int(label) for sid, label in zip(session_ids, labels)}
        clusters = []
        for cid in range(k):
            mask = labels == cid
            member_ids = [sid for sid, m in zip(session_ids, mask) if m]
            centroid = coords[mask].mean(axis=0) if mask.any() else np.zeros(coords.shape[1])
            clusters.append(ClusterInfo(
                cluster_id=cid,
                centroid=centroid,
                member_count=int(mask.sum()),
                session_ids=member_ids,
            ))

        return assignments, clusters

    # PURPOSE: クラスタに PJ ラベルを付与
    def label_clusters(
        self,
        clusters: list[ClusterInfo],
        axes: "FieldAxes",
    ) -> list[ClusterInfo]:
        """クラスタに PJ ラベルを付与する。

        手順:
          1. PJ seed がある場合、cosine 類似度でマッチング
          2. 類似度 > 0.7 → 既存 PJ 名を継承
          3. 類似度 < 0.7 → "Cluster_{id}" (新 PJ 候補)

        Args:
            clusters: クラスタ情報のリスト
            axes: FieldAxes (PJ seed の射影に使用)

        Returns:
            ラベル付与済みの ClusterInfo リスト
        """
        if not self._pj_seeds:
            # seed なし: 連番ラベル
            for c in clusters:
                c.label = f"Cluster_{c.cluster_id}"
            return clusters

        # PJ seed を固有軸空間に射影
        pj_projected = {}
        for name, seed_embedding in self._pj_seeds.items():
            pj_coords = seed_embedding @ axes.eigenvectors
            pj_projected[name] = pj_coords

        # 各クラスタの centroid と PJ seed の cosine 類似度
        for c in clusters:
            if c.centroid is None:
                c.label = f"Cluster_{c.cluster_id}"
                continue

            best_sim = -1.0
            best_name = ""

            for name, pj_coords in pj_projected.items():
                # cosine 類似度
                dot = np.dot(c.centroid, pj_coords)
                norm_a = np.linalg.norm(c.centroid)
                norm_b = np.linalg.norm(pj_coords)
                if norm_a < 1e-10 or norm_b < 1e-10:
                    continue
                sim = float(dot / (norm_a * norm_b))

                if sim > best_sim:
                    best_sim = sim
                    best_name = name

            if best_sim > 0.7:
                c.label = f"PJ:{best_name}"
            else:
                c.label = f"Cluster_{c.cluster_id}"

            log.debug(
                f"[FieldClassifier] クラスタ {c.cluster_id}: "
                f"label={c.label} (sim={best_sim:.3f})"
            )

        return clusters

    # PURPOSE: タグの演繹的導出
    @staticmethod
    def derive_tags(
        coords: np.ndarray,
        eigenvalues: np.ndarray,
        cluster_label: str,
    ) -> list[str]:
        """座標値からタグを決定論的に導出する。

        タグ生成規則:
          1. クラスタラベル → "PJ:{name}" or "Cluster_{id}"
          2. 各軸 i で |c_i| > 1σ の方向 → "Axis{i}:+" or "Axis{i}:-"
          3. 主軸 (λ最大) の座標値の符号 → "Primary:+" or "Primary:-"

        Args:
            coords: 固有軸空間の座標値 (k,)
            eigenvalues: 固有値 (k,)
            cluster_label: クラスタラベル

        Returns:
            タグのリスト
        """
        tags = []

        # 1. クラスタラベル
        if cluster_label:
            tags.append(cluster_label)

        # 2. 有意な軸方向のタグ
        if len(coords) > 0:
            # 座標値の標準偏差 (全セッション間の基準として1を使う仮置き)
            # 本来は全セッションの座標値の σ を使うべきだが、単独計算では不可
            for i, c in enumerate(coords):
                if abs(c) > 1.0:  # 暫定閾値 (後で σ に置換)
                    direction = "+" if c > 0 else "-"
                    tags.append(f"Axis{i}:{direction}")

        # 3. 主軸の方向
        if len(coords) > 0:
            primary_dir = "+" if coords[0] > 0 else "-"
            tags.append(f"Primary:{primary_dir}")

        return tags

    # PURPOSE: 全セッション一括分類
    def classify_all(
        self,
        axes: "FieldAxes",
        source_filter: Optional[str] = None,
    ) -> list[ClassificationResult]:
        """全セッションを分類する。

        手順:
          1. 全セッションを固有軸空間に射影
          2. HDBSCAN でクラスタリング
          3. PJ ラベル付与
          4. タグ演繹

        Args:
            axes: compute_axes() で得た固有軸
            source_filter: ソースフィルタ

        Returns:
            ClassificationResult のリスト
        """
        fisher = self._get_fisher()

        # 1. 射影
        projected = fisher.project_all_sessions(axes, source_filter=source_filter)
        if not projected:
            log.warning("[FieldClassifier] 射影するセッションがありません")
            return []

        # 2. クラスタリング
        assignments, clusters = self.cluster(projected)

        # 3. ラベル付与
        clusters = self.label_clusters(clusters, axes)

        # クラスタ ID → ラベルのマップ
        label_map = {c.cluster_id: c.label for c in clusters}

        # 4. 分類結果の構築
        results = []
        for sid, coords in projected.items():
            cid = assignments.get(sid, -1)
            label = label_map.get(cid, "Noise")

            tags = self.derive_tags(
                coords=coords,
                eigenvalues=axes.eigenvalues,
                cluster_label=label,
            )

            # 確信度: クラスタの centroid との距離 (近い = 高確信度)
            confidence = 0.0
            if cid >= 0:
                matching = [c for c in clusters if c.cluster_id == cid]
                if matching and matching[0].centroid is not None:
                    dist = np.linalg.norm(coords - matching[0].centroid)
                    # 距離を [0, 1] の確信度に変換 (指数減衰)
                    confidence = float(np.exp(-dist))

            results.append(ClassificationResult(
                session_id=sid,
                coords=coords,
                cluster_id=cid,
                cluster_label=label,
                tags=tags,
                confidence=confidence,
            ))

        log.info(
            f"[FieldClassifier] 分類完了: {len(results)} セッション, "
            f"{len(clusters)} クラスタ"
        )

        return results

    # PURPOSE: 単一セッションの分類
    def classify_session(
        self,
        session_id: str,
        axes: "FieldAxes",
        clusters: Optional[list[ClusterInfo]] = None,
    ) -> Optional[ClassificationResult]:
        """単一セッションを分類する。

        既存クラスタへの最近傍割り当て。
        新規セッション追加時の増分分類用。

        Args:
            session_id: セッション ID
            axes: 固有軸
            clusters: 既存クラスタ (None → 全体を再クラスタリング)

        Returns:
            ClassificationResult。セッションが見つからなければ None。
        """
        fisher = self._get_fisher()
        coords = fisher.project_session(session_id, axes)
        if coords is None:
            return None

        if clusters is None:
            # クラスタがなければ全体分類して自分だけ返す
            all_results = self.classify_all(axes)
            for r in all_results:
                if r.session_id == session_id:
                    return r
            return None

        # 最近傍クラスタに割り当て
        best_cluster = None
        best_dist = float("inf")

        for c in clusters:
            if c.centroid is None:
                continue
            dist = float(np.linalg.norm(coords - c.centroid))
            if dist < best_dist:
                best_dist = dist
                best_cluster = c

        if best_cluster is None:
            cluster_id = -1
            cluster_label = "Noise"
        else:
            cluster_id = best_cluster.cluster_id
            cluster_label = best_cluster.label

        tags = self.derive_tags(
            coords=coords,
            eigenvalues=axes.eigenvalues,
            cluster_label=cluster_label,
        )

        confidence = float(np.exp(-best_dist)) if best_dist < float("inf") else 0.0

        return ClassificationResult(
            session_id=session_id,
            coords=coords,
            cluster_id=cluster_id,
            cluster_label=cluster_label,
            tags=tags,
            confidence=confidence,
        )

    # ── F2 永続化 ──────────────────────────────────────────────

    # PURPOSE: 分類結果を GnosisIndex に書き戻す
    def persist_classifications(
        self,
        results: list[ClassificationResult],
        index: Optional[object] = None,
    ) -> int:
        """ClassificationResult リストを GnosisIndex に永続化する。

        classify_all() / classify_session() の出力を
        GnosisIndex.update_f2_fields() に渡す変換ブリッジ。

        Args:
            results: ClassificationResult のリスト
            index: GnosisIndex インスタンス (None → 自動生成)

        Returns:
            更新されたレコード数
        """
        if not results:
            return 0

        # GnosisIndex の取得
        if index is None:
            try:
                from mekhane.anamnesis.index import GnosisIndex
                index = GnosisIndex()
            except Exception as e:  # noqa: BLE001
                log.error(f"[FieldClassifier] GnosisIndex 初期化失敗: {e}")
                return 0

        # ClassificationResult → update_f2_fields() 形式に変換
        classifications = [
            {
                "session_id": r.session_id,
                "cluster_label": r.cluster_label,
                "tags": r.tags,
                "confidence": r.confidence,
            }
            for r in results
        ]

        updated = index.update_f2_fields(classifications)
        log.info(f"[FieldClassifier] ✅ {updated} レコードに F2 分類を永続化")
        return updated
