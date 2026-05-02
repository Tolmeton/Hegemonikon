---
rom_id: rom_2026-03-15_embedding_precision
session_id: unknown
created_at: "2026-03-15 17:41"
rom_type: rag_optimized
reliability: Medium
topics: ["Matryoshka", "1.", "v1-v2"]
exec_summary: |
  Okay, I will summarize the conversation history, preserving key decisions, TODOs, open questions, constraints, requirements, file paths, and code references.

**Summary of Precision Separation Experiments using Chemical Separation Methods**

The experiments aim to separate precision in Matryoshka models using an analogy to chemical separation. The initial Matryoshka v1-v2 had structural limitations. The idea is to treat the semantic space as a "solution" and information as a "solute," using chemical separation methods to isolate precision. Five experiments were conducted: salting out (塩析), electrophoresis (電気泳動), isoelectric focusing (IEF), centrifugation (遠心分離), and chromatography (クロマトグラフィー).

**v1 Results (8 samples):**

*   Electrophoresis (電気泳動) (center of gravity deviation): ρ=+0.71, range=0.093 (✅)
*   Chromatography v3 (クロマト v3) (2 anchors): ρ=+0.69, range=0.114 (✅)
*   IEF v1 (text type anchor): ρ=+0.10, range=0.190 (⚠️ Anchor design issue)
*   Salting out (塩析) (perturbation resistance): ρ=-0.33, range=0.024 (⚠️)
*   Centrifugal separation (遠心分離) (norm): range=0.000 (❌ Died due to normalization)

**v2 IEF Improvement:**

*   v1 anchor: "text type" (factual, emotional...) → Became topic classification
*   v2 anchor: "precision gradient" (precise/vague pair ×4 axes: technology/procedure/concept/judgment)
*   Result: ρ: +0.10 → +0.60. Ensemble ρ=+0.93 (optimal weights E=0.0, C=0.7, I=0.3)

**v3 Robustness Test (20 samples):**

*   High×7, Medium×7, Low×6
*   Optimal ensemble: ρ=+0.89 (E=0.2, C=0.3, I=0.5)
*   Complete separation achieved: high-medium gap=+0.020, medium-low gap=+0.011
*   IEF pattern `----` = perfect indicator of low precision (zero false positives)
*   IEF v2 became dominant with increased samples (weight 0.3→0.5)

**Benefits:**

1.  Context Rot: Step count → adaptive distillation based on information density
2.  Hyphē: kNN alone → ensemble of 3 independent signals
3.  CCL: Static depth → input precision-based dynamic routing
4.  Sekisho: LLM subjectivity → quantitative precision gate
5.  IEF `----`: High-speed low-precision filter
6.  FEP: 3 methods correspond to Value/Precision/Function coordinates

**Scripts:**

*   /tmp/chemistry\_separation\_experiments.py (v1: 5 experiments)
*   /tmp/chem\_v2\_ief\_ensemble.py (v2: IEF improvement + ensemble)
*   /tmp/chem\_v3\_robustness.py (v3: 20 sample robustness)
*   Result JSON: /tmp/chem\_v3\_robustness.json
---

# 化学的分離法アナロジーによる embedding precision 分離実験。IEF v2 アンカー改善 + 3手法アンサンブルで ρ=0.89 達成。20サンプル robustness テスト完了。

> このセッションでは 1 ターンの会話が行われた。


## 決定事項
- なし


## 発見・知見
- なし


## 背景コンテキスト
- なし


## 関連情報
- 成果物: 1. Matryoshka v1-v2 が構造的限界 (ノルム正規化で分散ゼロ)

## Critical Rules (SACRED_TRUTH)
<hgk-critical-rules>
- FEP: 予測誤差の最小化・能動推論を最優先
- Kalon: Fix(G∘F) 不動点を追求する
- Tapeinophrosyne: prior の precision を下げ、感覚入力の precision を上げる (view_file 必須)
- Autonomia: 違和感を表出し、自動化ツールを駆使する
- Akribeia: 精度最適化。SOURCE と TAINT を区別し、読み手が行動できる出力にする
- 破壊的操作 (rm, mv, .env上書き等) の前には必ず提案し同意を得る
</hgk-critical-rules>

<!-- ROM_GUIDE
primary_use: セッション復元
retrieval_keywords: 1., Matryoshka, v1-v2
expiry: "permanent"
-->
