# Cursor カスタムモデル — OpenAI 互換ブリッジ

ローカルで `mekhane.ochema.openai_compat_server` を起動し、Cursor の **Custom API / OpenAI-compatible Base URL** から `OchemaService`（Gemini = Cortex 直、Claude = Language Server 経由）へ接続します。

**根拠 (DX-010):** Claude を REST `generateChat` だけで叩くと応答が偽陽性（表示モデルと実推論が一致しない）になるため、本ブリッジは **必ず `OchemaService`** を経由し、Claude は LS ConnectRPC 側に寄せます。

## 前提

- Python 環境に Mekhane の依存が入っていること（`fastapi` / `uvicorn`）。
- Google Antigravity / Cortex 用の認証が既に通っていること（`OchemaService` が通常どおり動く状態）。
- Claude を **ストリーミング**で使う場合は Language Server が利用可能であること（IDE 連携など）。

## 環境変数

| 変数 | 必須 | 説明 |
|------|------|------|
| `HGK_OPENAI_COMPAT_TOKEN` | はい | Bearer トークン。Cursor の **API Key** に同じ文字列を設定。 |
| `HGK_OPENAI_COMPAT_ALLOW_REMOTE` | いいえ | `1` のとき `verify_localhost` をバイパスし、ループバック以外の TCP 接続元を許可。**cloudflared 等でトンネル経由**からブリッジへ接続する場合に必要。Bearer 認証は必須のまま。 |
| `HGK_OPENAI_COMPAT_HOST` | いいえ | 既定 `127.0.0.1` |
| `HGK_OPENAI_COMPAT_PORT` | いいえ | 既定 `8765` |
| `HGK_LS_CONNECT_HOST` | いいえ | **ブリッジ → LS (ConnectRPC)** の接続先ホスト。既定 `127.0.0.1`。LS とブリッジが同一マシンならそのまま。別ホストの LS や SSH ローカルフォワード先はここか `~/.gemini/antigravity/ls_daemon.json` の `"host"` で揃える。**失敗の主因はタイムアウトではなく、この TCP 到達性（ポート取り違え含む）**のことが多い。 |
| `HGK_CLAUDE_CODE_BIN` | いいえ | `model=claude-code` 時のみ。Claude Code 実行ファイル（既定 `claude`）。 |
| `HGK_CLAUDE_CODE_EXTRA_ARGS` | いいえ | `claude-code` 時、`claude` と `-p` の間に shlex 挿入（例: `--bare`）。 |

**cloudflared / リモート公開:** トンネル先でブリッジを動かす場合は、`HGK_OPENAI_COMPAT_ALLOW_REMOTE=1` を設定し、`HGK_OPENAI_COMPAT_TOKEN` を Cursor の API Key と一致させる。`HGK_OPENAI_COMPAT_HOST` を `0.0.0.0` に広げると LAN から到達可能になります。Bearer トークンがあっても**露出面が増える**ため、本番用途では推奨しません。ループバックのまま運用するか、リバースプロキシと TLS で別途保護してください。

### Cloudflare Tunnel で URL を固定する

**クイックトンネル**（`cloudflared tunnel --url http://127.0.0.1:8765`）は **起動のたびに別の `*.trycloudflare.com` になる**。**同じ HTTPS URL を保ちたい**場合は **名前付きトンネル（Named Tunnel）** と **Cloudflare に載せたドメイン**が必要（無料アカウントでも可。ゾーンにドメインを追加する）。

| 方式 | URL | 備考 |
|------|-----|------|
| クイック | 毎回ランダム | 認証なしで試す向き |
| **名前付き** | **固定**（例: `https://ochema.example.com`） | `cloudflared tunnel create` + Public Hostname + DNS |

**概要手順:**

1. **`cloudflared tunnel login`** — ブラウザで Cloudflare にログイン。
2. **`cloudflared tunnel create <名前>`** — UUID と `~/.cloudflared/<UUID>.json`（認証情報）ができる。
3. **ルーティング** — [Zero Trust ダッシュボード](https://one.dash.cloudflare.com/) → **Networks → Tunnels** → 該当トンネル → **Public Hostname** で `Service: http://127.0.0.1:8765`、ホスト名を `ochema-openai.example.com` のように指定。または **`cloudflared tunnel route dns`** でサブドメインをトンネルに向ける（[Create a locally-managed tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-local-tunnel/)）。
4. **常時起動** — `cloudflared tunnel --config <config.yml> run`。Windows ではサービス化（[As a Windows service](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/configure-tunnels/local-management/as-a-service/windows/)）も可。

**Cursor の Base URL:** `https://<固定したホスト名>/v1`（末尾 `/v1`）。ブリッジ側はトンネル経由のため **`HGK_OPENAI_COMPAT_ALLOW_REMOTE=1`** を継続。

**設定ファイルの雛形:** 同ディレクトリの [cloudflared_config.example.yml](cloudflared_config.example.yml) を `%USERPROFILE%\.cloudflared\config.yml` 等にコピーし、`tunnel` / `credentials-file` / `hostname` を自分の値に置換する。

### 自動化スクリプト（Windows PowerShell）

`mekhane/ochema/scripts/` に起動用スクリプトを置いた。**固定 URL** は Cloudflare アカウント作業が必要なため [Register-NamedTunnel.ps1](scripts/Register-NamedTunnel.ps1) まで自動化し、DNS / Public Hostname はダッシュボードまたは `tunnel route dns` で完了させる。

| やりたいこと | コマンド（`scripts` で実行） |
|--------------|-------------------------------|
| ブリッジだけ（別ウィンドウ） | `.\Start-OchemaBridge.ps1 -Background` |
| ブリッジ + クイックトンネル | `.\Start-OchemaRemoteStack.ps1` |
| 名前付きトンネルだけ | `.\Start-OchemaNamedTunnel.ps1`（要 `config.yml`） |
| トンネル新規作成（login + create） | `.\Register-NamedTunnel.ps1` |

詳細は [scripts/README.md](scripts/README.md)。

## 起動

PowerShell の例:

```powershell
cd "…\20_機構｜Mekhane\_src｜ソースコード"
$env:HGK_OPENAI_COMPAT_TOKEN = "REPLACE_WITH_LONG_RANDOM_SECRET"
python -m mekhane.ochema.openai_compat_server
```

同等の uvicorn 直接起動:

```powershell
$env:HGK_OPENAI_COMPAT_TOKEN = "REPLACE_WITH_LONG_RANDOM_SECRET"
uvicorn mekhane.ochema.openai_compat_server:app --host 127.0.0.1 --port 8765
```

## Cursor 側の設定

1. **Settings → Models**（または Custom OpenAI-compatible API）を開く。
2. **Base URL** に次を指定（末尾は `/v1` を含む）:  
   `http://127.0.0.1:8765/v1`
3. **API Key** に `HGK_OPENAI_COMPAT_TOKEN` と**同じ**文字列を入力。
4. モデル一覧に載せたい **Model ID** を、下表の ID で選ぶ（Cursor のドロップダウンはクライアントにより `/v1/models` または手入力）。

## モデル名マッピング

サーバー実装は `OchemaService` のルーティングにそのまま渡します。主な ID（`mekhane/ochema/service.py` の `AVAILABLE_MODELS` と一致）:

| Model ID (例) | 備考 |
|---------------|------|
| `gemini-3-flash-preview` | 既定に近い Gemini（Cortex） |
| `gemini-3-pro-preview` | Gemini Pro |
| `claude-sonnet` / `claude-sonnet-4-6` | LS 経由（**実体は LS が解決**） |
| `claude-opus` / `claude-opus-4-6` | LS 経由 |
| `opus-vertex` / `opus-direct` | Vertex 経路（別クォータ・要 GCP 設定） |
| `claude-code` | **Anthropic Claude Code CLI**（`claude -p` headless）。PATH に `claude` または `HGK_CLAUDE_CODE_BIN`。LS/Cortex とは別ルート。 |

エイリアス（ブリッジ側の簡易マップ）: `gpt-4` / `gpt-4o` / `default` → `gemini-3-flash-preview`。

## エンドポイント

- `GET /health` — 認証なし（プロセス生存確認用）。
- `GET /v1/models` — Bearer 必須。`mekhane/ochema/service.py` の **`AVAILABLE_MODELS` を静的に列挙**（`OchemaService.models()` の動的マージは未実装。必要なら Python から直接 `OchemaService.get().models()` を参照）。
- `POST /v1/chat/completions` — OpenAI 形式。`content` は文字列のほか、Cursor が送る **配列形式**（例: `[{"type":"text","text":"..."}]`）は `openai_compat_server` の `ChatMessage` で**文字列に平坦化**。tool 呼び出しは未対応。`stream: true` のときは SSE (`data: ...` / `[DONE]`)。

## 診断・スモークテスト (curl)

**Base URL を変えたら最初にここで確認する**（再発防止の最小コスト）。

- Windows PowerShell では `curl` が `Invoke-WebRequest` のエイリアスになるため、次の例は **`curl.exe`** を使う。

**1. プロセス生存（認証なし）**

```powershell
curl.exe -sS "http://127.0.0.1:8765/health"
```

期待: `{"status":"ok"}` 相当。

**2. ルート認証（Bearer なしで 401 を確認）**

JSON ボディをファイルに置いてから実行するとエスケープ事故を避けられる。

```powershell
@'
{"model":"gemini-3-flash-preview","messages":[{"role":"user","content":"hi"}]}
'@ | Set-Content -Path $env:TEMP\ochema_smoke.json -Encoding utf8
curl.exe -sS -X POST "http://127.0.0.1:8765/v1/chat/completions" -H "Content-Type: application/json" --data-binary "@$env:TEMP\ochema_smoke.json" -w "`nHTTP_CODE:%{http_code}`n"
```

期待: `HTTP_CODE:401` と `Missing or invalid Authorization header`（ルートは生きている）。

**3. 完全な応答（`choices[0].message.content` の確認）**

`HGK_OPENAI_COMPAT_TOKEN` と同じ文字列を `YOUR_TOKEN` に置き換える。

```powershell
curl.exe -sS -X POST "http://127.0.0.1:8765/v1/chat/completions" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_TOKEN" `
  --data-binary "@$env:TEMP\ochema_smoke.json"
```

期待: HTTP 200 かつ JSON の `choices[0].message.content` に**非空**の文字列（Cortex / LS が利用可能な環境で）。

**4. リモート（trycloudflare 等）**

- トンネル URL が `https://<name>.trycloudflare.com` のとき、Base URL は **`https://<name>.trycloudflare.com/v1`**（末尾 `/v1`）。
- オリジン（ブリッジ）が停止していると **502 Bad Gateway**（Cloudflare 側のメッセージ）。先にローカルで手順 1–3 を通す。

## トラブルシュート

- **401 / Missing API key:** Cursor の API Key と `HGK_OPENAI_COMPAT_TOKEN` が一致しているか確認。
- **403 Only loopback:** リモートからは接続できません（127.0.0.1 のみ）。**cloudflared 等でトンネル経由**にする場合は `HGK_OPENAI_COMPAT_ALLOW_REMOTE=1` を設定し、Bearer を必ず維持する。
- **502 Bad Gateway (trycloudflare 等):** オリジンのブリッジが落ちている、またはトンネル先ポートがずれている。ローカルで「診断・スモークテスト」の手順 1–3 を先に通す。
- **Cursor で本文が空／「メッセージが空のようです」:** (1) 上記 curl で `choices[0].message.content` が非空か確認。ここで空なら **応答 JSON の契約**（推論だけ別フィールド等）を疑う。(2) curl は正常で Cursor だけ空なら **Base URL**（末尾 `/v1`）・**モデル ID**・Cursor バージョンを確認。(3) **本ブリッジ以外**のゲートウェイでは、Cursor の **multipart `content`** を平坦化していないとユーザー文が空になり、下流が空応答を返す。→「ブリッジ以外の OpenAI 互換プロキシ」を参照。
- **Claude（LS 経路）+ `stream: true` で表示だけ空:** 実装は互換のため **最初の SSE チャンクで `delta.content` が空**になり、その後に本文チャンクが続く。クライアントが最初のチャンクだけ描画すると空に見える。`stream: false` で再現するか比較する。
- **Claude でエラー（ストリーミング）:** LS が上がっていない可能性があります。`OchemaService` の LS 接続を確認してください。
- **`claude-code` で FileNotFound / 非ゼロ終了:** Claude Code をインストールし PATH を通すか `HGK_CLAUDE_CODE_BIN` を設定。対話プロンプトは出さず `-p` のみ使用。
- **利用規約・クォータ:** Google / Antigravity の契約とクォータはユーザー側の責任で確認してください（`kernel/doxa/DX-010_ide_hack_cortex_direct_access.md` 参照）。

## ブリッジ以外の OpenAI 互換プロキシを使う場合

LiteLLM、vLLM の OpenAI 互換、自前リバースプロキシなど **本リポジトリの `openai_compat_server` を経由しない**場合も、Cursor は `messages[].content` を **配列**で送ることがある。ゲートウェイがそれを解釈せず空文字になると、下流モデルが「空のユーザー入力」に反応し、本文が出ない／定型文だけになる。

**対処の方向性:** プロキシ側で OpenAI 形式の `content` を **文字列へ正規化**する、または LiteLLM のドキュメントに従い Cursor 向けの変換・モデルプロファイルを確認する。切り分けは「診断・スモークテスト」の curl で、**同じ JSON をプロキシに直 POST**して `choices[0].message.content` を見る。

## Gnōsis CLI ベクトル検索（関連）

`faiss` が入らない環境では、`python -m mekhane.anamnesis.cli search "query" --backend numpy` で brute-force バックエンドに切り替え可能です（大規模インデックスでは遅い）。

---

## アーキテクチャ全体像

```
┌─────────────────────────────────────┐
│  Cursor IDE (Agent / Chat)          │
│  Base URL: http://127.0.0.1:8765/v1 │
└────────────┬────────────────────────┘
             │ OpenAI 互換 HTTP
             ▼
┌─────────────────────────────────────┐
│  openai_compat_server.py            │
│  (FastAPI / uvicorn)                │
│  - Bearer 認証                      │
│  - ループバック制限                   │
│  - モデル名エイリアス解決              │
└────────────┬────────────────────────┘
             │ OchemaService.ask() / .stream()
             ▼
┌─────────────────────────────────────┐
│  OchemaService (service.py)         │
│  ┌──────────┐  ┌──────────────┐     │
│  │ CortexAPI │  │ LS ConnectRPC│     │
│  │ (Gemini)  │  │ (Claude)     │     │
│  └─────┬────┘  └──────┬───────┘     │
│        │              │             │
│   account_router      ls_manager    │
│   (ラウンドロビン)      (プロセス管理) │
└────────┬──────────────┬─────────────┘
         │              │
    ┌────▼────┐   ┌─────▼──────┐
    │ Cortex  │   │ LS Daemon  │
    │ REST API│   │ (ls_daemon │
    │ (GCP)   │   │  .py)      │
    └─────────┘   └────────────┘
```

- **Gemini 系モデル** → `CortexClient` → Google Cloud Cortex REST API 直接接続
- **Claude 系モデル** → `NonStandaloneLSManager` → Language Server ConnectRPC 経由
- Claude を REST で直接叩かないのは **DX-010** で定義された偽陽性問題の回避のため

## マルチアカウント LS プール

`account_router.py` でパイプラインごとにアカウントを割り当て、quota 競合を防止する。

### パイプライン → アカウント対応表

| パイプライン | アカウント | 方式 |
|:-----------|:----------|:-----|
| `ide` | `default` | 固定 |
| `mcp` | `movement`, `Tolmeton` | ラウンドロビン |
| `hermeneus` | `movement`, `Tolmeton` | ラウンドロビン |
| `periskope` | `movement`, `Tolmeton`, `rairaixoxoxo`, `hraiki` | ラウンドロビン |
| `chat` | `movement`, `Tolmeton` | ラウンドロビン |
| `batch` | `movement`, `Tolmeton`, `rairaixoxoxo`, `hraiki` | ラウンドロビン |
| `reserve` | `nous` | 固定（予備） |

### 使い方

```python
from mekhane.ochema.account_router import get_account_for

account = get_account_for("periskope")  # → "rairaixoxoxo" or "hraiki" ...
client = CortexClient(account=account)
```

未知のパイプライン名を渡すと `"auto"` が返り、TokenVault が自動選択する。

## LS デーモン運用

`ls_daemon.py` は Non-Standalone LS を常駐プロセスとして管理するデーモン。IDE に依存せず LS プールを維持する。

### 起動

```powershell
cd "…\20_機構｜Mekhane\_src｜ソースコード"
python -m mekhane.ochema.ls_daemon --num-instances 2
```

主なオプション:

| オプション | 既定 | 説明 |
|:----------|:-----|:-----|
| `--num-instances` | `1` | 同時に起動する LS インスタンス数 |
| `--workspace-prefix` | `nonstd_hgk` | LS ワークスペース名のプレフィックス |
| `--source` | `local` | `local` / `docker`（接続情報マージ時の識別子） |

### 接続情報の保存

起動するとデーモンは `~/.gemini/antigravity/ls_daemon.json` に接続情報を書き出す。`OchemaService` はこのファイルを自動的に読み取って LS に接続する。

環境変数 `LS_DAEMON_INFO_PATH` で保存先を変更可能（コンテナ運用時に利用）。

### 監視

デーモンはメインループでプロセスの生存を定期チェックし、クラッシュ時に自動再起動する。`SIGTERM`（Linux）でグレースフルシャットダウン。

## Cursor Agent 連携の注意

Cursor Agent チャットからこのブリッジを利用する場合:

1. **モデル名を正確に指定**する — Cursor の Model ドロップダウンで登録した ID と `AVAILABLE_MODELS` の ID が一致していること
2. **system_instruction はそのまま渡される** — Cursor の Rules / Knowledge が `system` ロールとして送信され、ブリッジが分離して `OchemaService.ask()` の `system_instruction` パラメータに渡す
3. **Agent の tool 呼び出しは未対応** — Cursor 標準のツール機能（ファイル操作等）はブリッジを経由しない。ブリッジは純粋なテキスト生成のみ対応

## セキュリティ詳細

| 防御層 | 実装 | 突破条件 |
|:------|:-----|:--------|
| ループバック制限 | `verify_localhost()` — クライアント IP を検査 | リバースプロキシ等で `X-Forwarded-For` を偽装（ただし `Request.client.host` は TCP 接続元なので偽装困難） |
| Bearer 認証 | `verify_bearer()` — `Authorization: Bearer <token>` を検査 | `HGK_OPENAI_COMPAT_TOKEN` の漏洩 |
| バインドアドレス | uvicorn `--host 127.0.0.1` | `0.0.0.0` への変更（環境変数） |

**推奨:** トークンは最低32文字のランダム文字列にする。`.env` に保存し、チャットやログに露出させない（θ4.6 / θ4.7 準拠）。

## 既知の制限

| 項目 | 状態 | 備考 |
|:-----|:-----|:-----|
| Tool Use (`tools` / `function_calling`) | **未対応** | Cursor 標準のツール呼び出しはブリッジを通らない |
| マルチパート Content (`content: [...]`) | **平坦化** | Cursor の配列 `content` は受信時にテキストへ結合（`openai_compat_server.ChatMessage`）。画像パート等は未対応 |
| `/v1/models` の動的マージ | **未実装** | `AVAILABLE_MODELS` の静的リスト。`OchemaService.models()` の結果をマージする拡張は TODO |
| 画像入力 | **未対応** | Gemini のマルチモーダル入力はブリッジ経由では利用不可 |
| クォータ表示 | **外部** | `ochema info(action='quota')` MCP ツールで確認 |
| Claude REST 直接接続 | **非推奨** | DX-010 で定義された偽陽性問題のため、LS 経由を使用すること |

## 関連ドキュメント

- [HANDOFF_CLAUDE_CODE_CURSOR_BRIDGE.md](./HANDOFF_CLAUDE_CODE_CURSOR_BRIDGE.md) — モデル ID `claude-code`（Claude Code CLI 経由）の実装背景・引き継ぎ用
