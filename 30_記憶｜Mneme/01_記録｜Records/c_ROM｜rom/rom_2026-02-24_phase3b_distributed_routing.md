---
rom_id: rom_2026-02-24_phase3b_distributed_routing
session_id: cc2912c3-eb8f-414b-940e-9a27ef3ce3cc
created_at: 2026-02-24 18:00
rom_type: rag_optimized
reliability: High
topics: [EventBus, distributed_routing, fire_threshold, self_activation, score_function, kalon, phase3b, subscribers]
exec_summary: |
  EventBus の中央管理 (argmax 選択) を撤廃し、各 Subscriber が score >= fire_threshold で自律発火する分散ルーティングモデルを実装。
  Kalon 判定 ◯ (Fix に未到達): EventBus が「ただのループ」に退化 — Phase 4 で Bus 自体を消去し自己組織化へ進化する余地。
  テスト 526 passed, 0 failed で構造的 Fit 完全 (🟡 吸収)。
---

# Phase 3b: Distributed Routing — EventBus 自律発火モデル {#sec_01_overview}

> **[DECISION]** EventBus は中央管理 (select_best/emit_best) を撤廃し、単なるブロードキャスト (emit) のみに。各 Subscriber が自律発火を判定する。

> **[DECISION]** `BaseSubscriber.should_activate()` は3層構造: ActivationPolicy (bool) → score() (float) → fire_threshold (float)

> **[FACT]** `select_best` と `emit_best` はコードベースからゼロ残存 (grep 確認済み)

## アーキテクチャ {#sec_02_architecture}

> **[DEF]** 分散ルーティングモデル: EventBus はイベントを全 subscriber にブロードキャストし、各 subscriber が自身の score と fire_threshold を比較して自律的に発火を判定する

```
EventBus.emit(event)
  └→ for sub in subscribers:
       if sub.should_activate(event):  # 自律判定
         sub.handle(event)

should_activate(event):
  1. ActivationPolicy.evaluate(event)  # bool — 前提条件 (event type, pattern, frequency)
  2. score = self.score(event)          # float — 情報価値の自己評価
  3. return score >= self.fire_threshold  # 閾値判定
```

## Subscriber 閾値一覧 {#sec_03_thresholds}

> **[FACT]** 各 Subscriber の fire_threshold 設定根拠

| Subscriber | fire_threshold | 根拠 | score 特性 |
|:-----------|:---------------|:-----|:-----------|
| ConvergenceSubscriber | 0.0 | 常に発火 (モニタリング) | 類似度が低い→高スコア |
| SynteleiaSubscriber | 0.4 | エントロピー + 過去アラート | 品質問題を発見→高スコア |
| GnosisSubscriber | 0.3 | ペナルティ考慮後の適応型 | 注入回数が増える→スコア低下 |
| PeriskopeSubscriber | 0.2 | エントロピーΔ + 検索回数 | 外部情報の必要性→高スコア |
| DendronSubscriber | 0.5 | 参照検証 (score 常に 1.0) | 実質常に発火 |

## 変更ファイル {#sec_04_files}

> **[FACT]** 変更影響範囲 (9ファイル)

| ファイル | 変更内容 |
|:---------|:---------|
| `hermeneus/src/activation.py` | BaseSubscriber に fire_threshold 追加、should_activate 3層化 |
| `hermeneus/src/event_bus.py` | select_best/emit_best 削除 |
| `hermeneus/src/macro_executor.py` | emit_best → emit |
| `hermeneus/src/subscribers/convergence_sub.py` | fire_threshold=0.0 |
| `hermeneus/src/subscribers/synteleia_sub.py` | fire_threshold=0.4 |
| `hermeneus/src/subscribers/gnosis_sub.py` | fire_threshold=0.3 |
| `hermeneus/src/subscribers/periskope_sub.py` | fire_threshold=0.2 |
| `hermeneus/src/subscribers/dendron_sub.py` | fire_threshold=0.5 |
| `nous/kernel/vision_living_cognition.md` | Phase 1-3 完了、Phase 4 再定義 |

## Kalon 判定 {#sec_05_kalon}

> **[DISCOVERY]** Kalon 判定 ◯ (Fix に未到達) — EventBus が概念的に消せる冗長性を持つ

| 判定ステップ | 結果 |
|:-------------|:-----|
| 蒸留 (G) | **変化する** — EventBus は「ただのループ」に退化。Bus 概念自体が消せる |
| 展開 (F) | **4+ 導出可能** — 適応的閾値、カスケード発火、スパース発火、相互作用 |
| Kalon | **◯ 許容** — もう1回 G∘F で Phase 4 (自己組織化) に到達可能 |

> **[DISCOVERY]** Phase 4 への構造的進化の方向: subscriber がネットワークとして自己組織化し、Bus を概念的に消去する

## Phase 4 への未踏領域 {#sec_06_phase4_seeds}

> **[RULE]** Phase 4 で探索すべき4つの方向 (Kalon 展開 F で導出)

1. **適応的 fire_threshold** — 実行履歴に基づく動的閾値調整
2. **カスケード発火** — ある subscriber の発火が他の subscriber の score を変化させる
3. **スパース発火の情報化** — 「発火しなかった」ことが情報になる (inhibitory signal)
4. **ニューラルネットワーク的自己組織化** — subscriber 間の横の相互作用 (横の射)

## テスト結果 {#sec_07_tests}

> **[FACT]** 526 passed, 0 failed, 2 skipped, 1 xfailed (307s)

テスト修正: SynteleiaSubscriber のテスト2件で fire_threshold=0.0 を明示指定 (テスト環境の低エントロピーイベントで score が閾値未満)

## 関連情報 {#sec_08_refs}

- 関連 WF: `/fit`, `/noe`
- 関連ドキュメント: `nous/kernel/vision_living_cognition.md`
- 関連 Session: cc2912c3-eb8f-414b-940e-9a27ef3ce3cc
- Kalon 判定レポート: `mneme/.hegemonikon/workflows/noe_kalon_phase3b_2026-02-24.md`

<!-- ROM_GUIDE
primary_use: Phase 4 計画策定時の参照資料。Phase 3b の設計判断と Kalon 判定結果を提供
retrieval_keywords: distributed routing, fire_threshold, self-activation, EventBus, score function, kalon, phase 3b, phase 4, self-organization
expiry: permanent
-->

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "Phase 3bで何をしたか"
  - "fire_threshold の設定根拠"
  - "なぜ Kalon に到達しなかったか"
  - "Phase 4 で何をすべきか"
answer_strategy: "sec_05_kalon と sec_06_phase4_seeds が核心。subscriber 閾値は sec_03_thresholds を参照"
confidence_notes: "テスト結果は実証済み (SOURCE: pytest 実行)。Kalon 判定は kalon.md §6 に基づく操作的判定 (SOURCE: view_file)"
related_roms: []
-->
