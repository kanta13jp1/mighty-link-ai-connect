from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
LANGUAGE_GROUP_LABELS = {
    "ja": "言語を選択",
    "en": "Select language",
    "zh": "选择语言",
    "ko": "언어 선택",
}


def test_language_switch_group_name_has_a_localized_markup_contract():
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        assert (
            '<div class="language-switch" role="group" aria-label="言語を選択" '
            'data-i18n-aria-label="language_switch_label">'
        ) in html
        for label in LANGUAGE_GROUP_LABELS.values():
            assert f'language_switch_label: "{label}"' in html, (html_file, label)


def test_language_switch_group_name_tracks_language_and_persistence(fastapi_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            http_credentials={"username": "test-admin", "password": "test-password"},
        )
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")
        switcher = page.locator(".language-switch")

        for language, expected_label in LANGUAGE_GROUP_LABELS.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert page.evaluate("document.documentElement.lang") == language
            assert switcher.get_attribute("aria-label") == expected_label
            for button_language in LANGUAGE_GROUP_LABELS:
                expected_pressed = "true" if button_language == language else "false"
                assert (
                    page.locator(
                        f".language-switch button[data-lang='{button_language}']"
                    ).get_attribute("aria-pressed")
                    == expected_pressed
                )

        page.reload(wait_until="domcontentloaded")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert switcher.get_attribute("aria-label") == LANGUAGE_GROUP_LABELS["ko"]

        browser.close()
