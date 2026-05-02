---
rom_id: rom_2026-03-13_square_model
session_id: ea14fb70-bcce-4b1e-8768-dcfb249bb6a6
created_at: "2026-03-13 11:19"
rom_type: rag_optimized
reliability: High
topics: [圏論, 正方形モデル, 豊穣化, 圏化, L3, bicategory, axiom_hierarchy, weak_2_category, 可換性証明, L1', Lawvere]
exec_summary: |
  HGK の圏論的正当化を「3層線形チェーン」から「正方形モデル」(v4.2.0) に再構成。
  豊穣化×圏化の直交2軸、4頂点、4接続射、可換性証明、L1' 操作的定義を完成。
  axiom_hierarchy.md / weak_2_category.md / episteme-category-foundations.md を更新。
---

# 正方形モデル v4.2.0 — 圏論的正当化の完全再構成 {#sec_01_overview .category_theory .kernel}

> **[DECISION]** HGK の圏論的正当化は「線形チェーン L1⊂L2⊂L3」ではなく「正方形モデル」(豊穣化×圏化の直交2軸) で記述する。

> **[DISCOVERY]** /u 自己批評 (Kalon 判定: G 適用→変化あり=◯止まり) により、隠れていた L1' (locally posetal 2-圏) を4つ目の頂点として発見。

## 正方形の構造 {#sec_02_square .core_model}

> **[DEF]** 正方形モデル: L1(前順序圏) から L3([0,1]-豊穣 bicategory) への拡張は2つの独立な方向を持つ

```
                   豊穣化 (Hom を量的にする)
L1 (前順序圏)  ──────────────────────→  L2 ([0,1]-豊穣圏)
     │                                       │
  圏化                                     圏化
  (2-cell を追加する)                      (2-cell を追加する)
     ↓                                       ↓
L1' (locally posetal 2-圏) ──────────→  L3 ([0,1]-豊穣 bicategory)
                   豊穣化
```

> **[FACT]** 4頂点の定義:

| 頂点 | 圏論的構造 | Hom 集合 | 2-cell | HGK 解釈 |
|:-----|:----------|:---------|:-------|:---------|
| L1 | 前順序圏 | {0,1} | なし | A≤B = 「行ける」。到達可能性のみ |
| L2 | [0,1]-豊穣圏 | [0,1] | なし | Drift ∈ [0,1] で遷移の「質」を測定 |
| L1' | locally posetal 2-圏 | {0,1} | あり (≤) | パイプライン間に比較関係 (質なし) |
| L3 | [0,1]-豊穣 bicategory | [0,1] | あり | Drift + パイプライン変形の完全モデル |

## 接続射 (4辺) {#sec_03_morphisms .formal}

> **[DEF]** 4辺の接続射:

- **I**: `Preord ↪ [0,1]-Cat` — Lawvere 包含。I(A≤B):=0, I(A≰B):=1。前順序圏 = {0,1}-豊穣圏
- **J**: `Preord ↪ 2-Cat_lp` — locally posetal 埋め込み。自明な 2-cell (≤関係) のみ
- **U**: `[0,1]-Cat → BiCat` — underlying bicategory 構成 (Fujii & Lack 2022)
- **K**: `2-Cat_lp → [0,1]-BiCat` — Hom-poset の [0,1] 豊穣化

## 可換性証明 U∘I ≅ K∘J {#sec_04_commutativity .proof}

> **[FACT]** 正方形は可換 (U∘I ≅ K∘J up to natural isomorphism)

構成的証明 (各層で両経路の出力を比較):

- **0-cell**: 対象 x は全関手で不変。両経路とも x → x → x ✅
- **1-cell**: 存在(A≤B)→Drift=0、不在(A≰B)→Drift=1。両経路同一 ✅
- **2-cell**: L1 出発→豊穣化も圏化も自明化。両経路とも恒等/trivial ≤ のみ ✅

> **[RULE]** 核心原理: L1 から出発する限り、拡張は何も加えない。新しさは L1 外部から L2/L1' を経由して初めて現れる。

> **[FACT]** 系: 正方形の可換性は「どちらの順序で一般化しても同じ理論に到達する」ことを保証 → L3 は ad hoc でなく必然的。

## L1' の操作的定義 {#sec_05_l1prime .operational}

> **[DEF]** L1' = 24 Poiesis を 0-cell、CCL パイプラインを 1-cell、パイプライン間の ≤ 関係を 2-cell とする locally posetal 2-圏

> **[DISCOVERY]** L2 と L1' の直交性が HGK の WF 設計と対応:

| 問い | L2 (豊穣化) | L1' (圏化) |
|:-----|:-----------|:-----------|
| 「どのくらい良い？」 | Drift = 0.15 (量的) | 答えられない |
| 「どちらが良い？」 | 答えられない (1-圏) | f ≥ g (順序的) |
| HGK での用途 | `/fit` による品質測定 | `/vet` による比較判定 |

> **[DISCOVERY]** `/fit` と `/vet` は豊穣化と圏化の操作的対応。偶然ではなく体系構造の帰結。

## 学術的根拠 {#sec_06_references .academic}

> **[FACT]** 消化済み論文:

- Bacci et al. 2023 (DOI: 10.46298/entics.12292) — 「前順序圏は [0,1]-豊穣圏の特殊ケース」(Lawvere 1973 の定量的アナロジー)
- Fujii & Lack 2022 (DOI: 10.70930/tac/byeb4zi0) — B-Cat の 2-圏は slicing で bicategory に拡張
- Liu & Li 2022 (DOI: 10.46298/entics.10339) — quantaloidal completions (前順序→quantaloid)
- Dagnino et al. 2025 (arXiv: 2508.11623) — quantale-valued metric space の前順序圏的構造

## 更新ファイル {#sec_07_files .artifacts}

> **[FACT]** 更新した3ファイル:

1. `axiom_hierarchy.md` → v4.2.0: 旧3層テーブル→正方形モデル+接続射+可換性証明+L1'操作的定義
2. `weak_2_category.md` → v1.1.0: タイトル・§1を[0,1]-豊穣bicategoryに更新, Drift明示
3. `episteme-category-foundations.md`: user_rulesに正方形モデル知識ブロック追加 (全セッション注入)

## 関連情報 {#sec_08_related}

- 関連 WF: /noe (認識), /u (主観), /fit (品質測定), /vet (比較判定)
- 関連 KI: kalon.md (Fix(G∘F) 不動点)
- 関連 PJ: Formal Derivation (08_形式導出)

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "HGK の圏論的正当化は何か"
  - "正方形モデルとは何か"
  - "L1, L2, L1', L3 の違いは"
  - "可換性証明の核心は"
  - "豊穣化と圏化の違いは"
  - "/fit と /vet の圏論的対応は"
answer_strategy: "正方形の図を先に示し、4頂点→4辺→可換性の順で説明。L1' の操作的意味を /fit vs /vet で具体化"
confidence_notes: "可換性証明は構成的で各層の一致を直接示す。ただし厳密な2-categorical equivalence の詳細は省略"
related_roms: []
search_extensions:
  synonyms: ["enrichment", "categorification", "Lawvere metric", "weak 2-category", "bicategory", "locally posetal"]
  abbreviations: ["L1", "L2", "L3", "L1'"]
  related_concepts: ["Galois connection", "Drift", "associator", "quantale", "前順序圏"]
-->

*ROM burned: 2026-03-13 11:19 — Session ea14fb70*
