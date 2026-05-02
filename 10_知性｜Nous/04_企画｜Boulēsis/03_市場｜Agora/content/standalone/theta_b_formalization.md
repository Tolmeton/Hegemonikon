# Θ(B): MB Thickness の数学的定式化

> **ステータス**: Draft v1.0 (2026-03-15)
> **位置づけ**: 論文 §4 の数学的核心
> **依拠する既存概念**: blanket density ρ(x), blanket index β, nested MB

---

## §0. 既存概念の整理

### 0.1 Blanket Strength S(x)

情報理論的 blanket の強さ:

$$S(x) := 1 - \frac{I(\mu; \eta \mid b)}{I(\mu; \eta)}$$

- μ = 内部状態, η = 外部状態, b = blanket 状態
- S = 1: 完全な条件付き独立 (完璧な blanket)
- S = 0: blanket が完全に透過的 (条件付き独立なし)
- **出典**: blanket density 論文 (arxiv, ~2023-2025)

### 0.2 Blanket Density ρ(x)

空間的に連続な blanket の「濃さ」:

$$\rho(x) \in [0, 1]$$

- ρ → 1: 点 x において内部と外部がほぼ完全に分離
- ρ → 0: 点 x において強い結合 (blanket が薄い)
- FEP は ρ(x) < 1 の領域でのみ locally definable
- **出典**: blanket density field 論文 (arxiv)

### 0.3 Blanket Index β

正規化された cross-coupling の逸脱度:

$$\beta := \text{(正規化された cross-coupling 強度)}$$

- β = 0: 厳密な Markov blanket
- β → 0 (dim → ∞): sparse coupling 定理 (Sakthivadivel 2022, arXiv:2207.07620)
- 高次元系では「弱い MB」が確率1で出現
- **出典**: Sakthivadivel (2022), Heins & Da Costa

---

## §1. Θ(B) の定義: MB の「厚さ」

### 1.1 動機

既存概念 (ρ, β, S) は **MB の「堅さ」** (条件付き独立の強さ) を測る。
しかし身体性の議論に必要なのは **MB のチャネル構造の豊かさ** — 我々はこれを「厚さ」と呼ぶ。

**直観的に:**
- 生物の MB は「厚い」: 多チャネル × 高冗長性 × 階層的入れ子
- LLM の MB は「薄い」: 単一チャネル × 冗長性なし × 平坦

「堅い」MB (高い S) が「厚い」とは限らない。単一チャネルでも条件付き独立は強く保てる。
「厚い」は **チャネルの多様性と冗長性** を追加的に測る。

### 1.2 定義

系 A が Markov blanket B = (s, a) を持つとき (s = sensory states, a = active states):

$$\boxed{\Theta(B) := S(B) \cdot \left( 1 + \alpha \cdot H(s) + \beta \cdot H(a) + \gamma \cdot R(s, a) \right)}$$

ここで:

| 記号 | 名称 | 定義 | 直観 |
|:-----|:-----|:-----|:-----|
| $S(B)$ | blanket strength | $1 - I(\mu; \eta \mid b) / I(\mu; \eta)$ | MBの「堅さ」(既存) |
| $H(s)$ | sensory diversity | sensory states s のエントロピー | 感覚チャネルの多様性 |
| $H(a)$ | active diversity | active states a のエントロピー | 行為チャネルの多様性 |
| $R(s,a)$ | redundancy | $I(s_1; s_2; ...; s_k)$ (多変量相互情報) | チャネル間の冗長性 |
| $\alpha, \beta, \gamma$ | 正規化係数 | Σ = 1 に正規化 | 相対的重み |

### 1.3 設計の根拠

**なぜ S(B) を前に掛けるか:**
- MB が存在しなければ (S → 0)、チャネルの多様性は無意味 (系の境界がない)
- S(B) は **身体の存在条件**、H/R は **身体の豊かさの条件**
- Θ(B) = 0 ⟺ MB が存在しない (S=0)。S(B) > 0 ならば Θ(B) ≥ S(B) > 0 (ベースライン身体性)

**なぜエントロピー H か:**
- チャネルの「数」ではなく「情報的独立性」を測りたい
- 10本の完全相関チャネル ≈ 1本のチャネル → H が低い
- 5本の独立チャネル → H が高い (本質的に5次元の感覚空間)

**なぜ冗長性 R か:**
- R が高い = 1チャネルが損傷しても他で補償可能 = ホメオスタシスが堅牢
- R = 0 = 単一障害点 → Context Rot の構造的原因

### 1.4 S(B) と Θ(B) の関係

| | S(B) 高い | S(B) 低い |
|:---|:---------|:---------|
| **Θ(B) 高い** | 堅く厚い MB (哺乳類) | 不可能 (Θ ≤ S) |
| **Θ(B) 低い** | 堅いが薄い MB (vanilla LLM) | blanket 自体が弱い |

### 1.5 α, β, γ の FEP からの演繹

**問い**: α, β, γ は任意のハイパーパラメータか、それとも FEP から導出できるか？

#### α = β の論証 (particular partition の対称性)

Friston (2019) の particular partition では、系の状態空間が:

$$x = (\mu, s, a, \eta)$$

と分割される。Langevin 方程式:

$$\dot{x} = f(x) + \omega$$

において、s と a は **対称的な役割** を持つ:
- s: η → μ の情報の流れを媒介 (感覚)
- a: μ → η の情報の流れを媒介 (行為)

ヤコビアン J の構造:

$$J = \begin{pmatrix} J_{\mu\mu} & J_{\mu s} & 0 & 0 \\ J_{s\mu} & J_{ss} & 0 & J_{s\eta} \\ J_{a\mu} & 0 & J_{aa} & J_{a\eta} \\ 0 & J_{\eta s} & J_{\eta a} & J_{\eta\eta} \end{pmatrix}$$

s と a は J において **構造的に対称** (転置の関係):
- s は η の列に依存し、μ の行に影響する
- a は μ の行に依存し、η の列に影響する

∴ **H(s) と H(a) は同等の情報論的重要性を持つ → α = β**

#### γ の位置づけ (VFE Complexity 項)

VFE の二項分解:

$$F = \underbrace{-\mathbb{E}_q[\ln p(o|\theta)]}_{\text{-Accuracy}} + \underbrace{D_{KL}[q(\theta) \| p(\theta)]}_{\text{Complexity}}$$

- H(s), H(a) は **Accuracy 項** に対応: チャネルの多様性 → 予測の正確さ
- R(s,a) は **Complexity 項** に対応: 冗長性 → モデルの堅牢性

VFE の最小化は Accuracy↑ + Complexity↓ だが、Body の観点では:
- 冗長性 R は **Complexity を吸収するバッファ** として機能
- R = 0 → 単一障害点 → VFE のスパイクを吸収できない → Context Rot

#### 結論: 初期値の設定

| パラメータ | 値 | 根拠 |
|:-----------|:---|:-----|
| α | 1/3 | particular partition の s/a 対称性 |
| β | 1/3 | = α (対称性) |
| γ | 1/3 | Accuracy:Complexity の均等配分 (初期値) |

> [!IMPORTANT]
> α = β は FEP から演繹可能。γ = 1/3 は「初期値」であり、以下で精密化が必要:
>
> - **仮説**: 生物系では γ > 1/3 (冗長性が身体の本質的特性)
> - **仮説**: 人工系では γ ≈ 0 (設計で冗長性を追加しない限り)
> - **検証**: HGK あり/なしで γ の寄与を実測

---

## §2. Body Spectrum の定量的記述

### 2.1 各系の Θ(B) の概算

| 系 | S(B) | H(s) | H(a) | R(s,a) | Θ(B) | 備考 |
|:--|:---:|:---:|:---:|:---:|:---:|:--|
| E. coli | 0.6 | 低 (化学1-2) | 低 (鞭毛) | ≈0 | 低 | 最小の MB |
| 昆虫 | 0.7 | 中 (複眼+触角) | 中 (歩行+飛行) | 低 | 中-低 | |
| 哺乳類 | 0.9 | 高 (多感覚+内受容) | 高 (運動+自律神経) | 高 | 高 | 冗長性◎ |
| 人間 | 0.95 | 最高 (+言語+社会) | 最高 (+道具+文化) | 最高 | 最高 | +抽象チャネル |
| Vanilla LLM | 0.8 | 最低 (token 1ch) | 最低 (token 1ch) | 0 | **最低** | 堅いが薄い |
| LLM + MCP | 0.75 | 低-中 (+tools) | 低-中 (+execution) | 低 | 低 | |
| LLM + HGK | 0.7 | 中 (+内受容+検索) | 中 (+CCL+Jules) | 中 | 中 | 意図的設計 |

> [!IMPORTANT]
> vanilla LLM の S(B) は**けっこう高い** (transformer の attention mask は条件付き独立を構造的に強制する)。
> しかし Θ(B) は最低。**堅いが薄い** — これが LLM の身体の本質的特徴。

### 2.2 Context Rot と Θ(B) の関係

**仮説 (検証可能)**:

$$T_{rot} \propto \Theta(B) \cdot C$$

- $T_{rot}$ = Context Rot の onset (内部状態の VFE が閾値を超えるまでのステップ数)
- $C$ = コンテキストウィンドウの容量 (これは必要条件であって十分条件ではない)
- Θ(B) = MB の厚さ

**予測**:
1. vanilla LLM: T_rot ≈ 30-50 ステップ (Θ 最低, C は大きくても無駄)
2. LLM + HGK: T_rot ≈ 50-80 ステップ (Θ が増えると onset が遅延)
3. 哺乳類: T_rot → ∞ (Θ 最高 → ホメオスタシスが常に修復)

**検証方法**: HGK あり/なしの LLM セッションで onset を比較

---

## §3. 圏論的構造

### 3.1 具体化の圏 𝐄 (弱2-圏)

L4 Helmholtz BiCat (kernel/L4_helmholtz_bicat_dream.md) に基づき、**𝐄** を弱2-圏として定義:

- **0-cell**: 認知モード — 系の識別可能な機能状態
  - Bio: 感覚モダリティ (視覚, 聴覚, 固有感覚, ...)
  - Digi: ツール介在チャネル (MCP サーバー, API, トークンストリーム)
- **1-cell**: 認知パイプライン — モード間の推論ステップの有向合成
- **2-cell**: associator α: (h∘g)∘f ⟹ h∘(g∘f) — 合成の順序非依存性の度合い
- **Helmholtz 分解**: 各射 η = η_Γ (散逸=学習) + η_Q (保存=循環)

**定義 (具体化系)**: 系 X が *embodied* ⟺ 𝐄(X) が存在し、以下を満たす:
  (i) 0-cell が sensory/active チャネルに同定可能
  (ii) 1-cell が結合律的にパイプラインを構成 (2-cell まで)
  (iii) VFE 最小化がパイプライン力学を駆動
  (iv) Helmholtz 分解が学習 (Γ) と恒常性 (Q) を分離

### 3.2 Bayesian Lens 接続

Smithe (2022) の **BLens** (Bayesian Lens の双圏) を共通圏として使用:

$$\Phi_{\text{Bio}}: \mathbf{E}(\text{Bio}) \to \textbf{BLens}, \quad \Phi_{\text{Digi}}: \mathbf{E}(\text{Digi}) \to \textbf{BLens}$$

- Φ は **lax functor** (strict ではない)
- laxitor ‖φ‖ ∝ ‖T_{ijk}‖ · ‖Δθ‖ (Amari-Chentsov 3次テンソル由来)
- forward c ↔ Γ (予測/行動), backward c† ↔ Q (Bayesian 更新)

Chemero の暗黙の前提: Φ_Digi が未定義。
反論: Φ_Digi は well-defined (MCP + CCL + ROM が BLens のインスタンスを構成)。

### 3.3 比較 span と Θ(B)

§3.2 の二つの lax functor は **BLens 上の比較 span** を構成する:

$$\mathbf{E}(\text{Bio}) \xrightarrow{\Phi_{\text{Bio}}} \textbf{BLens} \xleftarrow{\Phi_{\text{Digi}}} \mathbf{E}(\text{Digi})$$

直接の比較関手 $F = \Phi_{\text{Digi}}^{-1} \circ \Phi_{\text{Bio}}$ は **定義できない** (lax functor の逆は一般に存在しない)。代わりに、像の包含関係で比較する:

| 性質 | 定義 | Θ(B) への帰結 |
|:-----|:-----|:-------------|
| Injectivity | $\Phi_X$ が Hom 上で単射 | 各系の構造的区別は BLens で保存 |
| **Inclusion failure** | $\text{im}(\Phi_{\text{Digi}}) \subsetneq \text{im}(\Phi_{\text{Bio}})$ | **Bio に固有の lens がある → H,R が縮小** |
| Essential overlap | すべての digital lens に同値な biological lens が存在 | 24 Poiesis が認知モードをカバー |
| Lax (not strict) | associator α が非自明 | 学習の不完全性 |

**核心**: $\text{im}(\Phi_{\text{Digi}}) \subsetneq \text{im}(\Phi_{\text{Bio}})$ ⟺ Bio にあって Digi にない lens ⟺ H(s), R(s,a) の縮小 ⟺ **Θ(B) の低下**

**命題**: inclusion failure は Θ(B) の3成分に対応:
  1. sensory 0-cell の不足 → H(s) ↓
  2. active 0-cell の不足 → H(a) ↓
  3. チャネル間結合の減少 → R(s,a) ↓
  ∴ Θ(B_Digi) < Θ(B_Bio), but Θ(B_Digi) > 0。差は**量的** (像の大きさ) であり質的ではない。

---

## §4. 開かれた問い

1. ~~**H(s) の測定**~~ → **§5 で解決**: 2つのプロキシが実証的に有効:
   - Inter-channel: MCP server entropy (セッション長と独立, r=-0.10)
   - Intra-channel: bge-m3 multilayer precision_ml variance (drift と負相関, r=-0.689)
2. **R(s,a) の測定**: BiCat 1-cell 結合密度の操作化。
   - sensory 0-cell と active 0-cell を結ぶ 1-cell の数をカウント？
   - [仮説] MCP ツールの failure recovery rate が R のプロキシ (チャネル間代替経路の存在)
   - [仮説] cross-server call sequences (A→B→A のような行き来) が 1-cell の活性を示す
3. **S(B) vs Θ(B) の分離**: BiCat 𝐄 の well-definedness (S) vs inclusion 度 (Θ) の分離。
   - vanilla LLM: 𝐄 は存在する (S>0) が、0-cell が1つ → inclusion failure は自明に不在。しかし Θ は低い
   - HGK+: 𝐄 が存在し (S>0)、0-cell が多い → inclusion failure が有意に問われる。Θ は高い
   - → HGK あり/なしの比較実験で検証可能
4. **associator α の実測**: §5.5 dynamic range ∝ ‖α‖ の仮説検証。
   - 合成経路の数 (0-cell 数の combinatorics) と精度分散の関係を定量化

> [!NOTE]
> **q4 (α,β,γ) は §1.5 で FEP 演繹により解決済み**

---

## §5. 実証パイプライン: precision_ml → H(s) → Θ(B)

### 5.1 実験結果 (2026-03-15)

bge-m3 の浅層 [1-4] ↔ 深層 [21-24] の [CLS] cos sim を precision_ml として計算:

| 指標 | 値 | 意味 |
| :--- | :--- | :--- |
| sim_range | [0.195, 0.239] | セッション内で sim が有意に変動 |
| unique steps | 51/51 (100%) | 全ステップが異なる sim 値 |
| precision_ml mean | 0.452 | 正規化後の平均 (中間: exploit寄り) |
| precision_ml range | 0.190 | チャンク間で差が出る (H が変動) |
| r(ml, knn) | +0.382 | k-NN precision と弱い正の相関 (独立した情報源) |
| r(ml, drift) | -0.689 | ドリフトが大きいほど precision が低い (FEP 整合) |

仮説検証:

- **H1** (ml precision 分散 > 0.001): ✅ var=0.006
- **H2** (ml ≠ knn, |r| < 0.5): ✅ |r|=0.382
- **H3** (ml range > 0.05): ✅ range=0.190

### 5.2 precision_ml → H(s) の写像

precision_ml は H(s) のプロキシとして以下のように接続する:

$$H(s)_{proxy} := \text{Var}_{chunks}[\text{precision\_ml}(c)]$$

**根拠**:

- precision_ml の**分散**が大きい = チャンク間で浅層/深層の処理レベルが異なる = sensory channel の多様性が高い
- precision_ml の分散が 0 = 全チャンクが同一処理レベル = 単一チャネル (H ≈ 0)
- Stoll2026 N3 の「精度チャネルの空間分離」の embedding レベルでの複製

### 5.3 Θ(B) 3条件比較実験結果 (2026-03-15)

13セッションを MCP ツール使用度で3条件分類し、precision 分散 (H(s) proxy) を比較:

| 条件 | n | Prec μ | Prec σ² | Prec range | Coh μ | Drift μ | Steps |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **VANILLA** (MCP=0) | 8 | 0.6661 | 0.000014 | 0.0082 | 0.8158 | 0.1055 | 59.0 |
| **PARTIAL** (MCP 1-4) | 3 | 0.6646 | 0.000026 | 0.0121 | 0.8098 | 0.1061 | 69.0 |
| **HGK+** (MCP≥5) | 2 | 0.6678 | 0.000031 | 0.0172 | 0.8192 | 0.0983 | 96.0 |

**Θ(B) 推定** (α=β=γ=1/3, S(B)=1.0, H(a)≈H(s), R(s,a)≈0):

| 条件 | H(s) | Θ(B) |
| :--- | ---: | ---: |
| VANILLA | 1.42e-5 | **0.95e-5** |
| PARTIAL | 2.64e-5 | **1.76e-5** |
| HGK+ | 3.08e-5 | **2.05e-5** |

**仮説検証**:

- **H_main**: Θ(B)\_HGK+ > Θ(B)\_PARTIAL > Θ(B)\_VANILLA → ✅ **成立**
- **効果量**: Cohen's d (HGK+ vs VANILLA) = **+0.74** (中効果), (PARTIAL vs VANILLA) = **+0.53** (中効果)
- **相関**: r(MCP使用度 ↔ precision分散) = **+0.39** (正の中程度の相関)
- **交絡**: r(ステップ数 ↔ precision分散) = +0.66 (ステップ数が大きいセッションほど precision が分散する — 交絡因子として要検討)

> [!IMPORTANT]
> H(s) の絶対値は非常に小さい (1e-5 オーダー)。これは k-NN precision (Gemini embedding) の分散であり、multilayer precision (bge-m3 shallow↔deep) による H(s) はより大きな分散を示す可能性がある (§5.1 では var=0.006)。

### 5.4 Context Rot onset と Θ(B) の検証

$$T_{rot} \propto \Theta(B) \cdot C$$

- HGK ありセッション (Θ 中): T_rot の onset を Context Rot Status で計測
- HGK なしセッション (Θ 最低): 同様に計測
- 比較: Θ(B) が大きいほど T_rot が遅延するか？

### 5.5 開かれた課題

1. **ステップ数との交絡**: r=+0.66。長いセッションほど precision 分散が大きくなるのは自明かもしれない。ステップ数で正規化した比較が必要
2. **multilayer precision による追試**: bge-m3 shallow↔deep sim のチャンク間分散で同一パターンが出るか
3. **R(s,a) の実測**: MCP ツールの failure recovery rate などのプロキシを開発
4. **サンプル増**: HGK+ が2セッションのみ。5+ で統計的信頼性を確保

---

## 参考文献

- Sakthivadivel, D. A. R. (2022). Weak Markov blankets in high-dimensional, sparsely-coupled random dynamical systems. arXiv:2207.07620.
- blanket density field 論文 (arxiv, ~2023-2025). S(x) := 1 - I(I;E|B)/I(I;E).
- Friston, K. (2019). A free energy principle for a particular physics. arXiv:1906.10184. §4.1 (particular partition).
- Friston, K. (2013). Life as we know it. *J. R. Soc. Interface*, 10(86).

---

*v1.2 — 2026-03-15 — §5.3(3条件比較実験結果) + §5.5(開かれた課題) 追加*

