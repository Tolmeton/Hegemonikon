# 02_車体｜Ochema

> **PURPOSE**: LLM ブリッジ。Claude/Gemini を Language Server 経由で呼び出す統合インターフェース。

## `_src/` 対応コード
- [`mekhane/ochema/`](../../_src｜ソースコード/mekhane/ochema/) — Ochema MCP サーバー実装

## 機能
- `ask` / `ask_cortex` / `ask_with_tools` — LLM 呼び出し
- `start_chat` / `send_chat` / `close_chat` — 多ターン会話
- `context_rot_distill` / `context_rot_status` — Context Rot 管理
- `models` / `cortex_quota` — モデル・クォータ管理

## MAP
- KI: `system_architecture` → mcp_server_configuration

---
*Created: 2026-03-13*
