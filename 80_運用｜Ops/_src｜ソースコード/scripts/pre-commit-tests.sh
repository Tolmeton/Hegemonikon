#!/usr/bin/env bash
# PROOF: [L2/CI] <- mekhane/ A0→テスト自動化→pre-commit hookが担う
# PURPOSE: Git commit 前に統合テスト + Kalon テストを実行
# USAGE: .git/hooks/pre-commit から呼び出される / 手動: bash scripts/pre-commit-tests.sh
#         --no-verify で commit 時にスキップ可能 (Git 標準)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_DIR}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔬 Hegemonikón Pre-commit Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Phase 0: Secret Detection — OAuth credentials leak prevention
echo ""
echo "🔐 Secret scan (staged files)..."
if git diff --cached --name-only | xargs grep -l "GOCSPX-\|681255809395-oo8ft2oprdrnp9e3aqf6av3hmdib135j" 2>/dev/null; then
    echo "❌ OAuth credentials detected in staged files! Commit blocked."
    echo "   Move secrets to ~/.config/cortex/oauth.json"
    exit 1
fi
echo "✅ No secrets detected"
echo ""

# Phase 1: Dendron Guard — 変更ファイルの PROOF/PURPOSE チェック
echo ""
echo "🛡️  Dendron Guard (staged files)..."
PYTHONPATH=. .venv/bin/python -m mekhane.dendron guard 2>&1
DENDRON_EXIT=$?
if [ $DENDRON_EXIT -ne 0 ]; then
    echo "⚠️  Dendron guard warnings detected (non-blocking)"
fi
echo ""

# Phase 1.5: Basanos Δε/Δt — kernel/mekhane 変更の構造的整合性チェック
KERNEL_CHANGED=$(git diff --cached --name-only | grep -c "^kernel/" || true)
MEKHANE_CHANGED=$(git diff --cached --name-only | grep -c "^mekhane/" || true)
if [ "$KERNEL_CHANGED" -gt 0 ] || [ "$MEKHANE_CHANGED" -gt 0 ]; then
    echo ""
    echo "🔍 Basanos Δε/Δt scan (kernel/mekhane changes detected)..."
    PYTHONPATH=. .venv/bin/python -m mekhane.basanos.l2.cli scan --type delta 2>&1 || true
    echo ""
fi

# Phase 1.7: Nous Sync Check — nous/ → nous/ の同期差分チェック (非ブロック)
if [ -f "${PROJECT_DIR}/scripts/sync_nous.py" ]; then
    echo ""
    echo "📂 Nous sync check (dry-run)..."
    SYNC_OUT=$(PYTHONPATH=. .venv/bin/python scripts/sync_nous.py 2>&1 | tail -1)
    if echo "$SYNC_OUT" | grep -q "合計 0"; then
        echo "✅ nous/ は同期済み"
    else
        echo "⚠️  $SYNC_OUT"
        echo "   同期するには: python scripts/sync_nous.py --apply"
    fi
    echo ""
fi

# Phase 2: Test Suite
PYTHONPATH=. .venv/bin/python -m pytest \
    mekhane/tests/ \
    mekhane/peira/tests/ \
    --ignore=mekhane/tests/test_guardian_integration.py \
    -x -q --timeout=60 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ All tests passed. Committing."
else
    echo ""
    echo "❌ Tests failed. Commit blocked."
    echo "   Use 'git commit --no-verify' to skip."
fi

exit $EXIT_CODE
