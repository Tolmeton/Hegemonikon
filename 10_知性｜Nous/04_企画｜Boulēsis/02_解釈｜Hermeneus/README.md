# 02_解釈｜Hermeneus

> **PURPOSE**: CCL パーサー・WF 実行エンジン (Hermēneus) の設計・実装計画を管理する。

## SCOPE

本ディレクトリは Hermēneus MCP サーバーの開発ロードマップと各フェーズの設計書を格納する。

| ファイル | フェーズ | 内容 |
|:---------|:---------|:-----|
| `mek_hermeneus_ccl.md` | Phase 1 | CCL パーサー基盤 |
| `mek_phase2_lmql_runtime.md` | Phase 2 | LMQL ランタイム統合 |
| `mek_phase3_langgraph.md` | Phase 3 | LangGraph WF 実行エンジン |
| `mek_phase4_verification.md` | Phase 4a | 検証フレームワーク |
| `mek_phase4b_prover.md` | Phase 4b | 証明器 |
| `phase4_dspy_optimizer.md` | Phase 4-DSPy | DSPy 最適化器 |
| `mek_phase5_production.md` | Phase 5 | プロダクション化 |
| `mek_phase6_executor.md` | Phase 6 | WorkflowExecutor |
| `mek_phase7_mcp.md` | Phase 7 | MCP サーバー化 |
| `mek_hermeneus_integration_test.md` | テスト | 統合テスト計画 |

## MAP

### 実装コード
- [20_機構｜Mekhane/_src/hermeneus/](../../../20_機構｜Mekhane/_src/hermeneus/) — Python 実装本体
- [20_機構｜Mekhane/02_解釈｜Hermeneus/](../../../20_機構｜Mekhane/02_解釈｜Hermeneus/) — モジュールドキュメント

### KI (Knowledge Items)
- `cognitive_algebra` — CCL 代数 (ccl_algebra)
- `mcp_server_ecosystem` — MCP サーバーエコシステム
- `system_architecture` — ワークフローディレクトリ構造

### Handoff
- [handoff_20260210_hermeneus_pipeline](../../../30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff/archive/2026-02/handoff_20260210_hermeneus_pipeline.md)

### Artifact
- [tak_hermeneus_roadmap_20260131](../../../30_記憶｜Mneme/01_記録｜Records/d_成果物｜artifacts/tak_hermeneus_roadmap_20260131.md) — 初期ロードマップ

### Session
- `2026-02-01 Hermeneus Development Planning`
- `2026-02-01 Hermeneus LLM Execution Test`
- `2026-02-10 Hermeneus MCP`
- `2026-03-01 Hermeneus Health Check`
- `2026-03-01 Hermeneus Macro Resolution Fix`

### 関連 PJ
- [01_意味論｜Semantikē](../16_CCL｜CCL/01_意味論｜Semantikē/) — CCL 演算子の圏論的意味論 (旧 01_美論｜Kalon)
- [10_統合｜GWSIntegration](../10_統合｜GWSIntegration/) — GWS MCP + CCL マクロ

## STATUS

- **現状**: Phase 7 (MCP サーバー化) 完了済み。hermeneus_run / hermeneus_dispatch が稼働中
- **未踏**: Phase 4b (証明器) の深化、DSPy 最適化器の実装

---
*Created: 2026-03-13*
