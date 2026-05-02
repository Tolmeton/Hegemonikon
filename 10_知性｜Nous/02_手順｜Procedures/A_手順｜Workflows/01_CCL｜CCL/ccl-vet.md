---
description: "確かめる — /ops+{git_diff}_/dok+{quality}_C:{V:{/ele+}_/dio+}_/pei+{test}_/pei+{dendron_guard}_/akr+{check}_/kat+"
lcm_state: stable
min_convergence_iters: 3
version: "3.1"
lineage: "v1.0 → v2.0 → v3.0 (v4.1 再構成) → v3.1 (xrev: /dio+, /akr+ 適用)"
ccl_signature: "@vet"
hegemonikon: Diástasis × Krisis × Methodos × Orexis
layer: "CCL マクロ"
trigonon:
  verbs: [V14, V12, V18, V20, V07, V15, V09]
  coordinates: [I/Macro, I/U+Mi, I/-, I/修正, I/Explore+Mi, I/Micro, I/C]
---

# /ccl-vet: 自己検証マクロ (v3.0)

> **CCL**: `@vet = /ops+{git_diff}_/dok+{quality}_C:{V:{/ele+}_/dio+}_/pei+{test}_/pei+{dendron_guard}_/akr+{check}_/kat+`
> **用途**: 実装完了後の構造的自己検証
> **認知骨格**: 差分確認→品質計量→検証修正ループ→テスト→技術チェック→確定
> **深度**: 全ステップ `+` (深層)
> **動詞数**: 7つの異なる v4.1 動詞、4族にまたがる

## v3.0 零からの再構成

| # | 認知操作 | 旧 (v2.0) | 新 (v3.0) | 族 | 座標 | なぜこの動詞か |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 差分確認 | `/ops{git_diff}` | **`/ops+{git_diff}`** | Diástasis | Sc:Ma | Synopsis: 変更の全体像。深化 |
| 2 | 品質計量 | `/dok{quality}` | **`/dok+{quality}`** | Krisis | Pr:U, Sc:Mi | Dokimasia: 小さく検証。深化 |
| 3 | 検証→修正ループ | `C:{V:{/dia+}_/ene+}` | **`C:{V:{/ele+}_/dio+}`** | Orexis×Orexis | Vl:- × 修正 | 反駁→**Diorthōsis (修正)**。汎用行為→専門修正に昇格 |
| 4 | テスト実行 | `/pei{test}` | **`/pei+{test}`** | Methodos | Fu:Explore, Sc:Mi | Peira: 実験的検証。深化 |
| 5 | PROOF チェック | `/pei{dendron_guard}` | **`/pei+{dendron_guard}`** | Methodos | Fu:Explore, Sc:Mi | 同上 |
| 6 | 精密検証 | `/tek{check}` | **`/akr+{check}`** | Diástasis | Sc:Mi | **Akribeia: 精密な検証。** 技法チェックより精密検証が適切 |
| 7 | 確定 | `/pis_/dox` | **`/kat+`** | Krisis | Pr:C | 検証結論を確定 |

### 除去された旧体系要素

| 旧要素 | 理由 |
| :--- | :--- |
| `/kho{context}` | `/ops+{git_diff}` に吸収 (文脈も俯瞰の一部) |
| `/dia+` (検証ループ内) | `/ele+` に置換 (反駁 = Elenchos の本質) |
| `/fit` | `/ele+` による反駁検証に吸収 |
| `/pis_/dox` | `/kat+` に統合 |

## 展開

| # | ステップ | 動詞 (v4.1) | 意味 |
| :--- | :--- | :--- | :--- |
| 1 | `/ops+{git_diff}` | V14 Synopsis | git diff で変更スコープを俯瞰 |
| 2 | `/dok+{quality}` | V12 Dokimasia | 品質を計量: テスト、エラー処理、可読性 |
| 3 | `C:{V:{/ele+}_/ene+}` | V18 × V04 | 反駁→修正の収束ループ |
| 4 | `/pei+{test}` | V07 Peira | テスト実行 |
| 5 | `/pei+{dendron_guard}` | V07 Peira | PROOF/PURPOSE チェック |
| 6 | `/tek+{check}` | V08 Tekhnē | 技術妥当性: スタック整合、過剰設計、依存リスク |
| 7 | `/kat+` | V09 Katalēpsis | 検証完了を確定 |

## Dendron Guard

// turbo

```bash
cd ~/oikos/01_ヘゲモニコン｜Hegemonikon && PYTHONPATH=. .venv/bin/python -m mekhane.dendron guard .
```

## 使用例

```ccl
@vet                       # 標準検証
@build _ @vet              # 構築→検証
@vet _ @xrev               # 検証→クロスモデルレビュー
```

## Anti-Shallow Gate

| # | チェック | 閾値 | 違反時 |
| :--- | :--- | :--- | :--- |
| G1 | `git diff --stat` の出力がある | 存在 | diff を取得 |
| G2 | `/dok+` にテーブルが含まれる | 1つ以上 | 品質テーブルを追記 |
| G3 | テスト結果 (PASS/FAIL) がある | 存在 | テストを実行 |

## 射の提案

| 条件 | 射 | 意味 |
| :--- | :--- | :--- |
| 外部検証 | `>> @xrev` | クロスモデルレビュー |
| 記録 | `>> @learn` | 永続化 |
| 修正 | `>> /ene+` | 追加修正 |

---
*v2.0 — V12 Dokimasia + P4 Tekhnē 統合 (24定理活用深化 Phase 2)*
*v2.1 — Execution Guide + Anti-Shallow Gate 追加 (2026-02-24)*
*v3.0 — v4.1 零からの再構成 (随伴)。7動詞4族。/dia→/ele, /pis+/dox→/kat (2026-02-27)*
