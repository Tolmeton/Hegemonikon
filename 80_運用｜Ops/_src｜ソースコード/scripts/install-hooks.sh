#!/bin/bash
# install-hooks.sh — Git hooks をインストールするスクリプト
#
# Usage: ./scripts/install-hooks.sh
#
# pre-push hook をインストールし、push 前の Periskopē テスト自動実行を有効化。
# Syncthing/clone 時に .git/hooks/ が複製されないため、このスクリプトで復元する。

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "🔧 Git hooks をインストールしています..."

# pre-push hook
cat > "$HOOKS_DIR/pre-push" << 'HOOK_EOF'
#!/bin/bash
# Git pre-push hook: Run Periskopē MCP tests before push
set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

echo "🔍 Pre-push: Running Periskopē MCP tests..."

PYTHONPATH=. .venv/bin/python -m pytest \
    mekhane/mcp/tests/test_periskope_benchmark.py \
    mekhane/mcp/tests/test_periskope_handlers.py \
    --timeout=30 -q 2>&1

if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Push aborted."
    exit 1
fi

echo "✅ All tests passed. Pushing..."

# Hint: run ./scripts/reload-mcp-periskope.sh after code changes
# to reload the MCP server with updated code.
HOOK_EOF
chmod +x "$HOOKS_DIR/pre-push"
echo "   ✅ pre-push hook installed"

echo ""
echo "🎉 全 hooks インストール完了"
echo "   reload MCP: ./scripts/reload-mcp-periskope.sh"
