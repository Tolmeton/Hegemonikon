from __future__ import annotations
# PROOF: mekhane/kube/playwright_bridge.py
# PURPOSE: kube モジュールの playwright_bridge
"""
Kyvernetes PlaywrightBridge — Playwright の薄い抽象化層。

将来の CDP 直接化 (VISION_cdp_direct.md) に備え、
agent.py が Playwright API に直接依存しないようにする。
"""


import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class PageState:
    """Observe フェーズの出力: ブラウザの構造化された状態"""
    url: str
    title: str
    snapshot: str          # Accessibility Tree (テキスト形式)
    interactive_count: int  # インタラクティブ要素の数


@dataclass
class ActionResult:
    """Act フェーズの出力"""
    success: bool
    error: Optional[str] = None
    data: Optional[str] = None  # extract 時のテキスト


class PlaywrightBridge:
    """
    Playwright Python ライブラリの薄いラッパー。

    Kube Agent は このクラスだけを通じてブラウザを操作する。
    将来 CDP 直接に差し替える場合、このクラスだけを書き換えればよい。
    """

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._page = None

    async def launch(self, headless: bool = True) -> None:
        """ブラウザを起動する"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError(
                "playwright is not installed. Run: pip install playwright && playwright install chromium"
            )

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=headless)
        self._page = await self._browser.new_page()
        log.info("PlaywrightBridge: browser launched (headless=%s)", headless)

    async def close(self) -> None:
        """ブラウザを閉じてリソースを解放"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._page = None
        self._browser = None
        self._playwright = None

    # ── Observe ──────────────────────────────────────────────

    async def observe(self) -> PageState:
        """現在のページ状態を構造化して返す (OODA: Observe)"""
        page = self._ensure_page()
        
        # Python Playwright は page.accessibility を直接公開していないため、
        # CDP セッション経由で Accessibility Tree を取得する
        client = await page.context.new_cdp_session(page)
        tree_response = await client.send("Accessibility.getFullAXTree")
        nodes_flat = tree_response.get("nodes", [])
        
        # CDPのフラットなリストをネスト構造にビルド
        snapshot_tree = self._build_nested_tree(nodes_flat)

        tree_text = self._serialize_a11y_tree(snapshot_tree)
        interactive = self._count_interactive(snapshot_tree)

        return PageState(
            url=page.url,
            title=await page.title(),
            snapshot=tree_text,
            interactive_count=interactive,
        )

    # ── Act ──────────────────────────────────────────────────

    async def navigate(self, url: str) -> ActionResult:
        page = self._ensure_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            return ActionResult(success=True)
        except Exception as e:  # noqa: BLE001
            return ActionResult(success=False, error=str(e))

    async def click(self, selector: str) -> ActionResult:
        page = self._ensure_page()
        try:
            await page.click(selector, timeout=5000)
            return ActionResult(success=True)
        except Exception as e:  # noqa: BLE001
            return ActionResult(success=False, error=str(e))

    async def type_text(self, selector: str, text: str, submit: bool = False) -> ActionResult:
        page = self._ensure_page()
        try:
            await page.fill(selector, text, timeout=5000)
            if submit:
                await page.press(selector, "Enter")
            return ActionResult(success=True)
        except Exception as e:  # noqa: BLE001
            return ActionResult(success=False, error=str(e))

    async def scroll_down(self) -> ActionResult:
        page = self._ensure_page()
        try:
            await page.keyboard.press("PageDown")
            await asyncio.sleep(0.3)
            return ActionResult(success=True)
        except Exception as e:  # noqa: BLE001
            return ActionResult(success=False, error=str(e))

    async def scroll_up(self) -> ActionResult:
        page = self._ensure_page()
        try:
            await page.keyboard.press("PageUp")
            await asyncio.sleep(0.3)
            return ActionResult(success=True)
        except Exception as e:  # noqa: BLE001
            return ActionResult(success=False, error=str(e))

    async def go_back(self) -> ActionResult:
        page = self._ensure_page()
        try:
            await page.go_back(timeout=5000)
            return ActionResult(success=True)
        except Exception as e:  # noqa: BLE001
            return ActionResult(success=False, error=str(e))

    async def extract_text(self, selector: str) -> ActionResult:
        page = self._ensure_page()
        try:
            text = await page.text_content(selector, timeout=5000)
            return ActionResult(success=True, data=text)
        except Exception as e:  # noqa: BLE001
            return ActionResult(success=False, error=str(e))

    async def select_option(self, selector: str, value: str) -> ActionResult:
        page = self._ensure_page()
        try:
            await page.select_option(selector, value, timeout=5000)
            return ActionResult(success=True)
        except Exception as e:  # noqa: BLE001
            return ActionResult(success=False, error=str(e))

    async def wait_for(self, text: str, timeout: float = 10.0) -> ActionResult:
        page = self._ensure_page()
        try:
            await page.wait_for_selector(f"text={text}", timeout=timeout * 1000)
            return ActionResult(success=True)
        except Exception as e:  # noqa: BLE001
            return ActionResult(success=False, error=str(e))

    # ── Internal ─────────────────────────────────────────────

    def _ensure_page(self):
        if not self._page:
            raise RuntimeError("Browser not launched. Call launch() first.")
        return self._page

    def _build_nested_tree(self, nodes_flat: list[dict]) -> dict:
        """CDP Accessibility.getFullAXTree の結果をネスト構造に変換"""
        if not nodes_flat:
            return {}
        
        nodes_by_id = {str(n.get("nodeId")): n for n in nodes_flat}
        
        # parentId を持たないノードをルートとみなす
        root_id = None
        for n in nodes_flat:
            if "parentId" not in n:
                root_id = str(n.get("nodeId"))
                break
        
        if not root_id and nodes_flat:
            root_id = str(nodes_flat[0].get("nodeId"))

        def build(node_id: str) -> dict:
            if node_id not in nodes_by_id:
                return {}
            n = nodes_by_id[node_id]
            
            role = n.get("role", {}).get("value", "")
            name = n.get("name", {}).get("value", "")
            
            props = {}
            for p in n.get("properties", []):
                val = p.get("value", {}).get("value")
                if val is not None:
                    props[p["name"]] = val
                    
            children = []
            for child_id in n.get("childIds", []):
                child_node = build(str(child_id))
                if child_node:
                    children.append(child_node)
                    
            return {
                "role": role,
                "name": name,
                "value": props.get("value"),
                "checked": props.get("checked"),
                "disabled": props.get("disabled", False),
                "children": children
            }
            
        return build(root_id)

    def _serialize_a11y_tree(self, node: dict, depth: int = 0) -> str:
        """Accessibility Tree を テキスト形式に変換"""
        if not node:
            return ""

        lines = []
        indent = "  " * depth
        role = node.get("role", "")
        name = node.get("name", "")

        # interactive 要素のみフィルタ (depth 0 は常に含める)
        interesting_roles = {
            "link", "button", "textbox", "combobox", "checkbox",
            "radio", "menuitem", "tab", "heading", "img",
            "searchbox", "slider", "spinbutton", "switch",
        }

        if depth == 0 or role in interesting_roles or name:
            label = f'{role} "{name}"' if name else role
            props = []
            if node.get("value"):
                props.append(f'value="{node["value"]}"')
            if node.get("checked") is not None:
                props.append(f'checked={node["checked"]}')
            if node.get("disabled"):
                props.append("disabled")
            prop_str = f" [{', '.join(props)}]" if props else ""
            lines.append(f"{indent}- {label}{prop_str}")

        for child in node.get("children", []):
            lines.append(self._serialize_a11y_tree(child, depth + 1))

        return "\n".join(line for line in lines if line)

    def _count_interactive(self, node: dict) -> int:
        """インタラクティブ要素の総数をカウント"""
        count = 0
        interactive_roles = {
            "link", "button", "textbox", "combobox", "checkbox",
            "radio", "menuitem", "tab", "searchbox",
        }
        if node.get("role") in interactive_roles:
            count = 1
        for child in node.get("children", []):
            count += self._count_interactive(child)
        return count
