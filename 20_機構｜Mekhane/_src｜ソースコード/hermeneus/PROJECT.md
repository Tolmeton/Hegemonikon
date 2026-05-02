---
name: "Hermēneus"
status: active
phase: "Phase 8: Precision-Aware Routing"
updated: 2026-03-15
next_action: "gemini-embedding-001 移行後の閾値再計算"
---

# Hermēneus Project Status

> CCL 実行保証コンパイラ — 認知制御言語を解析・実行・検証する統合エンジン

## Current Phase

**Phase 8: Precision-Aware Routing** — bge-m3 浅層↔深層分析による実行戦略の動的決定

## Milestones

- [x] Phase 1: パーサー実装
- [x] Phase 2: ランタイム実装
- [x] Phase 3: LangGraph 状態管理
- [x] Phase 4: Multi-Agent Debate + Audit
- [x] Phase 5: CLI + Production
- [x] Phase 6: Workflow Executor + Synergeia
- [x] Phase 7: MCP Server (AI 自己統合)
- [x] Phase 8: Precision-Aware Routing (Consumer 実装完了)

## Active Work

### Precision-Aware Routing (Activity 3)

- [x] `precision_router.py` — bge-m3 浅層↔深層 cos sim → ExecutionStrategy
- [x] `dispatch.py` — precision_strategy を result に含める
- [x] `mcp_server.py` — Consumer: search_budget/gnosis_search で検索制御
- [ ] 閾値再検証 (n=13 → n≥30)
- [ ] gemini-embedding-001 移行後の閾値再計算
- [ ] ドキュメント: PROOF.md に Precision Routing の公理対応追記

### CCL-IR (中間表現)

- [x] `ccl_ir.py` — CCLIR / CCLIRNode データ構造
- [ ] Embedding Futamura Projection 統合
- [ ] IR 最適化パス

## Next Steps

1. gemini-embedding-001 移行: bge-m3 → Gemini Embedding
2. 閾値の統計的再検証: n≥30 セッションでの Q1/Q3 再計算
3. CCL-IR 最適化パスの実装
