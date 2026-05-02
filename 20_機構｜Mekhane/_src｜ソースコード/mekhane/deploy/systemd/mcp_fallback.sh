#!/bin/bash
# PROOF: MCP フォールバック機構 v3 — systemd 統合版
# PURPOSE: systemd の hgk-mcp-fwd@.service / hgk-mcp@.service を単一管理平面とする
#
# v2 → v3 変更点:
#   - socat 手動管理 → systemd に全面委譲
#   - PID ファイル → systemctl is-active で状態判定
#   - check は systemctl restart/stop/start のみ
#   - 状態表示は維持
#
# サブコマンド:
#   status  — サーバーごとの状態を表示
#   check   — 個別ヘルスチェック → systemd で部分フェイルオーバー
#   forward — 全サーバーを FORWARD モードに切替 (systemd)
#   local   — 全サーバーを LOCAL モードに切替 (systemd)
#   stop    — 全停止

set -uo pipefail

# === 設定 ===
HGK_HOST="hgk.tail3b6058.ts.net"
PROBE_TIMEOUT=3
LOG_FILE="${HOME}/.hegemonikon/logs/mcp_fallback.log"

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

SERVERS=("ochema" "sympatheia" "hermeneus" "mneme" "sekisho" "periskope" "digestor" "jules" "typos" "phantazein")

# === ログ ===
log() {
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[$(date -Iseconds)] $*" | tee -a "$LOG_FILE"
}

# === ヘルパー関数 ===

# 特定サーバーが hgk で応答しているか
is_server_alive_on_hgk() {
    local server="$1"
    local port="${PORTS[$server]}"
    local http_code
    http_code=$(curl -s --connect-timeout "$PROBE_TIMEOUT" --max-time "$((PROBE_TIMEOUT + 2))" \
        -o /dev/null -w "%{http_code}" "http://${HGK_HOST}:${port}/mcp" 2>/dev/null) || return 1
    [ "$http_code" != "000" ]
}

# systemd フォワーダーが動いているか
is_server_forwarding() {
    local server="$1"
    systemctl --user is-active "hgk-mcp-fwd@${server}.service" >/dev/null 2>&1
}

# 本機 MCP が動いているか
is_server_local() {
    local server="$1"
    systemctl --user is-active "hgk-mcp@${server}.service" >/dev/null 2>&1
}

# systemd フォワーダーを起動 (排他: ローカル MCP は自動停止)
start_server_forwarding() {
    local server="$1"
    systemctl --user stop "hgk-mcp@${server}.service" 2>/dev/null || true
    systemctl --user reset-failed "hgk-mcp-fwd@${server}.service" 2>/dev/null || true
    systemctl --user start "hgk-mcp-fwd@${server}.service" 2>/dev/null || true
    log "FWD  $server → systemd"
}

# systemd フォワーダーを停止
stop_server_forwarding() {
    local server="$1"
    systemctl --user stop "hgk-mcp-fwd@${server}.service" 2>/dev/null || true
    log "STOP_FWD $server"
}

# 本機 MCP を起動 (排他: フォワーダーは自動停止)
start_server_local() {
    local server="$1"
    systemctl --user stop "hgk-mcp-fwd@${server}.service" 2>/dev/null || true
    systemctl --user start "hgk-mcp@${server}.service" 2>/dev/null || true
    log "LOCAL_START $server"
}

# 本機 MCP を停止
stop_server_local() {
    local server="$1"
    systemctl --user stop "hgk-mcp@${server}.service" 2>/dev/null || true
    log "LOCAL_STOP $server"
}

# === サブコマンド ===

cmd_status() {
    echo "=== MCP フォールバック状態 (v3 systemd) ==="
    echo ""
    printf "%-14s %-6s %-10s %-10s %s\n" "サーバー" "ポート" "hgk" "fwd(sd)" "local(sd)"
    printf "%-14s %-6s %-10s %-10s %s\n" "──────────" "────" "────────" "────────" "──────"

    local hgk_ok=0 hgk_ng=0 fwd=0 local_mcp=0

    for server in "${SERVERS[@]}"; do
        local port="${PORTS[$server]}"
        local hgk_status fwd_status local_status

        if is_server_alive_on_hgk "$server"; then
            hgk_status="🟢"
            ((hgk_ok++))
        else
            hgk_status="🔴"
            ((hgk_ng++))
        fi

        if is_server_forwarding "$server"; then
            fwd_status="🔀"
            ((fwd++))
        else
            fwd_status="⬜"
        fi

        if is_server_local "$server"; then
            local_status="🏠"
            ((local_mcp++))
        else
            local_status="⬜"
        fi

        printf "%-14s %-6s %-10s %-10s %s\n" "$server" "$port" "$hgk_status" "$fwd_status" "$local_status"
    done

    echo ""
    echo "集計: hgk応答 $hgk_ok / 不応答 $hgk_ng / fwd(systemd) $fwd / local(systemd) $local_mcp"

    # モード判定
    if [ "$hgk_ng" -eq 0 ] && [ "$fwd" -eq 10 ]; then
        echo "📡 モード: FORWARD (全サーバー hgk 経由)"
    elif [ "$hgk_ok" -eq 0 ] && [ "$local_mcp" -eq 10 ]; then
        echo "🏠 モード: LOCAL (全サーバー本機)"
    elif [ "$hgk_ng" -gt 0 ] && [ "$hgk_ok" -gt 0 ]; then
        echo "🔀 モード: HYBRID (部分フェイルオーバー)"
    elif [ "$fwd" -eq 0 ] && [ "$local_mcp" -eq 0 ]; then
        echo "❌ モード: 停止 (MCP 不通)"
    else
        echo "⚠️  モード: 混在"
    fi
}

cmd_check() {
    log "CHECK 開始"
    local changed=0

    for server in "${SERVERS[@]}"; do
        if is_server_alive_on_hgk "$server"; then
            # hgk で応答あり → フォワーダーモードにすべき
            if is_server_local "$server"; then
                echo "  [$server] hgk 応答あり → LOCAL停止 → FWD起動"
                start_server_forwarding "$server"
                ((changed++))
            elif ! is_server_forwarding "$server"; then
                echo "  [$server] hgk 応答あり → FWD起動"
                start_server_forwarding "$server"
                ((changed++))
            fi
        else
            # hgk で応答なし → 本機にフォールバック
            if is_server_forwarding "$server"; then
                echo "  [$server] hgk 不応答 → FWD停止 → LOCAL起動"
                stop_server_forwarding "$server"
                start_server_local "$server"
                ((changed++))
            elif ! is_server_local "$server"; then
                echo "  [$server] hgk 不応答 → LOCAL起動"
                start_server_local "$server"
                ((changed++))
            fi
        fi
    done

    if [ "$changed" -gt 0 ]; then
        log "CHECK 完了: $changed 件変更"
    else
        log "CHECK 完了: 変更なし"
    fi

    echo ""
    cmd_status
}

cmd_forward() {
    echo "=== 全サーバー FWD モード (systemd) ==="
    for server in "${SERVERS[@]}"; do
        start_server_forwarding "$server"
    done
    sleep 2
    cmd_status
}

cmd_local() {
    echo "=== 全サーバー LOCAL モード (systemd) ==="
    for server in "${SERVERS[@]}"; do
        stop_server_forwarding "$server"
        start_server_local "$server"
    done
    sleep 2
    cmd_status
}

cmd_stop() {
    echo "=== 全停止 (systemd) ==="
    for server in "${SERVERS[@]}"; do
        stop_server_forwarding "$server"
        stop_server_local "$server"
    done
}

# === メイン ===

case "${1:-status}" in
    status)  cmd_status  ;;
    check)   cmd_check   ;;
    forward) cmd_forward ;;
    local)   cmd_local   ;;
    stop)    cmd_stop    ;;
    *)
        echo "Usage: $0 {status|check|forward|local|stop}"
        echo ""
        echo "  status   サーバーごとの状態を表示 (read-only)"
        echo "  check    ヘルスチェック → systemd で部分フェイルオーバー"
        echo "  forward  全サーバーを FORWARD モードに (systemd)"
        echo "  local    全サーバーを LOCAL モードに (systemd)"
        echo "  stop     全停止 (systemd)"
        exit 1
        ;;
esac
