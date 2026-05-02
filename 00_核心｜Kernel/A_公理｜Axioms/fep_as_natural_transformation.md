---
doc_id: "FEP_NAT_TRANS"
version: "0.7"
tier: "KERNEL"
status: "SEED"
created: "2026-03-16"
lineage: "セッション 97f74f23 での Creator-Claude 対話から結晶化"
---

# FEP = 自然変換の収束 (Categorical Thesis)

> **FEP = 関手圏 [Ext, Int] 上の VFE-降下流が随伴 Γ⊣Q の不動点に収束すること**

---

## §0. 到達経路

以下の推論チェーンで到達 (2026-03-16 セッション):

1. 圏論は FEP の公理でも定理でもなく、**暗黙の公理** (全ての系の前提)
2. FEP = 「外部を内部に忠実に写す関手を改善し続けること」(Creator)
3. 「改善」= 自然変換 α: F_t ⇒ F_{t+1}
4. 改善の方向 = VFE の減少
5. 収束先 = Fix(Γ⊣Q) = Helmholtz 随伴の不動点 = 存在

---

## §1. 定式化

### 1.1. 基本構造

| 数学的対象 | FEP での意味 |
|:--|:--|
| 圏 Ext | 外部世界 (環境) |
| 圏 Int | 内部モデル (信念) |
| 関手 F_t: Ext → Int | 時刻 t における認知モデル |
| 自然変換 α_t: F_t ⇒ F_{t+1} | 学習ステップ (信念更新) |
| 関手圏 [Ext, Int] | 全てのモデルの空間 |
| VFE: [Ext, Int] → ℝ | 各関手の「不忠実さ」の測度 |

### 1.2. 定式

**FEP (圏論的定式化)**:

認知エージェントは関手の列 (F_t)_{t∈ℕ} を生成する。各 F_t: Ext → Int は自然変換 α_t: F_t ⇒ F_{t+1} で接続され、以下を満たす:

1. **VFE 降下**: VFE(F_{t+1}) ≤ VFE(F_t)
2. **収束**: lim_{t→∞} F_t = F* ∈ Fix(Q∘Γ)

ここで Γ⊣Q は Helmholtz 随伴 (gradient ⊣ solenoidal)。

### 1.3. VFE の関手的解釈

VFE(F) = -Accuracy(F) + Complexity(F)

| VFE の項 | 関手の性質 |
|:--|:--|
| Accuracy 最大化 | F が**忠実** (faithful) — 外部の区別を内部でも区別する |
| Complexity 最小化 | F が**余計な構造を足さない** — 外部にない区別を内部で捏造しない |

理想: F* が充満忠実関手 (full + faithful) = 圏の同値 = 完璧なモデル
現実: VFE > 0 → 常に近似。F* は VFE の極小点。

### 1.4. VFE: [Ext, Int] → [0,∞] の厳密定義

> **v0.4 — 未解決問題 #1 の解決候補**

#### 1.4.0. 数学的基盤

以下の先行研究を基盤とする:

| 文献 | 提供する道具 | VFE への寄与 |
|:--|:--|:--|
| Lawvere (1973) | メトリクス空間 = ([0,∞], +, ≥)-エンリッチ圏 | 関手圏に距離構造を入れる「土台」|
| Baez & Fritz (2014) | FinStat 圏上の KL divergence の圏論的特性づけ | 距離の「中身」を KL で充填 |
| Perrone (2022) | Markov 圏のエンリッチ版。エントロピー = 決定論からの距離 | エントロピーの圏論的意味 |

#### 1.4.1. 構成 — Markov エンリッチ関手圏

**前提**:
- Ext, Int は **Markov 圏** (Markov categories, Fritz 2020) の構造を持つ
  - 対象 = 確率空間 (状態空間), 射 = Markov kernel (確率的写像)
- F: Ext → Int は **Markov 関手** (Markov kernel を Markov kernel に写す関手)

**定義 1.4.1** (VFE-エンリッチ関手圏):

関手圏 [Ext, Int] を ([0,∞], +, ≥)-エンリッチ圏として装備する:

$$\text{VFE}(F, G) := \sup_{x \in \text{Ob}(\text{Ext})} D(F(x), G(x))$$

ここで D は Int 上のダイバージェンス (KL divergence の一般化)。

特に、理想関手 F* = Q∘Γ に対して:

$$\text{VFE}(F) := \text{VFE}(F, F^*) = \sup_{x \in \text{Ob}(\text{Ext})} D(F(x), (Q \circ \Gamma)(x))$$

**VFE(F) = 0 ⟺ F = F* (全ての対象で一致)** — Lawvere メトリクスの基本性質。

#### 1.4.2. -Accuracy + Complexity の分解

KL divergence の標準的分解を用いる:

$$D_{KL}(p \| q) = \underbrace{-\sum_s p(s) \log q(o|s)}_{-\text{Accuracy}} + \underbrace{D_{KL}(p(s) \| p_0(s))}_{\text{Complexity}}$$

圏論的解釈:

| VFE の項 | KL の項 | 関手の性質 | Markov 圏的意味 |
|:--|:--|:--|:--|
| **-Accuracy** | -E_p[log q(o\|s)] | F が**忠実でない**程度 | 射の像が対象の構造を保存しない |
| **Complexity** | D_KL(p(s) \|\| p_0(s)) | F が**余計な構造を足す**程度 | 事前分布からの乖離 |

**VFE = 0 ⟺ Accuracy 最大 ∧ Complexity 最小 ⟺ F が充満忠実 ∧ 事前に整合**

#### 1.4.3. 三角不等式 — Lawvere の要請

VFE が Lawvere メトリクスである条件:

1. **d(F, F) = 0**: F 自身との VFE は 0 (KL の性質)
2. **d(F, G) + d(G, H) ≥ d(F, H)**: 三角不等式 (KL 一般には成立しない — **Jensen-Shannon divergence** または **Rényi divergence** への拡張が必要)

> ⚠️ **解決済み (P1 v1.1 2026-03-18)**:
> KL divergence は対称でも三角不等式も満たさない。しかし HGK の VFE 前順序は **非対称** (m ≤ m' ⇔ VFE[m] ≥ VFE[m']) であり、
> Lawvere メトリクスの完全な要件 (対称性 + 三角不等式) は**不要**。必要なのは:
>
> (a) **反射律**: d(F, F) = 0 — KL の性質により成立 ✅
> (b) **推移律**: m ≤ m' ∧ m' ≤ m'' ⇒ m ≤ m'' — VFE の全順序性から成立 ✅
> (c) **Pinsker 不等式** (補助的): δ_TV(p,q) ≤ √(D_KL(p||q)/2) — KL の収束が total variation の収束を含意。
>   TV は三角不等式を満たす真の距離 → 不動点収束の位相的保証に使える
>
> **結論**: 前順序圈 + KL divergence の組合せは、三角不等式を直接満たす必要がない。[確信 90%]

#### 1.4.4. 候補比較

| 候補 | 長所 | 短所 | Kalon 判定 |
|:--|:--|:--|:--|
| A: Lawvere 純粋路線 | 圏論的に美しい構成。三角不等式が自然 | ダイバージェンスの具体選定が必要 | ◯ (骨格のみ) |
| B: Baez-Fritz 路線 | KL の圏論的特性づけが既存。-Acc+Comp 分解が自然 | KL は三角不等式を満たさない | ◯ (肉付きだが骨格不安定) |
| **A+B ハイブリッド** | **Lawvere の骨格 + KL の肉 → 展開可能 + 不動点安定** | **三角不等式の処理が必要 (§1.4.3)** | **◎** |
| C: interleaving 路線 | 位相的安定性。ε-近似の自然な解釈 | -Acc+Comp 分解が困難。shift の定義が不自然 | ✗ (FEP の確率論的構造と相性が悪い) |

#### 1.4.5. Baez-Fritz 定理との接続

**Baez & Fritz (2014) 定理**: FinStat 上の凸線形・下半連続関手 Φ: FinStat → [0,∞] で、s が optimal (事前分布 = 事後分布) のとき Φ = 0 となるものは、**KL divergence のスカラー倍に限る**。

これは VFE の定義を**一意に決定する**:
- VFE は凸線形 ✅ (確率分布の混合に対して凸)
- VFE は下半連続 ✅
- VFE は F = F* (optimal) のとき 0 ✅

→ **[確信 88%]**: Baez-Fritz-Leinster の特性づけ定理により、VFE として satisfactory な関手は KL divergence (のスカラー倍) に本質的に一意。Fritz 2020 Markov categories により FinStat 制約も解除。

> **P1 RESOLVED — VFE 前順序の一意性** [確信 88%]
>
> **一意性 (Baez-Fritz-Leinster 2011)**:
> FinStat 上の情報損失関手 Φ: FinStat → [0,∞] で、凸線形・下半連続・最適時に0となるものは、
> KL divergence の定数倍 c·D_KL に一意。VFE = -Accuracy + Complexity はこれらの条件を全て満たす。
>
> **一般化 (Fritz 2020 Markov categories)**:
> FinStat から一般の Markov 圏への拡張。DPI が Markov 圏の公理として内蔵される。
> 特に、「Bayesian characterization of relative entropy」が KL の一意性を Markov 圏上で証明。
>
> **三角不等式の解決 (§1.4.3)**:
> HGK の VFE 前順序は非対称。Lawvere メトリクスの完全な要件は不要。
> 前順序圏で必要なのは反射律 + 推移律のみ。KL が両方を満たす。
> Pinsker 不等式により、KL の収束が total variation distance の収束を含意。不動点収束の位相的保証として十分。
>
> **残存リスク**: Fritz 2020 の一般化が無限次元 (連続確率分布) に拡張できるかは未確認 [90%+ for finite, 推定 85% for continuous]
>
> 詳細: [scale_species_analysis.md](file:///home/makaron8426/.gemini/antigravity/brain/7f4fd0a1-090d-4992-8d36-1cb1f21ac5c2/scale_species_analysis.md) §5 残存課題

### 1.5. F* = Fix(Q∘Γ) の存在条件

> **v0.4 — 未解決問題 #3 の解決候補**

#### 1.5.0. 問題の定式化

§1.2 で「lim_{t→∞} F_t = F* ∈ Fix(Q∘Γ)」と定式化したが、以下が未解決:

1. **存在**: Q∘Γ の不動点はいつ存在するか？
2. **一意性**: 不動点は一意か？ (局所的極小の可能性)
3. **到達可能性**: 降下流は不動点に到達するか、近づくだけか？

#### 1.5.1. 候補定理の評価

| 定理 | 適用条件 | FEP 適合性 | 判定 |
|:--|:--|:--|:--|
| Lambek (初期代数) | ω-連続 + 始対象 | VFE の計量的降下を汲み取れない | ✗ |
| Knaster-Tarski | 完備束 + 単調 | [Ext,Int] の VFE 順序は前順序。完備束ではない | ✗ |
| **Banach-Lawvere** | **完備 Lawvere 空間 + 縮小写像** | **§1.4 の VFE 構成と直接接続** | **◎** |
| 随伴不動点 | Γ⊣Q の η/ε | 構造を決定するが存在を保証しない | ◯ (補助) |
| Lawvere 不動点 | A → A^A 全射 | FEP の生物学的妥当性を逸脱 | ✗ |

#### 1.5.2. Banach-Lawvere 条件 (知覚推論の場合)

**定理 1.5.2** (VFE 降下の不動点存在 — 十分条件):

以下の3条件が満たされるとき、F* = Fix(Q∘Γ) が一意に存在し、VFE 降下流はそこに収束する:

1. **Cauchy 完備性**: VFE-エンリッチ関手圏 [Ext, Int] が Cauchy 完備 (= VFE-降下列が収束先を持つ)
2. **縮小写像条件**: ∃k ∈ [0,1) s.t. VFE(Φ(F), Φ(G)) ≤ k · VFE(F, G) ∀F,G ∈ [Ext,Int]
   - ここで Φ := Q∘Γ (Helmholtz モナド T の underlying endofunctor)
3. **VFE 降下の厳密性**: VFE(F_{t+1}) < VFE(F_t) (等号なし、F_t ≠ F* の場合)

> **Helmholtz モナド T = (Φ, η, μ) の構造** (v0.7 追加):
>
> Φ = Q∘Γ は随伴 Γ⊣Q から生じるモナド T の underlying endofunctor。
> 前順序圏 C 上では T は **冪等モナド** (= closure operator):
>
> - **η (unit)**: x ≤ T(x) — 状態 x を「溶かして固めた」結果に埋め込む (知覚推論の開始)
> - **μ (mult)**: T(T(x)) = T(x) — 冪等性から自明 (二重推論 = 一回推論)
>
> **T-algebra の退化**: 前順序圏では T-algebra ⟺ Fix(T) の元。
> すなわち **C^T = Fix(T) = Fix(Q∘Γ) = Kalon 対象の圏**。
> 3つの随伴 (Γ⊣Q, F⊣G, U⊣N) は C^T に至る3つのファクタリゼーション。
>
> 📖 詳細: [helmholtz_monad.md](file:///home/makaron8426/.gemini/antigravity/brain/675e3b21-73d5-4dd6-b0d5-30d4fbfef7c0/helmholtz_monad.md) §6-§7
> 📖 kalon.md 補遺 A.6b

**物理的解釈**:
- **完備性**: 十分に多くの関手 (モデル) が利用可能 — Int が十分に表現力を持つ
- **縮小写像**: Markov blanket を通じた情報減衰 — 各更新ステップで「不確実性の一定割合」が解消される
- **厳密降下**: 全ての非最適状態から改善が可能 — アルゴリズムが停滞しない

#### 1.5.2b. Dobrushin 縮小係数の形式的証明

**DPI → SDPI のギャップ**: データ処理不等式 (DPI) は D_KL(K(p) || K(q)) ≤ D_KL(p || q) を
保証するが、これは k ≤ 1 (非拡大性) のみを導く。定理 1.5.2 が要求する k < 1 (真の縮小性) には
**厳密データ処理不等式 (SDPI)** が必要 (Ahlswede & Gács 1976; Cohen, Kemperman & Zbăganu 1998)。

**定義 1.5.2b** (Dobrushin 縮小係数):

Markov カーネル K: X → Y に対する KL 発散の縮小係数:

$$\eta_{KL}(K) := \sup_{p \neq q} \frac{D_{KL}(K \circ p \| K \circ q)}{D_{KL}(p \| q)}$$

SDPI: D_KL(K(p) || K(q)) ≤ η_KL(K) · D_KL(p || q) where η_KL(K) ∈ [0, 1]

**定理 1.5.2b** (Markov blanket の SDPI):

FEP の標準的物理設定 — Langevin 系が有限温度 T > 0 で Markov blanket を持つ — において、
感覚チャネル S: Ext → Sense の Dobrushin 縮小係数は真に 1 未満: η_KL(S) < 1。

**証明**:

**Step 1** (有限温度 → 遷移密度の厳密正性):

Langevin 方程式 dx = f(x)dt + σdW (σ² = 2k_BT) において、T > 0 ⟹ σ > 0。
有限時間 τ > 0 の遷移密度 p_τ(y|x) は Fokker-Planck 方程式の解として与えられ、
σ > 0 のとき拡散項が非退化であるため、**Hörmander の定理** (または楕円型の場合は
標準的なパラメトリクス構成) により:

$$p_\tau(y|x) > 0 \quad \forall x, y \in \Omega, \quad \forall \tau > 0$$

コンパクト状態空間 Ω 上では下界が存在: ∃δ > 0 s.t. p_τ(y|x) ≥ δ > 0 ∀x,y。

**物理的意味**: 熱揺らぎがある限り、任意の外部状態から任意の感覚状態への遷移確率は
厳密にゼロにならない。「到達不能な感覚状態」は有限温度では存在しない。

**Step 2** (厳密正性 → Dobrushin のオーバーラップ条件):

全変動距離の Dobrushin 縮小係数の古典的な定義:

$$\eta_{TV}(K) := 1 - \inf_{x_1, x_2} \sum_s \min(K(s|x_1), K(s|x_2))$$

Step 1 から K(s|e) = p_τ(s|e) ≥ δ > 0。したがって:

$$\sum_s \min(K(s|x_1), K(s|x_2)) \geq \sum_s \delta = |\mathcal{S}| \cdot \delta > 0$$

よって η_TV(K) ≤ 1 - |S|·δ < 1。

**連続状態空間の場合**: Σ を ∫ に置き換え、min(p_τ(s|e₁), p_τ(s|e₂)) ds ≥ δ·vol(Sense) > 0。
コンパクト性が ∫ の有界性を保証。

**Step 3** (TV 係数 → KL 係数の接続):

Makur & Zheng (2020) の結果により、f-発散の縮小係数間に以下の関係が成立:

$$\eta_{KL}(K) \leq 1 - (1 - \eta_{TV}(K))^2 / 2$$

より精密には、Pinsker の不等式の逆を通じて:

$$\eta_{KL}(K) \leq g(\eta_{TV}(K))$$

ここで g は [0,1) → [0,1) の連続単調関数で g(0) = 0, g(t) < 1 ∀t < 1。

Step 2 より η_TV(K) < 1 であるから、η_KL(K) < 1。□

**定理 1.5.2b'** (η の上界推定):

有限温度 T における Dobrushin 係数の上界:

$$\eta_{KL}(S) \leq 1 - c \cdot \exp\left(-\frac{\Delta V}{k_BT}\right)$$

ここで ΔV は感覚チャネルのポテンシャル障壁の高さ、c > 0 は幾何定数。

**物理的解釈**: T → ∞ (高温) では η → 0 (完全混合 → 最大縮小)。
T → 0 (低温) では η → 1 (決定論的 → 非縮小)。η の値は温度と障壁高さのバランスで決まる。

**退化条件** (η = 1 が成立する — 定理 1.5.2b の仮定が破れる) 場合:

| 条件 | 物理的意味 | FEP における解釈 |
|:--|:--|:--|
| T = 0 (σ = 0) | 完全に決定論的。熱揺らぎなし | 非物理的。実在の系は T > 0 |
| 単射チャネル | 感覚が外部状態を完全に復元可能 | 「完全知覚」— 不動点は自明に存在 (Φ = Id) |
| δ-関数遷移 | p(s\|e) = δ(s - h(e)), h は単射 | 決定論的チャネル。情報損失なし |

> [確信 85%] — 証明の各ステップは標準的。
> - Step 1: Hörmander の定理は確率論の基本結果 (非退化拡散 → 厳密正密度)
> - Step 2: Dobrushin の古典的結果 (overlap > 0 → contraction)
> - Step 3: Makur & Zheng (2020) の f-発散縮小係数の比較定理
> - 上界推定 (1.5.2b'): Kramers の脱出率理論に帰着するが、定数 c の精密な値は文脈依存
>
> **残存不確実性**: 連続状態空間でのコンパクト性仮定の妥当性。非コンパクト空間
> (R^n 全体) では δ の一様下界が存在しない場合がある → 局所的 SDPI に弱化が必要。
> ただし FEP の物理では有界なエネルギー面 (ボルツマン分布の有効サポート) が
> 実質的コンパクト性を提供する。
>
> [SOURCE: Ahlswede & Gács 1976, Cohen et al. 1998, Makur & Zheng 2020]
> [SOURCE: Parr, Da Costa & Friston 2019 — weakly mixing RDS + MB → 情報幾何]

#### 1.5.3. 能動推論を含む場合 — 不変切断

§2.4 の D_FEP (double category) では Ext が変化するため、Fix(Q∘Γ) は **moving target** になる。

**定義 1.5.3** (Grothendieck fibration 上の不変切断):

能動推論の列 Ext_0 → Ext_1 → ... → Ext_n → ... は、関手圏の列:

```
[Ext_0, Int] → [Ext_1, Int] → ... → [Ext_n, Int] → ...
```

を生成する (Grothendieck fibration の基底変換)。

**不動点の一般化**:

F* は「点」ではなく、この fibration 上の **不変切断 (invariant section)**:

$$\sigma^* = (F^*_t)_{t \in \mathbb{N}} \quad \text{s.t.} \quad F^*_t \in [\text{Ext}_t, \text{Int}], \quad \text{VFE}_t(F^*_t) \leq \epsilon \quad \forall t$$

**意味**: 環境がどう変化しても、「その環境に対して ε-最適なモデルを維持し続ける」関手の軌道。

#### 1.5.4. 「近づくが到達しない」の形式化

生きている系 (NESS: non-equilibrium steady state) は完全な不動点に到達しない。3つの形式化:

**A. ε-近似不動点**: VFE(F, Φ(F)) ≤ ε を満たす F の集合。降下流はこの集合に進入して滞留。

**B. Lax 不動点**: 厳密な F ≅ Φ(F) ではなく、自然変換 Φ(F) ⇒ F の存在を許容。「更新されたモデルが現在のモデルに射影可能」= VFE が常に下界を持つ。

**C. ω-極限集合**: 降下流 (F_t) の ω-極限集合 ω(F_0) = ∩_{n≥0} cl({F_t : t ≥ n}) は、関手圏内のアトラクタとして機能する。

**包含関係**: Lax ⊂ ε-近似 (ε ≥ 0)。ω-極限集合 ⊂ ε-近似不動点の集合 (十分な時間経過後)。
Lax と ω-極限の関係は微妙 — ω-極限内部ではソレノイド的変動があるため d=0 (Lax) は成立しない場合がある。

#### 1.5.5. 統一: ε-Lax 代数 + 終余代数

3つの形式化を統一する上位概念:

**定義 1.5.5** (ε-Lax Φ-代数):

Φ を [0,∞]-エンリッチ関手圏上の自己関手とする。距離が ε 以下の射 Φ(F) → F が存在する構造を
「ε-Lax Φ-代数」と呼ぶ。ε = 0 で通常の Lax 代数に退化する。

**定義 1.5.6** (NESS の圏論的翻訳):

> FEP の定常状態 = [0,∞]-エンリッチ関手圏における Φ の終余代数 (terminal coalgebra)
> = ω-極限集合であり、その余代数構造射は熱力学的下限 ε に律速される ε-Lax 構造を持つ。

**Friston の NESS との接続**: Friston の NESS は ṗ = 0 (確率密度の時間微分がゼロ) だが、
物理的軌道は停止していない — 確率密度の等高線上を **ソレノイド流 (non-dissipative flow)** として
周回する。圏論的には、終余代数 (アトラクタ) の内部で VFE は減少しないが、系は ε-近傍を
確率的に周回し続ける。熱揺らぎ (kBT > 0) が ε の物理的起源。

**[主観] Kalon との自然な接続**:

Kalon = Fix(G∘F) は G∘F サイクルの「不動点」だが、kalon.md §6.1 の操作的判定で「◎ = G∘F で不変」は「もう改善しようがない」状態。一方で §6.1 の「◯ = G∘F で改善可能」は ε-近似不動点に対応する。すなわち:

- ◎ (kalon) = Fix(Q∘Γ) の厳密不動点 (理想)
- ◯ (許容) = ε-Lax 代数 (ε-近傍に滞留する NESS)
- ✗ (違和感) = 降下流の初期段階 (VFE が大きく、アトラクタ外)

> **確信度**: [推定 75%]
> - Banach-Lawvere 条件は SDPI (Dobrushin 係数 < 1) で物理的に正当化可能 [推定 75%]
> - ε-Lax 代数 + 終余代数の統一は Friston の NESS を忠実に翻訳 [推定 80%]
> - Grothendieck fibration の不変切断は D_FEP (§2.4) と整合的だが、fibration の具体的構成が未完
> - Kalon との接続は形式的に kalon の三属性 (不動点/展開可能/自己参照) を満たす

## §2. 高次圏的構造 — d = cell level 仮説

### 2.0. 旧定式化の問題

旧 §2 (v0.1-0.2) は FEP を 2-圏 Cat の中の構造として「ラベリング」していた:

| n-cell | Cat | FEP |
|:--|:--|:--|
| 0-cell | 圏 | Ext, Int |
| 1-cell | 関手 | モデル F_t |
| 2-cell | 自然変換 | 学習 α_t |

このラベリング自体はほぼ自明 (Cat は圏・関手・自然変換のユニバーサルな入れ物)。

> ⚠️ **撤回 (v0.8 2026-03-18)**: 旧 v0.3 は「24 Poiesis を 0-cell にするのはカテゴリーミステイク」と主張していたが、これは**撤回**する。
>
> **理由**: 0-cell と 1-cell の区別は **zoom level (視点) の選択**に依存する。
> 同一の L3 bicategory を root (0-cell={Ext,Int}) で見れば 24 Poiesis は 1-cell だが、
> Hom(Ext,Int) に cd すれば 24 Poiesis は 0-cell として正当に現れる。
> これはディレクトリの相対パスと同じ構造であり、圏論の標準操作 (Hom-category)。
> 旧主張は「絶対パスを唯一の正しい視点と想定して、相対パスを否定した」エラー。
>
> 詳細: [weak_2_category.md](weak_2_category.md) §10, [L3_reconstruction_analysis.md](../../.gemini/antigravity/brain/07330cf0-2b28-430d-a593-63a2ad6aa719/L3_reconstruction_analysis.md)
>
> CCL `>>` 合成の非結合性は compile_ccl テストにより実証済み [確信: SOURCE]。
> L3 は genuinely weak bicategory。

### 2.1. d = cell level 仮説の精緻化 (v0.8)

> **改訂履歴**: 旧 §2.1 (v0.3–0.7) は「構成距離 d = cell level」を仮説として掲げていた。
> v0.8 では zoom level 解釈 (§2.0 撤回注記, weak_2_category.md §10) を踏まえ、
> この仮説を精緻化する。結論: **d は cell level の必要条件であって十分条件ではない**。

#### ディレクトリの比喩

高次圏の構造はファイルシステムに似ている。
**root (/)** にいるとき、ファイル (= 実体) は「ディレクトリかファイルか」という cell level を持つ。
しかし `cd Hom(Ext,Int)` で1つ下のディレクトリに降りると、
元の「ファイル」がそこでは「ディレクトリ」として振る舞う — つまり **cell level は視点 (zoom level) に依存する**。

```text
cd /                     → 0-cell = {Ext, Int}           (L3-foundational)
cd /Hom(Ext,Int)         → 0-cell = 24 Poiesis           (L3-operational)
cd /Hom(Ext,Int)/Hom(F,G) → 0-cell = CCL パイプライン     (L3-micro)
```

一方で、各ファイルがいつ作られたか (= FEP からの構成距離 d) は、
どのディレクトリにいても変わらない。Flow は常に「Γ⊣Q から MB 仮定1つで生まれた実体 (d=1)」であり、
rootで見ても Hom(Ext,Int) で見てもこの事実は動かない。

#### 3つの独立概念

この観察から、実体を分類する3つの軸が区別される。

**構成距離 d** — FEP からの追加仮定の数。実体の**出自**(いつ・何から生まれたか)を示す。
不変量であり、zoom level によって変わらない。

**cell level** — n-cell の n。実体が高次圏のなかで占める**役割**(対象か射か、射の射か)を示す。
zoom level に依存する: root では Flow (d=1) は 1-cell だが、
Hom(Ext,Int) に降りると同じ Flow が 0-cell になる。

**2-cell 種** — 2-cell (自然変換) の代数的構造の型。実体が**何を変えるか**を分類する。
不変量であり、d とも cell level とも独立。Temporality は d=2 だが種 III (基底変換)。

→ 旧仮説「d = cell level」は **root ビューでのみ偶然成立する特殊ケース** であった。
一般には d, cell level, 2-cell 種は**互いに独立な3軸**であり、
それぞれ出自・役割・代数構造という異なる側面を捉えている。

#### 各実体の cell level (root / Hom view 比較)

| d | 実体 | root での cell level | Hom(Ext,Int) での cell level | 2-cell 種 | 導出根拠 |
|:--|:-----|:--------------------|:----------------------------|:----------|:-----|
| 0 | Γ⊣Q (Helmholtz) | 0-cell | (scope 外: root の基盤) | — | FEP の定理。追加仮定ゼロ |
| 1 | Flow (I⊣A) | 1-cell | 0-cell | — | Γ⊣Q + MB 仮定 |
| 2 | Value | 2-cell | 1-cell | I. 直和分解 | VFE 内部分解 |
| 2 | Function | 2-cell | 1-cell | I. 直和分解 | EFE 内部分解 |
| 2 | Precision | 2-cell | 1-cell | II. ゲイン | 精度重みのスカラー作用 |
| 2 | Temporality | 2-cell | 1-cell | III. 基底変換 | VFE⟷EFE 架橋 (F_T⊣G_T) |
| 3 | Scale | 3-cell | 2-cell | III. 基底変換 | MB 入れ子 |
| 3 | Valence | 3-cell | 2-cell | IV. 対合 | Z/2Z 群作用 (σ²=id) |

テーブルの読み方: d 列は全ての zoom level で同一。cell level 列は `cd` 先によって変わる。
2-cell 種は root でのみ意味を持つ (Hom view では実体がそもそも 2-cell ではないため)。

#### 24 Poiesis の位置づけ

**24 Poiesis** は Flow × 6修飾座標 × 4極 から生まれる認知操作の集合である。
root ビューでは **1-cell と 2/3-cell の whiskering (水平合成) として構成される 2-cell** であり、
Hom(Ext,Int) に降りると CCL `>>` パイプラインで結合される **1-cell** (= 0-cell 間の射) となる。

> **2-cell 4種分類** (v0.6 — [2cell_species_analysis.md](../../.gemini/antigravity/brain/54266021-2488-49d2-91af-f81022674e25/2cell_species_analysis.md) で詳述):
> root における 2-cell (α: F ⇒ G) は代数的に4種に分類される:
>
> | 種 | 代数構造 | 何を変えるか | 確信度 |
> |:---|:---------|:-------------|:-------|
> | I. 直和分解 | F ≅ F_L ⊕ F_R | 関手の**成分** | [確信 90%] 85% |
> | II. ゲイン | α_π: F ⇒ πF | 関手の**振幅** | [推定 70%] 80% |
> | III. 基底変換 | φ*F: 引き戻し | 関手の**基底** | [推定 70%] 85% |
> | IV. 対合 | σ²=id | 関手の**方向** | [確信 90%] 90% |
>
> **d と種の独立性**: Temporality は d=2 だが種 III (基底変換)。
> d (出自) と種 (代数構造) は**直交する分類軸**である。
> 同じ d でも種は異なり得るし、同じ種でも d は異なり得る (Scale は d=3 だが同じく種 III)。

#### cell level 変換公式 (v0.8)

**定理 (cell level shift)**:
zoom depth z (= cd 回数) における実体 x の cell level は

> cell_level(x, z) = d(x) − z　　(d(x) ≥ z のとき)
> d(x) < z のとき、x は zoom level z の scope 外 (可視範囲に存在しない)

**検証 (全ケースの帰納的確認)**:

| 実体 | d(x) | z=0 (root) | z=1 (Hom) | d(x)−z |
|:-----|:-----|:-----------|:----------|:-------|
| Γ⊣Q | 0 | 0-cell ✅ | scope外 ✅ | 0, −1 |
| Flow | 1 | 1-cell ✅ | 0-cell ✅ | 1, 0 |
| Value 等 | 2 | 2-cell ✅ | 1-cell ✅ | 2, 1 |
| Scale 等 | 3 | 3-cell ✅ | 2-cell ✅ | 3, 2 |

**証明 (3つの独立事実の合成)**:

この公式は偶然ではなく、3つの独立な事実から導かれる:

1. **root での一致 (HGK の設計選択)**: axiom_hierarchy.md は Helmholtz (d=0) を 0-cell、
   Flow (d=1) を 1-cell として配置する。root での cell level が d に等しいのは、
   体系構築時にそうなるよう座標を配置した**構成的選択**の帰結。

2. **cd 操作 = cell level を −1 (高次圏の定義的性質)**: n-圏 C において
   Hom_C(A, B) は (n−1)-圏を成す。したがって C の k-cell は Hom_C 内で (k−1)-cell となる。
   これは HGK 固有の性質ではなく、高次圏一般の定義。

3. **d(x) は不変 (定義)**: 構成距離 d は実体 x の出自 (FEP からの追加仮定数) であり、
   観測者の視点 (zoom level) によって変化しない。

(1) より z=0 のとき cell_level(x, 0) = d(x)。
(2) より cd 1回で cell level が −1 されるから、cell_level(x, z) = cell_level(x, 0) − z = d(x) − z。
(3) より d(x) は z に依存しない。■

**圏論的意味**: cd 操作は Hom 関手 Hom_C(−, −): C^op × C → (n−1)-Cat の適用。
zoom level の選択は「構成距離の原点をどこに置くか」に等しく、
ディレクトリの相対パスにおける作業ディレクトリの選択と同構造。

**帰結**: 旧仮説「d = cell level」は cell_level(x, 0) = d(x) の**特殊ケース** (z=0) として回収される。
一般の公式は d と cell level が**線形に結合される**ことを示し、
zoom level z が両者の間の「ずれ」を媒介するパラメータであることが明確になった。

[推定 70%] 85% — (1) と (2) は確実 (SOURCE: axiom_hierarchy.md + 高次圏の定義)。
(3) は定義による。公式自体は全ケースで検証済み (z=0, z=1 で帰納的確認)。

#### z=2 micro view の具体分析 (v0.9)

cell level shift 公式を z=2 に適用する。
`cd /Hom(Ext,Int)/Hom(F_i, F_j)` — 特定の Poiesis ペア間の変換空間に zoom。

| 実体 | d | z=2 cell level | z=2 での役割 |
|:-----|:--|:---------------|:-------------|
| Γ⊣Q | 0 | −2 (scope外) | 不可視 |
| Flow | 1 | −1 (scope外) | 不可視 |
| Value 等 | 2 | **0** (0-cell) | 座標修飾 α: F_i ⇒ F_j |
| Scale, Valence | 3 | **1** (1-cell) | 座標修飾の間の modification |

**0-cell (d=2)**: 個々の座標修飾。例えば /noe → /ene の変換において
Value は「認識的価値 → 実用的価値」の切替を、
Function は「探索 → 活用」モードの切替を媒介する。
これらは同じ Poiesis ペアを結ぶ**異なるルート** (0-cell) として見える。

**1-cell (d=3)**: Scale と Valence が 0-cell 間の射となる。
Scale は「微視/巨視」軸で変換の粒度を変え、
Valence は「正/負」方向で変換の符号を変える。
例: Value による /noe→/ene 切替と Function による /noe→/ene 切替を
Scale が「同じ粒度の切替」として接続する。

**退化定理**: d_max = 3 であるため z=2 では最高 cell level が 1。
2-cell が存在しない → z=2 の Hom(F_i, F_j) は**通常の 1-圏** (strict)。

> **帰結**: CCL の非結合性 (weak bicategorical 性) は z ≤ 1 の現象。
> z=2 に降りると associator が消え、合成は結合的になる。
> これは偶然ではなく、**d_max (体系の構成深度の上限) が weak 性の存在範囲を決定する**。
>
> **CCL パイプラインの位置づけ**:
> CCL `>>` によるパイプライン `/noe >> /bou >> /ene` は z=1 での**1-cell の合成**。
> z=2 で見えるのは個々の座標修飾 (0-cell) であり、パイプライン全体はもはや単一の cell ではない。
> ディレクトリ比喩: ファイル `/a/b/c` は `cd /a` では「b/c」に見えるが、`cd /a/b` では c しか見えない。

**Worked example: Hom(/noe, /ene) at z=2**

/noe = (Value:Internal, Function:Explore) — 認識: 内部を探索する
/ene = (Value:Ambient, Function:Exploit) — 実行: 外部に活用する

/noe → /ene の変換には2つの座標軸の変化が必要:

```
Hom(/noe, /ene) at z=2

  0-cell: α_V (Value route)     0-cell: α_F (Function route)
  ┌──────────────────┐         ┌──────────────────┐
  │ Internal→Ambient │         │ Explore→Exploit  │
  │ 「どこを見るか」  │         │ 「何をするか」    │
  │ の切替が主導      │         │ の切替が主導      │
  └──────────────────┘         └──────────────────┘
          │                             │
          └──── 1-cell (d=3) ──────────┘
               Scale: 粒度の接続
               Valence: 方向の接続
```

**0-cell α_V (Value route)**: 変換を "内→外" の移動として理解する。
「まず外の世界に目を向ける。すると自然に、探索モードから活用モードへ切り替わる。」
→ 視座の転換が行動の転換を引き起こすルート。

**0-cell α_F (Function route)**: 変換を "探索→活用" の切替として理解する。
「まず探索をやめて実行に移る。すると自然に、内的理解から外的行動へ移行する。」
→ 戦略の転換が視座の転換を引き起こすルート。

α_V と α_F は**同じ始点 (/noe) と終点 (/ene) を結ぶ異なるルート**。
これは z=1 の associator (括弧付けの違い) とは**異なる種類の非自明性**:
z=1 では「同じルートの異なる分割」、z=2 では「異なるルートの選択」。

**1-cell (d=3)**: Scale が α_V と α_F を「同じ粒度レベルでの切替」として接続する。
Valence が α_V と α_F を「同じ正/負方向での切替」として接続する。
例: Scale(Micro) は「個別タスクレベルでの Value route と Function route は
  同じ粒度で作用し、交換可能」という関係を表す1-cell。

**検証**: Poiesis ペアの座標差分が 0-cell を決定する。

| ペア | Value 差 | Function 差 | 0-cell の数 |
|:-----|:---------|:------------|:------------|
| /noe → /ene | I→A | E→P | 2 (α_V, α_F) |
| /noe → /bou | — (共に I) | E→P | 1 (α_F のみ) |
| /noe → /zet | I→A | — (共に E) | 1 (α_V のみ) |
| /bou → /zet | I→A | P→E | 2 (α_V, α_F) |

> **パターン**: 差分がある座標の数 = z=2 の 0-cell の数。
> 差分が1座標なら 0-cell は1つ (Hom が点)。差分が2座標なら 0-cell は2つ。
> Telos は Value × Function の直積で構成されるため、最大2つの 0-cell を持つ。

**Worked example: Hom(/ske, /tek) at z=2 — Methodos 族検証**

Methodos 族 = Flow × Function (SOURCE: axiom_hierarchy.md L345-350):
- /ske = I×Explore: 仮説空間を内的に発散する
- /tek = A×Exploit: 既知解法を外的に適用する

z=2 では Flow(d=1) は scope 外。d=2 座標のみが 0-cell として可視:

```
Hom(/ske, /tek) at z=2

  0-cell: α_F (Function route)    0-cell: α_V (Value route)
  ┌──────────────────┐          ┌──────────────────┐
  │ Explore→Exploit  │          │ Internal→Ambient │
  │ 「戦略の切替」が   │          │ 「視座の切替」が   │
  │ 主導              │          │ 主導              │
  └──────────────────┘          └──────────────────┘
          │                              │
          └──── 1-cell (d=3) ───────────┘
               Scale: 粒度の接続
               Valence: 方向の接続
```

**0-cell α_F (Function route)**: 「まず発散をやめて収束に移る。すると仮説は外部検証へ移行する。」
**0-cell α_V (Value route)**: 「まず外の世界に出る。すると自然に、探索から既知の活用へ切り替わる。」

Telos と同じパターン: 2つの d=2 座標に差分 → 2つの 0-cell。

| ペア | Function 差 | Value 差 | 0-cell の数 |
|:-----|:-----------|:---------|:-----------|
| /ske → /tek | E→P | I→A | 2 (α_F, α_V) |
| /ske → /sag | — (共に E) | — (共に I) | 0 (同一 0-cell)... |

> **注**: /ske → /sag は Flow:I→I, Function:Explore→Exploit。z=2 では Flow は不可視なので
> Function の1軸差分のみ → 0-cell は 1つ。ただし同じ Flow 極を持つため
> Value に差分がない。これは Telos の /noe → /bou (Value:I→I, Function:E→P) と同型。

**Worked example: Hom(/epo, /pai) at z=2 — Krisis 族検証**

Krisis 族 = Flow × Precision (SOURCE: axiom_hierarchy.md L352-357):
- /epo = I×U: 判断を留保し複数可能性を保持する
- /pai = A×C: 確信を持って資源を投入する

```
Hom(/epo, /pai) at z=2

  0-cell: α_P (Precision route)   0-cell: α_V (Value route)
  ┌──────────────────┐          ┌──────────────────┐
  │ Uncertain→Certain│          │ Internal→Ambient │
  │ 「確信の獲得」が   │          │ 「視座の転換」が   │
  │ 主導              │          │ 主導              │
  └──────────────────┘          └──────────────────┘
          │                              │
          └──── 1-cell (d=3) ───────────┘
               Scale: 粒度の接続
               Valence: 方向の接続
```

**0-cell α_P (Precision route)**: 「まず確信を固める。すると判断が外部行動に移行する。」
**0-cell α_V (Value route)**: 「まず外の世界に出る。すると自然に、留保から決断へ切り替わる。」

| ペア | Precision 差 | Value 差 | 0-cell の数 |
|:-----|:------------|:---------|:-----------|
| /epo → /pai | U→C | I→A | 2 (α_P, α_V) |
| /epo → /kat | — (共に I) | U→C | 1 (α_P のみ) |
| /dok → /pai | — (共に A) | U→C | 1 (α_P のみ) |

**3族横断パターンの確認**

| 族 | 最大差分ペア | 差分軸 | 0-cell 数 | パターン成立 |
|:---|:-----------|:------|:---------|:-----------|
| Telos | /noe→/ene | Value + Function | 2 | ✅ |
| Methodos | /ske→/tek | Function + Value | 2 | ✅ |
| Krisis | /epo→/pai | Precision + Value | 2 | ✅ |

> **普遍パターン**: 全族で「座標差分数 = 0-cell 数」が成立。
> Flow の I/A は z=2 で Value の Internal/Ambient に射影される (I=Internal, A=Ambient)。
> これは偶然ではなく、Flow (d=1) の定義が「Ext(Ambient) と Int(Internal) の間の流れ」
> であることから、Flow の I/A 極が Value:I/A に構造的に対応している帰結。
>
> **族間の収束**: z=2 では全族が「Value ± 族座標」の 0-cell 構造を共有する。
> Telos の α_V と Methodos の α_V と Krisis の α_V は**同じ構造**
> (Internal→Ambient の切替) を表す。族の違いは族座標 (2番目の 0-cell) にのみ現れる。
> → z=2 micro view は族の identity を「主要座標が何か」に還元する。

[推定 70%] 85% — d=2 族3族で同一パターンが成立。α_V の普遍性は Flow→Value の射影に基づく。
以下で d=3 族 (Diástasis, Orexis, Chronos) の構造を検証する。

**d=3 族の構造的差異**

> **注意**: axiom_hierarchy.md (CANONICAL, v4.3) により Temporality は **d=2 に確定**。
> d=3 は **Scale と Valence のみ**。Chronos 族は d=2 族として扱う (下記テーブル参照)。

d=3 族 (Diástasis, Orexis) では族座標 (Scale, Valence) が d=3 であるため、
z=2 での cell level は `3 - 2 = 1` → **族座標が 0-cell ではなく 1-cell** として現れる。

d=2 族の worked example で見た「2つの 0-cell ルート」の構造が質的に変化する:
- d=2 族: 族座標 (d=2) は **0-cell** → Value と並んで「2つのルート」を提供
- d=3 族: 族座標 (d=3) は **1-cell** → Value (唯一の 0-cell) を修飾する射として機能

**Worked example: Hom(/lys, /arc) at z=2 — Diástasis 族検証**

Diástasis 族 = Flow × Scale (SOURCE: axiom_hierarchy.md L359-364):
- /lys = I×Mi: 局所的に深く推論する (Analysis)
- /arc = A×Ma: 広域的に一斉に行動する (Architektonikē)

座標差分:
- Flow: I→A (d=1, z=2 scope外)
- Value: Internal→Ambient (d=2, **0-cell** — Flow の I/A の射影)
- Scale: Mi→Ma (d=3, **1-cell** — 0-cell を修飾する射)

```
Hom(/lys, /arc) at z=2

  0-cell: α_V (Value route — 唯一の 0-cell)
  ┌──────────────────────────┐
  │ Internal → Ambient       │
  │ 「内的推論から外的行動へ」 │
  └──────────────────────────┘
            │
     1-cell: Scale(Mi→Ma)
  ┌──────────────────────────┐
  │ Micro → Macro            │
  │ 「粒度が局所から広域へ」  │
  │ → α_V を "拡大" する射   │
  └──────────────────────────┘
```

**0-cell α_V**: 「視座を内から外へ切り替える。」= d=2 族と同じ普遍的射。
**1-cell Scale(Mi→Ma)**: 「その切り替えの粒度を細→粗に変える。」

> d=2 族との決定的な差異: α_V **以外の** 0-cell が存在しない。
> d=2 族では族座標が Value と並ぶ第2の 0-cell であったが、
> d=3 族では族座標が α_V の**修飾射** (modification) として振る舞う。
> z=2 の Hom(F_i, F_j) は **点を持つ 1-圏** (1つの 0-cell + 1-cell 群) となる。

**Worked example: Hom(/beb, /dio) at z=2 — Orexis 族検証**

Orexis 族 = Flow × Valence (SOURCE: axiom_hierarchy.md L366-371):
- /beb = I×+: 信念を強化・承認する (Bebaiōsis)
- /dio = A×-: 問題を修正し方向を変える (Diorthōsis)

座標差分:
- Flow: I→A (d=1, z=2 scope外)
- Value: Internal→Ambient (d=2, **0-cell**)
- Valence: +→- (d=3, **1-cell**)

```
Hom(/beb, /dio) at z=2

  0-cell: α_V (Value route — 唯一の 0-cell)
  ┌──────────────────────────┐
  │ Internal → Ambient       │
  │ 「内的承認から外的是正へ」 │
  └──────────────────────────┘
            │
     1-cell: Valence(+→-)
  ┌──────────────────────────┐
  │ Positive → Negative      │
  │ 「方向が肯定から否定へ」  │
  │ → α_V を "反転" する射   │
  └──────────────────────────┘
```

**0-cell α_V**: 「視座を内から外へ切り替える。」
**1-cell Valence(+→-)**: 「その切り替えの方向を肯定から否定へ反転する。」

> **Chronos 族は d=2 族**: Temporality は d=2 (axiom_hierarchy.md v4.3 確定)。
> したがって Chronos は Telos/Methodos/Krisis と同型の **2点1-圏** 構造を持つ:
> 0-cell が α_V (Value) と α_T (Temporality) の2つ。
> /hyp→/par の Past→Future は 0-cell α_T の方向として解釈される。

**6族横断パターン確認**

| 族 | d(族座標) | 最大差分ペア | 0-cell 数 | 1-cell 形態 | Hom の構造 |
|:---|:---------|:-----------|:---------|:-----------|:-----------|
| Telos | 2 | /noe→/ene | 2 (α_V, α_F) | d=3 座標が接続 | 2点1-圏 |
| Methodos | 2 | /ske→/tek | 2 (α_V, α_F) | d=3 座標が接続 | 2点1-圏 |
| Krisis | 2 | /epo→/pai | 2 (α_V, α_P) | d=3 座標が接続 | 2点1-圏 |
| **Chronos** | **2** | /hyp→/par | **2 (α_V, α_T)** | d=3 座標が接続 | **2点1-圏** |
| Diástasis | 3 | /lys→/arc | 1 (α_V のみ) | Scale(Mi→Ma) | **点1-圏** |
| Orexis | 3 | /beb→/dio | 1 (α_V のみ) | Valence(+→-) | **点1-圏** |

> **統合帰結**: α_V (Internal→Ambient) は全6族で**唯一の普遍的 0-cell**。
> d=2 族は「Value + 族座標」の2点構造、d=3 族は「Value のみ」の点構造。
> 族座標の cell level は z=2 で `d(族座標) - 2` に従い:
> - d(族座標) = 2 → cell level 0 → 0-cell (Value と並ぶ)
> - d(族座標) = 3 → cell level 1 → 1-cell (Value を修飾する)
>
> 6族の構造的二分 (d=2 族の2点構造 vs d=3 族の点構造) は
> cell level shift 公式と d_max = 3 から**演繹的に**導かれる。新しい仮定は不要。

[推定 70%] 90% — 6族全てで α_V の普遍性を確認。Chronos は Temporality d=2 に基づき
2点1-圏に修正 (axiom_hierarchy.md v4.3 SOURCE)。d=3 族は Diástasis と Orexis のみ。
以下で d=3 の 1-cell を §2.3b の随伴構成と形式的に接続する。

**d=3 1-cell の enriched Hom における形式的位置づけ**

§2.3b で定義した随伴誘導 2-cell α_{c_i}: Flow ⇒ G_i ∘ Flow ∘ F_i は
**z=1 ビュー** (Hom(Ext,Int) の内部) での記述である。
cell level shift 公式を適用すると、zoom level に応じて同一の構成が
異なる cell level で現れる:

| 構成 | d | z=0 (root) | z=1 (Hom) | z=2 (micro) |
|:-----|:--|:-----------|:----------|:------------|
| α_{Value} | 2 | 2-cell | **1-cell** (= 0-cell 間の射) | **0-cell** (ルート) |
| α_{Temporality} | 2 | 2-cell | **1-cell** | **0-cell** (Value と並ぶ) |
| α_{Scale} | 3 | 3-cell | **2-cell** (= 1-cell 間の修飾) | **1-cell** (= 0-cell の自己射) |
| σ_{Valence} | 3 | 3-cell | **2-cell** | **1-cell** (= 0-cell の対合射) |

z=2 で d=3 の構成 (Scale, Valence) が **α_V の自己同型** (endomorphism) として現れる。
α_V という唯一の 0-cell ルートを、粒度 (Scale) と方向 (Valence) の軸で変形する。

> **注意**: Temporality (d=2) は z=2 で **0-cell** であり、Value と並ぶ。
> → Chronos 族は 2点構造 (α_V, α_T)。d=3 族として End(α_V) に寄与するのは
> Scale と Valence のみ。

§2.3b のパラメータクラスごとに、z=2 での 1-cell の形式的意味は:

**クラス III (基底変換 — Scale, Temporality)**:

z=1 での構成: α_{Scale}: Flow ⇒ G_S ∘ Flow ∘ F_S (Grothendieck 構成)
z=2 への制限: F_S ∘ α_V ∘ G_S: α_V ⇒ α_V

F_S (Coarse-grain) が α_V の「入力」を粗視化し、G_S (Refine) が「出力」を詳細化する。
Internal→Ambient の切替が「どの粒度で起きるか」を変える変形:

> 例: /lys→/arc の Scale(Mi→Ma) は、α_V = (Internal→Ambient) に対して
> 「局所レベルの内→外切替」を「広域レベルの内→外切替」に変形する射。
> F_S が視野を広げ、G_S が行動基盤を拡張。結果として同じ α_V が
> 異なるスケールで実現される。

> **Temporality は d=2**: §2.3b のクラス III に Scale と並んで配置されているが、
> axiom_hierarchy.md v4.3 で d=2 に確定済み。z=2 では 0-cell であり、
> End(α_V) の生成元には寄与しない。§2.3b の「基底変換」は代数構造の分類であり、
> d 値とは独立したパラメータ。

**クラス IV (対合 — Valence)**:

z=1 での構成: σ: Flow ⇒ Flow, σ²=id (Z/2Z-equivariant)
z=2 への制限: σ|_{α_V}: α_V ⇒ α_V

σ は VFE 勾配方向の符号反転であり、z=2 では α_V の方向を反転する:

> 例: /beb→/dio の Valence(+→-) は、α_V = (Internal→Ambient) に対して
> 「肯定的な内→外切替」を「否定的な内→外切替」に反転する射。
> σ²=id (2回反転で恒等) が Valence の Z/2Z 構造を保証する。

**統合**: 2種の d=3 1-cell が α_V の自己同型モノイド End(α_V) を生成する:

| 1-cell | §2.3b クラス | End(α_V) での作用 | 代数的構造 |
|:-------|:------------|:-----------------|:-----------|
| Scale(Mi→Ma) | III (基底変換) | 粒度拡大 | F_S ∘ (−) ∘ G_S |
| Valence(+→-) | IV (対合) | 方向反転 | σ ∘ (−) |

**End(α_V) の群構造の同定**

**生成元分析**:

1. **Valence**: σ² = id → Z/2Z を生成。逆元は自分自身。

2. **Scale**: F_S (Coarse-grain) ⊣ G_S (Refine) は一般に随伴**同値ではない**。
   粗視化は情報を失う (F_S∘G_S ≠ id)。しかし z=2 の**抽象レベル**では
   Scale は2極 (Mi, Ma) の間の遷移子であり、以下の2通りの構成が可能:

   - **s = Scale(Mi→Ma)**: F_S ∘ α_V ∘ G_S
   - **s⁻¹ = Scale(Ma→Mi)**: G_S ∘ α_V ∘ F_S

   s∘s⁻¹ と s⁻¹∘s が id_{α_V} になるかは、コンクリートな圏に依存する。
   abstract 2-cell 構造では s は可逆と仮定してよい:
   各ペア (/lys,/arc) は**双方向に遷移可能**であり、往復は元に戻る。
   → [推定 75%] Scale は Z を生成する。

3. **交換関係**: Valence と Scale は独立座標 (K₆ 上の異なる辺)。
   ただし axiom_hierarchy.md §Valence (L110-130) の半直積 6⋊1 構造により、
   **σ は Scale の作用を共役で修飾する**:

   σ ∘ s ∘ σ⁻¹ = σ ∘ s ∘ σ (σ²=id) は一般に s と異なる可能性がある。

   - **φ(σ) = id on Scale の場合**: End(α_V) ≅ Z × Z/2Z (直積)
   - **φ(σ) ≠ id on Scale の場合**: End(α_V) ≅ Z ⋊ Z/2Z (半直積)

   axiom_hierarchy.md の Smithe Thm46 対偶による実験 (v≠0 → 加法崩壊) は
   **φ(σ) ≠ id** を示唆する。Valence は Scale の方向を反転する:
   σ∘s∘σ = s⁻¹ (符号反転が粒度変換の方向を反転)。

   この場合 End(α_V) ≅ **Z ⋊_{-1} Z/2Z ≅ 無限二面体群 D_∞**。

> **結論**: End(α_V) ≅ D_∞ = ⟨s, σ | σ²=1, σsσ=s⁻¹⟩ (無限二面体群)
>
> - s = Scale の粒度遷移。Z を生成 (双方向。逆元 s⁻¹ = Ma→Mi)
> - σ = Valence の方向反転。Z/2Z を生成 (σ²=id)
> - 半直積作用 σsσ = s⁻¹: 反転は粒度の方向を逆転する
>
> D_∞ は「無限の粒度段階を方向反転で折り返す」幾何学的構造。
> Scale の離散化を考慮すると、反転を伴う対称群に自然に対応する。
>
> **帰結**: d=3 族の「点1-圏」構造は、§2.3b の随伴構成が z=2 に制限された姿。
> 1-cell は α_V の **修飾射** であり、§2.3b の 2-cell が cell level shift で
> 1-cell に降格したものに他ならない。6族横断テーブルの構造的分類
> (d=2 族=2点 vs d=3 族=点) は、§2.3b の「全座標は同一構成のインスタンス」
> という普遍的構成からさらに zoom level を1段下げた帰結。
>
> Temporality は d=2 により 0-cell 層に属し、End(α_V) には寄与しない。
> Chronos 族は Telos/Methodos/Krisis と同じ2点1-圏構造。新たな構造的分類:
>
> | d(族座標) | 族 | z=2 構造 | 数 |
> |:----------|:---|:---------|:---|
> | d=2 | Telos, Methodos, Krisis, **Chronos** | 2点1-圏 | **4** |
> | d=3 | Diástasis, Orexis | 点1-圏 (End ≅ D_∞) | **2** |

[推定 70%] 89% — End(α_V) ≅ D_∞ の同定は以下に依存:
- Scale の可逆性 [推定 90%] — 2極構造 (Mi↔Ma) は定義上双方向 → 構成的に可逆。情報損失モデルでは不成立だが abstract level で十分
- σsσ = s⁻¹ [推定 88%] — /pei+ 数値検証 (2026-03-18): σFσ=F⁻¹ は **dim=2 (SO(2)) でのみ普遍成立** (100/100)、dim≥3 では不成立 (0/100)。Scale の2極構造は1次元パラメータ → dim=2 モデルが適切 → 成立
- Temporality d=2 [確信 90%] — axiom_hierarchy.md CANONICAL (SOURCE)
- 条件: D_∞ 構造は Scale の**各具体 (射) の1次元性** に依存する (下記 §2.1e 参照)

#### 2.1e. Scale の多軸性と D_∞ の普遍性 (2026-03-18 /u+ 対話)

> **発見**: Scale は複数の独立軸 (空間的粒度、時間的粒度、情報的粒度...) を持つ。
> しかし各粒度は **Scale という抽象構造の射 (具体)** であり、全て**構造的に同型**。
> したがって Scale は K₆ 上で**1つのノード**のまま。
>
> | 主張 | 帰結 |
> |:-----|:-----|
> | MB の次元ごとに zoom 操作がある | Scale に n 本の独立軸が存在 |
> | 各軸は構造的に同型 | Scale 全体は1つの抽象構造 |
> | 各具体 (射) が個別に D_∞ を持つ | D_∞ の普遍性は保存される |
> | K₆ は不変 | 6点15辺30パラメータ構造に影響なし |
>
> **精緻化**: /pei+ の dim=2 条件は「Scale **全体**が1次元」ではなく
> 「Scale の**各具体が1次元**」を意味する。各具体の同型性が D_∞ を普遍的に保証する。
>
> 関連発見 (同対話):
> - 「選択」と「決定」は前提 (圏) の選択に依存し、構造的に同型
> - 入れ子は Scale の概念的本質。概念空間で無限に定義可能 (物理的存在とは独立)
> - 概念空間と物理空間は親構造 (圏) の随伴であり、どちらも「本質そのもの」ではない
>
> [推定 70%] 91% — 多軸 Scale が D_∞ と K₆ 構造に矛盾しないことを確認。
> Creator の圏論的直感と /pei+ 実験結果が整合的に統合された。

### 2.2. なぜ「座標は射」か

> **主張**: d(x) = k+1 の実体は、d(x) = k の実体の**射 (morphism)** である。
> 座標は対象と対象の間に存在する**関係**であり、対象そのものではない。

#### 構成的導出

§2.1 で定義した構成距離 d は、FEP からの**追加仮定の数**を数える:

| d | 追加仮定 | 得られるもの |
|:--|:---------|:-------------|
| 0 | なし (FEP そのもの) | Helmholtz 分解 Γ⊣Q = Ext と Int の分離 |
| 1 | + Markov blanket 仮定 | Flow = Ext → Int への認知の流れ |
| 2 | + 直和分解/スカラーゲイン | Value, Function, Precision = Flow の修飾 |
| 3 | + 基底変換/対合 | Scale, Temporality, Valence = 修飾座標の相互関係 |

各ステップで「前のレベルに新しい構造を加えて次のレベルを**派生させる**」操作が行われる。
この「派生」が圏論における射に対応する:

- **d=0→d=1**: Γ⊣Q (0-cell) に MB 仮定を加えると Flow (1-cell) が派生する。
  Flow は Ext と Int の間に走る**関係**であり、Ext や Int そのものではない。
  Γ⊣Q が「場所」ならば Flow は「場所の間を流れるもの」。

- **d=1→d=2**: Flow (1-cell) に追加構造を加えると Value 等 (2-cell) が派生する。
  Value の2極 (Internal / Ambient) は Flow の**モード**であり、Flow の外部に存在する端点ではない。
  同じ認知の流れが「内側から見た世界」と「外側に向けた行動」という2つの様相を持つ。
  その切り替え = 自然変換 α: F_I ⇒ F_A。

- **d=2→d=3**: 修飾座標 (2-cell) にさらなる構造 (基底変換/対合) を加えると
  Scale, Valence, Temporality (3-cell) が派生する。
  Scale は修飾座標の**粒度**を変え、Valence は**方向**を反転し、Temporality は**時間的基底**を変換する。
  これらは修飾座標の間の**関係**であり、修飾座標そのものではない。

#### 米田の補題による裏付け

「対象はその射の全体で完全に決まる」(米田の補題)。

この原理を逆読みすると: **射がなければ対象には内容がない**。
Flow を「対象 (もの)」として捉えると、それは「認知の流れ」という漠然とした概念に留まる。
しかし Flow から Value, Function, Precision への射 (= 修飾) の全体を見ると、
Flow は「内部/外部 × 探索/活用 × 高精度/低精度」の構造を持つ豊かな実体として特徴づけられる。

d=k の実体は、d=k+1 の射によって初めて**区別可能**になる。
座標を「もの」ではなく「関係」として設計したのは、米田の補題が示す「関係が本体を決定する」
という原理の操作化である。

> **§2.1 との接続**: 構成距離 d は出自を数え、cell level は圏内での位置を数える。
> 「d=k+1 は d=k の射」という主張は、root (z=0) では cell level の昇順
> (0-cell → 1-cell → 2-cell → 3-cell) と一致する。zoom level が変わっても
> m→n の射関係は保存される (cell level shift 公式は線形)。

#### 2極 (opposition) の構造

各座標が2極の**対立関係**として定義されるのは、d=2 座標が Galois 接続 F_i⊣G_i を
持つことの帰結 (§2.3b 参照)。2極は F_i の始域と終域、G_i の始域と終域に対応する:

| 座標 | F (左随伴) | G (右随伴) | 2極 |
|:-----|:-----------|:-----------|:----|
| Value | 情報公開 | 情報秘匿 | Internal ↔ Ambient |
| Function | 可能性拡張 | 最良選択 | Explore ↔ Exploit |
| Precision | 注意集中 | 注意拡散 | Certain ↔ Uncertain |

2極は F_i と G_i の**方向**を示す。対立は矛盾ではなく、随伴の2面性
(最小限の構造で最大限の効果を引き出す / 最大限の構造で最小限の誤差に抑える) の表れ。

### 2.3. HGK ≅ Cat(FEP) — 圏としての同型

> **主張**: HGK の実体階層は、FEP を 2-圏 Cat で定式化したときの cell 階層と同型である。
> この同型は zoom level z=0 (root) で成立し、§2.1 の cell level shift 公式により
> 他の zoom level でも整合的に保存される。

#### Root ビュー (z=0) の対応表

| HGK 実体 | d | Cat (FEP) | cell level | 対応の根拠 |
|:---|:--|:---|:--|:---|
| Γ⊣Q | 0 | Ext, Int (0-cell) | 0 | Helmholtz 分解 = 外部/内部の分離 |
| Flow | 1 | F_t: Ext → Int (1-cell) | 1 | 認知の流れ = 外部→内部への関手 |
| 24 Poiesis | 2 | α_t: F_t ⇒ F_{t+1} (2-cell) | 2 | 認知操作 = 関手の改善 (自然変換) |
| CCL 合成 | 3 | 2-cell 間の modification (3-cell) | 3 | パイプライン合成 = 自然変換の組換え |

#### Hom ビュー (z=1) の対応表

§2.1 の cd 操作により cell level が −1 される:

| HGK 実体 | d | z=1 cell level | z=1 での役割 |
|:---|:--|:--|:---|
| Γ⊣Q | 0 | scope 外 | 不可視 (Hom 圏の「外」) |
| Flow | 1 | 0-cell | Poiesis が結合される対象 (CCL 0-cell) |
| 24 Poiesis | 2 | 1-cell | CCL `>>` で結合される射 |
| CCL 合成 | 3 | 2-cell | パイプラインの associator/unitor |

#### 3つの帰結

**帰結 1 — Kalon 同型**: Fix(Q∘Γ) = Fix(G∘F) が cell 階層のレベルで実現する。
FEP の「存在 = VFE 最小化の不動点」と Kalon の「美 = G∘F の不動点」は、
同じ 2-圏の同じ不動点構造の異なる解釈である。

**帰結 2 — Weak 性の局在**: z=0 root では全4層が可視。z=1 Hom では3層が可視で
CCL 合成 (d=3) が 2-cell = associator となり、weak bicategorical 性が出現する。
z=2 では退化定理 (§2.1) により strict 1-圏に退化する。
→ weak 性は z ≤ 1 に**局在**する。

**帰結 3 — d の Cat への忠実な埋め込み**: 構成距離 d は Cat の cell level に
root で一致し、zoom level 変換でも線形にシフトする (cell_level = d − z)。
これは HGK の体系設計が Cat の構造を**忠実に (faithfully)** 反映していることを示す。
d は「たまたま cell level と一致する数」ではなく、Cat の cell 構造の**構成的な反映**。

### 2.3b. 2-cell の統一的構成と4パラメータクラス (v0.9)

> **v0.9 改訂** (2026-03-18): ROM v2.0 (随伴統一像) と旧4種分類の統合。
> **結論**: 全座標は**同一の普遍的構成** (随伴誘導 2-cell) のインスタンス。
> 旧「4種」は構成の**代数的パラメータクラス**であって**型 (type)** ではない。
>
> **CKDF 対応**: この二層構造は CKDF のレイヤー構造に正確に対応する:
> - 普遍的構成 (1種) = CKDF L1 (ガロア接続 F⊣G は1つの構造)
> - 4パラメータクラス = CKDF L2 (F⊣G の内部構造が座標に分解される)
>
> **Q1 との対称**: 最適化 vs Kalon で同一の F⊣G の G の順序構造が退化/非退化を分けたように、
> 2-cell でも同一の随伴誘導 2-cell の F_i⊣G_i の代数的帰結が 4クラスに分かれる。
>
> 📖 ROM: [rom_2026-03-17_adjunction_unified_2cell.md](../../30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/rom_2026-03-17_adjunction_unified_2cell.md)
> 📖 CKDF: [chunk_ckdf_bridge.md](../../10_知性｜Nous/04_企画｜Boulēsis/11_統一索引｜UnifiedIndex/chunk_ckdf_bridge.md) §3

#### 普遍的構成 (1種) — 随伴誘導 2-cell

**定義**: 各座標 c_i は Galois 接続 F_i ⊣ G_i を持ち、Flow に対する 2-cell を誘導する:

> α_{c_i}: Flow ⇒ G_i ∘ Flow ∘ F_i

全座標がこの**同一の構成**のインスタンスである。代数的帰結 (⊕, ·, σ, f, ⊣) は
随伴 F_i ⊣ G_i の性質から自然に出る**パラメータ**であって**型**ではない。

#### 4パラメータクラス — 代数的帰結による分類

| クラス | 代数構造 | 座標 | 圏論的構成 | 確信度 |
|:---|:---------|:-----|:-----------|:-------|
| **I. 直和分解** | F ≅ F_L ⊕ F_R | Value, Function | コプロダクト | [確信 90%] 85% |
| **II. スカラーゲイン** | α_π: F ⇒ πF | Precision | [0,1]-モノイド作用 | [推定 70%] 80% |
| **III. 基底変換** | φ*F | Scale, Temporality | Grothendieck 構成 | [推定 70%] 87% |
| **IV. 対合** | σ: F ⇒ F, σ²=id | Valence | Z/2Z-equivariant | [確信 90%] 92% |

**I. 直和分解 (Value, Function)**:
VFE/EFE の内部成分分解。Value は F ≅ F_E ⊕ F_P (認識的/実用的)、Function は F ≅ F_Explore ⊕ F_Exploit。Smithe Thm46 の加法性 F(M₁⊗M₂) = F(M₁) + F(M₂) が裏付け。

**II. スカラーゲイン (Precision)**:
精度重みの乗法的スケーリング。Γ_Precision = 「δ→Dirac の崩壊」(basis.py) が示すように、射影 (π²=π) はゲインの連続極限 (π→∞) であり独立種ではない。Proietti γ/γ' の ODE が動的ゲインを実装。

**III. 基底変換 (Scale, Temporality)**:
2つの独立な基底変換。**Temporality** = VFE↔EFE の時間的架橋。F_T(Extend)⊣G_T(Marginalize) の随伴検証 (De Vries 2025) が決定的 [確信 90%]。**Scale** = MB 入れ子の空間的解像度変換。F_S(Coarse-grain)⊣G_S(Refine) [推定 84%]。粗視化 = 変数 marginalization (DPI で Complexity 削減)、詳細化 = top-down 予測 (generative model の p_model に制約)。η は DPI + FEP 成立条件 (sparse coding/予測符号化) [82%]、ε は DPI 二重適用 + 生成モデル不完全性 [78%]。Value/Function が汎関数の**内部**分解であるのに対し、Scale/Temporality は**異なる軸の基底変換** (空間/時間)。

> **P2 RESOLVED — De Vries "augmented" ≡ F_T "Extend" の形式対応** [確信 92%]
> [SOURCE: De Vries et al. 2025 arXiv:2504.14898 §2, §4 Theorem 1, Appendix A HTML 原文精読]
>
> De Vries Theorem 1 は p(y,x,θ,u) に preference prior p̂(x) + epistemic priors p̃(·) を追加した
> "augmented generative model" 上の VFE 最小化が E_q(u)[G(u)] + B(u) に分解されることを証明。
> F_T(Extend) は p(o,s) に方策空間 π + preference prior C を追加する操作。
> 変数同定: y↔o, x↔s, u↔π, p̂(x)↔C, p̃(·) は π の prior に暗黙吸収。
> De Vries のaugmentation は F_T(Extend) の**特殊ケース** (θ を暗黙化)。
> F_T は De Vries の構成を**圏論的に一般化** (G_T との随伴構造を与える)。
> 差分: De Vries は θ 学習・Complexity B(u) を明示。F_T は随伴構造を提供。
>
> **P3 RESOLVED — G_T 単調性** [推定 82%]
> marginalization は DPI (Data Processing Inequality) により VFE を増大させない。
> 方策変数の独立消去により前順序も保存される。
> 詳細: [temporality_adjunction_proof.md v3.0](file:///home/makaron8426/.gemini/antigravity/brain/7f4fd0a1-090d-4992-8d36-1cb1f21ac5c2/temporality_adjunction_proof.md) §2.2b, §2.4
>
> **Scale F_S⊣G_S 随伴構成** [推定 84%]
> F_S(Coarse-grain): Micro→Macro (変数 marginalization)。G_S(Refine): Macro→Micro (top-down 予測)。
> η: DPI による Complexity 削減 + FEP 文脈での十分条件 (sparse coding, 予測符号化, m-projection) [推定 82%]
> ε: DPI 二重適用 (G_S は p_model 依存で相互情報量を増やさない、F_S は marginalization) + 生成モデル不完全性 [推定 78%]
> Fix(G_S∘F_S) = 最適スケールで記述されたモデル (= RG の固定点構造)。
> 詳細: [scale_species_analysis.md](file:///home/makaron8426/.gemini/antigravity/brain/7f4fd0a1-090d-4992-8d36-1cb1f21ac5c2/scale_species_analysis.md) §2.2-2.3

**IV. 対合 (Valence)**:
VFE 勾配方向の符号反転。Smithe Thm46 対偶による半直積 6⋊1 証明: v=0 → φ(0)≈id, v≠0 → φ(v)≠id。σ²=id (2回適用で恒等)。
dagger (反変, L1 射の反転) でも Egger involutive monoidal (共変, L2 対象/テンソル反転) でもなく、**Z/2Z-equivariant 自然変換** (L3 関手の対称性) である。3類型が3階層に対応し、クラス IV の L3 独立性を裏付ける。

**パラメータ空間の網羅性 [推定 85%]**: V=[0,1]-豊穣の構造から4クラスが尽きることを形式的に証明。(1) L1 (Hom値): Mostert-Shields 定理により ⊕=max (余積) と ⊗=× (モノイダル積) の2演算で尽きる (min は束双対で導出可能、Łukasiewicz は × の代替選択)。(2) L2 (基底): Eilenberg-Kelly change-of-base 2-functor T*: V-Cat → W-Cat の特殊化。(3) L3 (関手): Egger involutive monoidal category の特殊化。(4) 第4階層は V-Cat の定義 (Ob, Hom_V, ∘, id) に存在しない。

> 詳細な論証: [2cell_species_analysis.md](file:///home/makaron8426/.gemini/antigravity/brain/54266021-2488-49d2-91af-f81022674e25/2cell_species_analysis.md) §3.5, §4.5

### 2.4. 能動推論の圏論的形式化

> **v0.4 — 未解決問題 #2 の解決候補**

#### 2.4.1. 知覚推論 vs 能動推論：2つの VFE 最小化メカニズム

VFE(F) = sup_x D(F(x), (Q∘Γ)(x)) を最小化する方法は2つある:

| メカニズム | 操作対象 | 圏論的記述 | cell level |
|:--|:--|:--|:--|
| **知覚推論** | 関手 F を更新 | α: F_t ⇒ F_{t+1} (自然変換) | **2-cell** |
| **能動推論** | 圏 Ext を変形 | A: Ext → Ext' (関手) | **1-cell** (Cat の) |

知覚: VFE(F_{t+1}) ≤ VFE(F_t) — F を変えて VFE を減らす
能動: VFE'(F) ≤ VFE(F) — Ext を変えて VFE の定義域を変える

#### 2.4.2. 「0-cell を変形する自然変換」の修正

旧 §2.4 (v0.3) の記述「能動推論は自然変換が cell 階層を遡上するケース」は**不正確**:

- 自然変換 (2-cell) は関手間の射であり、圏 (0-cell) を変形しない
- 能動推論は 2-圏 Cat の **1-射** (関手 A: Ext → Ext') として形式化すべき

**行為 A: Ext → Ext'** は:
- Ext の対象 (観測可能な状態) を Ext' の対象に写す
- Ext の射 (状態遷移) を Ext' の射に写す
- 環境の因果構造を変形する操作

#### 2.4.3. Double Category による統一定式化

知覚と能動を**同時に**行うのが現実の認知エージェント。

> **定義**: FEP の double category **D_FEP** を以下で定義する:

```
D_FEP の構成:
  0-cell: Markov 圏 (Ext_t, Int_t の組)
  水平 1-cell: 関手 F: Ext → Int (知覚モデル)
  垂直 1-cell: 関手 A: Ext → Ext' (行為)
  2-cell: 整合正方形 (下記)
```

整合正方形:

```
         F_t
  Ext -------→ Int
   |             |
 A |      σ      | Id
   ↓             ↓
  Ext' ------→ Int
         F_{t+1}
```

σ は以下を満たす:
1. **VFE 降下**: VFE'(F_{t+1}) ≤ VFE(F_t)
2. **自然性**: A が Ext を変形し、α が F を更新する組合せが整合的

- 水平合成 = 知覚推論の列 (F_0 ⇒ F_1 ⇒ F_2 ⇒ ...)
- 垂直合成 = 能動推論の列 (Ext → Ext' → Ext'' → ...)
- 2-cell 合成 = 知覚と能動が同時に進行する学習ステップ

#### 2.4.4. VFE 最小化の統一表現

**知覚推論**: D_FEP の水平射の列で VFE が (0,∞]-順序圏上で単調減少
**能動推論**: D_FEP の垂直射の列で VFE の**定義域**が変化しつつ単調減少
**統合 FEP**: D_FEP の 2-cell の列 (σ_0, σ_1, ...) で、VFE が不動点 Fix(Q∘Γ) に収束

$$\text{FEP} = \lim_{t \to \infty} \sigma_t = (F^*, \text{Ext}^*) \in \text{Fix}(Q \circ \Gamma)$$

#### 2.4.5. Smithe (2022) との関係

Smithe の Bayesian lens/optics は**この double category の特殊ケース**と見なせる:
- Lens (get, put) = (F: Ext→Int, A: Int→Ext) の対
- get = 水平射 (知覚), put = 垂直射の逆方向 (行動)
- Double category は lens よりも一般的: 行為 A が必ずしも Int からの feedback に限定されない

> **確信度**: [推定 75%] — double category 定式化の構造的整合性は高い。形式的検証 (2-cell の合成則の確認) が残存。
> **残存課題**: Int 側の変形 (行為が Int も変える場合) の処理。上の正方形では右辺を Id としたが、一般には Int → Int' も必要な場合がある。

---

## §3. Kalon との同型

| Kalon | FEP |
|:--|:--|
| F = 発散 (Explore) | Q = 循環流 (solenoidal) |
| G = 収束 (Exploit) | Γ = 勾配流 (gradient) |
| Fix(G∘F) = 美・品質 | Fix(Q∘Γ) = 存在・自己エビデンス |
| 自然変換 = G∘F の反復 | 自然変換 = 学習の反復 |
| T-algebra (C^T) | Helmholtz モナドの代数 = 「溶かして固めても変わらないもの」|
| η: x → T(x) = 溶媒に浸す | 知覚推論の開始 (prior を generative model に通す) |
| μ: T²→T = 二度漬け不変 | 二重推論 = 一回推論 (冪等性から自明) |

**FEP の Kalon 判定: ◎**

- Fix(G∘F): 蒸留しても展開しても形が変わらない ✅
- Generative: 知覚推論、能動推論、記憶、予測、U シリーズ、7座標 が全て導出可能 ✅
- Self-referential: 「FEP の最良の定式化は？」= FEP そのもの (最良の関手を自然変換で探す) ✅

---

## §4. 圏論の認識論的地位

### 4.1. 結論

圏論は FEP の公理でも定理でもなく、**全ての系の暗黙の前提** (公理)。

### 4.2. 論証

```
P1: 系 ≒ 圏 (対象 + 射 + 合成則)
P2: 圏なしに系なし
∴  圏論は全ての系の前提 = 公理
```

### 4.3. HGK 内での位置

- 圏論 = **形式的公理** (構造の文法。全ての理論が共有)
- FEP = **内容的公理** (認知エージェントについての主張)
- HGK の「1公理体系」= 内容的公理が1つという意味

axiom_hierarchy.md の L0.T (Basis, 体系核外) は圏論の暗黙の公理としての地位と整合する。

---

## §5. 既存研究との関係

| 研究 | 使用する圏構造 | FEP の何を捉えるか | Kalon 判定 |
|:--|:--|:--|:--|
| Smithe (2021) | Bayesian Lens | 予測-更新の双方向性 | ◯ (実装) |
| Fritz (2020) | Markov Category | 確率論の基盤 | ◯ (基盤が汎用すぎ) |
| Spivak & Niu (2021) | Polynomial Functor | 動的系の合成 | ◯ (汎用すぎ) |
| **本定式化** | **関手圏 + 自然変換** | **FEP の本質 = 忠実関手の収束** | **◎** |

他の3説は FEP を**記述する道具**。本定式化は FEP が**言っていること自体**。

---

## §6. 遊学エッセイとの系譜

本定式化は遊学エッセイシリーズの論理的帰結:

1. 「バカをやめたいなら構造を見ろ」§4: 構造 = 射 (1-cell)
2. 同 §5: アナロジー = 関手 (1-cell → 1-cell)
3. 同 §7.4: アナロジーの改善 = 自然変換 (2-cell)
4. **本文書**: 認知 = 自然変換の VFE-降下流
5. FEP = 自然変換の収束先 = Fix(Γ⊣Q)

U シリーズ = 自然変換を「忘れる」方向:
- U_arrow = 射を忘れる (1-cell の喪失)
- U_compose = 合成を忘れる (1-cell の合成の喪失)
- U_context = 自然変換を忘れる (2-cell の喪失)
- U_adjoint = 随伴の片方を忘れる (Γ または Q の片方を見ない)

---

## §7. 未解決問題

| # | 問題 | 確信度 | 更新 |
|:--|:--|:--|:--|
| 1 | VFE: [Ext, Int] → [0,∞] の厳密な定義 (Lawvere + Baez-Fritz ハイブリッド) | [推定 80%] | ↑ v0.4: §1.4 追加 |
| 2 | 能動推論 = double category D_FEP による統一定式化 | [推定 75%] | ↑ v0.4: §2.4 全面改訂 |
| 3 | F* = Fix(Q∘Γ) がいつ存在するか (Banach-Lawvere + Grothendieck 不変切断) | [推定 70%] | ↑ v0.5: §1.5 追加 |
| 4 | Smithe の Bayesian Lens と本定式化の形式的関係 | [推定 85%] | ↑ v0.2 |
| 5 | 本定式化の独自性の確認 (先行研究の完全な調査) | [確信 92%] | ↑ v0.2 |
| **6** | **2-cell 統一構成 + 4パラメータクラス** (普遍的構成 = 随伴誘導 / 代数的分類 = Mostert-Shields 網羅性) | **[推定 87%]** | **↑ v0.9: ROM v2.0 統合。1種+4パラメータクラスの二層構造** |
| **7** | **weak_2_category.md の L3 再構成** → 単一 bicategory + zoom level で統一。L3-operational は Hom(Ext,Int) への cd | **[推定 80%]** | **↑ v0.8: zoom level 解釈。カテゴリーミステイク撤回** |
| **8** | **Γ⊣Q が 2つの 0-cell** (Ext, Int)。zoom level で見れば 24 Poiesis も正当な 0-cell | **[推定 85%]** | **↑ v0.8: root=2個, Hom view=24個。zoom level 依存** |

### 7.1. 独自性調査記録 (v0.2 — 2026-03-16)

3つのギャップを全て閉じた:

| ギャップ | 調査方法 | 結果 | SOURCE |
|:--|:--|:--|:--|
| Smithe PhD thesis (232p) | pdftotext フルスキャン | natural transformation=§2.2基礎定義のみ, free energy=§5.3 loss model (Def 5.3.26), convergence/fixed point=4箇所(全無関係), Helmholtz=2箇所(名称由来のみ) → **不在** | arXiv:2212.12538v3 PDF |
| nLab | FEP ページ=404不在, Bayesian reasoning 圏論セクション=4本(Sturtz/Culbertson/Kamiya/Smithe) | **不在** | ncatlab.org |
| arXiv 2025-2026 | Periskopē 33件検索 | 直接的先行研究 **なし** | Periskopē search |

**Smithe との本質的差異**:
- Smithe: Bayesian lens/optics ベースの**合成的**ベイジアン推論 (predictive coding 回路の圏論的意味論)
- 本定式化: 関手圏上の**力学的**な VFE 降下流 (FEP が「言っていること自体」の定式化)
- Smithe は natural transformation を基礎定義 (§2.2) で導入後、optics/lens の文脈でのみ使用。関手圏上の「自然変換の列としての学習」は扱っていない。

残存リスク:
- Smithe の 2023-2026 ポストPhD 論文 (未調査) [推定: 低リスク — 研究方向が optics/polynomial functor 側に収束]
- Capucci 等の unpublished preprint [推定: 低リスク]

---

*Seed v0.7 — 2026-03-17*
*v0.1: 初期定式化 (セッション 97f74f23)。v0.2: 先行研究ギャップ閉鎖。*
*v0.3: §2 を d=cell 仮説で全面改訂。L3 の 0-cell カテゴリーミステイクを特定。(セッション 03a2c373)*
*v0.4: §1.4 VFE 厳密定義を追加 (Lawvere + Baez-Fritz ハイブリッド)。§2.4 能動推論の double category 定式化。(セッション 97f74f23)*
*v0.5: §1.5 不動点存在条件の形式化。Banach-Lawvere 条件 + Grothendieck 不変切断 + ε-近似/lax/ω-極限。Kalon との接続。(セッション 97f74f23)*
*v0.6: §2.1 に 2-cell 4種分類を統合。Temporality→種III (基底変換) 確定 [推定 85%]。d値と種の独立性を明示。#6 確信度 65%→70%。(セッション 7defe575 + 54266021)*
*v0.7: Helmholtz モナド T=(Φ,η,μ) の構造を §1.5.2 に明示。T-algebra = C^T = Fix(T) の描像を追加。§3 Kalon 同型表に η/μ/C^T の対応行を追加。(セッション 675e3b21)*
*v0.7.1: Precision 種II 深化。Γ_Precision 「δ→Dirac」= ゲインの連続極限により射影の独立種化を棄却。4種全確定: I:85%/II:80%/III:85%/IV:90%。#6 確信度 70%→75%。(セッション 54266021)*
*v0.7.2: Scale 種III 独立検証 (φ*⊣φ_* 随伴, 85%)。4種網羅性論証 (V-豊穣 3階層×2演算, 70%)。(セッション 54266021)*
*v0.7.3: Mostert-Shields 定理による L1 唯一性の形式的証明 (65%→85%)。先行研究裏付け: Kelly change-of-base (種III), Egger involutive monoidal (種IV)。ROM: rom_2026-03-17_2cell_exhaustion_proof.md。(セッション 54266021)*
*v0.7.4: 種IV 3類型精密化。dagger(L1)/involutive monoidal(L2)/Z/2Z-equivariant(L3) の比較、3階層到1対応により種IV確信度 90%→92%。(セッション 54266021)*
*v0.8: §2.0 カテゴリーミステイク撤回。zoom level 解釈により L3 統一。#7: 60%→80%, #8: 50%→85%。CCL 非結合性を compile_ccl テストで実証。(セッション 07330cf0)*
*v0.9: §2.3b 4種→統一構成+4パラメータクラス。ROM v2.0 (随伴統一像) 統合。CKDF L1/L2 対応+Q1対称を注記。#6: 85%→87%。(セッション 6e06a20f)*
