---
rom_id: rom_2026-02-14_bou_jules_kb_bridge
session_id: e46afc77-0f4d-49af-980f-e978cdd80da8
created_at: 2026-02-14 17:55
rom_type: distilled
reliability: High
topics: [jules, kb-bridge, bou, context-hub, gateway, cli, agents-md, plan-b, plan-a]
exec_summary: |
  Jules KB Bridge の @plan→@build 完了。/chr で hgk_gateway.py (1,845行) が既存と判明。
  Plan B (context/ 知識ハブ化) + Plan A (hegemonikon-kb CLI) を実装・検証済み。
  プロンプトサイズ 7,492→9,757 chars。AGENTS.md v5→v6。
---

# Jules KB Bridge — /bou 意志から実装まで

> **[DECISION]** Plan B (context/) + Plan A (CLI) の段階的アプローチを採択

Jules が HGK 知識基盤に自律アクセスできる状態を目指し、
3つの Plan から B+A を選択した。

- **Plan A**: hegemonikon-kb CLI → 既存 hgk_gateway.py に HTTP で問合せ
- **Plan B**: context/ に Sophia/Gnosis 自動生成 .md → プロンプト注入 ⭐推奨・先行
- **Plan C**: Gateway 公開 (ngrok/CF Tunnel) → セキュリティリスクで後回し

---

> **[DISCOVERY]** hgk_gateway.py (1,845行) は既に実装済み

`/chr` (資源確認) で発見。OAuth 2.1 + FastMCP + Streamable HTTP、
27ツール定義済み、gateway_policy.yaml によるセキュリティ管理。
「中期」と想定していた HTTP Gateway が既存資産だった。

### 既存資産一覧

| 資産 | パス | 状態 |
|:-----|:-----|:-----|
| HGK Gateway | mekhane/mcp/hgk_gateway.py (1,845行) | 完成済 |
| Jules MCP Server | mekhane/mcp/jules_mcp_server.py (406行) | 完成済 |
| Gateway Policy | mekhane/mcp/gateway_policy.yaml (148行) | 完成済 |
| Ochema MCP | mekhane/mcp/ochema_mcp_server.py | 完成済 |
| テスト | test_gateway_functional.py, test_gateway_security.py | 存在 |

---

> **[DECISION]** 実装成果物 (本セッション)

| ファイル | 種別 | 内容 |
|:---------|:-----|:-----|
| scripts/generate_jules_context.py | NEW | 4テーマ自動生成 (fep/design/ccl/qa) |
| scripts/hegemonikon-kb | NEW | Gateway HTTP CLI (search/status/paper/ccl) |
| AGENTS.md | MOD→v6 | KB CLI + context/ セクション追加 |
| context/{fep_foundation,design_patterns,ccl_language,quality_assurance}.md | NEW | テーマ別ドメイン知識 |

### 検証結果

- テスト: 9/9 通過 (test_generate_prompt.py)
- プロンプトサイズ: 7,492→9,757 chars (+30%)
- FEP 参照数: ~5→21

---

> **[CONTEXT]** /bou 方向性との接続

`bou_pipeline_direction_2026-02-14.md` による最新の意志:

- $goal = Jules Pipeline を本番稼働可能にする
- $constraints = 全キー枯渇中 (2/15 リセット待ち)
- 内向き×外向き補完を維持

KB Bridge は Pipeline 本番稼働の前提条件（レビュー品質向上）に位置する。

---

> **[CONTEXT]** 残タスク

| タスク | 条件 | 優先度 |
|:-------|:-----|:-------|
| Jules setup script 対応 | Gateway 公開方法決定後 | 低 |
| context/ テーマ追加 | 必要に応じて | 中 |
| knowledge 検索結果の品質向上 | CLI の --format json 対応後 | 中 |
| Plan C (Gateway 公開) | セキュリティ設計完了後 | 後回し |

## 関連情報

- 関連 WF: /bou, @plan, @build
- 関連 Session: e46afc77 (Jules Context Enhancement), 047300ae (前セッション)
- 関連 KI: jules_kb_bridge, hgk_gateway

<!-- ROM_GUIDE
primary_use: Jules KB Bridge の設計決定と実装結果の参照
retrieval_keywords: jules knowledge base bridge gateway cli context hub agents.md
expiry: permanent
-->
