from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
MOBILE_SHEET_DIALOG_LABELS = {
    "ja": "モバイル追加メニュー",
    "en": "More menu",
    "zh": "更多菜单",
    "ko": "추가 메뉴",
}
LOCALIZED_MARKUP = (
    'role="dialog" aria-modal="true" aria-label="モバイル追加メニュー" '
    'data-i18n-aria-label="mobile_more_menu_dialog_label"'
)


def test_mobile_bottom_sheet_dialog_has_a_localized_name_contract():
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        assert LOCALIZED_MARKUP in html
        for label in MOBILE_SHEET_DIALOG_LABELS.values():
            assert f'mobile_more_menu_dialog_label: "{label}"' in html, (html_file, label)


def test_mobile_bottom_sheet_dialog_name_tracks_language_and_persistence(
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
        dialog = page.locator('#mobile-bottom-sheet [role="dialog"]')

        for language, expected_label in MOBILE_SHEET_DIALOG_LABELS.items():
            page.evaluate("language => switchLanguage(language)", language)
            page.evaluate("openMobileBottomSheet()")
            assert page.evaluate("document.documentElement.lang") == language
            assert dialog.is_visible()
            assert dialog.get_attribute("aria-label") == expected_label
            page.evaluate("closeMobileBottomSheet()")

        page.reload(wait_until="domcontentloaded")
        page.evaluate("openMobileBottomSheet()")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert dialog.get_attribute("aria-label") == MOBILE_SHEET_DIALOG_LABELS["ko"]

        browser.close()
