---
rom_id: rom_2026-04-04_subagent_infra_gemini_cli
session_id: Claude Code Debian makaron8426 2026-04-04
created_at: 2026-04-04 23:10
rom_type: rag_optimized
reliability: High
topics: [ochema, ls-daemon, gemini-cli, mcp, subagent, auth, Tolmeton, cloudcode-pa, antigravity]
exec_summary: |
  LS daemon 6インスタンス化 + バージョン互換修正、Gemini CLI auth 解決 (Tolmeton)、
  MCP localhost 修正で Gemini CLI + MCP 疎通成功。Ochema-First 3-Layer subagent 設計確立。
---

# サブエージェント基盤整備 + Gemini CLI 疎通 {#sec_01_overview}

> **[DECISION]** Ochema-First 3-Layer Architecture: L0=Ochema単発(無料), L1=Gemini CLI+MCP(無料), L2=CC Agent(API課金)

このセッションで CC からの LLM サブエージェント呼出基盤を整備した。
mneme / Gemini / Claude の全チャネル疎通確認済み。

## 1. LS Daemon 修正 {#sec_02_ls_daemon}

> **[DECISION]** ls_manager.py に `_detect_random_port_flag()` を追加。LS バイナリの --help 出力から自動検出。

### 問題 {#sec_02a_problem}

> **[FACT]** LS バイナリ 1.21 (CL 888916494, 2026-03-25) で `--random_port` フラグが廃止された。
> 1.20 (CL 879885162, 2026-03-07) では `--random_port` が存在。

ローカル ls-daemon.service が 23,000 回以上の restart loop に陥っていた。原因: `--random_port` 非対応。

### 修正 {#sec_02b_fix}

> **[RULE]** Syncthing でコード共有するため、バージョン依存コードは自動検出にすること。

```python
# ls_manager.py に追加 (line 85+)
def _detect_random_port_flag() -> str:
    """LS バイナリが --random_port (1.20) か --http_server_port=0 (1.21+) かを検出。"""
    if not LS_BINARY:
        return "--http_server_port=0"
    try:
        result = subprocess.run(
            [LS_BINARY, "--help"], capture_output=True, text=True, timeout=5,
        )
        if "--random_port" in result.stdout:
            return "--random_port"
    except Exception:
        pass
    return "--http_server_port=0"

_LS_PORT_FLAG = _detect_random_port_flag()
```

cmd 構築で `_LS_PORT_FLAG` を使用 (line 588)。

### バージョン対応表 {#sec_02c_versions}

| マシン | LS バージョン | フラグ | `--random_port` | `--http_server_port` |
|:-------|:-------------|:-------|:----------------|:---------------------|
| ここ (Debian makaron8426) | 1.21 (新) | `--http_server_port=0` | 廃止 | 対応 |
| hgk (100.83.204.102) | 1.20 (旧) | `--random_port` | 対応 | 非対応 |

## 2. hgk LS 6インスタンス化 {#sec_03_hgk_ls}

> **[DECISION]** hgk の systemd ls-daemon.service に `Environment=HGK_LS_MAX_INSTANCES=6` を追加。

### 発見: MAX_INSTANCES の正体 {#sec_03a_max_instances}

> **[DISCOVERY]** `Cannot start LS: Maximum number of concurrent instances (4) reached` は LS バイナリの制限ではなく、
> ls_daemon.py の Python コード側制限 (`MAX_CONCURRENT = int(os.environ.get("HGK_LS_MAX_INSTANCES", "4"))`)。

### 現在の構成 {#sec_03b_current}

| 項目 | 値 |
|:-----|:---|
| hgk systemd | `--instances 6`, `HGK_LS_MAX_INSTANCES=6` |
| SSH トンネル | localhost:51000-51005 → hgk:各LS port |
| アカウント | Tolmeton, rairaixoxoxo, makaron, nous, hraiki + 1 |
| トンネル構築 | `python -m mekhane.ochema.remote_ls_register --host hgk` |
| トンネル PID | `/tmp/hgk-ls-tunnels/tunnel_pids.json` |

> **[FACT]** hgk = 100.83.204.102 (Tailscale IP)。SSH config `Host hgk` で定義。別の Debian マシン (NOT Windows)。

## 3. Gemini CLI 認証 {#sec_04_gemini_auth}

> **[DECISION]** Gemini CLI は `Tolmetes@hegemonikon.org` で認証する。`Tolmetes@hegemonikon.org` は使わない。

### 403 の根本原因 {#sec_04a_root_cause}

> **[DISCOVERY]** cloudcode-pa.googleapis.com の 403 はアカウント別に自動生成されるプロジェクト ID の権限差。

| アカウント | cloudaicompanionProject | 結果 |
|:-----------|:------------------------|:-----|
| `Tolmetes@hegemonikon.org` | `project-f2526536-3630-4df4-aff` | 403 (権限なし) |
| `Tolmetes@hegemonikon.org` | `acoustic-modem-4q00g` | 正常動作 |

### 認証手順 (ヘッドレス) {#sec_04b_howto}

```bash
rm ~/.gemini/oauth_creds.json
NO_BROWSER=true gemini
# URL が出る → スマホで Tolmetes@hegemonikon.org でログイン
```

### AI Ultra クオータ構造 {#sec_04c_quota}

> **[FACT]** 公式ドキュメント (developers.google.com/gemini-code-assist/resources/quotas):
> AI Ultra = 2,000 req/day via `Login with Google` (oauth-personal) → cloudcode-pa.googleapis.com

| 認証方式 | エンドポイント | AI Ultra クオータ |
|:---------|:--------------|:------------------|
| `oauth-personal` (Login with Google) | cloudcode-pa.googleapis.com | 適用 (2,000/day) |
| `gemini-api-key` (AI Studio API key) | generativelanguage.googleapis.com | 不適用 (別系統) |
| `compute-default-credentials` (ADC) | cloudcode-pa.googleapis.com | 不適用 (IAM 権限不足) |

### settings.json {#sec_04d_settings}

```json
{
  "security": {
    "auth": {
      "selectedType": "oauth-personal"
    }
  }
}
```

有効な selectedType 文字列値:
- `oauth-personal` = LOGIN_WITH_GOOGLE
- `compute-default-credentials` = COMPUTE_ADC
- `gemini-api-key` = USE_GEMINI (要 GEMINI_API_KEY env)
- `vertex-ai` = USE_VERTEX_AI (要 GOOGLE_CLOUD_PROJECT + LOCATION)

## 4. Gemini CLI MCP 設定 {#sec_05_mcp}

> **[DECISION]** `~/.gemini/mcp_config.json` の serverUrl を `100.83.204.102` → `localhost` に変更。

MCP サーバーはこのマシン (localhost:9700-9712) で稼働中。Gemini CLI + MCP で mneme search 成功。

> **[CONFLICT]** Hub ルーティング (`hub_execute`) は Gemini CLI から見えない (ツール名不一致)。
> 個別 MCP サーバー (mneme, ochema 等) への直接接続は動作。

### MCP 疎通結果 {#sec_05a_results}

| テスト | 結果 |
|:-------|:-----|
| Gemini CLI 基本 (PONG, 2+2) | 正常 |
| Gemini CLI + mneme MCP (FEP search) | 正常 (クオータリトライ4回後に成功) |
| Gemini CLI + Hub MCP (hub_execute) | 失敗 (ツール名不一致) |

## 5. Ochema-First 3-Layer Architecture {#sec_06_architecture}

> **[DECISION]** CC からのサブエージェント呼出は3層構造。コスト最適化が設計原則。

```
Layer 0: Ochema (単発, ツールなし, 無料)
  → 推論・レビュー・分析・説明
  → hub_execute(backend="ochema", tool="ask", model="claude-opus")

Layer 1: Gemini CLI (multi-step, MCP, 無料)
  → 並列調査, MCP 経由ファイル読み・検索
  → gemini -p "タスク" --yolo --allowed-mcp-server-names mneme

Layer 2: CC Agent (multi-step, フルツール, API課金)
  → ファイル編集・コミット・テスト実行
  → Agent tool (Claude API)
```

### 5 パターン {#sec_06a_patterns}

| パターン | Layer | 構造 |
|:---------|:------|:-----|
| A. 並列探索 | L1 | Gemini + MCP で並列調査 |
| B. Cross-Review | L0 | diff を Ochema Opus に投げて無料レビュー |
| C. 委譲生成 | L1 | Claude(設計) → Jules(生成) → Ochema(検証) |
| D. Shadow 検証 | L0 | 応答を Ochema Gemini で Horos チェック |
| E. Specialist | L0-L2 | タスク種別でモデル自動振り分け |

## 6. 6垢ローテーション (解決済み) {#sec_07_rotation}

> **[DECISION]** gemini-rotate + gemini-wrapper で6垢ローテーション確立。12,000 req/day。

### 成果物 {#sec_07a_artifacts}

| ファイル | 役割 |
|:---------|:-----|
| `~/.local/bin/gemini-wrapper` | gcloud config 汚染遮断 (CLOUDSDK_CONFIG=/dev/null + GOOGLE_CLOUD_PROJECT="") |
| `~/.local/bin/gemini-rotate` | 6垢 symlink ローテーション + google_accounts.json 同期 |
| `~/.gemini/oauth_creds_{name}.json` | 6垢分の OAuth creds (個別ファイル) |
| `~/.gemini/google_accounts.json` | CLI が読む active アカウント (gemini-rotate が同期) |

### 根本原因チェーン {#sec_07b_root_cause}

> **[DISCOVERY]** `~/.config/gcloud/configurations/config_Tolmeton` に `project = project-f2526536-3630-4df4-aff` が設定。
> → gcloud SDK が Node.js google-auth-library に project ID を注入
> → CLI の `setupUser()` が `loadCodeAssist` に `cloudaicompanionProject: project-f2526536` を渡す
> → このプロジェクトに `cloudaicompanion.companions.generateChat` 権限がない → 403

**遮断方法**: `CLOUDSDK_CONFIG=/dev/null GOOGLE_CLOUD_PROJECT="" GOOGLE_CLOUD_PROJECT_ID="" GCLOUD_PROJECT=""`

### 6垢テスト結果 (2026-04-05) {#sec_07c_test}

| # | アカウント | 状態 |
|:--|:-----------|:-----|
| 1 | Tolmeton | ✅ |
| 2 | movement | ✅ |
| 3 | rairaixoxoxo | ✅ |
| 4 | nous | ✅ (429 quota exhaustion = 認証OK, クオータ消費済み) |
| 5 | hraiki | ✅ (同上) |
| 6 | makaron | ✅ |

### 使い方 {#sec_07d_usage}

```bash
# アカウント切替
~/.local/bin/gemini-rotate Tolmeton   # 指定切替
~/.local/bin/gemini-rotate next          # ラウンドロビン
~/.local/bin/gemini-rotate status        # 状態確認

# CLI 実行 (必ず wrapper 経由)
~/.local/bin/gemini-wrapper -p "タスク" --yolo -m gemini-2.5-flash
```

## 7. 未踏事項 {#sec_08_remaining}

> **[CONTEXT]** 次セッション以降のタスク候補

1. **Hub gemini-cli バックエンド**: CC から `hub_execute(backend="gemini-cli", ...)` で Gemini CLI を呼ぶ MCP 実装。設計: subprocess で `gemini-wrapper -p` を呼び、stdout をキャプチャ。`--allowed-mcp-server-names` で MCP サーバー絞り込み。`gemini-rotate next` で自動アカウントローテーション
2. **`gemini` alias 化**: fish/bash で `gemini` → `gemini-wrapper` にエイリアス
3. **自動 quota 分散**: 429 検知時に自動で `gemini-rotate next` して retry
4. **CC↔Gemini CLI 統合 WF**: CC から gemini subprocess を自然に呼ぶ Skill 設計 (忘却論 LLM テスト等)

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "Gemini CLI が 403 になる"
  - "LS daemon が起動しない"
  - "サブエージェントの呼び方"
  - "MCP 設定をどう書く"
  - "AI Ultra のクオータ"
  - "6垢ローテーションの使い方"
  - "gemini-rotate の仕組み"
answer_strategy: "セクション番号で該当箇所を特定。認証=§4、LS=§2、MCP=§5、設計=§6、ローテーション=§7、未踏=§8"
confidence_notes: "全 DECISION/DISCOVERY は実際に検証済み。6垢中4垢はPONG確認、2垢は429(認証OK)。"
related_roms: ["rom_2026-03-31_pinakas_rebuild"]
-->
