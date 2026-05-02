---
name: fm-boot
description: FM workspace-local boot workflow for this FileMaker repository. Use when starting an FM session, checking current FileMaker workspace state, or before FM work that needs project status, recent changes, Syncthing conflicts, Forge MCP readiness, and workspace-local memory context.
---

# FM Boot

FM セッション開始時の確認は、この skill を使って workspace 内だけで完結させる。

## Source Rules

- 読む対象はこのワークスペース配下だけに限定する
- handoff は [`.agents/memory/handoff`](c:\Users\makar\Sync\oikos\02_作業場｜Workspace\A_仕事｜Work\a_ファイルメーカー｜FileMaker\.agents\memory\handoff) を参照する
- ROM は [`.agents/memory/rom`](c:\Users\makar\Sync\oikos\02_作業場｜Workspace\A_仕事｜Work\a_ファイルメーカー｜FileMaker\.agents\memory\rom) を参照する
- Forge 定義は [`.mcp.json`](c:\Users\makar\Sync\oikos\02_作業場｜Workspace\A_仕事｜Work\a_ファイルメーカー｜FileMaker\.mcp.json) を正本とする
- HGK 側 `30_記憶｜Mneme` や共通 `/boot` は読まない

## Check Order

1. ワークスペース直下の [AGENTS.md](c:\Users\makar\Sync\oikos\02_作業場｜Workspace\A_仕事｜Work\a_ファイルメーカー｜FileMaker\AGENTS.md) を確認する
2. `01_MICKS/` を見て案件一覧と直近変更を把握する
3. `*.fmp12` の更新日時とサイズを確認する
4. Syncthing 競合 (`*.sync-conflict-*`, `~syncthing~*`) を確認する
5. `.mcp.json` の `forge` 定義と `00_ツール｜Tools/forge` の配置を確認する
6. `.agents/memory/handoff` の最新 3 件を要約する
7. `.agents/memory/rom` の最新 3 件を要約する
8. FM 固有ルールを短く再掲する

## Report Requirements

- 案件一覧
- 直近更新ファイル
- 競合の有無
- Forge の利用可否
- 最新 handoff / ROM の要約
- 作業前に守るべき FM ルール

## Output Template

```text
🔧 FM BOOT COMPLETE
📁 案件: {案件名一覧}
🕒 直近変更: {要約}
⚠️ 競合: {なし / 件数}
🛠️ Forge: {利用可 / 要確認}
📝 Handoff: {最新要約}
🧠 ROM: {最新要約}
→ 次に着手できる FM 作業
```

## FM Rules Reminder

- Inspector で確認した実名だけを使う
- DDR XML は読み取り専用
- Excel 解析・XML 生成・マッピングは Forge MCP を使う
- 破壊的操作の前には現況を保存する
