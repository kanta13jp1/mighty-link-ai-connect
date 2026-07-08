"""T877_1 light-theme toggle: static, browser-free verification.

The CEO demo default (dark) must be byte-safe, so these tests assert the change
is ADDITIVE and correctly wired without a browser: required demo markers survive,
both index files stay identical, the light palette + toggle + persistence exist,
and the default remains dark.
"""

import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
SRC_INDEX = ROOT / "src" / "index.html"

REQUIRED_MARKERS = [
    "Mighty Skill-Bridge",
    "エンジニア＆案件 AIフィットシミュレーター",
    "bridge-btn",
    "runAnalysis()",
    "knowledge-flow-demo",
    "generateKnowledgeFlowArtifacts",
    "sampleEngineer",
    "radarChart",
]


@pytest.fixture(scope="module")
def html():
    return INDEX.read_text(encoding="utf-8")


# H1: both index files remain byte-identical (mirror invariant)
def test_h1_index_files_identical():
    assert INDEX.read_text(encoding="utf-8") == SRC_INDEX.read_text(encoding="utf-8")


# H2: all public-demo markers survive the edit
def test_h2_demo_markers_preserved(html):
    missing = [m for m in REQUIRED_MARKERS if m not in html]
    assert missing == [], f"missing markers: {missing}"


# H3: valid, parseable HTML
def test_h3_html_parses(html):
    HTMLParser().feed(html)


# H4: light palette defined via data-theme without touching the dark :root
def test_h4_light_theme_block_present(html):
    assert ':root[data-theme="light"]' in html
    # dark default still declares near-black bg on the base :root
    assert "--bg: #030303;" in html
    # light overrides bg to white
    light_block = html.split(':root[data-theme="light"]', 1)[1][:400]
    assert "--bg: #ffffff;" in light_block


# H5: toggle button wired with accessibility attributes
def test_h5_toggle_button_present(html):
    assert 'id="theme-toggle"' in html
    assert 'onclick="toggleTheme()"' in html
    assert 'aria-label="配色モードを切り替え"' in html
    assert 'aria-pressed=' in html


# H6: toggle JS applies/removes data-theme and updates aria-pressed
def test_h6_toggle_js_logic(html):
    assert "function toggleTheme()" in html
    assert "function applyTheme(theme)" in html
    assert 'setAttribute("data-theme", "light")' in html
    assert 'removeAttribute("data-theme")' in html


# H7: theme persisted in localStorage under a stable key
def test_h7_persistence(html):
    assert 'localStorage.setItem("msb-theme"' in html
    assert 'localStorage.getItem("msb-theme")' in html


# H8: default is dark — light only when explicitly saved
def test_h8_default_dark(html):
    assert 'applyTheme(saved === "light" ? "light" : "dark")' in html
    # the base <html>/:root has no data-theme attribute hard-coded
    assert not re.search(r'<html[^>]*data-theme=', html)


# H9: additive-only — the original dark rules are untouched (unique count checks)
def test_h9_additive_only(html):
    # the anchor rule we appended after still exists exactly once
    assert html.count(".card-stat.stat-yellow { color: var(--yellow); }") == 1
    # base body still uses its original dark gradient stack
    assert "#030303" in html
    # light theme keeps video surfaces dark for contrast
    assert "video surfaces stay dark for contrast" in html


# H10: toggle lives in the header tools, not buried
def test_h10_toggle_in_topbar(html):
    tools = html.split('class="topbar-tools"', 1)[1].split("</header>", 1)[0]
    assert 'id="theme-toggle"' in tools
