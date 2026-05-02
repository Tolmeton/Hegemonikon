# Git main untracked classification 2026-05-02

Scope: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane`

Purpose: prevent another broad `git add .` event while converging the repo to main-first operation.

## Source

Commands run from repo root:

```bash
git status --short --branch --untracked-files=no
git ls-files -d | wc -l
find '20_機構｜Mekhane' -type f | wc -l
du -sh '20_機構｜Mekhane'
find '20_機構｜Mekhane' -name .git -type d -prune -print
git status --short --untracked-files=all -- '20_機構｜Mekhane'
rg -n -i --hidden --glob '!**/node_modules/**' --glob '!**/dist/**' --glob '!**/target/**' --glob '!**/__pycache__/**' --glob '!**/.pytest_cache/**' --glob '!**/.git/**' \
  '<old-github-id>|<old-gmail>|client_secret|api[_-]?key|access[_-]?token|refresh[_-]?token|password|oauth|OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY' \
  '20_機構｜Mekhane'
```

Observed:

| item | observed value |
|---|---:|
| tracked deletions after repair | 0 |
| staged files after repair | 0 |
| files under Mekhane | 61597 |
| Mekhane size | 797M |
| Git status entries under Mekhane | 8793 |
| files already tracked under Mekhane | 1977 |
| nested `.git` dirs under Mekhane | 0 |

## Classification

### A. Candidate for main, after narrow staging

These look like HGK-owned source or documentation. They still need per-slice secret scan before commit.

| path family | reason | default action |
|---|---|---|
| `20_機構｜Mekhane/00_概要｜Overview` through `20_機構｜Mekhane/17_協調｜Synergeia` | surface docs for Mekhane domains | commit as docs slice |
| `20_機構｜Mekhane/H_混合｜Mixins` | surface docs | commit as docs slice |
| `20_機構｜Mekhane/_src｜ソースコード/hermeneus` | HGK CCL/Hermeneus implementation | commit as isolated source slice after scan |
| `20_機構｜Mekhane/_src｜ソースコード/hgk` | HGK app/source, but includes build artifacts | commit source only; exclude `node_modules`, `dist`, `src-tauri/target` |
| `20_機構｜Mekhane/_src｜ソースコード/mekhane` | HGK machinery package | commit by module, not whole package |
| `20_機構｜Mekhane/_src｜ソースコード/pepsis` | HGK Pepsis source | commit as isolated source slice after scan |
| `20_機構｜Mekhane/_src｜ソースコード/synergeia` | HGK Synergeia source and rules | commit source only; inspect JSON state files first |

### B. External or vendor-like source

These should not be folded directly into Hegemonikon main without a separate decision.

| path family | observed scale | default action |
|---|---:|---|
| `20_機構｜Mekhane/_src｜ソースコード/openclaw` | largest untracked family; thousands of files | keep out of main or convert to separate repo/submodule/vendor policy |
| `20_機構｜Mekhane/_src｜ソースコード/openclaude` | large external source with bundled output/deps | keep out of main or convert to separate repo/submodule/vendor policy |

### C. Generated, dependency, cache, or runtime state

These should not be committed to main.

| pattern | reason |
|---|---|
| `**/node_modules/**` | dependency install output |
| `**/dist/**` | build output |
| `**/target/**` | Rust build output |
| `**/__pycache__/**` | Python bytecode cache |
| `**/.pytest_cache/**`, `**/.ruff_cache/**`, `**/.venv/**` | local tool/runtime state |
| `**/*.sqlite`, `**/*.db` | runtime databases |
| `20_機構｜Mekhane/_src｜ソースコード/data/quiz_log.json` | runtime data |
| `20_機構｜Mekhane/_src｜ソースコード/contexts.txt` | generated context dump; includes sensitive-code excerpts |
| root-level `fix_*.py`, `final_ruff_fix*.py`, `refactor_exceptions.py`, `narrow_exceptions.py`, `check_loggers.py`, `gather_contexts.py` | one-off repair/scanning scripts; review before keeping |

### D. Sensitive or account-risk zones

These are hard stop zones. Do not commit until line-level review passes.

| path or signal | why it is risky |
|---|---|
| `20_機構｜Mekhane/_src｜ソースコード/mekhane/ochema/scripts/ls_oauth.py` | prior push protection flagged this area; OAuth/token handling |
| `20_機構｜Mekhane/_src｜ソースコード/contexts.txt` | contains excerpts around OAuth/token handling |
| `20_機構｜Mekhane/_src｜ソースコード/refactor_exceptions.py` and `narrow_exceptions.py` | explicitly reference `ls_oauth.py` |
| `20_機構｜Mekhane/_src｜ソースコード/mekhane/ochema/token_vault.py` and `vault_setup.py` | OAuth client/secret/refresh-token handling code |
| any actual old GitHub ID or old Gmail hit | must be removed or kept out of main |

Current scan found OAuth/API/password terminology in code and tests, but no old GitHub ID or old Gmail hit under `HEAD`. The Mekhane working tree still requires line-level review before any Ochema commit.

## First safe commit sequence

1. Commit Mekhane surface docs only:
   - include `20_機構｜Mekhane/README.md`
   - include `20_機構｜Mekhane/00_概要｜Overview` through `20_機構｜Mekhane/17_協調｜Synergeia`
   - include `20_機構｜Mekhane/H_混合｜Mixins`
   - exclude `_src｜ソースコード`

2. Commit Hermeneus source as its own slice:
   - include `20_機構｜Mekhane/_src｜ソースコード/hermeneus`
   - run secret scan on that slice
   - run tests only if dependencies are already available

3. Commit `mekhane` package by module:
   - start with modules that do not touch OAuth/account routing
   - postpone `ochema` until explicit sensitive review

4. Keep `openclaw` and `openclaude` out of parent main until Tolmetes decides:
   - separate repo
   - submodule
   - vendor snapshot with license review
   - leave local-only

## Stop conditions

Stop and do not commit if any of the following appears:

| stop condition | required response |
|---|---|
| actual old GitHub ID or old Gmail account identifier | isolate file; do not stage |
| actual API key, OAuth refresh token, client secret, or access token | isolate file; do not stage |
| source slice expands above 200 files without a clear boundary | split slice smaller |
| generated output appears in `git diff --cached --name-only` | unstage generated output |
| `git ls-files -d` is nonzero | repair tracked deletion before continuing |
