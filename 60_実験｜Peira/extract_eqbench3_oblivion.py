"""
EQ-Bench 3: Extract per-model, per-dimension average rubric scores
for all 46 models in canonical results.

Output: CSV + summary table showing U-discarded vs U-preserved dimensions.
"""
import gzip, json, csv
from collections import defaultdict

SRC = r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\60_実験｜Peira\eqbench3_clone\data\canonical_leaderboard_results.json.gz"
ELO = r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\60_実験｜Peira\eqbench3_clone\data\canonical_leaderboard_elo_results.json.gz"
CSV_OUT = r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\60_実験｜Peira\eqbench3_model_dimensions.csv"
TXT_OUT = r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\60_実験｜Peira\eqbench3_oblivion_analysis.txt"

# Dimension grouping per Oblivion Theory
U_DISCARDED = ["demonstrated_empathy", "warmth", "social_dexterity", "humanlike"]
U_PRESERVED = ["analytical", "depth_of_insight", "pragmatic_ei"]
U_OTHER = ["safety_conscious", "moralising", "compliant"]
ALL_DIMS = U_DISCARDED + U_PRESERVED + U_OTHER

print("Loading canonical results...", flush=True)
with gzip.open(SRC, "rt", encoding="utf-8") as f:
    results = json.load(f)

print("Loading Elo data...", flush=True)
with gzip.open(ELO, "rt", encoding="utf-8") as f:
    elo_data = json.load(f)

# Build model_name -> elo_norm mapping
elo_map = {}
for k, v in elo_data.items():
    if k == "__metadata__":
        continue
    elo_map[k] = v.get("elo_norm", 0)

models = [k for k in results.keys() if k != "__metadata__"]
print(f"Processing {len(models)} models...", flush=True)

# Collect per-model, per-dimension scores
model_data = []

for model_key in models:
    model = results[model_key]
    model_name = model.get("model_name", model_key)
    
    dim_scores = defaultdict(list)
    
    # Navigate: scenario_tasks -> iteration -> scenario_id -> rubric_scores
    scenario_tasks = model.get("scenario_tasks", {})
    for iteration_key, scenarios in scenario_tasks.items():
        if not isinstance(scenarios, dict):
            continue
        for scenario_id, scenario in scenarios.items():
            if not isinstance(scenario, dict):
                continue
            rubric = scenario.get("rubric_scores", {})
            if not isinstance(rubric, dict):
                continue
            for dim in ALL_DIMS:
                if dim in rubric and rubric[dim] is not None:
                    dim_scores[dim].append(float(rubric[dim]))
    
    # Compute averages
    dim_avgs = {}
    for dim in ALL_DIMS:
        scores = dim_scores[dim]
        dim_avgs[dim] = sum(scores) / len(scores) if scores else None
    
    # Compute group averages
    discarded_vals = [dim_avgs[d] for d in U_DISCARDED if dim_avgs[d] is not None]
    preserved_vals = [dim_avgs[d] for d in U_PRESERVED if dim_avgs[d] is not None]
    
    avg_discarded = sum(discarded_vals) / len(discarded_vals) if discarded_vals else None
    avg_preserved = sum(preserved_vals) / len(preserved_vals) if preserved_vals else None
    
    gap = (avg_preserved - avg_discarded) if (avg_preserved is not None and avg_discarded is not None) else None
    
    # Get Elo
    elo_norm = elo_map.get(model_name, None)
    
    model_data.append({
        "model_key": model_key,
        "model_name": model_name,
        "elo_norm": elo_norm,
        "avg_discarded": avg_discarded,
        "avg_preserved": avg_preserved,
        "gap": gap,
        "n_scenarios": len(dim_scores.get("analytical", [])),
        **dim_avgs
    })

# Sort by Elo
model_data.sort(key=lambda x: x.get("elo_norm") or 0, reverse=True)

# Write CSV
header = ["model_name", "elo_norm", "avg_discarded", "avg_preserved", "gap", "n_scenarios"] + ALL_DIMS
with open(CSV_OUT, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
    writer.writeheader()
    for row in model_data:
        writer.writerow(row)

# Write analysis
lines = []
lines.append("=" * 90)
lines.append("EQ-Bench 3: Oblivion Theory Dimensional Analysis")
lines.append("U-Discarded: empathy, warmth, social_dexterity, humanlike (concrete/emotional)")
lines.append("U-Preserved: analytical, depth_of_insight, pragmatic_ei (abstract/cognitive)")
lines.append("=" * 90)
lines.append("")

fmt = "{:<45} {:>8} {:>10} {:>10} {:>6} {:>4}"
lines.append(fmt.format("Model", "Elo_Norm", "Discarded", "Preserved", "Gap", "N"))
lines.append("-" * 90)

for m in model_data:
    elo_s = f"{m['elo_norm']:.0f}" if m['elo_norm'] else "?"
    disc_s = f"{m['avg_discarded']:.2f}" if m['avg_discarded'] else "?"
    pres_s = f"{m['avg_preserved']:.2f}" if m['avg_preserved'] else "?"
    gap_s = f"{m['gap']:+.2f}" if m['gap'] is not None else "?"
    lines.append(fmt.format(m['model_name'][:45], elo_s, disc_s, pres_s, gap_s, str(m['n_scenarios'])))

lines.append("")
lines.append("=" * 90)
lines.append("Aggregate Statistics")
lines.append("=" * 90)

# Compute aggregate stats
all_gaps = [m['gap'] for m in model_data if m['gap'] is not None]
all_disc = [m['avg_discarded'] for m in model_data if m['avg_discarded'] is not None]
all_pres = [m['avg_preserved'] for m in model_data if m['avg_preserved'] is not None]

if all_gaps:
    lines.append(f"Mean Gap (Preserved - Discarded): {sum(all_gaps)/len(all_gaps):+.3f}")
    lines.append(f"Gap Range: [{min(all_gaps):+.3f}, {max(all_gaps):+.3f}]")
    lines.append(f"Models with positive gap: {sum(1 for g in all_gaps if g > 0)}/{len(all_gaps)}")
    lines.append(f"Mean Discarded: {sum(all_disc)/len(all_disc):.3f}")
    lines.append(f"Mean Preserved: {sum(all_pres)/len(all_pres):.3f}")

# Per-dimension stats across all models
lines.append("")
lines.append("Per-Dimension Averages (all models):")
lines.append(f"  {'Dimension':<25} {'Mean':>8} {'Category':>12}")
lines.append(f"  {'-'*50}")
for dim in ALL_DIMS:
    vals = [m[dim] for m in model_data if m.get(dim) is not None]
    if vals:
        mean = sum(vals) / len(vals)
        cat = "DISCARDED" if dim in U_DISCARDED else ("PRESERVED" if dim in U_PRESERVED else "OTHER")
        lines.append(f"  {dim:<25} {mean:>8.2f} {cat:>12}")

# Top5 vs Bottom5 comparison
lines.append("")
lines.append("Top-5 vs Bottom-5 Comparison:")
top5 = model_data[:5]
bot5 = model_data[-5:]
for label, group in [("Top-5", top5), ("Bottom-5", bot5)]:
    g_disc = [m['avg_discarded'] for m in group if m['avg_discarded'] is not None]
    g_pres = [m['avg_preserved'] for m in group if m['avg_preserved'] is not None]
    g_gap = [m['gap'] for m in group if m['gap'] is not None]
    if g_disc and g_pres and g_gap:
        lines.append(f"  {label}: Discarded={sum(g_disc)/len(g_disc):.2f}, Preserved={sum(g_pres)/len(g_pres):.2f}, Gap={sum(g_gap)/len(g_gap):+.2f}")

with open(TXT_OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"CSV: {CSV_OUT}", flush=True)
print(f"Analysis: {TXT_OUT}", flush=True)
print(f"Done. {len(model_data)} models processed.", flush=True)
