# Analogical Free Energy: How Functors Reduce the Complexity Cost of Learning

> **Draft v0.3** — 2026-03-16
> 親エッセイ: バカをやめたいなら構造を見ろ_v1.md

---

## Abstract

We prove that faithful functors between categories reduce the Complexity cost
(in the sense of Variational Free Energy) of learning models in a target domain,
by transferring learned structure from a source domain as an informative prior.
This result formalizes the cognitive efficiency of analogy — long recognized in
cognitive science (Gentner, 1983) and recently formalized via category theory
(Ott, 2025; Phillips, 2022) — within the Free Energy Principle framework
(Friston, 2010; Smithe, 2023). We introduce an *Information Preservation Index*
$\mathcal{I}(F)$ that quantifies a functor's faithfulness, derive a
decomposition $\Delta_F = \Delta_{\max} - \varepsilon_F$ of the achievable
Complexity reduction, and characterize the cost of unfaithfulness $\kappa_F$.
A key finding is that $\kappa_F$ is sign-indefinite — unfaithful functors can
accidentally improve the prior — but faithful functors are minimax-optimal:
they guarantee no structural information loss regardless of the target
distribution. This reframes Gentner's Systematicity Principle as a
decision-theoretic robustness criterion.

---

## §1. Introduction

### 1.1 The Problem

Why is analogy efficient? Cognitive science has long recognized that analogical
reasoning — the transfer of relational structure from a known domain to a new
one — is a powerful cognitive tool (Gentner, 1983; Holyoak & Thagard, 1995).
Recent work has formalized analogy as a functor between categories (Ott, 2025;
Phillips, 2022). Separately, the Free Energy Principle (FEP) provides a
mathematical framework for understanding cognition as Variational Free Energy
(VFE) minimization (Friston, 2010), and Smithe et al. (2023) have given this
framework a category-theoretic formulation.

However, **no existing work connects these three threads**: the functorial
formalization of analogy, the VFE framework, and the question of why analogy is
computationally efficient. This paper fills that gap.

### 1.2 Main Contribution

We prove:

1. **Theorem 1 (Analogical Complexity Reduction)**: A faithful functor
   $F: \mathbf{C} \to \mathbf{D}$, combined with a learned model in
   $\mathbf{C}$, yields a prior in $\mathbf{D}$ that reduces the Complexity
   term of VFE compared to an uninformative prior.

2. **Definition (Information Preservation Index)**: A quantitative measure
   $\mathcal{I}(F) \in [0, 1]$ of a functor's structure-preserving capacity,
   connecting faithfulness (category theory) to Complexity reduction
   (information theory).

3. **Theorem 2 (Decomposition and Bounds)**: The Complexity reduction
   decomposes as $\Delta_F = \Delta_{\max} - \varepsilon_F$, where
   $\varepsilon_F$ quantifies the imperfection of the functorial prior.
   The cost of unfaithfulness $\kappa_F$ is sign-indefinite, establishing
   faithfulness as the minimax-optimal analogy strategy.

4. **Proposition (Gentner Revisited)**: Gentner's Systematicity Principle is
   equivalent to maximizing $\mathcal{I}(F)$ — i.e., to choosing the
   minimax-robust analogy.

---

## §2. Preliminaries

### 2.1 Variational Free Energy

Following Friston (2010) and Parr, Pezzulo & Friston (2022), the Variational
Free Energy (VFE) of an agent with approximate posterior $q(s)$, generative
model $p(o, s)$, and observations $o$ is:

$$F[q] = \underbrace{D_{KL}[q(s) \| p(s)]}_{\text{Complexity}} - \underbrace{\mathbb{E}_q[\ln p(o \mid s)]}_{\text{Accuracy}}$$

The **Complexity** term $D_{KL}[q(s) \| p(s)]$ measures the divergence of the
approximate posterior from the prior. It represents the "cost" of updating
beliefs from prior to posterior.

**Key observation**: Complexity depends on the choice of prior $p(s)$. A prior
that is closer to the true posterior incurs lower Complexity.

### 2.2 Categories, Functors, Faithfulness

A **category** $\mathbf{C}$ consists of objects $\text{Ob}(\mathbf{C})$,
morphisms $\text{Mor}(\mathbf{C})$, and a composition law (Mac Lane, 1998).

A **functor** $F: \mathbf{C} \to \mathbf{D}$ maps objects to objects and
morphisms to morphisms, preserving composition and identities.

A functor $F$ is:
- **Faithful** if for all $A, B \in \text{Ob}(\mathbf{C})$, the map
  $F_{A,B}: \text{Hom}_\mathbf{C}(A, B) \to \text{Hom}_\mathbf{D}(F(A), F(B))$
  is injective.
- **Full** if each $F_{A,B}$ is surjective.
- **Fully faithful** if each $F_{A,B}$ is bijective.

Faithfulness means: **distinct relationships in C remain distinct in D**.
No distinctness of relationships is lost (faithfulness is injection, not
surjection — it preserves distinctions, not totality).

### 2.3 Push-forward of Distributions

Given a functor $F: \mathbf{C} \to \mathbf{D}$ and a probability distribution
$q$ over the **objects** of $\mathbf{C}$, the **push-forward**
$F_* q$ is the distribution over $\text{Ob}(\mathbf{D})$ defined by:

$$(F_* q)(d) = \sum_{c \in F^{-1}(d)} q(c)$$

for each $d \in \text{Ob}(\mathbf{D})$.

**Scope note.** Throughout this paper, distributions and KL divergences are
defined over object spaces. The IPI (Definition 2, §4.1) is defined over
morphism spaces. This separation is a deliberate modeling choice: objects carry
probabilistic mass ("which concept is active?"), while morphisms carry
structural information ("which relations are preserved?"). The connection
between these two levels is mediated by the functor: faithfulness on morphisms
guarantees that the object-level push-forward preserves structural distinctions
(see §4, §8.1 Limitation 4 for further discussion).

When $F$ is faithful, the push-forward preserves the relational structure
encoded in $q$.

---

## §3. Main Result: Analogical Complexity Reduction

### 3.1 Setup

Consider an agent that has learned a model of domain $\mathbf{C}$:
- Generative model: $M_C = p_C(o, s)$
- Learned approximate posterior: $q_C(s)$
- The agent has minimized $F[q_C]$, so $q_C$ is a good approximation.

The agent now encounters a new domain $\mathbf{D}$ and must learn a model
$M_D = p_D(o', s')$ with approximate posterior $q_D(s')$.

**Two strategies:**

**Strategy 1 (De novo):** Use an uninformative prior $p_0(s')$ (e.g., uniform).
$$\text{Complexity}_{\text{novo}} = D_{KL}[q_D \| p_0]$$

**Strategy 2 (Analogical):** Identify a functor $F: \mathbf{C} \to \mathbf{D}$
and use the push-forward $F_* q_C$ as the prior for $\mathbf{D}$.
$$\text{Complexity}_{\text{analogy}} = D_{KL}[q_D \| F_* q_C]$$

### 3.2 Theorem (Analogical Complexity Reduction)

**Theorem 1.** Let $F: \mathbf{C} \to \mathbf{D}$ be a functor. Let $q_C$ be
a distribution over $\mathbf{C}$ and $q_D$ be the target posterior over
$\mathbf{D}$. Define:

$$\Delta_F := \text{Complexity}_{\text{novo}} - \text{Complexity}_{\text{analogy}} = D_{KL}[q_D \| p_0] - D_{KL}[q_D \| F_* q_C]$$

Then:

$$\Delta_F = \mathbb{E}_{q_D}\left[\ln \frac{F_* q_C(s')}{p_0(s')}\right]$$

Moreover, $\Delta_F \geq 0$ if and only if:

$$D_{KL}[q_D \| p_0] \geq D_{KL}[q_D \| F_* q_C]$$

which holds whenever $F_* q_C$ is a better approximation to $q_D$ than $p_0$
in the sense of KL divergence.

**Proof.**

By definition of KL divergence:

$$D_{KL}[q_D \| p_0] = \mathbb{E}_{q_D}\left[\ln \frac{q_D(s')}{p_0(s')}\right]$$

$$D_{KL}[q_D \| F_* q_C] = \mathbb{E}_{q_D}\left[\ln \frac{q_D(s')}{F_* q_C(s')}\right]$$

Taking the difference:

$$\begin{aligned}
\Delta_F &= D_{KL}[q_D \| p_0] - D_{KL}[q_D \| F_* q_C] \\
&= \mathbb{E}_{q_D}\left[\ln \frac{q_D}{p_0} - \ln \frac{q_D}{F_* q_C}\right] \\
&= \mathbb{E}_{q_D}\left[\ln \frac{F_* q_C(s')}{p_0(s')}\right]
\end{aligned}$$

This quantity equals the **expected log-likelihood ratio** of the functorial
prior over the uninformative prior, evaluated under the true posterior.

**Interpretation**: $\Delta_F > 0$ when, on average under $q_D$, the functorial
prior $F_* q_C$ assigns higher probability than $p_0$ to the states that the
true posterior considers likely. In other words, the analogy is "good" when the
transferred structure from C correctly anticipates the structure of D.

$\square$

### 3.3 Corollary: Sufficient Condition for Analogical Advantage

**Corollary 1.1.** If $p_0$ is the uniform distribution over
$|\text{Ob}(\mathbf{D})|$ states, then:

$$\Delta_F = \ln |\text{Ob}(\mathbf{D})| + \mathbb{E}_{q_D}[\ln F_* q_C(s')] = \ln |\text{Ob}(\mathbf{D})| - H_{\times}(q_D, F_* q_C)$$

where $H_{\times}(q_D, F_* q_C) = -\mathbb{E}_{q_D}[\ln F_* q_C(s')]$ is the
cross-entropy.

Since $H_\times(q_D, F_* q_C) \leq \ln |\text{Ob}(\mathbf{D})|$ whenever
$F_* q_C$ has non-zero support on $\text{supp}(q_D)$, we have $\Delta_F \geq 0$.

**Equality** $\Delta_F = 0$ holds iff $F_* q_C = p_0$ (the functor produces
the uniform prior — e.g., a constant functor mapping all objects to a single
point).

### 3.4 Remark: Why This Is Not Trivial

One might object: "Of course a better prior reduces KL divergence. This is
trivially true."

We offer three responses:

1. **The non-trivial claim is the connection, not the components.** The fact
   that a functor (a category-theoretic notion) generates a prior (a
   probabilistic notion) that reduces Complexity (an information-theoretic
   notion) bridges three distinct mathematical frameworks. This bridge is new.

2. **The conditions for "goodness" are non-trivial.** Theorem 1 makes precise
   when analogy helps: $\Delta_F > 0$ iff $F_* q_C$ is closer to $q_D$ than
   $p_0$. This connects to the cognitive science question of what makes a
   "good" analogy (Gentner's systematicity).

3. **The quantification is non-trivial.** §4 introduces the Information
   Preservation Index, which relates the algebraic property of faithfulness to
   the magnitude of $\Delta_F$. See §7.2 for a fuller discussion.

---

## §4. Information Preservation Index

### 4.1 Definition

**Definition 2.** The **Information Preservation Index** (IPI) of a functor
$F: \mathbf{C} \to \mathbf{D}$ is:

$$\mathcal{I}(F) := \frac{\sum_{A,B} |F_{A,B}(\text{Hom}_\mathbf{C}(A,B))|}{\sum_{A,B} |\text{Hom}_\mathbf{C}(A,B)|} \in [0, 1]$$

where the sum ranges over all pairs of objects $(A, B)$ in $\mathbf{C}$.

**Properties:**
- $\mathcal{I}(F) = 1$ iff $F$ is faithful (no morphisms are identified)
- $\mathcal{I}(F) > 0$ for any functor (since functors preserve identities,
  each hom-set image contains at least one element). The infimum
  $\mathcal{I}(F) \to 0$ is approached as the ratio of preserved to total
  morphisms vanishes, but is never attained.
- $\mathcal{I}(F \circ G) \leq \mathcal{I}(F) \cdot \mathcal{I}(G)$
  (composition cannot increase information preservation)

### 4.2 Theorem 2a (Decomposition of Complexity Reduction)

**Theorem 2a.** With $p_0$ uniform over $|\mathbf{D}|$ states:

$$\Delta_F = \underbrace{\ln |\mathbf{D}| - H(q_D)}_{\Delta_{\max}} - \underbrace{D_{KL}[q_D \| F_* q_C]}_{\varepsilon_F}$$

where:
- $\Delta_{\max}$ = maximum possible Complexity reduction (achieved by a
  perfect oracle prior $p = q_D$)
- $\varepsilon_F$ = **analogy imperfection** — residual KL divergence between
  the true posterior and the functorial prior

**Proof.** From Corollary 1.1:

$$\Delta_F = \ln |\mathbf{D}| - H_\times(q_D, F_* q_C)$$

Decompose the cross-entropy using the identity
$H_\times(p, q) = H(p) + D_{KL}[p \| q]$:

$$H_\times(q_D, F_* q_C) = H(q_D) + D_{KL}[q_D \| F_* q_C]$$

Substituting:

$$\Delta_F = \ln |\mathbf{D}| - H(q_D) - D_{KL}[q_D \| F_* q_C] = \Delta_{\max} - \varepsilon_F$$

Since $D_{KL} \geq 0$, we have $\Delta_F \leq \Delta_{\max}$. Equality holds
iff $F_* q_C = q_D$ (perfect analogy). $\square$

**Interpretation**: Complexity reduction is bounded above by the entropy gap
between the uniform prior and the true posterior. The functor's contribution is
to close this gap; how much it closes depends on how well $F_* q_C$
approximates $q_D$.

### 4.3 Theorem 2b (Faithful Functor Bound)

**Theorem 2b.** Let $F: \mathbf{C} \to \mathbf{D}$ be a faithful embedding
($\mathcal{I}(F) = 1$, injective on objects). Then:

$$\Delta_F \geq \ln |\mathbf{D}| - H(q_C) - D_{KL}[q_D \| F_* q_C]$$

In particular, if $q_D = F_* q_C$ (perfect analogy):

$$\Delta_F^{\text{perfect}} = \ln |\mathbf{D}| - H(q_C)$$

**Proof.** Since $F$ is injective on objects, the object-level map
$F: \text{Ob}(\mathbf{C}) \to \text{Ob}(\mathbf{D})$ is a deterministic
injection. The push-forward $F_* q_C$ is then a distribution on
$\text{Ob}(\mathbf{D})$ concentrated on the image $F(\text{Ob}(\mathbf{C}))$.

By the data processing inequality for deterministic injective channels:

$$H(F_* q_C) = H(q_C)$$

(Injective maps preserve entropy — no states are merged, and the additional
states in $\mathbf{D} \setminus F(\mathbf{C})$ receive zero mass.)

From Theorem 2a:
$$\Delta_F = \ln |\mathbf{D}| - H(q_D) - D_{KL}[q_D \| F_* q_C]$$

For the perfect analogy case ($q_D = F_* q_C$), $D_{KL} = 0$ and
$H(q_D) = H(F_* q_C) = H(q_C)$, giving:

$$\Delta_F^{\text{perfect}} = \ln |\mathbf{D}| - H(q_C)$$

$\square$

**Remark.** The "injective on objects" assumption means the analogy maps
distinct source concepts to distinct target concepts. This is natural for
structural analogy (e.g., Sun ↦ nucleus, planet ↦ electron are distinct). When
$F$ is surjective but not injective on objects, some source concepts merge,
and the entropy inequality becomes $H(F_* q_C) \leq H(q_C)$ (with possible
strict inequality). The bound still holds but with a weaker equality
condition.

**Interpretation**: A faithful embedding from a well-learned source (low
$H(q_C)$) to a large target domain (high $\ln |\mathbf{D}|$) achieves the
greatest Complexity reduction. This formalizes the intuition that analogy is
most powerful when transferring concentrated knowledge to an unfamiliar domain.

### 4.4 Theorem 2c (Cost of Unfaithfulness)

**Setup.** Let $F: \mathbf{C} \to \mathbf{D}$ be a functor with
$\mathcal{I}(F) < 1$, meaning $F$ identifies some morphisms. Let
$F^{\dagger}$ be a faithful extension (agreeing on objects, injective on all
hom-sets).

**Definition.** The **cost of unfaithfulness** is:

$$\kappa_F = D_{KL}[q_D \| F_* q_C] - D_{KL}[q_D \| F^{\dagger}_* q_C]
= \mathbb{E}_{q_D}\left[\ln \frac{(F^{\dagger}_* q_C)}{(F_* q_C)}\right]$$

**Theorem 2c.** $\kappa_F$ satisfies:

(i) **Support Catastrophe**: If $\text{supp}(q_D) \not\subseteq
\text{supp}(F_* q_C)$, then $\kappa_F = +\infty$. The analogy is not merely
unhelpful but actively harmful — worse than no prior at all. This is the
**mathematical diagnosis of false analogy**.

(ii) **Harmless Identification**: If $F$ identifies only morphisms outside
$\text{supp}(q_C)$, then $\kappa_F = 0$.

(iii) **Sign Indeterminacy**: In general, $\kappa_F$ can be positive, negative,
or zero for a given $q_D$.

**Proof.**

*(i)* Immediate: if $(F_* q_C)(d) = 0$ for some $d$ with $q_D(d) > 0$, then
$D_{KL}[q_D \| F_* q_C] = +\infty$.

*(ii)* If $F$ identifies $f_1, f_2$ with $q_C(f_1) = q_C(f_2) = 0$, no
probability mass is moved, so $(F_* q_C)(d) = (F^{\dagger}_* q_C)(d)$ for all
$d$ in $\text{supp}(q_D)$. The log-ratio vanishes. $\square$

**Remark on (iii).** The possibility $\kappa_F < 0$ (an unfaithful functor
accidentally provides a *better* prior) is genuine but fragile. An unfaithful
$F$ that merges states in a way that concentrates mass exactly where $q_D$
places mass would outperform $F^{\dagger}$. However, this alignment depends on
the specific $q_D$, which is unknown at analogy construction time.

This yields the central normative conclusion:

> **Principle (Robust Analogy):** Faithfulness ($\mathcal{I}(F) = 1$) is the
> unique strategy that guarantees no structural information loss regardless of
> the target distribution $q_D$. This is Gentner's Systematicity Principle
> recast as a minimax argument: a faithful functor minimizes the worst-case
> cost of unfaithfulness.

**Corollary 2c.1.** By Theorem 2a, $\kappa_F > 0$ implies
$\Delta_F < \Delta_{F^{\dagger}}$, and $\kappa_F = +\infty$ implies
$\Delta_F = -\infty$. In the support catastrophe case, the functorial prior is
not merely uninformative but **anti-informative** — it drives the learner away
from the truth.

### 4.5 Summary of §4

| Result | Statement | Interpretation |
|:-------|:----------|:---------------|
| Thm 2a | $\Delta_F = \Delta_{\max} - \varepsilon_F$ | Reduction = ceiling − imperfection |
| Thm 2b | $\Delta_F^{\text{perfect}} \geq \ln |\mathbf{D}| - H(q_C)$ | Faithful + well-learned → max reduction |
| Thm 2c(i) | $\kappa_F = +\infty$ (support violation) | False analogy is worse than ignorance |
| Thm 2c(iii) | $\kappa_F$ sign-indefinite | Unfaithfulness may help or hurt |
| Principle | $\mathcal{I}(F) = 1$ is minimax-optimal | Systematicity = robustness |

---

## §5. Gentner Revisited: Systematicity as $\mathcal{I}(F)$ Maximization

### 5.1 Gentner's Systematicity Principle (1983)

Gentner's Structure-Mapping Theory states that good analogies preferentially
map **systems of relations** (interconnected relational structures) rather than
isolated relations. This is the **Systematicity Principle**.

### 5.2 Proposition (Systematicity ≅ Faithfulness)

**Proposition 3.** Gentner's Systematicity Principle is equivalent to
maximizing $\mathcal{I}(F)$:

- **Systematic analogy** = functor with high $\mathcal{I}(F)$
  (preserves systems of relations → preserves morphisms → faithful)
- **Surface analogy** = functor with low $\mathcal{I}(F)$
  (preserves only object attributes → loses morphisms → unfaithful)

**Argument.** Gentner distinguishes:
- **Attribute mappings**: correspondences between object properties (non-structural)
- **Relational mappings**: correspondences between relations (structural)
- **Systematic mappings**: correspondences between systems of relations (deeply structural)

In categorical terms:
- Attributes ≈ properties of objects (internalized as morphisms to terminal objects)
- Relations ≈ morphisms between objects
- Systems of relations ≈ compositions of morphisms (commutative diagrams)

A functor that preserves systems of relations necessarily preserves composition,
hence preserves morphisms, hence is faithful. The converse also holds: a
faithful functor preserves all distinctive morphisms, including system-level
compositions.

Therefore: **Systematicity = Faithfulness = High $\mathcal{I}(F)$**.

**Note.** This argument establishes a conceptual correspondence. A fully formal
proof would require a precise categorical axiomatization of Gentner's SME
primitives (attribute, relation, system), which is itself an open formalization
problem. The correspondence is nonetheless robust: any reasonable
categorification of "preserves systems of relations" entails faithfulness.

---

## §6. Worked Examples

### 6.1 Bohr's Solar System → Atom Analogy

**Source C**: Solar system.
Objects: {Sun, planets}. Morphisms: gravitational attraction, orbital motion,
Kepler's laws.

**Target D**: Atom.
Objects: {nucleus, electrons}. Morphisms: Coulomb force, orbital motion,
quantized orbits.

**Functor F**: Sun ↦ nucleus, planet ↦ electron, gravity ↦ Coulomb force,
orbital mechanics ↦ orbital mechanics.

$\mathcal{I}(F)$: High but not 1. The morphism "continuous orbital adjustment"
in C maps to "quantized orbital transition" in D — this is a partial
identification (non-faithful for this morphism). The retained morphisms
(central force law, inverse-square dependence, orbital stability) provide a
rich prior for atomic physics, dramatically reducing Complexity compared to
building quantum mechanics from scratch.

**Historical validation**: Bohr's model was superseded, but it was an enormously
productive starting point. The functorial prior $F_* q_C$ gave the right
structure for most atomic phenomena, with the unfaithful morphisms precisely
identifying where D diverges from C (quantization).

### 6.2 Quantitative Toy Example

To ground the theory, consider a minimal concrete instance.

**Source $\mathbf{C}$:**
Objects $\{a, b, c\}$ with non-identity morphisms
$f: a \to b$, $g: b \to c$, $h: a \to c$ (where $h = g \circ f$),
plus the three identity morphisms. Total: 4 distinct non-identity morphisms,
$|\text{Hom}| = 7$.

**Target $\mathbf{D}$:**
Objects $\{x, y, z, w\}$ ($|\mathbf{D}| = 4$).

**Faithful embedding $F$ ($\mathcal{I}(F) = 1$):**
$a \mapsto x, b \mapsto y, c \mapsto z$. All morphisms preserved distinctly.

**Source distribution:** $q_C = (0.5, 0.3, 0.2)$.

$H(q_C) = -(0.5 \ln 0.5 + 0.3 \ln 0.3 + 0.2 \ln 0.2) \approx 1.03$ nats.

$F_* q_C = (0.5, 0.3, 0.2, 0)$ on $\{x,y,z,w\}$. Since $F$ is injective on
objects, $H(F_* q_C) = H(q_C) \approx 1.03$ nats.

**Perfect analogy** ($q_D = F_* q_C$):

$$\Delta_F^{\text{perfect}} = \ln 4 - H(q_C) \approx 1.39 - 1.03 = 0.36 \text{ nats}$$

This equals $\ln 4 - \ln 4 + (\ln 4 - H(q_C)) = 0.36$ nats of Complexity
reduction. The analogy eliminates 26% of the maximal uncertainty
($\Delta_F / \ln 4 \approx 0.26$).

**Unfaithful variant $F'$:** Merge $f$ and $g$ into a single morphism
$\phi$ ($\mathcal{I}(F') = 6/7 \approx 0.86$). Now $F'$ loses the
distinction between "$a$-to-$b$" and "$b$-to-$c$" transitions. The structural
information loss $\kappa_{F'}$ depends on $q_D$: if the target domain treats
these transitions identically, $\kappa_{F'} < 0$ (accidental benefit); if not,
$\kappa_{F'} > 0$ (false analogy risk).

### 6.3 Raven's Progressive Matrices

Raven's test measures the ability to find F: Row → Col such that F preserves
the pattern-generating rules. This is precisely $c_F$ (the cost of identifying
the functor). High scores ↔ low $c_F$ ↔ efficient analogical reasoning.

The VFE interpretation: solving each matrix item requires choosing a prior over
possible completions. Analogical reasoners use $F_* q_{\text{row}}$ (transfer
the row pattern) as a prior, reducing Complexity. Non-analogical reasoners use
$p_0$ (enumerate all possibilities).

---

## §7. Discussion

### 7.1 Relation to Smithe's Theorem 46

Smithe, Tull & Kleiner (2023) prove that free energy is additive under tensor
product composition of models:

$$F(M_1 \otimes M_2, q_1 \otimes q_2, o_1 \otimes o_2) = F(M_1, q_1, o_1) + F(M_2, q_2, o_2)$$

This result concerns **decomposition** of independent subsystems, not
**transfer** between domains. Theorem 1 of the present paper addresses a
different question: not "can you decompose a composite model?" but "can you
transfer structure to reduce the cost of a new model?"

| | Smithe Thm 46 | This paper (Thm 1) |
|:--|:-------------|:-------------------|
| Operation | Tensor product $\otimes$ | Push-forward $F_*$ |
| Relation | Independence (no interaction) | Analogy (structural similarity) |
| Result | $F(M_1 \otimes M_2) = F(M_1) + F(M_2)$ | $\Delta_F = \Delta_{\max} - \varepsilon_F \geq 0$ |
| Cognitive correlate | Multi-task decomposition | Transfer learning |

Both rely on Smithe's category-theoretic formulation of FEP, but address
orthogonal aspects. This paper's contribution is that structure transfer via
functors, not model decomposition, underpins analogical reasoning.

### 7.2 Is $\Delta_F \geq 0$ trivial?

A potential objection: "Of course a better prior gives lower Complexity — this
is just Gibbs' inequality." We address this directly.

**What is trivial**: Given $q_D$ and any $p$ with
$D_{KL}[q_D \| p] < D_{KL}[q_D \| p_0]$, we have $\Delta > 0$. This is
indeed a consequence of the definition of KL divergence.

**What is not trivial**:

1. **The construction of $F_* q_C$.** The push-forward of a source model
   through a faithful functor is a specific, constructive mechanism for
   producing a good prior. Not any distribution works — the prior must be
   *derived from existing knowledge via structure-preserving maps*.

2. **The conditions for success (Theorem 2c).** The sign indeterminacy of
   $\kappa_F$ reveals that unfaithful structure transfer can either help or
   hurt, and that faithfulness is minimax-optimal. This is not derivable from
   generic information theory.

3. **The connection to Gentner (Proposition 3).** The re-formalization of
   Systematicity as $\mathcal{I}(F)$ maximization provides a new bridge
   between cognitive science and information theory that has not been
   previously established.

4. **The quantitative decomposition (Theorem 2a/2b).** The explicit formula
   $\Delta_F = \Delta_{\max} - \varepsilon_F$ and the bound
   $\Delta_F^{\text{perfect}} \geq \ln |\mathbf{D}| - H(q_C)$ connect
   algebraic properties of functors to information-theoretic quantities.

### 7.3 The Minimax Interpretation

Theorem 2c(iii) shows that $\kappa_F$ is sign-indefinite: an unfaithful functor
can accidentally provide a better prior than a faithful one. This result,
initially surprising, has a natural interpretation.

An unfaithful functor that "luckily" merges states in alignment with $q_D$ is
engaged in a form of **overfitting** — exploiting specific properties of $q_D$
that are unknown at analogy construction time. The Robust Analogy Principle
(§4.4) states that faithfulness is the unique strategy guaranteeing no
structural information loss regardless of $q_D$.

This is precisely a **minimax** criterion:

$$\mathcal{I}(F) = 1 \iff \min_{q_D} \kappa_F(q_D) = 0$$

The forward direction ($\Rightarrow$) is immediate: when $F$ is faithful,
$F_* q_C = F^\dagger_* q_C$ for any $q_D$, so $\kappa_F = 0$ identically.

The reverse direction ($\Leftarrow$) follows from Theorem 2c(iii). If $F$ is
not faithful, there exist morphisms $f \neq g$ with $F(f) = F(g)$. By
choosing $q_D$ concentrated on objects connected by $f$ or $g$ (but not both),
we obtain $\kappa_F(q_D) < 0$ for one choice and $\kappa_F(q_D) > 0$ for
another (sign indeterminacy). In particular, $\min_{q_D} \kappa_F < 0$, which
contradicts $\min_{q_D} \kappa_F = 0$.

Thus: a faithful functor achieves $\kappa_F = 0$ for any $q_D$ (assuming
support compatibility), while unfaithful functors necessarily have
$\kappa_F < 0$ for some $q_D$ and $\kappa_F = +\infty$ for others (Support
Catastrophe).

This minimax structure connects Gentner's Systematicity Principle to
decision-theoretic robustness: **systematic analogies are those that work
regardless of the specific target domain realization.**

---

## §8. Limitations and Future Directions

### 8.1 Limitations

1. **The functor must exist.** All results assume a faithful functor
   $F: \mathbf{C} \to \mathbf{D}$ exists. Finding such a functor — the $c_F$
   cost — is itself a cognitive challenge not addressed here. The present
   theory characterizes the *value* of analogy, not the *cost* of finding one.

2. **Finite categories.** The IPI (Definition 2) and the Complexity bounds
   require finite hom-sets. Extensions to enriched, topological, or
   $\infty$-categories require measure-theoretic and homotopical machinery.

3. **Push-forward fidelity.** The push-forward $F_* q_C$ is defined as a
   direct transfer with no adaptation. In practice, the transferred prior is
   refined through further learning (posterior updating). Our bounds apply to
   the *initial* Complexity reduction, before any refinement.

4. **State space vs. morphism space.** Our analysis operates on distributions
   over states (objects of $\mathbf{D}$), while the IPI is defined over
   morphisms. The connection between morphism-level faithfulness and
   state-level distributional quality requires the additional assumption that
   morphisms encode predictive structure relevant to the learning task.

5. **$\kappa_F$ is not bounded by $\mathcal{I}(F)$.** We initially sought a
   direct bound $\Delta_F \geq f(\mathcal{I}(F))$ but found that the
   relationship between IPI and Complexity reduction is mediated by $q_D$,
   which is unknown. The minimax result (§7.3) is the correct replacement.

### 8.2 Future Directions

1. **$c_F$ estimation and computational complexity.** What determines the cost
   of finding a good functor? Structure-mapping engine (SME) runtime is
   polynomial in the number of predicates (Falkenhainer et al., 1989). Can we
   connect $c_F$ to the combinatorial structure of the source and target
   categories?

2. **Natural transformations as analogy refinement.** If $F, G: \mathbf{C} \to
   \mathbf{D}$ are two functors (two analogies), a natural transformation
   $\eta: F \Rightarrow G$ represents a systematic refinement. The question:
   does $\Delta_G \geq \Delta_F$ when $\eta$ is "information-enriching"?

3. **Adjunctions and optimal analogy.** If $F \dashv G$ (F left adjoint to G),
   the adjunction provides a canonical factorization $\text{Id} \to G \circ F$.
   Does this represent an "optimal" analogy in some VFE sense? The connection
   to Helmholtz decomposition (Bayesian inference as adjunction) is suggestive.

4. **Quantitative $\kappa_F$ bounds.** While $\kappa_F$ is sign-indefinite in
   general, specific assumptions on the distributional structure (e.g., product
   categories, exponential families) may yield tighter bounds relating
   $\mathcal{I}(F)$ to expected $\kappa_F$.

5. **Empirical validation via Raven's matrices.** The theory predicts that
   matrix difficulty correlates with $\mathcal{I}(F)$ of the pattern-generating
   functor and $H(q_C)$ of the source pattern. This is empirically testable.

---

## References

- Cover, T. M. & Thomas, J. A. (2006). *Elements of Information Theory*, 2nd ed. Wiley.
- Falkenhainer, B., Forbus, K. D., & Gentner, D. (1989). The structure-mapping engine: Algorithm and examples. *Artificial Intelligence*, 41(1), 1-63.
- Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11(2), 127-138.
- Gentner, D. (1983). Structure-mapping: A theoretical framework for analogy. *Cognitive Science*, 7(2), 155-170.
- Halford, G. S., Wilson, W. H., & Phillips, S. (1998). Processing capacity defined by relational complexity. *Behavioral and Brain Sciences*, 21(6), 803-831.
- Holyoak, K. J. & Thagard, P. (1995). *Mental Leaps: Analogy in Creative Thought*. MIT Press.
- Mac Lane, S. (1998). *Categories for the Working Mathematician*, 2nd ed. Springer.
- Ott, M. (2025). Formal analogy as a functor. *Erkenntnis*.
- Parr, T., Pezzulo, G., & Friston, K. J. (2022). *Active Inference: The Free Energy Principle in Mind, Brain, and Behavior*. MIT Press.
- Phillips, S. (2022). A category theory perspective on analogy. *Proceedings of CogSci 2022*.
- Raven, J. C. (1938). Progressive Matrices: A perceptual test of intelligence. *British Journal of Medical Psychology*, 19(1), 137-150.
- Smithe, T. S. C. (2023). *Mathematical Foundations for a Compositional Account of the Bayesian Brain*. DPhil thesis, University of Oxford.
- Smithe, T. S. C., Tull, S., & Kleiner, J. (2023). Active Inference in String Diagrams. *arXiv:2308.00861*.
