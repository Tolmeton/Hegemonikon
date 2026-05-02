#!/usr/bin/env bash
# hgk-cli.sh — HTTP API helper for Hegemonikón
# MCP が不安定な環境向けの代替アクセス手段
# Usage: hgk-cli.sh <command> [args...]

set -euo pipefail

# Configuration
HGK_HOST="${HGK_HOST:-localhost}"
HGK_PORT="${HGK_PORT:-9698}"
HGK_BASE_URL="http://${HGK_HOST}:${HGK_PORT}"
TIMEOUT="${HGK_TIMEOUT:-10}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

usage() {
    cat <<EOF
${CYAN}hgk-cli.sh${NC} — Hegemonikón HTTP API ヘルパー

${YELLOW}使い方:${NC}
  hgk-cli.sh status              システム状態を確認
  hgk-cli.sh ask <message>       LLM に質問 (Gemini Flash)
  hgk-cli.sh ask-agent <message> Agent モードで質問 (tool use 付き)
  hgk-cli.sh jules-list          Jules セッション一覧
  hgk-cli.sh jules-status <id>   Jules セッション状態
  hgk-cli.sh search <query>      Gnōsis ベクトル検索
  hgk-cli.sh health              Peira ヘルスチェック
  hgk-cli.sh raw <method> <path> [data]  任意の API 呼出し

${YELLOW}環境変数:${NC}
  HGK_HOST     ホスト名 (default: localhost)
  HGK_PORT     ポート番号 (default: 9699)
  HGK_TIMEOUT  タイムアウト秒 (default: 10)

${YELLOW}例:${NC}
  hgk-cli.sh status
  hgk-cli.sh ask "FEP の公理は何ですか"
  hgk-cli.sh raw GET /api/v1/hgk/status
EOF
}

_curl() {
    local method="$1"
    local path="$2"
    shift 2
    curl -s -m "$TIMEOUT" -X "$method" \
        -H "Content-Type: application/json" \
        "${HGK_BASE_URL}${path}" "$@" 2>/dev/null
}

_check_connection() {
    if ! curl -s -m 3 "${HGK_BASE_URL}/api/health" >/dev/null 2>&1; then
        echo -e "${RED}✗ HGK API に接続できません (${HGK_BASE_URL})${NC}" >&2
        echo "  → uvicorn が起動しているか確認:" >&2
        echo "    pgrep -f 'uvicorn.*serve'" >&2
        echo "    PYTHONPATH=. .venv/bin/uvicorn hgk.api.serve:app --port ${HGK_PORT} --host 127.0.0.1" >&2
        exit 1
    fi
}

cmd_status() {
    _check_connection
    echo -e "${CYAN}━━━ HGK Status ━━━${NC}"
    _curl GET "/api/status" | python3 -m json.tool 2>/dev/null || \
    echo -e "${RED}✗ /api/status に接続できません${NC}"
}

cmd_ask() {
    _check_connection
    local message="${1:?メッセージを指定してください}"
    local data
    data=$(python3 -c "import json; print(json.dumps({'message': '$message', 'model': 'gemini-2.0-flash'}))")
    
    echo -e "${CYAN}━━━ Ask ━━━${NC}"
    _curl POST "/api/ask" -d "$data" | python3 -m json.tool 2>/dev/null || \
    echo -e "${RED}✗ /api/ask に接続できません${NC}"
}

cmd_ask_agent() {
    _check_connection
    local message="${1:?メッセージを指定してください}"
    local data
    data=$(python3 -c "import json; print(json.dumps({'message': '$message', 'model': 'gemini-3.1-pro-preview'}))")
    
    echo -e "${CYAN}━━━ Ask Agent ━━━${NC}"
    local timeout_save="$TIMEOUT"
    TIMEOUT=120
    _curl POST "/api/ask/agent" -d "$data" | python3 -m json.tool 2>/dev/null || \
    echo -e "${RED}✗ /api/ask/agent に接続できません${NC}"
    TIMEOUT="$timeout_save"
}

cmd_jules_list() {
    _check_connection
    echo -e "${CYAN}━━━ Jules Sessions ━━━${NC}"
    _curl GET "/api/jules/sessions" | python3 -m json.tool 2>/dev/null || \
    echo -e "${RED}✗ /api/jules/sessions に接続できません${NC}"
}

cmd_jules_status() {
    _check_connection
    local session_id="${1:?セッション ID を指定してください}"
    echo -e "${CYAN}━━━ Jules Session: ${session_id} ━━━${NC}"
    _curl GET "/api/jules/sessions/${session_id}" | python3 -m json.tool 2>/dev/null || \
    echo -e "${RED}✗ セッション情報を取得できません${NC}"
}

cmd_search() {
    _check_connection
    local query="${1:?検索クエリを指定してください}"
    local data
    data=$(python3 -c "import json; print(json.dumps({'query': '$query', 'limit': 10}))")
    
    echo -e "${CYAN}━━━ Gnōsis Search ━━━${NC}"
    _curl POST "/api/hgk/search" -d "$data" | python3 -m json.tool 2>/dev/null || \
    echo -e "${RED}✗ /api/hgk/search に接続できません${NC}"
}

cmd_health() {
    _check_connection
    echo -e "${CYAN}━━━ Health Check ━━━${NC}"
    _curl GET "/api/health" | python3 -m json.tool 2>/dev/null || \
    echo -e "${RED}✗ /api/health に接続できません${NC}"
}

cmd_raw() {
    _check_connection
    local method="${1:?HTTP メソッドを指定 (GET/POST/PUT/DELETE)}"
    local path="${2:?パスを指定 (例: /api/v1/status)}"
    shift 2
    
    echo -e "${CYAN}━━━ ${method} ${path} ━━━${NC}"
    if [ $# -gt 0 ]; then
        _curl "$method" "$path" -d "$1" | python3 -m json.tool 2>/dev/null
    else
        _curl "$method" "$path" | python3 -m json.tool 2>/dev/null
    fi
}

# Main dispatch
case "${1:-}" in
    status)     cmd_status ;;
    ask)        shift; cmd_ask "$@" ;;
    ask-agent)  shift; cmd_ask_agent "$@" ;;
    jules-list) cmd_jules_list ;;
    jules-status) shift; cmd_jules_status "$@" ;;
    search)     shift; cmd_search "$@" ;;
    health)     cmd_health ;;
    raw)        shift; cmd_raw "$@" ;;
    -h|--help|help|"") usage ;;
    *)          echo -e "${RED}不明なコマンド: $1${NC}"; usage; exit 1 ;;
esac
