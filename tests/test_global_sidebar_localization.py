from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
SIDEBAR_MAINTENANCE_SCRIPTS = (
    PROJECT_ROOT / "scripts" / "apply_global_saas_shell_part2.py",
)
WORKSPACE_NAVIGATION_LABELS = {
    "ja": "ワークスペースナビゲーション",
    "en": "Workspace navigation",
    "zh": "工作区导航",
    "ko": "워크스페이스 탐색",
}
LOCALIZED_MARKUP = (
    'id="global-sidebar" aria-label="ワークスペースナビゲーション" '
    'data-i18n-aria-label="workspace_navigation_label"'
)


def test_global_sidebar_has_a_localized_markup_contract():
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        assert LOCALIZED_MARKUP in html
        for label in WORKSPACE_NAVIGATION_LABELS.values():
            assert f'workspace_navigation_label: "{label}"' in html, (html_file, label)


def test_sidebar_maintenance_scripts_preserve_the_localized_name():
    for script in SIDEBAR_MAINTENANCE_SCRIPTS:
        assert LOCALIZED_MARKUP in script.read_text(encoding="utf-8"), script


def test_global_sidebar_name_tracks_language_and_persistence(fastapi_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            http_credentials={"username": "test-admin", "password": "test-password"},
        )
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")
        sidebar = page.locator("#global-sidebar")

        for language, expected_label in WORKSPACE_NAVIGATION_LABELS.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert page.evaluate("document.documentElement.lang") == language
            assert sidebar.get_attribute("aria-label") == expected_label

        page.reload(wait_until="domcontentloaded")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert sidebar.get_attribute("aria-label") == WORKSPACE_NAVIGATION_LABELS["ko"]

        browser.close()
