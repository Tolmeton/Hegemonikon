# Blind participant response — Gemini API gemini-3.1-flash-lite-preview

- timestamp_utc: `20260501T132107Z`
- prompt_file_inside_container: `/input/prompt.md`
- working_directory_inside_container: `/work`

## Response

As an independent theoretical analyst, I have synthesized the core decompositions found within the Free Energy Principle (FEP) and active inference literature. These represent the fundamental "splits" used to render the intractable problem of Bayesian inference tractable.

### 1. Table of Distinct Decompositions

| Label | Object/Structure | Contrast/Opposition | Literature Anchor | Category | Confidence | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Variational Split** | Evidence Lower Bound (ELBO) | Accuracy vs. Complexity | Friston et al. (2006) | Algebraic | High | Independent |
| **Markovian Cut** | Markov Blanket | Internal vs. External states | Friston (2013) | Boundary | High | Independent |
| **Active Split** | Expected Free Energy ($G$) | Epistemic vs. Pragmatic value | Friston et al. (2015) | Policy-functional | High | Independent |
| **Precision Weighting** | Precision ($\pi$) | Sensory evidence vs. Prior belief | Feldman & Friston (2010) | Precision | High | Internal |
| **Hierarchical Depth** | Generative Model | Top-down predictions vs. Bottom-up errors | Friston (2008) | Hierarchical | High | Independent |
| **Temporal Horizon** | Policy sequence | Immediate vs. Future consequences | Friston et al. (2017) | Temporal | Medium | Derived |
| **Affective Split** | Interoceptive inference | Allostatic set-points vs. Sensory input | Barrett & Simmons (2015) | Interoceptive | Medium | Domain-ext. |
| **Active/Passive** | Perception vs. Action | Changing beliefs vs. Changing world | Friston (2010) | Action/Inference | High | Independent |

---

### 2. Synthesis of Abstract Dimensions

The decompositions above suggest that the FEP operates across four fundamental abstract dimensions:

1.  **The Information-Theoretic Dimension (Accuracy vs. Complexity):** This is the foundational algebraic split. It defines the "cost" of existence as a trade-off between explaining sensory data and minimizing the complexity of the internal model.
2.  **The Structural-Boundary Dimension (Internal vs. External):** This dimension defines the "self" through the Markov blanket. It establishes the operational necessity of a boundary that separates the agent from the environment, allowing for the definition of "states" that are conditionally independent.
3.  **The Teleological Dimension (Epistemic vs. Pragmatic):** This dimension splits the agent’s objective function. The agent must simultaneously reduce uncertainty (epistemic) and satisfy homeostatic requirements (pragmatic). This is the core of active inference.
4.  **The Hierarchical-Temporal Dimension (Scale vs. Horizon):** This dimension organizes the generative model into levels of abstraction and time-scales. It suggests that the agent’s "depth" is a function of its ability to integrate information across different temporal and spatial granularities.

---

### 3. Missing or Weak Dimensions

*   **The Social/Collective Dimension:** While the literature discusses "shared" generative models, there is no formal, universally accepted decomposition for the "Collective Markov Blanket" or the split between individual and group-level variational free energy. The literature is currently exploring this, but it remains a weak dimension.
*   **The Computational-Resource Dimension:** Most FEP literature assumes an "ideal" agent. There is a lack of a formal decomposition that splits the *mathematical* free energy from the *physical/metabolic* cost of the computation itself (i.e., the energy required to perform the inference).
*   **The Non-Equilibrium Steady State (NESS) vs. Transient Dynamics:** While the FEP is anchored in NESS, the literature often struggles to clearly decompose the transition from transient learning (model building) to steady-state maintenance (model exploitation). The distinction between "learning" and "inference" is often blurred in the math.
*   **The Ontological/Structural Plasticity Dimension:** Most models assume a fixed generative model structure. There is no standard decomposition for the *evolution* of the model structure itself (i.e., how the Markov blanket changes over time), which remains a significant theoretical gap.

***

*Note on sources:* The anchors provided refer to the foundational papers by Karl Friston and colleagues (e.g., *NeuroImage* 2006, *Journal of the Royal Society Interface* 2013, *PLOS Biology* 2015). The "Affective Split" is anchored in the work of Lisa Feldman Barrett, which integrates interoception into the FEP framework; this is considered a domain-specific extension rather than a core mathematical axiom of the FEP itself.
