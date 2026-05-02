# ROM 2026-04-03: Cognitive Homeostasis Paradigm Collapse

## Discovery
The hypothesis that agents succeed by maintaining a constant cognitive load (low `t_gini` / "Cognitive Homeostasis") is **FALSE**. It was a statistical illusion caused by reverse causality.

## Evidence (Forward Prediction Test)
If low Gini drives success, it should be visible *before* the outcome is decided. We split trajectories in half and measured `early_t_gini`:

1. **N=500 Verified (Total Trajectory):** r = -0.19 (BF10 = 507.7) -> *Decisive correlation*
2. **N=500 Verified (First Half Only):** r = 0.10 (BF10 = 0.7) -> *Correlation completely disappears (flips slightly positive but anecdotal).*
3. **N=300 Lite (First Half Only):** r = -0.008 (BF10 = 0.07) -> *Substantial evidence for NO correlation.*

## Conclusion
High `t_gini` (variance in thought length) is merely a **post-hoc symptom** of an agent falling into an error loop later in the trajectory. When an agent fails, it typically encounters a stubborn bug near the end, causing it to generate massive, repetitive `thought` blocks trying to fix it, which spikes the Gini coefficient. 

`t_gini` is NOT an indicator of poor working memory or a lack of forgetfulness. It is simply an indicator that the agent "got stuck".

**Paradigm Pivot:** We must accept this Null Result. Gini-coefficient over trajectory lengths cannot be used to prove the utility of oblivion. Paper IV's focus must pivot from "proving the theorem" to "reporting the failure of macroscopic trajectory variance as a cognitive metric" and exploring alternative operationalizations of oblivion.