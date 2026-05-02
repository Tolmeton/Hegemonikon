# Handoff: Q4 Output Template Enforcement + 24定理拡張

## セッション概要

- **日時**: 2026-02-23 午後 (継続セッション)
- **目的**: CoVe Q4 リスク「出力テンプレートのプログラム的強制」の実装 + 24定理への拡張
- **結果**: translator.py に2段フォールバックテンプレート注入を実装。50テスト全通過。

## 成果物

| ファイル | 状態 | 内容 |
|:---------|:-----|:-----|
| `hermeneus/src/translator.py` | ✅ 修正 | `_translate_workflow()` に WF→SKILL 2段フォールバック追加 |
| `hermeneus/tests/test_template_enforcement.py` | ✅ 新規 | 15テスト (挿入×6WF, 構造×6WF, エスケープ, フォールバック, パス解決) |
| `.agent/workflows/{t,m,k,d,c,o}.md` | ✅ 修正 | Q1構造メモ + Q2時間制限削除 + Q3 KPT→C3統合 (前セッション) |

## 技術的内容

### Q4 実装: 2段フォールバック (translator.py L445-L500)

```
Workflow ノード (AST)
  ↓ wf.id
WorkflowRegistry.get() → metadata["output_template"] → 外部ファイル読込
  ↓ (なければ)
WF定義の skill_ref → SKILL.md を直接読み → 「統合出力形式」code block を正規表現抽出
  ↓
LMQL 文字列にエスケープ埋込 → argmax ブロックの指示として注入
```

### パス解決

- `source_path.parents` を遡行して `.agent/templates/` や `.agent/skills/` を探索
- Sync シンボリックリンク越しに正常動作を確認

### SkillRegistry が不採用になった理由

SkillRegistry は全SKILL.mdを初回パースするためI/Oが重い（30秒以上）。`skill_ref` パスから直接読む方式なら1ファイルのI/Oで済む。

## テスト結果

| スイート | 結果 |
|:---------|:-----|
| test_template_enforcement.py | 15 passed |
| test_executor.py + test_runtime.py | 35 passed |
| **合計** | **50 passed, 0 failed** |

## テンプレート挿入状態

| WF | ソース | 状態 |
|:---|:-------|:-----|
| `/t`, `/m`, `/k`, `/d`, `/c`, `/o` | 外部テンプレートファイル | ✅ |
| `/noe`, `/bou`, `/zet`, `/ene` | SKILL.md 統合出力形式 | ✅ |
| `/dia` | なし (正常: SKILL.md にセクションなし) | — |

## 未完了・次セッション候補

| # | タスク | 優先度 |
|:--|:-------|:-------|
| 1 | `/dia` SKILL.md に統合出力形式セクションを追加 | 低 |
| 2 | 残り19定理の「統合出力形式」有無の網羅確認 | 低 |
| 3 | 実行後の出力検証 (テンプレートとの構造一致チェック) | 中 |
| 4 | テンプレートサイズ上限 (トークン予算圧迫防止) | 低 |

## 学んだこと (KPT)

| 項目 | 内容 |
|:-----|:-----|
| Keep | パス遡行ロジックが Sync 移行にも耐えた。軽量な直接読み込みが正解 |
| Problem | SkillRegistry の初回パースが重すぎて translator 内で呼べない |
| Try | SKILL.md のテンプレート抽出をキャッシュする仕組み (LRU cache 等) |
