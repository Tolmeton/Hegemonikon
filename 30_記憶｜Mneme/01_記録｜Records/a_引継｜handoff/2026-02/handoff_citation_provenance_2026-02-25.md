# Handoff: Citation Provenance System

## セッション概要

- **日時**: 2026-02-25 16:38 - 20:17
- **目的**: Periskopē の Citation TAINT 問題を 4 層防御で解決 + NL API benchmark
- **結果**: 4 層全実装、テスト 9/9 通過、/fit 🟢 Naturalized

## 成果物

| ファイル | 状態 | 内容 |
|:--------|:-----|:-----|
| `mekhane/periskope/models.py` | ✅ 修正 | Layer E: `SearchResult.source_urls` 追加 |
| `mekhane/periskope/searchers/tavily_searcher.py` | ✅ 修正 | Layer B: answer → results[] URL 逆マッピング |
| `mekhane/periskope/citation_agent.py` | ✅ 修正 | Layer C: `_reverse_lookup_url` + pool保存 |
| `mekhane/periskope/url_auditor.py` | ✅ 新規 | Layer D: Gemini 3 Flash URL 妥当性精査 |
| `mekhane/periskope/engine.py` | ✅ 修正 | Layer D 統合 + source_urls indexing |

## アーキテクチャ

```
Layer E: SearchResult.source_urls — 構造的出所追跡 (models.py)
Layer B: Tavily answer → results[] URL (SequenceMatcher, sim≥0.15)
Layer C: CitationAgent 逆引き (keyword overlap≥0.4) 
Layer D: URLAuditor (Gemini 3 Flash) — TAINT のみ精査
```

## 前セッションからの継続

NL API 統合 (P1-P5) は前セッションで完了済み。本セッションでは:

1. L3 benchmark 実行 (Bach vs Friston): NDCG=0.89, Score=0.92, TAINT 7/13
2. TAINT 問題の構造分析 → 4 層防御の設計・実装
3. /fit 🟢 判定

## 未完了

| タスク | 優先度 | 備考 |
|:------|:------|:-----|
| E2E TAINT 率改善検証 | 高 | 同じ Bach vs Friston クエリで再測定 |
| NL API on/off benchmark (L2+) | 中 | NL API の品質差を定量化 |
| url_auditor テスト作成 | 中 | test_url_auditor.py 未作成 |
| `reasoning_trace` バグ | 低 | DialecticReport に属性なし (dialectic=true 時) |

## 設計判断

1. **Layer B 閾値 0.15**: Tavily answer は複数結果の合成なので低閾値で広く拾う
2. **Layer C 閾値 0.4**: 逆引きは誤マッチ防止のため高め
3. **Layer D は TAINT のみ**: コスト制御。SOURCE/FABRICATED は再判定不要
4. **CortexClient.generate()**: `url_auditor.py` L168-173 — `asyncio.to_thread` で同期 API をラップ

## Pyre Lint

既存の Pyre lint エラー (`+=` not supported, `Cannot index into str`) は Pyre2 の型推論限界。実行時問題なし。

## Git 状態

266 files changed (未コミット)。periskope/ 関連の変更を `git add mekhane/periskope/` でステージング推奨。
