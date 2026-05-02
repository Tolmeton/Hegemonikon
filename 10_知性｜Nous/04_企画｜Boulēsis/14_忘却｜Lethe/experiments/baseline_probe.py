#!/usr/bin/env python3
# PROOF: [L2/実験] <- 60_実験｜Peira/07_CCL-PL Phase B 信頼性検証
"""
Phase B 信頼性検証: ベースライン比較

批判的検討で特定した問題:
  1. 循環性 — CCL と LLM が同じ表面特徴を見ている可能性
  2. ベースライン不在 — TF-IDF でも同程度の相関が出るかもしれない

このスクリプトは以下のベースラインを追加し CodeBERT と比較する:
  B0: ランダムベクトル  → 偶然の相関の下限
  B1: TF-IDF cosine     → 表面的な語彙重複でどこまで行けるか
  B2: 一般 BERT         → コード特化でない LLM の構造理解度
  B3: コード長差分       → 単純な長さの違いが交絡因子になっていないか

Usage:
  python baseline_probe.py          # 全ベースライン実行
  python baseline_probe.py --skip-bert  # BERT スキップ (CPU 節約)
"""

# PURPOSE: Phase B ベースライン検証

import sys
import os
import ast
import json
import argparse
import textwrap
import math
from pathlib import Path

import numpy as np
from scipy import stats

# パス設定
_SCRIPT_DIR = Path(__file__).parent
_HGK_ROOT = _SCRIPT_DIR.parent.parent
_MEKHANE_SRC = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"
sys.path.insert(0, str(_MEKHANE_SRC))

from mekhane.symploke.code_ingest import python_to_ccl
from p3_benchmark import create_benchmark_pairs

# structural_probe.py の関数を再利用
from structural_probe import (
    prepare_data,
    cosine_similarity,
    normalized_levenshtein,
    _NumpyEncoder,
)


# ============================================================
# ベースライン実装
# ============================================================

# PURPOSE: TF-IDF ベースライン
def tfidf_baseline(data):
    """TF-IDF cosine 類似度を計算。
    
    コードのソーステキストに対する TF-IDF → cosine。
    CCL ではなく生のコード文字列を使用。
    循環性の検証: 単純な語彙重複で ρ がどこまで行くか。
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as sklearn_cos
    
    # 全ペアのコードを収集
    pairs = create_benchmark_pairs()
    pair_map = {p.pair_id: p for p in pairs}
    
    # 全コードスニペットを収集 (ペアごとに A, B)
    all_codes = []
    pair_indices = []
    for d in data:
        pair = pair_map[d.pair_id]
        all_codes.append(pair.func_a_source)
        all_codes.append(pair.func_b_source)
        pair_indices.append(len(all_codes) - 2)
    
    # TF-IDF ベクトル化
    vectorizer = TfidfVectorizer(
        token_pattern=r'[a-zA-Z_]\w*',  # 識別子を抽出
        max_features=1000,
        max_df=0.95,
        min_df=1,
    )
    tfidf_matrix = vectorizer.fit_transform(all_codes)
    
    # ペアごとの cosine
    tfidf_cosines = []
    for i, d in enumerate(data):
        idx_a = pair_indices[i]
        idx_b = idx_a + 1
        vec_a = tfidf_matrix[idx_a].toarray()
        vec_b = tfidf_matrix[idx_b].toarray()
        cos_val = sklearn_cos(vec_a, vec_b)[0, 0]
        tfidf_cosines.append(float(cos_val))
    
    return tfidf_cosines


# PURPOSE: ランダムベクトルベースライン
def random_baseline(data, dim=768, seed=42):
    """ランダムベクトルの cosine 類似度。下限の確認。"""
    rng = np.random.RandomState(seed)
    rand_cosines = []
    for _ in data:
        vec_a = rng.randn(dim)
        vec_b = rng.randn(dim)
        cos_val = cosine_similarity(vec_a, vec_b)
        rand_cosines.append(cos_val)
    return rand_cosines


# PURPOSE: コード長差分ベースライン
def length_baseline(data):
    """コード長の類似度 (1 - |len_a - len_b| / max(len_a, len_b))。
    
    交絡因子の検査: 長さの違いだけで ρ が出ているのでは？
    """
    pairs = create_benchmark_pairs()
    pair_map = {p.pair_id: p for p in pairs}
    
    length_sims = []
    for d in data:
        pair = pair_map[d.pair_id]
        len_a = len(pair.func_a_source)
        len_b = len(pair.func_b_source)
        if max(len_a, len_b) == 0:
            length_sims.append(1.0)
        else:
            length_sims.append(1.0 - abs(len_a - len_b) / max(len_a, len_b))
    
    return length_sims


# PURPOSE: 一般 BERT (非コード) ベースライン
def bert_baseline(data):
    """bert-base-uncased (一般英語モデル) の hidden state 類似度。
    
    コード特化でないモデルでどこまで行けるか。
    CodeBERT との差 = コード特化訓練の効果。
    """
    import torch
    from transformers import AutoModel, AutoTokenizer
    
    model_name = "bert-base-uncased"
    print(f"📦 ベースライン BERT ロード: {model_name}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name, output_hidden_states=True)
    model.eval()
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    
    pairs = create_benchmark_pairs()
    pair_map = {p.pair_id: p for p in pairs}
    
    n_layers = model.config.num_hidden_layers  # 12
    
    # 各ペアの全層 cosine を計算
    all_layer_cosines = {layer: [] for layer in range(n_layers + 1)}
    
    for d in data:
        pair = pair_map[d.pair_id]
        
        for side_code, hs_list_key in [(pair.func_a_source, "a"), (pair.func_b_source, "b")]:
            inputs = tokenizer(
                side_code, return_tensors="pt", truncation=True,
                max_length=512, padding=True,
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = model(**inputs)
            
            # mean pool
            mask = inputs["attention_mask"].unsqueeze(-1).float()
            hidden_states = outputs.hidden_states
            pooled = []
            for layer_hs in hidden_states:
                masked = layer_hs * mask
                mean_vec = masked.sum(dim=1) / mask.sum(dim=1)
                pooled.append(mean_vec[0].cpu().numpy())
            
            if hs_list_key == "a":
                hs_a = pooled
            else:
                hs_b = pooled
        
        for layer in range(n_layers + 1):
            cos_val = cosine_similarity(hs_a[layer], hs_b[layer])
            all_layer_cosines[layer].append(cos_val)
    
    return all_layer_cosines, n_layers


# ============================================================
# 分析 + 比較
# ============================================================

# PURPOSE: 1つのベースラインの結果を分析
def analyze_baseline(name, cosines, data):
    """Spearman ρ + Mann-Whitney U を計算。"""
    ccl_sims = [d.ccl_similarity for d in data]
    positive_mask = [d.is_positive for d in data]
    
    pos_cos = [c for c, m in zip(cosines, positive_mask) if m]
    neg_cos = [c for c, m in zip(cosines, positive_mask) if not m]
    
    # Mann-Whitney U
    try:
        _, mw_p = stats.mannwhitneyu(pos_cos, neg_cos, alternative="greater")
    except Exception:
        mw_p = 1.0
    
    # Spearman ρ
    try:
        rho, rho_p = stats.spearmanr(cosines, ccl_sims)
    except Exception:
        rho, rho_p = 0.0, 1.0
    
    pos_mean = float(np.mean(pos_cos))
    neg_mean = float(np.mean(neg_cos))
    gap = pos_mean - neg_mean
    
    return {
        "name": name,
        "spearman_rho": float(rho),
        "spearman_p": float(rho_p),
        "mannwhitney_p": float(mw_p),
        "pos_cos_mean": pos_mean,
        "neg_cos_mean": neg_mean,
        "gap": gap,
    }


def main():
    parser = argparse.ArgumentParser(description="Phase B: ベースライン検証")
    parser.add_argument("--skip-bert", action="store_true",
                        help="一般 BERT ベースラインをスキップ")
    args = parser.parse_args()
    
    # データ準備
    data = prepare_data()
    print(f"📊 データ: {len(data)} ペア")
    
    results = {}
    
    # --- CodeBERT 結果の読み込み (比較対象) ---
    codebert_path = _SCRIPT_DIR / "phase_b_codebert.json"
    if codebert_path.exists():
        with open(codebert_path) as f:
            cb_data = json.load(f)
        # best layer の情報を取得
        best_layer = cb_data.get("best_rho_layer", 11)
        best_rho = cb_data.get("best_rho", 0)
        results["CodeBERT (L11)"] = {
            "name": f"CodeBERT (Layer {best_layer})",
            "spearman_rho": best_rho,
            "spearman_p": cb_data["layers"][best_layer]["spearman_p"],
            "mannwhitney_p": cb_data["layers"][best_layer]["mannwhitney_p"],
            "pos_cos_mean": cb_data["layers"][best_layer]["pos_cos_mean"],
            "neg_cos_mean": cb_data["layers"][best_layer]["neg_cos_mean"],
            "gap": cb_data["layers"][best_layer]["gap"],
        }
        print(f"  ✅ CodeBERT 結果読み込み: best ρ={best_rho:.4f} @ Layer {best_layer}")
    
    # --- B0: ランダムベクトル ---
    print("\n🎲 B0: ランダムベクトルベースライン")
    rand_cos = random_baseline(data)
    results["B0: Random"] = analyze_baseline("B0: Random", rand_cos, data)
    print(f"  ρ = {results['B0: Random']['spearman_rho']:.4f}")
    
    # --- B1: TF-IDF ---
    print("\n📝 B1: TF-IDF ベースライン")
    try:
        tfidf_cos = tfidf_baseline(data)
        results["B1: TF-IDF"] = analyze_baseline("B1: TF-IDF", tfidf_cos, data)
        print(f"  ρ = {results['B1: TF-IDF']['spearman_rho']:.4f}")
    except ImportError:
        print("  ⚠️ scikit-learn が未インストール。pip install scikit-learn で追加")
        results["B1: TF-IDF"] = {"name": "B1: TF-IDF", "spearman_rho": None, "error": "sklearn missing"}
    
    # --- B3: コード長 ---
    print("\n📏 B3: コード長差分ベースライン")
    len_sims = length_baseline(data)
    results["B3: Length"] = analyze_baseline("B3: Length", len_sims, data)
    print(f"  ρ = {results['B3: Length']['spearman_rho']:.4f}")
    
    # --- B2: 一般 BERT ---
    if not args.skip_bert:
        print("\n🤖 B2: 一般 BERT (bert-base-uncased) ベースライン")
        try:
            bert_layer_cosines, bert_n_layers = bert_baseline(data)
            
            # 全層から best を探す
            best_bert_rho = -1.0
            best_bert_layer = -1
            for layer in range(bert_n_layers + 1):
                r = analyze_baseline(f"BERT L{layer}", bert_layer_cosines[layer], data)
                if r["spearman_rho"] > best_bert_rho:
                    best_bert_rho = r["spearman_rho"]
                    best_bert_layer = layer
                    best_bert_result = r
            
            best_bert_result["name"] = f"B2: BERT (Layer {best_bert_layer})"
            results["B2: BERT"] = best_bert_result
            
            # BERT の全層情報も保存
            bert_all_layers = []
            for layer in range(bert_n_layers + 1):
                r = analyze_baseline(f"BERT L{layer}", bert_layer_cosines[layer], data)
                bert_all_layers.append(r)
            results["B2: BERT"]["all_layers"] = bert_all_layers
            
            print(f"  best ρ = {best_bert_rho:.4f} @ Layer {best_bert_layer}")
        except Exception as e:
            print(f"  ⚠️ BERT ロード失敗: {e}")
            results["B2: BERT"] = {"name": "B2: BERT", "spearman_rho": None, "error": str(e)}
    
    # ============================================================
    # 比較テーブル
    # ============================================================
    print(f"\n{'='*80}")
    print("  ベースライン比較結果")
    print(f"{'='*80}")
    print(f"{'ベースライン':>25} | {'Spearman ρ':>10} | {'ρ p値':>10} | {'MW-U p':>10} | {'gap':>8}")
    print(f"{'-'*25}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*8}")
    
    for key, r in results.items():
        rho = r.get("spearman_rho")
        if rho is None:
            print(f"{key:>25} |     N/A    |     N/A    |     N/A    |    N/A")
            continue
        rho_p = r.get("spearman_p", 1.0)
        mw_p = r.get("mannwhitney_p", 1.0)
        gap = r.get("gap", 0.0)
        sig = "✅" if rho_p < 0.05 else "  "
        print(f"{key:>25} | {rho:10.4f} {sig}| {rho_p:10.2e} | {mw_p:10.2e} | {gap:+8.4f}")
    
    # 判定
    print(f"\n{'='*80}")
    print("  判定")
    print(f"{'='*80}")
    
    cb_rho = results.get("CodeBERT (L11)", {}).get("spearman_rho", 0)
    tfidf_rho = results.get("B1: TF-IDF", {}).get("spearman_rho")
    bert_rho = results.get("B2: BERT", {}).get("spearman_rho")
    rand_rho = results.get("B0: Random", {}).get("spearman_rho", 0)
    len_rho = results.get("B3: Length", {}).get("spearman_rho", 0)
    
    if tfidf_rho is not None:
        delta_tfidf = cb_rho - tfidf_rho
        if delta_tfidf > 0.1:
            print(f"  ✅ CodeBERT (ρ={cb_rho:.3f}) > TF-IDF (ρ={tfidf_rho:.3f}): Δ={delta_tfidf:+.3f}")
            print(f"     → CodeBERT は単純な語彙重複を超えた構造理解を持つ")
        elif delta_tfidf > 0:
            print(f"  ⚠️ CodeBERT (ρ={cb_rho:.3f}) > TF-IDF (ρ={tfidf_rho:.3f}): Δ={delta_tfidf:+.3f}")
            print(f"     → 差は小さい。CodeBERT の付加価値は限定的かもしれない")
        else:
            print(f"  ❌ CodeBERT (ρ={cb_rho:.3f}) ≤ TF-IDF (ρ={tfidf_rho:.3f}): Δ={delta_tfidf:+.3f}")
            print(f"     → CodeBERT は TF-IDF を超えていない。構造理解は幻想の可能性")
    
    if bert_rho is not None:
        delta_bert = cb_rho - bert_rho
        if delta_bert > 0.1:
            print(f"  ✅ CodeBERT (ρ={cb_rho:.3f}) > BERT (ρ={bert_rho:.3f}): Δ={delta_bert:+.3f}")
            print(f"     → コード特化訓練の効果がある")
        elif delta_bert > 0:
            print(f"  ⚠️ CodeBERT (ρ={cb_rho:.3f}) > BERT (ρ={bert_rho:.3f}): Δ={delta_bert:+.3f}")
            print(f"     → 差は小さい。コード特化の効果は限定的")
        else:
            print(f"  ❌ CodeBERT (ρ={cb_rho:.3f}) ≤ BERT (ρ={bert_rho:.3f}): Δ={delta_bert:+.3f}")
            print(f"     → 一般 BERT でも同等。コード特化は不要か")
    
    if abs(len_rho) > 0.5:
        print(f"  ⚠️ コード長差分 ρ={len_rho:.3f}: 長さが交絡因子の可能性")
    else:
        print(f"  ✅ コード長差分 ρ={len_rho:.3f}: 長さは主要な交絡因子ではない")
    
    # 保存
    out_path = _SCRIPT_DIR / "phase_b_baselines.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, cls=_NumpyEncoder)
    print(f"\n💾 結果保存: {out_path}")


if __name__ == "__main__":
    main()
