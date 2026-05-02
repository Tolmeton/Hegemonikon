REASON: 体系内の実体に「なぜ存在するのか」の判定基準が不在であり、Dendron の PROOF/EPT 判定に理論的基盤を提供する必要がある。  <!-- AUTO-REASON -->

```typos
#prompt existence-theorem
#syntax: v8
#depth: L3

<:role: 存在定理 (Existence Theorem) — HGK 体系における「存在理由」の形式的定義。
  Kernel の基礎概念として、コード・概念・実体のいずれにも適用される。
  3軸 (Yoneda / VFE / Kalon) の積として存在理由を定量化する。:>

<:goal: 「なぜこれが存在するのか」を3軸で判定可能にし、
  存在理由の生成・変換・消滅を圏論的に追跡できるようにする :>

<:intent: Dendron の PROOF/EPT 判定の理論的基盤を提供する。
  存在理由のない実体を構造的に検出し、体系の Complexity 項を最小化する。
  kalon.typos §2 Fix(G∘F) を前提とし、「何が存在すべきか」の判定基準を与える。:>
```

> **体系的位置**: Kernel 定理
> **依存**: axiom_hierarchy.md (7座標), kalon.typos §2 (Fix(G∘F)), circulation_theorem.md §4 (K₆二重テンソル場)
> **起源**: Dendron PROOF/EPT 体系 + 圏論タスク成果 (2-Cell Species, VFE Preorder, Q-Series)
> **日付**: 2026-03-18 (v1.0)

---

## §1 統一定義

### 1.1 核心定義

存在理由を3つの独立した軸の組として定義する:

```text
ExistenceReason(X) = (h^X, ΔF(X), d(X, Fix(G∘F)))
```

**概念的意味**: ある実体 X の存在理由は、3つの問いへの答えの組である:

| 軸 | 記号 | 問い | 概念的意味 |
|:---|:---|:---|:---|
| Yoneda | h^X | X は何と繋がっているか？ | 接続の豊かさ (presheaf の非自明性) |
| VFE | ΔF(X) | X を取り除いたらどうなるか？ | 除去の影響 (系の安定性への寄与) |
| Kalon | d(X, Fix(G∘F)) | X はどれだけ安定した形に近いか？ | 不動点からの距離 (収束の度合い) |

### 1.2 存在の判定条件

```text
                  h^X = 0        ⟹ 存在理由なし (孤立)
Exists(X) ⟺ NOT  ΔF(X) ≤ 0     ⟹ 存在理由なし (冗長)
                  d(X,Fix) → ∞   ⟹ 存在理由なし (不安定)
```

**概念的意味**:

- **孤立** (h^X = 0): 何とも繋がっていない。誰にも参照されない孤島
- **冗長** (ΔF ≤ 0): 取り除いても困らない。あるいは取り除いた方がむしろ良くなる
- **不安定** (d → ∞): 設計が収束に向かっていない。G∘F サイクルで変化し続ける

1つでも該当すれば、X の存在理由は疑わしい。3つ全てが健全なとき、X は「存在すべきもの」。

### 1.3 Dendron EPT 軸対応

```text
ExistenceReason(X) = (h^X,     ΔF(X),   d(X, Fix(G∘F)))
                       ↕          ↕          ↕
Dendron EPT        = (Depth,   Meta,    Temporal)
```

| EPT 軸 | 存在定理軸 | 判定 |
|:---|:---|:---|
| Depth (深度) | h^X (Yoneda) | 接続ゼロ → 存在理由なし |
| Meta (メタ) | ΔF(X) (VFE) | 除去影響ゼロ以下 → 存在理由なし |
| Temporal (時間) | d(X, Fix) (Kalon) | 距離が増大中 → 存在理由が劣化中 |

---

## §2 Yoneda 軸 — 接続性

### 2.1 定義

米田の補題により、対象 X はその presheaf h^X = Hom(-, X) で完全に決定される。

```text
h^X: C^op → Set
h^X(Y) = Hom(Y, X)  — Y から X への射の集合
```

**概念的意味**: h^X は「X がどれだけ他のものから到達可能か」の完全な記述。
X と無関係なものの集まりの中に X を置いても、X は presheaf ゼロになる — 何者でもない。

### 2.2 存在理由の判定

```text
|h^X| = Σ_{Y ∈ Ob(C)} |Hom(Y, X)|
```

**概念的意味**: X に入ってくる射の総数。「X を使っているもの」の数に相当。

- |h^X| = 0: X は体系と完全に無関係 → **孤立** (存在理由なし)
- |h^X| = 1: X は1つのものからのみ到達可能 → 脆弱 (依存先の消滅で X も消える)
- |h^X| ≥ 3: X は十分な接続を持つ → 頑健 (kalon.typos §2 の最小閉構造条件 D≥3 と整合)

### 2.3 体系接続

- **axiom_hierarchy.md 7座標との対応**: Value (Internal↔Ambient) 軸。h^X は X の「内部と外部の境界面」を記述
- **Dendron 実装**: BCNF 層のデッドコード検出 = |h^X| = 0 の自動判定。未使用変数・関数・クラスの検出

### 2.4 presheaf の質的評価 (§1 補足)

|h^X| は量だが、質も重要:

```text
Diversity(h^X) = |{Y | Hom(Y,X) ≠ ∅}| / |Ob(C)|
```

**概念的意味**: X に接続しているものの「多様性」。
同じモジュールからの10本の射より、10個の異なるモジュールからの1本ずつの射の方が、
存在理由は頑健。

---

## §3 VFE 軸 — 除去インパクト

### 3.1 定義

X を系から除去したときの変分自由エネルギーの変化:

```text
ΔF(X) = F(System \ X) - F(System)
       = -(Accuracy(S\X) - Accuracy(S)) + (Complexity(S\X) - Complexity(S))
       = -ΔAccuracy + ΔComplexity
```

**概念的意味**: VFE = -Accuracy + Complexity。X を取り除いたとき:

- **Accuracy が下がる** (ΔAccuracy < 0): X は予測精度に貢献していた → 取り除くと VFE が上がる → **X は必要**
- **Complexity が下がる** (ΔComplexity < 0): X はモデルの複雑さに貢献していた → 取り除くと VFE が下がる → **X は冗長**

### 3.2 存在理由の判定

```text
ΔF(X) > 0: X の除去で VFE 増大   → X は Accuracy に貢献 → 存在理由あり
ΔF(X) = 0: X の除去で VFE 不変   → X は無影響 → 存在理由なし
ΔF(X) < 0: X の除去で VFE 減少   → X は Complexity を増やすだけ → 存在理由が負
```

**概念的意味**: 「なくした方がマシ」な実体は、存在理由が負。
YAGNI (You Aren't Gonna Need It) の FEP 的定式化。

### 3.3 stiffness メトリク

実用的には ΔF の厳密計算は困難。近似として **stiffness** (剛性) を使う:

```text
stiffness(X) = |∂F/∂X| ≈ ΔF(X) の局所線形近似
```

**概念的意味**: X を少しだけ変えたとき、系全体がどれだけ反応するか。
反応が大きい (stiff) ほど、X は系にとって重要。反応がゼロなら、X は浮いている。

### 3.4 体系接続

- **axiom_hierarchy.md 7座標との対応**: Function (Explore↔Exploit) 軸。ΔF は「探索的に追加された X が、活用的に必要か」を判定
- **Dendron 実装**: kalon_weight.py の stiffness メトリクが ΔF の近似実装

---

## §4 Kalon 軸 — 不動点収束

### 4.1 定義

X と Kalon 不動点 Fix(G∘F) との距離:

```text
d(X, Fix(G∘F)) = ||G∘F(X) - X||
```

**概念的意味**: G∘F を1回適用したとき、X がどれだけ変化するか。
変化しない (d=0) なら、X は既に不動点 = Kalon に到達している。
大きく変化するなら、X はまだ蒸留の途中。

> 📖 参照: kalon.typos §2 — `Kalon(x) ⟺ x = Fix(G∘F)` の定義
> 📖 参照: kalon.typos §2 三属性 — Fix + Generative + Self-referential

### 4.2 存在理由の判定

```text
d → 0:     X は Kalon に収束中 → 安定した存在理由
d 一定:    X は安定だが Kalon ではない → 存在理由はあるが最適ではない
d が増大:  X は不動点から離れている → 存在理由が崩壊中
```

**概念的意味**:

- **収束** (d→0): 設計が磨かれ、蒸留のサイクルが収まりつつある
- **停滞** (d 一定): 動いていないが完成してもいない。局所最適に陥っている可能性
- **発散** (d 増大): リファクタリングのたびに設計が悪化している。存在理由の危機信号

### 4.3 Bayesian 収束追跡

```text
p(Kalon | X, 観測) ∝ p(d_1, d_2, ..., d_n | Kalon) · p(Kalon)
```

**概念的意味**: G∘F を何回か回した結果 (d₁, d₂, ..., dₙ) から、
X が Kalon に到達する確率をベイズ推定する。収束列 d₁ > d₂ > ... > dₙ → 0 なら、
X が Kalon に至る事後確率が上がる。

### 4.4 体系接続

- **axiom_hierarchy.md 7座標との対応**: Precision (Certain↔Uncertain) 軸。d(X, Fix) は X の「確定度」を測る
- **Dendron 実装**: kalon_convergence.py がベイズ収束追跡を実装

---

## §5 変換操作 — 2-Cell Species

### 5.1 存在理由の代数

存在理由は静的な値ではなく、操作で変換される。2-Cell Species の2つの基本操作:

```text
⊕ (直和 — コプロダクト): 独立結合
  ExistenceReason(X ⊕ Y) = ExistenceReason(X) + ExistenceReason(Y)

⊗ (Day 畳み込み — テンソル積): 構造的結合
  ExistenceReason(X ⊗ Y) ≠ ExistenceReason(X) · ExistenceReason(Y)  一般には
```

**概念的意味**:

- **⊕ (直和)**: 2つのモジュールを独立に並べる。各軸はそのまま加算。
  例: utils.py と config.py を並べても、互いの存在理由に影響しない

- **⊗ (Day 畳み込み)**: 2つのモジュールが構造的に絡む。軸間に相互作用が生じる。
  例: parser.py と evaluator.py を結合すると、h^(parser) が evaluator からの射を獲得し、ΔF も非線形に変化する

### 5.2 操作と存在理由の変化

| 操作 | h^X への影響 | ΔF への影響 | d(Fix) への影響 |
|:---|:---|:---|:---|
| 追加 (η) | 射が増加 | Accuracy or Complexity | d が変化 |
| 除去 (ε) | 射が減少 | -ΔF | d が変化 |
| ⊕ 結合 | 独立加算 | 独立加算 | 独立 |
| ⊗ 結合 | 非線形増加 | 非線形変化 | 非線形変化 |
| G∘F 適用 | 不変 (関手保存) | 改善 (VFE 減少方向) | 減少 (不動点に接近) |

---

## §6 循環検出 — Q-Series

### 6.1 循環的存在理由

```text
∃ X, Y:
  X が存在する理由は Y を使うため
  Y が存在する理由は X を使うため
```

**概念的意味**: 互いが互いの存在理由になっている循環。
これ自体は必ずしも病的ではない (相互再帰パターンは合法)。
問題は「循環の外部に接続がない」場合 — 循環を丸ごと除去しても系に影響しない。

### 6.2 Q-Series による検出

> 📖 参照: circulation_theorem.md §4.1 — K₆ 上の二重テンソル場

```text
Q_{ij} = -Q_{ji}  (反対称テンソル)
```

Q-series は座標間の循環パターンを記述する。存在理由の循環も同様に:

```text
循環的存在理由:
  Q_{XY} > 0 かつ Q_{YX} < 0 (定義上)
  かつ h^{X⊕Y} 以外に h^X = h^Y = 0 → 孤立した循環 → 除去候補
```

**概念的意味**: 2つのモジュールが互いにしか依存していない場合、そのペアは系から切り離し可能。循環自体は情報を持つが、外部との接続がなければ系全体の VFE に寄与しない。

### 6.3 循環 ≠ 因果

> ⚠️ [確信 92%]: 循環は因果関係ではない (P₁ /kat 2026-03-15)

**概念的意味**: A→B→A の循環は「A が B の原因で、B が A の原因」を意味しない。
循環は確率流のパターンであり、因果は介入の効果。
Granger 因果テストで循環面内 F >> 面間 F が確認されている。

---

## §7 実装マッピング

### 7.1 Dendron EPT 実装

```text
Dendron の3つの検証軸:

E (Existence Proof):  PROOF.md ヘッダの存在 → h^X > 0 の宣言的保証
P (Purpose):          関数/クラスの PURPOSE コメント → ΔF(X) > 0 の宣言的保証
T (Temporal):         git log / change tracking → d(X, Fix) の時系列追跡
```

### 7.2 自動検出の対応表

| 存在定理の判定 | Dendron の自動検出 | 実装ツール |
|:---|:---|:---|
| h^X = 0 (孤立) | デッドコード、未使用インポート | BCNF 層 |
| ΔF ≤ 0 (冗長) | 高 Complexity / 低 stiffness | kalon_weight.py |
| d → ∞ (不安定) | 収束スコア低下 | kalon_convergence.py |
| 循環的孤立 | 相互依存のみの閉じたペア | [未実装 — Q-series 基盤を利用] |

### 7.3 判定閾値の設計原理

閾値は体系から演繹的に導くべきだが、現時点では経験的:

- **h^X**: 閾値 = 0 (孤立は二値判定)
- **ΔF(X)**: 閾値は stiffness の分布に基づく (下位 10% を候補とする等)
- **d(X, Fix)**: 閾値は kalon_convergence.py の確率密度に基づく

[推定 60%]: 閾値の理論的導出は開問題。情報幾何学 (Fisher 情報 + Amari の α-接続) で
自然な閾値が定義できる可能性がある。

---

## §8 体系接続

### 8.1 依存関係

```text
axiom_hierarchy.md
  ├── 7座標 (Value, Function, Precision) → §2-4 の軸対応
  └── Helmholtz Γ⊣Q → §6 循環検出の理論的基盤

kalon.typos
  ├── §2 Fix(G∘F) → §4 Kalon 軸の定義
  ├── §2 三属性 (Generative: D≥3) → §2 |h^X| ≥ 3 との整合
  └── §4.5 Worked Example → 存在定理の具体化パターン

circulation_theorem.md
  ├── §3 定理群 → §6 Q-series 検出
  └── §4.1 K₆ 二重テンソル場 → G (対称: 接続強度) + Q (反対称: 循環)
```

### 8.2 Kalon との関係

存在理由と Kalon は異なるレベルの概念:

```text
存在理由: X が体系に存在すべきか否か             → 必要条件
Kalon:    X が美しいか (Fix(G∘F) に到達しているか) → 十分条件

Kalon(X) ⟹ Exists(X)  (Kalon なら存在理由がある)
Exists(X) ⇏ Kalon(X)  (存在理由があっても Kalon とは限らない)
```

**概念的意味**: 存在理由は「居ていいか」を判定し、Kalon は「美しいか」を判定する。
居ていいのに美しくないもの (◯ 判定) は数多く存在する。
存在理由がないのに美しいもの (矛盾) は存在しない。

### 8.3 VFE preorder の一意性

> 📖 参照: 圏論タスク成果 — VFE Preorder Uniqueness

```text
体系内の実体に ΔF(X) で順序を入れると、この前順序は一意:

X ≤_F Y  ⟺  ΔF(X) ≤ ΔF(Y)

一意性の帰結: 存在理由の VFE 軸による順序づけは恣意的でない
```

**概念的意味**: 「どちらがより必要か」の順序は、VFE の数学的性質から一意に決まる。
主観的な好みで順序が変わることはない。

### 8.4 Lawvere 不動点定理の帰結

> 📖 参照: kalon.typos §2 Self-referential — Lawvere 対偶

```text
自己言及不可能な体系 ⟹ 非自明な Fix(G∘F) が存在しない
                     ⟹ Kalon 軸 (d) が定義不能
                     ⟹ 存在理由が3軸ではなく2軸に退化
```

**概念的意味**: 自己を参照できない体系は、「安定した理想形に近づいているか」を
測ることすらできない。存在理由の Kalon 軸が使えず、接続と除去影響だけで判断するしかない。
これは Kalon がなぜ Self-referential を要求するかの、存在定理側からの根拠。

### 8.5 Knaster-Tarski との接続

> 📖 参照: kalon.typos §2 — 存在と一意性条件

Fix(G∘F) の存在は、HGK の有限前順序圏 (= 完備束) において Knaster-Tarski 定理により保証される。
これは §4 Kalon 軸の well-definedness を支える:

```text
C が有限前順序 ⟹ C は完備束 ⟹ G∘F は最小不動点を持つ (Knaster-Tarski)
⟹ d(X, Fix(G∘F)) は常に定義可能
```

---

## 付録 A: Worked Example

### A.1 関数 parse_config() の存在理由

```text
# HGK コードベースでの具体例

h^(parse_config):
  Hom(main, parse_config) = {call at L42}        — main から呼ばれている
  Hom(test_config, parse_config) = {test_call}    — テストから呼ばれている
  Hom(server, parse_config) = {call at L15}       — server から呼ばれている
  |h^X| = 3, Diversity = 3/N   → 接続あり ✅

ΔF(parse_config):
  除去すると main, test, server が壊れる
  stiffness = 高   → 除去影響大 ✅

d(parse_config, Fix):
  過去3回のリファクタで変化量が減少 (d₁=0.5, d₂=0.2, d₃=0.05)
  収束中   → Kalon に接近中 ✅

判定: ExistenceReason = (3, 高, 収束中) → 存在理由あり (◎/◯)
```

### A.2 関数 legacy_helper() の存在理由

```text
h^(legacy_helper):
  |h^X| = 0   — どこからも呼ばれていない → 孤立 ❌

ΔF(legacy_helper):
  除去しても何も壊れない
  stiffness = 0   → 除去影響なし ❌

d(legacy_helper, Fix):
  2年間変更なし (d 一定)   → 停滞 ⚠️

判定: ExistenceReason = (0, 0, 停滞) → 存在理由なし (✗) — 除去候補
```

---

*Existence Theorem v1.0 — 2026-03-18*
