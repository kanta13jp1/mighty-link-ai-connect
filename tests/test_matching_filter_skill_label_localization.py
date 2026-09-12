from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
SKILL_LABELS = {
    "ja": "必須スキル",
    "en": "Required skill",
    "zh": "必备技能",
    "ko": "필수 기술",
}


def test_matching_filter_skill_label_has_localized_contract():
    expected_markup = (
        '<label for="matching-filter-skill" '
        'data-i18n="matching_filter_skill_label">必須スキル</label>'
    )
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        assert html.count(expected_markup) == 1
        for label in SKILL_LABELS.values():
            assert f'matching_filter_skill_label: "{label}"' in html


def test_matching_filter_skill_label_tracks_language_and_selection(fastapi_server):
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

        label = page.locator('label[for="matching-filter-skill"]')
        select = page.locator("#matching-filter-skill")
        select.select_option("AWS")

        for language, expected_label in SKILL_LABELS.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert page.evaluate("document.documentElement.lang") == language
            assert label.text_content().strip() == expected_label
            assert select.input_value() == "AWS"

        assert label.get_attribute("for") == "matching-filter-skill"
        assert select.get_attribute("onchange") == "applyMatchingFilters()"

        page.reload(wait_until="domcontentloaded")
        page.evaluate("switchAppTab('#matching-section')")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert label.text_content().strip() == SKILL_LABELS["ko"]

        browser.close()
