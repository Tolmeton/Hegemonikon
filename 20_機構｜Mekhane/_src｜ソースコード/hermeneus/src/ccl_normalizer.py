# PROOF: [L2/インフラ] <- hermeneus/src/ccl_normalizer.py CCL 入力正規化
"""
CCL Input Normalizer — /ccl-xxx を @xxx に正規化する単一責任モジュール

設計原則:
  - DRY: 正規表現パターンは mekhane/ccl/macro_expander.py と同一構造
  - 入力層集約: dispatch, MacroExecutor, mcp_server が全てここを経由
  - 拡張性: ハイフン入りマクロ名 (/ccl-cross-review) にも対応
  - 依存方向: hermeneus → mekhane への逆向き import を避ける (AP-2)

Origin: 2026-02-25 /fit_/noe*/dia D1-D2 修復
"""

import re
from typing import Optional, Tuple

# CCL マクロ名パターン (共通構造):
#   名前: 英数字 + ハイフン区切り。末尾は英数字を保証。
#   派生: +, -, ^ の任意の組み合わせ。
# ⚠️ このパターンは mekhane/ccl/macro_expander.py の MACRO_PATTERN と同一構造。
#    変更時は両方を同期すること。
_MACRO_NAME_RE = r'([\w]+(?:-[\w]+)*)'
_DERIVATIVE_RE = r'([+\-^]*)'

# /ccl-{name}[{derivative}]
_CCL_MACRO_PATTERN = re.compile(r'^/ccl-' + _MACRO_NAME_RE + _DERIVATIVE_RE + r'$')

# @{name}[{derivative}]
_AT_MACRO_PATTERN = re.compile(r'^@' + _MACRO_NAME_RE + _DERIVATIVE_RE + r'$')


def normalize_ccl_input(ccl: str) -> str:
    """CCL 入力を正規化: /ccl-plan- → @plan-, → → _

    変換規則:
        /ccl-plan   → @plan
        /ccl-plan-  → @plan-
        /ccl-dig+   → @dig+
        /ccl-xrev   → @xrev
        /noe+       → /noe+  (変換なし — マクロではない)
        @plan       → @plan  (変換なし — 既にマクロ形式)
        /ops → /dio → /ops _ /dio  (Unicode 矢印をシーケンス演算子に変換)

    Returns:
        正規化された CCL 文字列
    """
    stripped = ccl.strip()

    # Phase 1: Unicode 矢印 → CCL シーケンス演算子 `_`
    # ドキュメント用の記法 (→, ⟹, ⇒) がそのまま入力されるケース対応
    # ただし Q[X→Y] 内の → は Q-series 構文なので保護する
    q_blocks = []
    def _protect_q_block(m):
        q_blocks.append(m.group(0))
        return f"__Q_BLOCK_{len(q_blocks) - 1}__"
    stripped = re.sub(r'Q\[[^\]]*\]', _protect_q_block, stripped)
    for arrow in ('⟹', '⇒', '→'):
        if arrow in stripped:
            stripped = stripped.replace(arrow, '_')
    # Q[...] ブロックを復元
    for i, block in enumerate(q_blocks):
        stripped = stripped.replace(f"__Q_BLOCK_{i}__", block)

    # Phase 2: /ccl-xxx → @xxx マクロ正規化
    m = _CCL_MACRO_PATTERN.match(stripped)
    if m:
        return f"@{m.group(1)}{m.group(2)}"
    return stripped


def is_ccl_macro(ccl: str) -> bool:
    """CCL 入力がマクロ形式かを判定

    Returns:
        True if ccl starts with @ or matches /ccl-* pattern
    """
    stripped = ccl.strip()
    if stripped.startswith("@"):
        return True
    return _CCL_MACRO_PATTERN.match(stripped) is not None


def parse_ccl_macro(ccl: str) -> Optional[Tuple[str, str]]:
    """CCL マクロ入力を (name, derivative) に分解

    Returns:
        (name, derivative) tuple or None if not a macro
        例: /ccl-plan- → ("plan", "-"), @dig+ → ("dig", "+")
    """
    stripped = ccl.strip()
    m = _CCL_MACRO_PATTERN.match(stripped)
    if m:
        return m.group(1), m.group(2)

    # @xxx[+-^] 形式
    m2 = _AT_MACRO_PATTERN.match(stripped)
    if m2:
        return m2.group(1), m2.group(2)

    return None
