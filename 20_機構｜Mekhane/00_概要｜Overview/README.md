# 00_概要｜Overview

> **PURPOSE**: Mekhane 全体のアーキテクチャ概要とモジュール一覧。

## モジュール ↔ `_src/` 対応表

| # | モジュール | `_src/` パッケージ | 説明 |
|:--|:----------|:------------------|:-----|
| 00 | 概要 Overview | — | 本ディレクトリ (全体俯瞰) |
| 01 | MCP | `mekhane/mcp/` | MCP サーバー基盤 |
| 02 | 車体 Ochema | `mekhane/ochema/` | LLM ブリッジ (Language Server) |
| 03 | 解釈 Hermeneus | `hermeneus/` | CCL パーサー・WF 実行エンジン |
| 04 | 共感 Sympatheia | `mekhane/sympatheia/` | 自律神経系 (WBC, Attractor, Digest) |
| 05 | 樹 Dendron | `mekhane/dendron/` | 存在証明チェッカー |
| 06 | 観察 Periskope | `mekhane/periskope/` | Deep Research エンジン |
| 07 | 試金石 Basanos | `mekhane/basanos/` | L0 静的解析 |
| 08 | 最適化 Aristos | `mekhane/fep/` | FEP エンジン・最適化 |
| 09 | 編組 Symploke | `mekhane/symploke/` | ワーカー協調 |
| 10 | 想起 Anamnesis | `mekhane/anamnesis/` | 知識検索 (Gnōsis/Sophia/Kairos) |
| 11 | 完遂 Synteleia | `mekhane/synteleia/` | タスク完遂エンジン |
| 12 | 制作 Poiema | `mekhane/poiema/` | 成果物生成 |
| 13 | FEP | `mekhane/fep/` | Free Energy Principle エンジン |
| 14 | 分類 Taxis | `mekhane/taxis/` | 射の提案・分類 |
| — | A_docs | — | 設計ドキュメント集 |

## 独立パッケージ

| パッケージ | 説明 |
|:----------|:-----|
| `hermeneus/` | CCL パーサー・WF エンジン (独立リポジトリ構造) |
| `hgk/` | HGK デスクトップアプリ (Tauri + Vite) |
| `synergeia/` | Jules ブリッジ + 外部 AI 連携 |
| `pepsis/` | テンプレートエンジン (Rust + Python) |
| `openclaw/` | 外部 OSS フォーク (OpenClaw) |

## MAP

### Kernel
- [axiom_hierarchy.md](../../00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md) — 座標系と動詞の定義

### 関連 Boulēsis PJ
- [02_解釈｜Hermeneus](../../10_知性｜Nous/04_企画｜Boulēsis/02_解釈｜Hermeneus/) — Hermeneus 設計書
- [04_随伴｜OssAdjoint](../../10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/) — OSS 随伴戦略
- [05_自律｜Autophonos](../../10_知性｜Nous/04_企画｜Boulēsis/05_自律｜Autophonos/) — 自律エージェント
- [09_能動｜Ergon](../../10_知性｜Nous/04_企画｜Boulēsis/09_能動｜Ergon/) — 能動層設計

---
*Created: 2026-03-13*
