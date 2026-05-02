# GPT-Researcher ⊣ Periskopē 随伴統合ビジョン (L3)

> **優先度**: A → ⑦ (Phase D: 仕上げ)
> **repo**: assafelovic/gpt-researcher (★ 25,500+)
> **HGK 対象**: Periskopē (Deep Research Engine)
> **ライセンス**: Apache-2.0
> **調査日**: 2026-03-14 (L3 SOURCE 完全読了版)

---

## 1. コードレベル構造比較

### 1.1 エントリポイント・オーケストレーション

| 観点 | GPT-Researcher | Periskopē |
|------|---------------|-----------| 
| **メインクラス** | `GPTResearcher` (agent.py, ~800行) | `PeriskopeEngine` (engine.py, 3072行) |
| **エントリメソッド** | `conduct_research()` → `write_report()` 2段階 | `research()` 単一メソッド (L700-1069) で全段完結 |
| **設定方式** | `Config` クラス + 環境変数 (70+ env vars) | YAML config (`config_loader.py`) |
| **初期化** | query ごとに `GPTResearcher` を new (特に deep_research で再帰的に new) | `PeriskopeEngine` をシングルトン的に使い回し |
| **ストリーミング** | WebSocket + `stream_output()` | `progress_callback` + `ProgressEvent` (各 Phase 開始/終了で通知) |
| **コスト追跡** | `add_costs()` + `step_costs` dict | なし (quota は TokenVault 側で集中管理) |
| **MCP 統合** | MCP _client_: `MCPClientManager` (`mcp/client.py`) — `langchain-mcp-adapters` ラッパー。3種トランスポート (stdio/websocket/streamable_http) 自動検出 | MCP _server_ として公開 (periskope MCP)。自身は MCP client ではない |

### 1.2 検索パイプライン

| 段階 | GPT-Researcher | Periskopē |
|------|---------------|-----------| 
| **クエリ拡張** | `plan_research()` → LLM で sub_queries 生成 (skills/researcher.py) | 多段階: Φ0 `IntentDecomposition` (L1150-1166) → Φ0 `QueryPlan` 3段戦略 (L1171-1193) → W3 bilingual `QueryExpander` (L1210-1219) → Φ0.5 `TaskDecomposer` (L787-868) |
| **盲点分析** | なし | Φ1 `phi1_blind_spot_analysis` (L1196) + `phi1_counterfactual_queries` (L1202-1208) |
| **発散思考** | なし | Φ2 `phi2_divergent_thinking` (L1234-1250) — depth≥2 で candidates 最大8個 |
| **文脈設定** | なし | Φ3 `phi3_context_setting` (L1252-1263) — site-scoped domains + query_type 分類 |
| **事前ランキング** | なし | Φ4 `phi4_pre_search_ranking` (L1265-1279) — max_queries=5 に収束 |
| **ソース型** | 6型分岐: Web/Local/Hybrid/Azure/LangChain/VectorStore. Retriever は `retrievers/__init__.py` で **15種をハードコードインポート** | `sources` パラメータ: 16個の Searcher を enabled/disabled |
| **検索実行** | `get_search_results()` → retriever 1つずつ順次実行 | `_phase_search()` → `asyncio.gather()` で全 Searcher 並列 (L909-911) + Entity-based source routing (L890-902) |
| **MCP 検索** | `MCPRetriever` — MCP _client_ として外部サーバに接続。`MCPToolSelector` (LLM ベース tool 選択 + pattern-match fallback) | 自身が MCP server。検索は自前実装 |
| **Deep Research** | `DeepResearchSkill` (skills/deep_research.py) — breadth/depth/concurrency でツリー探索。**各クエリに新しい GPTResearcher インスタンスを生成して再帰的に conduct_research()。** breadth は depth 減少で半減 `max(2, breadth//2)`, `asyncio.Semaphore` で並列制御 | `depth=3` + CoT Search Chain (Phase 2.5, L1410-1600+) + Φ0.5 Task Decompose (1段, L787-868) |

### 1.3 コンテキスト処理・フィルタリング

| 観点 | GPT-Researcher | Periskopē |
|------|---------------|-----------| 
| **コンテキスト圧縮** | `ContextCompressor` — LangChain Pipeline (RecursiveCharacterTextSplitter + EmbeddingsFilter). `VectorstoreCompressor`: FAISS + similarity_threshold. `WrittenContentCompressor`: 既存合成テキストとの重複排除. 全3種を `ContextManager` で統合 | `LLMReranker` (Stage 1 Flash + Stage 2 Pro cascade, L1350-1381). Dedup → Semantic Rerank → Quality Filter (domain blocklist + relevance_threshold=0.25) |
| **Deep Read** | `BrowserManager` — Playwright/BeautifulSoup/Selenium, 3段フォールバック | Phase 1.8 `_phase_deep_read` (L1384-1407) — `_select_urls_for_deep_read()` + `PageFetcher.fetch_many()` (httpx + Playwright fallback). depth≥2 で有効化 |
| **反復深化** | `DeepResearchSkill` の breadth×depth 再帰 (前述) | **Phase 2.5 CoT Search Chain** (L1410-1600+) — `ReasoningTrace` 蓄積型。max_iterations は depth 連動 ({1:1, 2:3, 3:5}). 4種の **Denoising Scheduler**: linear (default), cosine (Nichol & Dhariwal 2021), logsnr (Hang et al. ICCV 2025, Laplace decay), exponential. `KalonDetector` (Good-Turing saturation) + information gain 計測で早期停止 |
| **ソースキュレーション** | `SourceCurator` (skills/curator.py) — LLM でソースの credibility + relevance + reliability を評価しランキング | `phi4_pre_search_ranking` + `phi4_post_search_framing` (DecisionFrame) + `phi7_belief_update` |
| **コンテキスト制限** | `trim_context_to_word_limit()` — 25K words デフォルト | `_format_results()` (synthesizer.py L456-493) — 150K chars デフォルト, per-source adaptive budget |

### 1.4 合成・レポート・引用検証

| 観点 | GPT-Researcher | Periskopē |
|------|---------------|-----------| 
| **合成方式** | `ReportGenerator.write_report()` (skills/writer.py) — **単一 LLM call**. write_introduction/write_conclusion/get_subtopics/get_draft_section_titles 等の補助メソッド | `MultiModelSynthesizer` (synthesizer.py, 523行): **depth ベースのモデルルーティング** — L1: Gemini Pro / L2: Gemini Pro + Claude Sonnet / L3: Gemini Pro + Claude Opus. `asyncio.gather` で並列合成. 大量結果時はインクリメンタルチャンク合成 (15件/chunk) |
| **乖離分析** | なし | `detect_divergence()` (synthesizer.py L358-423) — confidence spread + BGE-M3/Vertex Embedder による semantic similarity. `agreement_score = 0.5 * (1 - confidence_spread) + 0.5 * semantic_similarity` |
| **引用検証** | なし | `CitationAgent` (citation_agent.py, 538行): **4層類似度計算** — (1) 直接部分文字列一致=1.0, (2) SequenceMatcher 文レベル, (3) keyword overlap, (4) semantic embedding (BGE-M3/Vertex). **N-10 TAINT 自動分類** — SOURCE≥0.85 / TAINT≥0.75 / FABRICATED<0.75 (Vertex Embedder calibrated). **F13 2-hop chain verification** — TAINT 引用のソース内リンクを辿り2次ソースで再検証 |
| **逆引き照合** | なし | `Layer C _reverse_lookup_url()` (citation_agent.py L462-508) — SearchResult pool から keyword overlap≥0.4 で URL 逆引き |
| **プロンプト管理** | ハードコード文字列 | Týpos `.prompt` ファイル (synthesizer.py L34-68) — `parse_file()` + `compile(format="markdown")` でコンパイル, フォールバック付き |
| **レポート型** | 7型: research/resource/outline/custom/subtopic/multi_agents/deep | 1型: `ResearchReport` (markdown/JSON 出力) |
| **認知フロー** | なし (Planner→Execution→Publisher の3段) | Φ0-Φ7 の7段階認知フロー (Phase 0-4 + belief update + auto-digest) |
| **次の問い** | なし | Φ7 `phi7_query_feedback` + `phi7_belief_update` (L1006-1042) + **Adaptive Depth**: quality < threshold で L(n)→L(n+1) 自動エスカレーション |

---

## 2. Gap 分析 (Periskopē に何が足りないか)

| ID | Gap | GPT-R 実装 | Periskopē 現状 | 影響度 |
|----|-----|-----------|---------------|--------|
| G-1 | **Retriever 登録の簡素化** | `get_retrievers(headers, cfg)` で config からクラスリスト生成。**ただし `retrievers/__init__.py` で15種をハードコードインポートしており、完全な動的登録ではない** (retrievers/utils.py の `get_all_retriever_names()` はディレクトリスキャンのみ) | `__init__` で 16 Searcher を直接初期化 | **両者とも制約あり。** GPT-R のインスタンス化パターンは参考になるが、import 自体は固定 |
| G-2 | **ツリー状深掘り** | `DeepResearchSkill` — breadth × depth × concurrency で**再帰的に新しい GPTResearcher を生成**。breadth 半減 `max(2, breadth//2)`. `asyncio.Semaphore` で並列制御 | Φ0.5 Task Decompose (max_subtasks=3) は1段のみ。CoT Search Chain は反復的だがツリー状ではない | L3 のサブトピック再帰探索が不可。**最も価値の高い Import 候補** |
| G-3 | **Agent 自動選択** | `choose_agent()` — LLM で最適 agent/role を決定 | なし (固定パイプライン) | 調査ドメインに応じた戦略切替ができない |
| G-4 | **コスト追跡** | `add_costs()` + step_costs per API call | なし | パイプライン毎のコスト最適化不能 |
| G-5 | **多レポート型** | 7つの ReportType (subtopic, multi_agents, deep 等) | 1つの ResearchReport | サブトピック別レポート等が不可 |
| G-6 | **MCP Client 統合** | `MCPClientManager` — `langchain-mcp-adapters` ラッパー + `MCPToolSelector` (LLM ベース tool 選択, relevance_score + reasoning, pattern-match fallback) | MCP _server_ として提供。外部 MCP client としての retrieval は未実装 | 外部ツールの retrieval を取り込めない |

### Periskopē が勝っている点

| ID | 優位点 | Periskopē 実装 | GPT-R 現状 |
|----|--------|---------------|-----------| 
| S-1 | **認知フロー** | Φ0 IntentDecomposition + QueryPlan → Φ1 blind-spot/counterfactual → Φ2 divergent → Φ3 context → Φ4 convergent ranking (engine.py L1074-1302) | なし |
| S-2 | **引用検証** | `CitationAgent` — 4層類似度 + N-10 TAINT 自動分類 + F13 2-hop chain verification (538行) | なし |
| S-3 | **多モデル合成** | `MultiModelSynthesizer` — depth ルーティング L1/L2/L3 + 並列合成 + `detect_divergence()` (BGE-M3/Vertex semantic similarity) | 単一 LLM call |
| S-4 | **Denoising Scheduler** | CoT Search Chain 内で4種の decay (linear/cosine/**logsnr**/exponential) + `KalonDetector` (Good-Turing saturation) | なし |
| S-5 | **並列検索** | 16 Searcher を `asyncio.gather` で並列 + Entity-based source routing (NL API) | Retriever 順次実行 |
| S-6 | **弁証法** | `DialecticEngine v2` (thesis/antithesis 並走) | なし |
| S-7 | **Adaptive Depth** | quality < threshold で自動的に depth エスカレーション (L1015-1042) | なし |
| S-8 | **プロンプト管理** | Týpos `.prompt` ファイル (コンパイル + フォールバック) | ハードコード文字列 |

---

## 3. Import 候補の判定

| ID | Candidate | 判定 | 根拠 |
|----|-----------|------|------|
| G-01 | **Retriever クラスリスト動的生成** | **Watch** | GPT-R 自身も `__init__.py` でハードコードインポート (15種) しており、完全な動的登録ではない。Periskopē もほぼ同構造 (16種)。参考にすべきは `get_retrievers()` のインスタンス化パターン (config → class dict → instance) だが、根本差はない |
| G-02 | **DeepResearchSkill ツリー探索** | **Import** | Periskopē の Φ0.5 は1段のみ。**GPT-R の再帰的 `conduct_research()` パターン** (query ごとに新 Researcher を生成、breadth 半減、Semaphore 並列制御) は L3 品質を構造的に向上させる。既存の `_in_subtask` フラグ + `synthesize_subtask_results()` 実装の拡張で実現可能 |
| G-03 | **Agent 自動選択** | **Watch** | `choose_agent()` は有用だが、Periskopē は Φ0-Φ7 認知フローで戦略を内包。分離のメリットが不明確 |
| G-04 | **Step-level コスト追跡** | **Watch** | TokenVault 集中管理で十分。GPT-R の `step_costs` は研究用メトリクスとして参考程度 |
| G-05 | **多レポート型** | **Skip** | Periskopē は MCP server として AI に統合されるため、レポート型多様化はクライアント側の責務 |
| G-06 | **MCP Client 統合** | **Watch** | GPT-R の `MCPRetriever` + `MCPToolSelector` (LLM ベース tool 選択) は興味深い。特に relevance_score ベースの tool 選択 + pattern-match fallback は将来的に有用。ただし Periskopē は MCP server 側のため、双方向化は設計変更が必要 |

---

## 4. Fix(G∘F) の実装上の核心

```
F: GPT-R DeepResearchSkill の再帰パターン → Periskopē Φ0.5 再帰化
   ・query ごとに research() を再帰呼出し (depth-1)
   ・breadth 半減: max(2, breadth // 2)
   ・Semaphore で並列制御 (concurrency_limit)
   ・コンテキスト制限: trim_context_to_word_limit → Periskopē の _format_results adaptive budget

G: Periskopē の認知フロー (Φ0-Φ7) + 多モデル合成 + 引用検証 → 再帰の各段に適用
   ・各再帰ステップが Φ1-4 cognitive expand を保持
   ・各段の合成で MultiModelSynthesizer + CitationAgent が動作
   ・再帰全体の統合時に Denoising scheduler が情報利得を制御

Fix(G∘F) = 再帰的深掘りを持ちながら各段で認知品質を保つ Periskopē
           ≈ GPT-R の探索幅 × Periskopē の認知深度
```

### 不動点の検証

| 条件 | F 適用後 (GPT-R → Periskopē) | G 適用後 (Periskopē → 再帰+認知) | Fix 検証 |
|------|------|------|------|
| L3 深掘り | 再帰的 subtask 探索が可能に | 各再帰段で Φ1-4 + TAINT 検証維持 | ✅ |
| 引用品質 | 再帰各段で CitationAgent 動作 | F13 2-hop chain verification が全段適用 | ✅ |
| 乖離検出 | MultiModelSynthesizer が再帰各段で並列合成 | divergence_report が各段で生成 → 統合時に比較 | ✅ |
| 早期停止 | KalonDetector + info_gain が再帰各段で計測 | saturation 検出で過剰深掘りを防止 | ✅ |
| コンテキスト制御 | `_format_results` adaptive budget が各段制限 | GPT-R の `trim_context_to_word_limit` 参考 | ✅ |

---

## 5. 実装ロードマップ

### Phase 0: Φ0.5 再帰化 (G-02) **← 最優先**

**対象**: `engine.py` L787-868 の `decompose_query` ブロック

```python
# Before: 1段の分解のみ
subtasks = await decompose_query(query, max_subtasks=3)
for st in subtasks:
    sub_report = await self.research(st.query, depth=max(1, depth-1), ...)
# → 各 subtask は必ず depth-1 で止まる

# After: GPT-R DeepResearchSkill 参考の再帰化
# 既存の _in_subtask + synthesize_subtask_results() を活用
async def research(self, ..., _recursion_depth: int = 0):
    if depth >= 3 and _recursion_depth < MAX_RECURSION:
        subtasks = await decompose_query(query, max_subtasks=breadth)
        breadth_next = max(2, breadth // 2)  # GPT-R パターン
        sem = asyncio.Semaphore(concurrency_limit)
        async def _sub(st):
            async with sem:
                return await self.research(
                    st.query, depth=depth-1,
                    _recursion_depth=_recursion_depth+1, ...
                )
        subtask_reports = await asyncio.gather(*[_sub(st) for st in subtasks])
```

- `MAX_RECURSION = 2` (GPT-R default depth=3 → 3段相当)
- 各再帰ステップで Φ1-4 cognitive expand + MultiModelSynthesizer + CitationAgent が動作
- `KalonDetector` + info_gain で再帰各段の早期停止を判断

### Phase 1: MCP Tool Selection パターン (G-06 — Optional)

GPT-R `MCPToolSelector` の relevance_score ベース tool 選択パターンを参考に、将来的に Periskopē が外部 MCP サーバの retrieval を利用可能にする設計を検討。

### Phase 2: Step-level メトリクス (G-04 — Optional)

`research()` 内の `_notify()` に elapsed + token_count を追加し、`ResearchReport` に `phase_metrics` を新設。

---

## 6. DependencyChain

```
G-02 (Φ0.5 再帰化) → Phase 0 ← 最優先・単独で実装可能
  ↓ (独立)
G-06 (MCP Tool Selection) → Phase 1 (Optional)
  ↓ (独立)
G-04 (Step-level メトリクス) → Phase 2 (Optional)
```

G-01 (Retriever 登録) は前回 Import 判定だったが、SOURCE 読了後に **Watch に降格**。GPT-R 自身もハードコードインポートであり、根本差がないため。

---

*L3 SOURCE 完全読了版: 2026-03-14*
*読了ファイル: engine.py (3072行), synthesizer.py (523行), citation_agent.py (538行), deep_research.py, mcp/client.py, mcp/tool_selector.py, retrievers/__init__.py, retrievers/utils.py, skills/context_manager.py, skills/curator.py, skills/writer.py*
