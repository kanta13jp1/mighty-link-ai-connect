from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
DATE_LABELS = {
    "ja": ("受信日（開始）", "受信日（終了）"),
    "en": ("Received date (start)", "Received date (end)"),
    "zh": ("接收日期（开始）", "接收日期（结束）"),
    "ko": ("수신일(시작)", "수신일(종료)"),
}


def test_matching_filter_date_inputs_have_localized_attribute_contracts():
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        assert html.count('data-i18n-aria-label="matching_filter_received_from_label"') == 1
        assert html.count('data-i18n-aria-label="matching_filter_received_to_label"') == 1
        for start_label, end_label in DATE_LABELS.values():
            assert f'matching_filter_received_from_label: "{start_label}"' in html
            assert f'matching_filter_received_to_label: "{end_label}"' in html


def test_matching_filter_date_names_follow_language_and_preserve_behavior(fastapi_server):
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
        start_input = page.locator("#matching-filter-received-from")
        end_input = page.locator("#matching-filter-received-to")

        assert start_input.get_attribute("type") == "date"
        assert end_input.get_attribute("type") == "date"
        expected_handler = "refreshSalesEmailMatchesForDateRange()"
        assert start_input.get_attribute("onchange") == expected_handler
        assert end_input.get_attribute("onchange") == expected_handler

        for language, (start_label, end_label) in DATE_LABELS.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert page.evaluate("document.documentElement.lang") == language
            assert start_input.get_attribute("aria-label") == start_label
            assert end_input.get_attribute("aria-label") == end_label

        start_input.fill("2026-09-01")
        end_input.fill("2026-09-05")
        assert start_input.input_value() == "2026-09-01"
        assert end_input.input_value() == "2026-09-05"

        page.reload(wait_until="domcontentloaded")
        page.evaluate("switchAppTab('#matching-section')")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert start_input.get_attribute("aria-label") == DATE_LABELS["ko"][0]
        assert end_input.get_attribute("aria-label") == DATE_LABELS["ko"][1]

        browser.close()
