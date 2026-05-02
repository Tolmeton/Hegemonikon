# 調査依頼: Cursor Agent モードのカスタム OpenAI API ルーティング

**作成**: 2026-03-28
**目的**: Cursor IDE の Agent モード (Composer) がカスタム OpenAI Base URL をサポートするか確定する

---

## 背景

Cursor Pro で「Override OpenAI Base URL」を設定し、自前の OpenAI 互換サーバーを指定している。curl での疎通は確認済み (200 OK)。しかし Cursor の Agent モードからリクエストが自前サーバーに到達しない。

### 確認済みの事実
- Cursor Settings > Models > Override OpenAI Base URL = ON
- Base URL: `http://<tailscale-host>:8765/v1` (正しく保存されている)
- API Key: 設定済み
- サーバー側 journalctl: Cursor からのリクエスト着信ゼロ (curl テストのみ記録)
- Cursor エラー: `[resource_exhausted] Error`
- エラースタック: `streamFromAgentBackend → getAgentStreamResponse`
- Cursor 内部 DB: `aiSettings.modelConfig.composer.modelName = "default"`, `availableAPIKeyModels = []`

---

## 調査事項 (Perplexity 向け)

### Q1: Agent モード (Composer) はカスタム OpenAI Base URL を経由するか？

Cursor の Agent モード (旧 Composer) で「Override OpenAI Base URL」を設定した場合、Agent モードのリクエストはそのカスタム URL に送信されるか？ それとも Agent モードは常に Cursor 自身のバックエンド (`api2.cursor.sh` / `api3.cursor.sh`) を経由し、カスタム URL は Ask モード等でのみ有効か？

特に知りたい点:
- Agent モードの内部関数 `streamFromAgentBackend` は OpenAI Base URL の override を参照するか？
- Cursor 0.46〜0.48 (2026年3月時点の最新版) での挙動
- Agent モード vs Ask モード vs Edit モード での API ルーティングの違い

### Q2: カスタムモデル名の選択が必要か？

Cursor のモデルドロップダウンで「default」を選んだままだと Cursor 内部モデルが使われる。カスタム OpenAI Base URL 経由のモデルを使うには:
- ドロップダウンにカスタムモデル名が自動で表示されるのか？
- それとも手動でモデル名を入力する必要があるのか？
- `availableAPIKeyModels` が空の場合、カスタムモデルは選択できないのか？

### Q3: `availableAPIKeyModels` はどう populate されるか？

Cursor の設定で `availableAPIKeyModels` が空配列 `[]` になっている。これは:
- `/v1/models` エンドポイントから自動取得されるのか？
- Cursor が `/v1/models` を呼んだとき、どのレスポンス形式を期待するか？ (OpenAI の `{"data": [{"id": "model-name", ...}]}` 形式？)
- Cursor が Base URL 設定後に自動で models を fetch するタイミングは？ (設定変更直後？ 起動時？)

### Q4: `resource_exhausted` エラーの意味

Cursor でカスタムモデルを選んだ際に `[resource_exhausted] Error` が出る。これは:
- Cursor 自身のクォータ制限のエラーか？ (Cursor Pro の使用量制限)
- それともカスタム API サーバーからのエラーをそのまま返しているのか？
- Agent モードでカスタム API が未対応の場合にこのエラーが出る仕様か？

### Q5: Cursor でカスタム OpenAI 互換サーバーを Agent モードで使う方法

成功事例があれば知りたい:
- ollama, LM Studio, vLLM, litellm 等のローカル LLM サーバーを Cursor Agent モードで使えている事例
- 必要な設定手順 (Base URL, API Key, モデル名の指定方法)
- Agent モードで使えない場合の回避策 (Ask モードのみ対応等)

---

## 検索キーワード候補

```
cursor agent mode custom openai base url not working
cursor composer custom api endpoint routing
cursor "override openai base url" agent mode
cursor availableAPIKeyModels empty
cursor resource_exhausted custom model
cursor agent mode local llm ollama
cursor streamFromAgentBackend custom api
cursor 0.47 agent mode openai compatible
```

---

## 期待する回答形式

各 Q に対して:
1. **結論** (YES/NO/不明)
2. **根拠** (公式ドキュメント / GitHub Issue / フォーラム投稿 / ソースコード分析)
3. **URL** (情報源のリンク)
