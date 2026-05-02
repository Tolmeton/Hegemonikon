# PROOF: [L2/インフラ] <- mekhane/ergasterion/typos/ A0→Týpos ロードユーティリティ
# PURPOSE: Týpos (.prompt) ファイルの読み込みとコンパイルを共通化する

import logging
from pathlib import Path

from mekhane.ergasterion.typos.typos import parse_file

logger = logging.getLogger(__name__)

# プロンプトキャッシュ (モジュールレベル)
_PROMPT_CACHE: dict[str, str] = {}


def load_typos_prompt(prompt_name: str, fallback_text: str = "") -> str:
    """Load a Týpos prompt by name from the standard prompts directory with caching.
    
    Args:
        prompt_name: Base name of the prompt file (e.g. "tool_use" for "tool_use.prompt")
        fallback_text: Text to return if loading or compilation fails
        
    Returns:
        Markdown compiled string of the prompt, or fallback_text on failure.
    """
    if prompt_name in _PROMPT_CACHE:
        return _PROMPT_CACHE[prompt_name]
        
    try:
        prompt_path = Path(__file__).resolve().parent / "prompts" / f"{prompt_name}.prompt"
        pf = parse_file(str(prompt_path))
        compiled = pf.compile(format="markdown")
        _PROMPT_CACHE[prompt_name] = compiled
        return compiled
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to load prompt '%s': %s", prompt_name, e)
        _PROMPT_CACHE[prompt_name] = fallback_text
        return fallback_text
