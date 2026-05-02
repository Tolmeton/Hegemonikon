#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ochema/acp_bridge.py A0→ACP クライアント統合ブリッジ
"""
ACP (Agent Client Protocol) クライアント。

Gemini CLI / Codex ACP を JSON-RPC over stdio で実行し、
ストリーミングイベントをそのまま Python 側へ流す。
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncGenerator

from mekhane.ochema.cli_agent_bridge import (
    _normalize_cli_request,
    _prepare_cli_cwd,
    _prepare_cli_env,
    _preferred_hgk_codex_repo,
)
from mekhane.ochema.gemini_bridge import _build_env as _build_gemini_env
from mekhane.ochema.gemini_bridge import _find_gemini
from mekhane.ochema.gemini_bridge import _normalize_gemini_model

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_INITIALIZE_PARAMS = {
    "protocolVersion": 1,
    "implementation": {"name": "hgk", "version": "1.0"},
    "capabilities": {},
}


class ACPError(RuntimeError):
    """ACP 実行時エラー。"""


@dataclass(slots=True)
class _RuntimeConfig:
    tool: str
    cmd_candidates: list[list[str]]
    cwd: str
    env: dict[str, str]
    project_dir: str | None
    model: str | None


class ACPProcess:
    """asyncio.subprocess で ACP エージェントを管理する。"""

    def __init__(self) -> None:
        self.process: asyncio.subprocess.Process | None = None
        self.session_id: str | None = None

    async def start(self, cmd: list[str], cwd: str, env: dict[str, str]) -> None:
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            env=env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def send(self, method: str, params: dict[str, Any], rpc_id: int) -> None:
        if self.process is None or self.process.stdin is None:
            raise ACPError("ACP process is not running")
        payload = {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "method": method,
            "params": params,
        }
        self.process.stdin.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
        await self.process.stdin.drain()

    async def read_line(self) -> dict[str, Any] | None:
        if self.process is None or self.process.stdout is None:
            raise ACPError("ACP process is not running")

        while True:
            raw = await self.process.stdout.readline()
            if not raw:
                return None
            text = raw.decode("utf-8", errors="replace").strip()
            if not text:
                continue
            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ACPError(f"invalid ACP JSON: {text[:200]}") from exc
            if not isinstance(data, dict):
                raise ACPError("invalid ACP payload: expected object")
            return data

    async def close(self) -> None:
        if self.process is None:
            return

        if self.process.returncode is None and self.session_id is not None:
            with contextlib.suppress(Exception):
                await self.send("session/end", {"sessionId": self.session_id}, rpc_id=9999)

        if self.process.stdin is not None and not self.process.stdin.is_closing():
            self.process.stdin.close()

        if self.process.returncode is None:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                self.process.kill()
                with contextlib.suppress(Exception):
                    await asyncio.wait_for(self.process.wait(), timeout=1.0)

        self.session_id = None


def _remaining_seconds(deadline: float) -> float:
    return max(deadline - asyncio.get_running_loop().time(), 0.1)


def _extract_rpc_error(payload: dict[str, Any]) -> str:
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message:
            return message
        return json.dumps(error, ensure_ascii=False)
    if error is not None:
        return str(error)
    return "ACP request failed"


async def _read_response(
    proc: ACPProcess,
    *,
    rpc_id: int,
    deadline: float,
) -> dict[str, Any]:
    while True:
        try:
            payload = await asyncio.wait_for(proc.read_line(), timeout=_remaining_seconds(deadline))
        except asyncio.TimeoutError as exc:
            raise ACPError("ACP timeout") from exc
        if payload is None:
            raise ACPError("process exited unexpectedly")
        if payload.get("id") != rpc_id:
            logger.debug("ignoring unexpected ACP payload while waiting id=%s: %s", rpc_id, payload)
            continue
        if "error" in payload:
            raise ACPError(_extract_rpc_error(payload))
        result = payload.get("result")
        if not isinstance(result, dict):
            raise ACPError("invalid ACP response: missing result object")
        return result


async def _drain_stderr(stream: asyncio.StreamReader | None) -> None:
    if stream is None:
        return
    while True:
        line = await stream.readline()
        if not line:
            return
        text = line.decode("utf-8", errors="replace").rstrip()
        if text:
            logger.debug("ACP stderr: %s", text)


def _resolve_runtime(tool: str, model: str | None, project_dir: str | None) -> _RuntimeConfig:
    if tool == "gemini-cli":
        gemini_path = _find_gemini() or shutil.which("gemini")
        if not gemini_path:
            raise ACPError("gemini CLI not found")
        resolved_project_dir = str(Path(project_dir).expanduser()) if project_dir else str(_PROJECT_ROOT)
        return _RuntimeConfig(
            tool=tool,
            cmd_candidates=[
                [gemini_path, "--experimental-acp"],
                [gemini_path, "--acp"],
            ],
            cwd=str(_PROJECT_ROOT),
            env=_build_gemini_env(),
            project_dir=resolved_project_dir,
            model=_normalize_gemini_model(model) or None,
        )

    if tool == "codex":
        npx_path = shutil.which("npx")
        if not npx_path:
            raise ACPError("npx not found")
        normalized_model = _normalize_codex_model(model)
        ascii_repo = _preferred_hgk_codex_repo()
        resolved_project_dir: str | None
        if project_dir:
            resolved_project_dir = str(Path(project_dir).expanduser())
        elif ascii_repo is not None:
            resolved_project_dir = str(ascii_repo)
        else:
            resolved_project_dir = None
        return _RuntimeConfig(
            tool=tool,
            cmd_candidates=[[npx_path, "@zed-industries/codex-acp"]],
            cwd=_prepare_cli_cwd("codex"),
            env=_prepare_cli_env("codex"),
            project_dir=resolved_project_dir,
            model=normalized_model,
        )

    raise ACPError(f"ACP unsupported tool: {tool}")


def _normalize_codex_model(model: str | None) -> str | None:
    if not model:
        return None
    model_name, _effort = _normalize_cli_request("codex", model)
    return model_name


def _build_session_new_params(
    runtime: _RuntimeConfig,
    *,
    include_model: bool = True,
) -> dict[str, Any]:
    if runtime.tool == "gemini-cli":
        params: dict[str, Any] = {
            "cwd": runtime.project_dir,
            "mcpServers": [],
        }
    else:
        params = {"projectDirectory": runtime.project_dir}
    if include_model and runtime.model:
        params["model"] = runtime.model
    return params


def _build_session_prompt_params(
    runtime: _RuntimeConfig,
    *,
    session_id: str,
    prompt: str,
) -> dict[str, Any]:
    content = [{"type": "text", "text": prompt}]
    if runtime.tool == "gemini-cli":
        return {"sessionId": session_id, "prompt": content}
    return {"sessionId": session_id, "input": content}


async def _start_initialized_process(
    runtime: _RuntimeConfig,
    cmd: list[str],
    *,
    deadline: float,
) -> tuple[ACPProcess, dict[str, Any], asyncio.Task[Any] | None]:
    proc = ACPProcess()
    stderr_task: asyncio.Task[Any] | None = None
    try:
        await proc.start(cmd, runtime.cwd, runtime.env)
        if proc.process is not None and proc.process.stderr is not None:
            stderr_task = asyncio.create_task(_drain_stderr(proc.process.stderr))
        init_result = await _send_and_wait(
            proc,
            method="initialize",
            params=_INITIALIZE_PARAMS,
            rpc_id=1,
            deadline=deadline,
        )
        return proc, init_result, stderr_task
    except Exception:
        if stderr_task is not None:
            stderr_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await stderr_task
        await proc.close()
        raise


async def _send_and_wait(
    proc: ACPProcess,
    *,
    method: str,
    params: dict[str, Any],
    rpc_id: int,
    deadline: float,
) -> dict[str, Any]:
    await proc.send(method, params, rpc_id)
    return await _read_response(proc, rpc_id=rpc_id, deadline=deadline)


async def _event_loop(
    proc: ACPProcess,
    *,
    prompt_rpc_id: int,
    deadline: float,
    started_at: float,
) -> AsyncGenerator[dict[str, Any], None]:
    accumulated: list[str] = []
    tool_calls: dict[str, dict[str, Any]] = {}

    while True:
        try:
            payload = await asyncio.wait_for(proc.read_line(), timeout=_remaining_seconds(deadline))
        except asyncio.TimeoutError:
            yield {"type": "error", "error": "ACP timeout"}
            return
        except ACPError as exc:
            yield {"type": "error", "error": str(exc)}
            return

        if payload is None:
            yield {"type": "error", "error": "process exited unexpectedly"}
            return

        if payload.get("method") == "session/update":
            params = payload.get("params") or {}
            update = params.get("update") or {}
            session_update = update.get("sessionUpdate")

            if session_update == "agent_message_chunk":
                content = update.get("content") or {}
                text = content.get("text", "")
                if text:
                    accumulated.append(text)
                    yield {"type": "text", "text": text}
                continue

            if session_update == "agent_thought_chunk":
                content = update.get("content") or {}
                text = content.get("text", "")
                yield {"type": "thought", "text": text}
                continue

            if session_update == "tool_call":
                tool_call_id = str(update.get("toolCallId", ""))
                entry = {
                    "tool_call_id": tool_call_id,
                    "title": update.get("title", ""),
                    "kind": update.get("kind"),
                    "status": update.get("status", "pending"),
                    "raw_input": update.get("rawInput", {}),
                    "raw_output": {},
                }
                tool_calls[tool_call_id] = entry
                yield {"type": "tool_call", **entry}
                continue

            if session_update == "tool_call_update":
                tool_call_id = str(update.get("toolCallId", ""))
                entry = tool_calls.setdefault(
                    tool_call_id,
                    {
                        "tool_call_id": tool_call_id,
                        "title": "",
                        "kind": None,
                        "status": None,
                        "raw_input": {},
                        "raw_output": {},
                    },
                )
                entry["status"] = update.get("status")
                entry["raw_output"] = update.get("rawOutput", {})
                yield {
                    "type": "tool_call_update",
                    "tool_call_id": tool_call_id,
                    "status": update.get("status"),
                    "raw_output": update.get("rawOutput", {}),
                }
                continue

            if session_update == "plan":
                yield {"type": "plan", "entries": update.get("entries", [])}
                continue

            logger.debug("ignoring unknown session/update: %s", update)
            continue

        if payload.get("id") == prompt_rpc_id:
            if "error" in payload:
                yield {"type": "error", "error": _extract_rpc_error(payload)}
                return
            result = payload.get("result") or {}
            yield {
                "type": "done",
                "stop_reason": result.get("stopReason", "end_turn"),
                "output": "".join(accumulated),
                "tool_calls": list(tool_calls.values()),
                "elapsed_s": round(time.time() - started_at, 2),
            }
            return

        logger.debug("ignoring unexpected ACP payload during prompt: %s", payload)


async def run_acp_agent(
    prompt: str,
    *,
    tool: str = "gemini-cli",
    model: str | None = None,
    timeout: int = 300,
    project_dir: str | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """ACP エージェントを実行し、イベントを逐次返す。"""
    started_at = time.time()
    deadline = asyncio.get_running_loop().time() + timeout

    try:
        runtime = _resolve_runtime(tool, model, project_dir)
    except ACPError as exc:
        yield {"type": "error", "error": str(exc)}
        return

    if runtime.project_dir is None:
        yield {"type": "error", "error": "codex ACP requires an ASCII alias repo or explicit project_dir"}
        return

    last_error = "ACP startup failed"
    for index, cmd in enumerate(runtime.cmd_candidates):
        proc: ACPProcess | None = None
        stderr_task: asyncio.Task[Any] | None = None
        try:
            proc, _init_result, stderr_task = await _start_initialized_process(
                runtime,
                cmd,
                deadline=deadline,
            )
            session_params = _build_session_new_params(runtime, include_model=True)

            try:
                session_result = await _send_and_wait(
                    proc,
                    method="session/new",
                    params=session_params,
                    rpc_id=2,
                    deadline=deadline,
                )
            except ACPError:
                if runtime.model:
                    session_result = await _send_and_wait(
                        proc,
                        method="session/new",
                        params=_build_session_new_params(runtime, include_model=False),
                        rpc_id=22,
                        deadline=deadline,
                    )
                else:
                    raise

            session_id = session_result.get("sessionId")
            if not isinstance(session_id, str) or not session_id:
                raise ACPError("session/new response missing sessionId")
            proc.session_id = session_id

            await proc.send(
                "session/prompt",
                _build_session_prompt_params(
                    runtime,
                    session_id=session_id,
                    prompt=prompt,
                ),
                rpc_id=3,
            )
            async for event in _event_loop(
                proc,
                prompt_rpc_id=3,
                deadline=deadline,
                started_at=started_at,
            ):
                yield event
                if event.get("type") in {"done", "error"}:
                    return
            return
        except ACPError as exc:
            last_error = str(exc)
            if index < len(runtime.cmd_candidates) - 1:
                logger.debug("ACP fallback: tool=%s cmd=%s error=%s", tool, cmd, exc)
                continue
            yield {"type": "error", "error": last_error}
            return
        finally:
            if proc is not None:
                await proc.close()
            if stderr_task is not None:
                stderr_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await stderr_task


def run_acp_agent_sync(
    prompt: str,
    *,
    tool: str = "gemini-cli",
    model: str | None = None,
    timeout: int = 300,
    project_dir: str | None = None,
) -> dict[str, Any]:
    """ACP エージェントを同期ラッパーで実行する。"""
    started_at = time.time()

    async def _runner() -> dict[str, Any]:
        async for event in run_acp_agent(
            prompt,
            tool=tool,
            model=model,
            timeout=timeout,
            project_dir=project_dir,
        ):
            if event.get("type") == "done":
                output = event.get("output", "")
                return {
                    "status": "ok",
                    "output": output,
                    "tool": tool,
                    "model": model or "default",
                    "elapsed_s": event.get("elapsed_s", 0.0),
                    "chars": len(output),
                    "tool_calls": event.get("tool_calls", []),
                }
            if event.get("type") == "error":
                return {
                    "status": "error",
                    "error": event.get("error", "ACP error"),
                    "tool": tool,
                    "model": model or "default",
                    "elapsed_s": round(time.time() - started_at, 2),
                }
        return {
            "status": "error",
            "error": "ACP stream ended without terminal event",
            "tool": tool,
            "model": model or "default",
            "elapsed_s": round(time.time() - started_at, 2),
        }

    return asyncio.run(_runner())


def get_status(tool: str, model: str | None = None) -> dict[str, Any]:
    """ACP の起動可否と initialize capabilities を返す。"""

    async def _runner() -> dict[str, Any]:
        try:
            runtime = _resolve_runtime(tool, model, project_dir=None)
        except ACPError as exc:
            return {
                "available": False,
                "cmd": None,
                "cwd": None,
                "project_dir": None,
                "capabilities": None,
                "fallback_used": False,
                "error": str(exc),
            }

        last_error: str | None = None
        for index, cmd in enumerate(runtime.cmd_candidates):
            proc: ACPProcess | None = None
            stderr_task: asyncio.Task[Any] | None = None
            try:
                deadline = asyncio.get_running_loop().time() + 15
                proc, init_result, stderr_task = await _start_initialized_process(
                    runtime,
                    cmd,
                    deadline=deadline,
                )
                return {
                    "available": True,
                    "cmd": cmd,
                    "cwd": runtime.cwd,
                    "project_dir": runtime.project_dir,
                    "capabilities": init_result.get("agentCapabilities"),
                    "fallback_used": index > 0,
                    "error": None,
                }
            except ACPError as exc:
                last_error = str(exc)
            finally:
                if proc is not None:
                    await proc.close()
                if stderr_task is not None:
                    stderr_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await stderr_task

        return {
            "available": False,
            "cmd": runtime.cmd_candidates[-1] if runtime.cmd_candidates else None,
            "cwd": runtime.cwd,
            "project_dir": runtime.project_dir,
            "capabilities": None,
            "fallback_used": len(runtime.cmd_candidates) > 1,
            "error": last_error,
        }

    return asyncio.run(_runner())
