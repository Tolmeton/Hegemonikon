import json
import pandas as pd
import numpy as np
import pingouin as pg
import statsmodels.api as sm

def gini_coefficient(array):
    if len(array) == 0:
        return 0.0
    array = np.array(array, dtype=np.float64)
    if np.amin(array) < 0:
        array -= np.amin(array)
    array += 1e-8
    array = np.sort(array)
    index = np.arange(1, array.shape[0] + 1)
    n = array.shape[0]
    return ((np.sum((2 * index - n  - 1) * array)) / (n * np.sum(array)))

def compute_gini_components(trajectory):
    if not trajectory:
        return 0.0, 0.0, 0.0
    
    t_len, o_len, total_len = [], [], []
    for obs in trajectory:
        t = len(str(obs.get("thought", ""))) + len(str(obs.get("response", "")))
        o = len(str(obs.get("observation", "")))
        total = t + o + len(str(obs.get("action", "")))
        
        t_len.append(t)
        o_len.append(o)
        total_len.append(total)
        
    return gini_coefficient(t_len), gini_coefficient(o_len), gini_coefficient(total_len)

# Load data
data_path = "C:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/experiments/swebench_verified_with_results.jsonl"
traj_path = "C:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/experiments/swebench_verified_real_traj.jsonl"

instances = [json.loads(l) for l in open(data_path, encoding='utf-8')]
trajectories = {json.loads(l)["instance_id"]: json.loads(l)["trajectory"] for l in open(traj_path, encoding='utf-8')}

df_data = []
for inst in instances:
    iid = inst["instance_id"]
    traj = trajectories.get(iid, [])
    t_gini, o_gini, total_gini = compute_gini_components(traj)
    
    df_data.append({
        "instance_id": iid,
        "success": 1.0 if inst.get("resolved") else 0.0,
        "issue_length": len(str(inst.get("problem_statement", ""))),
        "diff_size": len(str(inst.get("patch", ""))),
        "test_size": len(str(inst.get("test_patch", ""))),
        "t_gini": t_gini,
        "o_gini": o_gini,
        "total_gini": total_gini,
        "traj_steps": len(traj)
    })

df = pd.DataFrame(df_data)

print("=== Gini Components Distribution ===")
print(df[["t_gini", "o_gini", "total_gini", "traj_steps"]].describe())

print("\n=== Correlations with Success (N=300) ===")
for col in ["t_gini", "o_gini", "total_gini"]:
    res = pg.corr(df[col], df["success"])
    print(f"{col}: r={res['r'].iloc[0]:.4f}, p={res['p_val'].iloc[0]:.4f}, BF10={res['BF10'].iloc[0]}")

print("\n=== Stratified Analysis (by diff_size quartiles) for t_gini ===")
df['diff_q'] = pd.qcut(df['diff_size'], q=4, labels=['Q1(Easiest)', 'Q2', 'Q3', 'Q4(Hardest)'])
for q in ['Q1(Easiest)', 'Q2', 'Q3', 'Q4(Hardest)']:
    sub_df = df[df['diff_q'] == q]
    res = pg.corr(sub_df["t_gini"], sub_df["success"])
    print(f"[{q}] N={len(sub_df)}: r={res['r'].iloc[0]:.4f}, p={res['p_val'].iloc[0]:.4f}, BF10={res['BF10'].iloc[0]}")

print("\n=== Stratified Analysis (by issue_length quartiles) for t_gini ===")
df['issue_q'] = pd.qcut(df['issue_length'], q=4, labels=['Q1(Shortest)', 'Q2', 'Q3', 'Q4(Longest)'])
for q in ['Q1(Shortest)', 'Q2', 'Q3', 'Q4(Longest)']:
    sub_df = df[df['issue_q'] == q]
    res = pg.corr(sub_df["t_gini"], sub_df["success"])
    print(f"[{q}] N={len(sub_df)}: r={res['r'].iloc[0]:.4f}, p={res['p_val'].iloc[0]:.4f}, BF10={res['BF10'].iloc[0]}")
