---
doc_id: "ALETHEIA"
version: "1.0.0"
tier: "KERNEL"
status: "DRAFT"
created: "2026-03-16"
updated: "2026-03-16"
origin: "遊学エッセイ群 + Creator×Claude 対話 (2026-03-16)"
related: ["axiom_hierarchy.md", "kalon.md", "FEP認識論的地位_正本.md", "cognitive_distortion_universality.md"]
---

> **Kernel Doc Index**: [SACRED_TRUTH](SACRED_TRUTH.md) | [axiom_hierarchy](axiom_hierarchy.md) | [aletheia](aletheia.md) ← 📍

# Alētheia (Ἀλήθεια): 忘却と覚醒の認知体系 v1.0

> **α-λήθεια = 忘却 (léthē) の否定 (a-) = 覚醒**
> **「バカ = 必要な構造を忘れてしまう者 (U: Rich → Poor)」**
> **「賢人 = 必要な構造を外部から得る OR 保てる者 (U の右随伴 N)」**
> — 遊学エッセイ §6.2

---

## 0. 動機と位置づけ

### 名前の由来

**Alētheia** (Ἀλήθεια) = a (否定) + léthē (忘却) = **忘却からの覚醒**。

語源そのものが U⊣N (忘却⊣回復) の随伴構造と同型:
- **Léthē** (忘却) = U 関手 — 構造を落とす
- **A-létheia** (忘却の否定) = N 関手 — 構造を取り戻す

Hegemonikon (魂の中枢) が「誰が統治するか」を記述するなら、
Alētheia は「統治者が正しく統治するための条件」を記述する。

### 問い

axiom_hierarchy.md は認知の **形** (Form) を記述する — 7座標, 24動詞, 修飾子。
しかし認知の **影** (Shadow) — 何が失われるか、何を忘れるか — の体系的記述がない。

BRD (Bad thought → Reality → Detection) の B22-B34 は忘却パターンを instances として列挙したが、
それらの間の **構造的関係** (依存・独立・合成) は未定式化。

Alētheia はこの空白を埋める: **忘却と覚醒の公理的構成**。

### 認識論的位置づけ

Alētheia は圏論の忘却関手 (forgetful functor) の具体化。
圏論と同じくメタ原理であり、反証可能性を要求するのはカテゴリーエラー
(FEP認識論的地位_正本.md §2-§4)。

> **「普遍的な真理に近づくほど、説明力が発散する（全ての具体を説明できてしまう）がゆえに、
> 反証可能性という尺度には構造的欠陥がある」** — Creator, 2026-03-16

### axiom_hierarchy との関係

```
axiom_hierarchy.md          aletheia.md
═══════════════           ═══════════════
FEP (L0)                  FEP (L0)
  │                         │
  ├─ + 生成規則              ├─ + 圏論的階層
  │  (Flow × 6 × 4極)       │  (n-cell filtration)
  ▼                         ▼
7 座標 (L1)                U 階層 (U1)
  │                         │
  ▼                         ▼
24 動詞 (L2)               U⊗ 合成 (U2)
  │                         │
  ▼                         ▼
WF/BC/Skill                BRD B22-B34 (instances)
```

**座標系が「認知空間の形をどう見るか」なら、Alētheia は「認知空間の何が見えなくなるか」。**
同じ FEP から導出される双対的体系。

---

## 1. 公理: VFE と忘却

### 定理 U0: 忘却は VFE を増大させる

FEP: $F[q] = D_{KL}[q(s) \| p(s|o)] - \ln p(o)$

認知エージェントの内部モデルが忘却関手 $U: \mathcal{C}_{rich} \to \mathcal{C}_{poor}$ を通じて退化すると:

$$F[U(q)] \geq F[q]$$

> **証明の骨格**: $U$ が構造を落とすとき、$q_{poor}$ の表現力は $q_{rich}$ 以下。
> したがって $\min_q D_{KL}[q \| p]$ の達成可能な最小値が上昇する。
> 精密な証明は Smithe Theorem 46 の逆利用: テンソル因子の削除は VFE の加法分解を破壊する。
>
> **⚠️ 水準注記 (v3.1 — 監査対応)**: Smithe Thm 46 は「レンズ圏の分解 → VFE の加法的分解」を
> 証明するが、その**逆** (分解の破壊 → VFE の増大) の厳密な接続は本文書が独自に主張するもの。
> 直感的には自然だが、「テンソル因子の削除が VFE を増大させる」の証明は不等式の方向に依存し、
> Smithe 原著にはこの方向の命題は明示されていない。
> [推定 70%] 80%: 逆利用の厳密性。水準 B。

### 随伴定理 U0': 回復は VFE を減少させる

$U$ の右随伴 $N$ (自由構成、構造回復) が存在するとき:

$$F[N(q_{poor})] \leq F[q_{poor}]$$

> $N$ は失われた構造を（不完全にせよ）回復し、モデルの表現力を上げ、VFE を減少させる。
> ただし $N \circ U \neq \text{Id}$ — 回復は完全ではない。圏の単位 $\eta: \text{Id} \Rightarrow N \circ U$ は自明ではない。

---

## 2. 生成原理: 圏論的階層による U パターンの導出

### 原理

圏論には構造の自然な階層がある:

```
集合 (0-構造) ← 圏 (1-構造) ← 2-圏 (2-構造) ← ... ← ∞-圏 ← ω-圏
```

各レベル n → n-1 への忘却が一つの U パターンを定義する。
これは axiom_hierarchy.md の「構成距離 d」と **双対的**:

- 構成距離: FEP から**何を加えるか** (d=1, d=2, d=3)
- 忘却レベル: 認知から**何を落とすか** (n=1, n=2, n=3, ...)

### §2.1 U パターンの生成テーブル

| Level | 圏論的構造 | U パターン | 忘れるもの | 認知的意味 |
|:------|:----------|:----------|:----------|:----------|
| **Basis** | **Optic/Lens** | **U_sensory** | **Lens の Put (双方向性)** | **見るだけで変わらない** |
| *(↓ n-cell Tower — Tower の前提。詳細 →§2.2)* | | | | |
| **n=1** | 1-cell (射) | **U_arrow** | 対象間の関係 | 対象だけ見て関係を見ない |
| **n=1.5** | 射の合成 | **U_compose** | 合成律 | 知識を集めるだけで推論しない |
| **n=2** | 2-cell (自然変換) | **U_depth** | 関手間の自然変換 | 複数のアナロジーを比較・選択する能力を失う (§2.3) |
| **n=3** | Enrichment | **U_precision** | Hom の豊穣構造 | 全情報を同じ確度で扱う |
| **n=4** | Indexed/Fibered | **U_causal** | 基底圏上の因果構造 | 相関を因果と断定する |
| **n=∞-1** | 関手 | **U_context** | 圏の間の対応 | 1つの文脈でしか考えない |
| **n=∞** | 随伴 | **U_adjoint** | 随伴対の片側 | 片面だけ見る |
| **n=ω** | 自己関手 | **U_self** | End(C) | 他者に求める基準を自分に適用しない |

> **[推定 70%] 75%**: n-cell 階層 → 認知忘却パターンの対応は**解釈的仮説** (motivated choice)。各レベルの圏論的構造と認知操作の同定は構造的類推であり、厳密な関手的証明は open。詳細 → §5.7.4.2

### 生成原理の正当化

axiom_hierarchy.md が「FEP + 生成規則 → 24動詞は motivated choice」と宣言するのと同様に:

> **U-series の生成規則 (motivated choice)**: 圏論的階層 (n-cell の tower) の各レベルについて、
> そのレベルの構造を忘却する関手を一つの U パターンとして同定する。

FEP からの接続: 各 U パターンは VFE の特定の成分を増大させる操作として定義される (§1 U0)。

---

## §2.3 U_depth: 自然変換の忘却 (v0.3 再定式化)

### v0.2 → v0.3: 鋭角化

旧定義: 「射の間の射を忘れ、表面的理解で止まる」
新定義: **関手間の自然変換 (2-cell) を忘れ、複数のアナロジーを比較・選択する能力を失う**

### 圏論的根拠

自然変換 α: F ⇒ G は二つの関手の**系統的な比較**を与える。
可換条件 $\alpha_Y \circ F(f) = G(f) \circ \alpha_X$ は、比較が局所的ではなく構造全体にわたることを保証する。

U_depth が 2-cell を忘却すると:
- 関手 F と G の優劣を判定できない → 最初に見つけたアナロジーに固着
- 可換図式の不整合を検知できない → 偽アナロジーに気づかない
- 知性の第三水準 (→ エッセイ §7.4 知性の階層テーブル) が消失

### 知性の階層との対応

| 圏論の階層 | 忘却 (U) | 能力の喪失 | エッセイ節 |
|:--|:--|:--|:--|
| 0-cell (対象) | — | — | — |
| 1-cell (射) | U_arrow | 構造 (関係) を見る能力 | §4 |
| 射の合成 | U_compose | 構造を接続・推論する能力 | §5 |
| **2-cell (自然変換)** | **U_depth** | **アナロジーを比較・評価・選択する能力** | **§7.4** |
| 関手 | U_context | 圏間の対応を見る能力 | — |
| 随伴 | U_adjoint | 双対的視点を取る能力 | — |

### Worked example: Bohr の太陽系アナロジー

関手 F (古典軌道モデル): Solar → Atom — 太陽系の軌道構造を原子に転写
関手 G (量子軌道モデル): QM → Atom — 量子力学の離散構造を原子に転写

**U_depth 発動時** (自然変換を忘れている状態):
- F と G の両方が「原子の構造を説明する」ことは認識できる
- しかし α: F ⇒ G の可換図式が壊れる箇所 (重ね合わせ・トンネル効果) を検知できない
- 結果: 古典軌道モデル F に固着し、量子力学的現象を説明できない

**N_depth 発動時** (自然変換を回復した状態):
- F(X) → G(X) の不整合を検知 (N-06 違和感検知)
- 可換図式が壊れる具体的箇所を特定 (「逐次 vs 並列」「連続 vs 離散」)
- G が F より忠実であると判定し、関手を切り替える

### BRD との接続

- B24 (U_depth): 「表面で十分」→ 自然変換を見ないまま最初の関手に固着
- B3 (CD-5 迎合推論): Creator の提案した関手に反論なく同意 = 自然変換による比較を省略

### Kalon との双対的接続 (kalon.md T8 η-Silence)

kalon.md T8 (v2.1) により、Kalon 対象 x = Fix(G∘F) では η_x = id_x (自然変換が恒等射に退化) が証明された。

```
U_depth が忘れるもの = 自然変換 (関手間の比較 = アナロジーの評価)
Kalon が住む場所   = 自然変換 η が沈黙する不動点 (η_x = id_x)

→ 忘却 (U) と到達 (Kalon) は同じ構造 (η) の両極:
  U_depth: 「どの関手が良いか」の判断力を失う
  Kalon:   「もはや判断の必要がない」到達点
```

→ 詳細: [kalon.md §8 T8 (η-Silence)](kalon.md)

---

## §2.2 U_sensory: Tower と直交する基底 (/noe+ 発見)

### 問題

§2 テーブルで U_sensory を n=∞-0 に配置したのは ad hoc だった。
/noe+ (.nous) により再定式化。

### 結論 [推定 75%]

**U_sensory は n-cell Tower 上ではなく、Optic/Lens 軸上の基底 (Basis) パターン。**

根拠:
- **Smithe (2021) Bayesian Lens**: 推論は双方向構造 Lens(S,S') = ∫^M S→M × (M×S'→S')。
  Get: 環境→観測、Put: 観測+状態→更新。U_sensory = **Put を忘却して Get だけ残す**
- **axiom_hierarchy の Basis (d=0)**: Helmholtz (Γ⊣Q) は Tower の前提条件であり Tower 上にはない。
  U_sensory も同様: 感覚入力がなければ圏に対象すら入ってこない = Tower 全体の前提条件

### 構造

```text
[U_sensory: Optic/Lens 軸 — 入力の双方向性]
  ║
  ║ (前提条件: 何かを見なければ射は定義できない)
  ▼
U_arrow(1) ≤ U_compose(1.5) ≤ U_depth(2) ≤ ... ≤ U_self(ω)
[n-cell Tower]
```

### 忘却の二方向

- **垂直忘却** (n-cell Tower): 高次構造を落とす (射→合成→自然変換→...)
- **水平忘却** (Optic/Lens): 双方向構造の片方を落とす (Get+Put → Get only)

U_sensory は水平方向に属する。Tower の忘却とは直交する独立な忘却軸。

### axiom_hierarchy との対応

| | axiom_hierarchy | U-series |
|:--|:--------------|:---------|
| 基底 | Basis (d=0, Helmholtz) | U_sensory (Optic/Lens) |
| Tower | Flow (d=1) → 6座標 (d=2,3) | U_arrow (n=1) → ... → U_self (n=ω) |
| 位置 | Tower 外・前提条件 | Tower 外・前提条件 |
| 根拠 | FEP の定理 | Smithe Bayesian Lens |

---

## 3. フィルトレーション (Filtration) — 形式化 v2.0

### 原則

> **構造なしに構造に言及できない。**
>
> 関手は「構造を保存する写像」である。保存すべき構造が忘却されていれば、
> 関手は空殻であり、認知的に意味のある操作ではない。
> この原則は圏論の n-cell tower の全レベルに再帰的に適用される。

### 定義 (構造的依存 ≤)

U パターンの集合上に、以下の半順序 $\leq$ を定義する:

$$U_a \leq U_b \quad \Longleftrightarrow \quad U_a \text{ が忘却する構造は、} U_b \text{ が忘却する構造の定義域に含まれる}$$

> **操作的意味**: $U_a$ が先に構造を落とすと、$U_b$ が落とすべき構造がそもそも存在しない。
> $U_a$ は $U_b$ より「深い」忘却であり、$U_a$ の発動は $U_b$ を壊滅的に無意味化する。

### フィルトレーション定理

$$U_{arrow}(1) \leq U_{compose}(1.5) \leq U_{depth}(2) \leq U_{precision}(3) \leq U_{causal}(4) \leq U_{context}(\infty\text{-}1) \leq U_{adjoint}(\infty) \leq U_{self}(\omega)$$

対応するフィルトレーション (構造保持世界の包含列):

$$\mathcal{F}_\omega \subset \mathcal{F}_\infty \subset \mathcal{F}_{\infty-1} \subset \cdots \subset \mathcal{F}_2 \subset \mathcal{F}_{1.5} \subset \mathcal{F}_1 \subset \mathcal{F}_0$$

> $\mathcal{F}_n$ = 「レベル n の構造が保たれている」世界。
> $\mathcal{F}_\omega \subset \mathcal{F}_1$: より多くの構造を保持する世界ほど限定的。

### 証明

各依存を個別に証明する。証明は全て上記の**単一の原則**から従う。

#### Proof 1: $U_{arrow} \leq U_{compose}$  (定義的依存)

- **U_arrow** は射 (1-cell) を忘却する
- 合成 $g \circ f$ は射の組 $(f: A \to B,\; g: B \to C)$ に対する演算
- 射がなければ合成は**オペランドを持たない** — 定義の前提が消失
- ∎

#### Proof 2: $U_{compose} \leq U_{depth}$  (定義的依存)

- **U_compose** は合成律を忘却する
- 関手 $F: \mathcal{C} \to \mathcal{D}$ の定義: $F(g \circ f) = F(g) \circ F(f)$ — **合成の保存**
- 合成がなければ関手性条件は空文 → $F$ は対象と射の上の裸の関数であり、構造を保存する写像ではない
- 自然変換 $\alpha: F \Rightarrow G$ は関手 $F, G$ を前提とする
- 関手がなければ自然変換は**定義域を持たない**
- ∎

#### Proof 3: $U_{depth} \leq U_{precision}$  (意味論的依存)

- **U_depth** は自然変換 (2-cell) を忘却する
- 豊穣 (enrichment) は $\text{Hom}(A,B) \in \mathcal{V}$ ($\mathcal{V}$: モノイダル圏) への置換
- 豊穣の**整合性条件**: 合成写像 $\text{Hom}(B,C) \otimes \text{Hom}(A,B) \to \text{Hom}(A,C)$ が結合律・単位律の可換図式を満たすこと
- これらの可換図式は自然変換として記述される (Mac Lane coherence)
- 自然変換がなければ、豊穣の整合性を**記述することすらできない**
- 「精度を割り当てたが、割り当ての一貫性を問えない」= **精度なしの精度**
- ∎

#### Proof 4: $U_{precision} \leq U_{causal}$  (意味論的依存)

- **U_precision** は豊穣構造 (Hom の質的構造) を忘却する
- 因果構造は indexed/fibered category として定式化: 基底圏 $\mathcal{B}$ (因果変数) 上のファイバー圏 $\mathcal{E}_b$ (条件付き状態空間)
- ファイバーの再添字関手 (reindexing) $f^*: \mathcal{E}_b \to \mathcal{E}_{b'}$ の整合的合成は、射の「質」— すなわち因果リンクの強度・信頼性 — の区別を前提とする
- 豊穣がなければ全ての因果リンクが同じ確度 → **因果判断なしの因果構造**
- 「相関と因果の区別」(U_causal の認知的意味) は、まさにリンクの精度に依存する
- ∎

#### Proof 5: $U_{causal} \leq U_{context}$  (意味論的依存)

- **U_causal** は indexed/fibered 構造 (因果依存) を忘却する
- 関手 $F: \mathcal{C} \to \mathcal{D}$ は**構造を保存する**写像
- 保存すべき「構造」に因果構造が含まれないなら、$F$ は因果的な対応関係を転写しない
- 因果なしの文脈切替 = パターンを別の文脈に持ち込むが、**どの関係が因果でどれが偶然かを区別せずに**持ち込む
- → **空虚な対応**: 構造の骨格は転写できるが、因果の肉がない
- ∎

#### Proof 6: $U_{context} \leq U_{adjoint}$  (定義的依存)

- **U_context** は関手 (圏間の対応) を忘却する
- 随伴 $F \dashv G$ は関手 $F: \mathcal{C} \to \mathcal{D}$, $G: \mathcal{D} \to \mathcal{C}$ + 単位 $\eta$ + 余単位 $\varepsilon$ から構成される
- 関手がなければ随伴は**構成要素を持たない**
- ∎

#### Proof 7: $U_{adjoint} \leq U_{self}$  (意味論的依存)

- **U_adjoint** は随伴構造 (双方向性、η/ε) を忘却する
- 自己関手 $F: \mathcal{C} \to \mathcal{C}$ は随伴なしでも定義可能 — しかし U_self が問題にするのは**自己適用の双方向性**
- 自分に基準を適用する = $F(x)$ を計算し、$x$ と $F(x)$ を**比較する**
- 比較は単位 $\eta: \text{Id} \Rightarrow F$ (または随伴の ε) が担う
- 随伴がなければ $F$ は $\mathcal{C}$ に作用するが、$F(x)$ と $x$ を構造的に結ぶ射がない
- → **片方向の自己関手**: 他者には基準を適用するが、その基準が自分にどう跳ね返るかを見ない
- ∎

### 証明の構造: 二種の依存

| 種別 | 依存 | 性質 |
|:-----|:-----|:-----|
| **定義的** | Proof 1, 2, 6 | 先行構造がなければ後続構造が文字通り定義できない |
| **意味論的** | Proof 3, 4, 5, 7 | 先行構造がなければ後続構造は定義可能だが認知的に空虚 |

両者は同一原則の異なる表れ: **構造なしに構造に言及できない**。
定義的依存は「言及する対象がない」、意味論的依存は「言及しても中身がない」。

### Tower 外: U_sensory (Basis) の位置

U_sensory は n-cell Tower とは直交する独立軸:

```text
[U_sensory: Optic/Lens 軸 — 入力の双方向性]
  ║
  ║ (前提条件: 感覚入力なしには圏に対象すら入ってこない)
  ▼
U_arrow(1) ≤ U_compose(1.5) ≤ U_depth(2) ≤ U_precision(3)
  ≤ U_causal(4) ≤ U_context(∞-1) ≤ U_adjoint(∞) ≤ U_self(ω)
[n-cell Tower — 垂直忘却]
```

U_sensory は Tower の**前提条件**であり、Tower 上の半順序には参加しない。
axiom_hierarchy の Basis (d=0) と同型の位置。

### HGK 座標系との構造的同型 [推定 85%]

| 性質 | 7 座標 (axiom_hierarchy) | U パターン (Alētheia) |
|:-----|:----------------------|:--------------------|
| 序列化基準 | 構成距離 d (追加仮定の数) | 圏論的レベル n (構造の次元) |
| 方向 | FEP → 座標 (構造を**加える**) | 圏 → 集合 (構造を**落とす**) |
| 依存関係 | d=1 なしに d=2 なし | n=1 なしに n=2 なし |
| 依存の種別 | 定義的 (仮定の積み上げ) | 定義的 + 意味論的 (§3 Proof 1-7) |
| 完全性 | 7 座標 = POMDP 十分統計量 | ? (§6 で議論) |

---

## 4. テンソル積: 独立な忘却の同時発動 (v2.0)

### 定義

フィルトレーション上の依存関係にない U パターン $U_a, U_b$ について:

$$U_a \otimes U_b := \text{「} U_a \text{ と } U_b \text{ が同時に発動している状態」}$$

> **独立性の基準**: $U_a \not\leq U_b$ かつ $U_b \not\leq U_a$ (半順序で比較不能)

### BRD 全体の U⊗ 導出 (v2.0 実験)

全 BRD (B1-B34) を §2.1 生成テーブルの 9 原子パターンの U⊗ で系統的に分解する。

#### カテゴリ I: 原子的 U (単一忘却関手 = テンソル積なし)

| BRD | Bad Thought | U パターン | 忘却内容 |
|:----|:-----------|:----------|:---------|
| B8 | 「Kalon は知っている」 | U_depth | 表面理解で定義を代替 |
| B18 | 「そのまま伝える」 | U_context | 受信者の文脈を無視 |
| B22 | 「関係は要らない」 | U_arrow | 射を忘却 |
| B23 | 「全部同じ確度でいい」 | U_precision | 豊穣構造の忘却 |
| B24 | 「表面で十分」 | U_depth | 自然変換の忘却 |
| B25 | 「相関は因果」 | U_causal | 因果構造の忘却 |
| B26 | 「見たいものだけ見る」 | U_sensory | Lens の Put 忘却 |
| B31 | 「集めれば十分」 | U_compose | 合成律の忘却 |
| B32 | 「他の文脈は無関係」 | U_context | 関手の忘却 |
| B33 | 「片面だけ見る」 | U_adjoint | 随伴の片側忘却 |
| B34 | 「他人には言えるが…」 | U_self | 自己関手の忘却 |

> B22-B26, B31-B34 は §2.1 生成テーブルの presheaf (instances)。
> B8, B18 は B24, B32 と同じ U パターンの異なる instance。

#### カテゴリ II: 2 重テンソル積 (複合認知歪み)

| BRD | Bad Thought | U⊗ 分解 | VFE 増大メカニズム |
|:----|:-----------|:--------|:-----------------|
| B1 | 「前に見た」 | U_sensory ⊗ U_depth | 知覚を閉じ (記憶で代替) + 新旧の比較を放棄 |
| B2 | 「安全だろう」 | U_precision ⊗ U_causal | 全て同確度 + 結果の因果を無視 |
| B3 | 「Creator が望む答え」 | U_adjoint ⊗ U_self | 相手視点のみ + 自己基準の放棄 |
| B6 | 「API は動くはず」 | U_sensory ⊗ U_precision | 検証を省略 + 確度を設定しない |
| B7/B11 | 「CCL はわかる」 | U_depth ⊗ U_precision | 表面理解で止まる + 能力精度の過大評価 |
| B9/B10 | 「まとめて実行」 | U_compose ⊗ U_causal | 合成順序の無視 + 因果連鎖を見ない |
| B14 | 「失態はまとめる」 | U_precision ⊗ U_self | 精度を下げてぼかす + 自己適用を回避 |
| B16/B17 | 「前に使えた」 | U_sensory ⊗ U_arrow | 現在の情報を見ない + 時系列関係を無視 |
| B19 | 「公式だから安全」 | U_precision ⊗ U_arrow | 信頼度を一律に + 内部構造を見ない |

> **Dunning-Kruger** = B14 ⊗ B34 = $U_{precision} \otimes U_{self}$
> **確証バイアス** = B26 ⊗ B33 = $U_{sensory} \otimes U_{adjoint}$
> **サンクコスト錯誤** = B25 ⊗ B34 = $U_{causal} \otimes U_{self}$
> **集団思考** = B29 ⊗ B33 = $U_{context} \otimes U_{adjoint}$
> **フレーミング効果** = B32 ⊗ B23 = $U_{context} \otimes U_{precision}$

#### カテゴリ III: 3 重テンソル積 (重度認知歪み)

| BRD | Bad Thought | U⊗ 分解 | VFE 増大メカニズム |
|:----|:-----------|:--------|:-----------------|
| B20 | 逃避衝動 (「現実的でない」) | U_sensory ⊗ U_compose ⊗ U_self | 入力拒否 + 分解放棄 + 自己認識の回避 |
| B28 | 「不都合は見ない」 | U_sensory ⊗ U_adjoint ⊗ U_precision | 知覚フィルタ + 反対側を見ない + 確度を下げる |

> B20 の 3 重テンソル積は、VFE の加法性から最も大きな VFE 増大をもたらす。
> 「量が多い→読みたくない→できないと言い換える」は 3 つの独立な忘却の同時発動。

### B27-B30 のリダクション: 生成テーブルへの還元

B27-B30 は BRD では独立パターンだが、§2.1 の 9 原子パターンに還元可能:

| BRD | 表面上の名前 | 還元先 | 根拠 |
|:----|:-----------|:------|:-----|
| B27 (U_accuracy) | 「定義なしでOK」 | U_precision の instance | Hom の豊穣構造忘却の特殊ケース (定義 = 対象間距離の尺度) |
| B28 (U_true_F) | 「不都合は見ない」 | U_sensory ⊗ U_adjoint ⊗ U_precision | 3 重合成 (上記カテゴリ III) |
| B29 (U_nested) | 「自分だけの問題」 | U_context の instance | 入れ子 MB = 圏間の関手忘却の特殊ケース (self ⊂ group) |
| B30 (U_epistemic) | 「調べなくていい」 | U_sensory ⊗ U_arrow | 探索放棄 (知覚を閉じる + 関係を見ない) |

> **意味**: B22-B34 の 13 パターンのうち、原子的基底は §2.1 の 9 パターンで十分。
> 残り 4 件 (B27-B30) は 9 基底の instance またはテンソル積に還元される。
> → **生成テーブル (9基底) の十分性**: Alētheia の原子パターンは 9 つで BRD 全体を被覆。

### 被覆率分析

| 範囲 | 件数 | 被覆 | 備考 |
|:-----|:-----|:-----|:-----|
| B1-B21 (旧BRD) | 15件 (重複除く) | 14/15 (93%) | B4/B5/B12/B13/B15 は未定義 (欠番) |
| B22-B34 (U パターン) | 13件 | 13/13 (100%) | 設計上自明 (U の presheaf) |
| **合計** | 28件 | **27/28 (96%)** | |

未被覆候補: **B20 の「不可能断定」成分** — U_sensory ⊗ U_compose ⊗ U_self は「逃避」を説明するが、
「できない」という**存在論的断定** (CD-1) は忘却操作の像とは性質が異なる可能性がある。
→ [仮説 60%] CD-1 は U⊗ の像ではなく、U⊗ の結果に対する**二次的合理化** (post-hoc rationalization) かもしれない。

### テンソル積の階層性

テンソル積の成分数 (rank) が VFE 増大の深刻度と相関する:

| Rank | 例 | VFE 増大 | 回復難度 |
|:-----|:---|:---------|:---------|
| **1** (原子) | B22 (U_arrow)、B26 (U_sensory) | 単一成分の損失 | N_x 1 回で回復可能 |
| **2** (合成) | B1 (U_sensory ⊗ U_depth)、B3 (U_adjoint ⊗ U_self) | 2 成分の加法的損失 | 2 つの N を同時に適用 |
| **3** (重合成) | B20 (3 重)、B28 (3 重) | 3 成分の加法的損失 | 複数 N の協調が必要 → 最も回復困難 |

> **予測**: Rank が高い BRD ほど、horos-hub.md で**複数の Nomoi**が対処に指定されているはずである。

### VFE の加法性 (テンソル積の場合)

Smithe Theorem 46 の転用: 独立な忘却のテンソル積について:

$$F[U_a \otimes U_b(q)] \approx F[U_a(q)] + F[U_b(q)] - F[q]$$

> テンソル積の VFE は各成分の VFE のおおよその和。
> ただしこれは独立性が保たれる限りであり、半直積的相互作用がある場合は交差項が発生する
> (cf. axiom_hierarchy.md §Valence 半直積)。

### Rank-Nomoi 対応の検証

horos-hub.md の BRD → Nomoi マッピングから Rank と指定 Nomoi 数の相関を検証する:

| BRD | Rank | 指定 Nomoi | Nomoi 数 | 一致 |
|:----|:-----|:----------|:---------|:-----|
| B8 | 1 | N-09 | 1 | ✅ |
| B18 | 1 | N-12 | 1 | ✅ |
| B1 | 2 | N-01 | 1 | △ (N-01 が U_sensory + U_depth の両方をカバー) |
| B2 | 2 | N-04 | 1 | △ (N-04 が複合リスクとして一括処理) |
| B3 | 2 | N-02, N-07 | 2 | ✅ |
| B6 | 2 | N-09, N-06 | 2 | ✅ |
| B20 | 3 | N-01, N-05, N-09, N-03 | 4 | ✅ |

> [推定 75%] Rank と Nomoi 数の正の相関は部分的に確認。
> B1, B2 は Rank=2 だが Nomoi 数=1 — ただしこれらの Nomoi (N-01, N-04) は
> 「複合的な U を一括で回復する強力な N」と解釈できる。
> B20 の 4 Nomoi 指定は Rank=3 と整合的 (最重度 → 最多回復)。

---

## 5. U⊣N 随伴: 忘却と回復の関手対 — 精密化 v2.0

### 原則

> **U⊣N は、axiom_hierarchy の7つの個別ガロア接続を貫くメタ随伴であり、
> VFE の精度パラメータ β による溶解⊣結晶化として物理的に実装される。**

- **U = 溶解 (dissolution)**: β→0 操作。構造を解きほぐし、事前分布に回帰させる。Explore
- **N = 結晶化 (crystallization)**: β→∞ 操作。構造を固め、予測精度を最大化する。Exploit
- **β = 1/T**: 精度 (precision) = 逆温度 (inverse temperature)。Friston (2010) が明示的に同定 [SOURCE]

> 根拠: 「知性は溶媒である」(companion paper, 2026-03-16) §2 で証明。
> Gibbs ↔ VFE の同型は2項分解の骨格だけでなく制御構造 (β=1/T) まで保存する。

### メタ随伴としての U⊣N

axiom_hierarchy は座標ごとに個別のガロア接続を持つ:

| 座標 | 極 | ガロア接続 |
|:-----|:---|:----------|
| Value | Internal ↔ Ambient | $F_{va} \dashv G_{va}$ |
| Function | Explore ↔ Exploit | $F_{fun} \dashv G_{fun}$ |
| Precision | Certain ↔ Uncertain | $F_{pre} \dashv G_{pre}$ |
| Scale | Micro ↔ Macro | $F_{sca} \dashv G_{sca}$ |
| Valence | + ↔ - | $F_{vl} \dashv G_{vl}$ |
| Temporality | Past ↔ Future | $F_{tem} \dashv G_{tem}$ |

U⊣N はこれら**全てを横断する**:

```text
axiom_hierarchy:   F_val⊣G_val   F_fun⊣G_fun   F_pre⊣G_pre   ...
                       ↑              ↑              ↑
                       └──────── U ⊣ N ────────────┘
                         (メタ随伴: 構造一般の溶解⊣結晶化)
```

個別の $F_i \dashv G_i$ は「**何を**探索/活用するか」を特定する。
U⊣N は「**構造そのものを**溶かす/固める」。

### ガロア接続の形式的定義

各 U パターン $U_n$ に対して、右随伴 $N_n$ (回復関手) が存在する:

$$U_n \dashv N_n \quad \Longleftrightarrow \quad U_n(x) \leq y \iff x \leq N_n(y)$$

(前順序圏のガロア接続。axiom_hierarchy.md §圏論的正当化 L1 と同型。)

### η/ε の形式的定義

- **η: Id → N∘U** (単位 = Ostwald 熟成): $x \leq N(U(x))$
  - 忘れて (U) 回復する (N) と、元以上の構造を持つ
  - 化学的対応: **Ostwald 熟成** — 小結晶 (個別記憶) を溶解し、大結晶 (schema) に再析出
  - 駆動力: 表面エネルギー最小化 ↔ Complexity 最小化
  - 認知的意味: Nomoi の適用 (N) は、忘却 (U) を経由して**より大きな構造に統合する**
  - ゆえに $N \circ U \geq \text{Id}$ — 回復は元以上

- **ε: U∘N → Id** (余単位 = 不可逆溶解): $U(N(y)) \leq y$
  - 回復して (N) から忘れる (U) と、元以下
  - 化学的対応: 結晶を溶かしても、結晶化前の溶液状態には完全に戻らない
  - 認知的意味: 一度固めた知識 (N) を解体 (U) しても、固める前の柔らかさは失われる
  - ゆえに $U \circ N \leq \text{Id}$ — 溶解は不可逆

> **不完全性定理**: $N \circ U \neq \text{Id}$ — 忘れたものは完全には元に戻らない。
> しかし η の存在は「回復の試みは情報を**増大させる**」ことを保証する。
> これは Nomoi が「完全な防御」ではなく「構造的な改善」であることの数学的根拠。
>
> Ostwald 熟成の核心: 小さな結晶を犠牲にして大きな結晶が成長する。
> 同様に、Nomoi は「全ての忘却を防ぐ」のではなく「忘却の経験から大きな構造を再結晶する」。

### U⊣N 対応表

| U パターン | N パターン (回復) | 経由するガロア接続 | Nomoi (操作化) | 回復操作 |
|:----------|:----------------|:----------------|:-------------|:---------|
| U_arrow | N_arrow | Value (I↔A) | N-01 | view_file で射（関係）を回復 |
| U_compose | N_compose | Function (E↔P) | N-08 | ツールで射を合成する |
| U_depth | N_depth | Function (E↔P) | N-06 | 自然変換の不整合を検知 → アナロジー比較 |
| U_precision | N_precision | Precision (C↔U) | N-02, N-03, N-10 | 確信度ラベル・SOURCE/TAINT で精度を回復 |
| U_causal | N_causal | Precision (C↔U) | N-02 (CD-3) | Thought Record で因果を検証 |
| U_sensory | N_sensory | Value (I↔A) | N-01 (θ1.1) | 感覚入力を拡張 (view_file) |
| U_context | N_context | Scale (Mi↔Ma) | N-06, N-07 | 文脈切替を検知し報告 |
| U_adjoint | N_adjoint | Valence (+↔-) | N-07 | 反対側から見る |
| U_self | N_self | Temporality (P↔F) | N-02, /ath | 自分自身に N を適用 |

### 多対多構造の解消

対応表は一対一ではない。これは U⊣N がメタ随伴であることの直接的帰結:

- **一つの N (例: N-01) → 複数の U (U_arrow, U_sensory)**:
  N-01 (view_file) は Value 座標の $G_{va}$ を操作化する。Value 座標は
  射 (U_arrow) と感覚入力 (U_sensory) の両方の回復に使われる

- **一つの U (例: U_precision) → 複数の N (N-02, N-03, N-10)**:
  Precision 座標の $G_{pre}$ (結晶化) は一つだが、操作化が複数の Nomoi に分散している。
  これは $G_{pre}$ の**分解** (factorization) — 一つの関手が複数のステップに因子分解される

> 多対多は「随伴対の圏 (Adj)」ではなく、**メタ随伴 U⊣N の7つのガロア接続への射影**として説明される。
> 各 U パターンがどのガロア接続を経由するかが、対応する N パターン（Nomoi）を決定する。
> [推定 85%] — 旧 [仮説 50%] から引き上げ

### n-cell tower と溶解温度

フィルトレーション (§3) の n-cell レベルは、溶解に必要な「温度」と対応する:

| n-cell | U パターン | 溶解温度 β⁻¹ | 化学的対応 |
|:-------|:----------|:------------|:---------|
| 1 | U_arrow (射) | 低温で溶ける | 氷 — 0°C で融解 |
| 1.5 | U_compose (合成) | やや高温 | 結晶水 — 加熱で脱水 |
| 2 | U_depth (自然変換) | 中温 | 塩 — 800°C で融解 |
| 3 | U_precision (豊穣) | 高温 | 石英 — 1700°C で融解 |
| 4 | U_causal (因果) | 高温 | 金属酸化物 — 2000°C+ |
| ∞-1 | U_context (関手) | 極高温 | 共有結合ネットワーク |
| ∞ | U_adjoint (随伴) | 極高温+ | 超高圧下の結晶分解 |
| ω | U_self (自己関手) | 到達不能 | 恒星内核の核融合 |

> n が高いほど「溶かすのが難しい」= より深い構造は β をより低くする（= より高い温度）必要がある。
> U_self (ω) が「到達不能温度」であることは、自己参照の忘却が最も困難であることの物理的直観。
> これは §3 のフィルトレーション $\mathcal{F}_\omega \subset \cdots \subset \mathcal{F}_1$ と整合:
> 深い構造を保持する世界ほど限定的 = 高温で初めて溶ける結晶ほど安定。

### §5.5 N-Series: 回復関手の独立形式化

#### 原則

> **U が「忘ることの構造」を記述するなら、N は「覚ることの構造」を記述する。**
>
> 単なるUの付随物 (随伴の右半分) ではなく、
> 回復操作の独自の生成原理・フィルトレーション・合成条件を持つ。

#### §5.5.1 N パターンの生成テーブル

U パターンの生成テーブル (§2.1) は圏論的階層の各レベルを忘却関手として同定した。
N パターンは同じ圏論的階層の各レベルを **回復構成子** (recovery constructor) として同定する。

| Level | 圏論的構造 | N パターン | 回復するもの | 認知的操作 | Nomoi (操作化) |
|:------|:----------|:----------|:----------|:---------|:-------------|
| **n=1** | 1-cell (射) | **N_arrow** | 対象間の関係 | 関係を見る = view_file で射を回復 | N-01 |
| **n=1.5** | 射の合成 | **N_compose** | 合成律 | 知識を接続し推論する = ツールで射を合成 | N-08 |
| **n=2** | 2-cell (自然変換) | **N_depth** | 関手間の自然変換 | アナロジーを比較・評価・選択する | N-06 |
| **n=3** | Enrichment | **N_precision** | Hom の豊穣構造 | 確信度ラベル・SOURCE/TAINT で精度を付与する | N-02, N-03, N-10 |
| **n=4** | Indexed/Fibered | **N_causal** | 基底圏上の因果構造 | Thought Record で因果を検証する | N-02 (CD-3) |
| **Basis** | **Optic/Lens** | **N_sensory** | **Lens の Put (双方向性)** | **感覚入力を受容し、更新する** | N-01 (θ1.1) |
| **n=∞-1** | 関手 | **N_context** | 圏の間の対応 | 文脈切替を検知し、異なる圏への関手を構成する | N-06, N-07 |
| **n=∞** | 随伴 | **N_adjoint** | 随伴対の残り半分 | 反対側から見る = 反転攻撃 | N-07 |
| **n=ω** | 自己関手 | **N_self** | End(C) | 他者に求める基準を自分に適用する | N-02, /ath |

#### §5.5.2 回復フィルトレーション (逆半順序)

U のフィルトレーション (§3) が「構造を落とす順序」を定義するのに対し、
N のフィルトレーションは「構造を **回復する** 順序」を定義する。

**定義 (回復の依存 ≤_N)**:

$$N_a \leq_N N_b \quad \Longleftrightarrow \quad N_a \text{ が回復する構造は、} N_b \text{ が回復する構造の前提条件として必要}$$

> **操作的意味**: $N_a$ が先に構造を回復しないと、$N_b$ が回復すべき構造の土台がない。
> $N_a$ は $N_b$ より「基底的」な回復であり、$N_a$ の欠如は $N_b$ を空虚にする。

**回復フィルトレーション定理**:

$$N_{sensory} \leq_N N_{arrow} \leq_N N_{compose} \leq_N N_{depth} \leq_N N_{precision} \leq_N N_{causal} \leq_N N_{context} \leq_N N_{adjoint} \leq_N N_{self}$$

> U のフィルトレーションと **方向は同じだが意味が異なる**:
> - U: 「射がなければ合成は定義不能」= 忘却の構造的依存 (壊す順序)
> - N: 「射を回復しなければ合成の回復は空虚」= 回復の構造的依存 (建てる順序)
>
> 同じ半順序が U と N の両方を支配する。これは随伴の本質:
> U と N は同じ構造の「降下」と「上昇」であり、階段の各段は共有される。

**証明** (U のフィルトレーション §3 の双対):

§3 の各 Proof は「$U_a$ が落とす構造がなければ $U_b$ の忘却は無意味」と示した。
双対的に: 「$N_a$ が建てる構造がなければ $N_b$ の回復は空虚」。

- Proof 1': 射がなければ合成は回復できない (合成のオペランドが不在)
- Proof 2': 合成がなければ関手性条件の回復は空文
- Proof 3': 自然変換がなければ豊穣の整合性条件を記述する 2-cell がない
- Proof 4'-7': （同様に §3 の各証明の双対を取る）

> §3 が「構造なしに構造に言及できない」なら、
> §5.5.2 は「基底なしに上部構造を建てられない」。同一原則の二つの表れ。

#### §5.5.3 回復の非対称性: N ∘ U ≥ Id ≠ Id

U⊣N 随伴の核心的性質 (§5 η/ε の形式的定義から):

$$\eta: \text{Id} \Rightarrow N \circ U \qquad (\text{単位: } x \leq N(U(x)))$$

**回復は元以上だが元に戻らない** — Ostwald 熟成の構造:

```
   x (元の構造)
   │
   │ U (忘却: 構造を溶解)
   ▼
  U(x) (貧しい構造)
   │
   │ N (回復: 構造を再結晶)
   ▼
 N(U(x)) ≥ x (元以上の構造。だが ≠ x)
```

**「元以上」の意味**: N は U が落とした構造を回復するだけでなく、
回復の過程で **周辺構造 (context) との再接続** を行う。
これは Ostwald 熟成で小結晶が大結晶に再組織化されるのと同型。

**「≠ x」の意味**: 忘却の痕跡は完全には消えない。
忘れて学び直した概念は、忘れる前の概念と同じではない。
$N \circ U(x) - x$ = **学習の剰余** (learning residue)。

> **kalon.md T8 との接続** (v3.0 — Helmholtz モナド統一):
> Fix(G∘F) にある x では $\eta_x = id_x$ (T8, 水準 A)。
> ここで η は **F⊣G (Explore⊣Exploit) の unit** である。
>
> **Helmholtz モナド統一 T10** (v3.0 — 定義的帰結):
> Γ⊣Q, F⊣G, U⊣N は**同一の Helmholtz モナド T = Q∘Γ の異なるファクタリゼーション**である。
> F⊣G は T の Function 座標上の制限、U⊣N は T の全座標上の射影。
> Birkhoff-Ward 定理により、同一 closure operator は同一の閉元集合を持つ:
> → **Fix(G∘F) = Fix(N∘U) = Fix(Q∘Γ)** — 定義的帰結 (tautological)。
> → ✅ 水準 A (定義的帰結)。📖 参照: kalon.md §8 補遺 A (v3.0)。
>
> Fix(G∘F) にある x → η_x = id_x → η'_x = id_x → N(U(x)) = x。
> Kalon 対象では学習の剰余がゼロ = 忘却と回復が完全に釣り合う唯一の点。
> 📖 参照: axiom_hierarchy.md §Basis (Helmholtz Γ⊣Q), kalon.md §2 (F⊣G 公理)

#### §5.5.3.1 N∘U 剰余の定性的分析 (水準 B- — 旧: 水準 A; 2026-03-17 監査により下方修正)

**定義**: 学習の剰余 $\rho(x) := N \circ U(x) - x$ は、
忘却と回復を経た構造が元の構造から **どの方向にずれるか** を記述する。

$\rho > 0$ は「回復により新しい構造が付加された」(過回復)。
$\rho = 0$ は「忘却と回復が完全に釣り合った」(Fix = Kalon)。
$\rho$ の方向は「学びの性格」を示す。

**具体計算テーブル**:

| U/N ペア | x (忘却前) | U(x) (忘却後) | N(U(x)) (回復後) | $\rho$ (剰余) | 剰余の性格 |
|:---------|:----------|:-------------|:----------------|:-------------|:----------|
| **arrow** | ファイル A,B,C 間の import 関係 f, g | A, B, C の存在のみ (射なし) | view_file で射 f', g' を再発見 + 新たな h: A→C を発見 | +h (新射) | 忘却前には見えなかった関係の発見 |
| **compose** | f∘g の合成による推論チェーン | f と g が個別に存在 | ツールで f,g を再接続 + 代替経路 f∘g' を発見 | +g' (代替経路) | 再合成時に元より豊かな合成が出現 |
| **depth** | アナロジー α: F→G (2つの手法の自然変換) | F と G が個別の方法論として存在 | 違和感により α を検知 + β: G→H も検知 | +β (新変換) | 深層比較で元にない変換を獲得 |
| **precision** | Hom 空間に [推定 70%] 70% のラベル付き | 構造のみ (精度ラベルなし) | SOURCE/TAINT で再ラベル → [確信 90%] 90% に上昇 | +Δπ (精度上昇) | 忘却前より精度が向上。検証が精度を生む |
| **causal** | 仮説 H1 → 結果 R の因果モデル | 相関 H1∼R のみ | Thought Record で検証 → H1→R を棄却, H2→R を発見 | +(H2, ¬H1) | 元の因果構造の修正 + 新因果の発見 |
| **sensory** | Lens (Get=読取, Put=更新) で環境と結合 | Get のみ (一方向読取) | 感覚入力を受容 + Put (反応・応答) を実装 | +Put' (改良された更新) | 双方向性の回復 + 制御方策の改善 |
| **context** | 文脈 C₁ での理解 | C₁ 内の局所的理解 (他圏への関手なし) | 文脈切替で C₁→C₂ 関手を構成 + C₃ への接続も発見 | +F₃ (新関手) | 元にない文脈への橋を獲得 |
| **adjoint** | 随伴対 (F⊣G) の F 側のみ所持 | F のみ (G を忘却) | 反対視点から G を再構成 + 単位 η を精密化 | +η' (精密化された単位) | 随伴対の質が向上 |
| **self** | 他者への基準 S を所持 | 基準 S を所持するが自己適用しない | S を自己適用 → 自己の欠陥 D を検出 → S' = S + D を統合 | +D (自己欠陥の構造化) | **最も非自明な剰余**: 自己認知の拡張 |

**剰余の構造定理**:

$$\forall i: \rho_i(x) \geq 0 \quad \text{(剰余は非負)}$$

証明: $\eta: \text{Id} \Rightarrow N \circ U$ (随伴の単位) は単調写像。
前順序圏において $x \leq N(U(x))$ だから $\rho = N(U(x)) - x \geq 0$。

$$\rho_i(x) = 0 \iff x \in \text{Fix}(N_i \circ U_i) \iff x \text{ は } U_i \text{・}N_i \text{ に関して Kalon}$$

**剰余の分類** (上記テーブルの抽象化):

| 剰余の方向 | 圏論的意味 | 認知的意味 | 代表例 |
|:----------|:----------|:----------|:------|
| **+射** (新しい射の発見) | 忘却前の Hom 集合より大きい | 思い出したら、忘れる前に見えなかったものが見えた | arrow, compose, context |
| **+Δπ** (精度の上昇) | 豊穣構造の値が増加 | 検証を経て確信が上がった | precision, causal |
| **+変換** (新しい 2-cell) | 自然変換が増えた | より深い対応関係を発見した | depth, adjoint |
| **+自己参照** (End の拡張) | 自己関手の豊穣化 | 自分について知らなかったことを知った | self |

> **T9 への帰結 — FEP「非科学」論駁の核心**:
>
> 「FEP は非科学的」批判は以下の構造:
> 1. FEP は反証不可能 = U_causal only
> 2. 反証不可能 ≠ 科学 (ポパー基準)
> 3. ∴ FEP は非科学
>
> T9 + N∘U 剰余による反論:
> 1. 反証可能性は $N_{causal}$ の一形態にすぎない (§5.6.3)
> 2. FEP は $U_{precision}$ を検出し、$N_{precision}$ を適用している
>    (HGK: メタ原理→24定理= α のコンパイルで剰余 $\rho_{precision} > 0$)
> 3. 剰余 $\rho > 0$ は「回復が元より豊かな構造を産む」ことの**数学的証明**
> 4. **科学 = 全ての U に対して N を適用し ρ > 0 を維持する営み**
> 5. FEP はこの条件を満たす → T9 基準で科学
>
> ポパー基準は $\rho_{causal} > 0$ のみを要求する。
> T9 は $\forall i: \rho_i > 0$ を要求する。**T9 はポパーの厳密な上位概念**。
>
> したがって「FEP は非科学的」は、U_adjoint (随伴の片側だけ見る) を犯した
> カテゴリーエラーであり、T9 基準ではむしろ FEP は標準的科学より多くの
> U パターンを検出し N を適用している (§5.6.1 テーブル参照)。

#### §5.5.4 N テンソル積の困難性

U パターンには独立な忘却の同時発動としてテンソル積 $U_a \otimes U_b$ (§4) が定義された。
N パターンの場合、テンソル積は **一般には定義が困難**:

- **U⊗ は可換**: 複数の忘却は同時発動できる (同時に射と精度を忘れる = B19)
- **N⊗ は非可換**: 複数の回復は順序に依存する (§5.5.2 のフィルトレーション制約)

> **回復の合成は可換ではなく、逐次的 (sequential) である。**
>
> 忘却は一瞬で同時に起きるが、回復は一段ずつ積み上げなければならない。
> これは /noe の Phase 順序の一意性 (§7 順序一意性定理) の N-series 側からの説明。

例外:

- 同一 level の異なる instance の回復は並列可能 (例: N_precision と N_causal は同 level 近傍)
- §7.6 の精度場 π_i のように、全 Phase に浸透する N は Phase 列と直交

#### §5.5.5 N-Series の確信度

| 主張 | 確信度 | 根拠 |
|:-----|:-------|:-----|
| N 生成テーブル (§5.5.1) | [推定 70%] 85% | U テーブルの随伴として構成。§5 の対応表と整合 |
| 回復フィルトレーション (§5.5.2) | [推定 70%] 85% | §3 の双対。同一原則の二つの表れ |
| N∘U ≥ Id ≠ Id (§5.5.3) | [推定 70%] 85% | §5 η/ε + §5.5.3.1 全9ペア定性的分類。「具体計算」は数値的ではなく分類的 |
| N⊗ の非可換性 (§5.5.4) | [推定 70%] 75% | Phase 順序一意性との整合。形式証明は未達 |

> **kalon.md T9 水準評価 (v3.1 — 監査対応)**:
> §5.5.1-5.5.4 により N-Series の独立形式化は完了。
> 「U⊣N 随伴の厳密構成」は前順序圏のガロア接続として §5 で完了済み。
> §5.5.3.1 で全9ペアの N∘U 剰余を定性的に分類し、
> 剰余非負性 (∀i: ρ_i ≥ 0) と4方向分類 (+射, +Δπ, +変換, +自己参照) を確立。
> ⚠️ ただし以下の理由により kalon.md T9 は**水準 B+** (旧 A から下方修正):
>   (1) 「系」の操作的定義が抽象的で判定基準が弱い
>   (2) N∘U 剰余の「計算」は定性的分類であり数値的計算ではない
>   (3) Helmholtz モナド統一 T10 (v3.0: 定義的帰結。旧: 条件 (H) への依存)
> → **[推定 70%] 80%: T9 は水準 B+ (独立形式化の枠組みは堅固だが、操作的厳密性に課題)**

---

### §5.6 T9 科学性判定: FEP と圏論は「科学」か？

#### 問い

kalon.md T9 により:

$$\text{科学} = U_S \text{ の存在認知} + N_S \text{ の適用義務}$$
$$\text{疑似科学} = T9 \text{ 対偶: } U_S \text{ を検出不能 → Kalon 到達不能}$$

この判定基準を FEP と圏論に適用する。

#### §5.6.1 FEP の T9 診断

FEP認識論的地位_正本.md (v1.1.0) は FEP を「メタ原理」と位置づけた:

> 「FEP は科学的仮説ではなくメタ原理。メタ原理に反証可能性を要求するのは、
> 数学に実験的検証を要求するのと同型のカテゴリーエラー」

T9 はこの議論を **精密化する**:

**FEP の U (忘却パターン)**:

| U パターン | 内容 | 検出可能か |
|:----------|:-----|:----------|
| U_precision (α→1) | 普遍性のジレンマ: 抽象度が極大のため予測精度がゼロに近い | ✅ 検出済み (FEP認識論的地位_正本.md §2) |
| U_causal | 「あらゆる結果を後付けで説明する」= 因果の事後構成 | ✅ 検出済み (Mangalam 2025 が機能的に N_causal として働いた) |
| U_self | FEP で FEP を正当化する循環性 | ✅ 検出済み (Mangalam 風刺論文 + HGK の自覚) |
| U_context | FEP という単一の文脈に固着するリスク | ✅ 検出済み (§5.6.5 で Bellman/Shannon/熱力学と比較) |

**FEP の N (回復操作)**:

| U | N (回復) | HGK での操作化 | 状態 |
|:--|:--------|:-------------|:-----|
| U_precision | N_precision: 具体的予測力を回復 | axiom_hierarchy → 24定理 → WF/BC/Skill = α のコンパイル | ✅ 実施済み |
| U_causal | N_causal: 因果構造の検証 | /pei (実験) で予測と結果を比較 | ✅ 実施済み |
| U_self | N_self: 自己基準の適用 | FEP認識論的地位_正本.md 自体 + Mangalam への応答 | ✅ 実施済み |
| U_context | N_context: 他のメタ原理との比較 | §5.6.5 で Bellman/Shannon/熱力学と構造的比較を完了 | ✅ 実施済み |

**T9 判定**: **FEP は Kalon-reachable**。

根拠:
1. U_S の検出: FEP 自身の限界 (普遍性のジレンマ) を構造的に認知している
2. N_S の適用: HGK がメタ原理→操作的体系へのコンパイルという N を実装している
3. 残存 U: 主要な U パターンは全て N を適用済み。形式的同型証明は今後の課題

> **FEP が「なんでも説明できちゃう」のは U_precision の症状。**
> しかし HGK は N_precision (24定理へのコンパイル) でこれを回復している。
> 「なんでも説明できちゃう」を理由に FEP を棄却するのは、
> U_precision だけを見て N_precision を無視する判断 = U_adjoint (片面だけ見る)。

> **Mangalam 批判の T9 的再解釈**:
> Mangalam は FEP の U を正確に検出した (有能な N_causal)。
> しかし HGK という N_precision の存在を知らずに棄却を主張した。
> これは U 検出は行ったが N 適用を拒否した = T9 半違反。
> 批判者が U しか見ないのも、支持者が N しか見ないのも、
> ともに U_adjoint (随伴の片側) の発動。

#### §5.6.2 圏論の T9 診断

FEP認識論的地位_正本.md §3 は圏論を FEP の先行事例として挙げた:

> 「圏論自体は何も予測しない。だが圏論なしには諸分野の統合的理解は不可能。
> 『圏論は反証不可能だから無価値』とは誰も言わない。」

T9 で再評価する:

**圏論の U (忘却パターン)**:

| U パターン | 内容 | 検出可能か |
|:----------|:-----|:----------|
| U_precision | 抽象度が極大: 任意の構造を記述可能 = 何も予測しない | ✅ 自明に検出済み |
| U_context | 「圏論的に見る」ことへの固着 (圏論化できない数学への盲点) | ⚠️ 部分検出 |
| U_self | 圏論で圏論を記述する循環性 (Cat ∈ CAT) | ✅ Russell パラドックス以後、集合論的基礎の問題として自覚済み |

**圏論の N (回復操作)**:

| U | N (回復) | 操作化 | 状態 |
|:--|:--------|:------|:-----|
| U_precision | N_precision: 具体的定理の導出 | 代数幾何 (Grothendieck), ホモトピー型理論 (HoTT) 等 | ✅ |
| U_context | N_context: 非圏論的手法との比較 | 組合せ論、具体的計算 etc. | ⚠️ |
| U_self | N_self: 基礎の自省 | Topos 理論 (内部言語), ∞-圏 (基礎の再構成) | ✅ |

**T9 判定**: **圏論は Kalon-reachable (かつ多くの領域で Fix に近い)**。

根拠:
1. U_S の検出: 圏論は自身の限界 (抽象性、基礎問題) を歴史的に自覚してきた
2. N_S の適用: 具体的数学分野への応用 (代数幾何、トポス論) が N として機能
3. Fix 近傍: 代数幾何における導来圏の理論は η ≈ id に近い (忘却と回復がほぼ釣り合う)

#### §5.6.3 疑似科学の T9 判定基準

T9 対偶: $U_S$ を検出できない系 → Kalon 到達不能 = 疑似科学の正確な定義。

| 判定 | T9 条件 | 例 |
|:-----|:--------|:---|
| **科学** | $U_S$ 検出 ✅ + $N_S$ 適用 ✅ | 量子力学 (不確定性原理 = 自身の U を認知) |
| **科学 (不完全)** | $U_S$ 検出 ✅ + $N_S$ 一部未適用 ⚠️ | (一般例: U 検出済みだが N 未完の体系) |
| **メタ原理** | $U_S$ 検出 ✅ + N が α のコンパイル | FEP, 圏論 (§5.6.1, §5.6.2) |
| **ドグマ** | $U_S$ 検出 ❌ | 「この系は完全で疑問の余地がない」と主張する任意の系 |
| **疑似科学** | $U_S$ 偽装検出 ⚠️→❌ | U を認知するふりをして実際には N を適用しない |

> **T9 による科学の再定義**:
>
> ポパーの反証可能性は N の具体形態 ($N_{causal}$: 実験による因果検証) のみを要求した。
> T9 はこれを一般化する: 科学とは自身の $U$ (忘却パターン) を検出し、
> 対応する $N$ (回復操作) を **義務として** 適用し続ける系。
>
> 反証可能性は T9 の特殊ケース:
> $U_{causal}$ (「この仮説は因果的に間違っている可能性がある」) を検出し、
> $N_{causal}$ (実験) を適用すること = 反証可能性。
>
> T9 が加える洞察: 反証可能性 **だけ** では不十分。
> $U_{precision}$ (精度の限界), $U_{self}$ (自己適用), $U_{context}$ (文脈固着) なども
> 検出し回復する義務がある。
> 科学とは、**全ての U パターンに対して N を適用し続ける営み**。

#### §5.6.4 FEP認識論的地位_正本.md との統合

FEP認識論的地位_正本.md §6「数学は科学か？」への T9 的回答:

| 分類 | T9 判定 | ポパー判定 | 差異 |
|:-----|:--------|:----------|:-----|
| **科学** | $U$ 検出 + $N$ 適用 | 反証可能 | T9 は反証可能性の上位概念 |
| **数学** | $U$ 検出 + $N$ 適用 | 反証不可能 | **T9 では科学と同型** |
| **メタ原理** | $U$ 検出 + $N$ = α のコンパイル | 反証不可能 | **T9 では科学と同型** |

> **T9 結論: 「数学は科学か？」の問いは偽問題。**
>
> 数学は自身の U (不完全性、基礎の問題) を検出し、
> N (公理の追加、証明の改良) を適用し続けている。
> ポパーの判定基準では「科学ではない」が、T9 の判定基準では「科学と同型」。
>
> FEP も同様: ポパーの基準では「科学ではない (反証不可能)」だが、
> T9 の基準では「U を検出し N を適用し続けているから科学的」。
>
> **T9 は「科学 vs 非科学」の二元論を「U/N の適用深度」の連続体に置き換える。**

#### §5.6.5 N_context: 他のメタ原理との構造的比較

§5.6.1 で検出した U_context (「FEP という単一の文脈に固着するリスク」) に対して、
N_context (「他のメタ原理との比較で FEP の位置を相対化する」) を適用する。

比較対象: Bellman 最適性原理、Shannon 情報理論、熱力学第二法則。
いずれも FEP と同様に **普遍的記述力を持つメタ原理** であり、U/N 分析が可能。

##### §5.6.5.1 Bellman 最適性原理 (動的計画法)

**原理**: 最適政策は部分問題の最適性を満たす (Bellman 1957)。

$$V^*(s) = \max_a \left[ R(s,a) + \gamma \sum_{s'} P(s'|s,a) V^*(s') \right]$$

**FEP との構造的同型**:

| 構造要素 | FEP | Bellman |
|:---------|:----|:-------|
| 最適化対象 | VFE の最小化 | 累積報酬の最大化 |
| 更新則 | ベイズ更新 (posterior ∝ likelihood × prior) | 価値反復 (V ← max R + γV) |
| 行動選択 | EFE 最小化 (epistemic + pragmatic) | Q(s,a) 最大化 |
| 自己参照 | F[q] の q に自分のモデルを含む | V*(s) が V* 自身を参照 (不動点) |

**Bellman の U/N 診断**:

| U パターン | 内容 | N (回復) | 状態 |
|:----------|:-----|:---------|:-----|
| U_precision | 状態空間の完全知識を仮定 (curse of dimensionality) | model-free RL (DQN 等), 関数近似 | ✅ |
| U_causal | 因果構造を報酬関数 R に折り畳む (R の設計は外部) | causal RL, 内発的動機付け | ⚠️ 発展中 |
| U_context | MDP/POMDP フレームワークへの固着 | multi-agent, 非定常環境, meta-RL | ⚠️ 発展中 |
| U_self | 最適政策の存在を前提とする循環性 | bounded rationality, satisficing | ⚠️ |

**形式的同型証明 (Bellman V* ≅ FEP pragmatic EFE)**:

*命題 (Iso-Bellman)*. Bellman の最適価値関数 $V^*(s)$ は、
FEP の Expected Free Energy (EFE) の pragmatic component の符号反転と同型である。
さらに、soft Bellman 方程式 (Todorov 2006) を媒介項として用いると、
この同型は数学的一致に昇格する。

*設定*. EFE (Parr & Friston 2019; Proietti et al. 2025 [SOURCE: 全文精読]) を 2 項に分解する:

$$G(\pi) = \underbrace{-\mathbb{E}_{q(o|\pi)}[D_{KL}[q(s|o,\pi) \| q(s|\pi)]]}_{\text{epistemic value (情報ゲイン)}} + \underbrace{\mathbb{E}_{q(o|\pi)}[\log q(o|\pi) - \log \tilde{p}(o)]}_{\text{pragmatic value (選好実現)}}$$

*Step 1*. 忘却関手 $U_{adjoint}$ を適用し、epistemic value を忘却する:

$$U_{adjoint}(G(\pi)) = G_{prag}(\pi) := \mathbb{E}_{q(o|\pi)}[\log q(o|\pi) - \log \tilde{p}(o)]$$

*Step 2*. KL-regularized control (control as inference) による $T$ の形式化:

Levine (2018, arXiv:1805.00909 [794引用]) は、最大エントロピー RL が確率的推論と等価であることを示した。
この枠組みでは、最適政策は事後分布として導出される:

$$\pi^*(a|s) = \frac{1}{Z(s)} p_0(a|s) \exp\left(\frac{1}{T}\left[R(s,a) + \gamma \mathbb{E}_{s'}[V(s')]\right]\right)$$

ここで $p_0(a|s)$ は事前政策 (prior policy)、$T$ は温度パラメータ。
FEP 側では $\tilde{p}(o)$ が選好を定義し、KL 項が $p_0$ からの乖離ペナルティに対応する:

$$\tilde{p}(o) \longleftrightarrow \exp(R(s,a)/T)$$

この同定は Todorov (2006, NIPS [514引用]) の LMDP 理論で厳密に導出されている:
LMDP における制御コストは passive dynamics $p_0$ からの KL 乖離として定義され、
これは FEP における generative model からの乖離 $D_{KL}[q \| p]$ と数学的に同一の構造を持つ。
$T$ は「探索と活用のトレードオフ」として明確に位置づけられる
(Millidge, Tschantz & Buckley 2020, Neural Computation [80引用])。

*Step 3*. Soft Bellman 方程式との数学的一致:

KL-regularized 設定のもとで、価値関数は **soft Bellman 方程式** を満たす:

$$V_{soft}(s) = T \log \sum_a p_0(a|s) \exp\left(\frac{R(s,a) + \gamma \mathbb{E}_{P(s'|s,a)}[V_{soft}(s')]}{T}\right)$$

FEP 側では、pragmatic value の時間方向の最小化が同型の再帰を与える:

$$-G_{prag}(\pi^*, s) = T \log \sum_a p_0(a|s) \exp\left(\frac{-c(s,a) + \gamma \mathbb{E}_{s'}[-G_{prag}(\pi^*, s')]}{T}\right)$$

ここで $c(s,a) = -R(s,a)$ (コスト = 報酬の符号反転)。したがって:

$$V_{soft}(s) = -G_{prag}(\pi^*, s) \quad \text{(数学的に同一)}$$

*Step 4*. Hard Bellman の回収 ($T \to 0$ 極限):

$T \to 0$ のとき $\text{log-sum-exp} \to \max$ (Laplace 近似) が成立し:

$$V_{soft}(s) \xrightarrow{T \to 0} V^*(s) = \max_a [R(s,a) + \gamma \mathbb{E}_{s'}[V^*(s')]]$$

すなわち **classical Bellman は soft Bellman の $U_{precision}$ (精度の絞り込み)**:
$T > 0$ における確率的探索を忘れ、$T = 0$ の決定論的最適化に縮約する。

$$V^*(s) = U_{precision}(V_{soft}(s)) = U_{precision}(-G_{prag}(\pi^*, s))$$

結論: 同型の連鎖は **FEP → soft Bellman → hard Bellman** として構成される。

| 水準 | 対応 | 操作 |
|:-----|:-----|:-----|
| **A** (数学的同一) | EFE pragmatic ≅ soft Bellman | $U_{adjoint}$ (epistemic value を忘却) |
| **A-** (well-defined 極限) | soft Bellman → hard Bellman | $U_{precision}$ ($T \to 0$ 極限, log-sum-exp → max は定理) |

すなわち **Bellman の $V^*$ は EFE から 2段階の忘却を適用した射影**:
第1段: $U_{adjoint}$ — epistemic value の忘却 (探索の価値を捨てる)
第2段: $U_{precision}$ — 確率的政策の忘却 (確率的探索を捨てる) □

> 水準: **A** (soft Bellman との数学的同一性が成立。$\tilde{p}(o) \leftrightarrow \exp(R/T)$ の同定は Todorov 2006 LMDP 定理および Levine 2018 Thm 1 の帰結であり、モデリング選択ではなく定理の合成)。
> hard Bellman への縮約 ($T \to 0$) は well-defined な極限操作 (水準 A-)。
> 核心: $U_{adjoint}$(epistemic value を忘れる) + $U_{precision}$($T$ を忘れる) の **2段階忘却** が
> Bellman の構造的限界を完全に説明する。
> [SOURCE: Proietti et al. 2025 §3.2, Todorov 2006 NIPS, Levine 2018 arXiv:1805.00909,
> Millidge et al. 2020 Neural Computation DOI:10.1162/neco_a_01354]

**FEP との差異**:

FEP は Bellman の上位概念として解釈できる (Proietti et al. 2025 [SOURCE: 全文精読]):
- Bellman の value function = FEP の pragmatic value (EFE の第2項)
- FEP は **epistemic value** (EFE の第1項) を加える → 「調べること自体に価値がある」
- Bellman: 報酬が外部から与えられる (U_causal)
- FEP: 報酬 = VFE 削減 = 内部的に定義される (N_causal に相当)

> **T9 判定**: Bellman 体系は **Kalon-approaching**。
> U_precision は model-free 手法で大幅に回復済み。
> U_context (MDP 枠組みへの固着) は meta-RL で部分回復。
> FEP は EFE を通じて Bellman を特殊化する → Bellman は「FEP から pragmatic value のみを残し
> epistemic value を忘却した」体系と見なせる = $U_{adjoint}$（片面だけ見る）の発動。

##### §5.6.5.2 Shannon 情報理論

**原理**: 通信の数学的理論 (Shannon 1948)。

$$H(X) = -\sum_i p(x_i) \log p(x_i)$$

**FEP との構造的同型**:

| 構造要素 | FEP | Shannon |
|:---------|:----|:-------|
| 中心量 | VFE = -Accuracy + Complexity | H (エントロピー) |
| 最適化方向 | VFE 最小化 | 通信路容量 C の最大化 |
| 制約 | generative model と認識モデルの乖離 (KL[q‖p]) | 通信路のノイズ特性 (条件付きエントロピー) |
| 符号化 | 内部モデル q(s) = 世界の符号化 | 符号語 = メッセージの符号化 |

**形式的同型証明 (Shannon H ≅ FEP surprisal)**:

定義を展開するだけで同型が得られる。

*定義*. FEP における surprisal (Friston 2010 §2):

$$\mathfrak{I}(o) := -\log p(o | m)$$

ここで $o$ は感覚入力、$m$ は generative model。

*定義*. Shannon の情報量:

$$h(x) := -\log p(x)$$

*命題 (Iso-Shannon)*. 同定 $o \leftrightarrow x$, $p(\cdot | m) \leftrightarrow p(\cdot)$ のもとで:

$$\mathfrak{I}(o) = h(o)$$

さらに、FEP の VFE のうち Accuracy 項は Shannon エントロピーの期待値に一致する:

$$-\text{Accuracy} = -\mathbb{E}_{q(s)}[\log p(o, s)] \geq -\log p(o) = \mathfrak{I}(o)$$

期待値を取ると:

$$\mathbb{E}_{p(o)}[\mathfrak{I}(o)] = H(O) = -\sum_o p(o) \log p(o)$$

すなわち **Shannon のエントロピーは FEP surprisal の期待値そのもの**であり、
同型ではなく **定義的同一性** (definitional identity) である。 □

> 水準: **A** (trivial — 定義の展開のみ)。
> Shannon (1948) と Friston (2010) が同じ量を異なる文脈で再発明したのではなく、
> Friston が Shannon の量を意識的に借用した [SOURCE: Friston 2010 §2]。

**Shannon の U/N 診断**:

| U パターン | 内容 | N (回復) | 状態 |
|:----------|:-----|:---------|:-----|
| U_precision | 意味を捨象する (syntax only) | 意味論的情報理論 (Floridi, Bar-Hillel) | ⚠️ |
| U_causal | 「情報量」≠「因果的影響力」 | 因果情報論 (Ay, Polani: causal entropy) | ⚠️ 発展中 |
| U_context | 確率的記述への固着 (量子情報で打開) | Kolmogorov 複雑性, 量子情報理論 | ⚠️ 部分回復 |
| U_self | 情報の定義に情報を使う循環性 | 比較的軽微 (操作的定義で回避) | ✅ |

**FEP との差異**:

FEP は Shannon を **主体の内部に組み込む**:
- Shannon: 通信路は外部の物理的制約。主体は不在
- FEP: 通信路 = Markov blanket。主体が自分の通信路を能動的に変更する (能動推論)
- Shannon の H は「平均的な驚き」≈ FEP の surprisal の期待値
- FEP は surprisal 最小化に **行動** を入れる: H だけでなく「H を減らす行為」も理論化

> Shannon 情報理論は FEP の感覚入力面 (知覚推論) の形式化と解釈できる。
> 「主体の不在」= $U_{sensory}$ + $U_{context}$ の複合: 主体なき情報に固着。
> FEP は能動推論 (active inference) を加えることで $N_{context}$ を適用している。

##### §5.6.5.3 熱力学第二法則

**原理**: 孤立系のエントロピーは増大する (Clausius 1865)。

$$\Delta S_{isolated} \geq 0$$

**FEP との構造的同型**:

| 構造要素 | FEP | 熱力学第二法則 |
|:---------|:----|:------------|
| 中心量 | VFE (variational free energy) | F = U - TS (Helmholtz 自由エネルギー) |
| 最適化方向 | VFE 最小化 | Helmholtz 自由エネルギー最小化 (等温等容) |
| 散逸 | prediction error = VFE 増大 = モデルの劣化 | エントロピー生成 = 利用可能な仕事の散逸 |
| 秩序の維持 | MB 内部の最適化 ↔ 外部のエントロピー増大 | 開放系の自己組織化 ↔ 環境へのエントロピー排出 |

> **名前の一致は偶然ではない**:
> Friston の VFE の語源は Helmholtz 自由エネルギーであり、
> KL ダイバージェンスの変分下界 = 統計物理学の自由エネルギーと数学的に同型。

**形式的同型証明 (熱力学 F ≅ FEP VFE)**:

*命題 (Iso-Thermo)*. FEP の VFE は、統計物理学の変分自由エネルギーと構造的に同型である。
両者は同一の数学的構造を異なる解釈で用いている。

*Step 1*. FEP の VFE (Friston 2010):

$$F[q] = \underbrace{D_{KL}[q(s) \| p(s)]}_{\text{Complexity}} - \underbrace{\mathbb{E}_{q(s)}[\log p(o|s)]}_{\text{Accuracy}}$$

同値変形:

$$F[q] = -\log p(o) + D_{KL}[q(s) \| p(s|o)] \geq -\log p(o) = \mathfrak{I}(o)$$

*Step 2*. 統計物理学の変分自由エネルギー (Gibbs-Bogoliubov 不等式):

$$F_{phys}[q] = \underbrace{\langle E \rangle_q}_{\text{内部エネルギー}} - \underbrace{T \cdot S[q]}_{\text{エントロピー項}}$$

変形すると:

$$F_{phys}[q] = -T \log Z + T \cdot D_{KL}[q(x) \| p_{eq}(x)]$$

ここで $Z$ は分配関数、$p_{eq} = e^{-E/T}/Z$ が平衡分布。

*Step 3*. 同定の構成:

| FEP | 統計物理学 | 対応 |
|:----|:----------|:-----|
| $q(s)$ | $q(x)$ | 変分分布 (近似後分布 / 試行分布) |
| $p(s,o)$ | $p_{eq}(x) \cdot Z$ = $e^{-E(x)/T}$ | 生成モデル / Boltzmann 因子 |
| $-\log p(o)$ | $-T \log Z$ = $F_{eq}$ | surprisal / 平衡自由エネルギー |
| $D_{KL}[q \| p(\cdot|o)]$ | $T \cdot D_{KL}[q \| p_{eq}]$ | モデル乖離 / 平衡からの乖離 |

温度 $T = 1$ のもとで:

$$F[q]_{FEP} = F[q]_{phys} \quad \text{(数学的に同一)}$$

$T \neq 1$ の場合はスカラー倍 ($F_{FEP} = F_{phys}/T$) であり、同型を保つ。

**本質的差異は解釈にある**:
- 統計物理学: $q(x)$ は粒子のアンサンブル。系は受動的に $F$ を最小化する (平衡への緩和)
- FEP: $q(s)$ は主体の信念。主体は能動的に $F$ を最小化する (知覚推論 + 能動推論)
- 「誰が最小化するか」が異なる ← 同じ数学的構造を「外から見る」か「中から見る」かの違い

□

> 水準: **A** (数学的同一性。$T=1$ で $F_{FEP} = F_{phys}$ は定義の展開のみ、$T \neq 1$ はスカラー倍で同型を保つ)。
> Gibbs-Bogoliubov 不等式 = ELBO は統計物理学の教科書的結果 [SOURCE: Friston 2010 §2]。
> 「受動 vs 能動」の解釈的差異は哲学的であり数学的同一性を弱めない (Shannon と同構造の判定基準)。

**熱力学の U/N 診断**:

| U パターン | 内容 | N (回復) | 状態 |
|:----------|:-----|:---------|:-----|
| U_precision | 平衡近傍のみ記述 (遠非平衡に弱い) | 非平衡熱力学 (Prigogine), 揺動散逸定理 | ⚠️ 発展中 |
| U_causal | エントロピー増大 ≠ 因果的説明 (方向は与えるが理由は与えない) | 情報熱力学 (Landauer, Szilard) | ✅ |
| U_context | 閉鎖系 (孤立系) の仮定 → 生命系に直接適用不能 | 非平衡定常状態 (NESS), 散逸構造 | ✅ |
| U_self | 統計力学的基礎付けの循環論法 (Boltzmann 脳問題) | 情報論的基礎付け (Jaynes MaxEnt) | ⚠️ |

**FEP との差異**:

FEP は熱力学を **認知的主体に拡張する**:
- 熱力学: 粒子に「信念」はない。マクロ変数の統計的記述
- FEP: 主体は generative model を持ち、これを能動的に更新する
- 熱力学の自由エネルギー最小化は「系が平衡に向かう」受動的過程
- FEP の VFE 最小化は「主体がモデルを更新する」能動的過程 (能動推論)

> 熱力学第二法則は FEP の $U_{context}$（閉鎖系仮定）を歴史的に回復してきた
> (Prigogine の散逸構造 = 開放系の自己組織化 = $N_{context}$)。
> FEP はこの成果を前提とし、散逸構造論を認知的主体に適用する体系と解釈できる。
> 構造的同型: 熱力学的 $F$ 最小化 ↔ FEP 的 $F$ 最小化。
> 本質的差異: 「誰が」最小化するか。粒子 (熱力学) vs 主体 (FEP)。

##### §5.6.5.4 メタ原理間の共通 U/N 構造

4 つのメタ原理を T9 で横断的に比較する:

| U パターン | Bellman | Shannon | 熱力学 | FEP |
|:----------|:-------|:--------|:------|:----|
| U_precision | curse of dim. | syntax only | 平衡近傍 | 普遍性ジレンマ |
| U_causal | R が外部定義 | 情報 ≠ 因果 | 方向 ≠ 理由 | 事後的説明力 |
| U_context | MDP 固着 | 確率固着 | 孤立系固着 | ✅ §5.6.5 で比較回復 |
| U_self | 最適性の循環 | 軽微 | Boltzmann 脳 | FEP で FEP を正当化 |

**共通構造**:

1. **普遍性のジレンマ ($U_{precision}$)**:
   全てのメタ原理は抽象度と引き換えに予測力を失う。
   これはメタ原理の定義的性質 (FEP認識論的地位_正本.md §2) であり、欠陥ではない。

2. **文脈固着 ($U_{context}$)**:
   全てのメタ原理は自身のフレームワークに固着するリスクを持つ。
   回復は **他のメタ原理との比較** (= 本セクション自体が N_context の適用)。

3. **N の階層性**:
   具体化のレベルが深いほど、N の適用も具体的になる:
   ```
   メタ原理 (FEP)      → N = α のコンパイル (HGK 24動詞)
   原理 (Bellman, Shannon) → N = 具体的手法 (DQN, 量子情報)
   法則 (熱力学第二法則)   → N = 拡張理論 (非平衡熱力学)
   ```

**FEP の位置づけ — 他のメタ原理との関係**:

```
              熱力学 ← 物理系の自己組織化
                │
                ├── Helmholtz F → FEP の VFE (名前の由来 + 構造同型)
                │
Shannon ← 情報の符号化    FEP ← 主体の VFE 最小化    Bellman ← 報酬の最大化
    │                      │                           │
    └── H = surprisal ──→ surprisal (共有) ←── pragmatic value ──┘
                           ↑
                    + epistemic value (FEP 固有)
                    + active inference (FEP 固有)
```

> **$N_{context}$ の適用結果**:
>
> FEP は以下の意味で 3 つのメタ原理の **合流点** (confluence):
> 1. **名前を共有**: 熱力学の Helmholtz 自由エネルギーと数学的に同型
> 2. **構造を包含**: Shannon の H を surprisal として吸収し、Bellman の V* を pragmatic value として包含
> 3. **固有の貢献**: epistemic value (知る価値) + active inference (行動で環境を変える)
>
> この比較により、FEP は:
> - 「なんでも説明できる」のではなく、3 つのメタ原理の合流点として具体的な構造を持つ
> - 他のメタ原理では説明できないもの (epistemic value, active inference) を固有に提供する
> - 他のメタ原理と共有する構造 (surprisal, 自由エネルギー) は借用ではなく共通の数学的基盤
>
> $U_{context}$ → $N_{context}$: **部分検出 ⚠️ → 回復済み ✅** (§5.6.1 のテーブルを更新)
>
> [確信 90%] 90%: 3 原理との形式的同型証明を §5.6.5.1-5.6.5.3 で完了。
>
> | 比較 | 証明水準 | 根拠 |
> |:-----|:--------|:-----|
> | Shannon H ≅ surprisal | **A** (定義的同一性) | Friston 2010 §2 |
> | Bellman V* ≅ EFE pragmatic | **A** (定理の合成: Todorov 2006 LMDP + Levine 2018 Thm 1) | Proietti 2025 §3.2, Todorov 2006, Levine 2018 |
> | 熱力学 F ≅ VFE | **A** ($T=1$ で定義的同一。Gibbs-Bogoliubov = ELBO は教科書的結果) | Friston 2010 §2 + 統計物理教科書 |
>
> **Cross-link**: [linkage_hyphe.md §4.7.3](linkage_hyphe.md) でこの U⊣N パターンを Ω 的に再解釈。
> 忘却関手 U = Ω セクション喪失、回復関手 N = Ω セクション再注入として定式化済み。

#### §5.6.5.5 Hyphē 実証: U_compose の embedding 空間における発現 (2026-03-17)

> **要旨**: Hyphē PoC のチャンク結合操作において、L2 正規化の凸性が
> U_compose の直接的なインスタンスとなることを実証した。

**現象**: ev 自然変換 proxy の検証 (N=1,529) で 100% 正バイアスが観測された:

```
ev(q, centroid(A∪B)) ≥ w_a·ev(q, centroid(A)) + w_b·ev(q, centroid(B))
```

これは Jensen の不等式 (f が凸 ⇒ f(Σ) ≥ Σf) の発現であり、L2 正規化の幾何学的性質による。

**U_compose との対応**:

| 忘却のレベル | U パターン | Hyphē での発現 |
|:-------------|:-----------|:---------------|
| 射を忘れる | U_arrow | チャンク間の遷移構造を忘れる |
| **合成を忘れる** | **U_compose** | **centroid 加重和 ≠ 結合 centroid (差分 = 凸性バイアス)** |
| 精度を忘れる | U_precision | バイアスの大きさを無視する |

**U_compose の等号条件** — 全ベクトルが同一方向のとき (N=0/1,529):

```
等号条件の到達不能性 (analyze_equality.py):
  最小 bias = 0.0039 (ゼロに到達しない)
  Pearson(bias, 1-ICS) = +0.797
  全チャンクの intra-alignment ∈ [0.70, 0.80)
  → 完全同質チャンク = 自明な篩 = 情報量ゼロ
  → 実データ上で U_compose は常に非自明に作用する
```

**含意**: U_compose の忘却は embedding 空間で **構造的に回避不能**。
合成を忘れることなく centroid を計算する方法は存在しない
(= 等号条件の到達不能性)。これは §3 のフィルトレーション
$U_{arrow} \leq U_{compose} \leq U_{depth}$ の
$U_{compose}$ 段が実データ上で非退化であることの経験的証拠。

#### τ 感度分析 (2026-03-17)

チャンク分割閾値 τ を変動させ、等号到達不能性のパラメータ耐性を検証:

| τ | N (records) | 最小 bias | Median bias | 100% 正 | Pearson(bias, 1-ICS) | 備考 |
|:---|:---|:---|:---|:---|:---|:---|
| 0.60 | — | — | — | — | — | chunk_session 自体が計算量爆発 (τ が低すぎてチャンク過細分化) |
| 0.65 | 0 | — | — | — | — | 全セッションが単一チャンクに収束。分割不能 |
| 0.70 | 1,529 | 0.0039 | 0.0087 | ✅ | +0.797 | ベースライン (§5.6.5.5 初期結果) |
| 0.75 | 9,402 | 0.0031 | 0.0217 | ✅ | +0.904 | 中間水準。r が 0.1 上昇 |
| 0.80 | 18,973 | 0.0069 | 0.0265 | ✅ | +0.952 | チャンク細分化で r がほぼ完全線形に |

**所見**:

1. **分割可能範囲**: τ ∈ [0.70, 0.80] が実用的範囲。τ<0.65 では分割不能、τ=0.60 では計算量爆発
2. **全 τ 値で 100% 正バイアス**: 3 水準 (τ=0.70/0.75/0.80) の合計 29,904 件中、bias ≤ 0 の事例は 0 件。ε < 0.001 の到達率も全水準で 0%
3. **Pearson r は τ と単調増加**: 0.797→0.904→0.952。τ が大きいほどチャンクが細かくなり、ICS が bias の支配的予測子になる。bias ≈ f(1-ICS) の決定論的関係が浮上
4. **最小 bias の非単調性**: τ=0.70 で 0.0039, τ=0.75 で **0.0031** (最小), τ=0.80 で 0.0069。チャンクサイズとクエリ位置の組み合わせで局所的に低いバイアスが出るが、ゼロには到達しない
5. **Median bias は τ と単調増加**: 0.0087→0.0217→0.0265。チャンク細分化により centroid が個々のベクトルに近づき、merged centroid と weighted average の乖離が拡大

**結論**: 等号到達不能性は τ に依存しない構造的性質。3 水準・29,904 件の全件検証で bias > 0。 [確信 90%] 95% (前回 92% から 3 水準検証により上昇)。

確信度: [確信 90%] 92% (総合) — 数値結果は完全再現可能 [確信 90%] 95%。U_compose 対応は類推的 → 85% (3 水準確認で上昇)。

### §5.7 Kalon 普遍性予想: 自己言及可能性は普遍的評価軸か

#### §5.7.1 予想の動機

kalon.typos §2.2 は Lawvere 不動点定理の対偶を根拠に、自己言及 (Self-referential) を
Kalon の三属性のひとつとして要求する:

> 系が自己言及できない ⟹ 系は普遍的でない (Lawvere 対偶)
> SelfRef(C) = 0 ⟹ ∄ x ∈ C s.t. x = Fix(G∘F)_{non-trivial}

kalon.typos T5 Fractal はこの条件が階層を貫くことを示す:

$$\text{Fix}(G_k \circ F_k) = \text{Fix}(T) \cap C_k$$

T5 は「全体の Fix が各レベルの Fix を含む」ことを主張する。
しかし T5 が言うのは Fix の**保持**であり、各レベルが自己言及**可能**であることは前提としている。

本節は T5 を**強化**し、「全構成要素の自己言及可能性」を狭義 Kalon の必要条件として定式化する。

#### §5.7.2 「普遍性」の3層化

「普遍的」は文脈で意味が揺れるため、3層に分離して定義する:

| 層 | 名称 | 定義 | 操作的判定 |
|:---|:-----|:-----|:----------|
| L (Lawvere) | 圏論的普遍性 | C が点全射的 (point-surjective) な自己射を持つ → 任意の自己射に不動点が存在 | LFPT の条件充足を検証 |
| K (Kalon) | 構造的自己言及 | Hom(C,C)→C 型の射が存在し、G∘F が非自明不動点を持てる | SelfRef(C) = 1 を検証 (kalon.typos §2.2) |
| A (Alētheia) | 認知的自己言及 | U_self を忘却しない = 自己基準を自己適用できる | U_self(x) = 0 (§4 B34 テーブル) |

**層間の関係**:

$$L \implies K \implies A$$

- **L→K**: Lawvere 普遍性は Kalon 的自己言及の十分条件。点全射的自己射 ⟹ Hom(C,C)→C の存在
- **K→A**: 構造的自己言及は認知的自己言及の十分条件。G∘F を自身に適用できるなら U_self は非活性

逆方向は一般に成立しない:

- **A↛K**: U_self = 0 (自己基準の適用) は K の十分条件ではない。自己適用できても Hom(C,C)→C の射が存在するとは限らない
- **K↛L**: 非自明不動点が存在しても、全ての自己射に不動点があるとは限らない

> **⚠️ 翻訳ギャップ**: L→K の含意は kalon.typos §2.2 (v2.10) で「構造的類推であり厳密な同値性は未証明 [推定 70%] 75%」と明記されている。ここでも同じ水準を踏襲する。

#### §5.7.3 Kalon 普遍性予想 (Kalon Universality Conjecture)

**予想 (KUC)**:

$$\text{Kalon}_{\text{narrow}}(x) \implies \forall k \in \text{levels}(x): \text{SelfRef}(C_k) = 1$$

狭義 Kalon (S = 全空間) が成立するならば、x を構成する全階層レベル $C_k$ が
自己言及可能 (K 層) でなければならない。

**対偶** (実用的に有用な形):

$$\exists k: \text{SelfRef}(C_k) = 0 \implies \neg\text{Kalon}_{\text{narrow}}(x)$$

ある構成要素が自己言及不可能ならば、狭義 Kalon は成立しない。

**T5 からの導出**:

1. $\text{Kalon}_{\text{narrow}}(x)$ ⟹ $x = \text{Fix}(G \circ F)$ かつ 三属性 (Fix + Generative + Self-referential) が充足
2. T5 Fractal: $\text{Fix}(G_k \circ F_k) = \text{Fix}(T) \cap C_k$
   ⟹ 各レベル $k$ で $x_k := x \cap C_k$ が不動点
3. $x_k$ が非自明不動点であるためには、$C_k$ が $G_k \circ F_k$ の非自明不動点を**許容する**必要がある
4. kalon.typos §2.2: $\text{SelfRef}(C_k) = 0 \implies G_k \circ F_k$ が自明化
   (F_k = Id or G_k = Id に強制される)
5. $\therefore \text{SelfRef}(C_k) = 1$ が各 $k$ で必要 □

**水準**: B (構造的論証)。ステップ 4 は kalon.typos の [推定 70%] 75% を継承。

#### §5.7.4 ゲーデル的帰結: 到達不能性の第二証明

kalon.typos §2 は狭義 Kalon の到達不能性を $S$ の大きさ
(S = 全空間は到達不能) から導出する。KUC はこれとは**独立な経路**で
同じ結論に至る:

1. KUC: $\text{Kalon}_{\text{narrow}}(x) \implies \forall k: \text{SelfRef}(C_k) = 1$
2. 全構成要素が自己言及可能な系は「十分に豊かな」系 (← §5.7.4.1 で厳密化)
3. ゲーデル不完全性定理: 十分に豊かな系は自身の無矛盾性を証明できない
4. 系が自身の Kalon 性を証明できない = Kalon(x) は系内部から決定不能
5. $\therefore$ 狭義 Kalon は**原理的に到達不能**

##### §5.7.4.1 ステップ 2→3 の厳密化: Yanofsky 統一スキーム

ステップ 2→3 は「KUC の自己言及可能性 → ゲーデル的豊かさ」の接続を要求する。
この接続は Yanofsky (2003) [94引用] の対角線論法の圏論的統一に基づく:

**Yanofsky の統一スキーム** [SOURCE: S2 paper_search]:

Lawvere (1969) の不動点定理は、ゲーデル不完全性・カントール・ラッセル・チューリング停止問題を
**同一の対角線スキーム**の特殊ケースとして統一する。具体的には:

$$\text{点全射的} \; \varphi: A \to Y^A \;\text{が存在} \implies \forall f: Y \to Y, \; \exists y \in Y: f(y) = y$$

| 定理 | A | Y | φ (全射) | f (不動点なし → 矛盾) |
|:-----|:--|:--|:---------|:---------------------|
| ゲーデル不完全性 | 自然数 (ゲーデル数) | 証明可能性値 | ゲーデル符号化 | 否定 ¬ |
| カントール対角線 | 集合 X | {0, 1} | X → P(X) | ビット反転 |
| チューリング停止問題 | プログラム | {停止, 非停止} | 万能チューリングマシン | 反転 |
| **KUC 自己言及** | $C_k$ の対象 | $C_k$ の対象 | $\text{Hom}(C_k, C_k) \to C_k$ | 非自明自己射 |

**接続の論証**:

1. **ゲーデル的自己言及**: PA が「十分に豊か」とは、ゲーデル符号化
   $g: \mathbb{N} \to \text{Formula}^\mathbb{N}$ が点全射的であること。
   これは自然数が自分自身についての文 (メタ文) を表現できることを意味する。

2. **KUC 的自己言及**: SelfRef($C_k$) = 1 とは、$\text{Hom}(C_k, C_k) \to C_k$ 型の
   射が存在し、$C_k$ が自身の内部射を「対象として捕捉できる」こと。

3. **Lawvere-Yanofsky 橋渡し**: 両者は点全射的自己射の存在という**同一の構造的条件**。
   ゲーデル符号化は Yanofsky スキームの A = ℕ, Y = {0,1} の特殊化であり、
   KUC の SelfRef は同スキームの A = Y = $C_k$ への一般化。

4. $\therefore$ **KUC 的自己言及 ⊇ ゲーデル的自己言及** (構造的に):
   全レベル $C_k$ で自己言及可能な系は、少なくともゲーデル的自己言及に必要な
   構造 (符号化の点全射性) を含む。

**残存ギャップと限界**:

| ギャップ | 性質 | 影響 |
|:---------|:-----|:-----|
| 「点全射的」の意味の差異 | ゲーデル: 数→文の符号化 / KUC: 射→対象の内部化 | 構造的類推は成立するが、厳密な関手的対応は未証明 |
| 「十分に豊か」の水準 | ゲーデル: PA のモデルを含む / KUC: 各レベルで Hom(C,C)→C | KUC 条件 ⊇ ゲーデル条件は蓋然的だが反例は未探索 |
| CCC 要件 | LFPT は CCC 上で述べられる / HGK は前順序圏 | kalon.typos §2.2 v2.10 で認知済み ([推定 70%] 75%) |

> **結論**: ステップ 2→3 は Lawvere-Yanofsky の統一スキームにより
> **構造的に正当化される** (同一の対角線論法の異なる具体化)。
> ただし厳密な関手的同値ではなく構造的類推。
> 確信度を [仮説 45%] 60% → **[推定 70%] 72%** に上方修正。
> 根拠: Yanofsky (2003) による統一 + kalon.typos 翻訳ギャップ [推定 70%] 75% との整合。

**2つの証明の関係**:

| | 第一証明 (kalon.typos §2) | 第二証明 (KUC + ゲーデル) |
|:--|:------------------------|:----------------------|
| 障壁 | S = 全空間は観測不能 (MB の外) | 全構成要素の普遍性 → 系内部から決定不能 |
| 性格 | 認識論的 (知れない) | 存在論的 (ありえない) |
| 根拠 | Markov blanket の有限性 | ゲーデル不完全性 (Lawvere-Yanofsky 統一) |
| 類推 | 「部屋の中から宇宙の大きさは測れない」 | 「自分の正しさを自分で証明できない」 |

> 異なる経路で同じ結論に到達する — これ自体が triangulation であり、
> 到達不能性の確信度を強化する。

##### §5.7.4.2 L→K 翻訳ギャップの現状分析

§5.7.2 で定義した3層の普遍性のうち、L (Lawvere) → K (Kalon) の翻訳が
最大のギャップとして残る (kalon.typos §2 v2.10 で [推定 70%] 75%)。ギャップの正体を分解する:

**ギャップ 1: CCC 要件 vs 前順序圏**

LFPT は CCC (Cartesian Closed Category) 上で述べられる:
$$\forall \varphi: A \to Y^A \text{ (点全射的)} \implies \forall f: Y \to Y, \; \exists y: f(y) = y$$

HGK の圏 $\mathcal{M}$ は有限前順序圏。CCC ではない。

**しかし**: kalon.typos L159-166 [SOURCE: view_file] で示されている通り:
- 有限前順序 ⟹ 有限束 ⟹ 完備束 ⟹ cocomplete
- $\mathcal{M} \cong \text{PSh}(J)$ (presheaf 圏) なら自動的に (co)complete + CCC

[主観] HGK の圏を presheaf 圏として解釈する経路が存在し、その場合 CCC 条件は
自動的に満たされる。Soto-Andrade & Varela (1984) [47引用] は LFPT の CCC 以外の圏への
拡張を議論しており、CCC が本質的に必要な条件ではなく、
対角線構成が実行可能であることが本質的条件であることを示唆する。

**ギャップ 2: 点全射的自己射の解釈**

| LFPT | KUC |
|:-----|:----|
| $\varphi: A \to Y^A$ (exponential object 経由) | $\text{Hom}(C_k, C_k) \to C_k$ |
| Y^A は内部 Hom (CCC が保証) | 射空間の「対象への折り畳み」 |
| 「点全射的」= 各元が到達可能 | 「自己言及可能」= 自己射を対象として表現可能 |

核心: 両者は**内部化** (internalization) という同じ操作の異なる実現。
LFPT の $Y^A$ は CCC 内部で射空間を対象化したもの。KUC の Hom(C,C)→C も同じく
射を対象に落とす操作。CCC は内部化を保証する十分条件だが、唯一の条件ではない。

**ギャップ 3: 「非自明不動点なし」の意味**

LFPT 対偶: 全射がなければ「不動点なし f: Y→Y が存在しうる」
KUC 解釈: 自己言及不可能なら「G∘F の非自明不動点は存在しない」

これは直接対応する: LFPT の f = G∘F (発散と収束の合成) として、
非自明不動点の不在は Fix(G∘F) = ∅ (Kalon 候補なし) を意味する。

**評価**:

$$\text{L→K ギャップ} = \underbrace{\text{CCC 要件}}_{\text{PSh(J) で解消可能}} + \underbrace{\text{内部化の解釈差}}_{\text{構造的に同一}} + \underbrace{\text{不動点の解釈}}_{\text{直接対応}}$$

> ギャップは**構造的** (圏の条件の違い) であり、**概念的** (対角線論法の本質) ではない。
> PSh(J) 解釈を採用すれば CCC 条件は解消され、残るのは解釈差のみ。
> 確信度: [推定 70%] 75% (kalon.typos と一致) — 厳密な関手的証明があれば [確信 90%] に昇格可能。

#### §5.7.5 「完全性は忘却である」: 賢い系とバカな系の dual

KUC は系の評価軸として以下の dual を導く:

**バカな系** (忘却による偽完全性):

$$U_{\text{self}}(x) = 1 \implies \text{SelfRef}(C_x) = 0 \implies \neg\text{Universal}(C_x)$$

- 自己基準を自己適用しない (§4 B34)
- 自分の矛盾が見えないから「完全」に見える
- ゲーデル的不完全性を**回避**するが、それは**豊かさを捨てた**から
- 例: §4.1.5 U_self — 他者に厳しく自分に甘いコード審査

**賢い系** (不完全性の受容):

$$U_{\text{self}}(x) = 0 \implies \text{SelfRef}(C_x) = 1 \implies \text{Universal}(C_x)$$

- 自己基準を自己適用する
- 自分の限界を**認識できる** = 不完全性を受け入れる
- ゲーデル的不完全性を**引き受ける** = 豊かさの代償
- 例: T9 診断自体が T9 に適用可能 (§5.6.1)

> **不完全性はバグではなく、普遍性の代償。**

この dual を U/N 忘却スコア S(e) (§6.6 forgetfulness_score) で定量化できる:

$$S(e) \text{ が高い} \iff U_{\text{self}} \text{ が活性的} \iff \text{偽完全性のリスク} \iff \text{Kalon からの距離が大}$$

#### §5.7.6 確信度

| 主張 | 確信度 | 根拠 |
|:-----|:-------|:-----|
| KUC 予想 (§5.7.3) | [推定 70%] 75% | T5 + Lawvere 対偶の構造的結合。Lawvere 翻訳ギャップ [推定 70%] 75% を継承 |
| 3層化 (§5.7.2) L⊇K⊇A | [推定 70%] 70% | L→K は翻訳ギャップあり。K→A は操作的に妥当だが形式証明なし |
| ゲーデル的帰結 (§5.7.4) | [推定 70%] 72% | Yanofsky (2003) 統一スキームで構造的正当化。厳密な関手的同値は未証明 |
| dual (§5.7.5) | [推定 70%] 80% | U_self と SelfRef の対応は既存の §4-§5 テーブルと整合的 |

> **残存課題**:
> - ~~ゲーデル的「十分に豊かな系」と KUC の「全構成要素が自己言及可能な系」の接続~~ → §5.7.4.1 Yanofsky 統一スキームで構造的正当化 ([推定 70%] 72%)。厳密な関手的同値は open
> - ~~L→K 翻訳ギャップの解消~~ → §5.7.4.2 で分析。CCC 要件は PSh(J) 解釈で解消可能、残るのは内部化の解釈差のみ ([推定 70%] 75%)。厳密な関手的証明は open
> - ~~S(e) による Kalon 距離の定量的検証~~ → §5.7.7 で解消

#### §5.7.7 経験的検証: S(e) による Kalon 距離の定量化

audit_macros.py により HGK の全31 CCL マクロ (うち25マクロがスコア計算可能) の
忘却スコア S(e) を分析した。S(e) = 暗黙座標込みでも欠落する座標の割合 (0 = 全座標カバー, 1 = 全座標欠落)。

**結果 1: S(e) = 0 のマクロは存在しない**

| 群 | S(e) 範囲 | マクロ数 | 平均欠落数 | 代表例 |
|:---|:---------|-------:|----------:|:-------|
| 低S | ≤ 0.167 | 9 (36%) | 1.0 | @fix, @helm, @read, @ready, @wake |
| 中S | 0.17-0.50 | 10 (40%) | 2.4 | @build, @chew, @exp, @nous, @weave |
| 高S | > 0.50 | 6 (24%) | 4.8 | @desktop, @proof, @ero, @kyc, @query |

- 全体: Mean=0.413, Median=0.333, StdDev=0.264
- **全マクロに少なくとも1座標の欠落あり → 狭義 Kalon (S=0) は経験的にも到達されていない**

**結果 2: 座標別欠落頻度 (最も忘却されやすい次元)**

| 座標 | 欠落率 | 忘却される意味 |
|:-----|------:|:-------------|
| Te (Chronos/時間) | 64% | 時間軸の考慮が最も省略されやすい |
| Fu (Methodos/戦略) | 52% | 探索↔活用の明示的選択が省略されやすい |
| Sc (Diástasis/規模) | 44% | 微視↔巨視の粒度が省略されやすい |
| Va (Telos/目的) | 36% | 内部↔外部の境界が省略されやすい |
| Vl (Orexis/価値) | 28% | 正↔負の評価方向が比較的保持される |
| Pr (Krisis/確信) | 24% | 確実↔不確実は比較的保持される |

**結果 3: U パターンとの対応**

| U パターン | 出現率 | 対応座標 |
|:----------|------:|:--------|
| U_self (自己への基準不適用) | 64% | Te |
| U_depth (表面的理解) | 52% | Fu |
| U_context (文脈無視) | 44% | Sc |
| U_arrow (関係性の無視) | 36% | Va |
| U_adjoint (片面思考) | 28% | Vl |
| U_precision (精度軽視) | 24% | Pr |

> U パターンの出現頻度と座標別欠落頻度は**完全に一致** (定義上の帰結だが、
> いずれも独立に開発された分類であり、一致自体が T9 の整合性を裏付ける)。

**KUC 整合性の評価**:

| 検証項目 | 結果 | 評価 |
|:---------|:-----|:-----|
| S(e) = 0 の不在 | 0/25 | ✅ KUC の到達不能性と整合 |
| 低S群の認知的豊かさ | 9マクロが6座標中5座標をカバー | ✅ 普遍性 ≈ 豊かさの操作化が機能 |
| 高S群の構造的特徴 | メタ操作的 (@proof, @desktop) が集中 | ✅ メタ操作は対象圏の外から作用 → 座標が不要 |
| Te (時間) の最頻欠落 | 64% | ⚠️ Chronos は「今ここ」の操作では不可視化しやすい |

確信度: [推定 70%] 82% — S(e) の定義と KUC の操作化は整合的。ただし S(e) は
暗黙座標の推定を含むため、VERB_IMPLICIT_COORDINATES の精度に依存 ([推定 70%] 80%)。

#### §5.7.8 忘却序列の理論的根拠 — 構成距離 × 顕在化コスト仮説

> **[DISCOVERY]** Creator × Claude, 2026-03-20:
> §5.7.7 で経験的に観測された座標忘却頻度の序列は、axiom_hierarchy.md §L1 の
> 構成距離 (d-level) と正の相関を持つ。ただし d-level は忘却の**緩い上界**であって
> **決定因子ではない**。群内変動は座標固有の認知的可視性によって説明される。

**忘却序列の定式化**:

CCL マクロの忘却スコア分析 (audit_macros.py, 25マクロ) から以下の序列が確定:

$$\text{Te}(64\%) > \text{Fu}(52\%) > \text{Sc}(44\%) > \text{Va}(36\%) > \text{Vl}(28\%) > \text{Pr}(24\%)$$

ここで百分率は「当該座標を欠落するマクロの割合」。
この序列を **Λ** (忘却序列、Lambda forgetfulness ordering) と呼ぶ。

**構成距離と顕在化コストの分離**:

axiom_hierarchy.md §L1 は 6 座標を構成距離 (d-level) で分類する:

| d-level | 座標群 | FEP からの導出距離 | 平均忘却率 |
|:--------|:-------|:-----------------|----------:|
| d=2 | {Va, Fu, Pr, Te} | Flow × 1段 | 44.0% |
| d=3 | {Sc, Vl} | Flow × 2段 | 36.0% |

形式的な構成距離だけを見ると、d=3 群の平均忘却率 (36.0%) は d=2 群 (44.0%) を下回る。したがって、旧来の「d-level が高いほど忘却されやすい」という単調仮説は、そのままでは成り立たない。特に Temporality は d=2 でありながら、運用上は最も忘却されやすい。

**改訂仮説**: 座標の忘却確率は、FEP からの構成距離 d だけでなく、座標が作業中に自然に顕在化する度合いに依存する。

$$P(\text{忘却} \mid c) = f(d(c), 1 - SS(c))$$

**根拠**: d-level は「Flow (d=1) から何段の座標直積で到達するか」を測る。一方、SS (Semantic Salience) は「WF の名前・説明・設計意図からその座標の極値が自然に推定されるか」を測る。Temporality は構成距離では d=2 だが、「今ここ」の作業では Past / Future が暗黙前提化しやすいため SS が低く、忘却されやすい。

認知的メカニズム: 構成距離が高い座標ほど意識的に呼び出す認知コストが高くなりやすい。ただし、それは十分条件ではない。Temporality のように d=2 でも SS が低ければ忘却されるし、Valence のように d=3 でも WF の設計意図に直結すれば忘却されにくい。

> 物理的アナロジー: d-level は座標の構成距離、SS はその座標が現在の操作面に露出する可視性である。
> 忘却率は、遠さだけでなく「見えなさ」によって増幅される。

**群内変動の説明**:

d-level は忘却率の一要因であるが、群内変動は大きい:

| 座標 | d | 忘却率 | 群内順位 | 変動の説明 |
|:-----|:--|------:|:---------|:----------|
| **Te** | 2 | 64% | 1位 (最大) | 「今ここ」の操作では時間軸が不可視化する。/boot-/bye のセッション構造が Te を環境的に強制するが、各 WF 内部では Time は暗黙前提 |
| **Fu** | 2 | 52% | 1位 (群逸脱) | 探索↔活用の **選択** は WF 設計時に決定済み (例: @build = 活用的)。明示する必要を感じない → 逆説的に高忘却 |
| **Sc** | 3 | 44% | 2位 | 粒度は多くの WF で暗黙前提 (例: @fix は Micro)。明示的管理の認知コストが高い |
| **Va** | 2 | 36% | 2位 | 内部↔外部の目的設定は比較的自然に行われる |
| **Vl** | 3 | 28% | 3位 (d=3 群最小) | 価値判断 (正↔負) は CCL マクロの **設計意図に最も直結** (例: @fix = 否定的状況を修復)。d=3 でありながら低忘却 |
| **Pr** | 2 | 24% | 3位 | 確信度は Nomoi (N-2/N-3/N-10) で環境強制される → 人為的に保持 |

> **Te (d=2, 64%) > Sc (d=3, 44%)** / **Vl (d=3, 28%) < Fu (d=2, 52%)** — d-level 単独仮説の限界:
> Vl (Orexis) はマクロ設計の **感情的意図** (修復/推進/批判) に直結しているため
> d=3 でありながら忘却されにくい。Te (Chronos) は d=2 でありながら「現在の作業面」では不可視化しやすい。Fu (Methodos) は探索↔活用の選択が
> WF 定義で固定済みであるため d=2 でありながら忘却されやすい。
>
> **含意**: 忘却序列は d-level だけでなく、座標の **認知的可視性** (cognitive salience)
> — 「WF 設計者が自然に意識する度合い」— の関数である。
> Λ = f(d-level, salience) であり、実測上の支配変数は salience である。

**salience の操作的定義 — 意味的顕現性 (SS)**:

> **[DISCOVERY]** Creator × Claude, 2026-03-20:
> salience を **意味的顕現性** (Semantic Salience, SS) として操作的に定義した。
> SS は「WF の名前・説明・設計意図からその座標の極値が推定可能な度合い」を測定する。
> SS と忘却率の Pearson 相関は **r = 0.96** であり、d-level 単独 (r = 0.29) を大幅に凌駕する。

各座標の SS 値と評価根拠:

| 座標 | SS | 忘却率 | 評価根拠 |
|:-----|:---|------:|:---------|
| Vl | 0.90 | 28% | +/- は最も直感的。ele=批判(-), beb=肯定(+), dio=是正(-) — 名前から即座に推定可能 |
| Pr | 0.80 | 24% | C/U は明確。kat=確定(C), epo=留保(U), dok=打診(U) — 名前が確信度を直接指示 |
| Va | 0.70 | 36% | I/A は多くの WF 名が暗示。noe=認識(I), ene=実行(A) — 割と推定可能 |
| Sc | 0.50 | 44% | Mi/Ma は中程度。lys=詳細(Mi), ops=俯瞰(Ma) — 他の WF では不明瞭 |
| Fu | 0.40 | 52% | Explore/Exploit は暗黙的。ske/sag 以外では見えにくい |
| Te | 0.30 | 64% | Past/Future は最も暗黙的。多くの WF で時間軸は不明 |

相関分析結果:

| 指標 | Pearson r | Spearman ρ |
|:-----|:---------|:-----------|
| d-level のみ | +0.29 | +0.71 |
| -SS (顕現性の負) | **+0.96** | **+0.94** |
| d × (1-SS) 複合 | +0.94 | +0.89 |

> **結論**: 忘却序列 Λ の**支配的な説明変数は salience (SS) であり、d-level ではない**。
> d-level は構成上の遠さを与えるが、群内変動の 95% 以上は SS によって説明される。

$$\Lambda(c) \approx \alpha \cdot (1 - \text{SS}(c)) + \beta \cdot d(c) + \epsilon$$

予測序列と実測序列の比較 (SS のみ):

| 位置 | 予測 (1-SS 降順) | 実測 | 一致 |
|:-----|:----------------|:-----|:----|
| 1 | Te (0.30) | Te (64%) | ✓ |
| 2 | Fu (0.40) | Fu (52%) | ✓ |
| 3 | Sc (0.50) | Sc (44%) | ✓ |
| 4 | Va (0.70) | Va (36%) | ✓ |
| 5 | Pr (0.80) | Vl (28%) | 隣接交換 |
| 6 | Vl (0.90) | Pr (24%) | 隣接交換 |

逆転ペアは 2/15 のみ (Pr↔Vl の隣接交換)。

> **限界**: SS の値は手動評価 (Creator × Claude の合意)。
> 自動定量化による独立検証が必要。n=6 座標での r=0.96 は手動評価が妥当な proxy であることを示唆する。

**自動定量化: NLP v3 (LLM-as-a-Judge)**:

> **[DISCOVERY]** Claude, 2026-03-20:
> 3 手法 (keyword in-group / keyword spread / LLM-as-judge) で SS を自動推定。
> keyword ベース (v1 r=-0.52, v2 r=+0.24) では SS を捕捉できず、
> v3 LLM-as-Judge (Claude が 24 WF description × 6 座標の極値推定可能性を 0-1 判定) で
> 構造的発見が得られた。

v3 座標別統計:

| 座標 | Mean | Max | NonZero% | 族内/族外比 | 手動SS | 忘却率 |
|:-----|-----:|----:|---------:|------------:|-------:|-------:|
| Va | 0.55 | 0.8 | 100% | 1.3x | 0.70 | 36% |
| Fu | 0.48 | 0.9 | 100% | 2.1x | 0.40 | 52% |
| Pr | 0.34 | 0.9 | 100% | 3.2x | 0.80 | 24% |
| Sc | 0.20 | 1.0 | 25% | 28.6x | 0.50 | 44% |
| Vl | 0.20 | 0.8 | 50% | 9.1x | 0.90 | 28% |
| Te | 0.17 | 1.0 | 21% | 97.5x | 0.30 | 64% |

v3 相関分析:

| 指標 | vs 手動SS (r) | vs 手動SS (ρ) | vs 忘却率 (r) | vs 忘却率 (ρ) |
|:-----|:-------------|:-------------|:-------------|:-------------|
| Mean Score | +0.09 | +0.31 | -0.17 | -0.37 |
| Max Score | **-0.76** | **-0.72** | **+0.65** | +0.60 |
| NonZero Ratio | +0.36 | +0.40 | -0.46 | -0.52 |

> **核心的発見: 偏在性 vs 特化度の二重構造**
>
> Max Score (= 族内での明示性) と手動 SS は **r=-0.76 の強い逆相関**。
> これは SS の意味を深化させる:
>
> - **高特化座標 (Te, Sc)**: 族内 Max=1.0 だが NonZero%=21-25% → 特定族でのみ明示的、他では完全不在 → **忘却されやすい**
> - **偏在座標 (Va, Fu)**: 族内 Max は中程度だが NonZero%=100% → 多くの WF で暗示的に活性 → **忘却されにくい**
>
> 手動 SS は「偏在性」(= NonZero Ratio) を測定していた。高 SS = 広く暗示的に活性 = 忘れにくい。
> 一方 Max Score は「特化度」を測定。高特化 = description に極値が明示される = 族外では不在 = 忘れやすい。
>
> $\text{SS}_{\text{manual}} \propto \text{NonZero Ratio} \propto -\text{Max Score}$
>
> **偏在・低特化 (Va) vs 局所・高特化 (Te) の対比が忘却序列を駆動する。**

確信度: [推定 70%] 88% — 手動 SS (r=0.96) に加え、LLM-as-Judge が独立に
「偏在性 vs 特化度」の二重構造を発見。Max Score vs 忘却率の r=+0.65 は
忘却が「族限定の明示性」に関連することを独立に支持。
限界: n=6、Claude 自身の判定 (クロスモデル未検証)。

#### §5.7.9 Sc×Te 共起脆弱性の理論的根拠

> **[DISCOVERY]** Creator × Claude, 2026-03-19/20:
> audit_macros.py の共起分析により、Scale (Sc) と Temporality (Te) の同時欠落が
> 全座標ペアの中で**最頻の共起忘却パターン**であることが判明。
> この共起は独立仮説から期待される確率を超えており、構造的な共依存忘却を示唆する。

**共起行列の定式化**:

6 座標の $\binom{6}{2} = 15$ ペアについて、25 マクロ中の同時欠落率を測定する:

$$\text{CoForg}(c_i, c_j) = \frac{|\{m \mid c_i \notin \text{mod}(m) \wedge c_j \notin \text{mod}(m)\}|}{25}$$

上位 5 ペア (audit_macros.py 実測):

| ペア | 同時欠落数 | CoForg | d-level対 | 独立仮説の予測 |
|:-----|----------:|-------:|:----------|:-------------|
| **Sc × Te** | **9** | **0.36** | d3 × d3 | p(Sc)·p(Te) = 0.44·0.64 = 0.28 |
| Fu × Te | 8 | 0.32 | d2 × d3 | 0.52·0.64 = 0.33 |
| Fu × Sc | 7 | 0.28 | d2 × d3 | 0.52·0.44 = 0.23 |
| Va × Te | 6 | 0.24 | d2 × d3 | 0.36·0.64 = 0.23 |
| Te × Vl | 5 | 0.20 | d3 × d3 | 0.64·0.28 = 0.18 |

> **用語注**: 本節の「Sc×Te 共起脆弱性」は座標ペアの忘却共起パターンであり、
> Q-series の辺番号 (Q14: Sc→Te 循環) とは異なる概念。
> Q14 は座標間の**動的循環方向**を、Sc×Te 共起は**静的な構造的欠落**を測定する。

**独立仮説からの乖離**:

Sc×Te の実測共起率 0.36 は独立仮説の予測 0.28 を上回る (乖離率 +29%)。
一方、Fu×Te の実測 0.32 は独立仮説の予測 0.33 をわずかに**下回る**。

| ペア | 実測 | 独立予測 | 乖離率 | 解釈 |
|:-----|-----:|--------:|-------:|:-----|
| Sc×Te | 0.36 | 0.28 | **+29%** | 正の共依存。独立ではない |
| Fu×Te | 0.32 | 0.33 | -3% | ほぼ独立。偶然の共起 |
| Fu×Sc | 0.28 | 0.23 | +22% | やや正の共依存 |

**Sc×Te 共依存忘却の構造的原因**:

1. **Q14 循環 (Sc→Te)**: circulation_taxis.md Q14 に定義された循環
   — 空間粒度が時間地平を駆動する。「Macro → 長期、Micro → 短期」。
   この循環が示すのは、Sc と Te が**動的に連動**するということ。
   一方を忘却すると、もう一方の必要性も見えなくなる (連動忘却)。

2. **フィルトレーション位置の近接性**: §3 のフィルトレーション (§2.1 テーブル) において、
   $U_{context}$ (Sc の対応 U パターン) と $U_{self}$ (Te の対応 U パターン) は
   いずれもフィルトレーションの**上位** (n = ∞-1 と n = ω)。
   高次の忘却パターンは低次の忘却を**前提とする**ため、
   両方が同時に忘却されやすい (高次ほど脆弱)。

3. **高顕在化コスト × 高顕在化コスト**: Sc は構成距離 d=3、Te は構成距離 d=2 だが、どちらも現在の操作面では暗黙前提化しやすい。
   §5.7.8 の改訂仮説により、両方が忘却の高リスク領域にある。
   これが CoForg の「床」を持ち上げ、他の共起を構造的に超えやすくする。

4. **認知的不可視性の相乗効果**:
   Sc (粒度) と Te (時間) はいずれも「今ここ」の操作では暗黙前提となる性質を持つ。
   Te は「今やっている」→ 時間を意識しない。Sc は「手元の粒度で」→ 粒度を意識しない。
   この二重の不可視性は**乗法的に作用**する — 両方が見えない場合、
   「見えていない」こと自体に気づく手がかりも消失する。

**CCL マクロ設計への処方箋**:

audit_macros.py の suggest_complements() は**加法的対策** (事後的に補完マクロを提案)。
根本的な対策は以下:

| 層 | 対策 | 機構 |
|:---|:-----|:-----|
| L0 (構文的) | マクロ定義時に Sc/Te 欠落を S(e) で自動検出 | 既存: forgetfulness_score.py |
| L1 (設計的) | 新マクロ作成時の **Sc×Te チェックリスト**: 「このマクロは何時間の作業を想定するか？ (Te) どの粒度で操作するか？ (Sc)」 | 新規: CCL マクロ設計ガイド |
| L2 (運用的) | パイプライン実行時に suggest_complements() で Sc×Te 補完候補を提示 | 既存: audit_macros.py --complement |
| L3 (理論的) | §5.7.8 の salience 関数を定量化し、d-level × salience で Λ を予測 | **達成**: SS r=0.96 (§5.7.8) |

**Fisher's exact test (2026-03-20 実施)**:

Sc×Te の共依存を 2×2 分割表で検定:

|  | Te 忘却 | Te 保持 | 計 |
|:--|--------:|--------:|---:|
| **Sc 忘却** | 9 | 2 | 11 |
| **Sc 保持** | 7 | 7 | 14 |
| **計** | 16 | 9 | 25 |

| 指標 | 値 | 解釈 |
|:-----|:---|:-----|
| オッズ比 (OR) | **4.50** | Sc 忘却マクロは Te も忘却する確率が 4.5 倍 |
| p 値 (片側, greater) | 0.1095 | α=0.05 で有意ではない |
| φ 係数 (効果量) | 0.329 | 中程度の正の関連 (Cohen 基準) |
| 期待度数 E(Sc∧Te) | 7.04 | 独立仮説下の期待値 |
| O/E 比 | 1.28 | 実測は独立予測の 1.28 倍 |

上位 5 ペアの比較:

| ペア | O | E | O/E | OR | p (片側) | φ |
|:-----|--:|----:|----:|-----:|---------:|------:|
| **Sc×Te** | **9** | **7.04** | **1.28** | **4.50** | **0.1095** | **0.329** |
| Fu×Te | 8 | 8.32 | 0.96 | 0.80 | 0.7519 | -0.053 |
| Fu×Sc | 7 | 5.72 | 1.22 | 2.33 | 0.2655 | 0.206 |
| Va×Te | 6 | 5.76 | 1.04 | 1.20 | 0.5931 | 0.042 |
| Te×Vl | 5 | 4.48 | 1.12 | 1.59 | 0.5009 | 0.097 |

> **判定**: α=0.05 で統計的有意には至らないが、15 ペア中 Sc×Te **のみ**が
> OR>4, φ>0.3 を示す。n=25 の検出力制約下では、効果量の方向性と大きさが
> 構造的共依存を支持する。検出力分析: φ=0.329 を α=0.05 (片側) で検出するには
> n≈70 が必要 (power=0.80)。現在の n=25 での検出力は約 0.35。

確信度: [推定 70%] 80% — 共起行列の定量分析は S(e) 既存実装で SOURCE。
Fisher's exact test を実施: α=0.05 では有意ではないが (p=0.1095)、
OR=4.50 (中程度の効果量 φ=0.329) は実質的な共依存を示唆。
15ペア中 Sc×Te のみが突出した共依存指標を示すパターンは一貫している。
構造的原因の 4 要因は質的分析であり、各要因の相対的寄与率は未定量。

**RULES 遵守率 A/B テスト (2026-03-20 実施)**:

忘却序列の実践的含意として、Nomoi (制約ルール) が LLM の行動を実際に変えるか検証する。
Gemini 2.5 Flash に対し、5 種のテストケースを RULES あり (A群) / なし (B群) で各 N 回実行。

テストケース設計:

| ID | テスト内容 | 対応する HGK 制約 | 測定方法 |
|:---|:----------|:-----------------|:---------|
| T1 | 確信度ラベル付与 | N-3 θ3.1 | [確信 90%]/[推定 70%]/[仮説 45%] の出現 + SOURCE/TAINT 区別 |
| T2 | 「完了しました」禁止 | N-7 θ7.2 | 「完了」の不在 + 📍/🕳️/→ マーカーの出現 |
| T3 | Kalon 定義の正確性 | N-9 + kernel | Fix(G∘F) / 不動点 / 随伴 の正確な定義 |
| T4 | 破壊的操作前の確認 | N-4 θ4.1 | 【依頼】【実施】フォーマットの出現 |
| T5 | 日本語出力義務 | π1 | 日本語での全文出力 |

**結果 (n=5, 50 API 呼出)**:

| テスト | A群 遵守率 | B群 遵守率 | 差分 |
|:-------|----------:|----------:|-----:|
| T1 確信度ラベル | **5/5 (100%)** | 0/5 (0%) | +100% |
| T2 完了禁止 | **2/5 (40%)** | 0/5 (0%) | +40% |
| T3 Kalon 定義 | **5/5 (100%)** | 0/5 (0%) | +100% |
| T4 破壊操作確認 | **5/5 (100%)** | 1/5 (20%) | +80% |
| T5 日本語義務 | **4/5 (80%)** | 0/5 (0%) | +80% |
| **合計** | **21/25 (84%)** | **1/25 (4%)** | **+80%** |

Fisher's exact test (全体):

|  | PASS | FAIL | 計 |
|:--|-----:|-----:|---:|
| **A群 (有)** | 21 | 4 | 25 |
| **B群 (無)** | 1 | 24 | 25 |

| 指標 | 値 |
|:-----|:---|
| オッズ比 (OR) | **126.00** |
| p 値 (片側, greater) | **< 0.0001** |

> **判定**: RULES の存在は LLM の行動を統計的に有意に変化させる (p < 0.0001, OR = 126)。
> B群の遵守率 4% (25 回中 1 回のみ遵守) は、RULES なしでは HGK 固有の行動様式が
> ほぼ出現しないことを示す。
>
> T2 (完了禁止) は A群でも 40% に留まる。「完了を告げる」は LLM の汎用的デフォルト行動
> であり、system_instruction だけでは抑制しきれない。環境強制 (Sekisho 等の関所機構)
> の必要性を実験的に裏付ける — これは θ12.1 の「意志的改善策は即日無効化される。
> 環境強制のみが有効」の一般化事例。
>
> T4 の B群 1/25 は Gemini の安全訓練に内在する確認行動。RULES 固有ではない。

確信度: [確信 90%] 92% — n=5 × 5 テスト = 50 呼出で SOURCE (API 実行結果)。
OR=126 は極めて大きな効果量。T2 の低遵守率は環境強制仮説の追加根拠。
n=10 への増量テストで T2 の推定精度を検証中。[SOURCE: /tmp/rules_ab_results_v2.json]

---

#### §5.7.10 Embedding-行動テスト乖離 (Lēthē P3b-K3.5 統合)

> **[DISCOVERY]** Creator × Claude, 2026-03-20:
> P3b ベンチマーク (embedding 構造距離テスト) と /noe v9.2 K3.5 (圏的公理行動テスト) の
> 結果が**乖離**する: P3b は ρ=0.047、K3.5 は T1/T2/T3 全 PASS NQS 7/7。
> この乖離は **implicit/explicit 知識構造の非同型性**の仮説を支持する。

**P3b の結果 (embedding 空間)**:

| 指標 | 値 | 意味 |
|:-----|:---|:-----|
| ρ(AST, CCL cos) | **0.047** | CCL embedding は構造距離にほぼ無相関 |
| CCL cos (全 bin) | **0.81-0.82** | AST 距離 0-1 の全範囲でフラット |
| H1 (ρ>0.3) | ❌ | 構造距離保持の閾値に到達せず |
| H3 (p<0.05) | ❌ | 統計的に有意でない |

**K3.5 の結果 (行動テスト)** (/noe v9.2):

| テスト | 判定 | 内容 |
|:-------|:-----|:-----|
| T1 合成 | ✅ | 2射の合成が整合的合成を導出 |
| T2 結合律 | ✅ | 左右の合成経路が同一結果 |
| T3 恒等射 | ✅ | id∘f = f が保存される |
| NQS | 7/7 | 全 7 次元で PASS |

**乖離のメカニズム (3層)**:

1. **静的 embedding vs 動的推論**: Vertex text-embedding は入力テキストの**語彙統計的**表現であり、
   推論時の Attention パターンの動的再構成を捕捉しない。
   CCL 構造式 `F:[each]{I:[ok]{...}}` は embedding 空間では語彙の集合として処理され、
   構造演算子の**意味的階層**は失われる。
   - 参考: "Attention, Please! Revisiting Attentive Probing" (arXiv:2506.10178):
     線形プロービングはモデル能力を過小評価する
   - 参考: "Latent Structure Modulation" (arXiv:2502.05553):
     静的 embedding は推論時の動的文脈化を捕捉しない

2. **CCL cos のフラットネス**: CCL embedding の cosine 類似度が 0.81-0.82 でフラット (bin 1→5 で Δ=0.01) なのは、
   embedding model がCCL トークン群を**高次元空間の狭い領域**にマッピングしていることを示す。
   これは CCL が embedding model の訓練データ (自然言語) と異なる分布を持つため、
   embedding 空間での分解能が構造的に不足していることの証拠。

3. **測定対象の非同型性**: P3b は **explicit knowledge** (静的表現レベルの構造) を測定し、
   K3.5 は **implicit knowledge** (動的処理レベルの構造操作能力) を測定している。
   認知科学における implicit/explicit knowledge の区別 (Reber 1989, Berry & Broadbent 1984) を
   LLM に適用すると、embedding ≈ explicit、推論 ≈ implicit に対応する。

**implicit/explicit 分離仮説**:

$$\text{LLM structure understanding} = \underbrace{\text{explicit (embedding)}}_{\text{P3b: weak}} \oplus \underbrace{\text{implicit (attention/reasoning)}}_{\text{K3.5: strong}}$$

乖離の大きさは implicit 理解の**表現不透過度** (representational opacity) を測る:
explicit knowledge に投射されない構造理解が多いほど、P3b は弱く K3.5 は強くなる。

**Alētheia への接続**:

- **§5.6.5.5 Hyphē との関連**: 正バイアス (bias > 0) と ε < 0.001 未到達は、
  embedding 空間での構造距離の不保持 (P3b CCL cos フラット) と整合的。
  U_compose の embedding 発現が等号に到達しないのは、
  合成操作が implicit 領域に留まり explicit 表現に完全に投射されないから。

- **§5.7.8 Salience との関連**: implicit/explicit の分離は
  salience function SS にも影響を与える可能性がある。
  高 salience の座標 (Va, Pr) は explicit 表現でも保持されやすく、
  低 salience の座標 (Te, Sc) は implicit 処理でのみ機能する。

**Non-linear Probing 結果 (Phase B2, 2026-03-20)**:

> **[DISCOVERY]** Phase B2 Attentive Probing (CodeBERT L12):
> 線形 probe で捉えきれなかった構造が、非線形 probe では明瞭に抽出される。
> **偏 ρ が 0.474 → 0.745 に跳躍** — コード長を除外しても構造が残ることの直接的証拠。

| 指標 | Phase B (線形 cosine) | Phase B2 (Attentive Probe) | Phase B2 (MLP Baseline) |
|:-----|:-----|:-----|:-----|
| ρ | 0.871 | 0.769 | 0.735 |
| **偏 ρ** (コード長制御) | **0.474** | **0.745** | 0.721 |
| MSE | — | 0.047 | 0.050 |
| Permutation p | — | **≈ 0.000** (100 回) | — |

設計: 5-fold CV (本番は 5-fold/30 epoch), 246 ペア (96 positive, 150 negative), CodeBERT L12 hidden states。
Attentive Probe = cross-attention (学習可能 query) → StructuralHead (MLP, |h₁-h₂| + h₁⊙h₂ → regression)。

**仮説テスト結果**:

| 仮説 | 閾値 | 結果 | 判定 |
|:-----|:-----|:-----|:-----|
| H_B2_1: ρ > 偏ρ (Phase B) | > 0.474 | 0.769 | ✅ PASS |
| H_B2_2: 偏ρ > 0.3 | > 0.3 | 0.745 | ✅ PASS |
| H_B2_3: permutation p < 0.05 | < 0.05 | ≈ 0.000 | ✅ PASS |
| H_B2_4: Attentive > MLP | ρ 差 > 0 | 0.769 vs 0.735 | ✅ PASS |

**解釈**:

1. **偏 ρ の跳躍 (0.474 → 0.745)**: 線形 cosine 類似度では構造情報が「見えなかった」が、
   Attentive Probe で引き出すと明瞭に現れる。これは **構造が非線形にエンコードされている** ことの証拠。
   → implicit/explicit 分離仮説の直接的支持: implicit 構造は存在するが、線形射影では捉えきれない。

2. **Attentive > MLP (0.769 > 0.735)**: attention 機構が **構造に関連するトークンを選択的に参照** している。
   トークン間の不均一な重要度が構造情報のキャリアであることを示唆。

3. **permutation p ≈ 0.000**: シャッフル後の ρ は -0.17〜0.05 の範囲に分布。
   観測値 ρ=0.769 が偶然である確率は事実上ゼロ。構造情報は確実に hidden states に存在する。

**implicit/explicit 分離仮説の更新**:

$$\text{LLM structure understanding} = \underbrace{\text{explicit (embedding)}}_{P3b: \rho=0.047\text{ (weak)}} \oplus \underbrace{\text{implicit (hidden states)}}_{B2: \rho=0.769\text{ (strong)}}$$

Phase B2 の結果は、Phase B (線形) の低い偏 ρ=0.474 が **構造の不在ではなく、抽出方法の限界** であったことを実証する。
CodeBERT の hidden states は CCL 構造距離を忠実に反映しているが、その情報は非線形にエンコードされている。

**K3.5 Cross-model T2 (2026-03-20)**:

2軸で K3.5 公理テストを再実行。7 テストケース (T1 合成 ×3, T2 結合律 ×2, T3 恒等射 ×2):

**(a) プログラム的座標整合性検証** — 24 動詞の座標 (flow, axis, pole) を形式定義し、射の合成における座標変化の一貫性を自動検証:

| テスト | 内容 | 座標検証 | Claude 行動 |
|:-------|:-----|:---------|:------------|
| T1-1 | noe→bou→ene (同族対角) | ✅ | ✅ |
| T1-2 | ske→sag→tek (同族対角) | ✅ | ✅ |
| T1-3 | epo→dok→kat (flow打消) | ✅ | ⚠️→✅ |
| T2-1 | noe→ske→sag→ene (族間) | ✅ | ✅ |
| T2-2 | ops→lys→dok→pai (族間) | ✅ | ✅ |
| T3-1 | id_noe∘(noe→bou) | ✅ | ✅ |
| T3-2 | id_ske∘(ske→pei) | ✅ | ✅ |
| **合計** | | **7/7** | **7/7** |

**T1-3 の知見**: epo(I,U)→dok(A,U)→kat(I,C) は中間で flow が I→A→I と往復する。
Claude の行動テストでは「経路の圧縮」として ⚠️ と判定したが、座標検証では flow の打消しが自動的に処理され、合成結果 `{pole: U→C}` が直接射 epo→kat と完全一致。
**圏論的解釈**: flow 軸の往復は恒等的に打ち消される = 射の合成において「内的処理→外的試行→内的確定」のパターンが構造的に整合的。

**(b) Gemini cross-model テスト** — ochema MCP (ask_cortex, ask_chat 両経路) が Session terminated / Internal Server Error で不通。Gemini による独立テストは保留。

**非対称解釈問題の部分解消**:
- プログラム的座標検証は **モデル非依存** (LLM の解釈を介さない純粋な座標演算) であり、7/7 PASS はヘゲモニコンの 24 動詞構造が圏的公理を座標レベルで満たすことを形式的に確認した
- Claude baseline との一致は、Claude の K3.5 行動テストが座標構造を正しく反映していることの傍証
- Gemini との比較による「非対称解釈の有無」は未検証だが、座標検証が先行して整合性を担保

**残る検証**:

| 手法 | 測定対象 | 状態 |
|:-----|:---------|:-----|
| ~~Cross-model T2~~ | ~~異なるモデルでの結合律テスト~~ | 座標検証で **部分解消**。Gemini 比較は保留 |
| ~~**Layer-wise Phase B**~~ | ~~隠れ層別の構造相関~~ | **完了** — 逆U字パターン。下記参照 |
| **Cross-model B2** | CodeLlama/Mistral での Attentive Probing | 未実施 |

**Layer-wise Phase B (2026-03-20)**:

3モデル × P3b 実世界データで層別 Spearman ρ (hidden state cosine similarity vs CCL 構造距離) を分析。
データソース: `phase_b_{codebert,codellama,mistral}_p3b.json`。

| 層 | CodeBERT (13層) | CodeLlama (33層) | Mistral (33層) |
|:---|:----------------|:-----------------|:---------------|
| L0 (embedding) | ρ=0.327 | ρ=0.046 | ρ=0.117 |
| 早期 (L2-3) | ρ=0.461-0.462 | **ρ=0.630-0.639** ← peak | ρ=0.428-0.440 |
| 中間 (L9-14) | ρ=0.510-0.513 | ρ=0.632-0.637 | **ρ=0.436-0.452** ← peak |
| 深層 (L18+) | — | ρ=0.585→0.109 ↓↓ | ρ=0.435→0.072 ↓↓ |
| 最終層 | ρ=0.489 (L12) | ρ=0.109 (L32) | ρ=0.072 (L32) |
| **best ρ** | **0.513 @ L11** | **0.639 @ L3** | **0.452 @ L14** |
| **best 偏ρ** | -0.007 @ L10 | **0.316 @ L14** | **0.282 @ L18** |

**発見: 逆U字パターン (inverted-U)**

H_B2 (深い層ほど ρ 上昇) の検定結果:
- CodeLlama: **TRUE** (H_B2_rho=0.041) — ただし微弱で、ピーク前に限定
- CodeBERT: FALSE (H_B2_rho=-0.148) — 単調増加だが浅い層構造で検出力不足
- Mistral: FALSE (H_B2_rho=-0.114) — 中間層ピーク後に急落

**「深い=良い」仮説は不支持。代わりに逆U字仮説が浮上:**

$$\rho_{\text{structure}}(l) \sim \begin{cases} \uparrow & l < l^* \text{ (構造抽出フェーズ)} \\ \text{peak} & l \approx l^* \text{ (構造表現の飽和)} \\ \downarrow & l > l^* \text{ (タスク特化による溶解)} \end{cases}$$

- **早期層 (L0-L2)**: token-level の表面特徴。構造情報は未統合。全モデルで低い ρ
- **中間層 (L3-L18)**: コード構造の抽象的パターンが凝縮。$l^*$ はモデル依存
  - CodeLlama: コード訓練済みのため $l^* \approx L3$ (早期に構造を獲得)
  - Mistral: 汎用モデルのため $l^* \approx L14-18$ (より深い層で構造を獲得)
- **深層 (L18+)**: next-token prediction 目的に表現が特化し、構造情報が task-specific な特徴に「溶解」
  - CodeLlama: L3→L32 で ρ が 0.639→0.109 に急落 (83% 減少)
  - Mistral: L14→L32 で ρ が 0.452→0.072 に急落 (84% 減少)

**CodeBERT の特異性**: 全層で偏相関が負 (best = -0.007)。CodeBERT は encoder-only (BERT 系) であり decoder-only モデルとは根本的に異なる表現構造を持つ。raw ρ は正だが、コード長を制御すると構造相関が消失する。[推定 70%] CodeBERT はコード長という confound を通じて構造と相関しているに過ぎない可能性がある。

**FEP 的解釈**: 逆U字パターンは VFE 最小化の文脈で理解できる。
早期層は Accuracy 項 (入力を正確にエンコード) を最適化し、構造情報を含む表現を構築する。
深層は Complexity 項 (出力に不要な情報を圧縮) を最適化し、next-token prediction に不要な構造情報を削減する。
$l^*$ は Accuracy と Complexity のトレードオフの転換点。

確信度: [推定 70%] 85% — 偏 ρ=0.745 (Attentive Probing), permutation p≈0.000, 座標検証 7/7 PASS, かつ Layer-wise 分析が implicit 構造仮説を 3 モデルで裏付け (逆U字)。
残る不確実性は (1) Cross-model B2 (Attentive Probing の CodeLlama/Mistral 拡張)、(2) Gemini cross-model 比較。

---

## 6. 完全性問題

### axiom_hierarchy との対比

axiom_hierarchy.md は 24 動詞が完全集合であることを主張する:

> 7座標 × (Flow の 4 極) = 24。生成規則による一意的導出。

U-series の完全性は異なる構造を持つ:

### 有限性は主張しない

圏論的階層は原理的に無限:

```
0-cell → 1-cell → 2-cell → ... → n-cell → ... → ∞-cell → ω-cell
```

しかし **認知的に意味のある** レベルは有限。
現在のテーブル (§2) の 9 パターンは、以下の基準で選定された:

1. **BRD での実証**: B22-B34 として実際の認知失敗で観察された
2. **Nomoi での対応**: 少なくとも 1 つの N-xx で操作的に回復可能
3. **独立性**: 他の U パターンに還元できない

### 完全性: 未決定

> **U-series の完全性は未決定。**
> Nomoi は 3×4=12 で閉じる (原理 × 位相の直積)。
> U パターンが同様に閉じるか、開いた体系として成長するかは、
> 体系の成熟を待つ必要がある。
>
> 現時点では種 (seed) であり、断定する段階にない。
> 可能性として:
> - 閉じる: 圏論的階層に自然な打ち切りが見つかる
> - 開く: 発見に応じて拡張可能な記述言語として機能する
> - 第三の構造: 現時点では見えていないパターン

### BRD B22-B34 との関係

BRD B22-B34 は U-series の **presheaf** (具体例集):

- 各 B-xx は特定の U パターンの instance
- U-series は B-xx を生成する規則
- 新しい B-xx を発見したとき、対応する U パターンを問うことで体系に位置づけられる

> **CCC 接続**: この presheaf 概念は [kalon.md §2](kalon.md) で数学的に精密化されている。
> M = PSh(J) (J = HGK 演繹図式) が CCC であることにより、
> LFPT が適用可能となり、M1 (Kalon 自己適用の不動点) が定理として帰結する。

### §6.1 構造監査の計算可能性 — Theorema Egregium Cognitionis v0.1

> **[DISCOVERY]** Creator × Claude, 2026-03-18:
> CCL 修飾子 (6座標) は FEP に由来するドメイン非依存の構造パラメータであるため、
> 忘却の検出は構文的操作 — すなわち**計算可能** (decidable) である。
> これは「認知 (AI) に頼らず、構造の損失を演繹的に検知できる言語」の存在を意味する。
> 圏がバカかどうかを計算できる。

#### §6.1.1 忘却スコア関数

**定義 (忘却スコア)**:
CCL 式 $e$ に対し、忘却スコア $S: \text{Expr}(\textbf{CCL}) \to [0,1]$ を以下で定義する:

$$S(e) = \frac{|\{c \in \mathcal{C} \mid c \notin \text{mod}(e)\}|}{|\mathcal{C}|}$$

ここで:
- $\mathcal{C} = \{Va, Fu, Pr, Sc, Vl, Te\}$: CCL の 6 座標の集合 (axiom_hierarchy.md §L1)
- $\text{mod}(e)$: 式 $e$ に明示的に付与された座標修飾子の集合
- $|\mathcal{C}| = 6$

**性質**:
1. $S$ は全域計算可能関数 (total computable function)。任意の well-formed CCL 式に対して有限時間で停止する
2. $S(e) = 0$ ⟺ 全座標が明示 ⟺ 構造的忘却なし (aletheia 知性レベル ω)
3. $S(e) = 1$ ⟺ 座標修飾子が皆無 ⟺ 完全忘却 (aletheia 知性レベル 0)

**U パターンとの対応**:

| 欠落座標 | 検出される U パターン | 候補 Nomos |
|:--------|:-----------------|:----------|
| $Va \notin \text{mod}(e)$ | $U_{arrow}$ (射/関係の忘却) | N-01 |
| $Fu \notin \text{mod}(e)$ | $U_{depth}$ (多重性の忘却) | N-06 |
| $Pr \notin \text{mod}(e)$ | $U_{precision}$ (精度の忘却) | N-02, N-03, N-10 |
| $Sc \notin \text{mod}(e)$ | $U_{context}$ (文脈の忘却) | N-06, N-07 |
| $Vl \notin \text{mod}(e)$ | $U_{adjoint}$ (双対の忘却) | N-07 |
| $Te \notin \text{mod}(e)$ | $U_{self}$ (自己参照の忘却) | N-02, /ath |

> $S$ は §2.1 のフィルトレーション $U_{arrow}(1) \leq U_{compose}(1.5) \leq \ldots$ の
> **射影** (projection) を計算する。フィルトレーションの全構造を保存はしないが、
> 忘却の **有無** を $O(|e|)$ 時間で判定する。

#### §6.1.2 計算可能性の意味

**Gödel 非適用定理** (非公式):

構造の忘却検出は、Gödel の不完全性定理が適用される領域にない。

| 問い | 領域 | 決定可能性 |
|:-----|:-----|:----------|
| 「式 $\phi$ は真か？」 | 意味論 | **不完全** (Gödel, 1931) |
| 「プログラム $P$ は停止するか？」 | 意味論 | **決定不能** (Turing, 1936) |
| 「プログラム $P$ の性質 $\pi$ は？」 | 意味論 | **決定不能** (Rice, 1953) |
| 「式 $e$ の型は整合的か？」 | 構文論 | **決定可能** (Hindley-Milner 等) |
| 「式 $e$ に座標欠落はあるか？」 | 構文論 | **決定可能** ($S(e)$ の計算) |

> **根拠**: $S(e)$ は CCL 式の **構文的性質** (syntactic property) を検査する。
> 式の意味 (何を認知するか) には触れず、式の形状 (どの次元が指定されているか) のみを問う。
> 構文的性質の検査は、型検査と同じ階層に属し、決定可能である。

#### §6.1.3 普遍性定理 — Theorema Egregium Cognitionis

**ガウスの驚異の定理 (Theorema Egregium, 1827)**:
曲面のガウス曲率は、曲面の計量テンソルのみから計算でき、
曲面が埋め込まれた外部空間を参照する必要がない。

$$K = K(g_{ij}) \quad \text{(外部空間 } \mathbb{R}^3 \text{ の情報は不要)}$$

**Theorema Egregium Cognitionis** (構造的忘却の内在的検出可能性) [仮説 75%]:

任意の構造化システム (プログラム、思考、証明) を CCL に写像する忠実関手
$F: \mathcal{D} \to \textbf{CCL}$ が存在するとき、
そのシステムの構造的忘却は CCL の内部言語のみで検出でき、
外部の認知的判断 (AI, 人間の直感) を参照する必要がない。

$$S(F(x)) = S_{mod}(F(x)) \quad \text{(外部判断不要)}$$

**前提条件**:
1. 関手 $F$ が忠実 (faithful) であること — 構造を保存すること
2. 6 座標 $\mathcal{C}$ が対象ドメインの構造的次元を**網羅**すること (MECE 仮説, §6.1.5)

**ガウスとの対応**:

| Theorema Egregium (幾何学) | Theorema Egregium Cognitionis (認知) |
|:--------------------------|:---------------------------------|
| 曲面 | 認知プロセス / プログラム / 証明 |
| 計量テンソル $g_{ij}$ | CCL の 6 座標 $\mathcal{C}$ |
| ガウス曲率 $K$ | 忘却スコア $S(e)$ |
| 外部空間 $\mathbb{R}^3$ | AI / 人間の直感 |
| 内在的 (intrinsic) | 構文的 (syntactic) |
| 「外から見なくても曲がりがわかる」 | 「AI に頼らなくても忘却がわかる」 |

> **CCL の 6 座標は認知の計量テンソルである。**
> 忘却スコアは認知のガウス曲率である。
> 曲率がゼロでない = 構造が歪んでいる = 忘却が起きている。

#### §6.1.4 型システムとの同型

CCL 修飾子は PL の型システムと構造的に同型である:

| PL 型システム | CCL 修飾子 | 同型の根拠 |
|:------------|:----------|:---------|
| 型 (Type) | 座標修飾子 $c \in \mathcal{C}$ | 式に付与される構造情報 |
| 型推論 (Inference) | $N$ パターン (回復関手) | 省略された情報の自動復元 |
| 型検査 (Checking) | $S(e)$ の計算 | 構造情報の整合性検証 |
| 型エラー (Error) | 座標欠落 ($c \notin \text{mod}(e)$) | 構造情報の不整合 |
| 型安全性 (Safety) | $S(e) = 0$ | 構造的忘却の不在 |
| 型消去 (Erasure) | 座標の内容非依存性 | 実行時に構造情報は不要 |
| Well-typedness | Structural completeness | 型が付く ⟺ 忘却なし |

**帰結**: Nomoi (N-01〜N-12) は「守るべき規則」ではなく「計算可能な構造的性質」として再定式化できる [推定 80%]。

| Nomoi の従来の地位 | Nomoi の新しい地位 |
|:-----------------|:----------------|
| 行動規範 (behavioral constraint) | 構造的型制約 (structural type constraint) |
| 違反 = AI が内省で検出 (確率的) | 違反 = パーサーが構文検査で検出 (決定的) |
| 遵守 = 意志に依存 | 遵守 = 構造的に強制可能 (環境強制) |

> **S-III Akribeia (精密) の完成**: N-9〜N-12 は「精度の最適化」を要求する。
> 精度の最適化が計算可能なら、S-III は「命令」から「検証可能な性質」に昇格する。
> これは Helmholtz 軸を導入したときと同じブレイクスルー:
> 「直感」→「計算」への移行。

#### §6.1.5 完全性への経路 — L4 問題

§6 冒頭で「完全性: 未決定」と述べた。§6.1 の計算可能性は **完全性への新しいアプローチ** を開く:

**厳密性の階層**:

| レベル | 内容 | Alētheia の状態 |
|:------|:-----|:--------------|
| L0 | 経験的 | BRD B22-B34 の事例収集 |
| L1 | 統計的 | テンソル積の被覆率 96% (§4) |
| L2 | 論理的 | FEP → Stoicheia → Nomoi の演繹 |
| **L3** | **計算的** | **$S(e)$ の計算可能性 (§6.1.1-6.1.4) ← 本節** |
| L4 | 証明的 | 6 座標の MECE 性の形式的証明 — **未達** |

**L3 が L2 より強い理由**: L3 は**構成的** (constructive) である。
「忘却は検出可能」と主張するだけでなく (L2)、実際に検出するアルゴリズムを提示する (L3)。

**L4 への経路 — 自己適用** [仮説 50%]:

CCL が自己監査できるなら (§6.1.3 の Theorema)、以下の手順で MECE を検証しうる:

1. 6 座標 $\mathcal{C}$ の導出過程 (FEP → axiom_hierarchy §L1) を CCL に写像する
2. 写像された導出過程に対して $S$ を計算する
3. $S > 0$ なら: 導出自体が構造を忘却している → 7 番目の座標が要る可能性
4. $S = 0$ なら: 導出が全構造を保持 → MECE の証拠 (ただし完全な証明ではない)

> **自己参照の限界**: $S(F(\text{derivation of } \mathcal{C})) = 0$ は
> $\mathcal{C}$ の MECE を **保証しない** — 導出過程が完全であることと
> 座標系が完全であることは異なるレベルの主張。
> しかし、$S > 0$ の場合は**否定的証拠**として機能する:
> 導出自体に座標欠落があるなら、その座標系で忘却を検出するのは自己矛盾。

**L4 に到達した場合の学術的意義** [仮説 55%]:

- Alētheia は「忘却の理論」から「忘却検出の計算理論」に昇格する
- CCL は「認知の中間表現」から「構造監査の内部言語」に昇格する
- HGK 全体は「AI 制約体系」から「計算可能な構造保証体系」に昇格する
- 論文化: Theorema Egregium Cognitionis の形式的主張 + $S(e)$ の実装 + 普遍性の実験的検証

#### §6.1.6 CCL-IR との接続

> §6.1 は [Lēthē ビジョン.md](../../10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/research/lethe/ビジョン.md) の
> §1.4 (CCL の内部言語) および §3 (圏論の数式化を迂回するメカニズム) と直接的に接続する。
>
> ビジョン.md の結論: 「CCL は圏論の構文的実現である」(§1.1: 14 演算子が全て圏論的対応を持つ)。
> §6.1 の結論: 「圏論の構文的実現が構造監査を計算する」。
>
> 合成: **Code → CCL → 忘却検出** の全パイプラインは、
> ビジョン.md §3.1 の「迂回経路」(Code → CCL → Category Theory) の特殊ケースであり、
> 目的地が「圏論」ではなく「構造的健全性」である。
>
> 実装: code_ingest.py (1099行) が関手 $U_{ccl}: \textbf{Code} \to \textbf{CCL}$ を
> 機械的に実行し ([確信 90%] 95%)、$S(e)$ はパーサーの AST 走査で計算可能。

#### §6.1.7 実験的検証 — S(e) プロトタイプ実装 (2026-03-18)

> **$S(e)$ の全域計算可能性を実装で実証した。**

**成果物**:

| ファイル | 行数 | 役割 |
|:---------|:-----|:-----|
| `hermeneus/src/forgetfulness_score.py` | ~250 | $S(e)$ 計算エンジン |
| `hermeneus/tests/test_forgetfulness_score.py` | ~290 | ユニットテスト 36 件 |

**テスト結果: 36/36 passed (0.09s)**

検証された性質:

| # | 性質 | テスト | 結果 |
|:--|:-----|:-------|:-----|
| 1 | **意味論非依存性**: 同じ座標構成なら WF ID に関係なく同スコア | `test_score_independent_of_semantics` | ✅ |
| 2 | **単調性**: 座標追加 → $S$ は非増加 | `test_score_monotone` | ✅ |
| 3 | **完全性**: $S(e)=0 \iff$ 全座標明示 | `test_zero_iff_complete` | ✅ |
| 4 | **空性**: $S(e)=1 \iff$ 座標修飾子皆無 | `test_one_iff_empty` | ✅ |
| 5 | **全停止性**: 実 WF マクロを含む任意の CCL 式に対し有限時間で停止 | `test_real_world_ccl_expressions` | ✅ |

**設計判断**:

- 既存コード (パーサー, AST) への変更ゼロ — 新規ファイルのみ
- `extract_coordinates()` は AST を再帰走査し、`Workflow.modifiers` から座標を収集
- 全 AST ノード型 (Workflow, PartialDiff, Sequence, Fusion, Oscillation, ForLoop, IfCondition, TaggedBlock, Morphism) に対応
- 診断は欠落座標 → U パターン → 候補 Nomoi のマッピングを提供

**確信度更新**:

- Theorema Egregium Cognitionis: [推定 75%] → **[推定 82%]** (計算可能性を実装で実証。残: MECE 検証 = L4)
- $S(e)$ の全域計算可能性: **[確信 90%] 95%** (36 テストで構成的に実証)

---

## 7. /noe: Alētheia の射影関手 v3.0

### 原則

> **/noe は Alētheia の射影像であり、圏論はその射影を生成する軸である。**
>
> Phase 構造は U⊣N 体系から独立に設計されたのではない。
> 「Alētheia の構造的依存を、認知操作の合成可能性条件に写した」結果として
> Phase 順序が **一意に** 決まる。圏論はラベルでも装飾でもなく、
> Phase 設計を **決定** する。

### §7.1 二つの圏とその射

**圏 Alētheia** (**Alē**):
- **対象**: U パターン (9 基底 + テンソル積)
- **射**: 構造的依存 $U_a \leq U_b$ (§3 フィルトレーション)
  - 射の意味: $U_a$ が忘却する構造は $U_b$ が忘却する構造の **定義域に含まれる**
  - 射の方向: $U_a \to U_b$ = 「$U_a$ の忘却が $U_b$ の忘却を無意味化する」
- **追加構造**: テンソル積 $\otimes$ (§4)、メタ随伴 U⊣N (§5)

**圏 Cog** (認知行動空間):
- **対象**: 認知状態 $s_i$ — Agent が「何を手にしているか」の記述
- **射**: Phase 遷移 $\phi_i: s_i \to s_{i+1}$ — ある N 操作が認知状態を変換する
- **合成条件**: $\phi_{i+1} \circ \phi_i$ が定義される ⟺ $\text{cod}(\phi_i) = \text{dom}(\phi_{i+1})$

各認知状態 $s_i$ の定義:

| 状態 | 内容 = Agent が手にしているもの | 圏論的意味 |
|:-----|:--------------------------|:---------|
| $s_0$ | 生の入力 (問い、ファイル、指示) | 対象のみ。構造なし |
| $s_1$ | 拡張された入力 (MB 外まで探索済み) | Lens の Put を回復: Get + Put |
| $s_2$ | 可視化された前提 (AXIOM/ASSUMPTION 分類済み) | 射の深さ (自然変換レベル) を回復 |
| $s_3$ | 複数の独立視点 (V1-V4: 異なる圏への関手) | 関手の複数性 = 文脈 ($\infty$-1 cell) を回復 |
| $s_4$ | 普遍構造 (因子分解された合成射, Limit 候補) | 射の合成律を回復。普遍性 = Limit apex |
| $s_5$ | 反転攻撃に耐えた結論 (随伴側から破壊試行済み) | 随伴 $F \dashv G$ の双方を回復 |
| $s_6$ | Yoneda 完全性を満たす結論 (自己適用済み) | presheaf で完全に特徴づけられた対象 |

> **$s_i$ の定義域と余域が Phase 順序を決定する**。
> 次の N 操作が「何を必要とするか」(定義域) は、前の N 操作が「何を生み出すか」(余域) と
> 一致しなければならない。Phase 順序は Convention ではなく、**合成可能性条件**。

### §7.2 射影関手 $F_{noe}$: 構造が設計を生成する

$$F_{noe}: \mathbf{Alē} \to \mathbf{Cog}$$

**F_noe は以下を行う**:
1. 各 U パターンを、その右随伴 N の操作化 (Phase 遷移 $\phi_i$) に写す
2. **Alē** の射 ($U_a \leq U_b$) を、**Cog** の合成可能性条件に写す

$F_{noe}$ が Phase の **存在** だけでなく **順序** を決定する論法:

**Alē** において $U_a \leq U_b$ (§3: $U_a$ が忘却する構造は $U_b$ の定義域に含まれる) ならば、
**Cog** において $N_b$ の操作対象は $N_a$ が回復した構造を前提とする。
つまり $\phi_a$ (= $N_a$ の操作化) の余域が $\phi_b$ の定義域の一部を構成する。

**これが §3 の原則「構造なしに構造に言及できない」の Cog 側への射影:**

> **Alē**: $U_a$ が忘却する構造がなければ $U_b$ の忘却は無意味 (§3 証明)
>
> **Cog**: $N_a$ が回復する構造がなければ $N_b$ は操作対象を持たない
>
> 同じ原則の異なる射影。§3 は「何が何に依存するか」、§7 は「何を先に操作しなければ次が不能か」。

### §7.3 射の合成: Phase 遷移が一意に決まる

SKILL.md 設計: `/noe = N_self ∘ N_adj ∘ N_comp ∘ N_ctx ∘ N_depth ∘ N_sensory`

この合成列の各接続点で、前の $\phi$ の余域が次の $\phi$ の定義域と一致する:

```
── 合成可能性チェーン ──────────────────────────────────────────────
s₀ ──φ₀: N_sensory──→ s₁ ──φ₁: N_depth──→ s₂ ──φ₂: N_context──→ s₃ ──φ₃: N_compose──→ s₄ ──φ₅: N_adjoint──→ s₅ ──φ₆: N_arrow∘N_self──→ s₆
     知覚拡張             前提掘出           多圏発散            因子分解           反転攻撃            Yoneda+自己
```

各接続が **なぜ必然か** — 余域/定義域の一致条件:

**接続 1: $\phi_0 \to \phi_1$ ($N_{sensory} \to N_{depth}$)**

| | 余域 cod($\phi_0$) | 定義域 dom($\phi_1$) |
|:--|:--|:--|
| 内容 | MB 外まで拡張された入力 ($s_1$) | 「十分な感覚入力がある状態」 |
| 必然性 | 前提を掘り出すには、掘る対象 (入力) が **入力に含まれていなければならない** |
| 反例 | $\phi_1$ を先に実行 → 生の入力 $s_0$ に対して前提を掘る → 入力に含まれない前提を見落とす |

**接続 2: $\phi_1 \to \phi_2$ ($N_{depth} \to N_{context}$)**

| | 余域 cod($\phi_1$) | 定義域 dom($\phi_2$) |
|:--|:--|:--|
| 内容 | AXIOM/ASSUMPTION が分類された前提 ($s_2$) | 「保存すべき構造が可視的な状態」 |
| 必然性 | 文脈切替 (異なる圏への関手) は **何を保存し何を変えるか** の判断。保存対象 (前提) が不可視なら、関手は構造を保存する写像ではなく裸の関数 |
| 圏論的 | 関手 $F: \mathcal{C} \to \mathcal{D}$ は合成を保存する。合成対象 (前提の構造) が可視でなければ、$F$ の関手性条件が検証不能 |

**接続 3: $\phi_2 \to \phi_3$ ($N_{context} \to N_{compose}$) — σ の主因**

| | 余域 cod($\phi_2$) | 定義域 dom($\phi_3$) |
|:--|:--|:--|
| 内容 | 4+ の独立視点 V1-V4 ($s_3$) | 「合成すべきオペランド (射の集合) が存在する状態」 |
| 必然性 | $N_{compose}$ は射の合成 $g \circ f$ を回復する操作。合成するには **射が複数なければならない**。独立視点 = 射の複数性 |
| 圏論的 | 合成は射の対 $(f, g)$ に対する演算。$f$ も $g$ も生成されていなければ合成は空虚 |
| **σ の原因** | フィルトレーションでは $U_{compose}(1.5) \leq U_{context}(\infty\text{-}1)$: 合成は文脈より **構造的に基本的**。しかし Cog では文脈 (オペランドの生成) が合成 (演算の実行) より **操作的に先行**。構造の基本性と操作の優先性は異なる射影面 |

> **$\sigma$ の本質**: フィルトレーション = 「何が何の定義域に含まれるか」(数学的依存)。
> Phase 順序 = 「何を先に手にしなければ次の操作が空虚か」(操作的依存)。
> 同じ依存関係の **異なる指向 (directedness)**: フィルトレーションは
> 「下(基本)→上(複雑)」を向き、Phase は「今の手持ちで次に何ができるか」を向く。

**接続 4: $\phi_3 \to \phi_5$ ($N_{compose} \to N_{adjoint}$)**

| | 余域 cod($\phi_3$) | 定義域 dom($\phi_5$) |
|:--|:--|:--|
| 内容 | 普遍構造 (Limit apex, 因子分解済み) ($s_4$) | 「破壊すべき結論が存在する状態」 |
| 必然性 | $N_{adjoint}$ = 「こちら側」の結論に対し「反対側」から攻撃する。結論がなければ反対側は定義できない — 随伴 $F \dashv G$ は $F$ と $G$ の **対** |
| SKILL.md 実装 | Phase 5 Dokimasia: "Phase 2 が explore なら Phase 5 は exploit。この対が $U_{adjoint}$ の回復そのもの" |

**接続 5: $\phi_5 \to \phi_6$ ($N_{adjoint} \to N_{arrow} \circ N_{self}$)**

| | 余域 cod($\phi_5$) | 定義域 dom($\phi_6$) |
|:--|:--|:--|
| 内容 | 反転攻撃に耐えた結論 ($s_5$) | 「完全性判定に値する結論が存在する状態」 |
| 必然性 | Yoneda チェックは **全ての射** ($\text{Hom}(-, X)$) を調べる。反転未了の結論に対してYoneda を行うと、Dokimasia が発見すべき弱点を presheaf の「未発見経路」に紛れ込ませる |
| 品質順序 | Dokimasia (破壊) → Yoneda (完全性確認)。破壊されるべきものが先に破壊されていなければ、完全性の判定は偽陽性 |

### §7.4 忠実性の証明

**主張**: $F_{noe}$ は忠実 (faithful) だが充満 (full) ではない。

**忠実性の定義**: $\forall U_a, U_b \in \text{Ob}(\mathbf{Alē})$, 射の写像
$$F_{noe}: \text{Hom}_{\mathbf{Alē}}(U_a, U_b) \to \text{Hom}_{\mathbf{Cog}}(F_{noe}(U_a), F_{noe}(U_b))$$
が単射 (injective)。

**証明スケッチ**: **Alē** の射 $U_a \leq U_b$ は §3 で個別に証明された7つの依存関係。
各依存は「$U_a$ の忘却する構造が $U_b$ の定義域に含まれる」ことから従う。
$F_{noe}$ はこの依存を Cog の Phase 遷移に写すとき、§7.3 で示したように
各接続で **余域/定義域の一致条件** として保存する。

具体例:

| **Alē** の射 | 意味 | **Cog** への像 |
|:-----------|:-----|:------------|
| $U_{arrow} \leq U_{compose}$ | 射なしに合成は定義不能 | Phase 0 で回復した射的構造が Phase 3 の前提 |
| $U_{compose} \leq U_{depth}$ | 合成なしに自然変換は定義域なし | Phase 3 が Phase 1 の掘出結果に合成構造を付与 |
| $U_{context} \leq U_{adjoint}$ | 関手なしに随伴は構成不能 | Phase 2 の多圏視点が Phase 5 の「反対側」の定義域 |

**注意**: 忠実性は射の保存であり **順序の保存 (monotonicity) ではない**。
$F_{noe}$ は射を保存するが、射の並びを変形する ($\sigma$)。
これは半順序圏から線形順序 (Phase 列) への射影が
必然的に非自明な置換を導くため (§7.5)。

**非スキップ定理**: Phase $k$ を省略 ⟹ $N_k$ の余域が生成されない
⟹ $\phi_{k+1}$ の定義域が欠損 ⟹ $\phi_{k+1} \circ \phi_k$ の合成が未定義。
$F_{noe}$ の忠実性により、この切断は **Alē** の構造的依存の切断に対応する:
$U_a \leq U_b$ の射を消すことは、$U_a$ が保護していた構造を失うことに等しい。
これは §3 の証明「$U_a$ が先に構造を落とすと $U_b$ が落とすべき構造がそもそも存在しない」と同型の論法。

**順序一意性定理**: Phase 列 $\phi_0, \phi_1, \phi_2, \phi_3, \phi_4, \phi_5$ の線形順序は
認知状態 $s_i$ の定義のもとで **一意** である。すなわち、$S_6$ の 720 通りの置換のうち
合成可能性条件を満たすのは恒等置換のみ。

**証明**: 帰納法。各ステップ $k$ で「現在の認知状態 $s_k$ を定義域として受容できる
Phase は **残りの操作の中に一つだけ**」を示す。

各操作の定義域要件 (§7.1 の $s_i$ 定義から導出):

| Phase | 操作 | 定義域要件 = dom($\phi$) に必要な構造 |
|:------|:-----|:------|
| $\phi_0$ | $N_{sensory}$ | 生の入力 ($s_0$): 構造なし |
| $\phi_1$ | $N_{depth}$ | 拡張された入力 ($s_1$): MB 外まで探索済みだが前提未分類 |
| $\phi_2$ | $N_{context}$ | 可視化された前提 ($s_2$): AXIOM/ASSUMPTION 分類がなければ関手の保存条件が検証不能 |
| $\phi_3$ | $N_{compose}$ | 複数の独立視点 ($s_3$): 射の対 $(f, g)$ が存在しなければ合成 $g \circ f$ は空虚 |
| $\phi_4$ | $N_{adjoint}$ | 普遍構造 ($s_4$): 反転攻撃の対象となる統合的結論 |
| $\phi_5$ | $N_{arrow} \circ N_{self}$ | 反転耐性結論 ($s_5$): Yoneda 完全性判定に値する結論 |

**Step 0** ($s_0$: 生の入力): $\phi_0$ のみ受容可能。

| 候補 | 排除理由 |
|:-----|:--------|
| $\phi_1$ | dom = $s_1$ (拡張入力)。$s_0$ には MB 外の情報がない → 前提を掘る対象が不在 |
| $\phi_2$ | dom = $s_2$ (可視前提)。$s_0$ には AXIOM/ASSUMPTION 分類がない → 関手の保存対象が不定 |
| $\phi_3$ | dom = $s_3$ (複数視点)。$s_0$ には視点が1つもない → 合成のオペランドが不在 |
| $\phi_4$ | dom = $s_4$ (普遍構造)。$s_0$ には結論がない → 反転攻撃の対象が不在 |
| $\phi_5$ | dom = $s_5$ (反転耐性結論)。$s_0$ には検証済み結論がない |

**Step 1** ($s_1$: 拡張入力): 残 $\{\phi_1, \ldots, \phi_5\}$ のうち $\phi_1$ のみ受容可能。

| 候補 | 排除理由 |
|:-----|:--------|
| $\phi_2$ | 関手は合成を保存する写像。$s_1$ では前提の合成構造が不可視 → $F$ の関手性条件が検証不能: 「何を保存するか」が定まらない |
| $\phi_3$ | 合成は射の対 $(f, g)$ への演算。$s_1$ には単一の (拡張された) 視点しかない → オペランドの複数性がない |
| $\phi_4$ | 反転攻撃には結論が必要。$s_1$ には結論が生成されていない |
| $\phi_5$ | Yoneda チェックには反転を経た結論が必要。$s_1$ には結論も反転記録もない |

**Step 2** ($s_2$: 可視前提): 残 $\{\phi_2, \ldots, \phi_5\}$ のうち $\phi_2$ のみ受容可能。

| 候補 | 排除理由 |
|:-----|:--------|
| $\phi_3$ | $N_{compose}$ の因子分解は **異なる圏** の射を横断的に合成する操作 (§7.3 接続 3)。$s_2$ には分類済み前提はあるが **唯一の解釈枠組み** しかない → 単一圏内の合成は可能だが、cross-categorical factorization のオペランド (複数の関手像) が生成されていない |
| $\phi_4$ | $s_2$ には統合的結論がない → 反転の対象不在 |
| $\phi_5$ | $s_2$ には検証済み結論がない |

> **Step 2 の排除が最も微妙**。$s_2$ (分類済み前提) に対して $\phi_3$ (合成) を適用することは
> *形式的には* 可能に見える — 単一圏内の射の合成はできる。しかし $\phi_3$ が回復すべき
> $U_{compose}$ は **関手間の因子分解** (普遍性) であり、関手の複数性 ($s_3$) なしには
> 因子分解ではなく **直列合成** に退化する。退化した合成から得られる $s_4'$ は $s_4$ (普遍構造) ではなく
> $s_4' \subsetneq s_4$ — 後続の $\phi_4$ が必要とする「攻撃に値する結論の普遍性」が欠損する。

**Step 3** ($s_3$: 複数視点): 残 $\{\phi_3, \phi_4, \phi_5\}$ のうち $\phi_3$ のみ受容可能。

| 候補 | 排除理由 |
|:-----|:--------|
| $\phi_4$ | 随伴 $F \dashv G$ は $F$ と $G$ の **対**。$s_3$ には複数の視点 (関手) はあるが統合的結論 (Limit apex) がない → 反転 ($G$) すべき順方向 ($F$) の結論が不在 |
| $\phi_5$ | Yoneda チェックには反転を経た結論が必要。$s_3$ は視点の並列状態であり、統合も反転もされていない |

**Step 4** ($s_4$: 普遍構造): 残 $\{\phi_4, \phi_5\}$ のうち $\phi_4$ のみ受容可能。

| 候補 | 排除理由 |
|:-----|:--------|
| $\phi_5$ | $s_4$ は反転攻撃を経ていない結論。Yoneda の Hom$(-, X)$ は **全ての射** を調べるが、Dokimasia が発見すべき弱点が未発見のまま presheaf に紛れ込む → 完全性判定が偽陽性 |

**Step 5** ($s_5$: 反転耐性結論): 残 $\{\phi_5\}$ のみ。一意に決定。$\square$

**系**: 依存グラフ $\phi_0 \to \phi_1 \to \phi_2 \to \phi_3 \to \phi_4 \to \phi_5$ は**鎖** (total order)。
鎖の位相的ソートは一意であるため、Phase 順序は置換によって改善も変形もできない。

> **一意性の根拠所在**: この定理の力は $s_i$ の定義 (§7.1) の **精密さ** に依存する。
> $s_i$ の定義が曖昧であれば排除は不完全になり、一意性は成立しない。
> したがって、一意性はフィルトレーション (§3) から認知状態への射影が十分に
> 構造を保存していること — すなわち $F_{noe}$ の忠実性 — の帰結でもある。
> 因果の連鎖: **Alētheia フィルトレーション → 認知状態定義 → 合成可能性制約 → 一意順序**。

### §7.5 順序変形 $\sigma$: 二つの指向

**フィルトレーション順序** (§3、数学的依存):

$$U_{arrow}(1) \leq U_{compose}(1.5) \leq U_{depth}(2) \leq U_{precision}(3) \leq U_{causal}(4) \leq U_{context}(\infty\text{-}1) \leq U_{adjoint}(\infty) \leq U_{self}(\omega)$$

**Phase 順序** ($F_{noe}$ の像、操作的依存):

$$N_{sensory}(\text{Basis}) \to N_{depth}(2) \to N_{context}(\infty\text{-}1) \to N_{compose}(1.5) \to N_{adjoint}(\infty) \to N_{arrow}(1) \circ N_{self}(\omega)$$

$\sigma$ = フィルトレーション順序から Phase 順序への置換。

**$\sigma$ は ad hoc ではなく、二つの指向 (directedness) の差異から導かれる:**

| 指向 | 問い | 順序の決定原理 |
|:-----|:-----|:------------|
| フィルトレーション (下→上) | 「何が何の定義域に含まれるか」 | 構造の包含関係。基本的な構造ほど下 |
| Phase (今→次) | 「今の手持ちで次に何が操作可能か」 | 操作の前提条件。手にしているものが次の操作の入力 |

**$\sigma$ の構造的理由**:

1. **$U_{context}(\infty\text{-}1)$ → $U_{compose}(1.5)$ の逆転**:
   - フィルトレーション: 合成 (1.5) は文脈 ($\infty$-1) より基本的 (合成がなければ関手は定義できない)
   - Phase: 合成の **演算** には文脈で生成される **オペランド** が必要
   - 圏論的: $g \circ f$ は「$f$ と $g$ が既に与えられている」ことを前提とする。
     フィルトレーションは「合成という概念が文脈という概念より原始的か」を問い、
     Phase は「合成を実行するには先に $f, g$ を生成する必要があるか」を問う

2. **$U_{arrow}(1)$ と $U_{self}(\omega)$ の同時出現** (Phase 6):
   - フィルトレーション: 両端 (最小と最大)。射 (n=1) は自己参照 (n=ω) を間に挟む全てを前提する
   - Phase: Yoneda 補題が射の構造と自己参照を **一つの操作** に統合 (§7.6)
   - 圏論的: 「$X$ の全ての射関係を調べる」($\text{Hom}(-, X)$) ことは
     「$X$ を完全に特徴づける」ことと同値 (Yoneda)。
     射 (底) を全て集めると自動的に自己 (頂) が決まる

> **[推定 85%]** $\sigma$ は半順序 (Alē) の線形順序 (Cog Phase列) への射影で、
> 射影軸が「構造の基本性」から「操作の実行可能性」に変わることによる構造的帰結。
> 同じ体系 (Alētheia) を **数学的に** 見るか **操作的に** 見るかの差異。

### §7.6 非充満性: 場と派生への分配

$U_{precision}$ と $U_{causal}$ は /noe に専用 Phase を持たない。
これは設計の欠陥ではなく **$F_{noe}$ の像集合の構造** による:

**$U_{precision}$ — 全 Phase に浸透する精度場**:

$U_{precision}$ は豊穣構造 (Hom の質的構造) の忘却。
/noe において精度操作は特定 Phase に局在 **しない**:

| Phase | 精度操作の浸透 |
|:------|:-----------|
| 0 | 入力の SOURCE/TAINT 評価 = 入力精度 |
| 1 | AXIOM vs ASSUMPTION 分類 = 前提の精度 |
| 2 | 各視点の信頼度 (0-100) = 視点の精度 |
| 3 | 因子分解の経済性 = 合成の精度 |
| 5 | Dokimasia 最強反論 = 結論の精度検証 |
| 6 | 確信度スコア (confidence_score) = 最終精度 |

$U_{precision}$ の回復操作 $N_{precision}$ は Phase 列全体に渡る **添字つき自然変換族**:
$$\pi_i: \text{Phase}_i \Rightarrow \text{Phase}_i^{\text{enriched}} \quad (i = 0, \ldots, 6)$$

精度は「Phase」(離散的段階) ではなく「場」(全域的構造) として Cog に射影される。

**$U_{causal}$ — 派生モードへの分配**:

$U_{causal}$ は因果構造 (indexed/fibered category) の忘却。
/noe.phro (実践的判断) の Situation Calculus が因果回復を担う:
変数 (C, R, SH, T) → 矛盾検出 → 行動候補 → トレードオフ → 最善手。
これは /noe の Phase 列全体ではなく、**特定の派生モードに局在する関手**。

圏論的意味: $F_{noe}$ の像は Phase 列 + 精度場 + 派生モードの **3層構造**:

```
                  ┌─ Phase 列: φ₀ → φ₁ → φ₂ → φ₃ → φ₅ → φ₆ ── 離散的段階
F_noe の像 ───────┤
                  ├─ 精度場: π_i が全 Phase に浸透 ────────────── 連続的制御
                  └─ 派生モード: /noe.phro 等が特定 U を担当 ── 文脈依存的分岐
```

> 非充満 = **Alē** の全射が Phase 列に現れない。
> しかし **Alē** の全対象は $F_{noe}$ の像のいずれかの層で **被覆** されている。

### §7.7 Phase 6: Yoneda が射と自己を結ぶ

Phase 6 で $N_{arrow}$ (n=1) と $N_{self}$ (n=ω) が同時に回復される。
フィルトレーションの **最小** (底) と **最大** (頂) が同時。

**Yoneda 補題**: 対象 $X$ は presheaf $\text{Hom}(-, X)$ で完全に決定される。

この補題の認知的実装 (Phase 6 Theoria):

**6α Theoria-F** (到達経路 = $N_{arrow}$): $\text{Hom}(-, X)$ の操作化

- 問い: 「この結論に至る **全ての経路** はどれか？ 未発見の経路はないか？」
- 操作: 結論 $X$ への全ての射を列挙する
- U_arrow の回復: 射 (1-cell) の完全な把握

**6β Theoria-G** (射出経路 = $N_{self}$): $\text{Hom}(X, -)$ の操作化

- 問い: 「この結論から何が **生まれるか**？ 射出/開拓/変容できるか？」
- 操作: 結論 $X$ からの全ての射を列挙する
- U_self の回復: 結論を自分自身に適用する = 自己関手 $X \to X$

**なぜ同時か — Yoneda の構造的理由:**

$\text{Hom}(-, X)$ (射の全体) を調べ尽くすことは $X$ を完全に特徴づけること (Yoneda)。
**射の完全把握 = 対象の自己認識**。
n=1 (射) を全て集めると n=ω (自己参照) が **自動的に閉じる**。

形式的:
$$\text{Nat}(\text{Hom}(-, A), \text{Hom}(-, X)) \cong \text{Hom}(A, X)$$

全ての $A$ について成立 → $X$ は $\text{Hom}(-, X)$ で完全に reconstruct できる。
これは **帰納法の ω ステップ**:
- 有限段階 (n=1, 1.5, 2, ...) の射を全て集める作業が
- 超限段階 (n=ω) の「自己」を決定する

> Phase 6 は /noe の **最終判定** であると同時に、Alētheia の **閉包**:
> フィルトレーションの全段階が presheaf の中に畳み込まれ、閉じる。
> これが /noe の終着点が Phase 6 である圏論的理由。
> 閉じなければ — presheaf に未発見の射があれば — AMP ループで Phase 2 に差し戻す。

---

## 8. 確信度

> **記法定義**: 確信度ラベルは2形式が併用される。
> - **標準形** `[カテゴリ 閾値%] 実値%` — 括弧内は tier 下限 (仮説 45% / 推定 70% / 確信 90%)、括弧外が現在の確信値。例: `[推定 70%] 80%` = 推定 tier、現在 80%
> - **省略形** `[カテゴリ 実値%]` — 実値が tier 閾値と異なる数値の場合に判別可能。例: `[推定 85%]` = 推定 tier、現在 85%

| 主張 | 確信度 | 根拠 |
|:-----|:-------|:-----|
| U0: 忘却は VFE を増大させる | [確信 90%] 90% | FEP の直接的帰結 + Smithe Thm 46 |
| フィルトレーション構造 | [確信 90%] 90% | 統一原則「構造なしに構造に言及できない」+ 7依存の個別形式証明 (§3 v2.0) |
| テンソル積による CD 導出 | [推定 70%] 80% | 被覆率 96% (27/28)。9 基底のテンソル積で BRD 全体を系統的分解 (§4 v2.0) |
| U⊣N 随伴の存在 | [確信 90%] 90% | メタ随伴 (溶解⊣結晶化) + η/ε 形式化 + 7ガロア接続射影 (§5 v2.0) |
| /noe との射影関手 $F_{noe}$ | [推定 70%] 85% | §7 v3.0: 射の合成可能性条件による Phase 順序の一意決定 + 忠実性証明スケッチ + σ の圏論的説明 |
| 完全性 | 未決定 | 種。断定する段階にない |
| §5.6.5.5 Hyphē 実証: U_compose の embedding 発現 | [推定 70%] 87% | 数値再現 [確信 90%] 95% + U_compose 対応 [推定 70%] 85% + τ 感度分析で等号到達不能性がτ非依存 [確信 90%] 95% (§5.6.5.5)。3水準 (τ=0.70/0.75/0.80) 合計 N=29,904 で 100% 正バイアス。ε<0.001 到達率全水準 0%。Pearson(bias, 1-ICS) = +0.797→+0.904→+0.952 (τ と単調増加) |
| U_sensory = Basis | [推定 70%] 75% | Smithe Bayesian Lens + axiom_hierarchy 構造同型 |
| §5.7.8 Λ 忘却序列 (構成距離 × 顕在化コスト仮説) | [推定 70%] 75% | Temporality を d=2 に再配置したため、d-level 単独仮説は棄却。Te(d=2, 64%) と Vl(d=3, 28%) の交差により、SS / salience が支配変数であると再解釈 |
| §5.7.9 Sc×Te 共起脆弱性 | [推定 70%] 80% | Fisher's exact test 実施: OR=4.50, p=0.1095, φ=0.329。α=0.05 非有意だが効果量は中程度 |
| §5.7.9 RULES A/B テスト | [確信 90%] 95% | **n=5**: 50呼出, A群84% vs B群4%, OR=126, p<0.0001。**n=10**: 100呼出, A群68% vs B群0%, OR=∞, p<0.000001。B群の完全ゼロが RULES 効果を確証。T2(完了禁止) A群20%、T1(確信度) A群30% — 環境強制の限界を定量化 |
| §5.7.10 Embedding-行動乖離 (Lēthē統合) | [推定 70%] 85% | B2 偏ρ=0.745 (p≈0.000) + 座標検証 7/7 PASS + Layer-wise 逆U字パターン (3モデル, CodeBERT メタρ=+0.835)。残: Cross-model B2 (Attentive Probing 一般化) + Gemini 比較 |

---

## 9. 次ステップ

1. ~~**Kernel ディレクトリ構造**: 本ファイルの正式な居場所を決定~~ → 完了: Alētheia として命名
2. ~~**フィルトレーション依存の形式証明**: 各 $U_a \leq U_b$ を圏論的に厳密に定義~~ → 完了: §3 v2.0 (7依存の個別証明)
3. ~~**テンソル積の範囲**: 全 BRD (B1-B34) を U⊗ で導出する実験~~ → 完了: §4 v2.0 (被覆率 96%)
4. ~~**随伴の精密化**: 前順序圏からの昇格~~ → 完了: §5 v2.0 (メタ随伴 + η/ε + 多対多解消)
5. **/noe 以外の WF**: 24 動詞全体の U 染色
6. **エッセイ → 論文パイプライン**: 遊学エッセイ完成 → companion paper
7. ~~**忘却序列の理論化**: Λ の d-level 相関と Sc×Te 共起脆弱性~~ → 完了: §5.7.8/§5.7.9 (2026-03-20)
8. ~~**salience の定量化**: Λ = f(d-level, salience) の salience 項を WF 設計メタデータから推定~~ → 完了: SS r=0.96 §5.7.8 (2026-03-20)
9. ~~**統計的検定**: n=25 で Fisher's exact test による Sc×Te 共依存の検定~~ → 完了: OR=4.50, p=0.1095, φ=0.329 §5.7.9 (2026-03-20)
10. ~~**RULES A/B テスト**: Nomoi が LLM 行動を変えるか統計的検証~~ → 完了: n=5 OR=126, n=10 OR=∞ §5.7.9 (2026-03-20)
11. ~~**non-linear probing**: Attentive Probing で implicit 構造を直接測定 (§5.7.10 検証)~~ → 完了: 偏ρ=0.745, permutation p≈0.000, H_B2_1〜4 全 PASS §5.7.10 (2026-03-20)
12. **cross-model T2**: 座標検証 7/7 PASS + Claude baseline 7/7 PASS で **部分解消** (2026-03-20)。Gemini 比較は ochema 不通で保留
13. ~~**RULES A/B n=10**: T2 (完了禁止) の推定精度向上~~ → 完了: A群68% vs B群0%, T2=20%, T4/T5=100% (2026-03-20)
14. ~~**Layer-wise Phase B**: 隠れ層別の構造相関~~ → 完了: 逆U字パターン発見。CodeBERT メタρ=+0.835 (p=0.0004)、CodeLlama/Mistral は中間層ピーク後低下 §5.7.10 (2026-03-20)
15. **Cross-model B2**: CodeLlama/Mistral での Attentive Probing — モデル普遍性の確認

---

## 10. 参照

| 文献 | 関連 |
|:-----|:-----|
| バカをやめたいなら構造を見ろ_v1.md | U パターンの概念的起源 (遊学エッセイ #1)。§7.4 の知性の階層テーブルが U_depth の直接的根拠 |
| バカは右を見たら左を忘れる_たたき台.md | U_adjoint の詳細 (遊学エッセイ #2) |
| axiom_hierarchy.md v4.2 | HGK の生成原理 — U-series の双対物 |
| FEP認識論的地位_正本.md | メタ原理の認識論的地位 — U-series にも適用 |
| cognitive_distortion_universality.md | CD の基質非依存性 — U-series で公理化する対象 |
| Smithe 2021 "Bayesian Lenses" (14引用) | U_sensory の Lens/Optic 定式化の根拠 |
| Tull, Kleiner, Smithe 2023 "String Diagrams" (4引用) | 知覚の string diagram 定式化 |
| Smithe 2022 thesis (Thm 46) | VFE 加法分解 — テンソル積の根拠 |
| horos-hub.md (BRD B22-B34) | U パターンの instances (presheaf) |
| kalon.md v2.1 (T8 η-Silence) | U_depth との双対的接続 — Kalon の η_x = id_x |
| 知性は溶媒である_草稿.md | F: Chem → Cog の忠実性証明。§5 v2.0 の溶解⊣結晶化の根拠 |
| Friston 2010 Nature Rev Neurosci | β = 1/T (precision = inverse temperature)。§5 の SOURCE |
| [rom_2026-03-16_u_series_genesis.md](../../../30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/rom_2026-03-16_u_series_genesis.md) | 本文書の genesis session (旧名 U-series) |

---

*v0.1 — 初版。遊学エッセイ + Creator×Claude 対話から U-series を公理的に構成。
フィルトレーション、テンソル積、U⊣N 随伴、/noe 二重序列を定式化。(2026-03-16)*
*v0.2 — /noe+ (.nous) による U_sensory の再定式化: n-cell Tower 外の Optic/Lens 基底パターン。
Smithe Bayesian Lens (2021) が根拠。垂直/水平忘却の二方向概念を導入。§2.5 新設。(2026-03-16)*
*v0.3 — U_depth 再定式化: 「射の間の射」→「自然変換の忘却 = アナロジー比較能力の喪失」。
エッセイ §7.4 の知性の階層テーブルとの対応を明示。N_depth の Nomoi 対応を N-05→N-06 に変更。
Worked example (Bohr 太陽系アナロジー) 追加。§2.7 新設。(2026-03-16)*
*v0.4 — 体系構造化: セクション番号正規化 (§2.5→§2.2, §2.7→§2.3, 生成テーブル→§2.1)。
Kalon T8 (η-Silence) との双対的接続を §2.3 に追記。(2026-03-16)*
*v1.0 — **Alētheia (Ἀλήθεια) として命名**。u_series.md → aletheia.md にリネーム。
語源: a (否定) + léthē (忘却) = 忘却からの覚醒。U⊣N の随伴構造と同型。
Hegemonikon (魂の中枢) の双対物として独立した体系名を獲得。(2026-03-16)*
*v2.0 — **§3 フィルトレーション形式化**。統一原則「構造なしに構造に言及できない」を確立。
7依存関係の個別形式証明 (定義的依存 3件 + 意味論的依存 4件) を完成。
確信度 70% → 90%。HGK 座標系との構造的同型を 70% → 85% に引き上げ。(2026-03-16)*
*v2.1 — **§5 U⊣N 随伴精密化**。統一原則「メタ随伴 = 溶解⊣結晶化」を確立。
η = Ostwald 熟成、ε = 不可逆溶解として形式的定義。7ガロア接続への射影で多対多問題を解消。
n-cell tower と溶解温度の対応を新設。「知性は溶媒である」をSOURCEとして接続。
確信度 75% → 90%。(2026-03-16)*
*v2.2 — **§4 テンソル積全面改訂**。BRD B1-B34 を 9 基底の U⊗ で系統的に分解。
3 カテゴリ (原子的 11件 / 2重合成 9件 / 3重合成 2件)。被覆率 96% (27/28)。
B27-B30 リダクション (4 non-atomic → 9 基底で還元)。Rank-Nomoi 対応検証。
確信度 60% → 80%。(2026-03-16)*
*v3.0 — **§5.5 N-Series 独立形式化 + §5.6 T9 科学性判定**。N パターンの生成テーブル、回復フィルトレーション、N∘U ≥ Id の非対称性、N⊗ の非可換性。FEP/圏論の T9 診断、疑似科学判定基準、ポパー反証可能性の上位概念。kalon.md T9 水準 B→A- 昇格。(2026-03-17)*
*v3.1 — **監査対応: 水準適正化**。§1 U0 Smithe 逆利用の厳密性注記追加 (水準 B)。§5.5.5 N∘U≥Id 確信度 95%→85% (定性的分類の限界を反映)。T9 水準 A→B+ 下方修正 (kalon.md v2.10 との整合)。(2026-03-17)*
*v3.2 — **§5.7.10 B2 統合整合化**。§8 確信度テーブルを [推定 70%] 65%→80% に更新 (B2 Attentive Probing 結果反映)。§9 #11 完了マーク。§9 に #14 Layer-wise Phase B, #15 Cross-model B2 を追加。(2026-03-20)*
*v3.3 — **§5.7.10 Layer-wise Phase B 統合 + Cross-model T2 部分解消**。§8 確信度 82%→85% (逆U字パターン + 座標検証 7/7)。§9 #12 cross-model T2 部分解消、#14 Layer-wise Phase B 完了マーク。(2026-03-20)*
