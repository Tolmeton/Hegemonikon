---
rom_id: rom_2026-02-19_periskope_deep_evolution
session_id: 1e44fa67-7cb9-4632-9eb5-e125817a4b20
created_at: 2026-02-19 23:05
rom_type: rag_optimized
reliability: High
topics: [periskope, deep_research, crawling, page_fetcher, citation_verification, CCL, cognitive_tool, STORM, DeepResearcher]
exec_summary: |
  Periskopē Deep Research を「検索ツール」から「認知ツール」へ進化させるセッション。
  技術的改善 (35→80件) と哲学的転換 (問いの探索 = 真の Deep) の両方を達成。
  CCL `F:[×N]{/zet~*/sop}` が真の Deep Research の設計式。
---

# Periskopē Deep Research 進化 {#sec_01_overview}

> **[DECISION]** Periskopē は「検索ツール」ではなく「認知ツール」として再定義される。真の Deep = 問いが問いを生む連鎖。

> **[DISCOVERY]** 真の Deep Research の CCL 表現: `F:[×N]{/zet~*/sop}_~(/noe*/dia)` — 問いの探索と検索が収束的に発振し、深い認識と判定で品質評価する。

---

## 技術改善 (Fix 1-6) {#sec_02_technical_fixes}

> **[FACT]** セッション前: 35 件/126s → セッション後: 80 件/110s (同一クエリ L3 Deep)

### 実装した修正

| # | Fix | ファイル | 効果 |
|:--|:----|:---------|:-----|
| 1 | S2 API キーフォールバック | `semantic_scholar_searcher.py` | `S2_API_KEY` \|\| `SEMANTIC_SCHOLAR_API_KEY` |
| 2 | 内部ソース relevance フィルタ | `engine.py` Phase 1.75 | relevance < 0.3 除去 |
| 3 | 引用検証 Source Analysis 除外 | `citation_agent.py` | メタセクションを claim 抽出から除外 |
| 4 | max_results 深度連動 | `engine.py` | L1=10, L2=20, L3=30/ソース |
| 5 | PDF 対応 (オプショナル) | `page_fetcher.py` | pymupdf import で PDF テキスト抽出 |
| 6 | 構造化出力 | `page_fetcher.py` | trafilatura `include_formatting=True` |

### 追加修正

| Fix | ファイル | 効果 |
|:----|:---------|:-----|
| 内部ソース TF 正規化 | `internal_searcher.py` | スコア 0-1 正規化 + < 0.1 カット |
| S2 クエリ短縮 | `engine.py` | コロン前切り出し + 200文字制限 |

> **[FACT]** S2 は依然 0 件 (クエリ短縮後も)。API 接続自体に問題がある可能性。要別途調査。

---

## 哲学的転換 {#sec_03_philosophy}

> **[DISCOVERY]** 現在の Periskopē は `F:[×1]{/sop}` — 1 回検索して返すだけ。Claude.ai が 45 分で 468 件集めるのは反復的問い探索の結果。

### 「Wide」 vs 「Deep」

| | Wide (現在の Periskopē) | Deep (目指すべき姿) |
|:---|:---|:---|
| ループ | 1-2 パス | 10-30 パス |
| 問い | ユーザーの 1 つ | 派生 → さらに派生 |
| 時間 | 1-2 分 | 5-30 分 |
| 主体 | 検索エンジン | **問いを探索する認知エージェント** |
| CCL | `F:[×1]{/sop}` | `F:[×N]{/zet~*/sop}_~(/noe*/dia)` |

> **[RULE]** 真の Deep Research = 予測誤差が新たな探索行動を駆動するループ (FEP)

---

## 競合調査結果 {#sec_04_competitors}

> **[FACT]** 3 本の L3 Deep Research で 25+24+30 = 79 件の競合情報を収集。

### Perplexity Deep Research

- **TTC (Test Time Compute) expansion** — 推論時間拡大で反復分析サイクル模倣
- **多段階ランキング** — 低レイテンシ予算内で段階的精度向上
- 数十回検索 + 数百ソース読込

### Claude.ai Research

- **Multi-Agent Research System** (Anthropic 公式)
- 最大 **45 分** 稼働、数百ソース自律検索
- **Agentic アプローチ** — 複数検索が積み上がり異なる角度から質問を探索
- Web + Google Workspace + サードパーティ連携

### その他

- **Gemini Deep Research**: Web + Gmail + Drive + Chat 統合
- **OpenAI Deep Research**: GPT-5.2 ベース
- **Grok 3 DeepSearch**: X データ含む
- **Alici.AI, Kimi-Researcher**: 二番煎じ OSS

---

## 消化候補論文 {#sec_05_papers}

> **[DECISION]** 以下 3 論文を /eat+ で消化する (incoming/ に投入済み)

| 論文 | 被引用 | 核心 | HGK 接点 |
|:-----|:------:|:-----|:---------|
| **STORM** (Stanford, arXiv:2402.14207) | 120 | 多視点質問生成 | `/zet` の外部実装例 |
| **DeepResearcher** (GAIR-NLP, arXiv:2504.03160) | 152 | RL で Deep Research 学習 | BC-9 メタ認知の自然発生 |
| **SFR-DeepResearch** (Salesforce, arXiv:2509.06283) | 18 | 単一エージェント RL | Periskopē の設計指針 |

> **[FACT]** DeepResearcher の emergent behaviors: 計画策定、多ソース相互検証、自己反省、正直さ — これらは HGK の BC 体系と構造的に一致。

---

## 次のアクション {#sec_06_next}

1. **STORM 論文 /eat+** → 多視点質問生成アルゴリズムを Periskopē に統合
2. **DeepResearcher /eat+** → RL emergent behaviors と HGK BC の照合
3. **反復問い探索の実装** → `F:[×N]{/zet~*/sop}` を engine.py に実装
4. **S2 API 接続調査** → 依然 0 件の根本原因を特定

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "Periskopē の改善履歴"
  - "Deep Research の設計思想"
  - "CCL による認知ツール設計"
  - "競合 Deep Research サービスの比較"
answer_strategy: "技術改善 (Fix 1-6) と哲学的転換 (認知ツール化) を分けて説明。CCL 式 F:[×N]{/zet~*/sop} が核心。"
confidence_notes: "技術 Fix は全てテスト済み (15/15 PASSED)。哲学的転換は Creator 承認済み。S2 0件は未解決。"
related_roms: []
-->
