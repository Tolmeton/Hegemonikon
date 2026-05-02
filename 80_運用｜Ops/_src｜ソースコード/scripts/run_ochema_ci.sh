#!/usr/bin/env bash
# PURPOSE: Ochema CI テストパイプライン (C8)
# provision_state_db / DummyExtServer 不要のモックテストのみ実行
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "═══════════════════════════════════════════"
echo "  Ochema CI Test Pipeline (C8)"
echo "  $(date -Iseconds)"
echo "═══════════════════════════════════════════"
echo ""

# LS バイナリ / API キー不要のテストのみ実行
# test_k9_auth_e2e.py は @pytest.mark.skip でデフォルトスキップ
# test_f0_manual.py, test_ls_chat_e2e.py は手動テスト (skip マーク付き)
TEST_DIR="mekhane/ochema/tests"
FAILED=0

echo "▸ Phase 1: Unit Tests (mock-based)"
echo "-------------------------------------------"

# // turbo
PYTHONPATH=. .venv/bin/python -m pytest "$TEST_DIR" \
    -x --tb=short -q \
    --ignore="$TEST_DIR/__pycache__" \
    2>&1 || FAILED=1

echo ""
echo "═══════════════════════════════════════════"
if [[ $FAILED -eq 0 ]]; then
    echo "  ✅ All Ochema CI tests PASSED"
else
    echo "  ❌ Ochema CI tests FAILED"
fi
echo "═══════════════════════════════════════════"

exit $FAILED
