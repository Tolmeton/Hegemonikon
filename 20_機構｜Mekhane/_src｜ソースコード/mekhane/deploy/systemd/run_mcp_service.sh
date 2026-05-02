#!/bin/bash
set -e

SERVER_NAME="$1"

if [ -z "$SERVER_NAME" ]; then
    echo "Usage: $0 <server_name>"
    exit 1
fi

PROJECT_ROOT="/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
if [ -x "$PROJECT_ROOT/.tmp/mcp-runtime-venv/bin/python" ]; then
    PYTHON_BIN="$PROJECT_ROOT/.tmp/mcp-runtime-venv/bin/python"
else
    PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
fi

# ポートマッピング (mcp_ports.sh に一元管理)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/mcp_ports.sh"

# モジュールマッピング
declare -A MODULES
MODULES=(
    ["aisthetikon"]="mekhane.mcp.hub_mcp_server"
    ["dianoetikon"]="mekhane.mcp.hub_mcp_server"
    ["poietikon"]="mekhane.mcp.hub_mcp_server"
    ["ochema"]="mekhane.mcp.ochema_mcp_server"
    ["sympatheia"]="mekhane.mcp.sympatheia_mcp_server"
    ["hermeneus"]="hermeneus.src.mcp_server"
    ["phantazein"]="mekhane.mcp.mneme_server"  # 旧 mneme
    ["sekisho"]="mekhane.mcp.sekisho_mcp_server"
    ["periskope"]="mekhane.mcp.periskope_mcp_server"
    ["digestor"]="mekhane.mcp.digestor_mcp_server"
    ["jules"]="mekhane.mcp.jules_mcp_server"
    ["typos"]="mekhane.mcp.typos_mcp_server"
    ["phantazein-boot"]="mekhane.mcp.phantazein_mcp_server"
    ["gws"]="mekhane.mcp.gws_mcp_server"
    ["opsis"]="mekhane.mcp.opsis_mcp_server"
    ["api"]="mekhane.api.server"
)

PORT="${MCP_PORTS[$SERVER_NAME]}"
MODULE="${MODULES[$SERVER_NAME]}"

if [ -z "$PORT" ] || [ -z "$MODULE" ]; then
    echo "Unknown server name or configuration missing: $SERVER_NAME"
    exit 1
fi

echo "[$(date -Iseconds)] Starting $SERVER_NAME on port $PORT..."
# 20_機構 (メインコード) + 80_運用 (後方互換 shim: scripts.bc_violation_logger 等)
export PYTHONPATH="$PROJECT_ROOT/20_機構｜Mekhane/_src｜ソースコード:$PROJECT_ROOT/80_運用｜Ops/_src｜ソースコード"

# .env から環境変数をロード (JULES_API_KEY 等)
ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    set -a  # 自動 export
    source "$ENV_FILE"
    set +a
    echo "  Loaded .env ($(grep -c '=' "$ENV_FILE") vars)"
fi

# 起動前構文チェック: SyntaxError による crash loop を事前防止
MODULE_PATH="${MODULE//.//}.py"
for p in ${PYTHONPATH//:/ }; do
    if [ -f "$p/$MODULE_PATH" ]; then
        if ! "$PYTHON_BIN" -m py_compile "$p/$MODULE_PATH" 2>&1; then
            echo "FATAL: SyntaxError in $MODULE ($p/$MODULE_PATH) — 起動中止"
            exit 1
        fi
        echo "  Syntax check passed: $MODULE"
        break
    fi
done

# API サーバーは REST (--host) で起動、MCP サーバーは streamable-http で起動
if [ "$SERVER_NAME" = "api" ]; then
    exec "$PYTHON_BIN" -u -m "$MODULE" --port "$PORT" --host 127.0.0.1
elif [ "$SERVER_NAME" = "aisthetikon" ] || [ "$SERVER_NAME" = "dianoetikon" ] || [ "$SERVER_NAME" = "poietikon" ]; then
    PROFILE="${HGK_MCP_PROFILE:-local}"
    REMOTE_HOST="${HGK_REMOTE_MCP_HOST:-100.83.204.102}"
    exec "$PYTHON_BIN" -u -m "$MODULE" \
        --transport streamable-http \
        --port "$PORT" \
        --axis "$SERVER_NAME" \
        --placement-profile "$PROFILE" \
        --remote-upstream-host "$REMOTE_HOST"
else
    exec "$PYTHON_BIN" -u -m "$MODULE" --transport streamable-http --port "$PORT"
fi
