---
rom_id: rom_2026-04-02_oblivion_ceiling_empirical
session_id: e12e3d9d-7d23-456b-b820-0ef2773eca6e
created_at: 2026-04-02 21:25
rom_type: distilled
reliability: High
topics: [oblivion_theory, effect_size_ceiling, rho_estimation, K_estimation, BBH, prompt_engineering, ANOVA]
exec_summary: |
  忘却論 Paper IV の天井公式 r≤√(ρ/(K+1)) を BBH 公開データで独立検証。
  ρの多層構造 (macro/meso/micro) を発見。K∈[5,8]で構造的整合。
  次ステップ: ρ_fine の独自API実験による直接測定。
---

# 効果量天井公式の経験的検証

## 1. 天井公式 (定理 3.1.1)

> **[RULE]** r_obs ≤ √(ρ_spec / (K+1))
> - ρ_spec: スペクトラム効率 (プロンプトが説明する分散割合)
> - K: 交絡因子数 (温度, トークン化, コンテキスト窓 etc.)
> - r_obs: 観測される効果量

逆推定値 (Paper IV): ρ ≈ 0.3, K ≈ 8 → r ≤ 0.18 (18.3%)

## 2. ρ の独立推定 (実験1)

> **[FACT]** η²_prompt = 0.52 (BBH 23タスク, 3モデル×2条件, 2要因ANOVA)
> - 平均: 0.5204, SD: 0.2224, 中央値: 0.5931
> - 範囲: [0.002 (boolean_expressions), 0.843 (penguins_in_table)]
> - η²_model = 0.3541
> - データソース: Suzgun et al. (2022) Table 2

> **[DECISION]** η²=0.52 は AO vs CoT の「最大効果」→ ρ の上界推定
> 逆推定値 0.30 は CoT 内微調整スケールの推定として依然妥当

> **[DISCOVERY]** ρ はタスク依存パラメータ (SD=0.22)
> 公式を壊すのではなく精密化する: 天井はタスクの「プロンプト感受性」に依存

## 3. K の独立推定 (実験2)

> **[FACT]** Forward Selection (ΔR²>0.02) の結果:
> Step 1: multi_step → ΔR²=0.144
> Step 2: knowledge → ΔR²=0.042
> Step 3: reasoning → ΔR²=0.008 → STOP

> **[DECISION]** K_task=2 + K_env=3 (temperature, tokenization, context_window) = K_total=5
> K ∈ [5, 8]。独立推定5は下界、逆推定8は上界。構造的に整合。

## 4. ρ_fine の推定 (実験3: CoT 内微細変種)

> **[FACT]** CoT 内のモデル間変動 SS_within_CoT = 8894 (全変動の14.1%)
> プロンプト微調整効果 ≈ モデル間変動の 1/4 と概算

| 推定 | ρ_fine | r_ceiling (K=8) | r_ceiling (K=5) |
|:-----|:-------|:----------------|:----------------|
| 保守 (1/5) | 0.028 | 5.6% | 6.8% |
| **中央 (1/4)** | **0.035** | **6.3%** | **7.7%** |
| 楽観 (1/3) | 0.047 | 7.2% | 8.9% |

> **[DISCOVERY]** ρ の多層構造:
> - ρ_macro ≈ 0.52: AO vs CoT (方式レベル)
> - ρ_meso ≈ 0.30: 逆推定値 (方法論レベル)
> - ρ_micro ≈ 0.035: CoT 内微調整 (実務レベル)
> 天井公式は全スケールで成立。スケール選択が天井の高さを決定する。

## 5. 未解決: ρ_fine の直接測定

> **[CONTEXT]** 現在の ρ_micro ≈ 0.035 は「モデル間変動の1/4」という概算に依存。
> 独自 API 実験で直接測定する必要がある。

### 実験設計 (未実行)

**概要:** BBH サブセット × 5+ プロンプト変種 → η²_within_CoT を直接算出

**タスク選定 (3タスク):**
- temporal_sequences (η²=0.57, 高感受性)
- formal_fallacies (η²=0.22, 中感受性)
- boolean_expressions (η²=0.002, 低感受性)

**プロンプト変種 (5+):**
1. 標準 CoT (Suzgun et al. のプロンプトそのまま)
2. CoT + "Let's think step by step"
3. CoT + ペルソナ ("You are an expert logician")
4. CoT + フォーマット指定 ("Answer in JSON format")
5. CoT + self-consistency (majority vote over 5 samples)
6. CoT + 例示変更 (異なる few-shot examples)

**実行方法:**
- ochema ask (mode=cortex) で Gemini Flash を使用
- 各条件 250 問 × 5 変種 × 3 タスク = 3,750 回
- η²_fine = SS_between_variants / SS_total → ρ_fine の直接推定

**判定基準:**
- ρ_fine ∈ [0.02, 0.10] → 概算値 0.035 を支持
- ρ_fine < 0.01 → プロンプト微調整はほぼ無意味 (天井 < 3%)
- ρ_fine > 0.10 → 概算値は過小。天井は 10%+ に拡大

## 6. Paper IV の状態

> **[FACT]** Paper IV v1.3 に §7.4.1–7.4.3 追記済み
> ファイル: 10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/paper_IV_draft.md
> 参考文献: Suzgun et al. (2022) 追加済み

## 関連情報
- 関連 WF: /pei (実験), /tek (設計), /noe (統合分析)
- 関連 KI: hegemonikon_theoretical_foundations (公理系)
- 関連 Session: e12e3d9d-7d23-456b-b820-0ef2773eca6e

<!-- ROM_GUIDE
primary_use: 忘却論天井公式の検証状態と次ステップの復元
retrieval_keywords: oblivion ceiling rho K eta BBH prompt engineering effect size ANOVA
expiry: permanent
-->
