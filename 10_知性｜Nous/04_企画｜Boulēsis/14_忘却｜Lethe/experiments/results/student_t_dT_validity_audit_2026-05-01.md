# Student t dT validity audit for Paper I OP-I-7

## Scope

This audit checks whether the 2026-05-01 Student t `(nu, gamma)` sweep and interval scaffold are numerically credible. It does not promote the result to formal interval arithmetic or analytic proof.

## Checked Surfaces

- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/student_t_dT_nu_sweep.py`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/student_t_dT_interval_scaffold.py`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/results/student_t_dT_interval_scaffold_2026-05-01.md`

## Formula Checks

The score formulas used by the sweep were compared with centered finite differences of the Student t log density. Maximum absolute discrepancies over representative points `y in {-5,-2,-0.5,0,0.5,2,5}` were:

| nu | max score formula vs finite-difference error |
|---:|---:|
| 1.5 | 7.622e-10 |
| 2.0 | 1.090e-09 |
| 3.0 | 4.229e-10 |
| 5.0 | 9.562e-10 |

Interpretation: the implemented score formulas are consistent with the log-density derivatives at numerical precision relevant to this screen.

## Quadrature / Moment Sanity Checks

For each requested point, normalization and score means were checked across Gauss-Legendre node counts 200, 400, 600, 800, 1000.

| nu | node range | mass error scale | score mean scale | base dT spread across nodes |
|---:|:---|:---|:---|---:|
| 1.5 | 200-1000 | 8.046e-08 down to 6.477e-10 | <= 7.389e-07 | 6.430e-05 |
| 2.0 | 200-1000 | <= 1.075e-13 | <= 3.067e-09 | 6.075e-06 |
| 3.0 | 200-1000 | <= 1.097e-13 | <= 9.710e-13 | 1.185e-08 |
| 5.0 | 200-1000 | <= 1.099e-13 | <= 7.455e-14 | 2.054e-11 |

Interpretation: the weakest endpoint `nu=5` is highly stable under node changes. The heaviest-tail point `nu=1.5` has the largest quadrature sensitivity but remains far from zero.

## Dense Grid Check

A denser grid with 71 points on `nu in [1.5,5.0]` was checked at nodes 800 and 1000.

| nodes | grid size | signs | weakest nu | lower `|dT|` | lower `|dT|/||T||` |
|---:|---:|:---|---:|---:|---:|
| 800 | 71 | positive only | 5.0 | 6.532684319802e-01 | 1.393091356205e-01 |
| 1000 | 71 | positive only | 5.0 | 6.532684319965e-01 | 1.393091356240e-01 |

Interpretation: the 36-point scaffold did not miss an obvious interior zero or weaker sampled point at this resolution. The high-`nu` endpoint remains the limiting sampled region.

## Validity Judgment

The result is valid as numerical evidence for the Student t `(nu, gamma)` N1 twist-positive bucket on the sampled interval. The evidence is stronger than the initial four-point sweep because it passes formula finite-difference checks, quadrature sanity checks, node convergence checks, and a denser grid screen.

It is not yet valid as a theorem. It should not be stated as formal interval arithmetic or as a continuous convergence proof toward the Cauchy location-scale N0 witness. The tested tangent plane is `(nu, gamma)`, while the Cauchy closed-form witness concerns `(mu, gamma)`.

## Next Formal Upgrade

The next useful target is the high-`nu` endpoint region near `nu=5`, because both `|dT|` and `|dT|/||T||` are weakest there. A formal upgrade should either:

1. derive an analytic lower bound for `dT_{nu,gamma}` on `nu in [1.5,5]`, starting near the high-`nu` end, or
2. implement genuine interval arithmetic with outward-rounded bounds for quadrature, score terms, Fisher inversion, and finite-difference derivatives.
