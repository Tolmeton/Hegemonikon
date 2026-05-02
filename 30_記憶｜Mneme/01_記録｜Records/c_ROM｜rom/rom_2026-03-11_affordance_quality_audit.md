---
rom_id: rom_2026-03-11_affordance_quality_audit
session_id: 93755eae-bc09-4e8f-980e-f1cd2718e3d9
created_at: 2026-03-11 21:20
rom_type: distilled
reliability: High
topics: [affordance, intent, skill, telos, quality_audit, handoff, source_taint]
exec_summary: |
  Telos族 (V02/V03/V04) の affordance `<:intent:>` ブロック品質監査。
  5欠陥 (typo 3件 + TAINT 実績 + 実績不足) を検出し全修正完了。
  Handoff 8件精読で15件の SOURCE ベース実績に置換。
---

# Affordance 品質監査 — Telos 族 {#sec_01_overview}

> **[DECISION]** V02/V03/V04 の実績セクションは全て TAINT だった → Handoff 精読で SOURCE に置換

## セッション概要 {#sec_02_session}

> **[FACT]** Affordance Description Format v1.2 を Telos 族 (V01-V04) + V05 に適用するセッション。
> V01 は先行実装で高品質。V02-V04 は「一気に仕上げ」で品質低下が発生。
> Creator の「質は下がってない？」という指摘で品質監査を開始。

## 検出欠陥 (D1-D5) {#sec_03_defects}

> **[FACT]** 5欠陥全て修正済み

| ID | 重度 | 対象 | 内容 | 修正 |
|:---|:-----|:-----|:-----|:-----|
| D1 | LOW | V04 | 「慣重」→「慎重」 | ✅ |
| D2 | MED | V04 | 「誰差検知」→「偏差検知」(意味変更) | ✅ |
| D3 | MED | V03 | 「問いのきそのぶかさ」→「問いの浅さ」 | ✅ |
| D4 | HIGH | V02-V04 | 実績が全9件 TAINT (記憶ベース捏造) | ✅ |
| D5 | MED | V02-V04 | 実績3件 < V01の5件 | ✅ → 各5件 |

## Handoff SOURCE 検証結果 {#sec_04_source}

> **[DISCOVERY]** 旧実績9件中、Handoff と内容が一致したものは **0件**。全て記憶から捏造。

### 精読した Handoff (8件)

| Handoff | 確認対象 |
|:--------|:---------|
| `handoff_2026-02-08_1856.md` | V02: /bou 5タスク完遂 |
| `handoff_2026-02-08_2145.md` | V03: /zet+ 5層18問→8問解決 |
| `handoff_2026-02-10_1330.md` | V04: /ene 実装3件 |
| `handoff_2026-02-10_2210.md` | V04: /bou→/ene+ 3タスク |
| `handoff_2026-02-11_2052.md` | V02: /bou.x, V03: oscillation, V04: topics.yaml |
| `handoff_2026-02-11_2153.md` | V02: /bou~^/zet, V04: PURPOSE 582件 |
| `handoff_2026-02-13_1135.md` | V02: /bou+*^/zet, V03: VSearch Phase 2 |
| `handoff_2026-03-03_0700.md` | V03: 二重欠損, V04: Compile-Only フック |

### 確定 SOURCE 実績 (15件)

> **[RULE]** 全実績に `[SOURCE: handoff_YYYY-MM-DD_HHMM.md Lxx]` ラベル必須

**V02 /bou**: 02-08 5タスク + 02-11 /bou.x 方向転換 + 02-11 /bou~^/zet 5タスク駆動 + 02-13 BC-10自己適用 + 02-13 @plan 4セッション計画

**V03 /zet**: 02-08 5層18問→8問解決 + 02-11 oscillation 方向転換 + 02-13 VSearch Phase 2 + 02-18 4層20項目盲点 + 03-03 二重欠損→環境強制

**V04 /ene**: 02-11 PURPOSE 582件→100% + 02-11 WEAK 218件→0件 + 02-11 topics.yaml 拡張 + 02-10 演算子実装 + 03-03 Compile-Only フック

## Affordance Description Format v1.2 {#sec_05_format}

> **[RULE]** frontmatter `description` に Epistemic/Pragmatic 2行 + `<:intent:>` に5セクション

```
description: |
  {skill_name} — {WF名} — {1行要約}
  Epistemic: {認識的獲得}
  Pragmatic: {行為的獲得}

<:intent:>
  /xxx が無い世界: {counterfactual}
  獲得: {epistemic + pragmatic}
  喪失: {specific failure cases}
  実績: {5件, SOURCE Handoff 行番号付き}
  原則: {FEP根拠 + 行動原則}
/intent:>
```

## 教訓 (法則化) {#sec_06_lessons}

> **[RULE]** L1: 「一気に仕上げ」は品質低下の直接原因。基盤文書は1件ずつ本気でやれ
> **[RULE]** L2: Handoff 検索の初回結果が少ない=実績がない、ではない。検索クエリを工夫し複数回検索せよ
> **[RULE]** L3: 実績の SOURCE 検証は省略不可。TAINT 実績は捏造と区別できない
> **[RULE]** L4: V01 が高品質→V02-V04 もアンカリングで「同じ品質のはず」は偽。各件独立検証

## 残作業 {#sec_07_remaining}

> **[CONTEXT]** Methodos 族 (V06-V08) 以降の affordance 適用は未着手。V05 /ske は適用済み。

| 族 | Skills | 状態 |
|:---|:-------|:-----|
| Telos | V01-V04 | ✅ 完了 (品質監査済み) |
| Methodos | V05 | ✅ 完了 |
| Methodos | V06 Synagōgē, V07 Peira, V08 Tekhnē | ❌ 未着手 |
| Krisis | V09-V12 | ❌ 未着手 |
| Diástasis | V13-V16 | ❌ 未着手 |
| Orexis | V17-V20 | ❌ 未着手 |
| Chronos | V21-V24 | ❌ 未着手 |

<!-- ROM_GUIDE
primary_use: affordance format 適用時の品質基準と SOURCE 検証手順の参照
retrieval_keywords: affordance, intent, skill, quality, audit, handoff, source, taint, telos, V02, V03, V04
expiry: permanent
-->
