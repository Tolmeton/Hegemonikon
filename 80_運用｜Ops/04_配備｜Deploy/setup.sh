#!/bin/bash
# dotfiles setup — oikos/dotfiles をシンボリックリンクで配置
# Usage: bash ~/oikos/dotfiles/setup.sh

set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "📁 Dotfiles dir: $DOTFILES_DIR"

# Helper: backup if real file, then symlink
link() {
    local src="$1" dst="$2"
    if [ -L "$dst" ]; then
        rm "$dst"
    elif [ -e "$dst" ]; then
        echo "  📦 backup: $dst → ${dst}.bak"
        mv "$dst" "${dst}.bak"
    fi
    mkdir -p "$(dirname "$dst")"
    ln -s "$src" "$dst"
    echo "  🔗 $dst → $src"
}

echo ""
echo "=== Home dotfiles ==="
link "$DOTFILES_DIR/.xprofile"    "$HOME/.xprofile"
link "$DOTFILES_DIR/.xsessionrc" "$HOME/.xsessionrc"
link "$DOTFILES_DIR/.xbindkeysrc" "$HOME/.xbindkeysrc"

echo ""
echo "=== Antigravity settings ==="
link "$DOTFILES_DIR/antigravity/settings.json" "$HOME/.config/Antigravity/User/settings.json"

echo ""
echo "=== systemd user units ==="
link "$DOTFILES_DIR/systemd/cpulimit-ls.service" "$HOME/.config/systemd/user/cpulimit-ls.service"
link "$DOTFILES_DIR/systemd/cpulimit-ls.timer"   "$HOME/.config/systemd/user/cpulimit-ls.timer"

echo ""
echo "=== systemd reload ==="
systemctl --user daemon-reload
systemctl --user enable --now cpulimit-ls.timer 2>/dev/null || true

echo ""
echo "✅ Done. Reload Antigravity (Ctrl+Shift+P → Reload Window) to apply."
