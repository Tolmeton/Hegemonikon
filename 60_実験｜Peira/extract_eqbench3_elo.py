"""Extract EQ-Bench 3 Elo leaderboard from canonical JSON"""
import gzip, json

SRC = r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\60_実験｜Peira\eqbench3_clone\data\canonical_leaderboard_elo_results.json.gz"
OUT = r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\60_実験｜Peira\eqbench3_elo_extract.txt"

with gzip.open(SRC, "rt", encoding="utf-8") as f:
    data = json.load(f)

models = [k for k in data.keys() if k != "__metadata__"]
ranked = sorted(models, key=lambda m: data[m].get("elo_norm", 0), reverse=True)

lines = []
lines.append(f"Total models: {len(models)}")
lines.append("")
lines.append("# | Model | Elo | Elo_Norm | CI_Low_Norm | CI_High_Norm")
lines.append("-" * 90)

for i, m in enumerate(ranked, 1):
    d = data[m]
    elo = d.get("elo", 0)
    en = d.get("elo_norm", 0)
    cl = d.get("ci_low_norm", 0)
    ch = d.get("ci_high_norm", 0)
    lines.append(f"{i:>2}. {m:<50} {elo:>8.1f} {en:>8.1f}  [{cl:.1f} - {ch:.1f}]")

lines.append("")
lines.append("=== Structure of top model entry ===")
top = data[ranked[0]]
for k, v in top.items():
    val_str = str(v)[:120]
    lines.append(f"  {k} ({type(v).__name__}): {val_str}")

# Also dump metadata if exists
if "__metadata__" in data:
    lines.append("")
    lines.append("=== Metadata ===")
    meta = data["__metadata__"]
    lines.append(json.dumps(meta, indent=2, ensure_ascii=False)[:2000])

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Done. {len(models)} models extracted to {OUT}")
print(f"Top 5:")
for m in ranked[:5]:
    en = data[m].get("elo_norm", 0)
    print(f"  {m}: {en:.1f}")
