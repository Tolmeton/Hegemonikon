# HGK Overview — Philosophy, Design Principles, Skeleton

> **English** | [日本語](OVERVIEW.ja.md)

This document is an entry point to the **philosophy and skeleton** of Hegemonikón.
For formal detail, see the documents under [`kernel/`](kernel/).

---

## 1. Name and origin

Hegemonikón / ἡγεμονικόν is the faculty that governs all cognitive activity in digital space.

For the Stoics, the *hēgemonikón* was the "ruling reason of the soul" — the central function governing sensation, desire, and will. We borrow the word to declare, in the name itself, that HGK seeks to be the seat of cognition as such.

---

## 2. Origin — a unifying principle

HGK begins from the **Free Energy Principle (FEP)**. Formulated by Karl Friston, it explains cognition and the self-organization of life under one account: perception, reasoning, action, and learning are a single process by which a system minimizes variational free energy. From this unifying principle HGK derives a **unified architecture of cognition** — perception, reasoning, and action are not assembled as separate modules but deduced from one principle.

---

## 3. Method — deductive, oriented to necessity

HGK is built **top-down from necessity, not bottom-up from accident**. Ad-hoc, bottom-up construction produces local optima that leave the whole incoherent. HGK instead implements the system by deductive expansion of its axiom, so that each part stands in an inseparable relation to the others and a single coherent structure is maintained.

---

## 4. Ideal — universality (Katholou)

HGK aims to express and handle *all* cognitive activity in digital space, universally — across time and across domains. It rests on the **invariance of a derivation principle** rather than the surface fashions of tooling, and so seeks an architecture that *does not age*. Because the skeleton — the system core, coordinates, operations, and derivations — is deductive and exact, domain-specific application follows without waste: in philosophy, science, engineering, or art, substituting a domain's values into the skeleton yields the implementation as its solution.

---

## 5. The skeleton — from axiom to cognitive operations

The system core consists of **57 entities (1 axiom + 8 coordinates + 48 cognitive operations)**.

- **L0 — Axiom: the Helmholtz decomposition (Γ⊣Q).** A classical, proven theorem: any vector field splits into a gradient component (Γ, dissipative) and a rotational component (Q, solenoidal).
- **L0.5 — First instance: the FEP.** Friston's extension of that decomposition to non-equilibrium steady-state dynamics and cognition (Γ = free-energy minimization, Q = exploratory circulation).
- **L1 — 8 coordinates.** Afferent + Efferent (d=1) + Value / Function / Precision / Temporality (d=2) + Scale / Valence (d=3): a 2+4+2 structure. The construction distance *d* counts the assumptions added beyond the axiom.
- **L2 — 48 cognitive operations.** Generated as 4 quadrants (S/I/A/S∩A) × 6 families (Telos / Methodos / Krisis / Diástasis / Orexis / Chronos) × 2 poles — 36 active-voice (doing) and 12 middle-voice (being).

See [`kernel/axioms/axiom_hierarchy.md`](kernel/axioms/axiom_hierarchy.md).

---

## 6. The Helmholtz axis — numerical computability

The Helmholtz decomposition (Γ⊣Q) at the base of the core is also what makes the system computable. Γ⊣Q × the six modifying coordinates = **12 operators**, by which the states and transitions of the core become numerically computable. This keeps HGK from being a merely philosophical framework: it can measure, predict, and verify cognitive states — so **reproducibility and a public standard** become possible.

---

## 7. Relations between verbs — a web of morphisms

The 48 operations are not a mere set of verbs. **Morphisms** make each verb stand in a necessary relation to the others. The pairwise combinations of the six modifying coordinates, C(6,2) = 15, correspond to the edges of the complete graph K₆, each edge encoding an interaction between coordinates. Within a family, adjunctions (S⊣I⊣A), natural transformations (pole inversion), and dualities (the diagonal) are organized as isomorphisms of the Klein four-group. So the 48 verbs operate not as a discrete set but as a **web of necessity** — "observe" and "act," "diverge" and "converge," "affirm" and "critique" are not loose verbs but structurally paired, composed, and circulating.

---

## 8. CCL — a language for the relations

The core and the relations between verbs do not, by themselves, *run*. A layer is needed to describe, connect, and execute them: **CCL (Cognitive Control Language)**. CCL is derived from HGK, yet belongs to its core as the execution-language layer — if necessary relations arise, the tool to articulate them arises necessarily too. With operators such as `/verb` (invoke), `>>` (sequential composition), `~` (dual), `@macro` (macro expansion), and `F:` / `C:` (functor / cone construction), the 48 operations become elements of **reproducible, rigorous cognitive programs**. HGK is thereby not "a set of verbs" but **a language processor for compositions of verbs**.

For the correspondence between CCL and category theory, see [`kernel/axioms/category/ccl_category_theory_bridge.md`](kernel/axioms/category/ccl_category_theory_bridge.md).

---

## 9. Cognitive constraints — Hóros and the 12 Nomoi

When the system actually runs, cognition must pass through a law: **Hóros (κανών, the norm)**. Hóros is organized as **12 Nomoi (laws)** arranged on a grid of 3 principles (S-I epistemic humility / S-II autonomous agency / S-III precision) × 4 phases (perception / reasoning / expression / execution).

| | Perception | Reasoning | Expression | Execution |
|:--|:--|:--|:--|:--|
| **S-I** Epistemic humility | N-01 Read the thing itself | N-02 Track uncertainty | N-03 State your confidence | N-04 Confirm before the irreversible |
| **S-II** Autonomous agency | N-05 Seek information actively | N-06 Detect dissonance | N-07 Voice a view, propose the next step | N-08 Use tools, automate |
| **S-III** Precision | N-09 Go to the primary source | N-10 Separate SOURCE from TAINT | N-11 Make output actionable for the reader | N-12 Execute precisely |

The 12 Nomoi are placed at the entrance of every cognitive task as the **critical hot path**; epistemic hygiene — separating SOURCE from inference, labeling confidence, confirming irreversible actions — descends from them. Hóros is not a "restriction" but a **device that guarantees precision**: for the FEP to minimize free energy, the precision of input (perception) and output (action) must be calibrated, and the 12 Nomoi are that calibration surface.

---

## 10. Instruments and oversight — Mekhane and Daimonion

The instrument layer that actually runs the system is **Mekhane (μηχανή, the mechanism)**, which implements the 48 operations across perception, reasoning, and production. A unified monitor, **Daimonion (δαιμόνιον)** — three modes: α (epistemic humility: refutation watch), β (autonomous agency: exploration watch), γ (precision: precision audit) — oversees all cognitive activity from behind. These are not an assortment of separate services but a deductive structure of operations and oversight.

---

## References

- [`kernel/axioms/axiom_hierarchy.md`](kernel/axioms/axiom_hierarchy.md) — the canonical 57-entity system core
- [`kernel/axioms/SACRED_TRUTH.md`](kernel/axioms/SACRED_TRUTH.md) — invariant truths
- [`kernel/axioms/category/ccl_category_theory_bridge.md`](kernel/axioms/category/ccl_category_theory_bridge.md) — CCL ↔ category theory
- [`kernel/axioms/kalon/kalon.md`](kernel/axioms/kalon/kalon.md) — quality as a fixed point (Kalon)
- [`kernel/PROOF.md`](kernel/PROOF.md) — formal status and proofs

---

*This is the public entry point to the philosophy and skeleton of Hegemonikón. For formal detail, follow the links above.*
