# Bifurcation Alternative Metric Probe

## Scope

- Probe target: bifurcation が fixed threshold box ではなく、別の gap metrics でも残るか
- Note: これは raw activation を使う外部 metric replacement ではなく、既存 CKA-family profile 上の alternative decision metrics probe

## Raw Status

- OA-SAM records: 10
- Control records: 5
- Duplicate inputs ignored: 0

## final CKA gap

- description: final_epoch の (L2 CKA - L3 CKA)
- OA range: -0.8969 .. 0.8927
- Control range: 0.2122 .. 0.2625
- OA abs-min: 0.8795
- Control abs-max: 0.2625
- Joint-pass margins: 6/6

| margin | status | OA Path A | OA Path B | OA mixed | CTRL Path A | CTRL Path B | CTRL mixed |
|---:|:---|---:|---:|---:|---:|---:|---:|
| 0.30 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.40 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.50 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.60 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.70 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.80 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |

Seed values:

| method | seed | value |
|:--|---:|---:|
| OA-SAM (λ<0) | 42 | 0.8927 |
| OA-SAM (λ<0) | 43 | -0.8853 |
| OA-SAM (λ<0) | 44 | 0.8866 |
| OA-SAM (λ<0) | 45 | 0.8896 |
| OA-SAM (λ<0) | 46 | 0.8839 |
| OA-SAM (λ<0) | 47 | 0.8795 |
| OA-SAM (λ<0) | 48 | 0.8890 |
| OA-SAM (λ<0) | 49 | -0.8796 |
| OA-SAM (λ<0) | 50 | -0.8969 |
| OA-SAM (λ<0) | 51 | 0.8807 |
| Control (λ>0) | 42 | 0.2625 |
| Control (λ>0) | 43 | 0.2426 |
| Control (λ>0) | 44 | 0.2390 |
| Control (λ>0) | 45 | 0.2307 |
| Control (λ>0) | 46 | 0.2122 |

## temporal CKA gap mean

- description: 全 profile epoch における mean(L2 CKA - L3 CKA)
- OA range: -0.4881 .. 0.5906
- Control range: 0.1382 .. 0.1674
- OA abs-min: 0.4536
- Control abs-max: 0.1674
- Joint-pass margins: 6/6

| margin | status | OA Path A | OA Path B | OA mixed | CTRL Path A | CTRL Path B | CTRL mixed |
|---:|:---|---:|---:|---:|---:|---:|---:|
| 0.20 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.25 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.30 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.35 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.40 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.45 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |

Seed values:

| method | seed | value |
|:--|---:|---:|
| OA-SAM (λ<0) | 42 | 0.5807 |
| OA-SAM (λ<0) | 43 | -0.4815 |
| OA-SAM (λ<0) | 44 | 0.5492 |
| OA-SAM (λ<0) | 45 | 0.5906 |
| OA-SAM (λ<0) | 46 | 0.5485 |
| OA-SAM (λ<0) | 47 | 0.5182 |
| OA-SAM (λ<0) | 48 | 0.4854 |
| OA-SAM (λ<0) | 49 | -0.4536 |
| OA-SAM (λ<0) | 50 | -0.4881 |
| OA-SAM (λ<0) | 51 | 0.5485 |
| Control (λ>0) | 42 | 0.1674 |
| Control (λ>0) | 43 | 0.1518 |
| Control (λ>0) | 44 | 0.1611 |
| Control (λ>0) | 45 | 0.1397 |
| Control (λ>0) | 46 | 0.1382 |

## final grad gap

- description: final_epoch の (grad_phi[L3] - grad_phi[L2])
- OA range: -0.9140 .. 1.7867
- Control range: 0.0451 .. 0.1269
- OA abs-min: 0.8888
- Control abs-max: 0.1269
- Joint-pass margins: 8/8

| margin | status | OA Path A | OA Path B | OA mixed | CTRL Path A | CTRL Path B | CTRL mixed |
|---:|:---|---:|---:|---:|---:|---:|---:|
| 0.15 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.20 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.30 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.40 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.50 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.60 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.70 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.80 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |

Seed values:

| method | seed | value |
|:--|---:|---:|
| OA-SAM (λ<0) | 42 | 1.7512 |
| OA-SAM (λ<0) | 43 | -0.9090 |
| OA-SAM (λ<0) | 44 | 1.7661 |
| OA-SAM (λ<0) | 45 | 1.7867 |
| OA-SAM (λ<0) | 46 | 1.7830 |
| OA-SAM (λ<0) | 47 | 1.7744 |
| OA-SAM (λ<0) | 48 | 1.7506 |
| OA-SAM (λ<0) | 49 | -0.9140 |
| OA-SAM (λ<0) | 50 | -0.8888 |
| OA-SAM (λ<0) | 51 | 1.7769 |
| Control (λ>0) | 42 | 0.1269 |
| Control (λ>0) | 43 | 0.0531 |
| Control (λ>0) | 44 | 0.0451 |
| Control (λ>0) | 45 | 0.0581 |
| Control (λ>0) | 46 | 0.0538 |

## temporal grad gap mean

- description: 全 profile epoch における mean(grad_phi[L3] - grad_phi[L2])
- OA range: -0.4332 .. 1.2384
- Control range: -0.0467 .. -0.0132
- OA abs-min: 0.3811
- Control abs-max: 0.0467
- Joint-pass margins: 6/6

| margin | status | OA Path A | OA Path B | OA mixed | CTRL Path A | CTRL Path B | CTRL mixed |
|---:|:---|---:|---:|---:|---:|---:|---:|
| 0.10 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.15 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.20 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.25 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.30 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |
| 0.35 | OA+CTRL | 7 | 3 | 0 | 0 | 0 | 5 |

Seed values:

| method | seed | value |
|:--|---:|---:|
| OA-SAM (λ<0) | 42 | 1.2285 |
| OA-SAM (λ<0) | 43 | -0.4332 |
| OA-SAM (λ<0) | 44 | 1.1451 |
| OA-SAM (λ<0) | 45 | 1.2384 |
| OA-SAM (λ<0) | 46 | 1.1941 |
| OA-SAM (λ<0) | 47 | 1.1484 |
| OA-SAM (λ<0) | 48 | 1.0243 |
| OA-SAM (λ<0) | 49 | -0.4140 |
| OA-SAM (λ<0) | 50 | -0.3811 |
| OA-SAM (λ<0) | 51 | 1.1822 |
| Control (λ>0) | 42 | -0.0277 |
| Control (λ>0) | 43 | -0.0467 |
| Control (λ>0) | 44 | -0.0132 |
| Control (λ>0) | 45 | -0.0340 |
| Control (λ>0) | 46 | -0.0238 |
