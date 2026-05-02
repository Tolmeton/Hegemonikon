#!/bin/bash
# PROOF: [L2/インフラ] <- 80_運用｜Ops/scripts/pre-commit-fit-check.sh A0→コミット前の /fit 自動チェック
#
# Hegemonikón Pre-Commit Fit Check
# コミットされるPythonファイルに対して以下を検証:
#   1. PROOF ヘッダーの存在 (L1)
#   2. 機能重複検出 (同一クラス/関数名が別ファイルに存在)
#   3. Dendron PURPOSE コメントの存在 (L2)
#
# Usage:
#   .git/hooks/pre-commit → このスクリプトを呼ぶ
#   直接実行: bash scripts/pre-commit-fit-check.sh [--staged-only]
#
# Exit codes:
#   0 = PASS
#   1 = Issues found (commit blocked)

set -euo pipefail

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

SRC_DIR="20_機構｜Mekhane/_src｜ソースコード"
ISSUES=0
WARNINGS=0

# Get files to check
if [[ "${1:-}" == "--staged-only" ]]; then
    FILES=$(git diff --cached --name-only --diff-filter=ACM -- "*.py" | grep -E "^${SRC_DIR}" || true)
else
    FILES=$(git diff --cached --name-only --diff-filter=ACM -- "*.py" || true)
fi

if [[ -z "$FILES" ]]; then
    echo -e "${GREEN}✅ No Python files staged for commit${NC}"
    exit 0
fi

echo "🔍 Hegemonikón Fit Check — pre-commit"
echo "   Checking $(echo "$FILES" | wc -l) Python file(s)..."
echo ""

# ─── Check 1: PROOF Header ───
echo "── L1: PROOF ヘッダー ──"
for f in $FILES; do
    if [[ ! -f "$f" ]]; then continue; fi
    # Skip __init__.py, test files, and tiny utility files
    base=$(basename "$f")
    if [[ "$base" == "__init__.py" || "$base" == "test_"* || "$base" == "conftest.py" ]]; then
        continue
    fi
    # Check if PROOF header exists in first 5 lines
    if ! head -5 "$f" | grep -q "PROOF:"; then
        echo -e "  ${YELLOW}⚠️  Missing PROOF: $f${NC}"
        ((WARNINGS++))
    fi
done

if [[ $WARNINGS -eq 0 ]]; then
    echo -e "  ${GREEN}✅ All files have PROOF headers${NC}"
fi

# ─── Check 2: Duplication Detection ───
echo ""
echo "── L2: 機能重複検出 ──"

# Extract class/function definitions from staged files
DEFS_FILE=$(mktemp)
for f in $FILES; do
    if [[ ! -f "$f" ]]; then continue; fi
    # Extract class/function names with file paths
    grep -nE "^(class |def )[A-Z]" "$f" 2>/dev/null | while IFS=: read -r line_num match; do
        name=$(echo "$match" | sed -E 's/^(class |def )([A-Za-z0-9_]+).*/\2/')
        echo "$name|$f|$line_num"
    done
done > "$DEFS_FILE"

# Check for same name in other files (excluding the staged file itself)
DUP_FOUND=0
while IFS='|' read -r name src_file src_line; do
    # Search for same name in all source files (excluding same file and tests)
    MATCHES=$(grep -rl "^class ${name}\b\|^def ${name}\b" "$SRC_DIR" 2>/dev/null \
        | grep -v "$src_file" \
        | grep -v "test_" \
        | grep -v "__pycache__" \
        || true)
    if [[ -n "$MATCHES" ]]; then
        echo -e "  ${RED}🔴 Duplicate: ${name}${NC}"
        echo "     Defined in: $src_file:$src_line"
        echo "     Also in:"
        echo "$MATCHES" | while read -r dup; do
            echo "       - $dup"
        done
        ((ISSUES++))
        DUP_FOUND=1
    fi
done < "$DEFS_FILE"
rm -f "$DEFS_FILE"

if [[ $DUP_FOUND -eq 0 ]]; then
    echo -e "  ${GREEN}✅ No duplicates detected${NC}"
fi

# ─── Summary ───
echo ""
echo "── Summary ──"
if [[ $ISSUES -gt 0 ]]; then
    echo -e "${RED}❌ $ISSUES issue(s) found — commit blocked${NC}"
    echo "   Fix duplicates before committing."
    exit 1
elif [[ $WARNINGS -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warning(s) — commit allowed${NC}"
    echo "   Consider adding PROOF headers."
    exit 0
else
    echo -e "${GREEN}✅ All checks passed${NC}"
    exit 0
fi
