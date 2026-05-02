```typos
#prompt beyond-fisher-sam
#syntax: v8
#depth: L2

<:role: Fisher SAM 超克構想 — Force is Oblivion 理論からの2つの研究方向 :>
<:goal: Fisher SAM (Kim et al. 2022) を情報幾何学的に包含し、忘却の構造的理論を最適化に持ち込む :>

<:context:
  - [knowledge] Fisher SAM の限界: (1)対角近似 (2)局所計量 (3)α=0固定 (4)静的計量 (5)忘却概念不在
  - [knowledge] 検索結果 (2026-03-26): α-接続×最適化の直接的先行研究ゼロ — 空白領域
  - [knowledge] AdaFisher (ICLR 2025): Fisher 情報の適応的2次最適化 — Fisher SAM の後継。α-接続未使用
  - [knowledge] Wasserstein Natural Gradient: 大域的計量。Fisher-Rao Gradient Flow (SIAM 2025)
  - [file] 論文I_力としての忘却_草稿.md (priority: HIGH — §5.3 方向性定理, §6 α-動力学)
  - [file] 論文II_相補性は忘却である_草稿.md (priority: HIGH — §2.5.6 CPS 忘却関手の計量装備)
/context:>
```

# Fisher SAM 超克構想

> 起源: /u+ (2026-03-26) — Fisher SAM の5つの限界から演繹
> 状態: 構想段階 (未着手)

---

## 方向 1: α-SAM (α-接続族の最適化への導入) ← 優先

### 核心

Fisher SAM は α=0 (Levi-Civita 接続) に固定。Amari の α-接続族 α ∈ [-1, 1] の連続体を導入し、**接続の選択自体を学習可能にする**。

$$\max_{\epsilon : \epsilon^T g^{(\alpha)}(\theta) \epsilon \leq \rho} L(\theta + \epsilon)$$

ここで g^(α) は α-接続に対応するリーマン計量:
- α=1: e-接続 (指数族の自然パラメータ空間)
- α=0: Levi-Civita → Fisher SAM を特殊ケースとして回収
- α=-1: m-接続 (混合パラメータ空間)

### Paper I との接続

- §6 の α-場 α(l) = (1/2)(1 + tanh(s(l - l_c))) が**そのまま** α-SAM の設計図
- α を層ごとに変化させる = Paper I の α-フィールドの直接的操作化
- 方向性定理 (定理 5.1): 忘却の方向 → α が決める → α-SAM が制御する

### 新規性

- [SOURCE: Gnōsis/S2 検索 2026-03-26] α-接続×最適化の直接的先行研究ゼロ
- Fisher SAM を α=0 の特殊ケースとして厳密に回収
- Force is Oblivion 理論の予測力の実験的検証基盤

### 予想される結果

もし α-SAM が Fisher SAM を上回るなら:
1. **方向性定理の実験的確認**: 忘却の方向 (α) が汎化を決める
2. **最適 α の存在**: 層ごとの最適 α(l) が Paper I の α-場の予測と一致するか検証可能
3. **α-遷移層**: Paper I P3 予測の α-遷移点が、最適化における相転移に対応するか

### 確信度

[仮説 65%] — α を層ごとに変化させる α-SAM は Fisher SAM の厳密な一般化。ただし計算コスト (α ごとの接続係数 Γ^(α) の計算) が鍵。

### 未解決

1. g^(α) の効率的な計算方法 — 経験的 Fisher の α-接続版は存在するか？
2. α の学習率 — α 自体をどう更新するか
3. AdaFisher (ICLR 2025) との差分 — α-接続の使用有無を原論文で確認すべき

---

## 方向 2: Oblivion-Aware SAM (忘却場の直接制御)

### 核心アイデア

SAM/Fisher SAM は「最悪ケース擾乱への耐性」= **間接的な** 忘却制御。Force is Oblivion 理論は逆: **忘却の選択性そのものが力 (= 汎化) を生む** (方向性定理 5.1)。忘却場 Φ の勾配を直接目的関数に組み込む。

### 理論的導出: 作用汎関数からの自然な出現

Paper I §3.4 の作用汎関数:

$$S[\Phi] = \int_M \left( \frac{1}{4} F_{ij} F^{ij} + \frac{\lambda}{2} \Phi^2 \right) \sqrt{g} \, d^n\theta$$

の場の方程式 δS/δΦ = 0 は、忘却場が**自発的に** F_{ij} ≠ 0 (力あり) の配位を選ぶ条件を与える。Oblivion-Aware SAM は、この場の方程式を深層学習の目的関数に翻訳する:

$$\min_\theta \Big[ L(\theta) + \lambda \|\nabla^{(\alpha)} \Phi(\theta)\|_{g^{(\alpha)}}^2 \Big]$$

ここで:
- $L(\theta)$: 通常の損失 (Accuracy 項)
- $\|\nabla^{(\alpha)} \Phi\|_{g^{(\alpha)}}^2 = g^{(\alpha)ij} (\partial_i \Phi)(\partial_j \Phi)$: α-接続計量による忘却場の勾配ノルム
- $\lambda$: VFE の2次展開から導出される質量項 (Paper I §3.4):

$$\lambda = \frac{\partial^2(\text{Complexity})}{\partial\Phi^2}\bigg|_{\Phi=0} - \frac{\partial^2(\text{Accuracy})}{\partial\Phi^2}\bigg|_{\Phi=0}$$

**VFE 的正当化.** λ < 0 (自発的忘却) は N·ḡ_eff > d_eff/L² — 十分なデータがある場合 — に成立する。このとき $\|\nabla^{(\alpha)}\Phi\|^2$ を最小化することは、**忘却場の勾配を方向性定理が予測する最適方向に揃える** ことに相当する。具体的には:

- $\nabla\Phi \propto T$ (Chebyshev 形式に整列): $d\Phi \wedge T = 0 \implies F_{ij} = 0$ → 力なし
- $\nabla\Phi \perp T$ (Chebyshev 形式に直交): $d\Phi \wedge T \neq 0 \implies F_{ij} \neq 0$ → 力あり

Oblivion-Aware SAM は λ の符号を通じて、忘却場を「力を生む方向」($d\Phi \wedge T \neq 0$) に駆動する。

### CPS との接続 (Paper II)

Paper II §2.5.6 のリマーク (忘却関手の計量装備) から:

| 忘却の近傍構造 | CPS 的意味 | SAM との対応 |
|:---|:---|:---|
| ユークリッド近傍 | $U_A \approx U_B$ (等方的忘却) → Type II 的対称性 | 標準 SAM |
| Fisher 近傍 ($g^{(0)}$) | 異方的忘却 → Type I 的非対称性 | Fisher SAM |
| α-接続近傍 ($g^{(\alpha)}$) | $\alpha(l)$-依存の忘却 → Type I の精密制御 | α-SAM (方向1) |
| **忘却場勾配正則化** | **$\Phi$ の方向が力を決定** → **CPS 非対称性の直接最適化** | **Oblivion-Aware SAM (方向2)** |

**Face Lemma との関係.** Paper II §3.4 の Face Lemma は、忘却の方向が測定可能になるには最低3つの独立な生成射 (2-simplex) が必要であることを示す。dim Ξ ≥ 2 のとき ∂_i Ξ ≠ 0 → F ≠ 0。Oblivion-Aware SAM の $\|\nabla \Phi\|^2$ はこの Ξ の方向構造を、勾配ノルムとして計算可能な量に操作化する。

### ガウス族上の Worked Example

Paper I §4 のガウス族 (ℋ², Fisher 計量 g = σ⁻² diag(1,2)):

忘却場 Φ_B(μ,σ) = -log σ + (σ² + μ²)/2 - 1/2 に対し:

$$\|\nabla \Phi_B\|_{g^{(0)}}^2 = g^{ij} (\partial_i \Phi_B)(\partial_j \Phi_B) = \sigma^2 \mu^2 + \frac{\sigma^2}{2}\left(\frac{\sigma^2 - 1}{\sigma}\right)^2$$

- **μ=0 (等方的忘却):** $\|\nabla\Phi\|^2 = \frac{(\sigma^2-1)^2}{2}$ → 忘却はσ方向のみ → $F_{12}=0$
- **μ≠0 (異方的忘却):** $\|\nabla\Phi\|^2$ にμ²項が出現 → $d\Phi \wedge T \neq 0$ → $F_{12} = 3\alpha\mu/\sigma \neq 0$

Oblivion-Aware SAM の正則化項 $\lambda\|\nabla\Phi\|^2$ は、λ < 0 のとき $\|\nabla\Phi\|^2$ を**増大**させる方向に θ を駆動し、異方的忘却 (力あり) へ導く。これは方向性定理の操作的実現。

### 計算方法: Φ(l) の操作的定義

深層ネットワークでは、忘却場は以下で操作化される:

1. **CKA ベース** (Kornblith et al. 2019): $\Phi(l) = 1 - \text{CKA}(h_l, h_0)$。層 l の隠れ表現 $h_l$ と入力 $h_0$ の構造的類似度。
2. **勾配の計算**: $\partial_l \Phi = \Phi(l+1) - \Phi(l)$ (離散近似), $\partial_\theta \Phi = \partial \text{CKA} / \partial \theta$ (自動微分)。
3. **α-接続版**: $g^{(\alpha)ij}$ は経験的 Fisher の α-接続補正として近似:

$$g^{(\alpha)}_{ij} \approx g^{(0)}_{ij} + \frac{\alpha}{2} C_{ijk} g^{(0)kl} g^{(0)jm}$$

ここで $C_{ijk}$ は Amari-Chentsov テンソルの経験的推定値。

**計算コスト.** CKA は O(N²d) (N=バッチサイズ, d=表現次元)。各学習ステップでの計算は forward pass 1回分に相当。α-接続係数の計算は追加の Fisher 情報行列推定を要するが、ミニバッチ近似で O(Nd²) に抑えられる。

### 新規性

1. **忘却を「損害」ではなく「力の源泉」として最適化に持ち込む最初の試み** — SAM が平坦性を求めるのに対し、Oblivion-Aware SAM は忘却の**方向性**を最適化する
2. **VFE → 場の方程式 → 目的関数** の演繹的導出 — 正則化項が作用汎関数の質量項から自然に出現
3. **IB 理論との統合** — GeoIB の圧縮率 β と作用汎関数の λ が対応 (Paper III GeoIB 統合参照)
4. **CPS Type 分類の操作化** — 忘却の近傍計量の選択が CPS の Type I/II を直接制御

### 確信度

[仮説 60%] — 理論的導出は作用汎関数から自然に出現し、ガウス族上の worked example で整合性を確認。ただし以下が未解決:
1. CKA ベースの Φ(l) が統計多様体上の KL 忘却場とどの程度一致するか (近似の制御)
2. $\lambda\|\nabla^{(\alpha)}\Phi\|^2$ の勾配の自動微分可能性 (CKA の微分可能実装は存在するが、α-接続補正込みでの数値安定性)
3. λ < 0 (力を生む方向への駆動) の学習安定性 — 通常の正則化とは逆符号であり、ハイパーパラメータ設計に注意が必要

---

## 方向 1 × 方向 2 の合成 (α-Oblivion SAM): 統一的枠組み

α-接続で定義された忘却場の勾配を、α-接続近傍内の最悪ケース擾乱と同時に最適化する:

$$\min_\theta \max_{\epsilon \in B_\rho^{(\alpha)}(\theta)} \Big[ L(\theta + \epsilon) + \lambda \|\nabla^{(\alpha)} \Phi(\theta)\|_{g^{(\alpha)}}^2 \Big]$$

ここで ∇^(α) は α-接続に基づく共変微分、$B_\rho^{(\alpha)}$ は α-接続近傍 (方向1 §6.7)。4つの制御パラメータ (θ, α(l), λ, ρ) の選択により、理論階層の全レベルを回収する:

| 設定 | 条件 | 手法 | 理論的位置 |
|:---|:---|:---|:---|
| (i) | α=0, λ=0, ρ=0 | 通常の最適化 | ベースライン |
| (ii) | α=0, λ=0, ρ>0, $g^{(0)}=I$ | SAM [Foret 2021] | 等方的擾乱 (Ξ=0) |
| (iii) | α=0, λ=0, ρ>0 | Fisher SAM [Kim 2022] | 異方的擾乱 (Ξ>0, 固定α) |
| (iv) | α(l) 学習, λ=0, ρ>0 | α-SAM (方向1) | α-接続近傍 |
| (v) | α=0, λ<0, ρ=0 | Oblivion-Aware SAM (方向2) | 忘却場勾配の直接制御 |
| **(vi)** | **α(l) 学習, λ<0, ρ>0** | **α-Oblivion SAM** | **統一形態** |

**包含関係:**

$$\text{SGD} \subset \text{SAM} \subset \text{Fisher SAM} \subset \alpha\text{-SAM} \subset \alpha\text{-Oblivion SAM}$$
$$\text{SGD} \subset \text{Oblivion-Aware SAM} \subset \alpha\text{-Oblivion SAM}$$

**設計原理.** 各パラメータの理論的意味:
- **α(l)**: 方向性定理の操作化 — 忘却の**方向**を制御 (Paper I §6.3)
- **λ**: 作用汎関数 S[Φ] の質量項 — **自発的忘却/安定化**のバランス (Paper I §3.4)
- **ρ**: 最悪ケース擾乱の半径 — **局所平坦性**の要求 (SAM の常数)
- **θ**: パラメータ空間上の位置 — 学習の対象

**λ < 0 に関する注意.** 通常の正則化 (λ > 0) と異なり、Oblivion-Aware SAM は λ < 0 を本質的に使用する。これは忘却場の勾配を**増大**させる方向への駆動であり、方向性定理の「力を生む条件 $d\Phi \wedge T \neq 0$」の操作的実現。学習安定性を確保するため、|λ| はρ に対するスケーリング $|\lambda| \sim \rho \cdot \|T\|^2$ に従うべきであり、これにより SAM の平坦性要求と忘却の方向性要求がバランスする。

---

## Paper I/II への統合計画

### Paper I

- **§6.8 に追加 (§6.7 α-SAM の直後)**: 「Oblivion-Aware SAM: 忘却場勾配の直接最適化」
  - 作用汎関数 S[Φ] の場の方程式 → 目的関数への翻訳
  - λ < 0 の VFE 的正当化
  - ガウス族上の worked example ($\|\nabla\Phi_B\|^2$ の計算)
  - α-SAM との合成 (α-Oblivion SAM)
- **§9 予測一覧に P7 追加**: 「λ < 0 の正則化は、ユークリッド正則化 (λ > 0) よりも汎化性能を向上させる」
- **§10 結論に追記**: Oblivion-Aware SAM の実験的検証路

### Paper II

- **§2.5.6 リマークの拡張**: CPS Type 分類と SAM 系手法の対応表を拡張し、Oblivion-Aware SAM を含める
- **§3.3 層化定理への注記**: α-Oblivion SAM の4パラメータが層化構造 (底空間 Δd, ファイバー α(θ), 質量 λ, 擾乱 ρ) にどう対応するか

---

*初期構想: 2026-03-26 /u+ セッション*
*精密化: 2026-03-27 Oblivion-Aware SAM の理論的検討*
