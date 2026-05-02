#!/usr/bin/env python3
"""
デモ: 修飾子 (Dokimasia) の効果 — v4.1

CCL 式に修飾子を与えたとき、どのようにプロンプト (LMQL) に反映されるかを可視化する。
"""

import sys
from pathlib import Path

# パッケージパス追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from hermeneus.src.dispatch import dispatch
from hermeneus.src import compile_ccl

def show_demo(ccl_expr: str):
    print("=" * 60)
    print(f"▼ CCL 式: {ccl_expr}")
    print("=" * 60)
    
    # 1. Dispatch で修飾子構成をプレビュー
    res = dispatch(ccl_expr)
    plan = res.get("plan_template", "")
    
    in_mod = False
    mod_lines = []
    for line in plan.split("\n"):
        if line.startswith("【修飾子 (Dokimasia パラメータ)】"):
            in_mod = True
            mod_lines.append(line)
        elif in_mod and line.startswith("【"):
            break
        elif in_mod:
            mod_lines.append(line)
            
    if mod_lines:
        print("\n".join(mod_lines))
    else:
        print("【修飾子】なし")
        
    # 2. LMQL へのコンパイルで実際に追加されたプロンプトを確認
    lmql = compile_ccl(ccl_expr)
    
    print("\n【出力された LMQL の修飾子指示部分】")
    # LMQL の '追加制約:' や '【Value:' 等の行を抽出して表示
    prompt_lines = []
    for line in lmql.split("\n"):
        if "【Value:" in line or "【Function:" in line or "【Precision:" in line or "【Scale:" in line or "【Valence:" in line or "【Temporality:" in line:
            prompt_lines.append(line.strip(' "'))
            
    if prompt_lines:
        for p in prompt_lines:
            # 表示用に改行 \n を実際の改行に戻す
            print(p.replace("\\n", "\n  "))
    else:
        print("  (修飾子による追加指示なし)")
    
    print()

if __name__ == "__main__":
    examples = [
        "/noe",              # デフォルト修飾子の例
        "/noe[Va:P]",        # ユーザー明示指定によるデフォルト上書き
        "/dia[critical]",    # プリセット展開 + デフォルトマージ
        "/ske[innovative]",  # 創造的探索のプリセット
    ]
    
    print("修飾子 (Dokimasia) の動作デモ\n")
    for ex in examples:
        show_demo(ex)
