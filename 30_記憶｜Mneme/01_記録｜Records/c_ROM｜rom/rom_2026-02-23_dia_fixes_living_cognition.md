---
rom_id: rom_2026-02-23_dia_fixes_living_cognition
session_id: aea876b5-8025-41d6-b534-8e174d53ef60
created_at: 2026-02-23 22:39
rom_type: rag_optimized
reliability: High
topics: [MacroExecutor, 差分実行, コードブロック除外, E2E, レート制限, 収束ループ, pacing, estimate_convergence]
exec_summary: |
  /dia+ で検出した3つの残存リスクを全て対処し、use_llm=true の E2E テストに成功。
  差分実行 + pacing_sleep が API レート制限問題を実用的に解決した。
search_extensions:
  synonyms: [delta execution, 差分実行, コードブロック, fenced code, rate limit, 429, pacing]
  related_concepts: [n-gram Jaccard, 構造類似度, active_indices, convergence_threshold]
---

# /dia+ 指摘対処 — 生きた認知の実用化 {#sec_01_overview}

> **[DECISION]** /dia+ で検出した3点を全て対処し、E2E テスト (use_llm=true) に成功。

---

## 9a. コードブロック除外 {#sec_02_codeblock}

> **[FACT]** `_split_structured` の見出し/番号/箇条書き戦略がコードブロック内の `#` や `-` を誤認していた。

> **[DECISION]** ` ``` ` で囲まれた行を `in_code_block` フラグでマスクし、`active_indices` セットでフィルタ。3つの分割戦略全てに適用。

---

## 9b. C:{} 差分実行 (Delta Execution) {#sec_03_delta}

> **[DISCOVERY]** C:{} の収束ループで全ノードを毎回 LLM で実行すると、40+ API 呼び出しが数十秒に集中し、429 Too Many Requests に衝突する。

> **[DECISION]** 2つの対策を `_walk_convergence_loop` に実装:
>
> 1. **差分実行**: 入力コンテキストの similarity >= 0.95 なら前回結果を再利用 → LLM 呼び出しスキップ
> 2. **pacing_sleep**: 反復間に 1秒の sleep → API の「息継ぎ」

> **[RULE]** `$delta_skip = True` が ctx.variables に記録され、何回スキップされたかを事後分析可能。

---

## 9c. E2E テスト結果 {#sec_04_e2e}

> **[FACT]** `use_llm=true` で v5.0 CCL 式 `C:{/bou+~(/prm*/tek)_V:{/dia}}_/pis_/dox-` が完走。

| 指標 | 値 |
|:-----|:---|
| 所要時間 | 112.2秒 |
| 最終確信度 | 0.56 |
| エントロピー削減 | 0.061 |
| 終了コード | 0 (成功) |
| モデル | gemini-2.0-flash |

> **[DISCOVERY]** 429 エラーが発生しても CortexClient のリトライ機構が自動回復し、最終的に完走した。IDE と API クォータを共有しているため、IDE を同時利用中は遅延が増大する。

---

## 関連ファイル {#sec_05_files}

| ファイル | 変更内容 |
|:---------|:---------|
| `hermeneus/src/macro_executor.py` | コードブロック除外, 差分実行, pacing_sleep |
| `test_e2e_ccl.py` | E2E テストスクリプト |

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "C:{} がレート制限で動かない"
  - "差分実行とは何か"
  - "_split_structured がコードブロック内を誤認する"
  - "E2E テストの結果はどうだったか"
answer_strategy: "§3 の差分実行が核心。429 対策は pacing_sleep + CortexClient リトライの二重防御。"
confidence_notes: "E2E 実行は1回成功。統計的有意性は未確認だが動作証明としては十分。"
related_roms: ["rom_2026-02-23_plan_living_cognition"]
-->
