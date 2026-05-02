# 🛠️ Hegemonikón ツール チートシート v4.1

> **最終更新**: 2026-02-23
> **目的**: 「〜したい」→「何を使う」を即座に引ける実践ガイド

---

## 1. やりたいこと → ツール早見表

### 🔍 調べる

| やりたいこと   | ツール                              |
| :------- | :------------------------------- |
| ざっくり調べる  | `periskope_search`               |
| 深く調べる    | `periskope_research`             |
| 論文を探す    | `paper_search`                   |
| 知識を検索    | `sophia_search` / `mneme_search` |
| 内部ベクトル検索 | CLI: `cli.py search "query"`     |

### 🤖 LLM に聞く

| やりたいこと | ツール |
|:------------|:-------|
| 速く聞く (Gemini) | `ask_cortex` |
| 深く聞く (Claude) | `ask` |
| ツール付きで聞く | `ask_with_tools` |
| 会話する | `start_chat` → `send_chat` → `close_chat` |
| コードを書かせる | `jules_create_task` |

### ⚡ CCL を使う

| やりたいこと | ツール |
|:------------|:-------|
| CCL を解析 | `hermeneus_dispatch` |
| CCL を実行 | `hermeneus_execute` |
| WF 一覧を見る | `hermeneus_list_workflows` |
| 実行履歴を見る | `hermeneus_audit` |

### 🛡️ 管理・品質

| やりたいこと | ツール |
|:------------|:-------|
| システム状態 | `sympatheia_status` |
| ヘルスチェック | `sympatheia_peira_health` |
| 定理を推薦 | `sympatheia_attractor` |
| Nomoi 違反を記録 | `sympatheia_log_violation` |
| 違反ダッシュボード | `sympatheia_violation_dashboard` |
| モデル残量 | `cortex_quota` / `models` |

### 📚 消化・生成

| やりたいこと  | ツール               |
| :------ | :---------------- |
| 論文を消化   | `run_digestor`    |
| 消化候補を見る | `list_candidates` |
| プロンプト生成 | `typos_generate`  |
| プロンプト検証 | `typos_validate`  |

> [!tip]- 入力例 (クリックで展開)
>
> ```python
> # 調べる
> periskope_search(query="Rust async runtime")
> periskope_research(query="FEP and active inference", depth=3)
> paper_search(query="free energy principle", limit=10)
>
> # LLM
> ask_cortex(message="...", model="gemini-2.0-flash")
> ask(message="...", model="MODEL_CLAUDE_4_5_SONNET_THINKING")
> start_chat()  →  send_chat(conversation_id, "...")
>
> # CCL
> hermeneus_dispatch(ccl="/noe+")
> hermeneus_execute(ccl="/noe+", context="...", use_llm=true)
>
> # 管理
> sympatheia_attractor(context="目的を整理したい")
> jules_create_task(prompt="...", repo="owner/repo")
> ```

---

## 2. MCP サーバー詳細

### Hermēneus — CCL 実行ランタイム

> [!abstract]- 5ツール: CCL の解析・実行・検証
>
> | ツール | 概要 | 使いどころ |
> |:-------|:-----|:----------|
> | `hermeneus_dispatch` | CCL 式を AST にパース + 関連WF一覧 | CCL 式を見たらまず dispatch |
> | `hermeneus_execute` | CCL をコンパイル→LLM実行→検証 | WFの本格実行 |
> | `hermeneus_compile` | CCL → LMQL 変換 (実行なし) | デバッグ用 |
> | `hermeneus_list_workflows` | 利用可能WF一覧 | WF 名を忘れたとき |
> | `hermeneus_audit` | 実行履歴の照会 | 過去の CCL 実行を確認 |
> | `hermeneus_export_session` | チャット履歴のエクスポート | /bye 時に自動呼出し |

### Ochēma — LLM ブリッジ

> [!abstract]- 10+ツール: Claude/Gemini への統一アクセス
>
> | ツール | モデル | 特徴 |
> |:-------|:-------|:-----|
> | `ask` | Claude Sonnet 4.6 (default) | LS 経由。思考プロセス付き |
> | `ask_cortex` | Gemini 2.0 Flash (default) | 直接 API。高速・安定 |
> | `ask_with_tools` | Gemini 3.1 Pro (default) | ファイル読書き等のツール付き |
> | `ask_chat` | Gemini 3.1 Pro | 多ターン会話 (2MB, 100+ターン) |
> | `start_chat` | Claude/Gemini | 状態管理付き会話の開始 |
> | `send_chat` | — | 既存会話にメッセージ送信 |
> | `close_chat` | — | 会話を閉じてリソース解放 |
> | `jules_create_task` | Jules (Gemini) | コーディングタスクの作成 |
> | `jules_batch_execute` | Jules (Gemini) | 最大30タスク並列実行 |
> | `jules_get_status` | — | Jules タスクの進捗確認 |
> | `jules_list_repos` | — | 接続済み GitHub リポジトリ一覧 |
> | `models` | — | 利用可能モデル + 残量% |
> | `cortex_quota` | — | Gemini API クォータ確認 |
> | `status` | — | Cortex API 接続状態 |
> | `session_info` | — | 現在のセッション情報 |

### Periskopē — Deep Research

> [!abstract]- 6ツール: 多ソース並列検索 + 合成 + 検証
>
> | ツール | 所要時間 | 概要 |
> |:-------|:---------|:-----|
> | `periskope_search` | 10-15秒 | 軽量: 多ソース並列検索のみ |
> | `periskope_research` | 2-4分 | フル: 検索→合成→引用検証→レポート |
> | `periskope_sources` | 即時 | クエリに最適なソースを推薦 |
> | `periskope_track` | 即時 | 調査テーマの進捗管理 (CRUD) |
> | `periskope_metrics` | 即時 | 過去の品質メトリクス照会 |
> | `periskope_benchmark` | 数分 | 複数クエリの品質比較 |
>
> **ソース**: SearXNG, Brave, Tavily, Semantic Scholar, Gnosis, Sophia, Kairos
>
> **深度**: 1=Quick, 2=Standard (default), 3=Deep

### Sympatheia — 自律神経系

> [!abstract]- 8+ツール: 脅威分析・推薦・記憶圧縮・恒常性
>
> | ツール | 概要 |
> |:-------|:-----|
> | `sympatheia_status` | 全 state ファイルのサマリ (Boot Phase 4.9 推奨) |
> | `sympatheia_wbc` | 白血球: ファイル変更のスコアリング・脅威判定 |
> | `sympatheia_attractor` | 定理推薦: テキストから最適WFlを提案 |
> | `sympatheia_digest` | 記憶圧縮: 全 state ファイルの週次サマリ |
> | `sympatheia_feedback` | 恒常性: Health スコアで閾値を動的調整 |
> | `sympatheia_notifications` | 通知の取得・送信 |
> | `sympatheia_log_violation` | Nomoi 違反の JSONL 記録 |
> | `sympatheia_violation_dashboard` | 違反統計ダッシュボード |
> | `sympatheia_escalate` | Nomoi 違反の昇格候補検出 |
> | `sympatheia_peira_health` | 全サービスのヘルスチェック |
> | `sympatheia_basanos_scan` | AST ベースの品質スキャン |

### Digestor — 論文消化

> [!abstract]- 8ツール: Gnōsis → /eat 連携
>
> | ツール | 概要 |
> |:-------|:-----|
> | `paper_search` | Semantic Scholar で論文検索 |
> | `paper_details` | 論文の詳細情報 (DOI/arXiv ID) |
> | `paper_citations` | 被引用論文一覧 |
> | `list_candidates` | 消化候補の選出 |
> | `run_digestor` | 消化パイプライン実行 |
> | `get_topics` | 対象トピック一覧 |
> | `check_incoming` | 未消化ファイル確認 |
> | `mark_processed` | 消化完了→processed/ 移動 |

### Týpos — プロンプトエンジニアリング

> [!abstract]- 6ツール: .prompt ファイルの生成・解析・検証
>
> | ツール | 概要 |
> |:-------|:-----|
> | `generate` | 自然言語 → .prompt ファイル生成 |
> | `parse` | .prompt → JSON AST 解析 |
> | `validate` | .prompt の構文検証 |
> | `compile` | .prompt → システムプロンプト変換 |
> | `expand` | .prompt → 自然言語展開 |
> | `policy_check` | タスクが収束/発散かを判定 |

---

## 3. CLI ツール早見表

### 日常運用

```bash
# Quota チェック (Claude/Gemini 残量)
bash scripts/agq-check.sh

# セッション履歴
bash scripts/agq-sessions.sh --summary

# ログ収穫
bash scripts/agq-log-harvest.sh --env

# コンテキスト健全性
PYTHONPATH=. .venv/bin/python scripts/context_sentinel.py
```

### 知識検索

```bash
# Gnōsis ベクトル検索
PYTHONPATH=. .venv/bin/python mekhane/anamnesis/cli.py search "query"

# ソース指定検索 (session/handoff/rom)
PYTHONPATH=. .venv/bin/python mekhane/anamnesis/cli.py search "query" --source handoff --limit 3

# Gnōsis 再インデックス
PYTHONPATH=. .venv/bin/python scripts/reindex_gnosis.py
```

### Boot / Bye

```bash
# Boot 統合 (fast/standard/detailed)
PYTHONPATH=. .venv/bin/python mekhane/symploke/boot_integration.py --mode standard

# Boot Gnōsis 自動検索
PYTHONPATH=. .venv/bin/python scripts/boot_gnosis.py --queries 3

# PKS 能動的プッシュ
PYTHONPATH=. .venv/bin/python -m mekhane.pks.pks_cli auto --no-questions
```

### CCL / Hermēneus

```bash
# CCL パース
PYTHONPATH=. .venv/bin/python hermeneus/src/dispatch.py '/noe+'

# WF 実行
PYTHONPATH=. .venv/bin/python hermeneus/src/cli.py execute '/noe+' --context "分析対象"
```

### 品質・監査

```bash
# 存在証明チェック
PYTHONPATH=. .venv/bin/python mekhane/dendron/checker.py mekhane/

# Nomoi 違反分析
PYTHONPATH=. .venv/bin/python scripts/violation_analyzer.py

# WF ポストチェック
PYTHONPATH=. .venv/bin/python scripts/wf_postcheck.py /tmp/boot_report_*.md

# 定理利用スキャン
PYTHONPATH=. .venv/bin/python scripts/theorem_usage_scan.py
```

### インフラ

```bash
# PJ 自動登録
PYTHONPATH=. .venv/bin/python scripts/register_project.py <id> <path> --name "<名>"

# MCP プロセス確認
pgrep -af "mcp_server|mneme_server"

# Sync → テキスト同期
bash scripts/sync_hegemonikon_texts.sh
```

---

## 4. WF × ツール連携表

| WF | 使用ツール/モジュール | 備考 |
|:---|:---------------------|:-----|
| `/boot` | `boot_integration.py`, `agq-check.sh`, `boot_gnosis.py`, `pks_cli`, `context_sentinel.py` | 全自動統合 |
| `/bye` | `bye_persist.py`, `auto_bye.py`, `hermeneus_export_session` | Handoff 生成 |
| `/noe+` | `hermeneus_execute`, `ask`/`ask_cortex` | 7フェーズ深層思考 |
| `/dia` | `hermeneus_execute`, `verifier.py` | Multi-Agent Debate |
| `/eat` | `digestor`, `paper_search`, Periskopē | 論文消化パイプライン |
| `/sop` | `periskope_research` | Deep Research |
| `/ax` | `ax_pipeline.py`, 6× `peras_pipeline.py` | 6 Peras 統合 |
| `/ccl-plan` | `hermeneus_execute + macro_executor` | MacroExecutor 全自動 |
| `/ccl-search` | `periskope_search`/`periskope_research` | 多ソース検索 |
| `/ccl-vet` | `dendron`, `peira`, `hermeneus_execute` | 品質チェッカー |
| `/fit` | Manual analysis | HGK 適合度判定 |

---

## 5. モデル選択ガイド

| 用途 | 推奨モデル | Ochēma ツール | 深度 |
|:-----|:----------|:-------------|:-----|
| 速い回答 | Gemini 2.0 Flash | `ask_cortex` | L0-L1 |
| 標準分析 | Gemini 2.5 Flash | `ask_cortex(model="gemini-2.5-flash")` | L1-L2 |
| 深い思考 | Claude Sonnet 4.6 | `ask` | L2-L3 |
| 最深層 | Claude Opus 4.6 | `ask(model="MODEL_PLACEHOLDER_M26")` | L3 |
| ツール付き | Gemini 3.1 Pro | `ask_with_tools` | L1-L2 |
| 多ターン | Gemini 3.1 Pro | `ask_chat` | L1-L2 |
| コーディング | Jules (Gemini) | `jules_create_task` | — |

---

## 6. トラブルシューティング

| 症状 | 対処 |
|:-----|:-----|
| Quota 不明 | `bash scripts/agq-check.sh` |
| CCL が通らない | `hermeneus_dispatch(ccl="...")` でパースエラー確認 |
| LLM タイムアウト | `ask_cortex` (Gemini 直接) にフォールバック |
| Embedding 遅い | BGE-M3 CPU → VertexEmbedder に切替 (自動フォールバック済み) |
| Boot 遅い | `--mode fast` で軽量起動 |
| セッション劣化 | `context_sentinel.py` で N chat messages 確認 → `/bye` |
| MCP 接続エラー | IDE をリロード (`Reload Window`) + pgrep 確認 |

---

## 7. ファイル配置規約

| 生成物 | 配置先 |
|:-------|:-------|
| Handoff | `~/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff/handoff_*.md` |
| ROM | `~/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/rom_*.md` |
| Savepoint | `~/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff/savepoint_*.md` |
| Nomoi 違反ログ | `.agents/rules/behavioral_constraints/violations.md` |
| ブートレポート | `/tmp/boot_report_*.md` |
| チートシート | `~/Sync/01_ヘゲモニコン｜Hegemonikon/` |
| KI (Knowledge Item) | `~/.gemini/antigravity/knowledge/` |
| .prompt ファイル | `nous/skills/*/` |

---
*ツールチートシート v4.1 (2026-02-23)*

## 🔗 関連チートシート

- [[HGK_System_Structure_v4.1]] — 理論 (1公理 + 7座標 + 24動詞)
- [[HGK_WF_Cheatsheet_v4.1]] — 実践 (WF処理フロー・CCLマクロ)
- [[HGK_Project_Map_v4.1]] — 構造 (全モジュール・MCP・Skillカタログ)
- [[HGK_Tool_Cheatsheet_v4.1]] — 道具 (ツール早見・CLI・モデルガイド)
- [[HGK_Session_Lifecycle_v4.1]] — 運用 (BootからByeまでの標準フロー)
- [[HGK_Nomoi_Quick_Reference_v4.1]] — 規律 (Hóros 12法と BRD パターン)
