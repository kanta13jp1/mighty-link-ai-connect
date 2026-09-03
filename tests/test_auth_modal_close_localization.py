from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
AUTH_MODAL_CLOSE_LABELS = {
    "ja": "認証ダイアログを閉じる",
    "en": "Close authentication dialog",
    "zh": "关闭身份验证对话框",
    "ko": "인증 대화상자 닫기",
}
LOCALIZED_MARKUP = (
    'class="auth-modal-close" onclick="closeAuthModal()" '
    'aria-label="認証ダイアログを閉じる" '
    'data-i18n-aria-label="auth_modal_close_label"'
)


def test_auth_modal_close_button_has_a_localized_markup_contract():
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        assert LOCALIZED_MARKUP in html
        for label in AUTH_MODAL_CLOSE_LABELS.values():
            assert f'auth_modal_close_label: "{label}"' in html, (html_file, label)


def test_auth_modal_close_name_tracks_language_open_state_and_persistence(fastapi_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            http_credentials={"username": "test-admin", "password": "test-password"},
        )
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")
        close_button = page.locator("#auth-modal .auth-modal-close")

        for language, expected_label in AUTH_MODAL_CLOSE_LABELS.items():
            page.evaluate("language => switchLanguage(language)", language)
            page.evaluate("openAuthModal('login')")
            assert page.evaluate("document.documentElement.lang") == language
            assert close_button.is_visible()
            assert close_button.get_attribute("aria-label") == expected_label
            page.evaluate("closeAuthModal()")

        page.reload(wait_until="domcontentloaded")
        page.evaluate("openAuthModal('login')")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert close_button.get_attribute("aria-label") == AUTH_MODAL_CLOSE_LABELS["ko"]

        browser.close()
