from html.parser import HTMLParser
from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = (PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html")
MODAL_IDS = {"auth-modal", "shortcut-help-modal"}


class ModalAttributeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.modal_attributes: dict[str, dict[str, str | None]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id in MODAL_IDS:
            self.modal_attributes[element_id] = attributes


def test_hidden_modals_are_inert_in_both_html_entrypoints():
    for html_file in HTML_FILES:
        parser = ModalAttributeParser()
        parser.feed(html_file.read_text(encoding="utf-8"))

        assert set(parser.modal_attributes) == MODAL_IDS
        for modal_id, attributes in parser.modal_attributes.items():
            assert attributes.get("aria-hidden") == "true", (html_file, modal_id)
            assert "inert" in attributes, (html_file, modal_id)


def test_modal_open_close_keeps_inert_and_aria_hidden_in_sync(fastapi_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            http_credentials={"username": "test-admin", "password": "test-password"}
        )
        context.add_init_script(
            """
            localStorage.setItem(
                'mighty_auth_session',
                JSON.stringify({ email: 'qa@mightylink-app.com', token: 'mock' })
            );
            """
        )
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")
        page.wait_for_function("typeof openShortcutHelpModal === 'function'")

        for modal_id in MODAL_IDS:
            modal = page.locator(f"#{modal_id}")
            assert modal.get_attribute("aria-hidden") == "true"
            assert modal.evaluate("element => element.inert") is True

        page.locator("#run-analysis-btn").focus()
        page.evaluate("openShortcutHelpModal()")
        shortcut_modal = page.locator("#shortcut-help-modal")
        assert shortcut_modal.get_attribute("aria-hidden") == "false"
        assert shortcut_modal.evaluate("element => element.inert") is False
        assert page.evaluate(
            "document.querySelector('#shortcut-help-modal').contains(document.activeElement)"
        )

        page.evaluate("closeShortcutHelpModal()")
        assert shortcut_modal.get_attribute("aria-hidden") == "true"
        assert shortcut_modal.evaluate("element => element.inert") is True
        assert page.evaluate("document.activeElement.id") == "run-analysis-btn"

        page.evaluate("openAuthModal('login')")
        auth_modal = page.locator("#auth-modal")
        assert auth_modal.get_attribute("aria-hidden") == "false"
        assert auth_modal.evaluate("element => element.inert") is False

        page.evaluate("closeAuthModal(true)")
        assert auth_modal.get_attribute("aria-hidden") == "true"
        assert auth_modal.evaluate("element => element.inert") is True

        browser.close()
