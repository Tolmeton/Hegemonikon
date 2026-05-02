#!/usr/bin/env bash
set -euo pipefail

TS_BIN="${TOKEN_SAVIOR_BIN:-$HOME/.local/token-savior-venv/bin/token-savior}"
DEFAULT_ROOT="/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane"

export WORKSPACE_ROOTS="${WORKSPACE_ROOTS:-$DEFAULT_ROOT}"
export TOKEN_SAVIOR_PROFILE="${TOKEN_SAVIOR_PROFILE:-nav}"
export TOKEN_SAVIOR_CLIENT="${TOKEN_SAVIOR_CLIENT:-codex}"

if [[ ! -x "$TS_BIN" ]]; then
  echo "token-savior binary not found: $TS_BIN" >&2
  echo "Install upstream first: python3 -m venv ~/.local/token-savior-venv && ~/.local/token-savior-venv/bin/pip install -e '.[mcp]'" >&2
  exit 127
fi

exec "$TS_BIN" "$@"
