from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "index.html"
CSS_PATH = ROOT / "styles.css"
JS_PATH = ROOT / "app.js"
PRODUCTS = ("Codex", "Claude Code", "Claude Cowork", "Kiro", "Antigravity")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cards: list[dict[str, str]] = []
        self.buttons: list[dict[str, str]] = []
        self.aria_live = 0
        self.external_refs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name: value or "" for name, value in attrs}
        classes = values.get("class", "").split()
        if "agent-card" in classes:
            self.cards.append(values)
        if tag == "button":
            self.buttons.append(values)
        if values.get("aria-live"):
            self.aria_live += 1
        for name in ("href", "src"):
            value = values.get(name, "")
            if value.startswith(("http://", "https://", "//")):
                self.external_refs.append(value)


class SiteContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = read(HTML_PATH)
        cls.css = read(CSS_PATH)
        cls.javascript = read(JS_PATH)
        cls.parser = SiteParser()
        cls.parser.feed(cls.html)

    def test_t01_required_files_exist(self) -> None:
        for path in (HTML_PATH, CSS_PATH, JS_PATH):
            self.assertTrue(path.is_file(), f"missing: {path.name}")

    def test_t02_title_and_site_name(self) -> None:
        self.assertIn("<title>AI Agent Learning Hub</title>", self.html)
        self.assertIn("AI Agent Learning Hub", self.html)

    def test_t03_five_product_cards(self) -> None:
        self.assertEqual(len(self.parser.cards), 5)
        for product in PRODUCTS:
            self.assertIn(product, self.html)

    def test_t04_required_learning_content(self) -> None:
        for label in ("向いている仕事", "主な機能", "最初の一歩", "研修用サンプル"):
            self.assertIn(label, self.html)
        self.assertIn("assets/workshop-hero.png", self.html)

    def test_t05_synthetic_and_offline_boundary(self) -> None:
        self.assertIn("SYNTHETIC_DATA_ONLY", self.html)
        self.assertEqual(self.parser.external_refs, [])
        for forbidden in ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage"):
            self.assertNotIn(forbidden, self.javascript)

    def test_t06_filter_counts_are_5_4_1_5(self) -> None:
        filters = {
            button.get("data-filter")
            for button in self.parser.buttons
            if button.get("data-filter")
        }
        self.assertEqual(filters, {"all", "coding", "knowledge", "planning"})
        counts = [
            len(self.parser.cards),
            sum("coding" in card.get("data-tags", "").split() for card in self.parser.cards),
            sum("knowledge" in card.get("data-tags", "").split() for card in self.parser.cards),
            sum("planning" in card.get("data-tags", "").split() for card in self.parser.cards),
        ]
        self.assertEqual(counts, [5, 4, 1, 5])

    def test_t07_compare_is_limited_to_two(self) -> None:
        select_buttons = [
            button for button in self.parser.buttons if "select-button" in button.get("class", "").split()
        ]
        self.assertEqual(len(select_buttons), 5)
        self.assertRegex(self.javascript, r"selectedAgents\.size\s*>=\s*2")
        self.assertIn("比較できるのは2製品までです", self.javascript)

    def test_t08_accessible_state_is_announced(self) -> None:
        state_buttons = [button for button in self.parser.buttons if button.get("data-filter") or "select-button" in button.get("class", "")]
        self.assertTrue(state_buttons)
        self.assertTrue(all("aria-pressed" in button for button in state_buttons))
        self.assertGreaterEqual(self.parser.aria_live, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
