# Student t scale-reduction probe for Paper I OP-I-7

## Target Identity

For the Student t `(nu, gamma)` family in the scale coordinate `y = x/gamma`:

```text
T_nu(nu, gamma)    = U(nu)
T_gamma(nu, gamma) = V(nu) / gamma
dT(nu, gamma)      = V'(nu) / gamma
```

This turns the high-nu lower-bound problem into a one-variable lower bound for `V'(nu)`.

## Numerical Probe

- nodes: `800`
- nu values: `[1.5, 2.0, 3.0, 5.0]`
- gamma values: `[0.5, 1.0, 2.0, 4.0]`

| quantity | max spread across gamma |
|:---|---:|
| `T_nu` | 6.661338148e-16 |
| `gamma*T_gamma` | 4.440892099e-16 |
| `gamma*dT` | 2.220446049e-12 |

## Per-nu Spreads

| nu | spread `T_nu` | spread `gamma*T_gamma` | spread `gamma*dT` |
|---:|---:|---:|---:|
| 1.5 | 6.661338148e-16 | 4.440892099e-16 | 0.000000000e+00 |
| 2 | 0.000000000e+00 | 4.440892099e-16 | 2.220446049e-12 |
| 3 | 0.000000000e+00 | 0.000000000e+00 | 0.000000000e+00 |
| 5 | 0.000000000e+00 | 0.000000000e+00 | 0.000000000e+00 |

## Interpretation

The probe checks the numerical implementation of the scaling reduction. The proof obligation is then reduced to bounding V'(nu) for T_gamma = V(nu)/gamma.

The scaling identity itself follows from score scaling and tensor contraction scaling; this probe only checks that the numerical implementation obeys it.
