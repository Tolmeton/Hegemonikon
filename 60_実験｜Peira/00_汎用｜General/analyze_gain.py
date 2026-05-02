import json
import sys
from collections import defaultdict

gains_per_iter = defaultdict(list)
total_iters = []

try:
    with open('/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/metrics.jsonl', 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get('type') == 'iterative_deepening':
                    total_iters.append(data['iterations'])
                    curve = data.get('gain_curve', [])
                    for i, step in enumerate(curve):
                        gains_per_iter[i+1].append(step.get('info_gain', 0))
            except json.JSONDecodeError:
                pass
except FileNotFoundError:
    print('No metrics.jsonl found.')
    sys.exit(0)

print(f'{len(total_iters)} runs analyzed.')
if not total_iters:
    sys.exit(0)
    
print(f'Average iterations: {sum(total_iters)/len(total_iters):.2f}')
print('Average Information Gain per Iteration:')
for i in sorted(gains_per_iter.keys()):
    gains = gains_per_iter[i]
    avg_gain = sum(gains) / len(gains)
    print(f'  Iter {i}: {avg_gain:.4f} (N={len(gains)})')
