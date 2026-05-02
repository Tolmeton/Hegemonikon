"""Lēthē 相補型チェックの動作検証スクリプト"""
import json
from pathlib import Path
from mekhane.basanos.verify_on_edit import _check_structural_duplicates

sr = Path(r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード")

def test_file(target_file):
    print(f"\n============================================================")
    print(f"Testing: {Path(target_file).name}")
    dupes = _check_structural_duplicates([target_file], sr)
    
    exact = [d for d in dupes if d.get("type") == "exact"]
    similar = [d for d in dupes if d.get("type") == "similar"]
    
    print(f"\n--- Layer 1: R1 Exact (Alerts) : {len(exact)} ---")
    for d in exact[:5]:
        print(f"  🔴 {d['source_func']:30s} = {d['similar_func']:30s} ({Path(d['similar_file']).name}:{d['similar_line']})")
        
    print(f"\n--- Layer 2: 43d Similar (Hints) : {len(similar)} ---")
    for d in similar[:5]:
        print(f"  💡 {d['source_func']:30s} ≈ {d['similar_func']:30s} ({Path(d['similar_file']).name}:{d['similar_line']}) cos={d['cosine']:.4f}")

# テスト1: llm_evaluator.py (R1 同型 _load_fep_prompt を含む)
test_file(str(sr / "mekhane" / "fep" / "llm_evaluator.py"))

# テスト2: sympatheia_mcp_server.py
test_file(str(sr / "mekhane" / "mcp" / "sympatheia_mcp_server.py"))

# テスト3: hgk_gateway_sympatheia.py
test_file(str(sr / "mekhane" / "mcp" / "hgk_gateway_sympatheia.py"))
