import sys
import os
import re
import numpy as np
import signal

def handler(signum, frame):
    raise TimeoutError("Parsing timed out")
signal.signal(signal.SIGALRM, handler)

sys.path.insert(0, os.path.abspath('20_機構｜Mekhane/_src｜ソースコード'))
from hermeneus.src.parser import CCLParser
from hermeneus.src.forgetfulness_score import fast_score_ccl_implicit, COORDINATES

def gini(array):
    array = np.array(array, dtype=np.float64)
    if np.amin(array) < 0:
        array -= np.amin(array)
    array += 1e-9  
    array = np.sort(array)
    index = np.arange(1, array.shape[0] + 1)
    n = array.shape[0]
    return (np.sum((2 * index - n  - 1) * array)) / (n * np.sum(array))

def main():
    ccl_exprs = []
    
    # 1. WFマクロ
    agents_dir = '.agents/workflows'
    if os.path.exists(agents_dir):
        for file in os.listdir(agents_dir):
            if not file.endswith('.md'): continue
            with open(os.path.join(agents_dir, file), 'r') as f:
                content = f.read()
            desc_match = re.search(r'description:\s*\"?[^—]+—\s*([^\"]+)\"?', content)
            ccl = None
            if desc_match and '/' in desc_match.group(1):
                ccl = desc_match.group(1).strip()
            else:
                sig_match = re.search(r'ccl_signature:\s*\"?([^\"]+)\"?', content)
                if sig_match and '/' in sig_match.group(1):
                    ccl = sig_match.group(1).strip()
            if ccl:
                ccl = re.sub(r'[\r\n]+', '', ccl)
                ccl_exprs.append((file, ccl))
                
    # 2. SKILL.md
    skills_dir = '10_知性｜Nous/02_手順｜Procedures/C_技能｜Skills'
    if os.path.exists(skills_dir):
        for root, _, files in os.walk(skills_dir):
            if 'SKILL.md' in files:
                with open(os.path.join(root, 'SKILL.md'), 'r') as f:
                    lines = f.readlines()
                for line in lines:
                    # Very simple regex that matches `...` blocks starting with /
                    parts = re.split(r'`', line)
                    for i in range(1, len(parts), 2):
                        m = parts[i]
                        if m.startswith('/') and len(m) > 3 and '<' not in m and '"' not in m:
                            ccl_exprs.append((f"{os.path.basename(root)}/SKILL.md", m))

    unique_map = {c: f for f, c in ccl_exprs}
    ccl_exprs = [(f, c) for c, f in unique_map.items()]
    
    print(f"Found {len(ccl_exprs)} unique CCL expressions.", flush=True)
        
    parser = CCLParser()
    coords_list = sorted(list(COORDINATES))
    s_matrix = []  
    s_implicit_scores = []
    valid_count = 0
    error_count = 0
    
    for filename, ccl_expr in ccl_exprs:
        print(f"Parsing: {ccl_expr[:50]}...", flush=True)
        try:
            signal.alarm(3) 
            res = fast_score_ccl_implicit(ccl_expr, parser)
            signal.alarm(0)
            missing = res.missing_implicit
            row = [1.0 if c in missing else 0.0 for c in coords_list]
            s_matrix.append(row)
            s_implicit_scores.append(res.s_implicit)
            valid_count += 1
            print("  -> OK", flush=True)
        except Exception as e:
            error_count += 1
            signal.alarm(0)
            print(f"  -> ERROR: {e}", flush=True)
            
    print(f"\nProcessed {valid_count} expressions (skipped {error_count})", flush=True)
    if valid_count == 0:
        return
        
    s_matrix = np.array(s_matrix)
    if s_matrix.ndim == 1:
        s_matrix = s_matrix.reshape(1, -1)
        
    p_k = np.mean(s_matrix, axis=0)
    print("\n--- 座標別忘却率 (p_k: 1に近いほどよく忘却されている) ---", flush=True)
    for c, p in zip(coords_list, p_k):
        print(f"  {c}: {p:.4f}", flush=True)
        
    gini_p = gini(p_k)
    var_p = np.var(p_k)
    print(f"\n--- 分布構造測度 ---", flush=True)
    print(f"Mean(S_implicit): {np.mean(s_implicit_scores):.4f}", flush=True)
    print(f"Var(p_k): {var_p:.4f}", flush=True)
    print(f"Gini(p_k) [Ξ_discrete]: {gini_p:.4f}", flush=True)

if __name__ == '__main__':
    main()
