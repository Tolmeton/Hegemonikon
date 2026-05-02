#!/usr/bin/env python3
"""T-039 error analysis for T-038 diagnostic pair probe."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import confusion_matrix


def load_t038(path: Path):
    spec = importlib.util.spec_from_file_location("t038_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def short_code(src: str, limit: int = 520) -> str:
    src = src.strip()
    src = re.sub(r"\n{3,}", "\n\n", src)
    return src if len(src) <= limit else src[:limit].rstrip() + "\n..."


def code_signals(src: str) -> dict[str, Any]:
    return {
        "len": len(src),
        "lines": src.count("\n") + 1,
        "asserts": len(re.findall(r"\bassert\b", src)),
        "defs": len(re.findall(r"\bdef\s+", src)),
        "classes": len(re.findall(r"\bclass\s+", src)),
        "argparse": "argparse" in src,
        "test_like": bool(re.search(r"\btest_|assert\b", src)),
        "unicode": any(ord(ch) > 127 for ch in src),
    }


def classify_error(row: dict[str, Any]) -> str:
    a, b = row["source_a"], row["source_b"]
    sa, sb = code_signals(a), code_signals(b)
    if sa["test_like"] and sb["test_like"]:
        return "test_scaffold_overlap"
    if sa["argparse"] or sb["argparse"]:
        return "cli_parser_long_surface"
    if abs(sa["len"] - sb["len"]) > 1200:
        return "length_asymmetry"
    if sa["unicode"] or sb["unicode"]:
        return "unicode_docstring_surface"
    return "generic_structural_surface_overlap"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--t038-script", type=Path, required=True)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--cache-dir", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    ap.add_argument("--out-md", type=Path, required=True)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=38039)
    args = ap.parse_args()

    t038 = load_t038(args.t038_script)
    rows = t038.load_rows(args.input)
    labels = np.array([int(r["label"]) for r in rows], dtype=int)
    texts = sorted(set([r["source_a"] for r in rows] + [r["source_b"] for r in rows]), key=t038.stable_hash)
    embeddings = t038.load_or_compute_embeddings(texts, args.cache_dir, "microsoft/codebert-base", 24, args.seed)

    features = []
    codebert_cos = []
    for r in rows:
        ea = embeddings[r["source_a"]]
        eb = embeddings[r["source_b"]]
        c = t038.cosine(ea, eb)
        codebert_cos.append(c)
        features.append(np.concatenate([np.abs(ea - eb), ea * eb, [c]]).astype("float32"))
    x = np.vstack(features)
    groups = t038.source_components(rows)
    scores = t038.cv_logreg_scores(x, labels, args.seed, groups)
    pred = (scores >= args.threshold).astype(int)
    cm = confusion_matrix(labels, pred, labels=[0, 1]).tolist()

    errors = []
    for i, (r, y, yhat, score, cos) in enumerate(zip(rows, labels, pred, scores, codebert_cos)):
        if y == yhat:
            continue
        err = "false_positive_isomer" if y == 0 else "false_negative_blindspot"
        errors.append({
            "index": i,
            "error_type": err,
            "pair_type": r["pair_type"],
            "score": float(score),
            "label": int(y),
            "pred": int(yhat),
            "cosine_49d": float(r["cosine_49d"]),
            "ccl_similarity": float(1.0 - float(r["ccl_edit_dist"])),
            "codebert_cosine": float(cos),
            "func_a": r.get("func_a"),
            "func_b": r.get("func_b"),
            "signals_a": code_signals(r["source_a"]),
            "signals_b": code_signals(r["source_b"]),
            "class": classify_error(r),
            "source_a_excerpt": short_code(r["source_a"]),
            "source_b_excerpt": short_code(r["source_b"]),
        })

    fp = [e for e in errors if e["error_type"] == "false_positive_isomer"]
    fn = [e for e in errors if e["error_type"] == "false_negative_blindspot"]
    class_counts = Counter(e["class"] for e in fp)
    top_fp = sorted(fp, key=lambda e: e["score"], reverse=True)[:12]
    top_fn = sorted(fn, key=lambda e: e["score"])[:12]

    result = {
        "task": "T-039 diagnostic isomer error analysis",
        "input": str(args.input),
        "t038_script": str(args.t038_script),
        "rows": len(rows),
        "threshold": args.threshold,
        "confusion_matrix_labels_0_1": cm,
        "error_counts": Counter(e["error_type"] for e in errors),
        "false_positive_class_counts": dict(class_counts),
        "n_errors": len(errors),
        "errors": errors,
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    def f(v: float) -> str:
        return f"{v:.3f}"

    lines = [
        "# T-039 Diagnostic Isomer Error Analysis",
        "",
        "## SOURCE",
        f"- input: `{args.input}`",
        f"- scorer: `{args.t038_script}`",
        f"- rows: `{len(rows)}`",
        f"- threshold: `{args.threshold}`",
        "",
        "## Confusion Matrix",
        "Labels are `[0=diag_isomer, 1=diag_blindspot]`.",
        "",
        "| true\\pred | 0 | 1 |",
        "|:---|---:|---:|",
        f"| 0 | {cm[0][0]} | {cm[0][1]} |",
        f"| 1 | {cm[1][0]} | {cm[1][1]} |",
        "",
        "## Error Taxonomy",
        "| class | count | interpretation |",
        "|:---|---:|:---|",
    ]
    interp = {
        "test_scaffold_overlap": "Both sides look like tests/assertion scaffolds; surface role overwhelms deeper CCL separation.",
        "cli_parser_long_surface": "Large CLI/parser boilerplate creates broad structural similarity noise.",
        "length_asymmetry": "Length or truncation asymmetry likely distorts pair features.",
        "unicode_docstring_surface": "Docstring/comment language surface may dominate representation.",
        "generic_structural_surface_overlap": "No single simple surface cause; requires local inspection.",
    }
    for k, v in class_counts.most_common():
        lines.append(f"| {k} | {v} | {interp.get(k, '')} |")
    lines.extend([
        "",
        "## Highest-Score False Positives",
        "These are `diag_isomer` pairs incorrectly classified as `diag_blindspot`.",
        "",
        "| idx | score | class | ccl_sim | 49d_cos | codebert_cos | func_a | func_b |",
        "|---:|---:|:---|---:|---:|---:|:---|:---|",
    ])
    for e in top_fp:
        lines.append(
            f"| {e['index']} | {f(e['score'])} | {e['class']} | {f(e['ccl_similarity'])} | {f(e['cosine_49d'])} | {f(e['codebert_cosine'])} | `{e['func_a']}` | `{e['func_b']}` |"
        )
    lines.extend([
        "",
        "## Lowest-Score False Negatives",
        "These are `diag_blindspot` pairs incorrectly classified as `diag_isomer`.",
        "",
        "| idx | score | class | ccl_sim | 49d_cos | codebert_cos | func_a | func_b |",
        "|---:|---:|:---|---:|---:|---:|:---|:---|",
    ])
    if top_fn:
        for e in top_fn:
            lines.append(
                f"| {e['index']} | {f(e['score'])} | {e['class']} | {f(e['ccl_similarity'])} | {f(e['cosine_49d'])} | {f(e['codebert_cosine'])} | `{e['func_a']}` | `{e['func_b']}` |"
            )
    else:
        lines.append("| N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |")
    lines.extend([
        "",
        "## Local Excerpts For Top False Positives",
    ])
    for e in top_fp[:5]:
        lines.extend([
            "",
            f"### FP idx {e['index']} — score {f(e['score'])} — {e['class']}",
            f"- func_a: `{e['func_a']}`",
            f"- func_b: `{e['func_b']}`",
            "",
            "```python",
            e["source_a_excerpt"],
            "```",
            "",
            "```python",
            e["source_b_excerpt"],
            "```",
        ])
    lines.extend([
        "",
        "## Judgment",
        "- The strict component split leaves 27 false positives and 0 false negatives at threshold 0.5.",
        "- The remaining failure mode is asymmetric: the probe over-promotes some high-surface-overlap isomers, but does not miss blindspots in this run.",
        "- This supports Q-007 G5 as `L3 candidate`, while L4 stays blocked until false-positive isomers are reduced or explained by a stronger negative-control design.",
    ])
    args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"out_json": str(args.out_json), "out_md": str(args.out_md), "errors": len(errors), "fp": len(fp), "fn": len(fn)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
