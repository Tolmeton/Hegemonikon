#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ochema/ 定時 LS ウォームアップ
# PURPOSE: 6 本の Antigravity LS に最小プロンプトを送り、5時間系の利用枠を定時に揃える
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

from mekhane.ochema.antigravity_client import AntigravityClient, LSInfo
from mekhane.ochema.service import CLAUDE_MODEL_MAP

logger = logging.getLogger("ls_warmup")

DEFAULT_INFO_PATH = Path.home() / ".gemini" / "antigravity" / "ls_daemon.json"
DEFAULT_PROMPT = "Reply with exactly one word: hello"
DEFAULT_MODEL = "claude-sonnet-4-6"


def _load_entries(info_path: Path) -> list[dict[str, Any]]:
    if not info_path.exists():
        raise FileNotFoundError(f"ls_daemon.json not found: {info_path}")

    data = json.loads(info_path.read_text())
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected ls_daemon.json shape: {type(data)!r}")
    return [entry for entry in data if isinstance(entry, dict)]


def _resolve_model(model: str) -> str:
    return CLAUDE_MODEL_MAP.get(model, model)


def _to_ls_info(entry: dict[str, Any]) -> LSInfo:
    return LSInfo(
        pid=int(entry.get("pid", 0) or 0),
        port=int(entry.get("port", 0) or 0),
        csrf=str(entry.get("csrf", "")),
        workspace=str(entry.get("workspace", "")),
        is_https=bool(entry.get("is_https", False)),
        host=str(entry.get("host", "127.0.0.1") or "127.0.0.1"),
        source=str(entry.get("source", "local") or "local"),
        tunnel_pid=int(entry.get("tunnel_pid", 0) or 0),
        remote_pid=int(entry.get("remote_pid", 0) or 0),
        remote_host=entry.get("remote_host"),
        remote_port=int(entry.get("remote_port", 0) or 0),
    )


def _select_entries(entries: list[dict[str, Any]], accounts: list[str], all_entries: bool) -> list[dict[str, Any]]:
    if all_entries:
        return entries
    if not accounts:
        raise RuntimeError("Specify --all or at least one --account")

    wanted = set(accounts)
    selected = [entry for entry in entries if str(entry.get("account", "")) in wanted]
    missing = [name for name in accounts if name not in {str(entry.get("account", "")) for entry in selected}]
    if missing:
        raise RuntimeError(f"Accounts not found in ls_daemon.json: {', '.join(missing)}")
    return selected


def warm_entry(entry: dict[str, Any], prompt: str, model: str, timeout: float) -> dict[str, Any]:
    info = _to_ls_info(entry)
    account = str(entry.get("account", "")) or f"slot:{info.workspace or info.port}"
    if info.port <= 0 or not info.csrf:
        raise RuntimeError(f"Invalid LS entry for account={account}: port/csrf missing")

    client = AntigravityClient(ls_info=info)
    started = time.monotonic()
    response = client.ask(prompt, model=model, timeout=timeout)
    elapsed = round(time.monotonic() - started, 2)
    text = (response.text or "").strip().replace("\n", " ")
    return {
        "account": account,
        "workspace": info.workspace,
        "port": info.port,
        "source": info.source,
        "remote_port": info.remote_port,
        "elapsed_sec": elapsed,
        "reply": text[:80],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Warm up HGK LS pool with a minimal Claude request")
    parser.add_argument("--info-path", default=str(DEFAULT_INFO_PATH), help="Path to ls_daemon.json")
    parser.add_argument("--all", action="store_true", help="Warm all LS entries in the file")
    parser.add_argument("--account", action="append", default=[], help="Target account name (repeatable)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Friendly model name or raw LS model enum")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Minimal prompt to send")
    parser.add_argument("--timeout", type=float, default=45.0, help="Per-request timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    info_path = Path(args.info_path).expanduser()
    model = _resolve_model(args.model)

    entries = _load_entries(info_path)
    selected = _select_entries(entries, args.account, args.all)

    logger.info(
        "Starting LS warmup: %d target(s), model=%s, info_path=%s",
        len(selected), model, info_path,
    )

    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for entry in selected:
        account = str(entry.get("account", "")) or str(entry.get("workspace", ""))
        try:
            result = warm_entry(entry, prompt=args.prompt, model=model, timeout=args.timeout)
            results.append(result)
            logger.info(
                "Warmup OK account=%s workspace=%s port=%s elapsed=%ss reply=%r",
                result["account"], result["workspace"], result["port"],
                result["elapsed_sec"], result["reply"],
            )
        except Exception as exc:  # noqa: BLE001
            failures.append({"account": account, "error": str(exc)})
            logger.error("Warmup FAILED account=%s: %s", account, exc)

    summary = {
        "ok": len(failures) == 0,
        "targets": len(selected),
        "succeeded": len(results),
        "failed": len(failures),
        "results": results,
        "failures": failures,
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(
            f"targets={summary['targets']} succeeded={summary['succeeded']} failed={summary['failed']}",
            file=sys.stdout,
        )

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
