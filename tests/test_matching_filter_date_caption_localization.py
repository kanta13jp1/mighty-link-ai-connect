from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
DATE_CAPTIONS = {
    "ja": "受信日",
    "en": "Received date",
    "zh": "接收日期",
    "ko": "수신일",
}


def test_matching_filter_date_caption_has_localized_contract():
    expected_markup = (
        '<label for="matching-filter-received-from" '
        'data-i18n="matching_filter_received_date_label">受信日</label>'
    )
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        assert html.count(expected_markup) == 1
        for caption in DATE_CAPTIONS.values():
            assert f'matching_filter_received_date_label: "{caption}"' in html


def test_matching_filter_date_caption_tracks_language_and_persistence(fastapi_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            http_credentials={"username": "test-admin", "password": "test-password"},
        )
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(f"{fastapi_server}#matching-section", wait_until="domcontentloaded")
        page.evaluate("switchAppTab('#matching-section')")
        caption = page.locator('label[for="matching-filter-received-from"]')
        start_input = page.locator("#matching-filter-received-from")
        end_input = page.locator("#matching-filter-received-to")

        for language, expected_caption in DATE_CAPTIONS.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert page.evaluate("document.documentElement.lang") == language
            assert caption.text_content().strip() == expected_caption

        assert caption.get_attribute("for") == "matching-filter-received-from"
        assert start_input.get_attribute("type") == "date"
        assert end_input.get_attribute("type") == "date"
        expected_handler = "refreshSalesEmailMatchesForDateRange()"
        assert start_input.get_attribute("onchange") == expected_handler
        assert end_input.get_attribute("onchange") == expected_handler
        assert start_input.get_attribute("aria-label") == "수신일(시작)"
        assert end_input.get_attribute("aria-label") == "수신일(종료)"

        page.reload(wait_until="domcontentloaded")
        page.evaluate("switchAppTab('#matching-section')")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert caption.text_content().strip() == DATE_CAPTIONS["ko"]

        browser.close()
