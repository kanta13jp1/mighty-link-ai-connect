from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
CONTRACT_OPTIONS = {
    "ja": ["すべて", "準委任", "派遣", "請負", "正社員/契約社員"],
    "en": ["All", "Quasi-mandate", "Temporary staffing", "Contract work", "Permanent/contract employee"],
    "zh": ["全部", "准委托", "派遣", "承包", "正式员工/合同员工"],
    "ko": ["전체", "준위임", "파견", "도급", "정규직/계약직"],
}
OPTION_KEYS = [
    "matching_filter_contract_option_all",
    "matching_filter_contract_option_quasi_mandate",
    "matching_filter_contract_option_temporary_staffing",
    "matching_filter_contract_option_contract_work",
    "matching_filter_contract_option_employee",
]
OPTION_VALUES = ["", "準委任", "派遣", "請負", "正社員/契約社員"]


def test_matching_filter_contract_options_have_localized_contract():
    for html_file in HTML_FILES:
        html = html_file.read_text(encoding="utf-8")

        for key, value in zip(OPTION_KEYS, OPTION_VALUES, strict=True):
            assert html.count(f'<option value="{value}" data-i18n="{key}">') == 1
        for language_options in CONTRACT_OPTIONS.values():
            for key, label in zip(OPTION_KEYS, language_options, strict=True):
                assert f'{key}: "{label}"' in html


def test_matching_filter_contract_options_track_language_and_selection(fastapi_server):
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

        select = page.locator("#matching-filter-contract")
        select.select_option("派遣")

        for language, expected_options in CONTRACT_OPTIONS.items():
            page.evaluate("language => switchLanguage(language)", language)
            assert page.evaluate("document.documentElement.lang") == language
            assert select.locator("option").all_text_contents() == expected_options
            assert select.input_value() == "派遣"

        assert select.locator("option").evaluate_all("options => options.map(option => option.value)") == OPTION_VALUES
        assert select.get_attribute("onchange") == "applyMatchingFilters()"

        page.reload(wait_until="domcontentloaded")
        page.evaluate("switchAppTab('#matching-section')")
        assert page.evaluate("document.documentElement.lang") == "ko"
        assert select.locator("option").all_text_contents() == CONTRACT_OPTIONS["ko"]

        browser.close()
