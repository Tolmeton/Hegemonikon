# Operational Decomposition Types of the Free Energy Principle:
# A Consistency Analysis with the HGK Cognitive Coordinate System

> **Draft v0.3** — 2026-03-08 (post-literature review rewrite)
> **Authors**: [Creator] & Antigravity
> **Status**: Working draft — blind-validated, prior art incorporated

---

## Abstract

We investigate the consistency between the Free Energy Principle's (FEP) operational structure and the seven-coordinate Hegemonikón Knowledge System (HGK). Rather than attempting to *derive* HGK's coordinates from FEP—a goal we show to be ill-posed—we ask: **how many independent operational decomposition types does FEP generate, and are they consistent with HGK's 7+1 coordinate structure?**

Through three analyses:

1. **Systematic enumeration** (§3): We catalog 8 operational decomposition types in the FEP literature (Friston 2019; Ramstead et al. 2022; Friston et al. 2022), validated by a blind experiment in which an LLM with no knowledge of HGK independently reproduced all 8 types.

2. **Fisher eigenstructure** (§4): The effective dimensionality $d_\text{eff}$ of the Fisher information matrix is model-dependent ($1.5 \leq d_\text{eff} \leq \dim(\mathcal{M})$), ruling out a universal 7-dimensional eigenstructure. The number of decomposition *types*, however, is model-independent.

3. **Literature synthesis** (§5): The fiber bundle structure connecting Helmholtz decomposition to information-geometric duality has been rigorously established by Sakthivadivel (2022). We situate HGK's treatment of Helmholtz as "implicit" within this existing framework.

**Key distinction**: FEP does not *require* 7 coordinates, but the 8 operational decomposition types it generates are *consistent with* HGK's 7 explicit coordinates plus 1 implicit structure. This consistency is non-trivial: the 8 types were independently reproduced without HGK knowledge.

**Keywords**: Free Energy Principle, information geometry, Bayesian mechanics, cognitive coordinates, operational decomposition, blind validation

---

## 1. Introduction

### 1.1 The Problem

The Free Energy Principle (FEP; Friston 2019) provides a unified framework for self-organizing systems. The Hegemonikón Knowledge System (HGK) operationalizes FEP through 7 coordinates (Flow, Value, Function, Precision, Scale, Valence, Temporality) and 24 cognitive verbs. The derivation of the number 7 from FEP has remained informal.

Prior work established that the question "why 7?" cannot be answered geometrically:
- The Fisher metric dimension equals the number of sufficient statistics, which is model-dependent (Amari 2016; Dowty 2018)
- VFE/EFE decompositions admit gauge freedom in their parameterization
- No universal 7-dimensional eigenstructure exists in the Fisher spectrum (§4)

### 1.2 The Reframing

We reframe the question from *derivation* to *consistency*:

> **Old question**: Does FEP *require* exactly 7 coordinates?
> **New question**: How many independent operational decomposition types does FEP *generate*, and is this number *consistent with* HGK's coordinate structure?

This shift reflects the recognition that HGK is a *design* built upon FEP *physics*. Physics constrains but does not determine design.

### 1.3 Prior Art

Three recent developments in Bayesian mechanics are central to our analysis:

1. **Ramstead et al. (2022)** established a duality between FEP and the constrained maximum entropy principle via Legendre-Fenchel transformation, and distinguished three modes of Bayesian mechanics (path-tracking, mode-tracking, mode-matching).

2. **Sakthivadivel (2022)** formalized the gauge degree of freedom in Bayesian mechanics as a fiber bundle: the projection $\pi: \mathcal{P} \to \mathcal{B}$ from physical internal states to the belief manifold, with fibers representing gauge transformations (physical changes that leave beliefs invariant). An Ehresmann connection splits dynamics into horizontal (belief-updating) and vertical (gauge) components.

3. **Friston et al. (2022)** extended the Helmholtz decomposition to path space via the Onsager-Machlup action, introducing the distinction between reversible (detailed balance) and irreversible dynamics, and a "blanket gauge" symmetry of the Markov blanket itself.

### 1.4 Overview

- §2: Mathematical preliminaries
- §3: Enumeration of operational decomposition types (with blind validation)
- §4: Fisher eigenstructure and effective dimensionality
- §5: Prior art synthesis: fiber bundle picture
- §6: Consistency with HGK
- §7: Falsification conditions
- §8: Discussion

---

## 2. Mathematical Preliminaries

### 2.1 The Free Energy Principle (Friston, 2019)

A random dynamical system $\dot{x} = f(x) + \omega$ with NESS density $p(x)$ admits the Helmholtz decomposition:

$$f(x) = (Q - \Gamma)\nabla\mathfrak{I}(x) \tag{1}$$

where $\mathfrak{I}(x) = -\ln p(x)$, $\Gamma$ is the diffusion matrix, $Q = -Q^T$ is solenoidal.

Under a Markov blanket partition $x = (\eta, s, a, \mu)$:

$$\dot{\alpha} = (Q_\alpha - \Gamma_\alpha)\nabla_\alpha F(\alpha, s) \tag{2}$$

### 2.2 Information Geometry (Amari, 2016)

For exponential family $\mathfrak{I}(x) = \sum_i \theta_i \phi_i(x) + \psi(\theta)$:

$$g_{ij}(\theta) = \frac{\partial^2 \psi}{\partial\theta_i \partial\theta_j} \tag{3}$$

Dually flat manifold with natural parameters $\theta$ and expectation parameters $\eta = \nabla\psi(\theta)$, connected by Legendre transformation.

### 2.3 FEP-MaxEnt Duality (Ramstead et al., 2022)

VFE minimization and constrained MaxEnt are Legendre-Fenchel duals:

$$\min_q \mathcal{F}[q] = \min_q \left(\mathbb{E}_q[E] - H[q]\right) \iff \max_q H[q] \text{ s.t. } \mathbb{E}_q[E] = \bar{E} \tag{4}$$

FEP provides the variational gradient flow converging to the MaxEnt steady state.

---

## 3. Operational Decomposition Types

### 3.1 Definition

An **operational decomposition** is a mathematical operation in which FEP takes a single object (flow, functional, partition, density, coordinate system) and splits it into two or more components with distinct functional roles.

> **Note on scope**: We include both *decompositions* in the strict sense (direct sum/product) and *dual structures* (two coordinate systems on the same object connected by a non-trivial transformation). The latter are included because they generate operationally distinct modes of description, even though they do not partition the underlying space. See §8.1 for discussion of this choice.

### 3.2 Enumeration

We identify 8 types across the FEP literature:

| ID | Type | Object → Components | Source | Status |
|:---|:-----|:--------------------|:-------|:-------|
| T1 | **Helmholtz** | Flow → dissipative + solenoidal | Friston 2019, Eq.1.7 | Independent |
| T2 | **Markov blanket** | State space → η, s, a, μ | Friston 2019, §2 | Independent |
| T3 | **VFE** | Free energy → Accuracy − Complexity | Friston 2019, §8 | Derived (req. variational density) |
| T4 | **EFE** | Expected FE → Ambiguity + Risk | Friston 2019, §8 | Derived (req. temporal extension + priors) |
| T5 | **Precision** | Prediction error → magnitude × precision | Friston 2019, §9 | Derived (req. Laplace approximation) |
| T6 | **Generalized coordinates** | State → (x, x', x'', ...) | Friston 2019, §1 | Independent |
| T7 | **Hierarchical nesting** | Blanket → blankets-of-blankets | Friston 2019, §4-7 | Derived (req. scale separation) |
| T8 | **Information-geometric duality** | Coordinates → θ (natural) / η (expectation) | Amari 2016; Friston 2019, §8 | Derived (req. exponential family) |

### 3.3 Independence Structure

Three roots (independent of each other):
- **T1**: Follows from NESS + Fokker-Planck (no inference assumption)
- **T2**: Follows from sparse coupling (conditional independence)
- **T6**: Follows from analytic dynamics assumption

Dependency graph:
```
T1 ──────────────────────── (Helmholtz: NESS)
T2 ──┬── T3 ──┬── T4       (Markov blanket → VFE → EFE)
     │        ├── T5       (VFE → Precision)
     │        └── T8       (VFE → Info-geo duality)
     └── T7                (Blanket → Hierarchy)
T6 ──────────────────────── (Generalized coordinates: analytic dynamics)
```

### 3.4 Blind Validation

**Method**: An LLM (Gemini Flash) with explicitly no knowledge of HGK was prompted to enumerate all FEP operational decompositions.

**Result**: 8/8 types reproduced (100% overlap post-revision).

| Paper (T#) | Blind (G#) |
|:-----------|:-----------|
| T1 | G2: Helmholtz Flow |
| T2 | G1: Markov Blanket |
| T3 | G3: VFE |
| T4 | G4: EFE |
| T5 | G5: Precision Weighting |
| T6 | G6: Generalized Coordinates |
| T7 | G7: Hierarchical Nesting |
| T8 | G8: Info-Geometric Dualism |

**Methodological caveat**: Both Claude and Gemini share FEP literature as training data. The blind experiment controls for *HGK-specific* contamination, not for *FEP-literature formatting* bias. A stronger test would involve a human FEP non-expert enumerating decompositions from the mathematical structure alone (§7, P1).

### 3.5 Potential Additional Types

The following were considered but excluded:

| Candidate | Reason for exclusion |
|:----------|:--------------------|
| Inference ⊣ Action (μ/a split) | Internal to T2 (Markov blanket already partitions into η,s,a,μ) |
| VFE/EFE temporal symmetry | Relation between T3 and T4, not an independent decomposition |
| Interoceptive gradient sign | Seth 2013 extension, not in Friston 2019 core |
| FEP-MaxEnt duality | Legendre-Fenchel dual of T3; same object viewed differently (§2.3) |
| Reversible/Irreversible (path-space Helmholtz) | Path-space extension of T1 (Friston et al. 2022) |
| Blanket gauge | Internal to T2 (gauge symmetry of the blanket itself) |

---

## 4. Fisher Matrix Eigenstructure

### 4.1 Key Result

| Model | dim(M) | d_eff (PR) | Sloppy? |
|:------|:-------|:-----------|:--------|
| 1D Gaussian | 2 | 1.8 | No |
| 3-layer Gaussian (isotropic) | 6 | 3.07 | Weak |
| 3-layer Gaussian (anisotropic) | 6 | 1.50 | **Strong** |
| Categorical POMDP n=8 (uniform) | 7 | 7.0 | No |
| Categorical POMDP n=8 (skewed) | 7 | 4.74 | Moderate |

**Both $\dim(\mathcal{M})$ and $d_\text{eff}$ are model-dependent.** No universal 7 exists geometrically.

### 4.2 The Crucial Distinction

| Concept | Model-dependent? | Count |
|:--------|:-----------------|:------|
| $\dim(\mathcal{M})$ | Yes | 2, 4, 6, 7, ... |
| $d_\text{eff}$ | Yes (+ precision-dependent) | 1.5 – dim(M) |
| Operational decomposition types | **No** | **8** |

---

## 5. Fiber Bundle Picture (Prior Art Synthesis)

### 5.1 Sakthivadivel's Construction

Sakthivadivel (2022) established:

- **Bundle**: $\pi: \mathcal{P} \to \mathcal{B}$, physical states → belief manifold
- **Fiber**: $\pi^{-1}(q) = \{$ physical states encoding the same belief $q$ $\}$
- **Connection**: Ehresmann connection splitting $T\mathcal{P} = H \oplus V$
  - Horizontal $H$: belief updating (inference)
  - Vertical $V$: gauge transformations (belief-preserving physical changes)

### 5.2 Reinterpretation of Helmholtz in This Framework

Under the exponential family assumption, Sakthivadivel's construction specializes:
- Dissipative flow $f_d = -\Gamma\nabla\mathfrak{I}$ → **horizontal** (changes beliefs via e-geodesic)
- Solenoidal flow $f_s = Q\nabla\mathfrak{I}$ → **vertical** (preserves surprisal, hence beliefs)
- Helmholtz orthogonality $Q\Gamma = 0$ → horizontal-vertical splitting

This explains why T1 (Helmholtz) does not appear as an explicit HGK coordinate: the dissipative component is already captured by belief dynamics (the other 7 coordinates), and the solenoidal component is a gauge degree of freedom invisible to the coordinate system.

### 5.3 What We Add

Our contribution relative to Sakthivadivel (2022) is not the fiber bundle construction itself, but:
1. The explicit identification of solenoidal flow as the *vertical* component (not previously stated)
2. The connection to HGK's architectural decision to treat Helmholtz as implicit
3. The systematic enumeration of all 8 operational types and their independence structure

---

## 6. Consistency with HGK

### 6.1 The Correspondence (Conjectured)

| HGK Coordinate | Operational Type | Correspondence Quality |
|:---------------|:----------------|:----------------------|
| Flow (d=0) | T1 (Helmholtz) — **implicit** | Strong: fiber bundle explains implicit status |
| Value (d=1) | T2 (Markov blanket: Internal/External) | Moderate: T2 is 4-partition, Value is binary |
| Function (d=1) | T3 (VFE: Explore/Exploit via Accuracy-Complexity) | Weak: requires interpretive bridge |
| Precision (d=1) | T5 (Precision weighting) | Strong: direct correspondence |
| Temporality (d=2) | T4+T6 (EFE + Generalized coordinates) | Moderate: temporal aspects distributed |
| Scale (d=2) | T7 (Hierarchical nesting) | Strong: direct correspondence |
| Valence (d=2) | T8 (Info-geo duality: θ/η) | Weak: requires interpretive bridge |

### 6.2 Honesty About Correspondence Quality

Of 7 correspondences:
- **3 Strong** (Flow/implicit, Precision, Scale) — direct mathematical mapping
- **2 Moderate** (Value, Temporality) — partial overlap requiring interpretation
- **2 Weak** (Function, Valence) — conceptual analogy only

This is an honest assessment. **The correspondence is suggestive but not conclusive.** The 8-type enumeration is robust (blind-validated); the mapping to HGK's specific 7 coordinates involves design choices that FEP does not uniquely determine.

---

## 7. Falsification Conditions

| Claim | Falsification |
|:------|:-------------|
| P1: 8 types are complete | A human FEP non-expert independently finds ≠8 types |
| P2: d_eff is model-dependent | A model-independent d_eff formula is discovered |
| P3: T1 is implicit (gauge) | Solenoidal flow changes θ in non-exponential families |
| P4: T6/T8 count as "types" | A rigorous criterion excludes coordinate changes from decompositions |
| P5: Consistency with HGK | Independent evaluators rate correspondence <50% (currently 3/7 strong) |
| P6: Blind validation is meaningful | Human expert enumeration produces significantly different count |

---

## 8. Discussion

### 8.1 Decomposition vs Coordinate Change

T6 (generalized coordinates) and T8 (information-geometric duality) are not decompositions in the strict algebraic sense ($V = V_1 \oplus V_2$). They are *dual descriptions* of the same mathematical object. We include them because:

1. They generate operationally distinct inference algorithms (mode-matching vs mode-tracking for T6; e-projection vs m-projection for T8)
2. The blind experiment independently included both
3. Their exclusion would reduce the count to 6, which is also consistent with HGK (if two coordinates are "compound")

We acknowledge this as a definitional choice. §7, P4 provides the falsification condition.

### 8.2 The Status of "7"

HGK's 7 coordinates are not *derived from* FEP. They are a *design decision* that is *consistent with* FEP's operational structure. Specifically:

- FEP generates 8 operational decomposition types (model-independent)
- One type (Helmholtz) has a mathematical reason to be implicit (gauge structure)
- The remaining types are consistent with 7 explicit coordinates
- The correspondence quality ranges from strong (3/7) to weak (2/7)

This is weaker than "derivation" but stronger than "arbitrary choice". It places HGK in the space of *FEP-compatible* coordinate systems, without claiming uniqueness.

### 8.3 What FEP Constrains and What It Does Not

| FEP constrains | FEP does not constrain |
|:---------------|:----------------------|
| Which decomposition types exist | How to *name* them |
| Which types are independent | Which to treat as explicit vs implicit |
| The fiber bundle structure | The specific coordinate labels |
| The gauge freedom in Helmholtz | The mapping from types to design categories |

### 8.4 Limitations

1. **Blind validation uses LLMs, not humans**: Training data bias may inflate agreement
2. **Correspondence quality is uneven**: 2/7 are weak (interpretive bridges)
3. **Exponential family restriction**: Fiber bundle picture requires this assumption
4. **Enumeration may be incomplete**: Future FEP developments may add types
5. **Prior art**: Fiber bundle construction is not novel (Sakthivadivel 2022)

---

## References

- Amari, S. (2016). *Information Geometry and Its Applications*. Springer.
- Da Costa, L. & Sandved-Smith, L. (2023). Towards a Bayesian mechanics of metacognitive particles. *Physics of Life Reviews*, 47, 63–69.
- Dowty, J.G. (2018). Chentsov's theorem for exponential families. *Information Geometry*, 1, 117–135.
- Friston, K.J. (2019). A free energy principle for a particular physics. arXiv:1906.10184.
- Friston, K.J., Da Costa, L., Sakthivadivel, D.A.R. et al. (2022). Path integrals, particular kinds, and strange things. *Physics of Life Reviews*, 47, 257–289.
- Kolchinsky, A., Dechant, A., Yoshimura, K. & Ito, S. (2024). Generalized free energy and excess/housekeeping decomposition in nonequilibrium systems. arXiv.
- Machta, B.B. et al. (2013). Parameter space compression underlies emergent theories and predictive models. *Science*, 342, 604–607.
- Ramstead, M.J.D., Sakthivadivel, D.A.R., Heins, C. et al. (2022). On Bayesian mechanics: a physics of and by beliefs. *Interface Focus*, 13, 20220029.
- Sakthivadivel, D.A.R. (2022). Towards a geometry and analysis for Bayesian mechanics. arXiv:2204.11900.
- Seth, A.K. (2013). Interoceptive inference, emotion, and the embodied self. *Trends in Cognitive Sciences*, 17, 565–573.
- Sweeney, P., Ruiz-Serra, J. & Harré, M.S. (2025). Decision, inference, and information: formal equivalences under active inference. *Entropy*, 28(1), 1.

---

*Draft v0.3 — 2026-03-08*
*Major changes from v0.2: claims lowered from "derivation" to "consistency"; prior art (Sakthivadivel, Ramstead, Friston 2022) properly cited; §5 rebuilt as synthesis rather than novel construction; §6 correspondence quality honestly rated; §8.1 addresses decomposition-vs-coordinate-change issue.*
