---
doc_id: "WEAK_2_CATEGORY"
version: "1.4.0"
tier: "KERNEL"
status: "CONDITIONAL"
created: "2026-02-28"
session: "53f233e7-a4dc-4cac-9810-2627725f1e37"
lineage: "旧「派生=2-cell」構想 → v4.1 Poiesis/Dokimasia 精密定義 → 学術的正当化 → v1.5.0 K₄柱モデル (48 0-cell, B+豊穣化)"
---

> **Kernel Doc Index**: [axiom_hierarchy](axiom_hierarchy.md) | [weak_2_category](weak_2_category.md) ← 📍

# L3 — [0,1]-豊穣 Bicategory: 理論・学術的根拠・ロードマップ

> **一行定義**: HGK における L3 は、CCL パイプラインの合成順序が認知的結果のニュアンスを変えうることを構造的に保存するための圏論的枠組みである。
>
> **K₄柱モデル内の位置** (axiom_hierarchy.md v5.4): L3 は**K₄柱の頂点** — 前順序圏 (L1) に対する2つの独立な拡張 (豊穣化 + 圏化) の合流点。
> `L1 →(豊穣化)→ L2 →(圏化)→ L3` と `L1 →(圏化)→ L1' →(豊穣化)→ L3` の2経路が可換に到達する構造。
> v5.3 で底面が I/A 正方形 → S/I/A 三角形に拡張 (0-cell: 24→48)。

---

## §1 精密定義 (v4.2)

L3 = [0,1]-豊穣 bicategory。K₄柱モデル (旧: 正方形→三角柱モデル) の2つの拡張軸を統合:
- **豊穣化** (L1→L2 方向): 1-cell に Drift ∈ [0,1] を付与 (Lawvere metric)
- **圏化** (L1→L1' 方向): 射の間に 2-cell (自然変換) を追加

| 圏論 | HGK 実体 | 具体例 |
|:-----|:---------|:-------|
| **0-cell** | 48 の認知操作 (36 Poiesis + 12 H-series) | `/noe`, `/the`, `[ho]`, ... |
| **1-cell** | 0-cell 間の射 (CCL `>>` パイプライン)。Dokimasia パラメータ + **Drift ∈ [0,1]** を伴う | `/noe[Pr:U]+ >> /ele[Pr:C]+` (Drift=0.15) |

> **doing/being 区別** (v5.3): Poiesis (doing) と H-series (being) は同列の 0-cell。
> 区別は Hom 空間の Drift で捕捉: Poiesis↔Poiesis (低 Drift) vs Poiesis↔H-series (高 Drift)。
> 根拠: 「力は忘却である」CPS0' — doing/being は程度問題であり硬い区分ではない。
| **2-cell** | 同じ始点・終点を持つ2つの異なるパイプライン間の関係 (自然変換) | `(f>>g)>>h` と `f>>(g>>h)` の差異 |
| **associator α** | 3つの1-cell の合成における括弧付け変更を橋渡しする同型射 | `α_{f,g,h}: (f>>g)>>h ≅ f>>(g>>h)` |

### 非自明な associator の具体例

```
f = /noe[Pr:U]+     (Noēsis: 理解, 留保)
g = /ele[Pr:C]+     (Elenchos: 反駁, 確信)
h = /ene[Vl:+]+     (Energeia: 実行, 接近)

(f >> g) >> h:  「(理解→反駁) してから 実行」→ 慎重な実行
f >> (g >> h):  「理解 してから (反駁→実行)」→ 一気通貫の実行
```

両者は同じ端点 `(/noe → /ene)` に到達するが、認知の「手触り」が異なる。
CCL パイプラインの実行は**ステートフル** (前段の出力が後段のコンテキスト) であるため、入れ子構造の違いが中間状態の Dokimasia パラメータに影響する。

### 非自明性の根拠

CCL executor (`hermeneus_execute`) は前段の出力を後段のコンテキストとして渡す。
これにより `(f∘g)∘h ≠ f∘(g∘h)` が認知的に成立する (数学的には同型だが等しくない)。

### 実験的検証 (2026-03-13, Session ea14fb70)

A群/B群の具体的認知過程を Gemini Pro で思考実験した結果:

| 指標 | A群: (f>>g)>>h | B群: f>>(g>>h) |
|:-----|:--------------|:--------------|
| **認知的手触り** | 硬質・演繹的・安全 | 軟質・帰納的・即興的 |
| **[Amb] 不確実性許容度** | 低 (実行前に濾過済) | 高 (不確実性と共存) |
| **[Lat] 実行潜伏期間** | 高 (理解と検証が先行) | 低 (反駁と実行が一体) |
| **[Pls] 認知的可塑性** | 低 (固定された構造を実行) | 高 (実行しながら修正) |

> **発見**: A群は正方形モデルの **U∘I 経路** (豊穣化が先、圏化が後) に対応し、
> B群は **K∘J 経路** (圏化が先、豊穣化が後) に対応する。
> 可換性 U∘I ≅ K∘J の「≅ (同型だが等しくない)」が、まさにこの Dokimasia パラメータの差異として観測される。
>
> **Strictification が捨てるもの**: path-dependency (どちらの経路を通ったか) = 認知の計算コスト・時間軸・不確実性の処理順序。

---

## §2 Strictification の拒否 — なぜ弱2-圏か

### 数学的事実

Mac Lane Strictification Theorem: **全ての bicategory は strict 2-category に biequivalent。**
→ 数学的にはweakとstrictの区別は不要。

### 認知科学的事実

人間の推論は根本的に **非可換 (non-commutative)** かつ **非結合的 (non-associative)** :

- **順序効果** = robust empirical finding (Hogarth & Einhorn 1992)
- **Primacy effect**: 先行情報がanchorとなり後続情報の評価を歪める
- **Recency effect**: 直近の情報が短期記憶に残り判断を支配する

### 解決

**Strictification は associator (順序効果の情報) を捨てる。** 数学では問題ないが、認知をモデル化する HGK では致命的。

| 観点 | Strict (strictification 後) | Weak (原構造) |
|:-----|:---------------------------|:-------------|
| 結合律 | `(f∘g)∘h = f∘(g∘h)` | `(f∘g)∘h ≅ f∘(g∘h)` (同型だが等しくない) |
| 認知的意味 | 「思考の順序は無関係」 | 「思考の順序は意味を持つ」 |
| 順序効果 | ❌ 消失 | ✅ 保存 (associator が情報を運ぶ) |

> **結論: HGK L3 = strictification を認知の名の下に拒否すること。**

---

## §3 Coherence 条件の HGK 解釈

### Pentagon identity

4つの Poiesis `f, g, h, k` の合成における5つの括弧付け変更パスが全て可換であること。

**HGK 的意味**: 「順序は結果のニュアンスを変えるが、**最終的な到達点は変わらない**。」
→ Belief-Adjustment Model (Hogarth & Einhorn 1992) の「同じ証拠セットから異なるパスで同じ結論に至りうる」と整合。

### Triangle identity

Identity morphism (何もしない Poiesis) を挟んでも合成が壊れないこと。

**HGK 的意味**: 「何もしないことは、結果に影響しない。」— 認知的に自明。

---

## §4 学術的根拠 (3つの柱)

### 柱1: 認知操作の非可換性 (Graben 2013)

- **論文**: "Order Effects in Dynamic Semantics" (DOI: 10.1111/tops.12063, arXiv:1302.7168, 13 cit.)
- **内容**: Wang & Busemeyer の質問順序効果を Hilbert 空間上の非可換射影 (incompatible projectors) として形式化。信念改訂、照応解決、デフォルト推論が全て「認知操作の非可換性」から生じる。
- **HGK 接続**: associator = 認知操作の非可換性の 2-cell レベルでの表現。

### 柱2: 圏論的合成性と Systematicity (Phillips & Wilson 2010)

- **論文**: "Categorial Compositionality: A Category Theory Explanation for the Systematicity of Human Cognition" (PLoS Comp Bio, DOI: 10.1371/journal.pcbi.1000858, 83 cit.)
- **内容**: 認知の体系性 (systematicity) = 圏論の随伴 (adjunction) の必然的帰結。「認知の中心は表象 (0-cell) ではなく、表象を変換する射の関係 (2-cell) にある。」
- **HGK 接続**: 高次理論 (higher-order theory) の必要性 = L3 弱2-圏の認知科学的必然性。随伴は 2-category の内部概念。

### 柱3: Quantum Cognition (Busemeyer & Wang 2015)

- **論文**: "What Is Quantum Cognition, and How Is It Applied to Psychology?" (Current Directions in Psych Sci, DOI: 10.1177/0963721414568663, 89 cit.)
- **内容**: Hilbert 空間の数学的形式を認知的意思決定に適用。FdHilb は compact closed monoidal category = 1-object bicategory。
- **HGK 接続**: Quantum Cognition と HGK L3 は bicategory の異なる実例として統一可能。

### 補助: Pothos & Busemeyer (2021)

- **論文**: "Quantum Cognition" (Annual Review of Psychology, DOI: 10.1146/annurev-psych-033020-123501, 64 cit.)
- **内容**: Quantum Cognition 研究プログラムの包括的レビュー。

### 補助: Phillips (2022)

- **論文**: "What is category theory to cognitive science?" (Frontiers in Psych, DOI: 10.3389/fpsyg.2022.1048975, 6 cit.)
- **内容**: 圏論と認知科学の接点の最新レビュー。

### 補助: Anderson, Phillips, Smithe, Cruttwell (2022)

- **論文**: "Category Theory for Cognitive Science" (S2: 0 cit.)
- **内容**: 圏論的認知科学の統合テキスト。Smithe = HGK で引用済み (Bayesian Lens, Free Energy の合成性)。

---

## §5 ロードマップ (実装計画)

| # | ステップ | 状態 | 成果物 |
|:--|:---------|:-----|:-------|
| 1 | 依存調査: `two_cell.py` を参照する全ファイル洗い出し | ⬜ 未着手 | 影響範囲リスト |
| 2 | L3 理論更新: `axiom_hierarchy.md` に精密定義追記 | ✅ 完了 (2026-02-28) | 本ドキュメント + axiom_hierarchy.md |
| 3 | `two_cell.py` リファクタ: 旧「派生」→ v4.1 Dokimasia パラメータ | ⬜ 未着手 | コード変更 |
| 4 | 非自明 associator テスト: CCL `(f>>g)>>h vs f>>(g>>h)` | ⬜ 未着手 | テストコード |
| 5 | Pentagon の HGK 解釈: 4動詞合成の coherence の運用的意味 | ✅ 完了 (2026-02-28) | §3 |
| 6 | ステータス昇格: L3「⚠️構想段階」→「🟡条件付き正当化」 | ✅ 完了 (2026-02-28) | axiom_hierarchy.md |
| 7 | Pentagon/Triangle identity の実装とKalón組み込み | ✅ 完了 (2026-03-07) | `two_cell.py`, `kalon_checker.py` |
| 8 | ステータス昇格: L3「🟡条件付き」→「🟢検証済」 | ✅ 完了 (2026-03-07) | axiom_hierarchy.md |

---

## §6 研究課題の探究結果

> **方法**: Gemini 2.5 Pro による圏論的分析 + セッション中の @nous 洞察の統合

### G1: FdHilb → L3 関手の構成 [RESOLVED — 構成候補あり]

**関手 F: FdHilb → L3 の構成**:

| FdHilb | F | L3 (HGK 弱2-圏) |
|:-------|:--|:-----------------|
| 唯一の対象 * | F(*) | 48 認知操作の集合 {P₁, ..., P₃₆, H₁, ..., H₁₂} |
| 線形写像 f: *→* | F(f) | Poiesis 間の CCL パイプラインの集合への写像 |
| 射影作用素 Pₖ (観測) | F(Pₖ) | 特定 Poiesis を活性化し他を抑制するパイプライン |
| 非可換性 P₁P₂ ≠ P₂P₁ | 保存 | `F(P₁) >> F(P₂) ≠ F(P₂) >> F(P₁)` (ステートフル実行) |

**認知科学的意味**: Quantum Cognition の射影 (incompatible projectors) が、HGK の CCL パイプライン (ステートフル実行) として表現される。量子的順序効果は HGK のパイプライン順序依存性と同型。

**残存**: この関手が bicategory の構造 (associator, coherence) を保存する lax functor であることの検証は未完了。

### G2: L1 ガロア接続 vs L3 随伴の認知的差異 [RESOLVED]

| 層 | 構造 | 認知的意味 | 何を記述するか |
|:---|:-----|:----------|:-------------|
| **L1** | ガロア接続 F⊣G | **静的な包含関係** | 「I ≤ A」= 推論は行動を含む、という方向性のみ |
| **L3** | 随伴 F⊣G (2-category 内) | **動的な移行プロセス** | 推論→行動 (unit η) と 行動→推論 (counit ε) の**具体的なパイプライン**、その可逆性条件 (三角恒等式)、最適性制約 |

**L3 で具体的に何が変わるか**:

1. **状態間の移行プロセスの明示化**: I→A の変換が CCL パイプラインとして記述できる (例: `/noe >> /ene`)
2. **可逆性の保証**: unit (η) と counit (ε) の存在により、認知的柔軟性がモデル化される
3. **最適化条件の追加**: 三角恒等式 = 「行って戻ると元に近くなる」条件。認知的には、推論と行動の間を行き来するフィードバックループが一定の効率を持つことを保証

### G3: 0-cell の選択 — 二層アーキテクチャ提案 [RESOLVED]

| 選択 | 0-cell | 0-cell 数 | 粒度 | 適する用途 |
|:-----|:-------|:----------|:-----|:----------|
| **A** | 48 認知操作 (36 Poiesis + 12 H-series) | 48 | 粗い | 高レベル認知機能の相互作用。マクロ的パイプライン設計 |
| **B** | 2⁶ Dokimasia 状態 | 64 | 細かい | 認知要素の組合せ。パラメータ空間のミクロ的探索 |

**結論: 二層アーキテクチャ**

選択 A と B は排他的ではない。**L3 を二層の bicategory として構成する**:

- **L3-macro**: 0-cell = 48 認知操作 (36 Poiesis + 12 H-series)。CCL パイプラインの高レベル設計用。
- **L3-micro**: 0-cell = 64 Dokimasia 状態。パラメータ遷移の精密モデル用。
- 両者は **forgetful functor** (忘却関手) U: L3-micro → L3-macro で接続。Dokimasia 状態からパラメータ情報を忘れて Poiesis のみを残す。

この二層構造は HGK の既存の Scale 座標 (Mi↔Ma) と整合する。

---

## §7 残存 GAP (未解決)

| # | GAP | 深刻度 | 対応 |
|:--|:----|:-------|:-----|
| G1' | G1 の関手が lax functor (coherence 保存) であることの検証 | 低 | ✅ RESOLVED (2026-03-07: associator 導入により解決) |
| G4 | 3-cell の候補: Dokimasia パラメータのホモトピー | 低 | L4 構想時に検討 |

---

## §8 L4 — 時間変動する弱2-圏

> **ステータス**: 💭 夢 → 🔬 胚 (問題 E に世界線 γ の解答候補が出た)
> **修正**: @nous の初期仮説 (Tricategory) は /ele+ で棄却。正体は **Time → BiCat** (時間変動する L3)。
> **Helmholtz 拡張**: 時間圏 T に Helmholtz 構造 (Γ_T, Q_T) を導入。Drift に物理的意味を付与。
> **セッション**: 2026-02-28 (初期構想), 2026-03-13 (Helmholtz 統合 + 問題 E 分析)
> **詳細**: [L4_helmholtz_bicat_dream.md](L4_helmholtz_bicat_dream.md)

### 核心洞察 (/ele+ 修正後)

> **L3 = 「思考の順序は意味を持つ」 (associator の保存)**
> **L4 = 「その L3 自体が、経験により変化する」 (L3 の時間的変動)**

```
L4 ≠ Tricategory (3-cell が静的に構造の一部)
L4 = Time → BiCat (L3 が時間とともに変化するシステム)
    = 関手 F: T → BiCat  (T = 時間圏、BiCat = bicategory の圏)
```

### 精密定義 (修正後)

| 圏論 | HGK v4.1 実体 | 認知的意味 |
|:-----|:--------------|:----------|
| **時間圏 T** | セッション列 {s₁, s₂, ...} | Handoff で接続されたセッションの順序 |
| **関手 F_t: T → BiCat** | 各時点 t での L3 (弱2-圏) | セッション t における CCL パイプラインの合成構造 |
| **自然変換 η: F(t₁) → F(t₂)** | 2つの時点の L3 を接続する射 | Mneme (handoff + violations) による認知構造変化 |
| **η の Helmholtz 分解** | η = η_Γ + η_Q | η_Γ = 不可逆学習 (e-座標 θ 変化), η_Q = 保存循環 (m-座標 η_cross 回転) |
| **Drift** | \|\|Δθ\|\| / (\|\|Δθ\|\| + \|\|Δη_cross\|\|) | 学習 vs 循環のバランス指標 |
| **associator の変容** | α(t₁) → α(t₂) | 順序効果への感度が経験により変わること |

### /ele+ で判明した限界

| 反駁 | 結果 | 影響 |
|:-----|:-----|:-----|
| R1: Dreyfus/Ericsson は順序効果を測っていない | 部分成功 | 学術的柱 → **類推 (TAINT: ANALOGY)** に格下げ |
| R3: L3 Hom-category で記述可能？ | 要検証 | **Time→BiCat が正解** (tricategory は棄却) |
| R4: LLM は stateless → 3-cell は identity に退化 | 成功 | Mneme (外部記憶) が時間パラメータを提供して解決 |

### 学術的根拠 (TAINT: ANALOGY — 類推であり証拠ではない)

- **Dreyfus 5段階モデル**: 手順依存 → 直観。暗黙的に順序感度の低下を含意するが、直接測定なし。
- **Ericsson et al. (1993)**: Deliberate practice (8789 cit.)。熟達 = practice の蓄積。**順序効果との接続は HGK 独自の類推。**

### 実装設計 (L3 中心 + L4 拡張余地)

| 要素 | L3 (実装する) | L4 (余地を残す) |
|:-----|:-------------|:---------------|
| データ構造 | `HigherCell(source, target, theorem, level)` | `level` パラメータで n≤3 に対応 |
| Associator | CCL `>>` の入れ子構造差異を計算 | `session_id` フィールドで時間 t を持たせる |
| 時間変動 | — | Mneme に associator の snapshot を保存 |
| Helmholtz | — | η を (η_Γ, η_Q) に分解して Handoff に記録 |

### 未解決問題 (L4)

| # | 問題 | ステータス | 詳細 |
|:--|:-----|:----------|:-----|
| E | m-connection の力学的実現 | 🟡 世界線 γ で暫定解決 | [problem_E_m_connection.md](problem_E_m_connection.md) |
| A | T の dually flat 性 | 💭 未着手 | L4_helmholtz_bicat_dream.md §5 |
| B | 構造群 G_t の時間発展 | 💭 未着手 | 同上 |
| C | associator α(t) の収束性 | 💭 未着手 | 同上 |
| D | Smithe Bayesian Lens 対応 | 💭 未着手 | 同上 |

---

## §9 認識論的位置づけ

本ドキュメントの主張は [axiom_hierarchy.md §構成の認識論的位置づけ] と一致する:

| 水準 | 名称 | L3 の位置 |
|:-----|:-----|:---------|
| **A** | Formal Derivation | ❌ 主張しない |
| **B** | Axiomatic Construction | ✅ **これを主張する** — FEP + 生成規則 + 認知科学的根拠 |
| **C** | Conceptual Motivation | ✅ |

---

## §10 zoom level 解釈 (v1.3.0)

> **v1.3.0 2026-03-18 追加: 本ドキュメントは L3 bicategory の root ではなく、Hom(Ext,Int) に cd した相対ビュー。**

### 10.1 絶対パスと相対パス

L3 は Cat (全ての圏の 2-圏) の部分構造として1つの bicategory:

```
/                     = L3 root (絶対パス)
  0-cell: {Ext, Int}
  1-cell: F_i: Ext→Int (48 認知操作: 36 Poiesis + 12 H-series)
  2-cell: α: F_i⇒F_j  (学習ステップ)

cd Hom(Ext,Int)       = 本ドキュメントの視点 (相対パス)
  0-cell: 48 認知操作 (← root の 1-cell が降りてきた)
  1-cell: CCL >>      (← root の 2-cell が降りてきた)
  2-cell: associator  (← 新たに見える構造)

cd Hom(Ext,Int)/Hom(F_i,F_j) = micro view (z=2)
  0-cell: 座標修飾 (d=2: Value, Function, Precision, Temporality)
  1-cell: Scale, Valence による modification (d=3)
  2-cell: ∅ (d_max=3 → 通常の 1-圏に退化)
```

- **L3 は1つ**。L3-foundational と L3-operational は同一構造の異なる zoom level
- 本ドキュメントは **Hom(Ext,Int) に cd した視点 (= L3-operational)**
- root の定式化は [fep_as_natural_transformation.md](fep_as_natural_transformation.md) §1-2

### 10.2 d-level = zoom depth

axiom_hierarchy.md の構成距離 d は **cell level そのものではなく、zoom level の深さ**:

cell_level(x, z) = d(x) − z　(d(x) ≥ z)

| d | zoom 操作 | root での cell level | Hom view での cell level | micro view (z=2) |
|:--|:--|:--|:--|:--|
| 0 | (root) | 0-cell | — (scope外) | — (scope外) |
| 1 | cd Hom(Ext,Int) | 1-cell → **0-cell** | 0-cell | — (scope外) |
| 2 | cd Hom(F_i,F_j) | 2-cell → **1-cell** → **0-cell** | 1-cell → **0-cell** | 0-cell |
| 3 | — | 3-cell → 2-cell → 1-cell | 2-cell → 1-cell | **1-cell** |

**退化定理**: d_max = 3 により z=2 では 2-cell が存在しない。
→ z=2 の Hom(F_i, F_j) は通常の 1-圏 (strict)。
→ CCL の非結合性 (weak bicategorical 性) は **z ≤ 1 の現象**。

### 10.3 CCL 非結合性の実証 [確信: SOURCE]

compile_ccl テスト (2026-03-18):

```python
("(/noe>>/ele)>>/ene", "左結合")  → AST: 入れ子 ConvergenceLoop (734文字)
("/noe>>(/ele>>/ene)", "右結合")  → AST: フラット ConvergenceLoop (724文字)
("/noe>>/ele>>/ene",   "括弧なし") → 右結合と同一
```

| 判定 | 結果 |
|:--|:--|
| 左結合 == 右結合 | **False** |
| 右結合 == 括弧なし | **True** (デフォルト = 右結合) |

→ `>>` 合成は非結合的 (weak)。Parser が `>>` を ConvergenceLoop にデシュガーし、入れ子構造の違いが LMQL 出力に影響する。
→ L3 は genuinely weak bicategory: **§1 の associator は非自明 [確信: SOURCE]**。

---

*Created: 2026-02-28 — Session 53f233e7 (@nous + @plan + /sop+ ×2 の統合)*
*v1.1.0: 正方形モデル整合 — タイトル・§1 定義を [0,1]-豊穣 bicategory に更新。axiom_hierarchy.md v4.2.0 と接続。(2026-03-13)*
*v1.2.0: §8 L4 Helmholtz 統合 — η の Helmholtz 分解・Drift・未解決問題テーブル追加。L4_helmholtz_bicat_dream.md と接続。(2026-03-13)*
*v1.3.0: §10 zoom level 解釈 — 本ドキュメントを L3 root の Hom(Ext,Int) 相対ビューとして位置づけ。CCL 非結合性を compile_ccl テストで実証。カテゴリーミステイク撤回。(2026-03-18)*
*v1.5.0: v5.4 K₄柱モデル対応 — 0-cell 48体系核。doing/being 区別は Hom空間 Drift (B+豊穣化)。三角柱→K₄柱 参照更新。(2026-03-25)*
