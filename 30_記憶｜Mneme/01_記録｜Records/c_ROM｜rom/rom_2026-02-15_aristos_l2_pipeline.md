---
rom_id: rom_2026-02-15_aristos_l2_pipeline
session_id: a44c119a-3b6d-4b34-a478-4299cd53991f
created_at: 2026-02-15 08:55
rom_type: distilled
reliability: High
topics: [aristos, l2, evolution-engine, derivative-selector, feedback-pipeline, ga]
exec_summary: |
  Aristos L2 Evolution Engine のフィードバックパイプラインを完成。
  GA 進化済み重みを select_derivative() に閉ループ接続し、
  CLI (evolve_cli.py) で全パイプラインを実行可能にした。228/228 テスト合格。
---

# Aristos L2 フィードバックパイプライン完了 {#sec_01_overview}

> **[DECISION]** GA evolved weights を `select_derivative()` 内で centrally apply する設計を採用

## 実装アーキテクチャ {#sec_02_architecture}

> **[FACT]** 閉ループ: WF実行 → select_derivative →_log_selection → evolve_cli → evolved_weights.json →_apply_evolved_boost → select_derivative

### Phase 1: 逆接続 (selector → GA)

[derivative_selector.py](file:///home/makaron8426/Sync/oikos/hegemonikon/mekhane/fep/derivative_selector.py) に追加:

| 関数 | 役割 |
|:-----|:-----|
| `_load_evolved_weights()` | Lazy ローダー (1回だけ読込キャッシュ) |
| `_apply_evolved_boost()` | confidence にブースト係数を乗算 |
| `reload_evolved_weights()` | キャッシュ強制リロード API |
| `correct_selection()` | 明示的フィードバック (corrected_to) |

> **[DECISION]** 最小侵襲: config 2変数 + 共通関数1つ + select_derivative()内1行追加

### Phase 2: CLI オーケストレーター

[evolve_cli.py](file:///home/makaron8426/Sync/oikos/hegemonikon/.agent/projects/aristos/evolve_cli.py):
`--status`, `--theorem`, `--all`, `--gen`, `--pop`, `--dry-run`, `--convert-feedback`

> **[DISCOVERY]** YAML ログに null バイト混入の可能性あり → 除去処理を実装済み

## 設計判断の記録 {#sec_03_decisions}

> **[DECISION]** /dia+ レビューの4指摘は全て許容レベルと判断:

| 指摘 | 判断理由 |
|:-----|:---------|
| in-place 修正 | 変換のみで副作用軽微 |
| ログ先行の書込順序 | 冪等ログによりデータ損失なし |
| グローバルキャッシュ | 単一プロセス想定で十分 |
| ハードコードパス | 環境変数 `EVOLVED_WEIGHTS_PATH` で上書き可能 |

## Dendron 教訓 {#sec_04_dendron}

> **[DISCOVERY]** Dendron Guard は `# PROOF: [Level] <- parent` のv2フォーマットを要求。
> `# PROOF: テキスト` 形式ではパターン `PROOF_PATTERN_V2` にマッチしない。

## ファイルパス {#sec_05_paths}

| ファイル | パス |
|:---------|:-----|
| 選択ログ | `~/oikos/mneme/.hegemonikon/derivative_selections.yaml` |
| フィードバック | `~/oikos/mneme/.hegemonikon/feedback.json` |
| 進化済み重み | `~/oikos/mneme/.hegemonikon/evolved_weights.json` |

## テスト結果 {#sec_06_tests}

全 228/228 合格 (derivative_selector 143 + evolve 35 + router 50)

## 残タスク {#sec_07_remaining}

- [ ] Phase 3: Desktop Evolution Dashboard + API `/api/aristos/evolve`
- [ ] Phase 4: `Chromosome[MacroConfig]` 設計 + CostVector↔FitnessVector 双対
- [ ] Pyre2 lint (search root 未登録 — 実行には無影響)

<!-- ROM_GUIDE
primary_use: L2 Evolution Engine の設計判断と実装詳細の参照
retrieval_keywords: aristos, l2, evolution, ga, derivative, selector, feedback, pipeline, boost, weights
expiry: permanent
-->
