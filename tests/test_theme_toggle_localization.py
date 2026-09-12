from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
THEME_LABELS = {
    "ja": {
        "light": ("ライト", "ライトテーマに切り替え"),
        "dark": ("ダーク", "ダークテーマに切り替え"),
    },
    "en": {
        "light": ("Light", "Switch to light theme"),
        "dark": ("Dark", "Switch to dark theme"),
    },
    "zh": {
        "light": ("浅色", "切换为浅色主题"),
        "dark": ("深色", "切换为深色主题"),
    },
    "ko": {
        "light": ("라이트", "라이트 테마로 전환"),
        "dark": ("다크", "다크 테마로 전환"),
    },
}


def _assert_theme_control(page, target_theme: str, pressed: str, language: str) -> None:
    visible_label, accessible_name = THEME_LABELS[language][target_theme]
    button = page.locator("#theme-toggle")

    assert page.locator("#theme-toggle-label").inner_text() == visible_label
    assert button.get_attribute("aria-label") == accessible_name
    assert button.get_attribute("aria-pressed") == pressed
    assert visible_label.casefold() in accessible_name.casefold()


def test_theme_toggle_markup_and_i18n_contract_are_not_language_fixed():
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        assert 'id="theme-toggle" aria-label="ライトテーマに切り替え"' in html
        assert 'id="theme-toggle-label">ライト</span>' in html
        assert 'id="theme-toggle-label" data-i18n="theme_light"' not in html
        for language, values in THEME_LABELS.items():
            for target_theme, (_, accessible_name) in values.items():
                key = f"theme_toggle_to_{target_theme}"
                assert f'{key}: "{accessible_name}"' in html, (html_file, language, key)


def test_theme_toggle_name_tracks_language_state_and_persistence(fastapi_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            http_credentials={"username": "test-admin", "password": "test-password"},
        )
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")

        for language in THEME_LABELS:
            page.evaluate("language => switchLanguage(language)", language)
            _assert_theme_control(page, "light", "false", language)

            page.evaluate("toggleTheme()")
            _assert_theme_control(page, "dark", "true", language)

            page.evaluate("toggleTheme()")

        page.evaluate("switchLanguage('ko')")
        page.evaluate("toggleTheme()")
        page.reload(wait_until="domcontentloaded")

        assert page.evaluate("document.documentElement.lang") == "ko"
        assert page.evaluate("document.documentElement.dataset.theme") == "light"
        _assert_theme_control(page, "dark", "true", "ko")

        browser.close()
