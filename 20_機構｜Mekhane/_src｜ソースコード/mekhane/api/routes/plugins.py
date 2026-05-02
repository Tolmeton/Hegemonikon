from __future__ import annotations
# PROOF: F10 Plugin OS — API Routes
# PURPOSE: Plugin OS の REST API エンドポイント

"""
Plugin OS API Routes — /api/plugins

HGK の Plugin 管理 API。Phase 1 では Plugin #0 (HGK 自体) の情報を返す。
"""


import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from mekhane.plugin.loader import PluginLoader, PluginRegistry, get_hgk_root

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugins", tags=["plugins"])

# ── シングルトンレジストリ ──
_registry: PluginRegistry | None = None


def _get_registry() -> PluginRegistry:
    """PURPOSE: レジストリのシングルトン取得。初回アクセスで Plugin #0 をロード"""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        try:
            root = get_hgk_root()
            loader = PluginLoader(root)
            plugin = loader.load()
            _registry.register(plugin)
            logger.info(
                "Plugin #0 loaded: %s v%s (%d elements)",
                plugin.name,
                plugin.version,
                plugin.total_elements,
            )
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to load Plugin #0: %s", e)
    return _registry


# ── Endpoints ──


@router.get("")
async def list_plugins() -> dict[str, Any]:
    """PURPOSE: インストール済み Plugin 一覧を返す"""
    registry = _get_registry()
    return registry.to_dict()


@router.get("/{plugin_id}")
async def get_plugin(plugin_id: str) -> dict[str, Any]:
    """PURPOSE: 指定 Plugin の詳細を返す"""
    registry = _get_registry()
    plugin = registry.get(plugin_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")
    return plugin.to_dict()


@router.get("/{plugin_id}/elements")
async def get_plugin_elements(plugin_id: str) -> dict[str, Any]:
    """PURPOSE: 指定 Plugin の要素一覧を返す"""
    registry = _get_registry()
    plugin = registry.get(plugin_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")
    return {
        "plugin_id": plugin.id,
        "elements": {
            e.element_id: {
                "name": e.name,
                "count": e.count,
                "loaded": e.loaded,
                **e.details,
            }
            for e in plugin.elements
        },
        "total": plugin.total_elements,
    }


@router.post("/reload")
async def reload_plugins() -> dict[str, Any]:
    """PURPOSE: Plugin レジストリを再構築する"""
    global _registry
    _registry = None  # 次のアクセスで再ロード
    registry = _get_registry()
    return {
        "status": "reloaded",
        "plugins": registry.to_dict(),
    }
