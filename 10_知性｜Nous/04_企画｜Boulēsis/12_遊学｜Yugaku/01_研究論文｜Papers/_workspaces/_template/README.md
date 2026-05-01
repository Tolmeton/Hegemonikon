# Workspace — {{PAPER_TITLE}}

## 正本

| 種別 | Path | 状態 |
|:---|:---|:---|
| 本体 | `{{ABS_BODY_PATH}}` | {{BODY_STATUS}} |
| meta | `{{ABS_META_PATH}}` | {{META_STATUS}} |
| companion / source workspace | `{{ABS_COMPANION_OR_SOURCE_PATH}}` | {{COMPANION_STATUS}} |

## 趣旨

この workspace は、`{{PAPER_TITLE}}` の改稿、翻訳、投稿準備、外部レビュー、整合性監査、再現性 bundle を本体ファイルから分離して保持する。正本は本体と `.meta.md` であり、この workspace は証跡と変換面である。

## 構成

| Surface | 役割 |
|:---|:---|
| `STATUS.md` | 現在 phase、SOURCE inventory、未解決事項、次の一手 |
| `glossary.md` | 論文固有の術語・記号・訳語固定面 |
| `style_guide.md` | 論文固有の読者、文体、禁止される弱化 |
| `integrity_notes.md` | forward reference、依存、ドリフト、公開前 check |
| `decisions/` | Tolmetes 判断、採用・棄却・保留 |
| `reviews/` | `/exe`、外部レビュー、post-fix 監査 |
| `reproducibility/` | 実験、データ、script、MANIFEST、再現手順 |
| `source_snapshots/` | 外部 SOURCE / PDF / 実験出力の固定 snapshot |
| `chapters/` | 章分割翻訳・分割改稿が必要な場合の作業面 |
| `outputs/` | 投稿版、preprint 版、PDF / DOCX / TeX |
| `internal/` | 非公開 scratch、作業中断片、提出しない派生物 |
| `changelog.md` | workspace 変更履歴 |

## 初期 phase

{{INITIAL_PHASE}}

## 起票時チェック

- `{{ABS_BODY_PATH}}` が存在するか確認する。
- `{{ABS_META_PATH}}` が存在するか確認する。なければ本体編集前に作る。
- 本体と meta の主張核が一致しているか確認する。
- 外部 source / NotebookLM / AI 合成は TAINT として扱い、本文反映前に SOURCE 昇格する。
