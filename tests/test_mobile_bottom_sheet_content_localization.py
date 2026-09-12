from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
CONTENT_LABELS = {
    "ja": {
        "mobile_sheet_title": "メニュー & ツール",
        "mobile_sheet_setup": "初期設定",
        "mobile_sheet_self_assessment": "自己診断",
        "mobile_sheet_admin": "管理者",
        "mobile_sheet_support": "サポート",
    },
    "en": {
        "mobile_sheet_title": "Menu & Tools",
        "mobile_sheet_setup": "Setup",
        "mobile_sheet_self_assessment": "Self-assessment",
        "mobile_sheet_admin": "Admin",
        "mobile_sheet_support": "Support",
    },
    "zh": {
        "mobile_sheet_title": "菜单与工具",
        "mobile_sheet_setup": "初始设置",
        "mobile_sheet_self_assessment": "自我诊断",
        "mobile_sheet_admin": "管理",
        "mobile_sheet_support": "支持",
    },
    "ko": {
        "mobile_sheet_title": "메뉴 & 도구",
        "mobile_sheet_setup": "초기 설정",
        "mobile_sheet_self_assessment": "자가 진단",
        "mobile_sheet_admin": "관리자",
        "mobile_sheet_support": "지원",
    },
}
TARGETS = {
    "mobile_sheet_setup": "#onboarding-section",
    "mobile_sheet_self_assessment": "#aptitude-demo-section",
    "mobile_sheet_admin": "#admin-dashboard-section",
    "mobile_sheet_support": "#support",
}


def test_mobile_bottom_sheet_content_has_localized_markup_and_dictionary_contracts():
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        for key in CONTENT_LABELS["ja"]:
            assert html.count(f'data-i18n="{key}"') == 1, (html_file, key)
            for language in CONTENT_LABELS.values():
                assert f'{key}: "{language[key]}"' in html, (html_file, key, language[key])

        for key, href in TARGETS.items():
            assert f'href="{href}"' in html
            assert f'data-i18n="{key}"' in html


def test_mobile_bottom_sheet_content_tracks_language_and_persistence(fastapi_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            http_credentials={"username": "test-admin", "password": "test-password"},
        )
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")
        sheet = page.locator('#mobile-bottom-sheet [role="dialog"]')

        for language, expected_labels in CONTENT_LABELS.items():
            page.evaluate("language => switchLanguage(language)", language)
            page.evaluate("openMobileBottomSheet()")
            assert page.evaluate("document.documentElement.lang") == language
            assert sheet.is_visible()
            for key, expected_label in expected_labels.items():
                assert sheet.locator(f'[data-i18n="{key}"]').inner_text() == expected_label
            for key, href in TARGETS.items():
                assert sheet.locator(f'a:has([data-i18n="{key}"])').get_attribute("href") == href
            page.evaluate("closeMobileBottomSheet()")

        page.reload(wait_until="domcontentloaded")
        page.evaluate("openMobileBottomSheet()")
        assert page.evaluate("document.documentElement.lang") == "ko"
        for key, expected_label in CONTENT_LABELS["ko"].items():
            assert sheet.locator(f'[data-i18n="{key}"]').inner_text() == expected_label

        browser.close()
