from mekhane.mcp.opsis_backends import PlaywrightBackend


class _FakeCdpPage:
    def __init__(self, url: str):
        self.url = url
        self.closed = False
        self.goto_calls: list[tuple[str, str, int]] = []

    def is_closed(self) -> bool:
        return self.closed

    def goto(self, url: str, *, wait_until: str, timeout: int) -> None:
        self.goto_calls.append((url, wait_until, timeout))
        self.url = url


class _FakeCdpContext:
    def __init__(self, pages):
        self.pages = pages


class _FakeBrowser:
    def __init__(self):
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_cdp_session_prefers_disposable_startpage_over_user_tab() -> None:
    user_page = _FakeCdpPage("https://mail.google.com/")
    startpage = _FakeCdpPage("vivaldi://startpage")
    context = _FakeCdpContext([user_page, startpage])
    backend = PlaywrightBackend(cdp_endpoint="http://127.0.0.1:9222")
    backend._context = context

    page = backend._select_opsis_cdp_page()

    assert page is startpage
    assert user_page.url == "https://mail.google.com/"


def test_cdp_session_loads_landing_url_for_blank_disposable_tab() -> None:
    user_page = _FakeCdpPage("https://mail.google.com/")
    blank_page = _FakeCdpPage("about:blank")
    context = _FakeCdpContext([user_page, blank_page])
    backend = PlaywrightBackend(cdp_endpoint="http://127.0.0.1:9222")
    backend._context = context

    page = backend._select_opsis_cdp_page()

    assert page is blank_page
    assert page.url == "https://example.com/#hgk-opsis"
    assert len(context.pages) == 2
    assert user_page.url == "https://mail.google.com/"


def test_cdp_close_does_not_close_attached_browser() -> None:
    browser = _FakeBrowser()
    backend = PlaywrightBackend(cdp_endpoint="http://127.0.0.1:9222")
    backend._browser = browser
    backend._connected_over_cdp = True

    backend.close()

    assert browser.closed is False
