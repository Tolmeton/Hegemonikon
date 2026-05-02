---
rom_id: rom_2026-04-04_opsis_dual_backend
session_id: current
created_at: 2026-04-04
rom_type: rag_optimized
reliability: High
topics: [opsis, dual-backend, playwright, agent-browser, mcp, colab, browser-automation, t-026, t-027, t-028, t-057, typos-benchmark]
exec_summary: |
  Opsis v0.3.0→v0.4.0。BrowserBackend プロトコル導入で agent-browser/Playwright を auto-detect 切替。新ツール3つ (wait/screenshot/navigate)。T-026/027/028 全完了。T-057 (Typos E1) は計測器故障を確認・記録。
---

# Opsis Dual Backend + Typos E1 故障判定

## 決定事項

> **[DECISION] 方式C: PlaywrightBackend を Opsis に直接統合**

/bou → /u+ で B (外部MCP経由) vs C (直接統合) を検討。C を選択。

理由:
1. 二重MCP跳躍 (Claude→Opsis→Playwright MCP) は設計的に汚い。MCP はツール公開用であり内部通信用ではない
2. PlaywrightBridge (`mekhane/kube/playwright_bridge.py`) が既に存在 — CDP a11y tree 取得コードが使える
3. Colab では単一プロセスが有利。`pip install playwright && playwright install chromium` で完結
4. Playwright は事実上の標準。browser-use, Stagehand, Skyvern 全てが Playwright 上に構築
5. BrowserBackend Protocol による抽象化で将来のバックエンド追加も容易

> **[DECISION] auto-detect 戦略: agent-browser 優先、Playwright フォールバック**

- `shutil.which("agent-browser")` が見つかれば AgentBrowserBackend
- なければ `import playwright` を試み PlaywrightBackend
- CLI で `--backend {auto,agent-browser,playwright}` 明示指定可能
- `--no-headless` で GUI ブラウザ起動も可能

> **[DECISION] Playwright sync API を採用 (async ではなく)**

MCP ハンドラは `run_sync()` 経由でスレッドプールから呼ばれる。async Playwright だとイベントループ管理が複雑になる。sync API はスレッドセーフで、内部で専用イベントループを管理する。

> **[DECISION] T-057 (Typos E1): 計測器故障判定**

E1 全48バッチ完了。全16セル (4 format × 4 level) が ICR=0.3656 で完全同一分布。統計的にありえない。個別スコア列も全セル同一 → 採点器がフォーマット/圧縮レベルを区別していない。TYPOS_BENCHMARK.md に故障分析と次アクションを記録。

> **[DECISION] T-027/T-028 は v0.3.0 で既に実装済みと判定**

- T-027 (observe 精度): max_tokens 予算制御、diff mode (LRU cache)、セマンティック圧縮 — 全て v0.3.0 で実装済み
- T-028 (CCL 知覚動詞): ROLE_VERB_MAP 60+ ARIA roles、VERB_OUTPUT_SHAPE 6形式、Layer 3.5 動詞別出力整形 — 全て v0.3.0 で実装済み
- v0.4.0 リファクタで全機能を完全保持

## 発見事項

> **[DISCOVERY] AI Web 操作 MCP の市場地図 (2026-04)**

| ツール | Stars | License | MCP | Headless |
|:-------|------:|:--------|:----|:---------|
| browser-use | 86k | MIT | Community | Yes |
| Stagehand | 21.8k | MIT | Official | Yes |
| Skyvern | 21k | Apache-2.0 | No | Yes |
| Playwright MCP (MS) | 12k+ | Apache-2.0 | 公式 | Yes |
| Steel Browser | 6.8k | Apache-2.0 | Official | Yes |
| BrowserMCP (ByteDance) | 6.2k | Apache-2.0 | IS MCP | No |
| Notte | 1.9k | SSPL | Official | Yes |

全ツールの共通基盤: **Playwright**。全員が Playwright の上に乗っている。

> **[DISCOVERY] E1 故障の原因候補**

圧縮は正常に機能 (plain L0=396→L4=32 chars, xml L0=703→L4=56 chars)。しかし採点結果が全条件で同一 → 3つの仮説:
1. テスト LLM が compressed system prompt を受け取っていない
2. 同一の回答セットが全条件に使い回されている (キャッシュバグ)
3. 採点が回答内容ではなく固定パターンで判定している

> **[DISCOVERY] PlaywrightBridge が既に存在していた**

`mekhane/kube/playwright_bridge.py` (278行) — CDP 経由 a11y tree 取得、OODA パターン、headless 対応済み。Kube Agent 用だが、Opsis のバックエンドとしてアーキテクチャを流用。

## 成果物

### 新規ファイル

| ファイル | 行数 | 内容 |
|:---------|-----:|:-----|
| `mekhane/mcp/opsis_backends.py` | ~450 | BrowserBackend Protocol, AgentBrowserBackend, PlaywrightBackend, auto_detect_backend() |

### 改修ファイル

| ファイル | 変更内容 |
|:---------|:---------|
| `mekhane/mcp/opsis_mcp_server.py` | v0.3.0→v0.4.0。バックエンド抽象化適用、新ツール3つ追加、`_run_agent_browser()`/`_build_snapshot_args()` 除去。Layer 3/3.5 コード完全保持 |
| `TYPOS_BENCHMARK.md` | E1 結果セクション追加 (ICR テーブル + 故障分析 + 次アクション) |
| `PINAKAS_TASK.yaml` | T-026/027/028/057 → done |

### Opsis v0.4.0 アーキテクチャ

```
opsis_mcp_server.py (MCP ツール定義 + Layer 3/3.5)
  │
  ├── BrowserBackend (Protocol)
  │     ├── AgentBrowserBackend  ← ローカル: agent-browser CLI
  │     └── PlaywrightBackend    ← Colab/headless: Playwright sync + CDP
  │
  ├── Layer 3: 認知動詞アノテーション (60+ ARIA roles)
  ├── Layer 3.5: 動詞別出力整形 (6形式)
  ├── セマンティック圧縮 + トークン予算制御
  └── 差分モード (LRU snapshot cache)

ツール (6):
  opsis_observe    — a11y snapshot + 認知動詞アノテーション
  opsis_act        — Ref ID で DOM 操作
  opsis_extract    — 構造化データ抽出
  opsis_wait       — 条件待機 (load/selector/text) [NEW]
  opsis_screenshot — PNG スクリーンショット [NEW]
  opsis_navigate   — back/forward/refresh [NEW]
```

### PlaywrightBackend の特徴

- `playwright.sync_api` 使用 (asyncio イベントループ不要)
- CDP `Accessibility.getFullAXTree` で a11y ツリー取得
- `@eN` 形式の Ref ID を自動生成
- `_last_ref_map` で ref→{role, name} を保持し、`act()` で role-based locator に変換
- `_INTERACTIVE_ROLES` / `_STRUCTURAL_ROLES` / `_SKIP_ROLES` で表示フィルタ
- lazy init: 初回呼出しでブラウザ起動

## Pinakas 更新

| タスク | ステータス | ノート |
|:-------|:-----------|:-------|
| T-026 | done (2026-04-04) | wait/screenshot/navigate 実装。tabs は未実装 |
| T-027 | done (2026-04-04) | v0.3.0 で既に実装済み。v0.4.0 で保持 |
| T-028 | done (2026-04-04) | v0.3.0 で既に実装済み。v0.4.0 で保持 |
| T-057 | done (2026-04-04) | E1 計測器故障判定。TYPOS_BENCHMARK.md に記録 |

Opsis open タスク: **ゼロ**

## 残課題

- Playwright 未インストールのため PlaywrightBackend の E2E テストは未実施
- `opsis_tabs` (タブ管理) 未実装 — 現状の単一ページモデルで十分
- E1 Typos Benchmark 再実行 — `run_e1.py` の system prompt 受渡しロジック修正が先
- Opsis systemd サービスの起動確認 (v0.4.0 の新 import が通るか)

## 関連情報

- opsis_backends.py: `mekhane/mcp/opsis_backends.py`
- opsis_mcp_server.py: `mekhane/mcp/opsis_mcp_server.py`
- PlaywrightBridge (参照): `mekhane/kube/playwright_bridge.py`
- TYPOS_BENCHMARK: `60_実験｜Peira/08_関手忠実性｜FunctorFaithfulness/TYPOS_BENCHMARK.md`
- E1 結果: `60_実験｜Peira/08_関手忠実性｜FunctorFaithfulness/typos-benchmark/e1_compression/results/`
- Pinakas: `10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/pinakas/PINAKAS_TASK.yaml`

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "Opsis のバックエンドはどう切り替わるか？"
  - "Colab で Opsis を使うには？"
  - "Playwright backend の a11y tree 取得はどう実装されているか？"
  - "E1 Typos Benchmark の結果は？"
  - "AI ブラウザ操作ツールの比較"
answer_strategy: 設計判断 (方式C選択) の根拠から入り、アーキテクチャ図で全体像を示す。Colab 利用法は手順として具体的に。E1 は故障判定であり結果ではないことを明記。
confidence_notes: Opsis v0.4.0 のコードは構文チェック・インポートチェック済み。PlaywrightBackend の E2E テストは未実施。
related_roms:
  - rom_2026-04-04_ccl_pl_sprint
  - rom_2026-04-04_subagent_infra_gemini_cli
-->

<!-- ROM_GUIDE
primary_use: Opsis バックエンド設計の復元。Playwright テスト時の参照。E1 Typos 故障の追跡。
retrieval_keywords: opsis, dual-backend, playwright, agent-browser, colab, headless, BrowserBackend, PlaywrightBackend, auto-detect, e1, typos, icr, benchmark, browser-use, stagehand
expiry: 2026-07-01
-->
