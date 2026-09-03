from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
EXPECTED = {
    "ja": {
        "landmark": "モバイル主要ナビゲーション",
        "labels": ["ホーム", "アンケート", "勤怠", "マッチング", "その他"],
        "more": "その他のメニューを開く",
    },
    "en": {
        "landmark": "Mobile primary navigation",
        "labels": ["Home", "Survey", "Attendance", "Matching", "More"],
        "more": "Open more navigation options",
    },
    "zh": {
        "landmark": "移动端主导航",
        "labels": ["首页", "问卷", "考勤", "匹配", "更多"],
        "more": "打开更多导航选项",
    },
    "ko": {
        "landmark": "모바일 주요 탐색",
        "labels": ["홈", "설문", "근태", "매칭", "더보기"],
        "more": "추가 탐색 옵션 열기",
    },
}


def test_mobile_bottom_navigation_has_localized_markup_contract():
    required_markup = [
        'class="mobile-bottom-nav" aria-label="モバイル主要ナビゲーション" '
        'data-i18n-aria-label="mobile_navigation_label"',
        '<span class="mobile-nav-label" data-i18n="mobile_nav_home">ホーム</span>',
        '<span class="mobile-nav-label" data-i18n="mobile_nav_survey">アンケート</span>',
        '<span class="mobile-nav-label" data-i18n="mobile_nav_attendance">勤怠</span>',
        '<span class="mobile-nav-label" data-i18n="mobile_nav_matching">マッチング</span>',
        '<span class="mobile-nav-label" data-i18n="mobile_nav_more">その他</span>',
        'aria-label="その他のメニューを開く" '
        'data-i18n-aria-label="mobile_nav_more_menu_label"',
    ]

    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")
        for markup in required_markup:
            assert markup in html, (html_file, markup)
        for values in EXPECTED.values():
            for value in [values["landmark"], *values["labels"], values["more"]]:
                assert f'"{value}"' in html, (html_file, value)


def test_mobile_bottom_navigation_tracks_language_persistence_and_current_page(fastapi_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            http_credentials={"username": "test-admin", "password": "test-password"},
        )
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")
        navigation = page.locator(".mobile-bottom-nav")
        more_button = navigation.locator(".mobile-nav-btn")

        assert navigation.is_visible()
        for language, expected in EXPECTED.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert page.evaluate("document.documentElement.lang") == language
            assert navigation.get_attribute("aria-label") == expected["landmark"]
            assert navigation.locator(".mobile-nav-label").all_text_contents() == expected["labels"]
            assert more_button.get_attribute("aria-label") == expected["more"]
            assert navigation.locator(".mobile-nav-label").evaluate_all(
                "labels => labels.every(label => label.scrollWidth <= label.parentElement.clientWidth)"
            )

        navigation.locator('[data-nav="matching-section"]').click()
        assert navigation.locator('[data-nav="matching-section"]').get_attribute("aria-current") == "page"

        page.reload(wait_until="domcontentloaded")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert navigation.get_attribute("aria-label") == EXPECTED["ko"]["landmark"]
        assert navigation.locator(".mobile-nav-label").all_text_contents() == EXPECTED["ko"]["labels"]
        assert more_button.get_attribute("aria-label") == EXPECTED["ko"]["more"]

        browser.close()
