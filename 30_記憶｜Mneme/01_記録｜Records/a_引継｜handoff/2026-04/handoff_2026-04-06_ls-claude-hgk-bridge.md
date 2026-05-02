# Handoff: LS 経由 Claude — OpenAI 互換ブリッジ E2E 修復（hgk）

**Date**: 2026-04-06  
**Session Type**: infra / ochema / hgk  
**Confidence**: 高（hgk で実呼び出し確認済み）

---

## Situation

hgk 上で **トークン・ブリッジ・LS** が揃った状態で、**実 LS を含む E2E**（`curl` または `llm_judge.py`）が確実な経路である、という合意のもと、`POST /v1/chat/completions` が **502** になったり **assistant 本文が空**になったりする問題を潰した。

## Background

- **症状**: `/health` は通るが `POST /v1/chat/completions` が **502**（`timed out`）。`get_status` は成功しうるが **SendUserCascadeMessage** が失敗する、という切り分け。
- **原因1**: `urllib` の **既定 5s** がカスケード RPC（特に送信）のボディ待ちに不足。
- **原因2**: `TURN_STATES_DONE` に **空文字 `""`** が含まれ、**turnState 未設定**のまま「完了」とみなし、**応答本文なし**で `_parse_steps` が走っていた。

## Assessment（完了したこと）

1. **`antigravity_client.py`**  
   - `StartCascade` / `SendUserCascadeMessage` に **`rpc_http = max(30, timeout)`** を渡す。  
   - `_poll_response` の `GetAllCascadeTrajectories` / `GetCascadeTrajectorySteps` にも **`http_timeout`** を付与。

2. **`proto.py`**  
   - **`cascade_turn_complete()`** — 空 `turnState` では **本文が取れるか／終端 `stopReason`** があるまで完了にしない。  
   - **`extract_planner_response()`** — `finalResponse` / `content` / `assistantMessage` 等のフォールバック。  
   - **`TURN_STATES_DONE`** から **`""` を除去**（明示終端のみ）。

3. **`openai_compat_server.py` / `service.py`**（先行セッション側）  
   - LS 経路の非同期化、`system_instruction` のマージ等。

4. **検証**  
   - **SSH hgk** → `127.0.0.1:8766` → `model: "[LS]:Claude Opus 4.6"` → **HTTP 200**、指示どおりの **assistant 本文**（例: `pong` / `LS-Claude-OK`）。

## Recommendation（Next Actions）

- **トークン**: デバッグで `systemctl show` 等にトークンが出たことがあるなら **ローテーション**を検討。
- **ローカルテスト**: `mekhane/ochema/tests/test_model_fallback.py` が **10 件失敗**していた（asyncio マーク等）。今回の変更直結かは未確認。必要なら **venv + pytest-asyncio** で切り分け。
- **他ホスト**: 「hgk で動いた」＝ **そのマシンで LS が生きている**前提。別環境は同じとは限らない。

---

## 変更ファイル（本テーマ）

| ファイル | 内容 |
|----------|------|
| `20_機構｜Mekhane/_src｜ソースコード/mekhane/ochema/proto.py` | `cascade_turn_complete`, 応答抽出拡張, `TURN_STATES_DONE` |
| `20_機構｜Mekhane/_src｜ソースコード/mekhane/ochema/antigravity_client.py` | RPC/poll タイムアウト、ストリーム完了条件 |
| （関連）`mekhane/ochema/openai_compat_server.py`, `service.py` | LS パス非同期・system マージ |

## Git

- **latest_commit（参照時点）**: `970b095fc`（リポジトリ全体は大量のローカル変更あり）
- **branch**: master

---

## Value Pitch（なんのためか）

**「ブリッジは生きているのに本文が空／502」**を、**壁時計（タイムアウト数字）だけで誤魔化さず**、**LS の実際の RPC・ポーリング契約**に合わせて直した。次回 `/boot` で「hgk の Claude はここを叩け」と **再現可能な経路**が残る。

---

## Session Metrics（目安）

- **WF / スキル**: 調査・実装・SSH E2E・Handoff
- **テスト**: `test_service.py` + `test_openai_compat_server.py` 系は **28 passed**（当該実行時）

---

## Pinakas

Remaining: 本セッションでは Pinakas 差分なし
