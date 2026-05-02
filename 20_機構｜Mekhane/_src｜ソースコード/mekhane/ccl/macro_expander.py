# PROOF: [L1/定理] <- mekhane/ccl/macro_expander.py CCL→CCLパーサーが必要→macro_expander が担う
"""
CCL Macro Expander

Expands @macro references in CCL expressions.
Part of CCL v2.1 macro system.

v4 (2026-02-25): 派生 (+/-/^) を文字列連結ではなく分離して返す。
  派生は深度パラメータであり、マクロ展開後のCCL文字列を変更すべきではない。
"""

import re
from typing import Tuple, Optional
from .macro_registry import MacroRegistry


# PURPOSE: Expands @macro references in CCL expressions.
class MacroExpander:
    """Expands @macro references in CCL expressions."""

    # Pattern to match @macro_name with optional derivatives (+, -, ^)
    # 派生 (-) がマクロ名に含まれないよう、名前は英数字で終わることを保証
    MACRO_PATTERN = re.compile(r"@([\w]+(?:-[\w]+)*)([+\-^]*)")

    # Pattern to match old @N level syntax (for migration)
    OLD_LEVEL_PATTERN = re.compile(r"(@)(\d+)(?!\w)")

    # PURPOSE: Initialize the expander.
    def __init__(self, registry: Optional[MacroRegistry] = None):
        """
        Initialize the expander.

        Args:
            registry: Macro registry to use
        """
        self.registry = registry or MacroRegistry()

    # PURPOSE: Expand all @macro references in a CCL expression.
    def expand(self, ccl: str) -> Tuple[str, bool, str]:
        """
        Expand all @macro references in a CCL expression.

        派生 (+/-/^) はCCL文字列に適用せず、分離して返す。
        派生は深度パラメータとして呼び出し元で処理すべき。

        Args:
            ccl: CCL expression possibly containing @macros

        Returns:
            Tuple of (expanded CCL, whether expansion occurred, derivative string)
            例: expand("@plan-") → ("/bou-_/met_...", True, "-")
        """
        expanded_flag = False
        collected_derivative = ""

        def repl_macro(match):
            nonlocal expanded_flag, collected_derivative
            name = match.group(1)
            deriv = match.group(2)

            # Skip if it's a number (that's a level, not a macro)
            if name.isdigit():
                return match.group(0)

            macro = self.registry.get(name)
            if macro:
                # 派生は分離して保持 — CCL文字列には適用しない
                if deriv:
                    collected_derivative = deriv

                self.registry.record_usage(name)
                expanded_flag = True
                return macro.ccl

            return match.group(0)

        result = self.MACRO_PATTERN.sub(repl_macro, ccl)
        return result, expanded_flag, collected_derivative

    # PURPOSE: Migrate old @N level syntax to new :N syntax.
    def migrate_level_syntax(self, ccl: str) -> str:
        """
        Migrate old @N level syntax to new :N syntax.

        Args:
            ccl: CCL expression with old @N syntax

        Returns:
            CCL with :N syntax
        """
        # Replace @N with :N where N is a digit
        # But only when @ is followed by just digits (not a macro name)
        return self.OLD_LEVEL_PATTERN.sub(r":\2", ccl)

    # PURPOSE: Check if expression contains macro references.
    def has_macros(self, ccl: str) -> bool:
        """Check if expression contains macro references."""
        for match in self.MACRO_PATTERN.finditer(ccl):
            name = match.group(1)
            if not name.isdigit() and self.registry.get(name):
                return True
        return False

    # PURPOSE: List all macros used in an expression.
    def list_macros_in_expr(self, ccl: str) -> list:
        """List all macros used in an expression."""
        macros = []
        for match in self.MACRO_PATTERN.finditer(ccl):
            name = match.group(1)
            if not name.isdigit():
                macro = self.registry.get(name)
                if macro:
                    macros.append(macro)
        return macros
