"""
BBH eta-squared estimation (lightweight - numpy only)
rho_est = eta^2_prompt from Suzgun et al. (2022) BBH data
"""
import math

# PaLM 540B: [AO, CoT] accuracy (%)
palm = [
    ("boolean_expressions", 83.2, 80.0),
    ("causal_judgement", 57.8, 62.0),
    ("date_understanding", 41.6, 67.6),
    ("disambiguation_qa", 38.8, 63.6),
    ("dyck_languages", 16.4, 13.6),
    ("formal_fallacies", 52.4, 65.6),
    ("geometric_shapes", 11.6, 52.4),
    ("hyperbaton", 54.0, 76.0),
    ("logical_deduction_5", 31.6, 43.6),
    ("logical_deduction_7", 25.2, 37.2),
    ("logical_deduction_3", 42.0, 61.6),
    ("movie_recommendation", 62.0, 74.4),
    ("multistep_arithmetic", 1.2, 45.2),
    ("navigate", 52.4, 56.4),
    ("object_counting", 30.4, 57.6),
    ("penguins_in_a_table", 35.6, 63.0),
    ("reasoning_colored_obj", 32.0, 56.8),
    ("ruin_names", 44.4, 86.4),
    ("salient_translation", 30.8, 52.4),
    ("snarks", 52.8, 73.0),
    ("sports_understanding", 58.4, 80.4),
    ("temporal_sequences", 24.0, 99.6),
    ("web_of_lies", 51.6, 52.0),
]

# InstructGPT: [AO, CoT]
igpt = [
    ("boolean_expressions", 90.0, 87.6),
    ("causal_judgement", 61.5, 70.6),
    ("date_understanding", 53.2, 57.2),
    ("disambiguation_qa", 43.2, 56.8),
    ("dyck_languages", 8.0, 7.6),
    ("formal_fallacies", 50.4, 50.4),
    ("geometric_shapes", 18.0, 41.6),
    ("hyperbaton", 52.4, 51.2),
    ("logical_deduction_5", 28.8, 36.8),
    ("logical_deduction_7", 16.0, 20.0),
    ("logical_deduction_3", 39.2, 52.0),
    ("movie_recommendation", 50.4, 52.0),
    ("multistep_arithmetic", 0.4, 1.2),
    ("navigate", 48.8, 56.0),
    ("object_counting", 30.0, 45.6),
    ("penguins_in_a_table", 29.5, 52.7),
    ("reasoning_colored_obj", 20.4, 36.4),
    ("ruin_names", 32.4, 45.6),
    ("salient_translation", 22.0, 42.8),
    ("snarks", 55.1, 58.4),
    ("sports_understanding", 56.4, 70.8),
    ("temporal_sequences", 27.6, 30.4),
    ("web_of_lies", 48.8, 51.2),
]

# Codex: [AO, CoT]
codex = [
    ("boolean_expressions", 88.4, 92.8),
    ("causal_judgement", 55.6, 63.1),
    ("date_understanding", 53.2, 73.6),
    ("disambiguation_qa", 56.0, 64.4),
    ("dyck_languages", 22.0, 7.6),
    ("formal_fallacies", 52.0, 53.6),
    ("geometric_shapes", 30.4, 56.4),
    ("hyperbaton", 63.6, 72.4),
    ("logical_deduction_5", 30.8, 43.6),
    ("logical_deduction_7", 24.0, 30.0),
    ("logical_deduction_3", 52.4, 64.8),
    ("movie_recommendation", 61.6, 72.0),
    ("multistep_arithmetic", 2.4, 47.6),
    ("navigate", 52.0, 65.6),
    ("object_counting", 42.8, 73.2),
    ("penguins_in_a_table", 37.0, 72.6),
    ("reasoning_colored_obj", 36.0, 64.0),
    ("ruin_names", 60.4, 86.4),
    ("salient_translation", 36.4, 68.0),
    ("snarks", 56.7, 76.4),
    ("sports_understanding", 65.6, 88.4),
    ("temporal_sequences", 16.0, 99.6),
    ("web_of_lies", 51.2, 56.4),
]

def mean(xs):
    return sum(xs) / len(xs)

def std(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m)**2 for x in xs) / len(xs))

def median(xs):
    s = sorted(xs)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2

print("=" * 70)
print("BBH eta^2 Estimation Experiment")
print("Purpose: Independent estimation of rho via eta^2_prompt")
print("Data: Suzgun et al. (2022) arXiv:2210.09261 Table 2")
print("=" * 70)

# === Analysis 1: PaLM CoT-AO differences ===
print("\n--- Analysis 1: Per-Task Delta (PaLM 540B) ---")
diffs = []
print(f"{'Task':<30s} {'AO':>6s} {'CoT':>6s} {'Delta':>8s}")
print("-" * 55)
sorted_palm = sorted(palm, key=lambda x: x[2] - x[1], reverse=True)
for name, ao, cot in sorted_palm:
    d = cot - ao
    diffs.append(d)
    marker = "***" if abs(d) > 20 else ""
    print(f"{name:<30s} {ao:>6.1f} {cot:>6.1f} {d:>+8.1f} {marker}")

print(f"\nDelta mean: {mean(diffs):+.1f}%")
print(f"Delta SD:   {std(diffs):.1f}%")
print(f"Delta median: {median(diffs):+.1f}%")
print(f"CoT > AO: {sum(1 for d in diffs if d > 0)}/23")
print(f"AO > CoT: {sum(1 for d in diffs if d < 0)}/23")

# === Analysis 2: Cross-Model 2-factor ANOVA ===
print("\n" + "=" * 70)
print("--- Analysis 2: Cross-Model eta^2 (3 Models x 2 Prompts) ---")
print("=" * 70)

eta_prompt_list = []
eta_model_list = []
eta_inter_list = []

for i in range(23):
    task_name = palm[i][0]
    # 6 data points: iGPT-AO, iGPT-CoT, Codex-AO, Codex-CoT, PaLM-AO, PaLM-CoT
    data = [
        igpt[i][1], igpt[i][2],   # InstructGPT AO, CoT
        codex[i][1], codex[i][2], # Codex AO, CoT
        palm[i][1], palm[i][2],   # PaLM AO, CoT
    ]
    
    grand = mean(data)
    ss_total = sum((x - grand)**2 for x in data)
    
    # SS_prompt: AO vs CoT (indices 0,2,4 = AO; 1,3,5 = CoT)
    ao_vals = [data[0], data[2], data[4]]
    cot_vals = [data[1], data[3], data[5]]
    ao_m = mean(ao_vals)
    cot_m = mean(cot_vals)
    ss_prompt = 3 * ((ao_m - grand)**2 + (cot_m - grand)**2)
    
    # SS_model: 3 models (indices 0-1=iGPT, 2-3=Codex, 4-5=PaLM)
    m_means = [mean(data[0:2]), mean(data[2:4]), mean(data[4:6])]
    ss_model = 2 * sum((m - grand)**2 for m in m_means)
    
    # SS_interaction = SS_total - SS_prompt - SS_model (no replication)
    ss_inter = max(0, ss_total - ss_prompt - ss_model)
    
    if ss_total > 0:
        ep = ss_prompt / ss_total
        em = ss_model / ss_total
        ei = ss_inter / ss_total
    else:
        ep = em = ei = 0.0
    
    eta_prompt_list.append(ep)
    eta_model_list.append(em)
    eta_inter_list.append(ei)

print(f"\n{'Task':<30s} {'eta2_prompt':>11s} {'eta2_model':>11s} {'eta2_inter':>11s}")
print("-" * 66)
for i in range(23):
    print(f"{palm[i][0]:<30s} {eta_prompt_list[i]:>11.3f} {eta_model_list[i]:>11.3f} {eta_inter_list[i]:>11.3f}")

rho_est = mean(eta_prompt_list)
rho_med = median(eta_prompt_list)
rho_sd = std(eta_prompt_list)

print(f"\n{'='*66}")
print(f"eta2_prompt (rho_est):  mean={rho_est:.4f}  SD={rho_sd:.4f}  median={rho_med:.4f}")
print(f"eta2_model:             mean={mean(eta_model_list):.4f}")
print(f"eta2_interaction:       mean={mean(eta_inter_list):.4f}")

print(f"\n{'='*66}")
print(f"*** rho_est = {rho_est:.4f} ***")
print(f"Reverse estimate rho ~ 0.3, difference: {rho_est - 0.3:+.4f}")
print(f"Threshold: [0.15, 0.45]")
if 0.15 <= rho_est <= 0.45:
    print(f"-> SUPPORTED (eta^2 in [0.15, 0.45])")
elif rho_est < 0.10:
    print(f"-> REJECTED (eta^2 < 0.10)")
elif rho_est > 0.60:
    print(f"-> REJECTED (eta^2 > 0.60)")
else:
    print(f"-> INCONCLUSIVE")

# Ceiling prediction
K = 8
r_pred = math.sqrt(rho_est / (K + 1))
r_paper = math.sqrt(0.3 / 9)
print(f"\n--- Ceiling Prediction ---")
print(f"r_pred = sqrt({rho_est:.4f} / {K+1}) = {r_pred:.4f} ({r_pred*100:.1f}%)")
print(f"Paper IV (rho=0.3, K=8): r <= {r_paper:.4f} ({r_paper*100:.1f}%)")

# === Analysis 3: Task Variability ===
print(f"\n{'='*66}")
print(f"--- Analysis 3: Task Variability ---")
s_etas = sorted(eta_prompt_list)
print(f"min:    {s_etas[0]:.4f}")
print(f"Q25:    {s_etas[5]:.4f}")
print(f"median: {rho_med:.4f}")
print(f"Q75:    {s_etas[17]:.4f}")
print(f"max:    {s_etas[22]:.4f}")
print(f"SD:     {rho_sd:.4f}")
print(f"CV:     {rho_sd/rho_est:.2f}" if rho_est > 0 else "CV: inf")

if rho_sd > 0.15:
    print(f"\n-> WARNING: High task dependency (SD > 0.15)")
    print(f"   rho should be treated as task-dependent parameter")
else:
    print(f"\n-> OK: Task dependency is acceptable (SD <= 0.15)")
    print(f"   rho as fixed value is a reasonable first approximation")

print(f"\n{'='*66}")
print("Experiment complete.")
