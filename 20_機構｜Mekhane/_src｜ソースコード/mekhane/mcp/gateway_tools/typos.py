# PROOF: mekhane/mcp/gateway_tools/typos.py
# PURPOSE: mcp モジュールの typos
"""Gateway tools: typos domain."""
import time


def register_typos_tools(mcp):
    """Register typos domain tools (6 tools)."""
    from mekhane.mcp.gateway_tools._utils import _traced, _get_policy, _trace_tool_call, PROJECT_ROOT

    @mcp.tool()
    @_traced
    def hgk_typos_generate(requirements: str, domain: str = "", output_format: str = ".typos", model: str = "auto") -> str:
        """
        Generate Týpos code from natural language requirements. Returns structured prompt definition (.typos format).

        Args:
            requirements: Natural language description of what the prompt should do
            domain: Domain hint: 'technical', 'rag', or 'summarization'. Auto-detected if not specified.
            output_format: Output format: '.typos' or '.skill.md'
            model: Target LLM for generated prompt: 'auto' (default), 'gemini', 'claude', 'openai'
        """
        if not _ensure_typos_parser():
            return "❌ Týpos parser is not available"
        
        if not requirements:
            return "❌ requirements is required"

        if not domain:
            domain = _typos_detect_domain(requirements)
        domain = _typos_validate_domain(domain)
        policy = _typos_classify_task(requirements)

        code = _typos_generate(requirements, domain, output_format, model=model)

        lines = [
            "# [Hegemonikon] Týpos Generator v2.3\n",
            f"- **Requirements**: {requirements[:200]}",
            f"- **Detected Domain**: {domain}",
            f"- **Task Classification**: {policy['classification']} (confidence: {policy['confidence']})",
            f"- **Recommendation**: {policy['recommendation']}",
            "",
            "## Generated Code",
            "",
            "```typos",
            code,
            "```",
            "",
        ]

        if policy["classification"].startswith("divergent"):
            lines.extend([
                "> ⚠️ **警告**: このタスクは拡散的です。Týpos による構造化は多様性を阻害する可能性があります。",
                "> 自然言語での指示を検討してください。",
                "",
            ])

        return "\n".join(lines)
    @mcp.tool()
    @_traced
    def hgk_typos_parse(content: str = "", filepath: str = "") -> str:
        """
        Parse a .typos file into JSON AST. Supports v2.1 features: @rubric, @context, @if/@else, @extends, @mixin.
        """
        if not _ensure_typos_parser(): return "❌ Týpos parser is not available"
        import json
        try:
            source = _get_typos_content(content, filepath)
            parser = _PromptLangParser()
            ast = parser.parse(source)
            return json.dumps(ast, ensure_ascii=False, indent=2)
        except Exception as e:  # noqa: BLE001
            return f"❌ Parse Error: {e}"
    @mcp.tool()
    @_traced
    def hgk_typos_validate(content: str = "", filepath: str = "") -> str:
        """
        Validate .typos file syntax. Returns errors and warnings.
        """
        if not _ensure_typos_parser(): return "❌ Týpos parser is not available"
        try:
            source = _get_typos_content(content, filepath)
            parser = _PromptLangParser()
            ast = parser.parse(source)
            errors, warnings = parser.validate(ast)
        
            lines = []
            if not errors and not warnings:
                lines.append("✅ **Validation Passed**: No errors or warnings found.")
            if errors:
                lines.append("❌ **Errors found:**")
                for err in errors: lines.append(f"  - {err}")
            if warnings:
                lines.append("⚠️ **Warnings found:**")
                for warn in warnings: lines.append(f"  - {warn}")
            return "\n".join(lines)
        except Exception as e:  # noqa: BLE001
            return f"❌ Validation Error: {e}"
    @mcp.tool()
    @_traced
    def hgk_typos_compile(content: str = "", filepath: str = "", context: dict = None, model: str = "") -> str:
        """
        Compile .typos file to system prompt string (markdown format). Resolves @context, @if/@else, @extends, @mixin.
        """
        if not _ensure_typos_parser(): return "❌ Týpos parser is not available"
        try:
            source = _get_typos_content(content, filepath)
            ctx = context or {}
        
            # compile 実行のためのラッパー呼び出し等
            prompt_obj = _Prompt(name="inline_compile")
            parser = _PromptLangParser()
            ast = parser.parse(source)
        
            # 簡易コンパイル処理 (typos_mcp_server.py 準拠)
            prompt_obj.ast = ast
            prompt_obj._resolve_ast()
            text = prompt_obj.compile(context=ctx)
        
            if model:
                text = prompt_obj._apply_archetype(text, model)
            
            return text
        except Exception as e:  # noqa: BLE001
            return f"❌ Compilation Error: {e}"
    @mcp.tool()
    @_traced
    def hgk_typos_expand(content: str = "", filepath: str = "") -> str:
        """
        Expand .typos file to natural language prompt for human readability.
        """
        if not _ensure_typos_parser(): return "❌ Týpos parser is not available"
        try:
            source = _get_typos_content(content, filepath)
            prompt_obj = _Prompt(name="inline_expand")
            parser = _PromptLangParser()
            prompt_obj.ast = parser.parse(source)
            prompt_obj._resolve_ast()
            text = prompt_obj.expand()
            return text
        except Exception as e:  # noqa: BLE001
            return f"❌ Expansion Error: {e}"
    @mcp.tool()
    @_traced
    def hgk_typos_policy_check(task_description: str) -> str:
        """
        Check if a task is convergent (precision-oriented) or divergent (creativity-oriented).
        Based on FEP Function axiom (Explore ↔ Exploit).
        """
        if not _ensure_typos_parser(): return "❌ Týpos module is not available"
        import json
        policy = _typos_classify_task(task_description)
        return json.dumps(policy, ensure_ascii=False, indent=2)
