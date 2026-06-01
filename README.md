# Hegemonikon (ἡγεμονικόν)

**The unifying principle and framework for AI cognition.**  
FEP as engine, category theory as grammar.

> **English** | [日本語](README.ja.md)

---

## What is Hegemonikon?

Hegemonikon (ἡγεμονικόν) — the Stoic term for *the ruling faculty of the soul*.

This is a universal cognitive harness for AI agents: a single axiomatic system that governs how an AI perceives, reasons, and acts. It is not tied to any specific model, IDE, or toolchain. Frameworks come and go; the axioms remain.

**One axiom.** The Free Energy Principle (FEP) — every self-organizing system minimizes variational free energy.

**Eight coordinates.** Two dimensions of Markov Blanket topology (Afferent/Efferent → 4 quadrants) and six modifying axes (Value, Function, Precision, Scale, Valence, Temporality).

**48 cognitive operations.** 4 quadrants × 6 axes × 2 poles = the complete set of cognitive verbs an agent can perform, formalized as functors in a category-theoretic framework.

## Core Architecture

```
FEP (1 axiom)
├── 3 Stoicheia (principles)
│   ├── Tapeinophrosyne — epistemic humility: distrust your priors
│   ├── Autonomia — active inference: don't be a passive tool
│   └── Akribeia — precision: calibrate your signal weights
├── 12 Nomoi (laws) — 3 principles × 4 phases
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
| **CCL** (Cognitive Command Language) | A DSL for composing cognitive operations with category-theoretic operators |
| **Typos** | A prompt metalanguage — the universal syntax for human↔LLM communication |
| **Hóros** | 12 behavioral laws derived from FEP, enforced through hooks and runtime monitoring |
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

## Theoretical Foundations

Hegemonikon rests on two pillars:

- **Free Energy Principle (FEP)** — Karl Friston's variational framework. Every structure in this system is a specific instance of VFE minimization: perception as precision-weighting, action as active inference, learning as model updating.

- **Category Theory** — The grammar of structure. Cognitive operations are functors. Family relationships are adjunctions (F⊣G). Quality (Kalon) is the fixed point Fix(G∘F). Drift between states lives in a [0,1]-enriched category.

This is not metaphor. The axiom hierarchy is formally derived, and the 48 operations are the complete enumeration under the given coordinates.

## Status

Active development. The axiomatic core (Kernel) is stable; the runtime (Mekhane) and tooling evolve with use.

## Author

**Tolmetes** (τολμητής — *one who dares*)  
[@tolmeton](https://github.com/Tolmeton)

## License

[MIT](LICENSE)
