# PROOF: [L3/テスト] <- mekhane/mcp/mneme_server.py の symbol graph 入口が必要→test_mneme_symbol_graph.py が担う
"""
Tests for mneme_server symbol graph surfaces.
"""

from __future__ import annotations

import asyncio
import importlib
import json
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


def _import_mneme_server(monkeypatch):
    from mekhane.mcp import mcp_base

    class _DummyTextContent:
        def __init__(self, type: str, text: str) -> None:
            self.type = type
            self.text = text

    class _DummyTool:
        def __init__(self, name, description, inputSchema) -> None:
            self.name = name
            self.description = description
            self.inputSchema = inputSchema

    class _DummyServer:
        def list_tools(self):
            return lambda func: func

        def call_tool(self):
            return lambda func: func

    class _DummyBase:
        def __init__(self, name: str, version: str, instructions: str) -> None:
            self.server = _DummyServer()
            self.log = lambda *args, **kwargs: None
            self.TextContent = _DummyTextContent
            self.Tool = _DummyTool
            self.project_root = Path.cwd()

    monkeypatch.setattr(mcp_base, "MCPBase", _DummyBase)
    sys.modules.pop("mekhane.mcp.mneme_server", None)
    return importlib.import_module("mekhane.mcp.mneme_server")


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


def _make_graph():
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
            _node(f"class::{path_c}::Thing", "class", "Thing", path_c),
            _node(
                f"method::{path_c}::Thing.beta",
                "method",
                "Thing.beta",
                path_c,
                container_id=f"class::{path_c}::Thing",
            ),
        ],
        "edges": [
            {
                "source": f"class::{path_c}::Thing",
                "target": f"method::{path_c}::Thing.beta",
                "type": "contains",
                "count": 1,
                "line": 3,
                "resolver": "ast",
            },
            {
                "source": f"method::{path_c}::Thing.beta",
                "target": f"function::{path_a}::alpha",
                "type": "calls",
                "count": 1,
                "line": 5,
                "resolver": "jedi",
            },
        ],
    }
    return CodeSymbolGraph(payload)


def test_search_code_symbol_uses_symbol_graph(monkeypatch):
    mneme_server = _import_mneme_server(monkeypatch)

    monkeypatch.setattr(mneme_server, "_require_code_symbol_graph", lambda: _make_graph())

    result = mneme_server._handle_search_code(
        {"query": "Thing.beta", "code_mode": "symbol", "k": 5}
    )

    assert "Code Symbol Search Results" in result[0].text
    assert "Thing.beta" in result[0].text
    assert "exact qualname" in result[0].text


def test_require_code_symbol_graph_uses_cached_graph_without_sync_rebuild(monkeypatch, tmp_path: Path):
    from mekhane import paths
    from mekhane.symploke import code_symbol_graph as symbol_mod
    mneme_server = _import_mneme_server(monkeypatch)

    graph_path = tmp_path / "code_symbol_graph.json"
    graph_path.write_text("{}", encoding="utf-8")
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(paths, "CODE_SYMBOL_GRAPH_INDEX", graph_path)
    monkeypatch.setattr(symbol_mod, "get_code_symbol_graph", lambda path=None: _make_graph())
    monkeypatch.setattr(
        symbol_mod,
        "rebuild_code_symbol_graph",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("sync rebuild should not run")),
    )
    monkeypatch.setattr(
        mneme_server,
        "_start_code_symbol_graph_refresh",
        lambda log_fn, *, force_stale_refresh: calls.append(("start", force_stale_refresh)) or True,
    )
    monkeypatch.setitem(mneme_server._code_symbol_graph_status, "probe_started", False)
    monkeypatch.setitem(mneme_server._code_symbol_graph_status, "known_stale", None)

    graph = mneme_server._require_code_symbol_graph()

    assert graph.resolve_symbol("Thing.beta")["status"] == "unique"
    assert calls == [("start", True)]


def test_require_code_symbol_graph_missing_starts_background_refresh(monkeypatch, tmp_path: Path):
    from mekhane import paths
    from mekhane.symploke import code_symbol_graph as symbol_mod
    mneme_server = _import_mneme_server(monkeypatch)

    graph_path = tmp_path / "missing_symbol_graph.json"
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(paths, "CODE_SYMBOL_GRAPH_INDEX", graph_path)
    monkeypatch.setattr(symbol_mod, "is_jedi_available", lambda: True)
    monkeypatch.setattr(
        mneme_server,
        "_start_code_symbol_graph_refresh",
        lambda log_fn, *, force_stale_refresh: calls.append(("start", force_stale_refresh)) or True,
    )
    monkeypatch.setitem(mneme_server._code_symbol_graph_status, "probe_started", False)
    monkeypatch.setitem(mneme_server._code_symbol_graph_status, "known_stale", None)

    try:
        mneme_server._require_code_symbol_graph()
    except RuntimeError as exc:
        message = str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("missing graph should raise")

    assert "Background rebuild started" in message
    assert calls == [("start", True)]


def test_graph_code_symbol_returns_ambiguous_candidates(monkeypatch):
    mneme_server = _import_mneme_server(monkeypatch)

    monkeypatch.setattr(mneme_server, "_require_code_symbol_graph", lambda: _make_graph())

    result = asyncio.run(
        mneme_server._handle_graph_facade(
            {"action": "code_symbol", "symbol": "alpha", "output": "json"}
        )
    )
    payload = json.loads(result[0].text)

    assert payload["status"] == "ambiguous"
    assert len(payload["matches"]) == 2
    assert all(match["qualname"] == "alpha" for match in payload["matches"])


def test_graph_code_symbol_neighborhood_filters_edges(monkeypatch):
    mneme_server = _import_mneme_server(monkeypatch)

    monkeypatch.setattr(mneme_server, "_require_code_symbol_graph", lambda: _make_graph())

    result = asyncio.run(
        mneme_server._handle_graph_facade(
            {
                "action": "code_symbol",
                "symbol": "Thing.beta",
                "direction": "out",
                "edge_types": ["calls"],
                "depth": 2,
                "output": "json",
            }
        )
    )
    payload = json.loads(result[0].text)

    assert payload["root"]["qualname"] == "Thing.beta"
    assert payload["direction"] == "out"
    assert payload["depth"] == 2
    assert payload["edge_types"] == ["calls"]
    assert len(payload["edges"]) == 1
    assert payload["edges"][0]["type"] == "calls"


def test_start_code_symbol_graph_refresh_is_singleflight(monkeypatch):
    mneme_server = _import_mneme_server(monkeypatch)

    starts: list[str] = []

    class _DummyThread:
        def __init__(self, *args, **kwargs) -> None:
            self._alive = False
            starts.append(kwargs["name"])

        def start(self) -> None:
            self._alive = True

        def is_alive(self) -> bool:
            return self._alive

    monkeypatch.setattr(mneme_server.threading, "Thread", _DummyThread)
    monkeypatch.setattr(mneme_server, "_code_symbol_graph_refresh_thread", None)

    first = mneme_server._start_code_symbol_graph_refresh(
        lambda *_: None,
        force_stale_refresh=True,
    )
    second = mneme_server._start_code_symbol_graph_refresh(
        lambda *_: None,
        force_stale_refresh=True,
    )

    assert first is True
    assert second is False
    assert starts == ["code-symbol-graph-refresh"]


def test_symbol_error_does_not_break_existing_text_search(monkeypatch):
    mneme_server = _import_mneme_server(monkeypatch)

    class _DummyResult:
        def __init__(self) -> None:
            self.doc_id = "doc-1"
            self.score = 0.9
            self.content = "def needle(): pass"
            self.metadata = {
                "ki_name": "needle",
                "file_path": "/tmp/needle.py",
                "line_start": 1,
                "line_end": 1,
            }

    class _DummyEngine:
        def search(self, query, sources, k):
            assert query == "needle"
            assert sources == ["code"]
            assert k == 1
            return [_DummyResult()]

    monkeypatch.setattr(
        mneme_server,
        "_require_code_symbol_graph",
        lambda: (_ for _ in ()).throw(
            RuntimeError("Code symbol graph is missing or stale: /tmp/code_symbol_graph.json. jedi is required to rebuild it.")
        ),
    )
    monkeypatch.setattr(mneme_server, "get_engine", lambda: _DummyEngine())

    symbol_error = mneme_server._handle_search_code(
        {"query": "alpha", "code_mode": "symbol", "k": 1}
    )
    text_ok = mneme_server._handle_search_code(
        {"query": "needle", "code_mode": "text", "k": 1}
    )

    assert "Code symbol graph error" in symbol_error[0].text
    assert "Code Search Results" in text_ok[0].text
    assert "needle" in text_ok[0].text
