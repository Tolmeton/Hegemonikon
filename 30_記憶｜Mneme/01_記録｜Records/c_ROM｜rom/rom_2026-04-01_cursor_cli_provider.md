---
rom_id: rom_2026-04-01_cursor_cli_provider
session_id: 880f6741-d48c-42c0-bae9-b110c28be756
created_at: 2026-04-01 22:15
rom_type: distilled
reliability: High
topics: [cursor-cli, ochema, multi-agent-routing, subprocess, openai-compat, model-registry]
exec_summary: |
  Ochema ブリッジに Cursor CLI Provider を統合。Claude Code CLI と対称の subprocess パターンで
  _ask_cursor / _stream_cursor を実装し、5ルート・ルーティング基盤（LS / Cortex / Claude Code / Cursor / Vertex）を確立。
  _MODEL_REGISTRY による統一モデル名解決と、環境変数ベースのバイナリ構成を完成。テスト全 PASS。
---

# Cursor CLI Provider 統合 — Multi-Agent Routing Infrastructure

## [DECISION] 5ルート・ルーティング基盤

Ochema ブリッジは以下の5プロバイダへの透過的ルーティングを提供する:

| ルート | プロバイダ | 接続方式 | モデル名 |
|:---|:---|:---|:---|
| `ls` | Language Server | ConnectRPC | claude-sonnet-4-6, claude-opus-4-6, gemini-3.1-pro-preview |
| `cortex` | Cortex REST API | HTTP/JSON | gemini-3.1-pro-preview, claude-sonnet-4-6 |
| `claude_code` | Claude Code CLI | subprocess | claude-code |
| `cursor` | Cursor CLI | subprocess | cursor-agent |
| `vertex` | Vertex AI | gRPC | claude-opus-vertex |

## [DECISION] _MODEL_REGISTRY 設計

`openai_compat_server.py` L115-137 に配置。Cursor と Claude Code で**同一のモデル名**を共有可能:

```python
_MODEL_REGISTRY = {
    "[LS]:Claude Sonnet 4.6":  {"model": "claude-sonnet-4-6", "route": "ls", "tier": "1"},
    "[LS]:Claude Opus 4.6":    {"model": "claude-opus-4-6",   "route": "ls", "tier": "1"},
    "[Cortex]:Gemini 3.1 Pro": {"model": "gemini-3.1-pro-preview", "route": "cortex", "tier": "2"},
    "Claude code":             {"model": "claude-code",        "route": "claude_code", "tier": "util"},
    "Cursor agent":            {"model": "cursor-agent",       "route": "cursor", "tier": "util"},
}
```

**解決優先順位**: `_MODEL_REGISTRY` (完全一致) > ハイフンサフィックス (-ls, -cortex) > レガシー @記号

## [DECISION] Cursor CLI 実装パターン

Claude Code CLI と**完全対称**のパターンで実装:

| 側面 | Claude Code | Cursor |
|:---|:---|:---|
| ask | `_ask_claude_code` (subprocess.run) | `_ask_cursor` (subprocess.run) |
| stream | `_stream_claude_code` (Popen+Timer) | `_stream_cursor` (Popen+Timer) |
| バイナリ環境変数 | `HGK_CLAUDE_CODE_BIN` | `HGK_CURSOR_BIN` |
| 追加引数環境変数 | `HGK_CLAUDE_CODE_EXTRA_ARGS` | `HGK_CURSOR_EXTRA_ARGS` |
| CLI フラグ | `claude -p <prompt>` | `cursor -p <prompt>` |
| 認証 | ANTHROPIC_API_KEY | CURSOR_API_KEY |

## [DISCOVERY] ルーティング経路

OpenAI 互換エンドポイント (`/v1/chat/completions`) 経由:
```
Cursor/Claude Code → POST /v1/chat/completions (model="Cursor agent")
  → _normalize_model() → _MODEL_REGISTRY 完全一致 → model="cursor-agent", route="cursor"
  → svc.ask(model="cursor-agent")
  → _build_candidates() → [ModelCandidate(provider="cursor", model="cursor-agent")]
  → _execute_attempt() → _ask_cursor()
  → subprocess.run(["cursor", "-p", prompt])
```

Anthropic Messages API (`/v1/messages`) では cursor/claude_code ルートは 501 を返す（CLI ルートのため非対応）。

## [DISCOVERY] テスト結果

| テストクラス | 件数 | 結果 |
|:---|:---|:---|
| TestCursorCLI | 13 | ✅ 全 PASS |
| TestClaudeCodeCLI | 10 | ✅ 全 PASS |
| ルーティングテスト (ASGI) | 13 | ✅ 全 PASS |
| その他 (Singleton, Models等) | 19 | ✅ 全 PASS |
| K9/fcntl/psutil (既知) | 8 | ⚠️ 環境依存 |

## [CONTEXT] 変更ファイル

1. **service.py**: `AVAILABLE_MODELS` に `cursor-agent` 追加、`_build_candidates` / `_execute_attempt` / `stream()` に cursor ルート追加、`_ask_cursor` / `_stream_cursor` 新規実装
2. **openai_compat_server.py**: `_MODEL_REGISTRY` に Cursor agent 追加、501 ガードメッセージ修正
3. **tests/test_service.py**: `TestCursorCLI` クラス新規追加 (13テスト)

## 関連情報

- 関連 WF: /exe, /tek
- 関連 KI: hegemonikon_ochema_ls_infrastructure, hegemonikon_agent_design_patterns
- 関連 Session: 880f6741-d48c-42c0-bae9-b110c28be756
- 前セッション: 同 ID (複数 continue)

<!-- ROM_GUIDE
primary_use: Cursor CLI プロバイダの実装詳細と設計判断の参照
retrieval_keywords: cursor cli, ochema bridge, multi-agent routing, subprocess provider, model registry, openai compat
expiry: permanent (アーキテクチャ文書)
-->
