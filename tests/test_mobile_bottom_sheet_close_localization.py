from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
MOBILE_SHEET_CLOSE_LABELS = {
    "ja": "閉じる",
    "en": "Close",
    "zh": "关闭",
    "ko": "닫기",
}
LOCALIZED_MARKUP = (
    'class="auth-modal-close" onclick="closeMobileBottomSheet()" '
    'style="position:static;" aria-label="閉じる" '
    'data-i18n-aria-label="shortcut_modal_close"'
)


def test_mobile_bottom_sheet_close_button_has_a_localized_markup_contract():
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        assert LOCALIZED_MARKUP in html
        for label in MOBILE_SHEET_CLOSE_LABELS.values():
            assert f'shortcut_modal_close: "{label}"' in html, (html_file, label)


def test_mobile_bottom_sheet_close_name_tracks_language_state_and_persistence(
    fastapi_server,
):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            http_credentials={"username": "test-admin", "password": "test-password"},
        )
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")
        sheet = page.locator("#mobile-bottom-sheet")
        close_button = sheet.locator(".auth-modal-close")

        for language, expected_label in MOBILE_SHEET_CLOSE_LABELS.items():
            page.evaluate("language => switchLanguage(language)", language)
            page.evaluate("openMobileBottomSheet()")
            assert page.evaluate("document.documentElement.lang") == language
            assert sheet.get_attribute("aria-hidden") == "false"
            assert close_button.is_visible()
            assert close_button.get_attribute("aria-label") == expected_label
            page.evaluate("closeMobileBottomSheet()")
            assert sheet.get_attribute("aria-hidden") == "true"

        page.reload(wait_until="domcontentloaded")
        page.evaluate("openMobileBottomSheet()")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert close_button.get_attribute("aria-label") == MOBILE_SHEET_CLOSE_LABELS["ko"]

        browser.close()
