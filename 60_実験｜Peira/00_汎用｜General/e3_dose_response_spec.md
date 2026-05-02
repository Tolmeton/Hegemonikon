```typos
#prompt e3-dose-response-spec
#syntax: v8
#depth: L3

<:role: E3 実験仕様書 — Formal Prompt の用量反応実験
  E1 の結果を踏まえて別セッションで実行する大規模実験 :>

<:goal: 構造的圧縮度 (structural compression) と
  hidden-state structural encoding (ρ) の用量反応関係を定量化する :>

<:context:
  - [knowledge] 背景:
    Phase B CoT 実験: natural-language CoT は ρ を改善しない (partial ρ 0.249→0.203)
    論文 §7.1.2: "not inducible by natural-language CoT" — formal prompt は未検証
    理論的予測: recovery functor N は compositional constraints を通じて動作する
    → 構造的圧縮が高いほど N の活性化条件により近い

  - [knowledge] E1 との差異:
    E1 = 存在実験 (formal prompt は効くか? binary)
    E3 = 用量反応実験 (どの程度の形式性で効くか? spectrum)

  - [knowledge] 先行実験データ:
    bare (C0): partial ρ = 0.249 (layer 0)
    structure (C1): partial ρ = 0.248 (layer 0) — 統計的差なし
    step (C2): partial ρ = 0.203 (layer 0) — 有意に劣化
    モデル: CodeLlama-7B-Instruct, 4bit quantization
    データ: P3a benchmark (N=40 pairs)

  - [file] e1_formal_prompt_experiment.py — E1 実験スクリプト (E3 の基盤)
  - [file] cot_experiment.py — 既存 CoT 実験 (統計分析の再利用元)
/context:>

<:constraints:
  ## 実験設計

  ### 独立変数: 構造的圧縮度 (6水準)
  | 水準 | 条件名 | 圧縮度 | プロンプト例 |
  |------|--------|--------|-------------|
  | D0 | bare | 0 (なし) | コードのみ |
  | D1 | verbal_cot | 1 (最低) | "Step 1: This function..." |
  | D2 | structured_template | 2 | "Functions: 3, Loops: 2, Depth: 4" |
  | D3 | ccl_expression | 3 | "/noe>>/bou>>/ene" |
  | D4 | ccl_pipeline | 4 | "/noe_(/ske*/sag)>>/ene" |
  | D5 | categorical_notation | 5 (最高) | "Hom(A,B):f | F:C→C | η:A⇒B" |

  ### 従属変数
  - primary: best partial ρ (32層から最大)
  - secondary: ρ プロファイル (層別パターンの形状)
  - exploratory: 効く層の shift (formal prompt で best layer が変わるか)

  ### 仮説
  H0_E3: 圧縮度 D0-D5 と best partial ρ の間に単調関係はない
  H1_E3: 圧縮度が高いほど best partial ρ が単調に増加する

  ### 統計分析計画
  1. 6水準の best partial ρ に対する Spearman 相関
  2. D0 vs 各水準の paired permutation test (Bonferroni 補正 α=0.05/5)
  3. 隣接水準間の差 (D1-D0, D2-D1, ..., D5-D4) → 非線形性の検出
  4. Bootstrap CI (10,000 iterations) for Δρ
  5. Cohen's d for effect size

  ### サンプルサイズ計画
  - P3a: 40 pairs (既存データ) — 検出力: 中効果 (d=0.5) で power≈0.7
  - P3b: 60 pairs (拡張データ) — 検出力: 小効果 (d=0.3) で power≈0.6
  - 提案: P3a + P3b の両方で実行 (cross-validation)

  ### 制御変数
  - モデル: CodeLlama-7B-Instruct (4-bit)
  - 最大トークン長: 512
  - 乱数シード: 42
  - PCA 次元: 128

  ## 実行計画

  ### Phase 1: プロンプト設計 (E1 結果依存)
  - E1 結果を確認: CCL prompt が有効 → D3-D5 の設計を精緻化
  - E1 結果を確認: CCL prompt が無効 → D2 (structured template) に焦点を移す
  - D2 のテンプレート設計: AST 統計量 (関数数、ループ数、深度) + 制御フロー概要

  ### Phase 2: ベースライン抽出
  - D0 (bare) は Phase B の既存キャッシュを再利用可能
  - D1 (verbal_cot) は Phase B C2 の結果を再利用 (ρ=0.203)

  ### Phase 3: 新条件の実行
  - D2-D5 の hidden state 抽出 (GPU, 約30分/条件)
  - 全6条件の ρ プロファイル計算

  ### Phase 4: 用量反応分析
  - Spearman 相関 + 非線形性検出
  - 層別プロファイルの比較 (ヒートマップ)
  - 最適条件の特定

  ## 理論的意味
  - 用量反応が **正** → recovery functor N は compositional constraints の量に応答
    → T21 は "not CoT-inducible" に限定（形式的プロンプトは有効）
  - 用量反応が **平坦** → N は prompt 形式に依存しない
    → 構造的情報は事前学習で固定されており、プロンプトでは変わらない
  - 用量反応が **逆U字** → 過剰な形式性はノイズになる
    → 最適な圧縮度が存在する
/constraints:>
```

# E3 実験仕様書: Structural Compression 用量反応実験

## ステータス: E1 実験完了後に別セッションで実行

## 前提条件
- E1 実験の完了と結果の分析
- GPU マシン (34.146.167.24) へのアクセス
- `e1_formal_prompt_experiment.py` の検証済み実行

## 実行コマンド (予定)

```bash
# Phase 2: ベースライン確認
python e3_dose_response.py --dry-run --model codellama --bits 4

# Phase 3: 全条件実行
python e3_dose_response.py --model codellama --bits 4 --conditions all

# Phase 4: 用量反応分析 (結果JSON から)
python e3_dose_response.py --analyze e3_dose_response_codellama.json
```

## 結果の論文への統合先
- §7.1.2 (CoT probing) に E3 結果を追加
- §7.1.3 (新セクション?) として "Formal Prompt Dose-Response" を検討
- §8 future directions に結果を反映
