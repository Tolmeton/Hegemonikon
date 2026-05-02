# PROOF: [L2/検索] <- mekhane/symploke/ Python symbol graph が必要→code_symbol_graph.py が担う
"""
Code Symbol Graph v1.

Python 専用の symbol graph を AST + jedi で構築し、
Serena の N 面を HGK の内側へ吸収する。
"""

from __future__ import annotations

import ast
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from typing import Any, Iterable, Sequence

from mekhane.paths import CODE_SYMBOL_GRAPH_INDEX, HGK_ROOT
from mekhane.symploke.code_ingest import (
    CODE_SCAN_DIRS,
    _EXCLUDE_DIRS,
    _canonical_code_path,
)


GRAPH_VERSION = "2026-04-18-symbol-graph-v1"
NODE_KINDS = ("file", "class", "function", "method")
EDGE_TYPES = ("contains", "imports", "calls", "inherits")
DEFAULT_DIRECTION = "both"
MAX_NEIGHBORHOOD_DEPTH = 2
_CACHE: dict[str, Any] = {"path": None, "mtime": None, "graph": None}
_STALE_CACHE: dict[str, Any] = {"scan_dirs_key": None, "latest_source_mtime": None}
_STALE_CACHE_LOCK = Lock()


def _load_jedi():
    try:
        import jedi
    except ImportError as exc:  # pragma: no cover - exercised via caller behavior
        raise RuntimeError(
            "jedi is required to build or rebuild the code symbol graph"
        ) from exc
    return jedi


def is_jedi_available() -> bool:
    try:
        _load_jedi()
        return True
    except RuntimeError:
        return False


def _path_in_scan_roots(path: str | Path, scan_dirs: Sequence[tuple[Path, str]]) -> bool:
    target = Path(path).resolve(strict=False)
    for root, _ in scan_dirs:
        try:
            resolved_root = root.resolve(strict=False)
        except OSError:
            resolved_root = root
        try:
            target.relative_to(resolved_root)
            return True
        except ValueError:
            continue
    return False


def iter_code_files(
    scan_dirs: Sequence[tuple[Path, str]] = CODE_SCAN_DIRS,
) -> Iterable[Path]:
    """CODE_SCAN_DIRS を走査して対象 .py を返す。"""
    seen: set[Path] = set()
    for dir_path, _ in scan_dirs:
        if not dir_path.exists():
            continue
        for py_file in sorted(dir_path.rglob("*.py")):
            try:
                parts = set(py_file.relative_to(dir_path).parts)
            except ValueError:
                continue
            if parts & _EXCLUDE_DIRS:
                continue
            resolved = py_file.resolve(strict=False)
            if resolved in seen:
                continue
            seen.add(resolved)
            yield py_file


def build_code_symbol_manifest(
    scan_dirs: Sequence[tuple[Path, str]] = CODE_SCAN_DIRS,
) -> dict[str, float]:
    """symbol graph 用の code manifest を返す。"""
    manifest: dict[str, float] = {}
    for py_file in iter_code_files(scan_dirs):
        try:
            manifest[_canonical_code_path(py_file)] = py_file.stat().st_mtime
        except OSError:
            continue
    return manifest


def _scan_dirs_cache_key(
    scan_dirs: Sequence[tuple[Path, str]],
) -> tuple[str, ...]:
    return tuple(
        str(Path(dir_path).resolve(strict=False))
        for dir_path, _ in scan_dirs
    )


def clear_code_symbol_graph_stale_cache() -> None:
    with _STALE_CACHE_LOCK:
        _STALE_CACHE["scan_dirs_key"] = None
        _STALE_CACHE["latest_source_mtime"] = None


def _prime_code_symbol_graph_stale_cache(
    manifest: dict[str, float],
    scan_dirs: Sequence[tuple[Path, str]],
) -> None:
    with _STALE_CACHE_LOCK:
        _STALE_CACHE["scan_dirs_key"] = _scan_dirs_cache_key(scan_dirs)
        _STALE_CACHE["latest_source_mtime"] = max(manifest.values(), default=0.0)


def latest_code_source_mtime(
    scan_dirs: Sequence[tuple[Path, str]] = CODE_SCAN_DIRS,
    *,
    force_refresh: bool = False,
) -> float:
    cache_key = _scan_dirs_cache_key(scan_dirs)
    with _STALE_CACHE_LOCK:
        cached_key = _STALE_CACHE["scan_dirs_key"]
        cached_latest = _STALE_CACHE["latest_source_mtime"]
    if not force_refresh and cached_key == cache_key and cached_latest is not None:
        return float(cached_latest)

    manifest = build_code_symbol_manifest(scan_dirs)
    latest = max(manifest.values(), default=0.0)
    with _STALE_CACHE_LOCK:
        _STALE_CACHE["scan_dirs_key"] = cache_key
        _STALE_CACHE["latest_source_mtime"] = latest
    return latest


def is_code_symbol_graph_stale(
    graph_path: str | Path = CODE_SYMBOL_GRAPH_INDEX,
    scan_dirs: Sequence[tuple[Path, str]] = CODE_SCAN_DIRS,
    *,
    force_refresh: bool = False,
) -> bool:
    """symbol graph が欠落または古いかを返す。"""
    path = Path(graph_path)
    if not path.exists():
        return True
    latest = latest_code_source_mtime(scan_dirs, force_refresh=force_refresh)
    try:
        return path.stat().st_mtime < latest
    except OSError:
        return True


def clear_code_symbol_graph_cache() -> None:
    _CACHE["path"] = None
    _CACHE["mtime"] = None
    _CACHE["graph"] = None


def load_code_symbol_graph(path: str | Path = CODE_SYMBOL_GRAPH_INDEX) -> "CodeSymbolGraph":
    return CodeSymbolGraph.load(path)


def get_code_symbol_graph(path: str | Path = CODE_SYMBOL_GRAPH_INDEX) -> "CodeSymbolGraph":
    """JSON artifact から graph を lazy load する。"""
    graph_path = Path(path)
    if not graph_path.exists():
        raise FileNotFoundError(f"Code symbol graph not found: {graph_path}")
    mtime = graph_path.stat().st_mtime
    if (
        _CACHE["graph"] is None
        or _CACHE["path"] != str(graph_path)
        or _CACHE["mtime"] != mtime
    ):
        _CACHE["graph"] = load_code_symbol_graph(graph_path)
        _CACHE["path"] = str(graph_path)
        _CACHE["mtime"] = mtime
    return _CACHE["graph"]


def rebuild_code_symbol_graph(
    graph_path: str | Path = CODE_SYMBOL_GRAPH_INDEX,
    scan_dirs: Sequence[tuple[Path, str]] = CODE_SCAN_DIRS,
    project_root: str | Path = HGK_ROOT,
    jedi_module=None,
) -> "CodeSymbolGraph":
    """full rebuild して JSON artifact を atomically 保存する。"""
    clear_code_symbol_graph_stale_cache()
    graph = CodeSymbolGraph.build(
        scan_dirs=scan_dirs,
        project_root=project_root,
        jedi_module=jedi_module,
    )
    graph.save(graph_path)
    clear_code_symbol_graph_cache()
    _prime_code_symbol_graph_stale_cache(graph.manifest, scan_dirs)
    return graph


@dataclass
class _Reference:
    edge_type: str
    source_id: str
    file_path: str
    line: int
    column: int
    name: str
    container_id: str
    fallback_kind: str | None = None
    owner_name: str | None = None


@dataclass
class _FileContext:
    path: Path
    canonical_path: str
    source: str
    lines: list[str]
    tree: ast.Module


class _ScopedRefCollector(ast.NodeVisitor):
    """ネスト定義を無視して import / call を拾う。"""

    def __init__(
        self,
        builder: "_CodeSymbolGraphBuilder",
        file_ctx: _FileContext,
        source_id: str,
        container_id: str,
        class_id: str | None = None,
    ) -> None:
        self.builder = builder
        self.file_ctx = file_ctx
        self.source_id = source_id
        self.container_id = container_id
        self.class_id = class_id

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        return None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        return None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        return None

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        line_text = self.file_ctx.lines[node.lineno - 1] if node.lineno - 1 < len(self.file_ctx.lines) else ""
        cursor = 0
        for alias in node.names:
            token = alias.name.split(".")[0]
            column = _find_token_column(line_text, token, cursor)
            if column >= 0:
                cursor = column + len(token)
            self.builder.add_reference(
                _Reference(
                    edge_type="imports",
                    source_id=self.source_id,
                    file_path=self.file_ctx.canonical_path,
                    line=node.lineno,
                    column=max(column, 0),
                    name=token,
                    container_id=self.container_id,
                )
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if not node.names:
            return
        line_text = self.file_ctx.lines[node.lineno - 1] if node.lineno - 1 < len(self.file_ctx.lines) else ""
        cursor = 0
        for alias in node.names:
            token = alias.name.split(".")[0]
            if token == "*":
                continue
            column = _find_token_column(line_text, token, cursor)
            if column >= 0:
                cursor = column + len(token)
            self.builder.add_reference(
                _Reference(
                    edge_type="imports",
                    source_id=self.source_id,
                    file_path=self.file_ctx.canonical_path,
                    line=node.lineno,
                    column=max(column, 0),
                    name=token,
                    container_id=self.container_id,
                )
            )

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        name, column, fallback_kind, owner_name = _call_descriptor(node, self.file_ctx.lines)
        if name:
            self.builder.add_reference(
                _Reference(
                    edge_type="calls",
                    source_id=self.source_id,
                    file_path=self.file_ctx.canonical_path,
                    line=getattr(node.func, "lineno", getattr(node, "lineno", 0)),
                    column=column,
                    name=name,
                    container_id=self.container_id,
                    fallback_kind=fallback_kind,
                    owner_name=owner_name,
                )
            )
        self.generic_visit(node)


def _find_token_column(line_text: str, token: str, start: int = 0) -> int:
    if not line_text or not token:
        return -1
    return line_text.find(token, start)


def _expr_column(node: ast.expr) -> int:
    if isinstance(node, ast.Attribute) and hasattr(node, "end_col_offset"):
        return max(getattr(node, "end_col_offset", 0) - len(node.attr), 0)
    return max(getattr(node, "col_offset", 0), 0)


def _expr_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _call_descriptor(node: ast.Call, lines: list[str]) -> tuple[str, int, str | None, str | None]:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id, _expr_column(func), "same_file_bare", None
    if isinstance(func, ast.Attribute):
        fallback_kind = None
        owner_name = None
        if isinstance(func.value, ast.Name) and func.value.id in {"self", "cls"}:
            fallback_kind = "self_or_cls"
            owner_name = func.value.id
        return func.attr, _expr_column(func), fallback_kind, owner_name
    return "", 0, None, None


class _CodeSymbolGraphBuilder:
    def __init__(
        self,
        scan_dirs: Sequence[tuple[Path, str]],
        project_root: Path,
        jedi_module,
    ) -> None:
        self.scan_dirs = scan_dirs
        self.project_root = project_root
        self.jedi = jedi_module
        self.project = jedi_module.Project(path=str(project_root))
        self.nodes_by_id: dict[str, dict[str, Any]] = {}
        self.edges_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
        self.file_contexts: dict[str, _FileContext] = {}
        self.references_by_file: dict[str, list[_Reference]] = defaultdict(list)
        self.node_by_file_line: dict[tuple[str, int], str] = {}
        self.top_level_symbols: dict[tuple[str, str], list[str]] = defaultdict(list)
        self.class_methods: dict[tuple[str, str], str] = {}
        self.manifest: dict[str, float] = {}
        self.unresolved_totals: Counter[str] = Counter()
        self.external_totals: Counter[str] = Counter()

    def add_reference(self, ref: _Reference) -> None:
        self.references_by_file[ref.file_path].append(ref)

    def build(self) -> "CodeSymbolGraph":
        for py_file in iter_code_files(self.scan_dirs):
            self._register_file(py_file)
        for file_ctx in self.file_contexts.values():
            self._resolve_references(file_ctx)
        data = {
            "version": GRAPH_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "manifest": self.manifest,
            "stats": self._build_stats(),
            "nodes": self._sorted_nodes(),
            "edges": self._sorted_edges(),
        }
        return CodeSymbolGraph(data)

    def _register_file(self, py_file: Path) -> None:
        canonical_path = _canonical_code_path(py_file)
        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            return
        try:
            self.manifest[canonical_path] = py_file.stat().st_mtime
        except OSError:
            self.manifest[canonical_path] = 0.0
        lines = source.splitlines()
        file_ctx = _FileContext(
            path=py_file,
            canonical_path=canonical_path,
            source=source,
            lines=lines,
            tree=tree,
        )
        self.file_contexts[canonical_path] = file_ctx

        file_id = self._register_node(
            kind="file",
            canonical_path=canonical_path,
            qualname=py_file.name,
            symbol_name=py_file.name,
            line_start=1,
            line_end=max(len(lines), 1),
            container_id="",
        )

        # module-level executable statements belong to file node
        module_statements: list[ast.stmt] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._register_function(file_ctx, file_id, node)
                continue
            if isinstance(node, ast.ClassDef):
                self._register_class(file_ctx, file_id, node)
                continue
            module_statements.append(node)

        if module_statements:
            collector = _ScopedRefCollector(
                builder=self,
                file_ctx=file_ctx,
                source_id=file_id,
                container_id=file_id,
            )
            for stmt in module_statements:
                collector.visit(stmt)

    def _register_function(
        self,
        file_ctx: _FileContext,
        file_id: str,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        func_id = self._register_node(
            kind="function",
            canonical_path=file_ctx.canonical_path,
            qualname=node.name,
            symbol_name=node.name,
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            container_id=file_id,
            index_for_name_lookup=True,
        )
        self._add_edge(file_id, func_id, "contains", line=node.lineno, resolver="ast")
        collector = _ScopedRefCollector(
            builder=self,
            file_ctx=file_ctx,
            source_id=func_id,
            container_id=func_id,
        )
        for stmt in node.body:
            collector.visit(stmt)

    def _register_class(
        self,
        file_ctx: _FileContext,
        file_id: str,
        node: ast.ClassDef,
    ) -> None:
        class_id = self._register_node(
            kind="class",
            canonical_path=file_ctx.canonical_path,
            qualname=node.name,
            symbol_name=node.name,
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            container_id=file_id,
            index_for_name_lookup=True,
        )
        self._add_edge(file_id, class_id, "contains", line=node.lineno, resolver="ast")

        for base in node.bases:
            base_name = _expr_name(base)
            if not base_name:
                continue
            self.add_reference(
                _Reference(
                    edge_type="inherits",
                    source_id=class_id,
                    file_path=file_ctx.canonical_path,
                    line=getattr(base, "lineno", node.lineno),
                    column=_expr_column(base),
                    name=base_name,
                    container_id=class_id,
                )
            )

        class_statements: list[ast.stmt] = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_qualname = f"{node.name}.{item.name}"
                method_id = self._register_node(
                    kind="method",
                    canonical_path=file_ctx.canonical_path,
                    qualname=method_qualname,
                    symbol_name=item.name,
                    line_start=item.lineno,
                    line_end=getattr(item, "end_lineno", item.lineno),
                    container_id=class_id,
                    index_for_name_lookup=False,
                )
                self.class_methods[(class_id, item.name)] = method_id
                self._add_edge(class_id, method_id, "contains", line=item.lineno, resolver="ast")
                collector = _ScopedRefCollector(
                    builder=self,
                    file_ctx=file_ctx,
                    source_id=method_id,
                    container_id=method_id,
                    class_id=class_id,
                )
                for stmt in item.body:
                    collector.visit(stmt)
                continue
            class_statements.append(item)

        if class_statements:
            collector = _ScopedRefCollector(
                builder=self,
                file_ctx=file_ctx,
                source_id=class_id,
                container_id=class_id,
                class_id=class_id,
            )
            for stmt in class_statements:
                collector.visit(stmt)

    def _register_node(
        self,
        *,
        kind: str,
        canonical_path: str,
        qualname: str,
        symbol_name: str,
        line_start: int,
        line_end: int,
        container_id: str,
        index_for_name_lookup: bool = False,
    ) -> str:
        if kind == "file":
            node_id = f"file::{canonical_path}"
        else:
            node_id = f"{kind}::{canonical_path}::{qualname}"
        node = {
            "id": node_id,
            "kind": kind,
            "symbol_name": symbol_name,
            "qualname": qualname,
            "file_path": canonical_path,
            "line_start": line_start,
            "line_end": line_end,
            "container_id": container_id,
            "code_type": kind,
            "unresolved_counts": {
                "imports": 0,
                "calls": 0,
                "inherits": 0,
                "external_imports": 0,
                "external_calls": 0,
                "external_inherits": 0,
            },
        }
        self.nodes_by_id[node_id] = node
        self.node_by_file_line[(canonical_path, line_start)] = node_id
        if index_for_name_lookup:
            self.top_level_symbols[(canonical_path, symbol_name)].append(node_id)
        return node_id

    def _resolve_references(self, file_ctx: _FileContext) -> None:
        refs = self.references_by_file.get(file_ctx.canonical_path)
        if not refs:
            return

        script = self.jedi.Script(
            code=file_ctx.source,
            path=str(file_ctx.path),
            project=self.project,
        )
        for ref in refs:
            resolved, external = self._resolve_with_jedi(script, ref)
            if resolved:
                self._add_edge(
                    ref.source_id,
                    resolved,
                    ref.edge_type,
                    line=ref.line,
                    resolver="jedi",
                )
                continue
            fallback = self._resolve_fallback(ref)
            if fallback:
                self._add_edge(
                    ref.source_id,
                    fallback,
                    ref.edge_type,
                    line=ref.line,
                    resolver="fallback",
                )
                continue
            self._mark_unresolved(ref.source_id, ref.edge_type, external=external)

    def _resolve_with_jedi(self, script, ref: _Reference) -> tuple[str | None, bool]:
        try:
            definitions = script.goto(
                ref.line,
                ref.column,
                follow_imports=True,
                follow_builtin_imports=False,
            )
        except Exception:  # noqa: BLE001
            return None, False

        saw_external = False
        for definition in definitions or []:
            module_path = getattr(definition, "module_path", None)
            if not module_path:
                saw_external = True
                continue
            canonical_target = _canonical_code_path(module_path)
            if not _path_in_scan_roots(canonical_target, self.scan_dirs):
                saw_external = True
                continue

            if getattr(definition, "type", "") == "module":
                file_id = f"file::{canonical_target}"
                if file_id in self.nodes_by_id:
                    return file_id, False

            def_line = getattr(definition, "line", None)
            if def_line and (canonical_target, def_line) in self.node_by_file_line:
                return self.node_by_file_line[(canonical_target, def_line)], False

            name = getattr(definition, "name", "")
            candidates = self.top_level_symbols.get((canonical_target, name), [])
            if len(candidates) == 1:
                return candidates[0], False

        return None, saw_external

    def _resolve_fallback(self, ref: _Reference) -> str | None:
        if ref.edge_type != "calls":
            return None

        source_node = self.nodes_by_id.get(ref.source_id, {})
        file_path = source_node.get("file_path", ref.file_path)
        if ref.fallback_kind == "self_or_cls":
            container_id = source_node.get("container_id", "")
            class_id = container_id if container_id.startswith("class::") else ""
            if class_id:
                return self.class_methods.get((class_id, ref.name))

        if ref.fallback_kind == "same_file_bare":
            candidates = self.top_level_symbols.get((file_path, ref.name), [])
            if len(candidates) == 1:
                return candidates[0]

        return None

    def _mark_unresolved(self, source_id: str, edge_type: str, *, external: bool) -> None:
        node = self.nodes_by_id[source_id]
        key = f"external_{edge_type}" if external else edge_type
        node["unresolved_counts"][key] += 1
        if external:
            self.external_totals[edge_type] += 1
        else:
            self.unresolved_totals[edge_type] += 1

    def _add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        *,
        line: int,
        resolver: str,
    ) -> None:
        if source_id == target_id and edge_type == "contains":
            return
        key = (source_id, target_id, edge_type)
        if key not in self.edges_by_key:
            self.edges_by_key[key] = {
                "source": source_id,
                "target": target_id,
                "type": edge_type,
                "count": 1,
                "line": line,
                "resolver": resolver,
            }
            return
        self.edges_by_key[key]["count"] += 1

    def _build_stats(self) -> dict[str, Any]:
        node_kind_counts = Counter(node["kind"] for node in self.nodes_by_id.values())
        edge_type_counts = Counter(edge["type"] for edge in self.edges_by_key.values())
        return {
            "nodes": len(self.nodes_by_id),
            "edges": len(self.edges_by_key),
            "by_kind": {kind: node_kind_counts.get(kind, 0) for kind in NODE_KINDS},
            "by_edge_type": {edge_type: edge_type_counts.get(edge_type, 0) for edge_type in EDGE_TYPES},
            "unresolved": {edge_type: self.unresolved_totals.get(edge_type, 0) for edge_type in ("imports", "calls", "inherits")},
            "external": {edge_type: self.external_totals.get(edge_type, 0) for edge_type in ("imports", "calls", "inherits")},
        }

    def _sorted_nodes(self) -> list[dict[str, Any]]:
        return sorted(
            self.nodes_by_id.values(),
            key=lambda node: (node["kind"], node["file_path"], node["line_start"], node["qualname"]),
        )

    def _sorted_edges(self) -> list[dict[str, Any]]:
        return sorted(
            self.edges_by_key.values(),
            key=lambda edge: (edge["type"], edge["source"], edge["target"]),
        )


class CodeSymbolGraph:
    """in-memory code symbol graph."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.version = data["version"]
        self.generated_at = data["generated_at"]
        self.manifest = data.get("manifest", {})
        self.stats_data = data.get("stats", {})
        self.nodes = data.get("nodes", [])
        self.edges = data.get("edges", [])
        self._nodes_by_id: dict[str, dict[str, Any]] = {}
        self._out_edges: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._in_edges: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._build_lookup()

    @classmethod
    def build(
        cls,
        scan_dirs: Sequence[tuple[Path, str]] = CODE_SCAN_DIRS,
        project_root: str | Path = HGK_ROOT,
        jedi_module=None,
    ) -> "CodeSymbolGraph":
        jedi_mod = jedi_module or _load_jedi()
        builder = _CodeSymbolGraphBuilder(
            scan_dirs=scan_dirs,
            project_root=Path(project_root),
            jedi_module=jedi_mod,
        )
        return builder.build()

    @classmethod
    def load(cls, path: str | Path = CODE_SYMBOL_GRAPH_INDEX) -> "CodeSymbolGraph":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data)

    def save(self, path: str | Path = CODE_SYMBOL_GRAPH_INDEX) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict()
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=str(target.parent),
            suffix=".tmp",
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            tmp_name = handle.name
        os.replace(tmp_name, target)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "manifest": self.manifest,
            "stats": self.stats(),
            "nodes": self._sorted_nodes(),
            "edges": self._sorted_edges(),
        }

    def stats(self) -> dict[str, Any]:
        node_kind_counts = Counter(node["kind"] for node in self._nodes_by_id.values())
        edge_type_counts = Counter(edge["type"] for edge in self.edges)
        unresolved = Counter()
        external = Counter()
        for node in self._nodes_by_id.values():
            counts = node.get("unresolved_counts", {})
            for edge_type in ("imports", "calls", "inherits"):
                unresolved[edge_type] += int(counts.get(edge_type, 0))
                external[edge_type] += int(counts.get(f"external_{edge_type}", 0))
        return {
            "nodes": len(self._nodes_by_id),
            "edges": len(self.edges),
            "by_kind": {kind: node_kind_counts.get(kind, 0) for kind in NODE_KINDS},
            "by_edge_type": {edge_type: edge_type_counts.get(edge_type, 0) for edge_type in EDGE_TYPES},
            "unresolved": {edge_type: unresolved.get(edge_type, 0) for edge_type in ("imports", "calls", "inherits")},
            "external": {edge_type: external.get(edge_type, 0) for edge_type in ("imports", "calls", "inherits")},
        }

    def search_symbols(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """deterministic ranking で symbol を検索する。"""
        raw = query.strip()
        if not raw:
            return []

        canonical_pathqual = _canonicalize_pathqual_query(raw)
        canonical_node_id = _canonicalize_node_id_query(raw)
        raw_lower = raw.lower()
        matches: list[dict[str, Any]] = []

        for node in self._nodes_by_id.values():
            node_id = node["id"]
            pathqual = f"{node['file_path']}::{node['qualname']}"
            qualname = node["qualname"]
            bare = node["symbol_name"]
            reasons: tuple[int, str] | None = None

            if raw == node_id or (canonical_node_id and canonical_node_id == node_id):
                reasons = (0, "exact node id")
            elif raw == pathqual or (canonical_pathqual and canonical_pathqual == pathqual):
                reasons = (1, "exact path::qualname")
            elif raw == qualname:
                reasons = (2, "exact qualname")
            elif qualname.endswith(f".{raw}"):
                reasons = (3, "qualname suffix")
            elif raw == bare:
                reasons = (4, "exact bare name")
            elif (
                raw_lower in bare.lower()
                or raw_lower in qualname.lower()
                or raw_lower in node["file_path"].lower()
            ):
                reasons = (5, "substring")

            if reasons is None:
                continue

            matches.append(
                {
                    "node_id": node_id,
                    "kind": node["kind"],
                    "symbol_name": bare,
                    "qualname": qualname,
                    "file_path": node["file_path"],
                    "line_start": node["line_start"],
                    "line_end": node["line_end"],
                    "container_id": node.get("container_id", ""),
                    "in_edges": len(self._in_edges.get(node_id, [])),
                    "out_edges": len(self._out_edges.get(node_id, [])),
                    "match_priority": reasons[0],
                    "match_reason": reasons[1],
                }
            )

        matches.sort(
            key=lambda match: (
                match["match_priority"],
                match["file_path"],
                match["line_start"],
                match["qualname"],
                match["node_id"],
            )
        )
        return matches[:limit]

    def resolve_symbol(self, query: str, limit: int = 10) -> dict[str, Any]:
        matches = self.search_symbols(query, limit=limit)
        if not matches:
            return {"status": "not_found", "query": query, "matches": []}

        best_priority = matches[0]["match_priority"]
        best_matches = [match for match in matches if match["match_priority"] == best_priority]
        if len(best_matches) == 1:
            match = best_matches[0]
            return {
                "status": "unique",
                "query": query,
                "match": match,
                "node": self.node_snapshot(match["node_id"]),
            }
        return {
            "status": "ambiguous",
            "query": query,
            "matches": best_matches,
        }

    def node_snapshot(self, node_id: str) -> dict[str, Any]:
        node = self._nodes_by_id[node_id]
        return {
            **node,
            "in_edges": len(self._in_edges.get(node_id, [])),
            "out_edges": len(self._out_edges.get(node_id, [])),
        }

    def neighborhood(
        self,
        node_id: str,
        *,
        direction: str = DEFAULT_DIRECTION,
        edge_types: Sequence[str] | None = None,
        depth: int = 1,
    ) -> dict[str, Any]:
        if direction not in {"in", "out", "both"}:
            raise ValueError(f"Unsupported direction: {direction}")
        depth = max(1, min(int(depth), MAX_NEIGHBORHOOD_DEPTH))
        selected_edge_types = list(edge_types) if edge_types else list(EDGE_TYPES)

        visited_nodes: set[str] = {node_id}
        frontier: set[str] = {node_id}
        selected_edges: dict[tuple[str, str, str], dict[str, Any]] = {}

        for _ in range(depth):
            next_frontier: set[str] = set()
            for current in frontier:
                if direction in {"out", "both"}:
                    for edge in self._out_edges.get(current, []):
                        if edge["type"] not in selected_edge_types:
                            continue
                        key = (edge["source"], edge["target"], edge["type"])
                        selected_edges[key] = edge
                        next_frontier.add(edge["target"])
                if direction in {"in", "both"}:
                    for edge in self._in_edges.get(current, []):
                        if edge["type"] not in selected_edge_types:
                            continue
                        key = (edge["source"], edge["target"], edge["type"])
                        selected_edges[key] = edge
                        next_frontier.add(edge["source"])
            next_frontier -= visited_nodes
            visited_nodes |= next_frontier
            frontier = next_frontier
            if not frontier:
                break

        return {
            "root": self.node_snapshot(node_id),
            "direction": direction,
            "depth": depth,
            "edge_types": selected_edge_types,
            "nodes": [self.node_snapshot(nid) for nid in sorted(visited_nodes)],
            "edges": sorted(
                selected_edges.values(),
                key=lambda edge: (edge["type"], edge["source"], edge["target"]),
            ),
        }

    def _build_lookup(self) -> None:
        self._nodes_by_id = {node["id"]: node for node in self.nodes}
        self._out_edges = defaultdict(list)
        self._in_edges = defaultdict(list)
        for edge in self.edges:
            self._out_edges[edge["source"]].append(edge)
            self._in_edges[edge["target"]].append(edge)

    def _sorted_nodes(self) -> list[dict[str, Any]]:
        return sorted(
            self._nodes_by_id.values(),
            key=lambda node: (node["kind"], node["file_path"], node["line_start"], node["qualname"]),
        )

    def _sorted_edges(self) -> list[dict[str, Any]]:
        return sorted(
            self.edges,
            key=lambda edge: (edge["type"], edge["source"], edge["target"]),
        )


def _canonicalize_pathqual_query(query: str) -> str | None:
    if query.count("::") != 1:
        return None
    path_part, qualname = query.split("::", 1)
    if not path_part:
        return None
    if not (path_part.endswith(".py") or "/" in path_part or path_part.startswith(".")):
        return None
    canonical = _canonical_code_path(path_part)
    return f"{canonical}::{qualname}"


def _canonicalize_node_id_query(query: str) -> str | None:
    parts = query.split("::", 2)
    if len(parts) != 3 or parts[0] not in {"class", "function", "method"}:
        return None
    kind, path_part, qualname = parts
    canonical = _canonical_code_path(path_part)
    return f"{kind}::{canonical}::{qualname}"
