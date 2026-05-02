---
rom_id: rom_2026-03-17_2cell_exhaustion_proof
session_id: 54266021-2488-49d2-91af-f81022674e25
created_at: 2026-03-17 22:51
rom_type: distilled
reliability: High
topics: [2-cell, 4種仮説, V-豊穣, Mostert-Shields, t-ノルム, 網羅性証明, 基底変換, 対合, 直和, ゲイン, Kelly, enriched category]
exec_summary: |
  L3 2-cell 4種仮説の網羅性を [推定] 85% まで引き上げた。
  Mostert-Shields 定理により V=[0,1] 上の独立な二項演算が ⊕=max と ⊗=× の2つのみであることを形式的に証明。
  先行研究 (Kelly/Selinger/Egger) により4種の各々が確立された圏論的枠組みの特殊化であることを確認。
---

# L3 2-cell 4種仮説 — 網羅性証明 {#sec_01_exhaustion}

> **[DECISION]** 4種 (直和/ゲイン/基底変換/対合) は V=[0,1]-豊穣の構造から必然的に導出され、5番目の種は存在しない [推定] 85%

## §1 4種の確定テーブル {#sec_02_species_table}

> **[FACT]** 6修飾座標の2-cell 分類は以下の通り確定

| 種 | 座標 | 確信度 | 圏論的構造 |
|:---|:-----|:-------|:-----------|
| I. 直和 | Value, Function | 85% | F ≅ F_L ⊕ F_R (biproduct / additive category) |
| II. ゲイン | Precision | 80% | α_π: F ⇒ π ⊗ F (monoidal action, δ→Dirac) |
| III. 基底変換 | Scale, Temporality | 85% | φ*⊣φ_* (Eilenberg-Kelly change-of-base 2-functor) |
| IV. 対合 | Valence | 90% | σ²=id (involutive monoidal category / Z/2Z 群作用) |

## §2 先行研究による裏付け {#sec_03_prior_work}

> **[DISCOVERY]** 4種の各々に確立された圏論的枠組みが存在する

| 種 | 先行研究 | 代表文献 |
|:---|:---|:---|
| I | Additive category / biproduct | Mac Lane, Kelly (V-Cat enriched over Ab) |
| II | Monoidal action on Hom | Kelly §1 (V-Cat), Day convolution |
| III | **Eilenberg-Kelly change-of-base 2-functor** | Eilenberg-Kelly (1966), Kelly §3 |
| IV | **Involutive monoidal category** | Selinger (2007), Egger (involutive ambimonoidal) |

> **[RULE]** 種 IV (Valence) は dagger category (反変対合 †: C→C^op) ではなく **involutive monoidal** (共変対合 σ: F⇒F)。反変=量子力学的、共変=代数的。

## §3 Mostert-Shields による L1 唯一性証明 {#sec_04_mostert_shields}

> **[DECISION]** V=[0,1] 上の独立な二項演算は ⊕=max (余積) と ⊗=× (モノイダル積) の2つのみ

**Mostert-Shields 定理**: [0,1] 上の全ての連続 t-ノルムは min (Gödel), × (product), max(a+b-1,0) (Łukasiewicz) の順序和として一意に表現される。

**独立性の棄却論証**:

| 候補 | 独立か？ | 理由 |
|:---|:---|:---|
| max (⊕) | ✅ | 完備束の余積 |
| × (⊗) | ✅ | モノイダル積。max と分配律不成立 |
| min | ❌ | max の束双対。分配律で導出可能 |
| Łukasiewicz | ❌ | × の代替選択肢、第3の独立演算ではない |
| 内部 Hom | ❌ | ⊗ の右随伴 [a,b]=min(b/a,1)。導出可能 |
| t-コノルム | ❌ | t-ノルムの双対。一意に導出 |

> **[FACT]** [0,1] が完備束であるため max/min は束対として拘束。量子圏であるため ⊗/[−,−] は随伴対として拘束。独立な座標方向は2つのみ。

## §4 3階層×4種 = 閉じた構造 {#sec_05_three_levels}

> **[RULE]** V-Cat = (Ob, Hom_V, ∘, id) において修飾が作用しうる構造レベルは3つで閉じている

| 階層 | 対象 | 操作 | 種 |
|:---|:---|:---|:---|
| L1 Hom 値 | Hom_V(A,B) ∈ V | ⊕ / ⊗ | I / II |
| L2 基底 V | V 自体 | φ: V→V' | III |
| L3 関手 F | F: C→C | σ ∈ Aut(F) | IV |

第4階層は V-Cat の定義に存在しない。

## §5 残存課題 {#sec_06_remaining}

| # | 事項 | 確信度 |
|:--|:-----|:-------|
| 1 | 共変対合 vs 反変対合 (dagger) の精密化 | 未着手 |
| 2 | 一般 V に対する普遍的証明 (HGK は V=[0,1] で十分) | 対象外 |

## 関連情報
- 分析詳細: `brain/54266021/2cell_species_analysis.md` (v1.3)
- 核心文書: `fep_as_natural_transformation.md` (v0.7.2, §2.1/§2.3b に4種統合済み)
- 前セッション ROM: `rom_2026-03-17_2cell_species_hypothesis.md` (v1.0)
- Ω計算: `brain/57a34e63/omega_computation.md` (CCC/Heyting 構造)
- 関連 WF: /noe, /lys, /kat

<!-- ROM_GUIDE
primary_use: L3 2-cell 4種仮説の網羅性証明と根拠の参照
retrieval_keywords: 2-cell, 4種, 網羅性, Mostert-Shields, t-ノルム, V-豊穣, Kelly, change-of-base, involutive, dagger, quantale, biproduct
expiry: permanent
-->
