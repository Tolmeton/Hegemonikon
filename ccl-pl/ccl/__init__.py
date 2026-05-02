# CCL-PL: 圏論的構造を持つ汎用プログラミング言語
"""
CCL-PL (Cognitive Control Language - Programming Language)

演算子に圏論的意味論が直接埋め込まれたプログラミング言語。

固有性:
  1. 双対が first-class: adjoint compress <=> decompress → \\compress で自動逆転
  2. 振動が first-class: analyze ~* synthesize で不動点計算
  3. 射が 6 方向: >>, <<, >*, <*, *>, >%
  4. 代数/余代数が演算子: * = catamorphism(fold), % = anamorphism(unfold)
"""

__version__ = "0.1.0"
