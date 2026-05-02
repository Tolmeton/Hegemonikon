# 引き継ぎ: OpenAI互換ブリッジ Cursor接続問題

**作成**: 2026-03-28 10:40 (Antigravity Claude → Cursor Claude)
**目的**: Cursor カスタムモデルから HGK OpenAI互換ブリッジに接続できない問題のデバッグ続行

---

## 1. 現在の状態

### ブリッジ (GALLERIA サーバー)
- **稼働状態**: `active` (systemd user service `hgk-openai-bridge.service`)
- **curl テスト**: ストリーム含め全て正常 (**200 OK**)
- **ファイル**: `mekhane/ochema/openai_compat_server.py` (456行)
- **接続先**: `http://hgk.tail3b6058.ts.net:8765/v1`
- **環境変数**: `HGK_OPENAI_COMPAT_TOKEN=99gblZXTpNgce2ZR_U9PLTf0wFl8GQ2Oxx3dllvsOc8`

### Cursor 側
- **エラー**: `[resource_exhausted] Error` (全試行で同一)
- **クォータ**: 57% 使用 (枯渇ではない)
- **モデル一覧**: ドロップダウンにカスタムモデル名は表示されている

---

## 2. 確定した事実 (SOURCE)

| 事実 | 根拠 |
|:-----|:-----|
| ブリッジ起動直後、Cursor からの初回リクエストは **422 Unprocessable Content** | GALLERIA journalctl |
| 422 以降、Cursor からのリクエストはブリッジに **到達していない** | journalctl (エントリゼロ) |
| `resource_exhausted` のスタック: `streamFromAgentBackend` → `getAgentStreamResponse` | Cursor エラーログ |
| curl でのブリッジテストは全て成功 (非ストリーム/ストリーム両方 200 OK) | コマンド実行結果 |
| Cursor Pro クォータは 57% 使用 (Total)、70% Auto+Composer、13% API | 設定画面スクリーンショット |

---

## 3. 実施済みの対策

### 3.1 Responses API 互換化 (422 対策)
Cursor Agent モードが `input: [...]` (Responses API形式) を送信する問題に対応:
- `ChatCompletionRequest` に `input→messages` 変換バリデータ追加
- `model_config = {"extra": "ignore"}` で未知フィールドを許容
- Cursor が送る追加フィールド (`top_p`, `tools`, `stop` 等) を定義

### 3.2 デバッグミドルウェア
`_DebugBodyLogger` を追加し、`/v1/chat/completions` への POST のリクエストボディを `RAW_REQUEST_BODY` としてログに記録。

### 3.3 systemd サービス
```ini
[Service]
Environment=HGK_OPENAI_COMPAT_TOKEN=99gblZXTpNgce2ZR_U9PLTf0wFl8GQ2Oxx3dllvsOc8
Environment=HGK_OPENAI_COMPAT_HOST=0.0.0.0
Environment=HGK_OPENAI_COMPAT_PORT=8765
Environment=HGK_OPENAI_COMPAT_ALLOW_REMOTE=1
```

---

## 4. 未解決の核心問題

**Cursor がカスタムモデルを選択しても、ブリッジにリクエストを送信しない。**

可能性:
1. **Cursor が一度 422 を受けたプロバイダを一時的にブラックリストした** — Cursor の再起動で解消するか？
2. **Cursor の `resource_exhausted` は内部のルーティング問題** — Agent モードがカスタム OpenAI API をバイパスしている可能性
3. **Base URL / API Key の設定が不完全** — `state.vscdb` (SQLite) を検索したが、カスタム API 設定の明示的なエントリは見つからず

---

## 5. 次にやるべきこと

### 優先度順
1. **Cursor を完全に再起動** (422 ブラックリストのリセット)
2. **Ask モード** (Agent ではなく) でカスタムモデルを選んでテスト
3. リクエスト到達を確認: `ssh galleria "journalctl --user -u hgk-openai-bridge.service --no-pager --output=cat --since '1 min ago'"`
4. もし到達しない場合、Cursor Developer Tools (Help → Toggle Developer Tools) でネットワークタブを確認し、実際にどの URL にリクエストを送っているか特定

### curl での動作確認コマンド (正常動作するリファレンス)
```powershell
# 非ストリーム
$body = '{"model":"[Cortex]:Gemini 3.1 Pro[0.4]","messages":[{"role":"user","content":"Hello"}],"stream":false}'
$body | Out-File -Encoding utf8 C:\tmp\test.json
curl.exe -s -X POST http://hgk.tail3b6058.ts.net:8765/v1/chat/completions -H "Authorization: Bearer 99gblZXTpNgce2ZR_U9PLTf0wFl8GQ2Oxx3dllvsOc8" -H "Content-Type: application/json" -d @C:\tmp\test.json
```

---

## 6. 方針転換: Cursor Chat → Claude Code + Hub MCP

### 結論 (2026-03-28 セッション2)

**Cursor の Agent/Ask 両モードとも自前 API に到達しない。これは Cursor の設計的制限。**

Perplexity 調査 (RESEARCH_CURSOR_AGENT_ROUTING_20260328.md) により確定:
- Agent モードは Cursor バックエンド専用 (LiteLLM 公式が「Agent は custom keys 非対応」と明記)
- `resource_exhausted` は「BYOK で Agent を使おうとした → 課金プールチェックで拒否」
- Ask モードでも到達しなかった (実地テスト)

### 新方針: Claude Code + Hub MCP で自前 API を使う

```
Claude Code (Anthropic API) → Hub MCP (GALLERIA:9700) → ochema (9701) → Gemini/Claude
```

- `.mcp.json` を `localhost:9700` → `http://hgk.tail3b6058.ts.net:9700/mcp/hub` に変更済み
- 新セッションで Hub MCP が直接見えるはず (`hub_execute` 等)
- `hub_execute backend=ochema tool=ask` で自前 API (Gemini/Claude) にサブ質問を投げる

### 次にやること (新セッションで)
1. Hub MCP ツール (`hub_execute` 等) が見えるか確認
2. `hub_execute` で ochema 経由の Gemini/Claude に打診
3. 動作確認後、Claude Code → hgk_ask でサブ質問のワークフローを確立
4. 補助経路として Cursor API (Background Agent API) の調査

## 7. 変更ファイル

| ファイル | 変更内容 |
|:---------|:---------|
| `mekhane/ochema/openai_compat_server.py` | Responses API 互換化、デバッグミドルウェア追加 |
| `~/.config/systemd/user/hgk-openai-bridge.service` (GALLERIA) | 新規作成、環境変数設定 |
| `.mcp.json` | Hub MCP URL を `localhost:9700` → Tailscale アドレスに変更 |
| `mekhane/ochema/RESEARCH_CURSOR_AGENT_ROUTING_20260328.md` | Perplexity 調査依頼書+結果 |
