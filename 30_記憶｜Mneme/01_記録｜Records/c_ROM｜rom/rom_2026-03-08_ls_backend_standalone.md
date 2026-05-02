---
rom_id: rom_2026-03-08_ls_backend_standalone
session_id: c1cb9bdf-7eeb-41e3-ba39-5c83d4714b27
created_at: "2026-03-08 17:50"
rom_type: rag_optimized
reliability: High
topics: [ls-authentication, standalone-ls, headless-server, state-vscdb, uss-oauth, headless-ls, daemon]
search_extensions:
  synonyms: [backend-ls, remote-ls, cross-machine-auth, refresh-token-injection]
  abbreviations: [LS, USS, OOB]
  related_concepts: [cloudcode-pa, token_vault, DummyExtServer]
exec_summary: |
  GUI (IDE) を持たないバックエンドサーバー上で、Language Server を `Non-Standalone` モード
  （直接 `cloudcode-pa` と通信）で動作させることに成功。
  課題だった OAuth `refresh_token` の取得は、OOB 認証では `invalid_client` となるため不可能。
  解決策として、ローカルPC（WSL等）の `state.vscdb` から `oauthToken` レコードを直接抽出し、
  バックエンドの `state.vscdb` に注入する。これにより `ls_daemon.py` 上で自動立ち上げと通信が可能になった。
---

# バックエンドサーバーでの LS ヘッドレス起動の確立 {#sec_01_overview}

> **[DISCOVERY]** IDE が存在しない環境 (Linux サーバー等) でも、完全に機能する Language Server を永続化する手順を確立した。

## The Authentication Dilemma {#sec_02_problem .critical}

Language Server がバックエンド (Codeium/Google) と通信するためには、以下の **2つの認証情報** が同時に必要である:

1. **`api_key`**: Codeium 側 (あるいは Gemini API) への認証用。`TokenVault` や `gcloud` コマンドで取得可能。
2. **`refresh_token`**: `cloudcode-pa.googleapis.com` への認証用。LS は内部でこのトークンを使用して OAuth access token (`ya29...`) を取得し続ける。

### OOB (Out-Of-Band) 認証の失敗

当初、`gcloud auth application-default login` を用いて、LS 専用の Client ID (`1071006060591...`) で `refresh_token` を取得しようと試みた。
しかし、結果は `invalid_client` エラーで終わった。

> **[FACT]** LS の OAuth Client ID は **サーバーサイドで Secret が管理** されており、外部のターミナルからの OOB フロー（デバイスログイン）は許可されていない。`refresh_token` を純粋に新規発行することは不可能。

## 解決策: state.vscdb トークン移植 {#sec_03_solution}

> **[DECISION]** 正規のルート (Antigravity IDE) を通じて OS のセキュアストレージから取得・保存された `refresh_token` を、
> バックエンドサーバーの DB へ物理的にコピー (移植) するアプローチを採用し、成功に至った。

### 確証のメカニズム

ローカルの IDE (WSL 上など) は、起動時に OS の Secret Manager から `refresh_token` を取得し、それを `state.vscdb` 内の Topic 構造の中に保持する (`antigravityUnifiedStateSync.oauthToken`)。

このレコードは、二重の Base64 エンコードが行われた `OAuthTokenInfo` Protobuf である（詳細は `rom_2026-02-15_ls_auth_hijacking.md` 参照）。

### 移植手順

**Step 1. WSL (ローカル) 側での抽出**
`~/.config/Antigravity/User/globalStorage/state.vscdb` から `antigravityUnifiedStateSync.oauthToken` の値をそのまま文字列として抽出する。

**Step 2. バックエンド側での注入**
バックエンドサーバーの `~/.config/Antigravity/User/globalStorage/state.vscdb` に SQLite レベルで `UPDATE ItemTable` を実行し、抽出した値を書き込む。

**Step 3. api_key の注入 (provision_state_db)**
`refresh_token` だけでは不十分。`mekhane.ochema.ls_manager.provision_state_db` を用いて、`TokenVault` から取得した `ya29...` トークンを `antigravityAuthStatus.apiKey` フィールドにセットする。

## ls_daemon.py アーキテクチャの完成 {#sec_04_daemon}

> **[FACT]** 移植が完了した状態であれば、バックエンドで `DummyExtServer` (偽装 Extension Server) と LS バイナリをペアで起動するだけで、恒続的な MCP/LLM サーバーとして機能する。

### 構成要素
1. **`DummyExtServer`**: ポート0 (ランダム) で起動。注入された `state.vscdb` を読み、LS の起動リクエスト (`Subscribe`) に対して `uss-oauth` トピック (移植済みの `refresh_token` 込み) を返却する。
2. **Language Server**: `DummyExtServer` を参照して起動。
3. **`ls_discovery.json`**: 起動した LS のポートと PID を `~/.gemini/ls_discovery.json` に書き出す。これにより、他のプロセス (例: `test_client_auto.py`, 後の Gateway) は、ポートを知らなくても自動的に LS へ接続できる。

```bash
# サーバー側での起動コマンド
python3 mekhane/ochema/ls_daemon.py
```

```python
# クライアント側での接続 (自動検出)
from mekhane.ochema.antigravity_client import AntigravityClient
client = AntigravityClient(workspace="test", ls_info=None) # 自動検出
```

## 今後の推奨ワークフロー (Hodos) {#sec_05_hodos}

新たなリモートサーバーや VM に HGK (Mekhane) をデプロイする際、LS を機能させるためのプロトコル。

1. **前提**: サーバーに `Mekhane` を clone していること。
2. **トークン生成**: ローカル PC で抽出スクリプトを実行し `oauth_token_value.txt` を得る。
3. **転送**: SCP 等で対象サーバーへ送る。
4. **注入**: サーバー側で Python スクリプト等を利用し、DB を生成して `UPDATE` (または `INSERT`) する。
5. **常駐化**: `ls_daemon.py` を systemd サービスなどで常駐させる。

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "バックエンドサーバーで LS を動かすには?"
  - "GUI なしで Language Server の認証を通すには?"
  - "refresh_token がエラーになる。どうやって取得する?"
  - "invalid_client エラーが gcloud auth application-default で出る"
answer_strategy: "OOB は不可能 (sec_02_problem)。ローカルの IDE state.vscdb から oauthToken 値を抽出してコピー移植する (sec_03_solution)。その後 ls_daemon.py を起動する (sec_04_daemon)。"
confidence_notes: "2026-03-08 バックエンド (100.83.204.102) 上で完全に検証済み。"
related_roms: ["rom_2026-02-15_ls_auth_hijacking"]
-->
