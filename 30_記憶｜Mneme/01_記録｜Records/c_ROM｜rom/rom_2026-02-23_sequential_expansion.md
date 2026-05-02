---
rom_id: rom_2026-02-23_sequential_expansion
session_id: 1291fb63-4c0b-4b22-8d9f-420df1d3368d
created_at: 2026-02-23 12:09
rom_type: distilled
reliability: High
topics: [peras_pipeline, sequential_llm, phase_expansion, ax_pipeline, verb_dialogue]
exec_summary: |
  Phase 2 逐次化 (C0→C3 の4回逐次 LLM 呼び出し) の成功を受け、
  他フェーズへの逐次化拡張を要件定義する。2つの拡張候補を詳述。
---

# 逐次化フェーズ拡張 — 要件定義 {#sec_01_overview}

> **[DECISION]** Phase 2 逐次化は /fit で 🟡→🟢 に馴化済み (23テスト全パス)。
> この成功パターンを他フェーズに適用する。

## 背景: なぜ逐次化が有効か {#sec_02_why}

> **[FACT]** 単一の巨大プロンプトでは、LLM が出力フォーマットを揺らしパーサーが失敗する。
> 逐次呼び出しにより: (1) 各ステップの出力を制御可能、(2) 前ステップの結果を次に渡せる、(3) フォーマット揺れが局所化される。

> **[FACT]** Phase 2 逐次化の実績: C1-C3 空問題を根絶。LLM 呼び出し回数 1→4 (トレードオフ: +30秒, +3 API 呼び出し)

---

## 拡張候補 1: 定理間対話 (Phase 1 強化) {#sec_03_verb_dialogue}

### 現状

```
Phase 1: V01, V02, V03, V04 を並列実行 (各定理が独立に分析)
  → 4定理は互いの出力を知らない
```

### 改善案

```
Phase 1 逐次化:
  V01 → 出力を V02 に渡す → V02 は V01 の視点を踏まえて分析
  → V03 は V01+V02 の結果を知った上で問いを立てる
  → V04 は V01-V03 の全結果を踏まえて行為を提案
```

### 要件

| 項目 | 仕様 |
|:-----|:-----|
| 実装場所 | `PerasPipeline._phase1_verbs()` |
| 変更規模 | `asyncio.gather()` → 逐次 `await` ループ |
| プロンプト変更 | `_build_verb_prompt()` に `prior_results: List[VerbResult]` 引数を追加 |
| 注入テンプレート | `## 先行定理の分析結果\n{prior_results の要約}` |
| トレードオフ | 実行時間: 並列15秒 → 逐次60秒。品質改善 vs 速度劣化 |
| 深度連動 | `depth='+'` の時のみ逐次化、`depth='-'` は並列維持 |

### 検証方法

- E2E テスト: /t (Telos) で V04 の出力が V01-V03 の結論を参照しているか確認
- 定量比較: 逐次版 vs 並列版の確信度・C2 融合品質

### 優先度・難度

| 影響度 | 難度 | 推奨 |
|:-------|:-----|:-----|
| High (分析品質の大幅向上) | Medium (ループ変更 + プロンプト拡張) | ⭐⭐ 次セッションで着手 |

---

## 拡張候補 2: AxPipeline Phase 2 合成 {#sec_04_ax_synthesis}

### 現状

```
AxPipeline.run():
  Phase 1: 6 × PerasPipeline.run() → 6つの PerasResult
  Phase 2: 6結果の合成 → 未実装 (TODO)
  Phase 3: X-series 15エッジ張力分析 → 部分実装
  Phase 4: 最終レポート → 未実装
```

### 改善案

```
AxPipeline Phase 2 逐次合成:
  Step 1: 6つの Limit 結論を並べ、全体像を把握 (Synopsis)
  Step 2: 対立する結論を特定 (Tension Detection)
  Step 3: 対立を統合し、メタ結論を生成 (Synthesis)
  Step 4: メタ結論の Kalon 検証 (偏り排除)
```

### 要件

| 項目 | 仕様 |
|:-----|:-----|
| 実装場所 | `AxPipeline._phase2_synthesis()` (新規メソッド) |
| 入力 | `List[PerasResult]` (6 Series の結果) |
| 出力 | `AxResult` (メタ結論 + 確信度 + メタ座標判定) |
| LLM 呼び出し | 4回逐次 (PerasPipeline Phase 2 と同じパターン) |
| 依存 | Phase 1 の完了 (6 × PerasPipeline) |

### Step 別プロンプト設計

| Step | プロンプトの核心 | 入力 | 出力 |
|:-----|:----------------|:-----|:-----|
| S1 Synopsis | 「6つの結論を俯瞰し、全体像を1段落で」 | 6×conclusion | 全体像テキスト |
| S2 Tension | 「どの Series 間に矛盾/緊張があるか」 | S1 + 6×conclusion | 対立リスト |
| S3 Synthesis | 「対立を統合し、メタ結論を生成」 | S1 + S2 | メタ結論テキスト |
| S4 Kalon | 「メタ結論の偏り検証 + 最終判定」 | S3 | CONCLUSION, CONFIDENCE |

### 検証方法

- E2E テスト: `/ax` 全体実行 (6 Series + 合成 + X-series)
- 定量比較: 合成前 (6つの個別結論) vs 合成後 (メタ結論)

### 優先度・難度

| 影響度 | 難度 | 推奨 |
|:-------|:-----|:-----|
| Very High (/ax の完全動作に必須) | High (ax_pipeline.py の大幅変更) | ⭐⭐⭐ 最優先だが大規模 |

---

## 拡張しないもの {#sec_05_excluded}

> **[DECISION]** 以下は逐次化の対象外

| フェーズ | 理由 |
|:---------|:-----|
| Phase 3 (出力整形) | LLM 不要。テンプレートのみ |
| X-series 15エッジ分析 | 各エッジは独立。並列が適切 |
| Phase 1 の `depth='-'` | 速度優先時は並列を維持 |

---

## 実装順序の推奨 {#sec_06_order}

```
1. AxPipeline Phase 2 合成 (拡張候補2)
   → /ax の最低限の動作に必須
   → 4回逐次 LLM (Phase 2 逐次化と同じパターンを再利用)

2. 定理間対話 (拡張候補1)
   → depth='+' 限定なので影響範囲が限定的
   → Phase 2 合成が安定してから着手
```

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "逐次化の拡張方針"
  - "AxPipeline Phase 2 の実装方法"
  - "定理間対話の設計"
answer_strategy: "まず拡張候補2 (AxPipeline) の要件を参照し、次に拡張候補1を参照"
confidence_notes: "Phase 2 逐次化は E2E 実証済み。拡張候補は設計段階。"
related_roms: ["rom_2026-02-23_peras_pipeline"]
-->
