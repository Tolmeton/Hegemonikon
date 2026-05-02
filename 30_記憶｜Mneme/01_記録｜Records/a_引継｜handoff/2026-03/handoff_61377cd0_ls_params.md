# Handoff: LS パラメータ調査 + /ccl-learn 永続化

> **Session**: 61377cd0-1b7f-4823-b6db-a4a67bde8959
> **日時**: 2026-02-19 05:45 JST
> **前提**: DX-010 v6.0 更新完了

## 成果物

1. **DX-010 v6.0** — `kernel/doxa/DX-010_ide_hack_cortex_direct_access.md`
   - D.4: LS パラメータ制約 (ThinkingBudget/MaxOutputTokens/Temperature は LS 内部管理)
   - D.5: 全モデルリスト (8モデル + LS 内部 ID)
   - D.6: 未公開モデル名 (HORIZONDAWN, COSMICFORGE, INFINITYJET, HAIKU_THINKING)

## 核心的発見

### 1. LS はパラメータの完全なブラックボックス

- IDE JS 側 (extension.js, main.js) に thinkingBudget/maxOutputTokens の設定コードは存在しない
- settings.json にもユーザー制御可能なパラメータ設定はない
- **全てが LS Go バイナリ (169MB, stripped) 内部で管理**

### 2. Claude API パラメータの抽象化

- `extended_thinking`, `budget_tokens`, `reasoning_effort` は LS バイナリの strings に存在しない
- Claude 固有パラメータは Gemini と共通の `ModelInfo.ThinkingBudget` にマッピング
- [推定: 80%] — 間接証拠のみ。strace で直接確認が残課題

### 3. モデルバリアント名にパラメータヒント

- Gemini 3 Pro (High) / (Low) → ThinkingLevel の違い
- Claude Sonnet 4.5 / 4.5 (Thinking) → extended_thinking の有無
- GPT-OSS 120B (Medium) → quality/speed トレードオフ

### 4. 未公開モデル名

- MODEL_CLAUDE_4_5_HAIKU_THINKING
- MODEL_GOOGLE_GEMINI_HORIZONDAWN / COSMICFORGE / INFINITYJET

## 残課題

| # | 課題 | 推奨手法 | 優先度 |
|:--|:-----|:---------|:-------|
| 1 | ThinkingBudget の具体的なデフォルト値 | `strace -p <LS_PID>` で API リクエスト傍受 | 中 |
| 2 | Claude の実際の budget_tokens 値 | 同上 | 中 |
| 3 | vscdb の全モデル設定取得 | IDE を停止してから sqlite3 で読む | 低 |
| 4 | MaxOutputTokens の実測 | Cortex API vs IDE で同一プロンプトの出力長比較 | 中 |

## 技術的制約 (学んだこと)

| 制約 | 原因 | 回避策 |
|:-----|:-----|:-------|
| 169MB Go バイナリの全スキャン | I/O バウンド (全手法タイムアウト) | strings のみ成功 (キャッシュ効果) |
| vscdb の直接アクセス | IDE の WAL ロック | IDE 停止 or WAL+shm 同時コピー |
| PTY ハング | GCP 環境の問題 | write_to_file + timeout 付き実行 |
| Protobuf の具体値 | stripped バイナリ | strace で実行時の値を傍受 |

## パターン化

### P1: LS 解析の優先手法

```
strace (実行時傍受) > strings + grep (静的文字列) > Ghidra (逆アセンブル) > objdump/readelf (汎用)
```

### P2: vscdb アクセス

```
IDE 停止 → sqlite3 直接読み > cp -f db + wal + shm → 別パスで読み > nolock=1 (不安定)
```

### P3: 大容量バイナリのキャッシュ

```
cat file > /dev/null (プリロード) → 連続コマンドで活用 (キャッシュ有効時間は短い)
```

---

*Handoff by Claude | Session 61377cd0 | 2026-02-19 05:45 JST*
