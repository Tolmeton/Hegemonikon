# Integrity Notes — FEPの操作的分解型 v05

Meta:
`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v05.meta.md`

## Source Gap

`FEPの操作的分解型_v05.meta.md` は本体として次を参照している。

`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v05.md`

2026-05-01 の HGK root 探索で、次の worktree 側候補を発見した。

`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.claude/worktrees/serene-clarke/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v05.md`

観測: 363 行。SHA256 `49d921c8a7f9287d48bb064353fb88782e1cb8bc38af7a6ccae8e850e3ba3345`。冒頭は 2026-03-11 Draft v0.5 の英語稿で、24 operation completeness / two-layer filter を主張している。これは current meta の 2026-04-29 48-frame B+C 改稿状態より古い可能性が高い。

判断: source gap は「所在不明」から「worktree 旧稿候補あり / main 未昇格」へ状態遷移。main へ機械的コピーする前に、meta §M1-§M7 と改稿 spine との差分監査が必要。

## Integrity Ledger

| Anchor | Target | Check Needed |
|:---|:---|:---|
| meta §M1 | 改稿 spine | F / G が 48-frame rewrite と一致しているか |
| C1 | 本文 §3 / §4 | FEP は語名ではなく座標層を導出する、という境界が保たれているか |
| C2 | H-series 説明 | `S∩A` 中動態 core として読めるか |
| C3 | two-layer filter | 完全性証明ではなく admissibility lemma として定式化されているか |
| C4 | CE/CI defense | 48 slots の強主張と語名非導出が両立しているか |
| blind protocol | prompt / rubric / log | 未実行結果を validation として扱っていないか |
| worktree body candidate | meta / 改稿 spine | 旧 24 operation proof が 48-frame 改稿後の正本として使えるか |

## Open Checks

- worktree 旧稿候補を main に昇格するか、spine を暫定正本にするかを決める。
- `Scale` の扱いが meta と本文で一致しているか。
- external CLI 失敗ログを再試 plan に接続する。
- `FEP分解型_blind_participant_prompt.md` と `FEP分解型_blind_evaluator_rubric.md` の contamination gate を再確認する。
