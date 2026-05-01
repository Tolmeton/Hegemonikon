# FEP v05 Compare Memo 2026-05-01

## Purpose

`refs/stash` に残っていた旧 FEP v05、現在の root live body、現在の workspace live body を比較し、canonical body の判断面を固定する。

このメモは比較結果であり、復元・上書き・merge は行っていない。

## Compared Sources

| Side | Path | Lines | SHA256 | Status |
|---|---|---:|---|---|
| stash old body | `/tmp/hgk-recover-top/20260501T224916+0900/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v05.md` | 363 | `49d921c8a7f9287d48bb064353fb88782e1cb8bc38af7a6ccae8e850e3ba3345` | extracted from `refs/stash^1` mirror |
| root live body | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v05.md` | 453 | `cd8bab46de43091716985aaada667e405d4f73c7be775de4ce9c1713fd1acdbe` | live untracked root paper path |
| workspace live body | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/_workspaces/FEPの操作的分解型_v05/FEPの操作的分解型_v05.md` | 453 | `96e9d39e3ed9f382b60f1632ac0490a8ab1a7a764ce33536aaf0437c10618a33` | live untracked workspace body |

Diff shortstats:

```text
stash old body -> root live body:      1 file changed, 276 insertions(+), 186 deletions(-)
stash old body -> workspace live body: 1 file changed, 276 insertions(+), 186 deletions(-)
root live body -> workspace live body: 1 file changed, 26 insertions(+), 26 deletions(-)
```

## Direct Observations

| Feature | Stash old body | Root live body | Workspace live body |
|---|---|---|---|
| title | English FEP taxonomy title | Japanese FEP coordinate-derivation title | same title |
| date / draft | `2026-03-11 (Draft v0.5)` | `2026-04-29 (草稿 v0.7 / 48-frame B+C 改稿)` | same date |
| core frame | 8 decomposition types -> two-layer filter -> 24 operations | 8 stable types + Scale provisional -> CE/CI separation -> 48-frame | 9 types with D9 Scale strong derivation -> CE/CI separation -> 48-frame |
| blind result | old n=1 blind validation is used as evidence | old n=1 result is retained as preliminary; 48-frame protocol is future/retry protocol | same protocol, but pass/fail includes Basis |
| operation count | `6 × 4 = 24 cognitive operations` | `36 Poiesis + 12 H-series = 48 認知操作` | same 48-frame count |
| two-layer filter | completeness-generating central proof | local admissibility lemma for direct/mediated coordinate coupling | same role |
| Scale | coordinate row via `D7+D9` | coordinate support retained; independent D9 is provisional | D9 Scale decomposition treated as strong independent decomposition type |
| CE/CI distinction | absent as central defense | explicit methodological core | explicit methodological core |

## Current Git State Around FEP

| Path state | Meaning |
|---|---|
| `?? .../Papers/FEPの操作的分解型_v05.md` | root live body exists but is not tracked |
| `?? .../Papers/_workspaces/FEPの操作的分解型_v05/FEPの操作的分解型_v05.md` | workspace live body exists but is not tracked |
| `M  .../Papers/FEPの操作的分解型_v05.meta.md` | root companion artifact is tracked and modified |
| `M  .../Papers/FEPの操作的分解型_改稿spine.md` | root companion artifact is tracked and modified |
| `M  .../Papers/FEP分解型_blind_*.md` | root blind protocol artifacts are tracked and modified |
| `?? .../Papers/_workspaces/FEPの操作的分解型_v05/*.md` | workspace companion copies are untracked |

## Judgment

[確信] The stash old body is not the current intellectual draft. It is an archive/reference source for the old 24-operation proof line.

[推定] The live bodies supersede the stash body. The real current decision is not stash vs live, but root live variant vs workspace live variant.

[主観] The root live body is more conservative: Scale remains provisional as an independent ninth decomposition type. The workspace live body is stronger: Scale is D9 and part of the 9-type classification. Given Yugaku's anti-retreat rule, the stronger workspace variant is likely the better canonical candidate, but it needs a SOURCE-backed check that D9 is defensible before promotion.

## Proposed Recovery Classification

| Artifact | Bucket | Decision |
|---|---|---|
| stash old body | `archive-reference` | keep as old v0.5 / 24-operation source |
| root live body | `compare-with-live` | current root placement candidate, but weaker Scale claim |
| workspace live body | `restore-candidate` | strongest current body candidate; verify D9 before making canonical |
| root companion artifacts | `compare-with-live` | keep tracked, reconcile with chosen body variant |
| workspace companions | `restore-candidate` | likely current companion set |

## Open Decision

Canonical placement and claim strength are still undecided.

Option A: root path canonical, root live body content retained. This preserves the expected paper path and the more cautious Scale stance.

Option B: root path canonical, workspace live body content promoted into root path. This preserves expected path while adopting the stronger D9 Scale stance.

Option C: workspace path canonical. This preserves workspace isolation, but conflicts with existing root-level paper path expectations.

Default recommendation: Option B after a focused D9 check against Friston 2008 and scale-free active inference. Do not overwrite anything before that check.
