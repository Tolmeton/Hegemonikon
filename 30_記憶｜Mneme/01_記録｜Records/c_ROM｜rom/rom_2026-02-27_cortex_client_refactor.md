---
rom_id: rom_2026-02-27_cortex_client_refactor
session_id: 0262af21-6c75-484a-8adb-3f50bf8b710b
created_at: 2026-02-27 16:12
rom_type: rag_optimized
reliability: High
topics: [ochema, cortex_client, refactor, composition, auth, delegation]
exec_summary: |
  cortex_client.py (1,973行/78KB) を委譲パターンで分割中。
  Step 1 (cortex_auth.py 抽出) 完了。Step 2-4 が残。
  設計: Mixin → 委譲に /ele+ で変更。全192テスト PASS。
---

# cortex_client.py リファクタリング {#sec_01_main}

> **[DECISION]** cortex_client.py を 5モジュールに分割する。Mixin ではなく **委譲 (Composition)** パターンを採用。 {#sec_02_decision}

> **[FACT]** cortex_client.py は 1,973行 / 78KB。CortexClient クラスに7つの責任が混在する God Object。 {#sec_03_problem}

> **[DISCOVERY]** /ele+ 検証で Mixin パターンの問題を検出: `_call_api` は7箇所、`_get_token` は10箇所から呼ばれ密結合。Mixin は暗黙の self.* 共有に依存し依存方向が不可視。 {#sec_04_discovery}

## 分割計画 {#sec_05_plan}

| # | ファイル | 責任 | 行数 | 状態 |
|:--|:---------|:-----|:-----|:-----|
| Step 1 | `cortex_auth.py` | 認証 (トークン取得・キャッシュ・リフレッシュ) | 245 | ✅ 完了 |
| Step 2 | `cortex_api.py` | API通信基盤 (`_call_api`, `_build_request`, `_get_project`) | ~190 | ⬜ |
| Step 3 | `cortex_chat.py` | generateChat + ChatConversation | ~330 | ⬜ |
| Step 4 | `cortex_tools.py` | ask_with_tools (Function Calling) | ~180 | ⬜ |

> **[RULE]** CortexClient はファサードとして残す。外部 import (`from mekhane.ochema.cortex_client import CortexClient`) は変更しない。21ファイルの後方互換を維持。 {#sec_06_rule}

## Step 1 の実装詳細 {#sec_07_step1}

> **[FACT]** コミット `bae6b008e`: 3 files changed, 356 insertions(+), 253 deletions(-) {#sec_08_commit}

**委譲パターン**:

```python
class CortexClient:
    def __init__(self, ...):
        self._auth = CortexAuth(account=account)
        self._auth._on_token_change = self._invalidate_project_cache
    
    def _get_token(self) -> str:
        return self._auth.get_token()  # 委譲

    @property
    def vault(self) -> TokenVault:
        return self._auth.vault  # 委譲
```

> **[DECISION]** `self._token = None` (リトライ時) は `self._auth._token = None` に変更。3箇所修正済み。 {#sec_09_token_clear}

> **[FACT]** test_token_fallback.py のモック対象を `CortexClient._get_ls_token` → `CortexAuth._get_ls_token` に更新。 {#sec_10_test}

## Step 2-4 の実装方針 {#sec_11_next}

> **[RULE]** 各ステップ後に CI (`run_ochema_ci.sh`) を実行し、192テスト PASS を確認する。 {#sec_12_ci}

**Step 2 (`cortex_api.py`)**: `_call_api`, `_build_request`, `_parse_response`, `_get_project` を `CortexAPI` クラスに抽出。`CortexClient.__init__` で `self._api = CortexAPI(self._auth)` として初期化。

**Step 3 (`cortex_chat.py`)**: `chat`, `chat_stream`, `start_chat`, `_parse_chat_response`, `ChatConversation` を抽出。API 層に依存。

**Step 4 (`cortex_tools.py`)**: `ask_with_tools` を抽出。API 層に依存。

## 外部依存ファイル (21件) {#sec_13_deps}

```
ochema/: service.py, hgk_dev.py, session_notes.py, __init__.py, テスト4件
basanos/: hom.py, g_semantic.py
periskope/: engine.py, synthesizer.py, url_auditor.py, query_expander.py, llm_reranker.py
ergasterion/: deep_engine.py, sweep_engine.py, cortex_n8n_bridge.py
symploke/: run_cortex_reviews.py
api/: agent.py, cortex_ask.py
```

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "cortex_client.py の分割はどこまで進んだ？"
  - "委譲パターンの実装方法は？"
  - "Step 2-4 の残タスクは？"
  - "テストのモック先はどう変わった？"
answer_strategy: "Step 完了状態テーブルを参照し、各ステップの実装方法はコードブロックを確認"
confidence_notes: "Step 1 は SOURCE (コミット bae6b008e, CI 192 PASS)。Step 2-4 は計画段階。"
related_roms: []
-->
