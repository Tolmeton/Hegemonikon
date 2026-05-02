# PROOF: F10 Plugin OS — Package Init
# PURPOSE: mekhane.plugin パッケージの公開 API を定義

"""
mekhane.plugin — HGK Plugin OS モジュール。

HGK 自体を Plugin #0 として認識し、将来的には外部 Plugin のロード・管理を行う。
"""

from mekhane.plugin.loader import (
    ElementCount,
    PluginInfo,
    PluginLoader,
    PluginRegistry,
    get_hgk_root,
    load_self,
)

__all__ = [
    "ElementCount",
    "PluginInfo",
    "PluginLoader",
    "PluginRegistry",
    "get_hgk_root",
    "load_self",
]
