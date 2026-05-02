# FEP v05 audit pack — 2026-05-02

## Scope

対象は `FEPの操作的分解型_v05` の tracked Papers 面と workspace 面の同期状態である。

## SOURCE

| 面 | SOURCE |
|:---|:---|
| tracked status | `git -c core.quotePath=false status --short | rg 'FEP\|blind_outputs\|_workspaces'` |
| tracked files | `git -c core.quotePath=false ls-files -- '01_研究論文｜Papers/_workspaces/FEPの操作的分解型_v05'` |
| equality check | `diff -q` across tracked Papers files and workspace files |
| hash check | `sha256sum` for main, meta, blind evaluation |
| workspace state | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/_workspaces/FEPの操作的分解型_v05/README.md` |
| workspace status | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/_workspaces/FEPの操作的分解型_v05/STATUS.md` |
| integrity notes | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/_workspaces/FEPの操作的分解型_v05/integrity_notes.md` |

## Findings

| ID | Finding | Judgment |
|:---|:---|:---|
| F1 | `Papers/FEPの操作的分解型_v05.md` and workspace `FEPの操作的分解型_v05.md` are byte-identical. SHA256: `96e9d39e3ed9f382b60f1632ac0490a8ab1a7a764ce33536aaf0437c10618a33`. | 本体の workspace duplicate は昇格差分ではない。 |
| F2 | `Papers/FEPの操作的分解型_v05.meta.md` and workspace meta are byte-identical. SHA256: `ebaef4e3a29d61e9f1c0977e6bc3e63d0b87105886814a9b85713ed1732d41fb`. | meta も昇格差分ではない。 |
| F3 | `diff -q` showed no content difference for spine, rubric, execution log, participant prompt, and systematic refutation. | 未追跡 workspace files の大半は tracked Papers 面の duplicate。 |
| F4 | Only `FEP分解型_blind_evaluation_gemini_2026-05-01.md` differs. Tracked version marks the result as `Weak pass`; workspace version marks it as `Fail`. | 主張強度に関わる唯一の実質差分。 |
| F5 | Tracked blind evaluation was introduced by commit `af03b5fa7 docs(yugaku): add FEP decomposition review artifacts`. | tracked 側は既に commit 済みの published state。 |
| F6 | Workspace `README.md` / `STATUS.md` / `integrity_notes.md` still describe the main body as not placed in main `Papers/`, but live tracked state now contains the main body and matches workspace. | workspace 台帳が current live state に追随していない。 |
| F7 | `01_研究論文｜Papers/blind_outputs/gemini_gemini-3.1-flash-lite-preview_20260501T132107Z.md` is untracked and is referenced by the tracked blind evaluation. | evaluation SOURCE が未追跡なので、再現性 pack としては不足が残る。 |

## Blind evaluation fork

| 面 | Basis treatment | Verdict |
|:---|:---|:---|
| tracked Papers | `Basis` is not gated; local FEP physics SOURCE must support it. | Weak pass under revised rubric |
| workspace duplicate | `Basis` remains a hard gate. | Fail |

この差分は「どちらが正しいか」という表現差分ではなく、blind protocol の射程をどこまでに制限するかの判断差分である。

## Judgment

[推定] FEP v05 の current main line は tracked Papers 側である。workspace 側の untracked artifact 群は、ほぼ duplicate であり、唯一の例外が blind evaluation の旧 rubric / hard-gate 判定である。

[主観] 次に直すべきは本文ではなく、reproducibility と workspace ledger である。具体的には、`blind_outputs/` の SOURCE を追跡するか、evaluation から参照を外して再取得手順へ落とすかを先に決めるべきである。

## Next

1. Workspace `STATUS.md` / `integrity_notes.md` を current state に更新する。
2. `blind_outputs/gemini_gemini-3.1-flash-lite-preview_20260501T132107Z.md` を追跡対象にするか、再現手順のみ残すかを決める。
3. `FEP分解型_blind_evaluation_gemini_2026-05-01.md` の rubric revision を `decisions/` に明示し、`Fail -> Weak pass` の判断理由を台帳化する。
4. duplicate の workspace article/meta/spine/prompt/rubric/log/refutation を残す目的がないなら、削除ではなく archive policy を先に決める。
