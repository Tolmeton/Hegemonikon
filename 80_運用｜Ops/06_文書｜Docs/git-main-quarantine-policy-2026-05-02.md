# Git Main Quarantine Policy 2026-05-02

## Scope

This policy locks down the unsafe untracked surfaces found while converging the repository to main-first operation.

SOURCE:

```bash
git status --porcelain=v1 --untracked-files=all
git ls-files --others --exclude-standard
rg -n -i 'old account identifiers' .
```

READ ledger:

```text
/tmp/hgk-untracked-audit-20260502/untracked_classification.tsv
/tmp/hgk-untracked-audit-20260502/read_evidence.tsv
/tmp/hgk-untracked-audit-20260502/summary.json
```

Observed scan:

| class | count |
|---|---:|
| untracked entries | 12,397 |
| read evidence rows | 10,904 |
| keep candidates before narrowing | 1,520 |
| deep review | 9,417 |
| generated/dependency | 702 |
| old/duplicate | 621 |
| sensitive/quarantine | 137 |

## Hard Quarantine

Do not stage these surfaces directly into main:

| surface | reason |
|---|---|
| raw handoff/session/chat exports | full dialogue, absolute paths, identity/account traces |
| `.env`, `.secrets`, credential-shaped files | live secrets or secret-adjacent config |
| `openclaude`, `openclaw` source trees | external source imports; require separate repo/submodule/vendor decision |
| LanceDB, FAISS, sqlite, model weights | generated stores and large binary artifacts |
| promptfoo logs, hook traces, runtime audit logs | generated and often private |
| old/sync-conflict/backup snapshots | duplicate or stale material |
| private publication workspaces and measurement raw data | public strategy, raw trace, identity-sensitive material |

## Current Old Account Residue

Tracked `HEAD` has no old account identifier hit in the current scan.

One untracked raw handoff JSONL still contains an old account reference:

```text
30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff/2026-05/chat_export_2026-05-02_1047_lemma_a6_v02_6stage.jsonl
```

It is now covered by the raw handoff ignore rules and must not be staged. Redaction or deletion requires an explicit separate operation because this is raw untracked material.

## Safe Next Stage Candidates

Stage only narrow, reviewed slices:

| surface | current action |
|---|---|
| `20_機構｜Mekhane/_src｜ソースコード/mekhane/fep/krisis_helmholtz.py` | keep candidate |
| `20_機構｜Mekhane/_src｜ソースコード/mekhane/fep/tests/test_krisis_helmholtz.py` | keep candidate |
| `20_機構｜Mekhane/_src｜ソースコード/mekhane/mcp/aisthetikon_mcp_server.py` | keep candidate |
| `20_機構｜Mekhane/_src｜ソースコード/mekhane/mcp/dianoetikon_mcp_server.py` | keep candidate |
| `20_機構｜Mekhane/_src｜ソースコード/mekhane/mcp/poietikon_mcp_server.py` | keep candidate |
| selected `hooks/` run helpers | keep candidate after line review |
| selected `80_運用｜Ops` docs/scripts | keep candidate after line review |
| selected `60_実験｜Peira` source scripts | keep candidate; generated outputs stay ignored |

## Stop Conditions

Stop before staging if any of these appear:

| condition | response |
|---|---|
| `git ls-files -d` nonzero | restore tracked deletions before continuing |
| old account identifier appears in staged diff | unstage and redact/quarantine |
| secret or token value appears in staged diff | unstage and quarantine |
| generated output appears in staged diff | unstage and update ignore rules |
| external source tree appears in staged diff | unstage and decide repo/submodule/vendor policy |
