# Claude Code Context Inventory

最終確認: 2026-04-10

この文書は、HGK で Claude Code に流入するコンテキストを
`常時` / `条件付き` / `参照のみ` / `ドリフト` に分けて棚卸するための現況メモ。
設定変更の正本ではなく、現況把握のためのインデックスとして使う。

## 1. 正本と実体

| 層 | 現在の正本 | 実体 |
|---|---|---|
| ユーザー共通 instruction | `~/.claude/CLAUDE.md` | 存在。HGK OS / Advisor Strategy / Rules 概要を含む |
| ユーザー共通 hooks | `~/.claude/settings.canonical.json` | 存在。`SessionStart` / `PreToolUse` / `PostToolUse` / `Stop` を定義 |
| ユーザー共通 runtime settings | `~/.claude/settings.json` | 存在。SessionStart で canonical がマージされる |
| プロジェクト指示 | `.claude/CLAUDE.md` | 存在。ただし一部記述が現況とズレる |
| プロジェクト settings | `.claude/settings.json` | 存在。`permissions` / `additionalDirectories` のみ |
| Rules | `~/.claude/rules/*.md` | 20本。`alwaysApply: true` は `horos-hub.md` のみ |
| Skills | `~/.claude/skills/*/SKILL.md` | 82 skill がトップレベルに存在 |
| repo local skills | `.claude/skills/` | 現在は空 |
| repo local contract | `.agents/rules/skill-execution-contract.md` | 存在。explicit skill / CCL 用の hard contract |

## 2. 常時入るもの

### 2.1 常時 instruction

- `~/.claude/CLAUDE.md`
  - HGK OS 本体
  - Advisor Strategy
  - Pinakas / project-index / Compact rules
  - Rules と tool routing の要約

### 2.2 alwaysApply rule

- `~/.claude/rules/horos-hub.md`
  - `alwaysApply: true`
  - 12 Nomoi の俯瞰
  - BRD パターン
  - 深度システム

### 2.3 skill の常時認識

- `~/.claude/skills/` 直下の skill は、セッション開始時に一覧として認識される
  - 根拠: `~/.claude/plans/harmonic-prancing-hanrahan.md`
  - 重要: `SKILL.md` の全文が常時プリロードされるわけではない
  - 公式 docs では skill 本文は必要時に読み込まれる。トップレベルでは主に skill 名 / 説明が discovery 面に載る
  - `disable-model-invocation: true` を frontmatter に入れると、自動選択を止めつつ `/name` では使える

現在のトップレベル skill 数:

- user-global: 82
- repo-local: 0
- auto candidate: 43
- manual-only (`disable-model-invocation: true`): 39

## 3. SessionStart で入るもの

定義元:

- `~/.claude/settings.canonical.json`

実行 hook:

1. `python3 ~/.claude/hooks/sync-settings.py`
   - `settings.canonical.json` の `hooks` / `effortLevel` / `enableAllProjectMcpServers` を
     `~/.claude/settings.json` に上書きマージする
   - `permissions` はローカル保持
2. `python3 ~/.claude/hooks/project-index-start.py`
   - `~/.claude/project-index/{project_key}/project_index.json` を読み、
     前セッション情報を `additionalContext` として注入する
   - 注入内容:
     - 前回 `session_id`
     - `return_ticket_path`
     - `decision_log_path`
     - `transcript_path`
     - `prev_goal`
     - `context_pack_goal`
     - `context_pack_files`
     - `open_questions`
3. `bash ~/.claude/hooks/sync-mcp-servers.sh`
   - 非同期。MCP 同期
   - 直接の文脈注入ではなく環境整備

## 4. 条件付きで入るもの

### 4.1 PreToolUse

- `python3 ~/.claude/hooks/advisor-pretooluse.py`
  - 大きめのコード編集時にのみ `additionalContext`
  - 内容は「Codex に委譲しないか」の soft reminder
  - `.md`, `.toml`, `~/.claude/hooks/`, `~/.claude/skills/` などは除外

### 4.2 PostToolUse

- `python3 ~/.claude/hooks/audit-posttooluse.py`
  - 監査ログと `patterns_{session_id}.json` を更新
  - 主に side effect。通常は user-visible な注入ではない
- `python3 ~/.claude/hooks/pinakas-queue.py`
  - Pinakas 記法を queue 化
  - これも主に side effect

### 4.3 Stop

- `python3 ~/.claude/hooks/stop-l0-precheck.py`
- `python3 ~/.claude/hooks/advisor-delegation-audit.py`
- `python3 ~/.claude/hooks/project-index-stop.py`
- `python3 ~/.claude/hooks/pinakas-remind.py`
  - queue があるときだけ `additionalContext`
  - `/bye` で post を促す
- `bash ~/.claude/hooks/export-transcript.sh`
  - transcript のコピー
  - 文脈注入ではなく永続化

## 5. 参照のみ

### 5.1 repo docs / agents

- `.claude/CLAUDE.md`
  - プロジェクト向けの説明文書
  - 現況説明には有用だが、live behavior の完全な正本ではない
- `.claude/agents/hgk-context.md`
  - subagent 用の condensed context
  - Claude Code 本体への常時注入ではない
- `.agents/rules/skill-execution-contract.md`
  - explicit skill / CCL のときのみ強く効く contract
  - implicit な通常会話では alwaysApply ではない

### 5.2 additionalDirectories

`~/.claude/settings.json`:

- `/home/makaron8426`
- `/home/makaron8426/.claude`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff/2026-04`
- `/home/makaron8426/.gemini`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff`

`.claude/settings.json`:

- `/home/makaron8426/.gemini`

注意:

- `additionalDirectories` は「参照可能領域を増やす」設定であって、
  それ自体が全文常時注入を意味するわけではない
- ただし `~/.claude` や handoff がここにあるため、
  hooks / project-index と組み合わせると実質的に常時参照面になる

## 6. Rules 現況

`~/.claude/rules/`:

- 総数: 20
- `alwaysApply: true`: 1
  - `horos-hub.md`
- `alwaysApply: false`: 19
  - `horos-N01` 〜 `horos-N12`
  - `episteme-*`

実務上の意味:

- 常時重いのは実質 `horos-hub.md` だけ
- 個別 `horos-Nxx` と `episteme-*` は必要文脈で読む前提

## 7. Skills 現況

`~/.claude/skills/` の top-level skill: 82

主な群:

- 36 Poiesis verbs
- `h-*` 系
- `ccl-*` 系
- `boot` / `bye`
- FM 専用
- advisor / browser / template 系

管理観点:

- 認知負荷の制御は 2 層ある
- 1. discovery から完全に外す: `~/.claude/skills/` の外へ移す
- 2. slash 候補は残しつつ auto 選択だけ止める: frontmatter に `disable-model-invocation: true`
- 現在は 36動詞 + hub 動詞を auto candidate とし、それ以外を manual-only に寄せる方針

## 8. ドリフト状況

2026-04-10 時点で確認していた以下のズレは解消済み:

1. `AGENTS.md`
   - `horos-hub` 参照先を `~/.claude/rules/horos-hub.md` に統一
2. `.claude/settings.json`
   - project-local `hooks` を除去し、`permissions` / `additionalDirectories` のみに整理
3. `.claude/CLAUDE.md` / `.claude/README.md` / `.claude/hooks/README.md`
   - hooks 正本と repo-local skills の現況説明を更新
4. `.claude/agents/hgk-context.md`
   - hooks 正本 / runtime settings の所在に合わせて更新

## 9. 管理方針の提案

### A. 常時注入面の正本を 3 つに固定する

- instruction: `~/.claude/CLAUDE.md`
- hooks/runtime: `~/.claude/settings.canonical.json`
- always rule: `~/.claude/rules/horos-hub.md`

### B. project 側は「説明」と「permissions」に寄せる

- `.claude/settings.json` は本来どおり `permissions` / `additionalDirectories` に限定
- repo 側 `hooks` は削除するか、少なくとも deprecated と明記する

### C. skill は 2 層で管理する

- 「slash 候補に残したい」と「モデルに自動選択させたい」は分離する
- slash 候補は残しつつ auto を止めたい skill には `disable-model-invocation: true`
- discovery から完全に外したいときだけ `~/.claude/skills/` の外へ移す

### D. repo 内にこの棚卸しを維持する

- live behavior を変えたら、この文書を更新する
- 特に以下が変わったら必ず追記:
  - `~/.claude/settings.canonical.json`
  - `~/.claude/CLAUDE.md`
  - `~/.claude/rules/horos-hub.md`
  - top-level skill 数

## 10. 次にやるとよい整理

1. repo の説明文書を現況に合わせて修正
2. project `.claude/settings.json` から `hooks` を除去
3. core / manual-only の keep-list を維持
4. `AGENTS.md` の参照先をユーザー全体ルール正本へ揃える
