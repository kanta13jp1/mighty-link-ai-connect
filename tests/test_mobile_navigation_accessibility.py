"""Accessibility guards for the mobile navigation disclosure button."""

from html.parser import HTMLParser
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class NavigationRelationshipParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.mobile_button_attrs: list[tuple[str, str | None]] | None = None
        self.element_ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            self.element_ids.add(element_id)
        if tag == "button" and element_id == "mobile-menu-btn":
            self.mobile_button_attrs = attrs


@pytest.mark.parametrize("relative_path", ["index.html", "src/index.html"])
def test_mobile_menu_controls_only_the_sidebar(relative_path: str) -> None:
    parser = NavigationRelationshipParser()
    parser.feed((PROJECT_ROOT / relative_path).read_text(encoding="utf-8"))

    assert parser.mobile_button_attrs is not None
    controls = [
        value
        for name, value in parser.mobile_button_attrs
        if name == "aria-controls"
    ]
    assert controls == ["global-sidebar"]
    assert controls[0] in parser.element_ids
