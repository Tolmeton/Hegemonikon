# CCL-PL REPL (対話的実行環境)
"""
CCL-PL REPL — 対話的にCCLを書いて実行する

機能:
  - 複数行入力 (未完結式の検出)
  - セッション内変数保持
  - 色付きプロンプトとエラー
  - メタコマンド (:help, :ast, :py, :quit)
  - 履歴 (readline)
"""

import sys
import os
from typing import Optional

from ccl.errors import CCLError, report_error

# readline は Unix/Windows で動作が異なる
try:
    import readline  # noqa: F401
    _HAS_READLINE = True
except ImportError:
    _HAS_READLINE = False


# ANSI カラー
_USE_COLOR = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    if _USE_COLOR:
        return f"\033[{code}m{text}\033[0m"
    return text


BANNER = f"""
{_c("96;1", "CCL-PL")} v0.1.0 — 圏論的構造を持つ汎用プログラミング言語
{_c("2", "演算子: _ (seq)  * (fold)  % (unfold)  ~ (oscillate)  ~* (converge)")}
{_c("2", "        >> (forward)  << (reverse)  \\\\ (dual)  || (adjoint)")}
{_c("2", ":help でヘルプ  :quit で終了")}
"""

HELP_TEXT = """
{bold}CCL-PL REPL コマンド:{reset}

  {cyan}:help{reset}       このヘルプを表示
  {cyan}:quit{reset}       REPL を終了 (Ctrl+D でも可)
  {cyan}:ast EXPR{reset}   CCL 式の AST をダンプ
  {cyan}:py EXPR{reset}    CCL 式のトランスパイル結果 (Python) を表示
  {cyan}:vars{reset}       現在のスコープ内変数を表示
  {cyan}:clear{reset}      スコープをクリア

{bold}CCL 演算子:{reset}

  {cyan}_  {reset}  シーケンス (逐次実行)      |  {cyan}*  {reset}  融合 (catamorphism/fold)
  {cyan}%  {reset}  展開 (anamorphism/unfold)   |  {cyan}~  {reset}  振動 (2操作の循環)
  {cyan}~* {reset}  収束振動 (不動点探索)       |  {cyan}~! {reset}  発散振動 (全軌跡)
  {cyan}>> {reset}  順射 (pushforward)          |  {cyan}<< {reset}  逆射 (pullback)
  {cyan}>* {reset}  射的融合 (lax actegory)     |  {cyan}<* {reset}  逆射融合 (oplax)
  {cyan}\\  {reset}  双対 (dual)                |  {cyan}|| {reset}  随伴宣言 (adjoint)
""".format(
    bold="\033[1m" if _USE_COLOR else "",
    reset="\033[0m" if _USE_COLOR else "",
    cyan="\033[96m" if _USE_COLOR else "",
)


class REPL:
    """CCL-PL REPL"""

    def __init__(self):
        from ccl.executor import CCLExecutor
        self.executor = CCLExecutor()
        self._buffer: list = []  # 複数行入力バッファ

    def run(self) -> None:
        """REPL メインループ"""
        print(BANNER)

        while True:
            try:
                prompt = _c("92;1", "ccl> ") if not self._buffer else _c("2", "...> ")
                line = input(prompt)
            except (EOFError, KeyboardInterrupt):
                print("\n" + _c("2", "bye."))
                break

            # メタコマンド
            if line.strip().startswith(":"):
                self._handle_meta(line.strip())
                continue

            # 空行: バッファがあれば実行
            if not line.strip():
                if self._buffer:
                    self._execute_buffer()
                continue

            # バッファに追加
            self._buffer.append(line)

            # 単行の場合は即実行
            if len(self._buffer) == 1 and self._is_complete(line):
                self._execute_buffer()

    def _is_complete(self, line: str) -> bool:
        """式が完結しているか判定"""
        # 未閉じブレースやパイプラインの途中は incomplete
        stripped = line.strip()
        if stripped.endswith("_") or stripped.endswith("~"):
            return False  # シーケンス/振動の途中
        if stripped.count("{") > stripped.count("}"):
            return False  # 未閉じブレース
        if stripped.count("[") > stripped.count("]"):
            return False  # 未閉じブラケット
        if stripped.count("(") > stripped.count(")"):
            return False  # 未閉じ括弧
        return True

    def _execute_buffer(self) -> None:
        """バッファの内容を実行"""
        source = "\n".join(self._buffer)
        self._buffer.clear()

        if not source.strip():
            return

        try:
            result = self.executor.execute(source)
            if result is not None:
                print(_c("93", f"=> {repr(result)}"))
        except CCLError as e:
            report_error(e)
        except Exception as e:
            from ccl.errors import report_python_error
            report_python_error(e, ccl_source=source)

    def _handle_meta(self, cmd: str) -> None:
        """メタコマンドを処理"""
        parts = cmd.split(None, 1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if command in (":quit", ":q", ":exit"):
            print(_c("2", "bye."))
            sys.exit(0)

        elif command == ":help":
            print(HELP_TEXT)

        elif command == ":ast":
            if not arg:
                print(_c("91", "使い方: :ast CCL_EXPR"))
                return
            try:
                ast = self.executor.get_ast(arg)
                print(ast)
            except Exception as e:
                print(_c("91", f"パースエラー: {e}"))

        elif command == ":py":
            if not arg:
                print(_c("91", "使い方: :py CCL_EXPR"))
                return
            try:
                py_source = self.executor.get_transpiled(arg)
                print(_c("96", py_source))
            except Exception as e:
                print(_c("91", f"エラー: {e}"))

        elif command == ":vars":
            # ユーザ変数のみ表示 (prelude/runtime は除外)
            from ccl.prelude import get_prelude
            prelude_keys = set(get_prelude().keys())
            runtime_keys = {
                "merge", "product", "oscillate", "converge", "diverge",
                "meta", "pipe", "parallel", "validate", "cycle", "memo",
                "dual", "dual_of", "register_dual", "invert_pipeline",
                "with_dual", "right_adjoint", "left_adjoint",
                "morphism_forward", "morphism_reverse",
                "morphism_lax", "morphism_oplax",
                "morphism_directed_fuse", "morphism_pushforward",
                "backward", "__ccl_result__", "__builtins__",
            }
            exclude = prelude_keys | runtime_keys
            user_vars = {
                k: v for k, v in self.executor._globals.items()
                if k not in exclude and not k.startswith("_")
            }
            if user_vars:
                for k, v in user_vars.items():
                    print(f"  {_c('96', k)} = {repr(v)}")
            else:
                print(_c("2", "  (変数なし)"))

        elif command == ":clear":
            # prelude + runtime を保持してユーザ変数をクリア
            from ccl.executor import CCLExecutor
            self.executor = CCLExecutor()
            print(_c("2", "スコープをクリアしました"))

        else:
            print(_c("91", f"未知のコマンド: {command}。:help で一覧を確認してください"))
