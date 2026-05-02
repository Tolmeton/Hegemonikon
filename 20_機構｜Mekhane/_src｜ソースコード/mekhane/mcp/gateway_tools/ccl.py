# PROOF: [L2/インフラ] <- mekhane/mcp/gateway_tools/ccl.py A0→CCL 実行機能を MCP ツールとして公開
"""Gateway tools: CCL domain.

CCL (Cognitive Control Language) の解析・実行ツール群。
循環 import 防止: このモジュールのトップレベルでは hgk_gateway を import しない。
全ての参照は関数内で遅延 import する。
"""
import time


def register_ccl_tools(mcp):
    """CCL ドメインの 3 tools を mcp インスタンスに登録する。

    Args:
        mcp: FastMCP インスタンス (DI)
    """
    from mekhane.mcp.gateway_tools._utils import _traced, _get_policy, _trace_tool_call

    # =========================================================================
    # CCL Dispatch (構文解析)
    # =========================================================================

    # PURPOSE: CCL 式をパースし、構造を解析する
    @mcp.tool()
    @_traced
    def hgk_ccl_dispatch(ccl: str, context: str = "") -> str:
        """
        CCL (Cognitive Control Language) 式をパースし、構造を解析する。

        Args:
            ccl: CCL 式 (例: "/noe+", "/dia+~*/noe", "/sop")
            context: コンテキスト (precision routing 用)。省略可。
        """
        try:
            from hermeneus.src.dispatch import dispatch

            result = dispatch(ccl, context=context)

            if not result["success"]:
                return f"## ❌ CCL パースエラー\n\n**CCL**: `{ccl}`\n**エラー**: {result['error']}"

            # Precision-Aware Routing の結果を表示
            precision_section = ""
            ps = result.get("precision_strategy")
            if ps:
                precision_section = f"""

### Precision-Aware Routing
- **precision_ml**: {ps['precision_ml']:.4f}
- **戦略**: {ps['strategy']}
- **search_budget**: {ps['search_budget']}
- **gnosis_search**: {ps['gnosis_search']}"""

            return f"""## ✅ CCL ディスパッチ結果

**CCL**: `{ccl}`

### AST 構造
```
{result['tree']}
```

### 関連ワークフロー
{', '.join(f'`{wf}`' for wf in result['workflows'])}

### 実行計画
{result['plan_template']}{precision_section}"""
        except Exception as e:  # noqa: BLE001
            return f"## ❌ エラー\n\n`{e}`"

    # =========================================================================
    # CCL Execute (実行)
    # =========================================================================

    # PURPOSE: CCL 式を Hermēneus 経由で実行し、結果を返す
    @mcp.tool()
    def hgk_ccl_execute(ccl: str, context: str = "") -> str:
        """
        CCL 式を実行し、結果を返す。
        dispatch (構文解析のみ) とは異なり、ワークフローを実際に実行する。

        Args:
            ccl: CCL 式 (例: "/noe+", "/dia+~*/noe")。最大 500 文字。
            context: 実行コンテキスト (分析対象など)。最大 2000 文字。
        """
        # Input validation (policy-driven)
        _start = time.time()
        max_ccl = _get_policy("hgk_ccl_execute", "max_ccl_size", 500)
        max_ctx = _get_policy("hgk_ccl_execute", "max_context_size", 2000)
        if len(ccl) > max_ccl:
            _trace_tool_call("hgk_ccl_execute", len(ccl), (time.time() - _start) * 1000, False)
            return f"❌ CCL 式が長すぎます (最大 {max_ccl} 文字)"
        if len(context) > max_ctx:
            _trace_tool_call("hgk_ccl_execute", len(context), (time.time() - _start) * 1000, False)
            return f"❌ コンテキストが長すぎます (最大 {max_ctx} 文字)"

        try:
            from hermeneus.src.macro_executor import execute_and_explain
            result = execute_and_explain(ccl, context)
            # W12 Token Explosion 対策: 出力を最大 5000 文字に制限
            if len(result) > 5000:
                result = result[:5000] + "\n\n... (出力が 5000 文字を超えたため切り詰めました)"
            _trace_tool_call("hgk_ccl_execute", len(ccl) + len(context), (time.time() - _start) * 1000, True)
            return result
        except ImportError:
            return "❌ Hermēneus が利用できません (import エラー)"
        except Exception as e:  # noqa: BLE001
            return f"❌ CCL 実行エラー: {e}"

    # =========================================================================
    # CCL Run (パース + 実行のアトミック処理)
    # =========================================================================

    # PURPOSE: CCL 式をパースし、連続して実行する (θ12.1)
    @mcp.tool()
    def hgk_ccl_run(ccl: str, context: str = "") -> str:
        """
        Parse AND Execute CCL expressions (θ12.1).
        dispatch によるパース結果と、execute の実行結果を結合して返す。
        通常の CCL 実行には必ずこのツールを使用すること。

        Args:
            ccl: CCL 式 (例: "/noe+", "/dia+~*/noe")。最大 500 文字。
            context: 実行コンテキスト (分析対象など)。最大 2000 文字。
        """
        dispatch_result = hgk_ccl_dispatch(ccl, context=context)

        if "❌ CCL パースエラー" in dispatch_result:
            return dispatch_result

        execute_result = hgk_ccl_execute(ccl, context)

        return f"{dispatch_result}\n\n---\n\n{execute_result}"
