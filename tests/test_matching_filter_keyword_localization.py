from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
KEYWORD_COPY = {
    "ja": ("フリーワード", "案件名・要員・送信元など"),
    "en": ("Keyword", "Project, talent, sender, etc."),
    "zh": ("关键词", "项目、人才、发件人等"),
    "ko": ("키워드", "프로젝트, 인재, 발신자 등"),
}


def test_matching_filter_keyword_has_localized_contract():
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        assert (
            '<label for="matching-filter-keyword" '
            'data-i18n="matching_filter_keyword_label">フリーワード</label>'
        ) in html
        assert 'data-i18n-placeholder="matching_filter_keyword_placeholder"' in html
        for label, placeholder in KEYWORD_COPY.values():
            assert f'matching_filter_keyword_label: "{label}"' in html
            assert f'matching_filter_keyword_placeholder: "{placeholder}"' in html


def test_matching_filter_keyword_tracks_language_without_losing_query(fastapi_server):
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

        label = page.locator('label[for="matching-filter-keyword"]')
        keyword_input = page.locator("#matching-filter-keyword")
        keyword_input.fill("AWS")

        for language, (expected_label, expected_placeholder) in KEYWORD_COPY.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert page.evaluate("document.documentElement.lang") == language
            assert label.text_content().strip() == expected_label
            assert keyword_input.get_attribute("placeholder") == expected_placeholder
            assert keyword_input.input_value() == "AWS"

        assert label.get_attribute("for") == "matching-filter-keyword"
        assert keyword_input.get_attribute("type") == "search"
        assert keyword_input.get_attribute("autocomplete") == "off"
        assert keyword_input.get_attribute("oninput") == "applyMatchingFilters()"
        page.evaluate(
            """() => document.getElementById('matching-filter-keyword')
                .dispatchEvent(new Event('input', { bubbles: true }))"""
        )

        page.reload(wait_until="domcontentloaded")
        page.evaluate("switchAppTab('#matching-section')")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert label.text_content().strip() == KEYWORD_COPY["ko"][0]
        assert keyword_input.get_attribute("placeholder") == KEYWORD_COPY["ko"][1]

        browser.close()
