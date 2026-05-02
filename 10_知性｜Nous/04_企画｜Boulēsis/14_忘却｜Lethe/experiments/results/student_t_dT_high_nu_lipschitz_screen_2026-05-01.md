# Student t dT high-nu Lipschitz screen for Paper I OP-I-7

- nu interval: `4.5` to `5.0`
- gamma: `1.0`
- grid size: `101`
- nodes: `1000`
- safety factor over observed slope: `20.0`
- status: `PASS`
- proof status: numerical Lipschitz screen only; not formal interval arithmetic

## Guarded Lower Bound Screen

| quantity | value |
|:---|---:|
| observed Lipschitz proxy for base dT | 1.255496845e-01 |
| guarded Lipschitz proxy | 2.510993691e+00 |
| grid cell radius | 2.500000000e-03 |
| weakest sampled nu | 5 |
| weakest sampled lower `|dT|` | 6.532684320e-01 |
| guarded cell lower `|dT|` | 6.469909478e-01 |

## Interpretation

This screen supports positivity near the high-nu endpoint under an empirical Lipschitz guard. It is not formal interval arithmetic because the Lipschitz constant is estimated numerically and the quadrature is not outward rounded.

The screen remains far from zero even after multiplying the observed slope by the safety factor. 
This makes the high-nu endpoint a good first target for a real interval or analytic proof, but it does not replace that proof.
