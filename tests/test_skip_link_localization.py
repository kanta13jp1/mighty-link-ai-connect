from html.parser import HTMLParser
from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
EXPECTED_LABELS = {
    "ja": "メインコンテンツへ移動",
    "en": "Skip to main content",
    "zh": "跳至主要内容",
    "ko": "주요 콘텐츠로 건너뛰기",
}


class SkipLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.attributes: dict[str, str | None] | None = None
        self.text = ""
        self.in_skip_link = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "a" and "skip-link" in (attributes.get("class") or "").split():
            self.attributes = attributes
            self.in_skip_link = True

    def handle_data(self, data: str) -> None:
        if self.in_skip_link:
            self.text += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.in_skip_link:
            self.in_skip_link = False


def test_skip_link_has_japanese_default_and_i18n_hook_in_both_entrypoints():
    for html_file in HTML_FILES:
        parser = SkipLinkParser()
        parser.feed(html_file.read_text(encoding="utf-8"))

        assert parser.attributes is not None, html_file
        assert parser.attributes.get("href") == "#top"
        assert parser.attributes.get("data-i18n") == "skip_to_main"
        assert parser.text == EXPECTED_LABELS["ja"]


def test_skip_link_tracks_language_persistence_and_moves_focus_to_main(fastapi_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            http_credentials={"username": "test-admin", "password": "test-password"},
        )
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")
        page.wait_for_function("typeof switchLanguage === 'function'")

        skip_link = page.locator(".skip-link")
        for language, label in EXPECTED_LABELS.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert skip_link.inner_text() == label

        page.evaluate("switchLanguage('ko')")
        page.reload(wait_until="domcontentloaded")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert skip_link.inner_text() == EXPECTED_LABELS["ko"]

        skip_link.focus()
        page.keyboard.press("Enter")
        page.wait_for_function("location.hash === '#top'")
        assert page.evaluate("document.activeElement.id") == "top"

        browser.close()
