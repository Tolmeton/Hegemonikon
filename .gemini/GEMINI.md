# Hegemonikón — プロジェクト指示 (Gemini CLI)

> **正本:** [`.claude/CLAUDE.md`](../.claude/CLAUDE.md)
> プロジェクトルール・エージェント構成・フック定義は **`.claude/`** がマスター。
> ユーザーレベル指示 (`~/.gemini/GEMINI.md`) に Doctrine v4.3 を配置済み。

---

## 言語

- **全出力は日本語**。コードコメントも日本語。
- 簡潔かつ丁寧。壁のような散文禁止。構造化 (テーブル・箇条書き) 必須。

## リポジトリ構造

```
00_核心｜Kernel/    — 公理・定理の根幹 (SACRED_TRUTH, kalon, u_series)
10_知性｜Nous/      — 制約・手順・知識・企画・素材
20_機構｜Mekhane/   — ソースコード + モジュール docs
30_記憶｜Mneme/     — 記憶・コンテキスト・記録
40_作品｜Poiema/    — HGK 産出物
50_外部｜External/  — 外部 OSS
60_実験｜Peira/     — 実験・テスト
80_運用｜Ops/       — スクリプト・開発ツール
90_保管庫｜Archive/ — アーカイブ
```

## 中核プロジェクト

| PJ | パス | 概要 |
|:---|:-----|:-----|
| Hermēneus | `hermeneus/` | CCL 実行保証コンパイラ |
| Ochēma | `mekhane/ochema/` | LLM ルーター (LS + Cortex) |
| Periskopē | `mekhane/periskope/` | Deep Research エンジン |
| Dendron | `mekhane/dendron/` | 存在目的テンソル (EPT) |
| CCL Runtime | `mekhane/ccl/` | CCL パーサー・実行エンジン |
| HGK App | `hgk/` | Tauri v2 デスクトップアプリ |
| CCL-PL | `ccl-pl/` | CCL プログラミング言語 |

## 作業上の注意

1. **破壊的操作前に確認** — ファイル削除・上書き前に提案
2. **HGK 独自概念は `kernel/` を参照** — kalon, poiesis, stoicheia は自然言語と別物
3. **コード変更後はテスト** — `pytest` で検証
4. **コミットメッセージは物語** — 何をなぜ変えたかを記述
5. **`.env` / API キーを出力しない**

## MCP サーバー

ユーザーレベル (`~/.gemini/mcp_config.json`) に 12 サーバーを定義済み:
ochema, hermeneus, mneme, digestor, jules, periskope, sekisho, sympatheia, typos, motherbrain, prokataskeve, forge

## WF / Skills

- ワークフロー定義: `.agents/workflows/*.md`
- スキル定義: `.claude/skills/`
