#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENSURE_ALIAS="${SCRIPT_DIR}/ensure-codex-alias.sh"
DEFAULT_ALIAS_PATH="$HOME/Sync/oikos/hgk-codex"
RAW_ALIAS_PATH="${HGK_CODEX_REPO:-}"
ALIAS_PATH="$DEFAULT_ALIAS_PATH"
MODEL=""
TIMEOUT="300"
PROMPT=""
CONTRACT_MODE="block"

usage() {
  cat <<'EOF'
Usage: bash hooks/delegate-codex.sh "<prompt>" [--model MODEL] [--timeout SECONDS] [--contract-mode MODE]

Run Codex through the HGK bridge with ASCII-only workspace surfaces.
EOF
}

if [[ -n "$RAW_ALIAS_PATH" ]] && LC_ALL=C grep -q '^[ -~]*$' <<<"$RAW_ALIAS_PATH"; then
  ALIAS_PATH="$RAW_ALIAS_PATH"
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      MODEL="${2:?--model requires a value}"
      shift 2
      ;;
    --timeout)
      TIMEOUT="${2:?--timeout requires a value}"
      shift 2
      ;;
    --contract-mode)
      CONTRACT_MODE="${2:?--contract-mode requires a value}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "$PROMPT" ]]; then
        PROMPT="$1"
        shift
      else
        echo "unexpected argument: $1" >&2
        usage >&2
        exit 2
      fi
      ;;
  esac
done

if [[ -z "$PROMPT" ]]; then
  echo "prompt is required" >&2
  usage >&2
  exit 2
fi

if [[ "$CONTRACT_MODE" != "block" && "$CONTRACT_MODE" != "warn" && "$CONTRACT_MODE" != "off" ]]; then
  echo "invalid --contract-mode: $CONTRACT_MODE" >&2
  usage >&2
  exit 2
fi

bash "$ENSURE_ALIAS" >/dev/null

export HGK_CODEX_REPO="$ALIAS_PATH"
export HGK_CODEX_HOME="${HGK_CODEX_HOME:-$HGK_CODEX_REPO/.tmp/codex-home}"
mkdir -p "$HGK_CODEX_HOME"

python_candidates=(
  "$HGK_CODEX_REPO/.venv/bin/python"
  "$HGK_CODEX_REPO/.venv/Scripts/python.exe"
  "$REPO_ROOT/.venv/bin/python"
  "$REPO_ROOT/.venv/Scripts/python.exe"
)
PYTHON_BIN=""
for candidate in "${python_candidates[@]}"; do
  if [[ -x "$candidate" ]]; then
    PYTHON_BIN="$candidate"
    break
  fi
done
if [[ -z "$PYTHON_BIN" ]]; then
  printf 'python not found in candidates:\n' >&2
  printf '  %s\n' "${python_candidates[@]}" >&2
  exit 1
fi

SRC_ROOT="$HGK_CODEX_REPO/20_機構｜Mekhane/_src｜ソースコード"
if [[ ! -d "$SRC_ROOT" ]]; then
  SRC_ROOT="$REPO_ROOT/20_機構｜Mekhane/_src｜ソースコード"
fi

RUN_HGK_CODEX_REPO="$HGK_CODEX_REPO"
RUN_HGK_CODEX_HOME="$HGK_CODEX_HOME"
RUN_SRC_ROOT="$SRC_ROOT"
if [[ "$PYTHON_BIN" == *.exe ]] && command -v cygpath >/dev/null 2>&1; then
  RUN_HGK_CODEX_REPO="$(cygpath -w "$HGK_CODEX_REPO")"
  RUN_HGK_CODEX_HOME="$(cygpath -w "$HGK_CODEX_HOME")"
  RUN_SRC_ROOT="$(cygpath -w "$SRC_ROOT")"
fi

cd "$HOME"
unset PYTHONHOME
unset PYTHONPATH
unset OLDPWD
export PWD="$HOME"

cmd=(
  "$PYTHON_BIN"
  -m
  mekhane.ochema.cli_agent_bridge
  ask
  codex
  "$PROMPT"
  --timeout
  "$TIMEOUT"
)
# NOTE: cli_agent_bridge ask no longer accepts --contract-mode (2026-05-02 SOURCE: ask --help).
# CONTRACT_MODE is still accepted at this script's CLI for forward compat but not forwarded.
: "${CONTRACT_MODE:=block}"

if [[ -n "$MODEL" ]]; then
  cmd+=(--model "$MODEL")
fi

result_json="$(
  MSYS2_ARG_CONV_EXCL="*" \
  MSYS_NO_PATHCONV=1 \
  HGK_CODEX_REPO="$RUN_HGK_CODEX_REPO" \
  HGK_CODEX_HOME="$RUN_HGK_CODEX_HOME" \
  PYTHONWARNINGS="${PYTHONWARNINGS:-ignore}" \
  PYTHONPATH="$RUN_SRC_ROOT" \
  "${cmd[@]}"
)"

status="$(printf '%s' "$result_json" | "$PYTHON_BIN" -c 'import json,sys; print(json.load(sys.stdin).get("status", "error"))')"
if [[ "$status" == "blocked" ]]; then
  blocked_payload="$(printf '%s' "$result_json" | "$PYTHON_BIN" -c 'import json,sys; data=json.load(sys.stdin); print(data.get("output", "").strip())')"
  if [[ -n "$blocked_payload" ]]; then
    printf '%s\n' "$blocked_payload"
  else
    printf '%s\n' "$result_json"
  fi
  exit 3
fi

if [[ "$status" == "error" ]]; then
  error_payload="$(printf '%s' "$result_json" | "$PYTHON_BIN" -c 'import json,sys; data=json.load(sys.stdin); print(data.get("error", "").strip())')"
  if [[ -n "$error_payload" ]]; then
    printf '%s\n' "$error_payload" >&2
  fi
  printf '%s\n' "$result_json"
  exit 1
fi

advisory_payload="$(printf '%s' "$result_json" | "$PYTHON_BIN" -c 'import json,sys; data=json.load(sys.stdin); report=data.get("contract_report") or {}; print(report.get("advisory_markdown", "").strip())')"
if [[ -n "$advisory_payload" ]]; then
  printf '%s\n' "$advisory_payload" >&2
fi

printf '%s\n' "$result_json"
