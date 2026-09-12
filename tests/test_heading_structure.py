"""Accessibility guards for the production document heading structure."""

from html.parser import HTMLParser
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PageHeadingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.headings: list[dict[str, object]] = []
        self._current: dict[str, object] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "h1":
            attributes = dict(attrs)
            self._current = {
                "classes": (attributes.get("class") or "").split(),
                "parts": [],
            }

    def handle_data(self, data: str) -> None:
        if self._current is not None:
            self._current["parts"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1" and self._current is not None:
            self.headings.append(self._current)
            self._current = None


@pytest.mark.parametrize("relative_path", ["index.html", "src/index.html"])
def test_production_html_has_one_branded_page_heading(relative_path: str) -> None:
    html = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
    parser = PageHeadingParser()
    parser.feed(html)

    assert len(parser.headings) == 1
    heading = parser.headings[0]
    assert " ".join("".join(heading["parts"]).split()) == "Mighty Skill-Bridge"
    assert "brand-title" in heading["classes"]
