#!/usr/bin/env bash
# CI wrapper for Periskopē cognitive benchmark
# Runs benchmark and compares against previous results
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$PROJECT_DIR/output/benchmarks"
RESULTS_FILE="$OUTPUT_DIR/benchmark_results.json"
PREV_FILE="$OUTPUT_DIR/benchmark_results_prev.json"

cd "$PROJECT_DIR"

echo "=== Periskopē Benchmark CI ==="
echo "Date: $(date -Iseconds)"

# Backup previous results
if [[ -f "$RESULTS_FILE" ]]; then
    cp "$RESULTS_FILE" "$PREV_FILE"
    echo "Previous results backed up"
fi

# Run benchmark
PYTHONPATH=. timeout -k 15 600 .venv/bin/python scripts/benchmark_cognition.py

# Compare if previous exists
if [[ -f "$PREV_FILE" && -f "$RESULTS_FILE" ]]; then
    echo ""
    echo "=== Regression Check ==="
    PYTHONPATH=. .venv/bin/python3 -c "
import json, sys

with open('$PREV_FILE') as f:
    prev = json.load(f)
with open('$RESULTS_FILE') as f:
    curr = json.load(f)

# Compare overall scores
prev_scores = {r['query']: r.get('overall_score', 0) for r in prev['raw']}
curr_scores = {r['query']: r.get('overall_score', 0) for r in curr['raw']}

regression = False
for q in curr_scores:
    p = prev_scores.get(q, 0)
    c = curr_scores[q]
    delta = c - p
    status = '🟢' if delta >= 0 else ('🔴' if delta < -0.05 else '🟡')
    if delta < -0.05:
        regression = True
    print(f'{status} {q[:40]:40s} {p:.3f} → {c:.3f} ({delta:+.3f})')

if regression:
    print('\n⚠️  REGRESSION DETECTED: Score dropped >5pt')
    sys.exit(1)
else:
    print('\n✅ No regression detected')
"
fi
