---
description: "組む — /bou+_(/ske+*/sag+)_/ark+_/tek+_/ene+_V:{/ele+}_I:[✓]{/kat+}"
lcm_state: stable
min_convergence_iters: 2
version: "2.1"
lineage: "v1.0 (旧体系) → v2.0 (v4.1 再構成) → v2.1 (xrev: /ark+ 追加。8動詞5族)"
ccl_signature: "@build"
hegemonikon: Telos × Methodos × Diástasis × Orexis × Krisis
layer: "CCL マクロ"
trigonon:
  verbs: [V02, V05, V06, V16, V08, V04, V18, V09]
  coordinates: [I/P+Future, I/Explore, I/Exploit, I/Macro, I/Exploit+C, I/P+Exploit, I/-, I/C]
---

# /ccl-build: 構築マクロ (v2.0)

> **CCL**: `@build = /bou+_(/ske+*/sag+)_/ark+_/tek+_/ene+_V:{/ele+}_I:[✓]{/kat+}`
> **用途**: 0から作る。設計→実装→検証→記録の一気通貫
> **圏論**: @eat (外→内: 消化) の随伴。内→外の具現化
> **深度**: 全ステップ `+` (深層)
> **動詞数**: 8つの異なる v4.1 動詞、5族にまたがる

## v2.0 零からの再構成

| # | 認知操作 | 旧 (v1.0) | 新 (v2.0) | 族 | 座標 | なぜこの動詞か |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 何を作るか | `/bou-` | **`/bou+`** | Telos | Va:P, Te:Future | 目的を深く問う。`-`ではなく`+` |
| 2 | 方略設計 | `/met`+`/ske` | **`(/ske+*/sag+)`** | Methodos | Fu:Explore⊗Exploit | 拡げつつ絞る |
| 3 | 構造設計 | — | **`/ark+`** | Diástasis | Sc:Ma | **Architektonikē: 全体構造を設計。** (xrev v2.1 追加) |
| 4 | 技法選択 | `/tek` | **`/tek+`** | Methodos | Fu:Exploit, Pr:C | 維持。既知の方法で確実に |
| 5 | 実行 | `/ene+` | **`/ene+`** | Telos | Va:P, Fu:Exploit | 維持。意志を具現化 |
| 5 | 検証 | `V:{/dia-}` | **`V:{/ele+}`** | Orexis | Vl:- | **Elenchos: 反駁で検証。** `/dia`→`/ele`。`-`→`+`で深い検証 |
| 6 | 確定 (成功時) | `I:[✓]{/dox-}` | **`I:[✓]{/kat+}`** | Krisis | Pr:C | 成功時に確定 |

### @build の特徴: Methodos 族が3つ

| 動詞 | 族 | 座標 | 意味 |
| :--- | :--- | :--- | :--- |
| `/ske+` | Methodos | Fu:**Explore** | 可能性を拡げる |
| `/sag+` | Methodos | Fu:**Exploit** | 最適解に絞る |
| `/tek+` | Methodos | Fu:**Exploit**, Pr:C | 既知の技法で確実に |

> 「組む」は **方法の芸術** — 3つの Methodos 動詞が構築の核心を担う。

## 展開

| 相 | ステップ | 動詞 (v4.1) | 意味 |
| :--- | :--- | :--- | :--- |
| Prior | `/bou+` | V02 Boulēsis | 何を作るか、目的を深く定義 |
| Prior | `(/ske+*/sag+)` | V05 × V06 | 構築方略: 拡げつつ絞る |
| Likelihood | `/tek+` | V08 Tekhnē | 技法選択: 既知の方法で確実に |
| Likelihood | `/ene+` | V04 Energeia | 実行: 意志を具現化 |
| Posterior | `V:{/ele+}` | V18 Elenchos | 検証: 反駁で弱点を炙り出す |
| Posterior | `I:[✓]{/kat+}` | V09 Katalēpsis | 成功時: 確定 |

## 使用例

```ccl
@build                     # 標準構築
@build _ @vet              # 構築後に自己検証
F:[api,ui,db]{@build}      # 3コンポーネントそれぞれに構築
@ready _ @build            # 見渡し→構築
```

## Anti-Shallow Gate

| # | チェック | 閾値 | 違反時 |
| :--- | :--- | :--- | :--- |
| G1 | `/ene+` にファイル変更一覧がある | 存在 | 追記する |
| G2 | `/tek+` に比較テーブルがある | 存在 | 候補を追加する |
| G3 | 動作確認結果が記録されている | 存在 | テストを実行する |

## 射の提案

| 条件 | 射 | 意味 |
| :--- | :--- | :--- |
| 検証したい | `>> @vet` | クロスモデル検証 |
| 消化する | `>> @chew` | 学びを消化 |
| 記録する | `>> @learn` | 永続化 |

---
*v1.0 — 構築マクロ初版*
*v1.1 — Execution Guide + Anti-Shallow Gate 追加 (2026-02-24)*
*v2.0 — v4.1 零からの再構成 (随伴)。7動詞4族。Methodos 3動詞が核心 (2026-02-27)*
