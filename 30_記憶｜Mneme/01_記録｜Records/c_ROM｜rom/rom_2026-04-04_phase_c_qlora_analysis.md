---
rom_id: rom_2026-04-04_phase_c_qlora_analysis
session_id: phase_c_qlora_analysis_5chain
created_at: 2026-04-04
rom_type: distilled
reliability: High
topics: [Phase_C, QLoRA, N_compose_U, structural_attention, CodeLlama, representation, architecture, ablation, nonlinear_amplification, adjunction]
exec_summary: |
  Phase C v2 QLoRA (ρ=0.857) vs C-mini Structural Attention (ρ=0.963) の Δρ=0.106 を
  /his→/akr→/lys→/noe→/his の5連鎖で分析。
  核心発見: 認識 = N∘U (回復関手∘忘却関手)。U の質が N の効果を非線形に増幅/飽和させる。
  ただし U と N は完全に直交しない — 49d は SA 専用形式であり QLoRA には流し込めない。
  Phase C v3 (A/B/D 3条件) は設計+データ準備済み・未実行。v3 は U の変分のみで N は固定。
  2×2 交差実験 (U×N) なしでは N∘U の寄与分離は不能。
---

# Phase C QLoRA 結果分析 — N∘U 仮説と U/N 非直交性 {#sec_01_main}

## [DECISION] Δρ=0.106 の因果構造: E1→E2→E3 {#sec_02_causal}

| 因子 | 独立変数 | 寄与推定 |
|:-----|:---------|:---------|
| E1 表現形式 | テキスト (BPE) vs 49d ベクトル | 主因 60-70% |
| E2 注入経路 | トークンアテンション vs 専用構造空間 | 副因 20-30% |
| E3 パラメータ効率 | 13M汎用 vs 2M構造特化 | E2 の帰結 |
| E4 データ条件 | 1000 vs 246 ペア | 反証的 (≤0%) |

因果連鎖: E1→E2→E3。表現形式の選択が注入経路を制約し、パラメータ効率に波及。
データ量 4倍差はアーキテクチャ差を覆せなかった。

## [DISCOVERY] 認識 = N∘U (回復∘忘却) {#sec_03_compose}

「表現が認識を制約する」は半分正しく半分不完全。正確な構造:

```
認識 ρ = f(U_encoding, N_architecture)

U: 入力信号の忘却関手 (何を保存し何を捨てるか)
N: 回復関手 (忘却された構造をどこまで復元できるか)

Phase C-mini: U_49d (構造保存的) × N_SA (構造特化) = 0.963
Phase C v2:   U_BPE (構造分散的) × N_LoRA (汎用)   = 0.857
Phase B2:     U_49d (構造保存的) × N_probe (制限的) = 0.745
Baseline:     U_BPE (構造分散的) × N_none            = 0.244
```

非線形増幅: U が保存的なとき N の効果が増幅 (0.74→0.96)。U が分散的なとき N の効果が飽和 (0.24→0.86)。

## [DISCOVERY] BPE は「破壊」ではなく「分散」 {#sec_04_dispersion}

Phase B2 の Attentive Probe (ρ=0.745) = BPE で分散した構造情報をアテンションで部分的に再集約できる。
構造情報は消えるのではなくトークン列全体に散布される。
この知見は A1 前提の精密化: 「BPE が構造を破壊する」→「BPE が構造を分散させる」。

## [DISCOVERY] U と N の非直交性 {#sec_05_nonorthogonal}

2×2 交差実験の理想:

|              | N_LoRA (汎用) | N_SA (構造特化) |
|:-------------|:--------------|:----------------|
| U_49d (ベクトル)  | ❓ 未実験     | C-mini: 0.963   |
| U_BPE (CCLテキスト) | v2: 0.857    | ❓ 未実験       |

しかし 49d は SA の専用入力形式であり QLoRA のトークンパイプラインに流し込めない。
つまり U を変えると N も変わらざるを得ない — U と N は完全には直交しない。
この交絡こそが「非線形増幅」の正体かもしれない。

随伴対 U⊣N の性質: 忘却関手と回復関手は独立に選択できない。
U を選んだ瞬間に N の自然な選択肢が制約される。

## [CONTEXT] Phase C v3 の状態 {#sec_06_v3_status}

- 設計: phase_c_v3.py — A/B/D 3条件 (CCLのみ/Code+CCL/Codeのみ)
- データ: 7ファイル生成済み (条件×本実験+診断)
- 結果: **未生成** (phase_c_v3_results.json なし, EXPERIMENTS.md §24 なし)
- v3 は N を固定 (全条件 QLoRA) して U だけを変える実験
- N の変分には右列 (N_SA + テキスト入力) が必要だが未設計

## [CONTEXT] 未検証の問い {#sec_07_open}

1. U_BPE ∘ N_SA: テキスト入力 + Structural Attention → 2×2 右上セル
2. N のスケーリング限界: 13B→70B で天井は上がるか (P42)
3. データ量のスケーリング: 1000→10000 で QLoRA は改善するか
4. ρ_ccl > ρ_49d が成立するか (v3 の核心仮説)

## 関連 ROM
- `rom_2026-03-31_phase_c_bou_input_format.md` — A/B/D 設計の意志確定
- `rom_2026-03-31_phase_c_v3_defect_fixes.md` — v3 欠陥修正
- `rom_2026-03-31_49d_purification_chemistry.md` — 49d = 分子式

<!-- ROM_GUIDE
primary_use: Phase C 実験結果の解釈と次ステップ判断。N∘U 仮説の前提知識
retrieval_keywords: Phase C, QLoRA, N compose U, representation, architecture, nonlinear amplification, BPE dispersion, adjunction, non-orthogonal, 2x2 crossing
expiry: permanent
-->
