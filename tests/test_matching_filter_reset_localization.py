from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
RESET_LABELS = {
    "ja": "絞り込み条件をリセット",
    "en": "Reset filters",
    "zh": "重置筛选条件",
    "ko": "필터 조건 초기화",
}


def test_matching_filter_reset_has_localized_attribute_contracts():
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        assert html.count('data-i18n-aria-label="matching_filter_reset_label"') == 1
        assert html.count('data-i18n-title="matching_filter_reset_label"') == 1
        assert 'document.querySelectorAll("[data-i18n-title]")' in html
        for label in RESET_LABELS.values():
            assert f'matching_filter_reset_label: "{label}"' in html


def test_matching_filter_reset_name_tooltip_and_action_follow_language(fastapi_server):
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
        reset_button = page.locator(".matching-filter-reset")

        for language, expected_label in RESET_LABELS.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert page.evaluate("document.documentElement.lang") == language
            assert reset_button.get_attribute("aria-label") == expected_label
            assert reset_button.get_attribute("title") == expected_label

        page.locator("#matching-filter-keyword").fill("AWS")
        page.locator("#matching-filter-skill").select_option("Java")
        reset_button.click()
        assert page.locator("#matching-filter-keyword").input_value() == ""
        assert page.locator("#matching-filter-skill").input_value() == ""

        page.reload(wait_until="domcontentloaded")
        page.evaluate("switchAppTab('#matching-section')")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert reset_button.get_attribute("aria-label") == RESET_LABELS["ko"]
        assert reset_button.get_attribute("title") == RESET_LABELS["ko"]

        browser.close()
