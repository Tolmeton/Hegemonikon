# D4 関手忠実性実験 — コーパス

## 概要

| 項目 | 値 |
|:--|:--|
| 総数 | 110 プロンプト |
| 正テスト | 100 (5カテゴリ × 20) |
| 否定テスト (C2) | 10 |
| 言語 | 日本語 55 / 英語 55 |
| 形式 | JSONL (1行 = 1 JSON オブジェクト) |

## カテゴリ

| ファイル | カテゴリ | 数 | 内容 |
|:--|:--|--:|:--|
| `A_analysis.jsonl` | 分析系 | 20 | コード分析、データ分析、テキスト分析、ビジネス分析 |
| `B_creative.jsonl` | 創造系 | 20 | 文章作成、デザイン、アイデア生成、カリキュラム設計 |
| `C_judgment.jsonl` | 判断系 | 20 | 評価、比較、リスク査定、意思決定 |
| `D_metacognitive.jsonl` | メタ認知系 | 20 | 自己反省、認知バイアス検出、学習戦略 |
| `E_composite.jsonl` | 複合系 | 20 | 多段階タスク、分析→策定→実行の複合操作 |
| `N_negative.jsonl` | 否定テスト | 10 | 非認知的プロンプト (情報検索、計算、挨拶等) |
| `corpus_all.jsonl` | 統合 | 110 | 全ファイルの結合 |

## JSONL スキーマ

```json
{
  "id": "A01",           // 一意識別子 (カテゴリ頭文字 + 連番)
  "category": "analysis", // カテゴリ名
  "lang": "ja",          // 言語 (ja/en)
  "prompt": "...",       // プロンプト本文
  "source": "...",       // 出典パターン
  "difficulty": "low"    // 期待される変換難易度 (low/medium/high/n/a)
}
```

否定テスト追加フィールド:
```json
{
  "expected_result": "non-cognitive",  // 期待される判定
  "reason": "..."                     // 非認知の理由
}
```

## ソース

- `dev-community`: ソフトウェア開発コミュニティの実務プロンプト
- `business-prompts`: ビジネス・経営関連プロンプト集
- `academic-prompts`: 学術・教育プロンプト
- `critical-thinking`: 批判的思考・論理学プロンプト
- `designed-negative`: D4 実験用に意図的に設計した否定テスト
- その他: `marketing-prompts`, `hr-prompts`, `pm-prompts`, `ux-design`, `ops-prompts` 等

## 選択基準

1. HGK とは無関係に独立して作成されたプロンプトパターン
2. 日本語/英語の均等配分
3. 単純 (low) → 複合 (high) のグラデーション
4. 否定テスト 10個を混入 (C2 制御機構)
