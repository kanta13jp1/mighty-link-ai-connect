from html.parser import HTMLParser
from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
EXPECTED_LABELS = {
    "ja": ("ナビゲーションメニューを開く", "ナビゲーションメニューを閉じる"),
    "en": ("Open navigation menu", "Close navigation menu"),
    "zh": ("打开导航菜单", "关闭导航菜单"),
    "ko": ("내비게이션 메뉴 열기", "내비게이션 메뉴 닫기"),
}


class MobileMenuButtonParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.attributes: dict[str, str | None] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if attributes.get("id") == "mobile-menu-btn":
            self.attributes = attributes


def test_mobile_menu_initial_accessible_name_is_japanese_in_both_entrypoints():
    for html_file in HTML_FILES:
        parser = MobileMenuButtonParser()
        parser.feed(html_file.read_text(encoding="utf-8"))

        assert parser.attributes is not None, html_file
        assert parser.attributes.get("aria-label") == EXPECTED_LABELS["ja"][0]
        assert parser.attributes.get("aria-expanded") == "false"


def test_mobile_menu_accessible_name_tracks_language_and_expanded_state(fastapi_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            http_credentials={"username": "test-admin", "password": "test-password"},
        )
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")
        page.wait_for_function("typeof toggleSidebarDrawer === 'function'")

        button = page.locator("#mobile-menu-btn")
        for language, (open_label, close_label) in EXPECTED_LABELS.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert button.get_attribute("aria-expanded") == "false"
            assert button.get_attribute("aria-label") == open_label

            button.click()
            assert button.get_attribute("aria-expanded") == "true"
            assert button.get_attribute("aria-label") == close_label

            page.evaluate("closeSidebarDrawer()")
            assert button.get_attribute("aria-expanded") == "false"
            assert button.get_attribute("aria-label") == open_label

        browser.close()
