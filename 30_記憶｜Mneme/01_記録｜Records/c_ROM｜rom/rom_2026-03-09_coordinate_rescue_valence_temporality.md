---
rom_id: rom_2026-03-09_coordinate_rescue_valence_temporality
session_id: bd704717-b48e-4884-8987-555603b634ef
created_at: 2026-03-09 14:46
rom_type: rag_optimized
reliability: High
topics: [valence, temporality, FEP, coordinate, structural_coupling, VFE, EFE, Pattisapu, Millidge, Pezzulo, axiom_hierarchy, Fisher_information]
search_expansion_terms: [感情価, 時間性, 自由エネルギー原理, 座標救出, 構造的結合, 交差項, メタ状態, 能動推論, 期待自由エネルギー, Hessian, 情報幾何, 進化代数]
exec_summary: |
  Valence (80%) と Temporality (75%) の FEP 内導出を確定。
  Valence は4定式化 (Joffily/Hesp/Pattisapu/Seth) 全て FEP 内だが VFE Hessian で構造的結合 (交差項比率0.7119)。
  Temporality は VFE≠EFE 定理 (Millidge 2020) と進化的独立性 (Pezzulo 2021) で 55%→75%。
---

# Coordinate Rescue: Valence + Temporality {#sec_01_overview}

> **[DECISION]** Valence と Temporality は両方 FEP 内に格上げ。d=3 を維持しつつ確信度を大幅引上げ

> **[DISCOVERY]** VFE Hessian 解析で Valence×ω の交差項比率 **0.7119** — 概念的独立と情報幾何学的結合の二重性

> **[DISCOVERY]** Millidge 2020: VFE の自然な未来拡張は探索を阻害する → EFE は構造的に異なるオブジェクト → Past≠Future は FEP 内証明

---

## Valence Rescue (65% → 80%) {#sec_02_valence}

### 4定式化 {#sec_02a_formalizations}

> **[FACT]** Valence の FEP 内定式化は4つ存在し、全て身体性仮定不要:

| # | 定式化 | 論文 | 引用 | 特徴 |
|:--|:-------|:-----|:-----|:-----|
| 1 | −dF/dt | Joffily & Coricelli 2013 | 258 | VFE 勾配方向。最シンプル |
| 2 | Expected action precision (AC) | Hesp et al. 2021 | 184 | 階層モデルの期待精度 |
| 3 | utility − E[utility] | Pattisapu et al. 2024 | — | RPE/ドーパミン類似。Circumplex Model |
| 4 | 内受容予測誤差 | Seth & Critchley 2013 | (身体性必要。唯一の FEP 外候補) |

### 構造的結合 {#sec_02b_coupling}

> **[FACT]** VFE Hessian (Fisher 情報量) 解析: Valence × ω (精度) 交差項比率 = **0.7119** (> 0.1 = 強い結合)

> **[RULE]** Valence はパラメータ空間の直積ブロックではなく、他パラメータを調節する**メタ状態**として振る舞う

> **[DECISION]** 概念的独立性は保持。情報幾何学的結合は正直に開示。Pattisapu 2024 の operational independence が根拠

### Valence × Precision 独立性 {#sec_02c_independence}

> **[FACT]** Pattisapu 2024: Valence (utility差) と Arousal (posterior entropy ≈ inverse Precision) を EFE から独立導出。シミュレーションで独立変動を実証

> **[CONFLICT]** operational independence (概念レベル) vs structural coupling (Fisher レベル) の二重性

### 確信度テーブル {#sec_02d_confidence}

| 項目 | 旧 | 新 | 根拠 |
|:-----|:---|:---|:-----|
| FEP 内在性 | 65% | **80%** | 4定式化全て FEP 内 (SOURCE: 論文3本) |
| Surprise Joy 解決 | — | **75%** | Pattisapu utility差 + 認知/情動の分離 |
| V × P 独立性 | 75% | **85%** | Pattisapu + 構造的結合の正直な開示 |

---

## Temporality Rescue (55% → 75%) {#sec_03_temporality}

### VFE ≠ EFE 定理 {#sec_03a_vfe_efe}

> **[FACT]** Millidge, Tschantz & Buckley 2020 "Whence the Expected Free Energy?" (Neural Computation, 80引用):
> - VFE を未来に自然拡張した汎関数は**探索を積極的に阻害**する
> - EFE は VFE とは数学的に異なるオブジェクト
> - → Past (VFE が支配) ≠ Future (EFE が支配) は FEP 内で証明可能

> **[RULE]** 導出チェーン: FEP → VFE最小化 + EFE最小化 → VFE≠EFE (証明済み) → Past≠Future → Temporality

### 進化的独立性 {#sec_03b_evolutionary}

> **[FACT]** Pezzulo, Parr & Friston 2021 "The evolution of brain architectures" (Phil Trans R Soc B, 83引用):
> - 生成モデルの進化代数には4つの独立軸がある
> - **Hierarchical depth** (空間スケール = Scale) と **Temporal depth** (時間的深度 = Temporality) は明示的に独立な演算子
> - σ∝τ は弱い経験的相関であり構造的同一性ではない

### 反証と応答 {#sec_03c_refutations}

> **[CONFLICT]** σ∝τ 仮説 → 応答: 反例多数 (短期記憶は空間的に局所だが時間的に長い etc.)。進化データも T/H 独立
> **[CONFLICT]** EFE は FEP から導出可能か → 論争中 (Da Costa vs Millidge) だが VFE≠EFE の事実自体は確定
> **[CONFLICT]** 引用年精度: axiom_hierarchy が "Pezzulo 2022" と引用 → 修正: Pezzulo 2021 (Phil Trans R Soc B)

### 確信度更新 {#sec_03d_confidence}

| 項目 | 旧 | 新 | 根拠 |
|:-----|:---|:---|:-----|
| FEP 内在性 | 55% | **75%** | VFE≠EFE 定理 (Millidge 2020) |
| Scale との独立性 | — | **80%** | Pezzulo 2021 (独立進化軸) |
| d=3 正当性 | — | **70%** | modeling choice の要素あり |

---

## 更新した成果物 {#sec_04_artifacts}

| ファイル | 更新内容 |
|:---------|:---------|
| `axiom_hierarchy.md` | Valence 定義、V×P独立性行、VFE交差項行、Temporality セクション、理論的基盤表 |
| `derivation_valence_fep_internal` | §3 構造的結合注記 |
| `derivation_correct_fep_coordinates` | Valence: 帰納的→FEP内、Temporality: 引用強化 |
| `derivation_valence_v3` | §6 open issue #4 (構造的結合) |
| `rom_valence_fep_v3` | [FACT] 構造的結合 |
| `result_maxent_vfe_hybrid` | 補遺: Valence 構造的結合の定量評価 (Creator 加筆) |
| **NEW** `derivation_temporality_fep_internal` | Temporality の FEP 内導出分析 v1 |

---

## 残存リスク・Open Problems {#sec_05_risks}

> **[CONFLICT]** EFE の出自: FEP から導かれるか追加公理か (Da Costa 2020 vs Millidge 2020)
> **[CONFLICT]** 4定式化のうちどれを HGK 公式定義とするか
> **[CONFLICT]** Prior preferences C の出自 (EFE の C は進化/学習/外部定義?)
> **[CONFLICT]** temporal depth を「座標」とする理論的必然性の強化
> **[FACT]** 構造的結合 (0.7119) は Valence が直積ブロック独立でないことを示す → メタ状態再定義の必要性

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "Valence の FEP 内導出は?"
  - "Temporality は Scale と独立か?"
  - "VFE と EFE の数学的違いは?"
  - "構造的結合 (0.7119) とは?"
  - "座標の確信度は?"
answer_strategy: "確信度テーブルを参照し、根拠論文を引用して回答。構造的結合の二重性 (概念的独立+情報幾何的結合) を必ず言及"
confidence_notes: "Valence 80%, Temporality 75% — 両方 FEP 内だが open problems あり。構造的結合は正直に開示"
related_roms: ["rom_2026-03-09_valence_fep_derivation_v3"]
-->
