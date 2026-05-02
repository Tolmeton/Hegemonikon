#!/usr/bin/env python3
"""CCL型推論の検証スクリプト"""
import ast, sys
from pathlib import Path

src = Path(r'c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード')
sys.path.insert(0, str(src))

from mekhane.symploke.code_ingest import ccl_infer_type, ccl_type_seq, ccl_type_features, ccl_feature_vector, python_to_ccl

passed = 0
failed = 0

def check(name, got, expected):
    global passed, failed
    if got == expected:
        print(f"  OK  {name}")
        passed += 1
    else:
        print(f"  FAIL {name}: got {got!r}, expected {expected!r}")
        failed += 1

print("=== 1. Token check ===")
# まず実際の ¥ 文字を code_ingest が生成するものから確認
code = "def f(x): return x"
tree = ast.parse(code)
func = tree.body[0]
ccl = python_to_ccl(func)
print(f"  CCL for 'def f(x): return x': {ccl!r}")
toks = ccl.split()
if toks:
    yen_tok = toks[0]
    print(f"  First token: {yen_tok!r} (bytes: {yen_tok.encode('utf-8')})")
    print(f"  ccl_infer_type(first_token): {ccl_infer_type(yen_tok)!r}")

print()
print("=== 2. ccl_infer_type ===")
check("fn -> T", ccl_infer_type("fn"), "T")
check("sorted -> T", ccl_infer_type("sorted"), "T")
check("~ -> P", ccl_infer_type("~"), "P")
check("^ -> M", ccl_infer_type("^"), "M")
check(">> -> None", ccl_infer_type(">>"), None)
check("# -> S", ccl_infer_type("#"), "S")
check("str_ -> S", ccl_infer_type("str_"), "S")
check("num_ -> S", ccl_infer_type("num_"), "S")
check("[def] -> M", ccl_infer_type("[def]"), "M")
check("pred -> T", ccl_infer_type("pred"), "T")
check(".append -> T", ccl_infer_type(".append"), "T")
check("() -> S", ccl_infer_type("()"), "S")

print()
print("=== 3. ccl_type_seq ===")
# Use actual CCL output from python_to_ccl
code2 = "def f(x): return sorted(x)"
tree2 = ast.parse(code2)
func2 = tree2.body[0]
ccl2 = python_to_ccl(func2)
seq2 = ccl_type_seq(ccl2)
print(f"  CCL: {ccl2!r}")
print(f"  TypeSeq: {seq2}")
check("contains T", "T" in seq2, True)
check("len >= 2", len(seq2) >= 2, True)

# Empty
check("empty -> ['S']", ccl_type_seq(""), ["S"])

# Complex
code3 = """
def process(items):
    filtered = [x for x in items if x > 0]
    result = sorted(filtered)
    return result
"""
tree3 = ast.parse(code3)
func3 = tree3.body[0]
ccl3 = python_to_ccl(func3)
seq3 = ccl_type_seq(ccl3)
print(f"  CCL (process): {ccl3!r}")
print(f"  TypeSeq (process): {seq3}")
check("process has T", "T" in seq3, True)

print()
print("=== 4. ccl_type_features ===")
feats = ccl_type_features(ccl3)
check("8d", len(feats), 8)
check("dist sums to 1", abs(sum(feats[:4]) - 1.0) < 1e-10, True)
print(f"  Features: {feats}")

print()
print("=== 5. ccl_feature_vector 51d ===")
vec = ccl_feature_vector(func3)
check("51d", len(vec), 51)
check("all float", all(isinstance(v, float) for v in vec), True)

# Verify last 8 = ccl_type_features
tf = ccl_type_features(ccl3)
check("last 8 = type_features", vec[-8:], tf)

print()
print(f"=== RESULTS: {passed} passed, {failed} failed ===")
