#!/usr/bin/env bash
# HGK APP リモートアクセス起動スクリプト
# Win PC から http://100.80.43.103:1420 でアクセス可能にする
set -euo pipefail

HGK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_PORT="${API_PORT:-9698}"
VITE_PORT="${VITE_PORT:-1420}"

echo "🚀 HGK Remote Access Starting..."
echo "   API:  http://0.0.0.0:${API_PORT}"
echo "   Vite: http://0.0.0.0:${VITE_PORT}"
echo "   Win:  http://100.80.43.103:${VITE_PORT}"
echo ""

# 1. FastAPI バックエンド (TCP モード)
echo "[1/2] Starting FastAPI backend..."
cd "$HGK_ROOT"
PYTHONPATH=. nohup .venv/bin/python -m mekhane.api.server \
  --host 0.0.0.0 --port "$API_PORT" \
  > /tmp/hgk-api.log 2>&1 &
API_PID=$!
echo "   PID=$API_PID (log: /tmp/hgk-api.log)"

# 2. Vite dev server
echo "[2/2] Starting Vite dev server..."
cd "$HGK_ROOT/hgk"
nohup npm run dev > /tmp/hgk-vite.log 2>&1 &
VITE_PID=$!
echo "   PID=$VITE_PID (log: /tmp/hgk-vite.log)"

echo ""
echo "✅ Both services started."
echo "   API log:  tail -f /tmp/hgk-api.log"
echo "   Vite log: tail -f /tmp/hgk-vite.log"
echo ""
echo "🛑 To stop: kill $API_PID $VITE_PID"
echo "   or: pkill -f 'mekhane.api.server'; pkill -f 'vite'"
