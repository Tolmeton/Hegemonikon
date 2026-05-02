import json
import sys
from pathlib import Path

def get_best_rho(filepath):
    p = Path(filepath)
    if not p.exists(): return None
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if 'layers' in data:
        return max(l.get('spearman_rho', 0) for l in data['layers'])
    elif 'B1: TF-IDF' in data:
        return data['B1: TF-IDF'].get('spearman_rho', 0)
    return None

def main():
    base_dir = Path("C:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments")
    
    # VFE(0): TF-IDF on P3a
    rho_0 = get_best_rho(base_dir / "phase_b_baselines.json")
    vfe_0 = 1.0 - rho_0 if rho_0 else None
    
    models = ["codebert", "codellama", "mistral"]
    
    print("=== P7 VFE 単調性 (H4) の検証 ===")
    print("VFE(n) = 1 - Spearman_ρ(n)")
    print(f"VFE(0) [TF-IDF Baseline]: {vfe_0:.3f}\n")
    
    for m in models:
        # VFE(1): P3b (Real world, mostly U_arrow local structure)
        rho_1 = get_best_rho(base_dir / f"phase_b_{m}_p3b.json")
        vfe_1 = 1.0 - rho_1 if rho_1 else None
        
        # VFE(1.5): P3a (Synthetic, U_compose synthetic structure)
        rho_15 = get_best_rho(base_dir / f"phase_b_{m}.json")
        vfe_15 = 1.0 - rho_15 if rho_15 else None
        
        if vfe_1 and vfe_15:
            is_monotonic = (vfe_0 >= vfe_1 >= vfe_15)
            print(f"Model: {m}")
            print(f"  VFE(1)   [P3b]: {vfe_1:.3f}")
            print(f"  VFE(1.5) [P3a]: {vfe_15:.3f}")
            print(f"  Monotonic (VFE(0) >= VFE(1) >= VFE(1.5)): {'✅ PASS' if is_monotonic else '❌ FAIL'}\n")

if __name__ == '__main__':
    main()
