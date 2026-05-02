#!/bin/bash
# reload-mcp-periskope.sh — MCP サーバーのホットリロード
#
# Usage: ./scripts/reload-mcp-periskope.sh
#
# Kills existing Periskopē MCP server processes and waits for IDE
# to auto-restart them. If IDE doesn't restart, launches manually.

set -e

SCRIPT_PATH="mekhane/mcp/periskope_mcp_server.py"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "🔄 Periskopē MCP サーバーをリロードします..."

# 1. Find and kill existing processes
PIDS=$(pgrep -f "$SCRIPT_PATH" 2>/dev/null || true)
if [ -n "$PIDS" ]; then
    echo "   既存プロセスを停止: $PIDS"
    kill $PIDS 2>/dev/null || true
    sleep 2
    # Force kill if still running
    REMAINING=$(pgrep -f "$SCRIPT_PATH" 2>/dev/null || true)
    if [ -n "$REMAINING" ]; then
        echo "   強制終了: $REMAINING"
        kill -9 $REMAINING 2>/dev/null || true
        sleep 1
    fi
else
    echo "   既存プロセスなし"
fi

# 2. Wait for IDE auto-restart (up to 10 seconds)
echo "   IDE の自動再起動を待機中..."
for i in $(seq 1 10); do
    NEW_PID=$(pgrep -f "$SCRIPT_PATH" 2>/dev/null || true)
    if [ -n "$NEW_PID" ]; then
        echo "✅ MCP サーバー再起動完了 (PID: $NEW_PID)"
        exit 0
    fi
    sleep 1
done

# 3. IDE didn't restart — launch manually
echo "   IDE による自動再起動なし。手動起動します..."
nohup "$REPO_ROOT/.venv/bin/python" "$REPO_ROOT/$SCRIPT_PATH" \
    > /tmp/periskope-mcp.log 2>&1 &
NEW_PID=$!
echo "✅ MCP サーバー手動起動完了 (PID: $NEW_PID)"
echo "   ログ: /tmp/periskope-mcp.log"
echo ""
echo "⚠️  手動起動のため IDE の MCP 接続が切れている可能性があります。"
echo "   IDE のコマンドパレットから 'Developer: Reload Window' を実行してください。"
