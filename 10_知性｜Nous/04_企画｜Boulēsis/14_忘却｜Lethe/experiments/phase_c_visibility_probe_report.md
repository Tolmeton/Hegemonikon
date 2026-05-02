# Phase C Visibility Probe Report

- Date: 2026-04-18
- Script: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_visibility_probe.py
- Results: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_visibility_probe_results.json

## Hypothesis

D-only LXI gain is caused by a structural visibility gap on the input surface.

## Intervention

1. `D_code`: original D condition (code only)
2. `D_plus_ccl_aligned`: inject aligned CCL scaffold from B
3. `D_plus_ccl_shifted`: inject mismatched CCL scaffold from another pair

## Key Checks

- B/D metadata alignment: `938/938` on `label`, `cosine_49d`, `ccl_edit_dist`, `ccl_sim`
- B code vs D code text alignment: `938/938`

## Mean Results

| Condition | acc | rho_ccl | partial_rho_ccl |
|:--|--:|--:|--:|
| D_code | 0.7335 | 0.3950 | 0.2925 |
| D_plus_ccl_aligned | 0.7282 | 0.3866 | 0.2611 |
| D_plus_ccl_shifted | 0.7495 | 0.3954 | 0.2488 |

## Contrasts

- `aligned_minus_code_partial_rho_ccl = -0.0315`
- `aligned_minus_shifted_partial_rho_ccl = +0.0123`
- `aligned_minus_code_acc = -0.0053`

## Minimal Conclusion

Adding explicit CCL scaffold to D did **not** recover structural alignment for this lightweight surface probe.
Therefore, the simple form of the input-surface hypothesis is weakened.

The result is more consistent with:

1. surface-visible CCL tokens alone are insufficient
2. the useful bridge requires deeper composition than a linear lexical probe can exploit
3. the next discriminating experiment should move from surface intervention to layer-placement sensitivity
