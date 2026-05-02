"""
Opsis Browser Backends — agent-browser / Playwright 切替可能バックエンド

BrowserBackend: 共通プロトコル
AgentBrowserBackend: agent-browser CLI (ローカルデスクトップ向き)
PlaywrightBackend: Playwright sync API (headless / Colab 向き)
auto_detect_backend(): 環境に応じた自動選択
"""

import base64
import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

log = logging.getLogger("opsis.backends")


# =============================================================================
# 共通型
# =============================================================================


@dataclass
class BrowserResult:
    """ブラウザ操作の統一結果型"""

    success: bool
    data: Any = None
    error: str | None = None


@dataclass
class SnapshotData:
    """snapshot の構造化出力"""

    snapshot: str  # テキスト形式の a11y ツリー
    refs: dict[str, dict]  # ref_id -> {role, name, ...}


# =============================================================================
# プロトコル
# =============================================================================


@runtime_checkable
class BrowserBackend(Protocol):
    """ブラウザバックエンドの共通インターフェース"""

    @property
    def name(self) -> str: ...

    def navigate(self, url: str) -> BrowserResult: ...

    def snapshot(
        self,
        *,
        depth: int | None = None,
        interactive: bool = True,
        compact: bool = True,
        selector: str | None = None,
    ) -> BrowserResult: ...

    def wait_for_load(self, timeout: int = 30) -> BrowserResult: ...

    def act(
        self, action: str, ref: str, value: str | None = None
    ) -> BrowserResult: ...

    def get_url(self) -> str: ...

    def extract(
        self, what: str, target: str | None = None
    ) -> BrowserResult: ...

    def eval_js(self, js: str) -> BrowserResult: ...

    def screenshot(self, *, full_page: bool = False) -> BrowserResult: ...

    def go_back(self) -> BrowserResult: ...

    def go_forward(self) -> BrowserResult: ...

    def refresh(self) -> BrowserResult: ...

    def close(self) -> None: ...


# =============================================================================
# AgentBrowserBackend — agent-browser CLI
# =============================================================================


class AgentBrowserBackend:
    """agent-browser CLI バックエンド (デスクトップ向き)"""

    name = "agent-browser"

    def __init__(self, session_name: str = "opsis"):
        self._bin = shutil.which("agent-browser") or str(
            Path.home() / "AppData" / "Roaming" / "npm" / "agent-browser.cmd"
        )
        self._session = session_name

    def _run(self, args: list[str], timeout: int = 60) -> BrowserResult:
        cmd = [self._bin, "--session-name", self._session] + args
        log.debug("agent-browser: %s", " ".join(cmd))
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            if result.returncode != 0:
                return BrowserResult(
                    success=False,
                    error=f"exit {result.returncode}: {stderr or stdout}",
                )
            try:
                parsed = json.loads(stdout)
                if "success" in parsed:
                    return BrowserResult(
                        success=parsed["success"],
                        data=parsed.get("data"),
                        error=parsed.get("error"),
                    )
                return BrowserResult(success=True, data=parsed)
            except json.JSONDecodeError:
                return BrowserResult(success=True, data=stdout)
        except subprocess.TimeoutExpired:
            return BrowserResult(
                success=False, error=f"Timeout after {timeout}s"
            )
        except FileNotFoundError:
            return BrowserResult(
                success=False,
                error=f"agent-browser not found at {self._bin}",
            )

    def navigate(self, url: str) -> BrowserResult:
        return self._run(["open", url])

    def snapshot(
        self,
        *,
        depth: int | None = None,
        interactive: bool = True,
        compact: bool = True,
        selector: str | None = None,
    ) -> BrowserResult:
        args = ["snapshot", "--json"]
        if interactive:
            args.append("-i")
        if compact:
            args.append("-c")
        if depth is not None:
            args.extend(["-d", str(depth)])
        if selector:
            args.extend(["-s", selector])
        result = self._run(args)
        if result.success and isinstance(result.data, dict):
            result.data = SnapshotData(
                snapshot=result.data.get("snapshot", ""),
                refs=result.data.get("refs", {}),
            )
        return result

    def wait_for_load(self, timeout: int = 30) -> BrowserResult:
        return self._run(
            ["wait", "--load", "networkidle"], timeout=timeout
        )

    def act(
        self, action: str, ref: str, value: str | None = None
    ) -> BrowserResult:
        if not ref.startswith("@"):
            ref = f"@{ref}"
        if action in ("click", "hover", "check", "uncheck"):
            return self._run([action, ref])
        elif action in ("fill", "type"):
            return self._run([action, ref, value or ""])
        elif action == "select":
            return self._run(["select", ref, value or ""])
        elif action == "press":
            return self._run(["press", ref])
        return BrowserResult(
            success=False, error=f"Unknown action: {action}"
        )

    def get_url(self) -> str:
        result = self._run(["get", "url"])
        return result.data if result.success else "unknown"

    def extract(
        self, what: str, target: str | None = None
    ) -> BrowserResult:
        args = ["get", what]
        if target:
            args.append(target)
        return self._run(args)

    def eval_js(self, js: str) -> BrowserResult:
        return self._run(["eval", js])

    def screenshot(self, *, full_page: bool = False) -> BrowserResult:
        args = ["screenshot"]
        if full_page:
            args.append("--full-page")
        return self._run(args)

    def go_back(self) -> BrowserResult:
        return self._run(["go-back"])

    def go_forward(self) -> BrowserResult:
        return self._run(["go-forward"])

    def refresh(self) -> BrowserResult:
        return self._run(["refresh"])

    def close(self) -> None:
        pass  # agent-browser manages its own lifecycle


# =============================================================================
# PlaywrightBackend — Playwright sync API + CDP
# =============================================================================

# フィルタ用 role 分類
_INTERACTIVE_ROLES = frozenset({
    "link", "button", "textbox", "combobox", "checkbox", "radio",
    "menuitem", "menuitemcheckbox", "menuitemradio", "tab",
    "searchbox", "slider", "spinbutton", "switch", "option",
    "treeitem",
})

_STRUCTURAL_ROLES = frozenset({
    "heading", "img", "image", "navigation", "main", "banner",
    "contentinfo", "complementary", "region", "search", "form",
    "table", "list", "article", "section", "dialog", "alertdialog",
    "alert", "status", "progressbar",
})

_SKIP_ROLES = frozenset({
    "none", "presentation", "generic", "InlineTextBox", "LineBreak",
    "RootWebArea",
})


class PlaywrightBackend:
    """Playwright sync API + CDP バックエンド (headless / Colab 向き)"""

    name = "playwright"

    def __init__(self, headless: bool = True, cdp_endpoint: str | None = None):
        self._headless = headless
        self._cdp_endpoint = cdp_endpoint or os.environ.get(
            "HGK_OPSIS_CDP_ENDPOINT"
        )
        self._pw = None
        self._browser = None
        self._context = None
        self._page = None
        self._connected_over_cdp = False
        self._cdp_page_name = os.environ.get("HGK_OPSIS_CDP_PAGE_NAME", "hgk-opsis")
        self._cdp_landing_url = os.environ.get(
            "HGK_OPSIS_CDP_LANDING_URL",
            "https://example.com/#hgk-opsis",
        )
        self._last_ref_map: dict[str, dict] = {}  # ref→{role, name} for act()

    def _page_is_open(self, page) -> bool:
        try:
            return not page.is_closed()
        except Exception:
            return True

    def _cdp_page_url(self, page) -> str:
        try:
            return page.url or ""
        except Exception:
            return ""

    def _is_opsis_cdp_url(self, url: str) -> bool:
        return bool(self._cdp_page_name and self._cdp_page_name in url)

    def _is_disposable_cdp_url(self, url: str) -> bool:
        return (
            url == ""
            or url == "https://example.com/"
            or url.startswith("about:blank")
            or url.startswith("chrome://newtab")
            or url.startswith("vivaldi://startpage")
            or url.startswith("chrome://vivaldi-webui/startpage")
        )

    def _select_opsis_cdp_page(self):
        for page in reversed(self._context.pages):
            if self._page_is_open(page) and self._is_opsis_cdp_url(
                self._cdp_page_url(page)
            ):
                return page

        for page in reversed(self._context.pages):
            if self._page_is_open(page) and self._is_disposable_cdp_url(
                self._cdp_page_url(page)
            ):
                if self._cdp_landing_url and self._cdp_page_url(page) in {
                    "",
                    "about:blank",
                }:
                    try:
                        page.goto(
                            self._cdp_landing_url,
                            wait_until="domcontentloaded",
                            timeout=15000,
                        )
                    except Exception:
                        log.debug(
                            "PlaywrightBackend: failed to load Opsis CDP landing page",
                            exc_info=True,
                        )
                return page

        if (
            os.environ.get("HGK_OPSIS_CDP_ALLOW_USER_TAB") == "1"
            and self._context.pages
        ):
            return self._context.pages[-1]

        raise RuntimeError(
            "No disposable Opsis CDP tab found. Open a Vivaldi Start Page or blank tab, "
            "or set HGK_OPSIS_CDP_ALLOW_USER_TAB=1 to allow using the active user tab."
        )

    def _ensure_browser(self):
        if self._page is not None and self._page_is_open(self._page):
            return
        self._page = None
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError(
                "playwright not installed. Run: "
                "pip install playwright && playwright install chromium"
            )
        self._pw = sync_playwright().start()

        if self._cdp_endpoint:
            self._browser = self._pw.chromium.connect_over_cdp(self._cdp_endpoint)
            self._connected_over_cdp = True
            self._context = (
                self._browser.contexts[0]
                if self._browser.contexts
                else self._browser.new_context()
            )
            self._page = self._select_opsis_cdp_page()
            log.info(
                "PlaywrightBackend: connected to Chrome CDP (%s)",
                self._cdp_endpoint,
            )
            return

        self._browser = self._pw.chromium.launch(headless=self._headless)
        self._context = self._browser.new_context()
        self._page = self._context.new_page()
        log.info(
            "PlaywrightBackend: launched (headless=%s)", self._headless
        )

    # ── Navigate ────────────────────────────────────────────

    def navigate(self, url: str) -> BrowserResult:
        self._ensure_browser()
        try:
            self._page.goto(
                url, wait_until="domcontentloaded", timeout=30000
            )
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    # ── Snapshot ────────────────────────────────────────────

    def snapshot(
        self,
        *,
        depth: int | None = None,
        interactive: bool = True,
        compact: bool = True,
        selector: str | None = None,
    ) -> BrowserResult:
        self._ensure_browser()
        try:
            page = self._page

            # CDP で a11y tree 取得 (try/finally で session リーク防止)
            client = page.context.new_cdp_session(page)
            try:
                tree = client.send("Accessibility.getFullAXTree")
            finally:
                client.detach()

            nodes = tree.get("nodes", [])
            nested = self._build_tree(nodes)

            # refs dict + テキスト生成
            refs: dict[str, dict] = {}
            lines: list[str] = []
            counter = [0]
            self._walk_tree(
                nested, refs, lines, counter,
                cur_depth=0, max_depth=depth,
                interactive_only=interactive, compact=compact,
            )

            self._last_ref_map = refs
            return BrowserResult(
                success=True,
                data=SnapshotData(
                    snapshot="\n".join(lines), refs=refs
                ),
            )
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    def _build_tree(self, nodes_flat: list[dict]) -> dict:
        """CDP Accessibility.getFullAXTree → ネスト構造"""
        if not nodes_flat:
            return {}

        by_id: dict[str, dict] = {}
        for n in nodes_flat:
            by_id[str(n.get("nodeId", ""))] = n

        root_id = None
        for n in nodes_flat:
            if "parentId" not in n:
                root_id = str(n.get("nodeId", ""))
                break
        if not root_id and nodes_flat:
            root_id = str(nodes_flat[0].get("nodeId", ""))

        def build(nid: str) -> dict | None:
            n = by_id.get(nid)
            if not n:
                return None

            rv = n.get("role", {})
            role = rv.get("value", "") if isinstance(rv, dict) else str(rv)
            nv = n.get("name", {})
            name = nv.get("value", "") if isinstance(nv, dict) else str(nv)

            props: dict[str, Any] = {}
            for p in n.get("properties", []):
                pv = p.get("value", {})
                val = pv.get("value") if isinstance(pv, dict) else pv
                if val is not None:
                    props[p["name"]] = val

            children = []
            for cid in n.get("childIds", []):
                child = build(str(cid))
                if child:
                    children.append(child)

            return {
                "role": role,
                "name": name,
                "value": props.get("value"),
                "checked": props.get("checked"),
                "disabled": props.get("disabled", False),
                "focused": props.get("focused", False),
                "children": children,
            }

        return build(root_id) or {}

    def _walk_tree(
        self,
        node: dict,
        refs: dict[str, dict],
        lines: list[str],
        counter: list[int],
        *,
        cur_depth: int,
        max_depth: int | None,
        interactive_only: bool,
        compact: bool,
    ):
        if not node:
            return

        role = node.get("role", "")
        name = node.get("name", "")
        has_name = bool(name and name.strip())

        if role in _SKIP_ROLES and cur_depth > 0:
            # スキップするが子は処理する
            if max_depth is None or cur_depth < max_depth:
                for child in node.get("children", []):
                    self._walk_tree(
                        child, refs, lines, counter,
                        cur_depth=cur_depth, max_depth=max_depth,
                        interactive_only=interactive_only, compact=compact,
                    )
            return

        is_interactive = role in _INTERACTIVE_ROLES
        is_structural = role in _STRUCTURAL_ROLES

        # 表示判定
        show = False
        if cur_depth == 0:
            show = True
        elif interactive_only:
            show = is_interactive
        elif compact:
            show = is_interactive or is_structural or has_name
        else:
            show = bool(role)

        if show:
            counter[0] += 1
            ref_id = f"@e{counter[0]}"

            # refs dict エントリ
            entry: dict[str, Any] = {"role": role, "name": name}
            if node.get("value") is not None:
                entry["value"] = node["value"]
            if node.get("checked") is not None:
                entry["checked"] = node["checked"]
            if node.get("disabled"):
                entry["disabled"] = True
            if node.get("focused"):
                entry["focused"] = True
            refs[ref_id] = entry

            # テキスト行
            indent = "  " * cur_depth
            label = f'{role} "{name}"' if has_name else role
            props = []
            if node.get("value"):
                props.append(f'value="{node["value"]}"')
            if node.get("checked") is not None:
                props.append(f"checked={node['checked']}")
            if node.get("disabled"):
                props.append("disabled")
            ps = f" [{', '.join(props)}]" if props else ""
            lines.append(f"{indent}{ref_id} {label}{ps}")

        # 再帰 (深さ制限)
        if max_depth is None or cur_depth < max_depth:
            for child in node.get("children", []):
                self._walk_tree(
                    child, refs, lines, counter,
                    cur_depth=cur_depth + 1, max_depth=max_depth,
                    interactive_only=interactive_only, compact=compact,
                )

    # ── Wait ────────────────────────────────────────────────

    def wait_for_load(self, timeout: int = 30) -> BrowserResult:
        self._ensure_browser()
        try:
            self._page.wait_for_load_state(
                "networkidle", timeout=timeout * 1000
            )
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    # ── Act ─────────────────────────────────────────────────

    def act(
        self, action: str, ref: str, value: str | None = None
    ) -> BrowserResult:
        self._ensure_browser()

        if not ref.startswith("@"):
            ref = f"@{ref}"

        info = self._last_ref_map.get(ref)
        if not info:
            return BrowserResult(
                success=False,
                error=f"Unknown ref {ref}. Run opsis_observe first.",
            )

        role = info["role"]
        name = info.get("name", "")

        try:
            if name:
                loc = self._page.get_by_role(role, name=name).first
            else:
                loc = self._page.get_by_role(role).first

            if action == "click":
                loc.click(timeout=5000)
            elif action == "hover":
                loc.hover(timeout=5000)
            elif action == "fill":
                loc.fill(value or "", timeout=5000)
            elif action == "type":
                loc.type(value or "", timeout=5000)
            elif action == "select":
                loc.select_option(value or "", timeout=5000)
            elif action == "check":
                loc.check(timeout=5000)
            elif action == "uncheck":
                loc.uncheck(timeout=5000)
            elif action == "press":
                loc.press(value or "Enter", timeout=5000)
            else:
                return BrowserResult(
                    success=False, error=f"Unknown action: {action}"
                )
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    # ── Extract ─────────────────────────────────────────────

    def get_url(self) -> str:
        self._ensure_browser()
        return self._page.url

    def _resolve_target(self, target: str):
        """target を Playwright locator に変換。ref ID (@eN) → role+name locator。"""
        page = self._page
        if target.startswith("@"):
            info = self._last_ref_map.get(target)
            if not info:
                return None, f"Unknown ref {target}. Run opsis_observe first."
            role = info["role"]
            name = info.get("name", "")
            if name:
                return page.get_by_role(role, name=name).first, None
            return page.get_by_role(role).first, None
        # CSS selector
        return page.locator(target).first, None

    def extract(
        self, what: str, target: str | None = None
    ) -> BrowserResult:
        self._ensure_browser()
        try:
            page = self._page
            if what == "url":
                return BrowserResult(success=True, data=page.url)
            elif what == "title":
                return BrowserResult(success=True, data=page.title())

            # target が指定されている場合、locator に変換
            loc = None
            if target:
                loc, err = self._resolve_target(target)
                if err:
                    return BrowserResult(success=False, error=err)

            if what == "text":
                if loc:
                    text = loc.text_content(timeout=5000)
                else:
                    text = page.locator("body").text_content()
                return BrowserResult(success=True, data=text)
            elif what == "html":
                if loc:
                    html = loc.inner_html(timeout=5000)
                else:
                    html = page.content()
                return BrowserResult(success=True, data=html)
            elif what == "count":
                if not target:
                    return BrowserResult(
                        success=False, error="count requires target"
                    )
                # count は locator.count() が必要 — ref の場合は常に1
                if target.startswith("@"):
                    return BrowserResult(success=True, data=1 if loc else 0)
                return BrowserResult(
                    success=True, data=page.locator(target).count()
                )
            elif what == "value":
                if not loc:
                    return BrowserResult(
                        success=False, error="value requires target"
                    )
                val = loc.input_value(timeout=5000)
                return BrowserResult(success=True, data=val)
            return BrowserResult(
                success=False, error=f"Unknown extract type: {what}"
            )
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    def eval_js(self, js: str) -> BrowserResult:
        self._ensure_browser()
        try:
            result = self._page.evaluate(js)
            return BrowserResult(success=True, data=result)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    # ── Navigation ──────────────────────────────────────────

    def screenshot(self, *, full_page: bool = False) -> BrowserResult:
        self._ensure_browser()
        try:
            png = self._page.screenshot(full_page=full_page)
            b64 = base64.b64encode(png).decode()
            return BrowserResult(
                success=True,
                data={"format": "png", "base64": b64, "size": len(png)},
            )
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    def go_back(self) -> BrowserResult:
        self._ensure_browser()
        try:
            self._page.go_back(timeout=5000)
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    def go_forward(self) -> BrowserResult:
        self._ensure_browser()
        try:
            self._page.go_forward(timeout=5000)
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    def refresh(self) -> BrowserResult:
        self._ensure_browser()
        try:
            self._page.reload(timeout=15000)
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    def close(self) -> None:
        if self._browser and not self._connected_over_cdp:
            try:
                self._browser.close()
            except Exception:
                pass
        if self._pw:
            try:
                self._pw.stop()
            except Exception:
                pass
        self._page = None
        self._context = None
        self._browser = None
        self._pw = None
        self._connected_over_cdp = False


# =============================================================================
# Auto-detect
# =============================================================================


def auto_detect_backend(
    prefer: str | None = None, headless: bool = True
) -> AgentBrowserBackend | PlaywrightBackend:
    """環境に応じてバックエンドを自動選択。

    prefer: "agent-browser" | "playwright" | None (auto)
    headless: Playwright 使用時の headless フラグ
    """
    if prefer == "playwright":
        log.info("Backend: PlaywrightBackend (explicit)")
        return PlaywrightBackend(headless=headless)

    if prefer == "agent-browser":
        log.info("Backend: AgentBrowserBackend (explicit)")
        return AgentBrowserBackend()

    # Auto: agent-browser があればそれ、なければ Playwright
    if shutil.which("agent-browser"):
        log.info("Backend: AgentBrowserBackend (auto-detected)")
        return AgentBrowserBackend()

    try:
        import playwright  # noqa: F401

        log.info("Backend: PlaywrightBackend (fallback)")
        return PlaywrightBackend(headless=headless)
    except ImportError:
        raise RuntimeError(
            "No browser backend available. Install either:\n"
            "  npm install -g agent-browser\n"
            "  pip install playwright && playwright install chromium"
        )
