---
rom_id: rom_2026-03-31_phase_c_bou_input_format
session_id: hyphe_phase_c_bou
created_at: 2026-03-31
rom_type: distilled
reliability: High
topics: [Phase_C, input_format, QLoRA, CCL, structural_attention, U_adjoint_N, CodeLlama, ablation, Boulesis, Hyphe, Lethe]
exec_summary: |
  Phase C の入力形式を /bou で意志確定。4候補 (A: raw CCL / B: Code+CCL並置 /
  C: CCL専用vocab / D: Code→構造学習) を U⊣N 随伴の方向問題として整理。
  C を除外し A/B/D 3条件比較を Colab Pro+ で実行する意志を確定。
  Phase C-mini (ρ=0.963) は実は D方式であり「CCL直接入力」ではないという再認識。
---

# Phase C 入力形式の意志確定 — U⊣N 方向問題としての 4候補 {#sec_01_main}

## [DECISION] A/B/D 3条件比較で Phase C の定義を実験的確定 {#sec_02_decision}

| 候補 | 入力 | U⊣N 方向 | 化学比喩 | 判定 |
|:-----|:-----|:---------|:---------|:-----|
| **A** Raw CCL テキスト | CCL 文字列 → embedding | N 方向 (CCL→表現) | SMILES 記法 | ✅ 即実行 |
| **B** Code+CCL 並置 | Code + CCL 両方 → embedding | 両方向同時 | 構造式+分子名併記 | ✅ 即実行 |
| **C** CCL 専用 vocab | 専用 tokenizer → embedding | N 方向 (純粋) | 独自化学記号 | ❌ 除外 (事前学習不可) |
| **D** Code→構造学習 | Code → QLoRA → CCL 構造理解 | U 方向 (Code→構造) | X線結晶構造解析 | ✅ 即実行 (既存) |

**根源的洞察**: 入力形式の選択は技術的選択ではなく、**U⊣N 随伴のどちら側からアプローチするか**という理論的問題。

## [DISCOVERY] Phase C-mini は D方式 — 「CCL直接入力」ではない {#sec_03_discovery}

Phase C-mini (ρ=0.963) のアーキテクチャ:
```
Code → [CodeBERT 凍結 L12] → hidden_states → [Structural Attention] → similarity
```

これは **Code を入力し、CodeBERT の内部表現に CCL 構造を後付けアテンションで読み出す** = D方式。
CCL テキストを直接入力していない。「構造式を読ませる」ではなく「分子式を読んだ脳波にフィルタをかけた」。

**真の Phase C (A方式)** = CCL テキスト `¥ >> sorted >> F:[each]{fn} >> #` をそのまま transformer に入力。
これは**まだ誰もやっていない**。

## [DISCOVERY] /u+ 分析: Phase C (B) vs 49d改良 (A) のσ比較 {#sec_04_sigma}

Phase C のσが明確に高い根拠 (3本の独立した矢印):

1. **CodeBERT 反転**: 線形ρ≈0 → 注意的ρ=0.745 — attention は系列から構造を読める
2. **化学の同型**: 構造式 > 分子式は原理的 — カウント精緻化は本質的限界内
3. **テンソル積実験**: 453d でも baseline 未達 — カウント空間拡張には天井がある

Path A (統計的化合物発見) は Phase C の**事後的解釈ツール**として位置づけ:
transformer の attention 可視化 → 「どの CCL パターンに注目するか」= 統計的に発見された普遍的化合物

## [DECISION] /bou 意志: 3条件 + baseline の4条件比較 {#sec_05_will}

```
条件0: Phase C-mini (CodeBERT 125M, D方式) — ρ=0.963 (既存ベースライン)
条件A: CodeLlama 7B QLoRA + raw CCL テキスト入力
条件B: CodeLlama 7B QLoRA + Code+CCL 並置入力
条件D: CodeLlama 7B QLoRA + Code入力→CCL構造学習 (phase_c_v2.py 既存)
```

- 衝動スコア: 25/100 (熟慮された意志)
- T1-T3: 全合格
- 実行環境: Colab Pro+ A100, 推定 1条件 2-4時間, 1日完走可能

## [CONTEXT] 既存アセット {#sec_06_assets}

| アセット | パス | 状態 |
|:---------|:-----|:-----|
| Phase C-mini 結果 | `14_忘却｜Lethe/phase_c_mini_report.md` | ρ=0.963 確定 |
| Phase C v2 スクリプト (D方式) | `14_忘却｜Lethe/experiments/phase_c_v2.py` | CodeLlama 7B QLoRA 実装済み |
| 学習データ | `experiments/phase_c_training_ccl.jsonl` | 246ペア |
| QLoRA notebook | `experiments/phase_c_qlora_v2.ipynb` | 存在 |
| Code→CCL トランスパイラ | `mekhane/symploke/code_ingest.py` | 稼働中 |

## [CONTEXT] 49d 浄化実験からの前提知識 {#sec_07_49d}

- 49d = 分子式 (カウントベクトル)。構造異性体の区別不可
- 22d 演繹核: R@1=0.4% で壊滅。アドホック次元が「偶然の化合物」として結合パターンを暗黙エンコード
- テンソル積 (2次/3次): baseline 未達。カウント空間の限界は原理的
- 8つの CCL 演算子 (>>, ~, *, %, ^, \, |, &) = 8種の化学結合

→ Phase C は「構造式を直接読む」= この限界を超える唯一の道

## 関連情報
- 前提 ROM: `rom_2026-03-31_49d_purification_chemistry.md`
- Phase C-mini: `14_忘却｜Lethe/phase_c_mini_report.md`
- Phase C v2: `14_忘却｜Lethe/experiments/phase_c_v2.py`
- Hyphē README: `11_肌理｜Hyphē/README.md`

<!-- ROM_GUIDE
primary_use: Phase C 実験設計時の前提知識。入力形式 A/B/D の定義と U⊣N 方向問題
retrieval_keywords: Phase C, input format, raw CCL, Code+CCL, QLoRA, CodeLlama, ablation, U adjoint N, structural attention, SMILES, chemistry analogy
expiry: permanent
-->

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "Phase C の入力形式は何がある？"
  - "Phase C-mini と Phase C v2 の違いは？"
  - "なぜ 49d を捨てて Phase C に進むのか？"
answer_strategy: 4候補 A/B/C/D を U⊣N 方向で分類し、C 除外の理由と共に説明。Phase C-mini が D方式であることを強調
confidence_notes: /bou で意志確定済み。衝動スコア 25/100。実験設計はこれから
related_roms: ["rom_2026-03-31_49d_purification_chemistry"]
-->
