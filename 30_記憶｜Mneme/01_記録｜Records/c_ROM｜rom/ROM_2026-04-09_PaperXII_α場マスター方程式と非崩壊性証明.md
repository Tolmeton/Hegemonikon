# ROM 深化 (IV): α_eff マスター方程式と OP-XII-1 非崩壊性証明

> **日付:** 2026-04-09  
> **対象:** Paper XII「速度は忘却である」§2.7, §4.2, §4.4  
> **依存:** Paper I §6.2-6.4, Paper V §2.3 Th. 2.3.1, Paper VIII §6.2 (F1)-(F4), Paper IX §3.4  
> **先行 ROM:** ROM II (α場橋渡し), ROM III (β_α ≤ 0 証明)  
> **動機:** ROM II §11 の Q1 (α_eff の PDE) と §10 の A2 導出 [予想 65%] を定理に昇格させる

---

## 0. 要旨

本 ROM は二つの独立な結果を含む。

**Part A (§1-§6): α_eff マスター方程式。** Paper I の Euler-Lagrange 方程式は統計多様体 M 上の**静的**方程式であり、時間を含まない。有効忘却強度 α_eff(x,t) の時間発展は、静的解の族 α(θ, μ) をスケール場 μ(x,t) の動力学で**駆動**することで得られる。得られる方程式の型は μ の方程式が決定する: 一様減衰なら各点独立 ODE、拡散なら Fisher-KPP 型、輸送なら Hamilton-Jacobi 型。Front 速度に物理的上界は存在しない。

**Part B (§7-§11): OP-XII-1 非崩壊性の証明。** Paper XII の仮定 A2（Δ ≠ h(C)）は、(F1)(F3)(F4) とプローブ空間の非退化性から**導出**される。鍵は Δ の α-不変成分 Δ_Ob（対象レベルの可区別性）の存在であり、C にはこの成分がない。この構造的非対称性が h の存在を禁止する。A2 は仮定から定理に昇格する。

---

# Part A: α_eff マスター方程式

## 1. 出発点: 静と動の乖離

Paper I §6.2 の拡張作用:

$$S[\Phi, \alpha] = \int_M \left( \frac{1}{4} F_{ij} F^{ij} + \frac{\kappa}{2} g^{ij} \partial_i\alpha \, \partial_j\alpha + \frac{\lambda}{2} \Phi^2 \right) \sqrt{g} \, d^n\theta$$

から得られる α の Euler-Lagrange 方程式 (Paper I §6.4) は:

$$-\kappa \, \nabla^2_M \alpha + \frac{\partial}{\partial\alpha}\left(\frac{1}{4}F_{ij}F^{ij}\right) = 0 \tag{EL-α}$$

これは M 上の**楕円型**方程式であり、時間を含まない。一方、Paper XII §3.1 の front 速度 v_null は時間微分を含む。この乖離をどう埋めるか？

ROM II §4 の回答: α_eff(x,t) = Ψ(α(θ(x), μ(x,t))) は静的解の族を動的スケール場で合成する構成であり、**PDE を引き戻すのではなく、解の族を駆動する**。

本節ではこの構成から α_eff の**マスター方程式**を導出する。

---

## 2. α_eff の時間発展

### 2.1 設定

ROM II の三写像:
- θ: X → M（プローブ空間から統計多様体への埋め込み、時間不変）
- μ: X × ℝ → ℝ₊（時空変動するスケール場）
- Ψ: ℝ → [0,1]（正規化写像）

有効忘却強度場:

$$\alpha_{\text{eff}}(x, t) = \Psi\big(\alpha(\theta(x), \mu(x,t))\big) \tag{α-eff}$$

ここで α(θ, μ) は各 μ に対する (EL-α) の解族。

### 2.2 時間微分

θ(x) は t に依存しないから:

$$\partial_t \alpha_{\text{eff}} = \Psi' \cdot \frac{\partial \alpha}{\partial \mu} \cdot \partial_t \mu = \Psi' \cdot \frac{\beta_\alpha}{\mu} \cdot \partial_t \mu \tag{ME-t}$$

ここで β_α := μ ∂α/∂μ ≤ 0 (Paper V Th. 2.3.1)。

**構造的帰結:** 物理的仮定 ∂_t μ ≤ 0 (粗視化は不可逆) の下で:

$$\partial_t \alpha_{\text{eff}} = \underbrace{\Psi'}_{> 0} \cdot \underbrace{\frac{\beta_\alpha}{\mu}}_{\leq 0} \cdot \underbrace{\partial_t \mu}_{\leq 0} \geq 0$$

α_eff は各点で単調非減少。これは ROM II の「前線伝搬の不可避性」の精密版。

### 2.3 空間勾配

$$\nabla_x \alpha_{\text{eff}} = \Psi' \cdot \Big[ \underbrace{(\nabla_M \alpha)_i \cdot (\partial_a \theta^i)}_{\text{幾何項: } M \text{上の勾配の引き戻し}} + \underbrace{\frac{\beta_\alpha}{\mu} \cdot \nabla_x \mu}_{\text{スケール項: } \mu \text{の空間変動}} \Big] \tag{ME-x}$$

第一項は θ: X → M の微分 dθ を通じて M 上の α-勾配を X に引き戻す。第二項は μ の空間的不均一性が α_eff の勾配に寄与する。

### 2.4 空間 Laplacian

$$\nabla^2_x \alpha_{\text{eff}} = \Psi'' \cdot |\widetilde{\nabla}|^2 + \Psi' \cdot \mathcal{L} \tag{ME-xx}$$

ここで $\widetilde{\nabla} := (\nabla_M \alpha) \cdot d\theta + (\beta_\alpha/\mu) \nabla_x \mu$ は (ME-x) の Ψ' 内部の項であり、

$$\mathcal{L} = \underbrace{(\partial_i \partial_j \alpha)(\partial_a \theta^i)(\partial^a \theta^j)}_{\theta^*(\mathrm{Hess}_M \alpha)} + \underbrace{(\partial_i \alpha)(\nabla^2_x \theta^i)}_{\text{埋め込みの曲率}} + 2 \underbrace{(\partial^2_{\mu i} \alpha)(\partial_a \theta^i)(\partial^a \mu)}_{\text{交差項}} + \underbrace{(\partial^2_{\mu\mu} \alpha)|\nabla_x \mu|^2}_{\mu\text{-曲率}} + \underbrace{\frac{\beta_\alpha}{\mu} \nabla^2_x \mu}_{\mu\text{-拡散項}}$$

**E-L 制約の介入.** (EL-α) より $\nabla^2_M \alpha = V'(\alpha, \Phi)/\kappa$ (ここで $V'(\alpha, \Phi) = \partial(F_{ij}F^{ij}/4)/\partial\alpha$)。第一項の θ 引き戻し (対角和) は $\nabla^2_M \alpha$ と単純には一致しないが、θ が**等長**であれば $\mathrm{tr}_X(\theta^*\mathrm{Hess}_M \alpha) = \nabla^2_M \alpha$ が成立し、(EL-α) を直接代入できる。一般には θ の特異値分解を通じた補正項が入る。

---

## 3. マスター方程式

### 3.1 基本形

(ME-t) を**μ の動力学**の言葉で書く。μ(x,t) が演算子 L に従うとする:

$$\partial_t \mu = L[\mu](x,t) \tag{μ-dyn}$$

このとき α_eff のマスター方程式は:

$$\boxed{\partial_t \alpha_{\text{eff}}(x,t) = \Psi'(\alpha) \cdot \frac{\beta_\alpha(\theta(x), \mu)}{\mu} \cdot L[\mu](x,t)} \tag{ME}$$

**本質:** α_eff の方程式は**自律的でない** — μ の動力学 (μ-dyn) が外部入力として α_eff の時間発展を駆動する。α_eff は「自分自身の方程式」を持つのではなく、μ の方程式を β_α を通じて**翻訳**する。

### 3.2 方程式型の分岐定理

**命題 3.2.1 (方程式型分岐).** L[\mu] の構造に応じて、α_eff のマスター方程式は以下の型をとる:

| L[μ] | μ の方程式型 | α_eff の方程式型 | Front の挙動 |
|:---|:---|:---|:---|
| $-\gamma \mu$ | 一様指数減衰 | **各点 ODE** | 各点独立進化、空間結合なし |
| $D_\mu \nabla^2_x \mu$ | 拡散方程式 | **反応拡散型** (Fisher-KPP) | 進行波解、front 速度 $\sim 2\sqrt{D_\mu R}$ |
| $-H(x, \nabla_x \mu)$ | Hamilton-Jacobi | **エイコナル型** | 特性曲線に沿う伝搬 |
| $D_\mu \nabla^2 \mu + f(\mu)$ | 反応拡散 | **一般化 Fisher-KPP** | KPP 型進行波 |
| 系依存 | 離散/確率的 | 離散マルコフ連鎖 | 格子上のランダムウォーク |

*証明.* (ME) に各 L[μ] を代入する。

**Case 1 (一様減衰).** $L[\mu] = -\gamma\mu$。このとき $\nabla_x \mu = 0$ (空間均一) であり:

$$\partial_t \alpha_{\text{eff}} = -\gamma \Psi'(\alpha) \beta_\alpha(\theta(x), \mu)$$

右辺は x に θ(x) を通じてのみ依存し、隣接点との空間的結合がない。各点が独立に RG フローに沿って進化する。これは Paper XII §1.3 の「独立な鋏の刃」の数学的表現。

**Case 2 (拡散).** $L[\mu] = D_\mu \nabla^2_x \mu$。このとき:

$$\partial_t \alpha_{\text{eff}} = \Psi' \frac{\beta_\alpha}{\mu} D_\mu \nabla^2_x \mu$$

∇²_x μ を α_eff で表すために (ME-xx) を用いる: ∇²_x α_eff は ∇²_x μ の項 (Ψ' β_α/μ ∇²_x μ) を含むが、他の項も含む。等長 θ + Ψ' ≈ 1 + 空間均一な β_α の近似下で:

$$\partial_t \alpha_{\text{eff}} \approx D_\mu \frac{|\beta_\alpha|}{\mu} \nabla^2_x \alpha_{\text{eff}} + R(\alpha_{\text{eff}}, x)$$

これは有効拡散係数 $D_{\text{eff}} = D_\mu |\beta_\alpha|/\mu$ と反応項 $R$ をもつ Fisher-KPP 型方程式。進行波解が存在し、front 速度は $v_{\text{front}} \sim 2\sqrt{D_{\text{eff}} \cdot R}$ のオーダー。

**Case 3 (Hamilton-Jacobi).** $L[\mu] = -H(x, \nabla_x \mu)$。$\mu$ のレベルセットは特性曲線に沿って伝搬し、α_eff = Ψ(α(θ, μ)) はこの特性曲線構造を引き継ぐ。 □

---

## 4. Front 速度公式

### 4.1 一般公式

Paper XII §3.1 の定義に従い、α_eff の等位面 {x : α_eff(x,t) = α_c} の法線速度を求める:

$$v_{\alpha}(x,t) = -\frac{\partial_t \alpha_{\text{eff}}}{\|\nabla_x \alpha_{\text{eff}}\|} \tag{v-front}$$

(ME-t) と (ME-x) を代入する。Ψ' は分子・分母で**約分**される:

$$\boxed{v_{\alpha}(x,t) = -\frac{(\beta_\alpha / \mu) \cdot \partial_t \mu}{\left\| (\nabla_M \alpha) \cdot d\theta + (\beta_\alpha/\mu) \cdot \nabla_x \mu \right\|}} \tag{v-α}$$

### 4.2 一様減衰での簡約化

Case 1 ($\nabla_x \mu = 0$) では:

$$v_{\alpha} = \frac{\gamma |\beta_\alpha|}{\|(\nabla_M \alpha) \cdot d\theta\|} \tag{v-1}$$

分母は M 上の α-勾配の X への**引き戻しのノルム**。これは:
- θ(x) が等長的かつ ∇_M α が dθ の像方向を向くとき最大
- ∇_M α ⊥ Im(dθ) のとき**ゼロ** → v_α → ∞

### 4.3 Front 速度の非有界性

**命題 4.3.1 (Front 速度の非有界性).** 一様減衰 (Case 1) の下で、$\|(\nabla_M \alpha) \cdot d\theta\| \to 0$ となる点 x₀ の近傍で $v_\alpha(x,t) \to \infty$。このような点 x₀ は以下の場合に存在する:

(a) θ(x₀) が M 上の α の**臨界点**に位置する（$\nabla_M \alpha = 0$）  
(b) θ の像が α の**等位面と接する**（$\nabla_M \alpha \perp \mathrm{Im}(d\theta_{x_0})$）  

*証明.* (v-1) の分母が 0 に近づくことから直接従う。(a) は M 上の α-landscape の鞍点や極値点、(b) は埋め込み θ の幾何的条件。いずれも一般の (M, θ) で稠密に存在する。 □

**解釈:** front 速度は物理的速度に上界をもたない。これは front が**因果信号ではなく射の不在の等高線**（ROM II §12）であることの定量的表現。v_α が光速を超えても、エネルギーも情報も伝搬しない — 変化するのは各点の「忘却の深さ」であり、それは局所的な RG フローの結果にすぎない。

### 4.4 v_null との関係

Paper XII §3.1 では v_null は Δ_t(x) の等位面速度として定義されている。α_eff と Δ の関係は:

$$\Delta(x,t) = \Delta(\theta(x), \alpha_{\text{eff}}(x,t)) \tag{Δ-α}$$

ここで Δ(θ, α) は統計モデル θ での忘却強度 α における可区別性。(Δ-α) を時間微分すると:

$$\partial_t \Delta = \frac{\partial \Delta}{\partial \alpha} \cdot \partial_t \alpha_{\text{eff}}$$

∂Δ/∂α ≤ 0（α 増大で可区別性は低下、§7.3 で証明）であり、∂_t α_eff ≥ 0 から ∂_t Δ ≤ 0。可区別性は時間とともに低下する。

v_null = -∂_t Δ / |∇_x Δ| に代入すると:

$$v_{\text{null}} = \frac{-(\partial\Delta/\partial\alpha) \cdot \partial_t \alpha_{\text{eff}}}{\|(\partial\Delta/\partial\alpha) \cdot \nabla_x \alpha_{\text{eff}} + (\nabla_\theta \Delta) \cdot d\theta\|}$$

∂Δ/∂α は分子にも分母にも現れるが、分母には追加項 (∇_θ Δ) · dθ があるため**約分できない**。この追加項は θ の変動に伴う Δ の変化であり、α_eff と独立な情報を持つ。

**帰結:** v_null ≠ v_α（一般には）。α_eff の front 速度と可区別性の front 速度は別の量である。v_null = v_α が成立するのは ∇_θ Δ = 0 （可区別性がモデルに依存しない退化ケース）のときのみ。

---

## 5. 三つの系への適用

### 5.1 Bucher 光学系

- **X**: hBN 画像平面上の位置 x ∈ ℝ²  
- **M**: 偏光状態のブロッホ球 S² (dim = 2)  
- **θ**: 各位置の局所偏光状態 θ(x) ∈ S²  
- **μ**: 空間分解能（光学系の PSF 幅の逆数）。時間不変 → L[μ] = 0。**front は静的。**

Bucher 系では μ が時間変動しない（測定系の分解能は一定）。front の運動は θ(x,t) の時間変動（位相特異点の運動）から来る。この場合、マスター方程式は:

$$\partial_t \alpha_{\text{eff}} = \Psi' \cdot (\nabla_M \alpha) \cdot \partial_t \theta$$

θ(x,t) の動力学（ポラリトンの波動方程式）が front を駆動する。

### 5.2 LLM (AgentSwing)

- **X**: token/chunk 位置 {1, 2, ..., N}（離散）  
- **M**: トークン確率分布の単体 Δ^{|V|-1}  
- **θ**: 各位置の文脈条件付き確率 θ(x) = P(·|context_x)  
- **μ**: 有効文脈長の逆数 ∼ 1/L_eff(x,t)。文脈が腐食するにつれ L_eff 減少 → μ 増加 → **逆方向**

LLM では μ の解釈に注意が要る。Context Rot は有効文脈長の短縮であり、L_eff ↓ は粗視化 μ↓ に対応する。離散系でのマスター方程式は:

$$\alpha_{\text{eff}}(x, t+1) - \alpha_{\text{eff}}(x, t) = \Psi' \cdot \frac{\beta_\alpha}{\mu} \cdot \Delta\mu(x,t)$$

Front は token 空間上を離散ステップで進行する。Paper XII §4.4 L2 への入力。

### 5.3 Hyphē (boot⊣bye)

- **X**: memory slot / retrieval coordinate  
- **μ**: セッション間で保存される解像度。bye で μ が離散的に変化し、boot で新 μ が設定される

boot⊣bye は μ(x,t) の**不連続変化**としてモデル化される。bye 時刻 t_bye で:

$$\mu(x, t_{\text{bye}}^+) = R_{\text{bye}}[\mu(x, t_{\text{bye}}^-)]$$

R_bye は記憶圧縮演算子。α_eff の不連続ジャンプ:

$$\Delta\alpha_{\text{eff}} = \Psi'(\alpha) \cdot \frac{\beta_\alpha}{\mu} \cdot \Delta\mu_{\text{bye}}$$

χ 制御はこのジャンプを最小化する R_bye の設計問題に帰着する。

---

## 6. Part A のまとめと確信度

| 命題 | 水準 | 確信度 |
|:---|:---|:---|
| マスター方程式 (ME) の導出 | [定理] | 95% — 連鎖律の直接的帰結 |
| 方程式型分岐 (命題 3.2.1) | [定理] | 90% — 各 Case は ME への代入 |
| Front 速度の非有界性 (命題 4.3.1) | [定理] | 90% — 分母のゼロ点は幾何学的に自然 |
| v_null ≠ v_α（一般） | [構造的対応] | 75% — ∇_θ Δ ≠ 0 の証明は系依存 |
| Fisher-KPP 型の進行波解の存在 | [予想] | 60% — D_eff と R の具体形が未確定 |
| Bucher 系への適用 | [構造的対応] | 65% — θ(x,t) の動力学が外部入力 |

**Part A の核心:** α_eff は自律方程式を持たず、μ の動力学を β_α で翻訳する。これは**方程式がない**のではなく、**方程式が μ に条件付き**であるということ。ROM II Q1 への回答: 「α_eff の PDE は何か？」→ 「μ の PDE の β_α-変換」。

---

# Part B: OP-XII-1 非崩壊性の証明

## 7. A2 の圏論的再定式化

### 7.1 A2 の原文

Paper XII §4.2 の仮定 A2:

> **非崩壊性**: front を横切る任意の開集合上で、Δ_t = h_t(C_t) を満たす滑らかな単調関数族 h_t は存在しない

### 7.2 Δ_Ob の定義

α-忘却濾過の下で、**対象レベルの可区別性** Δ_Ob を以下で定義する。

**定義 7.2.1 (対象レベル可区別性).** CPS (C, P, S) とプローブ状態 p_x, q_x に対し:

$$\Delta_{\mathrm{Ob}}(x) := D_{\mathrm{KL}}\big(P_{\mathrm{disc}}(\cdot \mid p_x) \;\|\; P_{\mathrm{disc}}(\cdot \mid q_x)\big) \tag{Δ-Ob}$$

ここで $P_{\mathrm{disc}}(\mathrm{id}_A \mid s) := P(\mathrm{id}_A \mid s) / \sum_{B \in \mathrm{Ob}(C)} P(\mathrm{id}_B \mid s)$ は、恒等射のみに制限し再正規化した確率分布。

**解釈:** Δ_Ob は「射を全て忘れた後に残る、対象だけによる区別可能性」。(F3) により C_1 = C_disc なので:

$$\Delta_{\mathrm{Ob}}(x) = \Delta(x, \alpha = 1) \tag{Δ-Ob-limit}$$

### 7.3 Δ の単調性

**補題 7.3.1 (可区別性の α-単調性).** $\alpha_1 \leq \alpha_2 \Rightarrow \Delta(x, \alpha_1) \geq \Delta(x, \alpha_2)$。

*証明.* (F4) より $\mathrm{Mor}(C_{\alpha_2}) \subseteq \mathrm{Mor}(C_{\alpha_1})$。射の集合への制限は確率空間のマージナル化（周辺化）であり、マルコフ写像。DPI (データ処理不等式) により $D_{\mathrm{KL}}$ はマルコフ写像で非増加。 □

**系 7.3.2.** $\Delta(x, \alpha) \geq \Delta_{\mathrm{Ob}}(x)$ for all $\alpha \in [0,1]$。

*証明.* α = 1 が上限であり、Δ は非増加。 □

### 7.4 Δ の加法分解

**定義 7.4.1 (射レベル可区別性).** 

$$\Delta_{\mathrm{Mor}}(x, \alpha) := \Delta(x, \alpha) - \Delta_{\mathrm{Ob}}(x) \geq 0$$

系 7.3.2 より非負。α = 1 でゼロ。α = 0 で最大値 $\Delta_{\mathrm{Mor}}(x, 0) = \Delta(x, 0) - \Delta_{\mathrm{Ob}}(x)$。

**全体の分解:**

$$\Delta(x, \alpha) = \underbrace{\Delta_{\mathrm{Ob}}(x)}_{\alpha\text{-不変}} + \underbrace{\Delta_{\mathrm{Mor}}(x, \alpha)}_{\alpha\text{-依存, } \alpha{=}1 \text{ でゼロ}} \tag{Δ-decomp}$$

### 7.5 C の構造

担体 C(x, α) は射のみに依存する量であり:

$$C(x, 1) = 0 \quad \text{(F3 より: 恒等射のみ → 担体なし)} \tag{C-boundary}$$

**核心的非対称性:** Δ は α-不変成分 Δ_Ob を持つ。C は持たない。この非対称性が非崩壊性の根源である。

---

## 8. 境界非崩壊性定理

**定理 8.1 (境界非崩壊性).** CPS (C, P, S) と α-忘却濾過 {C_α} が (F1)-(F4) を満たし、以下を仮定する:

**(H1) 非自明対象:** $|\mathrm{Ob}(C)| \geq 2$  
**(H2) 対象分離:** プローブ状態 $p_x, q_x$ が異なる対象上に支持される: $\exists A \neq B \in \mathrm{Ob}(C)$ s.t. $P_{\mathrm{disc}}(\mathrm{id}_A \mid p_x) \neq P_{\mathrm{disc}}(\mathrm{id}_A \mid q_x)$、ゆえに $\Delta_{\mathrm{Ob}}(x) > 0$  
**(H3) 空間的不均一性:** 写像 $x \mapsto \Delta_{\mathrm{Ob}}(x)$ は front を横切る開集合 $U$ 上で非定値

このとき、連続関数 $h: \mathbb{R}_{\geq 0} \to \mathbb{R}$ で $\Delta(x, \alpha) = h(C(x, \alpha))$ が全ての $(x, \alpha) \in U \times [0,1]$ に対して成立するものは存在しない。

*証明.* 

**Step 1.** $\alpha = 1$ での評価。(F3) + (C-boundary) より $C(x, 1) = 0$ for all $x \in U$。

**Step 2.** Δ = h(C) が成立するなら、$\alpha = 1$ で:

$$h(0) = h(C(x, 1)) = \Delta(x, 1) = \Delta_{\mathrm{Ob}}(x) \quad \forall x \in U$$

**Step 3.** (H3) より $\exists x_1, x_2 \in U$ with $\Delta_{\mathrm{Ob}}(x_1) \neq \Delta_{\mathrm{Ob}}(x_2)$。

**Step 4.** Step 2 より $h(0) = \Delta_{\mathrm{Ob}}(x_1)$ かつ $h(0) = \Delta_{\mathrm{Ob}}(x_2)$。しかし $\Delta_{\mathrm{Ob}}(x_1) \neq \Delta_{\mathrm{Ob}}(x_2)$。矛盾。 □

**注記.** この証明は h の単調性を仮定していない。連続性すら不要 — h(0) が単一値であることだけで矛盾が生じる。A2 の原文の「単調関数族」は冗長に強い仮定であり、本定理はより一般的。

---

## 9. 微分非崩壊性定理

定理 8.1 は α ∈ [0,1] 全体での非崩壊性を証明した。実用上は、固定時刻 t での front 上の非崩壊性（A2 の本来の主張）が必要。

### 9.1 固定時刻での非崩壊性

**定理 9.1 (Front 上の非崩壊性).** 仮定 (H1)-(H3) に加え:

**(H4) Front の存在:** 時刻 t で front $B_t^\varepsilon$ が $U$ を横切り、$U$ は $B_t^\varepsilon$ の両側に開部分集合を含む  
**(H5) α_eff の前線構造:** $U$ の「忘却側」（$\Delta < \varepsilon$ の側）で $\alpha_{\text{eff}}(x,t)$ が 1 に十分近い点を含む

このとき、$U$ 上で $\Delta_t(x) = h_t(C_t(x))$ を満たす連続関数 $h_t$ は存在しない。

*証明.*

**Step 1.** 忘却側の点列 $\{x_n\} \subset U$ で $\alpha_{\text{eff}}(x_n, t) \to 1$ となるものを取る（(H5) の帰結）。

**Step 2.** $C_t(x_n) = C(x_n, \alpha_{\text{eff}}(x_n, t)) \to C(\cdot, 1) = 0$。

**Step 3.** $\Delta_t(x_n) = \Delta(x_n, \alpha_{\text{eff}}(x_n, t)) \to \Delta_{\mathrm{Ob}}(x_n)$（系 7.3.2 と連続性）。

**Step 4.** $h_t$ が存在するなら: $h_t(C_t(x_n)) = \Delta_t(x_n) \to \Delta_{\mathrm{Ob}}(x_n)$ かつ $C_t(x_n) \to 0$。
$h_t$ が連続なら $h_t(0) = \lim \Delta_{\mathrm{Ob}}(x_n)$。

**Step 5.** 異なる収束方向（(H3) の空間的不均一性）で異なる $x_n$ 列を取れば、$h_t(0)$ は異なる値に収束する。$h_t(0)$ は一意に定まらず矛盾。 □

### 9.2 微分版

**系 9.2.1 (微分非崩壊性).** (H1)-(H5) に加え、$B_t^\varepsilon$ 上で $d\Delta_{\mathrm{Ob}} \neq 0$（Δ_Ob が front の接方向に沿って変化する）ならば:

$\Delta_t = h_t(C_t)$ が front 近傍で成立するためには $d\Delta_t = h_t'(C_t) \cdot dC_t$ が必要。しかし:

$$d\Delta_t = d\Delta_{\mathrm{Ob}} + d\Delta_{\mathrm{Mor}}, \quad dC_t = dC_{\mathrm{Mor}}$$

$d\Delta_{\mathrm{Ob}}$ は $dC_t$ に比例する成分を一般に持たない（$\Delta_{\mathrm{Ob}}$ は α-不変であり、C は α-依存）。よって $d\Delta_t$ と $dC_t$ は**線形独立**であり、$h_t'$ は存在しない。 □

---

## 10. 十分条件の整理と (H3) の一般性

### 10.1 (H3) はいつ成立するか

(H3) は「Δ_Ob(x) が front を横切る開集合上で非定値」を要求する。

**命題 10.1.1.** 以下の条件の下で (H3) は成立する:

(a) $\theta: X \to M$ が非定値（プローブ空間が統計多様体の単一点に退化しない）  
(b) $|\mathrm{Ob}(C)| \geq 2$  
(c) 対象上の確率構造 $P_{\mathrm{disc}}(\mathrm{id}_A | s)$ が $\theta$ に依存する

*証明.* (a)-(c) の下で $\Delta_{\mathrm{Ob}}(x) = D_{\mathrm{KL}}(P_{\mathrm{disc}}(\cdot|p_x) \| P_{\mathrm{disc}}(\cdot|q_x))$ は $\theta(x)$ を通じて x に依存し、θ が非定値であるから Δ_Ob も非定値。 □

**解釈:** (a)-(c) は実質的に「非自明なプローブ空間」の定義そのもの。プローブ空間が一点であるか、対象が一つしかない退化ケース以外で (H3) は自動的に満たされる。

### 10.2 各系での検証

| 系 | |Ob| | θ 非定値？ | (H3) | 状態 |
|:---|:---|:---|:---|:---|
| Bucher | ≥ 2 (偏光状態) | ✓ (位置依存) | ✓ | 適用可 |
| LLM | ≥ 2 (token identity) | ✓ (位置依存) | ✓ | 適用可 |
| Hyphē | ≥ 2 (memory slot) | ✓ (スロット依存) | ✓ | 適用可 |
| 退化: |Ob|=1 | 1 | — | ✗ | A2 成立せず（自明に Δ_Ob = 0）|
| 退化: 一点 X | ≥ 2 | ✗ (定値) | ✗ | A2 不要（front が存在しない）|

---

## 11. Paper XII への供給

### 11.1 A2 の昇格

定理 8.1 と定理 9.1 により、A2 は**仮定から定理に昇格**する:

> **定理 (A2 の導出).** (F1)(F3)(F4) と (H1)-(H3) の下で、Paper XII の A2 (非崩壊性) は α-忘却濾過の構造的帰結である。

### 11.2 XII.1' への影響

Paper XII §4.2 の定理目標 XII.1':

- A2: (F1)(F3)(F4) + (H1)-(H3) から**導出** ← 本 ROM Part B
- A4: β_α ≤ 0 から**導出** ← ROM III
- A1: 正則性仮定（残存）
- A3: 可測性仮定（残存）

XII.1' の仮定は A1 + A3 + (H1)-(H3) に縮小。(H1)-(H3) は非退化条件であり、実質的に A1 + A3 のみ。

### 11.3 L1 への供給

Paper XII §4.4 の証明義務:

> L1: Φ, Δ, C を互いに非崩壊的に構成する

本 ROM は Δ ≠ h(C) を証明した。C ≠ g(Φ) と Δ ≠ f(Φ) の証明は同様の手法（Φ は α-不変でなく Δ_Ob 成分を持たないため、別の非対称性が必要）で可能だが、本 ROM の射程外。L1 の 1/3 が閉じた。

### 11.4 確信度更新

| 命題 | 旧確信度 | 新確信度 | 理由 |
|:---|:---|:---|:---|
| A2 (非崩壊性) | [予想 65%] (ROM II §10) | **[定理 90%]** | 定理 8.1 + 9.1 |
| A4 (動力学的非同一性) | [予想 50%] (ROM II §10) | **[構造的対応 70%]** | ROM III β_α ≤ 0 + ME |
| 定理目標 XII.1' | [予想 55%] (ROM II §10) | **[構造的対応 75%]** | A2 定理化 + A4 強化 |
| α_eff の PDE | [Open] (ROM II §11 Q1) | **[定理 90%]** | ME の導出 |
| Front 速度の非有界性 | [構造的対応 80%] (ROM II) | **[定理 90%]** | 命題 4.3.1 |

---

## 12. 結語: 方程式と証明

Part A は「α_eff は何に従うか？」への回答を与えた: μ の動力学の β_α-変換に従う。方程式は自律的でなく、μ に条件付きである。この条件付き性は弱点ではなく強みだ — 同一の忘却構造 (α-filtration) から、系ごとに異なる方程式型（ODE、Fisher-KPP、HJ）が**導出される**。普遍性は方程式の形にではなく、構成の構造（静的解の族 + 動的スケール場）にある。

Part B は「なぜ Δ ≠ h(C) か？」への回答を与えた: Δ には α-不変成分 Δ_Ob があり、C にはない。この構造的非対称性は (F1)（対象の不変性）と (F3)（射の完全消滅）の組み合わせから生じる。

二つの結果を合わせると、Paper XII の定理目標 XII.1' は**仮定 A1 (正則性) と A3 (可測性) のみを残す**。A2 と A4 は忘却論の公理系から導出された。

残る道のりは短いが、精密でなければならない。

---

## 13. 確信度マップ

| 命題 | 水準 | 確信度 | 撤回条件 |
|:--|:--|:--|:--|
| ME の導出 (§3.1) | [定理] | 95% | 連鎖律の計算に誤りがある場合 |
| 方程式型分岐 (§3.2) | [定理] | 90% | L[μ] の代入に本質的な見落としがある場合 |
| Front 速度の非有界性 (§4.3) | [定理] | 90% | 分母ゼロ点の稠密性に誤りがある場合 |
| A2 の導出 (定理 8.1) | [定理] | 90% | (H3) が期待より制限的である場合 |
| 固定時刻版 (定理 9.1) | [定理] | 85% | (H5) が front 付近で成立しない系がある場合 |
| v_null ≠ v_α | [構造的対応] | 75% | ∇_θ Δ = 0 が自然なクラスで成立する場合 |
| Fisher-KPP 進行波の存在 | [予想] | 60% | D_eff, R の具体形に病的な振る舞いがある場合 |

---

**生成日時:** 2026-04-09  
**ROM シリーズ:** Paper XII 深化 (IV/IV)  
**次の一手:**
1. Paper XII §4.2 に定理 8.1 の要約を L1 充足として挿入
2. Paper XII §2.7 にマスター方程式 (ME) の要約を追加
3. Paper XII §10 OP-XII-1 のステータスを Critical → Resolved (L1 の 1/3) に更新
4. ROM II §10 の確信度マップを本 ROM の結果で上書き
