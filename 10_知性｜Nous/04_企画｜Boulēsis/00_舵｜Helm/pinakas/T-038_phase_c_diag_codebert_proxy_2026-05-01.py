#!/usr/bin/env python3
"""T-038 diagnostic-pair probe for Q-007 structural-understanding gates.

This is a deliberately small, reproducible proxy experiment:
- SOURCE: phase_c_diagnostic.jsonl diagnostic pairs.
- Encoder: microsoft/codebert-base last hidden state mean pooling.
- Probe: balanced logistic regression over pair features.
- Baselines: 49d cosine, CCL similarity, CodeBERT cosine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("has_source") and row.get("source_a") and row.get("source_b"):
            rows.append(row)
    return rows


def rank_array(x: np.ndarray) -> np.ndarray:
    # Average-rank implementation without pandas dependency.
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    i = 0
    while i < len(x):
        j = i + 1
        while j < len(x) and x[order[j]] == x[order[i]]:
            j += 1
        avg = (i + 1 + j) / 2.0
        ranks[order[i:j]] = avg
        i = j
    return ranks


def safe_spearman(x: np.ndarray, y: np.ndarray) -> float | None:
    if len(x) < 3 or len(np.unique(x)) < 2 or len(np.unique(y)) < 2:
        return None
    val = spearmanr(x, y).correlation
    if val is None or math.isnan(float(val)):
        return None
    return float(val)


def partial_spearman(pred: np.ndarray, true: np.ndarray, confound: np.ndarray) -> float | None:
    if len(pred) < 4 or len(np.unique(pred)) < 2 or len(np.unique(true)) < 2:
        return None
    pred_r = rank_array(pred).reshape(-1, 1)
    true_r = rank_array(true).reshape(-1, 1)
    conf_r = rank_array(confound).reshape(-1, 1)
    pred_res = pred_r - LinearRegression().fit(conf_r, pred_r).predict(conf_r)
    true_res = true_r - LinearRegression().fit(conf_r, true_r).predict(conf_r)
    return safe_spearman(pred_res.ravel(), true_res.ravel())


def retrieval_at_k(scores: np.ndarray, labels: np.ndarray, k: int) -> float | None:
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return None
    hits = 0
    for score in pos:
        rank = int(np.sum(neg > score))
        if rank < k:
            hits += 1
    return hits / len(pos)


def point_biserial_like(score: np.ndarray, labels: np.ndarray) -> float | None:
    return safe_spearman(score, labels.astype(float))


def score_summary(scores: np.ndarray, labels: np.ndarray, rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    pred = (scores >= 0.5).astype(int) if name.endswith("prob") else (scores >= np.median(scores)).astype(int)
    if len(np.unique(scores)) >= 2:
        try:
            auc = float(roc_auc_score(labels, scores))
        except ValueError:
            auc = None
    else:
        auc = None
    ccl_true = 1.0 - np.array([float(r["ccl_edit_dist"]) for r in rows], dtype=float)
    cos49 = np.array([float(r["cosine_49d"]) for r in rows], dtype=float)
    confound = np.array([(len(r["source_a"]) + len(r["source_b"])) / 2 for r in rows], dtype=float)
    return {
        "name": name,
        "threshold_rule": "0.5 for probabilities; median otherwise",
        "acc": float(accuracy_score(labels, pred)),
        "f1": float(f1_score(labels, pred, zero_division=0)),
        "auc": auc,
        "rho_label": point_biserial_like(scores, labels),
        "rho_49d": safe_spearman(scores, cos49),
        "rho_ccl": safe_spearman(scores, ccl_true),
        "partial_rho_ccl_len": partial_spearman(scores, ccl_true, confound),
        "r_at_1": retrieval_at_k(scores, labels, 1),
        "r_at_5": retrieval_at_k(scores, labels, 5),
        "r_at_10": retrieval_at_k(scores, labels, 10),
    }


def cv_logreg_scores(x: np.ndarray, y: np.ndarray, seed: int, groups: np.ndarray | None = None) -> np.ndarray:
    scores = np.zeros(len(y), dtype=float)
    if groups is None:
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
        splits = cv.split(x, y)
    else:
        cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
        splits = cv.split(x, y, groups)
    for train_idx, test_idx in splits:
        clf = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, class_weight="balanced", solver="liblinear", random_state=seed),
        )
        clf.fit(x[train_idx], y[train_idx])
        scores[test_idx] = clf.predict_proba(x[test_idx])[:, 1]
    return scores


def permutation_null(x: np.ndarray, y: np.ndarray, observed_auc: float | None, seed: int, n_perm: int, groups: np.ndarray | None = None) -> dict[str, Any]:
    if observed_auc is None:
        return {"n_perm": n_perm, "metric": "auc", "observed": None, "p_ge_observed": None}
    rng = np.random.default_rng(seed)
    vals = []
    for i in range(n_perm):
        y_perm = rng.permutation(y)
        s = cv_logreg_scores(x, y_perm, seed + i + 1, groups)
        try:
            vals.append(float(roc_auc_score(y_perm, s)))
        except ValueError:
            continue
    vals_arr = np.array(vals, dtype=float)
    p = float((np.sum(vals_arr >= observed_auc) + 1) / (len(vals_arr) + 1)) if len(vals_arr) else None
    return {
        "n_perm": int(len(vals_arr)),
        "metric": "auc",
        "observed": observed_auc,
        "mean": float(np.mean(vals_arr)) if len(vals_arr) else None,
        "p_ge_observed": p,
    }



def source_components(rows: list[dict[str, Any]]) -> np.ndarray:
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for r in rows:
        union(stable_hash(r["source_a"]), stable_hash(r["source_b"]))
    comp_to_id: dict[str, int] = {}
    groups = []
    for r in rows:
        root = find(stable_hash(r["source_a"]))
        comp_to_id.setdefault(root, len(comp_to_id))
        groups.append(comp_to_id[root])
    return np.array(groups, dtype=int)

def load_or_compute_embeddings(texts: list[str], cache_dir: Path, model_name: str, batch_size: int, seed: int) -> dict[str, np.ndarray]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, np.ndarray] = {}
    missing: list[str] = []
    for text in texts:
        key = stable_hash(text)
        p = cache_dir / f"{key}.npy"
        if p.exists():
            out[text] = np.load(p)
        else:
            missing.append(text)
    if not missing:
        return out

    import torch
    from transformers import AutoModel, AutoTokenizer

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device)
    model.eval()

    with torch.no_grad():
        for start in range(0, len(missing), batch_size):
            batch = missing[start : start + batch_size]
            enc = tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors="pt")
            enc = {k: v.to(device) for k, v in enc.items()}
            hidden = model(**enc).last_hidden_state
            mask = enc["attention_mask"].unsqueeze(-1).to(hidden.dtype)
            pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
            arr = pooled.detach().cpu().numpy().astype("float32")
            for text, emb in zip(batch, arr):
                key = stable_hash(text)
                np.save(cache_dir / f"{key}.npy", emb)
                out[text] = emb
    return out


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom else 0.0


def claim_level(row: dict[str, Any]) -> str:
    if row.get("auc") is not None and row["auc"] >= 0.9 and row.get("partial_rho_ccl_len") is not None and row["partial_rho_ccl_len"] >= 0.3:
        if row.get("r_at_10") is not None and row["r_at_10"] >= 0.7:
            return "L3 candidate; G5 depends on per-pair diagnostic robustness"
        return "L2 candidate"
    if row.get("auc") is not None and row["auc"] >= 0.7:
        return "L1 candidate"
    return "L0 / fail"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    ap.add_argument("--out-md", type=Path, required=True)
    ap.add_argument("--cache-dir", type=Path, required=True)
    ap.add_argument("--model", default="microsoft/codebert-base")
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--seed", type=int, default=38039)
    ap.add_argument("--n-perm", type=int, default=50)
    args = ap.parse_args()

    rows = load_rows(args.input)
    labels = np.array([int(r["label"]) for r in rows], dtype=int)
    texts = sorted(set([r["source_a"] for r in rows] + [r["source_b"] for r in rows]), key=stable_hash)
    embeddings = load_or_compute_embeddings(texts, args.cache_dir, args.model, args.batch_size, args.seed)

    pair_features = []
    codebert_cos = []
    for r in rows:
        ea = embeddings[r["source_a"]]
        eb = embeddings[r["source_b"]]
        codebert_cos.append(cosine(ea, eb))
        pair_features.append(np.concatenate([np.abs(ea - eb), ea * eb, [codebert_cos[-1]]]).astype("float32"))
    x = np.vstack(pair_features)
    codebert_cos_arr = np.array(codebert_cos, dtype=float)

    groups = source_components(rows)
    prob = cv_logreg_scores(x, labels, args.seed)
    prob_group = cv_logreg_scores(x, labels, args.seed, groups)

    # Direction: high score means positive label (diag_blindspot).
    cos49_raw = np.array([float(r["cosine_49d"]) for r in rows], dtype=float)
    ccl_sim = 1.0 - np.array([float(r["ccl_edit_dist"]) for r in rows], dtype=float)
    baselines = {
        "49d_inverse_similarity": 1.0 - cos49_raw,
        "ccl_similarity_oracle": ccl_sim,
        "codebert_inverse_cosine": 1.0 - codebert_cos_arr,
        "codebert_pair_logreg_row_prob": prob,
        "codebert_pair_logreg_source_component_prob": prob_group,
    }
    summaries = [score_summary(v, labels, rows, k if k.endswith("prob") else k) for k, v in baselines.items()]
    for s in summaries:
        s["claim_level"] = claim_level(s)

    logreg_summary = next(s for s in summaries if s["name"] == "codebert_pair_logreg_source_component_prob")
    null = permutation_null(x, labels, logreg_summary.get("auc"), args.seed + 9000, args.n_perm, groups)

    per_type: dict[str, Any] = {}
    for pair_type in sorted(set(r["pair_type"] for r in rows)):
        idx = np.array([r["pair_type"] == pair_type for r in rows], dtype=bool)
        type_labels = labels[idx]
        type_scores = prob_group[idx]
        type_rows = [r for r, keep in zip(rows, idx) if keep]
        pred = (type_scores >= 0.5).astype(int)
        ccl_true = 1.0 - np.array([float(r["ccl_edit_dist"]) for r in type_rows], dtype=float)
        confound = np.array([(len(r["source_a"]) + len(r["source_b"])) / 2 for r in type_rows], dtype=float)
        per_type[pair_type] = {
            "n": int(np.sum(idx)),
            "label_values": sorted(set(int(v) for v in type_labels.tolist())),
            "mean_score": float(np.mean(type_scores)),
            "acc": float(accuracy_score(type_labels, pred)),
            "error_rate": float(1.0 - accuracy_score(type_labels, pred)),
            "rho_ccl": safe_spearman(type_scores, ccl_true),
            "partial_rho_ccl_len": partial_spearman(type_scores, ccl_true, confound),
            "r_at_1": None,
            "r_at_5": None,
            "r_at_10": None,
            "note": "R@k is global-only because this diagnostic type has a single class label." if len(set(type_labels.tolist())) == 1 else "",
        }

    result = {
        "task": "T-038 / Q-007 diagnostic pair evaluation",
        "input": str(args.input),
        "model": args.model,
        "seed": args.seed,
        "n_rows_source": len(rows),
        "n_unique_sources": len(texts),
        "label_semantics": {"0": "diag_isomer", "1": "diag_blindspot"},
        "feature_shape": list(x.shape),
        "source_component_count": int(len(set(groups.tolist()))),
        "source_component_largest_pair_count": int(max(np.bincount(groups))),
        "summaries": summaries,
        "per_type_codebert_pair_logreg": per_type,
        "permutation_null_codebert_pair_logreg_source_component": null,
    }
    def fmt(v: Any) -> str:
        if v is None:
            return "N/A"
        if isinstance(v, float):
            return f"{v:.3f}"
        return str(v)

    # Claim-level wording is evidence-role aware; controls/oracles are not representation evidence.
    for s in summaries:
        if s["name"] == "ccl_similarity_oracle":
            s["claim_level"] = "target-side oracle; not representation evidence"
        elif s["name"] == "49d_inverse_similarity":
            s["claim_level"] = "construction/control baseline; not independent representation evidence"
        elif s["name"] == "codebert_pair_logreg_row_prob":
            s["claim_level"] = s["claim_level"] + "; row split has source-leakage risk"
        elif s["name"] == "codebert_pair_logreg_source_component_prob":
            s["claim_level"] = s["claim_level"] + "; source-component split"

    result["summaries"] = summaries
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# T-038 Phase C Diagnostic Pair Evaluation — CodeBERT Proxy",
        "",
        "## SOURCE",
        f"- input: `{args.input}`",
        f"- rows_used: `{len(rows)}` / unique_sources: `{len(texts)}`",
        f"- source_components: `{len(set(groups.tolist()))}` / largest_component_pairs: `{int(max(np.bincount(groups)))}`",
        f"- model: `{args.model}`",
        f"- cache_dir: `{args.cache_dir}`",
        "",
        "## Overall Metrics",
        "| score | acc | f1 | auc | rho_label | rho_49d | rho_ccl | partial_rho_ccl_len | R@1 | R@5 | R@10 | claim_level |",
        "|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|",
    ]
    for s in summaries:
        lines.append(
            "| {name} | {acc} | {f1} | {auc} | {rho_label} | {rho_49d} | {rho_ccl} | {partial} | {r1} | {r5} | {r10} | {claim} |".format(
                name=s["name"],
                acc=fmt(s["acc"]),
                f1=fmt(s["f1"]),
                auc=fmt(s["auc"]),
                rho_label=fmt(s["rho_label"]),
                rho_49d=fmt(s["rho_49d"]),
                rho_ccl=fmt(s["rho_ccl"]),
                partial=fmt(s["partial_rho_ccl_len"]),
                r1=fmt(s["r_at_1"]),
                r5=fmt(s["r_at_5"]),
                r10=fmt(s["r_at_10"]),
                claim=s["claim_level"],
            )
        )
    lines.extend([
        "",
        "## G3 Shuffle Null",
        f"- metric: `{null['metric']}`",
        f"- observed: `{fmt(null['observed'])}`",
        f"- null_mean: `{fmt(null.get('mean'))}`",
        f"- n_perm: `{null['n_perm']}`",
        f"- p_ge_observed: `{fmt(null['p_ge_observed'])}`",
        "",
        "## G5 Diagnostic Pair Robustness — CodeBERT Pair LogReg",
        "| pair_type | n | labels | mean_score | acc | error_rate | rho_ccl | partial_rho_ccl_len | R@1 | R@5 | R@10 | note |",
        "|:---|---:|:---|---:|---:|---:|---:|---:|:---|:---|:---|:---|",
    ])
    for pair_type, s in per_type.items():
        lines.append(
            "| {pt} | {n} | {labels} | {mean_score} | {acc} | {err} | {rho} | {partial} | {r1} | {r5} | {r10} | {note} |".format(
                pt=pair_type,
                n=s["n"],
                labels=",".join(map(str, s["label_values"])),
                mean_score=fmt(s["mean_score"]),
                acc=fmt(s["acc"]),
                err=fmt(s["error_rate"]),
                rho=fmt(s["rho_ccl"]),
                partial=fmt(s["partial_rho_ccl_len"]),
                r1=fmt(s["r_at_1"]),
                r5=fmt(s["r_at_5"]),
                r10=fmt(s["r_at_10"]),
                note=s["note"],
            )
        )
    lines.extend([
        "",
        "## Interpretation",
        "- `ccl_similarity_oracle` is a target-side oracle and is not representation evidence.",
        "- `codebert_pair_logreg_row_prob` is exploratory and has source-overlap leakage risk.",
        "- `codebert_pair_logreg_source_component_prob` is stricter: connected source components are not split across folds.",
        "- Even the stricter probe can satisfy G5 only as proxy evidence, not final causal proof.",
        "- `R@k` is defined globally: each positive diagnostic blindspot is ranked against all negative diagnostic isomers.",
    ])
    args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"out_json": str(args.out_json), "out_md": str(args.out_md), "rows": len(rows), "unique_sources": len(texts)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
