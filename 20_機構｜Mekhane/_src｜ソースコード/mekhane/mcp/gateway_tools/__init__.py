"""Gateway tools package — ドメイン別ツール登録。

依存注入(DI)パターン:
  register_all(mcp) は hgk_gateway.py から mcp インスタンスを引数で受け取り、
  各ドメイン register_xxx_tools(mcp) に伝播する。
  これにより gateway_tools/ → hgk_gateway への逆インポート依存が解消され、
  __main__ の二重インポート問題が根本的に回避される。
"""


def register_all(mcp):
    """全ドメインのツールを mcp インスタンスに登録する (55 tools + CCL 3 tools = 58).

    Args:
        mcp: FastMCP インスタンス (hgk_gateway.py から注入)
    """
    from mekhane.mcp.gateway_tools.ccl import register_ccl_tools
    from mekhane.mcp.gateway_tools.knowledge import register_knowledge_tools
    from mekhane.mcp.gateway_tools.search import register_search_tools
    from mekhane.mcp.gateway_tools.digestor import register_digestor_tools
    from mekhane.mcp.gateway_tools.ochema import register_ochema_tools
    from mekhane.mcp.gateway_tools.sympatheia import register_sympatheia_tools
    from mekhane.mcp.gateway_tools.jules import register_jules_tools
    from mekhane.mcp.gateway_tools.periskope import register_periskope_tools
    from mekhane.mcp.gateway_tools.typos import register_typos_tools
    from mekhane.mcp.gateway_tools.hub import register_hub_tools
    from mekhane.mcp.gateway_tools.sekisho import register_sekisho_tools

    register_ccl_tools(mcp)
    register_knowledge_tools(mcp)
    register_search_tools(mcp)
    register_digestor_tools(mcp)
    register_ochema_tools(mcp)
    register_sympatheia_tools(mcp)
    register_jules_tools(mcp)
    register_periskope_tools(mcp)
    register_typos_tools(mcp)
    register_hub_tools(mcp)
    register_sekisho_tools(mcp)

