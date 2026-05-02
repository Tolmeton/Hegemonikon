# B: Polynomial Functors による Linkage の定式化

> **PJ-07 サブタスク B** (2026-03-11)
> **目的**: Spivak の polynomial functor で Euporía|_{Linkage} を定式化する

---

## §1 Polynomial Functor の定義

> 📖 参照: Niu & Spivak (2023) arXiv:2312.00990, Cambridge UP (2025)

### 基本定義

Polynomial functor `p: Set → Set` は以下の形:

```
p(y) = Σ_{i ∈ I} y^{B_i}
```

- **I** = positions (位置の集合) — 系が取りうる「状態」
- **B_i** = directions at position i — 位置 i からの「行為の集合」
- **y^{B_i}** = B_i → y — 各行為に対する「次の入力」の割当て

### 直感的意味

**p は「インターフェース」を表す**:
- 位置 i にいるとき、系は B_i 個の行為を選択できる
- 各行為 b ∈ B_i に対して、環境から y 型の応答が返る

**例**: チャット AI のインターフェース
- I = {待機, 応答中} (2つの位置)
- B_{待機} = {受信} (1つの行為)
- B_{応答中} = {返答, 質問, 保留} (3つの行為)
- → p(y) = y^1 + y^3 = y + y³

### 射 (Lens)

Poly の射 `(f, f♯): p → q` は:
- f: I_p → I_q (forward: 位置の写像)
- f♯_i: B_{f(i)}^q → B_i^p (backward: 方向の引き戻し)

**なぜ forward + backward か**: 
位置は「見せる情報」(output)、方向は「受け取る情報」(input)。
output は同じ方向に流れ、input は逆方向に流れる — これは光学 (optics) の構造。

---

## §2 AY との対応

### 核心的対応

| Polynomial Functor | Euporía (AY) | 対応 |
|:-------------------|:-------------|:-----|
| p(y) = Σ y^{B_i} | 操作前の状態 | 行為可能性の集合 = B_i |
| q(y) = Σ y^{C_j} | 操作後の状態 | 行為可能性の集合 = C_j |
| |B_i| | 操作前に可能な行為の数 | |Hom(before, −)| |
| |C_{f(i)}| | 操作後に可能な行為の数 | |Hom(after, −)| |

### AY の polynomial functor 的定式化

```
認知操作 f: WF を射 (f, f♯): p → q と見なす。

AY(f, i) = |B_{f(i)}^q| - |B_i^p|    (位置 i における方向数の変化)
```

### §2.1 Euporía-lens [R1 修正]

> ⚠️ `/ele` 反駁 R1 の修正: Poly の射 (lens) は方向数の大小を保証しない。
> AY > 0 は lens の性質ではなく、**Euporía が lens に課す追加条件**。

Poly の射 `(f, f♯): p → q` において:
- `f♯_i: B_{f(i)}^q → B_i^p` は backward map (方向の引き戻し)
- `f♯` は全射でも単射でもない → 方向数の増減は保証されない

**定義 (Euporía-lens)**:
```
Euporía-lens := {(f, f♯): p → q ∈ Poly | ∃i ∈ I_p: |B_{f(i)}^q| > |B_i^p|}

つまり: 少なくとも1つの位置で方向数を増やす lens のクラス

AY(f) = Σ_i max(0, |B_{f(i)}^q| - |B_i^p|) > 0

強い条件 (全位置):
  Strong-Euporía: ∀i ∈ I_p: |B_{f(i)}^q| ≥ |B_i^p|
```

**設計的意義**: 全ての lens が Euporía を満たすのではない。
FEP は全ての行為を説明するが、**良い認知操作**を選ぶのが Euporía。
Euporía-lens は Poly の部分圏 (subcategory) を構成する。

### [DISCOVERY] Monomial と AY の同型

**Monomial** y^B (1つの position, B 個の direction) は
「B 個の行為が可能な状態」を表す。

```
チャンク c の状態 = monomial y^{B_c}
  B_c = c から到達可能な行為の集合

索引操作 index: Chunks → Linked_Chunks は
  射 (id, f♯): y^{B_c} → y^{B_{linked(c)}}
  where |B_{linked(c)}| > |B_c|

AY(index) = |B_{linked(c)}| - |B_c| > 0
```

**これは Creator の定義「索引 = チャンクの Markov blanket を構成する行為」の
polynomial functor 的再定式化である。**

---

## §3 Linkage の定式化

### §3.1 チャンクの MB を polynomial functor で表現 [R2 修正]

> ⚠️ `/ele` 反駁 R2 の修正: MB の全要素を行為可能性とするのは不正。
> FEP の MB は {μ, s, a, η} に分割され、行為可能性 = active states (a) のみ。
> 📖 参照: constructive_cognition.md L40-43

```
FEP における Markov blanket の4変数:
  μ = internal states   (内部モデル — チャンクの「内容」)
  s = sensory states    (受動入力 — 他チャンクから c への参照)
  a = active states     (能動出力 — c から他チャンクへの参照)
  η = external states   (環境 — MB の外)

制御可能 (τὰ ἐφ᾿ ἡμῖν):   μ + a
制御不能 (τὰ οὐκ ἐφ᾿ ἡμῖν): s + η
```

**行為可能性 = active states のみ**:
```
チャンク c の行為可能性:
  Act(c) = a(c) = {c から他チャンクへの参照 (出力方向)}
  Sens(c) = s(c) = {他チャンクから c への参照 (入力方向)}

Polynomial functor として:
  p_c(y) = y^{|Act(c)|}    ← active のみが方向数

  (旧) y^{|MB(c)|} は sensory を過剰カウントしていた
  (新) y^{|Act(c)|} が正確な行為可能性の表現
```

> **注**: sensory states は「環境が c に作用する方向」であり、
> c 自身が選択できる行為ではない。直感的には:
> - Act(c) = c が出せるリンクの数 (能動)
> - Sens(c) = c に届くリンクの数 (受動)
>
> AY は Act(c) の変化のみを追跡する。

### §3.2 索引操作の定式化 [R2 修正適用]

```
索引操作 Idx: Chunk_System → Chunk_System

Before: p = Π_{c ∈ C} y^{|Act_0(c)|}   (索引前の能動方向数)
After:  q = Π_{c ∈ C} y^{|Act_1(c)|}   (索引後の能動方向数)

AY(Idx) = Σ_{c ∈ C} (|Act_1(c)| - |Act_0(c)|)

Euporía 条件 (§2.1):
  AY(Idx) > 0 ⟺ ∃c ∈ C: |Act_1(c)| > |Act_0(c)|
  つまり: 索引により少なくとも1つのチャンクの能動方向数が増えた
```

### §3.3 sensory 増加の意味

Sens(c) の増加も意味はある — チャンク c がより多くの文脈から参照される。
しかしこれは c の「行為可能性」ではなく「到達可能性」(reachability):

```
Reach(c) = |Sens(c)|   ← c がどれだけ「見つけやすいか」
Afford(c) = |Act(c)|    ← c からどれだけ「進めるか」

AY はAfford の変化を追跡する。
Reach は品質指標としては有用だが、Euporía の定義からは外れる。
```

### [DISCOVERY v2] 索引 = Active 方向の拡張操作

**定理 (Linkage-AY 同値, R2 修正版)**:

```
Idx が Euporía を満たす (AY(Idx) > 0)
  ⟺ ∃c ∈ C: |Act_1(c)| > |Act_0(c)|
  ⟺ 索引操作が少なくとも1つのチャンクの能動方向数を拡張する
  ⟺ Idx は Euporía-lens (§2.1)
```

### Kalon の条件 (Fix(G∘F) 到達)

```
G∘F サイクル:
  F (発散): チャンク c の能動方向の候補を列挙 (Act の拡張候補)
  G (収束): 最も有効な方向のみを保持 (Act の刈り込み)

Fix(G∘F):
  「これ以上 Act を拡張しても刈り込まれ、刈り込んでも拡張される」不動点
  = チャンクの最適 active 方向数
  = 索引の Kalon 状態
```

---

## §4 3ドメインへの横展開

| ドメイン | Polynomial Functor | 位置 I | 方向 B_i (= Act) | AY |
|:---------|:-------------------|:-------|:------------------|:---|
| Cognition | WF の入出力 | WF 状態 | 次に取れる認知操作 | |Act_after| - |Act_before| |
| Description | プロンプト構造 | 記述状態 | 読み手が取れる行動 | |Act_structured| - |Act_raw| |
| Linkage | チャンク連結 | チャンク | c から他チャンクへの参照 | |Act_after| - |Act_before| |

**全ドメイン共通**: 方向 = **active states のみ** (sensory は除外)。
Euporía-lens (§2.1) が全ドメインに適用される統一条件。

---

## §4.1 Π vs Σ と AY の加法性 [R3/R4 解決] {#sec_41_additivity}

> ⚠️ `/ele` 反駁 R3 (Π/Σ混用) と R4 (AY加法性) の解決。
> 📖 参照: Niu & Spivak (2023) §2.2 Products of polynomials

### R3: なぜ Π (product) を使うか

§1 で polynomial functor は `p(y) = Σ_{i} y^{B_i}` (直和) と定義した。
チャンクシステムは各チャンクが独立に状態を持つので **product** を使う:

```
単一チャンク: p_c(y) = y^{|Act(c)|}         (monomial = 1つの位置)
チャンクシステム: P(y) = Π_{c ∈ C} p_c(y)    (product in Poly)
```

Poly の圏における product `Π p_c` の構造:
```
位置:  I_P = Π_{c ∈ C} I_c = Π_{c} {*} = {*}  (各 p_c は monomial → 位置1つ)
方向:  B_P = ⊔_{c ∈ C} B_c = ⊔_{c} Act(c)     (方向は coproduct = 直和)
```

> **[FACT]** Poly における product の方向は **coproduct** (直和) になる。
> これは Poly が圏として持つ構造的性質であり、仮定ではない。

### R4: 加法性の導出

Product の方向が coproduct であることから:

```
|B_P| = |⊔_{c} Act(c)| = Σ_{c} |Act(c)|

したがって:
  AY(Idx) = |B_{P_1}| - |B_{P_0}|
           = Σ_{c} |Act_1(c)| - Σ_{c} |Act_0(c)|
           = Σ_{c} (|Act_1(c)| - |Act_0(c)|)
```

> **[DISCOVERY]** AY の加法性は Poly の product 構造から**自動的に導出**される。
> 追加の公理や仮定は不要。R4 は Poly の圏の性質として解消される。

### 直感的理解

チャンクシステムの「合計行為可能性」= 各チャンクの行為可能性の合計。
これは独立なチャンクの product が方向を coproduct として合成するから。

ただし:
- チャンク間に**依存関係**がある場合 (例: c₁ の act が c₂ の sens に直結)、
  product ではなく **composition** (`◁`, dependent lens) が適切な場合もある
- この場合 AY の加法性は崩れうる → 将来の検討事項

---

## §5 未解決

1. **p-coalgebra としての動的モデル**: 索引操作の時間発展 (S → p(S)) はどう表現されるか？
2. ~~**Poly のモノイダル構造**~~: → R3/R4 で解決 (§4.1)。残る問題は dependent composition (◁) のケース
3. **Hóros の位置**: 制約は polynomial functor の「quotient」(商) として表現可能か？
   - 制約 = 方向の制限 → B_i の部分集合 → p のサブファンクター
   - これなら Hóros はドメインではなく、polynomial functor への制約条件
4. **Kalon-Poly 接続** (R5): Fix(G∘F) を Poly の終余代数 or Lambek 不動点と接続
5. **依存チャンク**: composition (◁) での AY — 加法性は崩れるか？

---

*PJ-07B v0.3 — R1 + R2 + R3/R4 修正 | 2026-03-11 | [仮説] 段階*
