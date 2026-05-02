# PROOF: mekhane/mcp/gateway_tools/search.py
# PURPOSE: mcp モジュールの search
"""Gateway tools: search domain."""
import time
import os
import sys
import signal


def register_search_tools(mcp):
    """Register search domain tools (1 tools)."""
    from mekhane.mcp.gateway_tools._utils import _traced, _get_policy, _trace_tool_call

    # =============================================================================
    # Paper Search (論文検索)
    # =============================================================================

    # PURPOSE: Semantic Scholar 経由で学術論文を検索する
    @mcp.tool()
    def hgk_paper_search(query: str, limit: int = 5) -> str:
        """
        学術論文を検索する (Semantic Scholar 経由)。
        Gnōsis 知識ベースの拡充や調査依頼に使用。

        Args:
            query: 検索クエリ (例: "active inference free energy")。最大 200 文字。
            limit: 最大結果数 (1-20、デフォルト 5)。
        """
        # Input validation (policy-driven)
        _start = time.time()
        max_q = _get_policy("hgk_paper_search", "max_query_size", 200)
        max_r = _get_policy("hgk_paper_search", "max_results", 20)
        if len(query) > max_q:
            _trace_tool_call("hgk_paper_search", len(query), (time.time() - _start) * 1000, False)
            return f"❌ クエリが長すぎます (最大 {max_q} 文字)"
        limit = max(1, min(max_r, limit))

        try:
            import signal

            # Anarkhia 対策: 30 秒タイムアウト
            # PURPOSE: [L2-auto] 内部処理: timeout_handler
            def _timeout_handler(signum, frame):
                raise TimeoutError("API タイムアウト (30秒)")

            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(30)

            try:
                from mekhane.pks.semantic_scholar import SemanticScholarClient
                client = SemanticScholarClient()
                results = client.search(query, limit=limit)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

            if not results:
                return f"🔍 '{query}' の検索結果: 0 件"

            lines = [f"## 🔍 論文検索: '{query}' ({len(results)} 件)\n"]
            for i, paper in enumerate(results, 1):
                # Paper は dataclass — 属性アクセスを使用 (.get() は使えない)
                title = getattr(paper, "title", "不明")
                year = getattr(paper, "year", None) or "?"
                citations = getattr(paper, "citation_count", 0)
                paper_authors = getattr(paper, "authors", []) or []
                authors = ", ".join(
                    a if isinstance(a, str) else str(a) for a in paper_authors[:3]
                )
                if len(paper_authors) > 3:
                    authors += " et al."
                lines.append(f"### {i}. {title} ({year})")
                lines.append(f"- **著者**: {authors}")
                lines.append(f"- **被引用数**: {citations}")
                abstract = getattr(paper, "abstract", "") or ""
                if abstract:
                    # Abstract を 200 文字に制限
                    if len(abstract) > 200:
                        abstract = abstract[:200] + "..."
                    lines.append(f"- **要旨**: {abstract}")
                lines.append("")

            _trace_tool_call("hgk_paper_search", len(query), (time.time() - _start) * 1000, True)
            return "\n".join(lines)
        except TimeoutError as e:
            _trace_tool_call("hgk_paper_search", len(query), (time.time() - _start) * 1000, False)
            return f"⏱️ {e}"
        except ImportError:
            _trace_tool_call("hgk_paper_search", len(query), (time.time() - _start) * 1000, False)
            return "❌ SemanticScholarClient が利用できません (import エラー)"
        except Exception as e:  # noqa: BLE001
            return f"❌ 論文検索エラー: {e}"
