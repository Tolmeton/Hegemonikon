# CCL-PL 統合実行エンジン
"""
CCL-PL Executor — パース → トランスパイル → 実行の統合パイプライン

使用例:
    from ccl.executor import CCLExecutor

    exe = CCLExecutor()
    result = exe.execute("/noe+_/dia")
    result = exe.execute_file("program.ccl")
"""

import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

from ccl.errors import (
    CCLError, CCLParseError, CCLRuntimeError, CCLNameError,
    SourceLocation, report_python_error,
)
from ccl.prelude import get_prelude
from ccl.extension import ExtensionLoader


class CCLExecutor:
    """CCL 式を実行するエンジン"""

    def __init__(self):
        # グローバルスコープ (セッション間で変数を保持)
        self._globals: Dict[str, Any] = {}
        # prelude を注入
        self._globals.update(get_prelude())
        # ランタイム関数を注入
        self._inject_runtime()
        # ユーザ定義関数レジストリ
        self._user_functions: Dict[str, Any] = {}
        # ユーザ定義随伴対 (adjoint 宣言)
        self._globals["__ccl_adjoint_pairs__"] = []
        # Extension ローダー
        self._ext_loader = ExtensionLoader()
        self._init_extension_paths()

    def _inject_runtime(self) -> None:
        """CCL ランタイム関数をグローバルスコープに注入"""
        try:
            from ccl.runtime.core import (
                merge, product, oscillate, converge, diverge,
                meta, pipe, parallel, validate, cycle, memo,
                dual, dual_of, register_dual, invert_pipeline,
                with_dual, right_adjoint, left_adjoint,
                morphism_forward, morphism_reverse,
                morphism_lax, morphism_oplax,
                morphism_directed_fuse, morphism_pushforward,
                backward,
            )
            runtime_fns = {
                "merge": merge, "product": product,
                "oscillate": oscillate, "converge": converge, "diverge": diverge,
                "meta": meta, "pipe": pipe, "parallel": parallel,
                "validate": validate, "cycle": cycle, "memo": memo,
                "dual": dual, "dual_of": dual_of,
                "register_dual": register_dual,
                "invert_pipeline": invert_pipeline,
                "with_dual": with_dual,
                "right_adjoint": right_adjoint,
                "left_adjoint": left_adjoint,
                "morphism_forward": morphism_forward,
                "morphism_reverse": morphism_reverse,
                "morphism_lax": morphism_lax,
                "morphism_oplax": morphism_oplax,
                "morphism_directed_fuse": morphism_directed_fuse,
                "morphism_pushforward": morphism_pushforward,
                "backward": backward,
            }
            self._globals.update(runtime_fns)
        except ImportError as e:
            # ランタイムが読めなくても動作は継続
            print(f"[warn] ランタイム読込スキップ: {e}", file=sys.stderr)

    def _init_extension_paths(self) -> None:
        """Extension の検索パスを初期化"""
        import os
        # 1. 環境変数 CCL_EXT_PATH
        env_paths = os.environ.get("CCL_EXT_PATH", "")
        for p in env_paths.split(":"):
            if p:
                self._ext_loader.add_search_path(Path(p))
        # 2. CWD (プロジェクト内の ccl-ext-* を発見)
        self._ext_loader.add_search_path(Path.cwd())
        # 3. ホームディレクトリ
        home_ext = Path.home() / ".ccl" / "extensions"
        self._ext_loader.add_search_path(home_ext)

    def _handle_use(self, module_path: str, filename: str) -> None:
        """use 文を処理: Extension をロードしてグローバルスコープに注入"""
        try:
            ext = self._ext_loader.load(module_path)
        except FileNotFoundError as e:
            loc = SourceLocation(file=filename, source_line=f"use {module_path}")
            raise CCLNameError(str(e), loc=loc) from e

        # 関数をグローバルスコープに登録
        for fn_name, fn in ext.functions.items():
            self._globals[fn_name] = fn

        # 随伴対を登録
        pairs = self._globals.get("__ccl_adjoint_pairs__", [])
        pairs.extend(ext.adjoint_pairs)
        self._globals["__ccl_adjoint_pairs__"] = pairs

    def register_function(self, name: str, fn: Any) -> None:
        """ユーザ定義関数を登録"""
        self._user_functions[name] = fn
        self._globals[name] = fn

    def execute(self, ccl_source: str, filename: str = "<repl>") -> Any:
        """CCL 式を実行して結果を返す

        パイプライン: CCL ソース → 文ごとに パース → トランスパイル → exec

        複数文のファイルは行ごとに逐次実行される。
        let 定義や関数はグローバルスコープに蓄積される。

        Args:
            ccl_source: CCL ソースコード (1文 or 複数文)
            filename: ファイル名 (エラー報告用)

        Returns:
            最後の式の実行結果
        """
        ccl_source = ccl_source.strip()
        if not ccl_source:
            return None

        # 文を分割 (改行区切り、コメント/空行を除去)
        statements = self._split_statements(ccl_source)
        if not statements:
            return None

        # 各文を逐次実行
        last_result = None
        for stmt in statements:
            last_result = self._execute_single(stmt, filename)

        return last_result

    def _split_statements(self, source: str) -> list:
        """ソースを文のリストに分割する"""
        statements = []
        for line in source.split("\n"):
            stripped = line.strip()
            # 空行とコメントをスキップ
            if not stripped or stripped.startswith("#"):
                continue
            statements.append(stripped)
        return statements

    def _execute_single(self, ccl_source: str, filename: str) -> Any:
        """単一の CCL 文を実行

        パイプライン: Parse → (UseDecl → Extension ロード) → Optimize → Transpile → Exec
        """
        # 1. パース
        try:
            from ccl.parser.core import CCLParser
            parser = CCLParser()
            ast = parser.parse(ccl_source)
        except Exception as e:
            loc = SourceLocation(file=filename, source_line=ccl_source)
            raise CCLParseError(f"構文エラー: {e}", loc=loc) from e

        # 1.5. UseDecl → Extension ローダーで処理 (トランスパイラーをバイパス)
        from ccl.parser.ast import UseDecl
        if isinstance(ast, UseDecl):
            self._handle_use(ast.module_path, filename)
            return None

        # 2. 最適化 (圏論的 AST 変換)
        try:
            from ccl.optimizer import ASTOptimizer
            optimizer = ASTOptimizer()
            # hgk-stdlib の随伴対を登録
            try:
                from ccl.stdlib.hgk import ALL_ADJOINT_PAIRS
                optimizer.register_adjoint_pairs(ALL_ADJOINT_PAIRS)
            except ImportError:
                pass
            # ユーザ定義の随伴対 (adjoint 宣言) を登録
            user_pairs = self._globals.get("__ccl_adjoint_pairs__", [])
            if user_pairs:
                optimizer.register_adjoint_pairs(user_pairs)
            ast = optimizer.optimize(ast)
        except Exception:
            pass  # オプティマイザのエラーは無視して続行

        # 3. トランスパイル
        try:
            from ccl.transpiler import CCLTranspiler
            transpiler = CCLTranspiler()
            python_source = transpiler.transpile(ast, include_header=False)
        except Exception as e:
            loc = SourceLocation(file=filename, source_line=ccl_source)
            raise CCLRuntimeError(f"トランスパイルエラー: {e}", loc=loc) from e

        # 4. 実行
        return self._exec_python(python_source, ccl_source, filename)

    def _exec_python(self, python_source: str, ccl_source: str, filename: str) -> Any:
        """生成された Python コードを実行"""
        # result 変数を None で初期化
        self._globals["__ccl_result__"] = None

        # result = ... の最後の代入を __ccl_result__ にマッピング
        # トランスパイラは最後に "result = vN" を出力する
        exec_source = python_source
        if "\nresult = " in exec_source:
            exec_source = exec_source.replace(
                "\n\n# === CCL 実行結果 ===\nresult = ",
                "\n\n# === CCL 実行結果 ===\n__ccl_result__ = "
            )

        try:
            exec(exec_source, self._globals)
        except NameError as e:
            loc = SourceLocation(file=filename, source_line=ccl_source)
            # 未定義関数のフレンドリーメッセージ
            msg = str(e)
            raise CCLNameError(
                f"未定義の関数または変数: {msg}\n"
                f"  ヒント: fn で関数を定義するか、prelude の関数を確認してください",
                loc=loc
            ) from e
        except Exception as e:
            loc = SourceLocation(file=filename, source_line=ccl_source)
            raise CCLRuntimeError(f"{type(e).__name__}: {e}", loc=loc) from e

        result = self._globals.get("__ccl_result__")
        return result

    def execute_file(self, path: str) -> Any:
        """CCL ファイルを実行"""
        filepath = Path(path)
        if not filepath.exists():
            raise CCLError(f"ファイルが見つかりません: {path}")
        if not filepath.suffix == ".ccl":
            raise CCLError(f"CCL ファイル (.ccl) を指定してください: {path}")

        source = filepath.read_text(encoding="utf-8")
        return self.execute(source, filename=str(filepath))

    def get_transpiled(self, ccl_source: str) -> str:
        """CCL 式をトランスパイルして Python ソースを返す (実行はしない)"""
        from ccl.parser.core import CCLParser
        from ccl.transpiler import CCLTranspiler

        parser = CCLParser()
        ast = parser.parse(ccl_source.strip())
        transpiler = CCLTranspiler()
        return transpiler.transpile(ast)

    def get_ast(self, ccl_source: str) -> Any:
        """CCL 式をパースして AST を返す"""
        from ccl.parser.core import CCLParser
        parser = CCLParser()
        return parser.parse(ccl_source.strip())
