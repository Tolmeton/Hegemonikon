#!/bin/bash
# Hegemonikón System Health Check
# 主要サービスの動作状態を一括チェックし、問題を報告する
# Usage: ./health_check.sh [--notify]

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

check_service() {
    local name="$1"
    local type="${2:-system}"  # system or user

    if [ "$type" = "user" ]; then
        status=$(systemctl --user is-active "$name" 2>/dev/null || true)
    else
        status=$(systemctl is-active "$name" 2>/dev/null || true)
    fi

    case "$status" in
        active)
            echo -e "  ${GREEN}✅${NC} $name ($type)"
            ;;
        inactive)
            echo -e "  ${YELLOW}⚫${NC} $name ($type) — inactive"
            ((WARNINGS++)) || true
            ;;
        failed)
            echo -e "  ${RED}❌${NC} $name ($type) — FAILED"
            ((ERRORS++)) || true
            ;;
        *)
            echo -e "  ${YELLOW}?${NC}  $name ($type) — $status"
            ((WARNINGS++)) || true
            ;;
    esac
}

check_nvidia() {
    if nvidia-smi --query-gpu=name,driver_version,temperature.gpu --format=csv,noheader &>/dev/null; then
        local info
        info=$(nvidia-smi --query-gpu=name,temperature.gpu --format=csv,noheader 2>/dev/null)
        echo -e "  ${GREEN}✅${NC} NVIDIA GPU: $info"
    else
        echo -e "  ${RED}❌${NC} NVIDIA GPU: nvidia-smi failed"
        ((ERRORS++)) || true
    fi
}

check_dkms() {
    local kernel
    kernel=$(uname -r)
    # sudo なしで dkms status を試行。失敗時は /var/lib/dkms を直接確認
    if dkms status 2>/dev/null | grep -q "$kernel.*installed"; then
        echo -e "  ${GREEN}✅${NC} DKMS: nvidia module built for $kernel"
    elif [ -d "/var/lib/dkms/nvidia-current" ] && ls /lib/modules/"$kernel"/updates/dkms/nvidia*.ko* &>/dev/null; then
        echo -e "  ${GREEN}✅${NC} DKMS: nvidia module present for $kernel (file check)"
    else
        echo -e "  ${YELLOW}⚠️${NC}  DKMS: could not verify nvidia module for $kernel"
        ((WARNINGS++)) || true
    fi
}

check_disk() {
    local usage
    usage=$(df / --output=pcent | tail -1 | tr -d ' %')
    if [ "$usage" -gt 90 ]; then
        echo -e "  ${RED}❌${NC} Disk: ${usage}% used (>90%)"
        ((ERRORS++)) || true
    elif [ "$usage" -gt 80 ]; then
        echo -e "  ${YELLOW}⚠️${NC}  Disk: ${usage}% used (>80%)"
        ((WARNINGS++)) || true
    else
        echo -e "  ${GREEN}✅${NC} Disk: ${usage}% used"
    fi
}

check_failed_units() {
    local failed_system
    local failed_user
    failed_system=$(systemctl --failed --no-legend 2>/dev/null | wc -l)
    failed_user=$(systemctl --user --failed --no-legend 2>/dev/null | wc -l)

    if [ "$failed_system" -gt 0 ]; then
        # system の failed unit は HGK の管轄外 → warning
        echo -e "  ${YELLOW}⚠️${NC}  Failed system units: ${failed_system} (not in HGK scope)"
        systemctl --failed --no-legend 2>/dev/null | while read -r unit _; do
            echo -e "       ${YELLOW}↳${NC} $unit"
        done
        ((WARNINGS += failed_system)) || true
    fi
    if [ "$failed_user" -gt 0 ]; then
        # user の failed unit は HGK の責任 → error
        echo -e "  ${RED}❌${NC} Failed user units: ${failed_user}"
        systemctl --user --failed --no-legend 2>/dev/null | while read -r unit _; do
            echo -e "       ${RED}↳${NC} $unit (user)"
        done
        ((ERRORS += failed_user)) || true
    fi
    if [ "$failed_system" -eq 0 ] && [ "$failed_user" -eq 0 ]; then
        echo -e "  ${GREEN}✅${NC} No failed units"
    fi
}

echo "═══════════════════════════════════════"
echo " Hegemonikón System Health Check"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════"

echo ""
echo "📦 Core Services:"
check_service "ssh" "system"
check_service "NetworkManager" "system"
check_service "docker" "system"
check_service "cron" "system"
check_service "rustdesk" "system"
check_service "nvidia-persistenced" "system"

echo ""
echo "👤 User Services:"
check_service "syncthing" "user"
check_service "pipewire" "user"

echo ""
echo "🖥️ Hardware:"
check_nvidia
check_dkms

echo ""
echo "💾 Storage:"
check_disk

echo ""
echo "🔍 Failed Units (systemd):"
check_failed_units

echo ""
echo "═══════════════════════════════════════"
if [ "$ERRORS" -gt 0 ]; then
    echo -e " ${RED}Result: ${ERRORS} errors, ${WARNINGS} warnings${NC}"
    exit 1
elif [ "$WARNINGS" -gt 0 ]; then
    echo -e " ${YELLOW}Result: ${WARNINGS} warnings${NC}"
    exit 0
else
    echo -e " ${GREEN}Result: All healthy ✅${NC}"
    exit 0
fi
