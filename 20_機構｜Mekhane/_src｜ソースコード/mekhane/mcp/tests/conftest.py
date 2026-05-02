# PROOF: テスト実行環境の PYTHONPATH 汚染を防止する conftest
# PURPOSE: ワークスペース内に複数の .venv (CCL-PL, Hyphē 等) が共存する環境で、
#          信頼済みプロジェクトの依存関係のみが使用されることを保証する。
# 根本原因: PYTHONPATH に他プロジェクトの .venv/site-packages が混入すると、
#          依存関係の解決が壊れてテストが偽陰性を出す (2026-03-20 発見)。
# 修正: 1. 信頼済み .venv (ワークスペースルート + _src) 以外を sys.path から除去
#       2. 信頼済み .venv の site-packages を最優先に挿入

import sys
from pathlib import Path

# _src|ソースコード / mekhane / mcp / tests / conftest.py → parents[3] = _src|ソースコード
_SRC_DIR = Path(__file__).resolve().parents[3]
# ワークスペースルート = _src の 2 階層上 (20_機構/Mekhane/_src → ヘゲモニコン)
_WORKSPACE_ROOT = _SRC_DIR.parent.parent

# 信頼済み .venv パス (mcp SDK はワークスペースルートの .venv にある)
_TRUSTED_VENVS = [
    _SRC_DIR / ".venv",
    _WORKSPACE_ROOT / ".venv",
]


def _sanitize_sys_path() -> None:
    """信頼済みプロジェクト以外の .venv site-packages を sys.path から除去し、
    信頼済みの site-packages を最優先に挿入する。

    これにより、CCL-PL 等の実験プロジェクトの依存関係が
    テスト実行に干渉することを防ぐ。
    """
    trusted_prefixes = [str(v) for v in _TRUSTED_VENVS]

    # --- Phase 1: 信頼済み以外の .venv を sys.path から除去 ---
    cleaned = []
    for p in sys.path:
        if ".venv" in p:
            if any(p.startswith(prefix) for prefix in trusted_prefixes):
                cleaned.append(p)  # 信頼済み: 残す
                continue
            else:
                continue  # 非信頼: 除去
        cleaned.append(p)
    sys.path[:] = cleaned

    # --- Phase 2: 信頼済み .venv の site-packages を追加 ---
    for venv_dir in _TRUSTED_VENVS:
        if not venv_dir.exists():
            continue
        for sp in venv_dir.glob("lib/python*/site-packages"):
            sp_str = str(sp)
            if sp_str not in sys.path:
                sys.path.insert(0, sp_str)
            break

    # --- Phase 3: ソースディレクトリ自体も確保 ---
    src_str = str(_SRC_DIR)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)


_sanitize_sys_path()
