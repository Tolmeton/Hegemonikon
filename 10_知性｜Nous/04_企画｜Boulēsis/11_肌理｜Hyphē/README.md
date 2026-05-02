# Hyphē (ὑφή) — 肌理

> **Status**: 設計中 (PJ 統合: 2026-03-31)
> **Origin**: 統一索引構想 (2026-03-10) → Lethe 実験との理論⊣実験統合 (2026-03-31)
> **Etymology**: ὑφή (hyphē) — 織物・テクスチャ。コンテキストの織り目を検出する

## 1つの物語

Hyphē は**1つの問い**から始まる:

> 「知識の断片をどう見つけ、どう繋ぐか」

この問いに対して、2つの独立した探究が同じ答えに収束した:

- **理論** (本ディレクトリ): チャンクは意味空間の Markov blanket として**発見される**。最適化 (NP-hard) ではなく不動点検出 (P) で到達できる
- **実験** ([Lethe](../14_忘却｜Lethe/)): CCL embedding が code の構造的類似度を捕捉する (ρ=0.507, AUC=0.967)。49d 特徴量空間に座標構造が存在する (PC 3軸, d_eff=18.8)

**主張**: 構造を**発見**する (Kalon△) ことは構造を**最適化**する (Kalon▽) ことより計算量的に安く、かつ生物学的に自然である。

## CKDF 4層アーキテクチャ

| 層 | 数学 | Hyphē における実現 | Lethe 実験的支持 |
|:---|:-----|:-------------------|:-----------------|
| **L0** 格子構造 | 完備束 C + 順序 ≤ | 意味空間 Ω + 類似度前順序 | (基盤 — 直接検証不要) |
| **L1** Galois 接続 | F⊣G (探索⊣活用) | index_op ⊣ Search | Code→Code 検索の実装 ✅ |
| **L2** 座標検出 | 固有分解 → d 軸 | 6座標 TypedRelation | **PC Loading 3軸** (合成長 31.6%, 変換密度 14.5%, MB比率 7.3%) ✅ |
| **L3** 局所不動点 | Fix(G∘F) = Kalon△ | チャンク = MB の不動点 | Ξ=1.083, Gini=0.613 (存在示唆) △ |
| **L∞** 大域不動点 | Kalon▽ (到達不能) | 最適クラスタリング (NP-hard) | (到達不能 = 正しい) |

## 理論 ⊣ 実験 対応マップ

| 理論的主張 (Hyphē) | 実験的支持 (Lethe) | 強度 | 参照 |
|:---|:---|:---|:---|
| Chunk = Markov blanket | CCL embedding で構造類似度測定可能 | 間接 | Phase 4, ρ=0.507 |
| index_op ⊣ Search | Code→Code 検索の Cache 実装 | 直接 | ROADMAP §8.2 |
| Fix(G∘F) で NP 回避 | 49d 特徴量安定 (Ξ=1.083) | 弱い | Phase B, §22b |
| L2 座標検出 | PC Loading 3軸が座標構造を示す | **強い** | Phase B, PC分析 |
| Kleinberg Scale-Invariance 放棄 | Bin 2-4 の ρ 低下 = スケール依存性 | 間接 | Phase 3, 5-bin分析 |
| 6座標 TypedRelation | — | **未検証** | — |
| Coherence (Pentagon identity) | — | **未検証** | — |

## 研究プログラム — Gap を埋める実験

| 優先度 | 実験 | 検証対象 | 設計 | エレガント度 |
|:---|:---|:---|:---|:---|
| **1** | Fix(G∘F) 収束過程の実測 | L3 不動点到達 = NP回避の核心 | 初期チャンク分割に G∘F 反復適用 → 収束速度測定。Banach なら指数的 | ★★★★ |
| **2** | MB 境界直接検出 | Chunk = MB の直接検証 | 49d 空間で k-NN グラフ → 接続成分境界 vs chunker 切断点 | ★★★ |
| **3** | F⊣G unit/counit 測定 | 随伴の実在性 | GFG ≈ G, FGF ≈ F の等冪性を cos 距離で測定 | ★★ |
| **4** | Kleinberg 公理直接テスト | Scale-Invariance 破れ | τ を変えてチャンク数変化を観察 (既存 τ=0.70/0.75 二層方式で検証可能) | ★★ |
| **5** | 6座標 TypedRelation | 座標と関係型の対応 | 人手アノテーション + 統計検定 | ★ |

## ディレクトリ構造

### 理論 (本ディレクトリ)

| ファイル | 内容 |
|:---------|:-----|
| [chunk_axiom_theory.typos](chunk_axiom_theory.typos) | チャンク公理 — MB としてのチャンク定義、Linkage、Galois 接続 |
| [ckdf_theory.md](ckdf_theory.md) | CKDF 完全定義 — L0-L∞ 4層構造、Knaster-Tarski、Kalon⊃Optimization |
| [chunk_ckdf_bridge.md](chunk_ckdf_bridge.md) | チャンク公理→CKDF の理論的橋渡し (L0-L3 対応) |
| [ckdf_kalon_detection.typos](ckdf_kalon_detection.typos) | CKDF Kalon 検出の role 定義 |
| [np_hard_avoidance_via_fep.md](np_hard_avoidance_via_fep.md) | NP-hard 回避仮説 — FEP 不動点アプローチ |
| [f2_auto_classification.md](f2_auto_classification.md) | セッション自動分類 — Fisher 情報行列の固有分解 |
| [chemistry_of_ccl_features.md](chemistry_of_ccl_features.md) | CCL 特徴量の化学 — 原子(22d)→分子式(テンソル積)→構造式(演算子パターン) の階層と実験結果 |
| [multi_scale_chemistry_isomorphism.md](multi_scale_chemistry_isomorphism.md) | F: Chem→Cog の3スケール忠実性 — 情報理論的証明 (定理2-4) + マクロ/メソ/ミクロ整合 |

### 実験 ([14_忘却｜Lethe](../14_忘却｜Lethe/))

| Phase | 内容 | 成果 |
|:------|:-----|:-----|
| A | パイプライン構築 | Code→CCL→Embedding 変換 |
| B | 構造的プローブ | 49d 特徴量, PC 3軸, Ξ=1.083 |
| C | Structural Attention (QLoRA) | **着手前** — CodeLlama 13B ファインチューン |

### 実装 ([mekhane/hyphe/](../../../20_機構｜Mekhane/_src｜ソースコード/mekhane/hyphe/))

| モジュール | 内容 |
|:-----------|:-----|
| `chunker.py` | Nucleator 理論チャンカー — pairwise@τ=0.70 + knn@τ=0.75 二層方式 |

## 接続

- [14_忘却｜Lethe](../14_忘却｜Lethe/) — CCL embedding 実験 (Phase A-C)
- [01_美論｜Kalon](../01_美論｜Kalon/) — CKDF × Kalon 理論
- [mekhane/hyphe/](../../../20_機構｜Mekhane/_src｜ソースコード/mekhane/hyphe/) — チャンカー実装
- [00_核心/fep_as_natural_transformation.md](../../../00_核心｜Kernel/A_公理｜Axioms/fep_as_natural_transformation.md) — CKDF §3 参照

---
*Created: 2026-03-10 | 統合: 2026-03-31 — 理論 (旧UnifiedIndex) と実験 (Lethe) を1つの物語に*
