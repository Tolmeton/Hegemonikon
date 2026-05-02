# Cortex API Migration Plan (generateContent → generateChat)

**Document Status**: Draft
**Created**: 2026-02-20
**Target Component**: `mekhane/ochema/cortex_client.py`

## 背景 (Background)

現在、`CortexClient.ask()` メソッドは `generateContent` エンドポイントを主に使用しています。しかし、Gemini 3.1 Pro Preview のような最新モデルはリリース直後には `generateContent` に対応しておらず、`generateChat` エンドポイントでのみ利用可能であるケースが確認されました (DX-010 参照)。
現在は 404 エラーを検知して動的キャッシュ (`_chat_only_cache`) に登録し、自動で `generateChat` (すなわち `chat()` メソッド) にフォールバックする暫定対応が入っていますが、長期的には `ask()` も `generateChat` に完全移行することでコードの単純化と新モデル即時対応の恩恵を受けられると考えられます。

本ドキュメントでは、`generateContent` から `generateChat` への統一を図るためのアーキテクチャ設計と技術的課題を整理します。

## 検討事項 (Considerations)

### 1. `ask()` 内部の `chat()` への統一の是非

**メリット (Pros):**

- **コードベースの単純化**: `_build_request` (generateContent用) と `chat()` 向けペイロードの二重管理を解消できる。
- **最新モデルの即時対応**: 新モデルがリリースされた直後でも、エラーなくすぐに呼び出せる (動的フォールバックが不要になる)。
- **一貫性**: IDE 機能が依存している cloudcode-pa と完全にパスが一致するため、IDE 側から見えている機能との乖離がなくなる。

**デメリット (Cons):**

- **JSON Structured Output**: `generateChat` が JSON schema (response_mime_type, response_schema) をサポートしているか未検証。`generateContent` で多用される構造化出力が使えなくなるリスクがある。
- **Tools / Function Calling**: `generateChat` が tool use を完全に等価にサポートしているか要検証。

### 2. メタデータパラメータの扱い

`generateChat` エンドポイントで以下のパラメータをどう表現するかの実装方針：

| パラメータ | 現行実装 (`generateContent`) | 移行実装 (`generateChat`) |
|:---|:---|:---|
| **`system_instruction`** | `systemInstruction` フィールド | `history` 配列の先頭に `{"author": 0, "content": "..."}` として挿入 |
| **`temperature`** | `generationConfig.temperature` | **未対応** (generateChat は温度指定を無視/未定義のもよう) |
| **`max_tokens`** | `generationConfig.maxOutputTokens` | **未対応** (現状では渡す正規のフィールドが不明) |
| **`thinking_budget`** | `generationConfig.thinkingConfig` | `include_thinking_summaries: true` としてブール値で指定 (予算制御は現状不可) |

### 3. Breaking Changes (破壊的変更)

全面移行した場合にユーザー（呼び出し側）へ影響する可能性のある変更：

1. **`temperature`, `max_tokens` 指定の無視**: パラメータを渡しても API 側が受け付けないため、出力のランダム性制御や上限制御が効かなくなる。
2. **`system_instruction` の解釈の差異**: `system_instruction` を `history` の `author: 0` 要素として扱うため、モデル側のコンテキスト解釈で厳密な意味合い (システムプロンプト vs 初回メッセージ) が変わる可能性がある。
3. **Structured Output の非互換**: 前述の通り動作しない可能性が高く、JSON 形式を要求する Agent ワークフローが破損する危険性がある。

## 結論と推奨アプローチ (Conclusion & Recommendation)

現時点では、`generateChat` には `temperature` などの微調整機能や Structured Output のサポートに関する不明点が多く、**`ask()` を完全に `generateChat` へ移行するのは時期尚早**です。

**推奨:**
当面は、現行のハイブリッド方式 (基本は `generateContent` で実行し、未対応モデルには 404 検知で `chat()` にフォールバックする方式) を維持します。`generateChat` ならではの専用機能が必要になった場合、または `generateChat` 側で `generationConfig` が完全にサポートされた段階で、再検討を行います。
