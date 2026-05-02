#!/usr/bin/env python3
"""CCL 型推論の手動検証スクリプト"""
import sys
from pathlib import Path
import ast

# mekhane パスを追加
_root = Path(r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon")
sys.path.insert(0, str(_root / "20_機構｜Mekhane" / "_src｜ソースコード"))

from mekhane.symploke.code_ingest import (
    ccl_infer_type, ccl_type_seq, ccl_type_features,
    ccl_feature_vector, python_to_ccl,
)

errors = []

print("=== ccl_infer_type ===")
for tok, expected in [
    ('¥', 'S'), ('#', 'S'), ('str_', 'S'), ('num_', 'S'), ('()', 'S'),
    ('fn', 'T'), ('sorted', 'T'), ('.append', 'T'), ('pred', 'T'),
    ('~', 'P'), ('^', 'M'), ('[def]', 'M'),
    ('>>', None), ('(', None), ('*', None),
]:
    result = ccl_infer_type(tok)
    status = "OK" if result == expected else f"FAIL (got {result})"
    if result != expected:
        errors.append(f"ccl_infer_type('{tok}'): expected {expected}, got {result}")
    print(f"  {tok:12s} -> {str(result):6s} {status}")

print("\n=== ccl_type_seq ===")
for ccl, expected in [
    ("¥ >> sorted", ['S', 'T']),
    ("#", ['S']),
    ("", ['S']),
    ("fn >> fn >> fn", ['T', 'T', 'T']),
]:
    result = ccl_type_seq(ccl)
    status = "OK" if result == expected else f"FAIL (got {result})"
    if result != expected:
        errors.append(f"ccl_type_seq('{ccl}'): expected {expected}, got {result}")
    print(f"  {ccl:30s} -> {result} {status}")

print("\n=== Real functions ===")
codes = [
    ("simple",      "def f(x): return sorted(x)"),
    ("filter_map",  "def g(items):\n    filtered = [x for x in items if x > 0]\n    return sorted(filtered)"),
    ("conditional", "def h(x):\n    if x > 0:\n        return x\n    else:\n        return 0"),
]
for name, code in codes:
    tree = ast.parse(code)
    func = tree.body[0]
    ccl = python_to_ccl(func)
    seq = ccl_type_seq(ccl)
    features = ccl_type_features(ccl)
    vec = ccl_feature_vector(func)
    print(f"\n  [{name}]")
    print(f"    CCL:      {ccl}")
    print(f"    TypeSeq:  {seq}")
    print(f"    type_f:   {[round(x, 3) for x in features]}")
    print(f"    vec dim:  {len(vec)}")
    if len(vec) != 51:
        errors.append(f"{name}: vec dim = {len(vec)}, expected 51")

print("\n=== Distribution sum ===")
features = ccl_type_features("¥ >> fn >> V:{pred} >> return")
dist_sum = sum(features[:4])
print(f"  sum = {dist_sum}")
if abs(dist_sum - 1.0) > 1e-10:
    errors.append(f"distribution sum = {dist_sum}, expected 1.0")

print("\n=== Feature vector match ===")
code = "def f(x, y): return x + y"
tree = ast.parse(code)
func = tree.body[0]
vec = ccl_feature_vector(func)
ccl_text = python_to_ccl(func)
tf = ccl_type_features(ccl_text)
match = vec[-8:] == tf
print(f"  last 8 match: {match}")
if not match:
    errors.append(f"feature vector last 8 mismatch: {vec[-8:]} != {tf}")

print(f"\n{'=' * 40}")
if errors:
    print(f"FAILED: {len(errors)} errors")
    for e in errors:
        print(f"  - {e}")
else:
    print("ALL PASSED")
