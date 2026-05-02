# 17_協調｜Synergeia — マルチエージェント協調 CCL 実行

> **_src 対応**: `_src/synergeia/` (Python + n8n)
> **詳細 README**: [`_src/synergeia/README.md`](../../_src｜ソースコード/synergeia/README.md)

---

## 概要

単一 AI の限界を超えるため、CCL 式を複数スレッドに分散実行する。

```
CCL 式 → bridge.py → n8n WF → Thread分散 (Ochēma/Jules/Perplexity/Hermēneus) → Merge → Response
```

## スレッド

| スレッド | CCL | バックエンド |
|:---------|:----|:------------|
| Ochēma | `/noe`, `/dia`, `/bou`, `/zet`, `/u` | Ochēma MCP → LLM |
| Jules | `/s`, `/mek`, `/ene`, `/pra` | Jules MCP → Gemini |
| Perplexity | `/sop` | Perplexity API |
| Hermēneus | default | Hermēneus MCP → LMQL |

## 関連ドキュメント

| ドキュメント | 在処 | 状態 |
|:------------|:-----|:-----|
| Synergeia README | `_src/synergeia/README.md` | 🟢 |
| Architecture | `_src/synergeia/architecture.md` | 🟢 |
| Threads | `_src/synergeia/threads.md` | 🟢 |

## 依存関係

```
synergeia/ (マルチエージェント協調)
  ├── n8n              → WF オーケストレーション
  ├── ochema MCP       → LLM ブリッジ
  ├── jules MCP        → 並列コード生成
  └── hermeneus MCP    → CCL パーサー
```

---

*Synergeia Docs v1.0 — 2026-03-13*
