# Middle-Band Weight Search

既存 `p3b_stratification.json` から `control_flow_distance` を復元し、`d_lethe_candidate` の重みを掃いて middle-band failure を最優先で下げる。

## Sample

- function_count: `200`
- pair_count: `500`
- alpha_grid: `0.00` → `1.00` (step `0.05`)
- tolerance: `0.05`
- near_guardrail_delta: `0.05`
- far_guardrail_delta: `0.05`

## Baseline vs Aggressive Best

| Metric | Baseline | Best | Delta |
|---|---:|---:|---:|
| alpha | 0.65 | 0.75 | +0.10 |
| mid_fail_rate | 0.539 | 0.500 | -0.039 |
| near_fail_rate | 0.348 | 0.457 | +0.109 |
| far_fail_rate | 0.076 | 0.059 | -0.017 |
| total_fail_rate | 0.412 | 0.392 | -0.020 |

## Baseline vs Guardrailed Best

| Metric | Baseline | Guardrailed | Delta |
|---|---:|---:|---:|
| alpha | 0.65 | 0.65 | +0.00 |
| mid_fail_rate | 0.539 | 0.539 | +0.000 |
| near_fail_rate | 0.348 | 0.348 | +0.000 |
| far_fail_rate | 0.076 | 0.076 | +0.000 |
| total_fail_rate | 0.412 | 0.412 | +0.000 |

## Recommendation

- aggressive_alpha: `0.75`
- aggressive_formula: `0.75 * ccl_normalized_distance + 0.25 * control_flow_distance`
- guardrailed_alpha: `0.65`
- guardrailed_formula: `0.65 * ccl_normalized_distance + 0.35 * control_flow_distance`

## Top Candidates

| alpha | mid | total | near | far |
|---|---:|---:|---:|---:|
| 0.75 | 0.500 | 0.392 | 0.457 | 0.059 |
| 0.80 | 0.500 | 0.398 | 0.522 | 0.059 |
| 0.85 | 0.512 | 0.414 | 0.696 | 0.025 |
| 0.90 | 0.518 | 0.422 | 0.717 | 0.034 |
| 0.70 | 0.524 | 0.408 | 0.435 | 0.068 |
| 0.95 | 0.527 | 0.430 | 0.717 | 0.042 |
| 1.00 | 0.533 | 0.434 | 0.739 | 0.034 |
| 0.65 | 0.539 | 0.412 | 0.348 | 0.076 |
| 0.60 | 0.548 | 0.422 | 0.348 | 0.093 |
| 0.55 | 0.565 | 0.434 | 0.348 | 0.093 |

## Sources

- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/p3b_stratification.json`
- baseline_formula: `0.65 * ccl_normalized_distance + 0.35 * control_flow_distance`
- cf_reconstruction: `control_flow_distance = clamp01((baseline_distance - source_alpha * ccl_distance) / source_control_flow_weight)`
