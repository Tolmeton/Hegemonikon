# Gemini Code Assist: Rules / Workflows スコープ体系

> **SOURCE**: 2026年3月 Google Codelabs 公式資料 + 公式ドキュメント

## スコープ定義

| スコープ | 種別 | パス |
|:---------|:-----|:-----|
| グローバル | Rules | `~/.gemini/GEMINI.md` |
| グローバル | Workflows | `~/.gemini/antigravity/global_workflows/<name>.md` |
| ワークスペース | Rules | `{workspace}/.agents/rules/` |
| ワークスペース | Workflows | `{workspace}/.agents/workflows/` |

## 重要事項

### GEMINI.md は全 IDE AI が読む
- `~/.gemini/GEMINI.md` は **Gemini Code Assist のグローバル Rules ファイル**
- Claude (Antigravity) も含め、IDE 上の全 AI がこのファイルを読み込む
- → Claude 専用指示を書く場所ではない。全 Agent 共通のインフラ指示を書く場所

### .agents/ (複数形) が正式
- コミュニティ投稿 (Reddit, Qiita 等) では `.agent/rules/` (単数形) の記載あり
- 2026年3月15日公開の **Google 公式 Codelabs** では `.agents/rules/` (複数形) が正式パス

### ワークスペース .gemini/GEMINI.md は不要
- ワークスペースの `.gemini/GEMINI.md` は Rules としてグローバルと重複する
- ワークスペース固有の Rules は `.agents/rules/*.md` に配置する
- HGK では `behavioral_constraints.md` + `horos-*.md` + `episteme-*.md` がこれに該当

## HGK での住み分け

| ファイル | 性質 | 内容 |
|:---------|:-----|:-----|
| `~/.gemini/GEMINI.md` | 環境指示 (非Kalon) | 言語設定、ディレクトリ構造、MCP 一覧、TYPOS-First 等 |
| `.agents/rules/behavioral_constraints.md` | 普遍法則 (Kalon) | Hóros 12法、S-I/II/III、BRD、FEP 演繹 |
| `.agents/rules/horos-N*.md` | 普遍法則 (Kalon) | 12法の個別定義 |
| `.agents/rules/episteme-*.md` | 知識基盤 | entity-map, fep-lens, kalon, tool-mastery |

---

*KI 作成: 2026-03-17 — Creator 指示に基づく*
