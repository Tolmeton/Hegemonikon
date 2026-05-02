"""
EQ-Bench 3: Generational Analysis of U-Gap (v3 - correct structure)
SOURCE: canonical_leaderboard_results.json.gz + canonical_leaderboard_elo_results.json.gz

Data structures:
  results.json.gz: {model_key_with_prefix: {scenario_tasks: {'1': {scenario_id: {rubric_scores: {...}}}}}}
  elo_results.json.gz: {model_key_no_prefix: {elo_norm: float, ...}}
"""
import json, gzip, os, re
from collections import defaultdict

BASE = r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\60_実験｜Peira"
DATA = os.path.join(BASE, "eqbench3_clone", "data")

DISCARDED = {'demonstrated_empathy', 'warmth', 'social_dexterity', 'humanlike'}
PRESERVED = {'analytical', 'depth_of_insight', 'pragmatic_ei'}

def load_data():
    with gzip.open(os.path.join(DATA, 'canonical_leaderboard_results.json.gz'), 'rt', encoding='utf-8') as f:
        results = json.load(f)
    with gzip.open(os.path.join(DATA, 'canonical_leaderboard_elo_results.json.gz'), 'rt', encoding='utf-8') as f:
        elo_data = json.load(f)
    return results, elo_data

def strip_prefix(key):
    """Remove prefix like '1_' or '20cd4a70_' from result keys"""
    m = re.match(r'^[0-9a-f]+_(.+)$', key)
    return m.group(1) if m else key

def compute_model_scores(model_data):
    dim_sums = defaultdict(float)
    dim_counts = defaultdict(int)
    scenario_count = 0
    for run_key, run_data in model_data.get('scenario_tasks', {}).items():
        if not isinstance(run_data, dict):
            continue
        for scenario_id, scenario in run_data.items():
            if not isinstance(scenario, dict):
                continue
            rubric = scenario.get('rubric_scores', {})
            if rubric:
                scenario_count += 1
                for dim, val in rubric.items():
                    if isinstance(val, (int, float)):
                        dim_sums[dim] += val
                        dim_counts[dim] += 1
    avgs = {dim: dim_sums[dim] / dim_counts[dim] for dim in dim_sums if dim_counts[dim] > 0}
    return avgs, scenario_count

def classify(dim_avgs):
    d = [dim_avgs[x] for x in DISCARDED if x in dim_avgs]
    p = [dim_avgs[x] for x in PRESERVED if x in dim_avgs]
    da = sum(d)/len(d) if d else 0
    pa = sum(p)/len(p) if p else 0
    return da, pa, pa - da

# ELO key (no prefix, / separators) to display names for families
FAMILIES = {
    'OpenAI GPT': [
        ('gpt-4-0314', 'gpt-4-0314', 1),
        ('chatgpt-4o-latest', 'chatgpt-4o-latest', 2),
        ('openai/chatgpt-4o-latest', 'openai/chatgpt-4o-latest', 3),
        ('gpt-4.1-nano', 'gpt-4.1-nano', 4),
        ('openai/gpt-4.1-mini', 'openai/gpt-4.1-mini', 5),
        ('openai/gpt-4.1', 'openai/gpt-4.1', 6),
        ('gpt-4.5-preview-2025-02-27', 'gpt-4.5-preview-2025-02-27', 7),
        ('openai/gpt-oss-20b', 'openai/gpt-oss-20b', 8),
        ('openai/gpt-oss-120b', 'openai/gpt-oss-120b', 9),
        ('gpt-5-chat-latest-2025-08-07', 'gpt-5-chat-latest-2025-08-07', 10),
        ('o3', 'o3', 11),
        ('o4-mini', 'o4-mini', 12),
    ],
    'Anthropic Claude': [
        ('claude-3.5-sonnet', 'anthropic/claude-3.5-sonnet', 1),
        ('claude-3.7-sonnet', 'anthropic/claude-3.7-sonnet', 2),
        ('claude-sonnet-4', 'claude-sonnet-4', 3),
        ('claude-opus-4', 'anthropic/claude-opus-4', 4),
    ],
    'Google Gemini': [
        ('gemini-2.0-flash', 'google/gemini-2.0-flash-001', 1),
        ('gemini-2.5-flash', 'google/gemini-2.5-flash-preview', 2),
        ('gemini-2.5-pro-03-25', 'google/gemini-2.5-pro-preview-03-25', 3),
        ('gemini-2.5-pro-05-07', 'gemini-2.5-pro-preview-2025-05-07', 4),
        ('gemini-2.5-pro-06-05', 'gemini-2.5-pro-preview-06-05', 5),
    ],
    'DeepSeek': [
        ('deepseek-v3-0324', 'deepseek/deepseek-chat-v3-0324', 1),
        ('deepseek-r1', 'deepseek/deepseek-r1', 2),
    ],
    'Qwen': [
        ('qwen-2.5-72b', 'qwen/qwen-2.5-72b-instruct', 1),
        ('Qwen3-32B', 'Qwen/Qwen3-32B', 2),
        ('Qwen3-8B', 'Qwen/Qwen3-8B', 3),
        ('Qwen3-235B-A22B', 'Qwen/Qwen3-235B-A22B', 4),
    ],
    'Meta LLaMA': [
        ('llama-3.2-1b', 'meta-llama/llama-3.2-1b-instruct', 1),
        ('llama-4-scout', 'meta-llama/llama-4-scout', 2),
        ('llama-4-maverick', 'meta-llama/llama-4-maverick', 3),
    ],
    'Mistral': [
        ('mistral-small-2501', 'mistralai/mistral-small-24b-instruct-2501', 1),
        ('mistral-small-3.1', 'mistralai/mistral-small-3.1-24b-instruct', 2),
        ('mistral-small-3.2', 'mistralai/mistral-small-3.2-24b-instruct', 3),
    ],
    'Google Gemma': [
        ('gemma-2-9b', 'google/gemma-2-9b-it', 1),
        ('gemma-3-4b', 'google/gemma-3-4b-it', 2),
        ('gemma-3-27b', 'google/gemma-3-27b-it', 3),
    ],
}

def main():
    results, elo_data = load_data()

    # Build unified lookup: elo_key -> {elo, discarded, preserved, gap, dims}
    # Results keys have prefix; Elo keys don't. Map via strip_prefix.
    
    # First, build results scores by stripped key
    result_scores = {}
    for rkey, rdata in results.items():
        if rkey == '__metadata__':
            continue
        stripped = strip_prefix(rkey)
        avgs, n = compute_model_scores(rdata)
        if avgs and n > 0:
            d, p, g = classify(avgs)
            result_scores[stripped] = {'discarded': d, 'preserved': p, 'gap': g, 'dims': avgs, 'n': n}
    
    # Build elo lookup by elo key
    elo_lookup = {}
    for ekey, edata in elo_data.items():
        if ekey == '__metadata__':
            continue
        if isinstance(edata, dict):
            elo_lookup[ekey] = edata.get('elo_norm', 0)
    
    # Merge: use elo key as canonical
    model_db = {}
    for ekey in elo_lookup:
        # Try direct match, then with _ substitution
        score = result_scores.get(ekey)
        if not score:
            # Try replacing / with _
            alt = ekey.replace('/', '_')
            score = result_scores.get(alt)
        if score:
            model_db[ekey] = {**score, 'elo': elo_lookup[ekey]}
        else:
            model_db[ekey] = {'elo': elo_lookup[ekey], 'discarded': 0, 'preserved': 0, 'gap': 0, 'dims': {}, 'n': 0}
    
    out = []
    out.append("=" * 90)
    out.append("EQ-Bench 3: Generational Analysis — U-Gap Evolution Within Model Families")
    out.append("U-Discarded: empathy, warmth, social_dexterity, humanlike")
    out.append("U-Preserved: analytical, depth_of_insight, pragmatic_ei")
    out.append("=" * 90)
    
    family_deltas = []
    
    for family_name, members in FAMILIES.items():
        out.append(f"\n{'─' * 90}")
        out.append(f"FAMILY: {family_name}")
        out.append(f"{'─' * 90}")
        out.append(f"{'Model':<25s} {'Elo':>6s} {'Disc':>8s} {'Pres':>8s} {'Gap':>8s} {'ΔGap':>8s} {'N':>4s}")
        out.append("-" * 68)
        
        prev_gap = None
        found = []
        
        for display, elo_key, order in sorted(members, key=lambda x: x[2]):
            m = model_db.get(elo_key)
            if m and m['n'] > 0:
                delta = f"{m['gap'] - prev_gap:+.2f}" if prev_gap is not None else ""
                out.append(f"{display:<25s} {m['elo']:>6.0f} {m['discarded']:>8.2f} {m['preserved']:>8.2f} {m['gap']:>+8.2f} {delta:>8s} {m['n']:>4d}")
                found.append((display, m))
                prev_gap = m['gap']
            else:
                out.append(f"{display:<25s}  ** NOT FOUND (elo_key: {elo_key})")
        
        if len(found) >= 2:
            f0, fl = found[0][1], found[-1][1]
            dg = fl['gap'] - f0['gap']
            de = fl['elo'] - f0['elo']
            trend = 'WIDENING ↑' if dg > 0.1 else 'NARROWING ↓' if dg < -0.1 else 'STABLE →'
            out.append(f"\n  → Δ(Gap): {dg:+.2f} | Δ(Elo): {de:+.0f} | {trend}")
            family_deltas.append((family_name, dg, de, len(found)))
    
    out.append(f"\n{'=' * 90}")
    out.append("CROSS-FAMILY SUMMARY")
    out.append(f"{'=' * 90}")
    out.append(f"{'Family':<22s} {'N':>3s} {'ΔGap':>8s} {'ΔElo':>8s} {'Trend':>15s}")
    out.append("-" * 60)
    for name, dg, de, n in family_deltas:
        trend = 'WIDENING ↑' if dg > 0.1 else 'NARROWING ↓' if dg < -0.1 else 'STABLE →'
        out.append(f"{name:<22s} {n:>3d} {dg:>+8.2f} {de:>+8.0f} {trend:>15s}")
    
    w = sum(1 for _,d,_,_ in family_deltas if d > 0.1)
    n = sum(1 for _,d,_,_ in family_deltas if d < -0.1)
    s = len(family_deltas) - w - n
    md = sum(d for _,d,_,_ in family_deltas) / len(family_deltas) if family_deltas else 0
    out.append(f"\nWidening: {w} / Narrowing: {n} / Stable: {s}")
    out.append(f"Mean ΔGap: {md:+.3f}")
    
    # Elo × Gap correlation
    out.append(f"\n{'=' * 90}")
    out.append("ELO vs GAP CORRELATION")
    out.append(f"{'=' * 90}")
    elos = [m['elo'] for m in model_db.values() if m['n'] > 0 and m['elo'] > 0]
    gaps = [m['gap'] for m in model_db.values() if m['n'] > 0 and m['elo'] > 0]
    if len(elos) > 2:
        nn = len(elos)
        me, mg = sum(elos)/nn, sum(gaps)/nn
        cov = sum((e-me)*(g-mg) for e,g in zip(elos,gaps))/nn
        se = (sum((e-me)**2 for e in elos)/nn)**0.5
        sg = (sum((g-mg)**2 for g in gaps)/nn)**0.5
        r = cov/(se*sg) if se>0 and sg>0 else 0
        out.append(f"r(Elo, Gap) = {r:.4f} (N={nn})")
        out.append(f"→ {'Higher Elo = larger U-Gap (thinning scales with ability)' if r > 0.05 else 'No clear relationship'}")
    
    # Per-dimension Elo correlation
    out.append(f"\n{'=' * 90}")
    out.append("PER-DIMENSION ELO CORRELATION")
    out.append(f"{'=' * 90}")
    all_dims = set()
    for m in model_db.values():
        all_dims.update(m.get('dims', {}).keys())
    
    dim_corrs = []
    for dim in sorted(all_dims):
        es, vs = [], []
        for m in model_db.values():
            if m['n'] > 0 and m['elo'] > 0 and dim in m.get('dims', {}):
                es.append(m['elo']); vs.append(m['dims'][dim])
        if len(es) > 2:
            nn = len(es)
            me, mv = sum(es)/nn, sum(vs)/nn
            cov = sum((e-me)*(v-mv) for e,v in zip(es,vs))/nn
            se = (sum((e-me)**2 for e in es)/nn)**0.5
            sv = (sum((v-mv)**2 for v in vs)/nn)**0.5
            r = cov/(se*sv) if se>0 and sv>0 else 0
            cat = "DISC" if dim in DISCARDED else "PRES" if dim in PRESERVED else "OTHER"
            dim_corrs.append((dim, r, cat))
    
    out.append(f"{'Dimension':<30s} {'r(Elo)':>8s} {'Cat':>6s}")
    out.append("-" * 48)
    for d, r, c in sorted(dim_corrs, key=lambda x: -x[1]):
        out.append(f"{d:<30s} {r:>+8.4f} {c:>6s}")
    
    dr = [r for _,r,c in dim_corrs if c=='DISC']
    pr = [r for _,r,c in dim_corrs if c=='PRES']
    if dr and pr:
        out.append(f"\nMean r(Elo) DISCARDED: {sum(dr)/len(dr):+.4f}")
        out.append(f"Mean r(Elo) PRESERVED: {sum(pr)/len(pr):+.4f}")
        out.append(f"Δ (PRES - DISC): {sum(pr)/len(pr)-sum(dr)/len(dr):+.4f}")
        out.append(f"→ {'PRESERVED scales faster = U confirmed' if sum(pr)/len(pr) > sum(dr)/len(dr) + 0.01 else 'No differential scaling'}")

    txt = "\n".join(out)
    with open(os.path.join(BASE, "eqbench3_generational_analysis.txt"), 'w', encoding='utf-8') as f:
        f.write(txt)
    print(txt)

if __name__ == '__main__':
    main()
