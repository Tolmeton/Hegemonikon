# CCL-PL 組込み関数 (prelude)
"""
CCL-PL Prelude — 全 CCL プログラムで自動的に利用可能な関数群

認知動詞は含まない (それは stdlib/hgk/ で提供)。
ここには汎用的な入出力・数学・データ操作関数のみ。
"""

import json
import math
from typing import Any, Callable, List


# =============================================================================
# 入出力
# =============================================================================

def print_result(value: Any) -> Any:
    """値を出力し、そのまま返す (パイプライン内で使えるように)"""
    print(value)
    return value


def read_input(prompt: str = "") -> str:
    """標準入力から1行読む"""
    return input(prompt)


def read_file(path: str) -> str:
    """ファイルの内容を文字列として読む"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str) -> str:
    """文字列をファイルに書く"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# =============================================================================
# 数学
# =============================================================================

def add(a: float, b: float) -> float:
    return a + b

def sub(a: float, b: float) -> float:
    return a - b

def mul(a: float, b: float) -> float:
    return a * b

def div(a: float, b: float) -> float:
    if b == 0:
        raise ZeroDivisionError("0 による除算")
    return a / b

def mod(a: float, b: float) -> float:
    return a % b

def pow_(a: float, b: float) -> float:
    return a ** b

def sqrt(x: float) -> float:
    return math.sqrt(x)

def abs_(x: float) -> float:
    return abs(x)

def sin(x: float) -> float:
    return math.sin(x)

def cos(x: float) -> float:
    return math.cos(x)

def log(x: float) -> float:
    return math.log(x)

def exp(x: float) -> float:
    return math.exp(x)

def floor(x: float) -> int:
    return math.floor(x)

def ceil(x: float) -> int:
    return math.ceil(x)


# =============================================================================
# データ操作
# =============================================================================

def length(x: Any) -> int:
    """長さを返す"""
    return len(x)

def head(lst: list) -> Any:
    """リストの先頭要素"""
    if not lst:
        return None
    return lst[0]

def tail(lst: list) -> list:
    """リストの先頭以外"""
    return lst[1:]

def append(lst: list, item: Any) -> list:
    """リストに要素を追加 (新リストを返す)"""
    return lst + [item]

def map_fn(fn: Callable, lst: list) -> list:
    """各要素に関数を適用"""
    return [fn(item) for item in lst]

def filter_fn(fn: Callable, lst: list) -> list:
    """条件を満たす要素のみ"""
    return [item for item in lst if fn(item)]

def reduce_fn(fn: Callable, lst: list, init: Any = None) -> Any:
    """畳み込み"""
    from functools import reduce
    if init is not None:
        return reduce(fn, lst, init)
    return reduce(fn, lst)

def range_fn(start: int, end: int = None, step: int = 1) -> list:
    """範囲リスト"""
    if end is None:
        return list(range(start))
    return list(range(start, end, step))

def sort_fn(lst: list, key: Callable = None, reverse: bool = False) -> list:
    """ソート"""
    return sorted(lst, key=key, reverse=reverse)

def reverse_fn(lst: list) -> list:
    """逆順"""
    return list(reversed(lst))


# =============================================================================
# JSON
# =============================================================================

def json_parse(text: str) -> Any:
    """JSON 文字列をパース"""
    return json.loads(text)

def json_dump(obj: Any) -> str:
    """オブジェクトを JSON 文字列に変換"""
    return json.dumps(obj, ensure_ascii=False, indent=2)


# =============================================================================
# 型変換
# =============================================================================

def to_int(x: Any) -> int:
    return int(x)

def to_float(x: Any) -> float:
    return float(x)

def to_str(x: Any) -> str:
    return str(x)

def to_list(x: Any) -> list:
    return list(x)


# =============================================================================
# Prelude のエクスポート (executor が使用)
# =============================================================================

def get_prelude() -> dict:
    """Prelude の全関数を辞書として返す"""
    return {
        # IO
        "print": print_result,
        "input": read_input,
        "read_file": read_file,
        "write_file": write_file,
        # 数学
        "add": add, "sub": sub, "mul": mul, "div": div, "mod": mod,
        "pow": pow_, "sqrt": sqrt, "abs": abs_,
        "sin": sin, "cos": cos, "log": log, "exp": exp,
        "floor": floor, "ceil": ceil,
        # データ
        "len": length, "head": head, "tail": tail, "append": append,
        "map": map_fn, "filter": filter_fn, "reduce": reduce_fn,
        "range": range_fn, "sort": sort_fn, "reverse": reverse_fn,
        # JSON
        "json_parse": json_parse, "json_dump": json_dump,
        # 型変換
        "int": to_int, "float": to_float, "str": to_str, "list": to_list,
        # Python 組込み
        "True": True, "False": False, "None": None,
        "type": type, "isinstance": isinstance,
    }
