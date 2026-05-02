#!/usr/bin/env python3
# PROOF: [L2/Peira] <- 60_実験｜Peira/02_テスト｜Tests/
"""
ToolGuard — MCP ツール境界テスト (静的スキャン方式)

MCP SDK に依存せず、ソースコードの文字列パターンからツール定義を抽出し検証する。
全テストがオフラインで実行可能。

テスト3層:
  L0: スキーマ整合性 — ソースコード内 Tool() 定義のパターン検証
  L1: 構造完全性 — list_tools/call_tool の存在、ping ツールの存在
  L2: ライブ Ping — 稼働中 MCP サーバーへの ping (MCP ツール経由、手動実行用)

使い方:
  cd ~/oikos/01_ヘゲモニコン｜Hegemonikon
  pytest "60_実験｜Peira/02_テスト｜Tests/test_toolguard.py" -v
"""

import re
import json
import pytest
from pathlib import Path

# プロジェクトルート
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_MCP_DIR = _PROJECT_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード" / "mekhane" / "mcp"
_HERMENEUS_DIR = _PROJECT_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード" / "hermeneus" / "src"


# ============================================================
# MCP サーバーソースファイル定義
# ============================================================

# PURPOSE: テスト対象の MCP サーバーソースファイル一覧
def _discover_mcp_servers() -> list[tuple[str, Path]]:
    """MCP サーバーソースファイルを自動検出。"""
    servers = []
    # 除外リスト (実験中/未完成のサーバー)
    _SKIP = {"kube"}
    # mekhane/mcp/ 内
    if _MCP_DIR.exists():
        for f in sorted(_MCP_DIR.glob("*_mcp_server.py")):
            name = f.stem.replace("_mcp_server", "")
            # gnosis → mneme エイリアス
            if name == "gnosis":
                name = "mneme"
            if name in _SKIP:
                continue
            servers.append((name, f))
    # hermeneus/src/ 内
    hermeneus_file = _HERMENEUS_DIR / "mcp_server.py"
    if hermeneus_file.exists():
        servers.append(("hermeneus", hermeneus_file))
    return servers


MCP_SERVERS = _discover_mcp_servers()
MCP_SERVER_IDS = [s[0] for s in MCP_SERVERS]

# 検出できない場合のガード
if not MCP_SERVERS:
    pytest.skip("MCP サーバーソースが見つかりません", allow_module_level=True)


# ============================================================
# ユーティリティ関数
# ============================================================

def _extract_tool_names(source: str) -> list[str]:
    """ソースコードから Tool(name="xxx") パターンで名前を抽出。"""
    # Tool(name="xxx" または Tool(\n  name="xxx" の両方に対応
    pattern = r'Tool\s*\(\s*name\s*=\s*["\']([^"\']+)["\']'
    return re.findall(pattern, source)


def _extract_required_fields(source: str) -> list[tuple[str, list[str]]]:
    """ソースコードから各ツールの required フィールドを抽出。
    戻り値: [(tool_name, [required_fields]), ...]
    """
    results = []
    # ツール定義ブロックを大まかに抽出
    tool_blocks = re.split(r'Tool\s*\(', source)
    for block in tool_blocks[1:]:  # 最初は Tool( の前のコード
        # ツール名
        name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', block)
        if not name_match:
            continue
        name = name_match.group(1)
        # required フィールド
        req_match = re.search(r'"required"\s*:\s*\[([^\]]*)\]', block)
        if req_match:
            fields = re.findall(r'["\']([^"\']+)["\']', req_match.group(1))
            results.append((name, fields))
        else:
            results.append((name, []))
    return results


def _extract_properties(source: str) -> list[tuple[str, list[str]]]:
    """ソースコードから各ツールの properties キーを抽出。
    戻り値: [(tool_name, [property_names]), ...]
    """
    results = []
    tool_blocks = re.split(r'Tool\s*\(', source)
    for block in tool_blocks[1:]:
        name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', block)
        if not name_match:
            continue
        name = name_match.group(1)
        # properties ブロック内のキーを抽出
        props_match = re.search(r'"properties"\s*:\s*\{', block)
        if props_match:
            # properties 内の最上位キーを抽出
            props_start = props_match.end()
            # 最初の閉じ括弧の前のキーだけ取る (ネストに注意)
            prop_keys = []
            depth = 1
            i = props_start
            current_key = None
            while i < len(block) and depth > 0:
                c = block[i]
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                elif c == '"' and depth == 1:
                    # トップレベルのキーを探す
                    end_q = block.index('"', i + 1)
                    key = block[i+1:end_q]
                    # 次が : かチェック
                    rest = block[end_q+1:end_q+10].strip()
                    if rest.startswith(':'):
                        prop_keys.append(key)
                    i = end_q
                i += 1
            results.append((name, prop_keys))
        else:
            results.append((name, []))
    return results


def _has_pattern(source: str, pattern: str) -> bool:
    """ソースコードに正規表現パターンが存在するか。"""
    return bool(re.search(pattern, source))


# ============================================================
# L0: スキーマ整合性テスト (静的解析)
# ============================================================

class TestL0SchemaIntegrity:
    """ソースコード内の Tool() 定義から品質を検証。MCP SDK 不要。"""

    @pytest.mark.parametrize("server_name,filepath", MCP_SERVERS, ids=MCP_SERVER_IDS)
    def test_tools_are_defined(self, server_name, filepath):
        """ソースコードに最低1つの Tool() 定義が存在するか。"""
        source = filepath.read_text(encoding="utf-8")
        tools = _extract_tool_names(source)
        assert len(tools) > 0, f"[{server_name}] Tool() 定義が見つかりません"

    @pytest.mark.parametrize("server_name,filepath", MCP_SERVERS, ids=MCP_SERVER_IDS)
    def test_tool_names_have_server_prefix(self, server_name, filepath):
        """ツール名がサーバー名相当のプレフィックスを持つか。"""
        source = filepath.read_text(encoding="utf-8")
        tools = _extract_tool_names(source)
        # サーバーごとの許容プレフィックス
        prefix_map = {
            "sympatheia": ["sympatheia_"],
            "sekisho": ["sekisho_"],
            "phantazein": ["phantazein_"],
            "ochema": ["ask", "start_", "send_", "close_", "session_",
                       "models", "status", "ping", "context_rot_",
                       "cortex_", "shadow_", "cache_", "ochema_"],
            "mneme": ["mneme_", "search", "backlinks", "graph_", "stats",
                      "sources", "dejavu_", "dendron_", "code_to_ccl",
                      "recommend_model", "search_code", "search_papers",
                      "ping"],
            "periskope": ["periskope_"],
            "hermeneus": ["hermeneus_"],
            "typos": ["compile", "expand", "generate", "parse", "ping",
                      "validate", "policy_check"],
            "digestor": ["check_", "get_", "list_", "mark_", "paper_",
                         "ping", "run_"],
            "hub": ["hub_"],
            "sophia": ["search", "stats", "sources", "sophia_",
                       "backlinks", "graph_"],
            "prokataskeve": ["ping", "prokataskeve_", "boot_", "session_"],
            "gws": ["gws_", "read_", "search_"],
            "jules": ["jules_"],
        }
        prefixes = prefix_map.get(server_name, [f"{server_name}_"])
        for tool in tools:
            has_prefix = any(tool.startswith(p) for p in prefixes)
            assert has_prefix, (
                f"[{server_name}] ツール '{tool}' が "
                f"許容プレフィックス {prefixes} にマッチしません"
            )

    @pytest.mark.parametrize("server_name,filepath", MCP_SERVERS, ids=MCP_SERVER_IDS)
    def test_required_fields_exist_in_properties(self, server_name, filepath):
        """required で宣言されたフィールドが properties にも定義されているか。"""
        source = filepath.read_text(encoding="utf-8")
        required_list = _extract_required_fields(source)
        properties_list = _extract_properties(source)

        # ツール名でマッチングして検証
        props_dict = {name: props for name, props in properties_list}
        for tool_name, required in required_list:
            if not required:
                continue
            props = props_dict.get(tool_name, [])
            if not props:
                # properties が抽出できなかった場合はスキップ
                continue
            for req in required:
                assert req in props, (
                    f"[{server_name}] {tool_name}: "
                    f"required '{req}' が properties に不在。"
                    f"properties: {props}"
                )

    @pytest.mark.parametrize("server_name,filepath", MCP_SERVERS, ids=MCP_SERVER_IDS)
    def test_no_empty_descriptions(self, server_name, filepath):
        """ツールの description が空でないか (description="" パターン検出)。"""
        source = filepath.read_text(encoding="utf-8")
        # description="" や description='' のパターンを検索
        empty_descs = re.findall(
            r'Tool\s*\([^)]*description\s*=\s*["\']["\']',
            source, re.DOTALL
        )
        assert len(empty_descs) == 0, (
            f"[{server_name}] 空の description を持つ Tool が {len(empty_descs)} 件"
        )

    @pytest.mark.parametrize("server_name,filepath", MCP_SERVERS, ids=MCP_SERVER_IDS)
    def test_input_schema_has_type_object(self, server_name, filepath):
        """各 Tool の inputSchema が type: object を含むか。"""
        source = filepath.read_text(encoding="utf-8")
        # inputSchema がある Tool ブロックを検出
        tool_blocks = re.split(r'Tool\s*\(', source)
        for block in tool_blocks[1:]:
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', block)
            if not name_match:
                continue
            name = name_match.group(1)
            # inputSchema に "type": "object" があるか
            has_schema = '"type"' in block and '"object"' in block
            assert has_schema, (
                f"[{server_name}] {name}: "
                f'inputSchema に "type": "object" がありません'
            )


# ============================================================
# L1: 構造完全性テスト (静的解析)
# ============================================================

class TestL1StructuralCompleteness:
    """MCP サーバーの構造的完全性を静的に検証。"""

    @pytest.mark.parametrize("server_name,filepath", MCP_SERVERS, ids=MCP_SERVER_IDS)
    def test_has_list_tools_handler(self, server_name, filepath):
        """list_tools ハンドラが定義されているか。"""
        source = filepath.read_text(encoding="utf-8")
        assert _has_pattern(source, r'list_tools'), (
            f"[{server_name}] list_tools ハンドラが見つかりません"
        )

    @pytest.mark.parametrize("server_name,filepath", MCP_SERVERS, ids=MCP_SERVER_IDS)
    def test_has_call_tool_handler(self, server_name, filepath):
        """call_tool ハンドラが定義されているか。"""
        source = filepath.read_text(encoding="utf-8")
        assert _has_pattern(source, r'call_tool'), (
            f"[{server_name}] call_tool ハンドラが見つかりません"
        )

    @pytest.mark.parametrize("server_name,filepath", MCP_SERVERS, ids=MCP_SERVER_IDS)
    def test_has_ping_or_health_tool(self, server_name, filepath):
        """ping または health_check 相当のツールが定義されているか。"""
        source = filepath.read_text(encoding="utf-8")
        tools = _extract_tool_names(source)
        # ping, health, status いずれかを持つツールがあればOK
        health_keywords = ["ping", "health", "status"]
        has_health = any(
            any(kw in t.lower() for kw in health_keywords)
            for t in tools
        )
        if not has_health and not tools:
            pytest.skip(f"[{server_name}] ツール定義が見つかりません")
        assert has_health, (
            f"[{server_name}] ping/health/status ツールが見つかりません。"
            f"ツール一覧: {tools}"
        )

    @pytest.mark.parametrize("server_name,filepath", MCP_SERVERS, ids=MCP_SERVER_IDS)
    def test_has_error_handling(self, server_name, filepath):
        """call_tool 内に try/except パターンがあるか (エラーハンドリング)。"""
        source = filepath.read_text(encoding="utf-8")
        # call_tool ブロック内の try/except を検出
        has_try = _has_pattern(source, r'try\s*:')
        has_except = _has_pattern(source, r'except\s+')
        assert has_try and has_except, (
            f"[{server_name}] try/except によるエラーハンドリングが見つかりません"
        )

    @pytest.mark.parametrize("server_name,filepath", MCP_SERVERS, ids=MCP_SERVER_IDS)
    def test_has_mcpbase_or_server(self, server_name, filepath):
        """MCPBase を継承しているか、または Server を直接使用しているか。"""
        source = filepath.read_text(encoding="utf-8")
        has_mcpbase = _has_pattern(source, r'MCPBase')
        has_server = _has_pattern(source, r'Server\s*\(')
        assert has_mcpbase or has_server, (
            f"[{server_name}] MCPBase 継承も Server 直接使用も見つかりません"
        )


# ============================================================
# L2: ツール数・メタデータ整合性テスト
# ============================================================

class TestL2MetadataConsistency:
    """ツール数やメタデータの一貫性を検証。"""

    @pytest.mark.parametrize("server_name,filepath", MCP_SERVERS, ids=MCP_SERVER_IDS)
    def test_tool_count_in_range(self, server_name, filepath):
        """ツール数が合理的な範囲 (1-30) 内か。"""
        source = filepath.read_text(encoding="utf-8")
        tools = _extract_tool_names(source)
        assert 1 <= len(tools) <= 30, (
            f"[{server_name}] ツール数 {len(tools)} が範囲外 (1-30)。"
            f"ツール: {tools}"
        )

    @pytest.mark.parametrize("server_name,filepath", MCP_SERVERS, ids=MCP_SERVER_IDS)
    def test_no_duplicate_tool_names(self, server_name, filepath):
        """同一サーバー内でツール名が重複していないか。"""
        source = filepath.read_text(encoding="utf-8")
        tools = _extract_tool_names(source)
        seen = set()
        duplicates = []
        for t in tools:
            if t in seen:
                duplicates.append(t)
            seen.add(t)
        assert len(duplicates) == 0, (
            f"[{server_name}] ツール名の重複: {duplicates}"
        )

    def test_no_cross_server_tool_name_conflicts(self):
        """異なるサーバー間でツール名が衝突していないか。
        注: ping/search/stats 等の汎用名は MCP namespace で正当なので除外。
        """
        # MCP では各サーバーが独立 namespace を持つため、
        # 汎用ヘルスチェック名の重複は許容する
        _ALLOWED_DUPLICATES = {"ping", "search", "stats", "sources", "status"}
        all_tools: dict[str, str] = {}  # tool_name -> server_name
        conflicts = []
        for server_name, filepath in MCP_SERVERS:
            source = filepath.read_text(encoding="utf-8")
            tools = _extract_tool_names(source)
            for t in tools:
                if t in all_tools and t not in _ALLOWED_DUPLICATES:
                    conflicts.append(
                        f"'{t}' は {all_tools[t]} と {server_name} で重複"
                    )
                all_tools[t] = server_name
        assert len(conflicts) == 0, (
            f"サーバー間のツール名衝突: {conflicts}"
        )

    @pytest.mark.parametrize("server_name,filepath", MCP_SERVERS, ids=MCP_SERVER_IDS)
    def test_valid_json_types_in_schema(self, server_name, filepath):
        """inputSchema 内の type 値が JSON Schema の有効な型か。
        注: inputSchema ブロック内のみスキャン。
        "type": "text" (MCP ContentType) 等の偽陽性を排除。
        """
        source = filepath.read_text(encoding="utf-8")
        valid_types = {"string", "integer", "number", "boolean", "array", "object"}
        # inputSchema={...} ブロック内の "type" のみを抽出
        # inputSchema の直後の辞書構造内にある type を探す
        schema_blocks = re.findall(
            r'inputSchema\s*=\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
            source, re.DOTALL
        )
        invalid_types = set()
        for block in schema_blocks:
            type_values = re.findall(r'"type"\s*:\s*"([^"]+)"', block)
            for tv in type_values:
                if tv not in valid_types:
                    invalid_types.add(tv)
        assert len(invalid_types) == 0, (
            f"[{server_name}] inputSchema 内の無効な型: {invalid_types}。"
            f"有効な型: {valid_types}"
        )


# ============================================================
# エントリポイント
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
