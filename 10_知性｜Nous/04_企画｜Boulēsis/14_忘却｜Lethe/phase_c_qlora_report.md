# Phase C: CodeLlama 13B QLoRA — CCL Structural Similarity 実験報告

> **実験日**: 2026-03-31
> **環境**: GCE `lethe-phase-c` (g2-standard-4, NVIDIA L4 24GB, us-central1-a)
> **元データ**: `~/phase_c_results/phase_c_qlora_results.json`
> **実行スクリプト**: `phase_c_qlora_run.py`

---

## 1. 実験設計

### 1.1 目的

Phase C-mini (CodeBERT 125M) の結果を大規模モデル (CodeLlama 13B) で再現検証する:

| 仮説 | 問い | 判定基準 |
|:---|:---|:---|
| **P11' (Scale)** | CodeLlama 13B QLoRA は CodeBERT 125M Structural Attention (ρ=0.963) に匹敵するか | Δρ vs 0.963 |
| **P14 (L_Ξ at scale)** | L_Ξ 正則化の効果はモデル規模に依存するか | 条件 B (λ=1.0) vs 条件 A (λ=0) |
| **P15 (baseline)** | QLoRA 事前 baseline (ρ=0.2444) からの改善幅 | Δρ vs 0.2444 |

### 1.2 アーキテクチャ

```
Code → [CodeLlama 13B (QLoRA, r=16, α=32)] → hidden_states
     → [Contrastive Head] → similarity ∈ [0, 1]
```

- **QLoRA**: 4-bit quantization + LoRA (r=16, α=32, dropout=0.1)
- **データセット**: `phase_c_training_ccl.jsonl`
- **評価**: Spearman ρ, 偏 ρ (コード長除去)

### 1.3 条件設計

| 条件 | λ | ステップ | ~時間 | 意味 |
|:---|:---|:---|:---|:---|
| A (ベースライン) | 0.0 | 250 | ~3.6h | L_Ξ なし — QLoRA 単体の表現学習 |
| B | 1.0 | 250 | ~3.6h | L_Ξ あり — CCL 構造正則化付き |

### 1.4 比較ターゲット

| モデル | 手法 | ρ | Phase |
|:---|:---|:---|:---|
| CodeBERT 125M | Structural Attention (hybrid λ=1.0) | 0.963 | C-mini |
| CodeBERT 125M | Attentive Probe | 0.745 | B2 |
| CodeLlama 13B | QLoRA 事前 (fine-tune 前) | 0.2444 | C baseline |

---

## 2. 結果

<!-- 結果到着後に記入 -->

### 2.1 条件別比較

| 条件 | ρ (mean) | 偏ρ (mean) | Δρ (vs baseline 0.2444) | Δρ (vs C-mini 0.963) |
|:---|:---|:---|:---|:---|
| A (λ=0.0) | <!-- FILL --> | <!-- FILL --> | <!-- FILL --> | <!-- FILL --> |
| B (λ=1.0) | <!-- FILL --> | <!-- FILL --> | <!-- FILL --> | <!-- FILL --> |

### 2.2 P14 判定: L_Ξ 効果

| 指標 | 条件 A | 条件 B | Δ | 判定 |
|:---|:---|:---|:---|:---|
| ρ | <!-- FILL --> | <!-- FILL --> | <!-- FILL --> | <!-- FILL: 支持/不支持/不明 --> |

### 2.3 スケール効果

| 比較 | ρ 小 | ρ 大 | Δ | 解釈 |
|:---|:---|:---|:---|:---|
| CodeBERT vs CodeLlama (λ=0) | 0.958 | <!-- FILL --> | <!-- FILL --> | <!-- FILL --> |
| CodeBERT vs CodeLlama (λ=1) | 0.963 | <!-- FILL --> | <!-- FILL --> | <!-- FILL --> |

---

## 3. 解釈

<!-- FILL: 結果到着後に記入 -->

### 3.1 仮説検証

- **P11' (Scale)**: <!-- FILL -->
- **P14 (L_Ξ at scale)**: <!-- FILL -->
- **P15 (baseline)**: <!-- FILL -->

### 3.2 知見

<!-- FILL -->

### 3.3 次のステップ

<!-- FILL -->

---

## 4. 実行メタデータ

| 項目 | 値 |
|:---|:---|
| PID | 1667 |
| 開始 | 2026-03-31 14:58 JST |
| 完了 | <!-- FILL --> |
| GPU mem | 7.33 / 24 GB |
| コスト概算 | ~$0.70/h × <!-- FILL --> h = $<!-- FILL --> |
| result_json | `~/phase_c_results/phase_c_qlora_results.json` |
| 回収コマンド | `gcloud compute scp lethe-phase-c:~/phase_c_results/phase_c_qlora_results.json . --project=project-04762300-3537-489b-80b --zone=us-central1-a` |
