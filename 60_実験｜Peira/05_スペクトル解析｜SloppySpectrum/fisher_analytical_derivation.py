#!/usr/bin/env python3
"""
β*×LR ≈ 7.73 の解析的導出を試みる。

ソフトマックス分布 p_i ∝ exp(β × l_i) (l_i ∈ [-L, L], 線形間隔) において、
Fisher 情報行列の d_eff(95%) = 7 となる条件を解析的に求める。

アプローチ:
  1. 連続極限 (n → ∞) での厳密な式を導出
  2. エントロピー H の閉じた表現を求める
  3. d_eff(95%) の条件を積分方程式として定式化
  4. α = βL の関数として解く
"""

import numpy as np


def softmax_entropy_exact(n: int, alpha: float) -> float:
    """ソフトマックス分布の Shannon エントロピー (bits)。α = β × L。"""
    logits = np.linspace(alpha, -alpha, n)
    log_probs = logits - np.logaddexp.reduce(logits)
    probs = np.exp(log_probs)
    return -np.sum(probs * log_probs) / np.log(2)


def softmax_entropy_continuum(alpha: float) -> float:
    """連続極限でのソフトマックスのエントロピー（n の寄与を除く）。
    
    連続近似:
      p(x) = (α / sinh(α)) × exp(α × x) / 2,  x ∈ [-1, 1]
    
    H_cont = -∫ p(x) ln(p(x)) dx
           = ln(2 sinh(α) / α) - α × L(α)
    
    ここで L(α) = coth(α) - 1/α (ランジュバン関数)。
    """
    if alpha < 1e-6:
        return 0.0  # ln(1) - 0 = 0
    langevin = 1.0 / np.tanh(alpha) - 1.0 / alpha
    h_nats = np.log(2.0 * np.sinh(alpha) / alpha) - alpha * langevin
    return h_nats / np.log(2)


def d_eff_95_exact(n: int, alpha: float) -> int:
    """d_eff(95%) を正確に計算。α = β × L。"""
    logits = np.linspace(alpha, -alpha, n)
    log_probs = logits - np.logaddexp.reduce(logits)
    probs = np.exp(log_probs)
    eigenvalues = np.sort(1.0 / probs)[::-1]
    cumvar = np.cumsum(eigenvalues) / np.sum(eigenvalues)
    return int(np.searchsorted(cumvar, 0.95) + 1)


def fisher_cumulative_ratio_continuum(alpha: float, fraction: float) -> float:
    """連続極限で、最大固有値側から fraction の割合の固有値の累積比を計算。
    
    Fisher eigenvalue: λ(x) = 1/p(x) ∝ exp(-α x)
    最大固有値は x = -1 (p が最小のところ)。
    
    x ∈ [-1, -1 + 2f] の固有値の累積和 / 全体
    ここで f = fraction (0 < f < 1)
    
    = ∫_{-1}^{-1+2f} exp(-αx) dx / ∫_{-1}^{1} exp(-αx) dx
    = [exp(α) - exp(α - 2αf)] / [exp(α) - exp(-α)]
    = [1 - exp(-2αf)] / [1 - exp(-2α)]
    """
    if alpha < 1e-6:
        return fraction  # 一様分布の場合
    return (1.0 - np.exp(-2.0 * alpha * fraction)) / (1.0 - np.exp(-2.0 * alpha))


def find_fraction_for_95(alpha: float) -> float:
    """連続極限で cumulative = 0.95 となる fraction を求める。"""
    if alpha < 1e-6:
        return 0.95
    # 1 - exp(-2αf) = 0.95 × (1 - exp(-2α))
    rhs = 0.95 * (1.0 - np.exp(-2.0 * alpha))
    # exp(-2αf) = 1 - rhs
    if 1.0 - rhs <= 0:
        return 1.0
    f = -np.log(1.0 - rhs) / (2.0 * alpha)
    return min(f, 1.0)


def run_analytical_derivation():
    print("=" * 80)
    print("β*×LR ≈ 7.73 の解析的導出")
    print("=" * 80)

    # ============================================================
    # ステップ 1: 連続極限の解析式の検証
    # ============================================================
    print("\n## ステップ 1: 連続極限のエントロピー式 vs 離散計算\n")
    print(f"{'α=βL':>8} {'H_disc(n=256)':>14} {'H_cont+log₂n':>14} {'差':>8}")
    print("-" * 48)

    for alpha in [1.0, 3.0, 5.0, 7.73, 10.0, 15.0]:
        h_disc = softmax_entropy_exact(256, alpha)
        h_cont = softmax_entropy_continuum(alpha)  # n=1 の寄与のみ
        h_cont_with_n = h_cont + np.log2(256)  # log₂(n) を加算
        # 実際には離散の場合は logits の間隔も影響する
        print(f"{alpha:>8.2f} {h_disc:>14.4f} {h_cont_with_n:>14.4f} {h_disc - h_cont_with_n:>8.4f}")

    # ============================================================
    # ステップ 2: 連続極限での fraction → d_eff の対応
    # ============================================================
    print(f"\n\n## ステップ 2: α = βL = 7.73 での連続極限 fraction\n")
    alpha_star = 7.73
    f95 = find_fraction_for_95(alpha_star)
    print(f"cumulative = 0.95 となる固有値の fraction f = {f95:.6f}")
    print(f"→ 連続極限での d_eff = f × n = {f95:.6f} × n")
    print(f"   n=32 の場合: d_eff = {f95 * 32:.2f}")
    print(f"   n=64 の場合: d_eff = {f95 * 64:.2f}")
    print(f"   n=128 の場合: d_eff = {f95 * 128:.2f}")

    # ============================================================
    # ステップ 3: d_eff = 7 の条件 — f × n = 7 → f = 7/n
    # ============================================================
    print(f"\n\n## ステップ 3: d_eff = 7 の解析的条件\n")
    print("条件: f × n = 7 (離散の d_eff = 7 を連続の fraction で近似)")
    print(f"{'n':>6} {'f=7/n':>8} {'α (=βL) 解析':>14} {'α 数値':>8} {'H (bits)':>9}")
    print("-" * 50)

    for n in [16, 32, 64, 128, 256]:
        f_target = 7.0 / n
        # 解析式: 1 - exp(-2αf) = 0.95 × (1 - exp(-2α))
        # これを α について解く
        # f_target = -ln(1 - 0.95(1-exp(-2α))) / (2α)
        # これは陰関数方程式なので数値的に解く
        
        from scipy.optimize import brentq
        
        def equation(alpha):
            f = find_fraction_for_95(alpha)
            return f - f_target
        
        try:
            alpha_sol = brentq(equation, 0.1, 100.0)
            h = softmax_entropy_exact(n, alpha_sol)
            print(f"{n:>6} {f_target:>8.4f} {alpha_sol:>14.4f} {'—':>8} {h:>9.2f}")
        except Exception:
            print(f"{n:>6} {f_target:>8.4f} {'N/A':>14} {'—':>8} {'N/A':>9}")

    # ============================================================
    # ステップ 4: 閉じた形の解析式を探る
    # ============================================================
    print(f"\n\n## ステップ 4: 閉じた形の探索\n")
    print("cumulative 条件: 1 - exp(-2αf) = 0.95 × (1 - exp(-2α))")
    print("離散条件: f = k/n (k = d_eff, n = 状態数)")
    print()
    print("α が大きいとき (exp(-2α) ≈ 0):")
    print("  1 - exp(-2αf) ≈ 0.95")
    print("  exp(-2αf) ≈ 0.05")
    print("  2αf ≈ -ln(0.05) = ln(20) ≈ 3.00")
    print("  αf ≈ 1.50")
    print()
    print("d_eff = 7 なら f = 7/n:")
    print("  α × 7/n ≈ 1.50")
    print("  α ≈ 1.50 × n/7 = 0.2143 × n")
    print()
    print("検証:")
    print(f"{'n':>6} {'α = 0.2143n':>12} {'α 実測':>8} {'比率':>8}")
    print("-" * 38)

    for n in [16, 32, 64, 128, 256]:
        alpha_pred = 0.2143 * n
        # 実測
        try:
            alpha_actual = brentq(equation, 0.1, 100.0)
        except Exception:
            alpha_actual = float('nan')
        
        ratio = alpha_actual / alpha_pred if not np.isnan(alpha_actual) else float('nan')
        print(f"{n:>6} {alpha_pred:>12.2f} {alpha_actual:>8.2f} {ratio:>8.4f}")

    # ============================================================
    # ステップ 5: n → ∞ での厳密な α* と H* の導出
    # ============================================================
    print(f"\n\n## ステップ 5: n → ∞ での漸近解\n")
    print("大 n 近似: α* ≈ ln(20)/2 × n/k = (ln 20 / 2) × (n / 7)")
    print(f"ln(20)/2 = {np.log(20)/2:.6f}")
    print()
    print("しかし元のパラメータは β と L であり α = βL。")
    print("logit 範囲 L は固定で n → ∞ とすると、β* = α*/L → ∞。")
    print("これは n → ∞ ではより鋭い分布が必要になることを意味する。")
    print()
    print("逆に n が有限のとき:")
    print("  β*×L = α* = (ln 20 / 2) × (n / d_eff)")
    print(f"  n=32, d_eff=7: α* = {np.log(20)/2 * 32/7:.4f}")
    print(f"  実測: α* = 7.73")
    print(f"  ln(20)/2 × 32/7 = {np.log(20)/2 * 32/7:.4f}")
    print()
    
    # α* = (ln(1/0.05)) / 2 × (n / k) = ln(20)/2 × n/k
    # n=32, k=7: α* = 1.4979 × 4.571 = 6.848
    # ≠ 7.73 — 近似が粗い

    # 厳密解: 1 - exp(-2α × k/n) = 0.95 × (1 - exp(-2α))
    # n=32, k=7: exp(-14α/32) = 1 - 0.95(1 - exp(-2α))
    # = 0.05 + 0.95 × exp(-2α)
    print("厳密方程式 (n=32, k=7):")
    print("  exp(-7α/16) = 0.05 + 0.95 × exp(-2α)")
    print()
    
    # 数値解
    def exact_eq_32_7(alpha):
        lhs = np.exp(-7.0 * alpha / 16.0)
        rhs = 0.05 + 0.95 * np.exp(-2.0 * alpha)
        return lhs - rhs
    
    from scipy.optimize import brentq
    alpha_exact = brentq(exact_eq_32_7, 0.1, 50.0)
    print(f"数値解: α* = {alpha_exact:.6f}")
    print(f"→ β* × L ≈ {alpha_exact:.2f}")
    print()
    
    # H at this α
    h = softmax_entropy_exact(32, alpha_exact)
    print(f"このときの H = {h:.4f} bits")
    print(f"2^H = {2**h:.4f}")
    print()
    
    # 一般解: exp(-kα/n') = 0.05 + 0.95 × exp(-2α)
    # ここで n' = n/2 (logits が [-L, L] で n 点 → 半区間に n/2 点)
    # 実際は n' はパラメータ空間の次元 = n-1 (制約 Σp=1)
    
    print("一般的な閉じた式:")
    print("  exp(-k α / (n/2)) = 0.05 + 0.95 × exp(-2α)")
    print()
    print("  k=7 のとき: exp(-14α/n) = 0.05 + 0.95 × exp(-2α)")
    print()
    print("各 n での α* (β*L):")
    print(f"{'n':>6} {'α* (厳密)':>12} {'H* (bits)':>10} {'2^H*':>8}")
    print("-" * 40)
    
    for n in [8, 16, 32, 64, 128, 256, 512, 1024]:
        k = 7
        def eq(alpha):
            return np.exp(-k * alpha / (n / 2.0)) - 0.05 - 0.95 * np.exp(-2.0 * alpha)
        
        try:
            a = brentq(eq, 0.01, 200.0)
            h = softmax_entropy_exact(min(n, 256), a)  # n>256 は近似
            print(f"{n:>6} {a:>12.4f} {h:>10.4f} {2**h:>8.2f}")
        except Exception:
            print(f"{n:>6} {'N/A':>12}")


if __name__ == "__main__":
    run_analytical_derivation()
