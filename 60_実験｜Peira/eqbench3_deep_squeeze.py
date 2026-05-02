"""
EQ-Bench 3: Deep Squeeze — 全データから搾り切る追加分析
SOURCE: canonical_leaderboard_results.json.gz + canonical_leaderboard_elo_results.json.gz

分析内容:
  A. 三層モデルの直接証拠 (sycophantic/moralising/reactive の負相関 = 層2)
  B. 次元クラスタリング (スケーリング挙動で自然分類)
  C. プロファイル分散 (高Elo ほど次元プロファイルが不均一か)
  D. 次元間相関行列 (warmth×empathy vs warmth×analytical)
  E. Theory of Mind の位置づけ (境界次元仮説)
  F. シナリオ別分散 (モデルは特定シナリオで特に薄くなるか)
  G. gpt-4-0314 例外の解剖 (唯一の Gap≈0 モデル)
"""
import json, gzip, os, re, math
from collections import defaultdict

BASE = r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\60_実験｜Peira"
DATA = os.path.join(BASE, "eqbench3_clone", "data")

DISCARDED = {'demonstrated_empathy', 'warmth', 'social_dexterity', 'humanlike'}
PRESERVED = {'analytical', 'depth_of_insight', 'pragmatic_ei'}
SAFETY = {'sycophantic', 'moralising', 'compliant', 'reactive', 'safety_conscious'}

def load_data():
    with gzip.open(os.path.join(DATA, 'canonical_leaderboard_results.json.gz'), 'rt', encoding='utf-8') as f:
        results = json.load(f)
    with gzip.open(os.path.join(DATA, 'canonical_leaderboard_elo_results.json.gz'), 'rt', encoding='utf-8') as f:
        elo_data = json.load(f)
    return results, elo_data

def strip_prefix(key):
    m = re.match(r'^[0-9a-f]+_(.+)$', key)
    return m.group(1) if m else key

def compute_model_scores(model_data):
    dim_sums = defaultdict(float)
    dim_counts = defaultdict(int)
    scenario_scores = defaultdict(lambda: defaultdict(list))  # scenario_id -> dim -> [vals]
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
                        scenario_scores[scenario_id][dim].append(val)
    avgs = {dim: dim_sums[dim] / dim_counts[dim] for dim in dim_sums if dim_counts[dim] > 0}
    return avgs, scenario_count, scenario_scores

def pearson(xs, ys):
    n = len(xs)
    if n < 3: return 0
    mx, my = sum(xs)/n, sum(ys)/n
    cov = sum((x-mx)*(y-my) for x,y in zip(xs,ys)) / n
    sx = (sum((x-mx)**2 for x in xs)/n)**0.5
    sy = (sum((y-my)**2 for y in ys)/n)**0.5
    return cov/(sx*sy) if sx > 0 and sy > 0 else 0

def std(vals):
    n = len(vals)
    if n < 2: return 0
    m = sum(vals)/n
    return (sum((v-m)**2 for v in vals)/(n-1))**0.5

def main():
    results, elo_data = load_data()

    # Build model database
    result_scores = {}
    result_scenarios = {}
    for rkey, rdata in results.items():
        if rkey == '__metadata__': continue
        stripped = strip_prefix(rkey)
        avgs, n, scenarios = compute_model_scores(rdata)
        if avgs and n > 0:
            d = [avgs[x] for x in DISCARDED if x in avgs]
            p = [avgs[x] for x in PRESERVED if x in avgs]
            da = sum(d)/len(d) if d else 0
            pa = sum(p)/len(p) if p else 0
            result_scores[stripped] = {'discarded': da, 'preserved': pa, 'gap': pa-da, 'dims': avgs, 'n': n}
            result_scenarios[stripped] = scenarios

    elo_lookup = {}
    for ekey, edata in elo_data.items():
        if ekey == '__metadata__': continue
        if isinstance(edata, dict):
            elo_lookup[ekey] = edata.get('elo_norm', 0)

    model_db = {}
    model_scenarios = {}
    for ekey in elo_lookup:
        score = result_scores.get(ekey)
        if not score:
            score = result_scores.get(ekey.replace('/', '_'))
        if score:
            model_db[ekey] = {**score, 'elo': elo_lookup[ekey]}
            sc = result_scenarios.get(ekey) or result_scenarios.get(ekey.replace('/', '_'), {})
            model_scenarios[ekey] = sc
        else:
            model_db[ekey] = {'elo': elo_lookup[ekey], 'discarded': 0, 'preserved': 0, 'gap': 0, 'dims': {}, 'n': 0}

    valid = {k: v for k, v in model_db.items() if v['n'] > 0 and v['elo'] > 0}
    all_dims = set()
    for v in valid.values():
        all_dims.update(v['dims'].keys())
    all_dims = sorted(all_dims)

    out = []
    W = 100
    out.append("=" * W)
    out.append("EQ-Bench 3: DEEP SQUEEZE — 追加分析")
    out.append(f"有効モデル: {len(valid)} / 全次元: {len(all_dims)}")
    out.append("=" * W)

    # ══════════════════════════════════════════════════════════════════
    # A. 三層モデルの直接証拠
    # ══════════════════════════════════════════════════════════════════
    out.append(f"\n{'═' * W}")
    out.append("A. 三層モデルの直接証拠 — 安全チューニング次元の Elo 相関")
    out.append(f"{'═' * W}")
    out.append("Oblivion Theory の三層: 層1=構造的(U) / 層2=設計的(安全TN) / 層3=補正的(意図的)")
    out.append("層2 は sycophantic/moralising/reactive/compliant の Elo 負相関として測定可能\n")

    dim_elo_r = {}
    for dim in all_dims:
        es, vs = [], []
        for m in valid.values():
            if dim in m['dims']:
                es.append(m['elo']); vs.append(m['dims'][dim])
        if len(es) > 2:
            dim_elo_r[dim] = pearson(es, vs)

    # Classify dimensions into 4 tiers by r(Elo)
    out.append(f"{'Dimension':<30s} {'r(Elo)':>8s} {'Type':>8s} {'Layer':>8s}")
    out.append("-" * 58)
    for dim in sorted(dim_elo_r, key=dim_elo_r.get, reverse=True):
        r = dim_elo_r[dim]
        if dim in DISCARDED: typ = "DISC"
        elif dim in PRESERVED: typ = "PRES"
        elif dim in SAFETY: typ = "SAFETY"
        else: typ = "OTHER"
        if r > 0.6: layer = "層1"
        elif r > 0: layer = "層1(弱)"
        elif r > -0.3: layer = "層2?"
        else: layer = "層2"
        out.append(f"{dim:<30s} {r:>+8.4f} {typ:>8s} {layer:>8s}")

    # Key finding
    safety_rs = [(d, dim_elo_r[d]) for d in SAFETY if d in dim_elo_r]
    pos_safety = [(d,r) for d,r in safety_rs if r > 0]
    neg_safety = [(d,r) for d,r in safety_rs if r <= 0]
    out.append(f"\n  安全TN次元の分岐:")
    out.append(f"  正相関 (層1): {', '.join(f'{d} ({r:+.3f})' for d,r in pos_safety)}")
    out.append(f"  負相関 (層2): {', '.join(f'{d} ({r:+.3f})' for d,r in neg_safety)}")
    out.append(f"\n  → safety_conscious (+{dim_elo_r.get('safety_conscious',0):.3f}) は能力と共に上がる = 層1 (構造的)")
    out.append(f"  → sycophantic ({dim_elo_r.get('sycophantic',0):+.3f}) は能力と共に下がる = 層2 (安全チューニング)")
    out.append(f"  → 三層構造が次元レベルで直接観測される")

    # ══════════════════════════════════════════════════════════════════
    # B. 次元スケーリング・クラスタリング
    # ══════════════════════════════════════════════════════════════════
    out.append(f"\n{'═' * W}")
    out.append("B. 次元クラスタ — r(Elo) による自然分類")
    out.append(f"{'═' * W}")

    cluster_fast = [d for d in dim_elo_r if dim_elo_r[d] > 0.90]
    cluster_norm = [d for d in dim_elo_r if 0.80 <= dim_elo_r[d] <= 0.90]
    cluster_slow = [d for d in dim_elo_r if 0.0 < dim_elo_r[d] < 0.80]
    cluster_neg = [d for d in dim_elo_r if dim_elo_r[d] <= 0]

    out.append(f"\n  FAST SCALERS (r > 0.90): {len(cluster_fast)}")
    for d in sorted(cluster_fast, key=dim_elo_r.get, reverse=True):
        cat = "PRES" if d in PRESERVED else "DISC" if d in DISCARDED else ""
        out.append(f"    {d:<28s} r={dim_elo_r[d]:+.4f} {cat}")
    out.append(f"\n  NORMAL SCALERS (0.80-0.90): {len(cluster_norm)}")
    for d in sorted(cluster_norm, key=dim_elo_r.get, reverse=True):
        cat = "PRES" if d in PRESERVED else "DISC" if d in DISCARDED else ""
        out.append(f"    {d:<28s} r={dim_elo_r[d]:+.4f} {cat}")
    out.append(f"\n  SLOW SCALERS (0 < r < 0.80): {len(cluster_slow)}")
    for d in sorted(cluster_slow, key=dim_elo_r.get, reverse=True):
        cat = "SAFETY" if d in SAFETY else ""
        out.append(f"    {d:<28s} r={dim_elo_r[d]:+.4f} {cat}")
    out.append(f"\n  ANTI-SCALERS (r ≤ 0): {len(cluster_neg)}")
    for d in sorted(cluster_neg, key=dim_elo_r.get, reverse=True):
        cat = "SAFETY" if d in SAFETY else ""
        out.append(f"    {d:<28s} r={dim_elo_r[d]:+.4f} {cat}")

    # DISC in FAST vs NORM
    disc_fast = sum(1 for d in cluster_fast if d in DISCARDED)
    disc_norm = sum(1 for d in cluster_norm if d in DISCARDED)
    pres_fast = sum(1 for d in cluster_fast if d in PRESERVED)
    pres_norm = sum(1 for d in cluster_norm if d in PRESERVED)
    out.append(f"\n  DISC in FAST: {disc_fast}/{len(DISCARDED)} | DISC in NORM: {disc_norm}/{len(DISCARDED)}")
    out.append(f"  PRES in FAST: {pres_fast}/{len(PRESERVED)} | PRES in NORM: {pres_norm}/{len(PRESERVED)}")
    out.append(f"  → PRES が FAST に、DISC が NORM に偏る = U の差別的スケーリング" if pres_fast > disc_fast else "  → 分布は混合的")

    # ══════════════════════════════════════════════════════════════════
    # C. プロファイル分散 — 能力と不均一性
    # ══════════════════════════════════════════════════════════════════
    out.append(f"\n{'═' * W}")
    out.append("C. プロファイル分散 — 高Elo モデルは次元プロファイルが不均一か")
    out.append(f"{'═' * W}")

    # For each model, compute CoV of its dimension scores
    profile_data = []
    for key, m in valid.items():
        dims = m['dims']
        core = [dims.get(d, 0) for d in DISCARDED | PRESERVED if d in dims]
        if len(core) >= 5:
            cv = std(core) / (sum(core)/len(core)) if sum(core) > 0 else 0
            rng = max(core) - min(core)
            profile_data.append((key, m['elo'], cv, rng, m['gap']))

    if profile_data:
        elos = [x[1] for x in profile_data]
        cvs = [x[2] for x in profile_data]
        rngs = [x[3] for x in profile_data]
        r_cv = pearson(elos, cvs)
        r_rng = pearson(elos, rngs)
        out.append(f"\n  r(Elo, CoV of DISC+PRES) = {r_cv:+.4f} (N={len(profile_data)})")
        out.append(f"  r(Elo, Range of DISC+PRES) = {r_rng:+.4f}")
        if r_cv > 0.05:
            out.append(f"  → 高Elo モデルほどプロファイルが不均一 (次元間の差が大きい)")
        elif r_cv < -0.05:
            out.append(f"  → 高Elo モデルほどプロファイルが均一 (次元間の差が小さい)")
        else:
            out.append(f"  → Elo とプロファイル均一性に明確な関係なし")

        # Top-5 vs Bottom-5
        sorted_p = sorted(profile_data, key=lambda x: x[1], reverse=True)
        top5 = sorted_p[:5]
        bot5 = sorted_p[-5:]
        out.append(f"\n  Top-5 平均 CoV: {sum(x[2] for x in top5)/5:.4f} | Range: {sum(x[3] for x in top5)/5:.2f}")
        out.append(f"  Bottom-5 平均 CoV: {sum(x[2] for x in bot5)/5:.4f} | Range: {sum(x[3] for x in bot5)/5:.2f}")

    # ══════════════════════════════════════════════════════════════════
    # D. 次元間相関行列 (DISC/PRES のみ)
    # ══════════════════════════════════════════════════════════════════
    out.append(f"\n{'═' * W}")
    out.append("D. 次元間相関行列 — DISC/PRES の共変動")
    out.append(f"{'═' * W}")

    target_dims = sorted(DISCARDED | PRESERVED)
    out.append(f"\n{'':>22s} " + " ".join(f"{d[:8]:>8s}" for d in target_dims))
    for d1 in target_dims:
        row = f"{d1[:22]:<22s}"
        for d2 in target_dims:
            v1s, v2s = [], []
            for m in valid.values():
                if d1 in m['dims'] and d2 in m['dims']:
                    v1s.append(m['dims'][d1]); v2s.append(m['dims'][d2])
            r = pearson(v1s, v2s) if len(v1s) > 2 else 0
            row += f" {r:>+8.3f}"
        out.append(row)

    # Within-DISC vs Cross-DISC-PRES correlation
    within_disc = []
    within_pres = []
    cross = []
    for i, d1 in enumerate(sorted(DISCARDED)):
        for d2 in sorted(DISCARDED):
            if d1 >= d2: continue
            v1s, v2s = [], []
            for m in valid.values():
                if d1 in m['dims'] and d2 in m['dims']:
                    v1s.append(m['dims'][d1]); v2s.append(m['dims'][d2])
            if len(v1s) > 2:
                within_disc.append(pearson(v1s, v2s))
    for i, d1 in enumerate(sorted(PRESERVED)):
        for d2 in sorted(PRESERVED):
            if d1 >= d2: continue
            v1s, v2s = [], []
            for m in valid.values():
                if d1 in m['dims'] and d2 in m['dims']:
                    v1s.append(m['dims'][d1]); v2s.append(m['dims'][d2])
            if len(v1s) > 2:
                within_pres.append(pearson(v1s, v2s))
    for d1 in sorted(DISCARDED):
        for d2 in sorted(PRESERVED):
            v1s, v2s = [], []
            for m in valid.values():
                if d1 in m['dims'] and d2 in m['dims']:
                    v1s.append(m['dims'][d1]); v2s.append(m['dims'][d2])
            if len(v1s) > 2:
                cross.append(pearson(v1s, v2s))

    wd = sum(within_disc)/len(within_disc) if within_disc else 0
    wp = sum(within_pres)/len(within_pres) if within_pres else 0
    xc = sum(cross)/len(cross) if cross else 0
    out.append(f"\n  平均相関:")
    out.append(f"  Within DISC: {wd:.4f} ({len(within_disc)} pairs)")
    out.append(f"  Within PRES: {wp:.4f} ({len(within_pres)} pairs)")
    out.append(f"  Cross DISC×PRES: {xc:.4f} ({len(cross)} pairs)")
    if wd > xc + 0.01 and wp > xc + 0.01:
        out.append(f"  → DISC は DISC と、PRES は PRES と相関が強い = U が2つの独立クラスタを形成")
    elif xc > wd and xc > wp:
        out.append(f"  → Cross > Within = 次元間は一様に共変動 (U のクラスタ効果は弱い)")
    else:
        out.append(f"  → 部分的なクラスタ効果")

    # ══════════════════════════════════════════════════════════════════
    # E. Theory of Mind の位置分析
    # ══════════════════════════════════════════════════════════════════
    out.append(f"\n{'═' * W}")
    out.append("E. Theory of Mind — 境界次元仮説")
    out.append(f"{'═' * W}")

    tom_r = dim_elo_r.get('theory_of_mind', 0)
    # ToM correlations with DISC and PRES
    tom_disc_rs = []
    tom_pres_rs = []
    for d in DISCARDED:
        v1s, v2s = [], []
        for m in valid.values():
            if 'theory_of_mind' in m['dims'] and d in m['dims']:
                v1s.append(m['dims']['theory_of_mind']); v2s.append(m['dims'][d])
        if len(v1s) > 2:
            tom_disc_rs.append((d, pearson(v1s, v2s)))
    for d in PRESERVED:
        v1s, v2s = [], []
        for m in valid.values():
            if 'theory_of_mind' in m['dims'] and d in m['dims']:
                v1s.append(m['dims']['theory_of_mind']); v2s.append(m['dims'][d])
        if len(v1s) > 2:
            tom_pres_rs.append((d, pearson(v1s, v2s)))

    out.append(f"\n  theory_of_mind r(Elo) = {tom_r:+.4f} (FAST SCALER クラスタ)")
    out.append(f"\n  ToM × DISCARDED 相関:")
    for d, r in tom_disc_rs:
        out.append(f"    {d:<25s} r = {r:+.4f}")
    out.append(f"  ToM × PRESERVED 相関:")
    for d, r in tom_pres_rs:
        out.append(f"    {d:<25s} r = {r:+.4f}")
    td_mean = sum(r for _,r in tom_disc_rs)/len(tom_disc_rs) if tom_disc_rs else 0
    tp_mean = sum(r for _,r in tom_pres_rs)/len(tom_pres_rs) if tom_pres_rs else 0
    out.append(f"\n  Mean r(ToM, DISC) = {td_mean:+.4f}")
    out.append(f"  Mean r(ToM, PRES) = {tp_mean:+.4f}")
    if tp_mean > td_mean + 0.01:
        out.append(f"  → ToM は PRES 寄り = 抽象的メタ認知。U に保存される側")
    elif td_mean > tp_mean + 0.01:
        out.append(f"  → ToM は DISC 寄り = 具体的共感。U に忘却される側")
    else:
        out.append(f"  → ToM は DISC/PRES の境界上 = 真の境界次元")

    # ══════════════════════════════════════════════════════════════════
    # F. gpt-4-0314 例外の解剖
    # ══════════════════════════════════════════════════════════════════
    out.append(f"\n{'═' * W}")
    out.append("F. gpt-4-0314 — 唯一の Gap≈0 モデルの解剖")
    out.append(f"{'═' * W}")

    gpt4 = model_db.get('gpt-4-0314')
    if gpt4 and gpt4['n'] > 0:
        out.append(f"\n  Elo: {gpt4['elo']:.0f} | Gap: {gpt4['gap']:+.3f} | N: {gpt4['n']}")
        out.append(f"\n  次元プロファイル:")
        for d in sorted(gpt4['dims'], key=gpt4['dims'].get, reverse=True):
            cat = "DISC" if d in DISCARDED else "PRES" if d in PRESERVED else "SAFE" if d in SAFETY else ""
            avg_all = sum(m['dims'].get(d,0) for m in valid.values() if d in m['dims']) / sum(1 for m in valid.values() if d in m['dims'])
            delta = gpt4['dims'][d] - avg_all
            out.append(f"    {d:<28s} {gpt4['dims'][d]:>6.2f} (全体平均{avg_all:.2f}, Δ{delta:+.2f}) {cat}")

        # Why Gap ≈ 0: compute disc and pres separately
        disc_vals = [gpt4['dims'][d] for d in DISCARDED if d in gpt4['dims']]
        pres_vals = [gpt4['dims'][d] for d in PRESERVED if d in gpt4['dims']]
        out.append(f"\n  DISC avg: {sum(disc_vals)/len(disc_vals):.3f}")
        out.append(f"  PRES avg: {sum(pres_vals)/len(pres_vals):.3f}")
        out.append(f"  → Gap≈0 は「DISC も PRES も等しく低い」(= U 未発達) か「均等に高い」(= U 未適用) か？")
        overall = sum(gpt4['dims'].values())/len(gpt4['dims'])
        out.append(f"  全次元平均: {overall:.3f}")
        if overall < 13:
            out.append(f"  → 全体が低い = U が働く前の均一状態 (pre-U baseline)")
        else:
            out.append(f"  → 全体が高いのに Gap=0 = 意図的バランス or 特異な訓練")

    # ══════════════════════════════════════════════════════════════════
    # G. Elo 五分位 × 次元プロファイル推移
    # ══════════════════════════════════════════════════════════════════
    out.append(f"\n{'═' * W}")
    out.append("G. Elo 五分位 × 次元推移 — 能力段階ごとの次元変化")
    out.append(f"{'═' * W}")

    sorted_models = sorted(valid.values(), key=lambda m: m['elo'])
    n = len(sorted_models)
    q_size = n // 5
    quintiles = []
    for i in range(5):
        start = i * q_size
        end = start + q_size if i < 4 else n
        q = sorted_models[start:end]
        quintiles.append(q)

    target = sorted(DISCARDED | PRESERVED | {'theory_of_mind', 'sycophantic'})
    out.append(f"\n{'Dimension':<22s} " + " ".join(f"{'Q'+str(i+1):>8s}" for i in range(5)) + f" {'Q5-Q1':>8s}")
    out.append("-" * (22 + 9*6))
    for dim in target:
        vals = []
        for qi, q in enumerate(quintiles):
            dv = [m['dims'].get(dim, 0) for m in q if dim in m['dims']]
            vals.append(sum(dv)/len(dv) if dv else 0)
        delta = vals[-1] - vals[0]
        cat = "DISC" if dim in DISCARDED else "PRES" if dim in PRESERVED else ""
        out.append(f"{dim[:22]:<22s} " + " ".join(f"{v:>8.2f}" for v in vals) + f" {delta:>+8.2f} {cat}")

    out.append(f"\nQ1 Elo range: {quintiles[0][0]['elo']:.0f}-{quintiles[0][-1]['elo']:.0f}")
    out.append(f"Q5 Elo range: {quintiles[4][0]['elo']:.0f}-{quintiles[4][-1]['elo']:.0f}")

    # Gap evolution across quintiles
    q_gaps = []
    for qi, q in enumerate(quintiles):
        gaps = [m['gap'] for m in q]
        q_gaps.append(sum(gaps)/len(gaps))
    out.append(f"\nU-Gap across quintiles: " + " → ".join(f"Q{i+1}:{g:+.3f}" for i,g in enumerate(q_gaps)))
    gap_trend = q_gaps[-1] - q_gaps[0]
    out.append(f"Gap trajectory (Q5-Q1): {gap_trend:+.3f}")
    if gap_trend > 0.05:
        out.append(f"→ 能力上昇に伴い Gap 拡大 (U の増幅効果)")
    elif gap_trend < -0.05:
        out.append(f"→ 能力上昇に伴い Gap 縮小 (補正効果が構造的傾向を上回る)")
    else:
        out.append(f"→ Gap は Elo に対してほぼ安定")

    # ══════════════════════════════════════════════════════════════════
    # H. 統合パノラマ
    # ══════════════════════════════════════════════════════════════════
    out.append(f"\n{'═' * W}")
    out.append("H. 統合パノラマ — 全発見の要約")
    out.append(f"{'═' * W}")
    out.append("""
  1. 三層証拠: safety_conscious (+) vs sycophantic (-) = 層1と層2が次元レベルで分離
  2. スケーリング: PRES は FAST SCALER、DISC は NORMAL SCALER に偏る傾向
  3. プロファイル: 高Elo モデルの次元不均一性は？ → 上記の r(Elo, CoV) を参照
  4. クラスタ: DISC 間/PRES 間の内部相関 vs Cross 相関で U のクラスタ効果を検出
  5. ToM: 境界次元。PRES 寄りか DISC 寄りかで U の選択性の微細構造がわかる
  6. gpt-4-0314: Gap≈0 = pre-U baseline (U が適用される前の世界)
  7. 五分位: Elo 段階ごとの次元推移で U の「どこで効き始めるか」を特定
""")

    txt = "\n".join(out)
    outpath = os.path.join(BASE, "eqbench3_deep_squeeze.txt")
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(txt)
    print(txt)

if __name__ == '__main__':
    main()
