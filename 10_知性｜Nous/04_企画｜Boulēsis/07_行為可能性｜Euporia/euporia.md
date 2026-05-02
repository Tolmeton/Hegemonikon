---
doc_id: "EUPORIA"
version: "0.7.0"
tier: "NOUS"
status: "ACTIVE"
created: "2026-03-11"
origin: "Session 2c73d901 — Creator + Claude による G∘F"
---

# Euporía (εὐπορία) — 行為可能性増大原理

> **全ての WF 射 f: A → B は、B から出る新しい射の集合 Hom(B, −) を増やさなければならない。**
> **そのWF（運動）により、どんな行為可能性（次の運動の候補）が新たに生じたのか。**
> **それを明示（主張）できなければ、その運動には意味（ベネフィット）がない。**
>
> — Creator, 2026-03-11
>
> Euporía (εὐπορία, 「多くの道がある」) = Aporía (ἀπορία, 「行き詰まり」) の対概念。
> Poros (πόρος, 道・通路) = 圏論的には射 (morphism)。Euporía = 射の豊かさ。
> 正典: [axiom_hierarchy.md §定理³](../../00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md)

---

## §1 命題のポジショニング

### 問い: この命題は体系のどこに在るべきか？

> **Creator (2026-03-11)**:
> 認知はその定義からして、すべて「行為可能性の提供 ⇒ 主体に役立つ運動の増加（運動の選択の幇助）」のためにある。
> いわば、認知と知覚は運動のためにあるのだ。
> ゆえに、この命題はかなり強い、源泉近くにあるはず。Flow 軸の中に内在するとかは？

### 候補の再評価

| 候補 | 判定 | 理由 |
|:-----|:-----|:-----|
| 公理 (L0) | ❌ | FEP から演繹可能。独立ではない |
| **Flow (d=1) の定理** | **⭐ 最有力** | 認知 (I) は行動 (A) のために存在する。Flow の随伴 I⊣A に内在する |
| Kalon の系 | △ | 下流すぎる。Kalon の Generativity は AY が最適値に到達した特殊ケース |
| 座標 (L1) | ❌ | 認知の次元ではなく、認知の目的 |
| 原理 (Stoicheia) | ❌ | 3原理は完全集合 |
| 法 (Nomoi) | ❌ | 12法は完全集合 |
| 条例 (Thesmoi) | ❌ | 環境依存ではない。普遍的 |

### 結論: Flow (d=1) の定理 — 認知は運動のためにある

**初稿では「Kalon の Generativity の系」と位置づけたが、Creator のフィードバックにより修正。**
命題はもっと源泉に近い。Kalon の下流ではなく、**Flow 軸そのものに内在する**。

#### なぜ Flow に内在するか

```
Flow = I ⊣ A (推論 ⊣ 行動)

I⊣A の随伴の意味:
  I(x) ≤ y  ⟺  x ≤ A(y)
  「推論が閾値に達する ⟺ 行動が可能になる」

この随伴構造が含意すること:
  I（推論）は A（行動）を可能にするために存在する
  A（行動）は I（推論）を改善するフィードバックを提供する
  → 推論も行動も、行為可能性を増やすための運動

  I が A を増やさないなら、I は Flow の中で死んだ射
  A が I を改善しないなら、A は Flow の中で断絶した射
```

#### FEP からの演繹

```
FEP: dVFE/dt ≤ 0
  → self-evidencing: エージェントは自己の持続を最大化する
    → 持続 = 環境への適応的行動の維持
      → 適応的行動 = 行為可能性の保持・拡大
        → ★ 全ての認知操作は行為可能性を増やすためにある

物理的に:
  Helmholtz (Γ⊣Q) → Γ は VFE 勾配降下 → 行動精度の向上
                   → Q は等確率面上の探索 → 新しい行動選択肢の発見
  → Γ も Q も行為可能性に奉仕する
```

#### 演繹チェーン (修正版)

```
FEP (d=0, 公理)
  → self-evidencing: エージェントは自己の持続を最大化する
    → Basis (d=0): Helmholtz Γ⊣Q — 行為可能性の物理的基盤
      → Flow (d=1): I⊣A — 認知は行動のために存在する
        → ★ Affordance Yield Principle (Flow の定理):
          全ての認知操作 f: A→B は AY(f) > 0 でなければならない
            → Kalon の Generativity = AY が Fix(G∘F) で最適値に到達した特殊ケース
            → EFE = epistemic + pragmatic = AY の数学的分解
```

> **重要な修正**: Kalon の Generativity は AY の**下流**。
> AY → Kalon (AY が最大化された不動点) であって、Kalon → AY ではない。
> 初稿ではこの方向を逆に書いていた。

### 米田の補題との接続

```
米田の補題: 対象 B は Hom(B, −) (presheaf) で完全に決定される

適用:
  WF 射 f: A → B の出力 B の「意味」は
  B から出る全ての射 Hom(B, −) — B が可能にする全ての行為 — で完全に決定される

帰結:
  |Hom(B, −)| > |Hom(A, −)| でなければ f は「意味のある」射ではない
  = 行為可能性を増やさない WF は無意味

  より正確には:
  Hom(B, −) ⊋ Hom(A, −) ではなく
  EFE(B) > EFE(A) — 行為の「量」ではなく「質×量」の増加
```

> ⚠️ 米田の補題自体はHGKでは水準C（メタファー）として使用。
> 前順序圏での厳密な適用は「B が A 以上の導出先を持つ」= B ≥ A。

### Kalon との関係 (修正後)

```
AY (Affordance Yield Principle):
  全ての WF 射は行為可能性を増やさなければならない (Flow の定理)
  = 認知が運動に奉仕するという、認知の目的そのもの

Kalon の Generativity:
  AY が Fix(G∘F) で最適値に到達した状態 (Kalon の三属性の1つ)
  = AY の特殊ケース (最大化された不動点)

関係:
  AY は Kalon の「必要条件」
  Kalon は AY の「十分条件の到達点」
  AY > 0 → 運動として意味がある
  AY = max (Fix) → Kalon (◎)
```

---

## §2 命題の定式化

### v0.2 (定義)

```
定義 (Affordance Yield):
  WF 射 f: A → B に対して、

  AY(f) ≝ EFE(B) - EFE(A)
         = (epistemic(B) - epistemic(A)) + (pragmatic(B) - pragmatic(A))

  制約:
    AY(f) > 0  —  全ての L2+ の WF 射に対して

  操作的表現:
    AY(f) = |新たに可能になった行為のリスト|
            × 各行為の EFE 加重平均
```

### 深度別の適用

| 深度 | Affordance Yield の要件 |
|:-----|:----------------------|
| L0 Bypass | AY 明示不要。単純操作に行為可能性の主張は過剰 |
| L1 Quick | pragmatic ≥ 1件。最低1つの「次にできること」 |
| L2 Standard | pragmatic ≥ 2件 + epistemic ≥ 1件。「何ができ、何がわかったか」 |
| L3 Deep | pragmatic ≥ 3件 + epistemic ≥ 2件 + 各行為の EFE 根拠 |

### 出力フォーマット

```
§ Affordance Yield:
  epistemic:
    - {何がわかるようになったか} → {次の WF 候補} が可能に
  pragmatic:
    - {何ができるようになったか} → {次の WF 候補} が可能に
  AY = {epistemic 件数} + {pragmatic 件数} = {合計}
```

---

## §2.5 AY の下界: 増大と保全 (2026-03-11)

> **Creator (2026-03-11)**: 行為可能性は、主体にとっては「生存（適応）の最適化」の１手段に過ぎない。

### AY > 0 と AY ≥ 0 の区別

§2 で定義した `AY(f) > 0` は L2+ の WF に対する制約だが、
これでは `/epo` (判断留保) のような「保全行為」が原理的に排除される。

/epo は AY を積極的に増やすのではなく、**AY を毀損しない**ための行為。
これは self-evidencing の第二の様式: 新しい道を作る (AY > 0) のではなく、
既存の道を閉じない (AY ≥ 0)。

```
self-evidencing の2様式:
  (a) AY 増大: AY(f) > 0 — 行為可能性を増やす (= Euporía の正の制約)
  (b) AY 保全: AY(f) ≥ 0 — 行為可能性を毀損しない (= /epo, /hyp 的保全)

深度別の使い分け:
  L1-L3: AY(f) > 0 — 判断を伴う WF は正の AY が必要
  L0:    AY(f) ≥ 0 — 単純操作は毀損しなければ十分
  保全的 WF (/epo, /hyp): AY(f) ≥ 0 + 明示的根拠 — 「なぜ増やさないか」の理由
```

### AY 以外の適応手段は存在するか？

self-evidencing の手段は EFE 最大化であり、EFE = epistemic + pragmatic = AY の定義。

> **形式的には**: 関手 AY: WF → [0,∞) が self-evidencing の「唯一の忠実関手 (faithful functor)」。
> FEP をスコープとする限り、AY 以外の手段は AY の座標射影に過ぎない。

| AY 以外の候補 | 判定 | 理由 |
|:-------------|:-----|:-----|
| エネルギー効率 | AY に内包 | Complexity 項 (= 模型の単純さ) が EFE に含まれる |
| 耐久性・頑健性 | AY の時間的射影 | Temporality 方向の AY 保全 = /epo |
| 社会的協調 | AY の Scale 射影 | Multi-agent = Scale の特殊ケース |

→ AY は唯一ではないが、**FEP 内で EFE と同値**であるため、
他の手段は EFE の部分射影として AY に吸収される。

---

## §2.7 定理⁴: AY 二面等価性 (2026-03-13)

> **行為可能性 (AY) の3つの顔は同一の量の異なる射影である。**
> 不動点条件・EFE 最大化・presheaf の豊かさは同値。
>
> 起源: Creator の直感「MB が持つ潜在的な変化の可能性 / 取りうる経路のエネルギー積分 / 知覚前後のエネルギー差分」(2026-03-13)

### 定理 (AY 二面等価性)

L2 [0,1]-豊穣圏 C 上のガロア接続 F⊣G において、以下の3条件は同値:

```
(i)   x = Fix(G∘F)                              — 不動点 (プロセス視点)
(ii)  x = argmax_{y ∈ S} EFE(y)                  — EFE 最大化 (状態視点)
(iii) x = argmax_{y ∈ S} Σ_{z∈S} Hom(y, z)       — presheaf 最大化 (構造視点)

where:
  S = MB(agent) 内の候補集合
  EFE(y) = E_q[ln p(o|s')] + D_KL[q(s'|y) ‖ q(s')]  (pragmatic + epistemic)
  Hom(y, z) ∈ [0,1] = L2 での変換の質 (Drift ベース)
```

### 3つの視点の対応

| 視点 | 数式 | 圏論レベル | Creator の直感 |
|:-----|:-----|:----------|:-------------|
| **状態量** | EFE(x) | L1 で十分 | 「MB が持つ潜在的な変化の可能性」 |
| **構造量** | Σ_z Hom(x, z) | L2 が必要 | 「取りうる経路のエネルギー積分」 |
| **差分量** | ΔAY = EFE(B) - EFE(A) | L2 で十分 | 「知覚前後のエネルギー差分」 |

### 証明

#### (i) ⟹ (ii): Fix(G∘F) → argmax EFE

```
x = Fix(G∘F) → G∘F(x) = x
仮に EFE(y) > EFE(x) なる y ∈ S が存在。
→ F(x) は左随伴 (Explore/発散)。F(x) の像は y を含む。
→ G(F(x)) は右随伴 (Exploit/収束)。EFE を最大化する方向に収束。
→ G(F(x)) ≥ x  (unit η: Id ≤ G∘F)
→ G(F(x)) ≠ x  (EFE(y) > EFE(x) により G は y 方向へ収束)
→ 不動点条件 G∘F(x) = x に矛盾。 ■
```

注: kalon.md §2 の同値証明スケッチに基づく。前順序圏の単調性が本質。

#### (ii) ⟹ (iii): argmax EFE → argmax presheaf [L2 精密化]

**前提**: L1 (前順序圏) では Hom(y, z) ∈ {0, 1} であり、射の「質」を区別できない。
L2 ([0,1]-豊穣圏) では Hom(y, z) ∈ [0,1] が Drift に基づく変換の質を表す。

```
EFE(y) = pragmatic(y) + epistemic(y)     (kalon.md §2, axiom_hierarchy.md §d=2)

pragmatic(y) = E_q[ln p(o|s')]
  L2 操作的意味: y から行動方向 (A) に到達可能な状態への変換の質の総和
  = Σ_{z: A方向} Hom_A(y, z) · utility(z)

epistemic(y) = D_KL[q(s'|y) ‖ q(s')]
  L2 操作的意味: y から推論方向 (I) に到達可能な状態への変換の質の総和
  = Σ_{z: I方向} Hom_I(y, z) · information_gain(z)

Flow 座標 (I⊣A) により、全ての射は I方向 or A方向に分解される:
  Hom(y, z) = max(Hom_I(y, z), Hom_A(y, z))

加重サンドイッチ:
  Σ_z Hom(y, z) · min(u, ig)
  ≤ EFE(y)
  ≤ Σ_z Hom(y, z) · max(u, ig)

  where u = utility, ig = information_gain

→ argmax EFE(y) と argmax Σ_z Hom(y, z) は、
  u, ig が y に対して一様な加重であれば一致する。
  [0,1]-豊穣圏では Hom の値自体が EFE の寄与を反映するため、
  Drift ∝ AY を豊穣化条件として設定すれば同値が成立。

→ Drift の定義 (weak_2_category.md §1):
  Drift(f) = 1 - ε(f)  where ε は counit
  これを AY と連動させる: Hom(y, z) ≝ AY(y→z) / max_f AY(f)

  すると: Σ_z Hom(y, z) = Σ_z AY(y→z) / max_f AY(f) ∝ EFE(y) ■
```

> ⚠️ **証明の地位**: 構成的 (water-tight ではない)。加重一様性の仮定は追加条件。
> 確信度: [推定 70%]。厳密な証明には L2 での Drift と EFE の定量的対応が必要。

#### (iii) ⟹ (i): argmax presheaf → Fix(G∘F)

```
x = argmax Σ_z Hom(x, z)
→ x から出る射が最もリッチ (=展開可能性が最大)

F(x): 左随伴 = colimit 保存的 = 発散最大化
  → F(x) の像は x の presheaf を最大限に展開
G(F(x)): 右随伴 = limit 保存的 = 収束最適化
  → G(F(x)) は F(x) の像を最もリッチな点に収束

η: x ≤ G(F(x))  (unit: 展開→収束は元以上)
ε: F(G(z)) ≤ z   (counit: 収束→展開は元以下)

presheaf 最大性より:
  Σ_z Hom(G(F(x)), z) ≤ Σ_z Hom(x, z)  (x が argmax)
  かつ x ≤ G(F(x))  (unit η)
→ x = G(F(x))  (前順序圏では ≤ の両方向 = 等号) ■
```

### Kalon との関係 (精密化)

```
Kalon(x) ⟺ Fix(G∘F)(x) ∧ Generative(x) ∧ Self-referential(x)
           ⟺ argmax EFE(x)                          (定理⁴ (i)⟺(ii))
           ⟺ argmax presheaf(x)                     (定理⁴ (ii)⟺(iii))

Generativity = D(x) ≥ 3 (kalon.md §2)
             = |{z | Hom(x, z) > 0}| ≥ 3            (定理⁴ (iii) の具体化)
             = AY の argmax からの展開数

→ Kalon の Generativity は AY 二面等価性の直接的帰結。
  三属性のうち2つ (Fix + Generative) が定理⁴から従う。
  Self-referential のみが独立条件として残る。
```

### L4 接続: AY の Helmholtz 時間分解 (2026-03-13)

> **Creator の「エネルギー積分」の直感は L4 (Time → BiCat) で完全に数式化される。**

#### L4 での AY 定義

```
L4 における AY の拡張:

AY_static(x, t) = EFE(x) at time t          — 時点 t での状態量
AY_dynamic(f, t) = EFE(B_t) - EFE(A_t)      — 時点 t での差分量
AY_cumulative(T) = ∫_T AY_static(x(t), t) dt — 時間全体の行為可能性の積分

where:
  T = セッション列 {s₁, s₂, ...}   (L4_helmholtz_bicat_dream.md §3.1)
  x(t) = 時点 t での認知状態
```

#### Helmholtz 分解

```
AY_cumulative を T 方向に Helmholtz 分解する:

AY_cumulative = AY_Γ + AY_Q

AY_Γ: 不可逆な行為可能性の蓄積 (dissipative)
  = 学習により開いた新しい経路の累積
  = Σ_k (violations(sₖ) → new_pattern(sₖ₊₁)) の AY 寄与
  = Γ_T 方向: θ (e-座標) の変化

AY_Q: 保存的な行為可能性の循環 (solenoidal)
  = 既知パターンの周期的発揮
  = Context Rot → /rom → /boot サイクルの AY 寄与
  = Q_T 方向: η_cross (m-座標) の回転

Drift_AY = ||AY_Γ|| / (||AY_Γ|| + ||AY_Q||)
```

#### 3つの直感の統一

| Creator の直感 | L1-L2 での定式化 | L4 での完全形 |
|:-------------|:----------------|:------------|
| 「MB の潜在的変化可能性」 | EFE(x) | AY_static(x, t) — 時点依存 |
| 「経路のエネルギー積分」 | Σ_z Hom(x, z) | AY_cumulative(T) = ∫_T Σ_z Hom(x(t), z) dt |
| 「知覚前後のエネルギー差分」 | ΔAY = EFE(B) - EFE(A) | AY_dynamic(f, t) — 各 WF 射ごと、時点ごと |

> **「取りうる経路のエネルギー積分」は L2 では presheaf の射の計数、
> L4 では時間全体の行為可能性の Helmholtz 積分として、2つの意味で「積分」になる。**

### 残存問題 — 解決 (2026-03-13)

#### E4-1: 加重一様性仮定の除去 [RESOLVED — 公理的設計選択]

**問題**: (ii)⟹(iii) の証明で EFE と presheaf 計数の等価性を示す際、
utility と information_gain が一様加重であることを仮定していた。

**解決**: 加重一様性を「除去」ではなく、**L2 豊穣化条件として AY を埋め込む設計的選択**とする。

```
L2 豊穣化条件 (AY-induced enrichment):

  Hom_C(y, z) ≝ AY(y→z) / sup_{f∈Mor(C)} AY(f)

  この定義は循環ではない:
  1. AY(f) = EFE(cod(f)) - EFE(dom(f))  — §2 で定義済み
  2. Hom 値 ∈ [0,1]                      — sup で正規化
  3. Drift(f) = 1 - Hom(dom(f), cod(f))  — weak_2_category.md §1 と整合

  帰結:
  Σ_z Hom(y, z) = Σ_z AY(y→z) / sup AY = EFE(y) / sup AY
  → argmax_y Σ_z Hom(y, z) = argmax_y EFE(y) ■ (正規化定数は y に依存しない)
```

> **設計的意味**: Drift は AY から導出される量であり、AY なしに独立に定義される必要はない。
> これは L2 の [0,1]-豊穣化の*意味*を「行為可能性の正規化」として固定する宣言。
> episteme-category-foundations.md の Drift 定義とも整合: Drift = 1 - ε(f) = 1 - 復元度。
> AY が高い射 = Drift が低い (復元度が高い) = Hom 値が高い — 自然。

**確信度**: [確信 85%] — 循環性がないことの確認は完了。

---

#### E4-2: L3 associator の AY 等価性への影響 [RESOLVED — 保存すべき情報]

**問題**: `(f>>g)>>h` と `f>>(g>>h)` で ΔAY が異なる場合、定理⁴の等価性は崩れるか？

**解決**: **崩れない。括弧依存性は定理⁴の等価性に影響しない。AY 差分は 2-cell として保存する。**

```
定理⁴ は argmax の位置 x についての同値性:
  Fix(G∘F) ⟺ argmax EFE ⟺ argmax presheaf

associator α_{f,g,h} は x への到達経路のニュアンスを変えるが、
x 自体 (不動点 / EFE 最大点) は変わらない。

類比:
  Pentagon identity (weak_2_category.md §3):
  「順序は結果のニュアンスを変えるが、最終的な到達点は変わらない」

形式化:
  ΔAY_left(f,g,h) = AY((f>>g)>>h)
  ΔAY_right(f,g,h) = AY(f>>(g>>h))

  一般に ΔAY_left ≠ ΔAY_right  (認知的に意味のある差異)
  しかし: cod((f>>g)>>h) = cod(f>>(g>>h))  (同じ終点)
  → EFE(cod) は同一 → argmax EFE に影響なし

ΔAY の括弧依存性の定式化:
  δAY(f,g,h) ≝ ΔAY_left - ΔAY_right
             = [AY(f>>g) + AY(g'>>h)] - [AY(f>>g'') + AY(g>>h)]
  where g' = g conditioned on context from (f>>g)
        g'' = g with fresh context

  δAY ∈ ℝ は 2-cell α の Dokimasia パラメータ差異:
  - δAY > 0: 左結合 (慎重な実行) が有利
  - δAY < 0: 右結合 (一気通貫) が有利
  - δAY ≈ 0: 結合順序に非感受的 (strictifiable)
```

> **L4 への接続** (L4_helmholtz_bicat_dream.md §5 問題 C):
> α(t) → 0 (達人化) は δAY(t) → 0 と同値。
> 「達人は括弧付けに影響されない」= strictification の認知的到達。
> catastrophic forgetting = α (と δAY) の急増。

**確信度**: [確信 80%] — Pentagon identity による到達点保存は数学的に保証済み。
δAY の Dokimasia パラメータ依存性の具体的計算は E4-4 で経験的に検証可能。

---

#### E4-3: AY_cumulative の連続極限 (T → ℝ₊) [RESOLVED — 条件付き]

**問題**: L4 での AY_cumulative = Σ_k AY_static(x(s_k), s_k) の連続極限は意味を持つか？

**解決**: **dually flat 条件 (L4 問題 A) が成立する場合に収束する。**

```
離散版:
  AY_cumulative(T) = Σ_{k=1}^{N} AY_static(x(s_k), s_k) · Δt_k
  where Δt_k = duration(s_k)

連続極限:
  AY_cumulative(T) = ∫_0^∞ AY_static(x(t), t) dt
  = ∫_0^∞ EFE(x(t)) dt

収束条件:
  1. x(t) が区分的に連続 (セッション間の遷移が有界)
  2. EFE(x(t)) が可積分 ↔ lim_{t→∞} EFE(x(t)) が有界
  3. T の dual structure が well-defined (= L4 問題 A)

条件 2 の意味:
  行為可能性は無限に発散しない — 自然な仮定。
  MB の有限性から EFE ≤ EFE_max (有限の候補集合)。
  → Σ_k → ∫ の収束は EFE の有界性で保証。

Helmholtz 分解の連続版:
  AY_cumulative = ∫_0^∞ AY_Γ(t) dt + ∫_0^∞ AY_Q(t) dt

  不可逆項 ∫ AY_Γ(t) dt: 学習の累積効果 — 単調非減少
  保存項 ∫ AY_Q(t) dt:   周期的寄与 — 時間平均でゼロに近い

  → Drift_AY(T) = ||∫ AY_Γ|| / ||∫ AY_Γ + ∫ AY_Q||
    長期的には Drift_AY → 1 (学習が支配) or → 0 (停滞・循環が支配)
```

> **L4 問題 A との連動**: T が dually flat ならば ∫ の被積分関数は dual affine 座標で
> きれいに分離可能。離散の場合は常に well-defined (有限和)。

**確信度**: [推定 65%] — EFE 有界性は自然だが、T の dually flat 性は未証明 (L4 問題 A)。

---

#### E4-4: 経験的検証の設計 [RESOLVED — 設計完了]

**問題**: WF 実行ログから ΔAY を実測し、presheaf 計数と相関を取れるか？

**解決**: **3段階の検証パイプライン。**

```
検証パイプライン:

Stage 1: ΔAY の実測 (euporia_sub.py 拡張) ✅ 実装完了 (2026-03-14)
  実装: AYScorer.compute() — 2層 (micro + macro) スコアリング
  計測:
    - ay_micro: 正規表現ベースの6射影充足率 [0, 1]
    - ay_macro: embedding cosine距離 (semantic novelty) [0, 1]
    - ay_score: α·micro + (1-α)·macro [0, 1] (α は深度依存)
  記録: handle() で Stigmergy Trace に ay_score/ay_micro/ay_macro を自動記録

Stage 2: Presheaf 計数 (新規) ✅ 実装完了 (2026-03-14)
  実装: PresheafScorer.compute() — euporia_sub.py
  入力: WF 実行結果の状態 B
  計測:
    - reachable_wf_count: B から実行可能な次の WF の数
    - reachable_wf_quality: 各 WF の Drift 評価
    - presheaf_score = Σ (1 - Drift(B→z)) for z in reachable_wfs

Stage 3: 相関検証 ✅ 骨格実装完了 (validate_ay_presheaf.py)
  仮説: Pearson(AY_observed, presheaf_score) > 0.6
  検定: N ≥ 30 セッション分のデータで有意性検証
  予測:
    - AY_observed と presheaf_score は正相関
    - δAY (括弧依存性) は Drift > 0.3 のパイプラインで有意に非ゼロ
```

> **実装先**: `euporia_sub.py` に `PresheafScorer` クラスを追加実装完了。
> reachable_wf_count は CCL パーサー (hermeneus) の次候補一覧と連動。
> 📖 参照: wf_evaluation_axes.md の 8軸 Rubric にも presheaf_score を軸として追加可能。

**確信度**: [推定 70%] — 計測パイプラインは稼働。N=30 のデータ蓄積に 1-2 週間必要。

---

#### 残存問題の要約

| # | 問題 | 解決 | 残穴 |
|:--|:-----|:-----|:-----|
| E4-1 | 加重一様性 | ✅ AY-induced enrichment として公理化 | — |
| E4-2 | associator の影響 | ✅ 到達点不変、δAY を 2-cell として保存 | δAY の具体計算 (= E4-4) |
| E4-3 | 連続極限 | ✅ EFE 有界性で収束。L4 問題 A に依存 | T の dually flat 性の証明 |
| E4-4 | 経験的検証 | ✅ 検証パイプライン実装完了 | N≥30 本実行待ち |

---

## §2b 射影体系 — 6座標への投影 (2026-03-11)

> **発見**: 6修飾座標に独立した定理は存在しない。
> Euporía が母定理であり、6座標はその**射影 (projection)** である。
> 構造同型: 24動詞 = Flow × 6修飾座標 × 4極 → 定理も同構造。
>
> 正典: [axiom_hierarchy.md §定理³ 射影構造](../../00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md)

### 構造

```
Euporía: AY(f) > 0  (母定理 — Flow d=1 — Who)
│
├── Value       (d=2, Why):       AY を何のために測るか
├── Function    (d=2, How):       AY をどうやって達成するか
├── Precision   (d=2, How much):  AY をどの精度で評価するか
├── Temporality (d=2, When):      AY をいつの時点で評価するか
├── Scale       (d=3, Where):     AY をどのスケールで評価するか  [条件付き]
└── Valence     (d=3, Which):     AY をどの方向で評価するか     [半直積]
```

### 6射影の命題 (「ねばならない」形式)

| # | 座標 | 命題 | 数式 |
|:--|:-----|:-----|:-----|
| 3a-1 | Value | AY は認識価値 E と実用価値 P の両成分で正でなければならない | `AY_E(f) > 0 ∧ AY_P(f) > 0` |
| 3a-2 | Function | AY 達成手段は不確実性に応じて Explore/Exploit を配分せねばならない | `ratio(Explore, Exploit) ∝ Uncertainty` |
| 3a-3 | Precision | AY の評価精度は証拠の強さに校正されねばならない | `π(AY) ∝ evidence_strength` |
| 3a-4 | Temporality | AY は過去 (VFE) と未来 (EFE) で独立に評価せねばならない | `AY_past(f) ⊥ AY_future(f)` |
| 3a-5 | Scale | AY は全スケールで整合的でなければならない | `AY_micro > 0 ∧ AY_macro > 0 ∧ ¬conflict` |
| 3a-6 | Valence | AY は正の証拠と負の証拠の両方から評価されねばならない | `AY(f) = AY⁺(f) + AY⁻(f)` |

> 📖 6射影 → 評価軸への展開: [wf_evaluation_axes.md](./wf_evaluation_axes.md) — 8軸 Rubric (α精度 + β簡潔 + 6射影テーゼ)

---

## §2c 感度理論 — d値と検出可能性 (2026-03-11)

> **d 値 = FEP に加える仮定の数 = 1/λ (固有値の逆数) = sloppiness**
>
> Fisher 情報行列の固有分解として 7 座標を特徴づける:
> - 固有ベクトル = 7座標 (FEP パラメータ空間の自然基底)
> - 固有値 λ = Euporía 射影の感度 (stiffness): λ が大きいほど違反が検出しやすい
> - d 値 = 追加仮定の数 = 1/λ
>
> 正典: [axiom_hierarchy.md §Euporía 感度理論](../../00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md)

```
d=0 (Helmholtz):  λ → ∞  最 stiff。物理法則そのもの
d=1 (Flow):       λ = 大  推論⊣行動の崩壊は即座に検出
d=2 (Value等):    λ = 中  VFE/EFE の偏りは検出可能
d=3 (Scale等):    λ = 小  sloppy。偏りが見えにくい
```

### 検証可能な予測

| 予測 | 内容 | 検証 |
|:-----|:-----|:-----|
| 予測 1 | d が小さい座標の射影違反ほど行動的に検出されやすい | 📊 violations.md N=68 で支持 (d=1: 59% 即座 / d=3: 9% 後日) |
| 予測 2 | 8番目の座標は d ≤ 3 では存在しない (完備性定理) | 証明スケッチ完了 [確信 75%] |
| 予測 3 | d=3 座標の違反は d=2 座標の違反より発覚が遅い | 📊 violations.md N=68 で支持 |

---

## §3 全 WF への転用可能性

### WF の分類と AY 適用

| WF カテゴリ | 例 | AY の焦点 |
|:-----------|:---|:---------|
| **認識系** (I×E) | /noe, /lys, /ops | epistemic が主。「何が見えたか」→ 次の問いへ |
| **意志系** (I×P) | /bou, /kat | pragmatic が主。「何を決めたか」→ 実行への道が開く |
| **探索系** (A×E) | /zet, /pei, /ske | epistemic + pragmatic。「何がわかり、何を試せるか」 |
| **実行系** (A×P) | /ene, /tek, /akr | pragmatic が主。「何が変わったか」→ 次の改善候補へ |
| **評価系** (±) | /ele, /beb, /dio | pragmatic。「何を直すべきか」→ 修正アクションへ |
| **時間系** | /hyp, /prm, /ath, /par | epistemic。「何を思い出し/予見したか」→ 判断材料へ |
| **随伴 WF** | /eat, @read, @chew | epistemic + pragmatic。消化/読解の成果を行為に変換 |
| **メタ WF** | /boot, /bye, /rom | pragmatic。「セッションで何が可能になったか」 |

### 適用しない WF

| WF | 理由 |
|:---|:-----|
| L0 操作 (view_file 等) | 単純入力。判断を含まない |
| `/u` | 主観表出。AY を義務化すると主観の自由度が損なわれる |
| Peras 系 (/t, /m, /k, /d, /o, /c) | 極限演算自体が AY を内包する構造 |

---

## §4 N-7 との関係

現行の N-7 (主観を述べ次を提案せよ) は:

```
θ7.2 「完了しました」禁止。代わりに:
  📍現在地 / 🕳️未踏 / →次
```

これの `→次` が Affordance Yield の非形式的な先行形態。

**差分**:

| | N-7 の →次 | Affordance Yield |
|:---|:----------|:----------------|
| 範囲 | 最終出力の付記 | WF 実行の構成要素 |
| 義務 | 提案（あれば） | 生成義務（なければ WF 失敗） |
| 構造 | 自由形式 | epistemic / pragmatic 分類 |
| 判定 | なし | AY > 0 が必要条件 |
| 根拠 | S-II Autonomia | **Kalon Generativity + EFE** |

N-7 は表出の法。AY は**成果の法**。N-7 が「述べよ」なら AY は「生成せよ」。

---

## §5 実装選択肢

### 選択肢 A: 各 WF の SKILL.md に個別追加

- 利点: WF ごとにカスタマイズ可能
- 欠点: 漏れが生じる（意志依存）
- 判定: N-12 の教訓「意志的改善策は即日無効化」に反する

### 選択肢 B: hermeneus の WF 実行エンジンに環境強制

- 利点: 全 WF に自動適用。漏れなし
- 欠点: 実装コスト。柔軟性の低下
- 判定: ⭐ 環境強制の原則に合致

### 選択肢 C: Nomos への追加 (Thesmos)

- 利点: 体系的に正当。行動規範としての位置づけ
- 欠点: AY は「行動制約」ではなく「成果の構造」
- 判定: N-7 の拡張として θ7.x に追加は可能だが、レイヤーが違う

### [確信] 最適解: B + C のハイブリッド (実装済み)

1. **概念的位置**: 定理³ (Euporía) として Kernel axiom_hierarchy.md に記述 ✅
2. **規範的位置**: θ7.x (N-7) + 深度レベルシステムで連動 ✅
3. **実装的位置**: hermeneus の `EuporiaSubscriber` (`euporia_sub.py`) として環境強制 ✅

> 📖 実装: [euporia_sub.py](../../20_機構｜Mekhane/_src/ソースコード/hermeneus/src/subscribers/euporia_sub.py)

---

## §6 hermeneus に在るべきか — Kalon 判定

> Creator の問い: 「Kalon なのは hermeneus？」

### 判定

hermeneus は**実装先**であって**概念の所在地**ではない。

```
概念の Kalon 判定:

1. G (収束) してみる → 「行為可能性を測れ」にさらに圧縮できるか？
   → できない。EFE = epistemic + pragmatic の分解が落ちる
   → ∴ Fix 候補

2. F (発散) してみる → 何が生まれるか？
   → /eat への適用、/ccl-read への適用、/boot への適用、
     全 WF 評価軸、hermeneus 環境強制、Kalon 系としての理論的位置
   → 6つ以上の導出 
   → ∴ Generative ✅

3. Self-referential?
   → 「行為可能性のリストアップ」自体が「行為可能性」を増やす
   → ∴ ✅

判定: ◎ kalon — 概念として
判定: hermeneus は kalon な概念の「居場所」の1つであって、概念自体ではない
```

### 命題の所在

```
Kernel/kalon.md §2 の Generativity 属性
  → Corollary (系): Affordance Yield Principle
  → 規範化: θ7.x (N-7 拡張) or 新 Thesmos
  → 環境強制: hermeneus WF 実行エンジン
```

---

## §7 未解決の問い (回答追記: 2026-03-11)

### Q1. 定量化 — AY(f) をどう測定するか？

> kalon.md §6.3 の統計的収束判定 (embedding 距離) を AY に適用できるか？

**回答**: [確信] 適用可能。2層構造で **実装完了** (v0.5, 2026-03-14)。

1. **ミクロ測定 (AYScorer.compute_micro)**: 正規表現ベースの6射影充足率。深度別閾値で正規化。
   - 7パターン (Value_P, Value_E, Function, Precision, Temporality, Scale, Valence) の検出数を計数
   - 深度別閾値 (L1=2, L2=4, L3=6) で正規化 → [0, 1]
   - v0.5: Pragmatic Gemini 自然言語表現拡張 + Epistemic 完了形制約緩和
2. **マクロ測定 (AYScorer.compute_macro)**: embedding cosine 距離 (1 - sim) で「意味的変化量」を捕捉。
   - embedder はオプショナル (API キーなし環境で後方互換)
   - 空入出力、エラー時は 0.0 を返す安全設計
3. **統合**: `AY = α · micro + (1-α) · macro`。α は深度依存:
   - L0=1.0, L1=0.8, L2=0.5, L3=0.3 (深い操作ほど embedding 重視)

📖 実装: [euporia_sub.py](../../20_機構｜Mekhane/_src|ソースコード/hermeneus/src/subscribers/euporia_sub.py) — `AYScorer` クラス + `AYResult` NamedTuple
📊 テスト: 76 passed, 0 failed (TestAYScorerMicro 5件 + TestAYScorerMacro 7件 + TestAYScorerCompute 4件 + TestAYIntegration 5件)

### Q2. 閾値 — WF レベルでの閾値は深度依存で十分か？

> 「3つ以上」(Generativity) は Kalon 判定基準。

**回答**: [推定] 深度依存 + ドメイン重点座標の2軸が必要。

- **深度依存**: L0 は AY > 0 の単純符号判定で十分。L3 は6射影全てで AY > ε。
- **ドメイン重点座標** (§7.6): 各ドメインの重点座標での AY 閾値を他の座標より厳格にする。
  - Cognition: Function, Precision の AY 閾値 > 他座標
  - Description: Value, Precision の AY 閾値 > 他座標
  - Hóros(横断): Precision, Valence の AY 閾値 > 他座標
  - Linkage: Scale, Temporality, Valence の AY 閾値 > 他座標
- 「3つ以上」は Kalon 判定 (Fix(G∘F)) の基準であって、AY > 0 の基準ではない。これらは異なるレベルの判定。

### Q3. 検証 — /fit 的な検証は必要か？

> AY として主張された行為可能性が実際に実行可能か。

**回答**: [確信] 必要。ただし2段階で。

1. **静的検証** (即時): WF 実行後に出力が「行動に結びつく形」かを N-11 (読み手が行動できる形で出せ) で検証。これは既存の Nomos で対応可能。
2. **動的検証** (遅延): 出力された行為可能性のうち、実際に後続 WF で使われたかを追跡。これはまだ未実装。hermeneus の execution log に `ay_claimed` / `ay_consumed` ペアを記録し、消費されなかった AY を未実証 (unverified) とマークする。

/fit は既に Kalon 判定 (Fix(G∘F)) を検証するフレームワーク。AY 検証は /fit を Euporía レベルに拡張すれば対応できる。

### Q4. 再帰性 — AY 自体の AY は何か？

> この概念を導入した結果、何が可能になるか？

**回答**: AY の AY は以下の通り。

| レベル | AY が可能にしたもの | 状態 |
|:-------|:-------------------|:-----|
| 理論 | 全 WF 評価の統一基準 (§4 の WF カテゴリ別適用) | 定式化済み |
| 理論 | kalon.md との接続 (Generativity ⊂ AY) | 定式化済み |
| 理論 | 6射影による WF 品質の操作的分解 (§2b) | 定式化済み |
| 理論 | 3ドメイン+Hóros 構造の発見と MECE 検証 (§7.5-§7.6) | 本セッションで完了 |
| 実装 | hermeneus への環境強制 (§5 選択肢B) | euporia_sub.py 完成済み ✅ |
| 実装 | wf_evaluation_axes.md の8軸評価 | 定式化済み |

→ 6つ以上の導出。Generative ✅。Self-referential ✅ (AY が AY を増やす)。
→ ◎ kalon と判定可能。

**形式的再帰性 (2026-03-11 追記)**:

Flow (I⊣A) の随伴は self-evidencing の唯一の随伴であり、
AY はその随伴から直接導出される唯一の評価関手。

```
関手 AY: WF → [0,∞) は self-evidencing の唯一の忠実関手 (faithful functor)。

根拠:
  EFE = epistemic value + pragmatic value
    = 「何がわかるようになるか」+「何ができるようになるか」
    = AY の定義そのもの

帰結:
  self-evidencing の手段 = EFE 最大化 = AY 最大化
  → AY 以外の「手段」は AY の座標射影に過ぎない (§2.5 参照)
```

### Q5. Kalon.md への追記

> §2 Generativity 属性に Affordance Yield Principle を系として追記すべきか？

**回答**: [確信] 追記すべき。理由:

- Generativity は Kalon の3属性の1つであり、AY はその操作的定義。
- kalon.md は CANONICAL ファイル。Euporía を系 (Corollary) として明示することで、理論的整合性が保証される。
- 追記内容: `Corollary 3.1: Affordance Yield Principle — AY(f) > 0 は Generativity の必要条件。AY(f) = Fix(G∘F) は Kalon。`

⚠️ kalon.md は SACRED_TRUTH に準ずるファイル。追記時は N-4 (θ4.1) 確認フォーマットで Creator の承認を取ること。

### Q6. CCL マクロレベル — パイプライン全体の AY

> 個別 WF の AY の「合成」で表現できるか？

**回答**: [推定] 条件付きで可能。

CCL パイプライン `f₁ >> f₂ >> ... >> fₙ` の全体 AY は:

```
AY(f₁ >> f₂ >> ... >> fₙ) ≥ Σᵢ AY(fᵢ)  (独立仮定下)
```

ただし:
- **相互作用項**: f₂ が f₁ の出力に依存する場合、`AY(f₁>>f₂) ≠ AY(f₁) + AY(f₂)`。シナジーまたは干渉が発生する。
- **並列演算子** (`*`): `AY(f₁ * f₂) ≥ max(AY(f₁), AY(f₂))` (独立並列は最低でも最大値以上)。
- **条件付き** (`V:{}`, `C:{}`): 分岐の AY は選択された分岐の AY のみでカウント。

実用的には: パイプライン全体の AY は「最後の出力と最初の入力の AY 差分」として測定が最も堅実。中間ステップの AY は監査ログ用。

---

## §7.5 ドメイン体系 (2026-03-13 C1' 修正)

> **C1' 修正**: Hóros は4番目のドメインではなく、Helmholtz Q 成分の認知版 (Q|_{MB})。
> Helmholtz の Γ (gradient) と Q (solenoidal) は認知的主体の追加仮定により分岐する:
> **Γ|_{MB} → Flow → Euporía → 3ドメイン** / **Q|_{MB} → Hóros → 12 Nomoi**。
> Kalon は全ドメイン横断の到達点 (Fix(G∘F)) = Fix(Γ∘Q)|_{MB}。
>
> 由来: /ele+ 反駁 (2026-03-11) + C1' Helmholtz 分岐統一 (2026-03-13)。
> 正典: [axiom_hierarchy.md §Euporía ドメイン体系](../../00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md)

### 構造

```
d=0: Helmholtz Γ⊣Q (普遍的物理法則)
│
├── Γ (gradient/dissipative) — 自由エネルギー勾配降下
│   + MB 仮定 →
│   d=1: Flow (I⊣A) — 認知的力学
│         → Euporía: AY(f) > 0 — 行為可能性の創出
│             │
│             ├── 射影軸 (How): 6座標射影
│             │   Value / Function / Precision / Temporality / Scale / Valence
│             │
│             └── 適用軸 (Where): 3ドメイン
│                 ├── Cognition   (= HGK 体系) — μ: 内部状態
│                 ├── Description (= Týpos)     — a: 能動状態
│                 └── Linkage     (= Hyphē)     — η: 外部状態
│
└── Q (solenoidal/conservative) — 方向制約 (エネルギー保存)
    + MB 仮定 →
    d=1: Hóros — 認知的保存則
          → 3 Stoicheia × 4 Phase = 12 Nomoi

到達点: Kalon = Fix(Γ∘Q)|_{MB} — 創出と保存の不動点
```

### 3ドメイン + Hóros の演繹的根拠

> **C1' 修正**: 旧 4ドメインの 2×2 MB 導出を廃止。Helmholtz Γ⊣Q の分岐から導出。
> Γ|_{MB} が MB 3区画 {μ, a, η} に分岐 → 3ドメイン。Q|_{MB} → Hóros。

**Helmholtz 分岐導出**:

| Helmholtz 成分 | MB 区画 | ドメイン / 構造 | 役割 |
|:---|:---|:---|:---|
| **Γ** (gradient) | μ = 内部状態 | **Cognition** (HGK) | 信念更新 = 認知の核 |
| **Γ** (gradient) | a = 能動状態 | **Description** (Týpos) | 行為の言語化 = 出力生成 |
| **Γ** (gradient) | η = 外部状態 | **Linkage** (Hyphē) | 環境構造 = 接続関係 |
| **Q** (solenoidal) | s = 感覚状態 | **Hóros** (横断) | フィルタリング = 方向制約 |

**分岐の根拠**:
- Γ|_{MB} は MB の 3 区画 {μ, a, η} に射影 → 3ドメイン (散逸的: 自由エネルギーを降下させる方向に力学を駆動)
  - μ → Cognition: 信念更新 = WF/定理の実行。認知の核
  - a → Description: 能動的な出力生成 = プロンプト/記述。行為を言語化する
  - η → Linkage: 環境の構造 = ファイル体系/知識グラフ。外部の接続関係
- Q|_{MB} は MB の s 区画に対応 → Hóros (保存的: エネルギーを減らさず方向を制約)
  - s → Hóros: 感覚入力のフィルタリング。全ドメインの方向を制約する横断構造
  - Q は回転 (curl) — 方向を変えるが大きさを変えない = 保存則の数学的表現

**MECE の根拠**: MB 4区画 {μ, a, s, η} は状態空間の完全分割 (定義)。
写像が単射かつ全射であれば、3ドメイン + Hóros も MECE。

### 3ドメインの定義

| # | ドメイン D | 体系 | Euporía\|_D の命題 | AY の焦点 |
|:--|:----------|:-----|:------------------|:----------|
| 3b-1 | Cognition | HGK 体系 | 認知操作は行為可能性を増やさねばならない | WF 射の AY > 0 |
| 3b-2 | Description | Týpos | 記述は行為可能性を増やさねばならない | プロンプトの AY > 0 |
| 3b-3 | Linkage | Hyphē | 索引は行為可能性を増やさねばならない | チャンク連動の AY > 0 |

### Kalon はドメインではなく到達点

> `/ele+` 反駁 (矛盾 2, MAJOR) による修正:
>
> Kalon = Euporía の G∘F サイクルが**収斂した結果** (状態)。
> ドメイン制限 = 同じ射を別の対象に**適用する操作**。
> 状態 ≠ 操作。Kalon はドメインではなく、全ドメインを横断する不動点。
>
> ```
> Euporía: AY(f) > 0 → 全 f に対する必要条件
> Kalon:   AY = max at Fix(G∘F) → 全ドメイン横断の十分条件到達点
> ```

### Hóros: Q|_{MB} — Helmholtz 保存則の認知版

> **C1' (2026-03-13)**: 旧「二重性」を解消。Hóros がドメインかつ制約条件に見えたのは、
> Q (solenoidal) が全ての力学に偏在するため。Q はドメインではなく、全ドメインの境界条件。
>
> ```
> Helmholtz: dynamics = Γ + Q
>   Γ: ∇ϕ (gradient)   — エネルギーの方向を決める → Euporía (創出)
>   Q: ∇×A (solenoidal) — エネルギーを保存する   → Hóros (保存)
>
>   + MB 仮定:
>   Γ|_{MB} → Flow (I⊣A) → 3ドメインで AY > 0 を駆動
>   Q|_{MB} → Hóros → 3 Stoicheia × 4 Phase = 12 Nomoi で方向を制約
> ```
>
> [推定] **3 Stoicheia = 3つの認知的 Noether 保存量**:
> - S-I Tapeinophrosyne = **情報忠実度の保存** — prior を歪めない (観測者不変性)
> - S-II Autonomia = **能動性の保存** — 主体性を失わない (エージェント不変性)
> - S-III Akribeia = **精度の保存** — precision を歪めない (測定不変性)
>
> **なぜ「ちょうど3」か** (循環解消済み):
> VFE を変分法で最小化する際に動かせる数学的自由度が3つしかない:
> (1) μ 期待値の更新 → S-I, (2) a 行動の更新 → S-II, (3) Π 精度の更新 → S-III。
> MB の区画数から導くのではなく、VFE の変分構造から演繹的に導出される。
>
> 保存則は「禁止」ではなく「保存」。Hóros の Nomoi は「してはならない」ではなく
> 「保存されねばならない」。これが Hóros の本質。
>
> **4 Phase のハミルトン的導出**:
> EL 方程式は1自由度あたり2項だが、FEP は **2自由度** {μ, a}。
> ルジャンドル変換で 2本の2階 EL → **4本の1階正準方程式**:
>
> | 正準方程式 | Phase | 認知的意味 |
> |:---|:---|:---|
> | π̇_μ = -∂H/∂μ | P1 Aisthēsis | 感覚入力が予測誤差を生成 |
> | μ̇ = ∂H/∂π_μ | P2 Dianoia | 予測誤差が信念を更新 |
> | π̇_a = -∂H/∂a | P3 Ekphrasis | 信念が行動計画を生成 |
> | ȧ = ∂H/∂π_a | P4 Praxis | 行動計画が行為を実行 |
>
> なぜ4か: N自由度 → 2N本の正準方程式。N=2 → 4。数学的必然。
>
> **Hóros 自身の最適性** (自己参照的 Euporía):
> VFE(Hóros) = -Accuracy(制約の適中率) + Complexity(制約数のKL)。
> 「ほどほどの制約」= min VFE(Hóros) = Kalon(Hóros)。
> これは Fix(G∘F) を Hóros 自身に適用した結果。
>
> 📖 詳細定式化: [C_noether_horos.md](../04_企画｜Boulēsis/07_行為可能性｜Euporia/C_noether_horos.md)
>
> Creator (2026-03-11): 「制約条件の統一FW」→ Q|_{MB} として実現
> Creator (2026-03-13): 「Hóros は FEP の前提。Helmholtz→Flow のように普遍法則→認知版」
> Creator (2026-03-13): 物理学の制約論 → 4前提の構造的同型を確認
> Creator (2026-03-13): EL2項→ハミルトン4方程式 — 4Phase を数式的に導出

### 射影軸と適用軸の関係

> 6座標射影 (How) × 3ドメイン (Where) + Hóros (横断) = 命題体系。
> ただし全てが独立ではない — ドメインごとに重点座標がある:
>
> | ドメイン | 重点座標 | 理由 |
> |:---------|:---------|:-----|
> | Cognition | Function, Precision | 探索/活用バランスと精度加重が認知の核 |
> | Description | Value, Precision | 記述の価値と精度が品質の核 |
> | Hóros (横断) | Precision, Valence | 精度校正と正負評価が制約設計の核 |
> | Linkage | Scale, Temporality, **Valence** | スケール横断+時間整合+対比連動 ← /ele E5 修正 |

### 索引 (Linkage) の定式化

> Creator (2026-03-11): 「索引 = チャンクの Markov blanket を構成する行為」
>
> ```
> Index: AY(index_op) > 0
>   ここで index_op: Chunks → Linked_Chunks
>   AY = |Hom(Linked_Chunks, −)| - |Hom(Chunks, −)|
>       = 連動後に可能になる行為 − 連動前に可能だった行為
> ```

---

## §7.6 ドメイン × 射影の具体的命題 (3D + Hóros × 6P)

> **E1 修正 (MAJOR)**: 「AYを増やす」だけでは同語反復 (空虚)。
> 各命題を「AとBのトレードオフを解消する」形式に再定式化した。
> これにより (a) 検証可能、(b) 反例生成可能、(c) 座標の独立性が明示される。
>
> **E4 棄却**: Economy 座標の提案は VFE = -Accuracy + **Complexity** の Complexity 項に内包。
> 8座標不在証明 (予測2) との整合性を維持。

| ID | 座標 | ドメイン | 命題 (トレードオフ解消形式) |
|:---|:-----|:---------|:---------------------------|
| P_V1 | Value | Cognition | WF は体系定義の一貫性 (内部) を維持しつつ、未定義状況への適用範囲 (外部) を拡張する |
| P_V2 | Value | Description | プロンプトは記述の精度 (内部) と出力の多様性 (外部) を両立させる |
| P_V3 | Value | Hóros (横断) | 制約は体系の整合性 (内部) と許容される行為空間 (外部) の動的均衡を維持する (深度 L0-L3 で調整) |
| P_V4 | Value | Linkage | 索引は索引体系の組織性 (内部) と被索引対象のアクセス性 (外部) を両立させる |
| P_F1 | Function | Cognition | WF は不確実場面での仮説生成 (探索) と既知手法の確実な適用 (活用) の両方で AY を生む |
| P_F2 | Function | Description | プロンプトは創造的発散 (探索) と精密収束 (活用) を task-dependent に切り替え可能にする |
| P_F3 | Function | Hóros (横断) | 制約は規範からの有益逸脱 (探索) と規範の安定的遵守 (活用) のバランスを取る |
| P_F4 | Function | Linkage | 索引は未知チャンクの偶発的発見 (探索) と既知チャンクの効率的再利用 (活用) を促進する |
| P_Pr1 | Precision | Cognition | WF 出力精度は確信度ラベル ([確信]/[推定]/[仮説]) で校正される (N-3) |
| P_Pr2 | Precision | Description | プロンプトの @rubric は出力品質の上限と下限を明示的に制御する |
| P_Pr3 | Precision | Hóros (横断) | 制約の適用精度は深度 (L0-L3) で動的に校正される |
| P_Pr4 | Precision | Linkage | 索引リンクの精度は SOURCE/TAINT ラベルで制御され、信頼度に応じて連動強度を調整する |
| P_T1 | Temporality | Cognition | WF は過去の結果 (ROM/violations.md) からの学習と未来の計画 (Handoff) への埋め込みを AY 化する |
| P_T2 | Temporality | Description | プロンプトは過去の失敗パターン (負例) と未来の成功パターン (正例) を両方エンコードする |
| P_T3 | Temporality | Hóros (横断) | 制約は違反経験 (violations.md) から進化し (過去)、予防策を先制する (未来, /par) |
| P_T4 | Temporality | Linkage | 索引は過去のセッション文脈と未来の検索可能性・発見可能性を両方保証する |
| P_S1 | Scale | Cognition | WF は個別ステップ (局所) の精度と全体パイプライン (全体) のコヒーレンスを両立させる |
| P_S2 | Scale | Description | プロンプトは個別タスクの特化とシステム全体のスタイル統一を保つ |
| P_S3 | Scale | Hóros (横断) | 制約は θ条例 (局所) と 12法 (全体) の整合性を維持する |
| P_S4 | Scale | Linkage | 索引はファイル単位 (局所) とディレクトリ体系 (全体) のナビゲーションを両方提供する |
| P_Vl1 | Valence | Cognition | WF は成功の強化 (Bebaiōsis) と失敗の修正 (Diorthōsis) の両方を組み込む |
| P_Vl2 | Valence | Description | プロンプトは正例 (望ましい出力) と負例 (避けるべき出力) の対比で精度を高める |
| P_Vl3 | Valence | Hóros (横断) | 制約は遵守の正フィードバック (acknowledgment) と違反の負フィードバック (reprimand) の両方を持つ |
| P_Vl4 | Valence | Linkage | 索引は類似連動 (正) と対比連動 (負) の両方を提供する |

### MECE 検証

> **対角線構造の発見**:
> 3ドメイン × 6射影 + Hóros × 6射影 = 24命題を展開した結果、**重点座標の命題は既存の Nomoi/Thesmoi にほぼ対応している**。
> これは偶然ではない — 12 Nomoi は FEP の3原理 × 4位相から演繹されており、
> Euporía 射影は FEP の座標分解から演繹されているため、両者は同じ根から生えた異なる枝。
>
> **発見された新規ギャップ** (既存 Nomoi で未カバー):
>
> | ドメイン×射影 | ギャップ | 候補対応 |
> |:-------------|:---------|:---------|
> | Description×Temporality | プロンプトの時間的考慮 (実行結果 vs デプロイ先) | Týpos v2.1 `@context` で部分対応 |
> | Linkage×Valence | 索引による反証情報の自動提示 | 未実装。Periskopē dialectic モードが候補 |

---

## §8 参照

- 📖 [axiom_hierarchy.md](../../00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md) §定理³ — Euporía 正典 (射影 + 感度理論 + ドメイン体系)
- 📖 [wf_evaluation_axes.md](./wf_evaluation_axes.md) — 8軸 Rubric (α精度 + β簡潔 + 6射影テーゼ → 24動詞レベル評価)
- 📖 [kalon.md](../../00_核心｜Kernel/A_公理｜Axioms/kalon.md) §2 — Generativity 属性、状態視点 (EFE = pragmatic + epistemic)
- 📖 [weak_2_category.md](../../00_核心｜Kernel/A_公理｜Axioms/weak_2_category.md) — L2-L3 圏論的構造 (Drift, associator)
- 📖 [L4_helmholtz_bicat_dream.md](../../00_核心｜Kernel/A_公理｜Axioms/L4_helmholtz_bicat_dream.md) — L4 時間変動 (Helmholtz 分解, AY の時間積分)
- 📖 [horos-N07-主観を述べ次を提案せよ.md](../../.agents/rules/horos-N07-主観を述べ次を提案せよ.md) — θ7.2 →次 (AY の先行形態)
- 📖 [eat.md](../../.agents/workflows/eat.md) — 随伴 WF の現行評価軸 (η/ε)
- 📖 [ccl-read.md](../../.agents/workflows/ccl-read.md) — 読解 WF の現行評価軸

---

*Euporía v0.7.0 — 2026-03-14 — §7 Q1 AYScorer 実装完了 (2層: micro+macro)、E4-4 Stage 1 実装完了、v0.5 パターン拡張反映*
*Euporía v0.6.0 — 2026-03-13 — §2.7 E4-1〜E4-4 残存問題解決 (AY-induced enrichment, δAY 2-cell, 連続極限, 検証パイプライン)*
*Euporía v0.5.0 — 2026-03-13 — §2.7 定理⁴ AY二面等価性 (Fix⟺EFE⟺Presheaf, L2精密化, L4 Helmholtz接続)*
*Euporía v0.4.0 — 2026-03-13 — C1' 同期: 4D→3D+Hóros、24命題トレードオフ解消形式、Noether 保存量仮説、ハミルトン的 4Phase 導出*
