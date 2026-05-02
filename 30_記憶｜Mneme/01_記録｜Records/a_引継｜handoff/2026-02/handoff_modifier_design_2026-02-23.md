# Handoff: 修飾子 (Dokimasia) 設計と検証

## セッション概要

- **日時**: 2026-02-22 22:00 — 2026-02-23 09:14
- **目的**: 修飾子システムを「楽に使えるレベル」に引き上げる (Phase 4-6)
- **結果**: Phase 4 (`.ax` ドットサフィックス) を実装 → Creator レビューで「クソ構文」と判定 → revert。`[]` ブラケットに統一。

## 成果物

| ファイル | 状態 | 内容 |
|:---------|:-----|:-----|
| `hermeneus/src/ccl_ast.py` | ✅ `ModifierPeras` 追加 | 修飾子空間の Peras 演算用 AST ノード |
| `hermeneus/src/parser.py` | ✅ 修正 | `[Va % Fu]` 外積構文のパース。`.ax` は revert 済み |
| `hermeneus/src/translator.py` | ✅ 修正 | `_translate_modifier_peras` メソッド追加 |
| `hermeneus/src/dispatch.py` | ✅ 修正 | `_collect_wf_modifiers` に ModifierPeras 対応 |
| `hermeneus/src/modifier_presets.py` | ✅ (前セッション) | プリセット管理モジュール |

## 設計判断の経緯 (重要)

### 実装 → 叱責 → Revert のサイクル

1. **Phase 4 初案**: `/dox` を新 WF として提案 → Creator「動詞にすべきでない。`/dox` は既存 WF」
2. **修正案**: `.ax` ドットサフィックス → Creator「`.` と `[]` の2構文は互換性がないクソ」
3. **最終**: `.ax` を revert。**`[]` ブラケットに統一**

### 確定した構文

```
/noe[Va:E]       → 修飾子指定 (Phase 1-3 で実装済み)
/noe[critical]   → プリセット適用
/noe[Va % Fu]    → 外積対比 (Phase 5: 残存)
/noe             → WORKFLOW_DEFAULT_MODIFIERS で自動適用
```

### Creator の核心指摘

> 「なぜ .と [] の２通りの置換できないクソみたいな構文にしてんの」
> 「プリセットなら省略するだけで良くない？」

**教訓**: 新しい構文を増やす前に「既存構文で十分か」を問え。

## 現在の修飾子構文 (最終版)

| 構文 | 意味 | 例 |
|:-----|:-----|:---|
| `[Key:Value]` | 明示指定 | `/noe[Va:P]` |
| `[preset]` | プリセット | `/noe[critical]` |
| `[K1 % K2]` | 外積対比 | `/noe[Va % Fu]` |
| (何も書かない) | デフォルト適用 | `/noe` → Va:E |
| `.d` `.h` `.x` | relation suffix (変更なし) | `/noe.d` |

## 技術的注意

- **Python インポートハング**: `dispatch.py` のテストでハングが頻発。`translator.py` 経由で `lmql` 等の重い依存を引く。テストは `parser.py` 単体でやるのが安全。
- **ModifierPeras**: AST ノードとして残存。`[Va % Fu]` パース時に使用。ccl_ast.py の ASTNode Union に登録済み。

## 次のセッションで

1. `ModifierPeras` の `preset_name` フィールドは使われなくなった (`.critical` 削除)。フィールドの掃除を検討
2. `[Va % Fu]` の実際の LLM 実行テスト (MCP server 経由)
3. 修飾子ドキュメント (`ccl_language.md`) の更新 — 構文例を最終版に合わせる

---

*Generated: 2026-02-23 09:14*
