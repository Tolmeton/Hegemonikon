#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../../.." && pwd)"
VENV_DIR="${HGK_MCP_RUNTIME_VENV:-${REPO_ROOT}/.tmp/mcp-runtime-venv}"
PYTHON_BIN="${VENV_DIR}/bin/python"
REQ_FILE="${REPO_ROOT}/20_機構｜Mekhane/_src｜ソースコード/requirements.txt"
runtime_extras=(
  google-auth-oauthlib
)

required_imports=(
  uvicorn
  starlette
  sse_starlette
  mcp
  httpx
  pydantic
  pydantic_settings
  dotenv
  yaml
  requests
  fastapi
  aiohttp
  google.genai
  googleapiclient
  google_auth_oauthlib
  openai
  playwright
)

ensure_uv() {
  if ! command -v uv >/dev/null 2>&1; then
    echo "FATAL: uv is required to create HGK MCP runtime venv" >&2
    exit 1
  fi
}

create_venv() {
  ensure_uv
  mkdir -p "$(dirname "$VENV_DIR")"
  uv venv "$VENV_DIR" --python 3.12 >/dev/null
}

install_requirements() {
  ensure_uv
  if [[ ! -f "$REQ_FILE" ]]; then
    echo "FATAL: MCP runtime requirements not found: $REQ_FILE" >&2
    exit 1
  fi
  uv pip install --python "$PYTHON_BIN" -r "$REQ_FILE"
  uv pip install --python "$PYTHON_BIN" "${runtime_extras[@]}"
}

smoke_imports() {
  "$PYTHON_BIN" - "$@" <<'PY'
import importlib
import sys

mods = sys.argv[1:]
missing = []
for mod in mods:
    try:
        importlib.import_module(mod)
    except Exception as exc:
        missing.append(f"{mod}: {exc.__class__.__name__}: {exc}")

if missing:
    print("HGK MCP runtime import smoke failed:", file=sys.stderr)
    for item in missing:
        print(f"  - {item}", file=sys.stderr)
    raise SystemExit(1)
PY
}

if [[ ! -x "$PYTHON_BIN" ]]; then
  create_venv
fi

if ! smoke_imports "${required_imports[@]}" >/dev/null 2>&1; then
  install_requirements
fi

smoke_imports "${required_imports[@]}"
printf '%s\n' "$PYTHON_BIN"
