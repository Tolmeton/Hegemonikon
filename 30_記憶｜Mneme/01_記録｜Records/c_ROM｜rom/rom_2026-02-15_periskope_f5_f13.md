---
rom_id: rom_2026-02-15_periskope_f5_f13
session_id: 5b89bc53-129f-4d30-b73e-3a18e422c985
created_at: "2026-02-15 17:03"
rom_type: rag_optimized
reliability: High
topics: [periskope, citation, deduplication, search, api, desktop, cache, chain-verification]
exec_summary: |
  Periskopē 研究エンジンの品質・機能・統合を9タスク (F5-F13) で強化。
  全4 Sprint 完了、32/32テスト通過。
  閾値調整、URL dedup、query分類、2-hop citation chain が主要な成果。
---

# Periskopē F5-F13: 全Sprint完了 {#sec_01_overview .periskope .followup}

> **[FACT]** 全9タスク (F5-F13) を4つのSprintで実装完了。テスト 32/32 通過。

---

## Sprint 1: 品質強化 {#sec_02_sprint1 .quality}

### F5: Citation 閾値チューニング {#sec_03_f5 .citation .threshold}

> **[DECISION]** SOURCE 閾値を 0.6→0.65、TAINT 閾値を 0.3→0.40 に調整。
> コンストラクタパラメータで設定可能にした。

**変更ファイル**: `mekhane/periskope/citation_agent.py`
**理由**: FABRICATED 57%→0% 達成後の精度微調整。偽陽性（低品質 SOURCE）の排除。

### F6: 検索クエリ最適化 {#sec_04_f6 .search .query}

> **[DECISION]** `_preprocess_query` + `DOMAIN_BLACKLIST` + `min_score` フィルタを追加。

**変更ファイル**: `mekhane/periskope/searchers/searxng.py`
**DOMAIN_BLACKLIST**: pinterest.com, quora.com, reddit.com (低品質コンテンツの排除)

---

## Sprint 2: 並列合成 + キャッシュ {#sec_05_sprint2 .synthesis .cache}

### F7: Claude LS 並列合成 {#sec_06_f7 .claude .ls .parallel}

> **[DISCOVERY]** Claude LS 並列合成の E2E テスト成功。Gemini 95% / Claude LS 50%。
> `_synth_claude_ls` は `AntigravityClient` 経由で LS に接続。

**変更ファイル**: `mekhane/periskope/synthesizer.py` (既存実装の確認のみ)

### F8: Embedder キャッシュ {#sec_07_f8 .cache .embedding}

> **[DECISION]** SHA256[:16] → vector のハッシュベースキャッシュを `CitationAgent` に追加。
> 同一テキストの再埋め込みを回避。

**変更ファイル**: `mekhane/periskope/citation_agent.py`
**実装**: `_embed_cache: dict[str, list[float]]` + `_cached_embed()` ヘルパー

---

## Sprint 3: CLI拡張 + Desktop UI {#sec_08_sprint3 .cli .desktop}

### F9: Digest 深度制御 {#sec_09_f9 .digest .depth}

> **[DECISION]** `digest_depth` パラメータ (quick/standard/deep) を `research()` と CLI に追加。
> 3テンプレート: `_quick_template` (Phase 0のみ), `_standard_template` (+/fit), `_deep_template` (全7フェーズ)

**変更ファイル**: `mekhane/periskope/engine.py`, `mekhane/periskope/cli.py`
**CLI**: `--digest-depth {quick|standard|deep}`

### F10: Desktop API {#sec_10_f10 .api .desktop}

> **[DECISION]** FastAPI 4エンドポイント: `/periskope/status`, `history`, `report/{filename}`, `research` (POST, 非同期)

**新規ファイル**: `mekhane/api/routes/periskope.py`
**変更ファイル**: `mekhane/api/server.py` (ルーター登録)

---

## Sprint 4: 高度品質 {#sec_11_sprint4 .advanced .quality}

### F11: Cross-source 重複排除 {#sec_12_f11 .dedup}

> **[DECISION]** URL 正規化 (lowercase + trailing slash除去 + query param除去) でソース間重複を排除。
> URL なしの場合は `title:` プレフィックスでタイトルベース重複検知。

**変更ファイル**: `mekhane/periskope/engine.py`
**メソッド**: `_normalize_url()`, `_deduplicate_results()`

### F12: Adaptive Source Selection {#sec_13_f12 .source .selection}

> **[DECISION]** `_classify_query()` で academic/implementation/concept に3分類。
> 分類に応じて最適なソースサブセットを `select_sources()` で返す。

| 分類 | キーワード例 | 選択ソース |
|:-----|:-----------|:----------|
| academic | paper, arxiv, 論文 | gnosis, exa, searxng |
| implementation | 実装, code, tutorial | searxng, exa, sophia |
| concept | (デフォルト) | 全5ソース |

**変更ファイル**: `mekhane/periskope/engine.py`

### F13: Citation Chain (2-hop) {#sec_14_f13 .citation .chain}

> **[DECISION]** `verify_depth=2` で TAINT citation のソースコンテンツ内 URL を正規表現で抽出。
> 2次ソースで claim を再検証し、`THRESHOLD_SOURCE` 以上なら SOURCE に昇格。

**変更ファイル**: `mekhane/periskope/citation_agent.py`
**メソッド**: `_verify_chain()` — 最大3 URL/citation を試行

---

## Periskopē アーキテクチャ全体像 {#sec_15_architecture .architecture}

> **[FACT]** 現在の Periskopē パイプライン:

```
Query → [Phase 0: Auto source selection (F12)]
      → Phase 1: 5ソース並列検索 (SearXNG, Exa, Gnōsis, Sophia, Kairos)
      → Phase 1.5: Cross-source dedup (F11)
      → Phase 2: マルチモデル合成 (Gemini + Claude LS)
      → Phase 3: Citation 検証 (BGE-M3 + 2-hop chain)
      → Phase 4: Auto-digest (quick/standard/deep)
      → Report
```

**ソースファイル構成**:

| ファイル | 役割 |
|:---------|:-----|
| `engine.py` | パイプラインオーケストレーター |
| `synthesizer.py` | マルチモデル合成 |
| `citation_agent.py` | 引用検証 + 2-hop |
| `searchers/searxng.py` | SearXNG 検索 |
| `searchers/exa_searcher.py` | Exa 検索 |
| `searchers/internal_searcher.py` | Gnōsis/Sophia/Kairos |
| `models.py` | Pydantic データモデル |
| `cli.py` | CLI エントリポイント |

---

## 関連情報 {#sec_16_related}

- 関連 WF: `/sop` (Periskopē 起動元)
- 関連 KI: Periskopē アーキテクチャ
- 関連 Session: 5b89bc53 (本セッション)

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "Periskopē の現在の機能は何か"
  - "Citation 検証の仕組みは"
  - "検索ソースの選び方は"
  - "dedup はどう動くか"
  - "API のエンドポイントは"
answer_strategy: "Sprint 番号 → タスク番号 (F5-F13) → 変更ファイルの順で辿る"
confidence_notes: "32/32 テスト通過。実運用テスト (live query) は未実施"
related_roms: []
-->
