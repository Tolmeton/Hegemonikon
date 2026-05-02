#!/bin/bash
# PURPOSE: socat フォワーダー起動スクリプト — systemd から呼ばれる
# USAGE: run_mcp_forward.sh <server_name>
set -e

SERVER_NAME="$1"
HGK_HOST="hgk.tail3b6058.ts.net"

if [ -z "$SERVER_NAME" ]; then
    echo "Usage: $0 <server_name>" >&2
    exit 1
fi

# ポートマッピング (run_mcp_service.sh と同一)
declare -A PORTS=(
    ["ochema"]=9701
    ["sympatheia"]=9702
    ["hermeneus"]=9703
    ["mneme"]=9704
    ["sekisho"]=9705
    ["periskope"]=9706
    ["digestor"]=9707
    ["jules"]=9708
    ["typos"]=9709
    ["phantazein"]=9710
)

PORT="${PORTS[$SERVER_NAME]}"
if [ -z "$PORT" ]; then
    echo "Unknown server: $SERVER_NAME" >&2
    exit 1
fi

echo "[fwd] $SERVER_NAME :$PORT → $HGK_HOST:$PORT"
exec socat TCP-LISTEN:"$PORT",fork,reuseaddr TCP:"$HGK_HOST":"$PORT"
