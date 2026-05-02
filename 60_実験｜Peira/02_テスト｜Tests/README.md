# 02_テスト｜Tests — 自動化テスト

MCP サーバー・Cortex API・Embedder 等の自動化テスト群。

## 内容

| ディレクトリ / ファイル | 概要 |
|:------------------------|:-----|
| `31_テスト｜Tests/` | 統合テストスイート |
| `32_テスト根｜TestsRoot/` | ルートレベルテスト |
| `test_cortex.py` | Cortex (Gemini) API テスト |
| `test_get_embedder.py` | Embedder 取得テスト |
| `test_jules_client.py` | Jules クライアントテスト |
| `test_mcp2.py` | MCP v2 テスト |

## 実行方法

```bash
# 個別テスト
python test_cortex.py

# テストスイート
cd 31_テスト｜Tests && pytest
```
