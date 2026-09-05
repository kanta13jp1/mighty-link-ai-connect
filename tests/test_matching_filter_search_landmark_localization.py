from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
SEARCH_LABELS = {
    "ja": "営業メールAIマッチングの絞り込み",
    "en": "Sales email AI matching filters",
    "zh": "销售邮件 AI 匹配筛选",
    "ko": "영업 메일 AI 매칭 필터",
}


def test_matching_filter_search_landmark_has_localized_contracts():
    expected_markup = (
        'class="matching-filter-toolbar" role="search" '
        'aria-label="営業メールAIマッチングの絞り込み" '
        'data-i18n-aria-label="matching_filter_search_label"'
    )
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        assert html.count(expected_markup) == 1
        for label in SEARCH_LABELS.values():
            assert f'matching_filter_search_label: "{label}"' in html


def test_matching_filter_search_landmark_name_tracks_language_and_persistence(
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
        page.goto(f"{fastapi_server}#matching-section", wait_until="domcontentloaded")
        page.evaluate("switchAppTab('#matching-section')")
        search_landmark = page.locator(".matching-filter-toolbar")

        for language, expected_label in SEARCH_LABELS.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert page.evaluate("document.documentElement.lang") == language
            assert search_landmark.get_attribute("role") == "search"
            assert search_landmark.get_attribute("aria-label") == expected_label

        page.locator("#matching-filter-keyword").fill("AWS")
        assert page.locator("#matching-filter-keyword").input_value() == "AWS"
        page.locator(".matching-filter-reset").click()
        assert page.locator("#matching-filter-keyword").input_value() == ""

        page.reload(wait_until="domcontentloaded")
        page.evaluate("switchAppTab('#matching-section')")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert search_landmark.get_attribute("role") == "search"
        assert search_landmark.get_attribute("aria-label") == SEARCH_LABELS["ko"]

        browser.close()
