# 20_機構｜Mekhane — 実行基盤 (a: 行為)

> **POMDP 変数**: a (action) — 方策 π を実行する行為そのもの。
> Nous が「何をすべきか (π)」を定義し、Mekhane が「実際にやる (a)」。

---

## 構造: docs ↔ _src 1:1 対応

```
20_機構｜Mekhane/
│
│  【ドキュメント帯 — 設計・仕様・運用ガイド】
├── 00_概要｜Overview/         # 横断: アーキテクチャ全体図
├── 01_MCP｜MCP/               # → mekhane/mcp/
├── 02_車体｜Ochema/           # → mekhane/ochema/
├── 03_解釈｜Hermeneus/        # → hermeneus/
├── 04_共感｜Sympatheia/       # → mekhane/sympatheia/
├── 05_樹｜Dendron/            # → mekhane/dendron/
├── 06_観察｜Periskope/        # → mekhane/periskope/
├── 07_試金石｜Basanos/        # → mekhane/basanos/
├── 08_最適化｜Aristos/        # → (未実装)
├── 09_編組｜Symploke/         # → mekhane/symploke/
├── 10_想起｜Anamnesis/        # → mekhane/anamnesis/
├── 11_完遂｜Synteleia/        # → mekhane/synteleia/
├── 12_制作｜Poiema/           # → mekhane/poiema/
├── 13_FEP｜FEP/               # → mekhane/fep/
├── 14_分類｜Taxis/            # → mekhane/taxis/
├── 15_HGK｜HGK/              # → hgk/ (Tauri デスクトップ)
├── 16_消化｜Pepsis/           # → pepsis/ (設計哲学消化)
├── 17_協調｜Synergeia/       # → synergeia/ (マルチエージェント)
│
│  【コード帯 — Python パッケージ実体】
└── _src｜ソースコード/
    ├── mekhane/               # コアパッケージ (27 submodule)
    ├── hermeneus/             # CCL コンパイラ
    ├── hgk/                   # Tauri デスクトップアプリ → 15_HGK
    ├── pepsis/                # 消化パイプライン → 16_消化
    ├── synergeia/             # マルチエージェント → 17_協調
    ├── openclaw/              # 外部 OSS フォーク (doc未対応)
    └── tests/                 # テスト
```

## POMDP マッピング

| 帯 | POMDP | 役割 |
|:---|:------|:-----|
| docs (00-17) | P(o\|s) ドキュメント | 実装の「読み方」— コードが何を意味するか |
| _src/mekhane/ | a (行為) コア | 認知機構の実装 (27 submodule) |
| _src/hermeneus/ | a (行為) CCL | CCL パーサー・WF エンジン |
| _src/hgk/ | a (行為) UI | HGK デスクトップアプリ |
| _src/tests/ | V(a) 検証 | 行為の結果を検証 |

## 未対応の対称性 (検出された不一致)

| _src パッケージ | 対応 docs | 状態 |
|:---------------|:----------|:-----|
| hgk/ | 15_HGK | 🟡 ポータル README 作成済み (詳細は _src/hgk/README.md) |
| pepsis/ | 16_消化 | 🟡 ポータル README 作成済み (詳細は _src/pepsis/README.md) |
| synergeia/ | 17_協調 | 🟡 ポータル README 作成済み |
| openclaw/ | なし | 🟢 外部 OSS フォーク — docs 不要 |

---

*Mekhane POMDP Classification v2.0 — 2026-03-13*
