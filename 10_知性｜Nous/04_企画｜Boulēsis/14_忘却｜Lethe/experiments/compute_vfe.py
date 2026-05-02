import json
import glob
from pathlib import Path

def print_metrics():
    files = glob.glob('C:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_b_*.json')
    for path in files:
        p = Path(path)
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f'--- {p.name} ---')
        if isinstance(data, dict) and 'layers' in data:
            best_layer = max(data['layers'], key=lambda x: x.get('spearman_rho', 0))
            print(f"Best Layer {best_layer.get('layer')}: rho={best_layer.get('spearman_rho',0):.3f}, gap={best_layer.get('gap',0):.3f}, partial_rho={best_layer.get('partial_rho',0):.3f}")
        elif isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict) and 'spearman_rho' in v:
                    print(f"{k}: rho={v.get('spearman_rho',0):.3f}, gap={v.get('gap',0):.3f}")

if __name__ == '__main__':
    print_metrics()
