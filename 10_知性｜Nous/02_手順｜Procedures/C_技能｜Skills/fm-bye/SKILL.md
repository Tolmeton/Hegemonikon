---
name: fm-bye
description: FM workspace-local handoff and ROM workflow for this FileMaker repository. Use when ending an FM session, recording FileMaker progress, creating a durable FM note, or writing the next-action handoff without touching HGK shared memory.
---

# FM Bye

FM セッション終了時の handoff と ROM は、この skill で workspace 内に保存する。

## Source And Destination Rules

- 書き込み先は [`.agents/memory/handoff`](c:\Users\makar\Sync\oikos\02_作業場｜Workspace\A_仕事｜Work\a_ファイルメーカー｜FileMaker\.agents\memory\handoff) と [`.agents/memory/rom`](c:\Users\makar\Sync\oikos\02_作業場｜Workspace\A_仕事｜Work\a_ファイルメーカー｜FileMaker\.agents\memory\rom) のみ
- HGK 側 `30_記憶｜Mneme` に新規 handoff / ROM を書かない
- FM 固有の事実だけを書く
- 未検証事項は `[要確認]` を付ける

## Always Create

各セッション終了時に handoff を 1 件作る。

- ファイル名: `handoff_YYYY-MM-DD_HHmm.md`
- 保存先: `.agents/memory/handoff/`

handoff には最低限、次を含める。

- 主題
- 完了度
- 状態 (`in_progress | verification_complete | blocked`)
- 変更した FM ファイル
- 変更したテーブル / レイアウト / スクリプト
- 使用した Forge プロジェクト
- 次の一手

## Create ROM Only When Durable

次のどれかに当てはまるときだけ ROM を作る。

- 繰り返し使う FM 手順
- Forge 運用上の制約
- FileMaker 固有の落とし穴
- 命名規約や XML ペースト規約
- 次回以降も再利用する判断基準

ROM を作る場合:

- ファイル名: `rom_YYYY-MM-DD_{slug}.md`
- 保存先: `.agents/memory/rom/`
- handoff から ROM 名を参照する

## Handoff Structure

```yaml
session_handoff:
  version: "2.0"
  timestamp: "{ISO8601}"
  workspace: "fm-local"
  location: ".agents/memory/handoff"
  situation:
    primary_task: "{FM 作業の主題}"
    completion: {0-100}
    status: "in_progress | verification_complete | blocked"
  fm_context:
    files_modified: []
    tables_affected: []
    layouts_affected: []
    scripts_modified: []
    forge_projects: []
```
```
{本文要約}
```

## Final Check

- 保存先が workspace 内か
- FM 固有の変更点が明記されているか
- 次の一手が単独で読んでも実行可能か
- ROM を作るなら、handoff から参照できるか
