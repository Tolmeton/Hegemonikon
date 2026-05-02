# CCL-PL エラー報告
"""
CCL-PL エラー報告モジュール

行番号・カラム付きの人間が読めるエラーメッセージを生成する。
"""

import sys
from dataclasses import dataclass
from typing import Optional

# ANSI カラーコード (ターミナル対応時)
_USE_COLOR = hasattr(sys.stderr, "isatty") and sys.stderr.isatty()

class _C:
    """ANSI カラー定数"""
    RED = "\033[91m" if _USE_COLOR else ""
    YELLOW = "\033[93m" if _USE_COLOR else ""
    CYAN = "\033[96m" if _USE_COLOR else ""
    BOLD = "\033[1m" if _USE_COLOR else ""
    DIM = "\033[2m" if _USE_COLOR else ""
    RESET = "\033[0m" if _USE_COLOR else ""


@dataclass
class SourceLocation:
    """ソース位置情報"""
    file: str = "<repl>"
    line: int = 1
    col: int = 1
    source_line: str = ""


class CCLError(Exception):
    """CCL-PL エラーの基底クラス"""

    def __init__(self, message: str, loc: Optional[SourceLocation] = None):
        self.message = message
        self.loc = loc
        super().__init__(self.format())

    def format(self) -> str:
        """色付きフォーマットでエラーを表示"""
        parts = []

        if self.loc:
            parts.append(
                f"{_C.BOLD}{self.loc.file}:{self.loc.line}:{self.loc.col}{_C.RESET}"
            )

        parts.append(f"{_C.RED}{_C.BOLD}error{_C.RESET}: {self.message}")

        if self.loc and self.loc.source_line:
            parts.append(f"  {_C.DIM}{self.loc.line} |{_C.RESET} {self.loc.source_line}")
            # キャレットでエラー位置を指示
            pointer = " " * (len(str(self.loc.line)) + 3 + self.loc.col - 1) + f"{_C.RED}^{_C.RESET}"
            parts.append(pointer)

        return "\n".join(parts)


class CCLParseError(CCLError):
    """パースエラー"""
    pass


class CCLRuntimeError(CCLError):
    """実行時エラー"""
    pass


class CCLNameError(CCLError):
    """未定義の名前"""
    pass


class CCLTypeError(CCLError):
    """型エラー (将来の型システム用)"""
    pass


def report_error(error: CCLError) -> None:
    """エラーを stderr に出力"""
    print(error.format(), file=sys.stderr)


def report_python_error(exc: Exception, ccl_source: str = "", filename: str = "<repl>") -> None:
    """Python 例外を CCL エラーとして報告"""
    loc = SourceLocation(file=filename, source_line=ccl_source)
    ccl_err = CCLRuntimeError(f"{type(exc).__name__}: {exc}", loc=loc)
    report_error(ccl_err)
