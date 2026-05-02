# Handoff: Cortex API ツーリングセッション

> **日時**: 2026-02-14 00:25-00:57 JST
> **セッション**: 5697133d
> **品質**: ★★★★☆ (ツール完成 + 新モデル発見、ただし HGK 本体への直接的価値は周辺的)
> **コンテキスト**: 🟢 N=16 → ~25 (健全)

---

## 成果

### `scripts/cortex.sh` — Cortex API 直叩きスクリプト

DX-010 v2.0 の手順をワンライナー化。

**機能**:

- Token cache (55分) — refresh_token → access_token 自動管理
- system instruction (`-s`)
- モデル選択 (`-m gemini-2.5-pro` / `gemini-3-pro-preview`)
- ストリーミング (`--stream`)
- thinking budget (`--think 1024`)
- quota 確認 (`--quota`)
- loadCodeAssist 情報 (`--info`)
- token 使用量表示 (`--usage`)

**修正した問題**:

1. `HTTPS_PROXY` mitmproxy 残骸 → スクリプト冒頭で unset
2. Python クォート問題 → 環境変数 + heredoc で安全に解決

### テスト結果

| テスト | 結果 | 詳細 |
|:-------|:-----|:-----|
| 基本 generate | ✅ | `2+2?` → `Four` (14 tok) |
| system instruction | ✅ | 俳句ポエット → 正しく俳句生成 (38 tok) |
| gemini-2.5-pro | ✅ | FEP 日本語説明 (2053 tok, thinking 含む) |
| gemini-3-pro-preview | ✅ | 応答確認 (208 tok) |
| retrieveUserQuota | ✅ | 全12モデルバケット取得 |

### 🔥 発見: Quota API で確認された全モデル (12バケット)

```
gemini-2.0-flash / _vertex
gemini-2.5-flash / _vertex
gemini-2.5-flash-lite / _vertex
gemini-2.5-pro / _vertex
gemini-3-flash-preview / _vertex  ← 未公開
gemini-3-pro-preview / _vertex    ← 未公開 (応答確認済み)
```

---

## Creator からの重要な批判

> **「Opus が HGK の基盤なのに、Gemini API だけでは意味が薄いのでは？」**

**正当な指摘**。cortex.sh の価値は HGK 本体ではなく周辺:

- Jules Specialist Reviews (LS 死亡問題の回避)
- n8n 自動化タスク (Opus quota 節約)
- セカンドオピニオン (異なるモデルの視点)

HGK の WF 実行、対話、意思決定には Claude Opus が不可欠。

---

## DX-010 更新

- 利用可能モデルに gemini-3 系追加
- retrieveUserQuota テスト済みに変更
- アクションリスト 5/11 完了

---

## 変更ファイル (本セッション)

| ファイル | 状態 |
|:---------|:-----|
| `scripts/cortex.sh` | 🆕 新規作成 |
| `kernel/doxa/DX-010_*.md` | 📝 更新 (モデル一覧 + テスト結果) |

---

## 次にやるべきこと

1. streaming テスト (`--stream` オプション)
2. `thinkingConfig` 制御テスト (budget 指定)
3. Jules Specialist Reviews を cortex.sh 経由に移行 (LS 死亡問題の根本解決)
4. n8n → cortex.sh 統合

---

*Handoff generated — 2026-02-14 00:57 JST*
