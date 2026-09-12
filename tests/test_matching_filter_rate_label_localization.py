from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
RATE_LABELS = {
    "ja": ("単価下限", "単価上限"),
    "en": ("Minimum rate", "Maximum rate"),
    "zh": ("最低单价", "最高单价"),
    "ko": ("최소 단가", "최대 단가"),
}


def test_matching_filter_rate_labels_have_localized_contract():
    expected_markup = (
        '<label for="matching-filter-rate-min" '
        'data-i18n="matching_filter_rate_min_label">単価下限</label>'
    )
    expected_max_markup = (
        '<label for="matching-filter-rate-max" '
        'data-i18n="matching_filter_rate_max_label">単価上限</label>'
    )
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        assert html.count(expected_markup) == 1
        assert html.count(expected_max_markup) == 1
        for min_label, max_label in RATE_LABELS.values():
            assert f'matching_filter_rate_min_label: "{min_label}"' in html
            assert f'matching_filter_rate_max_label: "{max_label}"' in html


def test_matching_filter_rate_labels_track_language_and_selection(fastapi_server):
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

        min_label = page.locator('label[for="matching-filter-rate-min"]')
        max_label = page.locator('label[for="matching-filter-rate-max"]')
        min_select = page.locator("#matching-filter-rate-min")
        max_select = page.locator("#matching-filter-rate-max")
        min_select.select_option("60")
        max_select.select_option("90")

        for language, (expected_min, expected_max) in RATE_LABELS.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert page.evaluate("document.documentElement.lang") == language
            assert min_label.text_content().strip() == expected_min
            assert max_label.text_content().strip() == expected_max
            assert min_select.input_value() == "60"
            assert max_select.input_value() == "90"

        assert min_label.get_attribute("for") == "matching-filter-rate-min"
        assert max_label.get_attribute("for") == "matching-filter-rate-max"
        assert min_select.get_attribute("onchange") == "applyMatchingFilters()"
        assert max_select.get_attribute("onchange") == "applyMatchingFilters()"

        page.reload(wait_until="domcontentloaded")
        page.evaluate("switchAppTab('#matching-section')")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert min_label.text_content().strip() == RATE_LABELS["ko"][0]
        assert max_label.text_content().strip() == RATE_LABELS["ko"][1]

        browser.close()
