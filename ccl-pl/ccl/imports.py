"""CCL import semantics helper.

`use foo.bar` と `use foo.bar as alias` の runtime semantics を集約する。
"""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

from ccl.extension import ExtensionLoader

LOADER_SCOPE_KEY = "__ccl_loader__"
ALIASES_SCOPE_KEY = "__ccl_alias_imports__"


class ImportCollisionError(RuntimeError):
    """bare import / alias import の衝突エラー"""


class ImportedExtensionNamespace(SimpleNamespace):
    """alias import 用の namespace object"""

    def __init__(self, module_path: str, exports: dict[str, Any]):
        super().__init__(**exports)
        self.__ccl_module_path__ = module_path
        self.__ccl_exports__ = dict(exports)


def configure_default_loader(
    loader: ExtensionLoader,
    cwd: Optional[Path] = None,
) -> ExtensionLoader:
    """標準 search path を loader に追加する"""
    env_paths = os.environ.get("CCL_EXT_PATH", "")
    for raw_path in env_paths.split(":"):
        if raw_path:
            loader.add_search_path(Path(raw_path))

    loader.add_search_path(cwd or Path.cwd())
    loader.add_search_path(Path.home() / ".ccl" / "extensions")
    return loader


def ccl_use(
    scope: dict[str, Any],
    module_path: str,
    alias: Optional[str] = None,
    loader: Optional[ExtensionLoader] = None,
) -> Optional[ImportedExtensionNamespace]:
    """CCL extension import を実行する"""
    active_loader = _resolve_loader(scope, loader)
    ext = active_loader.load(module_path)
    _merge_adjoint_pairs(scope, ext.adjoint_pairs)

    if alias:
        return _bind_alias(scope, module_path, alias, ext.functions)

    _bind_bare(scope, module_path, ext.functions)
    return None


def _resolve_loader(
    scope: dict[str, Any],
    loader: Optional[ExtensionLoader],
) -> ExtensionLoader:
    if loader is not None:
        scope[LOADER_SCOPE_KEY] = loader
        return loader

    existing = scope.get(LOADER_SCOPE_KEY)
    if isinstance(existing, ExtensionLoader):
        return existing

    default_loader = configure_default_loader(ExtensionLoader())
    scope[LOADER_SCOPE_KEY] = default_loader
    return default_loader


def _merge_adjoint_pairs(scope: dict[str, Any], pairs: list[tuple[str, str]]) -> None:
    registered = scope.setdefault("__ccl_adjoint_pairs__", [])
    for pair in pairs:
        if pair not in registered:
            registered.append(pair)


def _bind_alias(
    scope: dict[str, Any],
    module_path: str,
    alias: str,
    exports: dict[str, Any],
) -> ImportedExtensionNamespace:
    existing = scope.get(alias)
    if existing is not None:
        if _matches_existing_alias(existing, module_path, exports):
            return existing
        raise ImportCollisionError(
            f"import alias '{alias}' は既存の名前と衝突しています。"
            f" module={module_path}"
        )

    namespace = ImportedExtensionNamespace(module_path, exports)
    scope[alias] = namespace
    scope.setdefault(ALIASES_SCOPE_KEY, {})[alias] = module_path
    return namespace


def _bind_bare(
    scope: dict[str, Any],
    module_path: str,
    exports: dict[str, Any],
) -> None:
    collisions: list[str] = []
    for name, fn in exports.items():
        existing = scope.get(name)
        if existing is not None and existing is not fn:
            collisions.append(name)

    if collisions:
        names = ", ".join(sorted(collisions))
        raise ImportCollisionError(
            f"bare import '{module_path}' で名前衝突: {names}. "
            f"`use {module_path} as <alias>` を使ってください。"
        )

    for name, fn in exports.items():
        scope[name] = fn


def _matches_existing_alias(
    existing: Any,
    module_path: str,
    exports: dict[str, Any],
) -> bool:
    if getattr(existing, "__ccl_module_path__", None) != module_path:
        return False

    existing_exports = getattr(existing, "__ccl_exports__", None)
    if not isinstance(existing_exports, dict):
        return False

    if existing_exports.keys() != exports.keys():
        return False

    return all(existing_exports[name] is exports[name] for name in exports)
