from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
SCORE_LABELS = {
    "ja": "適合度",
    "en": "Match score",
    "zh": "匹配度",
    "ko": "적합도",
}


def test_matching_filter_score_label_has_localized_contract():
    expected_markup = (
        '<label for="matching-filter-score" '
        'data-i18n="matching_filter_score_label">適合度</label>'
    )
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        assert html.count(expected_markup) == 1
        for label in SCORE_LABELS.values():
            assert f'matching_filter_score_label: "{label}"' in html


def test_matching_filter_score_label_tracks_language_and_selection(fastapi_server):
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

        label = page.locator('label[for="matching-filter-score"]')
        select = page.locator("#matching-filter-score")
        select.select_option("90")

        for language, expected_label in SCORE_LABELS.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert page.evaluate("document.documentElement.lang") == language
            assert label.text_content().strip() == expected_label
            assert select.input_value() == "90"

        assert label.get_attribute("for") == "matching-filter-score"
        assert select.get_attribute("onchange") == "applyMatchingFilters()"

        page.reload(wait_until="domcontentloaded")
        page.evaluate("switchAppTab('#matching-section')")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert label.text_content().strip() == SCORE_LABELS["ko"]

        browser.close()
