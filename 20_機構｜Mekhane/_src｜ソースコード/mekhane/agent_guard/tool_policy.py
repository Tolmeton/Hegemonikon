from __future__ import annotations
# PROOF: [L2/AgentGuard] <- mekhane/agent_guard/ Tool Policy Pipeline
"""
Tool Access Policy — ツールの有効/無効をカスケードパイプラインで制御する。

PURPOSE: Gateway 経由のツール呼出に対して allow/deny フィルタリングを実行する。
  2段構成: global (全サーバー共通) → server (MCP サーバー別)

  ※ これはツールの「アクセス可否」を制御する。
    ツールの「パラメータ制約」(max_input_size, rate_limit 等) は
    gateway_policy.yaml の tools: セクション + _utils.py _get_policy() が担当する。

FEP 解釈:
  deny = 高 precision prior (この行動は VFE を増大させるという強い信念)
  allow = 低 precision prior (この行動空間は安全だという弱い信念)
  deny > allow の優先順は精度加重から自然に導出される。
"""


from dataclasses import dataclass, field
from typing import Optional


# =============================================================================
# Tool Name Normalization
# =============================================================================

# PURPOSE: MCP ツール名のエイリアス解決
_TOOL_NAME_ALIASES: dict[str, str] = {
    # Hermēneus MCP サーバーのツール名 → Gateway 正規名
    "hermeneus_dispatch": "hgk_ccl_dispatch",
    "hermeneus_execute": "hgk_ccl_execute",
    "hermeneus_run": "hgk_ccl_execute",
    # Sekisho MCP サーバーのツール名 → Gateway 正規名
    "sekisho_audit": "hgk_sekisho_audit",
    "sekisho_gate": "hgk_sekisho_gate",
    # Digestor MCP サーバーのツール名 → Gateway 正規名
    "digestor_check_incoming": "hgk_digest_check",
    "digestor_list_candidates": "hgk_digest_list",
    "digestor_run_digestor": "hgk_digest_run",
    "digestor_mark_processed": "hgk_digest_mark",
    # Periskopē MCP サーバーのツール名 → Gateway 正規名
    "periskope_research": "hgk_research",
    "periskope_search": "hgk_research_search",
    # Ochēma MCP サーバーのツール名 → Gateway 正規名
    "ochema_ask": "hgk_ask",
    "ochema_ask_with_tools": "hgk_ask_with_tools",
}


def normalize_tool_name(name: str) -> str:
    """ツール名を正規化する。小文字化 + エイリアス解決。"""
    normalized = name.strip().lower()
    return _TOOL_NAME_ALIASES.get(normalized, normalized)


# =============================================================================
# Policy Types
# =============================================================================

@dataclass
class DenyEntry:
    """deny リストの1エントリ。理由フィールドで「なぜ危険か」を明示する。

    FEP 解釈: 高 precision prior — このツールが VFE を増大させるという
    具体的な根拠を reason に記録する。
    """
    tool: str
    reason: str = ""

    def __post_init__(self) -> None:
        self.tool = normalize_tool_name(self.tool)


@dataclass
class ToolPolicy:
    """allow/deny のペア。deny が allow に優先する (precision 支配)。

    - allow=None: 全許可 (prior なし = 全行動空間を許容)
    - allow=[]: 全拒否 (空集合への制約)
    - deny=None: 拒否なし
    """
    allow: list[str] | None = None
    deny: list[DenyEntry] | None = None

    def __post_init__(self) -> None:
        if self.allow is not None:
            self.allow = [normalize_tool_name(t) for t in self.allow]
        deny_list = self.deny
        if deny_list is not None:
            for entry in deny_list:
                entry.tool = normalize_tool_name(entry.tool)


@dataclass
class PolicyStep:
    """パイプラインの1段。ラベルでどの層のポリシーか識別する。"""
    policy: ToolPolicy | None
    label: str


@dataclass
class PolicyResult:
    """パイプライン適用結果。"""
    allowed: list[str]
    denied: dict[str, str]   # tool_name → reason
    warnings: list[str] = field(default_factory=list)


# =============================================================================
# Policy Application
# =============================================================================

# PURPOSE: 単一ポリシーでツールリストをフィルタする
def apply_policy(
    tool_names: list[str],
    policy: ToolPolicy,
) -> tuple[list[str], dict[str, str]]:
    """ToolPolicy を適用してツールリストをフィルタする。

    allow リストの意味論 (v1.1 修正):
      - allow=None: 全許可 (prior なし = 全行動空間を許容)
      - allow=[...]: リストに含まれるツールのみ許可。
        **リストに含まれないツールはスルー（通過）する。**
        (= allowlist はサーバーに属するツール群の定義)
      - deny は常に優先 (precision 支配)

    Returns:
        (allowed_tools, denied_map) — denied_map は {tool: reason}
    """
    normalized = [normalize_tool_name(t) for t in tool_names]

    # deny セット構築 (precision 支配: deny > allow)
    deny_map: dict[str, str] = {}
    deny_list = policy.deny
    if deny_list is not None:
        for entry in deny_list:
            deny_map[entry.tool] = entry.reason

    # allow セット構築
    allow_list = policy.allow
    allow_set: set[str] | None = None
    if allow_list is not None:
        allow_set = {t for t in allow_list}

    allowed: list[str] = []
    denied: dict[str, str] = {}

    for tool in normalized:
        if tool in deny_map:
            denied[tool] = deny_map[tool]
        elif allow_set is not None and tool not in allow_set:
            # v1.1: allowlist に含まれないツールはスルー (拒否しない)
            # サーバー別 allowlist は「そのサーバーのツール定義」であり、
            # 無関係なツールを拒否する意図ではない
            allowed.append(tool)
        else:
            allowed.append(tool)

    return allowed, denied


# =============================================================================
# Pipeline
# =============================================================================

# PURPOSE: 複数ポリシーを順次適用するカスケードパイプライン
def apply_pipeline(
    tool_names: list[str],
    steps: list[PolicyStep],
) -> PolicyResult:
    """多層ポリシーパイプラインを適用する。

    各ステップで surviving tools を順次フィルタリングする。
    deny > allow の優先順は各ステップ内で保証される。
    """
    current = [normalize_tool_name(t) for t in tool_names]
    all_denied: dict[str, str] = {}
    warnings: list[str] = []

    for step in steps:
        if step.policy is None:
            continue

        step_policy: ToolPolicy = step.policy
        allowed, denied = apply_policy(current, step_policy)

        for tool, reason in denied.items():
            all_denied[tool] = f"[{step.label}] {reason}" if reason else f"[{step.label}] Denied"

        current = allowed

    return PolicyResult(
        allowed=current,
        denied=all_denied,
        warnings=warnings,
    )


# =============================================================================
# Default Pipeline Steps (HGK 2段構成)
# =============================================================================

# PURPOSE: gateway_policy.yaml から HGK 用のデフォルト3段パイプラインを構築する
def build_steps_from_yaml(policy_config: dict) -> list[PolicyStep]:
    """gateway_policy.yaml の tool_policy セクションからパイプラインを構築する。

    YAML 構造:
        tool_policy:
          global:
            deny:
              - tool: run_command
                reason: "Gateway 経由でのコマンド実行は禁止"
          servers:
            jules:
              allow: [jules_create_task, jules_get_status, ...]
    """
    steps: list[PolicyStep] = []

    # 1. Global policy
    global_cfg = policy_config.get("global", {})
    if global_cfg:
        steps.append(PolicyStep(
            policy=_parse_policy(global_cfg),
            label="global",
        ))

    # 2. Server policies (各サーバー別)
    servers_cfg = policy_config.get("servers", {})
    for server_name, server_cfg in servers_cfg.items():
        if server_cfg:
            steps.append(PolicyStep(
                policy=_parse_policy(server_cfg),
                label=f"server:{server_name}",
            ))

    return steps


def _parse_policy(cfg: dict) -> ToolPolicy:
    """YAML の dict を ToolPolicy に変換する。"""
    allow = cfg.get("allow")
    deny_raw = cfg.get("deny")

    deny_entries: list[DenyEntry] | None = None
    if deny_raw is not None:
        deny_entries = []
        for item in deny_raw:
            if isinstance(item, str):
                deny_entries.append(DenyEntry(tool=item))
            elif isinstance(item, dict):
                deny_entries.append(DenyEntry(
                    tool=item.get("tool", ""),
                    reason=item.get("reason", ""),
                ))

    return ToolPolicy(allow=allow, deny=deny_entries)
