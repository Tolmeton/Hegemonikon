#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/gws_mcp_server.py A0→Google Workspace API へのMCPアクセスが必要→gws_mcp_server が担う
"""
GWS MCP Server — Google Workspace CLI ラッパー

gws CLI (v0.16.0+) を subprocess で呼び出し、MCP ツールとして公開する。
対応サービス: Drive, Gmail, Sheets, Calendar, Docs, Slides, Tasks

アカウント切替:
  - デフォルト: ~/.config/gws/ (Tolmetes@hegemonikon.org)
  - account="Tolmeton": ~/.config/gws-Tolmeton/ (Tolmetes@hegemonikon.org)
"""

import sys
import os
import json
import subprocess
import shutil

# ============ Import path + MCPBase ============
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mekhane.mcp.mcp_base import MCPBase, run_sync

# ============ 初期化 ============
base = MCPBase(
    name="gws",
    version="1.0.0",
    instructions="Google Workspace CLI ラッパー。Drive/Gmail/Sheets/Calendar/Docs/Slides/Tasks にアクセス。",
)
server = base.server
log = base.log

# ============ 設定 ============
# アカウント名 → config ディレクトリのマッピング
ACCOUNT_CONFIGS = {
    "default": Path.home() / ".config" / "gws",
    "makaron8426": Path.home() / ".config" / "gws",
    "Tolmeton": Path.home() / ".config" / "gws-Tolmeton",
}

# gws CLI パス
GWS_BIN = shutil.which("gws") or str(Path.home() / ".npm-global" / "bin" / "gws")


# ============ ヘルパー ============
# PURPOSE: gws CLI をサブプロセスで実行し、結果を返す
def _run_gws(args: list[str], account: str = "default", timeout: int = 30) -> dict:
    """gws CLI を実行して結果を JSON で返す。

    Args:
        args: gws のサブコマンド引数 (例: ["drive", "files", "list"])
        account: アカウント名 (default, makaron8426, Tolmeton)
        timeout: タイムアウト秒数

    Returns:
        {"success": bool, "data": dict|str, "error": str|None}
    """
    config_dir = ACCOUNT_CONFIGS.get(account, ACCOUNT_CONFIGS["default"])

    env = os.environ.copy()
    env["GOOGLE_WORKSPACE_CLI_CONFIG_DIR"] = str(config_dir)
    # PATH に npm-global を追加
    npm_bin = str(Path.home() / ".npm-global" / "bin")
    env["PATH"] = f"{npm_bin}:{env.get('PATH', '')}"

    cmd = [GWS_BIN] + args
    log(f"Executing: {' '.join(cmd)} (account={account})")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )

        output = result.stdout.strip()
        # gws は "Using keyring backend: keyring" を stderr に出す場合がある
        # stdout も keyring メッセージを含む場合があるのでフィルタ
        lines = output.split("\n")
        json_lines = []
        in_json = False
        for line in lines:
            if line.strip().startswith("{") or line.strip().startswith("["):
                in_json = True
            if in_json:
                json_lines.append(line)

        json_text = "\n".join(json_lines) if json_lines else output

        try:
            data = json.loads(json_text)
            # gws エラーレスポンスのチェック
            if isinstance(data, dict) and "error" in data:
                return {
                    "success": False,
                    "data": None,
                    "error": json.dumps(data["error"], ensure_ascii=False),
                }
            return {"success": True, "data": data, "error": None}
        except json.JSONDecodeError:
            # JSON でない場合はテキストとして返す
            if result.returncode != 0:
                return {
                    "success": False,
                    "data": None,
                    "error": output or result.stderr.strip(),
                }
            return {"success": True, "data": output, "error": None}

    except subprocess.TimeoutExpired:
        return {"success": False, "data": None, "error": f"タイムアウト ({timeout}秒)"}
    except FileNotFoundError:
        return {
            "success": False,
            "data": None,
            "error": f"gws CLI が見つかりません: {GWS_BIN}",
        }
    except Exception as e:  # noqa: BLE001
        return {"success": False, "data": None, "error": str(e)}


# ============ ツール定義 (11→3 ファサード統合) ============
@server.list_tools()
# PURPOSE: GWS MCP ツール一覧を返す (3 ファサード)
async def list_tools():
    """GWS で利用可能なツール一覧を返す。"""
    log("list_tools called")
    return [
        # ── gws_drive: Drive 操作ファサード (list/get/export) ──
        base.Tool(
            name="gws_drive",
            description=(
                "Google Drive 操作。action で操作を選択: "
                "list=ファイル一覧取得, get=ファイルメタデータ取得, "
                "export=Docs/Sheets/Slides をテキストエクスポート。"
                "Example: gws_drive(action='list', query='name contains \"報告\"')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "get", "export"],
                        "description": "操作: list(一覧), get(メタデータ), export(エクスポート)",
                    },
                    # list 用
                    "query": {
                        "type": "string",
                        "description": "action=list 時: 検索クエリ",
                        "default": "",
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "action=list 時: 取得件数 (デフォルト: 10, 最大: 100)",
                        "default": 10,
                    },
                    # get/export 用
                    "file_id": {
                        "type": "string",
                        "description": "action=get/export 時: ファイル ID",
                    },
                    # export 用
                    "mime_type": {
                        "type": "string",
                        "description": "action=export 時: エクスポート形式 (text/plain, text/csv, application/pdf)",
                        "default": "text/plain",
                    },
                    "account": {
                        "type": "string",
                        "description": "アカウント (default, makaron8426, Tolmeton)",
                        "default": "default",
                    },
                },
                "required": ["action"],
            },
        ),
        # ── gws_gmail: Gmail 操作ファサード (list/get/send) ──
        base.Tool(
            name="gws_gmail",
            description=(
                "Gmail 操作。action で操作を選択: "
                "list=メッセージ一覧取得, get=メッセージ内容取得, "
                "send=メール送信。"
                "Example: gws_gmail(action='list', query='is:unread')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "get", "send"],
                        "description": "操作: list(一覧), get(内容取得), send(送信)",
                    },
                    # list 用
                    "query": {
                        "type": "string",
                        "description": "action=list 時: Gmail 検索クエリ",
                        "default": "",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "action=list 時: 取得件数",
                        "default": 10,
                    },
                    # get 用
                    "message_id": {
                        "type": "string",
                        "description": "action=get 時: メッセージ ID",
                    },
                    # send 用
                    "to": {"type": "string", "description": "action=send 時: 宛先"},
                    "subject": {"type": "string", "description": "action=send 時: 件名"},
                    "body": {"type": "string", "description": "action=send 時: 本文"},
                    "account": {
                        "type": "string",
                        "description": "アカウント",
                        "default": "default",
                    },
                },
                "required": ["action"],
            },
        ),
        # ── gws_workspace: Sheets/Calendar/Tasks/Raw/Auth ファサード ──
        base.Tool(
            name="gws_workspace",
            description=(
                "Google Workspace 操作 (Sheets/Calendar/Tasks/Raw/Auth)。action で操作を選択: "
                "sheets_get=スプレッドシートデータ取得, "
                "calendar_list=カレンダー予定一覧, "
                "tasks_list=タスク一覧, "
                "raw=任意のgwsコマンド実行, "
                "auth_status=認証状態確認。"
                "Example: gws_workspace(action='calendar_list')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["sheets_get", "calendar_list", "tasks_list", "raw", "auth_status"],
                        "description": "操作: sheets_get, calendar_list, tasks_list, raw, auth_status",
                    },
                    # sheets_get 用
                    "spreadsheet_id": {"type": "string", "description": "action=sheets_get 時: スプレッドシート ID"},
                    "range": {"type": "string", "description": "action=sheets_get 時: セル範囲 (例: 'Sheet1!A1:D10')", "default": ""},
                    # calendar_list 用
                    "calendar_id": {"type": "string", "description": "action=calendar_list 時: カレンダー ID", "default": "primary"},
                    "max_results": {"type": "integer", "description": "action=calendar_list/tasks_list 時: 取得件数", "default": 10},
                    "time_min": {"type": "string", "description": "action=calendar_list 時: 開始日時 (RFC3339)", "default": ""},
                    # tasks_list 用
                    "tasklist_id": {"type": "string", "description": "action=tasks_list 時: タスクリスト ID", "default": "@default"},
                    # raw 用
                    "service": {"type": "string", "description": "action=raw 時: サービス名 (drive, gmail, sheets, calendar, docs, slides, tasks)"},
                    "resource": {"type": "string", "description": "action=raw 時: リソース名"},
                    "method": {"type": "string", "description": "action=raw 時: メソッド (list, get, create, update, delete)"},
                    "params": {"type": "object", "description": "action=raw 時: API パラメータ", "default": {}},
                    "account": {
                        "type": "string",
                        "description": "アカウント",
                        "default": "default",
                    },
                },
                "required": ["action"],
            },
        ),
    ]


# ============ ツール実行 (ファサード + エイリアス) ============
@server.call_tool(validate_input=True)
# PURPOSE: GWS ツール呼出しのルーティングと実行
async def call_tool(name: str, arguments: dict):
    """GWS ツール呼出しを処理する。"""
    log(f"call_tool: {name} with {list(arguments.keys())}")

    # ── エイリアス層: 旧ツール名 → 新ファサードにリダイレクト ──
    _ALIASES = {
        "gws_drive_list":   ("gws_drive",     {"action": "list"}),
        "gws_drive_get":    ("gws_drive",     {"action": "get"}),
        "gws_drive_export": ("gws_drive",     {"action": "export"}),
        "gws_gmail_list":   ("gws_gmail",     {"action": "list"}),
        "gws_gmail_get":    ("gws_gmail",     {"action": "get"}),
        "gws_gmail_send":   ("gws_gmail",     {"action": "send"}),
        "gws_sheets_get":   ("gws_workspace", {"action": "sheets_get"}),
        "gws_calendar_list":("gws_workspace", {"action": "calendar_list"}),
        "gws_tasks_list":   ("gws_workspace", {"action": "tasks_list"}),
        "gws_raw":          ("gws_workspace", {"action": "raw"}),
        "gws_auth_status":  ("gws_workspace", {"action": "auth_status"}),
    }

    if name in _ALIASES:
        new_name, defaults = _ALIASES[name]
        arguments = {**defaults, **arguments}
        log(f"alias redirect: {name} → {new_name} action={arguments.get('action')}")
        name = new_name

    account = arguments.get("account", "default")

    try:
        # ── gws_drive ファサード ──
        if name == "gws_drive":
            action = arguments.get("action", "list")
            if action == "list":
                params = {"pageSize": arguments.get("page_size", 10)}
                query = arguments.get("query", "")
                if query:
                    params["q"] = query
                result = await run_sync(
                    _run_gws,
                    ["drive", "files", "list", "--params", json.dumps(params)],
                    account,
                )
            elif action == "get":
                file_id = arguments.get("file_id", "")
                if not file_id:
                    return [base.TextContent(type="text", text="Error: file_id is required for action=get")]
                result = await run_sync(
                    _run_gws,
                    ["drive", "files", "get", "--params", json.dumps({"fileId": file_id, "fields": "id,name,mimeType,size,modifiedTime,owners,webViewLink"})],
                    account,
                )
            elif action == "export":
                file_id = arguments.get("file_id", "")
                if not file_id:
                    return [base.TextContent(type="text", text="Error: file_id is required for action=export")]
                mime_type = arguments.get("mime_type", "text/plain")
                result = await run_sync(
                    _run_gws,
                    ["drive", "files", "export", "--params", json.dumps({"fileId": file_id, "mimeType": mime_type})],
                    account,
                )
            else:
                return [base.TextContent(type="text", text=f"Unknown drive action: {action}")]

        # ── gws_gmail ファサード ──
        elif name == "gws_gmail":
            action = arguments.get("action", "list")
            if action == "list":
                params = {
                    "userId": "me",
                    "maxResults": arguments.get("max_results", 10),
                }
                query = arguments.get("query", "")
                if query:
                    params["q"] = query
                result = await run_sync(
                    _run_gws,
                    ["gmail", "users", "messages", "list", "--params", json.dumps(params)],
                    account,
                )
            elif action == "get":
                message_id = arguments.get("message_id", "")
                if not message_id:
                    return [base.TextContent(type="text", text="Error: message_id is required for action=get")]
                result = await run_sync(
                    _run_gws,
                    ["gmail", "users", "messages", "get", "--params", json.dumps({"userId": "me", "id": message_id, "format": "full"})],
                    account,
                )
            elif action == "send":
                import base64
                to = arguments.get("to", "")
                subject = arguments.get("subject", "")
                body = arguments.get("body", "")
                if not all([to, subject, body]):
                    return [base.TextContent(type="text", text="Error: to, subject, body are required for action=send")]
                raw_msg = f"To: {to}\r\nSubject: {subject}\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{body}"
                encoded = base64.urlsafe_b64encode(raw_msg.encode("utf-8")).decode("ascii")
                result = await run_sync(
                    _run_gws,
                    ["gmail", "users", "messages", "send", "--params", json.dumps({"userId": "me", "requestBody": {"raw": encoded}})],
                    account,
                )
            else:
                return [base.TextContent(type="text", text=f"Unknown gmail action: {action}")]

        # ── gws_workspace ファサード ──
        elif name == "gws_workspace":
            action = arguments.get("action", "auth_status")
            if action == "sheets_get":
                spreadsheet_id = arguments.get("spreadsheet_id", "")
                if not spreadsheet_id:
                    return [base.TextContent(type="text", text="Error: spreadsheet_id is required for action=sheets_get")]
                range_str = arguments.get("range", "")
                if range_str:
                    result = await run_sync(
                        _run_gws,
                        ["sheets", "spreadsheets", "values", "get", "--params", json.dumps({"spreadsheetId": spreadsheet_id, "range": range_str})],
                        account,
                    )
                else:
                    result = await run_sync(
                        _run_gws,
                        ["sheets", "spreadsheets", "get", "--params", json.dumps({"spreadsheetId": spreadsheet_id})],
                        account,
                    )
            elif action == "calendar_list":
                calendar_id = arguments.get("calendar_id", "primary")
                params = {
                    "calendarId": calendar_id,
                    "maxResults": arguments.get("max_results", 10),
                    "singleEvents": True,
                    "orderBy": "startTime",
                }
                time_min = arguments.get("time_min", "")
                if time_min:
                    params["timeMin"] = time_min
                result = await run_sync(
                    _run_gws,
                    ["calendar", "events", "list", "--params", json.dumps(params)],
                    account,
                )
            elif action == "tasks_list":
                tasklist_id = arguments.get("tasklist_id", "@default")
                result = await run_sync(
                    _run_gws,
                    ["tasks", "tasks", "list", "--params", json.dumps({"tasklist": tasklist_id})],
                    account,
                )
            elif action == "raw":
                service = arguments.get("service", "")
                resource = arguments.get("resource", "")
                method = arguments.get("method", "")
                if not all([service, resource, method]):
                    return [base.TextContent(type="text", text="Error: service, resource, method are required for action=raw")]
                params = arguments.get("params", {})
                args = [service, resource, method]
                if params:
                    args += ["--params", json.dumps(params)]
                result = await run_sync(_run_gws, args, account)
            elif action == "auth_status":
                result = await run_sync(
                    _run_gws, ["auth", "status"], account
                )
            else:
                return [base.TextContent(type="text", text=f"Unknown workspace action: {action}")]

        else:
            return [base.TextContent(type="text", text=f"Unknown tool: {name}")]

        # 結果をフォーマット
        if result["success"]:
            data = result["data"]
            if isinstance(data, dict) or isinstance(data, list):
                output = json.dumps(data, ensure_ascii=False, indent=2)
            else:
                output = str(data)
            return [base.TextContent(type="text", text=output)]
        else:
            return [base.TextContent(
                type="text",
                text=f"❌ Error: {result['error']}",
            )]

    except Exception as e:  # noqa: BLE001
        log(f"Error in {name}: {e}")
        return [base.TextContent(type="text", text=f"❌ Error: {e}")]


# ============ 起動時チェック ============
if shutil.which("gws") or Path(GWS_BIN).exists():
    log(f"✅ gws CLI found: {GWS_BIN}")
else:
    log(f"⚠️ WARNING: gws CLI not found at {GWS_BIN}")

# アカウント設定の確認
for name_key, config_path in ACCOUNT_CONFIGS.items():
    cred_file = config_path / "credentials.enc"
    if cred_file.exists():
        log(f"✅ Account '{name_key}': {config_path}")
    else:
        log(f"⚠️ Account '{name_key}': No credentials at {config_path}")

# ============ フック ============
base.install_all_hooks()

# ============ エントリポイント ============
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GWS MCP Server", add_help=False)
    parser.add_argument("--test", action="store_true", help="セルフテスト")
    args, _ = parser.parse_known_args()

    if args.test:
        print("GWS MCP Server Test")
        print("-" * 40)
        print(f"gws CLI: {GWS_BIN}")
        for n, p in ACCOUNT_CONFIGS.items():
            cred = p / "credentials.enc"
            print(f"  {n}: {'✅' if cred.exists() else '❌'} {p}")
        print("✅ Server module loaded successfully")
    else:
        base.run()
