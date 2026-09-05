from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
SCORE_OPTIONS = {
    "ja": ["すべて", "80%以上", "90%以上"],
    "en": ["All", "80% or higher", "90% or higher"],
    "zh": ["全部", "80%及以上", "90%及以上"],
    "ko": ["전체", "80% 이상", "90% 이상"],
}
OPTION_KEYS = [
    "matching_filter_score_option_all",
    "matching_filter_score_option_80",
    "matching_filter_score_option_90",
]
OPTION_VALUES = ["0", "80", "90"]


def test_matching_filter_score_options_have_localized_contract():
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        for key, value in zip(OPTION_KEYS, OPTION_VALUES, strict=True):
            assert html.count(f'<option value="{value}" data-i18n="{key}">') == 1
        for language_options in SCORE_OPTIONS.values():
            for key, label in zip(OPTION_KEYS, language_options, strict=True):
                assert f'{key}: "{label}"' in html


def test_matching_filter_score_options_track_language_and_selection(fastapi_server):
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

        select = page.locator("#matching-filter-score")
        select.select_option("90")

        for language, expected_options in SCORE_OPTIONS.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert page.evaluate("document.documentElement.lang") == language
            assert select.locator("option").all_text_contents() == expected_options
            assert select.input_value() == "90"

        assert select.locator("option").evaluate_all("options => options.map(option => option.value)") == OPTION_VALUES
        assert select.get_attribute("onchange") == "applyMatchingFilters()"

        page.reload(wait_until="domcontentloaded")
        page.evaluate("switchAppTab('#matching-section')")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert select.locator("option").all_text_contents() == SCORE_OPTIONS["ko"]

        browser.close()
