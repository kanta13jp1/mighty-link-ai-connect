from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
NAVIGATION_MAINTENANCE_SCRIPTS = (
    PROJECT_ROOT / "scripts" / "apply_global_saas_shell.py",
    PROJECT_ROOT / "scripts" / "fix_clean_i18n.py",
    PROJECT_ROOT / "scripts" / "fix_final_nav_parity.py",
    PROJECT_ROOT / "scripts" / "fix_nav_tests.py",
    PROJECT_ROOT / "scripts" / "unify_primary_nav_to_sidebar.py",
)
PRIMARY_NAVIGATION_LABELS = {
    "ja": "メインナビゲーション",
    "en": "Primary navigation",
    "zh": "主导航",
    "ko": "주요 탐색",
}
LOCALIZED_MARKUP = (
    'id="primary-navigation" aria-label="メインナビゲーション" '
    'data-i18n-aria-label="primary_navigation_label"'
)


def test_primary_navigation_has_a_localized_markup_contract():
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        assert LOCALIZED_MARKUP in html
        for label in PRIMARY_NAVIGATION_LABELS.values():
            assert f'primary_navigation_label: "{label}"' in html, (html_file, label)


def test_navigation_maintenance_scripts_preserve_the_localized_name():
    for script in NAVIGATION_MAINTENANCE_SCRIPTS:
        assert LOCALIZED_MARKUP in script.read_text(encoding="utf-8"), script


def test_primary_navigation_name_tracks_language_and_persistence(fastapi_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            http_credentials={"username": "test-admin", "password": "test-password"},
        )
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")
        navigation = page.locator("#primary-navigation")

        for language, expected_label in PRIMARY_NAVIGATION_LABELS.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert page.evaluate("document.documentElement.lang") == language
            assert navigation.get_attribute("aria-label") == expected_label

        page.reload(wait_until="domcontentloaded")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert navigation.get_attribute("aria-label") == PRIMARY_NAVIGATION_LABELS["ko"]

        browser.close()
