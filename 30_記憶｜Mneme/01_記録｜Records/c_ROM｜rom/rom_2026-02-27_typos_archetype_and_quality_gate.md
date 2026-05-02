---
rom_id: rom_2026-02-27_typos_archetype_and_quality_gate
session_id: 9b36d431-c977-4d2b-8a39-93f09d2f278e
created_at: 2026-02-27 09:36
rom_type: snapshot
---
# W1 Týpos アーキタイプ + W2 二段品質ゲート

W1: Týpos に model_archetypes.yaml を追加し compile() でモデル別変換 (Gemini/Claude/OpenAI) を実装。E2E 全通過。
W2: Dendron EPT → LLM の二段品質ゲートを実装。当初 /dia に配置したが Creator 指摘により /ele.diag に移設 — `/ele >> /dia` の合成パターンとして正しく配置した。
run_basanos_review.py に `run_dendron_precheck()` + `--skip-dendron` を追加。fail-fast 条件は PROOF 欠損のみ (PURPOSE は WARNING)。

## 決定事項

- [DECISION] model_archetypes.yaml で archetype パラメータを管理 (コード外に設定分離)
- [DECISION] Claude: contract-style → XML `<rules>` 変換 / OpenAI: JSON format hint
- [DECISION] 問題検知 (Dendron EPT) は /ele.diag の管轄。/dia は参照のみ (`/ele >> /dia`)
- [DECISION] fail-fast 条件: PROOF 欠損 = FAIL / PURPOSE 欠損 = WARNING (ディレクトリ全体スキャンでは厳しすぎるため)

## 次回アクション

- W3: Token Vault エネルギー予算管理 (Nucleus 式 Budget Proxy)
- W4: Ochema Tool Search (遅延ロード — Context Rot 根本対処)
- W5: Sympatheia MCP 監査ログ (MCPShield 式プロキシ)
