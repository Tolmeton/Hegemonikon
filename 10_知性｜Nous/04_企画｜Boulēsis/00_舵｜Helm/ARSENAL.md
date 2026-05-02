# 🔴 ARSENAL — HGK App 開発で使う既存 PJ 完全マップ

> **手作業でコードを書く前に、ここを確認しろ。**

---

## Tier 1: 開発タスク自動化 (CCL Pipeline)

| モジュール | パス | 能力 | CLI |
|:---|:---|:---|:---|
| **dispatch.py** | `hermeneus/src/dispatch.py` | CCL→AST→計画テンプレート | `python hermeneus/src/dispatch.py '/ene+'` |
| **Coordinator** | `synergeia/coordinator.py` | CCL→最適スレッド dispatch | `python synergeia/coordinator.py '/ene+'` |
| **JulesPool** | `synergeia/jules_api.py` | 6アカ/3並列/ラウンドロビン | `python synergeia/jules_api.py create "task"` |
| **jules_client** | `mekhane/symploke/jules_client.py` | async API, セッション追跡 | import のみ |
| **Executor** | `hermeneus/src/executor.py` | compile→execute→verify→audit | import のみ |

## Tier 2: アプリ機能のバックエンド

| モジュール | パス | 能力 |
|:---|:---|:---|
| **WorkflowRegistry** | `hermeneus/src/registry.py` | WF 定義の正本 (YAML→dataclass) |
| **CCLGraphBuilder** | `hermeneus/src/graph.py` | CCL AST → StateGraph (ノード+エッジ) |
| **morphism_proposer** | `mekhane/taxis/morphism_proposer.py` | trigonon→射提案 |
| **Attractor** | `mekhane/fep/attractor_advisor.py` | Series/Theorem 推薦 |
| **doxa_promoter** | `mekhane/symploke/doxa_promoter.py` | beliefs 昇格 |
| **Anamnesis** | `mekhane/anamnesis/` | Gnōsis ベクトル検索 + PKS 統合 |
| **Peira health** | `mekhane/peira/hgk_health.py` | ヘルスチェック |
| **Dendron** | `mekhane/dendron/` | 存在証明検証 |
| **Periskopē** | `mekhane/periskope/` | Deep Research エンジン |
| **Synteleia** | `mekhane/synteleia/` | 認知アンサンブル監査 |
| **Aristos** | `mekhane/fep/aristos/` | L2 進化的重み最適化 |
| **SweepEngine** | `mekhane/fep/sweep_engine.py` | 多視点パラメータスキャン |

## Tier 3: インフラ・安全

| モジュール | パス | 能力 |
|:---|:---|:---|
| **gpu_guard** | `mekhane/symploke/gpu_guard.py` | GPU 競合防止 (RTX 2070 SUPER) |
| **EnergeiaCoreResolver** | `mekhane/poiema/flow/energeia_core.py` | Metron レベル→モデル選択 |
| **EpocheShield** | `mekhane/poiema/flow/epoche_shield.py` | PII マスキング |
| **basanos_reviewer** | `mekhane/symploke/basanos_reviewer.py` | 偉人評議会レビュー |
| **CortexClient** | `mekhane/ochema/cortex_client.py` | Gemini/Claude API ラッパー |
| **TokenVault** | `mekhane/ochema/token_vault.py` | マルチアカウント認証管理 |

## MCP サーバー (全12サーバー稼働中)

| サーバー | パス / ソース | 機能 |
|:---|:---|:---|
| **digestor** | `mekhane/mcp/digestor_mcp_server.py` | 論文・文書消化プロセスの実行 |
| **gws** | `mekhane/mcp/gws_mcp_server.py` | Google Workspace 連携 |
| **hermeneus** | `hermeneus/src/mcp_server.py` | CCL 解析・実行・監査・ログエクスポート |
| **hub** | `mekhane/mcp/hub_mcp_server.py` | ゲート監査・ツール推奨・統計 |
| **jules** | `mekhane/mcp/jules_mcp_server.py` | Gemini Code Assist 連携と並列実行管理 |
| **mneme** | `mekhane/mcp/mneme_server.py` | 知識検索・MECE監査・Dejavu検知 |
| **ochema** | `mekhane/mcp/ochema_mcp_server.py` | LLM 呼び出し (Claude/Gemini)・計画生成 |
| **periskope** | `mekhane/mcp/periskope_mcp_server.py` | Deep Research・多ソース並列検索 |
| **phantazein** | `mekhane/mcp/phantazein_mcp_server.py` | Boot・成果物レポート・状態監視 |
| **sekisho** | `mekhane/mcp/sekisho_mcp_server.py` | Agent 最終応答 BC 監査 |
| **sympatheia** | `mekhane/mcp/sympatheia_mcp_server.py` | 自律神経系 (WBC, Attractor, Digest) |
| **typos** | `mekhane/mcp/typos_mcp_server.py` | .typos ファイル生成・コンパイル検証 |

## HGK API (serve.py, port 9698)

| カテゴリ | エンドポイント例 | 数 |
|:---|:---|---:|
| LLM | `/api/ask`, `/api/ask/stream`, `/api/ask/agent` | 5 |
| Jules | `/api/jules/sessions`, `/api/jules/sources` | 8 |
| Files | `/api/files/list`, `/api/files/read` | 3 |
| HGK Gateway | `/api/hgk/gateway/trace`, `/api/hgk/ide/*` | 5 |
| PKS / Sympatheia | `/api/pks/push`, `/api/sympatheia/notifications` | 3 |
| Status | `/api/health`, `/api/status` | 2 |

---

*Updated: 2026-03-20 — 最新 MCP サーバー構成（全12サーバー）を反映*
