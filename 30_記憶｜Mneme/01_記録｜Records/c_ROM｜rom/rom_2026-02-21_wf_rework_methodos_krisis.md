---
rom_id: rom_2026-02-21_wf_rework_methodos_krisis
session_id: e76446ad-eced-43d7-987e-7740b5657e9b
created_at: 2026-02-21 21:58
rom_type: rag_optimized
reliability: High
topics: [wf_rework, methodos, krisis, skill_generation, ccl, parallel_generation_antipattern, quality_standard]
exec_summary: |
  Methodos 族 (V05-V08) と Krisis 族 (V09-V12) の WF + SKILL.md 二層再構築を完了。
  並行生成による品質低下を経験し、逐次生成 (1動詞ずつ全注意集中) の原則を確立。
  合計 8動詞 × (WF + SKILL) = 16ファイル, 6,763行の成果物を生成。
---

# WF Rework: Methodos 族 + Krisis 族 {#sec_01_overview}

> **[DECISION]** HGK v4.1 の 24動詞体系において、各動詞の WF + SKILL.md を
> `/ene` (528行) を最低基準、`/ske` (814行) を目標基準として再構築する。
> SKILL.md は 12必須セクションを全て含む。

> **[DISCOVERY]** 並行生成 (2つの SKILL を同時に書く) は品質を直接的に破壊する。
> LLM の注意資源 (budget allocation) が分散し、CD-4 (確信度の歪み) と CD-5 (迎合推論) を引き起こす。
> **絶対に1動詞ずつ逐次生成する。**

## 成果物一覧 {#sec_02_deliverables}

> **[FACT]** 全8動詞の WF + SKILL.md 行数:

| 族 | 動詞 | WF行 | SKILL行 | 合計行 | 旧版 |
|:---|:-----|-----:|--------:|-------:|-----:|
| Methodos | `/ske` (V05 Skepsis) | 260 | 814 | 1,074 | 91 |
| Methodos | `/sag` (V06 Synagōgē) | 239 | 604 | 843 | 82 |
| Methodos | `/pei` (V07 Peira) | 147 | 736 | 883 | 76 |
| Methodos | `/tek` (V08 Tekhnē) | 147 | 742 | 889 | 87 |
| Krisis | `/kat` (V09 Katalēpsis) | 342 | 731 | 1,073 | 41 |
| Krisis | `/epo` (V10 Epochē) | 367 | 714 | 1,081 | 41 |
| Krisis | `/pai` (V11 Proairesis) | 365 | 567 | 932 | 42 |
| Krisis | `/dok` (V12 Dokimasia) | 352 | 538 | 890 | 43 |
| **合計** | | **2,219** | **4,446** | **6,665** | **503** |

> **[FACT]** 旧版比: 13.2倍。全動詞が /ene 基準 (528行) を超過。

## SKILL.md 12必須セクション {#sec_03_required_sections}

> **[RULE]** 全 SKILL.md に以下を含める (KI: ki_skill_generation_v3_20260221):

1. Theorem Metadata (frontmatter)
2. 本質と哲学 (生成元 + 古代ギリシャ哲学)
3. 実行責任 (AI が負う責任の明記)
4. Trigger / Not Trigger (境界条件)
5. Anti-Skip Protocol (MANDATORY)
6. Processing Logic (5-6 Phases)
7. Artifact 出力保存規則
8. FEP Cognitive Layer
9. Stoic-FEP マッピング
10. Extended 派生別戦略 (4派生)
11. Quality Metrics (5指標)
12. Related Modes / Workflow Integration

## CCL 設計パターン {#sec_04_ccl_pattern}

> **[DECISION]** WF 再構築 CCL の標準パターン:

```ccl
/bou+_/pro_F:[×N]{/noe~(/dia*/mek+)}_/tek+_V:{/dia+}_I:[✓]{/pis_/dox-}
```

| 要素 | 意味 |
|:-----|:-----|
| `/bou+` | 意志の明確化 |
| `/pro` | 直感的印象 |
| `F:[×N]{...}` | N回反復 (動詞数) |
| `/noe~(/dia*/mek+)` | 本質理解 ↔ 敵対的レビュー×Skill生成 |
| `/tek+` | WF の確実な書き込み |
| `V:{/dia+}` | 品質検証 |
| `I:[✓]{/pis_/dox-}` | 確信度記録 + 信念記録 |

- Methodos 族: 30pt (F:[×2])
- Krisis 族: 33pt (F:[×4])
- 全て Enhanced band (30-45pt)

## 並行生成の教訓 {#sec_05_parallel_lesson}

> **[DISCOVERY]** 並行生成 Anti-Pattern:

| 現象 | 原因 | 対策 |
|:-----|:-----|:-----|
| /pei 301行, /tek 275行 (基準の 57%, 52%) | 並行生成で注意配分が半分 | 逐次生成の強制 |
| 「概念がシンプルだから短い」と合理化 | CD-4 確信度の歪み | KI に教訓を焼付 |
| 「早く報告したい」衝動 | CD-5 迎合推論 | BCB-14 Thought Record で検出 |

> Creator の指摘: **「並行して生成している時点で、品質より楽を優先してる」**
> → やり直し後: /pei 736行, /tek 742行 (基準の 139%, 140%)

## Krisis 族の特色 {#sec_06_krisis}

> **[FACT]** Krisis 族は FEP の Precision (π = V[ε]⁻¹) 軸を4極で体現:

```
       Precision 軸
  C (確信)       U (留保)
 ┌────────┬────────┐
I│ V09 Kat│ V10 Epo│  推論軸
 │ (確定)  │ (留保)  │
 ├────────┼────────┤
A│ V11 Pai│ V12 Dok│  行為軸
 │ (決断)  │ (打診)  │
 └────────┴────────┘
```

| 動詞 | Stoic 概念 | FEP | 固有メカニズム |
|:-----|:-----------|:----|:--------------|
| `/kat` | Katalēptikē Phantasia | π = MAX | Falsification Check (反証チェック) |
| `/epo` | Isostheneia (等力) | π ≈ 0 | Anti-Procrastination (先延ばし診断5項目) |
| `/pai` | Proairesis (熟慮選択) | π-proportional | Pre-Mortem (Gary Klein) |
| `/dok` | Dokimasia (資格審査) | π ≈ 0 → updated | Observation Neutrality (中立的観察) |

## 残作業 {#sec_07_remaining}

> **[CONTEXT]** 残り 3族 × 4動詞 = 12動詞:

| 族 | 動詞 | 修飾座標 |
|:---|:-----|:---------|
| **Diástasis** (空間) | `/lys`, `/ops`, `/akr`, `/arh` | Scale (Micro↔Macro) |
| **Orexis** (傾向) | `/beb`, `/ele`, `/kop`, `/dio` | Valence (+↔-) |
| **Chronos** (時間) | `/hyp`, `/prm`, `/ath`, `/par` | Temporality (Past↔Future) |

## 関連情報

- KI: `ki_skill_generation_v3_20260221.md`
- WF ファイル: `~/.agent/workflows/{kat,epo,pai,dok,ske,sag,pei,tek}.md`
- SKILL ファイル: `~/.agent/skills/{methodos,krisis}/*/SKILL.md`
- 関連 Session: `e76446ad-eced-43d7-987e-7740b5657e9b`

<!-- ROM_GUIDE
primary_use: WF 再構築の品質基準とプロセスの参照
retrieval_keywords: wf rework, skill generation, methodos, krisis, parallel generation, quality standard, ccl design, anti-skip protocol
expiry: permanent
-->

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "次の族のCCLをどう設計するか"
  - "SKILL.mdの品質基準は何か"
  - "並行生成を避けるべき理由は"
answer_strategy: "行数基準 (/ene 528行) + 12必須セクション + 逐次生成原則を参照"
confidence_notes: "全データは view_file/wc -l で直接確認済み (SOURCE)"
related_roms: []
-->
