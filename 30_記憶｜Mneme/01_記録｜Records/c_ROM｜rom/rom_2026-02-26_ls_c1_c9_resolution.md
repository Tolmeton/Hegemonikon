---
rom_id: rom_2026-02-26_ls_c1_c9_resolution
session_id: 783a624a-39b2-4644-9143-353b5e610375
created_at: 2026-02-26 21:05
rom_type: distilled
reliability: High
topics: [non-standalone-ls, authentication, state.vscdb, headless, fallback]
exec_summary: |
  Non-Standalone LS を Ochema MCP 上に本番統合し、C1-C9の全矛盾を解消。
  最大の壁だった C9 (IDE不在時のトークン失効) を provision_state_db で解決した。
---

# Non-Standalone LS 統合と C1-C9 矛盾解消 {#sec_01_topic}

> **[DECISION]** Non-Standalone LS の認証情報は `state.vscdb` に直接逆注入する (AuthProvisioner)

Headless 環境で LS を起動すると、IDE による OAuth トークンの更新がないため最終的に失効し、推論（Cortex からのモデル取得）が失敗する (C9)。これを解決するため、`ls_manager.py` に `provision_state_db()` を実装した。TokenVault (gemini-cli で refresh されたもの) から最新トークンを取得し、`~/.config/Antigravity/User/globalStorage/state.vscdb` の `antigravityAuthStatus.apiKey` に JSON で書き戻す。

> **[DISCOVERY]** `state.vscdb` は LS 認証の単一障害点

LS プロセスは直接 `state.vscdb` を読んでいる。CortexClient も同様。これを SQLite で外部から更新すれば、IDE プロセスを一切起動することなく長期間の持続的な推論・並列推論が可能。

> **[DECISION]** OchemaService へ Strategy 1 (IDE) → Strategy 2 (Non-Standalone) の自動フォールバックを実装 (C1)

`service.py` (`_get_ls_client`) で、まず IDE LS 検出を試み、失敗した場合またはヘルスチェック (C4) で死亡している場合に、`NonStandaloneLSManager` へ自律的に切り替えるロジックを実装。プロセスリークを防ぐため `atexit` も追加した。

> **[DISCOVERY]** DummyExtServer の重要性 (C2, C4, C5, C6)

IDE の Extension Server なしでも LS は起動可能。`ext_server.py` に `DummyExtServer` (HTTP 200, 空プロトを返すだけ) を実装し、LS プロセスにこの DummyExtServer のポートと CSRF を伝えることで完全に自己完結したサイクルを構築。

> **[RULE]** Protobuf スキーマバージョンは固定 (C3)

`ide_version` は `package.json` から動的取得 (C7) できるようになったが、protobuf のスキーマ自体は実行時に動的パースすべきではない (`1.107.0` ベースで固定)。これは過剰エンジニアリングを避けるための意図的制約。

## 関連情報

- 関連 Skill: `antigravity-ide-expert`
- 関連 Session: 783a624a-39b2-4644-9143-353b5e610375
- 関連ファイル: `ls_manager.py`, `service.py`, `cortex_client.py`, `DX-010`

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "Headless で Antigravity LS が認証エラーになるのはなぜか？"
  - "NonStandaloneLSManager はどうやって認証を通しているか？"
  - "DummyExtServer の役割は何か？"
answer_strategy: "IDE なしで LS を動かすには、TokenVault から `state.vscdb` へのトークン逆注入と、DummyExtServer による疑似 Extension Server の2つが必要という構造を答える。"
confidence_notes: "C1-C9 はコードとして本番投入・実証済み (14/14 tests passed)。確信度は極めて高い。"
related_roms: []
-->
