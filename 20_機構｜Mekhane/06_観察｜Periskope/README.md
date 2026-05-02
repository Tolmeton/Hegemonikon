# 06_観察｜Periskope

> **PURPOSE**: Deep Research エンジン。多ソース並列検索 + 多モデル合成 + 引用検証。

## `_src/` 対応コード
- [`mekhane/periskope/`](../../_src｜ソースコード/mekhane/periskope/) — Periskope MCP サーバー

## 機能
- `periskope_search` — 軽量マルチソース検索 (10-15秒)
- `periskope_research` — フル Deep Research (2-4分)
- `periskope_benchmark` — 品質ベンチマーク (NDCG, Entropy, Coverage)
- `periskope_metrics` — メトリクス照会
- `periskope_sources` — クエリ分類 + ソース推薦
- `periskope_track` — 調査テーマ進捗管理

## ソース (14)
searxng, brave, tavily, semantic_scholar, gnosis, sophia, kairos, github, gemini_search, vertex_search, vector_search_ann, stackoverflow, reddit, hackernews

---
*Created: 2026-03-13*
