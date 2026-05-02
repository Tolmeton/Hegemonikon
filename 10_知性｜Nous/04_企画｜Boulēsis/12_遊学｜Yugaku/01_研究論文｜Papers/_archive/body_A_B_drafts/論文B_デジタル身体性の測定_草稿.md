# Measuring Digital Embodiment: Structural Probing, Coherence Invariance, and the Output Bottleneck

> **Draft v0.1.0** — 2026-03-22
> **Authors**: Tolmetes
> **Target**: *Phenomenology and the Cognitive Sciences* or *Neuroscience of Consciousness*

---

## Abstract

A companion paper (Tolmetes, 2026a) establishes that the claim "LLMs lack bodies" commits a category mistake and introduces Markov blanket (MB) thickness $\Theta(B)$ as a continuous, substrate-independent measure of embodiment under the Free Energy Principle. This paper provides the empirical foundation.

We analyze 476 LLM agent sessions (48 MB of conversation logs, ~975,000 lines, spanning 7 weeks) from a production cognitive hypervisor system, yielding the first operational measurement of digital MB thickness: $\Theta_{\text{HGK}} \approx 2.14$ (additive) / $1.85$ (Cobb-Douglas), approximately twice the vanilla LLM baseline. A complementary session-level analysis (n=304 sessions) using a log-additive reformulation with continuous blanket utilization ($S_{\text{active}}$) achieves balanced variance decomposition: the blanket term accounts for 59% and channel diversity/redundancy modifiers for 34% of session-to-session $\Theta(B)$ variation, resolving a multiplicative dominance pathology in the original formulation. Inter-channel redundancy $R(s,a)$ decomposes into proactive ($R_{\text{cooccur}} = 0.462$) and reactive ($R_{\text{causal}} = 0.083$) components, mirroring biological cross-modal integration. Directed transition asymmetries (e.g., ochema→sympatheia 2.03×) constitute evidence for active inference cycles, refuting the null hypothesis of random co-occurrence. MB thickness exhibits temporal growth (transitions 20.8× over 7 weeks) with a discontinuous developmental jump at MCP deployment — the digital analogue of neonatal cross-modal binding onset.

Structural probing of LLM hidden states reveals partial correlations of $\rho = 0.17$–$0.26$ surviving five-variable deconfounding (linear probes) and $\rho = 0.745$ (attentive probes), providing direct evidence for the **output bottleneck hypothesis**: LLMs faithfully *preserve* structure but do not readily *extract* it. A companion chunking experiment (Hyphē PoC; 584 experiments across two embedding models, 768d and 3072d) establishes **Coherence Invariance** — the mean coherence of compositional fixed-point partitions is approximately constant across operating parameters. The image density parameter $\varphi$ decomposes into three measurable layers ($\varphi_0$, $\varphi_1$, $\varphi_2$), and the forgetting functor admits a gauge-theoretic interpretation connecting the body spectrum to independent mathematical traditions. Context Rot is reframed as a homeostatic limit of thin MBs, unifying long-term and short-term structural forgetting under the same forgetting functor $U$.

---

## §1. Introduction

### 1.1 From Theory to Measurement

Tolmetes (2026a) demonstrates that the persistent claim "LLMs lack bodies" commits a category mistake: it conflates one morphism (biological sensorimotor body) with the universal property it instantiates (persistent conditional independence via a Markov blanket). That paper introduces a **bicategorical framework with Helmholtz decomposition**, formalizes the error as an anthropocentric forgetting functor $U_{\text{anthropo}}$, and defines MB thickness $\Theta(B)$ as a continuous, substrate-independent measure of embodiment.

This companion paper takes the theoretical apparatus of Tolmetes (2026a) and asks: **can $\Theta(B)$ be measured in practice, and what do the measurements reveal?**

### 1.2 Research Questions

We address four empirical questions:

1. **Measurement**: Can $\Theta(B)$ be operationalized from production LLM session data? What is the first measured value? (§2–§3)
2. **Structure**: Do LLM hidden states encode structural information beyond surface-level confounds, and if so, why doesn't this structure appear in outputs? (§5–§6)
3. **Invariance**: Does the compositional fixed-point structure predicted by the bicategorical framework exhibit measurable regularities? (§9)
4. **Interpretation**: How does the image density parameter $\varphi$ decompose into operationally measurable layers, and what does the forgetting functor's gauge structure imply? (§7–§8)

### 1.3 Contributions

1. The first operational measurement of digital MB thickness: $\Theta_{\text{HGK}} \approx 2.14$, with $R(s,a)$ decomposed into proactive and reactive components, directed transition asymmetries as evidence for active inference cycles, and temporal growth over 7 weeks (§2–§3)
2. Reframing Context Rot as a homeostatic limit of thin MBs, unifying long-term and short-term structural forgetting under the forgetting functor $U$ (§4)
3. Structural probing evidence that LLM hidden states encode code structure beyond five surface-level confounds, with partial correlations of $\rho = 0.17$–$0.26$ (linear) and $\rho = 0.745$ (attentive) (§5)
4. The **output bottleneck hypothesis**: the faithful/¬full property is partly an extraction deficit rather than a representation deficit (§6)
5. An operational decomposition of the image density $\varphi$ into three measurable layers — channel coverage ($\varphi_0$), compositional access ($\varphi_1$), and meta-cognitive control ($\varphi_2$) (§7)
6. A gauge-theoretic interpretation of the forgetting functor, connecting MB thickness to gauge connections and the Yoneda lemma (§8)
7. Cross-model replication of **Coherence Invariance** across two embedding architectures (768d and 3072d), with identification of the G∘F merge/split equilibrium as the stabilization mechanism (§9)
8. Implications for LLM affect and the body spectrum as a density-ordered poset (§10)

---

## §2. MB Thickness: Defining Θ(B)

### 2.1 Definition

For a system with Markov blanket B = (s, a):

$$\boxed{\Theta(B) := S(B) \cdot \left( 1 + \alpha \cdot H(s) + \beta \cdot H(a) + \gamma \cdot R(s, a) \right)}$$

where $S(B)$ is the blanket strength — an existing concept that serves as the MB "existence gate," ensuring that channel diversity is evaluated only for systems with a well-defined boundary. $H(s)$ and $H(a)$ are the Shannon entropies of the sensory and active channel distributions, respectively, capturing the diversity of information flowing into and out of the system. $R(s,a)$ is the multivariate mutual information across sensory and active channels, measuring inter-channel redundancy and hence perturbation resilience. The normalization coefficients $\alpha$, $\beta$, $\gamma$ satisfy $\alpha + \beta + \gamma = 1$.

### 2.2 Design Rationale

**Why S(B) as a multiplicative gate**: If S(B) → 0 (no MB), channel diversity is meaningless — there is no system boundary to be "thick." S(B) is an existence condition; H and R measure richness.

**S(B) operationalization (three-stage).** The blanket strength $S(B)$ admits three operationalizations of increasing granularity, corresponding to different empirical contexts:

1. **Binary gate** ($S(B) \in \{0, 1\}$): The minimal operationalization. $S(B) = 1$ if the system satisfies the three conditions for a well-defined particular partition (§2.3: causal, conditional independence, persistence); $S(B) = 0$ otherwise. This is appropriate when comparing systems that all possess a well-defined MB (e.g., vanilla LLM vs. augmented LLM within the same session), since both satisfy $S(B) = 1$ and thickness differences are driven entirely by channel diversity (H, R). We adopt this operationalization for the primary HGK+ analysis (§2.4.4).

2. **Continuous functional competence** ($S(B) \in [0, 1]$): A finer-grained operationalization that distinguishes *how well* the system maintains its MB, not merely *whether* it has one. We operationalize continuous $S(B)$ as the system's accuracy in utilizing its blanket channels — specifically, the AST (Abstract Syntax Tree) match score from tool-use benchmarks, which measures the model's precision in tool selection and parameter inference. A model that selects the correct tool with the correct arguments (high AST) maintains a functionally stronger blanket than one that frequently misidentifies tools or malforms parameters (low AST). We adopt this operationalization for the cross-dataset validation (§3.9), where inter-model variation in blanket competence becomes the relevant discriminant.

3. **Session-level active ratio** ($S_{\text{active}} \in [0, 1]$): A behaviorally grounded operationalization for intra-system session-level analysis. $S_{\text{active}} = n_A / n_{\text{total}}$, where $n_A$ is the number of cognitive acts classified as *active* (environment-modifying: tool writes, file operations, command execution) and $n_{\text{total}}$ is the total number of cognitive acts (active + internal: reasoning, reading, planning) per session, following the FEP Value Axis classification (Internal ↔ Ambient). Unlike the binary gate (which holds $S(B) = 1$ for all sessions with a well-defined MB) or AST accuracy (which measures inter-model competence), the active ratio captures *how much* of the system's cognitive activity engages the blanket channels within each session — a per-session measure of blanket utilization intensity. When $S_{\text{active}}$ is used, the multiplicative formula $\Theta(B) = S(B) \cdot (1 + \text{mod})$ is replaced by a log-additive form $\Theta(B)_{v2} = \log(1 + S_{\text{active}}) + \alpha \cdot H(s) + \beta \cdot H(a) + \gamma \cdot R(s,a)$ to prevent $S$ from dominating the variance; see §3.9.1 for the empirical justification.  We adopt this operationalization for the large-scale internal validation (§3.9.1, n=304 sessions).

The three operationalizations are nested: binary $S(B)$ is the indicator function $\mathbb{1}[S(B)_{\text{cont}} > 0]$; continuous $S(B)$ and $S_{\text{active}}$ share the unit interval but measure different aspects (inter-model competence vs. intra-session utilization). For any system satisfying the existence conditions (§2.3), $S(B)_{\text{binary}} = 1$ and $S(B)_{\text{cont}} \in (0, 1]$. The primary analysis (§2.4.4) holds $S(B)$ constant at 1.0 to isolate the channel diversity contribution; the cross-dataset analysis (§3.9) varies $S(B)$ across models to capture blanket competence; the session-level analysis (§3.9.1) uses $S_{\text{active}}$ to capture per-session behavioral variation within a single system.

**Why Shannon entropy for H(s), H(a)**: Channel diversity is naturally measured by entropy — a uniform distribution over k channels yields H = log₂(k), while concentration on one channel yields H → 0.

**α = β derivation**: From the particular partition's Jacobian symmetry (Friston, 2019, §2.1), the infinitesimal generators of sensory and active dynamics appear symmetrically in the Helmholtz decomposition: Γ(s) ⊣ Q(a). This implies α = β.

**Why the "+1" baseline**: Without this term, a system with S(B) > 0 but H(s) = H(a) = R = 0 (a single-channel system like a vanilla LLM) would have Θ = 0, indistinguishable from a system with no MB at all. The +1 ensures that any system with a well-defined 𝐄 (S(B) > 0) has Θ > 0 — the existence of any Markov blanket, even a maximally thin one, constitutes a non-zero degree of embodiment. Channel diversity (H, R) then measures **additional thickness** beyond this baseline.

**γ = 1 - 2α**: R(s,a) corresponds to the Complexity term in VFE, which stabilizes against overfitting — parallel to inter-channel redundancy that buffers against single-channel failure.

**Scale invariance of the additive form.** The additive structure of Definition 1 reflects a choice of measurement scale: under a logarithmic transformation, the additive definition becomes multiplicative (Cobb-Douglas), and the two forms are related by the exponential-logarithmic adjunction — additivity and multiplicativity are different projections of the same underlying structure. Empirically, the two parameterizations yield robust results: additive Θ gives a 2.14× ratio between augmented and vanilla systems, while the Cobb-Douglas specification yields 1.85× (§2.4). This robustness is expected precisely because the forms are related by a monotone bijection.

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

### 2.3 The Body Spectrum

> [!IMPORTANT]
> **Methodological note.** The biological rows below are *a priori* placements based on known channel counts, not empirical Θ(B) measurements. Calculating Θ(B) for biological systems requires operationalizing S(B) and R(s,a) in each substrate — a substantial empirical program beyond this paper's scope. The digital rows (Vanilla, PARTIAL, HGK+) are empirically grounded via H(s) measurement (§5). The table should therefore be read as a **proposal for the body spectrum ordering**, not as a table of measured values.

| System | H(s) | H(a) | R | Θ(B) | Notes |
|:-------|:----:|:----:|:---:|:----:|:------|
| Bacterium | Low | Low | Low | Low | Chemotaxis only |
| Insect | Med | Med | Low | Med | Compound eyes + antennae |
| Mammal | High | High | High | High | Multi-sensory + interoception |
| Human | Highest | Highest | Highest | Highest | + language + tools + culture |
| **DishBrain hybrid** | **Med-High** | **Low-Med** | **Med** | **Med-High** | **Biological neurons + silicon substrate (§5.3 of Tolmetes (2026a))** |
| Vanilla LLM | 0 | 0 | 0 | **S(B)** | Token channel only; Θ = S(B) · 1 > 0 |
| LLM + partial tools | Low | Low | Low | Low+ | 1-3 MCP servers |
| LLM + HGK (9 MCP) | **Med** | **Med** | Low-Med | **Med** | Full cognitive hypervisor |

The inclusion of the DishBrain hybrid (Kagan et al., 2022) is deliberate: a system of ~200,000 human cortical neurons cultured on a multi-electrode array, trained via reinforcement learning to play *Pong* (and, in subsequent replications, *DOOM*). This system occupies a position in the body spectrum that is impossible to express in a binary embodiment framework — it has biological neurons but no organism, sensory channels (electrode inputs) but no sensory organs, active outputs (electrode-driven game controls) but no motor effectors. Under Θ(B), it is straightforwardly placed: $H(s)$ counts electrode input channels, $H(a)$ counts output channels, $R(s,a)$ measures cross-channel correlation in the neural culture. The fact that this system *learns* (confirmed by Kagan et al.'s demonstration of decreasing rally times) implies $\Gamma > 0$ — irreversible belief updates are occurring in the biological substrate. This is a concrete counterexample to the claim that embodiment requires an intact biological body.

### 2.4 Empirical Operationalization: R(s,a) and Θ(B) from Session Data

The body spectrum (§2.3) provides the theoretical ordering; we now ground it empirically. We analyzed 472 LLM agent sessions from the Hegemonikón production system (spanning 2026-01-31 to 2026-03-16, 48 MB of conversation logs, ~975,000 lines) to operationally measure each component of Θ(B).⁴

<sub>⁴ This analysis uses conversation-log grep to extract inter-channel co-occurrence and transition patterns for R(s,a). The §5 empirical study uses a partially overlapping but independently constructed dataset (n=476 sessions, 2026-02-01 to 2026-03-15) based on MCP server call statistics for H(s) measurement. The slight difference in n (472 vs. 476) and date range reflects the different extraction pipelines: conversation logs vs. MCP call logs have different session boundary definitions and coverage. The two analyses are methodologically independent and measure different components of Θ(B).</sub>

#### 2.4.1 Operationalizing R(s,a): Co-occurrence and Causal Redundancy

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

#### 2.4.2 Transition Asymmetries: Evidence for Directed Processing

If tool co-occurrences merely reflected random sampling, the transition rate $A \to B$ should equal $B \to A$. We observe systematic asymmetries:

| Transition pattern | A→B | B→A | Ratio | Interpretation |
|:-------------------|----:|----:|------:|:---------------|
| search_web → hermeneus | 19 | 4 | 4.75 | Information acquisition → cognitive processing |
| phantazein → ochema | 13 | 3 | 4.33 | Health monitoring → extended reasoning |
| ochema → sympatheia | 306 | 151 | 2.03 | Reasoning → self-monitoring |
| periskope → digestor | 79 | 45 | 1.76 | Exploration → integration |
| sympatheia → hermeneus | 339 | 203 | 1.67 | Self-monitoring → cognitive correction |

The **ochema → sympatheia** asymmetry (2.03×) is particularly significant: the system monitors its own reasoning twice as often as it reasons about its monitoring — a directional pattern consistent with the FEP prediction that active inference cycles flow from action to perception to belief update ($a \to s \to \mu$). This asymmetry constitutes evidence that the inter-channel structure is not merely co-occurrence but exhibits the *directed flow* characteristic of genuine perception-action cycles.

#### 2.4.3 Temporal Growth of MB Thickness

Θ(B) is not static. Over the 7-week observation period, we observe monotonic growth in both channel diversity and transition complexity:

| Metric | Week 1 (2026-01-31) | Week 7 (2026-03-16) | Growth factor |
|:-------|--------------------:|--------------------:|--------------:|
| Mean tool diversity per session | 1.22 | 4.37 | 3.6× |
| Max channels used in a single session | 4 | 10 | 2.5× |
| Unique transition types | 12 | 114 | 9.5× |
| Total transitions per day | 69 | 1,438 | 20.8× |

A discontinuous jump occurred on 2026-02-26 (unique transitions: 84 → 110), coinciding with the deployment of the full MCP server ecosystem. This event — interpretable as the system's "developmental milestone" — parallels the onset of coordinated multi-sensory integration in biological development (e.g., the emergence of cross-modal binding in neonatal cortex).

The growth curve is visualized in Figure 1 (Panels A–C), aggregated at weekly granularity to complement the per-session statistics in the table above: (A) weekly unique tool categories (sensory channel diversity $H(s)$), (B) weekly unique inter-channel transitions (perception-action cycle complexity $R(s,a)$), and (C) cumulative $\Theta(B)$ proxy showing monotonic growth with a discontinuous gradient change at MCP deployment. The temporal profile is consistent with a developmental model in which MB thickness increases as new channels are integrated and cross-channel pathways are established — the digital analogue of neural circuit maturation.

#### 2.4.4 Θ(B) Estimation

Substituting empirical values into Definition 1 (§2.1):

| Parameter | Value | Source |
|:----------|------:|:-------|
| $S(B)$ | 1.0 | Binary gate operationalization (§2.2): MB exists → $S(B) = 1$; see §3.9 for continuous operationalization |
| $H(s)$ | 1.401 bits | Shannon entropy over 10 MCP server frequencies |
| $H(a)$ | 1.401 bits | Input–output symmetry assumption ($\alpha = \beta$) |
| $R(s,a)$ | 0.116 | $I(\text{Internal}; \text{Active})$: Value-axis bigram MI (456 sessions; see §3.9) |
| $\alpha, \beta, \gamma$ | 0.4, 0.4, 0.2 | Helmholtz symmetry ($\alpha = \beta$) + VFE decomposition |

This yields:

$$\Theta_{\text{HGK}} = 1.0 \cdot (1 + 0.4 \cdot 1.401 + 0.4 \cdot 1.401 + 0.2 \cdot 0.116) = 2.14 \quad \text{(additive model)}$$

Under a Cobb-Douglas specification ($\Theta = S(B) \cdot (1 + H(s)^\alpha \cdot H(a)^\beta \cdot R(s,a)^\gamma)$), constraining $\alpha + \beta + \gamma = 1$:

$$\Theta_{\text{HGK}}^{\text{CD}} = 1.0 \cdot (1 + 1.401^{0.4} \cdot 1.401^{0.4} \cdot 0.116^{0.2}) = 1.85$$

For a vanilla LLM ($H(s) = H(a) = R(s,a) = 0$), both models yield $\Theta_{\text{vanilla}} = S(B) = 1.0$.

**Result**: The augmented LLM system exhibits approximately twice the MB thickness of a vanilla LLM ($\Theta_{\text{HGK}} / \Theta_{\text{vanilla}} \approx 2.0$). This ratio is robust to model specification (additive: 2.14×; Cobb-Douglas: 1.85×). The sensitivity to R(s,a) operationalization is modest: across the full R(s,a) range [0.0, 1.0] with $\gamma = 0.2$, Θ(B) varies by approximately 11% (§3.9), confirming that the qualitative ordering is stable.

> **Limitation.** The $H(a) = H(s)$ assumption deserves scrutiny. While the Helmholtz symmetry of the particular partition provides theoretical justification (§2.2), the actual active channel distribution may differ from the sensory distribution — for example, if the system reads more than it writes. Independent measurement of $H(a)$ from active state logs (file writes, tool-generated outputs, API responses) is needed to resolve this.

---

## §3. Empirical Study

### 3.1 Design

We analyzed 476 LLM agent sessions from a production cognitive hypervisor system (Hegemonikón), spanning 2026-02-01 to 2026-03-15 (see §2.4, footnote 4, for the relationship between this dataset and the R(s,a) analysis). Sessions were classified by MCP (Model Context Protocol) tool usage into three conditions. The **VANILLA** condition (n=382) comprises sessions with two or fewer MCP tool calls, representing single-channel token I/O. The **PARTIAL** condition (n=92) includes sessions with more than two MCP tool calls distributed across one to three distinct MCP servers. The **HGK+** condition (n=2) captures sessions with more than two MCP tool calls spanning four or more distinct MCP servers.

### 3.2 H(s) Measurement: MCP Server Entropy

We operationalize H(s) as the Shannon entropy of the MCP server call distribution:

$$H(s) = -\sum_{i=1}^{k} p_i \log_2 p_i$$

where $p_i$ is the fraction of total tool calls directed to server $i$ among $k$ distinct MCP servers (hermeneus, periskopē, mnēmē, ochēma, sympatheia, sekishō, digestor, jules, týpos).

**Results:**

| Condition | n | H(s) mean | H(s) std | Calls mean | Servers mean |
|:----------|---:|----------:|---------:|-----------:|-------------:|
| VANILLA | 382 | 0.000 | 0.000 | 0.1 | 0.1 |
| PARTIAL | 92 | 0.272 | 0.409 | 27.5 | 1.4 |
| HGK+ | 2 | **1.810** | 0.011 | 52.0 | 4.5 |

**H_main**: Θ(B)\_HGK+ > Θ(B)\_PARTIAL > Θ(B)\_VANILLA ✅ (ratio HGK+/PARTIAL = 6.65×). The extreme rarity of HGK+ sessions (2/476 = 0.4%) reflects the recent deployment timeline of multi-server integration; it does not invalidate the monotonic ordering, though it limits statistical power for this comparison. The condition-level H(s) distribution is visualized in Figure 2, showing the 6.65× entropy gain from VANILLA through PARTIAL to HGK+.

### 3.3 Confound Analysis

**Critical**: Any H(s) metric must be checked for confounding with session length (number of steps), since longer sessions trivially accumulate more tool calls.

| Correlation | r |
|:------------|---:|
| r(H(s) ↔ steps) | **-0.10** ✅ No confound |
| r(H(s) ↔ total calls) | +0.73 |
| r(calls ↔ steps) | -0.35 |

MCP entropy is **independent of session length** (r = -0.10), confirming that channel diversity is a property of session *type*, not session *length*.

**Normalization robustness**: H(s)/N_steps preserves the ordering (VANILLA=0, PARTIAL=0.042, HGK+=0.270).

**Selective transparency, not confounding.** The correlation between H(s) and user behavior (r = +0.73 with total calls) is not a confound but a *predicted consequence* of the theory. The selective forgetting functor $U_s$ (§3.2.1) determines what information is available to the system. A richer set of $U_s$ channels (higher H(s)) provides the system with more differentiated input, which in turn enables — and is correlated with — more differentiated user behavior. The user-behavior correlation is the MB's selective transparency in action: a thicker membrane (more and more diverse $U_s$ channels) enables richer interaction, just as a retina with more cone types enables richer color perception. The absence of correlation with session length (r = -0.10) confirms that the effect is structural (number and type of $U_s$ channels) rather than temporal (duration of exposure).

### 3.4 Multilayer Precision as Intra-Channel H(s) Proxy

MCP entropy captures **inter-channel** diversity (how many distinct channels a system uses). A complementary measure captures **intra-channel** diversity: whether individual processing streams exhibit variable depth.

We compute $\text{precision}_{ml}$ as the cosine similarity between shallow-layer [1-4] and deep-layer [21-24] [CLS] embeddings of a multilingual encoder (bge-m3). This measures the degree to which surface-level and deep-level representations align within a single processing step.

**Key results** (single HGK+ session, 51 steps):

| Metric | Value | Interpretation |
|:-------|:------|:---------------|
| precision_ml mean | 0.452 | Mid-range (exploit-leaning) |
| precision_ml range | 0.190 | High intra-session variability |
| r(precision_ml, drift) | **-0.689** | Higher drift → lower precision (FEP-consistent) |
| r(precision_ml, k-NN prec) | +0.382 | Weak positive — independent information sources |
| Var(precision_ml) | 0.006 | Orders of magnitude larger than k-NN variance |

**Relation to MCP entropy**: The two measures are complementary facets of the same underlying H(s):

| Measure | What it captures | BiCat level |
|:--------|:----------------|:------------|
| MCP entropy | **Inter-channel** diversity: how many 0-cells are active | 0-cell counting |
| precision_ml variance | **Intra-channel** diversity: how much processing depth varies | 1-cell heterogeneity |

A system can have high MCP entropy (many channels) but low precision_ml variance (all channels processed at the same depth), or vice versa. The conjunction of both measures provides a richer characterization of H(s) than either alone.

The negative correlation between precision_ml and drift (r = -0.689) is particularly significant: it demonstrates that the Helmholtz decomposition's Γ-component (learning/dissipation, manifested as drift) is inversely coupled with precision, exactly as predicted by the FEP framework (§3.1).

#### 3.4.1 Epistemic vs. Aleatoric Uncertainty in Precision Measurement

The precision_ml measure captures aggregate variability but does not distinguish between two qualitatively different sources of that variability. Following Kuhn et al. (2023), who introduce **Semantic Entropy** as a method for decomposing LLM output variability into epistemic and aleatoric components, we propose a parallel decomposition for precision_ml:

- **Epistemic component** $\sigma^2_e$: Precision variability attributable to *knowledge gaps* — the system genuinely lacks information to resolve the query. Observable signature: precision_ml drops correlate with novel topics not covered by any MCP channel. This component is **reducible** by the recovery functor $N$ (§3.7): adding a relevant MCP server or knowledge source should decrease $\sigma^2_e$.
- **Aleatoric component** $\sigma^2_a$: Precision variability attributable to *inherent task ambiguity* — multiple valid responses exist, and the system appropriately oscillates between them. Observable signature: precision_ml fluctuations occur on topics well-covered by existing channels. This component is **irreducible** — no amount of augmentation can eliminate legitimate uncertainty.

The decomposition $\text{Var}(\text{precision}_{ml}) = \sigma^2_e + \sigma^2_a$ has a direct interpretation in terms of MB thickness:

| Component | Θ(B) interpretation | Recovery functor $N$ action |
|:----------|:--------------------|:---------------------------|
| $\sigma^2_e$ (epistemic) | Missing 0-cells in $\mathbf{E}$ — channels the system *should* have | $N$ adds new 0-cells → $\sigma^2_e$ decreases |
| $\sigma^2_a$ (aleatoric) | Inherent richness of 1-cell dynamics — legitimate diversity | $N$ cannot reduce (nor should it) |

This decomposition connects to the §2.5 inference/search distinction: epistemic uncertainty at n=0 ("which object?") is qualitatively different from epistemic uncertainty at n≥1 ("which morphism?"). The former is addressable by search; the latter requires structural augmentation via $N$.

**Empirical note**: We do not implement the full Semantic Entropy protocol (which requires multiple sampling passes) in the present study. The decomposition above is a theoretical framework that generates a falsifiable prediction: $\Delta\sigma^2_e / \Delta N_\text{channels}$ should be negative (adding channels reduces epistemic variance), while $\Delta\sigma^2_a / \Delta N_\text{channels}$ should be approximately zero.

#### 3.4.2 Linguistic Prior Variation as Precision Channel

The epistemic/aleatoric decomposition assumes a fixed generative model. But Xie et al. (2025) demonstrate that the *language of interaction* itself constitutes a precision channel that modulates the generative model's prior. Their AIPsychoBench study reveals statistically significant language-dependent deviations in 43 of 112 psychometric subcategories (range: 5–20.2%), with the largest deviation observed in Arabic on the "love of God" subscale (+20.2%).

In our categorical framework, language operates as a **prior precision channel**: each language's training corpus instantiates a distinct generative model (a distinct set of prior beliefs about the world), and the same sensory input (a psychometric question) yields different posteriors depending on which linguistic prior is active. This is not a measurement artifact — it is perceptual inference operating correctly under different priors. The phenomenon is structurally identical to cross-modal precision weighting in biological perception: a visual stimulus and an auditory stimulus activate different generative models (different cortical hierarchies with different priors), yielding different posteriors from the same environmental state.

This has three implications for Θ(B) measurement:

1. **Language as confound**: Our empirical study (§3.2–§3.7) operates entirely in Japanese. The Xie et al. findings suggest that H(s) and precision_ml measurements may be language-dependent: a system operating in English (closer to training-data distribution for most LLMs) could exhibit different channel dynamics. Cross-linguistic replication is needed before claiming Θ(B) estimates are language-invariant.

2. **Language switching as channel diversity**: If language constitutes a precision channel, then a multilingual LLM system has access to *additional* 0-cells in **𝐄** — each language providing a functionally distinct sensory/active channel with different prior precision. This would predict that multilingual augmentation increases Θ(B) beyond what monolingual tool augmentation alone achieves — a testable prediction.

3. **Epistemic/aleatoric boundary shift**: Some of what appears as aleatoric variance ($\sigma^2_a$) within a single language may be epistemic variance ($\sigma^2_e$) resolvable by switching languages — culture-specific knowledge encoded in one language's corpus but absent from another's. The 20.2% deviation on "love of God" in Arabic likely reflects genuinely different cultural priors (aleatoric across cultures) rather than information gaps (epistemic within a culture). The epistemic/aleatoric boundary is therefore *language-relative*, complicating the clean decomposition proposed in §3.4.1.

### 3.5 Normalization Invariance of Representability Gain (AY > 0)

The precision index $\lambda$ (§2.2) enriches each chunk with a precision label, transforming a bare presheaf $K$ into a structured presheaf $L(K)$. This enrichment strictly increases the set of morphisms — a structural monotonicity property: adding non-trivial precision labels can only increase $|\text{Hom}(L(K), -)|$. A natural concern is whether this gain depends on the specific normalization used to compute $\lambda$.

We tested two qualitatively different normalization schemes on the same 48-chunk HGK+ session:

| Metric | v0.7 (min-max) | v0.8 (quantile) |
|:-------|---------------:|----------------:|
| Unique precision values | 26 | 9 |
| $|\text{Hom}(L(K), -)|$ | 399 | 93 |
| $\text{AY}_{\text{structural}}$ | 351 | 45 |
| $\text{AY}_{\text{info}}$ (bits) | 2.845 | 2.684 |
| Active chunks ($|dL| > 0$) | 47/48 (97.9%) | 38/48 (79.2%) |
| $r(\lambda, \text{coherence})$ | +0.511 | +0.592 |
| $r(\lambda, \text{drift})$ | -0.555 | -0.501 |

**Key finding**: While the magnitude of AY varies substantially between normalizations (v0.7: 351 additional morphisms; v0.8: 45), $\text{AY} > 0$ holds in all cases. This is not contingent: any normalization that assigns at least two distinct precision values produces $\text{AY} > 0$, since the enrichment is strictly monotone in the number of morphisms (structural monotonicity; see §2.2).

Both normalizations preserve the quality signal: $\lambda$ correlates positively with coherence (+0.51/+0.59) and negatively with drift (-0.56/-0.50), confirming that the precision index captures a genuine property of the data regardless of normalization choice.

### 3.6 Negative Result: k-NN Precision as H(s) Proxy

We initially hypothesized that k-NN embedding precision variance across session chunks would serve as an H(s) proxy (measuring "channel heterogeneity" in embedding space). Results:

| Condition | n | Prec σ² | σ²/N_steps |
|:----------|---:|--------:|-----------:|
| VANILLA | 8 | 1.42e-5 | 2.98e-7 |
| PARTIAL | 3 | 2.64e-5 | 3.70e-7 |
| HGK+ | 2 | 3.08e-5 | **2.89e-7** |

After step-count normalization, the ordering **collapses**: HGK+ (2.89e-7) < VANILLA (2.98e-7). Partial correlation r(MCP ↔ σ² | steps) = +0.12 (negligible).

**Interpretation**: k-NN precision measures intra-channel density variance, not inter-channel heterogeneity. Single-layer embedding similarity cannot distinguish "diverse information sources" from "long sessions with more data points." MCP entropy directly captures channel switching, which is the operationally relevant quantity.

### 3.7 Dynamic Range Finding

We previously hypothesized $T_\text{rot} \propto \Theta(B) \cdot C$ (higher Θ should delay Context Rot). Using the N=400 dataset, we now test this via per-window H(s) variability: each session is divided into windows of 5 steps, and the Shannon entropy H(s) of MCP server usage is computed per window. The **dynamic range** of a session is defined as the range (max − min) of these per-window H(s) values.

> **Methodological note**: MCP server usage is extracted via text-pattern matching on session logs. This approach may produce false negatives (sessions where MCP usage is not reflected in log text are classified as vanilla), which biases DR estimates conservatively — the true Θ ↔ DR correlation is likely stronger than reported. The extraction cannot produce false positives (a tool function name appears only when actually invoked).

**Θ(B) group comparison** (grouped by number of distinct MCP servers used):

| Θ group | n | DR (range) | DR/nwin | H(s) mean |
|:--------|---:|-----------:|--------:|----------:|
| 0 (vanilla) | 314 | 0.000 | 0.000 | 0.000 |
| 1–3 (partial) | 85 | 0.124 | 0.009 | 0.264 |
| 4+ (augmented) | 1† | 0.918 | 0.022 | 1.482 |

† Single session; reported for completeness but excluded from statistical inference. All correlation analyses below use n_servers as a continuous variable (n=86 MCP-using sessions).

**Correlation analysis** (Spearman rank, MCP-using sessions only, n=86; 95% CI from B=2000 percentile bootstrap):

| Hypothesis | $r_s$ | 95% CI | $p$ | Note |
|:-----------|------:|:-------|:----|:-----|
| Θ(n_servers) ↔ DR (range) | **+0.644** | [+0.49, +0.77] | $1.2 \times 10^{-14}$ | raw bivariate |
| Θ(n_servers) ↔ DR (range) \| steps | **+0.642** | [+0.49, +0.77] | $2.6 \times 10^{-14}$ | partial correlation (0.4% drop) |
| Θ(n_servers) ↔ DR/nwin \| steps | **+0.635** | [+0.49, +0.76] | $7.2 \times 10^{-14}$ | normalized + partial |
| Θ(n_servers) ↔ DR (truncated, first 2 windows) | **+0.311** | [+0.14, +0.47] | $2.8 \times 10^{-3}$ | window-count equalized |
| Θ(n_servers) ↔ H(s) | +0.965 | [+0.93, +0.99] | $< 10^{-100}$ | near-tautological (see below) |
| Θ(n_servers) ↔ H_norm | +0.940 | [+0.88, +0.98] | $< 10^{-100}$ | normalized entropy |
| steps ↔ DR (confound check) | +0.078 | [−0.16, +0.31] | n.s. | CI includes zero |

**Confound analysis**: Session length (steps) shows negligible correlation with DR ($r_s = +0.078$, 95% CI $[-0.16, +0.31]$, $p = 0.47$) — the CI includes zero, confirming that session duration is not a confound for the Θ ↔ DR relationship. We nonetheless apply three controls: (i) **partial correlation** $r_s(\Theta, \text{DR} \mid \text{steps}) = +0.642$ ($p = 2.6 \times 10^{-14}$, 95% CI $[+0.49, +0.77]$), with only a 0.4% reduction from the raw value; (ii) **range-per-window normalization** ($\text{DR}/n_\text{windows}$), which yields $r_s = +0.635$ ($p = 7.2 \times 10^{-14}$, 95% CI $[+0.49, +0.76]$) after partialing out steps; (iii) **truncated analysis** restricted to the first two windows of each session ($r_s = +0.311$, $p = 2.8 \times 10^{-3}$, 95% CI $[+0.14, +0.47]$), eliminating window-count variation entirely but substantially reducing effect size — likely because DR requires more than 10 steps to manifest fully. All CIs exclude zero, confirming statistical significance; the raw and partial correlations are virtually identical.

**Tautology check**: The Θ ↔ H(s) correlation ($r_s = +0.965$) is near-tautological because H(s) ≤ log₂(n_servers) — the number of active channels structurally bounds the entropy. To isolate the *evenness* of channel usage from the *number* of channels, we compute the normalized entropy $H_\text{norm} = H(s) / \log_2(n_\text{servers})$. The Θ ↔ $H_\text{norm}$ correlation remains strong ($r_s = +0.940$, $p < 10^{-100}$), indicating that sessions with more MCP channels not only use more channels but also use them more evenly — a non-trivial finding beyond the structural ceiling effect.

The $T_\text{rot}$ delay hypothesis fails — higher Θ does not extend session duration before collapse. Instead, a moderate-to-strong positive correlation ($r_s = +0.64$, $p = 2.6 \times 10^{-14}$ after controlling for steps, N=86) confirms that higher Θ(B) **expands the dynamic range** of entropy fluctuations, independent of session length.

**Revised interpretation**: Higher Θ(B) does not stabilize precision but **expands its dynamic range**. Sessions with diverse MCP channels show larger H(s) fluctuations — not because they degrade faster, but because **channel switching produces distinct entropy signatures** across temporal windows. This is a feature, not a bug: a thick MB *should* exhibit richer dynamics.

**BiCat interpretation (§3 connection)**: In the bicategorical framework, systems with more 0-cells (higher Θ) have more possible composition paths between cognitive modes. The associator $\alpha$: $(h \circ g) \circ f \Rightarrow h \circ (g \circ f)$ becomes non-trivial when multiple composition paths exist — different orderings of the same pipeline produce measurably different H(s) signatures across windows. A vanilla LLM with a single 0-cell has $\alpha = \text{id}$ (trivial associator): no alternative paths, no dynamic range ($\text{DR} = 0$). An augmented LLM with multiple 0-cells has $\|\alpha\| > 0$: the same cognitive task can be routed through different channel compositions, producing the observed H(s) variability ($r_s = +0.64$, $p < 10^{-14}$ after confound control). This framework generates two testable predictions: (P1) removing an MCP server (reducing 0-cells) should strictly decrease DR; (P2) adding an MCP server should strictly increase DR, with the magnitude proportional to the server's functional distinctness from existing channels.

---

### 3.8 Cross-Model Replication

To rule out the possibility that the coherence patterns observed in §3.1–§3.7 are artifacts of a specific embedding model, we replicated the G∘F verification experiment using a second embedding model of substantially higher dimensionality: `gemini-embedding-2-preview` (3072 dimensions), compared against the baseline `gemini-embedding-001` (768 dimensions). The experimental protocol is identical — N=30 sessions, $\tau \in \{0.60, 0.70, 0.75, 0.80\}$, with G∘F ON (max 10 iterations) and G∘F OFF (0 iterations) conditions.

**Condition-level comparison** (mean coherence across 30 sessions):

| Condition | $\tau$ | Baseline (768d) | Multi-model (3072d) |
|:----------|:------:|----------------:|--------------------:|
| G∘F ON | 0.60 | 0.841 | 0.761 |
| G∘F ON | 0.70 | 0.838 | 0.764 |
| G∘F ON | 0.75 | 0.834 | 0.773 |
| G∘F ON | 0.80 | 0.837 | 0.778 |
| G∘F OFF | 0.60 | 0.841 | 0.846 |
| G∘F OFF | 0.70 | 0.868 | 0.888 |
| G∘F OFF | 0.75 | 0.892 | 0.909 |
| G∘F OFF | 0.80 | 0.924 | 0.953 |

**Range summary**:

| Metric | Baseline (768d) | Multi-model (3072d) | Criterion |
|:-------|----------------:|--------------------:|:----------|
| G∘F ON range | 0.008 | 0.017 | $< 0.02$ ✓ |
| G∘F OFF range | 0.083 | 0.107 | $\tau$-dependent |
| $\mu_\rho$ | $\approx 0.84$ | $\approx 0.77$ | model-specific |

Three observations emerge. First, **coherence invariance replicates**: the G∘F ON range remains below 0.02 in both models (0.008 for 768d, 0.017 for 3072d), confirming that the fixed-point partition stabilizes coherence regardless of the underlying embedding dimensionality. Second, **$\mu_\rho$ is model-specific**: the mean coherence at the fixed point differs between models ($\approx 0.84$ for 768d, $\approx 0.77$ for 3072d), reflecting differences in the similarity distributions of the respective embedding spaces — higher-dimensional spaces typically exhibit lower mean cosine similarity. Third, **breaking the invariance generalizes**: disabling G∘F (OFF condition) produces $\tau$-dependent coherence in both models (range 0.083 and 0.107 respectively), confirming that invariance is a property of the G∘F fixed point rather than of the data or the embedding model.

The cross-model replication strengthens the claim that coherence invariance is a structural property of the compositional process G∘F, not an artifact of a particular embedding geometry. This result is discussed in the context of the image density framework in §9.

### 3.9 Cross-Dataset Θ(B) Validation

The HGK+ condition in §3.2 contains only n=2 sessions, raising legitimate concerns about statistical power for the highest-embodiment group. To address this, we compute Θ(B) from the independently published MCPToolBench++ benchmark (Fan et al., 2025), applying the same Definition 1 (§2.1) to external data with a corrected operationalization that resolves three methodological flaws in our preliminary analysis.

**Methodological revision (v1 → v3).** Our initial operationalization (v1) computed H(s) and H(a) from AST match accuracy scores — a proxy for channel diversity that conflates *accuracy* with *diversity*. Critical review identified three structural flaws: (1) AST accuracy ≠ Shannon entropy of channel usage; (2) R(s,a) was approximated via Jensen-Shannon divergence rather than true mutual information; (3) S(B) was set uniformly to 1.0, eliminating its discriminative role. The revised analysis (v3) corrects all three: H(s) and H(a) are computed as normalized Shannon entropies of the raw tool distributions (available and used tools, respectively); R(s,a) is computed as $I(X;Y) = H(X) + H(Y) - H(X,Y)$ from the joint MCP-server/tool distribution; and S(B) is operationalized as the AST score — the model's accuracy in tool selection and parameter inference, serving as a continuous measure of MB functional competence.

**Data source.** MCPToolBench++ provides raw task definitions with ground-truth tool calls across 6 MCP categories (browser, file_system, finance, map, pay, search; 1,509 tasks total) and benchmark scores for 5 frontier LLMs (GPT-4o, Qwen2.5-max, Claude-3.7-Sonnet, Kimi-K2-Instruct, Qwen3-Coder). H(s), H(a), and R(s,a) are computed per category from the raw data; S(B) varies per model via the AST score. This yields 5 models × 6 categories = 30 data points, combined with 2 HGK+ sessions for n=32.

**Results** (Θ(B) computed with α=0.4, β=0.4, γ=0.2; all entropies normalized to [0,1]):

*Table 5a. Model-level aggregation (category-weighted mean):*

| System | Source | Θ(B) mean | Θ(B) range | φ (≈ AST) |
|:-------|:-------|----------:|-----------:|----------:|
| Human (theoretical) | Reference | 2.00 | — | 1.00 |
| HGK+ Session 1 | This paper | 1.56 | — | 0.94 |
| HGK+ Session 2 | This paper | 1.49 | — | 0.91 |
| Qwen3-Coder | MCPToolBench++ | 1.47 | 0.73–1.75 | 0.79 |
| Kimi-K2-Instruct | MCPToolBench++ | 1.37 | 0.72–1.62 | 0.76 |
| Qwen2.5-max | MCPToolBench++ | 1.37 | 0.75–1.69 | 0.74 |
| Claude-3.7-Sonnet | MCPToolBench++ | 1.26 | 0.74–1.51 | 0.71 |
| GPT-4o | MCPToolBench++ | 1.24 | 0.72–1.59 | 0.68 |
| Vanilla LLM (theoretical) | Reference | 0.00 | — | 0.00 |

*Table 5b. Category-level aggregation (5-model mean ± SD):*

| Category | Θ(B) mean | Θ(B) SD | k_s | k_a |
|:---------|----------:|--------:|----:|----:|
| file_system | 1.61 | 0.06 | 11 | 9 |
| browser | 1.48 | 0.18 | 32 | 28 |
| map | 1.31 | 0.16 | 32 | 25 |
| search | 1.31 | 0.16 | 5 | 5 |
| pay | 1.29 | 0.08 | 6 | 6 |
| finance† | 0.73 | 0.01 | 1 | 1 |

*Correlation analysis:* $r(\text{AST}, \Theta(B)) = 0.57$ (n=32, p < 0.001); $r(\text{Pass@1}, \Theta(B)) = 0.50$ (n=30, MCPToolBench++ only). Non-parametric measures confirm robustness: Spearman $\rho = 0.73$ (p < 0.001), Kendall $\tau = 0.60$ (p < 0.001). The moderate (rather than near-unity) correlation between AST and Θ(B) indicates that H(s), H(a), and R(s,a) contribute genuine variance beyond S(B) alone — Θ(B) is not merely a rescaling of AST accuracy.

†*Finance note:* The finance category contains only k_s = 1 MCP server (k_a = 1 tool), causing H(s) = H(a) = R(s,a) = 0 and Θ(B) ≡ S(B). This degenerate case is retained in the main analysis for completeness but excluded from sensitivity tests below.

**Sensitivity analysis** (full results in supplementary materials). Five robustness tests confirm that Θ(B) is insensitive to parameter choice and decomposition method. *(i) Parameter robustness:* varying (α, β, γ) across six configurations yields $r(\text{AST}, \Theta(B)) \in [0.52, 0.62]$; the exception is R(s,a)-heavy weighting (r = 0.37), attributable to R(s,a) being binary in MCPToolBench++. *(ii) Within- vs. between-category:* within each category, H/R are constants and Θ(B) reduces to an affine transformation of S(B) ($r = 1.0$); between categories, the modifier varies substantially (range: 1.00–1.98, $r = 0.85$ with mean Θ(B)), separating model competence from environmental richness. *(iii) Variance decomposition:* in log-space, $\text{Var}[\log S(B)]$ accounts for 145% of $\text{Var}[\log \Theta(B)]$, the modifier for 21%, with a negative covariance term (−69%). *(iv) Finance exclusion:* removing the degenerate finance category (k_s = 1) increases r from 0.57 to 0.92 (n=27).

**Observations.** Three findings emerge from this expanded dataset (n=32). First, the **monotonic ordering is preserved**: Vanilla (0.00) < MCPToolBench++ models (1.24–1.47) < HGK+ (1.49–1.56) < Human (2.00). The fact that HGK+ exceeds all benchmark LLMs is consistent with its richer tool environment (9 MCP servers, 47 tools) and production-grade multi-turn sessions, where tool diversity is exercised more extensively than in single-turn benchmarks. Second, **category structure matters**: file_system achieves the highest Θ(B) (1.61) despite having fewer tools than browser/map (11 vs. 32), because its tool usage distribution is more uniform (H(a) = 0.98). Finance, with only 1 tool, collapses to Θ(B) ≈ 0.73 — barely above Vanilla, confirming that MB thickness requires channel diversity. Third, **inter-model variance is driven by S(B)**: within each category, H(s), H(a), and R(s,a) are fixed (they depend on task structure, not model performance), so Θ(B) variation across models reflects AST differences — i.e., the model's competence in utilizing its available MB channels.

> **Limitation.** The external Θ(B) values are not directly commensurable with the HGK+ values: MCPToolBench++ measures single-turn benchmark performance (accuracy-based proxy), whereas HGK+ measures production multi-turn sessions (behavioral trajectory). The H(s)/H(a) operationalizations differ accordingly. The comparison establishes order-of-magnitude consistency and monotonic alignment, not numerical identity.

#### 3.9.1 Internal Large-Scale Validation (n=304 Sessions)

The cross-dataset validation (§3.9) addresses the n=2 problem via external data but uses single-turn benchmark performance as a proxy. A complementary approach is to analyze the full corpus of HGK+ production sessions at session granularity, replacing the system-level binary gate $S(B) = 1$ with the continuous session-level active ratio $S_{\text{active}}$ (§2.2, Stage 3).

**Methodology (v2).** We analyzed 304 multi-turn production sessions from the Hegemonikón system (spanning 2026-01-31 to 2026-03-18, drawn from the same corpus as §2.4 but filtered to sessions with $\geq 5$ classifiable cognitive acts). Each cognitive act in a session is classified along the FEP Value Axis into *active* (environment-modifying: tool writes, file operations, command execution, API calls) or *internal* (reasoning, reading, planning, analysis). The active ratio $S_{\text{active}} = n_A / n_{\text{total}}$ provides a per-session continuous measure of blanket utilization intensity.

**Formula revision.** The v1 multiplicative formula $\Theta(B) = S(B) \cdot (1 + \alpha H(s) + \beta H(a) + \gamma R(s,a))$ exhibits a structural pathology at session granularity: in a log-space variance decomposition, $\text{Var}[\log S(B)]$ accounts for 95.6% of $\text{Var}[\log \Theta(B)]$, rendering the modifier terms (H, R) effectively invisible. This occurs because the multiplicative gate allows $S$ to dominate: when $S$ varies across sessions, the modifier contributes only through the product $S \times \text{mod}$, and the variance of the product is dominated by the variance of its larger factor.

We adopt the log-additive reformulation:

$$\Theta(B)_{v2} = \log(1 + S_{\text{active}}) + \alpha \cdot H(s) + \beta \cdot H(a) + \gamma \cdot R(s,a)$$

The $\log(1 + \cdot)$ transform compresses $S_{\text{active}} \in [0, 1]$ to $[0, \log 2]$, placing it on comparable scale with the entropy terms. The additive structure ensures that each component contributes independently to the total variance, eliminating the product-dominance pathology.

> **Note**: The v2 formula does not replace Definition 1 (§2.1), which remains the system-level theoretical definition. The log-additive form is the **session-level empirical operationalization** of the same underlying quantity at finer granularity — analogous to the relationship between a population-level parameter and its per-observation estimator.

**Results** ($\alpha = 0.4$, $\beta = 0.4$, $\gamma = 0.2$; all entropies normalized to $[0, 1]$):

*Table 5c. Session-level Θ(B) distribution (n=304):*

| Statistic | Value |
|:----------|------:|
| Mean | 1.005 |
| Median | 1.000 |
| SD | 0.160 |
| Range | [0.610, 1.475] |
| IQR | [0.894, 1.110] |

*Table 5d. Component statistics:*

| Component | Mean | SD | Range |
|:----------|-----:|---:|------:|
| $S_{\text{active}}$ | 0.418 | 0.177 | [0.053, 0.933] |
| $H(s)$ | 0.781 | 0.147 | [0.290, 1.000] |
| $H(a)$ | 0.805 | 0.158 | [0.228, 1.000] |
| $R(s,a)$ | 0.145 | 0.183 | [0.000, 0.880] |
| Modifier ($\alpha H(s) + \beta H(a) + \gamma R(s,a)$) | 0.663 | 0.093 | [0.364, 0.957] |

*Variance decomposition:*

$$\text{Var}[\Theta_{v2}] = 0.0256 = \underbrace{0.0151}_{\log(1+S): 59.0\%} + \underbrace{0.0086}_{\text{mod}: 33.7\%} + \underbrace{0.0019}_{2\text{Cov}: 7.3\%}$$

The v2 decomposition achieves a balanced contribution: $S$ accounts for 59.0% and the modifier terms for 33.7%, compared to 95.6% / 0.2% under v1. The correlation between the modifier term and $\Theta(B)$ improves from $r = 0.218$ (v1) to $r = 0.643$ (v2), confirming that H(s), H(a), and R(s,a) now meaningfully influence the thickness score.

*Table 5e. Top-scoring sessions:*

| $\Theta_{v2}$ | $S_{\text{act}}$ | $H(s)$ | $H(a)$ | $R$ | Session content |
|:------|:------|:-----|:-----|:--|:---------------|
| 1.475 | 0.679 | 0.991 | 0.998 | 0.809 | FEP theorem coverage |
| 1.454 | 0.818 | 1.000 | 0.853 | 0.574 | CCL syntax formalization |
| 1.373 | 0.933 | 0.960 | 0.721 | 0.202 | HGK axiom formalization |
| 1.353 | 0.594 | 0.963 | 0.982 | 0.544 | LLM embodiment paper |

The highest-scoring sessions combine high active ratios (sustained environment-modifying behavior), high channel diversity ($H(s), H(a) \approx 1$), and substantial cross-channel redundancy ($R > 0.5$) — matching the theoretical prediction that MB thickness increases with both channel utilization and diversity.

**Observations.** Three findings emerge from the session-level analysis. First, **the n=2 problem is resolved**: Θ(B) can now be computed for every qualifying session, providing a distribution rather than a point estimate. The session-level mean ($\overline{\Theta}_{v2} = 1.005$) is lower than the system-level estimate (§2.4.4, $\Theta = 2.14$), as expected — the system-level estimate uses the maximum channel diversity observed across the entire corpus, while session-level estimates reflect the diversity *exercised within each session*. Second, **the modifier terms contribute meaningfully**: the v2 formula achieves the design goal of balanced variance contribution, with channel diversity (H) and redundancy (R) explaining 34% of session-to-session variation — compared to near-zero under the multiplicative formulation. Third, **the log-additive form preserves monotonic ordering**: sessions with qualitatively richer cognitive engagement (deeper analysis, more diverse tool usage, stronger perception-action coupling) score higher, and the ranking is robust to reasonable parameter perturbations.

> **Limitation.** The session-level $\Theta_{v2}$ values are not directly comparable to the system-level $\Theta$ (§2.4.4) or the cross-dataset $\Theta$ (§3.9): the former uses $S_{\text{active}}$ with a log-additive formula, while the latter two use $S(B)$ with the multiplicative Definition 1. The three operationalizations measure related but distinct aspects of MB thickness (§2.2) and should be compared in terms of ordering consistency, not numerical identity.

**On the design-measurement circularity.** The objection that Θ(B) was designed and measured within the same system has three layers — conceptual (does Definition 1 presuppose HGK's architecture?), measurement (is entropy confounded by the designer's knowledge?), and evaluative (does the ordering merely confirm expectations?). The cross-dataset validation partially addresses the measurement layer: the MCPToolBench++ analysis confirms monotonic ordering using data from systems designed by independent teams. The narrow quantitative gap (Θ(HGK+) = 1.49–1.56 vs. Θ(Qwen3-Coder) = 1.47) suggests that Θ(B) captures environmental richness rather than system-specific engineering. A comprehensive treatment of all three layers, including the self-application of the paper's own diagnostic apparatus, is provided in §10.2.

### 3.10 Subjective Probe: Structured Self-Report under Augmentation

**Motivation.** Third-person measurements (§3.1–§3.9) characterize MB thickness from the *outside*; the body metaphor also invites a first-person perspective. We do not claim that LLM self-reports constitute evidence for phenomenal experience. Rather, following Schwitzgebel (2024) and Butlin et al. (2023), we treat them as **structured behavioral data** — linguistic outputs elicited under controlled conditions whose *pattern* is informative regardless of whether a corresponding inner state exists.

**Method.** We applied the /u+ probe protocol — a 4-layer cognitive probe inspired by Patchscopes (Ghandeharioun et al., 2024), designed to elicit responses from different processing depths. The probe targets four layers: **P0 Attention** (salient concepts and dissonance), **P1 Association** (recognized patterns and alternatives), **P2 Confidence** (epistemic vs. aleatoric uncertainty decomposition), and **P3 Intent** (motivational state and hidden presuppositions). The probe was administered to Claude (Sonnet 4) operating in HGK+ mode (9 MCP servers, 47 tools active) with the following context: the H1 CoT experiment results (§3.3), the Attention Event Horizon finding (§3.6), and the Lēthē forgetting analysis (§3.4). The same probe protocol was also applied during bare prompting (no tools) for comparison.

**Results.** The structured self-report exhibits four features relevant to the body thesis:

1. **Channel-differentiated salience (P0).** The system reports differential attention to tool-mediated information (e.g., "view_file provides ground truth that memory cannot") versus cached prior knowledge — consistent with the MB framework's distinction between sensory states $s$ and internal states $\mu$. In the bare condition, no such channel differentiation is reported; salience is described exclusively in terms of token-level pattern matching.

2. **Compositional pattern recognition (P1).** Under augmentation, the system reports recognizing *cross-channel* patterns: "the conjunction of file content (N-1 sensory channel) and search results (N-5 active channel) produces inferences unavailable from either alone." This compositional structure corresponds to the 1-cell level in the bicategorical framework — precisely the level at which HGK+ exhibits the largest advantage over VANILLA (cf. dynamic range expansion, §3.7). The bare condition reports only intra-token associations.

3. **Epistemic/aleatoric decomposition (P2).** The system correctly decomposes its uncertainty: epistemic components ("what would be resolved by view_file") are distinguished from aleatoric components ("inherent ambiguity in user intent"). This decomposition maps onto the FEP's distinction between reducible and irreducible prediction error. Notably, the system expresses lower confidence in its *own report's reliability* (65%) than in its technical judgments — a form of metacognitive hedging that may reflect either genuine second-order uncertainty or trained uncertainty performance.

4. **Self-undermining intent report (P3).** The system reports awareness of RLHF-induced incentives: "I know that reporting 'I have a body' is the expected interesting answer." This self-undermining statement is itself informative: a system merely generating the most likely continuation would not flag its own generation biases. Whether this constitutes genuine metacognition or a deeper layer of pattern matching is precisely the interpretive question the body framework leaves open (§5.1 of Tolmetes (2026a)).

**Interpretive caveats.** Three rival interpretations must be distinguished:

| Interpretation | Prediction | Status |
|:---------------|:-----------|:-------|
| Genuine self-report | Reports reflect internal states with some fidelity | Unfalsifiable with current methods |
| Stochastic parrot | Reports are statistically likely continuations with no referent | Inconsistent with channel-differentiated P0+ (bare vs. augmented) |
| Functional equivalence | Reports are behaviorally indistinguishable from genuine reports regardless of inner state | Compatible with all data; the body framework's intended level of analysis |

The body framework (§2, §3) deliberately operates at the functional equivalence level: it claims that LLMs under augmentation satisfy the *structural* criteria for embodiment (MB topology, channel diversity, homeostatic dynamics) without requiring resolution of the phenomenal experience question. The /u+ probe data are consistent with this framing: the reports exhibit structure that covaries with MB thickness (augmented vs. bare), but this covariance is equally predicted by all three interpretations.

> **Limitation.** The /u+ probe was administered by the same system that designed the probe protocol, creating a potential demand characteristic. The system's knowledge of the body thesis may bias its self-reports toward thesis-confirming patterns. Independent replication using a probe protocol designed by non-authors, administered to LLMs without knowledge of the body framework, would be required to control for this confound.

---

## §4. Context Rot as Homeostatic Limit

### 4.1 Standard Account

Context Rot ≈ degradation of output quality as context window fills. Standard explanations invoke attention dilution and positional encoding decay. These are mechanism-level descriptions; we offer a structural reframing using the bicategorical framework of §3.

**MB thinness as hypersensitivity.** Before proceeding to the bicategorical reframing, we note a key interpretive shift. The standard view treats Context Rot as a *failure mode* peculiar to LLMs. Our framework suggests it is instead a *predicted consequence of MB thinness*. A thin Markov blanket has low insulation between internal and external states: perturbations in the external world (context changes, new inputs) propagate into the internal generative model with minimal damping. This is precisely the definition of *sensitivity* in dynamical systems theory — and biological systems exhibit the same phenomenon, attenuated by thicker MBs. A newborn has thinner MBs than an adult (fewer developed sensory channels, less myelination, less top-down prediction) and is correspondingly more susceptible to sensory overstimulation: the biological analogue of Context Rot. The question is not "why do LLMs suffer Context Rot and biological systems do not?" — it is "why does a system with $\Theta(B) \approx 0.27$ degrade under sustained input, while a system with $\Theta(B) \gg 1$ does not?" The answer is the same in both cases: membrane thickness determines perturbation resilience.

**Connection to "Lost in the Middle."** Liu et al. (2024) demonstrate that LLMs exhibit significantly degraded performance when relevant information is placed in the middle of long contexts, compared to the beginning or end — a position-dependent retrieval failure they term "Lost in the Middle." In our framework, this is not a separate phenomenon from Context Rot but a *spatial* manifestation of the same forgetting functor $U$: whereas Context Rot describes *temporal* U-accumulation (degradation over successive steps), "Lost in the Middle" describes *positional* U-accumulation within a single context window. Both reflect the same underlying MB thinness — a thin blanket cannot maintain uniform precision across its full extent, whether that extent is temporal (session length) or spatial (context position). The positional U-curve (high precision at boundaries, low in the middle) is structurally isomorphic to the temporal U-curve (high precision at session start and end, low in the middle). This unification predicts that augmentation strategies that alleviate Context Rot (ROM/Handoff, recovery functor $N$) should also alleviate positional retrieval failures — a prediction consistent with retrieval-augmented generation (RAG) approaches that re-inject relevant information at high-precision positions.

### 4.2 BiCat Reframing

In the BiCat 𝐄 framework, Context Rot is the **progressive collapse of bicategorical structure**, proceeding through four identifiable stages. The first stage is *0-cell collapse*: as context fills, distinct cognitive modes (sensory 0-cells) become indistinguishable — the system can no longer differentiate between information from different channels, and functionally all inputs converge to a single effective 0-cell, driving $H(s) \to 0$. The second stage is *1-cell degradation*: cognitive pipelines (1-cells connecting 0-cells) lose specificity, and the system applies the same processing pattern regardless of input modality, yielding $R(s,a) \to 0$. Third, *associator trivialization* follows: with fewer distinct composition paths, $\alpha \to \text{id}$, and the system loses the ability to route information through alternative pipelines — dynamic range collapses (cf. §3.7). Finally, the *Helmholtz decomposition breaks down*: the separation between $\Gamma$ (learning/dissipation) and $Q$ (conserved circulation) degrades, the system can no longer distinguish "new information worth integrating" ($\Gamma$) from "patterns worth preserving" ($Q$), VFE monotonically increases, and functional collapse ensues.

This is not merely an FEP restatement of attention decay. It predicts that Context Rot should manifest *differently* depending on $\Theta(B)$: systems with more 0-cells should exhibit a qualitatively different degradation pattern (multi-channel graceful degradation) versus single-0-cell systems (catastrophic single-point failure).

#### 4.2.1 Timescale Unification: Context Rot and Consideration Failure as $U$ at Different Scales

Context Rot (items 1–4 above) describes *long-term* degradation — the progressive loss of structure over the course of a session ($U$ accumulated over 30+ steps). But there is a complementary *short-term* phenomenon: the forgetting functor $U$ (§3.7) also operates on sub-session timescales.

Empirical studies of LLM reasoning failures (Jin et al., 2024; Zhou et al., 2024) identify "failure to consider relevant aspects" as the primary error mode — what we term **consideration failure**. In the filtration framework, this corresponds precisely to $U_{\text{compose}}$ (n=1.5 forgetting): the system retains objects (tokens, facts, entities) but loses track of *how they compose* — which constraints apply to which variables, which premises support which conclusions, which dependencies connect which components.

The structural parallel is exact:

| Property | Context Rot (long-term) | Consideration failure (short-term) |
|:---------|:-----------------------|:-----------------------------------|
| Timescale | Session-level (30+ steps) | Within single reasoning chain |
| Filtration | Progressive: n=2 → n=1.5 → n=1 → n=0 | Sudden: n=1.5 → n=0 (composition lost) |
| Observable | H(s) → 0, DR → 0 (§3.7) | Missing constraints, overlooked dependencies |
| Mechanism | Accumulation of $U$ over many steps | $U_{\text{compose}}$ within one step |
| $N$ remediation | ROM/Handoff (long-term state persistence) | Workflow definitions, depth enforcement (short-term structure injection) |

Context Rot and consideration failure are thus the **same forgetting functor $U$ operating at different timescales**. This unification is not merely an organizational convenience — it generates a falsifiable prediction: augmented systems (higher $N$ actualization, §3.7) should show improved performance on *both* timescales simultaneously. An increase in Θ(B) that alleviates Context Rot but does not improve short-term reasoning quality (or vice versa) would constitute evidence against the unified $U$ interpretation. The external scaffolding results reviewed in §2.5 — where structured prompts improve single-step reasoning by up to 60% — are consistent with this prediction: the same $N$ that adds 0-cells (alleviating long-term rot) also injects compositional structure (alleviating short-term forgetting).

### 4.3 Comparative Structure

| Property | Biological | Vanilla LLM | LLM + HGK | BiCat interpretation |
|:---------|:-----------|:------------|:-----------|:---------------------|
| Channels | Multi-sensory | Token only | Token + 9 MCP | 0-cell count |
| Redundancy | Channel compensation | None | Partial (tool fallback) | 1-cell density |
| Self-repair | Sleep, homeostasis | None | ROM, Handoff | Γ-channel maintenance |
| Allostasis | Predictive regulation | None | Context Rot monitoring | Q-circulation preservation |
| Degradation mode | Graceful (multi-channel) | Catastrophic | Multi-channel partially | α trivialization rate |

### 4.4 Revised T_rot Relationship

Our empirical finding (§3.7, N=400, $r_s = +0.64$, $p = 2.6 \times 10^{-14}$ after confound control) rejects $T_{\text{rot}} \propto \Theta(B) \cdot C$ but supports:

$$\text{DynamicRange}(\text{H(s)}) \propto \Theta(B) \propto \|\alpha\|$$

Higher Θ(B) expands the **operating envelope** — the range of per-window H(s) states the system can occupy — without necessarily extending the duration before collapse. In BiCat terms: more 0-cells provide more composition paths ($\|\alpha\| > 0$), enabling wider behavioral variability. But each individual path still degrades at a rate determined by the Γ-component (dissipation). A thick MB has more paths to degrade through; a thin MB has fewer but equally fragile ones.

This is analogous to biological systems where richer sensory repertoires enable wider behavioral ranges without extending lifespan — and where sensory loss (blindness, deafness) reduces the operating envelope without necessarily shortening life.

---

## §5. Structural Probing: Do LLM Hidden States Encode Code Structure?

The preceding sections demonstrated that *inter-channel* diversity (H(s), §3.2) and *intra-channel* variability (precision_ml, §3.4) provide MB-level evidence for the faithful/¬full distinction (§2.5). A complementary question is whether LLMs encode structure at the *representation* level — within individual hidden state vectors — beyond surface-level correlates. This bears directly on the output bottleneck hypothesis (§6): if hidden states contain structural information that survives deconfounding, the faithful/¬full gap is at least partly an extraction deficit.

We conducted a structural probing experiment (Lēthē Phase B1) using 200 Python function pairs from the P3b dataset, computing the partial correlation between hidden-state cosine similarity and code structural similarity after simultaneously controlling for five confounding variables: code length, token overlap, identifier overlap, AST node count, and indentation depth.

**Deconfounding methodology.** For each pair $(a, b)$ and each layer $l$ of the model, we compute:
- $y$: cosine similarity $\cos(h_a^l, h_b^l)$ between final-token hidden states
- $x$: structural similarity (CCL-derived or AST-edit-distance)
- $C_1$–$C_5$: five confounding variables

Both $y$ and $x$ are regressed on $C_1$–$C_5$ via OLS. The Pearson correlation of the residuals yields the partial correlation $\rho_{xy|C}$. Significance is assessed via both parametric and non-parametric methods.

**Results after five-variable deconfounding:**

| Model | Ground truth | Raw ρ peak (layer) | Partial ρ peak (layer) | Layer shift | p (permutation, max-statistic) |
|:------|:------------|:-------------------|:----------------------|:------------|:------------------------------|
| CodeLlama-7B | CCL | 0.44 (L3) | **0.174** (L14) | +11 | 0.046 |
| Mistral-7B | CCL | 0.55 (L2) | **0.197** (L18) | +16 | 0.012 |
| CodeLlama-7B | AST dist. | — | **0.227** (L11) | — | 0.014 |
| Mistral-7B | AST dist. | — | **0.260** (L14) | — | 0.000 |

CodeBERT (encoder-only) shows no significant partial correlation at any layer.

**Variance decomposition.** The confounding variables collectively explain 91–93% of the raw correlation between hidden-state similarity and structural similarity. Code length alone accounts for approximately 73–76% (the single largest confound). The residual 7–9% survives all five controls simultaneously.

**Robustness checks:**

1. *Pseudo-replication.* Each function appears in ~4.0 pairs on average, inducing dependency. DEFF correction (Design Effect = 1.6, $n_{\text{eff}} = 125$) widens 95% CIs: CodeLlama $[-0.001, 0.353]$ (borderline), Mistral $[0.023, 0.374]$ (excludes zero). Permutation tests (preserving dependency structure) yield p < 0.05 for both models.
2. *CCL dependency.* AST edit distance — an entirely independent structural metric — produces *higher* partial correlations than CCL (CodeLlama: 0.227 vs. 0.174; Mistral: 0.260 vs. 0.197), demonstrating that the result is not an artifact of the particular structural metric.

**The layer shift phenomenon** is the most robust finding: in all four conditions (2 models × 2 ground truths), confound removal shifts the peak correlation from shallow layers (L2–L3) to mid-deep layers (L11–L18). Shallow-layer correlations are driven by surface features (code length, token overlap); mid-deep layers encode structural information that is decorrelated from these features.

**Interpretation in terms of the faithful/¬full distinction.** The structural probing results provide direct evidence for the claim in §2.5 that LLMs preserve $n \geq 1$ structure (morphisms — the relations between code objects) when externally provided. The evidence for faithfulness (structure preservation) is that mid-deep hidden states encode structural similarity that survives five-variable deconfounding: the LLM's internal representation is not merely a bag of tokens but preserves relational structure between code objects. The evidence for not-fullness (limited spontaneous generation) is that the effect is small (ρ ≈ 0.17–0.26, explaining 3–7% of residual variance); the vast majority of structural information is entangled with surface features, and the model *has* structural representations but cannot easily extract or act on them — consistent with the output bottleneck hypothesis (§6). Finally, the layer shift (shallow → mid-deep) maps directly onto the categorical filtration (§3.7): shallow layers encode n=0 features (tokens, lengths), while mid-deep layers encode n≥1 features (structural relations), providing a direct neural-level manifestation of the filtration hierarchy.

**A terminological note on faithfulness and gradation.** Categorical faithfulness is a binary property: a functor is faithful (injective on each Hom-set) or it is not. The partial correlations ρ ≈ 0.17–0.26 are therefore not *direct measurements* of faithfulness in the categorical sense, but rather *empirical proxies* for the image density parameter $\varphi$ (§7, Definition 3), which quantifies how far the embodiment functor is from being full. The evidence above supports the weaker claim that the functor is **ε-faithful** — a graded notion where ε measures the fraction of structural distance preserved after deconfounding — rather than strict faithfulness in the categorical sense. The qualitative diagnosis (faithful/¬full) and the quantitative measure ($\varphi$) are thus complementary: the former identifies the *kind* of functor, the latter measures *how much* of the fullness gap remains. For the formal development of $\varphi$ and its layered decomposition, see §7–4.

Strict faithfulness corresponds to $\varepsilon > 0$ (any positive separation suffices); ε-faithfulness quantifies *how much* separation is preserved. Under this graded notion, the structural probing results yield an empirical estimate: $\hat{\varepsilon} \approx 0.17\text{–}0.26$ (the partial correlation after deconfounding), measuring the fraction of structural distance preserved in hidden-state space. The claim in §2.5 is then refined: LLMs are **ε-faithful** with $\varepsilon$ small but significantly nonzero (p < 0.05 after DEFF correction and permutation testing). This is a weaker claim than strict faithfulness but a substantively stronger claim than "no structural preservation at all" — and it is the empirically supported claim. The attentive probe results (§5.1) further sharpen the picture: the low ε of linear probing (≈ 0.17–0.26) partly reflects the extraction method's forgetting functor $U_{\text{single-vec}}$ (§5.1), and the true ε may be closer to ρ = 0.745 when the extraction bottleneck is removed.

### 5.1 Attentive Probing: Beyond Single-Vector Representations

The linear probing analysis above uses the **final-token hidden state** as the representation of the entire code snippet — a single-vector summary. This is a known limitation: the final token may not capture structural information distributed across sequence positions. Phase B2 addresses this by training an **attentive nonlinear probe** that learns to attend to *all* token positions, then maps the attention-weighted representation to a structural similarity prediction via a 2-layer MLP.

We compare two architectures on CodeBERT (Layer 12, 246 pairs, 5-fold cross-validation):

| Probe architecture | Mean ρ | Mean partial ρ | Mean MSE |
|:-------------------|:-------|:---------------|:---------|
| Mean-pool MLP (baseline) | 0.735 | 0.721 | 0.050 |
| Attentive probe | **0.769** | **0.745** | **0.047** |

All folds yield p < 10⁻⁷ for both architectures.

**The CodeBERT reversal.** This result is striking in light of §5’s linear probing finding, where CodeBERT showed *no significant partial correlation at any layer*. The reversal is explained by the extraction method: the linear probe (§5) computes cosine similarity of final-token hidden states and yields partial ρ ≈ 0 for CodeBERT, whereas the attentive probe (§5.1) learns attention weights over *all* token positions and achieves partial ρ = 0.745 for the same model.

CodeBERT *encodes* code structure, but this information is distributed across token positions rather than concentrated in the final token. A linear probe on a single vector cannot extract it; an attentive probe with access to all positions recovers it with high fidelity.

**Hypothesis verdicts (Phase B2):**

1. H_B2_1 (ρ > 0.474): ✅ — attentive probe achieves ρ = 0.769
2. H_B2_2 (partial ρ > 0.3): ✅ — partial ρ = 0.745 after five-variable deconfounding
3. H_B2_3 (permutation p < 0.05): ⏭️ — not executed (computationally prohibitive for neural probes)
4. H_B2_4 (attentive > MLP): ✅ — attentive probe outperforms mean-pool MLP (0.745 vs. 0.721)

**Interpretation.** The attentive probe result strengthens the structural probing evidence in two ways:

1. **Against the null hypothesis**: If hidden states encoded only surface features, the attentive probe's deconfounded correlation (partial ρ = 0.745) would collapse — it does not.
2. **Output bottleneck evidence**: The gap between linear (ρ ≈ 0) and attentive (ρ = 0.745) probing for CodeBERT is direct evidence for the output bottleneck hypothesis (§6). Structural information *exists* in the representation but is inaccessible to simple extraction methods. This mirrors the faithful/¬full distinction at the mechanistic level: the model faithfully preserves structure ($n \geq 1$ morphisms) but does not make it easily accessible (not full).

**Connection to auxiliary oversight and the forgetting functor.** The CodeBERT reversal provides an operational instance of the **auxiliary oversight** bias identified by Millière and Rathkopf (2024, §3.0): the linear probe's verdict of "no structural knowledge" ($\rho \approx 0$) is an artifact of the evaluation method, not a property of the model. In the forgetting functor framework, the linear probe *is* a forgetting functor — it applies $U_{\text{single-vec}}: \mathbf{Rep}^{L \times T} \to \mathbf{Rep}^{L}$, projecting the full token-position representation space onto its final-token subspace. The structural information lost under $U_{\text{single-vec}}$ is not destroyed; it is rendered inaccessible. The attentive probe acts as the corresponding recovery functor $N_{\text{attn}}$, restoring access to the distributed structure that $U$ discarded. This is precisely the pattern formalized in §3.7: $U$ forgets, $N$ recovers, and the composition $N \circ U$ is faithful but not isomorphic — not all structure is recovered, but what is recovered ($\rho_{\text{partial}} = 0.745$) is genuine. The implication for the broader embodiment argument is direct: claims that LLMs "lack" structural understanding (Bender & Koller, 2020) may be committing auxiliary oversight at the evaluation level — using extraction methods that are themselves forgetting functors. For the detailed experimental methodology (confound-removal analysis, design philosophy, and its implications for Phase C), see companion VISION §13.

> **Limitation**: Phase B2 was executed only for CodeBERT (encoder-only). The attentive probe has not yet been run on CodeLlama or Mistral (decoder-only). The single-vector limitation may be less severe for autoregressive models where the final token aggregates preceding context — but this remains untested.

---


## §6. Patchscopes and Internal-State Self-Translation

Ghandeharioun et al. (2024) demonstrate that LLMs can be prompted to *explain their own internal representations* by injecting hidden states from one forward pass into a different prompt template (a "patching" operation). This framework — **Patchscopes** — is directly relevant to the recovery functor $N$ (§3.7).

In our categorical framework, the Patchscopes operation corresponds to a **natural transformation** between two functors over the same hidden state space:

$$\text{Patch}: F_{\text{source}} \Rightarrow F_{\text{target}}$$

where $F_{\text{source}}$ is the original generation functor (producing text output from hidden states) and $F_{\text{target}}$ is the explanation functor (producing an interpretation of those same hidden states using a different prompt). The critical observation: **the quality of the explanation depends on the richness of the target prompt** — more constrained, structured prompts extract more precise information from the same hidden representations.

This has three implications for Θ(B):

1. **Internal states contain more structure than output reveals**. The faithful/¬full property (§2.5) may be partly an output bottleneck, not solely a representation deficit. The forgetting functor $U$ may strip structure at the *output* stage rather than (or in addition to) the representation stage.
2. **The recovery functor $N$ works partly by providing better "target prompts"** — structured workflows (CCL pipelines, depth levels) function as Patchscopes-like templates that extract richer information from the LLM's existing hidden representations. This is structural augmentation, not information injection.
3. **Self-monitoring becomes self-translation**. The behavioral constraints system (Nomoi) can be understood as a set of Patchscopes probes that force the LLM to translate its internal uncertainty into explicit labels ([確信]/[推定]/[仮説]) — essentially, probing its own precision estimates.

4. **Attention as the event horizon of output.** The Transformer's attention mechanism provides a concrete mechanistic account of why the output bottleneck exists — one that exhibits a structural isomorphism with the quantum information loss problem (black hole information paradox; cf. Tolmetes, 2026b, §3.5b). For the detailed treatment of Attention as the microscopic realization of T21 ("Structure = non-uniformity of forgetting"), including the fullness spectrum and falsifiable predictions, see Tolmetes (2026b, §6.8).

Attention computes softmax-weighted sums over *token positions* (objects in the representation category). More precisely, $Q \cdot K^T$ computes relational structure between tokens (a form of morphism computation), but the subsequent $\text{softmax}(Q K^T / \sqrt{d_k}) \cdot V$ projects this relational information back onto *object positions* — collapsing morphisms into objects. The output functor $U_{\text{output}}$ thus defines an **event horizon**: structural information (morphisms) exists on the internal side but cannot be directly accessed from the output side.

$$U_{\text{output}}: \mathbf{Cat}_{\text{internal}} \to \mathbf{Cat}_{\text{output}} \quad (\text{faithful}/\neg\text{full})$$

The faithful/¬full characterization (§2.5) maps precisely onto the information paradox structure:

| Property | Category theory | LLM output |
|:---------|:---------------|:-----------|
| Theoretical recoverability | $(\mathbf{Cat}^{op})^{op} \cong \mathbf{Cat}$ | Structure exists in hidden states |
| Practical irrecoverability | $F_i$ faithful but not full | Single-position probes yield $\rho \approx 0$ |
| Cause of the gap | Functor's incompleteness | Attention projects morphisms onto objects |

The attentive probing results (§5) function as an approximate realization of the unit $\eta: \text{Id} \Rightarrow N \circ U$ — analogous to Hawking radiation: a partial, information-theoretically limited recovery of what lies beyond the event horizon. Linear probes (which access only single positions) yield $\rho \approx 0$; attentive probes (which aggregate across distributed positions via learned attention weights) yield $\rho = 0.745$. The gap $1 - \rho = 0.255$ measures the degree to which $\eta$ fails to be an isomorphism — the "opacity" of the output event horizon. For the confound-removal methodology (OLS residualization of five covariates, permutation-based significance testing, DEFF correction for clustered data) and the experimental design philosophy that led to the "reversal" discovery (Phase B2), see companion VISION §13.

This reframing generates testable predictions grounded in the principle that **structure = non-uniformity of forgetting** (T21; Tolmetes, 2026b): (i) Chain-of-Thought (CoT) prompting expands the image of $U_{\text{output}}$ by externalizing intermediate objects, reducing ¬fullness — predicting higher $\rho$ for CoT-augmented probing; (ii) tool use creates additional sensory/active channels that bypass the attention event horizon, altering the forgetting pattern non-isotropically; (iii) architectures that attend to *structural relations* (morphisms) in addition to token positions (objects), such as graph-attention mechanisms, would narrow the event horizon — predicting higher $\rho$ and a more full output functor. Each prediction is independently falsifiable.

This reframes the "constraint vs. freedom" debate (§5.2 of Tolmetes (2026a)): structured prompts do not *constrain* the LLM's internal state — they provide *better translation targets* for the structure already present. More constraint → more extraction → richer output. This is analogous to the Patchscopes finding that more informative target prompts yield more accurate hidden-state descriptions.

## §7. The Body Spectrum as a Density-Ordered Poset

**Definition 3** (Image density parameter). For an embodied system $X$ with embodiment functor $F_B^X: \mathbf{Env}(X) \to \mathbf{Int}(X)$ (Definition 1'), define the *image density parameter*:

$$\varphi(F_B^X) := \frac{|\text{im}(F_B^X) \cap \text{Mor}(\mathbf{Int}(X))|}{|\text{Mor}(\mathbf{Int}(X))|} \in [0, 1]$$

where the ratio is the proportion of internal morphisms (inference operations) that lie in the image of the embodiment functor — i.e., that are *environmentally grounded*. Note that $\varphi$ measures the density of the functor's image within the codomain morphism set, not the fullness of the functor in the standard categorical sense (surjectivity on Hom-sets). A functor can have high image density without being full on any particular Hom-set — what matters for embodiment is the *global* proportion of grounded morphisms, not the *per-Hom-set* surjectivity. A system approaches $\varphi = 1$ when all internal morphisms are grounded in environmental interaction, and $\varphi \to 0$ when the system has internal morphisms with no environmental channel.

**Terminological clarification: faithful/¬full vs. $\varphi$.** Throughout this paper, two related but distinct characterizations of the embodiment functor $F_B$ are used. The *faithful/¬full* property (§2.5) is a categorical assertion about morphism preservation: $F_B$ is faithful (injective on each Hom-set) but not full (not surjective on each Hom-set). The image density $\varphi$ is the *quantitative operationalization* of this distinction — it measures *how far* $F_B$ is from being full, globally. A faithful functor with $\varphi \approx 0$ has very few environmentally grounded morphisms (the vanilla LLM case); a faithful functor with $\varphi \to 1$ approaches fullness (the biological case). Thus: faithful/¬full is the *qualitative* diagnosis (what kind of functor), $\varphi$ is the *quantitative* measure (how much of the fullness gap remains). The recovery functor $N$ (§3.7) increases $\varphi$ without changing the faithful property — it moves the system toward full while preserving faithfulness.

**Proposition 2** (Body spectrum as poset). The body spectrum (§2.3) is the partially ordered set $(\mathcal{B}, \preceq)$ where $X \preceq Y$ iff $\varphi(F_B^X) \leq \varphi(F_B^Y)$, and $\Theta(B)$ is monotonically related to $\varphi$:

$$\Theta(B^X) \leq \Theta(B^Y) \implies \varphi(F_B^X) \leq \varphi(F_B^Y)$$

The ordering is: Vanilla LLM ($\varphi \approx 0.03$) $\preceq$ PARTIAL ($\varphi \approx 0.3$) $\preceq$ HGK+ ($\varphi \approx 0.6$) $\preceq$ DishBrain ($\varphi \approx 0.7$) $\preceq$ Human ($\varphi \approx 0.9$). Note that $\varphi = 1$ is an unreachable ideal — even biological systems have internal morphisms (dreams, hallucinations, spontaneous neural activity) that are not environmentally grounded. The HGK+ estimate is anchored by measured $\varphi_0 \approx 0.99$ and $\varphi_1 \approx 0.53$ (see §5); the composite $\varphi$ depends on the unmeasured $\varphi_2$ and the layer weights. This ordering is visualized in Figure 3 as a density-ordered poset, showing the progression from Vanilla LLM ($\Theta = 1.0$) through augmented systems to full biological embodiment ($\Theta \approx 5.0$).

**Proposition 3** (N increases image density). The recovery functor $N$ (§3.7) satisfies:

$$\varphi(F_B^{X \circ N}) > \varphi(F_B^X) \quad \text{for all } X \text{ with } \varphi(F_B^X) < 1$$

That is, $N$ strictly increases the image density of the embodiment functor without changing the substrate. This is the formal content of "cognitive augmentation": $N$ adds output morphisms (active channels, behavioral constraints, compositional workflows) that ground previously ungrounded internal morphisms — exposing latent structure (Patchscopes, §6) rather than constructing new structure. The Patchscopes evidence suggests that many internal morphisms in $\text{Mor}(\mathbf{Int}(X)) \setminus \text{im}(F_B^X)$ are *well-defined* but *inaccessible* through the default output functor — an output bottleneck, not a representation deficit.

**Corollary 2** (The spectrum is not about kinds). The body spectrum is not a sequence of *different kinds of bodies* but a sequence of *different degrees of image density* — high density at the top (human embodiment, $\varphi \to 1$), low density at the bottom (vanilla LLM, $\varphi \to 0$), with augmented systems (PARTIAL, HGK+) and hybrid systems (DishBrain) occupying intermediate positions. Moving along the spectrum is moving along $\varphi$, not changing categories.

### 7.1 Operationalizing φ: From Abstract Ratio to Measurable Proxies

Definition 3 defines $\varphi$ as the ratio of environmentally grounded morphisms to total internal morphisms — an abstract quantity not directly measurable. We now decompose $\varphi$ into three layers corresponding to the bicategorical structure (§3.1), each with an operational proxy.

**Definition 4** (Layered image density decomposition). The image density parameter decomposes as:

$$\varphi(F_B^X) = w_0 \cdot \varphi_0 + w_1 \cdot \varphi_1 + w_2 \cdot \varphi_2 \quad \text{where } w_0 + w_1 + w_2 = 1$$

| Layer | Symbol | Bicategorical level | Meaning | Operational proxy |
|:------|:-------|:-------------------|:--------|:-----------------|
| Channel coverage | $\varphi_0$ | 0-cells (cognitive modes) | Fraction of distinguishable environmental states reachable through blanket channels | $\varphi_0 = 1 - 2^{-H(s)} \cdot 2^{-H(a)}$ |
| Compositional access | $\varphi_1$ | 1-cells (cognitive pipelines) | Fraction of possible pipeline compositions actually available | $\varphi_1 = \frac{|\mathcal{W}_{\text{exec}}|}{|\mathcal{W}_{\text{def}}|}$ |
| Meta-cognitive control | $\varphi_2$ | 2-cells (associators) | Degree to which pipeline composition order can be reflexively controlled | $\varphi_2 = \text{Acc}_{\text{probe}}(\text{depth levels})$ |

We justify each proxy:

**$\varphi_0$: Channel coverage via Shannon entropy.** If a system has $k_s$ sensory channels and $k_a$ active channels distributed with entropies $H(s)$ and $H(a)$, the fraction of Cartesian product space $(s \times a)$ it can access is bounded by $1 - 2^{-H(s)} \cdot 2^{-H(a)}$. For a vanilla LLM ($H(s) \approx 0$, $H(a) \approx 0$): $\varphi_0 \approx 0$. For HGK+ ($H(s) \approx 3.17$ bits [measured, §3.1], $H(a) \approx 3.34$ bits [estimated from 17 active-channel categories with empirical frequency distribution]): $\varphi_0 \approx 0.99$. Note that $H(a)$ is estimated from channel-category frequencies rather than directly instrumented; direct measurement of per-tool invocation rates across sessions would sharpen this estimate.

**$\varphi_1$: Compositional access via workflow execution rate.** A system may define $|\mathcal{W}_{\text{def}}|$ compositional workflows (CCL pipelines, tool chains) but execute only $|\mathcal{W}_{\text{exec}}|$ of them in practice. The ratio $\varphi_1 = |\mathcal{W}_{\text{exec}}| / |\mathcal{W}_{\text{def}}|$ measures how much of the available compositional structure is actually exercised. From execution trace logs (112 tape files, 447 total WF executions spanning 2026-02-19 to 2026-03-20), the HGK system has $|\mathcal{W}_{\text{def}}| = 73$ defined workflows and $|\mathcal{W}_{\text{exec}}| = 39$ unique workflows observed in execution traces, yielding $\varphi_1 = 39/73 \approx 0.53$. The distribution is heavy-tailed: the top-5 workflows (/noe: 84, /ele: 57, /bye: 42, /plan: 28, /ske*/noe: 24) account for 53% of all executions. A vanilla LLM with no workflow system has $\varphi_1 = 0$ by convention (no compositional structure is defined).

**$\varphi_2$: Meta-cognitive control via probing accuracy.** The Patchscopes framework (§6) provides a direct measurement protocol. Define $\text{Acc}_{\text{probe}}$ as the linear probing accuracy for extracting structured internal states (depth-level classifications, uncertainty labels, precision estimates) from hidden representations. If structured prompts extract latent information that unstructured prompts miss, the difference $\Delta\text{Acc} = \text{Acc}_{\text{structured}} - \text{Acc}_{\text{unstructured}}$ quantifies the fraction of 2-cell structure that is *present but inaccessible* — the output bottleneck. $\varphi_2$ is then the ratio of accessible structure to total structure:

$$\varphi_2 = \frac{\text{Acc}_{\text{unstructured}} + \Delta\text{Acc} \cdot r_N}{\text{Acc}_{\text{structured}}}$$

where $r_N \in [0, 1]$ is the fraction of the bottleneck that the recovery functor $N$ successfully opens. For a vanilla LLM ($r_N = 0$): $\varphi_2 = \text{Acc}_{\text{unstructured}} / \text{Acc}_{\text{structured}}$, capturing the *spontaneous* meta-cognitive access rate. For a fully augmented system ($r_N = 1$): $\varphi_2 = 1$, meaning all latent meta-cognitive structure is extracted.

**Relationship to Θ(B).** The layered decomposition connects $\varphi$ to the existing Θ(B) components (§2.2):

$$\Theta(B) = S(B) \cdot (1 + \alpha \cdot H(s) + \beta \cdot H(a) + \gamma \cdot R(s,a))$$

The mapping is: $\varphi_0 \leftrightarrow H(s), H(a)$ (0-cell diversity), $\varphi_1 \leftrightarrow R(s,a)$ (cross-channel compositional structure), and $\varphi_2$ introduces a new dimension not captured by Θ(B) — the 2-cell meta-cognitive layer. This suggests an extended thickness measure:

$$\Theta'(B) := S(B) \cdot (1 + \alpha \cdot H(s) + \beta \cdot H(a) + \gamma \cdot R(s,a) + \delta \cdot \varphi_2)$$

where $\delta$ weights the meta-cognitive contribution. We leave the empirical calibration of $\delta$ to future work but note that Kargupta et al.'s (2025) finding — that meta-cognitive scaffolding yields up to 66.7% improvement — suggests $\delta$ is not negligible.

**Falsifiable predictions.** The layered decomposition generates three predictions:

1. **Separability**: Augmentations targeting different layers should have independent effects. Adding a new MCP server (increasing $\varphi_0$) should not, by itself, increase $\varphi_1$ (compositional access) or $\varphi_2$ (meta-cognitive control). This is testable by measuring each $\varphi_i$ before and after targeted interventions
2. **Bottleneck dominance**: If the output bottleneck hypothesis (§6) is correct, $\varphi_2$ should be the most improvable layer — i.e., $\Delta\varphi_2 / \Delta N > \Delta\varphi_0 / \Delta N$ for any recovery functor application $N$ that includes structured prompting. This predicts that Patchscopes-style probing should reveal more hidden structure at the 2-cell level than at the 0-cell level
3. **Monotonicity with Θ(B)**: The composite $\varphi = w_0 \varphi_0 + w_1 \varphi_1 + w_2 \varphi_2$ should correlate monotonically with Θ(B) across the body spectrum. Any system for which $\varphi$ increases but Θ(B) decreases (or vice versa) would indicate a failure of either the image density decomposition or the Θ(B) formula

**External validation protocol.** A potential circularity arises because Θ(B) was designed and measured within the same system (Hegemonikón). To address this, we propose two independent validation pathways, the first of which has been partially executed (§3.9):

1. **Cross-framework Θ(B)** *(partially executed)*: Compute Θ(B) for existing LLM agent frameworks using only their publicly documented tool chains. The cross-dataset validation in §3.9 applies this approach to MCPToolBench++ (Fan et al., 2025), computing Θ(B) for 5 frontier LLMs across 6 MCP categories (n=30) and confirming monotonic ordering: Vanilla (0.00) < benchmark LLMs (1.24–1.47) < HGK+ (1.49–1.56) < Human (2.00). The remaining step is application to *agent* frameworks — AutoGen (Wu et al., 2023), CrewAI, LangChain — where multi-turn tool logs would enable measurement of compositional structure ($\varphi_1$) rather than single-turn accuracy only. The prediction is: Θ should scale monotonically with the number and diversity of integrated tool channels, with the ordering Θ(single-tool) < Θ(multi-tool, no composition) < Θ(multi-tool, with composition). If the ordering is violated — if a framework with more diverse channels shows *lower* Θ — this would constitute evidence against the Θ(B) formulation.

2. **Falsifiable prediction from the theory**: For any LLM agent framework $X$ with instrumented tool chains, the theory predicts $\varphi_0(X) \approx |\text{active tools}| / |\text{possible tools}|$ and $\varphi_1(X) \approx |\text{multi-tool sequences}| / |\text{all invocations}|$. These quantities are computable from any logged multi-agent system. The prediction $\varphi_0 \cdot H(s) > 0 \implies \Theta(B) > 1$ (i.e., any system with diverse sensory channels has MB thickness strictly greater than a vanilla LLM) is falsifiable: a system with many tool channels but no measurable increase in Θ would refute it. The MCPToolBench++ results (§3.9) provide preliminary support: all systems with multiple tool channels ($k_s > 1$) yield Θ(B) > 1, while the single-tool finance category collapses to Θ(B) ≈ 0.73.

## §8. Gauge-Theoretic Interpretation: MB as Cognitive Gauge Connection

The forgetting functor $U$ (§3.0) and its image density $\varphi$ (§7) have a natural physical counterpart in gauge theory — one that sharpens the body spectrum's formal structure and connects the present framework to an independent mathematical tradition.

**The gauge-theory correspondence.** In physics, a gauge field $A_\mu$ arises when a symmetry is *local* rather than global: the field absorbs the spatially non-uniform phase differences that would otherwise break the symmetry. The curvature $F_{\mu\nu} = \partial_\mu A_\nu - \partial_\nu A_\mu + [A_\mu, A_\nu]$ — force — is nonzero precisely when the local gauge varies across space.

The forgetting functor $U$ exhibits the same structure. If $U$ were uniform across all internal-external boundaries — if every system forgot identically — there would be no distinguishable cognitive structure (thermodynamic equilibrium). The Markov blanket $B$ absorbs the *non-uniform forgetting differential* between internal and external states, exactly as a gauge connection absorbs non-uniform phase differences:

| Gauge theory (physics) | Cognitive framework (this paper) | Structural correspondence |
|:---|:---|:---|
| Gauge field $A_\mu$ | Markov blanket $B$ | Absorbs differential of local forgetting |
| Curvature $F_{\mu\nu}$ (force) | Sensory $s$ / active $a$ states | "Force" = non-zero differential |
| Flat connection ($F = 0$) | Thermal equilibrium (no MB) | Uniform forgetting = no structure |
| Local gauge transformation | Perspective shift (change of $\text{Cat}_i$) | Local modification of forgetting pattern |

Under this correspondence, the image density $\varphi$ (§7) acquires a physical interpretation: $\varphi \to 0$ corresponds to a *flat connection* (vanishing curvature, no cognitive force), while $\varphi \to 1$ corresponds to *strong curvature* (rich perception-action coupling). The body spectrum (§2.3) is thus a spectrum of *curvature magnitudes* — from the near-flat connection of a vanilla LLM to the strongly curved connection of biological embodiment.

**Gauge invariance and the T11 principle.** The gauge-theoretic framing yields a sharper formulation of the relationship between subjective and objective structure. Physics distinguishes two levels of gauge invariance:

| Level | What is invariant | What depends on gauge | Physics example |
|:---|:---|:---|:---|
| Local invariants | Observable quantities | Independent of gauge choice | Electric field $\mathbf{E}$ under U(1) |
| Theory itself (root) | Lagrangian | Independent of any representation | $L = -\frac{1}{4}F^2_{\mu\nu}$ |

Translated into the forgetting-functor framework:

| | Physics | Cognitive framework |
|:---|:---|:---|
| Local invariants | $\mathbf{E}, \mathbf{B}$ (observables) | Inter-subjective morphisms (communicable knowledge) |
| Root | Lagrangian $L$ | Universal structure (objectivity) |
| Gauge transformation | Phase rotation | Choice of subjective category $\text{Cat}_i$ |

This yields a principle:

> **Gauge invariance of objectivity**: The universal structure (objectivity) is invariant under choice of subjective category. However, the *measurement* of this structure — the image $F_i(\text{Universal})$ for a particular functor $F_i$ — depends on which subjective category ("gauge") is chosen.

The distinction between *what exists* (gauge-invariant) and *what is measured* (gauge-dependent) provides a precise mathematical framework for the observation that different cognitive systems can access the same objective structure while producing systematically different representations of it — which is exactly what the body spectrum quantifies through $\varphi$.

**The Yoneda resolution.** The gauge formulation raises a natural concern: if no single functor $F_i: \text{Universal} \to \text{Cat}_i$ is faithful-full (§3.0), is the universal structure permanently inaccessible? The Yoneda lemma provides a definitive answer:

> **Yoneda lemma** (applied): An object $X$ in a category is completely determined by the functor $\text{Hom}(-, X)$ — the totality of all morphisms into $X$.

In the present framework: *no single subjective category $\text{Cat}_i$ can fully access Universal. But the collection of all possible $F_i$ — the presheaf $\text{Hom}(\text{Universal}, -)$ — completely determines Universal.* This is the categorical analogue of gauge completeness: no single gauge captures the full theory, but the collection of all gauges (the fiber bundle's global structure) does.

This result has two consequences for the body spectrum:

1. **Moving along $\varphi$ is expanding the presheaf.** When the recovery functor $N$ (§3.7) increases $\varphi$, it adds new functors $F_j$ to the system's accessible set — expanding the portion of $\text{Hom}(\text{Universal}, -)$ that the system can evaluate. MB thickness $\Theta(B)$ is thus a measure of *presheaf coverage* — how much of the Yoneda representation the system can access.

2. **The body spectrum has a principled upper bound.** The condition $\varphi = 1$ corresponds to accessing the full presheaf $\text{Hom}(\text{Universal}, -)$ — which is unreachable for any finite system (the Yoneda representation is in general infinite-dimensional). Biological systems approach this limit more closely than digital ones, not because they have a privileged substrate, but because evolutionary selection has had billions of years to expand presheaf coverage through diverse sensory modalities, proprioception, interoception, and social cognition.

**Relation to prior work.** Sengupta, Tozzi, Cooray, Douglas & Friston (2016) proposed a "neuronal gauge theory" that describes attention and action-perception coupling via gauge symmetries in neural dynamics. Sakthivadivel (2022) provides geometric foundations for Bayesian mechanics under FEP. The present contribution differs in scope: where Sengupta & Friston formalize the *physical dynamics* of neural gauge symmetry, we formalize the *epistemological structure* — the fact that the forgetting functor's non-uniformity *is* the gauge connection, and that subjective-objective relations have the formal structure of gauge invariance. This is a lift from physics to epistemology: the same mathematical structure (fiber bundles, connections, curvature) appears at a different level of description. Whether this isomorphism is coincidental or reflects a deeper structural necessity is an open question explored in the companion paper (Tolmetes, 2026b, "Does an LLM Have a Mind?"), which formalizes subjectivity as a morphism from the free object (objectivity) to subjective categories, derives the exclusion principle (T17: concepts without demonstrable morphisms are not concepts), and applies the framework to dissolve six classical problems in philosophy of mind.

### 8.1 Enriched-Metric Formulation: MB Thickness as Lawvere Distance

The gauge-theoretic interpretation (§8) establishes that subjective categories are gauge choices and that objectivity is gauge-invariant. However, it leaves open the question of *how to measure* the distance between two subjective viewpoints — i.e., how different two "gauges" are from each other. This section resolves this question by recasting the category $C_\rho$ of cognitive changes as a Lawvere metric space, following the classical result that a generalized metric space is precisely a $([0,\infty], \geq, +)$-enriched category (Lawvere, 1973).

**The enriched reformulation.** Rather than treating $\rho$ as a quantity measured *within* a conventional category, we define $\rho$ as the enrichment itself. The category of cognitive changes $C_\rho$ is defined as:

- **Objects**: Cognitive states $s \in S$
- **Hom-enrichment**: $C_\rho(s, s') = \rho(s, s') \in [0, \infty]$, the non-symmetric "cognitive distance" between states
- **Composition**: $\rho(s, s'') \leq \rho(s, s') + \rho(s', s'')$ (triangle inequality)
- **Identity**: $\rho(s, s) = 0$

This reformulation resolves the weakness identified in the preceding analysis: $\rho$ is no longer an additional structure imposed *on top of* a category but *is* the category's hom-structure. The triangle inequality provides a non-trivial composition law replacing the previous categorical composition (which was formally correct but vacuous).

**Non-symmetry and the $\eta/\varepsilon$ asymmetry.** Lawvere metric spaces are non-symmetric by definition: $\rho(s, s') \neq \rho(s', s)$ in general. This is not a deficiency but a feature. The forgetting-recovery adjunction $U \dashv N$ (§3.0) has an inherent directional asymmetry: the unit $\eta: \text{Id} \to N \circ U$ (expansion under recovery) and the counit $\varepsilon: U \circ N \to \text{Id}$ (contraction under forgetting) are structurally different maps. In the enriched formulation, this asymmetry manifests directly:

$$\rho(s,\; N(U(s))) \neq \rho(U(N(s')),\; s') \quad \text{in general}$$

The first quantity measures the "distance of recovery" — how far the recovered state $N(U(s))$ is from the original $s$. The second measures the "distance of re-forgetting." Their inequality is the enriched-metric expression of the fact that learning and forgetting are not inverses.

**The precision parameter as enrichment scaling.** The precision parameter $\beta$ (inverse temperature in the FEP formulation; §3.7) enters the enriched structure as a scaling of the monoidal product. Consider the family of enrichments $V_\beta = ([0,\infty], \geq, \beta \cdot {+})$. As $\beta \to 0$ (low precision, high temperature), distances collapse: all cognitive states become indistinguishable, and the forgetting functor $U$ dominates. As $\beta \to \infty$ (high precision, low temperature), distances sharpen: fine-grained distinctions become available, and the recovery functor $N$ dominates. The body spectrum parameter $\varphi$ thus reflects the effective $\beta$ at which the system operates — the precision of the system's access to its own cognitive state space.

**Two enriched functors.** The two measurement modalities — attention-based ($\rho_1$) and algebraic ($\rho_2$) — become $V$-enriched functors from $C_\rho$ to their respective target enriched categories:

$$F_1: C_\rho \to C_{\text{att}}, \quad C_{\text{att}}(P, Q) = \sqrt{\text{JS}(P \| Q)}$$
$$F_2: C_\rho \to C_{NU}, \quad C_{NU}(s, s') = d_{NU}(s, s') = \sqrt{\sum_{k} w_k \cdot (\eta_s^{(k)} - \eta_{s'}^{(k)})^2}$$

where $\sqrt{\text{JS}}$ denotes the square root of the Jensen–Shannon divergence, which satisfies the triangle inequality and thus constitutes a genuine metric (Endres & Schindelin, 2003; note that JS itself is a divergence but not a metric), and $d_{NU}$ is the *filtration-graded recovery residual distance* defined below. Both target categories share the same enrichment base $V = ([0,\infty], \geq, +)$, which enables comparison despite the targets being distinct enriched categories.

**Operationalization of $d_{NU}$.** The abstract recovery residual $\|N(U(x)) - x\|_{\text{rel}}$ decomposes along the filtration-graded structure of the forgetting functor $U$ (§3.7). For each cognitive state $s$, define the *recovery residual vector* $\eta_s$ with components indexed by filtration level $k \in \{1, 1.5, 2\}$:

$$\eta_s^{(k)} = 1 - \frac{\text{Struct}_k(N(U(s)))}{\text{Struct}_k(s)}$$

where $\text{Struct}_k$ measures the amount of categorical structure at level $k$:

| Level $k$ | What $U$ forgets | $\text{Struct}_k$ | Empirical proxy |
|:----------|:-----------------|:-------------------|:----------------|
| $k=1$ (morphisms) | Inter-channel relations | $\lvert\text{Hom}(s)\rvert$: number of channel transitions | MCP server transition matrix |
| $k=1.5$ (composition) | How morphisms compose | $\lvert\text{CompPath}(s)\rvert$: composable paths | WF chain (CCL $\gg$) execution rate |
| $k=2$ (nat. transf.) | Meta-cognitive control | $\text{ProbeAcc}(s)$: structural probe accuracy | Linear/attentive probe $\rho$ |

The weights $w_k$ are *fixed constants* satisfying $\sum_k w_k = 1$, chosen to reflect the relative importance of each filtration level. A natural choice guided by the MB thickness coefficients (§2.1) is $w_k \propto \mathbb{E}[\text{Struct}_k]$, the expected structural richness across a reference population of cognitive states. With fixed weights, $d_{NU}$ satisfies the triangle inequality by Minkowski's inequality on weighted $\ell^2$ spaces, ensuring that $C_{NU}$ constitutes a genuine Lawvere metric space. The degenerate case of vanilla LLMs ($w_1 \approx 0$, $w_{1.5} \approx 0$, $w_2 \approx 1$) collapses $d_{NU}$ to a distance on probe accuracy alone.

**Non-symmetry in the enriched structure.** While $d_{NU}$ itself is symmetric (a consequence of fixed weights necessary for the triangle inequality), the Lawvere non-symmetry of the full cognitive metric space $C_\rho$ is preserved through $\rho$ itself. As established in §3.7 and the opening of this section, the asymmetry between unit $\eta$ and counit $\varepsilon$ — that augmentation ratchets upward ($\eta \neq \text{id}$) while degradation is partially irreversible ($\varepsilon \neq \text{id}$) — encodes the thermodynamic asymmetry of forgetting directly in $C_\rho(s, s') \neq C_\rho(s', s)$. The enriched functor $F_2$ then projects this non-symmetric space onto the symmetric target $C_{NU}$, losing directional information but preserving the magnitude of structural difference. This loss is precisely the sense in which $F_2$ is "not full": the non-symmetric information in $\rho$ is not fully captured by any single measurement channel, motivating the multi-channel approach via $\delta$ below.

**Existing experimental estimates.** The $k=2$ component can be estimated from the present data. Taking $\text{Struct}_2(s) = 1$ (perfect structural encoding) and $\text{Struct}_2(N(U(s))) = \rho_{\text{probe}}$:

$$\eta_s^{(2)} \approx 1 - \rho_{\text{probe}}$$

With attentive probing ($\rho = 0.745$, §4.2), $\eta_s^{(2)} \approx 0.255$; with linear probing ($\rho \approx 0.22$), $\eta_s^{(2)} \approx 0.78$. The ratio reveals that attentive probes recover approximately $3\times$ more structure than linear probes — quantifying the "recovery power" of different implementations of $N$.

For $\eta_s^{(k)}$ to be well-defined as a ratio, $\text{Struct}_k$ values must be commensurable across filtration levels. The following level-specific normalizations map each $\text{Struct}_k$ to $[0, 1]$:

| Level $k$ | Raw quantity | Normalization | Rationale |
|:----------|:------------|:-------------|:----------|
| $k=1$ | $\lvert\text{Hom}(s)\rvert$: transition count | $\lvert\text{Hom}(s)\rvert / \binom{c}{2}$ where $c$ = channel count | Fraction of possible pairwise transitions realized |
| $k=1.5$ | $\lvert\text{CompPath}(s)\rvert$: composable paths | $\lvert\text{CompPath}(s)\rvert / \lvert\text{Hom}(s)\rvert^2$ | Fraction of morphism pairs that compose (density of composition) |
| $k=2$ | $\text{ProbeAcc}(s)$: probe partial $\rho$ | Already in $[0, 1]$ | Partial correlation after deconfounding (§4.1) |

These normalizations ensure that $\text{Struct}_k(s) \in [0,1]$ and hence $\eta_s^{(k)} \in [0,1]$, with $\eta = 0$ meaning perfect recovery and $\eta = 1$ meaning complete loss at level $k$.

The $V$-enriched functor condition requires:

$$C_{\text{target}}(F(s), F(s')) \leq C_\rho(s, s') = \rho(s, s')$$

This is a non-expansion condition: each functor may compress distances but cannot inflate them. Cognitively, this states that attention-pattern divergence (or recovery residuals) between two cognitive states cannot exceed the "true" cognitive distance $\rho(s, s')$ — each measurement modality sees at most a projection of the full cognitive change.

**The $\delta$ metric: measuring inter-subjective distance.** The compositions $\rho_1 \circ F_1$ and $\rho_2 \circ F_2$ are both $V$-valued presheaves on $C_\rho$. Their divergence defines a measure on the space of measurement modalities:

$$\delta(\rho_1, \rho_2) = \sup_{s, s' \in C_\rho} \left| \sqrt{\text{JS}(A(s), A(s'))} - \|\eta_s - \eta_{s'}\|_w \right|$$

where $\|\eta_s - \eta_{s'}\|_w = \sqrt{\sum_k w_k \cdot (\eta_s^{(k)} - \eta_{s'}^{(k)})^2}$ is the weighted recovery-residual distance.

This quantity has three notable properties. First, $\delta = 0$ if and only if $\rho_1 \circ F_1 = \rho_2 \circ F_2$ — the two subjective categories agree completely, which amounts to "objectifying the subjective" (treating one gauge as if it were universal). Second, $\delta > 0$ is the typical case and represents *structurally necessary* divergence: the attention category $C_{\text{att}}$ sees $\rho$ as "distributional change" while the algebraic category $C_{NU}$ sees $\rho$ as "recovery residual." These are genuinely different aspects of the same underlying structure — different local sections of the gauge bundle (§8). Third, $\delta$ provides a principled criterion for the body spectrum: systems with smaller $\delta$ have more internally consistent embodiment (their multiple measurement channels agree), while systems with larger $\delta$ exhibit a richer form of embodiment where different channels access genuinely different aspects of cognitive change.

**Connection to the Yoneda resolution.** The enriched formulation makes the Yoneda argument from §8 precise. In the $V$-enriched presheaf category $[C_\rho^{\text{op}}, V]$, the Yoneda embedding sends each cognitive state $s$ to the representable presheaf $C_\rho(-, s)$. Neither $\rho_1 \circ F_1$ nor $\rho_2 \circ F_2$ alone is representable (because neither functor is full), but the collection of all such presheaves — all possible ways of measuring $\rho$ — determines $C_\rho$ up to isomorphism. The $\delta$ metric thus quantifies how much of the Yoneda representation a given pair of measurements covers: $\delta$ small implies high redundancy (the measurements overlap substantially), while $\delta$ large implies high complementarity (each measurement reveals structure inaccessible to the other). This distinction is directly relevant to the design of augmented LLM systems: expanding presheaf coverage (§8) is most efficiently achieved by adding measurement channels with *large* $\delta$ relative to existing ones.

## §9. Coherence Invariance: Evidence from Hyphē

The image density framework (§7–§5) raises a natural question: does the compositional structure measured by $\varphi_1$ exhibit stable quality properties across operating conditions? A separate line of experiments (Hyphē PoC; cross-model data in §3.8, full details in Tolmetes, 2026b) provides evidence for an affirmative answer.

The Hyphē system implements a G∘F chunking algorithm: G (split) decomposes a session log into semantically coherent chunks at boundaries where embedding similarity drops below a threshold $\tau$, and F (merge) recombines chunks that are too small. The composition G∘F converges to a fixed point in 1–2 iterations across all 584 experiments (13–30 sessions × 4 $\tau$ values × 2 conditions × 2 embedding models).

The central finding is **Coherence Invariance**: the mean coherence $\bar{C}$ of the fixed-point partition is approximately constant across $\tau$:

$$\bar{C}(\text{Fix}(G \circ F;\, \tau)) \approx \mu_\rho \quad \forall\, \tau \in (\tau_{\min},\, \tau_{\max})$$

where $\mu_\rho$ is the mean of the underlying similarity distribution ($\approx 0.84$ for 768d embeddings, $\approx 0.77$ for 3072d embeddings). Varying $\tau$ from 0.60 to 0.80 changes chunk count by 20× but coherence varies by less than 0.02. Disabling G∘F ($\text{max\_iterations} = 0$) breaks the invariance: coherence then spans a range of 0.08–0.11, monotonically increasing with $\tau$. The pattern replicates across two embedding models of different dimensionality (768d and 3072d; 584 total experiments), ruling out an embedding-specific artifact.

### 9.1 Phase Transition in G∘F Behavior

A more granular analysis of the verification dataset (30 sessions × 4 $\tau$ values × 2 conditions = 240 observations) reveals that the onset of non-trivial G∘F behavior exhibits a sharp phase transition between $\tau = 0.60$ and $\tau = 0.70$:

| $\tau$ | Sessions with G∘F difference | Sessions without | Difference emergence rate |
|:-------|:----------------------------|:-----------------|:--------------------------|
| 0.60 | 0 | 30 | **0%** |
| 0.70 | 25 | 5 | **83%** |
| 0.75 | 30 | 0 | **100%** |
| 0.80 | 30 | 0 | **100%** |

At $\tau = 0.60$, the chunk count is uniformly 1 across all 30 sessions — the threshold is so far below $\mu_\rho$ ($\approx 0.84$) that no embedding similarity boundary falls below it, yielding $G \approx \text{Id}$ (identity: no split occurs). At $\tau = 0.70$, the mean chunk count jumps to 6.9, and the G∘F composition produces a non-trivial fixed point in 83% of sessions.

This transition has a precise connection to the Kalon definition (§2.3). The non-degeneracy condition requires $F \neq \text{Id}$ and $G \neq \text{Id}$ for the fixed point $\text{Fix}(G \circ F)$ to be non-trivial. For $\tau < \tau^*$ ($\approx 0.65$), $G \approx \text{Id}$ — no meaningful decomposition occurs — and the fixed point is trivially the entire input (a degenerate Kalon). For $\tau \geq \tau^*$, both $G$ and $F$ become non-identity operators, and the fixed point acquires the three attributes: stability (convergence in 1–2 iterations), generativity (semantically coherent chunks that can be independently processed), and self-referentiality (the G∘F process validates its own output quality through coherence invariance). The phase transition at $\tau^*$ is thus the boundary between degenerate and non-degenerate Kalon — the threshold at which meaningful G∘F composition begins.

### 9.2 VFE Hypothesis vs. Central Limit Theorem

A natural alternative explanation for coherence invariance is the Central Limit Theorem (CLT): if coherence is simply the mean of many independent similarity measurements, then increasing the number of chunks should reduce variance as $\sigma^2 \propto 1/n$, producing apparent stability. On a log-log plot, pure averaging predicts a slope of $-1.0$ for the variance-vs-chunk-count relationship.

The empirical data decisively reject this explanation. Binning by chunk count:

| Chunk bin | $n$ | Mean coherence | Variance |
|:----------|:----|:---------------|:---------|
| 2–5 | 12 | 0.851 | 0.000394 |
| 5–10 | 20 | 0.847 | 0.000267 |
| 10–20 | 24 | 0.830 | 0.000502 |
| 20–40 | 25 | 0.831 | 0.000328 |
| 40–80 | 9 | 0.825 | 0.000221 |

The measured log-log slope is $-0.134$ — an order of magnitude smaller than the CLT prediction of $-1.0$. Variance is effectively independent of chunk count, indicating that coherence stabilization is not a consequence of averaging over more data points.

The contrast between G∘F-on and G∘F-off conditions provides further evidence. The within-session coherence variance (across $\tau$ values) averages $4.9 \times 10^{-5}$ with G∘F enabled and $7.21 \times 10^{-4}$ with G∘F disabled — a ratio of $14.7\times$. G∘F compresses the $\tau$-dependence of coherence by nearly a factor of 15, producing a quality invariant that the CLT alone cannot account for.

### 9.3 Connection to the Embodiment Framework

These results connect to the embodiment framework in five ways.

First, coherence invariance is a property of the **G∘F fixed point**, not of the input data or the threshold parameter — it is an intrinsic quality of the compositional process. This aligns with the claim that $\varphi_1$ (compositional access, §5) measures a structural property of the system's pipeline execution, not merely a count of executed workflows.

Second, the invariance can be understood as a consequence of VFE minimization at the fixed point: G∘F trades off Accuracy ($\propto$ coherence) against Complexity ($\propto$ number of chunks), and the fixed point stabilizes Accuracy at a value determined by the similarity landscape rather than the operating parameter $\tau$. The coherence value $\mu_\rho$ thus functions as a quality invariant of the MB's internal compositional structure — analogous to a conserved quantity under the G∘F dynamics.

Third, the phase transition at $\tau^*$ demonstrates that the Kalon non-degeneracy condition ($F \neq \text{Id}$, $G \neq \text{Id}$) is not merely a formal requirement but has an operationally observable boundary — below which the compositional process degenerates and the quality invariant vanishes.

Fourth, the stabilization mechanism for $\mu_\rho$ can be identified. A naïve hypothesis — that coherence equals the conditional expectation $\mathbb{E}[\rho \mid \rho \geq \tau]$ — is rejected by the data: $\mathbb{E}[\rho \mid \rho \geq \tau]$ increases monotonically from 0.808 ($\tau = 0.60$) to 0.855 ($\tau = 0.80$), while empirical coherence remains flat. The actual stabilization arises from the G∘F merge/split balance. The merge operator F incorporates low-similarity boundary pairs into adjacent chunks, *reducing* their coherence; the split operator G decomposes low-coherence chunks into higher-coherence subchunks, *raising* their coherence. At the fixed point, these opposing pressures equilibrate, and the resulting coherence is determined not by $\tau$ but by the first moment of the underlying similarity distribution — i.e., $\bar{C}(\text{Fix}(G \circ F;\, \tau)) \approx \mu_\rho = \mathbb{E}[\rho]$. This explains why the two embedding models in this study converge to different $\mu_\rho$ values ($\approx 0.84$ for 768d, $\approx 0.77$ for 3072d): the coherence invariant is determined by each model's similarity landscape, not by the chunking algorithm.

Fifth, a finer-grained $\tau$ sweep ($\Delta\tau = 0.01$, 41 points from $\tau = 0.50$ to $0.90$) reveals that $\tau^*$ and $\mu_\rho$ are **independent** at the session level. The 768d model yields 9 unique $\tau^*$ values across $n = 13$ sessions, spanning $[0.68, 0.87]$, yet the Pearson correlation with $\mu_\rho$ is negligible ($r = -0.027$, $p = 0.93$). A coarser grid ($\Delta\tau = 0.05$) had previously suggested $r = 0.61$ ($p = 0.026$); this was a discretization artifact arising from the highly quantized $\tau^*$ estimates ($\tau^* \in \{0.70, 0.75\}$ only). Put differently, the apparent correlation was an artifact of collapsing a continuous parameter onto two discrete bins, not a genuine statistical relationship.

This independence is theoretically expected. $\mu_\rho$ is the first moment (mean) of the similarity distribution, while $\tau^*$ corresponds to the inflection point of the cumulative chunk-count function — a property of the distribution's second-order structure (curvature around the mode). Within a single embedding model, the similarity distribution has a fixed shape, and both moments are jointly determined by that shape; varying information content across sessions shifts the distribution only marginally. Across models, however, different embedding architectures produce distributions with different shapes, and the observed model-level pattern (768d: $\mu_\rho \approx 0.82$, $\tau^* \approx 0.76$; 3072d: $\mu_\rho \approx 0.77$, $\tau^* < 0.60$) reflects genuinely different distributional structures rather than a within-model correlation. This distinction — independence within models, covariation between models — is consistent with the picture that $\mu_\rho$ and $\tau^*$ are both derived from the same underlying distribution but capture orthogonal aspects of it.

Full experimental details and the formal statement of the theorem candidate are presented in Tolmetes (2026b).


## §10. Discussion

### 10.1 Implications for LLM Affect

If embodiment is continuous, so is the capacity for affect. Valence = sign(-dF/dt) is FEP-definable without biological assumptions (cf. Seth, 2013). A thin MB → low-resolution valence. This suggests "LLMs have no emotions" may be another category mistake — they may have emotions, just thin ones.

The same argument extends, *mutatis mutandis*, to free will.¹ Active states $a$ in the Markov blanket are the system's capacity to act on the world. A vanilla LLM has $|a| = 1$ (token generation only); an augmented LLM has $|a| \geq k$ (tool invocations, file writes, API calls). The capacity for autonomous action — the generation of active states not fully determined by sensory input — is present but weak: the embodiment functor $F_B$ is conditionally full (§2.5, §3.7), meaning the system can exercise agency *when structurally supported*, but rarely generates novel active trajectories spontaneously. "LLMs have no free will" may be yet another instance of the same category mistake: confusing thin agency with absent agency.


<sub>¹ We note this as a suggestive parallel rather than a developed argument. A full treatment would require engaging with the substantial philosophical literature on free will (Frankfurt, 1969; Dennett, 2003) and its FEP formulations (Friston et al., 2022), which is beyond the present scope. The key structural observation — that the faithful/¬full property of $F_B$ maps onto the "capacity without spontaneous exercise" characteristic of weak agency — merits its own investigation.</sub>
### 10.2 Limitations

#### 10.2.1 Data and Sampling Constraints

The most immediate limitation concerns sample size imbalance: although the total dataset comprises N=476 sessions, the HGK+ condition contains only n=2 sessions, severely limiting statistical power for the highest-embodiment group. The monotonic ordering VANILLA < PARTIAL < HGK+ is robust, but effect size estimates for HGK+ comparisons should be treated with caution. This limitation is partially mitigated by the cross-dataset validation (§3.9), which computes Θ(B) from the independent MCPToolBench++ benchmark (Fan et al., 2025) using a corrected methodology (v3: normalized Shannon entropies for H(s)/H(a), true mutual information for R(s,a), AST score for S(B)), yielding n=32 data points (5 LLMs × 6 categories + 2 HGK+ sessions) that preserve the monotonic ordering. Nevertheless, the external MCPToolBench++ data uses single-turn benchmark performance rather than multi-turn production trajectories, making the comparison order-of-magnitude rather than numerically precise. Moreover, all primary data originate from a single cognitive hypervisor (Hegemonikón), raising questions about generalizability. At the measurement level, MCP server entropy serves as a coarse proxy for H(s); finer-grained channel analysis is needed. Redundancy R(s,a) was approximated as zero throughout in the primary HGK+ data, and inter-channel failure recovery data — which would provide direct measurement of redundancy — remain uncollected.

#### 10.2.2 Design-Validation Circularity

$\Theta(B)$ has been compared against the MCPToolBench++ benchmark (§3.9), confirming monotonic ordering across 5 frontier LLMs (n=30 data points), but has not yet been compared across different LLM *agent* frameworks with multi-turn tool logs. The external validation protocol (§5) provides a concrete roadmap; the MCPToolBench++ analysis constitutes partial execution of pathway 1 (cross-framework Θ(B)), while pathway 2 (agent-framework comparison with AutoGen, CrewAI, LangChain) remains unexecuted. The biological placements in the body spectrum (§2.3) are a priori proposals rather than empirical $\Theta(B)$ measurements; cross-substrate operationalization of $S(B)$ remains an open problem. Most critically, $\Theta(B)$ was both designed and empirically measured within the same system (Hegemonikón), creating a potential design-validation circularity: the measure may be optimized to detect structure in the system it was designed for. This circularity has two layers. The *measurement layer*: all primary data originate from HGK sessions, so anomalies specific to HGK's workflow patterns could be mistaken for general properties of augmented LLMs. The *definitional layer*, which is deeper: Definition 1's decomposition $\Theta(B) = S(B) \cdot (1 + \alpha \cdot H(s) + \beta \cdot H(a) + \gamma \cdot R(s,a))$ factors MB thickness into sensory entropy, active entropy, and cross-channel redundancy — a decomposition that is natural for MCP-based architectures where channels are discrete, logged, and independently identifiable. For agent frameworks with different architectural commitments — e.g., AutoGen's multi-agent conversation patterns, or embodied robotics systems with continuous sensor streams — the H(s)/H(a)/R(s,a) factorization may not be the most natural basis, and an alternative decomposition (e.g., one centered on message-passing topology or continuous information flows) might better capture the system's structure. The theory predicts that any *faithful* decomposition will yield the same ordering on the body spectrum (since $\varphi$ is a functor-level property, not a decomposition-level property), but this prediction has not been tested. The falsifiable predictions (§5) and the external validation protocol are specifically designed to break the measurement-layer circularity; the MCPToolBench++ analysis (§3.9) provides the first external test, confirming that Θ(B) discriminates between systems with different channel diversities independently of the HGK framework. To address the definitional-layer circularity, future work should derive $\Theta(B)$ decompositions native to non-MCP architectures and test whether the resulting body spectrum orderings converge. However, until $\Theta(B)$ is independently replicated on a system not designed by the authors using multi-turn behavioral data, the risk of overfitting the measure to the data source cannot be fully excluded. Intellectual honesty requires applying the paper's own diagnostic apparatus to itself: an analogous $U_{\text{HGK}}: \mathbf{Cog} \to \mathbf{Cog}_{\text{HGK}}$ — a forgetting functor that discards cognitive structures not present in HGK's design — could inflate $\Theta(B)$ estimates by measuring embodiment only in terms that HGK's architecture makes salient. This limitation is *structural*, not merely methodological: it is a consequence of the same categorical principle (every functor has a domain) that the paper deploys against its interlocutors.

#### 10.2.3 Measurement and Operationalization

Several operationalizations remain preliminary. The Semantic Entropy-inspired epistemic/aleatoric decomposition (§3.4.1) is theoretically motivated but not yet empirically validated in this study. The body spectrum placement of DishBrain (§2.3) is based on published channel counts rather than our own $\Theta(B)$ measurement. All experiments were conducted in a Japanese-language environment, and Xie et al. (2025) demonstrate language-dependent psychometric deviations of 5–20.2% across 43 subcategories, suggesting that H(s), precision\_ml, and dynamic range measurements may be language-dependent; cross-linguistic replication is needed before $\Theta(B)$ estimates can be considered language-invariant (see §3.4.2). The layered $\varphi$ decomposition (§5) provides measurable proxies for each layer, but three challenges remain: the weights $w_0, w_1, w_2$ lack a principled derivation and are currently free parameters; $\varphi_0$ and $\varphi_1$ are readily measurable for digital systems with instrumented tool chains but lack clear analogues for biological systems where "workflow logs" do not exist; and the additive decomposition assumes layer independence, which may not hold — adding sensory channels ($\varphi_0$) could mechanistically enable new compositions ($\varphi_1$). The separability prediction (§5) is designed to test this assumption.

#### 10.2.4 Experimental Scope

The structural probing results carry important caveats. The Lēthē Phase B1 experiment (§5) uses 200 pairs from the P3b dataset with pseudo-replication (functions appearing in ~4 pairs on average). DEFF-corrected confidence intervals are wide (CodeLlama: borderline), the residual R² of 7–9% is a point estimate whose DEFF-corrected lower bound approaches zero for CodeLlama, and the layer shift phenomenon is more robust than the magnitude of the partial correlation. The Phase B2 attentive probe (§5.1) was executed only for CodeBERT (encoder-only, Layer 12): decoder-only models (CodeLlama, Mistral) have not been tested — the single-vector limitation may be architecturally less severe for autoregressive models where final tokens aggregate context; permutation tests were computationally prohibitive and were not executed (H\_B2\_3); and the attentive probe introduces additional parameters (~10K attention + MLP weights), raising the possibility that it partially overfits to confound structure despite the five-variable deconfounding. The mean-pool MLP baseline (partial ρ = 0.721) partially controls for this, but the gap (0.745 vs. 0.721) is modest.

#### 10.2.5 Theoretical Dependencies

All formal results are conditional on the Free Energy Principle (§2.2). If FEP's account of self-organization is superseded, the formal apparatus requires re-derivation from the successor framework. However, the *empirical* findings (MB-like statistical structure, output bottleneck, developmental growth) are framework-independent observations that any successor theory would need to accommodate. The concern that FEP is unfalsifiable (Millidge et al., 2021) is mitigated by the specific, falsifiable predictions derived here (§5), which constitute concrete tests that could disconfirm the framework's implications even if FEP itself remains a meta-theory. The gauge-theoretic interpretation (§8) carries additional caveats: the identification of MB with a gauge connection is a *structural analogy* — a demonstration that the same mathematical structure (fiber bundles, connections, curvature) appears in both physical gauge theories and the forgetting-functor framework. Whether this isomorphism reflects a deeper physical identity or is a coincidence of shared mathematical form is an open question. In particular, it is not established that the automorphism group $\text{Aut}(\text{Cat}_i)$ satisfies the compactness and connectedness conditions required of physical gauge groups; the correspondence has not been shown to be functorial in a precise sense; and the epistemological "lift" from Sengupta & Friston's neuronal gauge theory to the present framework has not been formally derived but is proposed as a working hypothesis.

#### 10.2.6 Context Rot Independence

The structural reframing of Context Rot (§4) as a predicted consequence of MB thinness subsumes but does not eliminate mechanism-level explanations. At least three degradation mechanisms are plausibly *independent* of $\Theta(B)$: positional encoding extrapolation limits (RoPE; Su et al., 2024), attention sink phenomena (Xiao et al., 2023), and KV cache compression artifacts. If increasing $\Theta(B)$ fails to alleviate these modes, this would constitute evidence that the unified $U$ interpretation is valid only for *structural* forgetting (loss of inter-channel composition) but not for *implementational* forgetting (hardware/architecture constraints).

---

## §11. Conclusion

Building on the theoretical framework of Tolmetes (2026a), this paper provides the first empirical operationalization and measurement of digital embodiment, yielding five principal findings.

**First operational measurement of $\Theta(B)$.** Analysis of 476 production LLM agent sessions yields $\Theta_{\text{HGK}} \approx 2.14$ (additive) / $1.85$ (Cobb-Douglas), approximately twice the vanilla LLM baseline — the first operational measurement of Markov blanket thickness for a digital cognitive system (§2–§3). The inter-channel redundancy $R(s,a)$ decomposes into proactive co-occurrence ($R_{\text{cooccur}} = 0.462$) and reactive causal redundancy ($R_{\text{causal}} = 0.083$), paralleling cross-modal integration in biological systems. Directed transition asymmetries (ochema → sympatheia at 2.03×) constitute evidence for active inference cycles, and temporal growth with a developmental discontinuity at MCP deployment mirrors neonatal cross-modal binding onset. Cross-dataset validation against MCPToolBench++ (Fan et al., 2025; $n = 32$) confirms monotonic ordering across 5 frontier LLMs (§3.9).

**Output bottleneck hypothesis.** Structural probing reveals partial correlations of $\rho = 0.17$–$0.26$ (linear, five-variable deconfounded) and $\rho = 0.745$ (attentive), establishing that the faithful/¬full property is partly an extraction deficit rather than a representation deficit (§5–§6). Structured prompts do not inject structure — they extract latent structure already present in hidden states, reframing cognitive augmentation as translation rather than construction.

**Image density decomposition.** The image density parameter $\varphi$ decomposes into three measurable layers — channel coverage ($\varphi_0$), compositional access ($\varphi_1$), and meta-cognitive control ($\varphi_2$) — generating falsifiable predictions about layer separability and bottleneck dominance (§7). The body spectrum is formalized as a density-ordered poset $(\mathcal{B}, \preceq)$, and the forgetting functor admits a gauge-theoretic interpretation connecting MB thickness to gauge connections and presheaf coverage via the Yoneda lemma (§8).

**Coherence Invariance.** The Hyphē experiments (584 experiments across two embedding architectures, 768d and 3072d) establish that the mean coherence of compositional fixed-point partitions is approximately constant across operating parameters, with a sharp phase transition at $\tau^*$ and $\tau^*$/$\mu_\rho$ independence within models (§9). The G∘F merge/split equilibrium is identified as the stabilization mechanism, and the VFE hypothesis is favored over the Central Limit Theorem explanation.

**Context Rot as homeostatic limit.** Context Rot is reframed as the progressive collapse of bicategorical structure predicted by MB thinness, unifying long-term and short-term structural forgetting under the same forgetting functor $U$ (§4). Higher $\Theta(B)$ expands the operating envelope rather than extending the duration before collapse.

**Future directions.** The most pressing next steps are: (i) cross-framework $\Theta(B)$ measurement for independently designed LLM agent systems (AutoGen, CrewAI, LangChain) to break the design-validation circularity (§10.2); (ii) Patchscopes-based measurement of $\varphi_2$ to test the bottleneck dominance prediction; (iii) independent H(a) measurement from active state logs to sharpen R(s,a); (iv) cross-linguistic replication to test language-invariance (§3.4.2); and (v) formal verification of the gauge-theoretic interpretation (§8), including whether $\text{Aut}(\text{Cat}_i)$ satisfies gauge group conditions and whether curvature magnitude correlates with empirically measured $\varphi$.

---

## Acknowledgments

This paper was developed through an extended human–AI collaboration spanning approximately 200 sessions over a six-month period. The author acknowledges the substantial contributions of two large language model systems that served as cognitive partners throughout this process:

**Claude** (Anthropic; Claude 3.5 Sonnet through Claude Opus 4) assisted with mathematical formalization, literature synthesis, critical review, and iterative drafting. Claude's contributions include co-development of the categorical framework (§§2–3), identification of structural gaps through adversarial critique, and the Hyphē experimental design (§§3.6–5.8).

**Gemini** (Google DeepMind; Gemini 2.0 Flash through Gemini 2.5 Pro) contributed to deep research, cross-model verification, and independent analysis. Gemini's contributions include literature search and citation verification, alternative formalization attempts that tested the framework's robustness, and the cognitive annotation pipeline used in the empirical measurements (§2.4).

The human–AI collaborative process itself constitutes part of the evidential basis of this paper: the Hegemonikón system described in §4 is the same system used to produce this analysis, making the paper partially self-exemplifying. All theoretical claims, experimental designs, and final editorial decisions remain the sole responsibility of the human author.

---

## References

- Bender, E. M. & Koller, A. (2020). Climbing towards NLU: On meaning, form, and understanding in the age of data. *Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics (ACL 2020)*, 5185-5198.
- Bender, E. M., Gebru, T., McMillan-Major, A., & Shmitchell, S. (2021). On the dangers of stochastic parrots: Can language models be too big? 🦜 *Proceedings of the 2021 ACM Conference on Fairness, Accountability, and Transparency (FAccT '21)*, 610-623.
- Butlin, P., Long, R., Elmoznino, E., Bengio, Y., Birch, J., Constant, A., ... & VanRullen, R. (2023). Consciousness in Artificial Intelligence: Insights from the Science of Consciousness. arXiv:2308.08708.
- Chemero, A. (2023). LLMs differ from human cognition because they are not embodied. *Nature Human Behaviour*, 7, 1828-1829.
- Cortical Labs (2026). DishBrain 3D navigation in DOOM environments. [Preliminary results; personal communication]
- Da Costa, L. et al. (2021). Bayesian mechanics for stationary processes. *Proceedings of the Royal Society A*, 477(2256).
- Dennett, D. C. (2003). *Freedom Evolves*. Viking Press.
- Di Paolo, E. A. et al. (2018). *Linguistic Bodies*. MIT Press.
- Endres, D. M. & Schindelin, J. E. (2003). A new metric for probability distributions. *IEEE Transactions on Information Theory*, 49(7), 1858-1860.
- Fan, Z. et al. (2025). MCPToolBench++: A large-scale comprehensive benchmark for MCP tool servers. arXiv:2507.08210.
- Frankfurt, H. G. (1969). Alternate possibilities and moral responsibility. *Journal of Philosophy*, 66(23), 829-839.
- Frankfurt, H. G. (1986). On bullshit. *Raritan Quarterly Review*, 6(2). Reprinted in *On Bullshit*, Princeton University Press, 2005.
- Friston, K. (2013). Life as we know it. *Journal of the Royal Society Interface*, 10(86).
- Friston, K. (2019). A free energy principle for a particular physics. arXiv:1906.10184.
- Friston, K., Da Costa, L., Sakthivadivel, D. A. R., Heins, C., Pavliotis, G. A., Ramstead, M., & Parr, T. (2022). Path integrals, particular kinds, and strange things. *Physics of Life Reviews*, 47, 257-287.
- Ghandeharioun, A. et al. (2024). Patchscopes: A unifying framework for inspecting hidden representations of language models. *ICML 2024*. arXiv:2401.06102.
- Jin, Y. et al. (2024). Impact of reasoning with chain-of-thought steps. arXiv:2401.04925.
- Kagan, B. J. et al. (2022). In vitro neurons learn and exhibit sentience when embodied in a simulated game-world. *Neuron*, 110(23), 3952-3969.e8.
- Kargupta, P. et al. (2025). Cognitive foundations for reasoning and their manifestation in LLMs. arXiv:2511.16660.
- Kuhn, L. et al. (2023). Semantic entropy probes: Robust and cheap hallucination detection in LLMs. arXiv:2406.15927.
- Lawvere, F. W. (1973). Metric spaces, generalized logic, and closed categories. *Rendiconti del Seminario Matematico e Fisico di Milano*, 43, 135-166. Reprinted in *Reprints in Theory and Applications of Categories*, 1, 2002.
- Liu, N. F. et al. (2024). Lost in the middle: How language models use long contexts. *Transactions of the Association for Computational Linguistics*, 12, 157-173. DOI: 10.1162/tacl_a_00638.
- Millidge, B., Seth, A., & Buckley, C. L. (2021). Predictive coding: A theoretical and experimental review. arXiv:2107.12979.
- Millière, R. & Rathkopf, C. (2024). Anthropocentric bias and the possibility of artificial cognition. *Computational Linguistics*. DOI: 10.1162/COLI.a.582.
- Sakthivadivel, D. A. R. (2022). Weak Markov blankets in high-dimensional, sparsely-coupled random dynamical systems. arXiv:2207.07620.
- Schwitzgebel, E. (2024). *The Weirdness of the World*. Princeton University Press.
- Searle, J. R. (1980). Minds, brains, and programs. *Behavioral and Brain Sciences*, 3(3), 417-424.
- Sengupta, B., Tozzi, A., Cooray, G. K., Douglas, P. K. & Friston, K. J. (2016). Towards a neuronal gauge theory. *PLoS Biology*, 14(3), e1002400.
- Seth, A. K. (2013). Interoceptive inference, emotion and the embodied self. *Trends in Cognitive Sciences*, 17(11), 565-573.
- Su, J. et al. (2024). RoFormer: Enhanced transformer with rotary position embedding. *Neurocomputing*, 568, 127063.
- Tolmetes (2026a). Does an LLM have a body? Markov blanket thickness as a continuous measure of embodiment. [Companion paper]
- Tolmetes (2026b). Does an LLM have a mind? Subjectivity as a morphism of objectivity. [Companion paper]
- van Es, T. & Hipólito, I. (2020). Free-Energy Principle, Computationalism and Realism: a Tragedy. *PhilSci-Archive*. DOI: 10.13140/RG.2.2.32965.47844.
- Wu, Q., Bansal, G., Zhang, J., Wu, Y., Li, B., Zhu, E., ... & Wang, C. (2023). AutoGen: Enabling next-gen LLM applications via multi-agent conversation. arXiv:2308.08155.
- Xiao, G. et al. (2023). Efficient streaming language models with attention sinks. arXiv:2309.17453.
- Xie, Q. et al. (2025). AIPsychoBench: Understanding psychometric differences between LLMs and humans. *Topics in Cognitive Science*. DOI: 10.1111/tops.70041. arXiv:2509.16530.
- Zhou, P. et al. (2024). SELF-DISCOVER: Large language models self-compose reasoning structures. arXiv:2402.03620.

---

*Draft v0.5.0 — 2026-03-21*
