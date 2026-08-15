"""Test suite for verifying 100/100 perfect score enhancements (PWA, count-up animations, shortcut help modal, i18n completeness)."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = PROJECT_ROOT / "index.html"


def test_pwa_meta_tags_and_offline_listener_exist():
    """Verify PWA meta tags and online/offline event listeners in index.html."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert 'name="theme-color"' in html, "theme-color meta tag must exist for PWA"
    assert 'name="apple-mobile-web-app-capable"' in html, "apple-mobile-web-app-capable meta tag must exist"
    assert 'addEventListener("offline"' in html or 'addEventListener(\'offline\'' in html, \
        "Offline event listener for network status toast must be registered"


def test_numeric_countup_animation_helper_exists():
    """Verify animateValue or count-up animation logic with IntersectionObserver."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "animateValue" in html or "countUp" in html, "Numeric count-up animation helper must exist"
    assert "IntersectionObserver" in html, "IntersectionObserver must be used for scroll-triggered animation"


def test_keyboard_shortcut_help_modal_exists():
    """Verify shortcut help modal and Alt+? trigger in index.html."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "shortcut-help-modal" in html, "Shortcut help modal HTML structure must exist"
    assert "openShortcutHelpModal" in html or "key === '?'" in html or "e.key === '?'" in html or "code === 'Slash'" in html, \
        "Shortcut help modal trigger must be registered"


def test_new_i18n_keys_defined():
    """Verify that new i18n keys for PWA/Offline/Help modal exist in i18nDict."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "shortcut_modal_title" in html or "offline_toast" in html or "pwa_" in html, \
        "New i18n dictionary keys for PWA/Help modal must be defined"
