#!/bin/bash
# PURPOSE: MCP サービスの profile 別デプロイ (local / remote)
set -euo pipefail

PROFILE="${1:-${HGK_MCP_PROFILE:-local}}"
SOURCE_DIR="/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/deploy/systemd"
SYSTEMD_DIR="$HOME/.config/systemd/user"
API_PORT=9696

LOCAL_SERVERS=(
    "aisthetikon" "dianoetikon" "poietikon"
    "ochema" "sympatheia" "hermeneus" "phantazein" "sekisho" "typos"
    "phantazein-boot" "gws" "opsis" "api"
)
REMOTE_SERVERS=(
    "aisthetikon" "dianoetikon" "poietikon"
    "periskope" "digestor" "jules"
)
LOCAL_AUX_UNITS=("hgk-ls-remote-register.service")
REMOTE_AUX_UNITS=(
    "ls-daemon.service"
    "hgk-ls-warmup-morning.timer"
    "hgk-ls-warmup-noon.timer"
    "hgk-ls-warmup-evening.timer"
)
REMOTE_COPY_ONLY_UNITS=("hgk-ls-warmup.service")

if [ "$PROFILE" != "local" ] && [ "$PROFILE" != "remote" ]; then
    echo "Unknown profile: $PROFILE" >&2
    echo "Usage: $0 [local|remote]" >&2
    exit 1
fi

echo "=== Phase 1: systemd 準備 ($PROFILE) ==="
mkdir -p "$SYSTEMD_DIR"
for unit in hgk-mcp@.service "${LOCAL_AUX_UNITS[@]}" "${REMOTE_AUX_UNITS[@]}" "${REMOTE_COPY_ONLY_UNITS[@]}"; do
    if [ -f "$SOURCE_DIR/$unit" ]; then
        target="$SYSTEMD_DIR/$unit"
        src_real=$(readlink -f "$SOURCE_DIR/$unit")
        dst_real=$(readlink -f "$target" 2>/dev/null || true)
        if [ "$src_real" != "$dst_real" ]; then
            cp -f "$SOURCE_DIR/$unit" "$SYSTEMD_DIR/"
        fi
    fi
done
chmod +x "$SOURCE_DIR/run_mcp_service.sh"

echo "=== Phase 2: 旧 forward / port 残骸クリーンアップ ==="
for fwd in $(systemctl --user list-units 'hgk-mcp-fwd@*' --all --plain --no-legend 2>/dev/null | awk '{print $1}'); do
    systemctl --user stop "$fwd" 2>/dev/null || true
    systemctl --user mask "$fwd" 2>/dev/null || true
    systemctl --user reset-failed "$fwd" 2>/dev/null || true
    echo "  stopped + masked: $fwd"
done
for port in 9696 9701 9702 9703 9704 9705 9706 9707 9708 9709 9710 9711 9712 9713 9720 9721 9722; do
    socat_pids=$({ lsof -ti TCP:$port -sTCP:LISTEN 2>/dev/null || true; } | while read -r pid; do
        if grep -q socat /proc/$pid/comm 2>/dev/null; then echo "$pid"; fi
    done)
    if [ -n "$socat_pids" ]; then
        echo "  killing orphan socat on :$port (PIDs: $socat_pids)"
        echo "$socat_pids" | xargs kill 2>/dev/null || true
    fi
done
sleep 1

echo "=== Phase 3: daemon-reload + profile deployment ==="
systemctl --user daemon-reload

if [ "$PROFILE" = "local" ]; then
    SERVERS=("${LOCAL_SERVERS[@]}")
    ENABLE_UNITS=("${LOCAL_AUX_UNITS[@]}")
    DISABLE_UNITS=("${REMOTE_AUX_UNITS[@]}")
else
    SERVERS=("${REMOTE_SERVERS[@]}")
    ENABLE_UNITS=("${REMOTE_AUX_UNITS[@]}")
    DISABLE_UNITS=("${LOCAL_AUX_UNITS[@]}")
fi

for unit in "${DISABLE_UNITS[@]}"; do
    systemctl --user disable --now "$unit" 2>/dev/null || true
done

for server in "${SERVERS[@]}"; do
    echo "  Enabling and starting hgk-mcp@${server}.service..."
    systemctl --user enable "hgk-mcp@${server}.service"
    systemctl --user restart "hgk-mcp@${server}.service"
done

for unit in "${ENABLE_UNITS[@]}"; do
    echo "  Enabling and starting ${unit}..."
    systemctl --user enable "$unit"
    systemctl --user restart "$unit"
done

echo "=== Phase 4: 補助サービスの停止 ==="
ALL_SERVERS=("${LOCAL_SERVERS[@]}" "${REMOTE_SERVERS[@]}")
for server in "${ALL_SERVERS[@]}"; do
    keep=0
    for enabled in "${SERVERS[@]}"; do
        if [ "$server" = "$enabled" ]; then
            keep=1
            break
        fi
    done
    if [ "$keep" -eq 0 ]; then
        systemctl --user disable --now "hgk-mcp@${server}.service" 2>/dev/null || true
    fi
done

if [ "$PROFILE" = "local" ]; then
    echo "=== Phase 5: Tailscale Funnel 設定 ==="
    CURRENT_FUNNEL=$(sudo tailscale funnel status 2>/dev/null | grep -oP '127\.0\.0\.1:\K[0-9]+' || echo "")
    if [ "$CURRENT_FUNNEL" != "$API_PORT" ]; then
        echo "  Funnel ポートを $CURRENT_FUNNEL → $API_PORT に更新..."
        sudo tailscale funnel --bg --https=443 "127.0.0.1:$API_PORT"
        echo "  ✅ Funnel を $API_PORT に設定完了"
    else
        echo "  ✅ Funnel は既に :$API_PORT を指しています"
    fi
fi

echo "=== Phase 6: ヘルスチェック ==="
sleep 2
for port in 9720 9721 9722; do
    if curl -sf "http://127.0.0.1:$port/health" >/dev/null 2>&1; then
        echo "  ✅ axis router OK :$port"
    else
        echo "  ⚠️ axis router health failed :$port"
    fi
done

if [ "$PROFILE" = "local" ]; then
    if curl -sf "http://127.0.0.1:$API_PORT/health" >/dev/null 2>&1; then
        echo "  ✅ API ヘルスチェック OK (port $API_PORT)"
    else
        echo "  ⚠️ API ヘルスチェック失敗 (port $API_PORT)"
    fi
fi

echo
echo "=== デプロイ完了 ($PROFILE) ==="
echo "サービス一覧: systemctl --user list-units 'hgk-mcp@*'"
