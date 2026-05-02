#!/usr/bin/env python3
"""v0.7 vs v0.8: precision が λ schedule 経由で loss に与える実質影響を測定。

hyphe_chunker.py の precision-aware λ adjustment:
  delta_lambda1 = -0.1 * (precision - 0.5)
  delta_lambda2 = +0.1 * (precision - 0.5)
  → high precision → lambda1↓(drift軽減) lambda2↑(EFE重視)

loss = (lambda1 + delta_lambda1) * drift + (lambda2 + delta_lambda2) * (-EFE)

この delta_loss を v0.7 と v0.8 の precision で計算し比較する。
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def compute_lambda_impact(results_data, label):
    """precision → λ adjustment → loss への影響を計算。"""
    LAMBDA1_BASE = 0.4
    LAMBDA2_BASE = 0.6
    SCALE = 0.1  # precision adjustment scale

    ok = [r for r in results_data if r.get("status") == "ok"]
    
    rows = []
    for r in ok:
        sid = r["session_id"][:8]
        for c in r.get("chunks", []):
            p = c.get("precision", 0.5)
            drift = c.get("drift", 0.0)
            efe = c.get("efe", 0.0)
            loss_base = LAMBDA1_BASE * drift + LAMBDA2_BASE * (-efe)

            # precision-aware lambda adjustment
            dp = p - 0.5
            dl1 = -SCALE * dp
            dl2 = +SCALE * dp
            loss_adj = (LAMBDA1_BASE + dl1) * drift + (LAMBDA2_BASE + dl2) * (-efe)
            delta_loss = loss_adj - loss_base

            rows.append({
                "sid": sid,
                "cid": c["chunk_id"],
                "precision": p,
                "drift": drift,
                "efe": efe,
                "loss_base": loss_base,
                "loss_adj": loss_adj,
                "delta_loss": delta_loss,
                "dl1": dl1,
                "dl2": dl2,
            })
    
    print("\n" + "=" * 70)
    print(label)
    print("=" * 70)
    
    if not rows:
        print("NO DATA")
        return

    # セッション別詳細
    for row in rows:
        print("  {sid} c{cid:2d}: p={precision:.3f} drift={drift:.4f} efe={efe:.4f} "
              "dl1={dl1:+.4f} dl2={dl2:+.4f} dL={delta_loss:+.6f}".format(**row))
    
    # 集約統計
    n = len(rows)
    abs_dl = [abs(r["delta_loss"]) for r in rows]
    mean_abs_dl = sum(abs_dl) / n
    max_abs_dl = max(abs_dl)
    mean_dl = sum(r["delta_loss"] for r in rows) / n
    
    # precision > 0.5 のものは loss を下げる（良い）
    improve = [r for r in rows if r["delta_loss"] < -1e-6]
    worsen = [r for r in rows if r["delta_loss"] > 1e-6]
    neutral = [r for r in rows if abs(r["delta_loss"]) <= 1e-6]
    
    # base loss の統計
    base_losses = [r["loss_base"] for r in rows]
    adj_losses = [r["loss_adj"] for r in rows]
    mean_base = sum(base_losses) / n
    mean_adj = sum(adj_losses) / n
    var_base = sum((l - mean_base) ** 2 for l in base_losses) / n
    var_adj = sum((l - mean_adj) ** 2 for l in adj_losses) / n
    
    print("\n  Summary:")
    print("    chunks: {}".format(n))
    print("    mean |delta_loss|: {:.6f}".format(mean_abs_dl))
    print("    max  |delta_loss|: {:.6f}".format(max_abs_dl))
    print("    mean delta_loss:   {:+.6f}".format(mean_dl))
    print("    improved/worsened/neutral: {}/{}/{}".format(
        len(improve), len(worsen), len(neutral)))
    print("    loss_base: mean={:.6f} var={:.6f}".format(mean_base, var_base))
    print("    loss_adj:  mean={:.6f} var={:.6f}".format(mean_adj, var_adj))
    print("    loss var ratio (adj/base): {:.4f}".format(var_adj / var_base if var_base > 0 else 0))
    
    return {
        "n": n,
        "mean_abs_dl": mean_abs_dl,
        "max_abs_dl": max_abs_dl,
        "mean_dl": mean_dl,
        "improve": len(improve),
        "worsen": len(worsen),
        "var_base": var_base,
        "var_adj": var_adj,
    }


def main():
    results = {}
    for ver, fn in [("v0.7 min-max", "precision_v07_results.json"),
                    ("v0.8 quantile", "precision_v08_results.json")]:
        with open(BASE / fn) as f:
            data = json.load(f)
        stats = compute_lambda_impact(data, ver)
        if stats:
            results[ver] = stats

    # 比較
    if len(results) == 2:
        v7 = results["v0.7 min-max"]
        v8 = results["v0.8 quantile"]
        print("\n" + "=" * 70)
        print("COMPARISON")
        print("=" * 70)
        print("                     v0.7 min-max    v0.8 quantile   ratio")
        print("  mean |dL|:         {:.6f}        {:.6f}        {:.2f}x".format(
            v7["mean_abs_dl"], v8["mean_abs_dl"],
            v8["mean_abs_dl"] / v7["mean_abs_dl"] if v7["mean_abs_dl"] > 0 else 0))
        print("  max  |dL|:         {:.6f}        {:.6f}        {:.2f}x".format(
            v7["max_abs_dl"], v8["max_abs_dl"],
            v8["max_abs_dl"] / v7["max_abs_dl"] if v7["max_abs_dl"] > 0 else 0))
        print("  improved:          {:3d}/{}           {:3d}/{}".format(
            v7["improve"], v7["n"], v8["improve"], v8["n"]))
        print("  loss var ratio:    {:.4f}          {:.4f}".format(
            v7["var_adj"] / v7["var_base"] if v7["var_base"] > 0 else 0,
            v8["var_adj"] / v8["var_base"] if v8["var_base"] > 0 else 0))


if __name__ == "__main__":
    main()
