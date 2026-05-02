# 07_試金石｜Basanos

> **PURPOSE**: L0 静的解析スキャナー。AST パースによるコード品質検査。

## `_src/` 対応コード
- [`mekhane/basanos/`](../../_src｜ソースコード/mekhane/basanos/) — Basanos 実装

## 機能
- `sympatheia_basanos_scan` — Python ファイルの AST 解析 (Sympatheia 経由で呼出)

## 検出項目
- 未使用インポート
- 複雑すぎる関数 (cyclomatic complexity)
- セキュリティリスクパターン
- PROOF ヘッダー欠落 (Dendron 連携)

---
*Created: 2026-03-13*
