#!/usr/bin/env python3
# PROOF: [L2/実験] <- VISION §17.9 方向B — C3v2 fullness アブレーション
"""
C3v2 (¥/# トークン) の fullness への寄与を測定。

実験設計:
  - C3v2 ON (現行): python_to_ccl() = ¥/# で引数とローカル変数の出自を区別
  - C3v2 OFF: 全変数を "#" に統一 (出自情報なし)
  - 比較: CCL テキストの多様性 (ユニーク比率)、特徴ベクトルの分散、忘却率

fullness = CCL の構造的差異の保持率
  忘却率 = 1 - (CCL 空間でのユニーク/元の空間でのユニーク)
  fullness ≈ 1 - 忘却率
"""

import ast
import sys
import os
from pathlib import Path
from collections import Counter

import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import mannwhitneyu

# ワークスペースのコードインジェストモジュールをインポート
from mekhane.symploke.code_ingest import (
    python_to_ccl,
    ccl_features,
    ccl_feature_vector,
    _build_scope_map,
)


def python_to_ccl_no_c3v2(func_node: ast.FunctionDef) -> str:
    """C3v2 を無効化した CCL 変換。全変数を # に統一。"""
    from mekhane.symploke.code_ingest import _stmt_to_ccl
    # C3v2 OFF: arg_map を None (全変数が # にフォールバック)
    parts = []
    for stmt in func_node.body:
        if isinstance(stmt, ast.Expr) and isinstance(getattr(stmt, 'value', None), ast.Constant):
            if isinstance(stmt.value.value, str):
                continue
        ccl = _stmt_to_ccl(stmt, None)  # arg_map=None = C3v2 OFF
        if ccl:
            parts.append(ccl)
    if not parts:
        return "#"
    return " >> ".join(parts)


def extract_functions(root_dir: Path, max_files: int = 50) -> list[ast.FunctionDef]:
    """ワークスペースから関数 AST を抽出。"""
    funcs = []
    exclude = {'__pycache__', '.venv', 'node_modules', '.git', 'Archive', '90_保管庫'}

    py_files = sorted(root_dir.rglob("*.py"))
    n_files = 0
    for pf in py_files:
        parts = set(pf.relative_to(root_dir).parts)
        if parts & exclude:
            continue

        try:
            source = pf.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
        except Exception:
            continue

        n_files += 1
        if n_files > max_files:
            break

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 自明な関数を除外 (3行未満)
                if (node.end_lineno or node.lineno) - node.lineno < 3:
                    continue
                funcs.append(node)

    return funcs


def compute_fullness_metrics(ccl_texts: list[str], label: str) -> dict:
    """CCL テキスト群の fullness メトリクスを計算。"""
    n = len(ccl_texts)
    unique = len(set(ccl_texts))
    unique_ratio = unique / max(n, 1)

    # トークン多様性
    all_tokens = []
    for t in ccl_texts:
        all_tokens.extend(t.split())
    token_vocab = len(set(all_tokens))
    token_total = len(all_tokens)

    # CCL テキスト長の分布
    lengths = [len(t.split()) for t in ccl_texts]
    mean_len = np.mean(lengths)
    std_len = np.std(lengths)

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  関数数: {n}")
    print(f"  ユニーク CCL: {unique} ({unique_ratio:.1%})")
    print(f"  トークン語彙: {token_vocab} / 総トークン: {token_total}")
    print(f"  CCL 長: μ={mean_len:.1f} σ={std_len:.1f}")

    return {
        'n': n, 'unique': unique, 'unique_ratio': unique_ratio,
        'token_vocab': token_vocab, 'token_total': token_total,
        'mean_len': mean_len, 'std_len': std_len,
    }


def compute_feature_diversity(features: list[list[float]], label: str) -> dict:
    """特徴ベクトルの多様性を計算。"""
    X = np.array(features)
    # z-score 正規化
    mu = X.mean(axis=0)
    sigma = X.std(axis=0)
    sigma[sigma == 0] = 1
    Z = (X - mu) / sigma

    # ペアワイズ L1 距離
    dists = pdist(Z, metric='cityblock')
    mean_dist = np.mean(dists)
    std_dist = np.std(dists)

    # 分散 (各次元の平均分散)
    per_dim_var = np.var(Z, axis=0)
    total_var = np.sum(per_dim_var)

    # ¥ と # のカウント差
    yen_counts = X[:, 22] if X.shape[1] > 22 else np.zeros(len(X))  # arity = dim 22

    print(f"\n  特徴ベクトル多様性 ({label}):")
    print(f"    L1 ペア距離: μ={mean_dist:.2f} σ={std_dist:.2f}")
    print(f"    総分散: {total_var:.2f}")
    print(f"    ¥ (arity) 分布: μ={np.mean(yen_counts):.2f} σ={np.std(yen_counts):.2f}")

    return {
        'mean_dist': mean_dist, 'std_dist': std_dist,
        'total_var': total_var,
        'yen_mean': float(np.mean(yen_counts)),
        'yen_std': float(np.std(yen_counts)),
    }


def main():
    root = Path("/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon")

    print("=" * 60)
    print("  方向B: C3v2 Fullness アブレーション")
    print("=" * 60)

    # 関数を抽出
    print("\n📦 関数を抽出中...")
    funcs = extract_functions(root / "20_機構｜Mekhane" / "_src｜ソースコード", max_files=100)
    print(f"  抽出: {len(funcs)} 関数")

    if len(funcs) < 10:
        print("❌ 関数が少なすぎる")
        return

    # --- C3v2 ON (現行) ---
    ccl_on = []
    feats_on = []
    for f in funcs:
        try:
            ccl = python_to_ccl(f)
            feat = ccl_features(ccl)
            ccl_on.append(ccl)
            feats_on.append(feat)
        except Exception:
            pass

    m_on = compute_fullness_metrics(ccl_on, "C3v2 ON (¥/# トークン)")
    d_on = compute_feature_diversity(feats_on, "C3v2 ON")

    # --- C3v2 OFF (全変数 = #) ---
    ccl_off = []
    feats_off = []
    for f in funcs:
        try:
            ccl = python_to_ccl_no_c3v2(f)
            feat = ccl_features(ccl)
            ccl_off.append(ccl)
            feats_off.append(feat)
        except Exception:
            pass

    m_off = compute_fullness_metrics(ccl_off, "C3v2 OFF (全変数 = #)")
    d_off = compute_feature_diversity(feats_off, "C3v2 OFF")

    # --- 比較 ---
    print(f"\n{'='*60}")
    print(f"  比較結果")
    print(f"{'='*60}")

    # ユニーク率の差
    delta_unique = m_on['unique_ratio'] - m_off['unique_ratio']
    print(f"\n  ユニーク CCL 比率:")
    print(f"    C3v2 ON:  {m_on['unique_ratio']:.1%} ({m_on['unique']}/{m_on['n']})")
    print(f"    C3v2 OFF: {m_off['unique_ratio']:.1%} ({m_off['unique']}/{m_off['n']})")
    print(f"    差分: +{delta_unique:.1%}")

    # 語彙の差
    delta_vocab = m_on['token_vocab'] - m_off['token_vocab']
    print(f"\n  トークン語彙:")
    print(f"    C3v2 ON:  {m_on['token_vocab']}")
    print(f"    C3v2 OFF: {m_off['token_vocab']}")
    print(f"    差分: +{delta_vocab}")

    # 特徴ベクトル多様性の差
    delta_dist = d_on['mean_dist'] - d_off['mean_dist']
    delta_var = d_on['total_var'] - d_off['total_var']
    print(f"\n  特徴ベクトル (27d):")
    print(f"    L1 距離 ON:  {d_on['mean_dist']:.2f}")
    print(f"    L1 距離 OFF: {d_off['mean_dist']:.2f}")
    print(f"    差分: {delta_dist:+.2f}")
    print(f"    総分散 ON:  {d_on['total_var']:.2f}")
    print(f"    総分散 OFF: {d_off['total_var']:.2f}")
    print(f"    差分: {delta_var:+.2f}")

    # ¥ トークンの影響
    print(f"\n  ¥ トークン (dim 22: arity):")
    print(f"    ON:  μ={d_on['yen_mean']:.2f} σ={d_on['yen_std']:.2f}")
    print(f"    OFF: μ={d_off['yen_mean']:.2f} σ={d_off['yen_std']:.2f}")

    # --- CCL テキストの差分分析 ---
    print(f"\n{'='*60}")
    print(f"  CCL テキスト差分分析")
    print(f"{'='*60}")

    n_different = sum(1 for a, b in zip(ccl_on, ccl_off) if a != b)
    print(f"\n  C3v2 ON/OFF で異なる CCL: {n_different}/{len(ccl_on)} ({n_different/max(len(ccl_on),1):.1%})")

    # 差分の例を表示
    examples = 0
    for a, b in zip(ccl_on, ccl_off):
        if a != b and examples < 5:
            # ¥ を含む部分だけ抽出
            on_toks = set(a.split())
            off_toks = set(b.split())
            diff = on_toks - off_toks
            if diff:
                print(f"\n  [例 {examples+1}]")
                print(f"    ON:  {a[:120]}...")
                print(f"    OFF: {b[:120]}...")
                print(f"    差分トークン: {diff}")
                examples += 1

    # --- 忘却率の計算 ---
    print(f"\n{'='*60}")
    print(f"  忘却率 (§17.6 定義)")
    print(f"{'='*60}")

    # 忘却率 = 1 - unique_ccl / n_functions
    # fullness ≈ 1 - 忘却率 = unique_ccl / n_functions
    forgetting_on = 1 - m_on['unique_ratio']
    forgetting_off = 1 - m_off['unique_ratio']
    fullness_on = m_on['unique_ratio']
    fullness_off = m_off['unique_ratio']

    print(f"\n  C3v2 ON:  忘却率={forgetting_on:.3f}  fullness={fullness_on:.3f}")
    print(f"  C3v2 OFF: 忘却率={forgetting_off:.3f}  fullness={fullness_off:.3f}")
    print(f"  C3v2 の寄与: Δfullness={fullness_on - fullness_off:+.3f}")

    # --- ペアワイズ距離の統計的検定 ---
    if len(feats_on) == len(feats_off) and len(feats_on) > 10:
        X_on = np.array(feats_on)
        X_off = np.array(feats_off)
        mu_on = X_on.mean(axis=0)
        sig_on = X_on.std(axis=0); sig_on[sig_on == 0] = 1
        mu_off = X_off.mean(axis=0)
        sig_off = X_off.std(axis=0); sig_off[sig_off == 0] = 1

        Z_on = (X_on - mu_on) / sig_on
        Z_off = (X_off - mu_off) / sig_off

        dists_on = pdist(Z_on, metric='cityblock')
        dists_off = pdist(Z_off, metric='cityblock')

        # Mann-Whitney U 検定
        stat, p = mannwhitneyu(dists_on, dists_off, alternative='two-sided')
        print(f"\n  Mann-Whitney U 検定 (ペアワイズ L1 距離):")
        print(f"    U={stat:.0f}, p={p:.2e}")
        if p < 0.05:
            print(f"    → 有意差あり (p<0.05)")
        else:
            print(f"    → 有意差なし (p≥0.05)")

    # --- 結論 ---
    print(f"\n{'='*60}")
    print(f"  結論")
    print(f"{'='*60}")
    if fullness_on > fullness_off:
        print(f"\n  C3v2 は fullness を {fullness_off:.3f} → {fullness_on:.3f} に改善 (+{fullness_on - fullness_off:.3f})")
        print(f"  ¥/# トークンがデータの出自を保存し、CCL の構造的多様性を向上させている")
    else:
        print(f"\n  C3v2 の fullness への寄与は限定的 ({fullness_off:.3f} → {fullness_on:.3f})")


if __name__ == "__main__":
    main()
