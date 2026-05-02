# T-038 Phase C Diagnostic Pair Evaluation — CodeBERT Proxy

## SOURCE
- input: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.claude/worktrees/serene-clarke/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_diagnostic.jsonl`
- rows_used: `288` / unique_sources: `315`
- source_components: `88` / largest_component_pairs: `144`
- model: `microsoft/codebert-base`
- cache_dir: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/pinakas/.cache_t038_codebert`

## Overall Metrics
| score | acc | f1 | auc | rho_label | rho_49d | rho_ccl | partial_rho_ccl_len | R@1 | R@5 | R@10 | claim_level |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| 49d_inverse_similarity | 0.830 | 0.795 | 1.000 | 0.814 | -1.000 | 0.630 | 0.400 | 1.000 | 1.000 | 1.000 | construction/control baseline; not independent representation evidence |
| ccl_similarity_oracle | 0.830 | 0.795 | 1.000 | 0.815 | -0.630 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | target-side oracle; not representation evidence |
| codebert_inverse_cosine | 0.323 | 0.184 | 0.237 | -0.429 | 0.261 | -0.386 | -0.279 | 0.000 | 0.000 | 0.021 | L0 / fail |
| codebert_pair_logreg_row_prob | 0.962 | 0.945 | 0.998 | 0.811 | -0.662 | 0.624 | 0.362 | 0.926 | 0.958 | 0.989 | L3 candidate; G5 depends on per-pair diagnostic robustness; row split has source-leakage risk |
| codebert_pair_logreg_source_component_prob | 0.906 | 0.876 | 0.990 | 0.797 | -0.659 | 0.626 | 0.363 | 0.379 | 0.905 | 0.958 | L3 candidate; G5 depends on per-pair diagnostic robustness; source-component split |

## G3 Shuffle Null
- metric: `auc`
- observed: `0.990`
- null_mean: `0.506`
- n_perm: `50`
- p_ge_observed: `0.020`

## G5 Diagnostic Pair Robustness — CodeBERT Pair LogReg
| pair_type | n | labels | mean_score | acc | error_rate | rho_ccl | partial_rho_ccl_len | R@1 | R@5 | R@10 | note |
|:---|---:|:---|---:|---:|---:|---:|---:|:---|:---|:---|:---|
| diag_blindspot | 95 | 1 | 0.991 | 1.000 | 0.000 | 0.175 | 0.154 | N/A | N/A | N/A | R@k is global-only because this diagnostic type has a single class label. |
| diag_isomer | 193 | 0 | 0.141 | 0.860 | 0.140 | -0.082 | -0.042 | N/A | N/A | N/A | R@k is global-only because this diagnostic type has a single class label. |

## Interpretation
- `ccl_similarity_oracle` is a target-side oracle and is not representation evidence.
- `codebert_pair_logreg_row_prob` is exploratory and has source-overlap leakage risk.
- `codebert_pair_logreg_source_component_prob` is stricter: connected source components are not split across folds.
- Even the stricter probe can satisfy G5 only as proxy evidence, not final causal proof.
- `R@k` is defined globally: each positive diagnostic blindspot is ranked against all negative diagnostic isomers.
