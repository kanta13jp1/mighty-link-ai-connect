from html.parser import HTMLParser
from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
LANGUAGES = ("en", "zh", "ko", "ja")
LANGUAGE_MAINTENANCE_SCRIPTS = (
    PROJECT_ROOT / "scripts" / "fix_clean_i18n.py",
    PROJECT_ROOT / "scripts" / "fix_lang_switch_robust.py",
    PROJECT_ROOT / "scripts" / "debug_test_lang.py",
    PROJECT_ROOT / "scripts" / "run_debug_lang.py",
)


class LanguageSwitchParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_switcher = False
        self.controls: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        if tag == "div" and "language-switch" in classes:
            self.in_switcher = True
        elif self.in_switcher and attributes.get("data-lang"):
            self.controls.append((tag, attributes))

    def handle_endtag(self, tag: str) -> None:
        if self.in_switcher and tag == "div":
            self.in_switcher = False


def test_language_switch_uses_native_buttons_with_an_initial_pressed_state():
    for html_file in HTML_FILES:
        parser = LanguageSwitchParser()
        parser.feed(html_file.read_text(encoding="utf-8"))

        assert [attrs["data-lang"] for _, attrs in parser.controls] == list(LANGUAGES)
        assert all(tag == "button" for tag, _ in parser.controls)
        assert all(attrs.get("type") == "button" for _, attrs in parser.controls)
        assert [attrs.get("aria-pressed") for _, attrs in parser.controls] == [
            "false",
            "false",
            "false",
            "true",
        ]


def test_language_maintenance_scripts_do_not_reintroduce_link_controls():
    for script in LANGUAGE_MAINTENANCE_SCRIPTS:
        content = script.read_text(encoding="utf-8")
        assert ".language-switch a" not in content, script
        assert '<a href="javascript:void(0)" data-lang=' not in content, script


def test_language_switch_supports_space_enter_and_persists_pressed_state(fastapi_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            http_credentials={"username": "test-admin", "password": "test-password"},
        )
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")
        page.wait_for_function("typeof switchLanguage === 'function'")

        page.evaluate("switchLanguage('ja')")
        en_button = page.locator(".language-switch button[data-lang='en']")
        en_button.focus()
        page.keyboard.press("Space")
        page.wait_for_function("document.documentElement.lang === 'en'")

        for language in LANGUAGES:
            expected = "true" if language == "en" else "false"
            assert (
                page.locator(f".language-switch button[data-lang='{language}']")
                .get_attribute("aria-pressed")
                == expected
            )

        page.reload(wait_until="domcontentloaded")
        assert page.evaluate("document.documentElement.lang") == "en"
        assert en_button.get_attribute("aria-pressed") == "true"

        zh_button = page.locator(".language-switch button[data-lang='zh']")
        zh_button.focus()
        page.keyboard.press("Enter")
        page.wait_for_function("document.documentElement.lang === 'zh'")
        assert zh_button.get_attribute("aria-pressed") == "true"
        assert en_button.get_attribute("aria-pressed") == "false"

        browser.close()
