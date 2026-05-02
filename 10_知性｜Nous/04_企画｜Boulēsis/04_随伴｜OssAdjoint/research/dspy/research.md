# DSPy 深掘り調査

> **優先度**: A
> **repo**: stanfordnlp/dspy
> **stars**: 32,400 (adjoint_map 記載値 — 要鮮度検証)
> **HGK 対象**: hermēneus (CCL コンパイラ)

## import_candidates

1. **MIPROv2 Bayesian 最適化 → WF プロンプト自動チューニング**
   - DSPy の `mipro_optimizer_v2.py` が Bayesian 最適化でプロンプトを磨く
   - HGK での用途: WF のプロンプトテンプレートの自動改善
   - 判定: [ ]

2. **Signature の宣言的 I/O → CCL 型システム強化**
   - DSPy の `Signature` は入出力を宣言的に定義
   - HGK での用途: CCL の型システム (入力→出力の明示化)
   - 判定: [ ]

## 調査対象ファイル

- [ ] `dspy/predict/predict.py` — 推論パイプラインの核
- [ ] `dspy/teleprompt/mipro_optimizer_v2.py` — Bayesian 最適化
- [ ] `dspy/signatures/` — 宣言的 I/O

## 判定

| candidate | 判定 | 理由 |
|:----------|:-----|:-----|
| MIPROv2 | [ ] | |
| Signature | [ ] | |

---

*Created: 2026-02-28*
