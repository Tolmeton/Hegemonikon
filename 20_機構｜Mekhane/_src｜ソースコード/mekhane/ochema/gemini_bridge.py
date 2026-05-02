#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ochema/gemini_bridge.py A0→CC↔Gemini CLI 統合ブリッジ
"""
CC↔Gemini CLI 統合ブリッジ — Claude Code から Gemini CLI を自然に呼び出す。

Hub MCP サーバーが不要。直接 subprocess で gemini-wrapper を呼び出す。
Hub 経由 (hub_execute gemini-cli) と独立した軽量パス。

使い方 (CC の Bash tool から):
  SRC="20_機構｜Mekhane/_src｜ソースコード"
  python -m mekhane.ochema.gemini_bridge ask "2+2は？"
  python -m mekhane.ochema.gemini_bridge research "FEPの最新動向" --mcp mneme
  python -m mekhane.ochema.gemini_bridge review --file path/to/diff.txt
  python -m mekhane.ochema.gemini_bridge batch "質問1" "質問2" "質問3"
  python -m mekhane.ochema.gemini_bridge status

Ochema-First 3-Layer Architecture:
  L0: Ochema (単発, ツールなし, 無料)
  L1: Gemini CLI + MCP (無料) ← このモジュール
  L2: CC Agent (API課金)

設計:
  - gemini-wrapper 優先 (gcloud config 汚染遮断)
  - gemini-rotate next で毎回アカウントローテーション (6垢負荷分散)
  - 429 検知時に自動ローテーション + リトライ (最大5回 = 全6垢カバー)
  - JSON 出力 (CC がパース可能)

TODO(DRY): hub_mcp_server.py _handle_gemini_cli と共通ロジック (env 構築・コマンド構築・
  429 判定) を _gemini_common.py に抽出する。Hub リファクタ時に一括対応。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# プロジェクトルート (cwd として使用)
_PROJECT_ROOT = Path(__file__).resolve().parents[4]  # mekhane/ochema → _src → Mekhane → HGK root
_TEXT_SUBPROCESS_KWARGS = {
    "text": True,
    "encoding": "utf-8",
    "errors": "replace",
}


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _find_gemini() -> str | None:
    """gemini-wrapper を優先的に検索。なければ gemini を検索。"""
    wrapper = os.path.expanduser("~/.local/bin/gemini-wrapper")
    if os.path.isfile(wrapper) and os.access(wrapper, os.X_OK):
        return wrapper
    return shutil.which("gemini-wrapper") or shutil.which("gemini")


def _find_rotate() -> str | None:
    """gemini-rotate を検索。"""
    rotate = os.path.expanduser("~/.local/bin/gemini-rotate")
    if os.path.isfile(rotate) and os.access(rotate, os.X_OK):
        return rotate
    return shutil.which("gemini-rotate")


def _build_env() -> dict[str, str]:
    """gcloud config 汚染遮断の環境変数を構築。"""
    return {
        **os.environ,
        "CLOUDSDK_CONFIG": "/dev/null",
        "GOOGLE_CLOUD_PROJECT": "",
        "GOOGLE_CLOUD_PROJECT_ID": "",
        "GCLOUD_PROJECT": "",
    }


def _rotate_account(rotate_path: str, env: dict[str, str]) -> bool:
    """アカウントをローテーション。成功 (returncode==0) なら True。"""
    try:
        result = subprocess.run(
            [rotate_path, "next"],
            capture_output=True, timeout=5,
            env=env,
            **_TEXT_SUBPROCESS_KWARGS,
        )
        return result.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def _get_current_account(rotate_path: str | None, env: dict[str, str]) -> str:
    """現在のアクティブアカウント名を取得。"""
    if not rotate_path:
        return "unknown"
    try:
        result = subprocess.run(
            [rotate_path, "status"],
            capture_output=True, timeout=5,
            env=env,
            **_TEXT_SUBPROCESS_KWARGS,
        )
        for line in result.stdout.splitlines():
            if line.startswith("Active:"):
                return line.split(":", 1)[1].strip()
    except Exception:  # noqa: BLE001
        pass
    return "unknown"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_gemini(
    prompt: str,
    *,
    model: str = "",
    sandbox: bool = True,
    mcp_servers: list[str] | None = None,
    timeout: int = 300,
    max_retries: int = 5,
    rotate_before: bool = True,
) -> dict:
    """Gemini CLI を実行し結果を返す。

    Args:
        prompt: プロンプト文字列
        model: モデル名 (空なら Gemini デフォルト)
        sandbox: True=--sandbox, False=--yolo
        mcp_servers: MCP サーバー名リスト (research 用)
        timeout: タイムアウト秒数
        max_retries: 429 リトライ回数
        rotate_before: 実行前にアカウントをローテーションするか

    Returns:
        dict: {status, output/error, model, account, elapsed_s, attempts}
    """
    gemini_path = _find_gemini()
    if not gemini_path:
        return {"status": "error", "error": "gemini CLI not found"}

    rotate_path = _find_rotate()
    env = _build_env()

    # 実行前ローテーション (6垢負荷分散)
    if rotate_before and rotate_path:
        _rotate_account(rotate_path, env)

    account = _get_current_account(rotate_path, env)

    # コマンド構築
    cmd = [gemini_path, "-p", prompt]
    if model:
        cmd.extend(["-m", model])
    cmd.append("--sandbox" if sandbox else "--yolo")
    if mcp_servers:
        cmd.extend(["--allowed-mcp-server-names", ",".join(mcp_servers)])

    start = time.time()

    for attempt in range(max_retries + 1):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout,
                env=env,
                cwd=str(_PROJECT_ROOT),
                **_TEXT_SUBPROCESS_KWARGS,
            )
            elapsed = time.time() - start
            stdout = (result.stdout or "").strip()
            stderr = (result.stderr or "").strip()

            if result.returncode != 0:
                # 429 quota exhaustion → rotate and retry
                if "429" in stderr and rotate_path:
                    if attempt < max_retries:
                        _rotate_account(rotate_path, env)
                        account = _get_current_account(rotate_path, env)
                    continue  # 最終 attempt でも continue → ループ終了 → exhaustion メッセージ

                return {
                    "status": "error",
                    "error": f"exit code {result.returncode}",
                    "stderr": stderr[:2000] if stderr else None,
                    "stdout": stdout[:2000] if stdout else None,
                    "account": account,
                    "elapsed_s": round(elapsed, 1),
                    "attempts": attempt + 1,
                }

            return {
                "status": "ok",
                "output": stdout,
                "model": model or "default",
                "account": account,
                "chars": len(stdout),
                "elapsed_s": round(elapsed, 1),
                "attempts": attempt + 1,
            }

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            return {
                "status": "error",
                "error": f"timeout ({timeout}s)",
                "account": account,
                "elapsed_s": round(elapsed, 1),
                "attempts": attempt + 1,
            }
        except Exception as e:  # noqa: BLE001
            elapsed = time.time() - start
            return {
                "status": "error",
                "error": str(e),
                "account": account,
                "elapsed_s": round(elapsed, 1),
                "attempts": attempt + 1,
            }

    # 全アカウント quota exhaustion
    elapsed = time.time() - start
    return {
        "status": "error",
        "error": f"all accounts exhausted ({max_retries} retries)",
        "account": account,
        "elapsed_s": round(elapsed, 1),
        "attempts": max_retries + 1,
    }


def run_batch(
    prompts: list[str],
    *,
    model: str = "",
    sandbox: bool = True,
    mcp_servers: list[str] | None = None,
    timeout: int = 300,
) -> list[dict]:
    """複数プロンプトを順次実行。各呼出しで自動ローテーション (6垢分散)。

    Args:
        prompts: プロンプトリスト
        model: モデル名
        sandbox: sandbox モード
        mcp_servers: MCP サーバーリスト
        timeout: 各呼出しのタイムアウト

    Returns:
        list[dict]: 各プロンプトの結果リスト
    """
    results = []
    for i, prompt in enumerate(prompts):
        result = run_gemini(
            prompt,
            model=model,
            sandbox=sandbox,
            mcp_servers=mcp_servers,
            timeout=timeout,
            rotate_before=True,
        )
        result["index"] = i
        result["prompt_preview"] = prompt[:80]
        results.append(result)
    return results


def run_review(
    content: str,
    *,
    focus: str = "",
    model: str = "",
) -> dict:
    """コードレビューを Gemini に依頼。

    Args:
        content: レビュー対象のコード/diff
        focus: レビューの焦点 (例: "security", "performance")
        model: モデル名

    Returns:
        dict: レビュー結果
    """
    parts = ["以下のコード/diffをレビューしてください。"]
    if focus:
        parts.append(f"焦点: {focus}")
    parts.append("問題点、改善提案、良い点を構造的に報告してください。")
    parts.append(f"---\n{content}\n---")
    review_prompt = "\n\n".join(parts)

    return run_gemini(review_prompt, model=model, sandbox=True)


def get_status() -> dict:
    """Gemini CLI + アカウント状態を取得。"""
    gemini_path = _find_gemini()
    rotate_path = _find_rotate()
    env = _build_env()

    info: dict = {
        "gemini_path": gemini_path,
        "rotate_path": rotate_path,
        "available": gemini_path is not None,
    }

    if rotate_path:
        try:
            result = subprocess.run(
                [rotate_path, "status"],
                capture_output=True, timeout=5, env=env,
                **_TEXT_SUBPROCESS_KWARGS,
            )
            status_output = result.stdout.strip()
            info["rotate_output"] = status_output
            # "Active: <name>" をパースしてアカウント名を抽出
            for line in status_output.splitlines():
                if line.startswith("Active:"):
                    info["account"] = line.split(":", 1)[1].strip()
                    break
            else:
                info["account"] = "unknown"
        except Exception as e:  # noqa: BLE001
            info["rotate_error"] = str(e)
            info["account"] = "unknown"

    return info


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cmd_ask(args: argparse.Namespace) -> None:
    result = run_gemini(
        args.prompt,
        model=args.model or "",
        sandbox=not args.yolo,
    )
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()


def _cmd_research(args: argparse.Namespace) -> None:
    mcp = args.mcp.split(",") if args.mcp else []
    result = run_gemini(
        args.prompt,
        model=args.model or "",
        sandbox=not args.yolo,
        mcp_servers=mcp,
    )
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()


def _cmd_review(args: argparse.Namespace) -> None:
    if args.file:
        content = Path(args.file).read_text()
    else:
        content = sys.stdin.read()
    result = run_review(content, focus=args.focus or "", model=args.model or "")
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()


def _cmd_batch(args: argparse.Namespace) -> None:
    results = run_batch(
        args.prompts,
        model=args.model or "",
        sandbox=not args.yolo,
    )
    json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
    print()


def _cmd_status(_args: argparse.Namespace) -> None:
    info = get_status()
    json.dump(info, sys.stdout, ensure_ascii=False, indent=2)
    print()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    parser = argparse.ArgumentParser(
        prog="gemini_bridge",
        description="CC↔Gemini CLI 統合ブリッジ (L1: 無料 Gemini CLI)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ask — 単発プロンプト
    p_ask = sub.add_parser("ask", help="単発プロンプト実行")
    p_ask.add_argument("prompt", help="プロンプト")
    p_ask.add_argument("-m", "--model", default="", help="モデル名")
    p_ask.add_argument("--yolo", action="store_true", help="--yolo モード (非sandbox)")
    p_ask.set_defaults(func=_cmd_ask)

    # research — MCP 付き調査
    p_res = sub.add_parser("research", help="MCP 付き調査実行")
    p_res.add_argument("prompt", help="プロンプト")
    p_res.add_argument("--mcp", default="", help="MCP サーバー (カンマ区切り)")
    p_res.add_argument("-m", "--model", default="", help="モデル名")
    p_res.add_argument("--yolo", action="store_true", help="--yolo モード")
    p_res.set_defaults(func=_cmd_research)

    # review — コードレビュー
    p_rev = sub.add_parser("review", help="コードレビュー依頼")
    p_rev.add_argument("--file", help="レビュー対象ファイル (省略時: stdin)")
    p_rev.add_argument("--focus", default="", help="レビュー焦点 (例: security)")
    p_rev.add_argument("-m", "--model", default="", help="モデル名")
    p_rev.set_defaults(func=_cmd_review)

    # batch — 複数プロンプト順次実行
    p_batch = sub.add_parser("batch", help="複数プロンプト順次実行 (6垢分散)")
    p_batch.add_argument("prompts", nargs="+", help="プロンプト群")
    p_batch.add_argument("-m", "--model", default="", help="モデル名")
    p_batch.add_argument("--yolo", action="store_true", help="--yolo モード")
    p_batch.set_defaults(func=_cmd_batch)

    # status — 状態確認
    p_stat = sub.add_parser("status", help="Gemini CLI + アカウント状態確認")
    p_stat.set_defaults(func=_cmd_status)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
