#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
IMAGE_NAME="${YUGAKU_BLIND_IMAGE:-yugaku-blind-cli:latest}"
RUNTIME="${YUGAKU_CONTAINER_RUNTIME:-}"
PROMPT_FILE="${YUGAKU_BLIND_PROMPT:-${WORKSPACE_DIR}/01_研究論文｜Papers/FEP分解型_blind_participant_prompt.md}"
OUT_DIR="${YUGAKU_BLIND_OUT:-${WORKSPACE_DIR}/01_研究論文｜Papers/blind_outputs}"
CLAUDE_HOME_VOLUME="${YUGAKU_BLIND_CLAUDE_HOME:-yugaku-blind-claude-home}"
CODEX_HOME_VOLUME="${YUGAKU_BLIND_CODEX_HOME:-yugaku-blind-codex-home}"
ENV_FILE="${YUGAKU_BLIND_ENV:-${WORKSPACE_DIR}/../../../.env}"
GEMINI_ENV_KEY="${YUGAKU_GEMINI_ENV_KEY:-GOOGLE_API_KEY}"
GEMINI_MODEL="${YUGAKU_GEMINI_MODEL:-gemini-3.1-flash-lite-preview}"

usage() {
  cat <<'USAGE'
Usage:
  blind-cli.sh build
  blind-cli.sh versions
  blind-cli.sh login claude
  blind-cli.sh login codex
  blind-cli.sh models gemini
  blind-cli.sh run gemini
  blind-cli.sh run claude
  blind-cli.sh run codex
  blind-cli.sh check-output <file>

Environment overrides:
  YUGAKU_CONTAINER_RUNTIME=podman|docker
  YUGAKU_BLIND_PROMPT=/absolute/path/to/prompt.md
  YUGAKU_BLIND_OUT=/absolute/path/to/output-dir
  YUGAKU_BLIND_IMAGE=image-name
  YUGAKU_BLIND_ENV=/absolute/path/to/.env
  YUGAKU_GEMINI_ENV_KEY=GOOGLE_API_KEY
  YUGAKU_GEMINI_MODEL=gemini-3.1-flash-lite-preview
USAGE
}

detect_runtime() {
  if [[ -n "$RUNTIME" ]]; then
    printf '%s\n' "$RUNTIME"
    return
  fi
  if command -v podman >/dev/null 2>&1; then
    printf 'podman\n'
    return
  fi
  if command -v docker >/dev/null 2>&1; then
    printf 'docker\n'
    return
  fi
  printf 'No podman or docker found.\n' >&2
  exit 1
}

runtime() {
  detect_runtime
}

home_volume_for() {
  case "$1" in
    claude) printf '%s\n' "$CLAUDE_HOME_VOLUME" ;;
    codex) printf '%s\n' "$CODEX_HOME_VOLUME" ;;
    *) printf 'Unknown provider: %s\n' "$1" >&2; exit 2 ;;
  esac
}

ensure_paths() {
  if [[ ! -f "$PROMPT_FILE" ]]; then
    printf 'Prompt file not found: %s\n' "$PROMPT_FILE" >&2
    exit 1
  fi
  mkdir -p "$OUT_DIR"
}

read_env_value() {
  local key="$1"
  local file="$2"
  local line
  local value
  if [[ ! -f "$file" ]]; then
    printf 'Env file not found: %s\n' "$file" >&2
    exit 1
  fi
  line="$(awk -v key="$key" '
    BEGIN { found = "" }
    $0 ~ "^[[:space:]]*" key "[[:space:]]*=" { found = $0 }
    END { print found }
  ' "$file")"
  if [[ -z "$line" ]]; then
    printf 'Key not found in env file: %s\n' "$key" >&2
    exit 1
  fi
  value="${line#*=}"
  value="${value%%#*}"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  value="${value%\"}"
  value="${value#\"}"
  value="${value%\'}"
  value="${value#\'}"
  if [[ -z "$value" ]]; then
    printf 'Key is empty in env file: %s\n' "$key" >&2
    exit 1
  fi
  printf '%s\n' "$value"
}

run_login() {
  local provider="$1"
  local rt
  local home_volume
  rt="$(runtime)"
  home_volume="$(home_volume_for "$provider")"
  ensure_paths
  "$rt" run --rm -it \
    -v "${home_volume}:/blind-home" \
    -v "${PROMPT_FILE}:/input/prompt.md:ro" \
    -v "${OUT_DIR}:/out:Z" \
    -v "${SCRIPT_DIR}:/runner:ro" \
    -w /work \
    "$IMAGE_NAME" \
    "login-${provider}"
}

run_provider() {
  local provider="$1"
  local rt
  local home_volume
  rt="$(runtime)"
  home_volume="$(home_volume_for "$provider")"
  ensure_paths
  "$rt" run --rm \
    -v "${home_volume}:/blind-home" \
    -v "${PROMPT_FILE}:/input/prompt.md:ro" \
    -v "${OUT_DIR}:/out:Z" \
    -v "${SCRIPT_DIR}:/runner:ro" \
    -w /work \
    "$IMAGE_NAME" \
    "run-${provider}"
}

run_gemini() {
  local rt
  local google_api_key
  rt="$(runtime)"
  ensure_paths
  google_api_key="$(read_env_value "$GEMINI_ENV_KEY" "$ENV_FILE")"
  GOOGLE_API_KEY="$google_api_key" GEMINI_MODEL="$GEMINI_MODEL" "$rt" run --rm \
    --env GOOGLE_API_KEY \
    --env GEMINI_MODEL \
    -v "${PROMPT_FILE}:/input/prompt.md:ro" \
    -v "${OUT_DIR}:/out:Z" \
    -v "${SCRIPT_DIR}:/runner:ro" \
    -w /work \
    "$IMAGE_NAME" \
    run-gemini
}

models_gemini() {
  local rt
  local google_api_key
  rt="$(runtime)"
  google_api_key="$(read_env_value "$GEMINI_ENV_KEY" "$ENV_FILE")"
  GOOGLE_API_KEY="$google_api_key" "$rt" run --rm \
    --env GOOGLE_API_KEY \
    -v "${SCRIPT_DIR}:/runner:ro" \
    "$IMAGE_NAME" \
    models-gemini
}

check_output() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    printf 'Output file not found: %s\n' "$file" >&2
    exit 1
  fi
  rg -n 'Hegemonikon|HGK|CCL|36 Poiesis|12 H-series|48-frame|ギリシャ語ラベル|skill 名|動詞名|本稿 §5|座標表' "$file" || true
}

cmd="${1:-}"
case "$cmd" in
  build)
    "$(runtime)" build -t "$IMAGE_NAME" "$SCRIPT_DIR"
    ;;
  versions)
    "$(runtime)" run --rm \
      -v "${SCRIPT_DIR}:/runner:ro" \
      "$IMAGE_NAME" \
      versions
    ;;
  login)
    run_login "${2:-}"
    ;;
  run)
    case "${2:-}" in
      gemini) run_gemini ;;
      claude|codex) run_provider "${2:-}" ;;
      *) printf 'Unknown run provider: %s\n' "${2:-}" >&2; exit 2 ;;
    esac
    ;;
  models)
    case "${2:-}" in
      gemini) models_gemini ;;
      *) printf 'Unknown models provider: %s\n' "${2:-}" >&2; exit 2 ;;
    esac
    ;;
  check-output)
    check_output "${2:-}"
    ;;
  -h|--help|help|"")
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
