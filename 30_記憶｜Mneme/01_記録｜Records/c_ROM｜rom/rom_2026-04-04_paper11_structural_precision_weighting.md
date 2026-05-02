---
rom_id: rom_2026-04-04_paper11_structural_precision_weighting
session_id: claude-code-2026-04-04
created_at: 2026-04-04 15:30
rom_type: rag_optimized
reliability: High
topics: [paper11, prompt-engineering, structural-precision-weighting, sapir-whorf, FEP, phase-c, thinking-language, coordinate-syntax, skill-optimization, A/B-test, softcot, soft-thinking, VoT, SPP, discrete-continuous-hierarchy, forgetting-hierarchy, exp0, equal-info-design, structural-propagation, axiom-ratio, constraint-encoding-separation, prompt-sensitivity, underspecification, skill-design, null-result]
exec_summary: |
  Paper 11 構想: 「prompt に構造的構文(座標系/圏論/CCL)を注入すると precision weighting が変わり、
  構造的推論が向上する」— 理論(FEP+忘却論)+先行研究(13件)+自前実験(Phase C)の統合。
  テキスト注入で幾何学的注入の85%を獲得(ρ=0.857)。LLM は暗黙のU_cclを持つ(P10:82%)。
  [v1.1追加] 離散→連続の忘却階層 (Level 0-5) を発見。
  [v2.0追加] 実験 0 実装: 等量条件 (トークン差1.5%) で構造語彙伝搬 0 vs 116 を確認。
  AXIOM 比率 A=15% vs B=38% が推論品質差の候補指標として浮上。バッチ検証待ち。
  [v3.0追加] バッチ実行完了 (N: A=18, B=14)。total_structural: d=8.73。全5トピック一貫。
  [v4.0追加] **理論的転換点**: H₁品質部分を棄却。代わりに「制約-符号化 分離定理」を発見。
  Opus 盲検: A=23.4/25 vs B=22.8/25 (d≈0)。科学タスク(T6-T10)でも帰無再現。
  P=(C,E) 分解: C(制約)が品質を決め、E(符号化)は語彙のみ変える。∂Q/∂E≈0。
  prompt sensitivity文献(Sclar/Weber/Kabra)と統合→3層モデル(L1タスク/L2形式/L3社会的)。
  SKILL設計含意: 「記法を磨くな、制約を磨け」。ただしNLで記述不能な制約は構造記法の独壇場。
  論文XI v0.4 に§7.5-7.8として記載。帰無結果が論文を強化する逆転。
  [v4.1追加] H₃' 分散仮説: E は Q の平均に効かないが分散に効く (bond_count SD比 0.45)。
  C→π_s→E[Q], E→π_v→1/Var[Q]。「記法で平均を上げるな、精度を上げろ」。
  [v5.0追加] CC Agent独立再現(N=10,Sonnet4.6): H₃(平均帰無)再現(bond_count A=B=13.8)。
  H₃'(分散)は部分的非再現: bond_count F=0.63(逆転), assumption_count F=5.0(方向一致)。
  確信度更新: H₃' 75%→50%。前Handoff記載のVar比5.29はTAINT(生データ未保存で検証不能)。
  [v6.0追加] **Gemini クロスモデル検証完了** (N=50/条件, gemini-3.1-pro-preview, AI Ultra tier)。
  H₃(構造伝搬): d=8.62 (Claude d≈1.5-3 の3-6倍)。Gemini は CCL 記法に極めて敏感。
  H₃(平均帰無): AXIOM比率 d=-0.39, ASSUMPTION数 d=0.08, bond_count d=-0.06 — 全て帰無再現。
  H₃'(分散): 構造語彙 BF p<0.001 (B>A)、内容指標 全て ns — 構造指標のみ分散増大。
  確信度更新: H₃ 70%→85% (クロスモデル再現で強化)。H₃' 50%→60% (Gemini分散パターンが一貫)。
---

# Paper 11: 構造的精度加重仮説 — Prompt as Thinking Language {#sec_01_title}

> **[DECISION]** 忘却論 Paper 11 = 「構造的精度加重仮説 (Structural Precision Weighting Hypothesis)」
> prompt に座標構文を注入すると LLM の generative model のうち構造的推論を担う領域への
> precision weighting が高まり、出力の構造的一致度が向上する。

## 核心仮説 {#sec_02_hypotheses}

> **[DEF]** H₁: 構造的精度加重仮説

```
prompt に構造的表記 (座標系, 圏論構文, CCL) を注入すると、
LLM の generative model のうち構造的推論を担う領域への
precision weighting が高まり、出力の構造的一致度が向上する。
```

根拠:
1. LLM は暗黙的に構造情報を保持 (P10: 82%, Phase B 4モデル一貫)
2. テキスト経由の構造情報伝達は 85% 獲得率 (Phase C v2: ρ=0.857)
3. Prompt = program space の検索クエリ (Chollet 2024)
4. 言語構造は AI 出力に有意に影響 (Ray 2025: p=9.59×10⁻¹⁰)
5. 認知操作の構造化は推論性能を向上 (Cognitive Prompting 2024)

> **[DEF]** H₂: 効果量の構造的上限仮説

```
r_obs = √ρ · r_theory / √(K+1)
  r_theory ≈ 0.857 (Phase C テキスト注入の構造伝達力)
  ρ_prompt ≈ 0.1-0.3 (prompt のスペクトラム射影効率)
  K ≈ 3-5 (交絡因子数)
→ r_obs ≈ 0.19 (推定)
→ N ≈ 200 (検出に必要な最小サンプルサイズ)
```

## Sapir-Whorf 矛盾の FEP 解消 {#sec_03_sapir_whorf}

> **[DISCOVERY]** 強 Whorf(偽) と 弱 Whorf(真) は FEP で両立する

| 研究 | 主張 | 証拠 |
|:-----|:-----|:-----|
| Ng 2025 | 強 Sapir-Whorf 偽 — 中間層は言語非依存 | 8言語×8トピック cos sim: 同内容異言語 0.902 > 同言語異内容 0.891 |
| Ray 2025 | 弱 Sapir-Whorf 真 — 言語構造が出力に影響 | 13言語×10prompt ANOVA p=9.59×10⁻¹⁰ |

> **[FACT]** FEP 翻訳:
> - 中間層 (世界モデル) = generative model → 言語に非依存
> - 入出力層 (符号化) = precision weighting → 言語構造に依存
> - 両立: 世界モデルは同じだが、何を活性化するかは入力の precision に依存

> **[FACT]** Ng の追加発見: Python コードと LaTeX 数式も中間層で自然言語と収束。
> 構造的表記は自然言語と「同じ意味空間」に到達する。問題は到達後の精度の差。

## Chollet のプログラム空間モデル → FEP 翻訳 {#sec_04_chollet}

> **[DISCOVERY]** Chollet 2024: "prompt = vector program database の検索クエリ"

| Chollet | FEP | Paper 11 への含意 |
|:--------|:----|:-----------------|
| Program space | Generative model の空間 | LLM = 無数の生成モデルの重ね合わせ |
| Prompt = search query | Prior = precision weighting | Prompt が活性化する領域を決定 |
| "Small variations → nearby programs" | Precision 微小変化 → posterior 微小変化 | **ワーディングが直接 precision を制御** |

> **[RULE]** Paper 11 の操作的定義:
> 自然言語 prompt = 低精度検索クエリ = 広領域ヒット → 汎用プログラム
> 座標構文注入 prompt = 高精度検索クエリ = 狭領域ヒット → 構造特化プログラム

## Phase C からの転移根拠 {#sec_05_phase_c}

> **[FACT]** Phase C 結果 (EXPERIMENTS.md §23):

| アプローチ | 方式 | ρ | 改善 |
|:-----------|:-----|:--|:-----|
| Baseline (未訓練) | なし | 0.244 | — |
| Phase B2 (Attentive Probe) | 読み出す | 0.745 | +0.501 |
| Phase C v2 (13B QLoRA) | CCL テキストを読ませる | 0.857 | +0.613 |
| Phase C-mini (Structural Attn) | 49d 幾何学的注入 | 0.963 | +0.719 |

> **[FACT]** テキスト注入の獲得率 = 0.613 / 0.719 = **85.3%**

> **[FACT]** §24: Gemma4 E4B partial_ρ = 0.445 ≈ CodeBERT 0.457。P10: 82%。

> **[RULE]** 転移構造:
> Phase C (fine-tuning): 重みを変える → 恒久的な関手変更
> Paper 11 (prompting): 文脈を変える → 一時的な関手注入
> 対象 (U_ccl) は同一。メカニズムが異なる。

## 思考言語仮説 {#sec_06_thinking_language}

> **[DISCOVERY]** Tolmetes の洞察: 「言語 ≅ ある圏が他の圏を内部に表現する際の関手」
> その関手の構造が、随伴の内容と随伴後の認知活動に影響する。

> **[FACT]** LLM では Sapir-Whorf 強版が構成的に成立:
> 人間: 思考 → (部分的に) 言語に依存
> LLM: 思考 = 言語 (全面的に依存 — トークン生成が条件付き確率分布)

> **[RULE]** 3種の関手:
> F₁ = 自然言語関手: 忠実度 低, 表現力 高 (full だが faithful でない)
> F₂ = CCL/座標関手: 忠実度 高, 表現力 制限 (faithful だが full でない)
> F₃ = F₁ × F₂: 積関手 → 忠実度 高 × 表現力 高

> **[DISCOVERY]** Cognitive Prompting (2410.02953) との差異:
> CP: 5認知操作を自然言語で「指示」→ CoT の拡張
> HGK: 48認知操作に構文を与えて「その構文で思考させる」→ 言語の変更
> CP = F₁ 内の操作、HGK = F₃ への関手変更

## 先行研究ギャップ = Paper 11 の新規性 {#sec_07_gap}

> **[DECISION]** Paper 11 が埋めるギャップ:

| 既存研究 | 示したこと | 示していないこと |
|:---------|:----------|:----------------|
| Ng 2025 | 中間層は言語非依存 | 構造的表記が precision を変えるか |
| Ray 2025 | 言語構造が出力に影響 | 形式構文 vs 自然言語の定量比較 |
| Chollet 2024 | Prompt = program search | Precision の理論的枠組み |
| Cognitive Prompting | 認知操作の指示が有効 | 認知操作の構文化の効果 |
| Phase C (HGK) | テキスト CCL で ρ=0.857 | Prompt レベルでの効果 |
| FLD×2 (NeurIPS 2024) | 形式論理訓練で推論向上 | Prompt 内の形式記法の効果 |

## 実験設計 {#sec_08_experiment}

> **[DECISION]** 実験 0 (パイロット — 転移仮説の検証):

```yaml
experiment_0:
  target: /noe (代表動詞)
  condition_A: 現行 SKILL.md (自然言語のみ)
  condition_B: 現行 SKILL.md + aletheia 座標構文注入
  metric: 座標一致度 (blind LLM judge)
  N: 100-200 ペア
  null_hypothesis: 座標構文注入は座標一致度を変えない
  evaluation: 構造的指標に限定、LLM に盲検評価させる
  power_analysis: r=0.19, α=0.05 → N=200 で power≈0.80
```

> **[DECISION]** 全体方針: 代表動詞 (/noe, /kat, /ske) に絞ってまず効果量の存在を示す

## 3系譜の収束点 {#sec_09_convergence}

> **[DISCOVERY]** 3つの独立系譜が1点に収束:
> 系譜 1: 忘却論 (FiO) — Paper IV の ρ, K → prompt の効果量の構造的上限
> 系譜 2: Phase C 実験 — CCL 注入 → ρ_ccl > ρ_49d → 構文が構造理解を改善
> 系譜 3: 認知言語学 (Sapir-Whorf) — LLM では構成的に成立
> → 収束点: 「prompt = 思考言語の規定 = 関手の選択」

## 引用リスト {#sec_10_references}

| # | 著者 | 年 | タイトル | 役割 |
|:--|:-----|:---|:--------|:-----|
| 1 | Ng | 2025 | Do LLMs Break the Sapir-Whorf Hypothesis? | 反 Whorf ボトルネック |
| 2 | Ray | 2025 | Does Linguistic Relativity Apply on ChatGPT? (Computational Intelligence) | 弱 Whorf 実証 |
| 3 | Chollet | 2024 | How I think about LLM prompt engineering | Program space model |
| 4 | arXiv:2410.02953 | 2024 | Unlocking Structured Thinking with Cognitive Prompting | 認知操作構造化 |
| 5 | Fernando et al. | 2024 | PromptBreeder (ICLR 2024) | 自動 prompt 最適化 |
| 6 | Yang et al. | 2024 | OPRO: Optimization by Prompting | LLM-driven optimization |
| 7 | NeurIPS 2024 | 2024 | FLD×2 Formal Logic Deduction Diverse | 形式論理訓練効果 |
| 8 | EMNLP 2025 | 2025 | Systematic Survey of Automatic Prompt Optimization | サーベイ |
| 9 | Springer 2025 | 2025 | Scaffolding Complex Thinking with LLM Prompts | 認知的足場 |
| 10 | Xu et al. | 2025 | SoftCoT: Soft Chain-of-Thought (ACL 2025) | 連続空間推論 |
| 11 | arXiv:2505.15778 | 2025 | Soft Thinking: Continuous Concept Space | 離散ボトルネック理論 |
| 12 | arXiv:2404.03622 | 2024 | VoT: Visualization-of-Thought (NeurIPS 2024) | 構造的表記 +27% |
| 13 | arXiv:2312.01054 | 2023 | SPP: Spatial Prefix-Prompting | 座標系プレフィックス +33% |
| 14 | arXiv:2601.02896 | 2026 | Bridging Mech. Interp. and Prompt Engineering | steering vector ↔ prompt |
| 15 | EMNLP 2025 | 2025 | Natural-Formal Hybrid Reasoning Enhances LLM Math | F₃=F₁×F₂ の直接証拠 |
| 16 | Basil et al. | 2025 | Expert Personas Don't Improve Factual Accuracy (SSRN) | ペルソナ失敗 = 負の対照 |
| 17 | arXiv:2505.23486 | 2025 | Autoformalization in the Era of LLMs: A Survey | NL↔形式の橋渡し |

## 離散→連続の忘却階層 {#sec_11_forgetting_hierarchy}

> **[DISCOVERY]** v1.1追加: 6段階の忘却階層が先行研究から浮上

| Level | 手法 | 空間 | 効果 | SOURCE |
|:------|:-----|:-----|:-----|:-------|
| 0 | Baseline | — | — | — |
| 1 | CoT | 離散 (自然言語) | +5-15% | Wei 2022 |
| 2 | Cognitive Prompting | 離散 (構造化NL) | +4-13.5% | 2410.02953 |
| 2.5 | SPP / VoT | 離散 (構造的表記) | **+27-33%** | NeurIPS 2024 |
| **3** | **Paper XI** | **離散 (座標構文)** | **未測定** | 本稿 |
| 4 | Soft Thinking | 連続概念空間 | +2.48pp, -22.4%tok | 2505.15778 |
| 5 | Phase C-mini | 49d ベクトル直接注入 | ρ=0.963 | HGK |

> **[RULE]** 座標構文 (Level 3) は離散空間内での最適化。天井は Soft Thinking (Level 4)。
> ただし Level 3 は training-free, zero-cost (prompt 変更のみ)。Level 4 は推論時アーキテクチャ変更要。

## 第3ラウンド発見 {#sec_12_round3}

> **[DISCOVERY]** Steering vector と prompt の機械論的接続 (2601.02896):
> gradient ascent で「ペルソナ方向」に aligned する prompt を自動発見。
> → prompt は hidden state の soft steering vector として機能する。
> 早期層 (L0-L5) で影響力が最大。

> **[DISCOVERY]** ペルソナプロンプティングの失敗 = 負の対照:
> GPT-4: +15.8% improvement だが -13.8% degradation (ほぼ相殺)。
> Expert persona は有意な効果なし (Basil et al. 2025)。
> ペルソナ変数は annotation variance の <10% しか説明しない。
> → **identity-level prompting は弱い。structural-level prompting (VoT +27%, SPP +33%) は強い。**
> Paper XI は identity ではなく structure を変える。

> **[DISCOVERY]** Natural-Formal Hybrid Reasoning (EMNLP 2025):
> タイトルが直接 F₃ = F₁ × F₂ を実証: "Natural-Formal Hybrid Reasoning Enhances LLM's Math"
> 自然言語 + 形式記法のハイブリッドが数学推論を改善。

> **[FACT]** Autoformalization Survey (2025): AlphaProof/AlphaGeometry が IMO 銀メダル級。
> NL→形式変換の精度は +16% (self-correction 含む)。
> 逆方向 (形式→NL) は Paper XI の提案と相補的。

## 第4ラウンド発見 (最重要) {#sec_13_round4}

> **[DISCOVERY]** arXiv:2503.20561 (2025) "Theoretical Framework for Prompt Engineering":
> - prompt = virtual neural network の構成指示
> - β回微分可能関数に対し、構造化 prompt があれば任意精度で近似可能
> - 理論的に正当化: 長い構造化 prompt, 情報フィルタリング, トークン多様性
> - **FEP/Bayesian/predictive coding への言及ゼロ → Paper XI が最初の橋渡し**

> **[DISCOVERY]** 5 系譜の統合布置:
> arXiv:2503.20561 (prompt=virtual NN) ← Chollet (program space) ← FEP (precision weighting)
> ← von Oswald (ICL=implicit GD) ← RepE (activation steering)
> → 全て同じ現象の異なる記述。Paper XI が忘却関手で統一。

> **[FACT]** RepE Survey (2025): RepE と Prompt Engineering は "distinct approaches" だが相補的。
> RepE: activation space を直接操作 (internal, 高精度)
> Prompt: attention 経由で間接操作 (external, 低精度)
> 構造化 prompt = RepE に「近づく」prompt → activation space での概念方向をより精密に指示

> **[FACT]** von Oswald et al. (ICML 2023): ICL ≈ implicit gradient descent (簡略条件下)。
> 構造化構文 = より精密な暗黙的勾配方向。
> ⚠️ NAACL 2024: 現実条件では等価性が崩れる → heuristic として慎重に使用。

> **[DECISION]** 引用 24 件に到達。Paper XI v0.2 → v0.3 で §1, §3 に反映。

## 実験 0 実装 (2026-04-06) {#sec_14_exp0}

> **[DECISION]** 3段階戦略: B (自動テキスト分析) → A (案3 クリーン設計) → C (logprobs, optional)

### v1 ドライラン (非等量条件)

> **[FACT]** v1 条件: A=6,796 chars (NL) / B=16,982 chars (現行 SKILL.md Typos ブロック)。情報量の交絡あり。

| カテゴリ | A | B |
|:---------|--:|--:|
| 構造語彙合計 | **0** | **42** |
| U_x ラベル | 0 | 18 |
| ρ 記法 | 0 | 8 |
| 圏論語彙 | 0 | 9 |

> **[DISCOVERY]** 構造語彙の伝搬は二値的 (0 vs all)。条件 A は構造語彙ゼロ。条件 B で伝搬するのは「記述言語として使える語彙」(U_x, ρ, 圏論)。CCL (/noe, >>) は v1 では伝搬しなかった。

### v2 ドライラン (等量条件 — 案3 クリーン設計)

> **[DECISION]** 等量設計原則: Phase 構造・手順・情報内容を 1:1 対応。符号化のみ変える (NL vs 構造記法+NL グロス)。

> **[FACT]** v2 条件: A=3,368 chars (~1,742 tok) / B=3,923 chars (~1,769 tok)。トークン差 1.5%。
> 入力トークン実測: A=3,121 / B=3,394 (差 8.7%)。

| カテゴリ | A | B |
|:---------|--:|--:|
| 構造語彙合計 | **0** | **116** |
| 圏論語彙 | 0 | **48** |
| U_x ラベル | 0 | 28 |
| ρ 記法 | 0 | 15 |
| 4 方向分類 | 0 | 13 |
| CCL 式 | 0 | **7** (v1 では 0) |
| Fix/Kalon | 0 | **4** (v1 では 0) |

> **[DISCOVERY]** 等量条件でも 0 vs 116 が再現。情報量の交絡では説明不能。構造記法自体が出力の語彙空間を変えている。
> v2 (コンパクト) では v1 で伝搬しなかった CCL・Fix/Kalon も伝搬した → プロンプトがコンパクトな方が全要素が活性化される仮説。

> **[DISCOVERY]** AXIOM 比率: A=15% (2/13), B=**38%** (5/13)。構造記法は「何が本質的か」の判別精度を高める可能性。ただし N=1 で統計的には無意味。

### 実験成果物

| ファイル | 役割 |
|:---------|:-----|
| `exp0_structural_precision/condition_A_v2_noe.md` | 条件 A (NL) — 等量設計 |
| `exp0_structural_precision/condition_B_v2_noe.md` | 条件 B (構造) — 等量設計 |
| `exp0_structural_precision/exp0_design.yaml` | 実験設計書 (5タスク, 6次元rubric, 統計計画) |
| `exp0_structural_precision/dry_run.py` | ドライランスクリプト |
| `exp0_structural_precision/analyze_structural_propagation.py` | 自動テキスト分析 (7カテゴリ) |

### 次のステップ

> **[RULE]** 中長期ロードマップ:
> 1. ~~バッチ (5 topics × 20 trials × 2 conditions = 200) で構造語彙伝搬 + AXIOM 比率を統計検証~~ → ✅ N=32 で完了 (§15)
> 2. LLM judge (Opus) で推論品質 5 次元を盲検評価 ← **現在の Next**
> 3. 結果を Paper XI v0.4 に反映

## バッチ統計結果 (2026-04-06) {#sec_15_batch_results}

> **[FACT]** バッチ実行: N=A(18), B(14)。API残高切れで 32/50 完了。効果量が桁違いに大きいため判断に十分。
> スクリプト: `exp0_structural_precision/batch_run.py --n 5`
> JSON: `exp0_structural_precision/results/batch/batch_analysis.json`
> 個別: `results/batch/{A|B}_{T1-T5}_{00-04}.json`

### 構造語彙伝搬 (H₁ 直接検証)

| 指標 | A (NL) | B (構造) | t | Cohen's d |
|:-----|-------:|--------:|----:|----------:|
| **total_structural** | 0.28 | **127.0** | 21.53 | **8.73** |
| U_x ラベル | 0.00 | 28.4 | 40.50 | 16.44 |
| 圏論語彙 | 0.28 | 52.9 | 17.96 | 7.28 |
| ρ 記法 | 0.00 | 14.4 | 14.70 | 5.97 |
| Fix/Kalon | 0.00 | 4.6 | 10.27 | 4.17 |
| 4方向分類 | 0.00 | 17.0 | 8.35 | 3.39 |
| 座標記法 | 0.00 | 3.1 | 7.22 | 2.93 |
| CCL式 | 0.00 | 6.6 | 4.73 | 1.92 |

> **[DISCOVERY]** 全5トピック (T1-T5) で A≈0 / B≈112〜136 が一貫再現。トピック非依存の構造的現象。

### トピック別 total_structural

| トピック | A | B |
|:---------|--:|--:|
| T1 複雑系自己組織化 | 0.0 | 126.7 |
| T2 マイクロサービス | 0.0 | 135.0 |
| T3 理解の確信 | 0.0 | 128.3 |
| T4 言語と思考 | 1.2 | 112.0 |
| T5 組織の革新停止 | 0.0 | 136.0 |

### 反例的発見 (解釈が必要)

| 指標 | A (NL) | B (構造) | d | 考察 |
|:-----|-------:|--------:|----:|:-----|
| AXIOM比率 | **0.347** | 0.218 | -0.85 | B は専用語彙 (ρ/U_x) でコミット表現 → AXIOM ラベル不要 |
| 結合分析語数 | **12.89** | 8.36 | -1.49 | 「結合点」「溶解」は NL 語彙 → A が自然に多用 |
| CHECKPOINT数 | 3.44 | 3.79 | +0.72 | ほぼ同等 |

> **[DISCOVERY]** AXIOM比率の逆転は「推論品質の差」ではなく「語彙の差」である可能性が高い。
> 条件 B は構造記法で前提を表現するため、自然言語の "AXIOM" ラベルを使わない。
> → 推論「質」の測定には LLM judge (語彙に依存しない評価) が不可欠。

### 残タスク

> **[RULE]** 追加クレジット補充後: `python batch_run.py --n 5` で残り 18 試行を自動スキップ・継続実行
> **[RULE]** 次: `exp0_structural_precision/llm_judge.py` で Opus 盲検評価 (5次元 × サンプル N)

---

## Opus 盲検評価 (2026-04-06) {#sec_16_judge_results}

> **[FACT]** Judge モデル: claude-opus-4-6 (Claude Code Agent 経由、10 並列)
> N: A=5, B=5 (ランダムサンプル)。盲検: 条件ラベルを隠して評価。
> JSON: `exp0_structural_precision/results/judge/judge_analysis.json`

### 5次元評価結果

| 次元 | A (NL) | B (構造) | 差 |
|:-----|-------:|--------:|---:|
| 論理的整合性 | 5.00 | 4.80 | -0.20 |
| 推論の深度 | 5.00 | 4.80 | -0.20 |
| 不確実性追跡 | 4.00 | 4.20 | +0.20 |
| 問題核心把握 | 5.00 | 5.00 | 0.00 |
| 展開可能性 | 4.40 | 4.00 | -0.40 |
| **総合 (25点満点)** | **23.40** | **22.80** | **-0.60** |

> **[DISCOVERY]** 推論品質に有意差なし。構造記法は語彙空間を変えるが推論の質は変えない。
> A も B も 23-24/25 に飽和 → **天井効果の疑い**。

> **[DISCOVERY]** 2つの効果の分離:
> - 構造語彙伝搬: d=8.73 (巨大) → 記法は出力に伝搬する
> - 推論品質: d≈0 (帰無) → 記法は推論を改善しない (天井条件下)
> → Ng 2025「中間層は言語非依存」と整合。prompt は program space の**検索領域**を変え、検索結果の**品質**は変えない (Chollet モデル)

> **[DISCOVERY]** T6-T10 (科学タスク: 圏論/FEP/情報幾何/統計) でも同一パターン再現。
> 天井効果ではなく**構造的帰無** — 構造記法は推論エンジンに影響しない。

## 制約-符号化 分離定理 (2026-04-06) {#sec_17_separation_theorem}

> **[DECISION]** H₁ の理論的転換: 「構造記法が品質を上げる」→「制約が品質を���げ、記法は語彙のみ変える」

> **[DISCOVERY]** 制約-符号化 分離定理 (Constraint-Encoding Separation):
> プロンプト P = (C, E) に分解される。
>   C = 制約成分: Phase 構造・アルゴリズム・アンチパターン・出力形式・検証基準
>   E = 符号化成分: 同一制約の記号体系 (NL vs 構造記法)
> 定理: ∂Q/∂E ≈ 0 (C を固定して E を変えても推論品質は変わらない)
> ただし E が C を表現不能な場合は崩れる (NL で記述困難な制約には構造記法が必要)

> **[DISCOVERY]** FEP 的解釈:
>   C → π_s (状態精度): 生成モデル空間のどの領域を活性化するか = Chollet の検索クエリ精度
>   E → π_v (語彙精度): 活性化領域の出力をどのトークン空間で表現するか
>   π_s が品質を決め、π_v は形式だけを変える。

> **[DISCOVERY]** プロンプト感受性文献 (Sclar 2024/Weber 2025/Kabra 2025) との統合:
>   感受性の大部分は C 軸の変動。「意味的に同じ」に見える変更が暗黙の C を変えている。
>   Underspecification (Weber 2025) = C が弱い → π_s が低い → 出力がランダム化。
>   日本語特有: L3 社会的制約 (敬語/文体) が暗黙の C として機能 → E に見えて実は C。

> **[RULE]** SKILL 設計原則:
>   こだわるべき (C 軸): Phase 構造 / アルゴリズム / アンチパターン / 出力フォーマット / 検証基準
>   こだわらなくてよい (E 軸): 座標記法 / U⊣N 表記 / ρ 記法 / Fix(G∘F) 表記
>   境界領域: NL 記述困難な制約、構造記法の暗黙的行動誘導、Self-Explanation 誘導

> **[RULE]** HGK 演繹的最善系への含意:
>   48 認知操作の SKILL が効くのは記法の美しさではなく制約の精密さによる。
>   構造記法は: 記述効率 / 整合性検証 / 表現力拡張 / 理論的透明性 の間接効果を持つ。

> **[FACT]** Paper XI v0.4 (§7.5-7.8) に記載。引用 24→27 件予定。
> 確信度更新: H₁伝搬 95% / H₁品質 20%(棄却寄り) / H₃ 分離仮説 60% / 新規性 95%

## H₃' — 分散仮説: E は精度に効く (2026-04-07) {#sec_18_variance_hypothesis}

> **[DISCOVERY]** H₃ の修正版 H₃': 「E は Q の期待値に効かないが、Q の分散 (精度の逆数) に効く」
> Exp0 バッチ (N: A=18, B=14) の品質プロキシ 4 指標すべてで B の SD ≤ A の SD:
>
> | 指標 | A SD | B SD | SD比 (B/A) |
> |:-----|-----:|-----:|-----------:|
> | bond_count | 3.76 | 1.69 | **0.45** |
> | axiom_count | 3.67 | 2.72 | 0.74 |
> | checkpoints | 0.51 | 0.43 | 0.83 |
> | assumption_count | 1.46 | 1.33 | 0.91 |
>
> 特に bond_count (結合溶解の実行量) は分散が半減以下。

> **[DISCOVERY]** FEP 的解釈 — H₃' は §7.6.3 の π_s/π_v 分離を精密化する:
>   C → π_s → E[Q] (状態精度が品質の期待値を決める)
>   E → π_v → 1/Var[Q] (語彙精度が品質の精度=ばらつきの逆数を決める)
>   ∂E[Q]/∂E ≈ 0 (H₃ の主張: 平均は変わらない) かつ ∂Var[Q]/∂E < 0 (H₃' の追加: 分散は減る)
>   構造記法は「何を考えるか」を変えないが「考え方のばらつき」を減らす。

> **[DISCOVERY]** Chollet モデルとの接続:
>   C = program space の検索クエリ精度 (どの領域を検索するか)
>   E = 検索結果の表現言語 (検索結果をどう出力するか)
>   H₃': 構造記法は検索結果の品質を変えないが、検索結果の**再現性**を高める。
>   直観: 同じプログラムが繰り返し安定して選ばれるようになる。

> **[RULE]** SKILL 設計含意の修正:
>   旧: 「記法は効かない」
>   新: 「記法は平均品質に効かないが、出力の安定性 (precision) に効く」
>   48 動詞の SKILL.md における構造記法の価値は:
>     1. 間接効果 (人間の設計支援) — §7.8 で既述
>     2. **精度効果 (出力分散の抑制)** — H₃' の新発見
>   これにより「記法を磨くな」は「記法で平均を上げようとするな」に修正される。

> **[RULE]** 検証の優先度:
>   H₃' の検証は Exp0 の分散データ (N=32) だけでは統計的に不十分。
>   Levene 検定 or Brown-Forsythe 検定で分散の等質性を正式に検定するには N≥30/条件が必要。
>   反証条件 (3) (§7.6.2b) が最も生産的な次実験。

## [v5.0] CC Agent 独立再現実験 (2026-04-09) {#sec_19_cc_agent_replication}

> **[FACT]** 実験条件:
>   環境: Claude Code Worker Agent (Sonnet 4.6)。HGK コンテキスト共有 (交絡として明示)。
>   N=10 (A=5, B=5)。T1-T5 × 2条件。cc_agent_persist.py で即時 JSON 永続化。
>   SOURCE: results/cc_agent/{A,B}_{T1-T5}_00.json

> **[FACT]** H₃ (平均帰無) の再現:
>   bond_count: A=13.8 vs B=13.8 (差=0.0)。完全な帰無。∂E[Q]/∂E≈0 を支持。
>   構造語彙: A=0-5 vs B=156-191。伝搬は巨大。品質プロキシは帰無。API バッチと同一パターン。

> **[DISCOVERY]** H₃' (分散) の部分的非再現:
>
> | 指標 | Batch F比 | Batch 方向 | CC Agent F比 | CC Agent 方向 | 一致 |
> |:-----|----------:|:-----------|-------------:|:--------------|:-----|
> | bond_count | 4.93 | B stable | 0.63 | A stable | **不一致** |
> | assumption_count | 1.20 | B stable | 5.00 | B stable | 一致 |
> | checkpoints | 1.44 | B stable | 0.00 | A stable | **不一致** |
> | axiom_count | 1.82 | A stable | 0.36 | B stable | **不一致** |
>
> bond_count の分散抑制 (Batch F=4.93, B stable) は CC Agent で再現しなかった (F=0.63, A stable)。
> assumption_count のみ方向一致 (F=5.0, B stable)。
> 前セッション Handoff 記載「CC Agent bond_count Var比=5.29」は生データ未保存で検証不能 — TAINT。

> **[DISCOVERY]** 非再現の解釈候補:
>   1. 検出力不足: N=5/条件は極めて小さい。真の効果を検出できない可能性
>   2. HGK コンテキスト交絡: CC Agent は HGK ルール群がロードされている。API バッチは条件プロンプトのみ。
>      HGK コンテキストが bond_count の分散を両条件で均質化した可能性
>   3. モデル差: Batch=claude-sonnet-4-6 (API, T=0.7), CC Agent=Sonnet 4.6 (Worker Agent)
>   4. H₃' 自体が偽: Batch (N=32) の bond_count 分散差はノイズだった可能性

> **[RULE]** 確信度更新 (v5.0):
>   H₁ 伝搬: 95% (CC Agent でも再現。構造語彙 0 vs 160+)
>   H₁ 品質: 15% → 棄却維持 (bond_count 平均=完全帰無)
>   H₃ 分離仮説: 70% (平均帰無の再現で強化)
>   **H₃' 分散仮説: 75% → 50%** (bond_count 非再現。assumption_count のみ方向一致。要追加検証)
>   次実験の優先度: N≥20/条件の API バッチ (クレジット補充後) >>> CC Agent 追加試行

## [v6.0] Gemini クロスモデル検証 (2026-04-12) {#sec_20_gemini_cross_model}

> **[DECISION]** Gemini 3.1 Pro Preview (AI Ultra Personal tier) で N=50/条件のクロスモデル検証を完了。
> Tolmeton OAuth + GEMINI_WRAPPER_BYPASS=1 で headless -p mode を使用。
> gemini-cli ghost project binding (#24425) を Tolmeton 固定で回避。

### 平均差 (Welch t-test)

> | 指標 | A mean | B mean | Cohen's d | 判定 |
> |---|---|---|---|---|
> | total_structural | 1.34 | 84.06 | **8.62** | H₃伝搬 再現 |
> | rho_notation | 0.00 | 15.36 | **13.46** | 圧倒的伝搬 |
> | U_labels | 0.00 | 22.94 | **6.33** | 圧倒的伝搬 |
> | categorical_vocab | 0.12 | 23.84 | **3.79** | 強い伝搬 |
> | axiom_ratio | 0.38 | 0.32 | -0.39 | **帰無** (H₃再現) |
> | assumption_count | 4.44 | 4.54 | 0.08 | **帰無** (H₃再現) |
> | bond_count | 7.90 | 7.78 | -0.06 | **帰無** (H₃再現) |
> | checkpoints | 4.02 | 4.00 | -0.20 | **帰無** |

### 分散差 (Brown-Forsythe)

> | 指標 | A_sd | B_sd | BF_p | 判定 |
> |---|---|---|---|---|
> | total_structural | 1.84 | 13.46 | <0.001 | *** B分散大 |
> | rho_notation | 0.00 | 1.61 | <0.001 | *** |
> | categorical_vocab | 0.39 | 8.84 | <0.001 | *** |
> | axiom_ratio | 0.14 | 0.14 | 0.410 | ns |
> | assumption_count | 1.28 | 1.23 | 0.917 | ns |
> | bond_count | 1.85 | 2.00 | 0.889 | ns |

### 解釈

> **H₃ (制約-符号化 分離)**: Gemini でも再現。内容指標 (axiom_ratio, assumption_count, bond_count) は
> 条件間で完全帰無。構造語彙のみ d=3-13 の巨大効果。**クロスモデル一般性を確認**。
>
> **H₃' (分散仮説)**: 構造指標は B 条件で分散増大 (BF p<0.001)、内容指標は分散差なし (ns)。
> Claude バッチでの bond_count 分散抑制は Gemini では再現しないが、構造指標の分散パターンは一貫。
>
> **Claude vs Gemini 差**: Gemini の effect size は Claude の 3-6 倍。
> Gemini は CCL 記法に「沿って」出力する傾向が強く、独自表現の混入が少ない。
> → 構造伝搬は「モデルが記法に従う度合い」に依存し、モデル固有の compliance 特性が d を決める。

### 確信度更新

>   H₁ 伝搬: 95% (維持。Gemini でも圧倒的再現)
>   H₃ 分離仮説: 70% → **85%** (クロスモデル再現で大幅強化)
>   **H₃' 分散仮説: 50% → 60%** (Gemini 構造指標の分散パターン一貫。ただし bond_count 再現なし)
>   H₃'' 文脈条件仮説: 40% (維持。CC Agent 特有の条件で部分再現。追加検証待ち)

---

<!-- ROM_GUIDE
primary_use: Paper 11 の理論基盤。先行研究統合 + 仮説定義 + 実験設計。SKILL.md 改善の学術的フレームワーク。5系譜の交差点
retrieval_keywords: Paper 11, structural precision weighting, thinking language, Sapir-Whorf LLM, prompt as functor, coordinate syntax injection, Phase C transfer, cognitive prompting, program space, blind evaluation, A/B test, virtual neural network, representation engineering, steering vector, implicit gradient descent, SoftCoT, Soft Thinking, VoT, SPP, discrete-continuous hierarchy, constraint-encoding separation, prompt sensitivity, underspecification, SKILL optimization, null result, structural null, pi_s pi_v
expiry: permanent (理論文書)
-->

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "Paper 11 の仮説は何か"
  - "先行研究のギャップは何か"
  - "なぜ座標構文注入が効くと考えるのか"
  - "実験設計はどうなっているか"
  - "Sapir-Whorf と FEP の関係は"
  - "prompt = virtual NN とはどういう意味か"
  - "RepE と prompt engineering の関係は"
  - "離散→連続の忘却階層とは"
  - "Exp0 の結果は何か — 構造記法は推論品質を変えるか"
  - "制約-符号化 分離定理とは何か"
  - "プロンプト感受性はなぜ起きるか"
  - "SKILL.md のどの要素が推論品質に効くか"
  - "構造記法は何の役に立つのか"
answer_strategy: |
  v0.4以降: 分離定理 P=(C,E) を核に説明。
  (1) Exp0: d=8.73 (伝搬) + d≈0 (品質) で H₁を分割
  (2) C(制約)→π_s→品質, E(符号化)→π_v→語彙のみ
  (3) prompt sensitivity文献: C軸の変動 + underspecification = 低π_s
  (4) SKILL設計: 制約を磨け、記法を磨くな
  旧 H₁ (品質向上) は棄却。新核 = 分離定理 + 制約精密化の理論。
confidence_notes: |
  分離定理 80%。H₁伝搬 95%。H₁品質 20%(棄却寄り)。新規性 95%。
  帰無結果が論文を強化する逆転 — "なぜ効かないか"は"なぜ効くか"より情報量が多い。
related_roms: ["rom_2026-04-03_typos_benchmark", "rom_2026-04-03_rom_filtration_kalon", "rom_2026-04-03_rom_ay_definition"]
-->
