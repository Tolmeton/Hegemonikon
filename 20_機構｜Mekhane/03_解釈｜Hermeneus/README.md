# 03_解釈｜Hermeneus

> **PURPOSE**: CCL パーサー・WF 実行エンジン。認知制御言語 (CCL) を解析し、ワークフローをアトミックに実行する。

## `_src/` 対応コード
- [`hermeneus/`](../../_src｜ソースコード/hermeneus/) — 独立パッケージ (README 5KB, docs/, tests/)
- [`mekhane/ccl/`](../../_src｜ソースコード/mekhane/ccl/) — CCL 関連ユーティリティ

## 機能
- `hermeneus_dispatch` — CCL 式を AST に解析
- `hermeneus_run` — 解析+実行アトミック (dispatch + execute)
- `hermeneus_execute` — WF 実行
- `hermeneus_compile` — CCL → LMQL コンパイル
- `hermeneus_list_workflows` — 利用可能 WF 一覧

## MAP
- [Boulēsis/02_解釈](../../10_知性｜Nous/04_企画｜Boulēsis/02_解釈｜Hermeneus/) — **Phase 1-7 設計書** (10ファイル)
- [Boulēsis/01_美論](../../10_知性｜Nous/04_企画｜Boulēsis/01_美論｜Kalon/) — CCL 演算子の圏論的意味論
- KI: `cognitive_algebra` → ccl_algebra

---
*Created: 2026-03-13*
