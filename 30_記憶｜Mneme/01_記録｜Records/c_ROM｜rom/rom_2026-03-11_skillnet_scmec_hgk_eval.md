---
rom_id: rom_2026-03-11_skillnet_scmec_hgk_eval
session_id: 426036e9-3355-4668-b437-68ceceea951b
created_at: 2026-03-11 17:02
rom_type: rag_optimized
reliability: High
topics: [SkillNet, SCMEC, HGK評価, FEP演繹, 行為可能性, affordance, Skill品質]
exec_summary: |
  SkillNet SCMEC で HGK 4 Skill を評価 → Cost-awareness が体系的弱点。
  Creator 指摘: HGK は HGK で評価すべき。FEP から 6 評価軸を演繹スケッチ。
  Creator 直感: 行為可能性の最大化 × 座標分解 = 各族テーゼ。
---

# SkillNet SCMEC × HGK 評価軸演繹 {#sec_01_overview}

> **[FACT]** SkillNet 論文 (arXiv:2603.04448) を分析し、SDK (skillnet-ai) の疎通を確認した。

> **[FACT]** SCMEC 5次元 (Safety/Completeness/Executability/Maintainability/Cost-awareness) で 4 Skill を評価:

| Skill | S | C | E | M | Cost | Score |
|:------|:-:|:-:|:-:|:-:|:----:|------:|
| V03 Zētēsis | ◎ | ◎ | ◎ | ◎ | ◎ | 5/5 |
| FEP Engine | ◎ | ◎ | ◎ | ◎ | △ | 4/5 |
| V01 Noēsis | ◎ | ◎ | ◎ | ◎ | △ | 4/5 |
| V08 Tekhnē | ◎ | ◎ | △ | ◎ | ✗ | 3/5 |

## SCMEC の限界 {#sec_02_scmec_limits}

> **[DECISION]** SCMEC は HGK Skill の評価に不十分。Creator: 「HGK の評価はHGK体系でするべき。評価できないのは体系の欠陥」

- Kalon (Fix(G∘F)) が評価軸に不在
- Gnōsis (認識価値 = EFE epistemic) が不在
- Safety の粒度が HGK (N-4 + WBC) と不一致

## FEP 演繹 6 評価軸 (スケッチ) {#sec_03_six_axes}

> **[DISCOVERY]** FEP から 6 軸を演繹可能:

| FEP 項 | 評価軸 | 意味 |
|:-------|:-------|:-----|
| VFE: -Accuracy | 精度 (Akribeia) | prediction error 最小 |
| VFE: Complexity | 簡潔 (Parsimonia) | 必要最小限の構造 |
| EFE: epistemic | 認識価値 (Gnōsis) | 実行で何を学ぶか |
| EFE: pragmatic | 行為価値 (Praxis) | 実行で何を達成するか |
| Kalon: Fix(G∘F) | 不動点 (Kalon) | G∘F 安定性 |
| Kalon: Generative | 生成力 (Poiesis) | 3+ 派生可能性 |

## Creator 直感: 行為可能性 × 座標分解 {#sec_04_affordance}

> **[DISCOVERY]** 「恐らく行為可能性の最大化に行き着く (Flow の定理)。座標ごとの定義が各族のテーゼになる」

EFE pragmatic value の座標分解として:
- Telos (Value): 内部↔外部の行為可能性
- Methodos (Function): 探索↔活用の行為可能性
- Krisis (Precision): 確実↔不確実の行為可能性
- Diástasis (Scale): 微視↔巨視の行為可能性
- Orexis (Valence): 正↔負の行為可能性
- Chronos (Temporality): 過去↔未来の行為可能性

## 体系的弱点: Cost-awareness {#sec_05_cost}

> **[DECISION]** Anti-Skip Protocol の硬直性が根本原因。V03 Zētēsis の Kill Criteria パターンが唯一 Good。

改善候補: 早期離脱ゲート / Progressive Loading / Token Budget 明示

## 次のアクション {#sec_06_next}

> **[RULE]** FEP + 圏論から WF/動詞/族の評価軸を演繹的に導出する。行為可能性の座標分解が鍵。

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "HGK Skill の品質評価方法"
  - "FEP から評価軸を演繹"
  - "SCMEC と HGK の対応関係"
  - "行為可能性と座標分解"
answer_strategy: "FEP の VFE/EFE 分解 → 6 軸。Creator 直感: affordance × 座標 = 族テーゼ"
confidence_notes: "6 軸はスケッチ段階。演繹の正式化は未完了"
related_roms: []
-->
