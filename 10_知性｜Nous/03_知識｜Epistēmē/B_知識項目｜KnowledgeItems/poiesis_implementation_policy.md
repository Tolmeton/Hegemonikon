---
title: Poiesis 実装方針 — LLM 実行は意図的設計
created: 2026-03-12
status: 確定
tags: [poiesis, 実装方針, 設計判断, FEP]
related:
  - "[[axiom_hierarchy]]"
  - "[[system_manifest]]"
  - "[[rom_2026-02-21_poiesis_dokimasia]]"
  - "[[ele_report_system_elements]]"
---

# Poiesis 実装方針 — LLM 実行は意図的設計

## 結論

**Poiesis (24動詞) の実行は「WF 定義 (.md) を LLM が読んで実行する」方式が正系統 (canonical) である。これは技術的負債ではなく意図的設計。**

## 根拠

### 1. 三層の構造が異なる役割を持つ

| 層 | 役割 | 場所 | 内容 |
|---|---|---|---|
| **理論** | 定義 | `kernel/axiom_hierarchy.md` L249+ | 24 = Flow × 6修飾座標 × 4極 |
| **WF定義** | 実行手順 | `B_WFModules/A_Poiesis/03_生成｜Poiesis/` | 6族 × 4動詞 = 24 `.md` ファイル完備 |
| **コード** | 成果物監査 | `mekhane/synteleia/poiesis/` | 3エージェント (Ousia/Schema/Horme) |

- コード層の3エージェントは「テキストの曖昧表現検出・定義有無チェック」等の **監査** 機能
- 24動詞の「実行」とは関係がない — `ousia_agent.py` は正規表現による品質チェッカー
- `ele_report` の矛盾指摘は、`synteleia/poiesis/` (監査コード) と理論上の Poiesis (24動詞) を混同したことに起因

### 2. FEP 的根拠: 認知的柔軟性の保全

コード化は Exploit (固定化) 。動詞のコード化は以下を犠牲にする:

- **WF 定義の変更ごとにコード変更が必要になる** — 認知操作の定義は進化する
- **LLM の解釈余地 (Explore) がなくなる** — `/noe` の実行は文脈依存であるべき
- **24個全ての決定論的コード化は非現実的** — 各動詞は認知操作であり、アルゴリズムではない

FEP において: Function 座標 (Explore ↔ Exploit) の最適点は **完全なコード化 (Exploit 極) ではなく、WF定義 (構造) + LLM (柔軟性) のハイブリッド**。

### 3. ROM #4 (2026-02-21) で確定済み

> Poiesis = 独立 WF として実装  
> Dokimasia = WF の実行パラメータとして実装

この「独立 WF」は `.md` ファイルを指す。Python コードを指してはいない。

## `synteleia/poiesis/` の正体

| ファイル | 実際の機能 | 理論上の Poiesis との関係 |
|---|---|---|
| `ousia_agent.py` | 曖昧表現・未定義用語の検出 | 間接的 — O1 Noēsis の「本質の明確さ」を監査 |
| `schema_agent.py` | 構造設計の品質チェック | 間接的 — 構造の整合性を検証 |
| `horme_agent.py` | 動機・目的の明確さ検証 | 間接的 — 意志の明確さを監査 |

→ 旧体系の O/S/H (3視点) に由来する監査機能。24動詞=Poiesis の実行層ではない。

## 命名混乱への対処

> [!WARNING]
> `synteleia/poiesis/` という名前は、理論層の Poiesis (24動詞の生成層) と紛らわしい。
> これは `synteleia/audit_agents/` のような名前がより適切だが、リネームは破壊的変更であり本 KI のスコープ外。

## 具体例 (N-11: 抽象1+具体3)

1. **`/noe` (認識)**: noe.md を読み、Phase 0-6 を LLM が文脈に応じて実行。コードでは Phase の条件分岐が文脈依存すぎて実装不能
2. **`/ene` (行動)**: ene.md の6段階フレームワークを LLM が適用。各段階で必要な判断が異なるため決定論的コードは不適
3. **`/ele` (批判)**: patterns.yaml に基づく自動チェック (コード) と、WF 定義に基づく認知的批判 (LLM) は共存する。前者が `synteleia/poiesis/`、後者が WF 定義

---

📖 参照: `axiom_hierarchy.md` L249-364, `system_manifest.md` L39-99, `rom_2026-02-21_poiesis_dokimasia.md`, `ousia_agent.py` 全137行
