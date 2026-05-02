#!/usr/bin/env bash
# ============================================================================
# HGK Backend セットアップスクリプト (IaC)
# 対象: Debian 13 (trixie) / WSL2 / ベアメタル
# 用途: 新マシンへの HGK Backend 環境を再現可能に構築する
#
# 使い方:
#   1. SSH 鍵認証を設定 (ssh-copy-id makaron8426@<IP>)
#   2. ローカルから: scp setup_hgk_backend.sh makaron8426@<IP>:/tmp/
#   3. リモートで: bash /tmp/setup_hgk_backend.sh
# ============================================================================
set -euo pipefail

HGK_ROOT="${HOME}/Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
OIKOS_ROOT="${HOME}/Sync/oikos"

log() { echo "[$(date '+%H:%M:%S')] $*"; }
err() { echo "[ERROR] $*" >&2; exit 1; }

# ─── Phase 1: 基盤パッケージ ───
install_base() {
  log "Phase 1: 基盤パッケージのインストール"
  sudo apt-get update -qq
  sudo apt-get install -y -qq \
    git curl gnupg ca-certificates lsb-release \
    build-essential python3.13-venv python3.13-dev pybind11-dev \
    rsync
  log "Phase 1 完了"
}

# ─── Phase 2: Docker ───
install_docker() {
  if command -v docker &>/dev/null; then
    log "Docker は既にインストール済み: $(docker --version)"
    return 0
  fi
  log "Phase 2: Docker のインストール"
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
  log "Phase 2 完了 (再ログインが必要)"
}

# ─── Phase 3: Node.js ───
install_nodejs() {
  if command -v node &>/dev/null; then
    log "Node.js は既にインストール済み: $(node --version)"
    return 0
  fi
  log "Phase 3: Node.js 20.x のインストール"
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y -qq nodejs
  log "Phase 3 完了"
}

# ─── Phase 4: Syncthing ───
install_syncthing() {
  if command -v syncthing &>/dev/null; then
    log "Syncthing は既にインストール済み: $(syncthing --version | head -1)"
    return 0
  fi
  log "Phase 4: Syncthing のインストール"
  sudo mkdir -p /etc/apt/keyrings
  sudo curl -L -o /etc/apt/keyrings/syncthing-archive-keyring.gpg \
    https://syncthing.net/release-key.gpg
  echo "deb [signed-by=/etc/apt/keyrings/syncthing-archive-keyring.gpg] https://apt.syncthing.net/ syncthing stable" \
    | sudo tee /etc/apt/sources.list.d/syncthing.list > /dev/null
  sudo apt-get update -qq
  sudo apt-get install -y -qq syncthing
  systemctl --user enable syncthing
  systemctl --user start syncthing
  log "Phase 4 完了"
}

# ─── Phase 5: スリープ無効化 ───
disable_sleep() {
  log "Phase 5: スリープ/サスペンド無効化"
  sudo mkdir -p /etc/systemd/logind.conf.d
  sudo tee /etc/systemd/logind.conf.d/no-sleep.conf > /dev/null << 'LOGIND'
[Login]
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
HandleLidSwitchDocked=ignore
HandleSuspendKey=ignore
HandleHibernateKey=ignore
IdleAction=ignore
IdleActionSec=0
LOGIND
  sudo systemctl restart systemd-logind
  sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
  log "Phase 5 完了"
}

# ─── Phase 6: Python venv ───
setup_venv() {
  log "Phase 6: Python venv 構築"
  cd "${HGK_ROOT}"
  if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    log "venv 作成完了"
  fi
  .venv/bin/pip install --upgrade pip -q
  if [ -f "requirements.txt" ]; then
    .venv/bin/pip install -r requirements.txt -q
    log "requirements.txt からインストール完了"
  else
    log "WARNING: requirements.txt が見つかりません"
  fi
  log "Phase 6 完了"
}

# ─── Phase 7: Docker Compose サービス ───
start_docker_services() {
  log "Phase 7: Docker Compose サービスの起動"

  # .env をプロジェクトルートにコピー
  if [ -f "${OIKOS_ROOT}/.env" ]; then
    cp "${OIKOS_ROOT}/.env" "${HGK_ROOT}/20_機構｜Mekhane/_src｜ソースコード/mekhane/periskope/docker/.env"
    cp "${OIKOS_ROOT}/.env" "${HGK_ROOT}/20_機構｜Mekhane/_src｜ソースコード/mekhane/ergasterion/n8n/.env"
    log ".env ファイルを各 Docker プロジェクトルートにコピー"
  else
    log "WARNING: ${OIKOS_ROOT}/.env が見つかりません。VPN 認証に失敗する可能性があります"
  fi

  # SearXNG + Gluetun VPN
  cd "${HGK_ROOT}/20_機構｜Mekhane/_src｜ソースコード/mekhane/periskope/docker"
  docker compose up -d
  log "SearXNG + Gluetun VPN 起動完了"

  # n8n
  cd "${HGK_ROOT}/20_機構｜Mekhane/_src｜ソースコード/mekhane/ergasterion/n8n"
  docker compose up -d
  log "n8n 起動完了"
}

# ─── Phase 8: hgk-vite systemd サービス ───
setup_hgk_vite() {
  log "Phase 8: hgk-vite systemd サービスの設定"
  local HGK_APP="${HGK_ROOT}/40_応用｜Organon/_src｜ソースコード/hgk"

  if [ -d "${HGK_APP}" ]; then
    cd "${HGK_APP}"
    npm install --silent

    sudo tee /etc/systemd/system/hgk-vite.service > /dev/null << VITE
[Unit]
Description=HGK Vite Dev Server — Hegemonikón Frontend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${USER}
Group=${USER}
WorkingDirectory=${HGK_APP}
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/npx vite --host
Restart=on-failure
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hgk-vite
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=${OIKOS_ROOT} /tmp
PrivateTmp=true

[Install]
WantedBy=multi-user.target
VITE
    sudo systemctl daemon-reload
    sudo systemctl enable hgk-vite
    sudo systemctl start hgk-vite
    log "Phase 8 完了"
  else
    log "WARNING: hgk ディレクトリが見つかりません: ${HGK_APP}"
  fi
}

# ─── 検証 ───
verify() {
  log "=== 検証 ==="
  echo "Docker:     $(docker --version 2>/dev/null || echo 'NOT FOUND')"
  echo "Node.js:    $(node --version 2>/dev/null || echo 'NOT FOUND')"
  echo "Syncthing:  $(syncthing --version 2>/dev/null | head -1 || echo 'NOT FOUND')"
  echo "Python:     $(python3 --version 2>/dev/null || echo 'NOT FOUND')"
  echo "venv pip:   $(.venv/bin/pip --version 2>/dev/null || echo 'NOT FOUND')"
  echo ""

  echo "Docker containers:"
  docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "  (no containers)"
  echo ""

  echo "systemd services:"
  systemctl is-active hgk-vite 2>/dev/null || echo "  hgk-vite: not active"
  echo ""

  echo "Sleep targets:"
  systemctl is-enabled sleep.target suspend.target hibernate.target 2>&1 || true
  log "=== 検証完了 ==="
}

# ─── メイン ───
main() {
  log "HGK Backend セットアップ開始"
  install_base
  install_docker
  install_nodejs
  install_syncthing
  disable_sleep
  setup_venv
  start_docker_services
  setup_hgk_vite
  verify
  log "セットアップ完了"
}

main "$@"
