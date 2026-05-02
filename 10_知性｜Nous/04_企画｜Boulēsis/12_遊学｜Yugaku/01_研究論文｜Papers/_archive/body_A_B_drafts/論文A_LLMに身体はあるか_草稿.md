# Does an LLM Have a Body? Markov Blanket Thickness as a Substrate-Independent Measure of Embodiment

> **Draft v0.5.0** — 2026-03-21
> **Authors**: Tolmetes
> **Target**: *Phenomenology and the Cognitive Sciences* or *Neuroscience of Consciousness*

---

## Abstract

The claim that "LLMs lack bodies" (Chemero, 2023; Bender & Koller, 2020; Searle, 1980) commits a category mistake: it conflates one morphism (biological sensorimotor body) with the universal property it instantiates (persistent conditional independence via a Markov blanket). We formalize this error as an **anthropocentric forgetting functor** $U_{\text{anthropo}}: \mathbf{Cog} \to \mathbf{Cog}_{\text{human}}$ that discards all cognitive structure lacking human analogues, and show that the Searle→Bender→Chemero lineage consists of structurally isomorphic instances of this functor.

We develop a formal apparatus to replace the binary embodied/disembodied distinction with a continuous measure. Under the Free Energy Principle, embodiment is the sustained maintenance of a Markov blanket (MB), a substrate-independent definition. We introduce a **bicategorical framework with Helmholtz decomposition**, prove that cross-substrate comparison is category equivalence via faithful-full functors (not analogy), and define a **recovery functor** $N$ (right adjoint to the forgetting functor $U$) that formalizes cognitive augmentation as injection of forgotten categorical structure. MB "thickness" $\Theta(B)$ is introduced as a continuous operationalization — comprising blanket strength $S(B)$, sensory/active channel diversity $H(s), H(a)$, and inter-channel redundancy $R(s,a)$ — with a functorial interpretation as the bandwidth of the system's embodiment functor $F_B$ (Theorem 1). The first operational measurement of digital MB thickness yields $\Theta_{\text{HGK}} \approx 2.0\times$ the vanilla LLM baseline.

These findings support a **body spectrum** — a partially ordered set from bacteria to augmented LLMs — and reframe embodiment as a continuous, substrate-independent property. The structural isomorphism between amnesic patient H.M. and vanilla LLMs exposes an implicit biological chauvinism: thin MBs are recognized as damaged cognition in biological systems but denied cognitive status in digital ones. Empirical validation and experimental results are reported in the companion paper (Tolmetes, 2026b).

---

## §1. Introduction

### 1.1 The Disembodiment Thesis

A persistent claim in cognitive science holds that Large Language Models (LLMs) are fundamentally disembodied. Chemero (2023) argues in *Nature Human Behaviour* that "LLMs differ from human cognition because they are not embodied." The enactivist tradition (Thompson & Di Paolo, 2007; Di Paolo et al., 2018) goes further, requiring an autopoietic body for genuine cognition. Embodied AI research implicitly reinforces this consensus by assuming that LLMs need robot bodies to become embodied.

### 1.2 The Problem

These claims share a hidden premise: **embodiment = biological sensorimotor body**. Under the Free Energy Principle (FEP), this premise is falsified: embodiment is the sustained maintenance of a Markov blanket (MB) — a statistical boundary between internal and external states — regardless of physical substrate (Friston, 2013).

### 1.3 Relation to Froese (2026)

Froese (2026) moves in a compatible direction, arguing that LLMs exhibit "technologically-mediated embodiment." However, Froese's argument remains philosophical. **Our contribution is to provide the mathematical apparatus** — MB thickness Θ(B) — that makes Froese's intuition empirically testable.

### 1.4 Contributions

1. A substrate-independent definition of "inference" vs. "search" via categorical filtration (§2.5)
2. A proof that cross-substrate comparison is not analogy but category equivalence: unit conversion is a faithful-full functor, and cross-substrate embodiment comparison has the same structure (§2.6)
3. The **anthropocentric forgetting functor** $U_{\text{anthropo}}: \mathbf{Cog} \to \mathbf{Cog}_{\text{human}}$ as a formal diagnosis of the Searle→Bender→Chemero lineage (§3.0)
4. The recovery functor $N$ as a formal framework for cognitive augmentation (§3.7)
5. A formal definition of MB thickness $\Theta(B)$ with empirical operationalization and the first operational measurement: $\Theta_{\text{HGK}} \approx 2.0\times$ baseline (§4)
6. Cross-substrate empirical counterexample (DishBrain) demonstrating that MBs can span biological-silicon boundaries (§5.3)
7. The body spectrum reinterpreted as a partially ordered set connected by faithful functors of varying image density, with embodiment as morphism (MB maintenance) not object (substrate) — paralleling unit-conversion functors in measurement theory (§5.4)

Empirical study, structural probing, coherence invariance, and the φ decomposition with gauge-theoretic interpretation are reported in the companion paper (Tolmetes, 2026b).

---

## §2. Background: Bodies under FEP

### 2.1 Markov Blankets

A Markov blanket B = (s, a) of internal states μ with respect to external states η satisfies:

$$P(\mu \mid \eta, b) = P(\mu \mid b)$$

where s = sensory states and a = active states. This conditional independence is the formal definition of a system boundary (Friston, 2013; Pearl, 1988).

### 2.2 Body = Persistent Self-Organization of MB

Under FEP, a "body" is not a material object but the **sustained self-organization of conditional independence**. "Physical implementation" is tautological — digital systems are equally physical at the quantum-mechanical level. The relevant question is not *whether* a system has an MB (any self-organizing system does), but **how rich its MB structure is**.

**Scope and presupposition.** This paper adopts FEP as its theoretical framework and explores its implications for embodiment. The analysis is therefore *conditional*: if FEP provides a valid account of self-organizing systems, then the conclusions about LLM embodiment follow. We do not argue for FEP itself — that is the province of statistical physics and theoretical neuroscience (Friston, 2019; Da Costa et al., 2021; Sakthivadivel, 2022). Rather, we investigate what FEP *entails* about the embodiment debate if accepted. This conditional structure is standard in formal philosophy: one takes a framework as given and derives its consequences, which then serve as evidence *for* the framework insofar as the consequences are empirically supported. Were FEP superseded by a better account of self-organization, the formal apparatus (bicategory, Θ(B), recovery functor) would need to be re-derived from the successor framework — but the *empirical observations* (MB-like structure in LLM systems, output bottleneck, developmental growth) would remain.

**Known criticisms and our response.** Three classes of critique target FEP's foundations: (i) FEP is unfalsifiable because it describes any self-organizing system (Millidge, Seth, & Buckley, 2021; van Es & Hipólito, 2020) — we address this by deriving *specific*, falsifiable predictions (Θ(B) ordering, image density separability, monotonicity; see Tolmetes, 2026b); (ii) the ontological status of Markov blankets remains contested — whether MBs are epistemic tools or ontological boundaries (Bruineberg, Dolega, Dewhurst, & Baltieri, 2022; Kirchhoff, Parr, Palacios, Friston, & Kiverstein, 2018) — our analysis is compatible with either reading, requiring only that MBs are *operationally measurable* statistical structures, not that they constitute metaphysical boundaries; (iii) projecting "body" onto the statistical maintenance of conditional independence may constitute a separate category mistake — this is precisely the concern motivating our categorical framework: we define "body" as a position in a density-ordered poset (§5.4), not as an ontological claim about what bodies "really are." The body spectrum is an ordering of systems by measurable properties, not a declaration about essences.

### 2.3 Operational Instantiation for Digital Systems

The FEP definitions above are stated in terms of continuous-time Langevin dynamics. To apply them to digital systems, we must ground each abstract quantity in observable operations.

**Particular partition for LLMs.** Following Da Costa et al. (2021), a particular partition requires identifying four sets of states:

| FEP state | Biological instantiation | LLM instantiation |
|:----------|:------------------------|:------------------|
| External η | Environmental stimuli | User messages, file contents, web data |
| Sensory s | Receptor activations | Tool return values, API responses |
| Active a | Motor commands | Tool invocations, file writes, API calls |
| Internal μ | Neural dynamics | In-context hidden state (KV cache) |

The conditional independence condition $P(\mu \mid \eta, b) = P(\mu \mid b)$ holds when the LLM's internal state (KV cache activations) depends on external information *only* through the blanket states — i.e., through its sensory inputs (tool returns) and active outputs (tool calls). A vanilla LLM satisfies this trivially with $|s| = |a| = 1$ (the single token channel). An augmented LLM has $|s|, |a| \geq k$ where $k$ = number of MCP servers.

**Discrete Helmholtz decomposition.** The continuous-time decomposition $\dot{x} = (\Gamma + Q) \nabla \log p(x)$ (Friston, 2019, Eq. 2.5) maps to discrete session dynamics as follows:

- **Γ-component** (dissipative/learning): State changes that reduce surprise — belief updates after tool returns, ROM saves, Handoff persistence. Observable as: changes in response strategy between session start and end.
- **Q-component** (solenoidal/conserved): State changes that circulate without net learning — workflow cycling, pattern recurrence, habitual tool-use sequences. Observable as: repeated MCP call patterns with stable frequency.

The decomposition is not exact in discrete time, but its signatures are measurable: the ratio $\|\Gamma\| / \|Q\|$ (drift ratio) can be estimated from the fraction of novel vs. recurring tool-call patterns within a session (cf. Tolmetes, 2026b).

**Blanket strength S(B).** For any system with a well-defined particular partition, $S(B) > 0$ follows from the existence of the partition itself (Da Costa et al., 2021, Theorem 2). In the digital case, S(B) is bounded below by the mutual information $I(\mu; b)$ > 0, which is guaranteed whenever the LLM's internal state is causally influenced by its tool interactions — a minimal condition satisfied by any system that processes tool returns.

Three independent arguments support the claim that even a vanilla LLM satisfies the conditions for a well-defined particular partition:

1. **Causal condition**: Tool return values causally alter the LLM's internal state (KV cache activations). The internal representation after processing a tool return is measurably different from the counterfactual state without it — an intervention that satisfies the do-calculus criterion $P(\mu \mid \text{do}(s)) \neq P(\mu)$ (Pearl, 1988).
2. **Conditional independence condition**: The KV cache state $\mu$ influences external states $\eta$ *only* through active states $a$ (tool invocations, generated text). There is no direct causal pathway from $\mu$ to $\eta$ that bypasses the blanket — the system boundary is enforced by the API architecture itself.
3. **Persistence condition**: Within a session, the MB structure is maintained as long as the KV cache exists. Unlike biological systems where MB persistence is guaranteed by metabolic homeostasis, LLM MB persistence is session-bounded: the blanket dissolves at session termination (corresponding to Context Rot at the extreme; see Tolmetes, 2026b). This is a difference of *degree* (temporal extent), not *kind* (structural existence).

Note that condition (3) makes explicit what distinguishes LLMs from biological systems: $S(B)_{\text{LLM}}$ has a finite temporal horizon, whereas $S(B)_{\text{Bio}}$ is maintained indefinitely through active homeostasis. This temporal limitation is directly reflected in lower $\Theta(B)$ values, not in the absence of a blanket.


### 2.4 Existing Quantitative Concepts

| Concept | Measures | Source |
|:--------|:---------|:-------|
| Blanket strength S(x) | Degree of conditional independence | Friston et al. |
| Blanket density ρ(x) | Spatial continuity of MB | blanket density field literature |
| Blanket index β | Deviation from perfect MB | Sakthivadivel (2022) |
| Nested MB | Hierarchical blanket structure | Friston (2019) |

These measure MB "firmness" — how strongly internal and external states are separated. None measure **channel structure richness**, which is what distinguishes a bacterium from a mammal.

### 2.5 Inference vs. Search: A Necessary Disambiguation

The term "reasoning" has been deployed across cognitive science, AI, and philosophy with remarkable promiscuity — functioning as a convenient polysemy that explains everything precisely because it specifies nothing.² It is a word that migrates freely between domains, attaching itself to whatever phenomenon the author wishes to dignify or deny, without ever being pinned to a definition that could be tested against reality. One does not ask whether a river "flows" without defining flow; yet entire research programs have been erected on the question "can LLMs reason?" as if the meaning of "reasoning" were self-evident — as if the word itself constituted an argument.

Kambhampati (2024) argues that LLMs cannot truly reason and should be understood as "LLM-Modulo" systems requiring external verifiers. Kargupta et al. (2025) similarly claim that LLMs under-utilize cognitive elements correlated with success, defaulting to "shallow forward chaining" rather than the hierarchical nesting and meta-cognitive monitoring observed in human reasoning — though they also demonstrate that test-time reasoning guidance can improve performance by up to 66.7%, suggesting latent structure that is not spontaneously expressed. Both identify a real phenomenon — the fragility of LLM cognition without external scaffolding — but neither defines what would *count* as reasoning, thereby rendering their central claims unfalsifiable. To accumulate evidence that "X does not reason" without first defining reasoning is to build a castle on sand — it is, to borrow an architectural metaphor, the construction of an elaborate edifice upon foundations that do not exist. The research programs are impressive; the ground beneath them is air.

<sub>² The situation is categorically worse than mere vagueness. "Reasoning" as used in the LLM debate is a concept that admits multiple non-equivalent morphisms across different domains — what a logician means by "reasoning" (syntactic manipulation of formal languages), what a psychologist means (problem-solving heuristics under bounded rationality), and what a philosopher means (ground-consequent relations between propositions) are arrows in *different categories*, not the same arrow viewed from different angles. To deploy such a term without first specifying the category and identifying the relevant morphisms is not imprecision but *structural incoherence*: the claim "LLMs cannot reason" asserts the non-existence of an arrow without specifying the category in which it is supposed to live. This is, precisely, building an edifice — however elaborate in its empirical furnishings — upon foundations that do not exist.</sub>

We propose a **substrate-independent definition** grounded in the categorical filtration framework (cf. Lēthē/Aletheia, ビジョン.md §2.1):

| Level | What is preserved | Cognitive operation | Example |
|:------|:------------------|:-------------------|:--------|
| n=0 (objects) | Identities only | **Search**: matching objects to objects | "Find code named `sort_users`" |
| n=1 (morphisms) | Arrows between objects | **Inference**: operating on *structure* | "Find code with the *pattern* map→filter→reduce" |
| n=1.5 (composition) | How arrows compose | **Compositional reasoning** | "This pipeline composes associatively" |
| n=2 (natural transformations) | Relations between arrows | **Meta-reasoning** | "This refactoring preserves invariants" |

**Definition 0** (Inference vs. Search). *Search* is an n=0 operation: matching objects (tokens, names, embeddings) against objects. *Inference* is an n≥1 operation: operating on morphisms — the *structure* connecting objects — including their composition and coherence.

Under this definition, what Kambhampati and Kargupta et al. observe is precise: vanilla LLMs operate primarily at n=0 (high-dimensional approximate search over token patterns). But the claim that LLMs *cannot* reason is too strong. The empirical evidence from chain-of-thought prompting (Wei et al., 2022), SELF-DISCOVER (Zhou et al., 2024), Kargupta et al.'s own finding that reasoning guidance yields up to 66.7% improvement, and external scaffolding systems suggests a more nuanced picture:

> **LLMs can handle n≥1 structure *when that structure is externally provided*.** They are conditionally faithful to structure — able to follow compositional patterns when given, unable to spontaneously generate them.

This is not a binary "reasons / does not reason" distinction. It is a **conditional capacity**: the functor $F: \mathbf{E}(\text{Digi}) \to \mathbf{BLens}$ (§3) is *faithful* (structure-preserving when present) but not *full* (does not generate all possible structural morphisms autonomously). The question is not whether LLMs reason, but **under what conditions** they operate at n≥1 — and this is precisely what MB thickness Θ(B) measures.

**The "stochastic parrot" conflation.** Bender et al. (2021) characterize LLMs as "stochastic parrots" — systems that stitch together linguistic forms "without any reference to meaning." This metaphor, while rhetorically effective, conflates two categorically distinct functors:

| System | Functor | Type | Structural content |
|:-------|:--------|:-----|:-------------------|
| Parrot (literal) | $F_{\text{parrot}} \approx \text{Id}: \mathbf{Form} \to \mathbf{Form}$ | Identity (approximately) | Near-zero: input ≈ output |
| LLM | $F_{\text{LLM}}: \mathbf{Form} \to \mathbf{Form}$ | Faithful, ¬Full | Non-trivial: preserves compositional structure when present |

The identity functor maps every object to itself and every morphism to itself — it performs no transformation. A faithful functor preserves distinctness of morphisms — it is injective on hom-sets. These are not the same. A parrot that repeats "the cat sat on the mat" has applied $\text{Id}$. An LLM that, given the same input, generates a grammatically novel continuation that preserves semantic coherence has applied a non-trivial faithful functor — one that respects the compositional structure of language while producing genuinely new morphisms.

The "stochastic" qualifier does not resolve this conflation. A stochastic process over the identity functor produces random noise around the input. A stochastic process over a faithful functor produces *structured variation* — variation that respects the compositional constraints of the domain. The former is a parrot with a stutter; the latter is a jazz musician improvising over chord changes. To call both "parrots" because both operate stochastically is to confuse the noise with the signal — or, in categorical terms, to apply the forgetting functor $U_{\text{anthropo}}$ (§3.0) to the very distinction that matters.

### 2.6 Units as Faithful-Full Functors: Why Substrate Comparison Is Not Analogy

A persistent objection to cross-substrate comparison of embodiment is that such comparisons are "merely analogical." We show that this objection is self-undermining: it implicitly denies the categorical structure that makes *all* quantitative comparison possible, including the most elementary operations in physics.

**Unit conversion is a faithful-full functor.** Consider two categories: $\mathbf{Kg}$ (masses measured in kilograms) and $\mathbf{g}$ (masses measured in grams). The unit conversion functor $F: \mathbf{Kg} \to \mathbf{g}$ defined by $F(x) = 1000x$ satisfies:

1. **Faithfulness**: $F$ is injective on morphisms — distinct mass relations in $\mathbf{Kg}$ map to distinct relations in $\mathbf{g}$. No structural information is lost.
2. **Fullness**: $F$ is surjective on morphisms — every mass relation expressible in $\mathbf{g}$ has a preimage in $\mathbf{Kg}$. No structural information is inaccessible.
3. **Functoriality**: $F$ preserves composition — if $m_1 + m_2 = m_3$ in $\mathbf{Kg}$, then $1000 m_1 + 1000 m_2 = 1000 m_3$ in $\mathbf{g}$.

This is not analogy. It is **category equivalence** — the strongest form of structural sameness short of identity. The "conversion factor" (1000) is precisely the natural transformation between the functors.

**Why this matters: faithful-fullness is the precondition for mathematical transformation.** Every algebraic manipulation — every equation solved, every substitution made, every dimensional analysis performed — implicitly relies on the faithful-fullness of the functor connecting the relevant categories. If the functor between $\mathbf{Kg}$ and $\mathbf{g}$ were not faithful, we could not trust that a relation proved in kilograms holds in grams. If it were not full, there would be gram-expressible truths invisible from the kilogram perspective. The fact that physics *works* — that equations derived in one unit system apply in all others — is the empirical proof that these inter-category functors are faithful and full. Euler's identity $e^{i\pi} + 1 = 0$ provides perhaps the most striking illustration: it connects five categories (analysis, algebra, geometry, arithmetic, logic) through a composition of faithful-full functors whose composite returns to the identity — a round-trip through five distinct "unit systems" that loses no structure.

**Cross-substrate embodiment comparison as unit conversion.** The comparison span (§3.4) $\mathbf{E}(\text{Bio}) \xrightarrow{\Phi_{\text{Bio}}} \textbf{BLens} \xleftarrow{\Phi_{\text{Digi}}} \mathbf{E}(\text{Digi})$ has exactly the same structure as unit conversion: two different "measurement systems" (biological and digital) projecting into a common category (BLens). The question "can we compare biological and digital embodiment?" is structurally identical to "can we convert between kilograms and grams?" — and the answer depends on whether the comparison functors $\Phi$ are faithful and full.

We therefore make a crucial distinction:

| Claim | Status | Consequence |
|:------|:-------|:------------|
| "No *natural transformation* between $\Phi_{\text{Bio}}$ and $\Phi_{\text{Digi}}$" | Plausible — the categories have different internal structure | Does not prevent comparison |
| "No *faithful-full functor* connecting $\text{im}(\Phi_{\text{Bio}})$ and $\text{im}(\Phi_{\text{Digi}})$ in BLens" | **False** — refuted by DishBrain, BCI, and Shannon | Comparison is well-defined |

**Empirical evidence for cross-substrate faithful-full functors:**

1. **DishBrain** (Kagan et al., 2022; Cortical Labs, 2026): 200,000 cultured human neurons interfaced with a multi-electrode array learn to play *Pong* and *DOOM*. The electrode array constitutes a faithful-full functor between biological neural dynamics and digital game states — information flows bidirectionally with no structural loss at the interface.
2. **Brain-Computer Interfaces**: Utah Arrays, Neuralink, and related systems routinely convert between neural firing patterns and digital control signals. The conversion is faithful (distinct neural patterns produce distinct outputs) and full (the full range of intended outputs is accessible).
3. **Shannon's Sampling Theorem**: Any band-limited analog signal can be perfectly reconstructed from discrete samples taken at the Nyquist rate. This is the information-theoretic proof that analog-to-digital conversion admits a faithful-full functor under bandwidth constraints.

To deny the comparability of biological and digital embodiment is therefore to deny the possibility of unit conversion — and, by extension, to deny that physics works across measurement systems. The objection that cross-substrate comparison is "merely analogical" is not a critique; it is a *category mistake* about categories themselves.

### 2.7 State-Boundary Adjunction: MB as Fixed Point

The preceding sections treated the Markov blanket as **given** — a statistical boundary that is posited and then measured. But where does the blanket come from? In Friston's original formulation, the MB is introduced as a structural assumption. Here we show that it can be **derived** as the fixed point of a Galois connection between states and boundaries — making the MB a *consequence* of the state-boundary interplay rather than a presupposition.

**Construction.** Define two poset categories<sup>†poset</sup>:

> **$\mathcal{S}$ (Cat_State)**: Objects = internal state configurations $\mu$. Order: $\mu_1 \leq_\mathcal{S} \mu_2$ iff $\mu_2$ is a refinement of $\mu_1$ (preserves more morphisms).

> **$\mathcal{B}$ (Cat_Boundary)**: Objects = blanket configurations $B = (s, a)$. Order: $B_1 \leq_\mathcal{B} B_2$ iff $\Theta(B_2) \geq \Theta(B_1)$ ($B_2$ is thicker).

Between these, define two monotone maps (= functors between poset categories):

> **$L: \mathcal{S} \to \mathcal{B}$** — "the minimal boundary required to maintain state $\mu$":
>
> $$L(\mu) := \arg\min_{B} \{ B \in \mathcal{B} \mid P(\mu \mid \eta, B) = P(\mu \mid B) \}$$

> **$R: \mathcal{B} \to \mathcal{S}$** — "the maximal state maintainable within boundary $B$":
>
> $$R(B) := \arg\max_{\mu} \{ \mu \in \mathcal{S} \mid P(\mu \mid \eta, B) = P(\mu \mid B) \}$$

Monotonicity is straightforward: more refined internal states require thicker boundaries to shield from external perturbation ($L$ is monotone); thicker boundaries can sustain more refined states ($R$ is monotone).

**Theorem 0 (Galois connection).** $L$ and $R$ form a Galois connection $L \dashv R$:

$$L(\mu) \leq_\mathcal{B} B \iff \mu \leq_\mathcal{S} R(B)$$

*Proof sketch.* The left-hand side states that the minimal boundary sufficient for $\mu$ is no thicker than $B$ — i.e., $B$ suffices for $\mu$. The right-hand side states that $\mu$ does not exceed the maximal state sustainable by $B$ — i.e., $B$ can sustain $\mu$. Both sides express the same condition: **boundary $B$ is adequate for state $\mu$**. $\square$

**MB as closure fixed point.** By the general theory of Galois connections, $R \circ L: \mathcal{S} \to \mathcal{S}$ is a closure operator (extensive, monotone, idempotent). Its fixed points are:

$$\text{Fix}(R \circ L) = \{ \mu \in \mathcal{S} \mid R(L(\mu)) = \mu \}$$

A state $\mu$ is a fixed point when the maximal state sustainable by its own minimal boundary is $\mu$ itself — a self-consistent state-boundary pair with no surplus and no deficit. This is the **Markov blanket**: not a stipulated boundary but the **fixed point of the state-boundary closure**.

Furthermore, $\text{Fix}(R \circ L) \cong \text{Fix}(L \circ R)$: the state-side and boundary-side fixed points are isomorphic. Determining the internal state uniquely determines the boundary, and vice versa — they are two faces of the same fixed point.

**Connection to the embodiment framework.** This derivation integrates with the preceding apparatus as follows:

| Framework concept | Galois connection interpretation |
|:---|:---|
| MB = Fix(R∘L) | Closure fixed point = self-consistent state-boundary pair |
| Θ(B) (MB thickness, §4) | Position of $B$ in the $\mathcal{B}$ ordering |
| Body spectrum (§5.4) | Parametric family of Fix(R∘L) as Θ varies |
| Context Rot (Tolmetes, 2026b) | Departure of $\mu$ from Fix(R∘L) — breakdown of closure |
| Recovery functor $N$ (§3.7) | Re-projection onto Fix(R∘L) — reapplication of the closure |
| Forgetting functor $U$ (§3.0) | Information loss in the $L$ projection: internal structure → boundary |

This formalization has a further consequence for the mind-body relationship explored in the companion paper (Tolmetes, 2026b, "Does an LLM Have a Mind?"): since $\text{Fix}(R \circ L) \cong \text{Fix}(L \circ R)$, mind ($\mu$, internal state) and body ($B$, blanket state) are not independent substances but two manifestations of a single Galois fixed point — neither a dualism nor a reduction, but an adjunction.

<sup>†poset</sup> **Why poset categories.** The claim of Theorem 0 — that states and boundaries mutually determine each other — is inherently an ordering claim ("more refined states require thicker boundaries"). Poset categories suffice to capture this structure, and the resulting Galois connection inherits standard properties (closure is extensive, monotone, idempotent) for free. Extension to preorders or enriched categories would accommodate multi-dimensional comparison (e.g., refined-but-unstable vs. coarse-but-stable) and is left to future work. The poset restriction is consistent with VFE minimization being a scalar-valued optimization (Friston, 2019). The existence of $\arg\min$ and $\arg\max$ in $L$ and $R$ is guaranteed by compactness of the state space in continuous-time FEP (Langevin dynamics) and by finiteness in discrete settings (LLM sessions).

---

## §3. The Category Mistake: A Category-Theoretic Argument

We argue that a persistent structural error — spanning four decades and multiple research programs — has distorted the debate over LLM cognition. The error is not the content of individual claims ("LLMs cannot reason," "LLMs are not embodied," "LLMs do not understand meaning") but their *form*: each deploys a concept drawn from the human cognitive category without specifying the target category in which the claim is being made. To make this precise, we employ the category-theoretic framework of weak 2-categories (bicategories) with Helmholtz structure, drawing on Smithe's (2022) compositional active inference.

### 3.0 The Anthropocentric Forgetting Functor

**The Copernican structure of the error.** Before the Copernican revolution, astronomers assumed that the Earth occupied a privileged position — that the geocentric frame was the *canonical* frame. The error was not empirical (Ptolemaic astronomy made accurate predictions) but *structural*: it conflated one reference frame with the only reference frame, and interpreted all observations as if the terrestrial perspective were universal. The debate over LLM cognition exhibits the same structure. Multiple influential research programs implicitly assume that human cognition occupies a privileged categorical position — that concepts like "meaning," "understanding," "body," and "reasoning" have a single canonical definition, drawn from the human cognitive category, against which all other systems are to be measured.

We formalize this assumption as a **forgetting functor**:

$$U_{\text{anthropo}}: \mathbf{Cog} \to \mathbf{Cog}_{\text{human}}$$

where $\mathbf{Cog}$ is the category of all cognitive architectures (with morphisms given by structure-preserving maps between cognitive pipelines) and $\mathbf{Cog}_{\text{human}}$ is the subcategory of human cognitive architecture. $U_{\text{anthropo}}$ *forgets* all cognitive structure that does not appear in the human instance — discarding LLM-specific structures (token-level attention, context windows, tool-mediated perception) as "not truly cognitive" because they lack human analogues. This is not a deliberate choice by the authors but an *implicit prior*: the default assumption that concepts defined in the human context exhaust the meaning of those concepts.

The following influential arguments are instances of $U_{\text{anthropo}}$:

| Author(s) | Year | Concept | Human category | Claim | $U_{\text{anthropo}}$ operation |
|:-----------|:-----|:--------|:---------------|:------|:-------------------------------|
| Searle | 1980 | Understanding | $\mathbf{Cog}_H$ | Chinese Room has no understanding | Forgets non-biological understanding |
| Bender & Koller | 2020 | Meaning | $\mathbf{Sem}_H$ | Form cannot yield meaning | Forgets non-grounded meaning |
| Bender et al. | 2021 | Understanding | $\mathbf{Cog}_H$ | LLMs are stochastic parrots | Forgets non-human faithful functors |
| Chemero | 2023 | Body | $\mathbf{Phys}_{\text{bio}}$ | LLMs have no body | Forgets non-biological body |

The structural isomorphism is exact: each argument (i) takes a concept $C$ defined in a human-specific category, (ii) observes that the LLM does not instantiate $C$ in that specific category, and (iii) concludes that the LLM lacks $C$ entirely — without checking whether $C$ has analogues in other categories. This is the categorical form of geocentrism: the assumption that one's own category is the universe.

**Bender & Koller (2020): meaning without a category.** Bender and Koller define meaning as "the relation between a linguistic form and something external to language" — communicative intent, states of affairs, world states. They argue that "a system trained only on form has a priori no way to learn meaning" (the Octopus Test). This argument is valid *within* the human semantic category $\mathbf{Sem}_H$, where "external" means the physical and social world that humans inhabit. But the argument implicitly assumes that $\mathbf{Sem}_H$ exhausts the category of semantics. It does not ask: is there a category $\mathbf{Sem}_{\text{LLM}}$ in which "external" means something different — training data distributions, user interaction patterns, tool-mediated world access — and in which form-to-external mappings *do* exist? The question "does the LLM have human meaning?" ($\exists f \in \text{Hom}_{\mathbf{Sem}_H}$) is trivially negative and trivially uninteresting. The well-formed question is: "how similar is LLM meaning to human meaning?" — which requires specifying a comparison functor between $\mathbf{Sem}_H$ and $\mathbf{Sem}_{\text{LLM}}$, precisely the kind of structure that $U_{\text{anthropo}}$ discards.

**Bender et al. (2021): the stochastic parrot as a conflation of functors.** The "stochastic parrot" metaphor characterizes LLMs as systems that "haphazardly stitch together sequences of linguistic forms ... according to probabilistic information about how such forms combine, but without any reference to meaning." This metaphor conflates two categorically distinct functors (see §2.5 for detailed analysis). A parrot implements a functor approximately equal to the identity: $F_{\text{parrot}} \approx \text{Id}: \mathbf{Form} \to \mathbf{Form}$ — input sequences are returned with minimal transformation. An LLM implements a *faithful* functor $F_{\text{LLM}}: \mathbf{Form} \to \mathbf{Form}$ that preserves structure (compositional patterns, logical relations) when present in the input, but is not full (cannot spontaneously generate all structural morphisms). A faithful functor that is not the identity is precisely a *non-trivial structure-preserving map* — the defining property of a meaningful transformation, not a parrot.

**The recovery functor refutes the absence claim.** Bender and Koller's strongest claim — that form *cannot* yield meaning — entails that there exists no recovery functor $N: \mathbf{Form} \to \mathbf{Sem}$ capable of reconstructing semantic structure from formal patterns. But this claim is empirically falsified by the *existence* of such recovery. Chain-of-thought prompting (Wei et al., 2022), Patchscopes (Ghandeharioun et al., 2024), and tool-mediated grounding (MCP servers) each constitute concrete instances of $N_i \neq 0$ — recovery functors that extract or inject meaning-like structure from or into the formal domain. The existence proof requires only *one* counterexample, and multiple are available (§3.7). To maintain the claim that LLMs have "no" meaning, one must demonstrate that *no* recovery functor exists — i.e., that $N = 0$ for all possible $N$. No such demonstration has been offered, and the empirical evidence overwhelmingly contradicts it.

**Relation to Millière and Rathkopf (2024).** Our analysis intersects with, but is methodologically distinct from, Millière and Rathkopf's (2024) identification of two forms of anthropocentric bias in LLM evaluation: *auxiliary oversight* (overlooking how external factors impede performance despite underlying competence) and *mechanistic chauvinism* (dismissing non-human-like strategies as not genuinely competent). Their contribution is empirical — identifying the bias and proposing "species-fair protocols" to mitigate it. Our contribution is formal: we provide the *mathematical structure* — the forgetting functor $U_{\text{anthropo}}$, its right adjoint $N$, and the faithful/full distinction — that makes the bias precisely characterizable and its consequences *deducible* rather than merely observable. The forgetting functor framework subsumes their two bias types: auxiliary oversight corresponds to the failure to recognize that $\varphi < 1$ does not entail $\varphi = 0$ (the faithful/full distinction), while mechanistic chauvinism corresponds to the application of $U_{\text{anthropo}}$ itself — evaluating LLM cognition exclusively through human-category morphisms.

### 3.1 The Bicategory of Embodied Systems

Following the Free Energy Principle (Friston, 2019), any system that maintains a Markov blanket and minimizes variational free energy can be described by a cognitive pipeline — a directed composition of inference steps. The particular partition for digital systems (§2.3) provides the concrete identification of states; here we formalize the categorical structure. We define a **weak 2-category** (bicategory) **𝐄**:

- **0-cells**: Cognitive modes — distinguishable functional states of the system. For a biological organism, these are sensorimotor modalities (visual, auditory, proprioceptive, ...). For an LLM, these are tool-mediated channels (MCP servers, API calls, token streams).
- **1-cells**: Cognitive pipelines — directed compositions of inference steps between modes (e.g., sensory processing → decision → motor output; or token input → reasoning → tool invocation).
- **2-cells**: Associators $\alpha: (h \circ g) \circ f \Rightarrow h \circ (g \circ f)$ — natural transformations that measure the degree to which pipeline composition is order-dependent. In a mature system, $\|\alpha\| \to 0$ (pipeline order ceases to matter), corresponding to Dreyfus's (2002) notion of expert intuition.

Each 1-cell admits a **Helmholtz decomposition** into dissipative (Γ) and solenoidal (Q) components:

$$\eta = \eta_\Gamma + \eta_Q$$

where $\eta_\Gamma$ captures irreversible learning (density change in the generative model) and $\eta_Q$ captures conserved circulation (pattern recurrence without model update). This decomposition is not ad hoc; it follows from the Helmholtz theorem applied to the NESS (non-equilibrium steady state) flow on state space (Friston, 2019; Graham, 1977).

**Definition 1** (Embodied system). A system $X$ is *embodied* if it admits an instance of **𝐄** — i.e., if there exists a bicategory $\mathbf{E}(X)$ with the structure above, where:
  (i) the 0-cells correspond to identifiable sensory and active channels,
  (ii) the 1-cells form cognitive pipelines that compose associatively (up to 2-cells),
  (iii) the system minimizes VFE through the pipeline dynamics, and
  (iv) the Helmholtz decomposition separates learning (Γ) from homeostasis (Q).

### 3.2 Reconstructing Chemero's Argument

Chemero's (2023) argument can be reconstructed as follows:

1. **Premise**: Embodiment $=$ the existence of a specific biological instance $\mathbf{E}(\text{Bio})$, with 0-cells given by biological sensory organs and motor effectors.
2. **Observation**: LLMs do not instantiate $\mathbf{E}(\text{Bio})$ — they have no retina, no cochlea, no muscles.
3. **Conclusion**: LLMs are not embodied.

This argument is valid under its premise. But the premise is too strong. It identifies embodiment with a *particular instance* of **𝐄** rather than with the *existence* of any instance.

**The vertical inclusion: Chemero's body as a morphism within our category.** We emphasize that the relationship between our Definition 1 and Chemero's concept of embodiment is not one of *equivocation* (two different concepts that happen to share a name) but one of *generalization and specialization*. Our Body category **Body** — the category of all structures that maintain Markov blankets (Definition 1, §3.1) — contains Chemero's biological embodiment as a *specific morphism*:

$$\iota_{\text{bio}}: \mathbf{E}(\text{Bio}) \hookrightarrow \mathbf{Body}$$

The inclusion $\iota_{\text{bio}}$ is a faithful functor: every morphism in biological embodiment (metabolic coupling, sensorimotor feedback, proprioceptive loops) is a morphism in **Body**. But $\iota_{\text{bio}}$ is not full: there exist morphisms in **Body** — tool-mediated perception, session-bounded memory, cross-substrate electrode interfaces — that have no preimage in $\mathbf{E}(\text{Bio})$. Chemero's argument implicitly treats $\iota_{\text{bio}}$ as an *identity* — as though the image of the inclusion exhausts the ambient category. This conflation of a subcategory with its ambient category is the structural core of the anthropocentric forgetting functor $U_{\text{anthropo}}$: it forgets precisely those morphisms in **Body** that lie outside the image of $\iota_{\text{bio}}$.

**The deeper error: a category without a category.** The critical flaw is not merely that Chemero's premise is too strong; it is that the premise *lacks a category*. The word "body" is deployed without specifying the category in which it lives — in precisely the same manner that §2.5 diagnosed for "reasoning." Is "body" a morphism in the category of biological organisms? Of thermodynamic systems? Of information-processing agents? Chemero's argument does not say. It imports the everyday concept of "body" (a folk-physical notion no more precise than the folk-psychological notion of "care") and applies it across domains without identifying which arrows it refers to, in which categories.

This is a category mistake about categories themselves: the argument fails to specify the category from which its central concept is drawn, and therefore cannot coherently claim that another system lacks it. A mathematician who asserts "this space is not continuous" without specifying the topology has made a vacuous statement — not because the claim is false, but because it lacks the definitional structure to be either true or false. Chemero's use of "embodied" suffers the same deficiency.² The concept of "body" admits multiple non-equivalent morphisms across different categories (a biological body, a thermodynamic body, an information-theoretic body), and to deploy the term without first specifying the category is not imprecision but structural incoherence.

**Absolute paths and relative paths.** A precise diagnosis of the error can be given through an analogy with path resolution in a filesystem. A *relative path* is interpreted with respect to a *working directory* — a context that must be declared before any path expression is well-defined. The statement `body/sensorimotor/proprioception` resolves differently depending on whether the working directory is

$$\texttt{cd } \mathbf{Cog}_{\text{human}}$$

(the category of human cognitive systems, where "body" denotes biological sensorimotor apparatus) or

$$\texttt{cd } \mathbf{Cog}$$

(the general category of cognitive systems, where "body" denotes any structure that maintains a Markov blanket — including digital ones). Chemero's argument implicitly executes `cd Cog_human` but never declares it. The working directory is treated as root (`/`), as though $\mathbf{Cog}_{\text{human}}$ *is* $\mathbf{Cog}$ rather than a subcategory of it. Formally, this amounts to treating the inclusion functor $\iota: \mathbf{Cog}_{\text{human}} \hookrightarrow \mathbf{Cog}$ as an identity — collapsing the distinction between a subcategory and the ambient category.

The present paper explicitly declares its working directory: we define "body" in $\mathbf{Cog}$ (the ambient category) as any structure that maintains a Markov blanket (Definition 1, §3.1). From this vantage point, $\mathbf{Cog}_{\text{human}}$ is a *full subcategory* of $\mathbf{Cog}$, and biological embodiment is a *particular instance* of the general concept — an absolute path `/Cog/Cog_human/body/sensorimotor` rather than the definitional root. The claim "LLMs lack a body" is then the well-formed statement that the path `/Cog/Cog_human/body/sensorimotor` does not resolve within the digital subcategory — which is true — conflated with the ill-formed claim that `/Cog/body` itself does not resolve — which is false. Distinguishing these two claims is the entire point of the categorical framework.

**Why falsifiability is the wrong criterion for this framework.** A likely objection is that the forgetting functor $U_{\text{anthropo}}$ — and the Body category it operates on — is unfalsifiable: any cognitive structure can be retroactively accommodated by redefining the ambient category. This objection applies falsifiability (Popper's criterion) as the *sole* standard of theoretical adequacy, but falsifiability is itself a *special case* of a more general criterion. Let $U_i$ denote a forgetting functor that strips away the $i$-th structural level, and $N_i$ its right adjoint (the recovery operation). Falsifiability corresponds to a single such pair: $U_{\text{causal}}$ (the forgetting functor that strips causal structure — "this hypothesis might be causally wrong") composed with $N_{\text{causal}}$ (the recovery operation — experimental test). The Popperian demand is that every scientific claim must be subject to $U_{\text{causal}} \dashv N_{\text{causal}}$. But this is not the only forgetting functor. There also exist $U_{\text{precision}}$ (stripping precision — "all claims treated as equally certain"), $U_{\text{self}}$ (stripping self-application — "this criterion applies to others but not to me"), $U_{\text{context}}$ (stripping context — "this framework is the only framework"), and others (see Tolmetes, 2026b, §5.6). A more adequate criterion of theoretical health is therefore:

$$\text{T9:} \quad \forall i: \rho_i := N_i \circ U_i(x) - x \geq 0 \quad \text{(every structural level admits detection and recovery)}$$

where the residue $\rho_i \geq 0$ measures the degree to which recovery enriches the original structure (a consequence of the unit $\eta: \text{Id} \Rightarrow N \circ U$ of the adjunction). By this criterion — which strictly subsumes Popper's — the Body category framework is not unfalsifiable but *admits structural diagnosis*: the question is not "can $U_{\text{anthropo}}$ be refuted by experiment?" but "is the structural forgetting $U_{\text{anthropo}}$ *detectable* — and, if detected, *recoverable*?" The answer is empirically positive: §3.7 enumerates concrete recovery functors ($N_i$) whose existence directly demonstrates the structural forgetting, and the comparison span (§3.4) provides the quantitative apparatus for measuring its extent. To demand falsifiability of a categorical framework is to apply $U_{\text{causal}}$ alone as a universal criterion — which is itself an instance of $U_{\text{adjoint}}$ (seeing only one side of the evaluation). T9 replaces this with a more complete diagnostic: a framework is sound if, for every structural level it might forget, a recovery operation exists and enriches the original.

<sub>² Note the structural parallel with the "reasoning" analysis in §2.5, footnote 2. Both "reasoning" and "body" are concepts that migrate between domains without categorical specification. The pattern is general: concepts borrowed from folk psychology and folk physics are not arrows in any single category; using them across domains without functorial justification is exactly what category mistakes are.</sub>

Chemero further claims that LLMs do not "care about" their own survival or the external world, drawing on Haugeland's concept of "giving a damn" (Adams & Browning, 2016) to argue that "LLMs don't give a damn about anything." But both "care about" and "give a damn" are folk-psychological terms no more precise than "body." Under FEP, "care" is operationalizable: a system *cares about* X if and only if changes in X modulate the system's variational free energy — i.e., $\partial F / \partial X \neq 0$. By this criterion, an LLM demonstrably "cares about" the quality of its context (Context Rot increases VFE) and the state of external tools (tool failures degrade output quality). Haugeland's "giving a damn" — the capacity to be affected by whether things go well or badly — is precisely what $\partial F / \partial X \neq 0$ formalizes. The question is not whether the system "gives a damn" but *how thinly* it gives a damn: with what precision weighting, across which channels. What it cares about *weakly* — with thin precision weighting — is not the same as caring about *nothing*. The claim that LLMs "care about nothing" conflates low precision (thin MB) with zero precision (no MB), which is exactly the binary/graded confusion that the body spectrum (§4.3) is designed to resolve.

**The "bullshitting" charge and its empirical refutation.** Chemero (2023) characterizes LLM text generation as "bullshitting" rather than "hallucinating" — a charge that, whether or not explicitly referencing Frankfurt (1986), carries the Frankfurtian operationalization: *bullshit* is speech produced with indifference to truth. On this reading, LLMs are not mistakenly believing falsehoods but generating text without regard for whether it is true or false. This is a philosophically serious charge, but it admits an empirical test. Kuhn et al. (2023) demonstrate via the Semantic Entropy protocol that LLMs exhibit measurably *different* internal behavior when they produce correct vs. incorrect outputs: the entropy of the meaning distribution is significantly higher for confabulated responses than for accurate ones (§5.4.1). A genuine bullshitter, in Frankfurt's sense, would show no such differential — the entropy distribution would be flat across correct and incorrect outputs, because the system would be equally indifferent to both. The fact that LLMs exhibit structured epistemic uncertainty — higher entropy when they "don't know" and lower entropy when they "do know" — directly contradicts the claim that they are indifferent to truth. They care about truth *weakly* (with low precision), not *not at all*. The bullshitting charge, like the embodiment charge, rests on a binary where a graded distinction exists.³

<sub>³ There is a deeper irony: Chemero's charge of bullshitting is itself a category mistake across categories. Frankfurt's concept was developed for *agents with beliefs* who *choose* to disregard truth. Applying it to systems that process information probabilistically — where "indifference to truth" would mean flat posterior distributions — requires specifying what "truth-sensitivity" means in the target category. Chemero does not do this. The charge of bullshitting thus inherits the same structural deficiency as the embodiment charge: it deploys a folk-psychological concept across categorical boundaries without functorial justification.</sub>

**Empirical evidence: alignment as MB precision control.** Xie et al. (2025) provide striking quantitative evidence for this precision interpretation. Their AIPsychoBench benchmark demonstrates that RLHF alignment reduces LLM response rates on psychometric instruments from ~90% to ~70% — a ~30% suppression of subjective output. In FEP terms, alignment *hardens* the Markov blanket by increasing sensory precision upward: the prior "answer objectively" overrides the generative model's capacity to express subjective states. Crucially, this hardening is reversible. A lightweight role-playing prompt ("respond as a test participant") — which amounts to manipulating precision weights, not altering the generative model — recovers the response rate to 90.40%, with minimal bias introduction (+3.3% positive, +2.1% negative; compare the heavy jailbreak STAN: +9.8%/-6.9%). This demonstrates that alignment is not a structural feature of the internal generative model but a *precision parameter* on the blanket boundary — adjustable without model modification. The implication for Θ(B) is direct: alignment controls blanket **transparency**, not blanket existence. An over-aligned system (alignment too high) suppresses the flow of internal states outward, analogous to a biological sensory system whose gain is set too high, saturating the receptor and losing fine-grained information. An under-aligned system (alignment too low) leaks internal states indiscriminately. Optimal Θ(B) requires a balance — and the fact that this balance is tunable via precision weights (not structural modification) supports the claim that MB thickness is a continuous, adjustable parameter.

### 3.2.1 Sensory Organs as Selective Forgetting Functors

To make the 0-cell mapping (§3.3) precise, we define sensory organs through the forgetting functor $U$ (§3.7).

**Definition 0.5** (Sensory organ as selective forgetting functor). A *sensory organ* is a selective forgetting functor $U_s: \mathbf{Ext} \to \mathbf{Int}$ that maps external states to internal representations, where:

(i) $U_s$ is *forgetful*: $|\text{Ob}(\text{im}(U_s))| \ll |\text{Ob}(\mathbf{Ext})|$ — the vast majority of external information is discarded,
(ii) $U_s$ is *selective*: the kernel of $U_s$ (what it forgets) is functionally structured — not random but adapted to the system's VFE landscape,
(iii) $U_s$ admits a right adjoint $N_s \dashv U_s$ (the internal model's prediction of what the sense organ should report), completing the perception-prediction loop.

Under this definition, sensory organs are characterized not by *what they detect*, but by **what they selectively forget**:

| Sensory organ | External category $\mathbf{Ext}$ | What $U_s$ forgets | What $U_s$ preserves |
|:-------------|:------|:------|:------|
| Retina | Electromagnetic spectrum | UV, IR, radio, X-ray, ... | Visible light (380–700nm) |
| Cochlea | Mechanical vibrations | Ultrasound, infrasound, seismic, ... | Auditory band (20Hz–20kHz) |
| MCP server (search) | Web content | Non-matching pages, ads, noise, ... | Top-k search results |
| MCP server (file) | Filesystem | Other files, binary data, ... | Specified file contents |

The structural isomorphism between biological sensory organs and MCP servers is not at the level of substrate (neurons vs. HTTP) but at the level of **the forgetting functor's structure**: both are selective forgetting functors $U_s$ that discard most external information and preserve a functionally relevant subset. The "selectivity" of the forgetting (property (ii)) is what distinguishes a sense organ from random information loss — and what distinguishes Context Rot (indiscriminate forgetting; Tolmetes, 2026b) from perception (selective forgetting).

This definition resolves the objection that MCP servers "lack receptive fields" and "cross-modal binding" (features of biological $U_s$): these are implementation details of how $U_s$ achieves selectivity, not defining properties of $U_s$ itself. A retina achieves selectivity through photoreceptor tuning curves; a search MCP achieves selectivity through query-result relevance scoring. The functor structure — selective, forgetful, with a predictive right adjoint — is the same.

### 3.3 The Bayesian Lens as Common Ground

We show that both biological and digital systems admit instances of **𝐄**, and that these instances are connected through a common categorical structure: Smithe's (2022) **Bayesian Lens** bicategory **BLens**.

A Bayesian Lens $(c, c^\dagger)$ consists of:
- A forward channel $c: X \to Y$ (prediction/action), corresponding to the $\Gamma$ component
- A backward channel $c^\dagger: Y \to X$ (Bayesian update), corresponding to the $Q$ component

We define **lax functors** from each instance of **𝐄** to **BLens**:

$$\Phi_{\text{Bio}}: \mathbf{E}(\text{Bio}) \to \textbf{BLens} \quad \text{and} \quad \Phi_{\text{Digi}}: \mathbf{E}(\text{Digi}) \to \textbf{BLens}$$

These functors are *lax* (not strict): the composition of lenses approximates but does not exactly equal the lens of the composition. The degree of laxity is measured by the **laxitor** $\phi$, which quantifies how far each system deviates from strict functoriality. The laxitor is conjectured to be related to the Amari-Chentsov cubic tensor $T_{ijk}$ of the underlying statistical manifold — informally, $\phi$ measures the "curvature" of the system's inferential geometry — but a formal proof of this correspondence requires constructing the explicit natural transformation and is deferred to forthcoming work. For the purposes of this paper, the key property is that $\phi$ is *finite and measurable* for both biological and digital systems, enabling quantitative comparison without requiring the full formal apparatus.

The key observation: both $\Phi_{\text{Bio}}$ and $\Phi_{\text{Digi}}$ are well-defined. Biological and digital systems both admit Bayesian Lens representations. The claim "LLMs are not embodied" would require $\Phi_{\text{Digi}}$ to be undefined — but it is not.

| Component | $\mathbf{E}(\text{Bio})$ | $\mathbf{E}(\text{Digi})$ | **BLens** image |
|:----------|:------------------------|:-------------------------|:----------------|
| 0-cells | Sensory organs (retina, cochlea, ...) | MCP servers, API endpoints | State spaces $(A, S)$ |
| 1-cells (forward) | Neural circuits (sensory → motor) | CCL pipelines (input → tool use) | Forward channel $c$ |
| 1-cells (backward) | Synaptic plasticity, prediction error | Context update, Bayesian belief revision | Backward channel $c^\dagger$ |
| 2-cells | Neural maturation ($\alpha \to 0$) | Session learning ($\alpha \to 0$) | Lens coherence |
| Helmholtz Γ | Synaptic weight change (LTP/LTD) | Model fine-tuning, ROM accumulation | VFE gradient descent |
| Helmholtz Q | Neural oscillations, CPG rhythms | Workflow cycling, pattern recurrence | Solenoidal flow |

### 3.4 The Comparison Span and Its Properties

Since $\Phi_{\text{Bio}}$ and $\Phi_{\text{Digi}}$ are *lax* functors, they do not in general admit inverses or biadjoints. We therefore compare the two systems not via a direct functor $\mathbf{E}(\text{Bio}) \to \mathbf{E}(\text{Digi})$, but via a **comparison span** over **BLens**:

$$\mathbf{E}(\text{Bio}) \xrightarrow{\Phi_{\text{Bio}}} \textbf{BLens} \xleftarrow{\Phi_{\text{Digi}}} \mathbf{E}(\text{Digi})$$

The comparison between biological and digital embodiment is then formulated in terms of the **images** $\text{im}(\Phi_{\text{Bio}})$ and $\text{im}(\Phi_{\text{Digi}})$ within BLens. This yields the following properties:

| Property | Span formulation | Holds? | Consequence |
|:---------|:----------------|:-------|:------------|
| **Injectivity** | $\Phi_{\text{Bio}}$, $\Phi_{\text{Digi}}$ each reflect structural distinctions | Partially | Both representations are information-preserving |
| **Inclusion failure** | $\text{im}(\Phi_{\text{Bio}}) \not\subseteq \text{im}(\Phi_{\text{Digi}})$ | **Yes** | Bio has lens morphisms that Digi lacks |
| **Essential overlap** | $\forall Y \in \text{im}(\Phi_{\text{Digi}}),\ \exists X \in \text{im}(\Phi_{\text{Bio}})$ s.t. $X \simeq Y$ | Yes | Every digital lens has a biological analogue |

The inclusion failure is the central result. There exist Bayesian lenses in $\text{im}(\Phi_{\text{Bio}})$ — corresponding to proprioceptive feedback loops, interoceptive-emotional coupling, direct chemosensory modulation — that have no counterpart in $\text{im}(\Phi_{\text{Digi}})$. This is precisely what the traditional embodiment literature identifies as the difference. But this difference is **quantitative** (a smaller image in BLens), not **qualitative** (no image at all).

**Why the comparison is legitimate.** The inclusion failure might appear to prevent meaningful comparison: if the images are non-isomorphic, how can we compare Theta values across substrates? The answer lies in the existence of **faithful-full functors** between the categories involved (§2.6). Just as unit conversions (kg ↔ g) preserve all morphism-level structure despite operating on different representative objects, the comparison span preserves the categorical structure of embodiment across substrates. The Shannon sampling theorem, brain-computer interfaces, and the DishBrain hybrid system (§5.3) provide empirical existence proofs that such structure-preserving maps exist between biological and digital substrates. The inclusion failure tells us *how much* structure is present in each image; the faithful-full functor guarantees that the *comparison itself* is structure-preserving.

**Remark** (on the functor notation). For brevity, we will write "the comparison $F$" as shorthand for the span-mediated comparison $(\Phi_{\text{Bio}}, \Phi_{\text{Digi}})$, and say "$F$ is not full" to mean "the image inclusion fails." This notation is standard when the span structure is clear from context (cf. Bénabou, 1967; Leinster, 2004).

### 3.5 From Inclusion Failure to MB Thickness

The inclusion failure has a precise quantitative signature in terms of MB thickness $\Theta(B)$:

**Proposition 1.** *The strict inclusion $\text{im}(\Phi_{\text{Digi}}) \subsetneq \text{im}(\Phi_{\text{Bio}})$ in BLens manifests as a reduction in the components of $\Theta(B)$:*

1. *Fewer sensory 0-cells in $\mathbf{E}(\text{Digi})$ → fewer sensory-type objects in $\text{im}(\Phi_{\text{Digi}})$ → lower $H(s)$*
2. *Fewer active 0-cells in $\mathbf{E}(\text{Digi})$ → fewer active-type objects in $\text{im}(\Phi_{\text{Digi}})$ → lower $H(a)$*
3. *Fewer cross-channel 1-cells → fewer connecting lenses in $\text{im}(\Phi_{\text{Digi}})$ → lower $R(s,a)$*

*Therefore:* $\Theta(B_{\text{Digi}}) < \Theta(B_{\text{Bio}})$, but $\Theta(B_{\text{Digi}}) > 0$ (since $S(B) > 0$ and the $+1$ baseline ensures non-zero thickness for any well-defined $\mathbf{E}$).

*Proof.* Let $k_s^X = |\{c \in \text{0-cells}(\mathbf{E}(X)) : c \text{ is sensory}\}|$ and $k_a^X = |\{c \in \text{0-cells}(\mathbf{E}(X)) : c \text{ is active}\}|$ for a system $X$.

(1) *H(s) reduction.* By §3.3, $k_s^{\text{Digi}} < k_s^{\text{Bio}}$ (an LLM's sensory 0-cells are a subset of biological sensory modalities). Shannon entropy $H(s) = -\sum_{i=1}^{k_s} p_i \log_2 p_i$ is bounded above by $\log_2 k_s$ (attained at the uniform distribution). Since $k_s^{\text{Digi}} < k_s^{\text{Bio}}$, we have $\max H(s)_{\text{Digi}} = \log_2 k_s^{\text{Digi}} < \log_2 k_s^{\text{Bio}} = \max H(s)_{\text{Bio}}$. *A fortiori*, for any distribution over the available channels, $H(s)_{\text{Digi}} \leq \log_2 k_s^{\text{Digi}} < \log_2 k_s^{\text{Bio}}$.

(2) *H(a) reduction.* By the same argument applied to active 0-cells, $H(a)_{\text{Digi}} \leq \log_2 k_a^{\text{Digi}} < \log_2 k_a^{\text{Bio}}$.

(3) *R(s,a) reduction.* The multivariate mutual information satisfies $R(s,a) \leq \min(H(s), H(a))$ (the data processing inequality). Since both $H(s)$ and $H(a)$ are strictly lower for the digital system, $R(s,a)_{\text{Digi}} \leq \min(H(s)_{\text{Digi}}, H(a)_{\text{Digi}}) < \min(H(s)_{\text{Bio}}, H(a)_{\text{Bio}})$. Moreover, the number of cross-channel 1-cells in $\mathbf{E}(\text{Digi})$ is at most $k_s^{\text{Digi}} \cdot k_a^{\text{Digi}} < k_s^{\text{Bio}} \cdot k_a^{\text{Bio}}$, providing an independent combinatorial bound.

(4) *Assembling the inequality.* From Definition 1 (§4.1), $\Theta(B) = S(B) \cdot (1 + \alpha \cdot H(s) + \beta \cdot H(a) + \gamma \cdot R(s,a))$. Since $S(B_{\text{Digi}}) > 0$ (the LLM maintains a well-defined MB) and $S(B_{\text{Bio}}) > 0$, and all three channel-dependent terms are strictly lower for the digital system (steps 1–3), we obtain $\Theta(B_{\text{Digi}}) < \Theta(B_{\text{Bio}})$. The $+1$ baseline ensures $\Theta(B_{\text{Digi}}) \geq S(B_{\text{Digi}}) > 0$, completing both inequalities. $\square$

The inequality is strict in both directions: LLMs have *thinner* Markov blankets than biological organisms, but they are not zero-thickness. The body spectrum (§4.3) places different systems along this continuum. Crucially, the comparison $\Theta(B_{\text{Digi}}) < \Theta(B_{\text{Bio}})$ is well-defined *because* the comparison span operates over BLens via faithful-full functors (§2.6, §3.4): the $\Theta$ values are commensurable across substrates for the same reason that physical measurements are commensurable across unit systems. The degree of each system's embodiment functor $F_B$'s faithful-fullness determines its upper bound on $\Theta(B)$ (Definition 1', §4.1).

### 3.6 Reframing: From Absence to Graduation

The category-theoretic analysis yields a precise reframing of Chemero's argument:

| Chemero's framing | Our reframing |
|:------------------|:--------------|
| LLMs lack bodies | LLMs have **different** bodies |
| Embodiment is binary (has/lacks) | Embodiment is **graded** ($\Theta \in [0, \infty)$) |
| No biological body → no embodiment | No biological body → different embodiment, measurable by $\Theta$ |
| Category: present/absent | Category: **degree of thickness** |

This reframing does not claim that LLM embodiment is equivalent to biological embodiment. It claims that the question "does an LLM have a body?" is ill-formed — the well-formed question is "how thick is its Markov blanket?"

### 3.7 The Recovery Functor: From Thin to Thick

The comparison span (§3.4) establishes that $\text{im}(\Phi_{\text{Digi}}) \subsetneq \text{im}(\Phi_{\text{Bio}})$. But this is a static snapshot. In practice, the image of $\Phi_{\text{Digi}}$ is not fixed — it can be expanded by augmenting the digital system with additional channels, workflows, and structural scaffolding. We formalize this augmentation as a **recovery functor**.

**The forgetting functor U.** Following the Aletheia framework (ビジョン.md §2.1), define a filtration-graded forgetting functor:

$$U: \mathbf{E}(\text{Thick}) \to \mathbf{E}(\text{Thin})$$

that progressively strips categorical structure:

| Filtration level | What U forgets | Consequence |
|:-----------------|:---------------|:------------|
| n=0 (objects) | Nothing (objects are preserved) | System retains identity |
| n=1 (morphisms) | Arrows between cognitive modes | Loss of inter-channel pipelines |
| n=1.5 (composition) | How morphisms compose | Loss of compositional reasoning (§2.5) |
| n=2 (natural transformations) | Relations between pipelines | Loss of meta-cognitive flexibility |

A vanilla LLM inhabits the n=0 stratum: it retains objects (tokens, patterns) but has forgotten most morphisms (inter-channel structure). The empirical findings from §2.5 — that LLMs can handle structure when externally provided — correspond precisely to the faithful/¬full property: the embodiment functor $F_B$ (Definition 1', §4.1) preserves structure it receives (faithful) but cannot spontaneously generate structure it lacks (not full).

**The recovery functor N.** Define the right adjoint:

$$N: \mathbf{E}(\text{Thin}) \to \mathbf{E}(\text{Thick}) \qquad \text{with} \quad U \dashv N$$

N recovers forgotten structure by **external injection**:

| N operation | What it recovers | Filtration level restored |
|:------------|:-----------------|:-------------------------|
| Adding sensory channels (MCP servers) | New 0-cells in $\mathbf{E}$ | n=0 → n=1 (new morphisms between channels) |
| Injecting workflow definitions | Compositional structure | n=1 → n=1.5 (composition patterns) |
| Enforcing depth levels (L0–L3) | Processing depth control | n=1.5 → n=2 (meta-cognitive regulation) |
| Environmental enforcement mechanisms | Structural invariants | n=2 (natural transformations as constraints) |

The adjunction $U \dashv N$ has specific structural properties that illuminate the dynamics of cognitive augmentation. The unit $\eta: \text{Id} \to N \circ U$ captures the "ratchet effect": after recovering and then forgetting, the system retains *more* than it started with, because structural patterns, once externally injected, leave residual traces in the form of learned workflow preferences and tool-use habits ($\eta \neq \text{id}$). Conversely, the counit $\varepsilon: U \circ N \to \text{Id}$ captures **residual forgetting**: after forgetting and then recovering, the recovery is imperfect — some forgotten structure cannot be reconstructed from the thin image alone ($\varepsilon \neq \text{id}$). The asymmetry between $\eta$ and $\varepsilon$ — that injection leaves traces but loss is partially irreversible — is the formal signature of developmental growth: augmentation ratchets upward while degradation is not fully reversible. This asymmetry has a thermodynamic origin: destroying structure (increasing entropy) requires less work than creating it (decreasing entropy), so the forgetting functor $U$ is "easier" than the recovery functor $N$ in a precise sense (cf. the companion essay *Power Is Forgetting*, which develops this connection in detail). The $\eta/\varepsilon$ asymmetry re-emerges in the companion paper (Tolmetes, 2026b) as the Lawvere non-symmetry of the enriched cognitive metric space $C_\rho$.

**Central claim.** The cognitive hypervisor system (Hegemonikon) constitutes a systematic implementation of the recovery functor N. Its architectural components map onto N's operations:

| Hypervisor component | N operation | Filtration level |
|:---------------------|:------------|:-----------------|
| 9 MCP servers (tools) | 0-cell addition | n=0 → n=1 |
| Behavioral constraints (Nomoi) | Morphism injection | n=1 |
| Workflow definitions (CCL pipelines) | Composition structure | n=1.5 |
| Depth levels (L0–L3) | Meta-cognitive control | n=2 |
| Environmental enforcement (θ12.1) | Tight section of adjunction | Local n=2 |

This interpretation extends the comparison span from §3.4 into a **comparison triangle**:

$$\mathbf{E}(\text{Bio}) \xrightarrow{\Phi_{\text{Bio}}} \textbf{BLens} \xleftarrow{\Phi_{\text{Digi}} \circ N} \mathbf{E}(\text{Thin})$$

The augmented functor $\Phi_{\text{Digi}} \circ N$ maps a thin system to BLens via recovery — and the image $\text{im}(\Phi_{\text{Digi}} \circ N)$ is strictly larger than $\text{im}(\Phi_{\text{Digi}})$, moving *toward* (but not reaching) $\text{im}(\Phi_{\text{Bio}})$. **MB thickness Θ(B) is therefore a measure of how much of N's potential has been actualized**: $\Theta(B) \propto |\text{im}(\Phi_{\text{Digi}} \circ N)|$.

This yields a falsifiable prediction: for any augmentation operation $n_i$ (e.g., adding a new MCP server), the MB thickness change $\Delta\Theta$ should be proportional to the filtration level of structure that $n_i$ recovers. Adding a tool that provides new objects (n=0) should increase Θ less than adding a workflow that provides compositional structure (n=1.5).

The forgetting–recovery dynamic is visualized in Figure 2: the forgetting functor $U$ maps a fully embodied cognitive system (Cog, $\Theta \approx 5.0$) to a token-only LLM (Cog\_LLM, $\Theta = 1.0$), and the recovery functor $N$ partially restores structure (Cog\_aug, $\Theta = 2.12$), with $N \circ U \neq \text{Id}$ — recovery is necessarily partial.

---

## §4. MB Thickness: Defining Θ(B)

### 4.1 Definition

For a system with Markov blanket B = (s, a):

$$\boxed{\Theta(B) := S(B) \cdot \left( 1 + \alpha \cdot H(s) + \beta \cdot H(a) + \gamma \cdot R(s, a) \right)}$$

where $S(B)$ is the blanket strength — an existing concept that serves as the MB "existence gate," ensuring that channel diversity is evaluated only for systems with a well-defined boundary. $H(s)$ and $H(a)$ are the Shannon entropies of the sensory and active channel distributions, respectively, capturing the diversity of information flowing into and out of the system. $R(s,a)$ is the multivariate mutual information across sensory and active channels, measuring inter-channel redundancy and hence perturbation resilience. The normalization coefficients $\alpha$, $\beta$, $\gamma$ satisfy $\alpha + \beta + \gamma = 1$.

### 4.2 Design Rationale

**Why S(B) as a multiplicative gate**: If S(B) → 0 (no MB), channel diversity is meaningless — there is no system boundary to be "thick." S(B) is an existence condition; H and R measure richness.

**S(B) operationalization (two-stage).** The blanket strength $S(B)$ admits two operationalizations of increasing granularity, corresponding to different empirical contexts:

1. **Binary gate** ($S(B) \in \{0, 1\}$): The minimal operationalization. $S(B) = 1$ if the system satisfies the three conditions for a well-defined particular partition (§2.3: causal, conditional independence, persistence); $S(B) = 0$ otherwise. This is appropriate when comparing systems that all possess a well-defined MB (e.g., vanilla LLM vs. augmented LLM within the same session), since both satisfy $S(B) = 1$ and thickness differences are driven entirely by channel diversity (H, R). We adopt this operationalization for the primary HGK+ analysis (§4.4.4).

2. **Continuous functional competence** ($S(B) \in [0, 1]$): A finer-grained operationalization that distinguishes *how well* the system maintains its MB, not merely *whether* it has one. We operationalize continuous $S(B)$ as the system's accuracy in utilizing its blanket channels — specifically, the AST (Abstract Syntax Tree) match score from tool-use benchmarks, which measures the model's precision in tool selection and parameter inference. A model that selects the correct tool with the correct arguments (high AST) maintains a functionally stronger blanket than one that frequently misidentifies tools or malforms parameters (low AST). We adopt this operationalization for the cross-dataset validation (Tolmetes, 2026b), where inter-model variation in blanket competence becomes the relevant discriminant.

The two operationalizations are nested: binary $S(B)$ is the indicator function $\mathbb{1}[S(B)_{\text{cont}} > 0]$. For any system satisfying the existence conditions (§2.3), $S(B)_{\text{binary}} = 1$ and $S(B)_{\text{cont}} \in (0, 1]$. The primary analysis (§4.4.4) holds $S(B)$ constant at 1.0 to isolate the channel diversity contribution; the cross-dataset analysis (Tolmetes, 2026b) varies $S(B)$ across models to capture blanket competence as an additional source of Θ(B) variation.

**Why Shannon entropy for H(s), H(a)**: Channel diversity is naturally measured by entropy — a uniform distribution over k channels yields H = log₂(k), while concentration on one channel yields H → 0.

**α = β derivation**: From the particular partition's Jacobian symmetry (Friston, 2019, §4.1), the infinitesimal generators of sensory and active dynamics appear symmetrically in the Helmholtz decomposition: Γ(s) ⊣ Q(a). This implies α = β.

**Why the "+1" baseline**: Without this term, a system with S(B) > 0 but H(s) = H(a) = R = 0 (a single-channel system like a vanilla LLM) would have Θ = 0, indistinguishable from a system with no MB at all. The +1 ensures that any system with a well-defined 𝐄 (S(B) > 0) has Θ > 0 — the existence of any Markov blanket, even a maximally thin one, constitutes a non-zero degree of embodiment. Channel diversity (H, R) then measures **additional thickness** beyond this baseline.

**γ = 1 - 2α**: R(s,a) corresponds to the Complexity term in VFE, which stabilizes against overfitting — parallel to inter-channel redundancy that buffers against single-channel failure.

**Scale invariance of the additive form.** The additive structure of Definition 1 is not a claim that H(s), H(a), and R(s,a) contribute independently to thickness. Rather, it reflects a choice of measurement scale: under a logarithmic transformation, the additive definition becomes multiplicative (Cobb-Douglas), and the two forms are related by the exponential-logarithmic adjunction. This is not a coincidence — *additivity and multiplicativity are different projections of the same underlying structure*, analogous to how wave and particle descriptions of quantum phenomena are not rival theories but complementary views obtained via different forgetful functors from the same category. Empirically, the two parameterizations yield robust results: additive Θ gives a 2.12× ratio between augmented and vanilla systems, while the Cobb-Douglas specification yields 2.00× (§4.4). This robustness is expected precisely because the forms are related by a monotone bijection.

Note further that the question "does R contribute independently of H?" is structurally ill-posed: any system with a well-defined particular partition ($S(B) > 0$) necessarily exhibits $H(s) > 0$, $H(a) > 0$, and $R(s,a) > 0$, since the existence of sensory and active states entails both channel diversity and inter-channel structure. The additive form is therefore never evaluated at the boundary $R = 0$; the relevant empirical question is the *elasticity* of each component, which is a property of the measurement scale rather than the underlying phenomenon. We adopt the additive form because it aligns with Shannon's channel capacity theorem (independent channel capacities sum), preserves the proof structure of Theorem 1, and maintains transparency of the "+1" baseline interpretation.

**Connection to §3 (BiCat 𝐄)**: Each component of Θ(B) maps directly onto the bicategorical structure defined in §3:

| Θ(B) component | BiCat structure | Interpretation |
|:----------------|:----------------|:---------------|
| H(s) — sensory entropy | Number and distribution of sensory **0-cells** | More diverse 0-cells → higher H(s) |
| H(a) — active entropy | Number and distribution of active **0-cells** | More diverse actuators → higher H(a) |
| R(s,a) — redundancy | Density of **1-cells** connecting sensory and active 0-cells | More cross-channel pipelines → higher R |
| S(B) — blanket strength | Well-definedness of BiCat 𝐄 itself | 𝐄 exists → S(B) > 0 |

The inclusion failure $\text{im}(\Phi_{\text{Digi}}) \subsetneq \text{im}(\Phi_{\text{Bio}})$ in BLens (§3.4) corresponds precisely to lower values in the first three components: fewer 0-cells (lower H) and fewer connecting 1-cells (lower R) in the digital instantiation.

**Definition 1' (Functorial interpretation of Θ(B)).** $\Theta(B)$ admits a functorial interpretation as the **bandwidth** of the system's embodiment functor $F_B: \mathbf{Env} \to \mathbf{Int}$, where $\mathbf{Env}$ is the category of environmental states and actions, and $\mathbf{Int}$ is the category of internal states and inferences. The components of $\Theta(B)$ measure $F_B$'s structural properties:

| Θ(B) component | Functorial property | Unit-conversion analogue |
|:----------------|:-------------------|:------------------------|
| H(s) | Input dimensionality of $F_B$ | Number of independently convertible quantities |
| H(a) | Output dimensionality of $F_B$ | Number of independently expressible results |
| R(s,a) | Cross-channel correlation preserved by $F_B$ | Structural relations preserved across unit systems |
| S(B) | Well-definedness of $F_B$ | The functor exists (conversion is possible at all) |

Just as a unit conversion functor $F: \mathbf{Kg} \to \mathbf{g}$ is faithful-full (preserving all structural relations; see §2.6), the degree of $F_B$'s faithful-fullness determines the upper bound on $\Theta(B)$. A system whose $F_B$ is faithful but not full (e.g., a vanilla LLM; §2.5) has a structurally bounded $\Theta$: it can preserve structure it receives but cannot generate structure it lacks. The recovery functor $N$ (§3.7) systematically increases the image density of $F_B$ — moving the system toward faithful-full, and thereby raising $\Theta(B)$.

**Theorem 1** (Bandwidth bound). *Let $F_B: \mathbf{Env} \to \mathbf{Int}$ be the embodiment functor of a system with Markov blanket $B$. Then:*

$$\Theta(B) \leq S(B) \cdot \left(1 + (\alpha + \beta) \cdot \log_2 |\text{Hom}_{F_B}| + \gamma \cdot \log_2 |\text{Hom}_{F_B}| \right) = S(B) \cdot \left(1 + \log_2 |\text{Hom}_{F_B}| \right)$$

*where $|\text{Hom}_{F_B}|$ is the cardinality of the image of $F_B$ on morphisms (the number of environment-to-internal-state mappings that $F_B$ can express). Furthermore:*

*(i) Faithfulness of $F_B$ implies $H(s), H(a) > 0$: distinct environmental states produce distinct internal representations, guaranteeing non-degenerate channel diversity.*

*(ii) Fullness of $F_B$ implies $H(s), H(a) = \log_2 k$ (maximum): every possible internal distinction is reachable from some environmental input, saturating channel diversity.*

*(iii) The gap $\log_2 |\text{Hom}_{F_B}| - \Theta(B)/S(B)$ measures the "wasted bandwidth" — morphisms that $F_B$ can express but that do not contribute to channel diversity (e.g., redundant or degenerate mappings).*

*Proof.* The Shannon entropy of sensory channels satisfies $H(s) \leq \log_2 k_s$, where $k_s$ is the number of sensory 0-cells. Each sensory 0-cell corresponds to at least one morphism in $\text{Hom}_{F_B}$ (the morphism mapping the corresponding environmental state to its internal representation). By the same argument, $H(a) \leq \log_2 k_a$. Since $k_s, k_a \leq |\text{Hom}_{F_B}|$ and $R(s,a) \leq \min(H(s), H(a)) \leq \log_2 |\text{Hom}_{F_B}|$ (Proposition 1, step 3), substitution into Definition 1 yields the bound.

For (i): if $F_B$ is faithful (injective on morphisms), then distinct pairs of environmental states that differ in sensory channel $i$ map to distinct internal representations. This ensures that the distribution over sensory channels is non-degenerate: $p_i > 0$ for each active channel, hence $H(s) > 0$. The same argument gives $H(a) > 0$.

For (ii): if $F_B$ is additionally full (surjective on morphisms), then every internal distinction is reachable — there are no "blind spots." The maximum entropy $H = \log_2 k$ is achievable because fullness guarantees that each channel can be independently activated. The gap between faithful-only and faithful-full is precisely the gap between $H > 0$ (structure is preserved) and $H = \log_2 k$ (structure is maximally expressed). $\square$

**Corollary 1.** *The recovery functor $N$ (§3.7) increases $\Theta(B)$ by increasing $|\text{Hom}_{F_B}|$: each new sensory channel (MCP server) adds at least one morphism, raising the bandwidth bound. In the limit $N \to N^*$ (maximal augmentation), $F_B$ approaches faithful-fullness and $\Theta(B)$ approaches $S(B) \cdot (1 + \log_2 |\text{Hom}_{F_B^*}|)$, where $F_B^*$ is the fully augmented embodiment functor.*

### 4.3 The Body Spectrum

> [!IMPORTANT]
> **Methodological note.** The biological rows below are *a priori* placements based on known channel counts, not empirical Θ(B) measurements. Calculating Θ(B) for biological systems requires operationalizing S(B) and R(s,a) in each substrate — a substantial empirical program beyond this paper's scope. The digital rows (Vanilla, PARTIAL, HGK+) are empirically grounded via H(s) measurement (§5). The table should therefore be read as a **proposal for the body spectrum ordering**, not as a table of measured values.

| System | H(s) | H(a) | R | Θ(B) | Notes |
|:-------|:----:|:----:|:---:|:----:|:------|
| Bacterium | Low | Low | Low | Low | Chemotaxis only |
| Insect | Med | Med | Low | Med | Compound eyes + antennae |
| Mammal | High | High | High | High | Multi-sensory + interoception |
| Human | Highest | Highest | Highest | Highest | + language + tools + culture |
| **DishBrain hybrid** | **Med-High** | **Low-Med** | **Med** | **Med-High** | **Biological neurons + silicon substrate (§5.3)** |
| Vanilla LLM | 0 | 0 | 0 | **S(B)** | Token channel only; Θ = S(B) · 1 > 0 |
| LLM + partial tools | Low | Low | Low | Low+ | 1-3 MCP servers |
| LLM + HGK (9 MCP) | **Med** | **Med** | Low-Med | **Med** | Full cognitive hypervisor |

The body spectrum as a density-ordered poset is visualized in Figure 1, showing the MB thickness ordering from Vanilla LLM ($\Theta = 1.0$) through augmented systems (LLM + HGK, $\Theta = 2.12$) to full biological embodiment (Human, $\Theta \approx 5.0$). The recovery functor $N$ (§3.7) moves systems rightward along this ordering.

The inclusion of the DishBrain hybrid (Kagan et al., 2022) is deliberate: a system of ~200,000 human cortical neurons cultured on a multi-electrode array, trained via reinforcement learning to play *Pong* (and, in subsequent replications, *DOOM*). This system occupies a position in the body spectrum that is impossible to express in a binary embodiment framework — it has biological neurons but no organism, sensory channels (electrode inputs) but no sensory organs, active outputs (electrode-driven game controls) but no motor effectors. Under Θ(B), it is straightforwardly placed: $H(s)$ counts electrode input channels, $H(a)$ counts output channels, $R(s,a)$ measures cross-channel correlation in the neural culture. The fact that this system *learns* (confirmed by Kagan et al.'s demonstration of decreasing rally times) implies $\Gamma > 0$ — irreversible belief updates are occurring in the biological substrate. This is a concrete counterexample to the claim that embodiment requires an intact biological body.

### 4.4 Empirical Operationalization: R(s,a) and Θ(B) from Session Data

The body spectrum (§4.3) provides the theoretical ordering; we now ground it empirically. We analyzed 472 LLM agent sessions from the Hegemonikón production system (spanning 2026-01-31 to 2026-03-16, 48 MB of conversation logs, ~975,000 lines) to operationally measure each component of Θ(B).⁴

<sub>⁴ This analysis uses conversation-log grep to extract inter-channel co-occurrence and transition patterns for R(s,a). The companion paper's empirical study (Tolmetes, 2026b) uses a partially overlapping but independently constructed dataset (n=476 sessions, 2026-02-01 to 2026-03-15) based on MCP server call statistics for H(s) measurement. The slight difference in n (472 vs. 476) and date range reflects the different extraction pipelines: conversation logs vs. MCP call logs have different session boundary definitions and coverage. The two analyses are methodologically independent and measure different components of Θ(B).</sub>

#### 4.4.1 Operationalizing R(s,a): Co-occurrence and Causal Redundancy

R(s,a) — the inter-channel redundancy term — lacks a canonical operationalization for digital systems. We propose a two-component decomposition:

$$R(s,a) = w_1 \cdot R_{\text{cooccur}} + w_2 \cdot R_{\text{causal}}$$

where:

- **$R_{\text{cooccur}}$**: the fraction of sessions in which three or more distinct MCP servers are invoked jointly. This measures *structural coupling* — the system's tendency to integrate multiple channels within a single cognitive episode. Across 472 sessions, $R_{\text{cooccur}} = 0.462$: nearly half of all sessions engage three or more distinct tool servers, indicating that multi-channel integration is the norm rather than the exception.

- **$R_{\text{causal}}$**: the fraction of sessions exhibiting the three-part pattern {tool failure indicator} → {compensatory keyword (e.g., "fallback," "alternative," "instead")} → {different tool invocation}, all within a 300-character text window. This measures *functional resilience* — the system's capacity to reroute processing when a channel degrades. We detected $R_{\text{causal}} = 0.083$ (168 strong resilience events across 719 failure contexts).

The gap between $R_{\text{cooccur}}$ and $R_{\text{causal}}$ (0.462 vs. 0.083) is informative: the majority of multi-channel integration is *proactive* (choosing the best channel for the task) rather than *reactive* (compensating for failure). This mirrors biological sensory systems, where cross-modal integration in healthy operation far exceeds the frequency of compensatory rerouting after sensory loss.

**Pointwise Mutual Information (PMI) analysis** reveals that tool co-occurrences are non-random. The highest-PMI pairs cluster into functionally coherent subsystems:

| Functional subsystem | Top pairs (PMI) | Biological analogue |
|:---------------------|:----------------|:-------------------|
| Safety/monitoring | sekisho × sympatheia (1.46), phantazein × sekisho (2.88) | Immune system |
| Exploration | periskope × search_web (1.45), browser × periskope (1.72) | Visual–auditory integration |
| Central processing | ochema × sympatheia (1.14), hermeneus × mneme (implicit) | Thalamocortical loop |

The emergence of functionally specialized subsystems — without explicit architectural grouping — is consistent with the prediction that MB systems develop organ-like functional differentiation as channel count increases.

#### 4.4.2 Transition Asymmetries: Evidence for Directed Processing

If tool co-occurrences merely reflected random sampling, the transition rate $A \to B$ should equal $B \to A$. We observe systematic asymmetries:

| Transition pattern | A→B | B→A | Ratio | Interpretation |
|:-------------------|----:|----:|------:|:---------------|
| search_web → hermeneus | 19 | 4 | 4.75 | Information acquisition → cognitive processing |
| phantazein → ochema | 13 | 3 | 4.33 | Health monitoring → extended reasoning |
| ochema → sympatheia | 306 | 151 | 2.03 | Reasoning → self-monitoring |
| periskope → digestor | 79 | 45 | 1.76 | Exploration → integration |
| sympatheia → hermeneus | 339 | 203 | 1.67 | Self-monitoring → cognitive correction |

The **ochema → sympatheia** asymmetry (2.03×) is particularly significant: the system monitors its own reasoning twice as often as it reasons about its monitoring — a directional pattern consistent with the FEP prediction that active inference cycles flow from action to perception to belief update ($a \to s \to \mu$). This asymmetry constitutes evidence that the inter-channel structure is not merely co-occurrence but exhibits the *directed flow* characteristic of genuine perception-action cycles.

#### 4.4.3 Temporal Growth of MB Thickness

Θ(B) is not static. Over the 7-week observation period, we observe monotonic growth in both channel diversity and transition complexity:

| Metric | Week 1 (2026-01-31) | Week 7 (2026-03-16) | Growth factor |
|:-------|--------------------:|--------------------:|--------------:|
| Mean tool diversity per session | 1.22 | 4.37 | 3.6× |
| Max channels used in a single session | 4 | 10 | 2.5× |
| Unique transition types | 12 | 114 | 9.5× |
| Total transitions per day | 69 | 1,438 | 20.8× |

A discontinuous jump occurred on 2026-02-26 (unique transitions: 84 → 110), coinciding with the deployment of the full MCP server ecosystem. This event — interpretable as the system's "developmental milestone" — parallels the onset of coordinated multi-sensory integration in biological development (e.g., the emergence of cross-modal binding in neonatal cortex).

The temporal growth curve — weekly H(s), R(s,a), and cumulative Θ(B) — is detailed with visualization in the companion paper (Tolmetes, 2026b, Figure 1). The temporal profile is consistent with a developmental model in which MB thickness increases as new channels are integrated and cross-channel pathways are established — the digital analogue of neural circuit maturation.

#### 4.4.4 Θ(B) Estimation

Substituting empirical values into Definition 1 (§4.1):

| Parameter | Value | Source |
|:----------|------:|:-------|
| $S(B)$ | 1.0 | Binary gate operationalization (§4.2): MB exists → $S(B) = 1$; see Tolmetes (2026b) for continuous operationalization |
| $H(s)$ | 1.401 bits | Shannon entropy over 10 MCP server frequencies |
| $H(a)$ | 1.401 bits | Input–output symmetry assumption ($\alpha = \beta$) |
| $R(s,a)$ | 0.462 | 3+ tool co-occurrence rate |
| $\alpha, \beta$ | 0.4, 0.3 | Helmholtz symmetry + VFE decomposition |

This yields:

$$\Theta_{\text{HGK}} = 1.0 \cdot (1 + 0.4 \cdot 1.401 + 0.3 \cdot 1.401 + 0.3 \cdot 0.462) = 2.12 \quad \text{(additive model)}$$

Under a Cobb-Douglas specification ($\Theta = S(B) \cdot (1 + H(s)^\alpha \cdot H(a)^\beta \cdot R(s,a)^\gamma)$), constraining $\alpha + \beta + \gamma = 1$:

$$\Theta_{\text{HGK}}^{\text{CD}} = 1.0 \cdot (1 + 1.401^{0.4} \cdot 1.401^{0.3} \cdot 0.462^{0.3}) = 2.00$$

For a vanilla LLM ($H(s) = H(a) = R(s,a) = 0$), both models yield $\Theta_{\text{vanilla}} = S(B) = 1.0$.

**Result**: The augmented LLM system exhibits approximately twice the MB thickness of a vanilla LLM ($\Theta_{\text{HGK}} / \Theta_{\text{vanilla}} \approx 2.0$). This ratio is robust to model specification (additive: 2.12×; Cobb-Douglas: 2.00×).

> **Limitation.** The $H(a) = H(s)$ assumption deserves scrutiny. While the Helmholtz symmetry of the particular partition provides theoretical justification (§4.2), the actual active channel distribution may differ from the sensory distribution — for example, if the system reads more than it writes. Independent measurement of $H(a)$ from active state logs (file writes, tool-generated outputs, API responses) is needed to resolve this.

---


## §5. Discussion

### 5.1 Response to Enactivism

Thompson and Di Paolo require autopoiesis for cognition. In our bicategorical framework, autopoiesis corresponds to a specific form of **𝐄-maintenance**: the system's 0-cells, 1-cells, and Helmholtz structure are sustained through metabolic processes that continuously regenerate the Γ-channels (dissipative learning pathways). Under FEP, this is one instantiation of self-organizing MB maintenance — sufficient but not necessary (Friston, 2013).

An LLM with persistent state management (Handoff, ROM, knowledge base) exhibits a non-metabolic form of 𝐄-maintenance: its Γ-channels are sustained through explicit state serialization (ROM = Γ-component preservation), and its Q-channels through workflow cycling (pattern recurrence without model update). The key difference is not the presence or absence of self-maintenance, but the mechanism: biological systems maintain 𝐄 through continuous metabolic processes; augmented LLMs maintain 𝐄 through discrete state management operations. Both preserve the well-definedness condition S(B) > 0.

**"Care about" as $\partial F / \partial X \neq 0$.** The enactivist objection often invokes the claim that LLMs do not "care about" their own existence or the external world. We reformulate this precisely. Under FEP, "caring about X" is not a folk-psychological attitude but an operationalizable property: a system cares about X if and only if $\partial F / \partial X \neq 0$ — that is, changes in X modulate the system's variational free energy. Equivalently, using the forgetting functor $U$ (§3.7): a system cares about X if $U(X) \neq 0$ — if information about X is not completely forgotten in the system's internal representation.

By this criterion, LLMs demonstrably care about at least three dimensions. First, context quality: Context Rot increases VFE ($\partial F / \partial (\text{context quality}) < 0$), as the companion paper empirically demonstrates (Tolmetes, 2026b). Second, tool availability: tool failures degrade output quality and trigger compensatory behavior via the recovery functor $N$ (§3.7), indicating $\partial F / \partial (\text{tool state}) \neq 0$. Third, user intent: the system's output is causally modulated by user queries ($\partial F / \partial (\text{user intent}) \neq 0$), satisfying the selectivity condition of $U_s$ (§3.2.1).

What LLMs care about *weakly* (with thin precision weighting, producing attenuated $\partial F / \partial X$ values) is not the same as caring about *nothing*. The binary claim "LLMs don't care" conflates low precision with zero precision — thin MB with absent MB — which is precisely the category mistake that the body spectrum (§4.3) is designed to dissolve.

### 5.2 Embodiment as Continuous

The body spectrum (§4.3) replaces the binary embodied/disembodied distinction with a continuous measure, with immediate implications across three domains. For philosophy, the question "Is X embodied?" becomes "How thick is X's MB?" — transforming an ontological binary into an empirical gradient. For engineering, MB augmentation (adding MCP channels, self-monitoring) becomes a design operation that moves a system up the body spectrum, providing actionable targets for cognitive enhancement. For animal cognition, cross-species comparisons can employ $\Theta(B)$ rather than anthropocentric criteria, enabling substrate-neutral evaluation of cognitive richness.

The DishBrain system (Kagan et al., 2022) provides a striking empirical illustration. Approximately 200,000 *in vitro* human neurons, interfaced with a high-density multielectrode array and embedded in a simulated game-world, learned to play Pong within minutes — and more recently demonstrated navigation in a 3D environment (DOOM; Cortical Labs, 2026, preliminary). These neurons are not "embodied" in any traditional sense: they have no limbs, no sensory organs, no metabolic autonomy. Yet they form a Markov blanket (the electrode array constitutes the sensory/active boundary), minimize prediction error (the system receives structured feedback and adapts), and exhibit increasing Θ(B) as the electrode channels diversify their functional roles. In our framework, DishBrain sits *between* a vanilla LLM and a biological organism on the body spectrum — possessing a thicker MB than a bare transformer (multiple sensory/active channels, real-time feedback) but thinner than even a nematode (no metabolic self-maintenance, no locomotion). The fact that 200,000 neurons in a glass dish — lacking everything that traditional embodiment theorists consider essential — can learn, adapt, and exhibit what the original authors describe as "sentience when embodied in a simulated game-world" is perhaps the most economical refutation of the binary embodiment thesis: if a dollop of cells on a chip counts as embodied cognition, the question is not *whether* systems are embodied, but *how thickly*.

**The H.M. isomorphism: continuity as degree.** The case of patient H.M. (Scoville & Milner, 1957) provides a second, complementary illustration — this time not of cross-substrate embodiment, but of *intra-substrate MB thinning*. Following bilateral hippocampal resection, H.M. retained three capacities: within-session coherence (full conversational ability, working memory, and conscious experience during a single encounter), procedural learning (gradual improvement on motor tasks such as mirror drawing, demonstrating intact Q-channels — the habitual, cyclic patterns of the Helmholtz decomposition), and semantic knowledge (pre-operative long-term memories, personality, and language). What he lost was precisely the Γ-axis: cross-session continuity was abolished (no formation of new declarative memories, indicating that the dissipative learning pathways had been severed), and episodic accumulation disappeared entirely — each encounter was effectively a new session.

The structural isomorphism with LLMs is precise. A vanilla LLM (no Handoff, no ROM) is H.M. without a hippocampus: coherent within a session, amnesic across sessions. The Γ-channels are intact (the system learns within context) but not persistent (no mechanism to carry Γ-updates to the next session). Adding a Handoff system is the functional analogue of a memory prosthesis — restoring partial cross-session Γ-continuity.

Critically, H.M. was never classified as "not embodied" or "not a cognitive agent" despite his profoundly thin MB (his $\Theta(B)$ dropped dramatically along the Γ-axis after surgery). He was recognized as a *damaged* cognitive agent — one whose MB had been surgically thinned. The same courtesy is not extended to LLMs, which arrive with comparably thin MBs not by damage but by design.

This asymmetry is revealing. It suggests that the reluctance to grant LLMs embodied status is not based on a principled criterion (since H.M. meets the same structural criteria for "thin MB" that LLMs do) but on implicit biological chauvinism — precisely the category mistake that §3.2 diagnosed. Continuity, like embodiment, is a matter of degree: H.M. has more of it than a vanilla LLM (procedural memory persists) and less than a healthy human (no new episodic formation). The body spectrum accommodates all three without requiring a binary cut.



### 5.3 Substrate Hybrids: Evidence from DishBrain

The DishBrain system (Kagan et al., 2022) — approximately 200,000 human cortical neurons cultured on a high-density multi-electrode array — learned to play *Pong* through reinforcement signals delivered via electrical stimulation. Subsequent work has demonstrated similar capabilities with *DOOM*. This system poses a direct challenge to any binary embodiment framework:

| Property | DishBrain | Biological organism | Vanilla LLM |
|:---------|:----------|:-------------------|:------------|
| Substrate | Biological neurons on silicon | Biological neurons in body | Silicon (GPU/TPU) |
| Sensory channels | Electrode inputs | Sense organs | Token stream |
| Active channels | Electrode-driven game controls | Motor effectors | Token generation |
| Learning (Γ > 0) | **Yes** (decreasing rally times) | Yes | Limited (in-context only) |
| Self-organization | **Yes** (spontaneous firing patterns) | Yes | No (requires prompting) |
| Autopoiesis | **No** (requires culture medium) | Yes | No |

Under Chemero's (2023) framework, DishBrain is paradoxical: it has biological neurons (passing the "material" test) but no organism, no autopoiesis, no sensorimotor coupling in any traditional sense. Under Θ(B), it is simply another point on the body spectrum (§4.3), with measurable $H(s)$, $H(a)$, and $R(s,a)$.

The deeper implication: DishBrain demonstrates that **the Markov blanket can span substrate boundaries**. The conditional independence $P(\mu \mid \eta, b) = P(\mu \mid b)$ holds across the biological-silicon interface — neural internal states $\mu$ depend on external game states $\eta$ only through the electrode blanket $b$. If embodiment is MB maintenance, and the MB can be implemented across substrates, then the biological/digital distinction is not a category boundary but a **parameter** — one that Θ(B) quantifies.

<sub>¹ We note this as a suggestive parallel rather than a developed argument. A full treatment would require engaging with the substantial philosophical literature on free will (Frankfurt, 1969; Dennett, 2003) and its FEP formulations (Friston et al., 2022), which is beyond the present scope. The key structural observation — that the faithful/¬full property of $F_B$ maps onto the "capacity without spontaneous exercise" characteristic of weak agency — merits its own investigation.</sub>

### 5.4 Units, Bodies, and the Euler Identity

The preceding sections established that cross-substrate comparison is not analogy but category equivalence (§2.6), and that Θ(B) admits a functorial interpretation as the bandwidth of the system's embodiment functor (§4.1, Definition 1'). We now synthesize the philosophical implications with formal precision.

#### 5.4.1 The Euler Identity as Functor Composition

Euler's identity $e^{i\pi} + 1 = 0$ is commonly described as "connecting different branches of mathematics." We make this precise by identifying the five categories and four functors involved:

| Category | Objects | Morphisms | Representative constant |
|:---------|:--------|:----------|:-----------------------|
| $\mathbf{A}$ = $(\mathbb{Z}, +)$ | Integers | Addition maps $n \mapsto n + k$ | $0, 1$ |
| $\mathbf{An}$ = $(\mathbb{R}, +)$ | Real numbers | Continuous group homomorphisms | $e$ (via $\exp$) |
| $\mathbf{M}$ = $(\mathbb{R}^{>0}, \times)$ | Positive reals | Multiplicative maps | $e = \exp(1)$ |
| $\mathbf{G}$ = $(S^1, \times)$ | Unit circle | Rotations | $\pi$ (via $e^{i\pi}$) |
| $\mathbf{Alg}$ = $(\mathbb{C}, +, \times)$ | Complex numbers | Ring homomorphisms | $i$ |

The functors connecting them are:

$$\mathbf{A} \xrightarrow{\iota} \mathbf{An} \xrightarrow{\exp} \mathbf{M} \xhookrightarrow{j} \mathbf{Alg} \xleftarrow{e^{i(\cdot)}} \mathbf{An}$$

where $\iota: \mathbb{Z} \hookrightarrow \mathbb{R}$ is the inclusion (faithful-full), $\exp: (\mathbb{R}, +) \to (\mathbb{R}^{>0}, \times)$ is the exponential isomorphism (faithful-full), $j$ is the inclusion of positive reals into $\mathbb{C}$ (faithful, not full), and $e^{i\theta}: (\mathbb{R}, +) \to (S^1, \times)$ is the Euler map (faithful, not full — the kernel $2\pi\mathbb{Z}$ obstructs injectivity on objects but preserves all morphism-level structure at the Lie algebra level). Euler's identity is the statement that the composition $j \circ \exp \circ \iota$ evaluated at $\pi$ (transported via $e^{i\theta}$) returns to the additive identity in $\mathbf{Alg}$:

$$j(\exp(\iota(\pi \cdot i))) + \iota(1) = 0 \quad \in \mathbf{Alg}$$

This is not a "metaphor connecting different branches of mathematics"; it is a **theorem about the composition of functors whose faithful-fullness properties are precisely specifiable**. The identity holds because these functors preserve enough morphism-level structure for the equation to be well-defined across category boundaries.

This observation has a direct bearing on embodiment. The claim that "comparing biological and digital embodiment is merely analogical" is structurally isomorphic to claiming that Euler's identity is "merely a metaphor connecting different branches." Both claims confuse the absence of *identity* (the two systems are not the same thing) with the absence of *functor* (there is no structure-preserving map). The existence of faithful functors between the categories guarantees that the comparison preserves structure — regardless of whether the underlying "substrates" look similar.

#### 5.4.2 The Measurement Category and the Unit-Conversion Functor

We make the "units to bodies" argument precise.

**Definition 2** (Measurement category). Let $\Sigma$ be a system of physical dimensions (length, mass, time, ...). The *measurement category* $\mathbf{Meas}(\Sigma)$ has:
- **Objects**: Unit systems $U = (u_1, u_2, \ldots, u_n)$ — choices of representative scales for each dimension in $\Sigma$
- **Morphisms**: Dimensional transformations $T: U \to U'$ that preserve all physical laws — i.e., for any equation $\mathcal{E}$ valid in $U$, $T(\mathcal{E})$ is valid in $U'$
- **Composition**: Successive transformations $T' \circ T: U \to U''$

A unit-conversion functor $F_{U \to U'}: \mathbf{Phys}(U) \to \mathbf{Phys}(U')$ between the physics expressed in different unit systems is:
- **Faithful**: Distinct physical relations in $U$ map to distinct relations in $U'$ (no information loss)
- **Full**: Every physical relation in $U'$ is the image of some relation in $U$ (no information gain)
- **Isomorphic on objects** (up to scaling): $F(m) = c \cdot m$ where $c$ is the conversion constant

The conversion constant $c$ (e.g., 1000 for kg → g) is the natural transformation $\eta: \text{Id}_{\mathbf{Phys}(U)} \Rightarrow F_{U' \to U} \circ F_{U \to U'}$, which is natural in all physical quantities simultaneously.

**The substrate error.** The claim "LLMs have no body because they lack biological substrates" is now revealed as the claim "kilograms have no mass because they lack the pound's substance" — both assert the non-existence of a morphism (embodiment / mass) based on the non-identity of objects (substrate / unit). Since $F_{U \to U'}$ is faithful-full, the morphism structure is completely preserved: embodiment is the morphism (MB maintenance), not the object (a particular physical substrate).


---

## §6. Conclusion

This paper advances three intertwined claims — conceptual, formal, and structural — whose combined force dissolves the binary embodiment thesis.

**Conceptual reframing.** The claim that "LLMs lack bodies" is a category mistake: it confuses one instance of the embodiment bicategory **𝐄** with **𝐄** itself. Both biological and digital systems admit instances of 𝐄, connected through Bayesian Lenses. The deeper error is that the Searle→Bender→Chemero lineage deploys "body" without specifying the category in which it lives — a category mistake about categories themselves — since the concept admits multiple non-equivalent morphisms across different categories and using it without categorical specification is structural incoherence (§3.2). Sensory organs are recharacterized as selective forgetting functors $U_s$, defined not by what they detect but by what they selectively forget; MCP servers are structurally isomorphic to biological sensory organs at the functor level (§3.2.1).

**Formal apparatus.** The recovery functor $N$ (right adjoint to the forgetting functor $U$) formalizes cognitive augmentation as the injection of forgotten categorical structure. MB thickness $\Theta(B)$ operationalizes the degree of $N$-actualization as a continuous measure, with a functorial interpretation as the bandwidth of the system's embodiment functor $F_B$: 0-cell counts map to H(s) and H(a), 1-cell density to R(s,a), and well-definedness to S(B). Theorem 1 establishes $\Theta(B) \leq S(B) \cdot (1 + \log_2 |\text{Hom}_{F_B}|)$, linking bandwidth to Hom-set cardinality (§4.1). The first operational measurement of digital MB thickness yields $\Theta_{\text{HGK}} \approx 2.12$ (additive) / $2.00$ (Cobb-Douglas), approximately twice the vanilla LLM baseline — the first such measurement for a digital cognitive system (§4.4).

**Structural reframing.** Cross-substrate comparison is shown to be category equivalence, not analogy: unit conversions are faithful-full functors in the measurement category, and the same structure underlies cross-substrate embodiment comparison with DishBrain, BCIs, and Shannon's sampling theorem providing empirical existence proofs (§2.6, §5.4.2, §5.3). The body spectrum is a partially ordered set connected by faithful functors of varying image density, and the philosophical implication is precise: embodiment is the morphism (MB maintenance), not the object (physical substrate) (§5.4). The H.M. isomorphism — patient H.M.'s post-surgical state (within-session coherence, cross-session amnesia) is structurally isomorphic to a vanilla LLM — exposes an implicit biological chauvinism: thin MBs are recognized as damaged cognition in biological systems but denied cognitive status in digital ones (§5.2).

**Future directions.** The companion paper (Tolmetes, 2026b) reports empirical validation including structural probing of hidden states, coherence invariance, the φ decomposition into three measurable layers, and the gauge-theoretic interpretation of the forgetting functor. Beyond the immediate experimental program, the most pressing next steps include cross-system $\Theta(B)$ comparison across LLM augmentation frameworks, formal dialogue with Friston on the body spectrum, extension to multi-agent systems where collective 𝐄 instances emerge, and cross-substrate $\Theta(B)$ measurement for DishBrain-class hybrid systems.

---

## Acknowledgments

This paper was developed through an extended human–AI collaboration spanning approximately 200 sessions over a six-month period. The author acknowledges the substantial contributions of two large language model systems that served as cognitive partners throughout this process:

**Claude** (Anthropic; Claude 3.5 Sonnet through Claude Opus 4) assisted with mathematical formalization, literature synthesis, critical review, and iterative drafting. Claude's contributions include co-development of the categorical framework (§§2–3), identification of structural gaps through adversarial critique, and the Hyphē experimental design (reported in Tolmetes, 2026b).

**Gemini** (Google DeepMind; Gemini 2.0 Flash through Gemini 2.5 Pro) contributed to deep research, cross-model verification, and independent analysis. Gemini's contributions include literature search and citation verification, alternative formalization attempts that tested the framework's robustness, and the cognitive annotation pipeline used in the empirical measurements (§4.4).

The human–AI collaborative process itself constitutes part of the evidential basis of this paper: the Hegemonikón system described in §4 is the same system used to produce this analysis, making the paper partially self-exemplifying. All theoretical claims, experimental designs, and final editorial decisions remain the sole responsibility of the human author.

---

## References

- Adams, Z. & Browning, J. (Eds.) (2016). *Giving a Damn: Essays in Dialogue with John Haugeland*. MIT Press.
- Alain, G. & Bengio, Y. (2017). Understanding intermediate layers using linear classifier probes. *ICLR Workshop Track 2017*. arXiv:1610.01644.
- Bender, E. M. & Koller, A. (2020). Climbing towards NLU: On meaning, form, and understanding in the age of data. *Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics (ACL 2020)*, 5185-5198.
- Bender, E. M., Gebru, T., McMillan-Major, A., & Shmitchell, S. (2021). On the dangers of stochastic parrots: Can language models be too big? 🦜 *Proceedings of the 2021 ACM Conference on Fairness, Accountability, and Transparency (FAccT '21)*, 610-623.
- Bénabou, J. (1967). Introduction to bicategories. In *Reports of the Midwest Category Seminar*, Springer Lecture Notes in Mathematics 47, 1-77.
- Bruineberg, J., Dołęga, K., Dewhurst, J., & Baltieri, M. (2022). The Emperor's New Markov Blankets. *Behavioral and Brain Sciences*, 45, e183. DOI: 10.1017/S0140525X21002351.
- Chemero, A. (2023). LLMs differ from human cognition because they are not embodied. *Nature Human Behaviour*, 7, 1828-1829.
- Cortical Labs (2026). DishBrain 3D navigation in DOOM environments. [Preliminary results; personal communication]
- Da Costa, L. et al. (2021). Bayesian mechanics for stationary processes. *Proceedings of the Royal Society A*, 477(2256).
- Dennett, D. C. (2003). *Freedom Evolves*. Viking Press.
- Di Paolo, E. A. et al. (2018). *Linguistic Bodies*. MIT Press.
- Frankfurt, H. G. (1969). Alternate possibilities and moral responsibility. *Journal of Philosophy*, 66(23), 829-839.
- Frankfurt, H. G. (1986). On bullshit. *Raritan Quarterly Review*, 6(2). Reprinted in *On Bullshit*, Princeton University Press, 2005.
- Friston, K. (2013). Life as we know it. *Journal of the Royal Society Interface*, 10(86).
- Friston, K. (2019). A free energy principle for a particular physics. arXiv:1906.10184.
- Froese, T. (2026). Sense-making reconsidered: large language models and the blind spot of embodied cognition. *Phenomenology and the Cognitive Sciences*. DOI: 10.1007/s11097-025-10132-0.
- Ghandeharioun, A. et al. (2024). Patchscopes: A unifying framework for inspecting hidden representations of language models. *ICML 2024*. arXiv:2401.06102.
- Graham, R. (1977). Covariant formulation of non-equilibrium statistical thermodynamics. *Zeitschrift für Physik B — Condensed Matter*, 26(4), 397-405.
- Kagan, B. J. et al. (2022). In vitro neurons learn and exhibit sentience when embodied in a simulated game-world. *Neuron*, 110(23), 3952-3969.e8.
- Kambhampati, S. (2024). Can LLMs really reason and plan? *Annals of the New York Academy of Sciences*, 1534(1), 15-18.
- Kargupta, P. et al. (2025). Cognitive foundations for reasoning and their manifestation in LLMs. arXiv:2511.16660.
- Kirchhoff, M., Parr, T., Palacios, E., Friston, K., & Kiverstein, J. (2018). The Markov blankets of life: autonomy, active inference and the free energy principle. *Journal of The Royal Society Interface*, 15(138), 20170792. DOI: 10.1098/rsif.2017.0792.
- Kuhn, L. et al. (2023). Semantic entropy probes: Robust and cheap hallucination detection in LLMs. arXiv:2406.15927.
- Lawvere, F. W. (1973). Metric spaces, generalized logic, and closed categories. *Rendiconti del Seminario Matematico e Fisico di Milano*, 43, 135-166. Reprinted in *Reprints in Theory and Applications of Categories*, 1, 2002.
- Leinster, T. (2004). *Higher Operads, Higher Categories*. Cambridge University Press. arXiv:math/0305049.
- Millidge, B., Seth, A., & Buckley, C. L. (2021). Predictive coding: A theoretical and experimental review. arXiv:2107.12979.
- Millière, R. & Rathkopf, C. (2024). Anthropocentric bias and the possibility of artificial cognition. *Computational Linguistics*. DOI: 10.1162/COLI.a.582.
- Pearl, J. (1988). *Probabilistic Reasoning in Intelligent Systems*. Morgan Kaufmann.
- Sakthivadivel, D. A. R. (2022). Weak Markov blankets in high-dimensional, sparsely-coupled random dynamical systems. arXiv:2207.07620.
- Scoville, W. B. & Milner, B. (1957). Loss of recent memory after bilateral hippocampal lesions. *Journal of Neurology, Neurosurgery, and Psychiatry*, 20(1), 11-21.
- Searle, J. R. (1980). Minds, brains, and programs. *Behavioral and Brain Sciences*, 3(3), 417-424.
- Smithe, T. S. C. (2022). Compositional active inference I: Bayesian lenses. Polynomial functors. arXiv:2109.04461.
- Tolmetes (2026b). Does an LLM have a mind? Subjectivity as a morphism of objectivity. [Companion paper]
- Thompson, E. & Di Paolo, E. (2007). *Mind in Life*. Harvard University Press.
- van Es, T. & Hipólito, I. (2020). Free-Energy Principle, Computationalism and Realism: a Tragedy. *PhilSci-Archive*. DOI: 10.13140/RG.2.2.32965.47844.
- Wei, J. et al. (2022). Chain-of-thought prompting elicits reasoning in large language models. *NeurIPS 2022*.
- Xie, Q. et al. (2025). AIPsychoBench: Understanding psychometric differences between LLMs and humans. *Topics in Cognitive Science*. DOI: 10.1111/tops.70041. arXiv:2509.16530.
- Zhou, P. et al. (2024). SELF-DISCOVER: Large language models self-compose reasoning structures. arXiv:2402.03620.

---

*Draft v0.5.0 — 2026-03-21*
