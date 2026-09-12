from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
BRAND_HOME_LABELS = {
    "ja": "Mighty Skill-Bridge ホーム",
    "en": "Mighty Skill-Bridge home",
    "zh": "Mighty Skill-Bridge 首页",
    "ko": "Mighty Skill-Bridge 홈",
}
LOCALIZED_MARKUP = 'data-i18n-aria-label="brand_home_label"'


def test_brand_home_links_have_a_localized_markup_contract():
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        assert html.count(LOCALIZED_MARKUP) == 2
        assert 'aria-label="Mighty Skill-Bridge footer home"' not in html
        for label in BRAND_HOME_LABELS.values():
            assert f'brand_home_label: "{label}"' in html, (html_file, label)


def test_brand_home_link_names_track_language_and_persistence(fastapi_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            http_credentials={"username": "test-admin", "password": "test-password"},
        )
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")
        brand_links = page.locator("a.brand")

        assert brand_links.count() == 2
        for language, expected_label in BRAND_HOME_LABELS.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert page.evaluate("document.documentElement.lang") == language
            assert brand_links.evaluate_all(
                "(links, expected) => links.every(link => link.getAttribute('aria-label') === expected)",
                expected_label,
            )

        page.reload(wait_until="domcontentloaded")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert brand_links.evaluate_all(
            "(links, expected) => links.every(link => link.getAttribute('aria-label') === expected)",
            BRAND_HOME_LABELS["ko"],
        )

        browser.close()
