#!/usr/bin/env python3
"""
仮説 C: Complexity 項による位相的相転移 — BIC 型 VFE
/ske >> /pei の /pei 段階

VFE(k) = Complexity(k) - Accuracy(k)

Accuracy(k):
  k 個の独立な制約（十分統計量）があるとき、
  生成モデルの対数尤度の期待値。
  k が増えると対数尤度は向上するが、限界効用は逓減する。
  → Accuracy(k) = c * log(1 + k)  (上に凸の単調増加)

Complexity(k):
  BIC 近似: (k/2) * log(n_data)
  MDL 近似: k * log(n_states) / 2
  AIC: k
  → Complexity(k) = (k/2) * log(n)

VFE(k) = (k/2) * log(n) - c * log(1 + k)

最適 k*: dVFE/dk = 0
  log(n)/2 - c / (1 + k) = 0
  c / (1 + k) = log(n) / 2
  1 + k = 2c / log(n)
  k* = 2c/log(n) - 1

k* = 7 となる条件:
  8 = 2c / log(n)
  c = 4 * log(n)

つまり c/log(n) = 4 のとき k* = 7。
c は環境の複雑度、n は有効データ数。
"""

import numpy as np

def optimal_k_bic(c, n):
    """BIC 型の VFE で最適な制約数 k* を求める。"""
    if n <= 1:
        return float('inf')
    return 2 * c / np.log(n) - 1

def vfe_bic(k, c, n):
    """VFE(k) = (k/2)*log(n) - c*log(1+k)"""
    return (k / 2) * np.log(n) - c * np.log(1 + k)

print("=" * 60)
print("仮説 C: BIC 型 VFE による最適制約数 k*")
print("=" * 60)

print("\n## 解析解:")
print("k* = 2c / log(n) - 1")
print("k* = 7 ⟺ c = 4 log(n)")
print()

print("## 1. k*=7 を実現する c と n の関係\n")
print(f"{'n (data)':>10} {'log(n)':>8} {'c (=4 log n)':>12} {'k* (検算)':>10}")
print("-" * 45)
for n in [10, 50, 100, 500, 1000, 10000, 100000]:
    c = 4 * np.log(n)
    k_star = optimal_k_bic(c, n)
    print(f"{n:>10} {np.log(n):>8.2f} {c:>12.2f} {k_star:>10.1f}")

print("\n## 2. c/log(n) = 4 の物理的意味\n")
print("c = 環境からの情報ゲイン（1制約あたりの対数尤度改善の上限）")
print("log(n) = データ量のスケール")
print("c/log(n) = 4 は「環境の複雑度がデータ量の対数の4倍」を意味する")
print()
print("これは:")
print("  - 環境に「それなりの構造」がある（c が大きすぎない）")
print("  - データが「それなりにある」（n が大きすぎない）")
print("  - その中間地帯で k* = 7 が生じる")

# 非線形 Accuracy の場合
print("\n\n## 3. 他の Accuracy 関数での k*\n")

print("### Model 1: Accuracy = c * log(1 + k)")
print("  k* = 2c/log(n) - 1\n")

print("### Model 2: Accuracy = c * sqrt(k)")
print("  dA/dk = c/(2*sqrt(k))")
print("  log(n)/2 = c/(2*sqrt(k))")
print("  sqrt(k) = c/log(n)")
print("  k* = (c/log(n))^2\n")
print(f"{'c/log(n)':>10} {'k* (M1)':>8} {'k* (M2)':>8}")
print("-" * 30)
for ratio in [2, 3, 4, 5, 6, 7, 8]:
    k1 = 2 * ratio - 1
    k2 = ratio ** 2
    print(f"{ratio:>10} {k1:>8} {k2:>8}")

print("\n### Model 3: Accuracy = c * k^α (α < 1)")
print("  dA/dk = c*α*k^(α-1)")
print("  log(n)/2 = c*α*k^(α-1)")
print("  k^(1-α) = 2cα/log(n)")
print("  k* = (2cα/log(n))^(1/(1-α))\n")
print(f"{'α':>5} {'c/log(n)=4':>12} {'k*':>8}")
print("-" * 30)
for alpha in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    ratio = 4
    k_star = (2 * ratio * alpha) ** (1 / (1 - alpha))
    print(f"{alpha:>5.1f} {ratio:>12} {k_star:>8.1f}")

# FEP 固有の考察
print("\n\n## 4. FEP の POMDP テンソル分解からの制約\n")
print("POMDP の十分統計量:")
print("  T1: 状態推定 E[s] → 位置 (Value: Internal/Ambient)")
print("  T2: 行動選択 π(a) → 方策 (Function: Explore/Exploit)")
print("  T3: 精度推定 ω  → 確信度 (Precision: Certain/Uncertain)")
print("  T4: スケール s_h → 階層 (Scale: Micro/Macro)")
print("  T5: 情動推定 v  → 評価 (Valence: +/-)")
print("  T6: 時間推定 τ  → 時間 (Temporality: Past/Future)")
print("  T0: 流れ     F  → 基底 (Flow)")
print()
print("これらが independence を持つとすると、")
print("MaxEnt の制約数 k = 7 (= 6 修飾座標 + 1 基底 Flow)")
print()
print("BIC 型 VFE: k* = 7 ⟺ c/log(n) = 4")
print()
print("→ 結論: k*=7 は「環境構造 c と観測量 n の比率が")
print("   特定の範囲にある」場合に成立する。")
print("   c と n は環境に依存するが、HGK の 7 座標が")
print("   POMDP の十分統計量の自然な分解であるならば、")
print("   情報幾何学側からの k=7 は「制約の数」として")
print("   操作的型分析と一致する。")
print()
print("⚠️ ただし c/log(n)=4 の条件は依然として環境依存であり、")
print("   これだけでは「なぜ 7」かの完全な答えにはならない。")
print("   「7 つの十分統計量が独立である」ことこそが核心。")
