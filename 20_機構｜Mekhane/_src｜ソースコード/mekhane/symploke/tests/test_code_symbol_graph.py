# PROOF: [L3/テスト] <- mekhane/symploke/code_symbol_graph.py の機械証明が必要→test_code_symbol_graph.py が担う
"""
Tests for the Python code symbol graph.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys


sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


def _node(
    node_id: str,
    kind: str,
    qualname: str,
    file_path: str,
    *,
    symbol_name: str | None = None,
    line_start: int = 1,
    line_end: int = 1,
    container_id: str = "",
) -> dict:
    return {
        "id": node_id,
        "kind": kind,
        "symbol_name": symbol_name or qualname.split(".")[-1],
        "qualname": qualname,
        "file_path": file_path,
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


class _FakeDefinition:
    def __init__(self, name: str, module_path: str | None, line: int | None, type_: str) -> None:
        self.name = name
        self.module_path = Path(module_path) if module_path else None
        self.line = line
        self.type = type_


class _FakeProject:
    def __init__(self, path: str) -> None:
        self.path = Path(path)


class _FakeJedi:
    Project = _FakeProject

    class Script:
        def __init__(self, code: str, path: str, project: _FakeProject) -> None:
            self.code = code
            self.path = Path(path)
            self.project = project.path
            self.lines = code.splitlines()
            self._index = _build_fake_project_index(self.project)

        def goto(self, line: int, column: int, **_) -> list[_FakeDefinition]:
            line_text = self.lines[line - 1]
            token = _token_at(line_text, column)
            if not token:
                return []

            if f"self.{token}" in line_text or f"cls.{token}" in line_text:
                return []

            file_key = str(self.path.resolve(strict=False))
            aliases = self._index["aliases_by_file"].get(file_key, {})
            if token in aliases:
                return aliases[token]

            file_defs = self._index["defs_by_file"].get(file_key, {})
            if token in file_defs:
                return file_defs[token]

            return self._index["defs_by_name"].get(token, [])


def _token_at(line_text: str, column: int) -> str:
    for match in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", line_text):
        if match.start() <= column < match.end():
            return match.group(0)
    return ""


def _module_name(project_root: Path, py_file: Path) -> str:
    rel = py_file.relative_to(project_root)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = py_file.stem
    return ".".join(parts)


def _build_fake_project_index(project_root: Path) -> dict:
    defs_by_name: dict[str, list[_FakeDefinition]] = {}
    defs_by_file: dict[str, dict[str, list[_FakeDefinition]]] = {}
    module_files: dict[str, Path] = {}

    py_files = sorted(project_root.rglob("*.py"))
    for py_file in py_files:
        source = py_file.read_text(encoding="utf-8")
        tree = __import__("ast").parse(source, filename=str(py_file))
        file_key = str(py_file.resolve(strict=False))
        defs_by_file[file_key] = {}
        module_name = _module_name(project_root, py_file)
        module_files[module_name] = py_file
        module_files[py_file.stem] = py_file

        for node in tree.body:
            if node.__class__.__name__ in {"FunctionDef", "AsyncFunctionDef"}:
                definition = _FakeDefinition(node.name, file_key, node.lineno, "function")
                defs_by_name.setdefault(node.name, []).append(definition)
                defs_by_file[file_key].setdefault(node.name, []).append(definition)
            elif node.__class__.__name__ == "ClassDef":
                definition = _FakeDefinition(node.name, file_key, node.lineno, "class")
                defs_by_name.setdefault(node.name, []).append(definition)
                defs_by_file[file_key].setdefault(node.name, []).append(definition)

    aliases_by_file: dict[str, dict[str, list[_FakeDefinition]]] = {}
    for py_file in py_files:
        source = py_file.read_text(encoding="utf-8")
        tree = __import__("ast").parse(source, filename=str(py_file))
        file_key = str(py_file.resolve(strict=False))
        aliases: dict[str, list[_FakeDefinition]] = {}

        for node in tree.body:
            if node.__class__.__name__ == "Import":
                for alias in node.names:
                    key = alias.asname or alias.name.split(".")[0]
                    target = module_files.get(alias.name) or module_files.get(alias.name.split(".")[-1])
                    if target is None:
                        aliases[key] = [_FakeDefinition(key, None, None, "module")]
                    else:
                        aliases[key] = [_FakeDefinition(key, str(target), None, "module")]
            elif node.__class__.__name__ == "ImportFrom":
                module_name = node.module or ""
                for alias in node.names:
                    key = alias.asname or alias.name
                    target = defs_by_name.get(alias.name)
                    if target:
                        aliases[key] = target
                        continue
                    module_target = module_files.get(module_name) or module_files.get(module_name.split(".")[-1])
                    if module_target is None:
                        aliases[key] = [_FakeDefinition(key, None, None, "module")]
                    else:
                        aliases[key] = [_FakeDefinition(key, str(module_target), None, "module")]

        aliases_by_file[file_key] = aliases

    return {
        "defs_by_name": defs_by_name,
        "defs_by_file": defs_by_file,
        "aliases_by_file": aliases_by_file,
    }


def _make_temp_repo(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "base.py").write_text(
        "class Base:\n"
        "    pass\n",
        encoding="utf-8",
    )
    (pkg / "mod_b.py").write_text(
        "def helper():\n"
        "    return 42\n",
        encoding="utf-8",
    )
    (pkg / "mod_a.py").write_text(
        "import json\n"
        "from pkg.mod_b import helper\n"
        "from pkg.base import Base\n\n"
        "def local_target():\n"
        "    return 1\n\n"
        "def top():\n"
        "    return local_target()\n\n"
        "class Child(Base):\n"
        "    def method(self):\n"
        "        helper()\n"
        "        self.helper()\n"
        "        missing()\n\n"
        "    def helper(self):\n"
        "        return 2\n",
        encoding="utf-8",
    )
    return tmp_path


def _build_graph(tmp_path: Path):
    from mekhane.symploke.code_symbol_graph import CodeSymbolGraph

    repo_root = _make_temp_repo(tmp_path)
    return CodeSymbolGraph.build(
        scan_dirs=[(repo_root, "tmp")],
        project_root=repo_root,
        jedi_module=_FakeJedi,
    )


def test_build_graph_covers_core_edges_and_counts(tmp_path: Path):
    graph = _build_graph(tmp_path)

    edges = {(edge["source"], edge["target"], edge["type"]) for edge in graph.edges}
    stats = graph.stats()

    file_mod_a = "file::" + str((tmp_path / "pkg" / "mod_a.py").resolve(strict=False))
    func_top = "function::" + str((tmp_path / "pkg" / "mod_a.py").resolve(strict=False)) + "::top"
    func_local = "function::" + str((tmp_path / "pkg" / "mod_a.py").resolve(strict=False)) + "::local_target"
    class_child = "class::" + str((tmp_path / "pkg" / "mod_a.py").resolve(strict=False)) + "::Child"
    method_child = "method::" + str((tmp_path / "pkg" / "mod_a.py").resolve(strict=False)) + "::Child.method"
    method_helper = "method::" + str((tmp_path / "pkg" / "mod_a.py").resolve(strict=False)) + "::Child.helper"
    func_imported = "function::" + str((tmp_path / "pkg" / "mod_b.py").resolve(strict=False)) + "::helper"
    class_base = "class::" + str((tmp_path / "pkg" / "base.py").resolve(strict=False)) + "::Base"

    assert (file_mod_a, func_top, "contains") in edges
    assert (file_mod_a, func_local, "contains") in edges
    assert (class_child, method_child, "contains") in edges
    assert (class_child, method_helper, "contains") in edges
    assert (file_mod_a, func_imported, "imports") in edges
    assert (file_mod_a, class_base, "imports") in edges
    assert (class_child, class_base, "inherits") in edges
    assert (func_top, func_local, "calls") in edges
    assert (method_child, func_imported, "calls") in edges
    assert (method_child, method_helper, "calls") in edges

    method_node = next(node for node in graph.nodes if node["id"] == method_child)
    file_node = next(node for node in graph.nodes if node["id"] == file_mod_a)
    assert method_node["unresolved_counts"]["calls"] == 1
    assert file_node["unresolved_counts"]["external_imports"] == 1
    assert stats["by_edge_type"]["contains"] >= 4
    assert stats["external"]["imports"] == 1
    assert stats["unresolved"]["calls"] == 1


def test_graph_roundtrip_and_stale_detection(tmp_path: Path):
    from mekhane.symploke.code_symbol_graph import (
        CodeSymbolGraph,
        clear_code_symbol_graph_stale_cache,
        is_code_symbol_graph_stale,
    )

    repo_root = _make_temp_repo(tmp_path / "repo")
    graph = CodeSymbolGraph.build(
        scan_dirs=[(repo_root, "tmp")],
        project_root=repo_root,
        jedi_module=_FakeJedi,
    )

    graph_path = tmp_path / "code_symbol_graph.json"
    graph.save(graph_path)
    loaded = CodeSymbolGraph.load(graph_path)

    assert loaded.stats() == graph.stats()
    assert loaded.manifest == graph.manifest
    clear_code_symbol_graph_stale_cache()
    assert not is_code_symbol_graph_stale(
        graph_path,
        scan_dirs=[(repo_root, "tmp")],
        force_refresh=True,
    )

    newer_file = repo_root / "pkg" / "z_new.py"
    newer_file.write_text("def later():\n    return 0\n", encoding="utf-8")
    assert not is_code_symbol_graph_stale(
        graph_path,
        scan_dirs=[(repo_root, "tmp")],
        force_refresh=False,
    )
    assert is_code_symbol_graph_stale(
        graph_path,
        scan_dirs=[(repo_root, "tmp")],
        force_refresh=True,
    )


def test_search_ranking_and_ambiguity():
    from mekhane.symploke.code_symbol_graph import CodeSymbolGraph

    path_a = "/tmp/a.py"
    path_b = "/tmp/b.py"
    path_c = "/tmp/c.py"
    payload = {
        "version": "test",
        "generated_at": "2026-04-18T00:00:00+00:00",
        "manifest": {},
        "stats": {},
        "nodes": [
            _node(f"function::{path_a}::alpha", "function", "alpha", path_a),
            _node(f"function::{path_b}::alpha", "function", "alpha", path_b),
            _node(f"method::{path_c}::Thing.alpha", "method", "Thing.alpha", path_c, container_id=f"class::{path_c}::Thing"),
            _node(f"class::{path_c}::Thing", "class", "Thing", path_c),
        ],
        "edges": [
            {
                "source": f"class::{path_c}::Thing",
                "target": f"method::{path_c}::Thing.alpha",
                "type": "contains",
                "count": 1,
                "line": 3,
                "resolver": "ast",
            }
        ],
    }

    graph = CodeSymbolGraph(payload)

    exact_id_hits = graph.search_symbols(f"function::{path_a}::alpha")
    assert exact_id_hits[0]["match_reason"] == "exact node id"

    exact_pathqual_hits = graph.search_symbols(f"{path_c}::Thing.alpha")
    assert exact_pathqual_hits[0]["match_reason"] == "exact path::qualname"

    exact_qualname_hits = graph.search_symbols("Thing.alpha")
    assert exact_qualname_hits[0]["match_reason"] == "exact qualname"

    suffix_hits = graph.search_symbols("alpha", limit=10)
    assert suffix_hits[0]["match_reason"] == "exact qualname"
    assert graph.resolve_symbol("alpha")["status"] == "ambiguous"

    substring_hits = graph.search_symbols("/tmp/c.py", limit=10)
    assert substring_hits[0]["match_reason"] == "substring"
