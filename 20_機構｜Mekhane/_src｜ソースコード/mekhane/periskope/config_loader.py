# PROOF: mekhane/periskope/config_loader.py
# PURPOSE: periskope モジュールの設定管理 (config_loader)
"""Periskopē config loader — shared across engine and searchers.

Extracted from engine.py to avoid circular imports (H6).
"""
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).parent / "config.yaml"
_cached_config: dict | None = None


# PURPOSE: [L2-auto] load_config の関数定義
def load_config() -> dict:
    """Load config.yaml from periskope package directory.

    Caches the result after first load for performance.
    """
    global _cached_config
    if _cached_config is not None:
        return _cached_config
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            _cached_config = yaml.safe_load(f) or {}
    else:
        _cached_config = {}
    return _cached_config


# PURPOSE: [L2-auto] reload_config の関数定義
def reload_config() -> dict:
    """Force reload config (e.g. after editing config.yaml)."""
    global _cached_config
    _cached_config = None
    return load_config()
