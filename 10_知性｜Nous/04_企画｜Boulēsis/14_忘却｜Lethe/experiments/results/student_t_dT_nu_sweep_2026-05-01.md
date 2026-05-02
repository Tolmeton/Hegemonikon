# Student t dT ν sweep for Paper I OP-I-7

- quadrature: Gauss-Legendre on `y = tan(pi*u/2)`, nodes = 600
- gamma: 1.0
- criterion: min `|dT|` and min `|dT|/|T|` both exceed `1.0e-03`
- note: this checks the `(nu, gamma)` manifold; it is not the same tangent plane as the Cauchy location-scale N0 witness.

| nu | T = (T_nu, T_gamma) | base dT | dT envelope | lower |dT| | lower |dT|/|T| | verdict |
|:---|:---|---:|:---|---:|---:|:---|
| 1.5 | (-1.935272, +1.445663) | 1.272262e+00 | [1.272262e+00, 1.272262e+00] | 1.272262e+00 | 5.266814e-01 | PASS |
| 2 | (-1.475481, +2.050125) | 1.148044e+00 | [1.148044e+00, 1.148044e+00] | 1.148044e+00 | 4.545131e-01 | PASS |
| 3 | (-0.963942, +3.090224) | 9.407100e-01 | [9.407100e-01, 9.407100e-01] | 9.407100e-01 | 2.906047e-01 | PASS |
| 5 | (-0.518978, +4.660537) | 6.532684e-01 | [6.532684e-01, 6.532684e-01] | 6.532684e-01 | 1.393091e-01 | PASS |

## Interpretation

All requested nu values remain bounded away from zero under the step envelope. This supports the N1 twist-positive bucket for the Student t `(nu, gamma)` family at gamma = 1.0.

The sweep should not be read as a continuous convergence proof from N1 to the N0 Cauchy location-scale witness. The Cauchy proof in `cauchy_closed_form_chebyshev.py` concerns the `(mu, gamma)` location-scale manifold, whereas this sweep includes the `nu` direction as a parameter direction.
