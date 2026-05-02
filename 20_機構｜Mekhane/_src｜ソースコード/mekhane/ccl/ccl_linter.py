from __future__ import annotations
# PROOF: mekhane/ccl/ccl_linter.py
# PURPOSE: ccl モジュールの ccl_linter
"""CCL Linter — CCL 式の静的検証。

operators.md (SSOT) に基づいて CCL 式を検証し、
未定義演算子、矛盾する演算子の組合せ、ネスト深度超過を検出する。

>>> from mekhane.ccl.ccl_linter import lint
>>> warnings = lint("/noe+$zet")
>>> warnings[0].message
'未定義演算子: $'
"""


from dataclasses import dataclass
from typing import List, Optional

# 循環依存解消: spec_injector ではなく SSOT の operator_loader から直接ロード
from mekhane.ccl.operator_loader import load_operators, to_definitions_dict

# spec_injector と同じコアセットフィルタ (CCL 式の文字パースで検出するシンボル)
_CORE_SINGLE_SYMBOLS = {"+", "-", "^", "/", "?", "\\", "*", "~", "_", "!", "'"}
_CORE_COMPOUND_SYMBOLS = {"*^", "~*", ">>", "|>", "||", "~!", "*%"}

_all_loaded = load_operators()
_compound_loaded, _single_loaded, _ = to_definitions_dict(_all_loaded)
COMPOUND_OPERATORS = {k: v for k, v in _compound_loaded.items() if k in _CORE_COMPOUND_SYMBOLS}
OPERATOR_DEFINITIONS = {k: v for k, v in _single_loaded.items() if k in _CORE_SINGLE_SYMBOLS}
ALL_OPERATORS = {**COMPOUND_OPERATORS, **OPERATOR_DEFINITIONS}


# PURPOSE: [L2-auto] LintWarning のクラス定義
@dataclass
class LintWarning:
    """Lint 警告。"""
    level: str       # "error", "warning", "info"
    message: str
    position: Optional[int] = None  # CCL 式中の位置


# PURPOSE: 矛盾する演算子ペア
_CONFLICTING_PAIRS = [
    ("+", "-"),   # 深化と縮約は通常同時に使わない
]

# PURPOSE: ネスト深度上限
_MAX_NESTING = 4

# PURPOSE: 視覚的に混同しやすい演算子ペア (F5 — 2026-02-23)
_CONFUSABLE_PAIRS = [
    {
        "operator": "_",
        "confusable_with": "-",
        "meaning": "シーケンス（順次実行）",
        "confused_meaning": "軽量化",
        "regex": r"/[a-z]+_",
    },
    {
        "operator": "~",
        "confusable_with": "-",
        "meaning": "振動（反復実行）",
        "confused_meaning": "軽量化",
        "regex": r"/[a-z]+~",
    },
]

# PURPOSE: 誤解されやすい危険な演算子 (F5 — 2026-02-23)
_DANGEROUS_OPERATORS = [
    {
        "operator": "!",
        "meaning": "階乗 = 全派生同時実行",
        "common_mistake": "否定",
    },
    {
        "operator": "*^",
        "meaning": "融合 + メタ分析",
        "common_mistake": "単純な乗算",
    },
    {
        "operator": "\\",
        "meaning": "反転 (Antistrophē)",
        "common_mistake": "エスケープ文字",
    },
]

# PURPOSE: 演算子でもWF名でもないASCII記号 (CCL 的に未定義の可能性)
_KNOWN_NON_OPERATORS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n")
# WF/マクロで使うがパースしない文字 (Q-series 等の矢印も含む)
_STRUCTURAL_CHARS = set("(){}[]@:,.=|><→⇒⟹←⇔")


# PURPOSE: [L2-auto] lint の関数定義
def lint(ccl_expr: str) -> List[LintWarning]:
    """CCL 式を静的検証し、警告リストを返す。"""
    warnings: List[LintWarning] = []

    # Rule 1: 未定義演算子の検出
    all_defined = set(ALL_OPERATORS.keys())
    i = 0
    while i < len(ccl_expr):
        ch = ccl_expr[i]
        # 既知の非演算子はスキップ
        if ch in _KNOWN_NON_OPERATORS or ch in _STRUCTURAL_CHARS:
            i += 1
            continue
        # 2文字複合演算子チェック
        if i + 1 < len(ccl_expr):
            bigram = ccl_expr[i:i+2]
            if bigram in COMPOUND_OPERATORS:
                i += 2
                continue
        # 1文字演算子チェック
        if ch in OPERATOR_DEFINITIONS:
            i += 1
            continue
        # Unicode 演算子チェック (∂, ∫, Σ, √ etc.)
        if ch in all_defined:
            i += 1
            continue
        # 未定義
        warnings.append(LintWarning(
            level="warning",
            message=f"未定義演算子: {ch}",
            position=i,
        ))
        i += 1

    # Rule 2: 矛盾する演算子ペア
    found_ops = set()
    for k in ALL_OPERATORS:
        if k in ccl_expr:
            found_ops.add(k)

    for a, b in _CONFLICTING_PAIRS:
        if a in found_ops and b in found_ops:
            warnings.append(LintWarning(
                level="info",
                message=f"演算子 '{a}' と '{b}' が同時に使用されています（意図的か確認してください）",
            ))

    # Rule 3: ネスト深度チェック
    max_depth = 0
    current_depth = 0
    for ch in ccl_expr:
        if ch in "({":
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif ch in ")}":
            current_depth -= 1

    if max_depth > _MAX_NESTING:
        warnings.append(LintWarning(
            level="warning",
            message=f"ネスト深度 {max_depth} は推奨上限 {_MAX_NESTING} を超えています（let マクロで分解を推奨）",
        ))

    # Rule 4: 視覚的混同ペアの検出 (F5 — 2026-02-23)
    import re as _re
    for pair in _CONFUSABLE_PAIRS:
        matches = _re.findall(pair["regex"], ccl_expr)
        if matches:
            examples = ", ".join(f"`{m}`" for m in matches[:3])
            warnings.append(LintWarning(
                level="warning",
                message=(
                    f"`{pair['operator']}` は{pair['meaning']}です。"
                    f"`{pair['confusable_with']}`（{pair['confused_meaning']}）"
                    f"ではありません。 検出: {examples}"
                ),
            ))

    # Rule 5: 誤解されやすい危険演算子の検出 (F5 — 2026-02-23)
    for danger in _DANGEROUS_OPERATORS:
        if danger["operator"] in ccl_expr:
            warnings.append(LintWarning(
                level="warning",
                message=(
                    f"演算子 `{danger['operator']}` は"
                    f"「{danger['meaning']}」です。"
                    f"「{danger['common_mistake']}」ではありません。"
                ),
            ))

    # Rule 6: 未定義ワークフロー名の検出 (フォローアップ #4 — 2026-02-23)
    import re as _re2
    wf_names = _re2.findall(r'/([a-z]+)', ccl_expr)
    if wf_names:
        try:
            from pathlib import Path as _Path
            wf_dir = _Path(__file__).resolve().parent.parent.parent / "nous" / "workflows"
            if wf_dir.is_dir():
                existing_wfs = {p.stem for p in wf_dir.glob("*.md")}
                # マクロ名 (ccl-*) をストリップして WF 名にマッピング
                existing_wfs |= {p.stem.replace("ccl-", "") for p in wf_dir.glob("ccl-*.md")}
                for wf in set(wf_names):
                    if wf not in existing_wfs:
                        # Series 短縮形 (o, s, h, p, k, a, x, ax, t, m, c, d) は許可
                        series_shorts = {"o", "s", "h", "p", "k", "a", "x", "ax", "t", "m", "c", "d"}
                        if wf not in series_shorts and len(wf) <= 4:
                            warnings.append(LintWarning(
                                level="info",
                                message=f"ワークフロー `/{wf}` に対応する .md が見つかりません（タイポ？）",
                            ))
        except Exception:  # noqa: BLE001
            pass

    return warnings


# PURPOSE: [L2-auto] 警告対象となった演算子のセットを返す (重複排除用)
def get_warned_operators(ccl_expr: str) -> set:
    """警告対象となった演算子を返す。"""
    import re as _re
    warned = set()
    for danger in _DANGEROUS_OPERATORS:
        if danger["operator"] in ccl_expr:
            warned.add(danger["operator"])
    
    # _ vs - 混同防止
    if _re.search(r'/[a-z]+_', ccl_expr):
        warned.add("_")
    # ~ vs - 混同防止
    if _re.search(r'/[a-z]+~', ccl_expr):
        warned.add("~")
        
    return warned

if __name__ == "__main__":
    # Usage example
    test_cases = [
        "/noe+",
        "/noe+$zet",
        "/bou+_/dia-",
        "((({/noe+((/dia))}))",
    ]
    for expr in test_cases:
        result = lint(expr)
        if result:
            print(f"  {expr}:")
            for w in result:
                print(f"    [{w.level}] {w.message}")
        else:
            print(f"  {expr}: OK")
