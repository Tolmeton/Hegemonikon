# Bifurcation Threshold Sensitivity Probe

## Scope

- Probe target: fixed bifurcation classifier の threshold sensitivity
- Preserve cutoff (`hi`): 0.70, 0.75, 0.80, 0.85, 0.90
- Forget cutoff (`lo`): 0.10, 0.15, 0.20, 0.25, 0.30
- Methods: OA-SAM (λ<0), Control (λ>0)

## Raw Status

- OA-SAM records: 10
- Control records: 5
- Duplicate inputs ignored: 0
- Joint-pass combos: 25/25
- OA-only pass combos: 0
- Control-only pass combos: 0
- Fail combos: 0

## Canonical Check

- canonical `(hi=0.80, lo=0.20)`: OA+CTRL
- canonical OA counts: A=7, B=3, mixed=0
- canonical control counts: A=0, B=0, mixed=5

## Status Matrix

| hi \\ lo | 0.10 | 0.15 | 0.20 | 0.25 | 0.30 |
|:--|:--|:--|:--|:--|:--|
| 0.70 | OA+CTRL | OA+CTRL | OA+CTRL | OA+CTRL | OA+CTRL |
| 0.75 | OA+CTRL | OA+CTRL | OA+CTRL | OA+CTRL | OA+CTRL |
| 0.80 | OA+CTRL | OA+CTRL | OA+CTRL | OA+CTRL | OA+CTRL |
| 0.85 | OA+CTRL | OA+CTRL | OA+CTRL | OA+CTRL | OA+CTRL |
| 0.90 | OA+CTRL | OA+CTRL | OA+CTRL | OA+CTRL | OA+CTRL |

Legend:

- `OA+CTRL`: OA bifurcation exists and control zero-extremes both hold
- `OA_ONLY`: OA bifurcation holds but control zero-extremes fail
- `CTRL_ONLY`: control zero-extremes hold but OA bifurcation fails
- `FAIL`: both fail

### OA-SAM (λ<0)

| hi | lo | Path A | Path B | mixed/none |
|---:|---:|---:|---:|---:|
| 0.70 | 0.10 | 7 | 3 | 0 |
| 0.70 | 0.15 | 7 | 3 | 0 |
| 0.70 | 0.20 | 7 | 3 | 0 |
| 0.70 | 0.25 | 7 | 3 | 0 |
| 0.70 | 0.30 | 7 | 3 | 0 |
| 0.75 | 0.10 | 7 | 3 | 0 |
| 0.75 | 0.15 | 7 | 3 | 0 |
| 0.75 | 0.20 | 7 | 3 | 0 |
| 0.75 | 0.25 | 7 | 3 | 0 |
| 0.75 | 0.30 | 7 | 3 | 0 |
| 0.80 | 0.10 | 7 | 3 | 0 |
| 0.80 | 0.15 | 7 | 3 | 0 |
| 0.80 | 0.20 | 7 | 3 | 0 |
| 0.80 | 0.25 | 7 | 3 | 0 |
| 0.80 | 0.30 | 7 | 3 | 0 |
| 0.85 | 0.10 | 7 | 3 | 0 |
| 0.85 | 0.15 | 7 | 3 | 0 |
| 0.85 | 0.20 | 7 | 3 | 0 |
| 0.85 | 0.25 | 7 | 3 | 0 |
| 0.85 | 0.30 | 7 | 3 | 0 |
| 0.90 | 0.10 | 7 | 3 | 0 |
| 0.90 | 0.15 | 7 | 3 | 0 |
| 0.90 | 0.20 | 7 | 3 | 0 |
| 0.90 | 0.25 | 7 | 3 | 0 |
| 0.90 | 0.30 | 7 | 3 | 0 |

### Control (λ>0)

| hi | lo | Path A | Path B | mixed/none |
|---:|---:|---:|---:|---:|
| 0.70 | 0.10 | 0 | 0 | 5 |
| 0.70 | 0.15 | 0 | 0 | 5 |
| 0.70 | 0.20 | 0 | 0 | 5 |
| 0.70 | 0.25 | 0 | 0 | 5 |
| 0.70 | 0.30 | 0 | 0 | 5 |
| 0.75 | 0.10 | 0 | 0 | 5 |
| 0.75 | 0.15 | 0 | 0 | 5 |
| 0.75 | 0.20 | 0 | 0 | 5 |
| 0.75 | 0.25 | 0 | 0 | 5 |
| 0.75 | 0.30 | 0 | 0 | 5 |
| 0.80 | 0.10 | 0 | 0 | 5 |
| 0.80 | 0.15 | 0 | 0 | 5 |
| 0.80 | 0.20 | 0 | 0 | 5 |
| 0.80 | 0.25 | 0 | 0 | 5 |
| 0.80 | 0.30 | 0 | 0 | 5 |
| 0.85 | 0.10 | 0 | 0 | 5 |
| 0.85 | 0.15 | 0 | 0 | 5 |
| 0.85 | 0.20 | 0 | 0 | 5 |
| 0.85 | 0.25 | 0 | 0 | 5 |
| 0.85 | 0.30 | 0 | 0 | 5 |
| 0.90 | 0.10 | 0 | 0 | 5 |
| 0.90 | 0.15 | 0 | 0 | 5 |
| 0.90 | 0.20 | 0 | 0 | 5 |
| 0.90 | 0.25 | 0 | 0 | 5 |
| 0.90 | 0.30 | 0 | 0 | 5 |
