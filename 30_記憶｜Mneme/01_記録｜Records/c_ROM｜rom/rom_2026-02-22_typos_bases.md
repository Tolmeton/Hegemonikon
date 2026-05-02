---
rom_id: rom_2026-02-22_typos_bases
session_id: 92ef3033-c197-41a7-9f70-088b5c627979
created_at: 2026-02-22 09:40
rom_type: rag_optimized
reliability: High
topics: [typos, description-theory, rate-distortion, bases, salience, endpoint, poiesis, adversarial-review]
exec_summary: |
  TYPOS記述理論の7基底 (1+3+3) と24記述行為をRate-Distortion定式化から演繹し、
  内部3モデル検証+外部claude.aiレビューによる敵対的検証を経て構造を確定。
  d=0: Endpoint, d=1: Reason/Resolution/Salience, d=2: Context/Order/Modality。
search_extensions:
  synonyms: [タイポス, 記述理論, 情報理論, レート歪み, ロッシー圧縮, 言語哲学]
  related_concepts: [FEP, HGK, Searle-Vanderveken, Peirce, Shannon, Cover-Thomas, Austin speech-acts]
  abbreviations: [R-D, RT, A0, MB]
---

# TYPOS 記述理論: 基底構造の確定 {#sec_01_overview .core}

> **[DECISION]** TYPOS の体系核は **1 (公理) + 7 (基底) + 24 (記述行為) = 32**。
> HGK と同数だが、異なる公理から独立に導出された。

## 公理 A0 {#sec_02_axiom .foundational}

> **[DEF]** A0: 記述 = 信念分布 M の言語 L への不可逆圧縮 f: M → L

数式: $R(D) = \min_{p(\ell|m)} I(M; L) \quad \text{s.t.} \quad \mathbb{E}[w(m) \cdot d(m, \ell)] \leq D$

> **[FACT]** A0 は標準 Rate-Distortion (Cover & Thomas) と同一ではない。
> 標準 R-D は X = X̂（同一アルファベット）がデフォルト。
> A0 は「信念(連続・主観)→言語(離散・共有)」を明示的に規定しており、M ≠ L は公理に内在する。

> **[RULE]** 旧「Image」基底は A0 そのものであり基底ではない。
> HGK で FEP が座標ではないのと同じ。

---

## 7基底の確定構造 {#sec_03_bases .core}

> **[DECISION]** 構造: d=0 (1個) + d=1 (3個) + d=2 (3個) = 7基底

| d | 基底 | 対立 | 数式成分 | 追加仮定 |
|:--|:-----|:-----|:---------|:---------|
| 0 | **Endpoint** | source ↔ target | M, L | 0: f: M→L に内在 |
| 1 | **Reason** | arché ↔ telos | d(m,ℓ) | 1: 圧縮に目的がある |
| 1 | **Resolution** | precise ↔ compressed | β | 1: Rate-Distortion トレードオフ |
| 1 | **Salience** | focused ↔ diffuse | w(m) | 1: 全信念が等しく重要ではない |
| 2 | **Context** | local ↔ global | 階層的 M,L | 2: R-D + 階層的構文 + スコープ |
| 2 | **Order** | object ↔ meta | L の自己参照 | 2: R-D + Tarski + 自己参照 |
| 2 | **Modality** | actual ↔ possible | 代替 p(ℓ|m) | 2: R-D + Kripke + 到達可能性 |

> **[DISCOVERY]** d=1 の3基底はラグランジアンの3つの独立パラメータ (d, β, w) に完全対応。
> Gemini 3.1 Pro はこれを「白眉」と評価。

---

## Salience の独立性根拠 {#sec_04_salience .contested}

> **[FACT]** 数学的には w(m)·d(m,ℓ) = d'(m,ℓ) として Reason に吸収可能。
> しかし HGK の Precision も q(s) のパラメータとして吸収可能だが独立座標。

> **[RULE]** パラメトリック族の構造的分離: 吸収「できる」≠ 吸収「すべき」。
> w(m) は m にのみ作用、d(m,ℓ) は (m,ℓ) ペアに作用。関数型が異なる。

> **[CONFLICT]** 外部 claude.ai は 45% の確信度で独立性に懐疑的。
> 内部 Gemini 3.1 Pro は 85%、Gemini 2.5 Flash は 90% で正当と判断。
> 差分の原因: 外部は標準 R-D の観点、内部は HGK Precision との構造的同型性を重視。

---

## d=2 の導出構造 {#sec_05_d2 .extension}

> **[RULE]** d=2 は「公理 + ドメイン固有理論」から導出される。HGK と同じ構造。

| TYPOS d=2 | ドメイン理論 | HGK d=2 対応 | HGK のドメイン理論 |
|:----------|:-----------|:------------|:-----------------|
| Context | 言語学（階層的構文） | Scale | 階層的生成モデル |
| Order | Tarski（メタ言語） | Valence | Seth 2013（内受容予測） |
| Modality | Kripke（可能世界） | Temporality | Pezzulo 2022（時間的深度） |

> **[DISCOVERY]** 外部レビューは d=2 を「哲学的グラフト」と批判したが、
> HGK の Seth/Pezzulo も FEP から直接導出されない。同じ「ドメイン特化」構造。

---

## Valence/Temporality の位置 {#sec_06_excluded .boundary}

> **[DECISION]** Valence と Temporality は TYPOS の基底ではない。
> A0 の Rate-Distortion 式から導出できないため。

> **[RULE]** これらは TYPOS-HGK インターフェース上の次元。
> 「記述を使う認知主体」が持ち込む次元であり、記述の構造的基底ではない。

---

## 記述行為の生成規則 {#sec_07_poiesis .generative}

> **[DECISION]** Endpoint (生成子) × 6修飾基底 × 各2極 = 6 × 4 = 24 記述行為

> **[RULE]** Endpoint を含む組合せ = 記述行為（操作可能）。
> Endpoint を含まない組合せ = 記述修飾（パラメータ）。
> HGK の Flow が Poiesis/Dokimasia を分けるのと同じ原理。

> **[FACT]** 外部レビューが発見した先行研究:
>
> - Searle-Vanderveken (1985): 語内行為力の**7成分** — TYPOS の7基底と構造的平行
> - Peirce のサイン分類: sinsign 分岐における**24クラス** — TYPOS の24記述行為と符合
> - Jakobson の6機能モデル: 6要素からの機能生成原理

---

## 検証の全体サマリ {#sec_08_verification .meta}

| 検証者 | Q1 Salience | Q2 d=0 | Q3 24行為 | Q4 1+3+3 |
|:-------|:-----------|:-------|:---------|:---------|
| Gemini 3.1 Pro | ✅ 85% | ✅ 90% | ✅ 80% | ✅ 85% |
| Gemini 2.5 Flash | ✅ 90% | ⚠️ 80% | ⚠️ 条件付 | — |
| **外部 claude.ai** | ⚠️ 45% | ❌ 30% | ⚠️ 55% | ⚠️ 40% |
| **再反論後** | ✅ 80% | ✅ 90% | ✅ 80% | ✅ 80% |

> **[DISCOVERY]** 外部レビューの見落とし: A0 を標準 R-D と同一視した。
> A0 は「信念→言語」の変換を明示しており、M≠L は公理に内在する。

---

## 次ステップ候補 {#sec_09_next .actionable}

> **[OPINION]** 以下が理論完成に向けた残課題:

| # | タスク | 重要度 | 内容 |
|:--|:------|:-------|:-----|
| 1 | **24記述行為の命名と意味検証** | 🔴 必須 | Endpoint × 6基底 × 4極 = 24 パターンの網羅的意味付け |
| 2 | **先行研究との照合** | 🔴 必須 | Zaslavsky et al., Searle-Vanderveken, Peirce との系統的対照 |
| 3 | **Dokimasia 相当の定義** | 🟡 重要 | 修飾パラメータ C(6,2)=15 Series の意味付け |
| 4 | **具体例による検証** | 🟡 重要 | 実際の記述（論文・詩・法律文書）を7基底で分析 |
| 5 | **TYPOS-HGK 接合面** | 🟢 発展 | Valence/Temporality が住むインターフェースの圏論的定式化 |
| 6 | **kernel ドキュメント化** | 🟢 発展 | SACRED_TRUTH.md, axiom_hierarchy.md の TYPOS 版作成 |

---

## 外部レビューの価値ある参考文献 {#sec_10_references .bibliography}

| 文献 | 関連 | 状態 |
|:-----|:-----|:-----|
| Zaslavsky, Kemp, Regier, Tishby (PNAS 2018) | 110+言語の色彩命名が R-D 最適化 | 未消化 |
| Zaslavsky, Hu, Levy (2020/2021) | RD-RSA: 語用論を R-D として再定式化 | 未消化 |
| Futrell & Hahn (2024/2025) | 言語の体系性が予測情報最小化から創発 | 未消化 |
| Martinian, Wornell, Zamir (IEEE IT 2008) | 重み付き歪みの情報論的分析 | 未消化 |
| Searle & Vanderveken (1985) | 語内行為力の7成分 | 未消化 |
| Peirce sign classification | 24 sinsign クラス | 未消化 |

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "TYPOS の基底は何個？"
  - "Salience は独立か？"
  - "記述行為の生成規則は？"
  - "HGK との違いは？"
  - "外部レビューの結果は？"
answer_strategy: "基底構造→数式対応→検証サマリの順で回答。外部レビューの反論と再反論を必ず含める"
confidence_notes: "d=1 の3基底は最も確信度が高い (ラグランジアン対応)。Salience とd=0配置は論争あり。"
related_roms: []
-->
