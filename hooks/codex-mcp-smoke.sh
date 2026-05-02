#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PS1_PATH="$SCRIPT_DIR/codex-mcp-smoke.ps1"

if command -v pwsh >/dev/null 2>&1; then
  exec pwsh -NoLogo -NoProfile -File "$PS1_PATH" "$@"
fi

if command -v powershell.exe >/dev/null 2>&1; then
  exec powershell.exe -NoLogo -NoProfile -File "$(cygpath -w "$PS1_PATH")" "$@"
fi

echo "pwsh or powershell.exe not found" >&2
exit 1
