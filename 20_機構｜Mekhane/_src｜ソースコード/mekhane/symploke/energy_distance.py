from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/モジュール] <- mekhane/symploke → ED パイプライン (Lawvere 距離空間)
"""Energy Distance パイプライン — ファイル間構造距離の計算。

ED(L1) → centroid L1 フォールバック → cl^0.25 → Floyd-Warshall → d/(1+d)

ファイルを「関数群の分布」として扱い、Energy Distance で
分布間の距離を測定する。負 ED (群内分散 > 群間距離) が発生した場合、
centroid L1 距離で代替する (§17.12 フォールバック)。

理論的基盤:
- VISION.md §17 (ED → Lawvere 距離空間)
- §17.12 (縮退解消: centroid L1 フォールバック)

Usage:
    from mekhane.symploke.energy_distance import FileDistanceIndex

    idx = FileDistanceIndex()
    n = idx.build("path/to/code.pkl")
    d = idx.distance("file_a.py", "file_b.py")  # ∈ [0, 1]
    nn = idx.nearest("file_a.py", k=5)
"""

# PURPOSE: ファイル間の構造距離を ED + FW + フォールバックで計算する


import os
import pickle
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


# ============================================================
# 距離計算の基本関数
# ============================================================

# PURPOSE: L1 (マンハッタン) 距離
def l1_distance(a: list[float], b: list[float]) -> float:
    """2つのベクトル間の L1 距離を計算する。"""
    return sum(abs(x - y) for x, y in zip(a, b))


# PURPOSE: 群内ペアワイズ L1 距離
def _pairwise_distances(group: list[list[float]]) -> list[float]:
    """群内の全ペアの L1 距離を返す。"""
    dists = []
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            dists.append(l1_distance(group[i], group[j]))
    return dists


# PURPOSE: 群間クロス L1 距離
def _cross_distances(group_a: list[list[float]], group_b: list[list[float]]) -> list[float]:
    """2群間の全ペアの L1 距離を返す。"""
    dists = []
    for a in group_a:
        for b in group_b:
            dists.append(l1_distance(a, b))
    return dists


# PURPOSE: Energy Distance (L1 ベース)
def energy_distance(feats_p: list[list[float]], feats_q: list[list[float]]) -> float:
    """2つの関数群間の Energy Distance を計算する。

    ED = 2 * E[|X-Y|] - E[|X-X'|] - E[|Y-Y'|]

    群内分散が群間距離を上回る場合、負の値を返すことがある。
    呼出元で centroid L1 フォールバックを適用すること。

    Args:
        feats_p: ファイル P の関数群の特徴量ベクトル
        feats_q: ファイル Q の関数群の特徴量ベクトル

    Returns:
        Energy Distance (負になりうる)
    """
    cross = _cross_distances(feats_p, feats_q)
    cross_mean = sum(cross) / len(cross) if cross else 0.0
    wp_dists = _pairwise_distances(feats_p)
    wq_dists = _pairwise_distances(feats_q)
    wp = sum(wp_dists) / len(wp_dists) if wp_dists else 0.0
    wq = sum(wq_dists) / len(wq_dists) if wq_dists else 0.0
    return 2 * cross_mean - wp - wq


# PURPOSE: centroid (平均特徴量ベクトル) を計算
def compute_centroid(feats: list[list[float]]) -> list[float]:
    """関数群の centroid (平均特徴量) を返す。

    Args:
        feats: 関数群の特徴量ベクトル

    Returns:
        dim 次元の centroid ベクトル
    """
    if not feats:
        return []
    dim = len(feats[0])
    centroid = [0.0] * dim
    for feat in feats:
        for d in range(dim):
            centroid[d] += feat[d]
    n = len(feats)
    return [c / n for c in centroid]


# PURPOSE: Floyd-Warshall 閉包 (三角不等式を保証)
def floyd_warshall(names: list[str], dist_matrix: dict[tuple[str, str], float]) -> dict[tuple[str, str], float]:
    """Floyd-Warshall で距離行列の三角不等式閉包を計算する。

    Args:
        names: ファイル名リスト
        dist_matrix: {(a, b): distance} の辞書

    Returns:
        三角不等式を満たす距離行列
    """
    n = len(names)
    idx = {name: i for i, name in enumerate(names)}
    d = [[float('inf')] * n for _ in range(n)]
    for i in range(n):
        d[i][i] = 0.0
    for (a, b), val in dist_matrix.items():
        if a in idx and b in idx:
            i, j = idx[a], idx[b]
            d[i][j] = val
    # FW 本体
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if d[i][k] + d[k][j] < d[i][j]:
                    d[i][j] = d[i][k] + d[k][j]
    # 辞書に戻す
    result = {}
    for i in range(n):
        for j in range(n):
            result[(names[i], names[j])] = d[i][j]
    return result


# ============================================================
# FileDistanceIndex — ファイル間距離インデックス
# ============================================================

# PURPOSE: ファイル間の構造距離を保持するインデックス
class FileDistanceIndex:
    """ファイル間の ED ベース構造距離インデックス。

    ED(L1) → centroid L1 フォールバック (§17.12) → cl^0.25 → FW → d/(1+d)
    パイプラインで Lawvere [0,1]-距離空間を構成する。

    使い方:
        idx = FileDistanceIndex()
        idx.build("path/to/code.pkl")
        d = idx.distance("file_a.py", "file_b.py")  # ∈ [0, 1]
    """

    # フォールバック統計
    FEATURE_DIM = 43  # ccl_features が格納される次元数

    def __init__(self) -> None:
        self._distances: dict[tuple[str, str], float] = {}
        self._files: list[str] = []
        self._built = False
        # フォールバック統計
        self._alpha: float = 1.0
        self._neg_ed_count: int = 0
        self._total_pairs: int = 0

    @property
    def file_count(self) -> int:
        """インデックス内のファイル数。"""
        return len(self._files)

    # ================================================================
    # 構築
    # ================================================================

    # PURPOSE: code.pkl からファイルグルーピング → ED → フォールバック → FW → d/(1+d)
    def build(
        self,
        code_pkl_path: str,
        min_functions: int = 5,
        sample_size: int = 20,
        max_files: int = 50,
    ) -> int:
        """code.pkl から ED パイプラインを実行してファイル距離インデックスを構築する。

        Args:
            code_pkl_path: code.pkl のパス
            min_functions: ファイルに含まれる最小関数数 (これ未満は除外)
            sample_size: 各ファイルからサンプリングする関数数
            max_files: 処理するファイルの最大数 (計算量制御)

        Returns:
            インデックスに含まれるファイル数
        """
        # 1. code.pkl を読み込み、ファイルごとに関数特徴量をグルーピング
        file_groups = self._load_file_groups(code_pkl_path, min_functions)

        # 関数数でソートし、top-N を取得
        sorted_files = sorted(file_groups.items(), key=lambda x: -len(x[1]))
        if max_files:
            sorted_files = sorted_files[:max_files]
        file_groups = dict(sorted_files)

        names = list(file_groups.keys())
        if len(names) < 2:
            self._files = names
            self._built = True
            return len(names)

        # 2. ED 計算 + centroid L1 フォールバック
        ed_raw, centroids = self._compute_ed_matrix(names, file_groups, sample_size)

        # 3. フォールバック適用
        ed_fixed = self._apply_fallback(names, ed_raw, centroids)

        # 4. cl^0.25 変換
        d_pre: dict[tuple[str, str], float] = {}
        for (a, b), v in ed_fixed.items():
            d_pre[(a, b)] = max(0.0, v) ** 0.25

        # 5. Floyd-Warshall
        d_fw = floyd_warshall(names, d_pre)

        # 6. d/(1+d) 正規化
        self._distances = {}
        for (a, b), v in d_fw.items():
            self._distances[(a, b)] = v / (1 + v) if v < float('inf') else 1.0

        self._files = names
        self._built = True
        return len(names)

    # PURPOSE: code.pkl からファイル→関数特徴量のグルーピング
    def _load_file_groups(
        self,
        code_pkl_path: str,
        min_functions: int,
    ) -> dict[str, list[list[float]]]:
        """code.pkl を読み込み、ファイルごとに ccl_features をグルーピングする。"""
        with open(code_pkl_path, "rb") as f:
            data = pickle.load(f)

        metas = list(data.get("metadata", {}).values())
        by_file: dict[str, list[list[float]]] = defaultdict(list)

        for m in metas:
            if not isinstance(m, dict):
                continue
            feats = m.get("ccl_features")
            if not feats or len(feats) != self.FEATURE_DIM:
                continue
            fname = os.path.basename(str(m.get("file_path", "")))
            if fname:
                by_file[fname].append(list(feats))

        # 最小関数数フィルタ
        return {f: feats for f, feats in by_file.items() if len(feats) >= min_functions}

    # PURPOSE: 全ペアの ED + centroid を計算
    def _compute_ed_matrix(
        self,
        names: list[str],
        file_groups: dict[str, list[list[float]]],
        sample_size: int,
    ) -> tuple[dict[tuple[str, str], float], dict[str, list[float]]]:
        """全ファイルペアの ED と各ファイルの centroid を計算する。"""
        ed_raw: dict[tuple[str, str], float] = {}
        centroids: dict[str, list[float]] = {}

        # centroid 計算
        for f in names:
            feats = file_groups[f][:sample_size]
            centroids[f] = compute_centroid(feats)

        # ED 計算
        for f in names:
            ed_raw[(f, f)] = 0.0
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                f1, f2 = names[i], names[j]
                feats1 = file_groups[f1][:sample_size]
                feats2 = file_groups[f2][:sample_size]
                ed = energy_distance(feats1, feats2)
                ed_raw[(f1, f2)] = ed
                ed_raw[(f2, f1)] = ed

        return ed_raw, centroids

    # PURPOSE: §17.12 centroid L1 フォールバックの適用
    def _apply_fallback(
        self,
        names: list[str],
        ed_raw: dict[tuple[str, str], float],
        centroids: dict[str, list[float]],
    ) -> dict[tuple[str, str], float]:
        """負 ED を centroid L1 距離 × α で置換する。

        α = median(ED>0) / median(centroid_L1) で正規化し、
        フォールバック距離が ED 距離空間と同じスケールになるようにする。
        """
        # centroid L1 距離行列
        centroid_l1: dict[tuple[str, str], float] = {}
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                f1, f2 = names[i], names[j]
                cl1 = l1_distance(centroids[f1], centroids[f2])
                centroid_l1[(f1, f2)] = cl1
                centroid_l1[(f2, f1)] = cl1

        # α 正規化係数
        ed_pos = [v for (a, b), v in ed_raw.items() if a < b and v > 0]
        cl1_vals = [v for (a, b), v in centroid_l1.items() if a < b]

        if ed_pos and cl1_vals:
            self._alpha = float(np.median(ed_pos) / np.median(cl1_vals))
        else:
            self._alpha = 1.0

        # 負 ED カウント
        self._neg_ed_count = sum(1 for (a, b), v in ed_raw.items() if a < b and v <= 0)
        self._total_pairs = sum(1 for (a, b) in ed_raw if a < b)

        # フォールバック適用
        ed_fixed: dict[tuple[str, str], float] = {}
        for (a, b), v in ed_raw.items():
            if a == b:
                ed_fixed[(a, b)] = 0.0
            elif v <= 0:
                cl1 = centroid_l1.get((a, b), 0.0)
                ed_fixed[(a, b)] = self._alpha * cl1
            else:
                ed_fixed[(a, b)] = v

        return ed_fixed

    # ================================================================
    # 検索
    # ================================================================

    # PURPOSE: ファイル間距離の取得
    def distance(self, file_a: str, file_b: str) -> float:
        """2ファイル間の構造距離を返す。∈ [0, 1]。

        Args:
            file_a: ファイル名 (basename)
            file_b: ファイル名 (basename)

        Returns:
            [0, 1] の距離。ファイルが見つからない場合は 1.0。
        """
        if not self._built:
            return 1.0
        return self._distances.get((file_a, file_b), 1.0)

    # PURPOSE: 最近傍ファイル検索
    def nearest(self, file_name: str, k: int = 5) -> list[tuple[str, float]]:
        """指定ファイルに構造的に最も近いファイルを返す。

        Args:
            file_name: 検索対象のファイル名 (basename)
            k: 返す件数

        Returns:
            [(file_name, distance)] のリスト (距離昇順)
        """
        if not self._built or file_name not in self._files:
            return []

        pairs = []
        for other in self._files:
            if other == file_name:
                continue
            d = self._distances.get((file_name, other), 1.0)
            pairs.append((other, d))

        pairs.sort(key=lambda x: x[1])
        return pairs[:k]

    # PURPOSE: フォールバック統計の取得
    def stats(self) -> dict:
        """フォールバック統計を返す。"""
        return {
            "file_count": len(self._files),
            "total_pairs": self._total_pairs,
            "neg_ed_count": self._neg_ed_count,
            "alpha": self._alpha,
            "built": self._built,
        }

    # ================================================================
    # 永続化
    # ================================================================

    # PURPOSE: pkl に保存
    def save(self, path: str) -> None:
        """距離インデックスを pkl に保存する。"""
        data = {
            "version": 1,
            "files": self._files,
            "distances": self._distances,
            "alpha": self._alpha,
            "neg_ed_count": self._neg_ed_count,
            "total_pairs": self._total_pairs,
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)

    # PURPOSE: pkl から読込
    def load(self, path: str) -> None:
        """距離インデックスを pkl から読み込む。"""
        with open(path, "rb") as f:
            data = pickle.load(f)

        self._files = data["files"]
        self._distances = data["distances"]
        self._alpha = data.get("alpha", 1.0)
        self._neg_ed_count = data.get("neg_ed_count", 0)
        self._total_pairs = data.get("total_pairs", 0)
        self._built = True
