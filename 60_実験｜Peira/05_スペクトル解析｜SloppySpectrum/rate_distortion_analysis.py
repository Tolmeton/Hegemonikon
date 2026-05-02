#!/usr/bin/env python3
"""
Rate-Distortion 分析: 情報ボトルネックから最適圧縮次元を導出

背景:
  d_eff(95%) = 7 は 95% カットオフに依存する artifact。
  Rate-Distortion Theory (Tishby 2000) のフレームワークで、
  カットオフ不要な「最適圧縮次元」を導出する。

アプローチ:
  1. ソフトマックス分布の Fisher 行列の固有値分解
  2. Rate-distortion 関数 R(D) を固有値から計算
  3. 情報ボトルネックの最適トレードオフ点を同定
  4. AIC/BIC/MDL 的な次元選択を数値的に実装
  5. VFE (変分自由エネルギー) 的な次元選択
  6. 複数定義の一致点を探索
"""

import numpy as np
from typing import NamedTuple


class DimensionResult(NamedTuple):
    """各次元選択法の結果。"""
    method: str
    d_eff: int
    entropy_bits: float
    alpha: float
    criterion_value: float


def softmax_probs(n: int, alpha: float) -> np.ndarray:
    """ソフトマックス分布。α = β × logit_range。"""
    logits = np.linspace(alpha, -alpha, n)
    log_probs = logits - np.logaddexp.reduce(logits)
    return np.exp(log_probs)


def entropy_bits(probs: np.ndarray) -> float:
    """Shannon エントロピー (bits)。"""
    return -np.sum(probs * np.log2(probs + 1e-30))


def fisher_eigenvalues(probs: np.ndarray) -> np.ndarray:
    """Fisher情報行列の固有値（降順）。対角 = 1/p_i。"""
    return np.sort(1.0 / probs)[::-1]


# ==============================================================
# 1. Participation Ratio (カットオフ不要)
# ==============================================================
def d_eff_pr(eigenvalues: np.ndarray) -> float:
    """Participation Ratio = (Σλ)² / Σλ²。"""
    s1 = np.sum(eigenvalues)
    s2 = np.sum(eigenvalues**2)
    return s1**2 / s2


# ==============================================================
# 2. AIC 的次元選択 (Minka 2001 PCA version)
# ==============================================================
def d_eff_aic(eigenvalues: np.ndarray) -> int:
    """AIC 的次元選択。
    
    基本アイデア: k 次元で Fisher 行列を近似するとき、
    AIC(k) = -2 × Σᵢ₌₁ᵏ ln(λᵢ) + 2k
    → k が増えるほど data fit 改善、ペナルティ増大
    最適 k* = argmin AIC(k)
    
    ただし、Fisher 固有値が全て正の場合、
    実質的には「λ_k が exp(1) を下回ったら止める」に近い。
    """
    n = len(eigenvalues)
    best_k = 1
    best_aic = float('inf')
    
    for k in range(1, n):
        # log-likelihood 項: 上位 k 個の固有値の対数和
        log_lik = np.sum(np.log(eigenvalues[:k] + 1e-30))
        # ペナルティ
        aic = 2 * k - 2 * log_lik
        if aic < best_aic:
            best_aic = aic
            best_k = k
    
    return best_k


# ==============================================================
# 3. BIC 的次元選択
# ==============================================================
def d_eff_bic(eigenvalues: np.ndarray, n_samples: int = 100) -> int:
    """BIC 的次元選択（n_samples はサンプルサイズのアナロジー）。"""
    n = len(eigenvalues)
    best_k = 1
    best_bic = float('inf')
    
    for k in range(1, n):
        log_lik = np.sum(np.log(eigenvalues[:k] + 1e-30))
        bic = k * np.log(n_samples) - 2 * log_lik
        if bic < best_bic:
            best_bic = bic
            best_k = k
    
    return best_k


# ==============================================================
# 4. MDL 的次元選択 (Rissanen)
# ==============================================================
def d_eff_mdl(eigenvalues: np.ndarray) -> int:
    """MDL 次元選択。
    
    MDL(k) = -Σᵢ₌₁ᵏ ln(λᵢ) + k/2 × ln(Σλ)
    上位 k 個の固有値で説明し、残りはノイズとみなす。
    """
    n = len(eigenvalues)
    total = np.sum(eigenvalues)
    best_k = 1
    best_mdl = float('inf')
    
    for k in range(1, n):
        log_lik = np.sum(np.log(eigenvalues[:k] + 1e-30))
        mdl = -log_lik + (k / 2.0) * np.log(total)
        if mdl < best_mdl:
            best_mdl = mdl
            best_k = k
    
    return best_k


# ==============================================================
# 5. VFE 的次元選択 (FEP inspired)
# ==============================================================
def d_eff_vfe(eigenvalues: np.ndarray) -> int:
    """VFE (変分自由エネルギー) 的次元選択。
    
    Accuracy: 上位 k 個の固有値で説明される分散比
    Complexity: k × D_KL(posterior || prior) ≈ k/2 × ln(λ̄/λ_prior)
    
    VFE(k) = -Accuracy(k) + Complexity(k)
    k* = argmin VFE(k)
    
    FEP のバランス: 予測精度 vs モデルの単純さ
    """
    n = len(eigenvalues)
    total = np.sum(eigenvalues)
    
    # prior precision: 全固有値の幾何平均（「何も知らない」状態）
    log_geo_mean = np.mean(np.log(eigenvalues + 1e-30))
    
    best_k = 1
    best_vfe = float('inf')
    
    for k in range(1, n):
        # Accuracy: 上位 k 個の累積分散比（高いほど良い → 負にする）
        accuracy = np.sum(eigenvalues[:k]) / total
        
        # Complexity: KL divergence 項
        # 各選択された次元の固有値が prior からどれだけ離れているか
        complexity = 0.5 * np.sum(np.log(eigenvalues[:k] + 1e-30) - log_geo_mean)
        
        # VFE = -Accuracy + β_complexity × Complexity
        # β_complexity = 1 で純粋なバランス
        vfe = -accuracy + (1.0 / n) * complexity
        
        if vfe < best_vfe:
            best_vfe = vfe
            best_k = k
    
    return best_k


# ==============================================================
# 6. Elbow 法 (2次微分)
# ==============================================================
def d_eff_elbow(eigenvalues: np.ndarray) -> int:
    """固有値の対数プロットのエルボー点（2次微分最大）。"""
    log_ev = np.log(eigenvalues + 1e-30)
    if len(log_ev) < 3:
        return 1
    
    # 2次差分
    second_diff = np.diff(log_ev, n=2)
    # 最大の曲率変化点
    elbow = int(np.argmax(np.abs(second_diff))) + 1
    return max(1, min(elbow, len(eigenvalues) - 1))


# ==============================================================
# メイン分析
# ==============================================================
def run_analysis():
    print("=" * 80)
    print("Rate-Distortion 分析: カットオフ不要な有効次元の数値実験")
    print("=" * 80)
    
    n = 32
    
    # ============================================================
    # 実験 1: 各定義の d_eff を α の関数としてプロット
    # ============================================================
    print(f"\n## 実験 1: n={n} での各定義の d_eff vs α\n")
    print(f"{'α':>6} {'H(bits)':>8} {'d95%':>5} {'PR':>6} {'AIC':>5} {'BIC':>5} "
          f"{'MDL':>5} {'VFE':>5} {'Elbow':>6}")
    print("-" * 60)
    
    alphas = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0, 15.0, 20.0]
    
    for alpha in alphas:
        p = softmax_probs(n, alpha)
        h = entropy_bits(p)
        ev = fisher_eigenvalues(p)
        
        # d_eff(95%)
        cumvar = np.cumsum(ev) / np.sum(ev)
        d95 = int(np.searchsorted(cumvar, 0.95) + 1)
        
        pr = d_eff_pr(ev)
        aic = d_eff_aic(ev)
        bic = d_eff_bic(ev)
        mdl = d_eff_mdl(ev)
        vfe = d_eff_vfe(ev)
        elbow = d_eff_elbow(ev)
        
        print(f"{alpha:>6.1f} {h:>8.2f} {d95:>5} {pr:>6.1f} {aic:>5} {bic:>5} "
              f"{mdl:>5} {vfe:>5} {elbow:>6}")
    
    # ============================================================
    # 実験 2: d_eff = 7 となる α を各定義で逆算
    # ============================================================
    print(f"\n\n## 実験 2: d_eff = 7 となる α を各定義で逆算 (n={n})\n")
    print(f"{'定義':>12} {'α*':>8} {'H*(bits)':>9} {'カットオフ不要':>14}")
    print("-" * 48)
    
    # d_eff(95%) = 7
    for alpha in np.linspace(0.1, 30.0, 3000):
        p = softmax_probs(n, alpha)
        ev = fisher_eigenvalues(p)
        cumvar = np.cumsum(ev) / np.sum(ev)
        d95 = int(np.searchsorted(cumvar, 0.95) + 1)
        if d95 <= 7:
            h = entropy_bits(p)
            print(f"{'d95%':>12} {alpha:>8.3f} {h:>9.2f} {'❌':>14}")
            break
    
    # PR ≈ 7
    for alpha in np.linspace(0.1, 30.0, 3000):
        p = softmax_probs(n, alpha)
        ev = fisher_eigenvalues(p)
        pr_val = d_eff_pr(ev)
        if pr_val <= 7.0:
            h = entropy_bits(p)
            print(f"{'PR':>12} {alpha:>8.3f} {h:>9.2f} {'✅':>14}")
            break
    
    # AIC = 7
    prev_aic = n
    for alpha in np.linspace(0.1, 30.0, 3000):
        p = softmax_probs(n, alpha)
        ev = fisher_eigenvalues(p)
        aic_val = d_eff_aic(ev)
        if aic_val <= 7 and prev_aic > 7:
            h = entropy_bits(p)
            print(f"{'AIC':>12} {alpha:>8.3f} {h:>9.2f} {'✅':>14}")
            break
        prev_aic = aic_val
    
    # BIC = 7
    prev_bic = n
    for alpha in np.linspace(0.1, 30.0, 3000):
        p = softmax_probs(n, alpha)
        ev = fisher_eigenvalues(p)
        bic_val = d_eff_bic(ev)
        if bic_val <= 7 and prev_bic > 7:
            h = entropy_bits(p)
            print(f"{'BIC':>12} {alpha:>8.3f} {h:>9.2f} {'✅':>14}")
            break
        prev_bic = bic_val
    
    # MDL = 7
    prev_mdl = n
    for alpha in np.linspace(0.1, 30.0, 3000):
        p = softmax_probs(n, alpha)
        ev = fisher_eigenvalues(p)
        mdl_val = d_eff_mdl(ev)
        if mdl_val <= 7 and prev_mdl > 7:
            h = entropy_bits(p)
            print(f"{'MDL':>12} {alpha:>8.3f} {h:>9.2f} {'✅':>14}")
            break
        prev_mdl = mdl_val
    
    # VFE = 7
    prev_vfe = n
    for alpha in np.linspace(0.1, 30.0, 3000):
        p = softmax_probs(n, alpha)
        ev = fisher_eigenvalues(p)
        vfe_val = d_eff_vfe(ev)
        if vfe_val <= 7 and prev_vfe > 7:
            h = entropy_bits(p)
            print(f"{'VFE':>12} {alpha:>8.3f} {h:>9.2f} {'✅':>14}")
            break
        prev_vfe = vfe_val
    
    # ============================================================
    # 実験 3: n依存性 — 各定義の d_eff=7 となる H* は n不変か？
    # ============================================================
    print(f"\n\n## 実験 3: n依存性 — d_eff=7 の H* (bits) は n 不変か？\n")
    print(f"{'n':>6} {'d95%_H':>8} {'PR_H':>8} {'AIC_H':>8} {'BIC_H':>8} "
          f"{'MDL_H':>8} {'VFE_H':>8}")
    print("-" * 56)
    
    for n_val in [16, 32, 64, 128]:
        results = {}
        
        for method_name, method_fn in [
            ('d95%', lambda ev: int(np.searchsorted(np.cumsum(ev)/np.sum(ev), 0.95) + 1)),
            ('PR', lambda ev: int(round(d_eff_pr(ev)))),
            ('AIC', d_eff_aic),
            ('BIC', d_eff_bic),
            ('MDL', d_eff_mdl),
            ('VFE', d_eff_vfe),
        ]:
            found = False
            prev_val = n_val
            for alpha in np.linspace(0.1, 50.0, 5000):
                p = softmax_probs(n_val, alpha)
                ev = fisher_eigenvalues(p)
                val = method_fn(ev)
                if val <= 7 and prev_val > 7:
                    h = entropy_bits(p)
                    results[method_name] = h
                    found = True
                    break
                prev_val = val
            if not found:
                results[method_name] = float('nan')
        
        d95_h = results.get('d95%', float('nan'))
        pr_h = results.get('PR', float('nan'))
        aic_h = results.get('AIC', float('nan'))
        bic_h = results.get('BIC', float('nan'))
        mdl_h = results.get('MDL', float('nan'))
        vfe_h = results.get('VFE', float('nan'))
        
        print(f"{n_val:>6} {d95_h:>8.2f} {pr_h:>8.2f} {aic_h:>8.2f} {bic_h:>8.2f} "
              f"{mdl_h:>8.2f} {vfe_h:>8.2f}")
    
    # ============================================================
    # 実験 4: Rate-Distortion 関数 R(D)
    # ============================================================
    print(f"\n\n## 実験 4: Rate-Distortion 関数 (n=32)\n")
    print("Rate-Distortion: 固有値の逆水充填 (reverse water-filling)")
    print(f"{'D (歪み)':>10} {'R (レート)':>12} {'有効次元':>10}")
    print("-" * 36)
    
    n_rd = 32
    alpha_rd = 5.0  # 中程度の集中
    p_rd = softmax_probs(n_rd, alpha_rd)
    ev_rd = fisher_eigenvalues(p_rd)
    
    # 逆水充填: 歪み D に対して R(D) を計算
    # ガウスソースの R(D):
    #   R(D) = Σ max(0, 1/2 × log2(σ²_i / θ)) 
    #   ここで θ は D = Σ min(σ²_i, θ) を満たす
    # Fisher 固有値を分散と解釈して適用
    
    sigma2 = 1.0 / ev_rd  # 各方向の「分散」= 確率 p_i
    sigma2_sorted = np.sort(sigma2)[::-1]  # 降順
    
    for target_dim in [1, 2, 3, 5, 7, 10, 15, 20, 31]:
        # θ = target_dim 番目に大きい分散
        if target_dim >= len(sigma2_sorted):
            continue
        theta = sigma2_sorted[target_dim]
        D = np.sum(np.minimum(sigma2_sorted, theta))
        R = 0.5 * np.sum(np.maximum(0, np.log2(sigma2_sorted / theta)))
        print(f"{D:>10.4f} {R:>12.4f} {target_dim:>10}")
    
    print("\n\n" + "=" * 80)
    print("分析完了")
    print("=" * 80)


if __name__ == "__main__":
    run_analysis()
