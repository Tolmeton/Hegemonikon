#!/usr/bin/env python3
"""Phase C visibility probe.

Minimal causal probe for the Phase C v3 interpretation:
  D-only LXI gain comes from a structural visibility gap in the input surface.

Intervention:
  1. D_code               : original D condition (code only)
  2. D_plus_ccl_aligned   : inject aligned CCL scaffold from B
  3. D_plus_ccl_shifted   : inject mismatched CCL scaffold from another pair

Readout:
  - lightweight hashed-char ridge probe
  - structure metric: rho_ccl / partial_rho_ccl
  - label metric: accuracy

This is deliberately small and CPU-friendly. It does not try to reproduce the
full 7B LoRA training loop; it isolates the input-surface hypothesis.
"""

from __future__ import annotations

import argparse
import json
import math
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy.stats import rankdata, spearmanr


SCRIPT_DIR = Path(__file__).parent
DEFAULT_D = SCRIPT_DIR / "phase_c_condition_D.jsonl"
DEFAULT_B = SCRIPT_DIR / "phase_c_condition_B.jsonl"


@dataclass
class PairRecord:
    text_a: str
    text_b: str
    label: int
    cosine_49d: float
    ccl_edit_dist: float
    ccl_sim: float
    pair_type: str
    condition: str

    @property
    def pair_text(self) -> str:
        return f"Structure A:\n{self.text_a}\n\nStructure B:\n{self.text_b}"

    @property
    def text_len(self) -> int:
        return len(self.text_a) + len(self.text_b)


def load_jsonl(path: Path) -> list[PairRecord]:
    rows: list[PairRecord] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            rows.append(
                PairRecord(
                    text_a=obj["text_a"],
                    text_b=obj["text_b"],
                    label=int(obj["label"]),
                    cosine_49d=float(obj["cosine_49d"]),
                    ccl_edit_dist=float(obj["ccl_edit_dist"]),
                    ccl_sim=float(obj["ccl_sim"]),
                    pair_type=obj.get("pair_type", "unknown"),
                    condition=obj.get("condition", "unknown"),
                )
            )
    return rows


def split_code_ccl(text: str) -> tuple[str, str]:
    marker = "\n\n### CCL\n"
    if marker not in text:
        return text.strip(), ""

    code_part, ccl_part = text.split(marker, 1)
    code_part = code_part.replace("### Code\n", "", 1).strip()
    return code_part, ccl_part.strip()


def verify_alignment(b_rows: list[PairRecord], d_rows: list[PairRecord]) -> dict[str, int]:
    if len(b_rows) != len(d_rows):
        raise ValueError(f"B/D length mismatch: {len(b_rows)} vs {len(d_rows)}")

    checks = {
        "label": 0,
        "cosine_49d": 0,
        "ccl_edit_dist": 0,
        "ccl_sim": 0,
        "code_text": 0,
    }

    for b_row, d_row in zip(b_rows, d_rows):
        checks["label"] += int(b_row.label == d_row.label)
        checks["cosine_49d"] += int(math.isclose(b_row.cosine_49d, d_row.cosine_49d, abs_tol=1e-9))
        checks["ccl_edit_dist"] += int(math.isclose(b_row.ccl_edit_dist, d_row.ccl_edit_dist, abs_tol=1e-9))
        checks["ccl_sim"] += int(math.isclose(b_row.ccl_sim, d_row.ccl_sim, abs_tol=1e-9))

        b_code_a, _ = split_code_ccl(b_row.text_a)
        b_code_b, _ = split_code_ccl(b_row.text_b)
        checks["code_text"] += int(b_code_a == d_row.text_a.strip() and b_code_b == d_row.text_b.strip())

    return checks


def build_interventions(
    b_rows: list[PairRecord],
    d_rows: list[PairRecord],
) -> dict[str, list[PairRecord]]:
    n = len(d_rows)

    d_code = d_rows
    d_plus_aligned: list[PairRecord] = []
    d_plus_shifted: list[PairRecord] = []

    for idx, (b_row, d_row) in enumerate(zip(b_rows, d_rows)):
        _, ccl_a = split_code_ccl(b_row.text_a)
        _, ccl_b = split_code_ccl(b_row.text_b)

        shifted_row = b_rows[(idx + 1) % n]
        _, shifted_ccl_a = split_code_ccl(shifted_row.text_a)
        _, shifted_ccl_b = split_code_ccl(shifted_row.text_b)

        d_plus_aligned.append(
            PairRecord(
                text_a=f"{d_row.text_a.rstrip()}\n\n### CCL\n{ccl_a}",
                text_b=f"{d_row.text_b.rstrip()}\n\n### CCL\n{ccl_b}",
                label=d_row.label,
                cosine_49d=d_row.cosine_49d,
                ccl_edit_dist=d_row.ccl_edit_dist,
                ccl_sim=d_row.ccl_sim,
                pair_type=d_row.pair_type,
                condition="D_plus_ccl_aligned",
            )
        )
        d_plus_shifted.append(
            PairRecord(
                text_a=f"{d_row.text_a.rstrip()}\n\n### CCL\n{shifted_ccl_a}",
                text_b=f"{d_row.text_b.rstrip()}\n\n### CCL\n{shifted_ccl_b}",
                label=d_row.label,
                cosine_49d=d_row.cosine_49d,
                ccl_edit_dist=d_row.ccl_edit_dist,
                ccl_sim=d_row.ccl_sim,
                pair_type=d_row.pair_type,
                condition="D_plus_ccl_shifted",
            )
        )

    return {
        "D_code": d_code,
        "D_plus_ccl_aligned": d_plus_aligned,
        "D_plus_ccl_shifted": d_plus_shifted,
    }


def structural_marker_stats(rows: Iterable[PairRecord]) -> dict[str, float]:
    texts = [row.pair_text for row in rows]
    n = len(texts)
    if n == 0:
        return {}

    keys = {
        "has_ccl_header_rate": lambda s: "### CCL" in s,
        "has_arrow_rate": lambda s: ">>" in s,
        "has_gate_rate": lambda s: "V:{" in s,
        "has_hash_rate": lambda s: "#" in s,
        "mean_chars": len,
    }
    stats: dict[str, float] = {}
    for name, fn in keys.items():
        values = [fn(t) for t in texts]
        if name == "mean_chars":
            stats[name] = float(np.mean(values))
        else:
            stats[name] = float(np.mean([1.0 if v else 0.0 for v in values]))
    return stats


def hashed_char_tfidf(texts: list[str], dim: int, ngram_min: int, ngram_max: int) -> np.ndarray:
    x = np.zeros((len(texts), dim), dtype=np.float32)

    for row_idx, text in enumerate(texts):
        local = np.zeros(dim, dtype=np.float32)
        for n in range(ngram_min, ngram_max + 1):
            if len(text) < n:
                continue
            for pos in range(len(text) - n + 1):
                gram = text[pos: pos + n]
                bucket = zlib.crc32(gram.encode("utf-8")) % dim
                local[bucket] += 1.0
        total = float(local.sum())
        if total > 0:
            local /= total
        x[row_idx] = local

    df = (x > 0).sum(axis=0)
    idf = np.log((len(texts) + 1.0) / (df + 1.0)) + 1.0
    x *= idf.astype(np.float32)

    norms = np.linalg.norm(x, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    x /= norms
    return x


def ridge_fit_predict(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    alpha: float,
) -> np.ndarray:
    x_mean = x_train.mean(axis=0, keepdims=True)
    y_mean = float(y_train.mean())

    x_centered = x_train - x_mean
    y_centered = y_train - y_mean

    xtx = x_centered.T @ x_centered
    xty = x_centered.T @ y_centered
    beta = np.linalg.solve(xtx + alpha * np.eye(xtx.shape[0], dtype=np.float32), xty)
    return (x_val - x_mean) @ beta + y_mean


def partial_spearman(pred: np.ndarray, true: np.ndarray, confound: np.ndarray) -> float:
    def residualize(y: np.ndarray, x: np.ndarray) -> np.ndarray:
        x_centered = x - x.mean()
        denom = float((x_centered ** 2).sum())
        if denom < 1e-12:
            return y
        beta = float((x_centered * (y - y.mean())).sum() / denom)
        return y - beta * x_centered

    r_pred = rankdata(pred).astype(np.float32)
    r_true = rankdata(true).astype(np.float32)
    r_conf = rankdata(confound).astype(np.float32)
    res_pred = residualize(r_pred, r_conf)
    res_true = residualize(r_true, r_conf)
    rho, _ = spearmanr(res_pred, res_true)
    return float(rho)


def make_folds(n: int, n_splits: int = 5, seed: int = 42) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    indices = np.arange(n)
    rng.shuffle(indices)
    parts = np.array_split(indices, n_splits)
    folds: list[tuple[np.ndarray, np.ndarray]] = []
    for idx in range(n_splits):
        val_idx = np.sort(parts[idx])
        train_idx = np.sort(np.concatenate([parts[j] for j in range(n_splits) if j != idx]))
        folds.append((train_idx, val_idx))
    return folds


def evaluate_condition(
    rows: list[PairRecord],
    *,
    dim: int,
    ngram_min: int,
    ngram_max: int,
    alpha_label: float,
    alpha_struct: float,
    n_splits: int,
) -> dict[str, object]:
    texts = [row.pair_text for row in rows]
    x = hashed_char_tfidf(texts, dim=dim, ngram_min=ngram_min, ngram_max=ngram_max)
    y_label = np.array([row.label for row in rows], dtype=np.float32)
    y_ccl = np.array([row.ccl_sim for row in rows], dtype=np.float32)
    lengths = np.array([row.text_len for row in rows], dtype=np.float32)

    fold_metrics: list[dict[str, float]] = []
    for fold_id, (train_idx, val_idx) in enumerate(make_folds(len(rows), n_splits=n_splits), start=1):
        pred_label = ridge_fit_predict(x[train_idx], y_label[train_idx], x[val_idx], alpha=alpha_label)
        pred_struct = ridge_fit_predict(x[train_idx], y_ccl[train_idx], x[val_idx], alpha=alpha_struct)

        pred_label = np.clip(pred_label, 0.0, 1.0)
        pred_struct = np.clip(pred_struct, 0.0, 1.0)

        binary = (pred_label >= 0.5).astype(np.int32)
        acc = float(np.mean(binary == y_label[val_idx]))
        rho_ccl, _ = spearmanr(pred_struct, y_ccl[val_idx])
        p_rho_ccl = partial_spearman(pred_struct, y_ccl[val_idx], lengths[val_idx])

        fold_metrics.append(
            {
                "fold": float(fold_id),
                "acc": acc,
                "rho_ccl": float(rho_ccl),
                "partial_rho_ccl": float(p_rho_ccl),
            }
        )

    return {
        "n_pairs": len(rows),
        "surface_stats": structural_marker_stats(rows),
        "folds": fold_metrics,
        "mean_acc": float(np.mean([m["acc"] for m in fold_metrics])),
        "mean_rho_ccl": float(np.mean([m["rho_ccl"] for m in fold_metrics])),
        "mean_partial_rho_ccl": float(np.mean([m["partial_rho_ccl"] for m in fold_metrics])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase C visibility probe")
    parser.add_argument("--d-data", type=Path, default=DEFAULT_D)
    parser.add_argument("--b-data", type=Path, default=DEFAULT_B)
    parser.add_argument("--output", type=Path, default=SCRIPT_DIR / "phase_c_visibility_probe_results.json")
    parser.add_argument("--dim", type=int, default=2048)
    parser.add_argument("--ngram-min", type=int, default=3)
    parser.add_argument("--ngram-max", type=int, default=5)
    parser.add_argument("--alpha-label", type=float, default=8.0)
    parser.add_argument("--alpha-struct", type=float, default=8.0)
    parser.add_argument("--splits", type=int, default=5)
    args = parser.parse_args()

    b_rows = load_jsonl(args.b_data)
    d_rows = load_jsonl(args.d_data)
    alignment = verify_alignment(b_rows, d_rows)
    interventions = build_interventions(b_rows, d_rows)

    results = {
        "experiment": "phase_c_visibility_probe",
        "hypothesis": "D-only LXI gain comes from structural visibility gap on the input surface",
        "config": {
            "dim": args.dim,
            "ngram_min": args.ngram_min,
            "ngram_max": args.ngram_max,
            "alpha_label": args.alpha_label,
            "alpha_struct": args.alpha_struct,
            "splits": args.splits,
        },
        "alignment": alignment,
        "conditions": {},
    }

    for name, rows in interventions.items():
        results["conditions"][name] = evaluate_condition(
            rows,
            dim=args.dim,
            ngram_min=args.ngram_min,
            ngram_max=args.ngram_max,
            alpha_label=args.alpha_label,
            alpha_struct=args.alpha_struct,
            n_splits=args.splits,
        )

    baseline = results["conditions"]["D_code"]["mean_partial_rho_ccl"]
    aligned = results["conditions"]["D_plus_ccl_aligned"]["mean_partial_rho_ccl"]
    shifted = results["conditions"]["D_plus_ccl_shifted"]["mean_partial_rho_ccl"]
    results["contrasts"] = {
        "aligned_minus_code_partial_rho_ccl": aligned - baseline,
        "aligned_minus_shifted_partial_rho_ccl": aligned - shifted,
        "aligned_minus_code_acc": (
            results["conditions"]["D_plus_ccl_aligned"]["mean_acc"]
            - results["conditions"]["D_code"]["mean_acc"]
        ),
    }

    args.output.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(json.dumps(results["contrasts"], indent=2, ensure_ascii=False))
    print(f"saved={args.output}")


if __name__ == "__main__":
    main()
