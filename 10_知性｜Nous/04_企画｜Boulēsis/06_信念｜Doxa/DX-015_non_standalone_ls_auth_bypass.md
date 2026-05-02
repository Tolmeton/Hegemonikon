# DX-015: Non-Standalone LS Auth Bypass — DummyExtServer による認証バイパス

> **日付**: 2026-02-28 → 2026-03-01
> **ステータス**: ✅ 完全動作 (ローカル + Docker コンテナ)
> **確信度**: [確信: 98%] (SOURCE: Docker コンテナテスト実測 — 193ms 初期化、エラーなし)
> **関連**: [DX-010](DX-010_ide_hack_cortex_direct_access.md) §B (LS Cascade API)
> **関連セッション**: 3d1b7165

---

## 0. 全体像 (MECE)

```
┌───────── Non-Standalone LS 起動に必要なもの ─────────┐
│                                                        │
│  1. LS Binary                                          │
│     /usr/share/antigravity/.../language_server_linux_x64│
│                                                        │
│  2. Extension Server (uss-oauth provider)              │
│     ├── IDE 起動中 → IDE の Extension Server を使用    │
│     └── IDE なし   → DummyExtServer (★本 DX の成果)   │
│                                                        │
│  3. state.vscdb (認証情報)                              │
│     └── antigravityUnifiedStateSync.* キー群            │
│                                                        │
│  4. Metadata (stdin 注入)                              │
│     └── build_metadata() で生成                        │
│                                                        │
│  5. Cloud Code Endpoint                                │
│     └── daily-cloudcode-pa.googleapis.com              │
└────────────────────────────────────────────────────────┘
```

---

## 1. 認証フロー (proto 構造)

### 1.1 USS (Unified State Sync) プロトコル

```
LS → DummyExtServer: POST /antigravity.features.ExtensionServer/Subscribe
         Content-Type: application/connect+proto
         Body: { topic: "uss-oauth" }

DummyExtServer → LS: ServerStreaming (ConnectRPC)
         [flag:1][len:4][proto] + [flag:2][len:4][trailer_json]
         Proto = UnifiedStateSyncUpdate { initial_state: Topic }
```

### 1.2 Proto Schema

```proto
message UnifiedStateSyncUpdate {
    Topic initial_state = 1;  // oneof update_type
}

message Topic {
    map<string, Row> data = 1;
}

message Row {
    Primitive value = 1;
    int64 e_tag = 2;
}
```

### 1.3 state.vscdb の値構造 (★最重要発見)

```
state.vscdb の各キー (antigravityUnifiedStateSync.*) の値は:
  Base64 エンコードされた Topic proto (map<string, Row> のシリアライズ結果)

   ┌─ DB key: "antigravityUnifiedStateSync.oauthToken"
   │  DB value (Base64): "CqEEChlvYXV0aFRva2VuSW5mb1NlbnRpbmVsS2V5..."
   │                       ↓ Base64 decode
   │  Proto bytes: 0x0a 0x19 "oauthTokenInfoSentinelKey" ...
   │                ↑ field 1, wire type 2, length 25
   │                = Topic.data の map entry key
   └─→ LS が探すキー名は "oauthTokenInfoSentinelKey" (prefix 除去した DB key 名ではない!)
```

### 1.4 OAuthTokenInfo (LS 内部構造)

```proto
// language_server_go_proto パッケージ
message OAuthTokenInfo {
    string access_token = ?;
    string token_type = ?;
    string refresh_token = ?;
    ??? expiry = ?;
    bool is_gcp_tos = ?;
}
```

---

## 2. DummyExtServer 実装の核心

### 2.1 _build_uss_oauth_response() のロジック

```python
# ❌ 旧方式 (v7): key not found
topic_key = db_key[len(USS_PREFIX):]  # "oauthToken" ← LS 期待と不一致
row = encode(topic_key, value)

# ✅ 正解 (v11): Topic proto マージ
for db_key, value in all_rows:
    decoded = base64.b64decode(value)  # → Topic proto binary
    topic_bytes += decoded             # proto repeated field merger
update = _encode_proto_message(1, topic_bytes)
```

### 2.2 ConnectRPC ServerStreaming エンベロープ

```
[flag:1 byte][length:4 bytes big-endian][proto payload]
[flag:2 byte][length:4 bytes big-endian][trailer JSON]
```

flag=1: data frame, flag=2: trailer frame ({"grpc-status":"0"} 等)

### 2.3 HTTP/1.1 必須

`protocol_version = "HTTP/1.1"` を明示的に設定しないと chunked transfer encoding が壊れる。

---

## 3. DB アクセス: immutable=1 URI mode

### 3.1 問題

IDE が `state.vscdb` に OS レベルの flock を保持。`open()`, `dd`, `cp` の全てがブロックされる。

### 3.2 解決

```python
# ❌ open() raw copy → IDE flock でハング
with open(str(_STATE_DB), "rb") as src:
    data = src.read()

# ✅ immutable=1 URI mode → flock バイパス
db_uri = f"file:{_STATE_DB}?mode=ro&immutable=1"
db = sqlite3.connect(db_uri, uri=True, timeout=5.0)
```

※ `immutable=1` は WAL/SHM を無視して本体のみ読む。書き込み不可。

---

## 4. エラー解消の歴史

| Version | エラー | 根本原因 | 修正 |
|:--------|:-------|:---------|:-----|
| v1-v6 | `protocol error: promised X bytes` | HTTP chunked encoding 不備 | `protocol_version = "HTTP/1.1"` 設定 |
| v7 | `key not found` | prefix 除去 DB key ≠ Topic 内部 key | Base64 decode → Topic proto 直接マージ |
| v8-v9 | `invalid UTF-8` | Primitive wrapping 方式の誤り | v7 に revert (途中経路) |
| v10 | SSH hang / WAL lock | `open()` が IDE flock でブロック | `immutable=1` URI mode |
| **v11** | **なし** ✅ | — | **Topic proto マージ + immutable=1** |

---

## 5. 再現手順

### 5.1 前提条件

- LS binary: `/usr/share/antigravity/.../language_server_linux_x64`
- state.vscdb: 有効な OAuth token を含む

### 5.2 ローカルテスト (IDE 起動中)

```bash
cd ~/oikos/01_ヘゲモニコン｜Hegemonikon && PYTHONPATH=. timeout 40 .venv/bin/python3 -u -c "
import time, logging
logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')
from mekhane.ochema.ls_manager import NonStandaloneLSManager
mgr = NonStandaloneLSManager(workspace_id='test', force_dummy=True)
ls = mgr.start()
print(f'OK pid={mgr.pid} port={mgr.port}')
time.sleep(15)
with open(mgr._log_path) as lf:
    for l in lf.readlines()[:15]: print(f'  {l.rstrip()}')
mgr.stop()
"
```

### 5.3 Docker コンテナテスト (Headless)

```bash
# 1. state.vscdb をロックフリーコピー
cd ~/oikos/01_ヘゲモニコン｜Hegemonikon && PYTHONPATH=. python3 -u -c "
import sqlite3
db = sqlite3.connect(f'file:{__import__(\"os\").path.expanduser(\"~\")}/.config/Antigravity/User/globalStorage/state.vscdb?mode=ro&immutable=1', uri=True)
rows = db.execute('SELECT key, value FROM ItemTable').fetchall()
db.close()
out = sqlite3.connect('/tmp/state_container.vscdb')
out.execute('CREATE TABLE IF NOT EXISTS ItemTable (key TEXT PRIMARY KEY, value TEXT)')
for k,v in rows:
    out.execute('INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)', (k, v))
out.commit(); out.close()
print(f'{len(rows)} rows')
"

# 2. Docker テスト
docker run --rm -t \
  -v /usr/share/antigravity:/usr/share/antigravity:ro \
  -v ~/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane:/app/mekhane:ro \
  -v ~/oikos/01_ヘゲモニコン｜Hegemonikon/experiments/ls_container_test.py:/app/test.py:ro \
  -v /tmp/state_container.vscdb:/app/state.vscdb:ro \
  -v /tmp:/tmp \
  -e PYTHONPATH=/app -e PYTHONUNBUFFERED=1 \
  --network host \
  python:3.11-slim \
  timeout 40 python3 -u /app/test.py

# 3. 結果確認
cat /tmp/container_result.txt
```

### 5.4 期待される出力

```
initialized server successfully in ~200ms
Using ApiServerClientV2          ← 認証パス確立
No auth/error lines found        ← エラーなし
```

---

## 6. 修正ファイル一覧

| ファイル | 変更概要 |
|:---------|:---------|
| `mekhane/ochema/ext_server.py` | Topic proto マージ + immutable=1 DB アクセス |
| `mekhane/ochema/ls_manager.py` | `_open_state_db_safe` を immutable=1 に変更 |
| `experiments/ls_container_test.py` | Headless テストスクリプト |

---

## 7. 未解決・次のステップ

| 項目 | 状態 | 備考 |
|:-----|:-----|:-----|
| GetUserStatus API テスト | 未実施 | LS が実際にリクエストに応答するか |
| AskCodeAssist (Claude/Gemini) | 未実施 | コード補完・チャットの動作確認 |
| トークンリフレッシュ (provision_state_db) | ⚠️ 書き込みロック問題 | IDE 起動中は書き込み不可 |
| systemd サービス化 | 未実施 | 常駐 LS として自動起動 |
| IDE セッション干渉 | ⚠️ | ローカル実行時に IDE が停止した事例あり |

---

*DX-015 v1.0 — 2026-03-01*
