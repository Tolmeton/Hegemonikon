# proactive-knowledge-agent ⊣ PKS 随伴統合ビジョン (L3)

> **優先度**: B → ⑧ (Phase D: 仕上げ)
> **repo**: jpequegn/proactive-knowledge-agent
> **HGK 対象**: PKS (能動的知識プッシュエンジン — `mekhane/pks/` に15ファイル実装済み)
> **調査日**: 2026-03-14 (L3 SOURCE 完全読了版)

---

## 1. コードレベル比較

### 1.1 バックグラウンドスケジューリング

| 軸 | PKA (`daemon/scheduler.py`) | HGK (Motherbrain) |
| --- | --- | --- |
| フレームワーク | APScheduler `AsyncIOScheduler` | FastAPI 常駐プロセス (HTTP 委譲) + SQLite |
| ジョブ登録 | `IntervalTrigger` / `CronTrigger` ハードコード | MCP ツール呼び出し (手動/boot 時) |
| 即時実行 | `asyncio.create_task()` で起動時に全ジョブ fire | `motherbrain_boot` で Boot Context 生成 |
| ジョブ | RSS/60min, Market/240min, Podcast/360min, Fitness/120min, Report/Sun 18:00 | sync (full/incremental), health, quota, snapshot |
| 永続化 | PostgreSQL + pgvector + Redis | SQLite `motherbrain.db` |
| 死活監視 | なし | V-012 TCP health check 全 MCP サーバー |

**[SOURCE: scheduler.py]** PKA は `_setup_jobs()` で5つの `IntervalTrigger` / `CronTrigger` をハードコード登録。`run_forever()` で `asyncio.create_task()` による即時実行 + 無限ループ。

**[SOURCE: motherbrain_mcp_server.py L57]** HGK は `MB_API_BASE = http://127.0.0.1:9696/api/motherbrain` に HTTP で委譲する MCP プロキシ構造。バックグラウンドループ自体は FastAPI サーバー側。

### 1.2 エージェントアーキテクチャ

| 軸 | PKA (`agents/base.py`) | HGK (`pks/pks_engine.py`) |
| --- | --- | --- |
| 基底パターン | `BaseAgent` ABC — Monitor→Analyze→Decide→Alert | `pks_engine.py` + 15ファイル分散 |
| ドメインエージェント | 4種 (Tech/Fitness/Finance/Synthesis) | ドメイン非分割 (認知ワークフロー統合) |
| 確信度モデル | `Insight.confidence` (0.0-1.0) + `relevance_score` | Creator 関心プロファイルベース (推定) |
| フィルタリング | `min_confidence=0.5`, `min_relevance=0.3` | Sympatheia feedback ループ |
| 優先度計算 | `priority_score = level_weight × confidence × relevance` | `sympatheia_feedback()` 閾値動的調整 |
| プロジェクト提案 | `generate_project_ideas()` (abstract) | なし |

**[SOURCE: base.py]** PKA の `AlertLevel` 4段階: INFO (0.25) / WATCH (0.5) / ACTION (0.75) / URGENT (1.0)。`UserProfile.relevance_for_tech()` は interests/learning_goals/known_technologies の文字列マッチング (base 0.5 + interest 0.3 + learning 0.2 + known 0.1)。

**[SOURCE: sympatheia core.py]** HGK の Sympatheia は `sympatheia_notifications` (send/list/dismiss/purge) + `sympatheia_feedback` (閾値動的調整) + `sympatheia_wbc` (脅威分析) で通知基盤を提供。ただし「プロアクティブに情報をプッシュする」エージェントは不在。

### 1.3 World Model (知識グラフ)

| 軸 | PKA (`world_model/`) | HGK (Mneme/Gnōsis) |
| --- | --- | --- |
| ストレージ | PostgreSQL + pgvector (entity_versions, entity_mentions) | SQLite (Mneme) + JSONL (Gnōsis) + ファイルシステム (KI) |
| エンティティ型 | 6種 (Technology/Company/Person/Concept/Metric/Event) Pydantic | KI (知識アイテム) — フラット構造 |
| 関係 | `relationships.py` + `correlation.py` (cross-source) | `[[wikilink]]` バックリンク |
| 時間推論 | `TemporalReasoningService` — ChangeEvent, MentionStats, TrendResult, Anomaly | なし (手動 Handoff / ROM) |
| 変化検出 | `entity_versions` テーブル diff + 期間比較 | なし |
| 異常検出 | 3σ Spike / -2σ Drop / 14日 Silence | なし |
| 減衰関数 | `ExponentialDecay(half_life_days=7.0)` | Context Rot (N≤30 健全, >50 /bye 強制) |
| エンティティ抽出 | `extraction.py` (LLM ベース推定) | Digestor (Semantic Scholar API + 手動) |
| パイプライン | `pipeline.py` (Ingestion → Extraction → KG → Temporal) | Digestor → Gnōsis → Mneme (手動パイプライン) |

**[SOURCE: temporal.py]** PKA の `TemporalReasoningService` は核心的な差分:
- `get_changes_since()`: `entity_versions` テーブルから変更イベントを取得
- `get_mention_changes()`: 現在期間 vs 前期間の言及回数比較
- `analyze_trends()`: `TrendResult` (RISING/FALLING/STABLE + `change_ratio`)
- `detect_anomalies()`: `ABS(count - avg) > std * 2` の SQL ベース異常検出
- `ExponentialDecay`: `score = e^{-λt}` (λ = ln2/half_life)

**[SOURCE: entities.py]** 6種のエンティティ型は Pydantic BaseModel。各型に固有属性 (Technology.github_url, Company.stock_symbol, Person.organization 等)。`create_entity()` ファクトリ関数でディスパッチ。

### 1.4 MCP Server 統合

| 軸 | PKA (`outputs/mcp_server.py`) | HGK (9 MCP サーバー) |
| --- | --- | --- |
| プロトコル | MCP SDK 直接 (`mcp.server.Server` + `stdio_server`) | 同構造 (mcp-sdk) |
| ツール数 | 5 (search/trends/alerts/report/entity) | 9サーバー × 各4-12ツール |
| データアクセス | PostgreSQL 直接クエリ | HTTP 委譲 or 直接ファイルアクセス |
| 非同期 | `asyncio.run(main())` | 同 |

**[SOURCE: mcp_server.py]** PKA は `PKAMCPServer` クラスで `@self.server.list_tools()` / `@self.server.call_tool()` デコレータパターン。HGK と同一の MCP SDK 使用。

---

## 2. HGK PKS の実態

> [!IMPORTANT]
> 前回 ビジョン.md では「PKS は構想段階」と記載したが、実際には `mekhane/pks/` に**15ファイルの実装**が存在する。

```
pks/
├── __init__.py
├── attractor_context.py     # FEP 定理推薦コンテキスト
├── external_search.py       # 外部検索統合
├── feedback.py              # フィードバックループ
├── gateway_bridge.py        # ゲートウェイ連携
├── llm_client.py           # LLM クライアント
├── matrix_view.py          # マトリクス表示
├── narrator.py             # ナレーション生成
├── narrator_formats.py     # ナレーション形式
├── pks_cli.py              # CLI
├── pks_engine.py           # エンジン核心
├── push_dialog.py          # プッシュ通知ダイアログ
├── self_advocate.py        # 自己主張エンジン
├── semantic_scholar.py     # S2 統合
├── sync_watcher.py         # 同期ウォッチャー
```

### 既存の「プロアクティブ」機能 (散在)

| HGK モジュール | プロアクティブ機能 | PKA 対応 |
| --- | --- | --- |
| Motherbrain | Boot Context 自動生成, セッション監視, 全MCP死活監視 | scheduler + jobs |
| Sympatheia | 通知 (send/list/dismiss), フィードバック閾値動的調整, 脅威分析 (WBC) | alerts + base.py decide() |
| Digestor | Gnōsis 論文自動取り込み, Semantic Scholar API | ingestion/rss_processor |
| PKS | sync_watcher, push_dialog, narrator, self_advocate | world_model + agents |
| Mneme | 統合知識検索 (Gnōsis/Sophia/Kairos/Chronos) | world_model + mcp_server |

---

## 3. Gap 分析 (コードレベル)

| ID | Gap | PKA の実装 | HGK に足りないもの | 影響度 |
| --- | --- | --- | --- | --- |
| G-1 | **時間的推論** | `TemporalReasoningService` (変化検出, トレンド分析, 異常検出, 減衰関数) | KI/Gnōsis に temporal layer がない。変化は手動検出のみ | **高** |
| G-2 | **定期バックグラウンドジョブ** | APScheduler で 5 ジョブ自動実行 | Motherbrain はオンデマンド。定期 sync なし | **高** |
| G-3 | **ドメインエージェント** | 4種の特化エージェント (Monitor→Analyze→Decide→Alert) | PKS は単一エンジン。ドメイン分割なし | **中** |
| G-4 | **ユーザプロファイル** | `UserProfile` による relevance scoring | Creator 関心プロファイルの構造化データなし | **中** |
| G-5 | **エンティティ型モデル** | 6種の Pydantic エンティティ (Technology/Company/Person/Concept/Metric/Event) | KI は型なしフラット構造 | **低** |
| G-6 | **レポート自動生成** | `WeeklyReportGenerator` + Cron 日曜18時 | Motherbrain report はオンデマンド | **中** |

---

## 4. HGK 優位点

| ID | HGK の優位点 | PKA に欠けているもの |
| --- | --- | --- |
| S-1 | **認知フレームワーク統合** — Sympatheia (恒常性), Sekisho (監査), Hermeneus (CCL) との深い統合 | PKA は独立したシステム。認知制約なし |
| S-2 | **多モデル対応** — Ochema 経由で Claude/Gemini を使い分け | Claude API のみ (openai SDK 経由) |
| S-3 | **V-012 死活監視** — 全 9 MCP サーバーの TCP health check | なし |
| S-4 | **Context Rot 管理** — N≤30 健全 / 31-40 中間セーブ / >50 /bye 強制 | なし (セッション管理の概念自体がない) |
| S-5 | **学術知識基盤** — Gnōsis 222論文インデックス + Semantic Scholar API | RSS/Podcast/Market のみ。学術ソースなし |
| S-6 | **PKS 既存実装** — push_dialog, self_advocate, sync_watcher がプロアクティブ通知の萌芽 | 該当なし |

---

## 5. Import 候補の判定 (L3 再評価)

| ID | candidate | 判定 | 根拠 (SOURCE) |
| --- | --- | --- | --- |
| P-01 | **TemporalReasoningService パターン** | **Import** | PKA の変化検出・トレンド分析・異常検出 (3σ/14日) は HGK の Gnōsis/KI に完全に欠けている。MentionStats + TrendResult のデータモデルは PKS/Mneme に直接適用可能 |
| P-02 | **APScheduler 定期バックグラウンドジョブ** | **Import** | Motherbrain のオンデマンド実行を定期化するパターン。IntervalTrigger + CronTrigger の組み合わせは PKA の scheduler.py がそのまま参考になる |
| P-03 | **Monitor→Analyze→Decide→Alert パターン** | **Watch** | BaseAgent ABC は汎用パターンだが、HGK は認知ワークフロー (24動詞) により深い構造を持つ。ドメイン分割より認知分割が HGK の設計思想に合致 |
| P-04 | **UserProfile relevance scoring** | **Watch** | 文字列マッチングベースの素朴な実装 (base 0.5 + interest 0.3)。HGK には FEP ベースの Attractor (定理推薦) がある。Attractor の精度が上がれば不要 |
| P-05 | **6型エンティティモデル** | **Skip** | HGK は KI + Gnōsis + ROM で知識を管理。Pydantic 型分割は HGK のフラットな KI 構造に合わない |
| P-06 | **WeeklyReport 自動生成** | **Watch** | Motherbrain report + Handoff を組み合わせて近い機能が実現可能。専用の定期レポートは P-02 の Import で実現 |

---

## 6. Fix(G∘F) 随伴構造

```
F (発散・探索):
  PKA temporal → HGK に時間的推論を導入
  PKA scheduler → HGK に定期バックグラウンドジョブを導入
  PKA anomaly detection → HGK に異常検出を導入

G (収束・活用):
  HGK 認知フレームワーク (Sympatheia/Sekisho/Hermeneus) → PKA にない統合
  HGK Attractor (FEP 定理推薦) → UserProfile の代替 (精度↑)
  HGK Context Rot → セッション管理の代替

Fix(G∘F) = PIE (Proactive Intelligence Engine):
  Gnōsis/KI 変化検出 (temporal) ──→ 認知ワークフロー (24動詞) で分析
  ──→ Sympatheia 通知エンジンで Creator に通知
  ──→ Creator 反応 → Attractor 学習 → 時間的推論の精度向上
  ──→ ループ (Fix)
```

### 不動点検証

1. **時間的推論 × 認知ワークフロー**: temporal layer が Gnōsis の変化を検出 → /noe で分析 → Creator の発見が増える → 論文取り込みが増える → temporal layer の入力が増える → Fix
2. **定期バックグラウンド × Context Rot**: 定期 sync が Context Rot を予防 → 新鮮な情報が常時利用可能 → セッション品質向上 → Fix
3. **異常検出 × Sympatheia 通知**: 3σ 異常を自動検出 → Sympatheia 通知 → Creator が対応 → フィードバックで閾値調整 → 異常検出精度向上 → Fix

---

## 7. 実装ロードマップ

### Phase 0: TemporalReasoningService (P-01)

PKA の `temporal.py` パターンを HGK の Mneme/Gnōsis に適用:
- Gnōsis 論文の `first_seen` / `last_seen` / `mention_count` 追跡
- KI の変更履歴検出 (`git log` ベースの ChangeEvent)
- `analyze_trends()` による Gnōsis 論文のトレンド分析
- `detect_anomalies()` による新規トピックの急増検出

### Phase 1: SchedulerService (P-02)

PKA の `scheduler.py` パターンを Motherbrain に追加:
- `IntervalTrigger` で Gnōsis sync (6h), Mneme 再インデックス (24h)
- `CronTrigger` で週次レポート生成
- 起動時の即時実行 (`asyncio.create_task()`)
- Motherbrain FastAPI + APScheduler 統合

### Phase 2: Proactive Push (PIE 統合)

Phase 0 + Phase 1 + Sympatheia 通知の統合:
- temporal 変化検出 → Sympatheia `send()` でプッシュ
- フィードバックで閾値動的調整
- /boot 時に「前回セッションからの変化サマリ」を自動表示

---

## 8. 着手条件

| 前提 | 現状 | 判定 |
| --- | --- | --- |
| Digestor 安定稼働 | ✅ Gnōsis 222論文インデックス済み | 満たす |
| Sympatheia notification 成熟 | ✅ send/list/dismiss/purge 実装済み | 満たす |
| Motherbrain バックグラウンド安定 | ✅ FastAPI + SQLite + V-012 | 満たす |
| Creator 関心プロファイル蓄積 | ⚠️ Attractor (定理推薦) はあるがプロファイルは暗黙 | 一部 |

→ Phase 0 (TemporalReasoningService) は即着手可能。Phase 1-2 は Phase 0 完了後。

---

*Created: 2026-03-14 | Updated: 2026-03-14 (L3 SOURCE 完全読了版)*
