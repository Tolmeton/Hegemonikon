---
doc_id: "CATEGORICAL_STRUCTURE"
version: "1.0.0"
tier: "KERNEL"
status: "CANONICAL"
created: "2026-03-20"
lineage: "weak_2_category.md + axiom_hierarchy.md §L3 → 独立文書化。formal_derivation.md から圏論解釈部を分離"
---

```typos
#prompt categorical-structure
#syntax: v8
#depth: L2

<:role: 圏論的構造 — HGK 32 実体体系における圏論的解釈の文書。
  設計根拠 (formal_derivation.md) とは独立した解釈層。:>

<:goal: 弱2-圏構造、n-cell の割当て、strict 化拒否の数学的正当性を一箇所に集約する :>

<:context:
  - [knowledge] 設計根拠は formal_derivation.md に分離済み
  - [knowledge] 弱2-圏の既存詳細は weak_2_category.md (377行) にあり、本文書はその統合・更新版
  - [file] formal_derivation.md (CANONICAL — 設計根拠書)
  - [file] weak_2_category.md (REFERENCE — 本文書の前身の一つ)
  - [file] axiom_hierarchy.md (CANONICAL — 32実体体系)
/context:>
```

# 圏論的構造: HGK 体系の弱2-圏解釈

> **位置づけ**: 本文書は HGK の圏論的 **解釈** を記述する。設計根拠 (なぜ 7 座標・24 動詞か) は [formal_derivation.md](formal_derivation.md) を参照。
>
> **主張**: 32 実体を弱2-圏 (bicategory) として解釈すると、体系の操作的意味論が自然に表現される。しかしこの解釈は FEP 導出に **必須ではない** (追加の解釈層として提示)。

---

## §1 なぜ圏論か

### 動機

HGK の 32 実体は以下の構造を持つ:

1. **対象** (認知状態) 間の **射** (認知操作 = 動詞) — 標準的な圏
2. 射と射の間の **変換** (修飾、深度調整) — 高次圏
3. 射の合成が厳密には結合的でない (人間の認知は操作の **順序に依存** する)

3 つ目が鍵。もし射の合成が厳密に結合的なら、通常の 1-圏で十分。
しかし認知操作の非結合性 (order effect) を表現するには、**結合律を自然同型で緩めた** 弱2-圏 (bicategory) が自然な枠組みとなる。

### 圏論的段階

| 段階 | 名称 | 直感 | HGK の位置 |
|:-----|:-----|:-----|:-----------|
| L1 | 前順序圏 (preorder category) | 対象間の半順序 | ✅ 確立済み |
| L2 | 豊穣圏 (enriched category) | 射に厚みがある | ✅ 確立済み |
| L3 | **弱2-圏 (bicategory)** | 合成律が自然同型で成立 | ⭐ **本文書の主題** |
| L4 | BiCat の時間関手 (将来) | L3 が時間発展する | 🟡 L4_helmholtz_bicat_dream.md |

---

## §2 弱2-圏の定義

### 標準的定義 (Bénabou 1967)

弱2-圏 (bicategory) $\mathcal{B}$ は以下から構成される:

| 要素 | 定義 | 例 |
|:-----|:-----|:---|
| 0-cell | 対象 | 認知状態 |
| 1-cell | 0-cell 間の射 | 認知操作 (48: 36 Poiesis + 12 H-series, v5.3) |
| 2-cell | 1-cell 間の射 | 修飾 (Dokimasia) / 深度切替 |
| Associator α | (f⊗g)⊗h ≅ f⊗(g⊗h) | 「認知の順序効果を記録する自然同型」 |
| Left/Right Unitor λ,ρ | id⊗f ≅ f ≅ f⊗id | 「何もしない操作は恒等的」 |

> ⚠️ 鍵: Associator α が **等号ではなく同型**。(f⊗g)⊗h と f⊗(g⊗h) は同値だが等しくない。
> この差分 α が認知的に意味を持つ: **操作の順序を変えたときの認知コスト** をエンコードする。

### コヒーレンス条件

- **Pentagon identity**: 結合子を使った再括弧化が整合的
- **Triangle identity**: 単位子との整合性

形式的には:

```
Let A₁, A₂, A₃, A₄ be 0-cells and f: A₁→A₂, g: A₂→A₃, h: A₃→A₄ be 1-cells.

Pentagon coherence:
((f⊗g)⊗h)⊗k → (f⊗(g⊗h))⊗k → f⊗((g⊗h)⊗k)
     ↓                                    ↓
(f⊗g)⊗(h⊗k) ————→ f⊗(g⊗(h⊗k))
```

**[推定 70%] 80%** — Pentagon identity の認知的検証は未完了。形式的定義は標準数学だが、HGK の具体的 0-cell/1-cell 上でのコヒーレンス検証が残る。

---

## §3 HGK での n-cell 割当て

### 二層構造

HGK の弱2-圏は **二層** の bicategory として構成される。Scale 座標 (Micro↔Macro) の操作化:

**[推定 70%] 78%** — 二層構造は Scale 座標 (Micro↔Macro) を n-cell の粒度として操作化する自然な構成。Macro 層の 0-cell 数 = 48 は Poiesis (36) + H-series (12) から確定 (v5.3) [確信 90%]。Micro 層の 64 Dokimasia 状態はパラメータ空間の離散化であり、「64」の根拠 (6座標間の直積パラメータ) は組合せ論的に健全だが、全 64 状態が認知的に弁別可能かの検証は未完了 (sloppy spectrum 議論と関連)。

| 層 | 0-cell | 1-cell | 2-cell |
|:---|:-------|:-------|:-------|
| **Macro** (俯瞰) | 48 認知操作 (36 Poiesis + 12 H-series) | WF 遷移 (CCL 演算子 ~, *, >>) | WF パラメータ調整 |
| **Micro** (精密) | 64 Dokimasia 状態 | 48操作の Dokimasia 内実装 | 深度レベル切替 (L0-L3) |

### 0-cell の解釈

**Macro 層**: 各 0-cell は 48 認知操作の一つが active な認知状態
(POMDP の hidden state の粗い離散化と解釈可能)
- 0-cell の数: 48 (固定, v5.3)

**Micro 層**: 各 0-cell は Dokimasia の一状態
- 64 Dokimasia = 6修飾座標間の直積パラメータから生成されるコンテキスト
- 常に 24 動詞のいずれかの内部にいることを意味する

### 1-cell: 認知遷移

| 1-cell の種類 | Macro | Micro |
|:-------------|:------|:------|
| 基本遷移 | /noe → /bou (認識→意志) | 同一動詞内の状態遷移 |
| 合成遷移 | /noe >> /bou >> /ene (CCL 合成) | — |
| 並列遷移 | /noe * /ele (並列実行) | — |
| 条件遷移 | /noe ~ /bou (遷移条件付き) | — |

### 2-cell: 修飾と変換

2-cell は 1-cell 間の変換。2 つの認知遷移の「差分」をエンコードする:

| 2-cell の種類 | 例 | 意味 |
|:-------------|:---|:-----|
| 深度変更 | /noe → /noe+ | L2→L3 への深化 (同一動詞の異なる粒度) |
| Dokimasia 修飾 | /noe[Pr:C] → /noe[Pr:U] | 精度パラメータの変更 |
| 族内代替 | /noe ⇒ /bou (Telos 族内) | 同一座標の極性反転 |

---

## §4 Strict 化の拒否

### Strict 2-圏との違い

Strict 2-圏 = Associator α が恒等。すなわち (f⊗g)⊗h = f⊗(g⊗h)。

**Strict 化定理** (Mac Lane coherence, Gordon-Power-Street 1995): 任意の bicategory は strict 2-category と biequivalent。

→ なぜ strict 化しないのか？

### 拒否の根拠

**strict 化すると失われるもの**: Associator α が持つ情報。

HGK において α は「操作の順序変更に伴う認知コスト」を表す:

| 事例 | 非等価性の実証 |
|:-----|:---------------|
| (/noe ~/ele) ~/ene ≠ /noe ~(/ele ~/ene) | (認識→批判)→実行 ≠ 認識→(批判→実行): 左は「批判済みの認識を実行」、右は「認識後に批判的実行」。認知的に異なるアフォーダンスを持つ |
| (/ske ~/sag) ~/pei ≠ /ske ~(/sag ~/pei) | (発散→収束)→実験 ≠ 発散→(収束→実験): 左は「確定仮説の実験」、右は「発散中に収束的実験を開始」。実験設計が異なる |

### 数学的正当性

1. **Biequivalence は equality ではない**: strict 化定理は「同型な strict 2-category が存在する」と言うが、biequivalence は全ての構造を保存しない
2. **α の情報は計算において使われる**: HGK の CCL インタプリタは括弧位置 (結合順序) をパーサーが明示的に追跡する
3. **計算量の差**: α を保持するコストは O(n) の追加メモリだが、strict 化で失われる認知情報の再構成は一般に不可能

> Gordon, Power, Street 1995 からの引用 (Section 5.6):
> "Every bicategory is biequivalent to a strict 2-category, but this biequivalence need not preserve the coherence information that may be significant for applications."

**[推定 70%] 80%** — strict 化拒否の数学的議論は健全だが、「α の情報が HGK で operationally significant か」の実証的検証は部分的。CCL インタプリタでの括弧追跡は実装済みだが、α の具体的測定は未完了。

---

## §5 文脈マッピング: 遊学エッセイとの対応

### エッセイ vs HGK の n-cell

遊学エッセイシリーズでは独自の n-cell 割当てを行っている。HGK 体系との関係:

| n-cell | エッセイの割当て | HGK の割当て | 関係 |
|:-------|:----------------|:-------------|:-----|
| **0-cell** | 法則 (Nomoi) | 認知状態 (Poiesis) | **異なるレベルの記述** |
| **1-cell** | 原理 (Stoicheia) | 認知操作 (WF 遷移) | エッセイは「構造」、HGK は「操作」を見る |
| **2-cell** | 行為 (Praxis) | 修飾 (Dokimasia) | 概念的には近い |

> ⚠️ **v5 /ele+ 修正点 #5**: エッセイと HGK で n-cell の割当てが異なるのは矛盾ではない。
> 同一の bicategory を **異なる観点** から記述している:
> - エッセイ: **存在論的** 視点 — 体系の構成要素 (法則→原理→行為) を n-cell として見る
> - HGK: **操作論的** 視点 — 認知の操作 (状態→遷移→修飾) を n-cell として見る
>
> 両者の間のマッピングは **関手** (functor) として定式化可能だが、identity ではない。

---

## §6 Helmholtz BiCat 関手 (L4 展望)

### 概要

L3 の bicategory に時間変動を加えた **L4 構造** の展望:

$$\mathcal{F}: \text{Time} \to \text{BiCat}$$

- $\Gamma_T$ (不可逆学習): gradient 成分の時間発展。Handoff 間の構造変化
- $Q_T$ (循環パターン): solenoidal 成分の時間発展。WF 使用パターン

### Drift 指標

$$\text{Drift} = \frac{\|\Delta\Gamma\|}{\|\Delta\Gamma\| + \|\Delta Q\|}$$

- Drift ≈ 1: 主に不可逆学習 (構造変化)
- Drift ≈ 0: 主に循環パターン (定常運用)

**[仮説 45%] 50%** — L4 は理論的構想段階。数学的には well-defined だが、実装・検証は L4_helmholtz_bicat_dream.md に委ねる。

---

## §7 随伴対と Hom 構造

### 12 主要随伴対

axiom_hierarchy.md の 12 随伴対は L1 前順序圏の構造:

$$L \dashv R: \text{Explore} \rightleftarrows \text{Exploit}$$

| # | 左随伴 (L) | 右随伴 (R) | 座標 |
|:--|:-----------|:-----------|:-----|
| 1 | Noēsis (認識) | Zētēsis (探求) | Telos |
| 2 | Energeia (実行) | Boulēsis (意志) | Telos |
| 3 | Skepsis (発散) | Synagōgē (収束) | Methodos |
| 4 | Peira (実験) | Tekhnē (適用) | Methodos |
| 5 | Katalēpsis (確定) | Epochē (留保) | Krisis |
| 6 | Proairesis (決断) | Dokimasia (打診) | Krisis |
| 7 | Analysis (分析) | Synopsis (俯瞰) | Diástasis |
| 8 | Akribeia (精密) | Architektonikē (展開) | Diástasis |
| 9 | Bebaiōsis (肯定) | Elenchos (批判) | Orexis |
| 10 | Prokopē (推進) | Diorthōsis (是正) | Orexis |
| 11 | Hypomnēsis (想起) | Promētheia (予見) | Chronos |
| 12 | Anatheōrēsis (省み) | Proparaskeuē (仕掛け) | Chronos |

これらは L3 bicategory では 1-cell 間の adjunction として定式化される。

### Hom-set の豊穣

**[推定 70%] 75%** — Hom-set が Dokimasia パラメータで豊穣されるという構成は数学的に well-defined (豊穣圏の標準的構成)。64 パターンの全てが射の修飾として独立に機能するかは §3 の sloppy spectrum 問題と共有: 実効次元 d_eff < 64 の可能性を排除できない。形式的な豊穣圏の構成自体は [確信 90%] だが、具体的な Dokimasia 空間の「豊かさ」の程度が推定値。

L2 の豊穣圏として: 各 Hom-set $\text{Hom}(A, B)$ は修飾パラメータ (Dokimasia) で豊穣される。
- 射 f: A → B に対し、$\text{Hom}(A, B)$ は f の「どのような修飾のもとで実行するか」の空間
- 修飾の組合せ = Dokimasia の 64 パターン

---

## §8 残存する課題

| # | 課題 | 確信度 | 必要なアクション |
|:--|:-----|:-------|:----------------|
| 1 | Pentagon identity の HGK 具体的検証 | [推定 70%] 70% | 具体的 0-cell/1-cell 上でのペンタゴン図式の検証 |
| 2 | α (Associator) の計量化 | [仮説 45%] 50% | 操作順序変更の認知コストの定量的測定法の開発 |
| 3 | L4 の実装 | [仮説 45%] 40% | Time → BiCat 関手の具体的構成 |
| 4 | Macro-Micro 間の関手 | [推定 70%] 75% | 二層 bicategory 間の関手の形式的定義 |
| 5 | エッセイ→HGK 関手 | [推定 70%] 65% | 存在論→操作論のマッピングの厳密化 |

---

## §9 参照文献

| 文献 | 接続 |
|:-----|:-----|
| Bénabou 1967 | Bicategory の原定義 |
| Mac Lane 1998 | Coherence theorem (strict 化定理の原典) |
| Gordon, Power, Street 1995 | Bicategory の strict 化。biequivalence の限界 |
| Leinster 2003 | 高次圏の概観 |
| Smithe, Tull & Kleiner 2023 | Theorem 46: VFE 加法分解 (§7 随伴対の基礎) |
| 遊学エッセイシリーズ | n-cell の存在論的割当て (§5 対応表) |

---

*categorical_structure v1.0 — formal_derivation.md からの圏論解釈分離版。2026-03-20*
