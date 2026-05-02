"""Shadow Gemini --- 後方互換ラッパー。

全実装は mekhane.mcp.daimonion に移行済み。
このモジュールは既存コードの import 互換性のためだけに存在する。
"""
from mekhane.mcp.daimonion import (  # noqa: F401
    Daimonion as ShadowGemini,
    DaimonionFinding as ShadowFinding,
    DaimonionResult as ShadowResult,
    ActionRecord,
    get_daimonion as get_shadow,
)
