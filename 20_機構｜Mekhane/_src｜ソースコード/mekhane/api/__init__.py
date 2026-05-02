# PROOF: [L2/インフラ] <- mekhane/api/__init__.py
# PURPOSE: Hegemonikón Desktop App FastAPI バックエンド
"""
Hegemonikón API — mekhane モジュールの REST + MCP 統合サーバー

Vite dev server (port 1420) から /api proxy 経由で接続。
MCP クライアント (Claude.ai, ChatGPT) は /mcp パスで接続。
"""

__version__ = "0.2.0"
API_TITLE = "Hegemonikón API"
API_PREFIX = "/api"
DEFAULT_PORT = 9696
