#!/usr/bin/env python3
"""Phase C 診断ペア生成: 構造異性体 + 49d 盲点

49d の限界を直接測定するための診断ペアを生成。
Phase C が 49d を超えるかどうかのリトマス試験。

2種の診断ペア:
  isomer:    cosine_49d >= 0.85 AND ccl_sim < 0.4
             = 49d は「似ている」と言うが構造が異なる (偽陽性)
  blindspot: cosine_49d < 0.5  AND ccl_sim > 0.7
             = 49d は「違う」と言うが構造が似ている (偽陰性)

教師信号:
  cosine_49d — 既存 (49d の判断)
  ccl_edit_distance — 新規 (CCL 文字列の正規化編集距離)
  → Phase C が 49d を超えるなら、ccl_edit_distance との相関が cosine_49d より高くなるはず

Usage:
  python phase_c_diagnostic_pairs.py
  python phase_c_diagnostic_pairs.py --n-isomers 200 --dry-run
"""
from __future__ import annotations

import ast
import json
import random
import sys
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np

_SCRIPT_DIR = Path(__file__).parent
_HGK_ROOT = _SCRIPT_DIR.parent.parent.parent.parent
_DEFAULT_PKL = _HGK_ROOT / "30_記憶｜Mneme" / "02_索引｜Index" / "code_ccl_features.pkl"

WIN_PREFIX = "C:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/"
LINUX_PREFIX = str(_HGK_ROOT) + "/"


def win_to_linux(wp: str) -> str:
    return wp.replace("\\", "/").replace(WIN_PREFIX, LINUX_PREFIX)


def extract_function_source(file_path: str, func_name: str) -> str | None:
    try:
        source = Path(file_path).read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception:
        return None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == func_name:
                lines = source.splitlines()
                end = node.end_lineno or (node.lineno + 20)
                return "\n".join(lines[node.lineno - 1 : end])
    return None


def ccl_similarity(a: str, b: str, max_len: int = 300) -> float:
    """CCL 文字列の類似度 (SequenceMatcher)。"""
    if len(a) < 5 or len(b) < 5:
        return 0.0
    return SequenceMatcher(None, a[:max_len], b[:max_len]).ratio()


def normalized_edit_distance(a: str, b: str, max_len: int = 500) -> float:
    """正規化 Levenshtein 距離 (0=同一, 1=完全異なる)。簡易版。"""
    a, b = a[:max_len], b[:max_len]
    if not a and not b:
        return 0.0
    # SequenceMatcher の ratio を反転
    return 1.0 - SequenceMatcher(None, a, b).ratio()


def load_pkl(pkl_path: Path):
    import pickle
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)
    raw = np.vstack(data["vectors"]).astype(np.float32)
    mean, std = raw.mean(0), raw.std(0)
    std = np.where(std > 1e-10, std, 1.0)
    mat = (raw - mean) / std
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms = np.where(norms > 1e-10, norms, 1.0)
    mat = mat / norms
    return mat, data["metadata"]


def find_isomers(
    mat: np.ndarray, metadata: list[dict],
    n_target: int = 200, n_anchors: int = 500, seed: int = 42,
    cos_min: float = 0.85, ccl_sim_max: float = 0.4,
) -> list[dict]:
    """構造異性体: cosine_49d 高 + CCL 類似度低。"""
    rng = random.Random(seed)
    N = len(metadata)
    anchors = rng.sample(range(N), min(n_anchors, N))
    candidates = []

    for i in anchors:
        sims = mat @ mat[i]
        mask = (sims >= cos_min) & (sims < 0.999) & (np.arange(N) != i)
        for j in np.where(mask)[0]:
            ccl_i = metadata[i].get("ccl_expr", "")
            ccl_j = metadata[int(j)].get("ccl_expr", "")
            if len(ccl_i) > 10 and len(ccl_j) > 10:
                csim = ccl_similarity(ccl_i, ccl_j)
                if csim < ccl_sim_max:
                    candidates.append({
                        "i": i, "j": int(j),
                        "cosine_49d": float(sims[j]),
                        "ccl_sim": csim,
                        "ccl_edit_dist": normalized_edit_distance(ccl_i, ccl_j),
                    })

    # 多様性: ccl_sim が低い順 (最も異なる構造異性体を優先)
    candidates.sort(key=lambda x: x["ccl_sim"])
    # 重複除去
    used = set()
    unique = []
    for c in candidates:
        key = (min(c["i"], c["j"]), max(c["i"], c["j"]))
        if key not in used:
            used.add(key)
            unique.append(c)

    return unique[:n_target]


def find_blindspots(
    mat: np.ndarray, metadata: list[dict],
    n_anchors: int = 1000, seed: int = 42,
    cos_max: float = 0.5, ccl_sim_min: float = 0.7,
) -> list[dict]:
    """49d 盲点: cosine_49d 低 + CCL 類似度高。全数収集。"""
    rng = random.Random(seed)
    N = len(metadata)
    anchors = rng.sample(range(N), min(n_anchors, N))
    candidates = []

    for i in anchors:
        sims = mat @ mat[i]
        mask = (sims < cos_max) & (sims > -0.5) & (np.arange(N) != i)
        js = np.where(mask)[0]
        if len(js) == 0:
            continue

        ccl_i = metadata[i].get("ccl_expr", "")
        if len(ccl_i) < 20:
            continue

        sample = rng.sample(list(js), min(30, len(js)))
        for j in sample:
            ccl_j = metadata[int(j)].get("ccl_expr", "")
            if len(ccl_j) < 20:
                continue
            csim = ccl_similarity(ccl_i, ccl_j)
            if csim > ccl_sim_min:
                candidates.append({
                    "i": i, "j": int(j),
                    "cosine_49d": float(sims[j]),
                    "ccl_sim": csim,
                    "ccl_edit_dist": normalized_edit_distance(ccl_i, ccl_j),
                })

    # 重複除去
    used = set()
    unique = []
    for c in candidates:
        key = (min(c["i"], c["j"]), max(c["i"], c["j"]))
        if key not in used:
            used.add(key)
            unique.append(c)

    unique.sort(key=lambda x: x["ccl_sim"], reverse=True)
    return unique


def pairs_to_jsonl(
    pairs: list[dict], metadata: list[dict], pair_type: str, output_path: Path
) -> int:
    """診断ペアを統一 JSONL 形式で出力。3条件 (A/B/D) 対応。"""
    written = 0
    with open(output_path, "a", encoding="utf-8") as f:
        for p in pairs:
            mi, mj = metadata[p["i"]], metadata[p["j"]]

            # ソースコード抽出
            path_i = win_to_linux(mi.get("file_path", ""))
            path_j = win_to_linux(mj.get("file_path", ""))
            src_i = extract_function_source(path_i, mi.get("function_name", ""))
            src_j = extract_function_source(path_j, mj.get("function_name", ""))

            ccl_i = mi.get("ccl_expr", "")
            ccl_j = mj.get("ccl_expr", "")

            # 3条件対応の統合レコード
            rec = {
                "ccl_a": ccl_i,
                "ccl_b": ccl_j,
                "source_a": src_i or "",
                "source_b": src_j or "",
                "label": 1 if pair_type == "blindspot" else 0,  # 盲点=構造的正例, 異性体=構造的負例
                "cosine_49d": p["cosine_49d"],
                "ccl_sim": p["ccl_sim"],
                "ccl_edit_dist": p["ccl_edit_dist"],
                "pair_type": f"diag_{pair_type}",
                "has_source": bool(src_i and src_j),
                "func_a": f"{mi.get('file_path', '')}::{mi.get('function_name', '')}",
                "func_b": f"{mj.get('file_path', '')}::{mj.get('function_name', '')}",
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1
    return written


def write_condition_files(diag_path: Path, output_dir: Path) -> None:
    """診断データを A/B/D 条件別に変換して既存ファイルに追記。"""
    records = []
    with open(diag_path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    for cond, make_text in [
        ("A", lambda r: (r["ccl_a"], r["ccl_b"])),
        ("B", lambda r: (f"### Code\n{r['source_a']}\n\n### CCL\n{r['ccl_a']}",
                         f"### Code\n{r['source_b']}\n\n### CCL\n{r['ccl_b']}")),
        ("D", lambda r: (r["source_a"], r["source_b"])),
    ]:
        out_path = output_dir / f"phase_c_condition_{cond}_diag.jsonl"
        with_source = [r for r in records if r["has_source"]] if cond in ("B", "D") else records
        with open(out_path, "w", encoding="utf-8") as f:
            for r in with_source:
                ta, tb = make_text(r)
                rec = {
                    "text_a": ta,
                    "text_b": tb,
                    "label": r["label"],
                    "cosine_49d": r["cosine_49d"],
                    "ccl_sim": r["ccl_sim"],
                    "ccl_edit_dist": r["ccl_edit_dist"],
                    "pair_type": r["pair_type"],
                    "condition": f"{cond}_diag",
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"  {cond}_diag: {out_path.name} — {len(with_source)} pairs")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Phase C diagnostic pairs")
    parser.add_argument("--pkl", default=str(_DEFAULT_PKL))
    parser.add_argument("--n-isomers", type=int, default=200)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"📂 pkl: {args.pkl}")
    mat, metadata = load_pkl(Path(args.pkl))
    print(f"  {mat.shape[0]} vectors, {mat.shape[1]}d")

    # 構造異性体
    print(f"\n🔍 構造異性体 (cosine_49d≥0.85, ccl_sim<0.4)...")
    isomers = find_isomers(mat, metadata, n_target=args.n_isomers)
    print(f"  → {len(isomers)} ペア")

    # 49d 盲点
    print(f"\n🔍 49d 盲点 (cosine_49d<0.5, ccl_sim>0.7)...")
    blindspots = find_blindspots(mat, metadata)
    print(f"  → {len(blindspots)} ペア")

    if args.dry_run:
        print("\n🔍 Dry run — 書出しスキップ")
        return

    # 診断 JSONL 出力
    diag_path = _SCRIPT_DIR / "phase_c_diagnostic.jsonl"
    # 新規作成 (空にする)
    diag_path.write_text("")

    n_iso = pairs_to_jsonl(isomers, metadata, "isomer", diag_path)
    n_bs = pairs_to_jsonl(blindspots, metadata, "blindspot", diag_path)
    print(f"\n💾 {diag_path.name}: {n_iso} isomers + {n_bs} blindspots = {n_iso + n_bs} pairs")

    # 条件別ファイル生成
    print(f"\n💾 条件別 JSONL:")
    write_condition_files(diag_path, _SCRIPT_DIR)

    # 統計
    print(f"\n📊 診断データセット統計:")
    print(f"  構造異性体: {n_iso} (49d 偽陽性 — Phase C が区別できれば勝利)")
    print(f"  49d 盲点:   {n_bs} (49d 偽陰性 — Phase C が発見できれば勝利)")
    print(f"  教師信号:   cosine_49d + ccl_sim + ccl_edit_dist")


if __name__ == "__main__":
    main()
