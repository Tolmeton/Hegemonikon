# Decision — FEP v05 Source Gap

Date: 2026-05-01

## SOURCE

Meta anchor:
`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v05.meta.md`

Main path referenced by meta:
`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v05.md`

Found candidate:
`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.claude/worktrees/serene-clarke/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v05.md`

Observed facts:

| Item | Value |
|:---|:---|
| line count | 363 |
| sha256 | `49d921c8a7f9287d48bb064353fb88782e1cb8bc38af7a6ccae8e850e3ba3345` |
| visible draft state | 2026-03-11 Draft v0.5 English |
| main `Papers/` placement | absent |

## Decision

The source gap is not "file nowhere"; it is "body candidate exists only in a `.claude/worktrees/serene-clarke` worktree and is not promoted into the main Yugaku `Papers/` surface."

Do not copy or promote automatically. The found candidate still speaks in the old 8 decomposition / 24 operation / two-layer filter frame, while the live meta describes the 2026-04-29 48-frame B+C rewrite. Promotion requires a prior drift audit against `FEPの操作的分解型_v05.meta.md` and `FEPの操作的分解型_改稿spine.md`.

## Rejected

| Option | Reason |
|:---|:---|
| Copy worktree body into main immediately | It may resurrect stale 24-operation claims as if they were current |
| Treat spine as body without decision | It hides that the meta references a missing body path |
| Keep "not found" status | HGK root search found a concrete candidate |

## Next

1. Audit worktree body vs current meta/spine for stale 24-operation claims.
2. Decide whether to promote the worktree body, rebuild a v05 body from spine, or mark the worktree file as archival only.
3. Only after that, freeze blind protocol and reproducibility artifacts.
