# STATUS — FEPの操作的分解型 v05

更新日: 2026-05-01

## SOURCE Inventory

| 種別 | Path | 状態 |
|:---|:---|:---|
| meta | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v05.meta.md` | SOURCE。117 行。全体読取済み |
| 本体候補 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.claude/worktrees/serene-clarke/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v05.md` | HGK root 探索で発見。363 行。SHA256 `49d921c8a7f9287d48bb064353fb88782e1cb8bc38af7a6ccae8e850e3ba3345` |
| 改稿 spine | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_改稿spine.md` | SOURCE 入口 |
| blind prompt | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEP分解型_blind_participant_prompt.md` | SOURCE 入口 |
| blind rubric | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEP分解型_blind_evaluator_rubric.md` | SOURCE 入口 |
| blind log | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEP分解型_blind_execution_log_2026-05-01.md` | SOURCE 入口。external CLI 実行失敗の記録 |

## 現在地

本稿は、旧 24 operation proof ではなく `36 Poiesis + 12 H-series = 48` の 48-frame を中心に、FEP から CE 層の座標・象限・slot 数を支持し、語名・CCL 呼称を CI 層として分離する方向へ再編中。

## 未解決

| 項目 | 理由 |
|:---|:---|
| 本体 `FEPの操作的分解型_v05.md` の main workspace 配置 | worktree 側では発見済みだが、main `Papers/` 直下には未配置 |
| blind response 未取得 | 2026-05-01 の外部 CLI 実行は Gemini capacity exhaustion / Claude auth failure で未完 |
| C3 admissibility lemma | two-layer filter の降格後の正確な定式化が未固定 |
| Scale の扱い | L1 座標として内部導出、独立第9型としては仮止めという二重状態を本文で誤読なく出す必要がある |

## 次の一手

1. worktree 側の `FEPの操作的分解型_v05.md` を main `Papers/` 直下へ昇格するか、`FEPの操作的分解型_改稿spine.md` を暫定作業正本にするか決める。
2. 昇格する場合は、worktree 本体と meta / 改稿 spine の 48-frame 更新差分を先に監査する。
3. blind protocol は再試前に prompt / rubric / contamination gate を `reproducibility/` に固定する。
