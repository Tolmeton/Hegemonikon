#!/usr/bin/env python3
# PROOF: [L2/ユーティリティ] <- mekhane/symploke/phantazein_store.py
# PURPOSE: SQLite BLOB に numpy 配列を格納する際の encode/decode ユーティリティ
"""
NumPy BLOB ストレージユーティリティ

SQLite の BLOB カラムに numpy 配列を格納する際に、
shape ヘッダ付きフォーマットで保存・復元するための関数群。

フォーマット:
  [header: ndim × 4bytes (little-endian int32)] + [data: float64 bytes]

KI 参照: numpy_blob_storage_pattern.md
"""
import struct
from typing import Optional, Tuple

import numpy as np


def encode_ndarray_blob(arr: np.ndarray) -> bytes:
    """numpy 配列を shape ヘッダ付き BLOB にエンコード

    Args:
        arr: 任意 dtype の numpy 配列 (内部で float64 に変換)

    Returns:
        bytes: [shape header] + [float64 data]
    """
    # dtype を float64 に統一 (精度保証)
    arr_f64 = arr.astype(np.float64)
    # shape ヘッダ: 各次元を 4byte int で格納
    fmt = f"<{arr_f64.ndim}i"
    header = struct.pack(fmt, *arr_f64.shape)
    return header + arr_f64.tobytes()


def decode_ndarray_blob(
    blob: bytes,
    ndim: int,
    fallback_cols: Optional[int] = None,
) -> Tuple[np.ndarray, bool]:
    """shape ヘッダ付き BLOB から numpy 配列を復元

    Args:
        blob: encode_ndarray_blob で作成した BLOB (またはヘッダなし旧形式)
        ndim: 期待する次元数 (2 = 行列, 1 = ベクトル)
        fallback_cols: 旧形式フォールバック時の列数 (ndim=2 の場合に必要)

    Returns:
        (ndarray, is_new_format): 復元された配列と新形式かどうかのフラグ
    """
    if not blob:
        return np.array([]), False

    header_size = ndim * 4  # 各次元 4bytes

    # 新形式: ヘッダ付き
    if len(blob) > header_size:
        shape = struct.unpack(f"<{ndim}i", blob[:header_size])
        data = np.frombuffer(blob[header_size:], dtype=np.float64)

        expected_size = 1
        for s in shape:
            expected_size *= s

        if len(data) == expected_size and all(s > 0 for s in shape):
            return data.reshape(shape), True

    # 旧形式: ヘッダなし → shape 推定
    data = np.frombuffer(blob, dtype=np.float64)

    if ndim == 2 and fallback_cols is not None and fallback_cols > 0:
        rows = len(data) // fallback_cols
        return data.reshape(rows, fallback_cols), False

    if ndim == 1:
        return data, False

    # フォールバック不可
    return data, False
