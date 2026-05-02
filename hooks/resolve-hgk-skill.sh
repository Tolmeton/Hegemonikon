#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
PROJECT_CODEX_SKILLS_DIR="${REPO_ROOT}/.agents/skills"
PROJECT_SKILLS_DIR="${REPO_ROOT}/.claude/skills"
GLOBAL_CODEX_SKILLS_DIR="${HOME}/.agents/skills"
GLOBAL_SKILLS_DIR="${HOME}/.claude/skills"

usage() {
  cat <<'EOF'
Usage: bash hooks/resolve-hgk-skill.sh <skill-name>

Resolution order:
1. project .agents/skills/<name>/SKILL.md
2. global  ~/.agents/skills/<name>/SKILL.md
3. project .claude/skills/<name>/SKILL.md
4. global  ~/.claude/skills/<name>/SKILL.md
EOF
}

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 2
fi

skill_name="$1"

if [[ -f "${PROJECT_CODEX_SKILLS_DIR}/${skill_name}/SKILL.md" ]]; then
  printf '%s\n' "${PROJECT_CODEX_SKILLS_DIR}/${skill_name}/SKILL.md"
  exit 0
fi

if [[ -f "${GLOBAL_CODEX_SKILLS_DIR}/${skill_name}/SKILL.md" ]]; then
  printf '%s\n' "${GLOBAL_CODEX_SKILLS_DIR}/${skill_name}/SKILL.md"
  exit 0
fi

if [[ -f "${PROJECT_SKILLS_DIR}/${skill_name}/SKILL.md" ]]; then
  printf '%s\n' "${PROJECT_SKILLS_DIR}/${skill_name}/SKILL.md"
  exit 0
fi

if [[ -f "${GLOBAL_SKILLS_DIR}/${skill_name}/SKILL.md" ]]; then
  printf '%s\n' "${GLOBAL_SKILLS_DIR}/${skill_name}/SKILL.md"
  exit 0
fi

printf 'Skill not found: %s\n' "${skill_name}" >&2
exit 1
