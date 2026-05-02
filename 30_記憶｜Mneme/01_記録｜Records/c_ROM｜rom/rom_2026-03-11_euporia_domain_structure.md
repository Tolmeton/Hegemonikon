---
rom_id: rom_2026-03-11_euporia_domain_structure
session_id: 51b431fd-0087-40a8-ba33-207147e21875
created_at: 2026-03-11 21:24
rom_type: rag_optimized
reliability: High
topics: [Euporía, ドメイン体系, Kalon, Hóros, 圏論, polynomial functors, Markov blanket, Linkage, FEP, 変分原理]
exec_summary: |
  Euporía (AY>0) の4ドメイン体系 {Cognition, Description, Constraint, Linkage} を形式化。
  /ele+ 反駁で5矛盾を検出し修正。Hóros の「FEP前提条件」としての上位性を発見。
  次ステップ: Polynomial functors による Linkage の圏論的定式化。
---

# Euporía ドメイン構造の形式化 {#sec_01_overview .euporia .domain}

> **[DISCOVERY]** Euporía は6座標射影 (How) に加え、適用ドメイン (Where) への射影を持つ

Euporía 原理 (定理³): AY(f) > 0 — 全ての認知操作 f は行為可能性を増やさねばならない。

この原理は Flow (d=1) 上の普遍定理だが、**異なるドメインに制限**すると具体的な規範命題を生む。

```
Euporía: AY(f) > 0  (普遍定理 — Flow d=1)
│
├── 射影軸 (How — 既存): 6座標射影
│   Value / Function / Precision / Temporality / Scale / Valence
│
├── 適用軸 (Where — 新規): ドメイン
│   ├── Cognition   (= HGK 体系)   — 認知主体の行為可能性
│   ├── Description (= Týpos)       — 記述の行為可能性
│   ├── Constraint  (= Hóros)       — 制約の行為可能性 [二重性/前提性]
│   └── Linkage     (= Index PJ)    — 情報チャンク連動の行為可能性
│
└── 到達点 (Fix):
    └── Kalon = Fix(G∘F) of AY — 全ドメイン横断の不動点
```

📖 参照: [axiom_hierarchy.md](../../00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md) L651-735

---

## /ele+ 反駁結果 {#sec_02_refutation .elenchos .critical}

> **[FACT]** 5矛盾を検出。うち3件 MAJOR

| # | 矛盾 | 深刻度 | 解決 |
|:--|:-----|:-------|:-----|
| 1 | Kalon は Euporía の「到達不能な漸近線」なのに「ドメイン」として列挙 | MAJOR | Kalon をドメインから到達点に移動 |
| 2 | Hóros は制約条件であってドメインではない | MAJOR → Creator 裁定で MINOR に | 二重性として維持: 自律的 (ドメイン) + 機能的 (制約条件) |
| 3 | Description ドメインと Value 射影が重複 | MAJOR | Value は Euporía の「何を」、Description は「どの系で」— 異なるカテゴリ |
| 4 | Cognition は全ドメインの上位概念 | MINOR | Cognition = HGK 体系に限定。Týpos も認知だが別ドメイン |
| 5 | 4ドメインの生成原理が不明 (ad hoc) | MINOR → 未解決 | MECE 検証で継続 |

---

## Hóros の階層的位置 {#sec_03_horos .horos .hierarchy .critical}

> **[DISCOVERY]** Hóros は Euporía のドメインではなく、FEP が成立するための**前提条件** (膜)

### Creator の洞察 (2026-03-11)

> 「制約(構造や秩序の維持)は FEP の"前提"では？」
> 「いくら HGK で認知を構造化しようとも、それを保てなければ（例えばそれに違反し続ければ）、HGK は成り立たない。まさに"砂上の楼閣"」

### 構造

```
MaxEnt / 変分推論 (根源)
    │
    ├── 制約 (秩序の維持) ← Hóros の存在論的位置 = FEP の前提条件
    │     ↕ FEP が成立するために必要
    ├── FEP (= MaxEnt|_{自己組織化})
    │     └── Euporía (= FEP|_{行為可能性最大化})
    │           ├── Cognition (HGK)
    │           ├── Description (Týpos)
    │           └── Linkage (Index)
    │
    └── IB Principle (= MaxEnt|_{情報圧縮})
```

> **[RULE]** Hóros の二重性: 内視 = 認知制約のドメイン / 外視 = FEP の前提条件

> **[CONFLICT]** 4ドメイン → 3ドメイン+1前提条件か、4ドメインを維持するか未決

---

## Týpos の公理構造 {#sec_04_typos .typos .axiom}

> **[FACT]** Týpos の公理 A0: f: M → L (多次元意味空間 M から線形トークン列 L への準同型写像)

📖 参照: [constructive_cognition.md](../../00_核心｜Kernel/A_公理｜Axioms/constructive_cognition.md) L37-48

### Helmholtz 対応の問い

> **[OPINION]** Creator: 「Týpos にも Helmholtz と Flow の対応関係が存在するのでは？」

- HGK: Helmholtz (Γ⊣Q) → Flow (d=1) — 自由エネルギー分解 → 認知の流れ
- Týpos: A0 (f: M→L) → ??? — 写像の分解 → 記述の流れ

この問いは未解決。Týpos の「Helmholtz に相当するもの」が何かは、演繹的に導く必要がある。

---

## 圏論的統一の可能性 {#sec_05_category_theory .category .polynomial}

> **[DISCOVERY]** 「変分原理の統一」ではなく「合成性 (compositionality) の統一」として圏論を使う

### 文献ヒット

| 文献 | 年 | cited | 関連性 |
|:-----|:---|:------|:-------|
| Spivak & Niu "Polynomial Functors" | 2023/2025 | 15 | 動的相互作用の圏論的モデル。AY と構造的同型の可能性 |
| Fong & Spivak "Seven Sketches in Compositionality" | 2018 | 116 | ACT 教科書。合成性による統一 |
| Delvenne "Cat Theory for Autonomous Dynamical Systems" | 2019 | 6 | エントロピーの圏論的特徴づけ |
| Das "Categorical Basis of Dynamical Entropy" | 2023 | 7 | 動的エントロピーの圏論化 |

### Polynomial Functor と Euporía の対応

```
Spivak: p = Σ_{i∈I} y^{B_i}
  i = 系の「位置」、B_i = その位置からの「行為の集合」

Euporía: AY = |Hom(after, −)| − |Hom(before, −)|
  = 操作後に可能になる行為 − 操作前に可能だった行為

構造的同型: B_i の増加 ≡ AY > 0
```

> **[OPINION]** チャンクの MB を圏論的変分原理で定式化できれば Euporía|_{Linkage}。
> その定式化が Fix(G∘F) に至れば (展開可能 + 不動点) Kalon。

---

## 未解決の問い {#sec_06_open_questions .open}

> **[CONFLICT]** 以下は全て未解決

1. **ドメイン数**: 4 (Hóros をドメインとして維持) vs 3+1 (Hóros を前提条件に昇格)?
2. **3ドメインの生成原理**: FEP の {μ, s, a, η} からの演繹は可能か?
3. **Polynomial functors**: Euporía の AY を polynomial functor で厳密に定式化できるか?
4. **Týpos の Helmholtz**: A0 の分解構造は何か?
5. **Linkage の MB**: チャンクの Markov blanket を圏論的に定式化した具体的な射は何か?

---

## 次ステップ (2026-03-11 B プラン) {#sec_07_next .next}

> **[DECISION]** B = Polynomial functors で Linkage を定式化する

理由:
- Linkage だけは定義がある (「チャンクの MB を構成する行為」)
- Polynomial functor は Euporía の AY と構造が近い
- 具体的な数式が出れば、他ドメインへの横展開が可能
- Hóros の位置 (A) は B の結果から逆算できる

---

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "Euporía のドメインは何か？"
  - "Hóros は FEP の前提条件か？"
  - "Kalon とドメインの関係は？"
  - "圏論で Euporía を統一できるか？"
  - "Polynomial functors と AY の対応は？"
answer_strategy: "ドメイン体系は §sec_01、Hóros の位置は §sec_03、圏論は §sec_05 を参照"
confidence_notes: "ドメイン数 (3 vs 4) は未決。Hóros の位置は推定 70%。Polynomial functor 対応は仮説段階。"
related_roms: ["rom_2026-03-11_axiom_hierarchy"]
-->
