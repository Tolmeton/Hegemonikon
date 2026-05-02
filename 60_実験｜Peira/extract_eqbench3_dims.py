"""Extract EQ-Bench 3 dimensional scores from canonical results"""
import gzip, json

SRC = r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\60_実験｜Peira\eqbench3_clone\data\canonical_leaderboard_results.json.gz"
OUT = r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\60_実験｜Peira\eqbench3_dimensions_extract.txt"

print("Loading canonical results (17MB)...", flush=True)
with gzip.open(SRC, "rt", encoding="utf-8") as f:
    data = json.load(f)

print(f"Type: {type(data)}", flush=True)
if isinstance(data, dict):
    models = [k for k in data.keys() if k != "__metadata__"]
    print(f"Models: {len(models)}", flush=True)
    
    lines = []
    
    # Explore structure of first model
    first_model = models[0]
    lines.append(f"=== Structure of '{first_model}' ===")
    
    def explore(obj, prefix="", depth=0):
        if depth > 3:
            return
        if isinstance(obj, dict):
            for k in list(obj.keys())[:20]:
                v = obj[k]
                if isinstance(v, (int, float, str, bool)):
                    lines.append(f"{prefix}{k}: {v}")
                elif isinstance(v, dict):
                    lines.append(f"{prefix}{k}: dict({len(v)} keys)")
                    if depth < 2:
                        explore(v, prefix + "  ", depth + 1)
                elif isinstance(v, list):
                    lines.append(f"{prefix}{k}: list({len(v)})")
                    if v and depth < 2:
                        lines.append(f"{prefix}  [0]: {type(v[0]).__name__}")
                        if isinstance(v[0], dict):
                            explore(v[0], prefix + "    ", depth + 1)
                else:
                    lines.append(f"{prefix}{k}: {type(v).__name__}")
    
    explore(data[first_model])
    
    # Look for dimension scores
    lines.append("")
    lines.append("=== Searching for dimension keywords ===")
    
    dim_keywords = ["warm", "empathy", "analytic", "insight", "social", "humanlike",
                    "assertive", "compliant", "moralising", "pragmatic", "safety",
                    "rubric", "score", "dimension", "trait", "capability"]
    
    def search_keys(obj, path="", depth=0):
        if depth > 5:
            return
        if isinstance(obj, dict):
            for k in obj.keys():
                kl = k.lower()
                for kw in dim_keywords:
                    if kw in kl:
                        v = obj[k]
                        val_str = str(v)[:200] if not isinstance(v, dict) else f"dict({len(v)})"
                        lines.append(f"  FOUND: {path}.{k} = {val_str}")
                if isinstance(obj[k], dict) and depth < 4:
                    search_keys(obj[k], f"{path}.{k}", depth + 1)
    
    for m in models[:5]:
        lines.append(f"\n--- Searching {m} ---")
        search_keys(data[m], m)
    
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"Written to {OUT}", flush=True)
elif isinstance(data, list):
    print(f"List length: {len(data)}", flush=True)
    
print("Done.", flush=True)
