# Paper Workspaces

このディレクトリは、論文本体の横に置くと混ざりやすい作業証跡を、論文ごとに分離するための workspace 面である。

## 運用単位

| Workspace | Anchor | 用途 |
|:---|:---|:---|
| `_template/` | template | 新規 paper workspace 起票用の標準骨格 |
| `LLMは心を持つか_v0.7/` | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMは心を持つか_v0.7_日本語.md` | 本体改稿、英訳、投稿、整合性監査 |
| `FEPの操作的分解型_v05/` | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v05.meta.md` | 48-frame 改稿、CE/CI 防衛、blind protocol、検証証跡 |

## 標準構成

| Surface | 役割 |
|:---|:---|
| `README.md` | workspace の趣旨、正本、構成、使い方 |
| `STATUS.md` | 現在 phase、SOURCE inventory、未解決事項、次の一手 |
| `glossary.md` | 論文固有の術語・記号・訳語の固定面 |
| `style_guide.md` | 論文固有の読者、文体、禁止される弱化 |
| `integrity_notes.md` | forward reference、依存、ドリフト、公開前 open check |
| `decisions/` | Tolmetes 判断、棄却案、保留事項 |
| `reviews/` | `/exe`、外部レビュー、post-fix 監査 |
| `reproducibility/` | 実験、データ、script、MANIFEST、再現手順 |
| `outputs/` | 投稿版、preprint 版、PDF、DOCX、TeX |
| `internal/` | 非公開 scratch、作業中断片、提出しない内部物 |
| `source_snapshots/` | 外部 SOURCE / PDF / 実験出力の固定 snapshot |
| `chapters/` | 章分割翻訳・分割改稿が必要な場合の作業面 |
| `changelog.md` | workspace 内の変更履歴 |

## 境界

- 論文本体と `.meta.md` は `Papers/` 直下を正本とする。
- workspace は正本を置き換えない。レビュー、変換、公開、再現性、意思決定の証跡を保持する。
- `README.md` と `STATUS.md` は状態正本として扱う。古くなった場合は、本文改稿より先に更新する。
- NotebookLM、外部レビュー、AI 合成は TAINT として記録し、ローカル本文または原典で SOURCE 昇格してから本文へ反映する。
- 新規起票時は `_template/` を複製し、placeholder を実 path に置換してから作業を始める。
