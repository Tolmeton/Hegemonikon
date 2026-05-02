#!/usr/bin/env python3
# CCL-PL デモ — CCL → Python 変換のデモンストレーション
"""
CCL → Python トランスパイラ デモ

いくつかの CCL 式を Python に変換し、出力を比較表示する。
"""

import sys
from pathlib import Path

# パスの追加
_THIS_DIR = Path(__file__).parent
_MEKHANE_SRC = _THIS_DIR.parent.parent / "20_機構｜Mekhane" / "_src｜ソースコード"
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_MEKHANE_SRC))

from ccl_transpiler import transpile_ccl


# デモ用 CCL 式のコレクション
DEMO_EXPRESSIONS = [
    # --- 基本 ---
    ("/noe+", "単純ワークフロー (深化)"),
    ("/noe+_/dia_/ene+", "3段シーケンス (結果バケツリレー)"),
    
    # --- 融合 / 展開 ---
    ("/noe*/dia", "融合 — 2つの結果をマージ"),
    ("/noe%/dia", "展開 — 全組み合わせ"),
    
    # --- 振動 ---
    ("/u+~/noe+", "振動 — 対話的往復"),
    ("/u+~*/noe+", "収束振動 — 不動点へ"),
    ("/u+~!/noe+", "発散振動 — 可能性空間拡大"),
    
    # --- 制御構文 ---
    ("F:[×3]{/dia}", "FOR: 3回反復"),
    ("I:[V[]>0.5]{/noe+}E:{/noe-}", "IF/ELSE: 条件分岐"),
    ("W:[E[]>0.3]{/dia}", "WHILE: 条件ループ"),
    
    # --- パイプライン ---
    ("/noe+|>/dia+|>/ene+", "パイプライン: 3段変換"),
    
    # --- 複合式 ---
    ("V:{/noe+_/dia}", "検証付きシーケンス"),
    ("let analyze = /noe+~/dia", "変数束縛"),
    ("F:[×3]{/dia~*/noe}", "ループ内の収束振動"),
]


def demo():
    """デモ実行"""
    print("=" * 70)
    print("  CCL → Python トランスパイラ PoC デモ")
    print("=" * 70)
    
    for ccl_expr, description in DEMO_EXPRESSIONS:
        print(f"\n{'─' * 70}")
        print(f"  📝 {description}")
        print(f"  CCL: {ccl_expr}")
        print(f"{'─' * 70}")
        
        try:
            python_source = transpile_ccl(ccl_expr)
            print()
            for line in python_source.split("\n"):
                print(f"  {line}")
        except Exception as e:
            print(f"  ❌ エラー: {e}")
    
    print(f"\n{'=' * 70}")
    print(f"  PoC デモ完了: {len(DEMO_EXPRESSIONS)} 式を変換")
    print(f"{'=' * 70}")


def interactive():
    """対話的モード"""
    print("CCL → Python トランスパイラ (対話モード)")
    print("CCL 式を入力してください。'q' で終了。\n")
    
    while True:
        try:
            ccl_expr = input("CCL> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        
        if ccl_expr in ("q", "quit", "exit"):
            break
        
        if not ccl_expr:
            continue
        
        try:
            python_source = transpile_ccl(ccl_expr)
            print(f"\n{python_source}\n")
        except Exception as e:
            print(f"  ❌ エラー: {e}\n")


if __name__ == "__main__":
    if "--interactive" in sys.argv or "-i" in sys.argv:
        interactive()
    else:
        demo()
