# 行為可能性は忘却である — Coherence Invariance 定理と G∘F 結晶化の普遍性

**Paper VI — v1.1 (2026-04-12)**

> *概要.* Euporía の行為可能性増大原理 (AY > 0) は、忘却関手 G の商写像構造から導出できる。本稿は Linkage ドメインで 130+ 実験により実証された Coherence τ-Invariance——G∘F の不動点における平均 Coherence が制御パラメータ τ に依存しない——を G∘F 随伴一般の性質として証明し、Cognition・Description ドメインへの転用を実験的に検証する。中心的主張: **忘却 (G) は情報を殺すのではなく、行為可能性の商空間を開く。** Kalon = Fix(G∘F) は、行為可能性を最大化する情報単位への「結晶化」として3ドメイン共通に定式化される。
>
> **先行論文との関係:** Paper I (力は忘却である) — 忘却場 Φ と力 F_{ij}。Paper II (相補性は忘却である) — CPS, Drift, d = ker(d) への商写像。Paper III (Markov 圏の向こう側) — α ≤ 0 セクター。Paper IV (効果量減衰) — 効果量 √ρ_spec の減衰。Paper V (繰り込みは忘却である) — RG 不変性。本稿は「忘却が力を生む」メカニズムの**認知科学的インスタンス**を3ドメインで構成する。
>
> **後続論文との関係:** Paper VII (知覚は忘却である) — 普遍フィルトレーション U_arrow ≤ ⋯ ≤ U_self の各段階は、G∘F 結晶化の解像度レベルに対応する。Paper VIII (圏論的基礎における存在) — α-忘却濾過 {C_α} の公理系 (F1)-(F4) において、G∘F の結晶化パラメータ τ は α パラメータの操作的対応物として位置づけられる。
>
> **記号規約:** 本稿の ρ はチャンク内コヒーレンス ρ_coh（Def. 3.1.1）を指し、Paper IV のスペクトラム効率 ρ_spec ≡ Var(Ξ_obs)/Var(Ξ_theory) とは**異なる量**である。また、本稿の F は溶解関手（Def. 2.1.1, F ⊣ G 随伴対の左随伴）を指し、Paper I/III/IV/V の忘却曲率テンソル F_{ij} とは**異なる対象**である。統一記号表 (unified_symbol_table.md §1.5, §1.7) を参照。

---

## §1. 序論: なぜ忘却が行為可能性を増やすのか

### 1.1 フック

直観に反する: 忘れることが、できることを増やす。
しかし日常にこの例は溢れている。

- 地図は地形を忘れる → 道が見える (= 行為可能性: 経路選択)
- 要約は詳細を忘れる → 判断が可能になる (= 行為可能性: 意思決定)
- 結晶化は溶媒を忘れる → 構造が出現する (= 行為可能性: 操作可能な単位)

Paper I は「忘却が力を生む」を方向性定理 F ≠ 0 ⟺ dΦ∧T ≠ 0 で証明した。
本稿は「力」を「行為可能性 (affordance)」として具体化する。

忘却 → 商空間 → 商空間上の新しい射 → 行為可能性の増大

### 1.2 Euporía と忘却場の接続

Euporía (axiom_hierarchy.md): 全ての WF 射 f: A → B は |Hom(B, −)| > |Hom(A, −)| を満たさなければならない。

忘却論 (Paper I-V): 忘却関手 G: C → D は ker(G) に射影し、商空間 D = C/ker(G) を生成する。

**接続**: G の商写像が新しい射を生む条件は何か？

```
G: C → C/ker(G)

|Hom(C/ker(G), −)| > |Hom(C, −)|  ← AY > 0

⟺ ker(G) への射影が Hom を増やす
⟺ 忘却が行為可能性を増大させる
```

これは直観的には自明ではない。射影は一般に射を減らす (データ処理不等式)。
しかし、**Hom(C, −) ではなく Hom(C/ker(G), −) を測っている**点が鍵。
商空間の対象は「粗い」が、粗いからこそ**より多くの対象と関係を持てる**。

### 1.3 本稿の構成

- §2: G∘F 結晶化の定式化 — 3ドメイン共通の構造
- §3: Coherence τ-Invariance 定理 — 十分条件の導出
- §4: Linkage ドメインの実験的検証 (130+ 実験のまとめ)
- §5: Cognition ドメインへの転用と実験
- §6: Description ドメインへの転用と実験
- §7: 忘却と行為可能性の一般理論
- §8: 検証可能な予測と展望

---

## §2. G∘F 結晶化の定式化

### 2.1 結晶化の公理的定義

**定義 2.1.1 (結晶化随伴).** 意味空間 Ω 上の結晶化随伴 F⊣G とは:
- F (溶解): 結晶 → 場。情報単位の境界を溶解し、場の自由度を回復する射
- G (結晶化): 場 → 結晶。場の自由度を固定し、情報単位として析出する射
- Fix(G∘F) = Kalon な結晶 = AY を最大化する情報単位

**公理 C1 (τ-相対性):** G は制御パラメータ τ に依存する。τ は「結晶化温度」に対応。
- 高 τ (低温): 細かい結晶。各結晶の内部は高 Coherence
- 低 τ (高温): 粗い結晶。各結晶の内部は不均一

**公理 C2 (収束性):** Fix(G∘F) は有限反復で到達する。

**公理 C3 (ker 構造):** G は ker(G) への商写像。ker(G) は G が溶かせない座標の集合。

### 2.2 3ドメインのインスタンス

| | Linkage | Cognition | Description |
|:--|:--|:--|:--|
| **Ω (場)** | embedding 空間 | WF 状態空間 | 読者の解釈空間 |
| **結晶** | チャンク | WF ステージ | 指示単位 |
| **F (溶解)** | merge (小チャンクを結合) | 浅い段階の統合 | 類似指示の統合 |
| **G (結晶化)** | split (低 coherence を分割) | 過大段階の分解 | 曖昧指示の具体化 |
| **τ** | similarity threshold (連続) | depth (連続) | granularity (連続) |
| **ker(G)** | {Scale, Valence} | [要実験] | [要実験] |
| **AY の意味** | |Act_1(c)| − |Act_0(c)| | WF 行為増分 | 読者行為増分 |

**注 (τ の連続性):** WF depth (L0-L3) は便宜的離散化。実際の depth は連続量 (注意資源の配分比)。Description の granularity も同様に連続。離散表現は連続量の量子化にすぎない。

### 2.3 忘却論との同型 — d = ker(d) と G = ker(G)

Paper II §1.1 は微分 d の本質を次のように精密化した (前セッション 2026-03-29 修正):

> **d は ker(d) = ℝ (1次元) への商写像であり、忘却は積分定数のみに局在する。**
> d: C^∞ ↠ C^∞/ℝ

この商写像構造が Paper VI の結晶化 G と**同型**であることを示す。

#### 2.3.1 商写像としての忘却: 構造的対応表

| 構造 | Paper II: 微分 d | Paper VI: 結晶化 G | 同型の根拠 |
|:--|:--|:--|:--|
| **作用域** | C^∞(M) (滑らかな関数空間) | Ω (意味空間) | ともに「場」上の操作 |
| **操作の本質** | ker(d) = ℝ への商写像 | ker(G) への商写像 | ともに商写像 — 核に射影して商空間を開く |
| **核 (ker)** | ℝ (定数関数。1次元) | {Scale, Valence} (2座標。有限次元) | 核は有限次元部分空間。忘却は全体ではなく**局在する** |
| **核の外** | k ≠ 0 のフーリエモードで d は可逆 (スケーリング+回転) | ker(G) の補空間で G は構造を保存 (Coherence 保存) | 核の外では**情報損失ゼロ** |
| **商空間** | C^∞/ℝ (定数差を同一視した空間) | Ω/ker(G) (Scale・Valence 差を同一視した空間) | 商空間は「粗い」が、粗いからこそ**射が増える** |
| **逆操作** | ∫_a^x (初期条件 a を選ぶ切断) | F (溶解: 結晶を場に戻す) | ともに商写像の不完全な逆 |
| **unit η** | ∫∘d = id + C (C = f(a) — 対象ごとに異なる) | F∘G ≠ id (τ 依存で元の場に戻らない) | ともに η が**非自然**。復元が一意でない |
| **η の障害** | 全関数に整合的な初期条件 a を選べない | 全結晶に整合的な τ を選べない | 障害は**忘却量の大きさ**ではなく**復元経路の不定性** |
| **ループ** | sin→cos→-sin→-cos→sin (d の4次巡回) | G∘F→G∘F→Fix (1-2反復収束) | ともに核の外で操作が**閉じる** (構造保存) |
| **Drift** | Θ = ‖η - id‖ = |C| (復元の非一意性) | Drift = 1 - ε (bye→boot で失われた文脈) | ともに「忘却量」ではなく「**復元の非一意性の測度**」 |

#### 2.3.2 なぜ商写像が行為可能性を生むのか

Paper II §1.1 の枠組みで、d が行為可能性を増大させるメカニズムを記述する:

```
d: C^∞(M) → C^∞(M)/ℝ

微分方程式 dy/dx = f(x) の解集合:
  d 適用前: f(x) は C^∞ の1点 → Hom(f, −) は f からの射の集合
  d 適用後: [f] ∈ C^∞/ℝ は同値類 → 同値類の全元が解 → |Hom([f], −)| > |Hom(f, −)|

AY(d) = |Hom(C^∞/ℝ, −)| − |Hom(C^∞, −)| > 0
```

同じ構造が G に成立する:

```
G: Ω → Ω/ker(G)

結晶化後のチャンク [c] ∈ Ω/ker(G):
  G 適用前: テキスト全体は Ω の1点 → 到達可能な操作は限定的
  G 適用後: チャンク [c] は Scale・Valence を同一視 → より多くの対象と関係可能
  → |Act_1(c)| > |Act_0(c)|

AY(G) = Σ_c (|Act_1(c)| − |Act_0(c)|) > 0
```

**核心**: 商写像は情報を「殺す」のではなく「同値類を作る」。同値類の各元は、元の空間では異なる対象だったが、商空間では同一の対象として**新しい射の起点**になる。射が増える = 行為可能性が増大する。

これは Paper I の方向性定理 F ≠ 0 ⟺ dΦ∧T ≠ 0 の具体化である。忘却場 Φ の勾配 (dΦ) が捩れ (T) と非零の外積を持つとき力が生じる——Paper VI の言語では、ker(G) が Ω の部分空間として**非自明**であるとき (= 全てを忘れるのでも何も忘れないのでもないとき)、商空間上に新しい射が出現する。

#### 2.3.3 d ⊣ ∫ の障害と F ⊣ G の障害の同型

Paper II §1.1 は d ⊣ ∫ が**直接随伴にならない**ことを明示した。理由: η: Id → ∫∘d の非自然性 (初期条件 C = f(a) が関数ごとに異なる)。Zhang–Guo–Keigher の分配則 λ: DT ⇒ TD が迂回路を提供する。

F ⊣ G にも同じ障害が存在する:

| 障害の構造 | d ⊣ ∫ | F ⊣ G |
|:--|:--|:--|
| **η が自然変換にならない理由** | C = f(a) が対象ごとに異なる | Fix(G∘F; τ) が τ ごとに異なる |
| **迂回路** | DRB 圏 (微分 Rota-Baxter 代数) 経由の分配則 | G∘F の**反復** (gf_iterate) による不動点到達 |
| **迂回路の圏論的意味** | モナド/コモナドの混合分配則 λ | **idempotent monad** (G∘F)^n = (G∘F)^{n+1} (n ≥ 2) |

**重要な差異**: d ⊣ ∫ の障害は**原理的** (η の非自然性は解消不能)。F ⊣ G の障害は**実用的には解消可能** (Fix(G∘F) が有限反復で到達するため、不動点上では G∘F が冪等モナドとして機能する)。これは Paper III の α 分類で言えば: d ⊣ ∫ は α > 0 (Markov 圏の内部) だが η が非自然、F ⊣ G は Fix(G∘F) 上で α → 1 (ほぼ対称) に近づく。

#### 2.3.4 ker の構造比較と忘却の幾何

| ker の性質 | d | G (Linkage) | G (Cognition) | G (Description) |
|:--|:--|:--|:--|:--|
| **次元** | 1 (ℝ) | 2 ({Scale, Valence}) | [要実験] | [要実験] |
| **余次元** | ∞ − 1 ≈ ∞ | 4 (残り4座標) | [要実験] | [要実験] |
| **忘却の割合** | 1/∞ → 0% (ほぼ何も忘れない) | 2/6 = 33% | [要実験] | [要実験] |
| **行為可能性の源** | 微分方程式の解空間 | チャンク間の新しい連結 | WF の新しい分岐 | 読者の新しい解釈 |

**Paper V (繰り込みは忘却である) との接続**: ker(G) の次元は Paper V の β 関数 β_Φ = dΦ/d(ln μ) の固定点構造と対応する。ker(G) が小さい (= 忘却が少ない) ほど商空間が元の空間に近く、τ-invariance が成立しやすい。ker(G) が大きすぎると商空間が退化し、結晶化が意味を持たなくなる (Paper III の α < 0 セクター = copy 不能)。

**予測**: 3ドメインの ker(G) の次元比較が、各ドメインの τ-invariance の成立しやすさを予言する。ker(G) が小さいドメインほど τ-invariance が強い。Linkage (ker = 2/6 = 33%) で range = 0.008 なら、ker がより小さいドメインでは range < 0.008 が期待される。

---

## §3. Coherence τ-Invariance 定理

### 3.1 Coherence の定義

**定義 3.1.1 (Interior Boundary Coherence).** 結晶 c = [s₀, s₁, ..., s_n] の Coherence を、c 内部の隣接ペア間の整合性測度の平均として定義する:

```
Coh(c) = (1/(n-1)) Σ_{i=0}^{n-2} ρ(s_i, s_{i+1})
```

ここで ρ: Ω×Ω → [0,1] はドメイン固有の整合性測度。n = 1 (単一要素) の場合 Coh(c) = 1.0 と定める。

**重要**: Coherence は結晶の**内部境界ペア**の平均であり、結晶間の外部境界ペアは含まない。この区別が §3.2 の証明の鍵になる。

| ドメイン | ρ の具体形 | 測定手段 |
|:--|:--|:--|
| Linkage | cosine similarity (embedding) | Hyphē 実装済み |
| Cognition | WF 段階間の目的整合性 | LLM-as-judge / rubric scoring |
| Description | 指示文間の論理的一貫性 | inter-annotator agreement / perplexity |

**定義 3.1.2 (全体 Coherence).** 結晶集合 {c₁, ..., c_m} の全体 Coherence を:

```
C̄ = E_c[Coh(c)] = (1/m) Σ_{j=1}^{m} Coh(c_j)
```

τ-Invariance 定理は C̄ が τ に依存しないことを主張する。

### 3.2 F と G の Coherence への作用メカニズム

定理の十分条件を述べる前に、F と G が Coherence をどう変えるかを精密に記述する。

#### 3.2.1 F (溶解/merge) の作用

F は小さい結晶を隣接結晶に結合する。結晶 c₁ = [s₀, ..., s_k] と c₂ = [s_{k+1}, ..., s_n] を結合するとき:

```
F(c₁, c₂) = [s₀, ..., s_k, s_{k+1}, ..., s_n]

内部ペア集合: {c₁ の内部ペア} ∪ {(s_k, s_{k+1})} ∪ {c₂ の内部ペア}
                                    ↑ 新規追加
```

**F が追加するペア** (s_k, s_{k+1}) は、元々 c₁ と c₂ の**境界**にあったペアであり、結合により**内部**に移動する。このペアの ρ 値は一般に低い (境界 = coherence が途切れる場所)。

**Coherence への影響**:

```
Coh(F(c₁,c₂)) = [Σ(c₁の内部sim) + ρ_boundary + Σ(c₂の内部sim)] / (n-1)
```

ρ_boundary < Coh(c₁) かつ ρ_boundary < Coh(c₂) のとき (典型的)、merge は Coherence を**下降**させる。

#### 3.2.2 G (結晶化/split) の作用

G は結晶内部で最低の ρ 値を持つペアを見つけ、そこで分割する:

```
c = [s₀, ..., s_k, s_{k+1}, ..., s_n]  ここで ρ(s_k, s_{k+1}) = min(内部ペア)

G(c) = (c_left = [s₀, ..., s_k],  c_right = [s_{k+1}, ..., s_n])
```

**G が除去するペア** (s_k, s_{k+1}) は、内部ペアの最小値。分割により**内部から外部境界に移動**する (= Coherence の計算から除外される)。

**Coherence への影響**:

```
Coh(c_left)  = mean({内部ペア} \ {ρ_min})  — ρ_min より高い
Coh(c_right) = mean({内部ペア} \ {ρ_min})  — ρ_min より高い
```

split は常に Coherence を**上昇**させる (最小値を除去するため)。

#### 3.2.3 F と G の対称性: 同じプールの出し入れ

```
        内部ペア集合           外部境界ペア集合
        ┌──────────┐          ┌──────────┐
 G:     │ ρ_min ──────────→   │ ρ_min    │   (内部→外部: Coh 上昇)
        │          │          │          │
 F:     │ ρ_bnd ←──────────   │ ρ_bnd    │   (外部→内部: Coh 下降)
        └──────────┘          └──────────┘
```

**F と G は、低類似度ペアを内部と外部の間で対称的に転送する。** F は外部境界ペアを内部に入れ (Coherence 下降)、G は内部の最低ペアを外部に出す (Coherence 上昇)。

### 3.3 十分条件の形式的記述

**定理 3.3.1 (Coherence τ-Invariance).** 結晶化随伴 F⊣G が公理 C1-C3 を満たし、かつ以下の3条件を全て満たすとき、全体 Coherence C̄ は τ に依存しない。

**(S1) 共通測度条件:** F と G が同一の整合性測度 ρ を参照する。

```
F の結合判定: 結晶サイズ < min_steps (ρ を直接参照しない)
G の分割判定: 内部ペア ρ(s_i, s_{i+1}) < τ

ただし F が内部に追加するペアの ρ 値は、ρ の分布から抽出される
→ F と G が操作する「低類似度ペア」は同じ ρ 分布からのサンプル
```

**直観**: F が入れる不純物と G が取り出す不純物が、同じ「種類」の不純物であること。再結晶精製で言えば、溶媒が同じなので溶け方と析出の仕方が対称的。

**(S2) 不動点の存在と一意性:** Fix(G∘F) が有限反復で到達し (C2 より)、かつ不動点が一意 (境界集合が一意に確定する)。

```
不動点条件: ∀ 内部ペア ρ(s_i, s_{i+1}) ≥ τ  (これ以上 split できない)
          ∧ ∀ 結晶 |c| ≥ min_steps         (これ以上 merge の必要がない)
```

**直観**: G∘F が「止まる」場所が1つしかないこと。複数の不動点があると τ によって異なる不動点に落ちる可能性がある。

**(S3) 平均収束条件:** Fix(G∘F) における C̄ が、ρ の**場の内在的平均**に収束する。

```
C̄(Fix(G∘F; τ)) → μ_ρ    ここで μ_ρ = E_{(x,y)∈Ω×Ω}[ρ(x,y)]
```

μ_ρ は場 Ω の構造的性質であり、τ に依存しない定数。

**直観**: 再結晶を何度繰り返しても、最終的な結晶純度は溶媒の選択性 (= ρ の分布) で決まる。温度 (= τ) は結晶の大きさを変えるが、純度を変えない。

### 3.4 証明スケッチ

**Step 1: τ が変化したとき何が起きるか**

τ を τ₁ → τ₂ > τ₁ に上げると:
- G の閾値が上がる → より多くの内部ペアが τ₂ を下回る → より多く split
- 結晶が細分化 → 各結晶は小さく、内部ペアは全て ≥ τ₂

G のみの場合: 細かい結晶の Coh は高い (低 ρ ペアが除去されたため)。C̄ は τ₂ に依存して上昇する。これが G∘F OFF で range = 0.121 になる理由。

**Step 2: F の補償メカニズム**

τ₂ で細分化された結晶群に F を適用:
- 小さすぎる結晶 (< min_steps) が merge 対象
- τ₂ が高いほど → 結晶が小さい → merge 対象が増える
- merge は境界ペア (ρ < τ₂) を内部に追加 → Coh を下降させる

**Step 3: 打ち消しの数学**

チャンク c が n 要素を持ち、内部ペア数 = n-1 とする。

G が除去する最小ペア: ρ_min (< τ)
F が追加する境界ペア: ρ_bnd

不動点 Fix(G∘F) では G∘F が冪等 (§2.3.3) なので:
- G が除去したいペアが存在しない (全内部ペア ≥ τ)
- F が追加するペアの ρ 値 ≥ τ (そうでなければ G がすぐ除去する)

したがって Fix(G∘F) では:

```
全内部ペア ρ ≥ τ  かつ  追加される境界ペア ρ ≥ τ
```

**鍵の洞察**: τ を上げると「ρ ≥ τ」の条件が厳しくなるが、同時に結晶が小さくなり、内部ペア数が減る。1結晶あたりの内部ペアの ρ 分布は [τ, 1] の区間に切り詰められるが、切り詰められた分布の平均は τ に弱くしか依存しない。

具体的に: ρ が区間 [0, 1] 上でほぼ一様に分布しているとき、[τ, 1] に切り詰めた分布の平均は (1+τ)/2。τ ∈ [0.6, 0.8] では平均 ∈ [0.80, 0.90]。しかし実際の ρ 分布はピーク付き (多くのペアが ρ ≈ 0.8 に集中) なので、切り詰めの効果はさらに弱い。

**Step 4: なぜ C̄ ≈ μ_ρ に収束するか**

Fix(G∘F) の C̄ は「ρ ≥ τ のペアの平均」に近い。
一方、μ_ρ = E[ρ] は「全ペアの平均」。

τ が全ペアの平均 μ_ρ 付近にあるとき (Linkage では τ ≈ 0.7, μ_ρ ≈ 0.808)、ρ ≥ τ のペアの平均は μ_ρ に近い。τ が μ_ρ からどの方向にずれても、結晶の大きさと数が補償的に変化するため、C̄ は μ_ρ 付近に留まる。

これは §2.3.4 の ker(G) 次元依存性とも整合する: ker(G) が小さいほど、ρ 分布の有効次元が高く、切り詰めの影響が薄い → τ-invariance が強い。

### 3.5 定理の適用範囲と限界

**τ-invariance が成立する範囲**: τ ∈ [τ_min, τ_max] ここで:
- τ_min: 全データが1チャンクに落ちる点 (G が一度も split しない)
- τ_max: 各要素が独立チャンクになる点 (G が全ペアで split)
- 有効範囲: τ_min < τ < τ_max の内部。端点では退化する

**τ-invariance が崩壊するケース**:
1. **ρ 分布がバイモーダル**: 低 ρ クラスタと高 ρ クラスタに二極化 → τ がどちらのクラスタを含むかで C̄ が不連続に変化
2. **ker(G) が大きすぎる**: 忘却が 50% を超えると商空間が退化 → Fix(G∘F) の一意性が崩れる (§2.3.4)
3. **F と G が異なる ρ を使う**: S1 違反。merge 判定と split 判定が異なる測度を参照する場合、打ち消しが壊れる

**検証可能な予測** (§8 に追加):

| # | 予測 | S1-S3 との関係 |
|:--|:--|:--|
| P5 | バイモーダルな ρ 分布を持つデータで τ-invariance が崩壊 | S3 違反 |
| P6 | F の merge 判定に ρ を使う変種 (ρ-aware merge) で τ-invariance が強化 | S1 強化 |
| P7 | ker(G) > dim(Ω)/2 のドメインで τ-invariance が崩壊 | §2.3.4 予測の帰結 |

### 3.6 Linkage での検証 (実験的確認)

| 条件 | 値 | 定理との対応 |
|:--|:--|:--|
| G∘F ON, τ ∈ [0.60, 0.80] | C̄ range = 0.008 | **τ-invariant** (定理 3.3.1) |
| G∘F OFF, τ ∈ [0.60, 0.80] | C̄ range = 0.121 | F なし → Step 2 の補償なし |
| E[ρ] (858 similarity points) | ≈ 0.808 | μ_ρ (S3 の収束先) |
| Fix(G∘F) 収束 | 100%, 1-2 反復 | S2 充足 |
| ρ 分布 | 単峰 (ピーク ≈ 0.8) | S3 の前提条件充足 |
| F の merge 判定 | サイズベース (ρ 非参照) | S1 — F は ρ-blind だが操作するペアの ρ は同一分布 |
| G の split 判定 | ρ < τ | S1 — G は ρ を直接参照 |
| ker(G) | 2/6 = 33% < 50% | §2.3.4 の閾値以下 → τ-invariance 成立 |

---

## §4. Linkage ドメイン: 130+ 実験のまとめ

> **[要実験データ]** 本節は Hyphē PoC の Linkage ドメイン実験結果を統合する予定である。完成には以下のデータが必要:
>
> (a) Hyphē PoC results_analysis.md からの主要結果（ker(G) = {Scale, Valence} の FIM 分析）
>
> (b) 制御パラメータ τ に対する相転移点 τ* ≈ 0.720 の数値的検証データ
>
> (c) 130+ 実験の G∘F 正規化前後の ρ 分布（§3.3 表との整合性確認）
>
> (d) ker(G) のサイズと τ-invariance 成立条件の関係（§2.3.4 閾値 50% との比較）
>
> これらのデータが揃い次第、本節を完成させる。

---

## §5. Cognition ドメインへの転用

### 5.1 E14b: Handoff を用いた認知操作列の検証

最初に閉じるべき問いは、「live な WF 実行を直接いじったとき depth 不変か」ではなく、**認知操作の記録列に同じ G∘F を通したとき、結晶化後の Coherence が τ に依存せず安定するか**である。ここでは LLM-as-judge の離散誤差を避けるため、Linkage と同じ chunker `G∘F` と同じ embedding モデル `all-MiniLM-L6-v2` を Cognition にも適用した。

- データ: Handoff ファイル 20 本、415 段落
- セッション定義: 1 handoff = 1 cognition session
- τ 掃引: 0.50–0.95 (0.01 刻み, 46 点)
- structured 領域: τ > 0.60
- 判定規準: `CV_structured < 2%`

この設計は E2' の live depth 実験を完全に置き換えるものではない。しかし、**演算子 G∘F の transferability** を先に問うには十分である。もしここで CI が崩れるなら、depth 制御以前に「Cognition に G∘F を持ち込める」という前提自体が崩れる。

### 5.2 結果

| τ | mean chunks | mean coherence | std coherence |
|:--|------------:|---------------:|--------------:|
| 0.60 | 9.65 | 0.3913 | 0.0378 |
| 0.70 | 10.05 | 0.3970 | 0.0385 |
| 0.80 | 10.10 | 0.3944 | 0.0360 |
| 0.90 | 10.10 | 0.3944 | 0.0360 |
| 0.95 | 10.10 | 0.3944 | 0.0360 |

集計すると、Cognition ドメインの `C̄ = 0.3957`, `CV_full = 0.738%`, `CV_structured = 0.320%`, `range_structured = 0.00555`, `chunk_ratio = 1.14x` である。判定規準 `CV_structured < 2%` を大きく満たすため、**Cognition ドメインでも CI は成立する**。

重要なのは、chunk 数がほとんど動かないから CI が成立しているのではない点である。Handoff 自体が既にかなり構造化されているため、Linkage ほど大きな chunk 揺れは出ない。それでも `τ > 0.60` の構造化領域では Coherence の揺れは 0.006 未満に抑えられた。したがって depth 的変化がまず動かしているのは「値」ではなく「分割の仕方」であり、G∘F は認知記録列に対しても **粒度を調整しつつ品質を保存する**。

### 5.3 含意と制限

この結果が直接支持するのは、「Cognition における Kalon τ-Invariance の**演算子レベル**の成立」である。すなわち、認知操作列をどの τ で結晶化しても、結晶化後の内部 Coherence はほぼ不変である。深さは chunking の様相を変えるが、G∘F が到達する不動点の質を壊さない。

一方で、ker(G_Cog) の具体形はまだ未決である。E14b は CI を確かめる実験であり、何が忘却され何が保存されるかの座標同定までは行っていない。したがって Table 2.2 の `ker(G_Cog)` は保留のまま残す。次の段階は E2' の live depth 実験であり、ここではじめて `Temporality` や `Scale` が核なのか、あるいは別の座標が核なのかを問える。

---

## §6. Description ドメインへの転用

### 6.1 E14b: 構造化文書を用いた Description 検証

Description 側でも同じ設計をとる。対象は paper draft・spec 文書・Hyphē 文書群であり、各段落を 1 step とみなして `G∘F` を適用した。ここでの問いは、「説明対象が論文・仕様・理論メモに変わっても、granularity を決める τ に対して Coherence が不変に保たれるか」である。

- データ: 構造化文書 20 セッション、2,000 段落
- セッション定義: 文書または文書断片 1 本 = 1 description session
- τ 掃引: 0.50–0.95 (0.01 刻み, 46 点)
- structured 領域: τ > 0.60
- 判定規準: `CV_structured < 2%`

この設計は E3' の「同一内容を coarse / medium / fine prompt に量子化して比較する」直接実験より一段弱い。しかしその代わり、**Paper / Spec / Theory という既に高度に構造化された Description 空間に G∘F をそのまま投げても CI が保たれるか**を問える。これは `Týpos = Hyphē|_{Description}` という構想の前提条件である。

### 6.2 結果

| τ | mean chunks | mean coherence | std coherence |
|:--|------------:|---------------:|--------------:|
| 0.60 | 45.05 | 0.4574 | 0.0247 |
| 0.70 | 48.89 | 0.4492 | 0.0229 |
| 0.80 | 49.89 | 0.4492 | 0.0195 |
| 0.90 | 49.95 | 0.4490 | 0.0191 |
| 0.95 | 50.00 | 0.4496 | 0.0193 |

Description ドメインでは `C̄ = 0.4536`, `CV_full = 1.407%`, `CV_structured = 0.443%`, `range_structured = 0.00861`, `chunk_ratio = 1.33x` であり、ここでも `CV_structured < 2%` を十分に満たす。したがって **Description でも CI は成立する**。

この結果は Linkage と極めて近い。τ を上げると chunk 数は増えるが、結晶化後の Coherence は 0.449–0.458 の狭い帯域に留まる。つまり granularity は「説明を何片に割るか」を動かすが、「結晶化後の説明単位の質」をほとんど動かさない。これは `good description = 細かく書くこと` という単純図式を退ける。細密化そのものに価値があるのではない。**G∘F の不動点へ到達した説明単位が、粒度差を越えてほぼ同じ質を保つ**のである。

### 6.3 含意と制限

Description の結果は、Paper / Spec / Theory という異質な文書群にまたがって CI が成立する以上、Týpos 的な記述整形が単なる style transfer ではなく、**結晶化演算子の transfer** であることを支持する。特に `chunk_ratio = 1.33x` と `range_structured = 0.00861` の組は、「粒度変化は大きいのに品質揺れは小さい」という CI の典型的パターンである。

ただしここでも `ker(G_Desc)` の具体形は未同定である。Scale / Valence が核候補であるという推測は残るが、今回の実験はそこを証明しない。また、E3' の direct prompt 実験をまだ代替していない以上、「生成時のプロンプト粒度を直接いじっても同じ不変性が出るか」は今後の課題として残る。

### 6.4 SEAL — 学習可能単位への結晶化

Zweiger et al. による *Self-Adapting Language Models* (SEAL; arXiv:2506.10943) は、本稿の `G∘F` 結晶化を LLM 学習系に移した工学的事例として読める。SEAL では passage をそのまま重みに押し込むのではなく、implication / rewrite / self-QA 形式の self-edit に変換してから LoRA / SFT で更新する。これは raw passage を一度溶解し、**学習に効く単位として再析出する**操作である。

本稿の語彙で言えば、`F_SEAL` は raw passage の表層を溶かし、`G_SEAL` は downstream update utility が高い atomic facts / QA 単位へ結晶化する作用である。raw passage only の利得が小さく、self-edit の方が no-context 想起を大きく押し上げるという結果は、`AY(G)` が単なる情報量の多さではなく、**将来の推論を変形できる行為可能な単位の開口**によって増大することの外部接地を与える。ここでの行為可能性は読者の解釈や WF 分岐ではなく、重み更新を通じて将来の応答を変えることに対応する。

**命題候補 VI.SEAL.** 学習対象がそのままでは十分な update utility を持たないとき、`G∘F` による再表現を経た単位の方が raw context より高い結晶化効率を持つ。  
確信度: [推定 75%]  
撤回条件: raw passage only が implication / rewrite / self-QA 型 self-edit を複数タスクで一貫して上回るとき。

同時に、SEAL の sequential self-edit が prior tasks を徐々に損なうことは、局所 Kalon が大域 Kalon を保証しないことを示す。すなわち `Fix(G∘F)` は単発の update では成立しても、更新列 `G_t∘F_t` の合成では cross-edit coherence の制御がなければ drift が蓄積する。これは本稿の反例ではなく、`ker(G)` 設計と retention 項が結晶化の境界条件であることを示す。

### 6.5 Karpathy Wiki — symbolic 結晶化随伴の実装

Karpathy (2025) によるノート "LLM Wiki" パターン (gist) は、本稿の結晶化随伴 `F⊣G` (§2.1) を **markdown 離散空間への具体化**として読める。Karpathy は "the wiki is a persistent, compounding artifact" と述べ、従来の RAG が毎クエリごとに検索を再実行する揮発的戦略であるのに対し、LLM Wiki は検索結果を markdown ページとして蓄積・圧縮・修正するループを提案する。

本稿の語彙で整理する:

- `F_Wiki` (溶解): raw sources (conversation, retrieval output, human notes) → wiki draft。複数の入力を markdown ドラフトページに溶かす
- `G_Wiki` (結晶化): wiki draft + lint loop → coherent compounding artifact。重複・矛盾・孤立ページを検出・修正し、schema に整合する構造を析出する
- `Fix(G_Wiki∘F_Wiki)` = Karpathy の言う "persistent, compounding artifact" = Kalon な wiki

SEAL (§6.4) が weight 空間での結晶化であったのに対し、Karpathy Wiki は **symbolic markdown 空間での結晶化**である。両者は同じ `F⊣G` の 2 媒体: SEAL は `Δθ` (連続) に、Karpathy Wiki は markdown (離散) に結晶化先を持つ。

`ker(G_Wiki)` の候補は wiki の schema (命名規則、sidebar 階層、trivia 層の粒度判定) によって同値視される座標である。Zenn の dely_jp 実装例 (2025) では、Obsidian + Claude Code 環境下で SKILL.md による粒度判定を明文化している。これは `G_Wiki` の具体実装の公開例 — 「どのクエリ結果を新ページとして切り出すか、どの情報を既存ページに追記するか」を schema として固定する — と読める。Karpathy が提示する 3 層構造 (Raw sources / Wiki / Schema) のうち Schema は `ker(G_Wiki)` の決定装置として機能する。

**命題候補 VI.Wiki.** symbolic markdown 空間における結晶化随伴 `F_Wiki ⊣ G_Wiki` は公理 C1-C3 (§2.1) を満たし、`Fix(G_Wiki∘F_Wiki)` が有限反復で到達する。Coherence τ-Invariance (§3) は `τ_Wiki` = 新規ページ化の粒度閾値のもとで成立する。  
確信度: [推定 65%]  
撤回条件: wiki lint loop が収束せず、`τ_Wiki` を動かしたときに wiki 全体の Coherence (ページ間整合性) が系統的に変動する場合。

SEAL が連続 self-edit によって `Fix(G∘F)` の局所性と大域性の乖離 (§6.4 末尾) を示したのと同様に、Karpathy Wiki も連続編集によって wiki 内部の drift (孤立ページの蓄積、schema からの逸脱) を生じうる。この drift は SEAL のような weight-space drift と異なり、**人間が直接 lint 可能な symbolic level の drift** である。この性質は Paper X §4.6 で改めて論じる。

---

## §7. 忘却と行為可能性の一般理論

### 7.1 定理: 忘却が行為可能性を増大させる条件

**定理 7.1.1 (忘却-行為可能性定理).** G: C → C/ker(G) が忘却関手であるとき、

AY(G) = |Hom(C/ker(G), −)| − |Hom(C, −)| > 0

が成立する十分条件は:

**(A1)** ker(G) の次元 < C の次元の半分 (「半分以上を忘れない」)
**(A2)** C/ker(G) の対象間距離が C の対象間距離より均一 (「商空間の等方性」)

### 7.2 Paper I-V との統合

| Paper | 忘却の側面 | 本稿での対応 |
|:--|:--|:--|
| I: 力は忘却 | dΦ∧T ≠ 0 (方向性) | AY > 0 (行為可能性) |
| II: 相補性は忘却 | CPS スパン, Drift | ker(G) の構造, τ-invariance |
| III: Markov 圏の向こう | α ≤ 0 (copy 不可) | ker(G) が大きすぎると結晶化不能 |
| IV: 効果量減衰 | √ρ_spec の減衰 | Coherence の τ 安定性 |
| V: 繰り込みは忘却 | RG 不変性 | τ-invariance = RG 不変性のアナロジー |
| VII: 知覚は忘却 | U_arrow ≤ ⋯ ≤ U_self | 結晶化の解像度レベル ↔ フィルトレーション段階 |
| VIII: 圏論的基礎 | α-忘却濾過 {C_α} | τ パラメータ ↔ α パラメータの操作的対応 |

### 7.3 Kalon = Fix(G∘F) の3ドメイン統一

```
Kalon = Fix(Γ∘Q)|_{MB}
      = Fix(G_Cog∘F_Cog) × Fix(G_Desc∘F_Desc) × Fix(G_Link∘F_Link)
      = 認知結晶 × 記述結晶 × 連結結晶
```

3ドメインの不動点の直積が全体の Kalon を構成する。
各ドメインの τ-invariance が成立すれば、**Kalon は全制御パラメータに対して堅牢**。

---

## §8. 検証可能な予測と展望

### 8.1 検証可能な予測

| # | 予測 | 検証方法 | 期待される結果 |
|:--|:--|:--|:--|
| P1 | Cognition で τ-invariance | §5 実験 | 品質 range < 0.05 (G∘F ON) |
| P2 | Description で τ-invariance | §6 実験 | 品質 range < 0.05 (G∘F ON) |
| P3 | ker(G_Desc) ⊇ {Scale, Valence} | FIM 分析 | Linkage と同じ ker 構造 |
| P4 | 3ドメイン Kalon の直積分解可能性 | cross-domain 実験 | 各ドメインの Fix が独立 |
| P5 | SEAL 型 self-edit は raw passage only より高い結晶化効率を持つ | knowledge incorporation benchmark | no-context score が self-edit 条件で上回る |
| P6 | retention 項のない連続 self-edit では大域 Kalon が崩れる | continual editing benchmark | edit count に伴い prior-task quality が低下する |
| P7 | symbolic markdown 空間 (Karpathy Wiki) で Coherence τ-Invariance が成立 | wiki growth simulation + ページ間 coherence 測定 | `τ_Wiki` を変えても wiki 全体のページ間整合性 range < 0.05 |

### 8.2 展望

- **忘却論の認知科学的検証基盤**: Paper I-V は数学的構造。本稿は初めて実験データを持つ
- **AY の定量化基盤**: AY-3 (compute_ay.py) と本稿の 3ドメイン実験を接続
- **Euporía の深化**: AY > 0 が「なぜ」成立するか (忘却の商空間構造) の説明
- **SEAL 接続**: Cognition / Description での結晶化が weight update を介して将来の推論へ定着する工学的ケースを与える

---

## 参照

### 忘却論シリーズ（内部）
- [I] Paper I: 力は忘却である (v0.13)
- [II] Paper II: 相補性は忘却である (v1.0) — d = ker(d) への商写像
- [III] Paper III: 暗い側 — Z₂-次数付き CPS 圏 (v1.0)
- [IV] Paper IV: なぜ効果量は小さいか — 効果量減衰定理 (v1.0)
- [V] Paper V: 繰り込みは忘却である — RG 不変性 (v1.0)
- [VII] Paper VII: 知覚は忘却である — 普遍フィルトレーション (v1.2)
- [VIII] Paper VIII: 圏論的基礎における存在 — α-忘却濾過 (v1.4)

### プロジェクト内部参照
- [euporia.md](../../07_行為可能性｜Euporia/euporia.md) — Euporía 本体 (v0.8.0)
- [TASKS_euporia_hyphe_fusion.md](../../07_行為可能性｜Euporia/TASKS_euporia_hyphe_fusion.md) — AY タスク定義
- [linkage_crystallization.md](../../11_統一索引｜UnifiedIndex/linkage_crystallization.md) — 結晶化の定義
- [EXPERIMENT_paper_vi.md](../../../../60_実験｜Peira/06_Hyphē実験｜HyphePoC/EXPERIMENT_paper_vi.md) — Paper VI 実験設計書
- [e14_3domain_ci.py](../../../../60_実験｜Peira/06_Hyphē実験｜HyphePoC/e14_3domain_ci.py) — 3ドメイン CI 実験
- [e14_3domain_ci_results.json](../../../../60_実験｜Peira/06_Hyphē実験｜HyphePoC/e14_3domain_ci_results.json) — E14b 集計結果
- [THEORY.md](../../../../60_実験｜Peira/06_Hyphē実験｜HyphePoC/THEORY.md) — Hyphē 理論

### 外部文献
- Amari, S. (2016). *Information Geometry and Its Applications*. Springer.
- Fritz, T. (2020). A synthetic approach to Markov kernels. Adv. Math. 370, 107239.
- Gibson, J. J. (1979). *The Ecological Approach to Visual Perception*. Houghton Mifflin.
- Mac Lane, S. (1971). *Categories for the Working Mathematician*. Springer.
- Zweiger, A., Pari, J., Guo, H., Akyürek, E., Kim, Y., Agrawal, P. (2025). *Self-Adapting Language Models*. arXiv:2506.10943.
- Karpathy, A. (2025). *An LLM Wiki Pattern*. GitHub Gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- dely_jp (2025). *Karpathy 流 "LLM Wiki" を Obsidian + Claude Code で運用する*. Zenn: https://zenn.dev/dely_jp/articles/8b55114cc0b958

---

## 版履歴

| 版 | 日付 | 変更内容 |
|:---|:-----|:---------|
| v0.1 | 2026-03-29 | 初版骨子。Coherence τ-Invariance 定理、3ドメイン設計 |
| v1.0 | 2026-04-02 | ρ_coh/F 記号規約の明示、Papers VII-VIII との接続追加、参考文献セクション整備 |
| v1.1 | 2026-04-12 | E14b を §5-§6 に統合。Cognition / Description の operator-level CI 実測を追加し、設計段階から結果段階へ移行 |
| v1.2 | 2026-04-17 | §6.5 新設: Karpathy (2025) LLM Wiki パターンを結晶化随伴 `F⊣G` の symbolic 実装として定式化。命題 VI.Wiki 追加。§8.1 予測 P7 (symbolic 空間 Coherence τ-Invariance) 追加。参考文献に Karpathy (2025), dely_jp (2025) を追加。Paper X §4.6 と相互補完 |

---

*Paper VI v1.1 — 2026-04-12*
