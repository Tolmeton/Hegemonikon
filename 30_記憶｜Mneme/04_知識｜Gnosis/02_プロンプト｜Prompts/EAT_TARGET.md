# /eat 対象: プロンプトモジュール群

> **Created**: 2026-03-01
> **Status**: 未消化 — `/eat` で HGK v4.1 体系に統合すべき
> **優先度**: HIGH — 125ファイルの知的資産が HGK 外に孤立している

## 概要

| サブディレクトリ | 内容 | ファイル数 |
|:----------------|:-----|:----------|
| `modules/` | 汎用思考モジュール (第一原理思考, 自律思考, 発散と収束 等) | 26 |
| `modules/dev/` | 開発専用モジュール (TDD enforcement, chaos monkey 等) | 25 |
| `system-instructions/` | システムプロンプト集 (OMEGA, 品質審問官 等) | 20 |
| `templates/forge/` | 6フェーズ思考テンプレート (find→think→act→reflect) | 29+ |

## /eat 消化方針

1. **modules/**: 各ファイルが v4.1 のどの動詞・座標に対応するか分類
2. **modules/dev/**: code-protocols スキルに統合検討
3. **system-instructions/**: Týpos (.prompt) 形式に変換検討
4. **templates/forge/**: v4.1 ワークフローとの対応関係を整理

## 対応する CCL 式

```
/eat+ (Library/prompts全体を深堀り消化)
```
