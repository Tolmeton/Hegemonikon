# Access-Path Scorecard

Lethe canonical record から、`model size` と `access-path` の優先順位を再利用可能な形で固定する。

## Headline

| Metric | Value |
|---|---:|
| CodeBERT single-vector partial rho | 0.45 |
| CodeBERT attentive partial rho | 0.74 |
| CodeLlama single-vector partial rho | 0.17 |
| Mistral single-vector partial rho | 0.20 |
| Access lift | 0.29 |
| Size lift | -0.25 |
| Reversal margin | 0.54 |

## Structure Sensitivity

| Metric | Drop |
|---|---:|
| Destroy structural tokens | 0.110 |
| Shuffle token order | 0.141 |
| Normalize non-structural tokens | 0.153 |

## Middle-Band Geometry

| Family | Near fail | Mid fail | Far fail |
|---|---:|---:|---:|
| ccl_string | 0.739 | 0.533 | 0.034 |
| cosine_49d | 0.087 | 0.768 | 0.975 |
| d_lethe_candidate | 0.348 | 0.539 | 0.076 |

## Decision

- access_beats_size: `true`
- hypothesis_supported: `true`
- optimize_priority: `access_path_and_middle_band`

## Sources

- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/EXPERIMENTS.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/ablation_results.json`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/p3b_stratification.json`
