#!/bin/bash
# ============================================================================
# HGK Backend — Systemd Timer セットアップ
# hgk-backend GCE インスタンス上で実行すること
# ============================================================================
set -euo pipefail

SYSTEMD_DIR="${HOME}/.config/systemd/user"
mkdir -p "$SYSTEMD_DIR"

echo "=== Creating systemd service & timer files ==="

# --- Digestor Service ---
cat > "$SYSTEMD_DIR/hgk-digestor.service" << 'EOF'
[Unit]
Description=HGK Digestor Pipeline
After=network.target

[Service]
Type=oneshot
WorkingDirectory=%h/oikos/01_ヘゲモニコン｜Hegemonikon
Environment="PYTHONPATH=%h/oikos/01_ヘゲモニコン｜Hegemonikon"
EnvironmentFile=%h/oikos/01_ヘゲモニコン｜Hegemonikon/.env
ExecStart=%h/oikos/01_ヘゲモニコン｜Hegemonikon/.venv/bin/python -m mekhane.ergasterion.digestor.pipeline --execute --max-papers 50 --max-candidates 10
TimeoutStartSec=600
EOF

# --- Digestor Timer (毎日 JST 09:00) ---
cat > "$SYSTEMD_DIR/hgk-digestor.timer" << 'EOF'
[Unit]
Description=Timer for HGK Digestor Pipeline

[Timer]
OnCalendar=*-*-* 00:00:00 UTC
Persistent=true

[Install]
WantedBy=timers.target
EOF
# NOTE: JST 09:00 = UTC 00:00

# --- Gnosis Index Service ---
cat > "$SYSTEMD_DIR/hgk-gnosis-index.service" << 'EOF'
[Unit]
Description=HGK Gnosis Index Update
After=network.target

[Service]
Type=oneshot
WorkingDirectory=%h/oikos/01_ヘゲモニコン｜Hegemonikon
Environment="PYTHONPATH=%h/oikos/01_ヘゲモニコン｜Hegemonikon"
EnvironmentFile=%h/oikos/01_ヘゲモニコン｜Hegemonikon/.env
ExecStart=%h/oikos/01_ヘゲモニコン｜Hegemonikon/.venv/bin/python scripts/gnosis_index_update.py --quiet
TimeoutStartSec=600
EOF

# --- Gnosis Index Timer (毎日 JST 03:00) ---
cat > "$SYSTEMD_DIR/hgk-gnosis-index.timer" << 'EOF'
[Unit]
Description=Timer for HGK Gnosis Index Update

[Timer]
OnCalendar=*-*-* 18:00:00 UTC
Persistent=true

[Install]
WantedBy=timers.target
EOF
# NOTE: JST 03:00 = UTC 18:00

# --- LS Token Provisioning Service ---
cat > "$SYSTEMD_DIR/hgk-ls-token.service" << 'EOF'
[Unit]
Description=HGK LS Token Provisioning (state.vscdb refresh)
After=network.target

[Service]
Type=oneshot
WorkingDirectory=%h/oikos/01_ヘゲモニコン｜Hegemonikon
Environment="PYTHONPATH=%h/oikos/01_ヘゲモニコン｜Hegemonikon"
EnvironmentFile=%h/oikos/01_ヘゲモニコン｜Hegemonikon/.env
ExecStart=%h/oikos/01_ヘゲモニコン｜Hegemonikon/.venv/bin/python scripts/provision_ls_token.py
TimeoutStartSec=60
EOF

# --- LS Token Timer (45分ごと) ---
cat > "$SYSTEMD_DIR/hgk-ls-token.timer" << 'EOF'
[Unit]
Description=Timer for HGK LS Token Provisioning (every 45min)

[Timer]
OnBootSec=5min
OnUnitActiveSec=45min
Persistent=true

[Install]
WantedBy=timers.target
EOF
# NOTE: ya29.* トークンは約1時間で失効。45分間隔で余裕を持つ

echo "=== Reloading systemd ==="
systemctl --user daemon-reload

echo "=== Enabling and starting timers ==="
systemctl --user enable --now hgk-digestor.timer
systemctl --user enable --now hgk-gnosis-index.timer
systemctl --user enable --now hgk-ls-token.timer

echo "=== Timer status ==="
systemctl --user list-timers --all | grep hgk

echo ""
echo "✅ Setup complete."
echo "   手動テスト: systemctl --user start hgk-digestor.service"
echo "   ログ確認:   journalctl --user -u hgk-digestor.service -f"
