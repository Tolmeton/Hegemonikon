# CCL-PL Extension Loader — .ccl ファイルから拡張を読み込む
"""
Extension ローダー: .ccl 宣言ファイルを解釈し、関数群・随伴対を登録する。

設計決定 (2026-03-31 /ske struct → H1+H2+H4 合成):
  - .ccl が Universal Interface (どの言語でも .ccl に変換できれば Extension)
  - 実装パス: CCL-PL inline (H2) / Python bridge (H1) / FFI (将来)
  - Protocol による随伴対の構造的強制 (H4, 将来)

使用例:
    loader = ExtensionLoader()
    ext = loader.load("hgk.telos")
    # ext.functions: {"recognize": callable, "intend": callable, ...}
    # ext.adjoint_pairs: [("recognize", "explore"), ...]
"""

import importlib
import importlib.metadata
import importlib.util
import re
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Tuple


ENTRY_POINT_GROUP = "ccl.extensions.v1"


@dataclass
class LoadedExtension:
    """ロード済み Extension の表現"""
    name: str
    functions: Dict[str, Callable] = field(default_factory=dict)
    adjoint_pairs: List[Tuple[str, str]] = field(default_factory=list)


class ExtensionLoader:
    """Extension ローダー

    .ccl ファイルを検索パスから探し、宣言を解釈して関数・随伴対を返す。
    """

    def __init__(self, search_paths: Optional[List[Path]] = None):
        self._search_paths: List[Path] = search_paths or []
        self._cache: Dict[str, LoadedExtension] = {}
        self._entry_point_paths: Optional[List[Path]] = None
        self._file_module_cache: Dict[Path, ModuleType] = {}

    def add_search_path(self, path: Path) -> None:
        """検索パスを追加"""
        if path not in self._search_paths:
            self._search_paths.append(path)

    def load(self, module_path: str) -> LoadedExtension:
        """Extension をロードする

        Args:
            module_path: "hgk.telos" のようなドット区切りパス

        Returns:
            LoadedExtension with functions and adjoint_pairs
        """
        if module_path in self._cache:
            return self._cache[module_path]

        # 1. .ccl ファイルを検索
        ccl_file = self._find_ccl_file(module_path)
        if ccl_file is None:
            # フォールバック: Python モジュールとして直接ロード
            ext = self._load_python_fallback(module_path)
            if ext is not None:
                self._cache[module_path] = ext
                return ext
            raise FileNotFoundError(
                f"Extension '{module_path}' が見つかりません。"
                f"検索パス: {[str(p) for p in self._iter_search_paths()]}"
            )

        # 2. .ccl ファイルを解釈
        ext = self._parse_extension_file(ccl_file, module_path)
        self._cache[module_path] = ext
        return ext

    def _find_ccl_file(self, module_path: str) -> Optional[Path]:
        """検索パスから .ccl ファイルを探す

        "hgk.telos" → ccl-ext-hgk/telos.ccl or hgk/telos.ccl
        "demo.nested.core" → ccl-ext-demo/nested/core.ccl
        """
        parts = module_path.split(".")
        if len(parts) < 2:
            return None

        namespace = parts[0]   # "hgk"
        module_rel = Path(*parts[1:]).with_suffix(".ccl")

        candidates = [
            # ccl-ext-hgk/telos.ccl
            Path(f"ccl-ext-{namespace}") / module_rel,
            # hgk/telos.ccl
            Path(namespace) / module_rel,
            # extensions/hgk/telos.ccl
            Path("extensions") / namespace / module_rel,
        ]

        for search_path in self._iter_search_paths():
            for candidate in candidates:
                path = search_path / candidate
                if path.exists():
                    return path

        return None

    def _iter_search_paths(self) -> List[Path]:
        """明示 search path + pip entry point 由来の path を統合"""
        paths: List[Path] = []
        for path in [*self._search_paths, *self._discover_entry_point_paths()]:
            resolved = Path(path).expanduser()
            if resolved not in paths:
                paths.append(resolved)
        return paths

    def _discover_entry_point_paths(self) -> List[Path]:
        """pip package が公開した extension root を取得する"""
        if self._entry_point_paths is not None:
            return self._entry_point_paths

        self._entry_point_paths = []
        try:
            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, "select"):
                candidates = entry_points.select(group=ENTRY_POINT_GROUP)
            else:
                candidates = entry_points.get(ENTRY_POINT_GROUP, [])
        except Exception:
            return self._entry_point_paths

        for entry_point in candidates:
            try:
                provider = entry_point.load()
            except Exception:
                continue

            for path in self._coerce_extension_roots(provider):
                if path.exists() and path not in self._entry_point_paths:
                    self._entry_point_paths.append(path)

        return self._entry_point_paths

    def _coerce_extension_roots(self, provider: Any) -> List[Path]:
        """entry point の返り値を search path に正規化する"""
        if callable(provider):
            try:
                provider = provider()
            except Exception:
                return []

        if provider is None:
            return []

        if isinstance(provider, (str, Path)):
            return [Path(provider).expanduser().resolve()]

        if isinstance(provider, (list, tuple, set)):
            roots: List[Path] = []
            for item in provider:
                roots.extend(self._coerce_extension_roots(item))
            return roots

        package_paths = getattr(provider, "__path__", None)
        if package_paths:
            return [Path(path).expanduser().resolve() for path in package_paths]

        package_file = getattr(provider, "__file__", None)
        if package_file:
            return [Path(package_file).expanduser().resolve().parent]

        return []

    def _parse_extension_file(self, path: Path, module_path: str) -> LoadedExtension:
        """Extension .ccl ファイルを解釈する

        最小パーサー: fn 宣言, adjoint 宣言, -> python() bridge を認識
        """
        source = path.read_text(encoding="utf-8")
        ext = LoadedExtension(name=module_path)

        in_extension_block = False
        current_fn_name = None
        current_fn_params: List[str] = []
        brace_depth = 0

        for line in source.split("\n"):
            stripped = line.strip()

            # コメント・空行をスキップ
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                continue

            # extension ブロック開始
            if stripped.startswith("extension ") and "{" in stripped:
                in_extension_block = True
                brace_depth = 1
                continue

            if not in_extension_block:
                continue

            # ブレース追跡
            brace_depth += stripped.count("{") - stripped.count("}")
            if brace_depth <= 0:
                in_extension_block = False
                continue

            # adjoint 宣言
            adj_match = re.match(r'adjoint\s+(\w+)\s*<=>\s*(\w+)', stripped)
            if adj_match:
                ext.adjoint_pairs.append((adj_match.group(1), adj_match.group(2)))
                continue

            # fn with Python bridge: fn name(args) -> python("mod.func")
            bridge_match = re.match(
                r'fn\s+(\w+)\s*\(([^)]*)\)\s*->\s*python\("([^"]+)"\)',
                stripped,
            )
            if bridge_match:
                fn_name = bridge_match.group(1)
                target = bridge_match.group(3)
                fn = self._resolve_python_bridge(target)
                if fn is not None:
                    ext.functions[fn_name] = fn
                continue

            # fn with inline body: fn name(args) { body }
            inline_match = re.match(
                r'fn\s+(\w+)\s*\(([^)]*)\)\s*\{(.+)\}',
                stripped,
            )
            if inline_match:
                fn_name = inline_match.group(1)
                params_str = inline_match.group(2).strip()
                body = inline_match.group(3).strip()
                params = [p.strip() for p in params_str.split(",") if p.strip()]
                fn = self._make_inline_fn(fn_name, params, body)
                ext.functions[fn_name] = fn
                continue

            # fn declaration only (no body): fn name(args)
            decl_match = re.match(r'fn\s+(\w+)\s*\(([^)]*)\)\s*$', stripped)
            if decl_match:
                # 宣言のみ — 実装がないので placeholder
                fn_name = decl_match.group(1)
                ext.functions[fn_name] = self._make_placeholder(fn_name)
                continue

        return ext

    def _resolve_python_bridge(self, target: str) -> Optional[Callable]:
        """Python bridge を解決: "module.function" → callable"""
        parts = target.rsplit(".", 1)
        if len(parts) != 2:
            return None

        module_name, func_name = parts
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            module = self._load_file_module(module_name)
        if module is None:
            return None

        try:
            return getattr(module, func_name)
        except AttributeError:
            return None

    def _load_file_module(self, module_name: str) -> Optional[ModuleType]:
        """search path 上の Python ファイルから bridge module をロードする"""
        rel_module = Path(*module_name.split("."))
        candidates = [
            rel_module.with_suffix(".py"),
            rel_module / "__init__.py",
        ]

        for search_path in self._iter_search_paths():
            for candidate in candidates:
                path = (search_path / candidate).resolve()
                if not path.exists():
                    continue
                if path in self._file_module_cache:
                    return self._file_module_cache[path]

                synthetic_name = "_ccl_bridge_" + "_".join(path.parts[-4:])
                spec = importlib.util.spec_from_file_location(synthetic_name, path)
                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                except Exception:
                    continue

                self._file_module_cache[path] = module
                return module

        return None

    def _make_inline_fn(self, name: str, params: List[str], body: str) -> Callable:
        """CCL-PL inline body から Python 関数を生成"""
        # 最小実装: body を Python として eval
        # 将来的には CCL-PL パーサーで body をパース → トランスパイル
        param_str = ", ".join(params)
        fn_code = f"def {name}({param_str}):\n    return {body}\n"
        local_ns: Dict[str, Any] = {}
        try:
            exec(fn_code, {"__builtins__": __builtins__}, local_ns)
            return local_ns[name]
        except Exception:
            return self._make_placeholder(name)

    def _make_placeholder(self, name: str) -> Callable:
        """未実装関数の placeholder"""
        def _placeholder(*args, **kwargs):
            raise NotImplementedError(
                f"Extension function '{name}' は宣言のみで実装がありません。"
                f"inline body か python() bridge を追加してください。"
            )
        _placeholder.__name__ = name
        return _placeholder

    def _load_python_fallback(self, module_path: str) -> Optional[LoadedExtension]:
        """フォールバック: Python モジュールとして直接ロード

        ccl.stdlib.hgk.telos のように既存の stdlib をサポート
        """
        try:
            python_module = f"ccl.stdlib.{module_path}"
            mod = importlib.import_module(python_module)
        except ImportError:
            return None

        ext = LoadedExtension(name=module_path)

        # モジュールの公開関数を収集
        for attr_name in dir(mod):
            if attr_name.startswith("_"):
                continue
            obj = getattr(mod, attr_name)
            if callable(obj) and not isinstance(obj, type):
                ext.functions[attr_name] = obj

        # 随伴対を収集
        if hasattr(mod, "ADJOINT_PAIRS"):
            ext.adjoint_pairs = list(mod.ADJOINT_PAIRS)

        return ext
