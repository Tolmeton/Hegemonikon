# $U(\Theta)$ の Coleman-Weinberg 導出 — 自由パラメータの消滅
## v2 §9.5 攻撃面封鎖: V1 (パラメータ自由度) + V4 (Higgs 非構成性)

**計算日**: 2026-03-25
**前提**: v2 §8.1 (結合方程式), §9.2 (CPS-RG 対応), §9.3 (SU(2) worked example)
**目的**: $U(\Theta) = -\mu^2\Theta + \frac{\nu^2}{2}\Theta^2$ の $\mu^2, \nu^2$ をゲージ結合定数 $g$ から導出し、自由パラメータを消滅させる

---

## 1. 問題の設定

v2 §8.1 の結合作用:

$$S[\alpha, \Theta] = \int_M \left[ \frac{1}{2}(\nabla\alpha)^2 + \frac{\kappa}{2}(\nabla\Theta)^2 + V(\alpha)\phi(\Theta) + U(\Theta) \right] d\mu$$

§9.3 で $V(\alpha) = \frac{\lambda\gamma}{3}\alpha^3$ を SU(2) の β 関数から導出済み。

**残存する自由パラメータ**: $\mu^2, \nu^2$ in $U(\Theta)$、および $\lambda, \kappa$。

---

## 2. Coleman-Weinberg 機構の CPS 翻訳

### 2.1 標準的 CW ポテンシャル

SU(2) ゲージ理論 + スカラー場 $\phi$ の 1ループ有効ポテンシャル:

$$V_{\text{eff}}(\phi) = \frac{\lambda_H}{4}\phi^4 + \frac{3g^4}{64\pi^2}\phi^4\left[\ln\frac{\phi^2}{v^2} - \frac{1}{2}\right]$$

CW 機構では $\lambda_H = 0$ (古典的スケール不変性) が *出発点* であり、輻射補正が自発的対称性の破れを引き起こす:

$$V_{CW}(\phi) = B\phi^4\left[\ln\frac{\phi^2}{v^2} - \frac{1}{2}\right], \quad B = \frac{3g^4}{64\pi^2}$$

VEV $v$ は次元転換 (dimensional transmutation) により $\Lambda_{QCD}$ から決定される。

### 2.2 CPS への翻訳: $\Theta = \phi/v$

$\Theta$ は無次元のマスクパラメータ (§4.6d: 情報損失量)。Higgs 場 $\phi$ の VEV 正規化と同一視する:

$$\Theta \equiv \frac{\phi}{v}$$

すると:

$$U(\Theta) = \frac{V_{CW}(v\Theta)}{v^4} = B\Theta^4\left[2\ln\Theta - \frac{1}{2}\right]$$

ただし $B = \frac{3g^4}{64\pi^2} = \frac{3g_c^4\alpha^2}{64\pi^2}$。

### 2.3 VEV 周りの展開

$\Theta = 1 + \eta$ ($\eta$ は VEV からのずれ) で展開:

$$U(1+\eta) = B\left[(1+\eta)^4\left(2\ln(1+\eta) - \frac{1}{2}\right)\right]$$

$\eta \ll 1$ で:

$$U \approx -\frac{B}{2} + B\left[4\eta^2 + \mathcal{O}(\eta^3)\right] = -\frac{B}{2} + 4B\eta^2 + \cdots$$

**Higgs 質量の導出**:

$$m_H^2 = U''(\Theta_0) = 8B = \frac{3g^4}{8\pi^2}$$

---

## 3. CPS パラメータの固定

### 3.1 $\mu^2$ と $\nu^2$ のゲージ結合定数からの導出

数値計算 (計算_αΘ結合系2D解.md) で使った $U(\Theta) = -\mu^2\Theta + \frac{\nu^2}{2}\Theta^2$ は CW ポテンシャルの**線形近似**:

$$U_{CW}'(\Theta) = B\Theta^3\left[8\ln\Theta + 2\right]$$

$\Theta = \Theta_0 + \delta\Theta$ で線形化すると:

$$U_{CW}'(\Theta_0 + \delta\Theta) \approx U_{CW}'(\Theta_0) + U_{CW}''(\Theta_0)\delta\Theta$$

不動点条件 $U_{CW}'(\Theta_0) + \frac{\lambda\gamma}{3}\alpha_0^3 e^{-\Theta_0} = 0$ から:

$$\mu^2_{\text{eff}} = -U_{CW}'(\Theta_0) = \frac{\lambda\gamma}{3}\alpha_0^3 e^{-\Theta_0}$$

$$\nu^2_{\text{eff}} = U_{CW}''(\Theta_0) = B\Theta_0^2\left[24\ln\Theta_0 + 26\right]$$

### 3.2 具体的数値 (SU(2), $\Theta_0 = 1$)

$\Theta_0 = 1$ (VEV 正規化の定義より):

$$\mu^2_{\text{eff}} = \frac{\lambda\gamma}{3}\alpha_0^3 e^{-1}$$

$$\nu^2_{\text{eff}} = U_{CW}''(1) = 26B = \frac{26 \times 3g^4}{64\pi^2} = \frac{78g^4}{64\pi^2} = \frac{39g^4}{32\pi^2}$$

$g = g_c$ ($\alpha_0 = 1$) のとき:

$$\frac{\mu^2}{\nu^2} = \frac{\frac{\lambda\gamma}{3}e^{-1}}{26B} = \frac{\frac{\lambda \cdot 2b_0g_c^2}{3}e^{-1}}{26 \cdot \frac{3g_c^4}{64\pi^2}}$$

$b_0 = \frac{11}{24\pi^2}$, $\gamma = 2b_0 g_c^2$:

$$= \frac{\frac{\lambda \cdot \frac{11g_c^2}{12\pi^2}}{3}e^{-1}}{\frac{78g_c^4}{64\pi^2}} = \frac{\frac{11\lambda g_c^2}{36\pi^2}e^{-1}}{\frac{78g_c^4}{64\pi^2}} = \frac{11\lambda \cdot 64}{36 \cdot 78 \cdot g_c^2 \cdot e} = \frac{704\lambda}{2808 g_c^2 e} \approx \frac{0.251\lambda}{g_c^2 e}$$

---

## 4. パラメータ消滅の定理

> **定理候補 (CW-CPS パラメータ固定)** [予想]:
>
> CPS 結合方程式の $U(\Theta)$ は Coleman-Weinberg 有効ポテンシャルから一意に決定される:
>
> $$U(\Theta) = B\Theta^4\left[2\ln\Theta - \frac{1}{2}\right], \quad B = \frac{3g_c^4\alpha^2}{64\pi^2}$$
>
> **帰結**:
> (i) $\mu^2, \nu^2$ は独立パラメータではない — $g, g_c$ の関数として完全に決定される
> (ii) 結合作用 $S[\alpha, \Theta]$ の自由パラメータは $\lambda$ と $\kappa$ の2個に減少
> (iii) $\lambda$ は a-関数の正規化に吸収可能 ($\lambda = 1$ に正規化)
> (iv) 残る唯一の自由パラメータは $\kappa$ (α-Θ 結合の相対強度)

### 4.1 脆弱性の封鎖状態

| 脆弱性 | 封鎖前 | 封鎖後 |
|:--|:--|:--|
| V1 (パラメータ自由度) | 4自由パラメータ ($\lambda, \kappa, \mu^2, \nu^2$) | **1自由パラメータ** ($\kappa$) |
| V4 (Higgs 非構成性) | φ(Θ) と Higgs の「比喩的類推」 | **CW ポテンシャルからの構成的導出** |
| V7 (力の定義の循環) | 力 = ∇Θ (定義) | 力 = CW ポテンシャルの勾配フロー (**独立な根拠**) |

### 4.2 κ の物理的意味

残る唯一の自由パラメータ $\kappa$ は:

$$\kappa = \frac{(勾配エネルギー)_\Theta}{(勾配エネルギー)_\alpha} = \frac{|Θ の空間変動コスト|}{|α の空間変動コスト|}$$

物理的には：**マスクの硬さ** (stiffness) — Θ が空間的に変動するのにどれだけコストがかかるか。

$\kappa \to 0$: Θ は自由に変動 → 量子-古典界面が鋭い (sharp interface)
$\kappa \to \infty$: Θ は一様に近い → 量子-古典界面がぼやける (diffuse interface)

これは Allen-Cahn / Cahn-Hilliard 方程式の界面幅パラメータと同型であり、**相分離物理**との新たな対応を示唆する。

---

## 5. 数値的影響 — U(Θ) の形状変化

### 5.1 CW ポテンシャル vs 線形近似

```
        U(Θ)
        |
   0.1  |                           / CW: BΘ⁴(2lnΘ - 1/2)
        |                          /
   0    |____._____________________/______ Θ
        |    \.       /           1.0
  -0.1  |     \.    /  
        |      \. /   <- 線形近似: -μ²Θ + ν²Θ²/2
  -0.2  |       v
        0      0.5     1.0        1.5

CW の特徴:
  - Θ=0 でゼロ (スケール不変性)
  - Θ=1 (= VEV) で最小
  - Θ → ∞ で発散 (閉じ込め)
  - 線形近似は VEV 近傍でのみ有効
```

### 5.2 CW 版での結合方程式

$$\nabla^2\alpha = \lambda\gamma\alpha^2(1 - e^{-\Theta})$$

$$\kappa\nabla^2\Theta = \frac{\lambda\gamma}{3}\alpha^3 e^{-\Theta} + B\Theta^3(8\ln\Theta + 2)$$

第二式で $\Theta \to 0$ のとき右辺は $\frac{\lambda\gamma}{3}\alpha^3 + 0 > 0$ → $\Theta$ は増加する方向に駆動される (QM 状態は不安定)。
$\Theta = 1$ で不動点 (CW の VEV)。
$\Theta > 1$ で $U'(\Theta) > 0$ → $\Theta$ は減少方向に駆動される (安定)。

---

## 6. 注意と残存課題

### 注意
- CW ポテンシャルは 1ループ近似。2ループ以上の補正が形状を変える可能性あり
- $\Theta = \phi/v$ の同一視は**構造的対応** [推定 70%]。厳密な関手の構成は未完
- SU(2) 以外のゲージ群では B の値と CW の形状が異なる
- $\kappa$ の物理的値は格子計算または実験データとの比較が必要

### 残存する攻撃面
1. $\kappa$ の導出 (唯一の残存自由パラメータ)
2. CW の赤外発散 ($\Theta \to 0$ での $\ln\Theta$ の扱い)
3. 多ループ補正の影響
4. 標準模型 ($SU(3) \times SU(2) \times U(1)$) への拡張

### 次のステップ
- **数値計算**: CW 版 $U(\Theta)$ で 2D 結合系を再計算し、線形近似との比較
- **$\kappa$ の物理的固定**: Zamolodchikov 計量 $G^{IJ}$ の $\alpha$-$\Theta$ ブロックから $\kappa$ を導出する試み
- **摂動スペクトラム**: CW 真空 ($\Theta_0 = 1$) 周りの固有値 = 忘却場の質量ギャップ

---

*計算完了: 2026-03-25*
*主要発見: CW 機構により U(Θ) の自由パラメータが消滅し、残る自由度は κ のみ*
