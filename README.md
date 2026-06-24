# Hegemonikon (ἡγεμονικόν)

**The unifying principle and framework for AI cognition.**  
FEP as engine, category theory as grammar.

> **English** | [日本語](README.ja.md)

---

## What is Hegemonikon?

Hegemonikon (ἡγεμονικόν) — the Stoic term for *the ruling faculty of the soul*, the central function that governs perception, desire, and will.

Hegemonikon is a universal cognitive architecture for AI agents. Perception, reasoning, and action are not assembled as separate modules — they are **deduced from a single principle**. It is bound to no model, IDE, or toolchain. Frameworks come and go; the derivation remains.

## Why deduction, not assembly

Most agent frameworks grow bottom-up: ad-hoc parts bolted together, each locally optimized and globally incoherent. Hegemonikon is built top-down. Every component descends from one axiom, so each part stands in a necessary relation to every other — the whole holds together as a single structure.

The aim is permanence. Resting on the **invariance of a derivation principle** rather than the surface fashions of tooling, Hegemonikon seeks an architecture that *does not age*. The skeleton — axioms, coordinates, operations — is deductive and exact; filling it with a domain's values yields the implementation, in philosophy, science, engineering, or art alike.

## The axiom stack

- **L0 — Axiom: the Helmholtz decomposition (Γ⊣Q).** A classical, proven theorem of mathematics: any vector field splits into a gradient component (Γ, dissipative) and a rotational component (Q, solenoidal).
- **L0.5 — First instance: the Free Energy Principle (FEP).** Friston's extension of that decomposition to non-equilibrium steady-state dynamics and cognition — Γ as free-energy minimization, Q as exploratory circulation.
- **L1 — 8 coordinates.** Afferent + Efferent (Markov-blanket topology), plus six modifying axes: Value, Function, Precision, Temporality, Scale, Valence.
- **L2 — 48 cognitive operations.** 4 quadrants × 6 families × 2 poles — the complete enumeration of an agent's cognitive verbs, formalized as functors.

## Core Architecture

```
FEP — first instance of the L0 axiom (Helmholtz decomposition, Γ⊣Q)
├── 3 Stoicheia (principles)
│   ├── Tapeinophrosyne — epistemic humility: distrust your priors
│   ├── Autonomia — active inference: don't be a passive tool
│   └── Akribeia — precision: calibrate your signal weights
├── Hóros (cognitive constraint system)
│   └── 12 Nomoi (the complete set of twelve laws) — 3 principles × 4 phases
└── 48 Cognitive Operations — 6 families × 8 verbs
    ├── Telos (purpose): noēsis, boulēsis, zētēsis, energeia, ...
    ├── Methodos (strategy): skepsis, synagōgē, peira, tekhnē, ...
    ├── Krisis (commitment): katalēpsis, epochē, proairesis, dokimasia, ...
    ├── Diástasis (scale): analysis, synopsis, akribeia, architektonikē, ...
    ├── Orexis (valence): bebaiōsis, elenchos, prokopē, diorthōsis, ...
    └── Chronos (time): hypomnēsis, promētheia, anatheōrēsis, proparaskeuē, ...
```

## Key Components

| Component | Description |
|:----------|:------------|
| **CCL** (Cognitive Control Language) | A DSL for composing cognitive operations with category-theoretic operators |
| **Typos** | A prompt metalanguage — the universal syntax for human↔LLM communication |
| **Hóros** | Cognitive constraint system — the normative layer that calibrates perception, reasoning, expression, and execution at runtime |
| **Nomoi** | The complete set of twelve laws that constitute Hóros. `Nomos` is singular; `Nomoi` is plural |
| **Daimonion** | Unified monitoring system — Socrates' inner voice, implemented as 3-mode oversight |

## Repository Structure

```
kernel/      — Axioms, theorems, formal foundations (SACRED) ✅ Published
nous/        — Knowledge, planning, project management (future)
mekhane/     — Runtime infrastructure (future)
mneme/       — Long-term memory (future)
poiema/      — Creative output (future)
peira/       — Experiments and prototypes (future)
```

> **Phase 2**: Only `kernel/` is published. Other components will follow in future releases.

## Where to start

| If you want… | Read |
|:--|:--|
| The philosophy and skeleton in one read | [`OVERVIEW.md`](OVERVIEW.md) |
| The shortest entry into the kernel | [`kernel/README.md`](kernel/README.md) |
| The full axiom hierarchy and all 48 operations | [`kernel/axioms/axiom_hierarchy.md`](kernel/axioms/axiom_hierarchy.md) |
| How CCL maps onto category theory | [`kernel/axioms/category/ccl_category_theory_bridge.md`](kernel/axioms/category/ccl_category_theory_bridge.md) |
| Quality as a fixed point (Kalon) | [`kernel/axioms/kalon/kalon.md`](kernel/axioms/kalon/kalon.md) |
| Formal status and proofs | [`kernel/PROOF.md`](kernel/PROOF.md) · [`kernel/axioms/formalization/`](kernel/axioms/formalization/) |

## Theoretical Foundations

Hegemonikon rests on two pillars:

- **Free Energy Principle (FEP)** — Karl Friston's variational framework, the cognitive instance of the L0 axiom (the Helmholtz decomposition). Every structure in this system is a specific case of VFE minimization: perception as precision-weighting, action as active inference, learning as model updating.

- **Category Theory** — The grammar of structure. Cognitive operations are functors. Family relationships are adjunctions (F⊣G). Quality (Kalon) is the fixed point Fix(G∘F). Drift between states lives in a [0,1]-enriched category.

This is not metaphor. The axiom hierarchy is formally derived, and the 48 operations are the complete enumeration under the given coordinates.

## Status

Active development. The axiomatic core (Kernel) is stable; the runtime (Mekhane) and tooling evolve with use.

## Author

**Tolmetes** (τολμητής — *one who dares*)  
[@tolmeton](https://github.com/Tolmeton)

## License

[MIT](LICENSE)
