# Q-007 Structural Understanding Threshold Rubric

Date: 2026-05-01
Status: active evidence-admission gate; G5 proxy passed, L4 blocked
Scope: Lethe Phase B2 / Phase C metrics, especially `partial_rho_ccl`

## 1. Purpose

Q-007 asks when positive `partial_rho_ccl` can be treated as evidence of structural understanding. The answer is not `partial_rho_ccl > 0`. A positive value is only an entry signal. It becomes admissible evidence only when it survives baseline comparison, null/shuffle pressure, diagnostic-pair pressure, retrieval-rank agreement, and confound checks.

This rubric is an evidence gate for downstream tasks such as T-038 and T-104. It does not declare that Phase C has already passed every gate.

## 2. Source Surface

| source | role | path |
|---|---|---|
| Phase B2 CodeBERT | attentive probe precedent | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.claude/worktrees/serene-clarke/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_b2_results.json` |
| Phase B2 CodeLlama | attentive probe strong precedent | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.claude/worktrees/serene-clarke/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_b2_codellama.json` |
| Phase B2 Gemma4 | failed/control-like precedent | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.claude/worktrees/serene-clarke/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_b2_gemma4_results.json` |
| Phase C v3 | main Phase C ablation | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3_results.json` |
| Phase C visibility probe | surface-token confound check | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_visibility_probe_results.json` |
| Phase C layer sensitivity | layer/locus confound check | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_layer_sensitivity_results.json` |
| Phase C diagnostic pairs | adversarial diagnostic set | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.claude/worktrees/serene-clarke/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_diagnostic.jsonl` |
| T-038 CodeBERT diagnostic proxy | diagnostic-pair evaluation | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/pinakas/T-038_phase_c_diag_codebert_proxy_report_2026-05-01.md` |
| T-039 diagnostic error analysis | false-positive taxonomy | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/pinakas/T-039_diag_isomer_error_analysis_2026-05-01.md` |

## 3. Observed Anchors

| observation | value |
|---|---:|
| Phase B2 CodeBERT attentive `mean_partial_rho` | 0.7446 |
| Phase B2 CodeBERT baseline `mean_partial_rho` | 0.7211 |
| Phase B2 CodeLlama attentive `mean_partial_rho` | 0.8185 |
| Phase B2 CodeLlama baseline meanpool `mean_partial_rho` | 0.6397 |
| Phase B2 Gemma4 attentive/baseline `mean_partial_rho` | 0.0000 / 0.0000 |
| Phase C v3 A baseline `mean_partial_rho_ccl` | 0.5481 |
| Phase C v3 B baseline `mean_partial_rho_ccl` | 0.4509 |
| Phase C v3 D baseline `mean_partial_rho_ccl` | 0.3708 |
| Phase C v3 D best LXI delta in `mean_partial_rho_ccl` | +0.0689 at `lxi_0.1` |
| Visibility probe D_code `mean_partial_rho_ccl` | 0.2925 |
| Visibility probe D_plus_ccl_aligned `mean_partial_rho_ccl` | 0.2611 |
| Layer sensitivity D/shallow LXI delta | +0.0092 |
| Layer sensitivity D/mid LXI delta | -0.0024 |
| Layer sensitivity D/deep LXI delta | 0.0000 |
| Diagnostic pairs | 301 total = 200 `diag_isomer` + 101 `diag_blindspot` |
| T-038 source-bearing diagnostic pairs used | 288 = 193 `diag_isomer` + 95 `diag_blindspot` |
| T-038 CodeBERT component-split acc / f1 / auc | 0.906 / 0.876 / 0.990 |
| T-038 CodeBERT component-split `partial_rho_ccl_len` | 0.363 |
| T-038 CodeBERT component-split R@1 / R@5 / R@10 | 0.379 / 0.905 / 0.958 |
| T-039 component-split false positives / false negatives | 27 / 0 |
| T-039 false-positive dominant class | 17 `test_scaffold_overlap` |

## 4. Evidence Gate

A result may be called structural-understanding evidence only if it passes all five gates below.

| gate | required condition | pass/fail rule |
|---|---|---|
| G1 Positive structural signal | `partial_rho_ccl > 0` on the target condition | Required but never sufficient |
| G2 Baseline advantage | target probe/model exceeds its matched baseline or meanpool on `partial_rho_ccl` or equivalent `mean_partial_rho` | Must pass for positive claim; otherwise label as representation signal only |
| G3 Null and shuffle survival | signal remains under permutation, shuffled CCL, shifted scaffold, or equivalent negative control | Missing control means claim is provisional |
| G4 Rank agreement | R@1/R@5/R@10 move in the same direction as `partial_rho_ccl` | If rank and correlation diverge, downgrade to metric-specific signal |
| G5 Diagnostic-pair robustness | `diag_isomer` and `diag_blindspot` are reported separately, and the effect is not confined to easy pairs | Required before using the phrase structural understanding in paper-facing prose. If false positives concentrate in one surface family, mark as G5 proxy pass and keep L4 blocked. |

## 5. Claim Levels

| level | label | criteria | allowed wording |
|---|---|---|---|
| L0 | positive association | G1 only | "positive structural correlation" |
| L1 | probe-sensitive representation | G1 + partial G2 | "the representation carries CCL-aligned signal" |
| L2 | controlled structural signal | G1 + G2 + at least one G3 control | "controlled structural signal" |
| L3 | retrieval-consistent structural signal | G1 + G2 + G3 + G4 | "structural alignment evidence" |
| L4 | adversarially robust structural understanding evidence | G1 + G2 + G3 + G4 + G5 | "evidence of structural understanding" |

## 6. Current Classification

| target | classification | reason |
|---|---|---|
| Phase B2 CodeBERT attentive | L1 | Attentive exceeds baseline slightly: 0.7446 vs 0.7211. Need stronger null/control surface before paper-facing structural-understanding wording. |
| Phase B2 CodeLlama attentive | L2 candidate | Attentive strongly exceeds meanpool: 0.8185 vs 0.6397. Control surface still needs explicit alignment with this rubric. |
| Phase B2 Gemma4 | L0 fail | Both attentive and baseline are 0.0; do not use as positive evidence. |
| Phase C v3 A/B/D baseline | L1 | All positive, but positivity alone does not decide structural understanding. |
| Phase C v3 D LXI gain | L2 candidate | D shows positive LXI delta in Phase C v3; visibility and layer probes weaken simple explanations but do not yet establish adversarial robustness. |
| Phase C diagnostic pairs / T-038 | L3 candidate | CodeBERT pair probe passes a stricter source-component split: acc 0.906, f1 0.876, auc 0.990, `partial_rho_ccl_len` 0.363, R@10 0.958. This is structural alignment evidence, not yet full structural-understanding evidence. |
| Phase C diagnostic pairs / T-039 | L4 blocked | Error analysis found 27 false positives and 0 false negatives. The main residual failure class is `test_scaffold_overlap` (17/27), so adversarial robustness is not established. |

## 7. T-038 / T-039 G5 Result

T-038/T-039 fill the G5 table as follows. `R@k` is global because each diagnostic subtype has a single class label.

| pair type | n | acc | rho_ccl | partial_rho_ccl | R@1 | R@5 | R@10 | claim level |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| diag_isomer | 193 | 0.860 | -0.082 | -0.042 | N/A | N/A | N/A | false-positive blocker |
| diag_blindspot | 95 | 1.000 | 0.175 | 0.154 | N/A | N/A | N/A | no false-negative blocker |
| global | 288 | 0.906 | 0.626 | 0.363 | 0.379 | 0.905 | 0.958 | L3 candidate |

Judgment: T-038 gives a G5 proxy pass because both diagnostic sides are explicitly separated and the strict split survives shuffle pressure. T-039 prevents L4 promotion because the remaining false-positive mass is not random; it concentrates in `test_scaffold_overlap` and related surface families.

Allowed wording after T-038/T-039: "source-component-controlled structural alignment evidence."

Forbidden wording until the false-positive blocker is resolved: "adversarially robust evidence of structural understanding."

## 8. Use In T-104

T-104 should not substitute `partial_rho_ccl` directly for Pearson `r_obs` in the Paper IV ceiling formula. The admissible bridge is:

1. first classify the `partial_rho_ccl` result using this rubric;
2. then state whether the metric is a controlled proxy, not `r_obs` itself;
3. only after that derive a correction or non-substitution condition.

If the result is below L3, it should not be promoted into a paper-facing ceiling-formula claim.

## 9. Rejection Ledger

| rejected shortcut | reason |
|---|---|
| `partial_rho_ccl > 0` means structural understanding | Positive correlation can arise from length, surface tokens, metric alignment, or easy-pair bias. |
| A/B/D baseline positivity is enough | Phase C v3 shows all baseline values positive, but condition interpretation differs. |
| CCL token injection should improve D if the hypothesis is right | Visibility probe shows aligned CCL scaffold lowered D `mean_partial_rho_ccl` from 0.2925 to 0.2611, so surface token exposure is not enough. |
| deep-only locus | Layer sensitivity proxy does not support a simple deep-only story. |

## 10. Next Action

Resolve the T-039 blocker by adding or reweighting hard negative controls for `test_scaffold_overlap`, CLI/parser boilerplate, and unicode/docstring surface overlap. Re-run T-038/T-039 after the negative-control update before promoting any Phase C result to L4.
