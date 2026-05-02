#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CODEX_GLOBAL_SKILLS_DIR="${HOME}/.agents/skills"
GLOBAL_SKILLS_DIR="${HOME}/.claude/skills"

usage() {
  cat <<'EOF'
Usage:
  bash hooks/sync-codex-skill-bridges.sh --all
  bash hooks/sync-codex-skill-bridges.sh <skill> [<skill> ...]

Creates Codex-native global symlink bridges in ~/.agents/skills that point to ~/.claude/skills.
This is the OpenAI Codex custom-skill location. Existing real directories are left untouched.
EOF
}

bridge_one() {
  local skill_name="$1"
  local src="${GLOBAL_SKILLS_DIR}/${skill_name}"
  local dst="${CODEX_GLOBAL_SKILLS_DIR}/${skill_name}"

  if [[ ! -d "${src}" ]]; then
    printf 'missing:%s\n' "${skill_name}" >&2
    return 1
  fi

  if [[ -L "${dst}" ]]; then
    ln -sfn "${src}" "${dst}"
    printf 'linked:%s\n' "${skill_name}"
    return 0
  fi

  if [[ -e "${dst}" ]]; then
    printf 'skipped-existing:%s\n' "${skill_name}"
    return 0
  fi

  ln -s "${src}" "${dst}"
  printf 'linked:%s\n' "${skill_name}"
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 2
fi

mkdir -p "${CODEX_GLOBAL_SKILLS_DIR}"

declare -a skills=()
if [[ "$1" == "--all" ]]; then
  shift
  if [[ $# -ne 0 ]]; then
    usage >&2
    exit 2
  fi
  while IFS= read -r dir; do
    skills+=("$(basename "${dir}")")
  done < <(find "${GLOBAL_SKILLS_DIR}" -mindepth 1 -maxdepth 1 -type d | sort)
else
  skills=("$@")
fi

status=0
for skill_name in "${skills[@]}"; do
  if ! bridge_one "${skill_name}"; then
    status=1
  fi
done

exit "${status}"
