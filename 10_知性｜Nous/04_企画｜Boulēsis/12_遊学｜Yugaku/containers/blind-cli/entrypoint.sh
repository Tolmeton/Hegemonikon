#!/usr/bin/env bash
set -euo pipefail

PROMPT_FILE="${PROMPT_FILE:-/input/prompt.md}"
OUT_DIR="${OUT_DIR:-/out}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-3.1-flash-lite-preview}"

extract_prompt() {
  awk '/^```text$/{flag=1;next}/^```$/{if(flag){exit}}flag' "$PROMPT_FILE"
}

timestamp_utc() {
  date -u +%Y%m%dT%H%M%SZ
}

write_header() {
  local provider="$1"
  local out="$2"
  {
    printf '# Blind participant response — %s\n\n' "$provider"
    printf -- '- timestamp_utc: `%s`\n' "$(timestamp_utc)"
    printf -- '- prompt_file_inside_container: `%s`\n' "$PROMPT_FILE"
    printf -- '- working_directory_inside_container: `%s`\n\n' "$(pwd)"
    printf '## Response\n\n'
  } > "$out"
}

run_claude() {
  local out
  local prompt
  out="${OUT_DIR}/claude_$(timestamp_utc).md"
  prompt="$(extract_prompt)"
  write_header "Claude Code CLI" "$out"
  claude \
    --print \
    --tools "" \
    --no-session-persistence \
    --disable-slash-commands \
    --strict-mcp-config \
    --mcp-config '{}' \
    "$prompt" >> "$out"
  printf '%s\n' "$out"
}

run_codex() {
  local out
  local prompt
  out="${OUT_DIR}/codex_$(timestamp_utc).md"
  prompt="$(extract_prompt)"
  write_header "Codex CLI" "$out"
  codex exec \
    -C /work \
    --sandbox read-only \
    --ask-for-approval never \
    "$prompt" >> "$out"
  printf '%s\n' "$out"
}

run_gemini() {
  local out
  out="${OUT_DIR}/gemini_${GEMINI_MODEL}_$(timestamp_utc).md"
  write_header "Gemini API ${GEMINI_MODEL}" "$out"
  node /runner/gemini-generate.mjs >> "$out"
  printf '%s\n' "$out"
}

models_gemini() {
  node /runner/gemini-models.mjs
}

case "${1:-}" in
  login-claude)
    exec claude
    ;;
  login-codex)
    exec codex login
    ;;
  run-claude)
    run_claude
    ;;
  run-codex)
    run_codex
    ;;
  run-gemini)
    run_gemini
    ;;
  models-gemini)
    models_gemini
    ;;
  versions)
    printf 'node: '
    node --version
    printf 'npm: '
    npm --version
    printf 'claude: '
    claude --version
    printf 'codex: '
    codex --version
    ;;
  *)
    cat <<'USAGE'
Usage:
  entrypoint.sh login-claude
  entrypoint.sh login-codex
  entrypoint.sh run-claude
  entrypoint.sh run-codex
  entrypoint.sh run-gemini
  entrypoint.sh models-gemini
  entrypoint.sh versions
USAGE
    exit 2
    ;;
esac
