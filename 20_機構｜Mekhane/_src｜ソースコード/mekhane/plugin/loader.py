from __future__ import annotations
# PROOF: F10 Plugin OS — Plugin Loader
# PURPOSE: plugin.yaml を解析し、HGK 自体を Plugin #0 として認識するローダー

"""
Plugin Loader — HGK Plugin OS の中核モジュール。

plugin.yaml を読み込み、10要素 (E1-E7 + X1-X4) を動的にカウント・検証する。
HGK 自体が「Plugin #0」として自己認識するための仕組み。
"""


import glob as glob_mod
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from mekhane.paths import HGK_ROOT


# ──────────────────────────────────────────────
# Data Models
# ──────────────────────────────────────────────


@dataclass
class ElementCount:
    """PURPOSE: 各要素のカウント結果を保持する"""

    name: str
    element_id: str  # E1-E7, X1-X4
    count: int
    loaded: bool
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginInfo:
    """PURPOSE: Plugin の全情報を保持する"""

    id: str
    name: str
    version: str
    description: str
    author: str
    path: Path
    enabled: bool = True
    elements: list[ElementCount] = field(default_factory=list)
    compatibility: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def total_elements(self) -> int:
        """PURPOSE: ロードされた要素の総数"""
        return sum(e.count for e in self.elements)

    def to_dict(self) -> dict[str, Any]:
        """PURPOSE: API レスポンス用の辞書変換"""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "path": str(self.path),
            "enabled": self.enabled,
            "elements": {
                e.element_id: {
                    "name": e.name,
                    "count": e.count,
                    "loaded": e.loaded,
                    **e.details,
                }
                for e in self.elements
            },
            "total_elements": self.total_elements,
            "compatibility": self.compatibility,
            "meta": self.meta,
        }


# ──────────────────────────────────────────────
# Plugin Loader
# ──────────────────────────────────────────────


class PluginLoader:
    """PURPOSE: plugin.yaml を解析し、Plugin 情報を構築する"""

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)
        self.manifest_path = self.root_dir / "plugin.yaml"

    def load(self) -> PluginInfo:
        """PURPOSE: plugin.yaml を読み込み、全要素をカウントして PluginInfo を返す"""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"plugin.yaml not found: {self.manifest_path}")

        with open(self.manifest_path, encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        elements = []

        # E1: Skills
        elements.append(self._count_skills(manifest.get("elements", {}).get("skills", {})))

        # E2: Commands (Workflows)
        elements.append(self._count_commands(manifest.get("elements", {}).get("commands", {})))

        # E3: Agents
        agents = manifest.get("elements", {}).get("agents", [])
        elements.append(
            ElementCount(
                name="Agents",
                element_id="E3",
                count=len(agents),
                loaded=True,
                details={"roles": [a.get("role", "") for a in agents]},
            )
        )

        # E4: Hooks
        hooks = manifest.get("elements", {}).get("hooks", [])
        elements.append(
            ElementCount(
                name="Hooks",
                element_id="E4",
                count=len(hooks),
                loaded=True,
                details={"events": [h.get("event", "") for h in hooks]},
            )
        )

        # E5: MCP Servers
        mcp = manifest.get("elements", {}).get("mcp_servers", {})
        servers = mcp.get("servers", [])
        elements.append(
            ElementCount(
                name="MCP Servers",
                element_id="E5",
                count=len(servers),
                loaded=True,
                details={"servers": servers},
            )
        )

        # E6: LSP Servers (Optional)
        lsp = manifest.get("elements", {}).get("lsp_servers", {})
        lsp_servers = lsp.get("servers", [])
        elements.append(
            ElementCount(
                name="LSP Servers",
                element_id="E6",
                count=len(lsp_servers),
                loaded=True,
                details={"optional": lsp.get("optional", True)},
            )
        )

        # E7: Settings
        settings_cfg = manifest.get("elements", {}).get("settings", {})
        settings_path = self.root_dir / settings_cfg.get("config", "")
        elements.append(
            ElementCount(
                name="Settings",
                element_id="E7",
                count=1 if settings_path.exists() else 0,
                loaded=settings_path.exists(),
                details={"config": settings_cfg.get("config", "")},
            )
        )

        # X1: CCL
        elements.append(self._count_ccl(manifest.get("extensions", {}).get("ccl", {})))

        # X2: Constraints
        elements.append(
            self._count_glob_element(
                manifest.get("extensions", {}).get("constraints", {}),
                name="Constraints",
                element_id="X2",
            )
        )

        # X3: State
        elements.append(self._count_state(manifest.get("extensions", {}).get("state", {})))

        # X4: Foundation
        elements.append(self._count_foundation(manifest.get("extensions", {}).get("foundation", {})))

        return PluginInfo(
            id=manifest.get("id", "unknown"),
            name=manifest.get("name", "Unknown"),
            version=manifest.get("version", "0.0.0"),
            description=manifest.get("description", ""),
            author=manifest.get("author", ""),
            path=self.root_dir,
            enabled=True,
            elements=elements,
            compatibility=manifest.get("compatibility", {}),
            meta=manifest.get("meta", {}),
        )

    # ──────────────────────────────────────────
    # Element Counters
    # ──────────────────────────────────────────

    def _count_skills(self, cfg: dict) -> ElementCount:
        """PURPOSE: Skills (SKILL.md) をカウント"""
        path = cfg.get("path", "")
        pattern = cfg.get("glob", "**/SKILL.md")
        full_path = self.root_dir / path

        count = 0
        if full_path.exists():
            count = len(list(full_path.glob(pattern)))

        # symlink 経由でもカウント
        symlink = cfg.get("symlink_from", "")
        if symlink and count == 0:
            sym_path = self.root_dir / symlink
            if sym_path.exists():
                count = len(list(sym_path.glob(pattern)))

        return ElementCount(
            name="Skills",
            element_id="E1",
            count=count,
            loaded=count > 0,
            details={"path": path, "symlink": symlink},
        )

    def _count_commands(self, cfg: dict) -> ElementCount:
        """PURPOSE: Commands (Workflows) をカウント"""
        path = cfg.get("path", "")
        pattern = cfg.get("glob", "**/*.md")
        full_path = self.root_dir / path

        wf_count = 0
        if full_path.exists():
            wf_count = len(list(full_path.glob(pattern)))

        # symlink 経由でもカウント
        symlink = cfg.get("symlink_from", "")
        if symlink and wf_count == 0:
            sym_path = self.root_dir / symlink
            if sym_path.exists():
                wf_count = len(list(sym_path.glob(pattern)))

        # CCL マクロのカウント
        ccl_count = 0
        ccl_path = cfg.get("ccl_macros_path", "")
        if ccl_path:
            ccl_full = self.root_dir / ccl_path
            if ccl_full.exists():
                ccl_count = len(list(ccl_full.glob("**/*.md")))

        return ElementCount(
            name="Commands",
            element_id="E2",
            count=wf_count + ccl_count,
            loaded=wf_count > 0,
            details={
                "workflows": wf_count,
                "ccl_macros": ccl_count,
                "includes_ccl_macros": cfg.get("includes_ccl_macros", False),
            },
        )

    def _count_ccl(self, cfg: dict) -> ElementCount:
        """PURPOSE: CCL 演算子・マクロをカウント"""
        macros_path = cfg.get("macros_path", "")
        macros_full = self.root_dir / macros_path

        macro_count = 0
        if macros_full.exists():
            macro_count = len(list(macros_full.glob("**/*.md")))

        operators_path = cfg.get("operators", "")
        has_operators = (self.root_dir / operators_path).exists() if operators_path else False

        return ElementCount(
            name="CCL",
            element_id="X1",
            count=macro_count + (1 if has_operators else 0),
            loaded=has_operators,
            details={
                "operators": operators_path,
                "macros": macro_count,
                "has_runtime": (self.root_dir / cfg.get("runtime", "")).is_dir()
                if cfg.get("runtime")
                else False,
            },
        )

    def _count_glob_element(self, cfg: dict, name: str, element_id: str) -> ElementCount:
        """PURPOSE: glob パターンで要素をカウント (汎用)"""
        path = cfg.get("path", "")
        pattern = cfg.get("glob", "**/*.md")
        full_path = self.root_dir / path

        count = 0
        if full_path.exists():
            count = len(list(full_path.glob(pattern)))

        # symlink fallback
        symlink = cfg.get("symlink_from", "")
        if symlink and count == 0:
            sym_path = self.root_dir / symlink
            if sym_path.exists():
                count = len(list(sym_path.glob(pattern)))

        return ElementCount(
            name=name,
            element_id=element_id,
            count=count,
            loaded=count > 0,
            details={"path": path, "always_on": cfg.get("always_on", False)},
        )

    def _count_state(self, cfg: dict) -> ElementCount:
        """PURPOSE: State 層のアイテム数をカウント"""
        total = 0
        details = {}

        for key in ["handoff_dir", "ki_dir", "session_dir", "gnosis_dir"]:
            dir_path = cfg.get(key, "")
            if dir_path:
                full = self.root_dir / dir_path
                if full.exists():
                    items = len(list(full.glob("*.md")))
                    total += items
                    details[key] = items
                else:
                    details[key] = 0

        return ElementCount(
            name="State",
            element_id="X3",
            count=total,
            loaded=total > 0,
            details=details,
        )

    def _count_foundation(self, cfg: dict) -> ElementCount:
        """PURPOSE: Foundation 層のファイル存在を検証"""
        files_found = 0
        details = {}

        for key in ["sacred_truth", "axiom_hierarchy", "kalon"]:
            file_path = cfg.get(key, "")
            if file_path:
                exists = (self.root_dir / file_path).exists()
                files_found += 1 if exists else 0
                details[key] = exists

        return ElementCount(
            name="Foundation",
            element_id="X4",
            count=files_found,
            loaded=files_found > 0,
            details=details,
        )


# ──────────────────────────────────────────────
# Plugin Registry
# ──────────────────────────────────────────────


class PluginRegistry:
    """PURPOSE: インストール済み Plugin を管理するレジストリ"""

    def __init__(self):
        self._plugins: dict[str, PluginInfo] = {}

    def register(self, plugin: PluginInfo) -> None:
        """PURPOSE: Plugin をレジストリに登録"""
        self._plugins[plugin.id] = plugin

    def get(self, plugin_id: str) -> PluginInfo | None:
        """PURPOSE: Plugin ID で検索"""
        return self._plugins.get(plugin_id)

    def list_all(self) -> list[PluginInfo]:
        """PURPOSE: 全 Plugin を返す"""
        return list(self._plugins.values())

    def to_dict(self) -> dict[str, Any]:
        """PURPOSE: API レスポンス用"""
        return {
            "plugins": [p.to_dict() for p in self._plugins.values()],
            "total": len(self._plugins),
        }


# ──────────────────────────────────────────────
# Convenience
# ──────────────────────────────────────────────

_HGK_ROOT = Path(__file__).resolve().parents[3]  # mekhane/plugin/ → _src/ → Organon/ → HGK root? No.


def get_hgk_root() -> Path:
    """PURPOSE: HGK プロジェクトルートを取得する (plugin.yaml の存在で判定)"""
    # 環境変数で明示指定
    env_root = os.environ.get("HGK_ROOT")
    if env_root:
        return Path(env_root)

    # カレントディレクトリから上に辿って plugin.yaml を探す
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "plugin.yaml").exists():
            return parent

    # フォールバック: 既知のパス
    known = HGK_ROOT
    if (known / "plugin.yaml").exists():
        return known

    raise FileNotFoundError("HGK root not found (no plugin.yaml in parent directories)")


def load_self() -> PluginInfo:
    """PURPOSE: HGK 自体を Plugin #0 としてロードする"""
    root = get_hgk_root()
    loader = PluginLoader(root)
    return loader.load()
