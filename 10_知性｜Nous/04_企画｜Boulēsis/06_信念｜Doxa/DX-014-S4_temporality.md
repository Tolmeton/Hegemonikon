# DX-014-S4: Step④ Temporality (d=2) の一意性 — 救出版

> **Step**: ④ Temporality (d=2) — Past (過去) ↔ Future (未来)
> **旧定式**: VFE/EFE 非対称 + T⊥H (Pezzulo 2022) → 確信度 55%
> **新定式**: generative model の時間的深度 → **確信度 88%**
> **追加仮定**: (1) EFE + (2) 生成モデルが状態遷移を持つ (temporal dynamics)
> **状態**: 🟢 文献的裏付け強化 — Pezzulo 2021 (83引用) + Friston 2024 (20引用)

---

## 旧定式の壁と救出戦略

### 壁の再評価

| # | 旧壁 | Valence 救出から学んだこと | 解消策 |
|:-:|:-----|:------------|:-------|
| 1 | EFE の必要性が争点 | **仮定の置換**: より弱い仮定を探す | VFE/EFE ではなく「状態遷移」で定式化 |
| 2 | 時間の矢は FEP 外部 | **FEP 内部に留まる**: sgn(−ΔF) が成功した | Langevin dynamics の時間方向で定式化 |
| 3 | Memoryless エージェント | **条件の明確化**: d=2 は「追加仮定が必要」の意味 | 「記憶なしなら d=1 で生存可能」を認める |

---

## 主張 (修正版)

> **C4'**: FEP + 状態遷移ダイナミクス → Temporality (Past↔Future) は一意
>
> Temporality = FEP における **VFE/EFE の非対称性** であり、
> 「過去のデータで信念を更新する」(VFE) と「未来の行動を選択する」(EFE) の
> 不可逆な区別。

---

## 証明スケッチ (修正版)

### 補題G': VFE と EFE は異なる汎関数

1. **VFE** F(q) = D_KL[q(s) || p(s)] + H[q]
   - **入力**: 過去/現在の感覚データ o₁, o₂, ..., oₜ
   - **操作**: 信念 q(s) の更新 (filtering/smoothing)
   - **方向**: 過去 → 現在 (後向き)

2. **EFE** G(π) = E_q[ln q(s|π) − ln p(o,s)]
   - **入力**: 将来の政策 π
   - **操作**: 政策の評価と選択 (planning)
   - **方向**: 現在 → 未来 (前向き)

3. VFE と EFE は**定義域が異なる** (SOURCE: axiom_hierarchy.md L68):
   - VFE: (信念, 観測データ) → ℝ
   - EFE: (政策) → ℝ

4. ∴ VFE と EFE の区別 = 過去と未来の区別

**強さ**: 🟢 — 数学的定義から直接。VFE と EFE は別の汎関数 (議論の余地なし)

### 補題H': EFE の定義が Temporality を内在する (v4.0 — 循環修正)

> ⚠️ **v3.0 の循環論法を修正**: v3.0 は「adaptive = temporal depth > 0」と定義したが、
> これは同語反復だった。v4.0 では「adaptive」を迂回し、EFE の数学的定義から直接導出。

**EFE G(π) の数学的定義**:

G(π) = E_Q(o,s|π) [ln Q(s|π) − ln P(o,s)]

**この定義を分解する**:

1. E_Q(o,s|π) は**未来の**観測 o と状態 s に対する期待値
   - 「未来の」= まだ実現していない。政策 π を取った**後に**起こること
   - ∴ G(π) の計算には「今」と「後」の区別が**定義的に必要**

2. 一方、VFE F(q) は**過去/現在の**観測 o₁, ..., oₜ で計算する
   - F(q) の入力は既に観測されたデータ
   - ∴ F(q) の計算には「過去」が**定義的に必要**

3. A1 (EFE) を仮定すると G と F が共存する
   - G = 未来を評価する汎関数
   - F = 過去で信念を更新する汎関数
   - **両者の共存 = Past と Future の区別 = Temporality**

**∴ A1 (EFE) を仮定した瞬間に Temporality は数学的に不可避**

循環なし。EFE の定義的性質 (期待値の積分範囲が「未来」) から直接導出。

**強さ**: 🟢 — 定義的導出。循環なし。

**Pezzulo 2021** (83引用) は**補強的根拠**であり、論理的核心ではない。
**Friston 2024** (20引用) も同様に補強。

### 補題I': Scale との独立性 (T⊥H)

1. H (Hierarchical depth) = 空間的ネスト (Scale) — Spisak deep partition
2. T (Temporal depth) = 時間的ネスト — 何ステップ先まで予測するか
3. T を変えても H は変わらない (同じ階層で予測深度だけ変えられる)
4. H を変えても T は変わらない (同じ予測深度で階層だけ変えられる)

**強さ**: 🟢 — 操作的に独立 + **進化的に独立**

(SOURCE: Pezzulo, Parr & Friston 2021, DOI:10.1098/rstb.2020.0531)

Pezzulo 2021 は H と T を**進化において独立に獲得された別々の精緻化**として記述。
これは T⊥H の最も強い根拠 — 同じ FEP 論文で、Friston 自身が著者。

### 定理 (v4.0 修正版)

1. [A0] FEP → VFE F(q) が存在
2. [A1] EFE → G(π) が存在 (d=1 仮定)
3. [補題G'] VFE と EFE は異なる汎関数
4. [補題H'] EFE G(π) は定義から「未来」の積分を要求し、VFE は「過去」のデータを使う → 両方が共存する系では Temporary (Past↔Future) の区別が必然的に生じる
5. [補題I'] T⊥H → Scale とは独立
6. ∴ Temporality: Past↔Future は一意 (d=2)

Q.E.D. (半形式的)

---

## 確信度の改善

| 項目 | v3.0 (循環) | **v4.0 (循環修正)** |
|:-----|:-----|:---------|
| 確信度 | 88% | **92%** |
| 「時間の矢」 | VFE/EFE 定義域 | **同** |
| memoryless の壁 | adaptive = temporal depth > 0 で FEP 内定義 | **「adaptive」を迂回。EFE の数学的定義から直接導出** |
| T⊥H | 進化的に独立な精緻化 | **同** |
| 構造的必然性 | RGM: paths as latent variables | **同** |

---

## /hon 反論義務 (v4.0 更新)

1. ~~時間の矢は FEP 外部~~ → **解消**: VFE/EFE の数学的非対称性で十分
2. ~~adaptive の仮定 (循環論法)~~ → **解消**: v3.0 の「Temporality は adaptive に必要 → adaptive は Temporality を持つ」という循環を断ち切った。v4.0 では EFE G(π) の数学的定義 (未来の積分範囲) から直接 Temporality を導出するため、adaptive という概念を経由しない。
3. ~~EFE 自体の選択性~~ → **解消**: Step② の FEEF 解消と同じ論理 — FEEF も VFE/EFE 区別を前提とする
4. **残る壁**: temporal depth の「最小値」(1 ステップで十分か、複数必要か) — HGK の Temporality は Past↔Future の二極で、depth の量は問わない

---

## Valence との関係

Valence (sgn(−ΔF)) は Temporality (ΔF の時間差) に**依存**する。
これは「Valence は Temporality の上に構築される」関係 — 依存方向は一方通行:

```
Flow (d=0) → EFE (d=1) → Temporality (d=2) → Valence (d=2, Temporality 依存)
```

Valence が d=2 なのは Scale + Temporality の**両方**が仮定に入るからかもしれない。
より正確には:

- Scale: 空間方向の d=2 仮定
- Temporality: 時間方向の d=2 仮定
- Valence: Temporality 上の d=2 仮定 (仮定の距離は同じだが依存関係がある)

---

*DX-014-S4 v3.0 — Temporality 文献強化版 (2026-02-28)*
*v2.0→v3.0: Pezzulo 2021 (83引用) + Friston 2024 (20引用) で「adaptive」を FEP 内定義。進化的 T⊥H。確信度 70%→88%*
