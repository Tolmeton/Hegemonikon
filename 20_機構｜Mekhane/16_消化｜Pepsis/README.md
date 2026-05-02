# 16_消化｜Pepsis — 設計哲学消化フレームワーク

> **_src 対応**: `_src/pepsis/` (Python + Rust)
> **詳細 README**: [`_src/pepsis/README.md`](../../_src｜ソースコード/pepsis/README.md)
> **プロジェクト定義**: [`_src/pepsis/PROJECT.md`](../../_src｜ソースコード/pepsis/PROJECT.md)

---

## 概要

**Πέψις** (pepsis) = 消化。外部の設計哲学を模倣ではなく、
FEP に基づいて第一原理に分解 (G) し、HGK の構造として自由構成 (F) する。

- `/eat` が動詞 (行為) → Pepsis は名詞 (場所・体系)
- Digestor MCP が論文を**取得**、Pepsis が設計哲学を**消化**

## 消化テンプレート (T1-T4)

| Template | 名称 | 用途 |
|:---------|:-----|:-----|
| T1 | 対応表 (Mapping) | 構造保存写像 |
| T2 | 哲学抽出 (Extraction) | 格言・原則の吸収 |
| T3 | 機能消化 (Absorption) | WF/マクロ/演算子の生成 |
| T4 | 概念輸入 (Import) | kernel 構造の拡張 |

## 消化状態

| 対象 | Phase | 状態 | 成果物数 |
|:-----|:------|:-----|:---------|
| **Python** | Phase 5/5 | ✅ 完食 (骨髄まで) | designs 5件 + macros + mappings |
| **Rust** | Phase 1 | 🟡 開始 | designs 17件 + mappings |

## 関連ドキュメント

| ドキュメント | 在処 | 状態 |
|:------------|:-----|:-----|
| Pepsis README | `_src/pepsis/README.md` | 🟢 最新 |
| Pepsis PROJECT | `_src/pepsis/PROJECT.md` | 🟢 プロジェクト定義 |
| ロードマップ | `_src/pepsis/roadmap.md` | 🟢 |
| 備えマトリックス | `_src/pepsis/sonae.md` | 🟢 |
| 消化テンプレート | `_src/pepsis/templates/` | 🟢 |
| Digestor MCP | (MCP server) | 🟢 論文取得側 |

## 依存関係

```
pepsis/ (消化フレームワーク)
  ├── /eat WF          → 消化の動詞 (行為トリガー)
  ├── /fit WF          → 消化品質検証
  ├── digestor MCP     → 論文・外部コンテンツの取得
  └── kernel/          → 消化結果の帰着先 (T4)
```

---

*Pepsis Docs v1.0 — 2026-03-13*
