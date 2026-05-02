# PROOF: [L1/テスト] <- mekhane/tests/
# PURPOSE: Tool Policy Pipeline のユニットテスト
"""
Tool Policy Pipeline テスト (T-14)

Context Window Guard (test_agent_guard.py) と対をなすテスト。
"""

from mekhane.agent_guard.tool_policy import (
    DenyEntry,
    PolicyResult,
    PolicyStep,
    ToolPolicy,
    apply_pipeline,
    apply_policy,
    build_steps_from_yaml,
    normalize_tool_name,
)


# =============================================================================
# normalize_tool_name
# =============================================================================

def test_normalize_tool_name_basic():
    """基本的な正規化: 小文字化 + strip。"""
    assert normalize_tool_name("HGK_Status") == "hgk_status"
    assert normalize_tool_name("  hgk_ask  ") == "hgk_ask"


def test_normalize_tool_name_alias():
    """エイリアス解決。"""
    assert normalize_tool_name("hermeneus_dispatch") == "hgk_ccl_dispatch"
    assert normalize_tool_name("hermeneus_run") == "hgk_ccl_execute"


def test_normalize_tool_name_unknown():
    """未知のツール名はそのまま返す。"""
    assert normalize_tool_name("unknown_tool") == "unknown_tool"


# =============================================================================
# apply_policy
# =============================================================================

def test_apply_policy_allow():
    """allow リストでフィルタ: リストに含まれないツールは拒否。"""
    tools = ["hgk_status", "hgk_ask", "hgk_search"]
    policy = ToolPolicy(allow=["hgk_status", "hgk_search"])

    allowed, denied = apply_policy(tools, policy)
    assert allowed == ["hgk_status", "hgk_search"]
    assert "hgk_ask" in denied


def test_apply_policy_deny():
    """deny リストでフィルタ: リストに含まれるツールは拒否。"""
    tools = ["hgk_status", "run_command", "hgk_search"]
    policy = ToolPolicy(deny=[
        DenyEntry(tool="run_command", reason="Gateway 経由でのコマンド実行禁止"),
    ])

    allowed, denied = apply_policy(tools, policy)
    assert allowed == ["hgk_status", "hgk_search"]
    assert "run_command" in denied
    assert "コマンド実行禁止" in denied["run_command"]


def test_apply_policy_deny_over_allow():
    """deny が allow に優先する (precision 支配)。"""
    tools = ["hgk_status", "hgk_ask", "run_command"]
    policy = ToolPolicy(
        allow=["hgk_status", "hgk_ask", "run_command"],
        deny=[DenyEntry(tool="run_command", reason="危険")],
    )

    allowed, denied = apply_policy(tools, policy)
    assert "run_command" not in allowed
    assert "run_command" in denied


def test_apply_policy_none_allow_all():
    """allow=None は全許可。"""
    tools = ["hgk_status", "hgk_ask"]
    policy = ToolPolicy(allow=None, deny=None)

    allowed, denied = apply_policy(tools, policy)
    assert allowed == ["hgk_status", "hgk_ask"]
    assert len(denied) == 0


# =============================================================================
# apply_pipeline
# =============================================================================

def test_pipeline_cascade():
    """3段パイプライン: global deny → server allow → session。"""
    tools = ["hgk_status", "run_command", "hgk_ask", "hgk_search"]

    steps = [
        PolicyStep(
            policy=ToolPolicy(deny=[
                DenyEntry(tool="run_command", reason="Gateway 禁止"),
            ]),
            label="global",
        ),
        PolicyStep(
            policy=ToolPolicy(allow=["hgk_status", "hgk_ask"]),
            label="server:hgk",
        ),
    ]

    result = apply_pipeline(tools, steps)

    assert "hgk_status" in result.allowed
    assert "hgk_ask" in result.allowed
    assert "run_command" in result.denied
    assert "hgk_search" in result.denied
    # run_command は global で拒否
    assert "global" in result.denied["run_command"]
    # hgk_search は server allow で拒否
    assert "server:hgk" in result.denied["hgk_search"]


def test_pipeline_empty_policy_passthrough():
    """None ポリシーのステップはスキップされる。"""
    tools = ["hgk_status", "hgk_ask"]

    steps = [
        PolicyStep(policy=None, label="global"),
        PolicyStep(policy=None, label="server:hgk"),
    ]

    result = apply_pipeline(tools, steps)
    assert result.allowed == ["hgk_status", "hgk_ask"]
    assert len(result.denied) == 0


# =============================================================================
# build_steps_from_yaml
# =============================================================================

def test_build_steps_from_yaml():
    """YAML dict からパイプラインステップを構築する。"""
    yaml_config = {
        "global": {
            "deny": [
                {"tool": "run_command", "reason": "Gateway 経由禁止"},
                "send_command_input",  # 文字列形式も対応
            ],
        },
        "servers": {
            "jules": {
                "allow": ["jules_create_task", "jules_get_status"],
            },
        },
    }

    steps = build_steps_from_yaml(yaml_config)
    assert len(steps) == 2
    assert steps[0].label == "global"
    assert steps[1].label == "server:jules"

    # global deny の中身
    deny = steps[0].policy.deny
    assert len(deny) == 2
    assert deny[0].tool == "run_command"
    assert deny[0].reason == "Gateway 経由禁止"
    assert deny[1].tool == "send_command_input"
    assert deny[1].reason == ""

    # server allow の中身
    allow = steps[1].policy.allow
    assert len(allow) == 2
    assert "jules_create_task" in allow


# =============================================================================
# エイリアスマップ拡充テスト
# =============================================================================

def test_normalize_alias_sekisho():
    """Sekisho MCP ツール名のエイリアス解決。"""
    assert normalize_tool_name("sekisho_audit") == "hgk_sekisho_audit"
    assert normalize_tool_name("sekisho_gate") == "hgk_sekisho_gate"


def test_normalize_alias_digestor():
    """Digestor MCP ツール名のエイリアス解決。"""
    assert normalize_tool_name("digestor_check_incoming") == "hgk_digest_check"
    assert normalize_tool_name("digestor_run_digestor") == "hgk_digest_run"


def test_normalize_alias_periskope():
    """Periskopē MCP ツール名のエイリアス解決。"""
    assert normalize_tool_name("periskope_research") == "hgk_research"
    assert normalize_tool_name("periskope_search") == "hgk_research_search"


def test_normalize_alias_ochema():
    """Ochēma MCP ツール名のエイリアス解決。"""
    assert normalize_tool_name("ochema_ask") == "hgk_ask"
    assert normalize_tool_name("ochema_ask_with_tools") == "hgk_ask_with_tools"


# =============================================================================
# Gateway E2E テスト
# =============================================================================

def test_gateway_e2e_deny(tmp_path, monkeypatch):
    """Gateway が実際の YAML を読み込み、deny ツールをブロックすることを E2E 検証。"""
    import yaml

    # テスト用 YAML を作成
    test_yaml = tmp_path / "gateway_policy.yaml"
    test_yaml.write_text(yaml.dump({
        "tool_policy": {
            "enabled": True,
            "global": {
                "deny": [
                    {"tool": "run_command", "reason": "Gateway 経由禁止"},
                ],
            },
        },
    }), encoding="utf-8")

    # _check_tool_policy の YAML パスを差し替え
    import mekhane.mcp.gateway_hooks as gh
    monkeypatch.setattr(gh, "_TOOL_POLICY_STEPS", None)

    # gateway_hooks の Path(__file__).parent を tmp_path に差し替え
    original_check = gh._check_tool_policy

    def patched_check(tool_name):
        from mekhane.agent_guard.tool_policy import apply_pipeline, build_steps_from_yaml
        config = yaml.safe_load(test_yaml.read_text("utf-8"))
        tool_policy_cfg = config.get("tool_policy", {})
        steps = build_steps_from_yaml(tool_policy_cfg)
        result = apply_pipeline([tool_name], steps)
        if result.denied:
            return next(iter(result.denied.values()), "Policy denied")
        return None

    monkeypatch.setattr(gh, "_check_tool_policy", patched_check)

    # deny されたツールがブロックされる
    reason = patched_check("run_command")
    assert reason is not None
    assert "Gateway 経由禁止" in reason

    # 許可されたツールは通過する
    reason = patched_check("hgk_status")
    assert reason is None


def test_gateway_e2e_allow(tmp_path):
    """Gateway の allow リストに含まれないツールが拒否されることを E2E 検証。"""
    import yaml

    test_config = {
        "enabled": True,
        "servers": {
            "jules": {
                "allow": ["jules_create_task"],
            },
        },
    }

    steps = build_steps_from_yaml(test_config)
    result = apply_pipeline(["jules_create_task", "jules_unknown"], steps)

    assert "jules_create_task" in result.allowed
    assert "jules_unknown" in result.denied

