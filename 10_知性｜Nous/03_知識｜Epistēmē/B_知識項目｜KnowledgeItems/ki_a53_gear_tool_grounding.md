# A5.3: GEAR 的 SLM による Tool Grounding — HGK 翻訳メモ

> **出典**: EACL 2024 GEAR (Generalizable and Efficient tool Resolution)
> **パプくんレポート**: A5.3
> **ステータス**: 設計メモ (KI) — 未実装

---

## 原提言の要旨

- 大規模 LLM の手前に小型 LLM (SLM) を置き、query-tool grounding（どのツールを使うべきかのマッピング）を SLM に任せる。
- SLM がツール候補の grounding を行い、LLM に渡すことで、ツール選択ミスを減らす。

## HGK における既存対応

HGK の **Taxis classifier** (`mekhane/taxis/`) が既に部分的にこの役割を担っている:

- `task_classifier.py`: タスクの種別を分類
- `morphism_proposer.py`: 射（ワークフロー遷移）を提案

## 差分: 未実装部分

GEAR が追加で提案するのは **ツール選択の grounding** — つまり「この入力に対して、どの MCP ツールを呼ぶべきか」の判定を Taxis に追加すること。

具体的には:

1. Taxis に `tool_router.py` を新設
2. CCL 式をパースした AST から、必要な MCP ツール群を静的に列挙
3. LLM に渡す前にツール候補をフィルタ → コンテキスト圧縮
