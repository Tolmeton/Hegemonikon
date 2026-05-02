# Student t high-nu analytic proof scaffold for Paper I OP-I-7

## Claim Status

This is a proof scaffold, not a completed proof. Its role is to reduce the OP-I-7 Student t `(nu, gamma)` positivity problem to a smaller analytic target.

## Starting Point

The numerical screens identify the weakest sampled region as the high-`nu` endpoint near `nu = 5`:

- four-point sweep: lower `|dT| >= 6.532684320e-01` at `nu = 5`, `gamma = 1`
- grid scaffold on `nu in [1.5,5]`: weakest sampled point `nu = 5`
- high-nu Lipschitz screen on `nu in [4.5,5]`: guarded cell lower `|dT| >= 6.469909478e-01`

These are numerical witnesses only. The analytic task is to remove dependence on the quadrature and finite-difference pipeline.

## Lemma 1: Scale Reduction

Let `y = x/gamma`. For the Student t family parameterized by `(nu, gamma)`, the log-density score has the scaling form

```text
s_nu(nu, gamma; y)    = a(nu; y)
s_gamma(nu, gamma; y) = b(nu; y) / gamma
```

where the distribution of `y` depends on `nu` but not on `gamma`.

Therefore the Fisher metric and Amari-Chentsov tensor components have homogeneous gamma scaling:

```text
g_nu_nu       = A(nu)
g_nu_gamma    = B(nu) / gamma
g_gamma_gamma = D(nu) / gamma^2

C_{i j k} scales as gamma^{-m}, where m is the number of gamma indices.
```

The inverse metric has the dual scaling, so the Chebyshev one-form reduces to

```text
T_nu(nu, gamma)    = U(nu)
T_gamma(nu, gamma) = V(nu) / gamma
```

Thus

```text
dT(nu, gamma) = partial_nu T_gamma - partial_gamma T_nu
              = V'(nu) / gamma.
```

The OP-I-7 Student t proof target is therefore one-dimensional: bound `V'(nu)` away from zero on the chosen `nu` interval.

## Numerical Check Of Lemma 1

`student_t_scale_reduction_probe.py` checks the implementation against the scaling identity across `gamma in {0.5,1,2,4}`.

| quantity | max spread across gamma |
|:---|---:|
| `T_nu` | 6.661338148e-16 |
| `gamma*T_gamma` | 4.440892099e-16 |
| `gamma*dT` | 2.220446049e-12 |

Interpretation: the implementation respects the scale reduction at numerical precision. This does not prove the analytic lemma; the lemma follows from the score-scaling argument above.

## Lemma 2: Positivity Target

Define

```text
V(nu) := gamma * T_gamma(nu, gamma).
```

Because of Lemma 1, this is independent of `gamma`. To upgrade the N1 bucket from numerical scaffold to analytic lower bound, prove one of the following:

```text
Strong target: V'(nu) >= 0.6       for nu in [1.5, 5]
Local target:  V'(nu) >= 0.6       for nu in [4.5, 5]
Weak target:   V'(nu) >  0         for nu in [1.5, 5]
```

The current numerical evidence supports the strong target, but only the local target is the immediate proof step.

## Lemma 3: Required Analytic Ingredients

To make Lemma 2 rigorous, derive closed or bounded expressions for:

```text
A(nu), B(nu), D(nu)          Fisher metric coefficients
C_{nu nu nu}(nu)
C_{nu nu gamma}(nu)
C_{nu gamma gamma}(nu)
C_{gamma gamma gamma}(nu)
```

Each is an expectation under the one-dimensional Student t density in `y`. Terms are built from rational functions of `y^2`, `log(1 + y^2/nu)`, and digamma differences in `nu`.

A viable proof route is:

1. express rational moments by beta-function identities;
2. express log-weighted moments as derivatives of beta-function identities with respect to exponent parameters;
3. use monotone bounds for digamma / trigamma differences on `nu in [4.5,5]`;
4. bound the determinant of the Fisher block away from zero;
5. differentiate the resulting `V(nu)` expression and lower-bound it.

## Current Blocker

The runtime currently lacks `mpmath`, `sympy`, `scipy`, and interval libraries. Therefore no outward-rounded interval proof was produced in this run.

## Safe Paper-Level Use

This scaffold supports the following claim only:

```text
The Student t N1 numerical scaffold admits a scale reduction: dT(nu,gamma)=V'(nu)/gamma. Hence the next formal upgrade can focus on a one-variable lower bound for V'(nu), first near the high-nu endpoint.
```

It does not support:

```text
Student t N1 has been analytically proven twist-positive on [1.5,5].
```
