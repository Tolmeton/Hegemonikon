# D9 Scale Source Check 2026-05-01

## Purpose

FEP v05 の Scale を、暫定候補ではなく `D9 Scale decomposition` として扱えるかを、到達可能な一次 SOURCE に基づいて確認する。

## SOURCE

| Source | Relevant observation |
|---|---|
| Friston, K. (2008), `Hierarchical Models in the Brain`, PLoS Computational Biology, DOI `10.1371/journal.pcbi.1000211` | The abstract says the model comprises hidden layers of state-space or dynamic causal models, with the output of one providing input to another; the resulting hierarchy furnishes models of arbitrary complexity. The methods section states that hierarchies induce empirical priors and structural constraints. Later, the paper says hierarchical dynamic models have attributes including the number of levels or depth. |
| Friston et al. (2024), `From pixels to planning: scale-free active inference`, arXiv `2407.20292` | The abstract explicitly describes deep or hierarchical forms using the renormalisation group, and says the ensuing scale-invariant models can learn compositionality over space and time. |
| Local blind protocol artifacts | `FEP分解型_blind_evaluator_rubric.md` records D9 as scale / hierarchy, and the 2026-05-01 Gemini blind evaluation records D9 as recovered. |

## Interpretation

[SOURCE] The primary literature supports hierarchy, depth, and scale-invariant / scale-free active inference as internal FEP / active-inference structures.

[INFERENCE] The label `D9 Scale decomposition` is not a term directly used by Friston 2008 or Friston et al. 2024. It is this manuscript's classification label for the Micro / Macro projection of hierarchical and scale-free generative modelling.

[JUDGMENT] It is defensible to promote Scale from "weak external analogy" or "mere coordinate hint" to an FEP-internal decomposition class, provided the manuscript states that `D9` is a classification label introduced here, not a quoted source term.

## Decision

Use the workspace live body as the canonical intellectual variant:

`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/_workspaces/FEPの操作的分解型_v05/FEPの操作的分解型_v05.md`

Promote it to the expected root paper path:

`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v05.md`

## Residual Risk

D9 is justified as an internal scale/hierarchy class, but the exact construction distance `d=3` remains a manuscript-local taxonomy choice. It should be kept falsifiable by the blind protocol and by future related-work checks.
