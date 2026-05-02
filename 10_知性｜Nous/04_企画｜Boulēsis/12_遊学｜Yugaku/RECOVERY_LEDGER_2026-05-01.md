# Recovery Ledger 2026-05-01

## Purpose

`main` に統合されていない Yugaku / Oblivion / paper 成果を、復元・採用・保管・除外へ分けるための台帳。

この台帳は復元操作そのものではない。`checkout`、`restore`、`merge`、削除は実行していない。

## Current Grounding

| 面 | SOURCE | 観測 |
|---|---|---|
| root repo | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon` | current branch は `main`、current HEAD は `6269b65922eeaeecf31abb366b962eb987e292b8` |
| root stash | `refs/stash = c3b2841573ddf512557315c53c2536c33f4434b6` | stash message は `On main-clean: workspace-boot-2 claude-sync-rules` |
| stash base parent | `refs/stash^1 = 46eb00893a0ca20b5bcc87bba1cc944f993aec38` | Yugaku の旧 tracked 面がここから到達可能 |
| integration backup | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.git/worktree-backups/main-only-2026-05-01T2015+0900/hgk-integration/cached.patch` | `Current main is not a complete HGK source surface` と明記。`main` への merge は未実行 |
| nested Oblivion | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion` | current nested branch は `publish/oblivion-theory`。nested `main` との差分は 3542 path |

## Main Problem Statement

`main` は HGK / Yugaku の完全な source surface ではない。成果は少なくとも次の 4 面に割れている。

| 面 | 状態 | リスク |
|---|---|---|
| `refs/stash` | 旧 tracked 成果が reachable | branch ではないため、通常の履歴探索から見落とされる |
| live untracked | 現在の作業木に復帰済みだが未追跡 | `main` に入っていないため、次の整理で再び落ちる |
| worktree backup | 統合判断面が `.git/worktree-backups` に残る | backup surface であり、通常の project file ではない |
| nested Oblivion repo | `publish/oblivion-theory` と nested `main` が乖離 | root `main` と nested repo の source-of-truth が分裂する |

## Stash Surface

SOURCE command:

```bash
git -C /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon \
  -c core.quotePath=false diff --name-only --diff-filter=A HEAD refs/stash -- \
  '10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku'
```

Observed count:

| Diff | Count |
|---|---:|
| `HEAD -> refs/stash` added Yugaku paths | 206 |
| `HEAD -> refs/stash` deleted Yugaku paths | 97 |

Top-level distribution of added Yugaku paths in `refs/stash`:

| Surface | Count |
|---|---:|
| `03_忘却論｜Oblivion/experiments` | 52 |
| `03_忘却論｜Oblivion/drafts` | 48 |
| `03_忘却論｜Oblivion/calculations` | 28 |
| `01_研究論文｜Papers/figures` | 26 |
| `03_忘却論｜Oblivion/plans` | 16 |
| `01_研究論文｜Papers/_archive` | 9 |

High-signal `01_研究論文｜Papers` paths present in `refs/stash` but absent from `HEAD`:

| Path | Recovery class |
|---|---|
| `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v03.md` | `restore-candidate` |
| `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v05.md` | `compare-with-live` |
| `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMに身体はあるか_統合草稿.md` | `restore-candidate` |
| `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMは心を持つか_英語版草稿.md` | `restore-candidate` |
| `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/T9自己診断反論マッピング.md` | `restore-candidate` |
| `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/現況台帳.md` | `restore-candidate` |

## FEP v05 Current State

FEP v05 is no longer simply missing from disk. Current live state has two 453-line bodies: one at the expected root paper path and one under `_workspaces/FEPの操作的分解型_v05`. Both are untracked, and they differ by 26 changed lines. The root-level companion artifacts are modified tracked files; workspace companion copies are untracked.

| Artifact | Git state | Lines | Note |
|---|---|---:|---|
| `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v05.md` | untracked | 453 | root live body; 8-type/Scale provisional variant |
| `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/_workspaces/FEPの操作的分解型_v05/FEPの操作的分解型_v05.md` | untracked | 453 | workspace live body; 9-type/D9 strong Scale variant |
| `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v05.meta.md` | modified tracked | — | root companion artifact |
| `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEP分解型_blind_participant_prompt.md` | modified tracked | — | root companion artifact |
| `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEP分解型_blind_evaluator_rubric.md` | modified tracked | — | root companion artifact |
| `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEP分解型_blind_execution_log_2026-05-01.md` | modified tracked | — | root companion artifact |

Live FEP v05 body hash:

```text
cd8bab46de43091716985aaada667e405d4f73c7be775de4ce9c1713fd1acdbe  /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEPの操作的分解型_v05.md
96e9d39e3ed9f382b60f1632ac0490a8ab1a7a764ce33536aaf0437c10618a33  /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/_workspaces/FEPの操作的分解型_v05/FEPの操作的分解型_v05.md
```

Immediate FEP action is not blind restore-from-stash. It is `compare-with-live`: compare `refs/stash` old body, root live body, and workspace live body, then decide which variant and path should become canonical.

## Worktree Backup Surface

SOURCE: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.git/worktree-backups/main-only-2026-05-01T2015+0900/hgk-integration/cached.patch`

Key claims preserved there:

| Claim | Recovery meaning |
|---|---|
| `main` tracks 37 files at the time of inventory | `main` had already been recognized as incomplete |
| `codex/oblivion-full-separation-2026-04-29` tracks 54,776 files | integration base candidate exists outside current `main` |
| `master_only=1298`, `full_only=32044`, `common=22732` | bulk merge is unsafe; bucket audit is required |
| `No merge into main has been performed` | the integration decision was documented but not applied |

Recovery class: `decision-surface-restore`.

This file should be promoted into the project surface before any merge/repoint decision, because it records why current `main` is insufficient.

## Nested Oblivion Surface

SOURCE command:

```bash
git -C /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion \
  diff --name-only main publish/oblivion-theory
```

Observed:

| Field | Value |
|---|---|
| current nested branch | `publish/oblivion-theory` |
| nested `main` | `d62f7fd7046dd544c61495dab05ccd163c1f2413` |
| nested `publish/oblivion-theory` | `9ce97d5936b03bc5243df8dbbb5a5a98fdf0d401` |
| path diff count | 3542 |

Recovery class: `nested-main-reconcile`.

Do not treat nested `main` as the canonical Oblivion surface until this delta is bucketed. Current live nested branch already points to `publish/oblivion-theory`.

## Session Subagent Findings To Recheck

These were obtained by the 2026-05-01 subagent scan in this thread. They are high-signal, but each item should be rechecked from disk before write/merge action.

| Class | Candidate | Proposed first action |
|---|---|---|
| `runtime-missing` | `ccl-pl` bridge-free BF-C artifacts | locate exact paths, compare with current root, bucket `restore/archive/exclude` |
| `hyphē-missing` | `belief_lineage.md` | verify expected canonical path and whether it belongs under Hyphē or Mekhane |
| `hyphē-missing` | `hyphe_benchmark_rejection_ledger.md` | verify expected canonical path and restore class |
| `lethe-untracked` | OP-I-7 sweep / adaptive router artifacts | verify current untracked state, then decide tracking boundary |
| `blind-cli-untracked` | `containers/blind-cli/*` | decide whether this is Yugaku infra canon or experiment-only |

## Recovery Buckets

| Bucket | Meaning | Current candidates |
|---|---|---|
| `restore-candidate` | likely should become tracked project source | FEP v03, LLM integrated drafts, T9 map, current status ledger, many Oblivion drafts/plans |
| `compare-with-live` | same path or same concept exists live; do not overwrite blindly | FEP v05 body, blind protocol artifacts |
| `decision-surface-restore` | meta/inventory file needed before action | branch integration inventory in worktree backup |
| `nested-main-reconcile` | nested repo branch mismatch needs its own reconciliation | `03_忘却論｜Oblivion` publish vs main |
| `archive-reference` | useful prior state but not necessarily canon | old body drafts, figures, backup workspaces |
| `exclude` | likely not HGK canon | `.codex_tmp`, external checkouts, generated build material |

## Generated Follow-up Artifacts

| Artifact | Purpose |
|---|---|
| `/tmp/hgk-recover-top/20260501T224916+0900` | read-only extraction mirror for `refs/stash^1` Yugaku surface |
| `/tmp/hgk-recover-oblivion/20260501T224916+0900` | read-only extraction mirror for nested `publish/oblivion-theory` surface |
| `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/RECOVERY_BUCKETS_2026-05-01.tsv` | bucket ledger generated from stash, working tree, and nested publish/main delta |
| `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/FEP_V05_COMPARE_2026-05-01.md` | FEP v05 old stash body vs live workspace body comparison memo |

## Default Next Step

1. Decide canonical placement for FEP v05: root paper path or `_workspaces/FEPの操作的分解型_v05`.
2. If root paper path is chosen, promote the live workspace body and companion artifacts without overwriting from old stash.
3. Use `RECOVERY_BUCKETS_2026-05-01.tsv` to process `restore-candidate`, `compare-with-live`, `nested-main-reconcile`, and `archive-reference` buckets separately.
4. Reconcile nested Oblivion `publish/oblivion-theory` vs `main` before treating nested `main` as canonical.

## Non-Action

No recovery merge has been performed.

No file has been deleted.

No tracked file has been overwritten.
