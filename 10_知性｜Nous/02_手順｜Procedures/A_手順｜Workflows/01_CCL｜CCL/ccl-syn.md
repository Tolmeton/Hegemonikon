---
description: "監る — /kho_/s-_/pro_/dia+{synteleia}_~(/noe*/dia)_V:{/pis+}_/dox-"
lcm_state: beta
min_convergence_iters: 2
version: "1.0"
---

# /ccl-syn: Synteleia 監査マクロ

> **CCL**: `@syn = /kho_/s-_/pro_/dia+{synteleia}_~(/noe*/dia)_V:{/pis+}_/dox-`
> **用途**: Synteleia 監査 (L1+L2) を発動し、確信度を検証する
> **圏論**: 免疫系 = 恒等的自然変換 (同一性の検証)
> **認知骨格**: Prior → Likelihood → Posterior

## 展開

| 相 | ステップ | 意味 |
|:---|:---------|:-----|
| Prior | `/ops` | 監視対象の場を把握する |
| Prior | `/s-` | 何を監視するかの焦点を定める (方向性) |
| Prior | `/pro` | 「何かおかしい」直感を感じ取る (前感情) |
| Likelihood | `/dia+{synteleia}` | Synteleia 多角監査を発動 (L1静的 + L2セマンティック) |
| Posterior | `~(/noe*/dia)` | 監査結果を直観×判定で振動検証 |
| Posterior | `V:{/pis+}` | 確信度を検証ゲートで評価 |
| Posterior | `/dox-` | 監査結果を軽量記録 |

## 使用例

```ccl
@syn                       # 標準監査 (最後の出力を監査)
@syn _ /ene+               # 監査後に修正実行
@build _ @syn              # 構築後にセマンティック監査
C:{@build _ @syn}          # 監査合格まで収束ループ
```

## 統合先

| WF | 接続 | 発動条件 |
|:---|:-----|:---------|
| `/dia+` | 自動発動 | `{synteleia}` パラメータ指定時 |
| `@vet` | 手動接続 | `@vet _ @syn` で検証強化 |
| `@build` | 手動接続 | `@build _ @syn` で品質保証 |

---

## Execution Guide — 各ステップの期待出力

> 「監査しました」は監査ではない。何を監視し、何を発見し、どう判定したかを明示する。

### Prior 相 — 必須出力

- `/ops`: 監視対象の **具体的なファイル/モジュール/状態** を列挙
- `/s-`: **焦点** — 今回何に集中して監視するか (1-2行)
- `/pro`: **直感** — 「何かおかしい」と感じる点があるか (なければ「特になし」)

### Likelihood 相 — 必須出力

- `/dia+{synteleia}`: Synteleia 監査の結果テーブル:

| レベル | チェック | 結果 | 詳細 |
|:-------|:---------|:-----|:-----|
| L1 静的 | ... | PASS/FAIL | ... |
| L2 セマンティック | ... | PASS/FAIL | ... |

### Posterior 相 — 必須出力

- `~(/noe*/dia)`: 監査結果の **直観的評価** と **論理的評価** の照合
- `V:{/pis+}`: 確信度 (%) + 根拠
- `/dox-`: 発見パターンの1行記録

---

## Anti-Shallow Gate

| # | チェック | 閾値 | 違反時 |
|:--|:---------|:-----|:-------|
| G1 | 監視対象が **具体的に** 特定されている | ファイル/モジュール名あり | 対象を明記する |
| G2 | Synteleia 結果テーブルがある | L1/L2 各1行以上 | 監査を実行する |
| G3 | 確信度 (%) が記載されている | 存在 | 確信度を付与する |

---

*v1.0 — Synteleia 監査マクロ初版*
*v1.1 — Execution Guide + Anti-Shallow Gate 追加 (2026-02-24)*
