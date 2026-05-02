#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/hub_config.py A0→Hub MCP Proxy 設定
"""
Hub MCP Router 設定

3 軸 router / backend placement / Daimonion pipeline の単一ソース。
run_mcp_service.sh / deploy-mcp-services.sh / hub_mcp_server.py はここを参照する。

FEP 3能力 (τὸ -τικόν 系):
  Aisthetikon (τὸ αἰσθητικόν) — 知覚能力 (S群)
  Dianoetikon (τὸ διανοητικόν) — 推論能力 (I群)
  Poietikon (τὸ ποιητικόν) — 生産能力 (E群)

Daimonion (δαιμόνιον) — ソクラテスの内なる声:
  3 Stoicheia の自動監視を統一実体として実装。
  α Tapeinophrosyne (S-I): 反証 — prior を疑え
  β Autonomia (S-II): 探索監視 — 能動的に探せ
  γ Akribeia (S-III): 精密監査 — 規則適合 PASS/BLOCK
"""
from __future__ import annotations

import os

AXIS_TO_GROUP: dict[str, str] = {
    "aisthetikon": "S",
    "dianoetikon": "I",
    "poietikon": "E",
}
GROUP_TO_AXIS: dict[str, str] = {group: axis for axis, group in AXIS_TO_GROUP.items()}
AXIS_PORTS: dict[str, int] = {
    "aisthetikon": 9720,
    "dianoetikon": 9721,
    "poietikon": 9722,
}
DEFAULT_REMOTE_MCP_HOST = os.environ.get("HGK_REMOTE_MCP_HOST", "100.83.204.102")

LOCAL_RUN_PLACEMENTS = frozenset({"local", "hybrid", "local_ephemeral", "local_first"})
REMOTE_RUN_PLACEMENTS = frozenset({"remote"})

# PURPOSE: [L2-auto] バックエンドサーバー定義
# placement:
#   local           = ローカル常駐
#   hybrid          = ローカル常駐だが remote 依存あり (例: ochema -> remote LS)
#   remote          = 100.83 側で常駐
#   local_ephemeral = ローカル都度起動
#   local_first     = 当面ローカル優先
# runtime:
#   streamable-http / stdio_mcp / subprocess / external_mcp
# remote_dependency:
#   backend が別ホスト依存を持つ場合の補足
BACKENDS: dict[str, dict] = {
    "ochema": {
        "port": 9701,
        "module": "mekhane.mcp.ochema_mcp_server",
        "fep_group": "I",
        "axis": "dianoetikon",
        "placement": "hybrid",
        "runtime": "streamable-http",
        "remote_dependency": "ls_pool",
    },
    "sympatheia": {
        "port": 9702,
        "module": "mekhane.mcp.sympatheia_mcp_server",
        "fep_group": "I",
        "axis": "dianoetikon",
        "placement": "local",
        "runtime": "streamable-http",
        "remote_dependency": None,
    },
    "hermeneus": {
        "port": 9703,
        "module": "hermeneus.src.mcp_server",
        "fep_group": "I",
        "axis": "dianoetikon",
        "placement": "local",
        "runtime": "streamable-http",
        "remote_dependency": None,
    },
    "phantazein": {
        "port": 9704,
        "module": "mekhane.mcp.mneme_server",
        "fep_group": "S",
        "axis": "aisthetikon",
        "placement": "local",
        "runtime": "streamable-http",
        "remote_dependency": None,
    },  # 旧 mneme — 知識検索 query server
    "sekisho": {
        "port": 9705,
        "module": "mekhane.mcp.sekisho_mcp_server",
        "fep_group": "I",
        "axis": "dianoetikon",
        "placement": "local",
        "runtime": "streamable-http",
        "remote_dependency": None,
    },
    "periskope": {
        "port": 9706,
        "module": "mekhane.mcp.periskope_mcp_server",
        "fep_group": "S",
        "axis": "aisthetikon",
        "placement": "remote",
        "runtime": "streamable-http",
        "remote_dependency": None,
    },
    "digestor": {
        "port": 9707,
        "module": "mekhane.mcp.digestor_mcp_server",
        "fep_group": "S",
        "axis": "aisthetikon",
        "placement": "remote",
        "runtime": "streamable-http",
        "remote_dependency": None,
    },
    "jules": {
        "port": 9708,
        "module": "mekhane.mcp.jules_mcp_server",
        "fep_group": "E",
        "axis": "poietikon",
        "placement": "remote",
        "runtime": "streamable-http",
        "remote_dependency": None,
    },
    "typos": {
        "port": 9709,
        "module": "mekhane.mcp.typos_mcp_server",
        "fep_group": "I",
        "axis": "dianoetikon",
        "placement": "local",
        "runtime": "streamable-http",
        "remote_dependency": None,
    },
    "phantazein-boot": {
        "port": 9710,
        "module": "mekhane.mcp.phantazein_mcp_server",
        "fep_group": "meta",
        "axis": None,
        "placement": "local",
        "runtime": "streamable-http",
        "remote_dependency": None,
    },  # boot/health (将来 phantazein に統合)
    "gws": {
        "port": 9711,
        "module": "mekhane.mcp.gws_mcp_server",
        "fep_group": "S",
        "axis": "aisthetikon",
        "placement": "local",
        "runtime": "streamable-http",
        "remote_dependency": None,
    },
    "opsis": {
        "port": 9712,
        "module": "mekhane.mcp.opsis_mcp_server",
        "fep_group": "S",
        "axis": "aisthetikon",
        "placement": "local",
        "runtime": "streamable-http",
        "remote_dependency": None,
    },
    "xmcp": {
        "port": 9713,
        "module": None,
        "fep_group": "S",
        "axis": "aisthetikon",
        "placement": "local_first",
        "runtime": "external_mcp",
        "remote_dependency": None,
    },  # X (Twitter) API MCP — SNS運用+トレンド+検索 (外部プロセス)
    "codex-mcp": {
        "type": "stdio_mcp",
        "command": ["codex", "mcp-server"],
        "fep_group": "E",
        "axis": "poietikon",
        "placement": "local_ephemeral",
        "runtime": "stdio_mcp",
        "remote_dependency": None,
    },  # OpenAI Codex CLI MCP server mode — 実装・形式化・数学
    "gemini-cli": {
        "type": "subprocess",
        "module": None,
        "fep_group": "S",
        "axis": "aisthetikon",
        "placement": "local_ephemeral",
        "runtime": "subprocess",
        "remote_dependency": None,
    },  # gemini CLI via subprocess
    "notebooklm": {
        "type": "subprocess",
        "module": None,
        "fep_group": "S",
        "axis": "aisthetikon",
        "placement": "local_ephemeral",
        "runtime": "subprocess",
        "remote_dependency": None,
    },  # NotebookLM CLI — トークン消費ゼロの外部 RAG (Google AI ウルトラ)
    "copilot": {
        "type": "subprocess",
        "module": None,
        "fep_group": "I",
        "axis": "dianoetikon",
        "placement": "local_ephemeral",
        "runtime": "subprocess",
        "remote_dependency": None,
    },  # GitHub Copilot CLI
    "codex": {
        "type": "subprocess",
        "module": None,
        "fep_group": "E",
        "axis": "poietikon",
        "placement": "local_ephemeral",
        "runtime": "subprocess",
        "remote_dependency": None,
    },  # OpenAI Codex CLI fallback
    "cursor-agent": {
        "type": "subprocess",
        "module": None,
        "fep_group": "E",
        "axis": "poietikon",
        "placement": "local_ephemeral",
        "runtime": "subprocess",
        "remote_dependency": None,
    },  # Cursor Agent CLI
}

# PURPOSE: [L2-auto] FEP グループ名の定義
# -tikon 系: アリストテレスの能力名 (faculty) で統一。Nomoi Phase 名 (行為名) と直交。
FEP_GROUPS: dict[str, str] = {
    "S": "Aisthetikon (τὸ αἰσθητικόν) — 知覚能力: π_s 最大化 (調べたいとき)",
    "I": "Dianoetikon (τὸ διανοητικόν) — 推論能力: 内部モデル更新 (処理を深めたいとき)",
    "E": "Poietikon (τὸ ποιητικόν) — 生産能力: π_a 最大化 (成果物を生成したいとき)",
    "meta": "Meta — インフラ/健全性",
}

# FEP グループの短縮名 (ツール名用)
FEP_GROUP_TOOL_NAMES: dict[str, tuple[str, str]] = {
    # fep_group: (new_name, legacy_name)
    "S": ("hub_aisthetikon", "hub_sense"),
    "I": ("hub_dianoetikon", "hub_infer"),
    "E": ("hub_poietikon", "hub_effect"),
}


def get_backends_by_fep_group(group: str) -> list[str]:
    """指定した FEP グループに属するバックエンド名のリストを返す。"""
    return [name for name, cfg in BACKENDS.items() if cfg.get("fep_group") == group]

# PURPOSE: [L2-auto] バックエンドの MCP エンドポイント URL を生成
def backend_url(name: str, host: str = "127.0.0.1") -> str:
    """バックエンドの streamable-http URL を返す。

    subprocess バックエンド (port なし) の場合は ValueError を送出。
    """
    cfg = BACKENDS[name]
    if "port" not in cfg:
        raise ValueError(f"Backend '{name}' has no port (type={cfg.get('type', 'unknown')})")
    return f"http://{host}:{cfg['port']}/mcp"


def axis_url(axis_name: str, host: str = "127.0.0.1") -> str:
    """3軸 router の URL を返す。"""
    port = AXIS_PORTS[axis_name]
    return f"http://{host}:{port}/mcp"


def get_backend_axis(name: str) -> str | None:
    """バックエンドが属する軸名を返す。"""
    cfg = BACKENDS[name]
    axis = cfg.get("axis")
    if axis:
        return axis
    fep_group = cfg.get("fep_group")
    return GROUP_TO_AXIS.get(fep_group)


def backend_runs_in_profile(name: str, profile: str) -> bool:
    """指定 profile のホストで実際に起動すべきバックエンドか。"""
    placement = BACKENDS[name].get("placement", "local")
    if profile == "remote":
        return placement in REMOTE_RUN_PLACEMENTS
    if profile == "local":
        return placement in LOCAL_RUN_PLACEMENTS
    raise ValueError(f"Unknown profile: {profile}")


def backend_is_delegated_in_local_router(name: str) -> bool:
    """local router で remote axis upstream に委譲されるバックエンドか。"""
    return BACKENDS[name].get("placement") == "remote"


def get_backends_for_axis(axis_name: str) -> list[str]:
    """指定した axis に属するバックエンド一覧を返す。"""
    return [name for name in BACKENDS if get_backend_axis(name) == axis_name]


def get_runnable_backends_for_axis(axis_name: str, profile: str) -> list[str]:
    """指定 axis/profile で直接接続すべきバックエンド一覧を返す。"""
    return [
        name for name in get_backends_for_axis(axis_name)
        if backend_runs_in_profile(name, profile)
    ]


def get_delegated_backends_for_axis(axis_name: str, profile: str) -> list[str]:
    """指定 axis/profile で upstream 委譲になるバックエンド一覧を返す。"""
    if profile != "local":
        return []
    return [
        name for name in get_backends_for_axis(axis_name)
        if backend_is_delegated_in_local_router(name)
    ]


# PURPOSE: [L2-auto] 旧 hub 起動の後方互換デフォルトポート
HUB_PORT = AXIS_PORTS["aisthetikon"]

# PURPOSE: [L2-auto] パイプライン設定
PIPELINE_CONFIG = {
    # --- Ph1: ログ ---
    "log_enabled": True,

    # --- Daimonion (δαιμόνιον) — 統一監視体 ---
    # 旧 Shadow (Ph2) + 旧 Gate/Sekisho (Ph3) を 3 Stoicheia モードで統合

    # --- α Tapeinophrosyne (S-I): 反証 — prior を疑え ---
    # 旧 shadow_* 設定。連続的 (per-tool-call)。
    "daimonion_alpha_enabled": True,
    "daimonion_alpha_cooldown": 15.0,             # 最小クールダウン (秒)
    "daimonion_alpha_importance_threshold": 0.3,  # 最小重要度 (これ未満はスキップ)
    "daimonion_alpha_complexity_threshold": 0.2,  # 最小複雑度
    "daimonion_alpha_model": "gemini-3.1-pro-preview",
    "daimonion_alpha_max_tokens": 65536,
    "daimonion_alpha_timeout": 60.0,

    # --- β Autonomia (S-II): 探索監視 — 能動的に探せ ---
    # 新設。連続的 (per-tool-call)。α と並列実行。
    "daimonion_beta_enabled": True,
    "daimonion_beta_cooldown": 30.0,              # β は α より低頻度 (探索パターンは蓄積が必要)
    "daimonion_beta_importance_threshold": 0.5,   # 重要なツールのみ
    "daimonion_beta_model": "gemini-3.1-pro-preview",
    "daimonion_beta_max_tokens": 4096,
    "daimonion_beta_timeout": 30.0,

    # --- γ Akribeia (S-III): 精密監査 — 規則適合 PASS/BLOCK ---
    # 旧 gate_* 設定。終端的 (per-response)。
    "daimonion_gamma_enabled": True,
    "daimonion_gamma_auto_importance_threshold": 0.7,  # 自動発火: importance >= この値
    "daimonion_gamma_model": "gemini-3.1-pro-preview",
    "daimonion_gamma_max_tokens": 4096,
    "daimonion_gamma_timeout": 60.0,

    # --- 後方互換エイリアス (旧名 → 新名マッピング) ---
    # 既存コードが shadow_*/gate_* で参照している場合のフォールバック
    "shadow_enabled": True,              # → daimonion_alpha_enabled
    "shadow_cooldown": 15.0,             # → daimonion_alpha_cooldown
    "shadow_importance_threshold": 0.3,  # → daimonion_alpha_importance_threshold
    "shadow_complexity_threshold": 0.2,  # → daimonion_alpha_complexity_threshold
    "shadow_model": "gemini-3.1-pro-preview",  # → daimonion_alpha_model
    "shadow_max_tokens": 65536,          # → daimonion_alpha_max_tokens
    "shadow_timeout": 60.0,             # → daimonion_alpha_timeout
    "gate_enabled": True,               # → daimonion_gamma_enabled
    "gate_auto_importance_threshold": 0.7,  # → daimonion_gamma_auto_importance_threshold
    "gate_model": "gemini-3.1-pro-preview",  # → daimonion_gamma_model
    "gate_max_tokens": 4096,            # → daimonion_gamma_max_tokens
    "gate_timeout": 60.0,              # → daimonion_gamma_timeout

    # --- Secretary (Vision B 統合パイプライン) ---
    "secretary_routing_model": "gemini-3-flash-preview",   # 構造化JSON出力のみ → flash で十分
    "secretary_routing_max_tokens": 4096,
    "secretary_routing_timeout": 30.0,
    "secretary_shadow_model": "gemini-3.1-pro-preview",     # secretary shadow = 通常 shadow と同じ Pro
    "secretary_gate_depth": "L1",          # 毎回実行するので L1 で十分 (L2 は ~27s → L1 は ~15s)
    "secretary_gate_always": True,         # secretary では常に Gate 実行
    "secretary_shadow_parallel": True,     # Shadow を実行と並列に走らせる
}

# PURPOSE: [L2-auto] バックエンド×ツール別の重要度テーブル
# (importance, complexity) — Shadow がフィードバックを付ける価値の高さ
# 未登録ツールは DEFAULT_TOOL_SCORES を使用
DEFAULT_TOOL_SCORES = (0.3, 0.2)

TOOL_SCORES: dict[str, tuple[float, float]] = {
    # --- hermeneus (CCL エンジン) ---
    "hermeneus_run":        (0.9, 0.8),  # CCL 実行 = 最高価値
    "hermeneus_execute":    (0.9, 0.8),
    "hermeneus_dispatch":   (0.6, 0.5),
    "hermeneus_compile":    (0.5, 0.4),
    "hermeneus_list_workflows": (0.1, 0.1),
    "hermeneus_audit":      (0.4, 0.3),
    "hermeneus_export_session": (0.2, 0.1),

    # --- ochema (LLM ブリッジ) ---
    "ask_with_tools":       (0.9, 0.8),  # エージェントループ = 高リスク高価値
    "ask_cortex":           (0.6, 0.4),
    "ask":                  (0.7, 0.5),
    "ask_chat":             (0.5, 0.3),
    "start_chat":           (0.1, 0.1),
    "send_chat":            (0.4, 0.3),
    "ochema_plan_task":     (0.8, 0.7),
    "context_rot_distill":  (0.3, 0.2),
    "cache_boot_context":   (0.2, 0.1),

    # --- periskope (Deep Research) ---
    "periskope_research":   (0.7, 0.6),  # Deep Research = 高価値
    "periskope_search":     (0.5, 0.4),
    "periskope_benchmark":  (0.6, 0.5),
    "periskope_sources":    (0.2, 0.1),

    # --- phantazein (知識検索, 旧 mneme) ---
    "search":               (0.4, 0.3),
    "search_papers":        (0.5, 0.4),
    "backlinks":            (0.3, 0.2),
    "dendron_check":        (0.4, 0.3),
    "dendron_mece_check":   (0.4, 0.3),

    # --- sympatheia (自律神経系) ---
    "sympatheia_wbc":           (0.5, 0.4),
    "sympatheia_attractor":     (0.5, 0.4),
    "sympatheia_verify_on_edit": (0.6, 0.5),
    "sympatheia_basanos_scan":  (0.5, 0.4),
    "sympatheia_log_violation": (0.3, 0.2),

    # --- sekisho (監査 — Hub Gate で直接使用) ---
    "sekisho_audit":        (0.0, 0.0),  # Hub Gate として直接実行するため Shadow 不要
    "sekisho_gate":         (0.0, 0.0),

    # --- jules (並列コード生成) ---
    "jules_create_task":    (0.7, 0.6),
    "jules_batch_execute":  (0.8, 0.7),
    "jules_get_status":     (0.2, 0.1),
    "jules_list_repos":     (0.1, 0.1),

    # --- digestor (論文消化) ---
    "paper_search":         (0.4, 0.3),
    "paper_details":        (0.3, 0.2),
    "paper_citations":      (0.3, 0.2),
    "run_digestor":         (0.6, 0.5),
    "list_candidates":      (0.4, 0.3),

    # --- typos (Skill) ---
    "compile":              (0.4, 0.3),
    "generate":             (0.5, 0.4),
    "validate":             (0.3, 0.2),
    "parse":                (0.2, 0.1),
    "policy_check":         (0.3, 0.2),

    # --- phantazein-boot (Boot Context, 将来 phantazein に統合) ---
    "phantazein_boot":      (0.3, 0.2),
    "phantazein_health":    (0.2, 0.1),
    "phantazein_report":    (0.4, 0.3),
    "phantazein_consistency": (0.5, 0.4),
    "phantazein_snapshot":  (0.2, 0.1),

    # --- opsis (Web 視覚基盤) ---
    "opsis_observe":        (0.5, 0.4),  # DOM snapshot 取得
    "opsis_act":            (0.7, 0.6),  # DOM 操作 = 副作用あり
    "opsis_extract":        (0.4, 0.3),  # データ抽出

    # --- 共通 (全サーバーの ping/status 系) ---
    "ping":                 (0.0, 0.0),
    "status":               (0.0, 0.0),
    "models":               (0.0, 0.0),
    "session_info":         (0.0, 0.0),
    "cortex_quota":         (0.0, 0.0),
    "shadow_status":        (0.0, 0.0),
    "context_rot_status":   (0.1, 0.1),
    "close_chat":           (0.0, 0.0),
    "graph_stats":          (0.1, 0.1),
    "sources":              (0.1, 0.1),
    "stats":                (0.1, 0.1),

    # --- gemini-cli (subprocess バックエンド) ---
    "gemini_ask":           (0.6, 0.4),  # 単発プロンプト実行
    "gemini_research":      (0.7, 0.6),  # MCP 付き調査 (mneme/phantazein)

    # --- notebooklm (外部 RAG CLI — トークン消費ゼロ) ---
    "nlm_ask":              (0.5, 0.4),  # RAG クエリ (引用付き回答)
    "nlm_search":           (0.4, 0.3),  # ソース内検索
    "nlm_mind_map":         (0.4, 0.3),  # マインドマップ生成
    "nlm_source_add":       (0.3, 0.2),  # ソース追加
    "nlm_list":             (0.1, 0.1),  # ノートブック一覧

    # --- codex-mcp (stdio MCP バックエンド) ---
    # SOURCE: codex mcp-server (v0.118.0) list_tools() で確認済み (2026-04-07)
    # 2ツール構成: codex (セッション開始) + codex-reply (会話継続)
    "codex":                (0.7, 0.6),  # Codex セッション開始 (コード生成/レビュー等)
    "codex-reply":          (0.5, 0.4),  # Codex 会話継続 (thread_id + prompt)

    # --- cli_agent (subprocess バックエンド共通) ---
    "cli_agent_ask":        (0.6, 0.4),  # copilot / codex / cursor-agent 共通

    # --- xmcp (X API MCP — SNS運用+トレンド+検索) ---
    "createPosts":          (0.7, 0.5),  # ツイート投稿 = 外部公開 → 要注意
    "deletePosts":          (0.6, 0.4),  # ツイート削除 = 不可逆
    "searchPostsAll":       (0.5, 0.4),  # 全文検索
    "searchPostsRecent":    (0.4, 0.3),  # 最近の検索
    "searchUsers":          (0.3, 0.2),  # ユーザー検索
    "searchNews":           (0.4, 0.3),  # ニュース検索
    "getTrendsByWoeid":     (0.4, 0.3),  # トレンド取得
    "getTrendsPersonalizedTrends": (0.4, 0.3),  # パーソナライズドトレンド
    "getNews":              (0.4, 0.3),  # ニュース取得
    "getUsersMe":           (0.1, 0.1),  # 自己情報
    "getUsersByUsername":    (0.2, 0.1),  # ユーザー検索
    "getUsersPosts":        (0.3, 0.2),  # ユーザー投稿取得
    "getUsersTimeline":     (0.3, 0.2),  # タイムライン
    "getUsersMentions":     (0.3, 0.2),  # メンション
    "repostPost":           (0.5, 0.3),  # リポスト = 外部公開
    "likePost":             (0.2, 0.1),  # いいね
}


def get_tool_scores(tool_name: str) -> tuple[float, float]:
    """ツール名から (importance, complexity) スコアを返す。

    検索優先順位:
    1. ツール名そのまま (例: hermeneus_run)
    2. mcp_{server}_ プレフィックス除去 → {backend}.{stripped} で検索
    3. mcp_{server}_ プレフィックス除去 → {stripped} で検索
    4. {server}_ プレフィックス除去 → {stripped} で検索
    5. DEFAULT_TOOL_SCORES

    矛盾4修正: バックエンド固有の修飾キー (例: typos.compile) を
    先に検索し、異なるバックエンド間での同名ツールの誤マッチを防止。
    """
    # 1. そのまま検索
    if tool_name in TOOL_SCORES:
        return TOOL_SCORES[tool_name]

    # 2-3. mcp_{server}_ プレフィックスを除去して検索
    for prefix in BACKENDS:
        p = f"mcp_{prefix}_"
        if tool_name.startswith(p):
            stripped = tool_name[len(p):]
            # 2. バックエンド修飾キーで検索 (例: typos.compile)
            qualified = f"{prefix}.{stripped}"
            if qualified in TOOL_SCORES:
                return TOOL_SCORES[qualified]
            # 3. 単純キーで検索
            if stripped in TOOL_SCORES:
                return TOOL_SCORES[stripped]

    # 4. {server}_ プレフィックスを除去して検索
    for prefix in BACKENDS:
        p = f"{prefix}_"
        if tool_name.startswith(p):
            stripped = tool_name[len(p):]
            if stripped in TOOL_SCORES:
                return TOOL_SCORES[stripped]

    return DEFAULT_TOOL_SCORES

