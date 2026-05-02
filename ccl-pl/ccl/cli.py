# CCL-PL CLI
"""
CCL-PL コマンドラインインターフェース

使い方:
    ccl run <file.ccl>       CCL ファイルを実行
    ccl repl                 対話的実行環境を起動
    ccl parse <expr>         CCL 式の AST をダンプ
    ccl transpile <expr>     CCL 式を Python に変換
    ccl check <file.ccl>     構文チェック
    ccl version              バージョン表示
"""

import argparse
import sys
from pathlib import Path

from ccl import __version__
from ccl.errors import CCLError, report_error


def cmd_run(args: argparse.Namespace) -> int:
    """CCL ファイルを実行"""
    from ccl.executor import CCLExecutor

    filepath = Path(args.file)
    if not filepath.exists():
        print(f"error: ファイルが見つかりません: {args.file}", file=sys.stderr)
        return 1

    # .ccl 以外も許容 (ただし警告)
    if filepath.suffix != ".ccl":
        print(f"warn: CCL ファイルでない拡張子: {filepath.suffix}", file=sys.stderr)

    source = filepath.read_text(encoding="utf-8")

    executor = CCLExecutor()
    try:
        result = executor.execute(source, filename=str(filepath))
        if result is not None and not args.quiet:
            print(result)
    except CCLError as e:
        report_error(e)
        return 1
    except Exception as e:
        from ccl.errors import report_python_error
        report_python_error(e, ccl_source=source, filename=str(filepath))
        return 1

    return 0


def cmd_repl(_args: argparse.Namespace) -> int:
    """REPL を起動"""
    from ccl.repl import REPL
    repl = REPL()
    repl.run()
    return 0


def cmd_parse(args: argparse.Namespace) -> int:
    """CCL 式の AST をダンプ"""
    from ccl.executor import CCLExecutor

    executor = CCLExecutor()
    try:
        ast = executor.get_ast(args.expr)
        print(ast)
    except CCLError as e:
        report_error(e)
        return 1
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    return 0


def cmd_transpile(args: argparse.Namespace) -> int:
    """CCL 式を Python に変換"""
    from ccl.executor import CCLExecutor

    executor = CCLExecutor()
    try:
        py_source = executor.get_transpiled(args.expr)
        print(py_source)
    except CCLError as e:
        report_error(e)
        return 1
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """CCL ファイルの構文チェック"""
    from ccl.executor import CCLExecutor

    filepath = Path(args.file)
    if not filepath.exists():
        print(f"error: ファイルが見つかりません: {args.file}", file=sys.stderr)
        return 1

    source = filepath.read_text(encoding="utf-8")
    executor = CCLExecutor()

    # 各行をパースして構文チェック
    errors = []
    for i, line in enumerate(source.split("\n"), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            executor.get_ast(stripped)
        except Exception as e:
            errors.append((i, stripped, str(e)))

    if errors:
        for line_no, line_text, err_msg in errors:
            print(f"  {filepath}:{line_no}: {err_msg}", file=sys.stderr)
            print(f"    {line_text}", file=sys.stderr)
        print(f"\n{len(errors)} 件のエラー", file=sys.stderr)
        return 1
    else:
        print(f"✓ {filepath}: 構文OK")
        return 0


def cmd_version(_args: argparse.Namespace) -> int:
    """バージョン表示"""
    print(f"CCL-PL v{__version__}")
    return 0


def main() -> None:
    """CLI エントリポイント"""
    parser = argparse.ArgumentParser(
        prog="ccl",
        description="CCL-PL: 圏論的構造を持つ汎用プログラミング言語",
    )
    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    # ccl run <file>
    p_run = subparsers.add_parser("run", help="CCL ファイルを実行")
    p_run.add_argument("file", help="実行する .ccl ファイル")
    p_run.add_argument("-q", "--quiet", action="store_true", help="結果を出力しない")
    p_run.set_defaults(func=cmd_run)

    # ccl repl
    p_repl = subparsers.add_parser("repl", help="対話的実行環境を起動")
    p_repl.set_defaults(func=cmd_repl)

    # ccl parse <expr>
    p_parse = subparsers.add_parser("parse", help="CCL 式の AST をダンプ")
    p_parse.add_argument("expr", help="CCL 式")
    p_parse.set_defaults(func=cmd_parse)

    # ccl transpile <expr>
    p_transpile = subparsers.add_parser("transpile", help="CCL 式を Python に変換")
    p_transpile.add_argument("expr", help="CCL 式")
    p_transpile.set_defaults(func=cmd_transpile)

    # ccl check <file>
    p_check = subparsers.add_parser("check", help="CCL ファイルの構文チェック")
    p_check.add_argument("file", help="チェックする .ccl ファイル")
    p_check.set_defaults(func=cmd_check)

    # ccl version
    p_version = subparsers.add_parser("version", help="バージョン表示")
    p_version.set_defaults(func=cmd_version)

    args = parser.parse_args()

    if args.command is None:
        # コマンドなし → REPL 起動
        from ccl.repl import REPL
        repl = REPL()
        repl.run()
        return

    exit_code = args.func(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
