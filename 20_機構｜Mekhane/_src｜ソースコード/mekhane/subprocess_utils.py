# PROOF: [L2/インフラ] <- mekhane/subprocess_utils.py A0→サブプロセスUTF-8保証ユーティリティ
# PURPOSE: Windows環境でのサブプロセスUTF-8エンコーディングを保証する共通ユーティリティ。
#          MiroFish simulation_runner.py L180-200, L430-520 の設計パターンをHGK用に再構成。
#          Mimēsis 随伴 D6: Windows UTF-8 環境変数注入。
"""サブプロセス実行の共通ユーティリティ。

MiroFish の simulation_runner.py から抽出した設計パターン:
- PYTHONUTF8=1 による Python サブプロセスの UTF-8 保証
- PYTHONIOENCODING=utf-8 によるフォールバック
- クロスプラットフォーム対応 (Windows / Unix)
"""

import os
import subprocess
import sys
from typing import Any


def get_utf8_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """UTF-8 保証付きの環境変数辞書を返す。

    Windows でサブプロセスを起動する際に UTF-8 エンコーディングを強制する。
    MiroFish simulation_runner.py L432: env['PYTHONUTF8'] = '1'

    Args:
        extra: 追加の環境変数。既存の環境変数を上書きする。

    Returns:
        UTF-8 保証付きの環境変数辞書。
    """
    env = os.environ.copy()

    # Python 3.7+ の UTF-8 モード強制
    # https://docs.python.org/3/using/cmdline.html#envvar-PYTHONUTF8
    env.setdefault("PYTHONUTF8", "1")

    # レガシーフォールバック (Python 3.6 以前にも効果あり)
    env.setdefault("PYTHONIOENCODING", "utf-8")

    if extra:
        env.update(extra)

    return env


def run_utf8(
    cmd: list[str] | str,
    *,
    timeout: int | None = 30,
    check: bool = False,
    capture_output: bool = True,
    text: bool = True,
    cwd: str | None = None,
    extra_env: dict[str, str] | None = None,
    **kwargs: Any,
) -> subprocess.CompletedProcess:
    """UTF-8 保証付きでサブプロセスを実行する。

    subprocess.run() のラッパー。Windows での UTF-8 エンコーディング問題を解消し、
    タイムアウトとエラーハンドリングを統一する。

    Args:
        cmd: 実行するコマンド。
        timeout: タイムアウト秒数。None で無制限。デフォルト30秒。
        check: True の場合、非ゼロ終了コードで CalledProcessError を発生。
        capture_output: stdout/stderr をキャプチャするか。
        text: テキストモード (str) で出力するか。
        cwd: 作業ディレクトリ。
        extra_env: 追加の環境変数。
        **kwargs: subprocess.run() に渡す追加引数。

    Returns:
        subprocess.CompletedProcess オブジェクト。
    """
    env = get_utf8_env(extra_env)

    # Windows: locale (cp932) では schtasks/PowerShell の UTF-8 出力が decode 失敗する
    run_kw: dict[str, Any] = dict(kwargs)
    if text and capture_output:
        run_kw.setdefault("encoding", "utf-8")
        run_kw.setdefault("errors", "replace")

    return subprocess.run(
        cmd,
        timeout=timeout,
        check=check,
        capture_output=capture_output,
        text=text,
        cwd=cwd,
        env=env,
        **run_kw,
    )


def is_windows() -> bool:
    """Windows 環境かどうかを判定する。"""
    return sys.platform == "win32"
