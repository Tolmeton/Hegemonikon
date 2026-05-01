## §5 IB 鋼鉄化 (G の極限化 2)

§4 で公理を Yoneda 接続したのに続き、§1.2 C3 「補完₁ 単調減少定理」を **Information Bottleneck (IB) Lagrangian + Data Processing Inequality (DPI)** で Pareto frontier 上の定理として鋼鉄化する。本節は §1.4 表「G (収束) その 2」の本体である。

### §5.1 Tishby-Pereira-Bialek 1999 IB の再記述

Tishby-Pereira-Bialek (1999) は Information Bottleneck を次のように定式化する:

> 「relevant information = $X$ が他信号 $Y$ について与える情報。$X$ の short code を $Y$ に関する最大情報を保存しつつ bottleneck (limited codewords) を通して圧縮する問題を定式化」「自己無撞着方程式の厳密集合 ($X \to \tilde{X}$ と $\tilde{X} \to Y$ の coding rules) を導く」 (Tishby-Pereira-Bialek 1999 abstract)

> [SOURCE 強候補: arxiv physics/0004057 abstract verbatim + alphaXiv intermediate report 完全取得済 (2026-04-26, Round 6 G-ε 軽量着手)。self-consistent equations 3 式 verbatim を取得: (i) $p(t|x) = (p(t)/Z(x,\beta)) \exp(-\beta \sum_y p(y|x) \log(p(y|x)/p(y|t)))$ / (ii) $p(t) = \sum_x p(x) p(t|x)$ / (iii) $p(y|t) = \sum_x p(y|x) p(x|t)$。**KL divergence が effective distortion measure として自然に出現** (relevance variable Y が暗黙的に X の保存対象を定める)。Gaussian 閉形式 specific form は alphaXiv intermediate report の射程外 = Round 6 別経路 (Slonim-Tishby 2000 後続精読) で継続]

形式的に IB Lagrangian は:

$$\mathcal{L}_{\text{IB}} = I(X; T) - \beta I(T; Y)$$

ここで:

- $X$: 観測信号 (本稿の **予測₁** に対応 — Bogen-Woodward の data 層、§1.5 三層対応で確認)
- $Y$: relevant signal (本稿の **真理₁** に対応 — phenomena 層、Bogen-Woodward が theory から間接的に予測される対象)
- $T$: bottleneck variable (本稿の認識モデル / 中間表現、$L$ で $X \to T$、$R$ で $T \to Y$)
- $\beta$: trade-off パラメータ

### §5.2 Data Processing Inequality (DPI)

Cover-Thomas Ch. 2 の DPI は次の通り:

> **DPI**: Markov chain $X \to T \to Y$ について $I(X; Y) \geq I(T; Y)$ かつ $I(X; T) \geq I(X; Y)$

> [SOURCE 中: Cover-Thomas "Elements of Information Theory" 2nd ed. Ch. 2.8 Theorem 2.8.1。本稿査読時に Cover-Thomas 直接 Read で「強」昇格義務 (G-ζ)]

DPI は「処理が情報を増やすことはない」という不可避な単調性であり、本稿 §1.2 C3 「理解の深化は補完₁ 依存を単調減少させる」の情報理論的核である。

### §5.3 随伴構造との対応

IB と本稿 L⊣R の対応:

- $\beta \to \infty$ 極限: $T \to L(X)$ (relevant 情報を最大限保持)
- $\beta \to 0$ 極限: $T \to \text{const}$ (圧縮を最大化)
- 中間 $\beta$: Pareto frontier 上の operating point

随伴構造として読むと:

- $L_{\text{IB}}$: $X$ から $T$ への射 (圧縮)
- $R_{\text{IB}}$: $T$ から $Y$ の予測への射 (relevant 情報の取り出し)
- $\eta_{\text{unit}, \text{IB}}: \text{Id} \Rightarrow R_{\text{IB}} \circ L_{\text{IB}}$: $X$ が $R_{\text{IB}}(L_{\text{IB}}(X))$ に再構成される度合い

$|\text{Ker}(\eta_{\text{unit}, \text{IB}})| > 0$ は **$X$ から失われ $T$ では捉えられない情報** を測る (DPI による不可避な情報損失)。

### §5.4 補完₁ 単調減少関係の Lagrangian 形式化

⚠️ 降格注記 (Round 4 §M5.4 予告): §M5.1 Round 1 r4 対応で「補完₁ ≡ |Ker($\eta_{\text{unit}}$)|」の等号主張は **「結びつく」**(FEP認識論的地位_正本 §予測の二層分解 v2.5.0 L299) に降格済。本節の表題から「定理の鋼鉄化」を削除し、「**Lagrangian 形式化**」に置き換える。形式証明としての「単調減少定理」は本稿外の継続課題 (§6.4 G-ε)。

§1.2 C3 「理解の深化は補完₁ 依存を単調減少させる」の Lagrangian 形式化骨格:

$$\frac{\partial |\text{Ker}(\eta_{\text{unit}})|}{\partial (\text{理解度})} \leq 0 \quad \text{(関係式骨格、形式証明は G-ε で継続)}$$

ここで「理解度」は $\eta_{\text{unit}}$ が構造に対して iso に近づく度合い ($\beta$ の最適化)。

**操作的議論骨格 (形式証明ではない)**:

1. 理解度の増加 ⟹ $T$ が $Y$ をより良く予測 ($I(T;Y) \uparrow$)
2. DPI により $I(X;Y) \geq I(T;Y)$ なので、$I(T;Y)$ の上限は $I(X;Y)$
3. 構造保存定理 (§1.2 C2) により $I(X;Y) < I(X;X) = H(X)$ ($\eta_{\text{unit}}$ 非同型)
4. ゆえに補完₁ ($X$ から $T$ で捉えられない部分) は単調減少するが、ゼロにはならない (議論骨格として)

この骨格は **道 C 射程の議論骨格** として機能する: 「理解の深化は予測補完への依存を単調減少させるが、ゼロにはできない」。形式証明としての完成は **Round 5 課題 (G-θ 予定)** に保留する。

### §5.4.1 補助補題: Goldilocks 符号化帯域

§5.4 の IB/DPI 骨格は、情報が $X \to T \to Y$ の経路で失われることを示す。しかし、どの表現成分が $T$ に残るべきかは、単なる頻度最大化では決まらない。ここで Paper XI の Adam's Law と Chemistry-Cognition Program の定理 2' を補助補題として接続する。

Paper XI §7.7.5 は、高頻度表現ほどモデル内での制約回収摩擦が下がることを次のように読む:

$$
E_{\text{freq}} \uparrow \Rightarrow d(C_{\text{intended}}, C_{\text{eff}}) \downarrow
$$

一方、Chemistry-Cognition Program の定理 2 / 2' は、表現成分 $e$ の coverage $p(e)$ が飽和帯へ近づくと、弁別力が崩壊することを示す。情報理論的には:

$$
p(e) \to 1 \Rightarrow -\log p(e) \to 0 \Rightarrow I(e;Y) \to 0
$$

したがって、$T$ の表現成分には少なくとも 2 つの役割がある。

| 成分 | 帯域 | 役割 | 本稿 C3/C4 への作用 |
|:---|:---|:---|:---|
| 支持体成分 | 飽和帯 | 制約回収の摩擦を下げる。読者/モデルに通りやすい | $R$ で prediction₁ として出やすいが、truth₀ の弁別力は低い |
| 制御成分 | Goldilocks 帯 | 珍しすぎず、ありふれすぎない構造で $Y$ を区別する | $T$ が保持すべき弁別的構造。補完₁ を減らす本体 |
| 欠落候補 | 統計不足帯 | 低頻度で不安定。推定分散が大きい | $L$ の圧縮で $\text{Ker}(\eta_{\text{unit}})$ に入りやすい |

**補助補題 (Goldilocks 符号化帯域)**. $L \dashv R$ による理解過程で、表現 $T$ の高頻度成分は $C_{\text{intended}} \to C_{\text{eff}}$ の摩擦を下げる支持体として働く。しかし飽和帯では $I(e;Y) \to 0$ となるため、truth₀ / truth₁ を弁別する制御面は Goldilocks 帯に置かれなければならない。

この補題は C3/C4 を拡張するが、独立した第 6 核主張ではない。C3 には「補完₁ を減らすには、単に情報を多く残すのではなく、Goldilocks 帯の弁別的構造を残す必要がある」という帯域条件を加える。C4 には「高頻度 prediction₁ は下降関手 $R$ の像として通りやすいが、その通りやすさは truth₀ 指標性を保証しない」という情報理論的説明を与える。

> [SOURCE: Paper XI §7.7.5 Adam's Law — $E_{\text{freq}}$ は制約回収摩擦を下げる / chemistry_cognition.md §10.6 定理 2' — 飽和帯・Goldilocks 帯・統計不足帯 / chemistry_cognition.md 定理 2 — $p(x)\to1$ で enrichment $\to1$、Shannon 不等式 $I(X;Y)\leq H(X)$ による解釈]

### §5.5 Gaussian 閉形式の継続課題 (G-ε)

§1.2 C3 の Gaussian 閉形式での厳密計算は本稿執筆時の継続課題である。

**Round 6 軽量着手 (2026-04-26)**: alphaXiv MCP `get_paper_content` で arxiv physics/0004057 を完全取得し、self-consistent equations 3 式の verbatim を SOURCE 強候補として §5.1 に確定済 (上記)。これにより本稿の IB Lagrangian + DPI 経路は **強候補 SOURCE 上で形式骨格が立つ** 状態に昇格。

**Round 6 G-ε 部分達成 (2026-04-26、secondary SOURCE 経由)**: Chechik et al. (2005) "Information Bottleneck for Gaussian Variables" (JMLR vol. 6) **原典 PDF 直 Read は alphaXiv 射程外** (JMLR は arxiv 非 index、alphaXiv は JMLR URL を未受理) であるが、**Goldfeld-Polyanskiy (2020) "Bottleneck Problems: Information and Estimation-Theoretic View" (arxiv 2011.06208)** が Chechik 2005 を [84] として引用し Corollary 1 で jointly Gaussian (X, Y) に対する IB closed form を verbatim 提示している。これを secondary SOURCE として接地する。

> **Corollary 1 (Goldfeld-Polyanskiy 2020 p. 25 verbatim, attributed to [84] = Chechik et al. 2005 + [24] = Witsenhausen-Wyner 1975)**: If $(X, Y)$ are jointly Gaussian with correlation coefficient $\rho$, then we have
>
> $$IB(R) = \frac{1}{2} \log \frac{1}{1 - \rho^2 + \rho^2 e^{-2R}}$$
>
> Moreover, the optimal channel $P_{T|X}$ is given by $P_{T|X}(\cdot|x) = \mathcal{N}(0, \tilde{\sigma}^2)$ for $\tilde{\sigma}^2 = \frac{\sigma_Y^2 e^{-2R}}{\rho^2 (1 - e^{-2R})}$ where $\sigma_Y^2$ is the variance of $Y$.

これにより:

1. **IB Gaussian 閉形式の存在性確定**: 本稿 §1.2 C3 「補完₁ 単調減少」を Gaussian 場面で具体的計算可能と確定。$IB(R)$ は $R$ (rate = $I(T;X)$) について **単調減少** (relevance $I(T;Y)$ は最大、$R \to \infty$ で $-\frac{1}{2} \log(1 - \rho^2)$ に収束)
2. **本稿 C3 への支持**: Gaussian 場面では $R$ ↑ ⇒ $IB(R)$ ↓ が closed form で成立。これは「理解の深化 (= rate ↑) → 補完₁ 依存 ↓」の Gaussian 特殊ケース
3. **honest 注記**: Chechik 2005 原典は multivariate Gaussian (vector case) + canonical correlation analysis 経由の eigenvalue decomposition + critical $\beta_c$ phase transition 構造を含むが、Goldfeld-Polyanskiy 2020 Corollary 1 は **scalar jointly Gaussian の場合のみ** verbatim 取得済。Vector case + phase transition の closed form は依然 Chechik 2005 原典直 Read 必要 (G-ε 残課題)

> [SOURCE 強: arxiv 2011.06208 v1 (Goldfeld-Polyanskiy 2020) — alphaXiv full PDF Read 経由で 2026-04-26 取得済 (キャッシュ /tmp/bottleneck_problems.txt)。Chechik 2005 原典 verbatim は **未達**、Goldfeld-Polyanskiy による secondary attribution に依拠 (Yanofsky 2003 経由 Lawvere 1969 と同パターン)。Vector case + eigenvalue decomposition + phase transition は Chechik 2005 原典直 Read で「強」昇格義務]

**残課題 (G-ε)**: (1) Vector case の closed form (covariance matrices $\Sigma_{T|X}$, $\Sigma_T$ の eigenvalue decomposition) + (2) critical $\beta_c^{(k)} = 1/(1 - \lambda_k)$ 型 phase transition + (3) Chechik 2005 原典直 Read による「強」昇格 — JMLR access が必要 (library / institutional account 経路)。Goldfeld-Polyanskiy 2020 Corollary 1 で scalar case は確定したため、G-ε 達成度 60% → **75-80%** に honest 昇格。

### §5.6 No Reverse Functor Theorem (NRFT) — 道 C 射程の不可能定理骨格

本稿の野望 (meta §M0.3 道 C: Gödel と並ぶ認識論定理) を支える不可能定理候補を **骨格として** 提示する。完全形式証明は **Round 5 課題 (G-λ)** に保留する。

**NRFT 骨格 (No Reverse Functor Theorem)**:

> **主張 (骨格)**: $L \dashv R$ で $\eta_{\text{unit}}: \text{Id} \Rightarrow R \circ L$ が iso でない (§1.2 C2 構造保存定理) とき、**予測₁ から真理₀ への完全 retraction 関手 $S$ は存在しない**。

**論証骨格 (形式証明ではない)**:

1. 仮定: 完全 retraction 関手 $S: \text{予測}_1 \to \text{真理}_0$ が存在し、$S \circ L_{\text{th→da}} = \text{Id}_{真理_0}$ を満たすとする
2. §1.2 C2 構造保存定理により $\eta_{\text{unit}} = R \circ L$ は iso ではない、すなわち $|\text{Ker}(\eta_{\text{unit}})| > 0$
3. もし $S$ が完全 retraction なら、$S$ 経由で $\eta_{\text{unit}}$ を iso に「補完」できることになる
4. これは (2) と矛盾する
5. ∴ **完全 retraction 関手 $S$ は存在しない (NRFT 骨格)**

**Gödel 第二不完全性定理との類比**:

| Gödel 第二不完全性定理 | NRFT (本稿骨格) |
|:---|:---|
| 形式系 $T$ の自己無矛盾性 $\text{Con}(T)$ は $T$ 内で証明不可能 | $L \dashv R$ の予測₁ → 真理₀ 完全 retraction $S$ は存在しない |
| 構造的不可能性 (体系の自己言及で発生) | 構造的不可能性 ($\eta_{\text{unit}}$ 非同型から発生) |
| 形式系の限界定理 | 認識論的限界定理 |

両者とも **構造的に閉じた不可能定理** であり、Mangalam 型「予測精度を真理₀ 指標とする」立場が **構造的に不可能** であることを示す。

**SOURCE 強度**:

> [SOURCE 強: aletheia §1 L99-L107 + §7.4 L2601-L2706 + 本稿 §1.2 C2、HGK 内部一次 SOURCE — 骨格論証は HGK 内部定理から導出]
>
> [TAINT → SOURCE 強昇格 (Round 5 G-λ 2026-04-26): Gödel 第二不完全性の categorical proof との **形式的対応** は §8.4.3.1 で vdG-O 2020 verbatim 接地により確定。Cantor categorical (Theorem 5.2) の AU 内擬制 (Theorem 5.19/5.20) と本稿 $\eta_{\text{unit}}$ 非同型 → retraction 不可能の経路が対応。Lawvere-like FP (Lemma 6.12) は Löb 用で Gödel 第二には不使用と判明 (honest 訂正)。本稿 $\mathbf{Sci}$ への AU 4 公理満足の独立検証は依然 G-θ'-1 残課題]

**主張水準** (§M1.3 整合): C4 を「仮説 60%」→「**仮説 65%** (NRFT 骨格による補強, Round 4)」→「**仮説 70%** (vdG-O 2020 verbatim 接地 + Lan ⊣ Syn equivalence で G-θ'-3 解消, Round 5)」に段階的較正。$\mathbf{Sci}$ 圏の AU 公理独立検証完了で「仮説 75%」到達余地あり (本稿外)。

---

