from __future__ import annotations
"""
PURPOSE: Periskopē プロンプトファイルの共通ローダー。
Týpos v8 DSL ファイルを Markdown 形式にコンパイルし、LLM プロンプトとして使用する。
"""


import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PROMPT_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Týpos .typos ファイルからプロンプトをコンパイルする。

    Args:
        name: プロンプトファイル名 (例: "phi3_classify_query.typos")

    Returns:
        コンパイル済み Markdown 文字列。失敗時は空文字列。
    """
    try:
        from mekhane.ergasterion.typos.typos import parse_file
        pf = parse_file(str(_PROMPT_DIR / name))
        return pf.compile(format="markdown")
    except Exception as e:  # noqa: BLE001
        logger.warning("Týpos prompt %s load failed: %s", name, e)
        return ""
