# PROOF: [L2/インフラ] <- mekhane/ochema/cortex_tools.py A0→Function Calling エージェントループ
# PURPOSE: ask_with_tools (Tool Use) を CortexClient から分離
"""CortexTools — Function Calling agent loop.

Handles:
- ask_with_tools() — multi-turn tool use agent loop
- Dynamic tool loading via search_tools meta-tool (W4)
- Safety Gate for high-risk tools

Extracted from cortex_client.py for maintainability.
"""
from __future__ import annotations
from typing import Any, Optional


import logging
import time
from typing import TYPE_CHECKING, Callable

from mekhane.ochema.types import LLMResponse

if TYPE_CHECKING:
    from mekhane.ochema.cortex_api import CortexAPI

logger = logging.getLogger(__name__)


# --- CortexTools ---


# PURPOSE: Function Calling エージェントループを CortexClient から分離し、ツール実行の責任を集約する
class CortexTools:
    """Function Calling agent loop layer.

    Manages ask_with_tools() — the multi-turn agent loop where
    LLM requests tool calls and we execute them locally.
    Composed into CortexClient as self._tools.
    """

    def __init__(self, api: "CortexAPI") -> None:
        self._api = api

    # PURPOSE: Function Calling でローカルファイルを操作するエージェントループ。
    #   AI の認知自由の基盤。
    def ask_with_tools(
        self,
        message: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_instruction: Optional[str] = None,
        tools: Optional[list[dict]] = None,
        max_iterations: int = 10,
        thinking_budget: Optional[int] = None,
        timeout: float = 120.0,
        on_event: Optional[Callable[[str, dict], None]] = None,
        on_gate: Optional[Callable[[str, dict], bool]] = None,
    ) -> LLMResponse:
        """Send a prompt with tool use (Function Calling) support.

        Implements an agent loop:
        1. Send prompt + tool definitions to LLM
        2. If LLM returns functionCall → execute locally
        3. Send results back to LLM
        4. Repeat until LLM returns text (or max_iterations)

        Args:
            message: The prompt text
            model: Model name
            temperature: Temperature
            max_tokens: Max output tokens
            system_instruction: Optional system prompt
            tools: Tool definitions (default: TOOL_DEFINITIONS from tools.py)
            max_iterations: Max tool call rounds (default: 10)
            thinking_budget: Thinking budget for extended thinking models
            timeout: Per-API-call timeout
            on_event: Optional callback for streaming intermediate events.
                Called with (event_type, data_dict). Event types:
                "iteration" — new agent loop iteration started
                "tool_call" — LLM requested a tool call
                "tool_result" — tool execution completed
            on_gate: Optional Safety Gate callback for high-risk tools.
                Called with (tool_name, args) BEFORE execution.
                Returns True to approve, False to reject.
                Blocks the worker thread until approval is received.

        Returns:
            LLMResponse with final text (after all tool calls resolved)
        """
        def _emit(event_type: str, data: dict) -> None:
            if on_event is not None:
                try:
                    on_event(event_type, data)
                except Exception as _e:  # Intentional Catch-All (Callback Isolation)  # noqa: BLE001
                    logger.debug("Ignored exception: %s", _e)
                    pass  # Never let callback errors break the agent loop

        from mekhane.ochema.cortex_api import _BASE_URL
        from mekhane.ochema.tools import (
            TOOL_DEFINITIONS as DEFAULT_TOOLS,
            SEARCH_TOOLS_DEFINITION,
            GATED_TOOLS,
            execute_tool,
            execute_search_tools,
        )
        from hgk.api.tool_loop_guard import ToolLoopGuard
        import json as _json
        import os as _os
        import urllib.request as _urllib_request
        import urllib.error as _urllib_error

        # T-03: Tool Loop Guard — セッション単位のループ検出器
        guard = ToolLoopGuard()

        # W4: Core tools + search_tools (meta-tool) only at start.
        # Extended HGK tools are loaded dynamically via search_tools.
        if tools is not None:
            tool_defs = tools  # Caller-specified tools override lazy loading
        else:
            tool_defs = list(DEFAULT_TOOLS) + [SEARCH_TOOLS_DEFINITION]
        # Track dynamically loaded tool names to avoid duplicates
        _loaded_names: set[str] = {t["name"] for t in tool_defs}

        contents: list[dict[str, Any]] = [
            {"role": "user", "parts": [{"text": message}]}
        ]

        total_usage: dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        # --- Direct API フォールバック (GOOGLE_API_KEY 利用) ---
        # Cortex API (cloudcode-pa) が ADC/quota 問題で 403 になる場合、
        # GOOGLE_API_KEY 経由で generativelanguage.googleapis.com を直接呼ぶ。
        _use_direct_api = False  # Cortex API が 403 ならフォールバック
        _google_api_key = _os.environ.get("GOOGLE_API_KEY") or _os.environ.get("GEMINI_API_KEY")
        # .env からも取得を試みる
        if not _google_api_key:
            try:
                from mekhane.ochema.cortex_cache import CortexCache
                _cache = CortexCache()
                _google_api_key = _cache.api_key
            except ImportError as _e:
                logger.debug("Ignored exception: %s", _e)

        def _direct_api_call(
            contents_payload: list[dict],
            model_name: str,
            sys_instruction: Optional[str],
            temp: float,
            max_tok: int,
            thinking_bud: Optional[int],
            tool_definitions: Optional[list[dict]],
            api_key: str,
            call_timeout: float,
        ) -> dict:
            """generativelanguage.googleapis.com v1beta を直接呼ぶ。"""
            # モデル名の正規化: 'models/' プレフィクスが必要
            _model = model_name if model_name.startswith("models/") else f"models/{model_name}"
            _url = f"https://generativelanguage.googleapis.com/v1beta/{_model}:generateContent?key={api_key}"

            body: dict[str, Any] = {
                "contents": contents_payload,
                "generationConfig": {
                    "temperature": temp,
                    "maxOutputTokens": max_tok,
                },
            }
            if sys_instruction:
                body["systemInstruction"] = {
                    "role": "user",
                    "parts": [{"text": sys_instruction}],
                }
            if thinking_bud is not None:
                body["generationConfig"]["thinkingConfig"] = {
                    "thinkingBudget": thinking_bud
                }
            if tool_definitions:
                _ALLOWED = {"name", "description", "parameters"}
                sanitized = [
                    {k: v for k, v in t.items() if k in _ALLOWED}
                    for t in tool_definitions
                ]
                body["tools"] = [{"functionDeclarations": sanitized}]

            data = _json.dumps(body, ensure_ascii=False).encode("utf-8")
            req = _urllib_request.Request(
                _url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with _urllib_request.urlopen(req, timeout=call_timeout) as resp:
                    return _json.loads(resp.read().decode("utf-8"))
            except _urllib_error.HTTPError as http_err:
                err_body = http_err.read().decode("utf-8", errors="replace")
                logger.error("Direct API error %d: %s", http_err.code, err_body[:500])
                from mekhane.ochema.cortex_client import CortexAPIError
                raise CortexAPIError(
                    f"Direct API error: HTTP {http_err.code}",
                    status_code=http_err.code,
                    response_body=err_body,
                )

        # F2-Ochema: RAG Context Injection — 関連 KI を system context に注入
        try:
            from mekhane.agent_guard.apotheke import retrieve_context
            related_kis = retrieve_context(message, top_k=3)
            if related_kis:
                ki_context = "\n---\n".join(related_kis)
                ki_section = f"\n\n## 関連知識 (Apothēkē 自動取得)\n{ki_context}"
                if system_instruction:
                    system_instruction += ki_section
                else:
                    system_instruction = ki_section
                logger.info("F2-Ochema: injected %d related KIs into context", len(related_kis))
        except Exception as e:  # noqa: BLE001
            logger.debug("F2-Ochema: RAG injection skipped: %s", e)

        # F2-Ochema: Context Window size resolution (for eviction threshold)
        _cw_size = 1_000_000  # Default 1M tokens
        try:
            from mekhane.agent_guard.context_window import resolve_context_window
            _cw_size = resolve_context_window(model)
            logger.debug("F2-Ochema: context window = %d tokens", _cw_size)
        except ImportError as _e:
            logger.debug("Ignored exception: %s", _e)
            pass  # Use default

        for iteration in range(max_iterations):
            _emit("iteration", {"iteration": iteration + 1, "max": max_iterations})

            if _use_direct_api and _google_api_key:
                # Direct API モード: Cortex API をバイパスして Gemini を直接呼ぶ
                try:
                    response = _direct_api_call(
                        contents_payload=contents,
                        model_name=model,
                        sys_instruction=system_instruction,
                        temp=temperature,
                        max_tok=max_tokens,
                        thinking_bud=thinking_budget,
                        tool_definitions=tool_defs,
                        api_key=_google_api_key,
                        call_timeout=timeout,
                    )
                except Exception as direct_err:  # noqa: BLE001
                    logger.error("Direct API call failed: %s", direct_err)
                    raise
            else:
                # 通常モード: Cortex API (cloudcode-pa) を使う
                request_body = self._api._build_request(
                    contents=contents,
                    model=model,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    thinking_budget=thinking_budget,
                    tools=tool_defs,
                )

                from mekhane.ochema.cortex_client import CortexAPIError
                try:
                    response = self._api._call_api(
                        f"{_BASE_URL}:generateContent",
                        request_body,
                        timeout=timeout,
                    )
                except CortexAPIError as e:
                    if e.status_code == 403:
                        if _google_api_key:
                            # Cortex API が 403 → Direct API にフォールバック
                            logger.warning(
                                "ask_with_tools: Cortex API 403 (ADC/quota問題)。"
                                "GOOGLE_API_KEY で generativelanguage.googleapis.com にフォールバック。"
                            )
                            _use_direct_api = True
                            try:
                                response = _direct_api_call(
                                    contents_payload=contents,
                                    model_name=model,
                                    sys_instruction=system_instruction,
                                    temp=temperature,
                                    max_tok=max_tokens,
                                    thinking_bud=thinking_budget,
                                    tool_definitions=tool_defs,
                                    api_key=_google_api_key,
                                    call_timeout=timeout,
                                )
                            except Exception as direct_err:  # noqa: BLE001
                                logger.error("Direct API fallback also failed: %s", direct_err)
                                raise
                        else:
                            # API キーなし → 従来の project キャッシュクリア + リトライ
                            if iteration == 0:
                                logger.warning(
                                    "ask_with_tools: 403 on generateContent (iter=%d), "
                                    "clearing project cache and rebuilding request",
                                    iteration,
                                )
                                self._api._project = None
                                request_body = self._api._build_request(
                                    contents=contents,
                                    model=model,
                                    system_instruction=system_instruction,
                                    temperature=temperature,
                                    max_tokens=max_tokens,
                                    thinking_budget=thinking_budget,
                                    tools=tool_defs,
                                )
                                response = self._api._call_api(
                                    f"{_BASE_URL}:generateContent",
                                    request_body,
                                    timeout=timeout,
                                )
                            else:
                                raise
                    else:
                        raise

            result = self._api._parse_response(response)

            # Accumulate token usage
            for key in total_usage:
                total_usage[key] += result.token_usage.get(key, 0)

            # Check for function calls
            fn_calls = getattr(result, "function_calls", [])
            if not fn_calls:
                # No tool calls → final response
                result.token_usage = total_usage
                logger.info(
                    "Tool use completed: %d iterations, %d total tokens",
                    iteration + 1,
                    total_usage.get("total_tokens", 0),
                )
                return result

            # Execute tool calls and build response
            # Gemini 3 thought_signature: preserve raw model parts as-is
            # to maintain thinking context across multi-turn function calling.
            # See: https://ai.google.dev/gemini-api/docs/thought-signatures
            raw_parts = getattr(result, "raw_model_parts", [])
            user_parts: list[dict[str, Any]] = []

            for fc in fn_calls:
                name = fc.get("name", "")
                args = fc.get("args", {})

                logger.info("Tool call [%d/%d]: %s(%s)", iteration + 1, max_iterations, name, args)
                _emit("tool_call", {"name": name, "args": args})

                # T-03: Tool Loop Guard — ループ検出 (execute_tool 前)
                loop_result = guard.detect(name, args)
                if loop_result.stuck:
                    if loop_result.level == "critical":
                        logger.error("ToolLoopGuard BLOCKED: %s", loop_result.message)
                        tool_result = {
                            "error": f"Tool loop detected (CRITICAL): {loop_result.message}",
                        }
                        _emit("tool_result", {
                            "name": name,
                            "output": "",
                            "error": f"loop_detected:{loop_result.detector}",
                            "duration_ms": 0,
                        })
                        user_parts.append({
                            "functionResponse": {
                                "name": name,
                                "response": tool_result,
                            }
                        })
                        continue
                    else:
                        # warning — ログ出力のみ、実行は継続
                        logger.warning("ToolLoopGuard WARNING: %s", loop_result.message)

                # Phase 5: Safety Gate — block on high-risk tools until approved
                if on_gate is not None and name in GATED_TOOLS:
                    logger.info("Safety Gate: awaiting approval for %s", name)
                    try:
                        _approved = on_gate(name, args)
                    except Exception as _e:  # Intentional Catch-All (Safety Gate Isolation)  # noqa: BLE001
                        logger.debug("Ignored exception: %s", _e)
                        logger.info("Safety Gate: %s REJECTED by user", name)
                        tool_result = {"error": f"Tool '{name}' was rejected by user"}
                        _emit("tool_result", {
                            "name": name,
                            "output": "",
                            "error": "rejected_by_user",
                            "duration_ms": 0,
                        })
                        user_parts.append({
                            "functionResponse": {
                                "name": name,
                                "response": tool_result,
                            }
                        })
                        continue

                # T-03: ツール呼び出しを記録 (実行前)
                guard.record_call(name, args)

                # Execute the tool locally
                _t0 = time.monotonic()
                if name == "search_tools":
                    # W4: Meta-tool — discover and dynamically load extended tools
                    search_result = execute_search_tools(args)
                    tool_result = {"output": search_result["output"]}
                    # Merge newly discovered tools into tool_defs for next iteration
                    for new_tool in search_result.get("loaded_tools", []):
                        if new_tool["name"] not in _loaded_names:
                            tool_defs.append(new_tool)
                            _loaded_names.add(new_tool["name"])
                            logger.info("W4: Dynamically loaded tool: %s", new_tool["name"])
                else:
                    tool_result = execute_tool(name, args)
                _duration_ms = int((time.monotonic() - _t0) * 1000)

                # T-03: ツール結果を記録 (実行後)
                guard.record_outcome(name, args, result=tool_result)

                # Emit tool result (truncate output for SSE to avoid huge payloads)
                _output_str = str(tool_result.get("output", tool_result.get("error", "")))
                _emit("tool_result", {
                    "name": name,
                    "output": _output_str[:500] if len(_output_str) > 500 else _output_str,
                    "error": tool_result.get("error"),
                    "duration_ms": _duration_ms,
                })

                # Build function response part (our result)
                user_parts.append({
                    "functionResponse": {
                        "name": name,
                        "response": tool_result,
                    }
                })

            # Add model's original response (with thought_signatures intact)
            if raw_parts:
                contents.append({"role": "model", "parts": raw_parts})
            else:
                # Fallback for non-thinking models
                model_parts = [{"functionCall": fc} for fc in fn_calls]
                contents.append({"role": "model", "parts": model_parts})
            # Add our function responses
            contents.append({"role": "user", "parts": user_parts})

            # F2-Ochema: Eviction check — contents 膨張時の lossless eviction
            try:
                from mekhane.agent_guard.compaction import estimate_history_tokens
                from mekhane.agent_guard.apotheke import extract_evictable, run_postprocess
                _flat = " ".join(
                    p.get("text", "") for c in contents
                    for p in c.get("parts", []) if isinstance(p, dict) and "text" in p
                )
                _estimated = estimate_history_tokens(_flat)
                if _estimated > _cw_size * 0.7:
                    _eviction = extract_evictable(contents, keep_recent=6)
                    if _eviction.evicted:
                        logger.info(
                            "F2-Ochema: evicting %d messages (%d tokens est.)",
                            _eviction.evicted_turns, _estimated,
                        )
                        _emit("memory_eviction", {
                            "evicted": _eviction.evicted_turns,
                            "estimated_tokens": _estimated,
                        })
                        contents = _eviction.kept
                        # Async background: LLM × Týpos ナレッジ化
                        import asyncio as _aio
                        _session_id = f"awt_{id(guard)}"
                        try:
                            _loop = _aio.get_running_loop()
                            _loop.create_task(run_postprocess(
                                _eviction.evicted, _session_id,
                                ask_fn=self._api.ask,
                            ))
                        except RuntimeError:
                            # No running event loop — schedule for later
                            logger.debug("F2-Ochema: no event loop, KI化 deferred to /bye")
            except OSError as _evict_err:
                logger.debug("F2-Ochema: eviction check skipped: %s", _evict_err)

        # Max iterations reached
        logger.warning("ask_with_tools: max iterations (%d) reached", max_iterations)
        result = LLMResponse(
            text="[Tool Use] Maximum iterations reached. Last tool calls may be incomplete.",
            model=model,
            token_usage=total_usage,
        )
        return result
