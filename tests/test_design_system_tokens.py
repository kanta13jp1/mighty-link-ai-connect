"""Test suite for verifying design system tokens, SVG interactive visuals, and mobile navigation attributes (T768/T909/T917)."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = PROJECT_ROOT / "index.html"


def test_design_system_css_tokens_defined():
    """Verify that CSS tokens for glassmorphism panels and theme-adaptive glow exist in index.html."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "--glass-panel-bg" in html, "index.html must define --glass-panel-bg CSS variable"
    assert "data-theme=\"light\"" in html, "Light mode CSS theme rules must be present"


def test_svg_visual_containers_exist():
    """Verify that SVG chart containers for Ops Analytics and Aptitude Gauges exist in index.html."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "ops-trend-svg" in html, "Ops trend SVG container must exist"
    assert "ops-donut-svg" in html, "Ops donut SVG container must exist"
    assert "aptitude-gauge-svg" in html, "Aptitude gauge SVG container must exist"


def test_mobile_bottom_nav_aria_current_supported():
    """Verify that mobile bottom navigation supports dynamic aria-current update."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "mobile-bottom-nav" in html, "Mobile bottom navigation structure must exist"
    assert "aria-current" in html or "setActiveMobileNav" in html, \
        "Mobile bottom nav active state handler must be present"
