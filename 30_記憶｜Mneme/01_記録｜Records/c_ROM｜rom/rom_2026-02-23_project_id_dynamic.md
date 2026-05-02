# ROM: Project ID は動的に生成される（実測確定）

> **日付**: 2026-02-23
> **確信度**: [確信: 95%] (SOURCE: 同一マシンのログファイル6件から実測)
> **関連**: DX-010 v9.0, ROM claude_ls_independent

---

## 確定事実

`loadCodeAssist` API が返す `cloudaicompanionProject` は**呼出しごと（またはプロセスごと）に動的生成**される。ハードコードは原理的に不可能。

## 実測証拠

同一マシン (`hgk`) のログから6個の異なる Project ID を発見:

| 時期 | Project ID | 出典 |
|:-----|:-----------|:-----|
| 2026-02-13 | `robotic-victory-pst7f0` | ls-standalone-reference |
| 2026-02-15 | `augmented-key-v3lbr` | ROM cloudcode_pa |
| 不明 | `driven-circlet-rgkmt` | DX-010 旧版 |
| 不明 | `double-theater-4gdjz` | uvicorn.log |
| 不明 | `acoustic-modem-4q00g` | hgk_serve.log |
| 2026-02-23 | `spatial-gearing-xwz46` | cot_e2e_v2.log |

## 実装上の含意

| 項目 | 対応 |
|:-----|:-----|
| **CortexClient** | `_get_project()` でセッション中キャッシュ。再起動時に再取得 |
| **ドキュメント** | Project ID をハードコードしない。「検証時のスナップショット」として扱う |
| **テスト** | Project ID を固定値で比較しない |

## 未解明

- ローテーション間隔（プロセスごと？トークンリフレッシュごと？日次？）
- 同一プロセス内で `loadCodeAssist` を複数回呼んだ場合に同じ ID が返るか

---

*ROM v1.0 — 2026-02-23 実測確定*
