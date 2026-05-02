#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/opsis_mcp_server.py A0→Web DOM の構造化取得が必要→opsis が担う
"""
Opsis MCP Server — HGK Web 視覚基盤 (ὄψις = 視覚)

Web DOM を HGK 認知動詞体系で構造化して返す MCP サーバー。

6ツール:
  opsis_observe    — URL の a11y snapshot を取得し、認知動詞アノテーション付きで返す
  opsis_act        — Ref ID 指定で DOM 要素を操作する
  opsis_extract    — URL からスキーマ準拠の構造化データを抽出する
  opsis_wait       — 指定条件の成立を待機する
  opsis_screenshot — ページのスクリーンショットを取得する
  opsis_navigate   — ブラウザの back/forward/refresh 操作

設計判断:
  - バックエンド: agent-browser CLI (ローカル) / Playwright (headless/Colab)
  - auto-detect: agent-browser があればそちら、なければ Playwright にフォールバック
  - Layer 3: DOM 要素の role から HGK 認知動詞の可能操作をアノテーション
  - Notte の SSPL コードには一切依存しない (随伴であり、インポートではない)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# ============ Import path + MCPBase ============
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mekhane.mcp.mcp_base import MCPBase, run_sync
from mekhane.mcp.opsis_backends import (
    BrowserResult,
    SnapshotData,
    auto_detect_backend,
)

# ============ 初期化 ============
base = MCPBase(
    name="opsis",
    version="0.4.0",
    instructions=(
        "Opsis — HGK Web 視覚基盤。Web DOM を構造化取得し、"
        "HGK 認知動詞体系でアノテーションして返す。"
        "v0.4: Dual Backend (agent-browser / Playwright), "
        "セッション永続化, networkidle 待機, トークン予算制御, セマンティック圧縮, 差分モード, "
        "60+ ARIA roles, 動詞別出力整形 (Layer 3.5), "
        "新ツール (wait/screenshot/navigate)。"
    ),
)
server = base.server
log = base.log
TextContent = base.TextContent
Tool = base.Tool


# =============================================================================
# Layer 3: HGK 認知動詞 Perception Layer
# =============================================================================

# 認知動詞ごとの snapshot パラメータ自動調整マップ
VERB_DEPTH_MAP: dict[str, dict[str, Any]] = {
    "/ski": {"depth": 1, "interactive": True, "compact": True},    # 走査: 浅く広く
    "/the": {"depth": 5, "interactive": False, "compact": False},  # 観照: 深く全体
    "/ere": {"depth": 2, "interactive": True, "compact": True},    # 探知: 中間
    "/sap": {"interactive": False, "compact": False},              # 精読: 特定要素 (selector で絞る)
    "/lys": {"depth": 3, "interactive": False, "compact": True},   # 分析: 構造重視
    "/per": {"depth": 2, "interactive": False, "compact": True},   # 一覧: 広域構造
}

# DOM role → 可能な認知動詞操作のマッピング (30+ ARIA roles)
ROLE_VERB_MAP: dict[str, list[str]] = {
    # --- 操作系 (Widgets) ---
    "link":        ["/tek(click)", "/sap(name読取)"],
    "button":      ["/tek(click)", "/sap(label読取)"],
    "textbox":     ["/tek(fill)", "/sap(value読取)"],
    "checkbox":    ["/tek(check/uncheck)", "/sap(状態読取)"],
    "combobox":    ["/tek(select)", "/sap(選択肢読取)"],
    "radio":       ["/tek(select)", "/sap(状態読取)"],
    "switch":      ["/tek(toggle)", "/sap(状態読取)"],
    "slider":      ["/tek(set value)", "/sap(値読取)"],
    "spinbutton":  ["/tek(increment/decrement)", "/sap(値読取)"],
    "searchbox":   ["/tek(fill)", "/sap(value読取)"],
    "option":      ["/tek(select)", "/sap(label読取)"],
    "menuitem":    ["/tek(click)", "/sap(label読取)"],
    "menuitemcheckbox": ["/tek(check)", "/sap(状態読取)"],
    "menuitemradio":    ["/tek(select)", "/sap(状態読取)"],
    # --- コンテンツ構造系 ---
    "heading":     ["/sap(テキスト精読)", "/the(セクション観照)"],
    "paragraph":   ["/sap(テキスト精読)"],
    "blockquote":  ["/sap(引用精読)", "/the(観照)"],
    "code":        ["/sap(コード精読)", "/lys(構造分解)"],
    "article":     ["/the(全文観照)", "/lys(構造分解)", "/sap(精読)"],
    "section":     ["/the(セクション観照)", "/lys(内部分解)"],
    "figure":      ["/the(図版観照)", "/sap(caption読取)"],
    "img":         ["/the(画像観照)", "/sap(alt読取)"],
    "image":       ["/the(画像観照)", "/sap(alt読取)"],
    # --- テーブル系 ---
    "table":       ["/lys(行列分解)", "/sap(セル精読)"],
    "row":         ["/sap(行読取)", "/lys(セル分解)"],
    "cell":        ["/sap(値読取)", "/lys(行分析)"],
    "columnheader": ["/sap(列名読取)"],
    "rowheader":   ["/sap(行名読取)"],
    # --- リスト系 ---
    "list":        ["/per(項目一覧)", "/lys(リスト分析)"],
    "listitem":    ["/sap(内容読取)", "/lys(リスト分析)"],
    "listbox":     ["/per(選択肢一覧)", "/tek(select)"],
    # --- ナビゲーション系 ---
    "navigation":  ["/per(リンク一覧)", "/ere(構造探知)"],
    "menu":        ["/per(メニュー一覧)", "/ere(構造探知)"],
    "menubar":     ["/per(メニューバー一覧)", "/ere(構造探知)"],
    "tab":         ["/tek(click)", "/sap(label読取)"],
    "tablist":     ["/per(タブ一覧)", "/ere(構造探知)"],
    "tabpanel":    ["/the(パネル観照)", "/lys(内容分解)"],
    "tree":        ["/per(ツリー一覧)", "/lys(階層分析)"],
    "treeitem":    ["/tek(expand/collapse)", "/sap(内容読取)"],
    "breadcrumb":  ["/per(パス一覧)", "/sap(現在位置読取)"],
    # --- フォーム・入力系 ---
    "form":        ["/lys(フィールド分解)", "/tek(fill+submit)"],
    "group":       ["/lys(グループ分解)", "/the(観照)"],
    "toolbar":     ["/per(ツール一覧)", "/ere(構造探知)"],
    # --- フィードバック系 ---
    "alert":       ["/sap(メッセージ精読)", "/ant(変化検知)"],
    "alertdialog": ["/sap(メッセージ精読)", "/tek(confirm/dismiss)"],
    "dialog":      ["/the(ダイアログ観照)", "/lys(内容分解)", "/tek(操作)"],
    "status":      ["/sap(状態読取)", "/ant(変化検知)"],
    "progressbar": ["/sap(進捗読取)", "/ant(変化検知)"],
    "log":         ["/per(ログ一覧)", "/sap(最新読取)"],
    "marquee":     ["/sap(テキスト読取)"],
    "timer":       ["/sap(値読取)", "/ant(変化検知)"],
    "tooltip":     ["/sap(テキスト精読)"],
    # --- ランドマーク系 ---
    "banner":      ["/the(ヘッダー観照)", "/per(要素一覧)"],
    "complementary": ["/the(サイドバー観照)", "/ere(構造探知)"],
    "contentinfo": ["/the(フッター観照)", "/per(要素一覧)"],
    "main":        ["/the(メインコンテンツ観照)", "/lys(構造分解)"],
    "region":      ["/the(リージョン観照)", "/lys(内容分解)"],
    "search":      ["/tek(fill)", "/sap(value読取)"],
    # --- セマンティック分類 (Layer 3.5) ---
    "separator":   ["/ant(境界検知)"],
    "presentation": [],  # 装飾要素 — 認知動詞不要
    "none":        [],   # 同上
}

# デフォルト (未知の role)
DEFAULT_VERBS = ["/the(観照)", "/sap(精読)"]

# 動詞別出力整形: verb が output shape を決定する
VERB_OUTPUT_SHAPE: dict[str, dict[str, Any]] = {
    "/ski": {
        "format": "scan",         # 1行サマリー形式
        "ref_detail": "minimal",  # ref_id + role + name のみ
        "group_by_role": True,    # role でグループ化
    },
    "/the": {
        "format": "full",         # 全展開
        "ref_detail": "full",     # 全フィールド + hgk_verbs
        "group_by_role": False,
    },
    "/ere": {
        "format": "explore",      # interactive 要素 + ランドマーク構造
        "ref_detail": "standard", # ref_id + role + name + hgk_verbs
        "group_by_role": False,
    },
    "/sap": {
        "format": "precise",      # 対象要素のみ、全属性展開
        "ref_detail": "full",
        "group_by_role": False,
    },
    "/lys": {
        "format": "structure",    # MECE 構造ツリー
        "ref_detail": "standard",
        "group_by_role": True,    # role でグループ化して構造可視化
    },
    "/per": {
        "format": "catalog",      # カタログ形式: role ごとのカウント + 代表例
        "ref_detail": "minimal",
        "group_by_role": True,
    },
}


# =============================================================================
# Layer 3 ヘルパー (バックエンド非依存)
# =============================================================================

# 直前の snapshot を保持 (差分モード用, LRU 上限付き)
_last_snapshot: dict[str, Any] = {}  # url -> {"snapshot": str, "refs": dict}
_SNAPSHOT_CACHE_MAX = 20  # 最大保持 URL 数 — 超過時は最古を破棄


def _annotate_refs(refs: dict[str, dict]) -> dict[str, dict]:
    """refs に HGK 認知動詞アノテーションを追加する (Layer 3)。"""
    annotated = {}
    for ref_id, ref_data in refs.items():
        role = ref_data.get("role", "")
        verbs = ROLE_VERB_MAP.get(role, DEFAULT_VERBS)
        annotated[ref_id] = {
            **ref_data,
            "hgk_verbs": verbs,
        }
    return annotated


def _shape_output(refs: dict[str, dict], verb: str | None) -> dict[str, Any]:
    """動詞別出力整形: verb が output の形を決定する (Layer 3.5)。"""
    if not verb or verb not in VERB_OUTPUT_SHAPE:
        return {"shaped": False, "refs": refs}

    # _summary_ エントリをフィルタ
    refs = {k: v for k, v in refs.items() if not k.startswith("_summary_")}

    shape = VERB_OUTPUT_SHAPE[verb]
    fmt = shape["format"]
    detail = shape["ref_detail"]

    def _slim_ref(ref_id: str, ref_data: dict) -> dict:
        if detail == "minimal":
            return {"ref": ref_id, "role": ref_data.get("role", ""), "name": ref_data.get("name", "")}
        elif detail == "standard":
            return {"ref": ref_id, "role": ref_data.get("role", ""), "name": ref_data.get("name", ""), "hgk_verbs": ref_data.get("hgk_verbs", [])}
        else:  # full
            return {"ref": ref_id, **ref_data}

    if fmt == "scan":
        groups: dict[str, list[dict]] = {}
        for ref_id, ref_data in refs.items():
            role = ref_data.get("role", "unknown")
            groups.setdefault(role, []).append(_slim_ref(ref_id, ref_data))
        scan_result = []
        for role, items in sorted(groups.items(), key=lambda x: -len(x[1])):
            preview = [it["name"] for it in items[:3] if it.get("name")]
            scan_result.append({
                "role": role, "count": len(items), "preview": preview,
                "hgk_verbs": ROLE_VERB_MAP.get(role, DEFAULT_VERBS),
            })
        return {"shaped": True, "format": "scan", "groups": scan_result, "total_refs": len(refs)}

    elif fmt == "catalog":
        groups = {}
        for ref_id, ref_data in refs.items():
            role = ref_data.get("role", "unknown")
            groups.setdefault(role, []).append(_slim_ref(ref_id, ref_data))
        catalog = []
        for role, items in sorted(groups.items()):
            catalog.append({
                "role": role, "count": len(items), "items": items[:5],
                "hgk_verbs": ROLE_VERB_MAP.get(role, DEFAULT_VERBS),
            })
        return {"shaped": True, "format": "catalog", "roles": catalog, "total_refs": len(refs), "role_count": len(catalog)}

    elif fmt == "structure":
        groups = {}
        for ref_id, ref_data in refs.items():
            role = ref_data.get("role", "unknown")
            groups.setdefault(role, []).append(_slim_ref(ref_id, ref_data))
        structure = []
        for role, items in sorted(groups.items()):
            structure.append({"role": role, "count": len(items), "elements": items})
        return {"shaped": True, "format": "structure", "tree": structure, "total_refs": len(refs)}

    elif fmt == "explore":
        interactive = []
        landmarks = []
        landmark_roles = {"navigation", "main", "banner", "contentinfo", "complementary", "search", "region", "form"}
        for ref_id, ref_data in refs.items():
            role = ref_data.get("role", "")
            slim = _slim_ref(ref_id, ref_data)
            if role in landmark_roles:
                landmarks.append(slim)
            elif ref_data.get("hgk_verbs") and any("/tek" in v for v in ref_data.get("hgk_verbs", [])):
                interactive.append(slim)
        return {"shaped": True, "format": "explore", "landmarks": landmarks, "interactive": interactive,
                "landmark_count": len(landmarks), "interactive_count": len(interactive), "total_refs": len(refs)}

    elif fmt == "precise":
        precise = [{"ref": ref_id, **ref_data} for ref_id, ref_data in refs.items()]
        return {"shaped": True, "format": "precise", "elements": precise, "total_refs": len(refs)}

    else:
        return {"shaped": True, "format": "full", "refs": refs, "total_refs": len(refs)}


def _compress_refs(refs: dict[str, dict], max_tokens: int | None = None) -> tuple[dict[str, dict], dict[str, int] | None]:
    """セマンティック圧縮: 同種要素をグループ化し、トークン予算内に収める。"""
    if not max_tokens and len(refs) <= 50:
        return refs, None

    role_groups: dict[str, list[tuple[str, dict]]] = {}
    for ref_id, ref_data in refs.items():
        role = ref_data.get("role", "unknown")
        role_groups.setdefault(role, []).append((ref_id, ref_data))

    role_summary = {role: len(items) for role, items in role_groups.items()}

    if not max_tokens:
        return refs, role_summary

    estimated_tokens = sum(len(json.dumps(v, ensure_ascii=False)) // 4 for v in refs.values())
    if estimated_tokens <= max_tokens:
        return refs, role_summary

    compressed: dict[str, dict] = {}
    budget_per_role = max(3, max_tokens // max(len(role_groups), 1) // 15)

    for role, items in role_groups.items():
        kept = items[:budget_per_role]
        for ref_id, ref_data in kept:
            compressed[ref_id] = ref_data
        if len(items) > budget_per_role:
            compressed[f"_summary_{role}"] = {
                "role": role, "type": "summary", "count": len(items),
                "shown": budget_per_role, "omitted": len(items) - budget_per_role,
                "hgk_verbs": ROLE_VERB_MAP.get(role, DEFAULT_VERBS),
            }

    return compressed, role_summary


def _compute_diff(url: str, new_refs: dict[str, dict], new_snapshot: str) -> dict[str, Any] | None:
    """前回の snapshot との差分を計算する。"""
    prev = _last_snapshot.get(url)
    if not prev:
        return None

    prev_refs = set(prev.get("refs", {}).keys())
    new_ref_keys = set(new_refs.keys())

    added = new_ref_keys - prev_refs
    removed = prev_refs - new_ref_keys

    changed = []
    for ref_id in prev_refs & new_ref_keys:
        old_data = prev["refs"].get(ref_id, {})
        new_data = new_refs.get(ref_id, {})
        if old_data.get("name") != new_data.get("name") or old_data.get("role") != new_data.get("role"):
            changed.append(ref_id)

    return {
        "added": {k: new_refs[k] for k in added},
        "removed": list(removed),
        "changed": {k: new_refs[k] for k in changed},
        "added_count": len(added),
        "removed_count": len(removed),
        "changed_count": len(changed),
        "unchanged_count": len(new_ref_keys) - len(added) - len(changed),
    }


def _truncate_snapshot(snapshot: str, max_chars: int) -> tuple[str, bool]:
    """snapshot テキストを max_chars 以内に切り詰める。"""
    if len(snapshot) <= max_chars:
        return snapshot, False

    lines = snapshot.split("\n")
    result_lines = []
    current_len = 0

    for line in lines:
        if current_len + len(line) + 1 > max_chars:
            break
        result_lines.append(line)
        current_len += len(line) + 1

    truncated = "\n".join(result_lines)
    truncated += f"\n... [truncated: {len(snapshot) - len(truncated)} chars omitted, {len(snapshot)} total]"
    return truncated, True


# =============================================================================
# バックエンド初期化 (遅延)
# =============================================================================

_backend = None


def _init_backend(prefer: str | None = None, headless: bool = True):
    """バックエンドを明示的に初期化する。"""
    global _backend
    _backend = auto_detect_backend(prefer=prefer, headless=headless)
    log(f"Opsis v0.4.0 — backend: {_backend.name}")


def _get_backend():
    """バックエンドを取得 (未初期化なら auto-detect)。"""
    if _backend is None:
        _init_backend()
    return _backend


# =============================================================================
# MCP ツール定義
# =============================================================================

@server.list_tools()
async def list_tools():
    """Opsis ツール一覧を返す。"""
    return [
        Tool(
            name="opsis_observe",
            description=(
                "Web ページの DOM を Ref ID 付きアクセシビリティツリーとして取得。"
                "HGK 認知動詞アノテーション付き。verb パラメータで自動最適化。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "取得する URL"},
                    "verb": {
                        "type": "string",
                        "description": "HGK 認知動詞 (/the, /ere, /ski, /sap, /lys, /per)。snapshot パラメータを自動調整",
                        "enum": ["/ski", "/the", "/ere", "/sap", "/lys", "/per"],
                    },
                    "depth": {"type": "integer", "description": "ツリーの深さ制限 (1-10)。verb 指定時は自動設定"},
                    "selector": {"type": "string", "description": "CSS セレクタでスコープを絞る (/sap 向き)"},
                    "interactive_only": {"type": "boolean", "description": "操作可能要素のみ取得", "default": True},
                    "max_tokens": {"type": "integer", "description": "出力トークン予算。超過時は自動圧縮"},
                    "diff": {"type": "boolean", "description": "前回 snapshot との差分のみ返す", "default": False},
                    "wait": {"type": "boolean", "description": "ページロード完了を待機してから snapshot", "default": True},
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="opsis_act",
            description=(
                "Ref ID を指定して DOM 要素を操作する。click, fill, select 等。"
                "事前に opsis_observe で Ref ID を確認すること。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["click", "fill", "select", "check", "uncheck", "hover", "type", "press"]},
                    "ref": {"type": "string", "description": "操作対象の Ref ID (例: @e3)"},
                    "value": {"type": "string", "description": "fill/select/type 時の入力値"},
                    "observe_after": {"type": "boolean", "description": "操作後に自動で diff snapshot を取得", "default": False},
                },
                "required": ["action", "ref"],
            },
        ),
        Tool(
            name="opsis_extract",
            description="Web ページから構造化データを抽出する。CSS セレクタまたは Ref ID で対象を指定。",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "抽出元 URL"},
                    "ref": {"type": "string", "description": "抽出対象の Ref ID"},
                    "selector": {"type": "string", "description": "CSS セレクタ"},
                    "what": {"type": "string", "enum": ["text", "html", "value", "title", "url", "count"], "default": "text"},
                    "eval_js": {"type": "string", "description": "JavaScript を評価して結果を返す"},
                },
            },
        ),
        # ── T-026 新ツール ──
        Tool(
            name="opsis_wait",
            description="指定された条件が満たされるまで待機する。ページロード完了、要素の出現、テキストの出現など。",
            inputSchema={
                "type": "object",
                "properties": {
                    "condition": {
                        "type": "string",
                        "enum": ["load", "selector", "text"],
                        "description": "load=ページロード完了, selector=CSS要素出現, text=テキスト出現",
                    },
                    "value": {"type": "string", "description": "selector or text (condition が selector/text の場合必須)"},
                    "timeout": {"type": "integer", "description": "タイムアウト秒数", "default": 30},
                },
                "required": ["condition"],
            },
        ),
        Tool(
            name="opsis_screenshot",
            description="現在のページのスクリーンショットを取得する (PNG, base64)。",
            inputSchema={
                "type": "object",
                "properties": {
                    "full_page": {"type": "boolean", "description": "ページ全体をキャプチャ", "default": False},
                },
            },
        ),
        Tool(
            name="opsis_navigate",
            description="ブラウザのナビゲーション操作 (back/forward/refresh)。",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["back", "forward", "refresh"]},
                },
                "required": ["action"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """ツール呼び出しをルーティングする。"""
    log(f"Tool call: {name} args={list(arguments.keys())}")

    try:
        if name == "opsis_observe":
            result = await run_sync(_handle_observe, arguments)
        elif name == "opsis_act":
            result = await run_sync(_handle_act, arguments)
        elif name == "opsis_extract":
            result = await run_sync(_handle_extract, arguments)
        elif name == "opsis_wait":
            result = await run_sync(_handle_wait, arguments)
        elif name == "opsis_screenshot":
            result = await run_sync(_handle_screenshot, arguments)
        elif name == "opsis_navigate":
            result = await run_sync(_handle_navigate, arguments)
        else:
            result = json.dumps({"error": f"Unknown tool: {name}"})

        return [TextContent(type="text", text=result)]
    except Exception as e:  # noqa: BLE001
        log(f"Tool error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False))]


# =============================================================================
# ツール実装
# =============================================================================

def _handle_observe(arguments: dict) -> str:
    """opsis_observe の実装。"""
    backend = _get_backend()
    url = arguments["url"]
    verb = arguments.get("verb")
    depth = arguments.get("depth")
    selector = arguments.get("selector")
    interactive = arguments.get("interactive_only", True)
    max_tokens = arguments.get("max_tokens")
    diff_mode = arguments.get("diff", False)
    wait_load = arguments.get("wait", True)

    # Step 1: Navigate
    nav_result = backend.navigate(url)
    if not nav_result.success:
        return json.dumps({"error": f"Failed to open {url}: {nav_result.error}"}, ensure_ascii=False)

    # Step 1.5: Wait for load
    if wait_load:
        wait_result = backend.wait_for_load(timeout=30)
        if not wait_result.success:
            log(f"wait networkidle failed (non-fatal): {wait_result.error}")

    # Step 2: Snapshot (verb による自動調整)
    effective_depth = depth
    compact = True
    if verb and verb in VERB_DEPTH_MAP:
        preset = VERB_DEPTH_MAP[verb]
        if effective_depth is None:
            effective_depth = preset.get("depth")
        interactive = preset.get("interactive", interactive)
        compact = preset.get("compact", True)
        if selector is None:
            selector = preset.get("selector")

    attempts = []
    snapshot_text = ""
    refs: dict[str, dict] = {}

    for attempt in range(3):
        snap_result = backend.snapshot(
            depth=effective_depth, interactive=interactive,
            compact=compact, selector=selector,
        )
        if not snap_result.success:
            return json.dumps({"error": f"Snapshot failed: {snap_result.error}"}, ensure_ascii=False)

        snap_data: SnapshotData = snap_result.data
        snapshot_text = snap_data.snapshot
        refs = snap_data.refs

        # トークン予算チェック
        if max_tokens:
            estimated = len(snapshot_text) // 4 + len(refs) * 15
            attempts.append({"depth": effective_depth, "interactive": interactive, "tokens": estimated})
            if estimated <= max_tokens:
                break
            if effective_depth is None or effective_depth > 2:
                effective_depth = max(1, (effective_depth or 5) - 2)
                log(f"Budget retry {attempt+1}: depth={effective_depth}, est={estimated} > budget={max_tokens}")
            elif not interactive:
                interactive = True
                log(f"Budget retry {attempt+1}: switching to interactive-only")
            else:
                break
        else:
            break

    # Step 3: Layer 3 — HGK 認知動詞アノテーション
    annotated_refs = _annotate_refs(refs)

    # Step 4: セマンティック圧縮
    compressed_refs, role_summary = _compress_refs(annotated_refs, max_tokens)

    # Step 5: 差分モード
    diff_result = None
    if diff_mode:
        diff_result = _compute_diff(url, refs, snapshot_text)

    # Step 6: snapshot 保存 (次回の diff 用, LRU)
    _last_snapshot[url] = {"snapshot": snapshot_text, "refs": refs}
    if len(_last_snapshot) > _SNAPSHOT_CACHE_MAX:
        oldest_key = next(iter(_last_snapshot))
        del _last_snapshot[oldest_key]

    # Step 7: snapshot テキストの truncation
    output_snapshot = snapshot_text
    was_truncated = False
    if max_tokens:
        refs_tokens = sum(len(json.dumps(v, ensure_ascii=False)) // 4 for v in compressed_refs.values())
        snapshot_budget_chars = max(200, (max_tokens - refs_tokens) * 4)
        output_snapshot, was_truncated = _truncate_snapshot(snapshot_text, snapshot_budget_chars)

    # Step 8: レスポンス構築
    estimated_tokens = len(output_snapshot) // 4 + sum(
        len(json.dumps(v, ensure_ascii=False)) // 4 for v in compressed_refs.values()
    )

    response: dict[str, Any] = {
        "url": url,
        "verb": verb or "default",
        "backend": backend.name,
        "ref_count": len(refs),
        "estimated_tokens": estimated_tokens,
    }

    if diff_mode and diff_result:
        response["mode"] = "diff"
        response["diff"] = diff_result
    else:
        response["mode"] = "full"
        response["snapshot"] = output_snapshot
        response["snapshot_chars"] = len(output_snapshot)
        if was_truncated:
            response["snapshot_truncated"] = True
            response["snapshot_original_chars"] = len(snapshot_text)

        shaped = _shape_output(compressed_refs, verb)
        if shaped.get("shaped"):
            response["shaped"] = shaped
        else:
            response["refs"] = compressed_refs

    if role_summary:
        response["role_summary"] = role_summary

    if max_tokens:
        if len(attempts) > 1:
            response["budget_retries"] = attempts
        if estimated_tokens > max_tokens:
            response["budget_warning"] = f"Estimated {estimated_tokens} tokens exceeds budget {max_tokens} after {len(attempts)} attempt(s)."

    return json.dumps(response, ensure_ascii=False, indent=2)


def _handle_act(arguments: dict) -> str:
    """opsis_act の実装。"""
    backend = _get_backend()
    action = arguments["action"]
    ref = arguments["ref"]
    value = arguments.get("value")
    observe_after = arguments.get("observe_after", False)

    result = backend.act(action, ref, value)

    if not result.success:
        return json.dumps({"error": f"Action failed: {result.error}"}, ensure_ascii=False)

    current_url = backend.get_url()

    response: dict[str, Any] = {
        "action": action, "ref": ref, "value": value,
        "success": True, "current_url": current_url,
    }

    if observe_after:
        backend.wait_for_load(timeout=15)

        snap_result = backend.snapshot(interactive=True, compact=True)
        if snap_result.success:
            snap_data: SnapshotData = snap_result.data
            new_refs = snap_data.refs
            new_snapshot = snap_data.snapshot

            diff = _compute_diff(current_url, new_refs, new_snapshot)
            annotated = _annotate_refs(new_refs)

            response["observe_after"] = {
                "ref_count": len(new_refs),
                "estimated_tokens": len(new_snapshot) // 4,
            }

            if diff:
                response["observe_after"]["diff"] = diff
            else:
                response["observe_after"]["snapshot"] = new_snapshot
                response["observe_after"]["refs"] = annotated

            _last_snapshot[current_url] = {"snapshot": new_snapshot, "refs": new_refs}
            if len(_last_snapshot) > _SNAPSHOT_CACHE_MAX:
                oldest_key = next(iter(_last_snapshot))
                del _last_snapshot[oldest_key]

    return json.dumps(response, ensure_ascii=False, indent=2)


def _handle_extract(arguments: dict) -> str:
    """opsis_extract の実装。"""
    backend = _get_backend()
    url = arguments.get("url")
    ref = arguments.get("ref")
    selector = arguments.get("selector")
    what = arguments.get("what", "text")
    eval_js = arguments.get("eval_js")

    if url:
        open_result = backend.navigate(url)
        if not open_result.success:
            return json.dumps({"error": f"Failed to open {url}: {open_result.error}"}, ensure_ascii=False)

    if eval_js:
        result = backend.eval_js(eval_js)
        if not result.success:
            return json.dumps({"error": f"eval failed: {result.error}"}, ensure_ascii=False)
        return json.dumps({"type": "eval", "result": result.data}, ensure_ascii=False, indent=2)

    target = None
    if ref:
        target = ref if ref.startswith("@") else f"@{ref}"
    elif selector:
        target = selector

    result = backend.extract(what, target)

    if not result.success:
        return json.dumps({"error": f"Extract failed: {result.error}"}, ensure_ascii=False)

    return json.dumps({"what": what, "target": target or "page", "data": result.data}, ensure_ascii=False, indent=2)


# ── T-026 新ツール実装 ──

def _handle_wait(arguments: dict) -> str:
    """opsis_wait の実装。"""
    backend = _get_backend()
    condition = arguments["condition"]
    value = arguments.get("value")
    timeout = arguments.get("timeout", 30)

    import time

    if condition == "load":
        result = backend.wait_for_load(timeout=timeout)
    elif condition == "selector":
        if not value:
            return json.dumps({"error": "selector condition requires 'value'"}, ensure_ascii=False)
        # selector 待機: ポーリングで要素出現を待つ
        deadline = time.monotonic() + timeout
        result = BrowserResult(success=False, error=f"Selector '{value}' not found within {timeout}s")
        while time.monotonic() < deadline:
            check = backend.extract("count", value)
            if check.success and check.data and int(check.data) > 0:
                result = BrowserResult(success=True, data={"found": int(check.data)})
                break
            time.sleep(0.5)
    elif condition == "text":
        if not value:
            return json.dumps({"error": "text condition requires 'value'"}, ensure_ascii=False)
        # テキスト待機: ポーリングで出現を待つ
        js = f"document.body.innerText.includes({json.dumps(value)})"
        deadline = time.monotonic() + timeout
        result = BrowserResult(success=False, error=f"Text '{value}' not found within {timeout}s")
        while time.monotonic() < deadline:
            check = backend.eval_js(js)
            if check.success and check.data:
                result = BrowserResult(success=True, data={"text_found": True})
                break
            time.sleep(0.5)
    else:
        return json.dumps({"error": f"Unknown condition: {condition}"}, ensure_ascii=False)

    if not result.success:
        return json.dumps({"error": result.error}, ensure_ascii=False)

    return json.dumps({"condition": condition, "value": value, "success": True, "data": result.data}, ensure_ascii=False, indent=2)


def _handle_screenshot(arguments: dict) -> str:
    """opsis_screenshot の実装。"""
    backend = _get_backend()
    full_page = arguments.get("full_page", False)

    result = backend.screenshot(full_page=full_page)
    if not result.success:
        return json.dumps({"error": f"Screenshot failed: {result.error}"}, ensure_ascii=False)

    return json.dumps(result.data, ensure_ascii=False, indent=2)


def _handle_navigate(arguments: dict) -> str:
    """opsis_navigate の実装。"""
    backend = _get_backend()
    action = arguments["action"]

    if action == "back":
        result = backend.go_back()
    elif action == "forward":
        result = backend.go_forward()
    elif action == "refresh":
        result = backend.refresh()
    else:
        return json.dumps({"error": f"Unknown action: {action}"}, ensure_ascii=False)

    if not result.success:
        return json.dumps({"error": f"Navigate failed: {result.error}"}, ensure_ascii=False)

    current_url = backend.get_url()
    return json.dumps({"action": action, "success": True, "current_url": current_url}, ensure_ascii=False, indent=2)


# =============================================================================
# エントリポイント
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Opsis MCP Server")
    parser.add_argument(
        "--backend", choices=["auto", "agent-browser", "playwright"],
        default="auto", help="Browser backend selection",
    )
    parser.add_argument(
        "--headless", action="store_true", default=True,
        help="Run Playwright in headless mode (default: True)",
    )
    parser.add_argument(
        "--no-headless", action="store_false", dest="headless",
        help="Run Playwright with visible browser window",
    )

    # MCPBase の引数と共存するため、unknown args は無視
    args, unknown = parser.parse_known_args()

    # バックエンドを明示的に初期化
    prefer = None if args.backend == "auto" else args.backend
    _init_backend(prefer=prefer, headless=args.headless)

    base.install_all_hooks()
    base.run()
