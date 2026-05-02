# 02_手順｜Procedures

> **PURPOSE**: HGK の手順体系。ワークフロー (WF), スキル, マクロ, フック, テンプレート, CCL, 基準を格納。

## ディレクトリ構造

| ディレクトリ | 内容 |
|:-----------|:-----|
| `A_手順｜Workflows/` | 24動詞 WF + ユーティリティ WF (Ω/Δ/τ 3階層) |
| `B_WFモジュール｜WFModules/` | WF の再利用可能モジュール |
| `C_技能｜Skills/` | 24定理対応スキル (SKILL.md) |
| `D_マクロ｜Macros/` | CCL マクロ定義 (ccl-plan, ccl-fix 等 32個) |
| `E_フック｜Hooks/` | WF 実行前後のフック |
| `F_雛形｜Templates/` | 出力テンプレート |
| `G_CCL｜CCL/` | CCL 構造定義 |
| `H_基準｜Standards/` | 手順基準 |

## MAP
- `.agents/workflows/` — ランタイム WF 定義 (Agent が直接参照)
- [Boulēsis/02_解釈](../04_企画｜Boulēsis/02_解釈｜Hermeneus/) — Hermeneus Phase 設計書
- [Mekhane/03_解釈](../../20_機構｜Mekhane/03_解釈｜Hermeneus/) — WF 実行エンジン

---
*Created: 2026-03-13*
