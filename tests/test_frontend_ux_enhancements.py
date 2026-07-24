"""Test suite for verifying frontend UX, accessibility keyboard shortcuts, and i18n auto-detection (T768/T909)."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = PROJECT_ROOT / "index.html"


def test_browser_language_auto_detection_implemented():
    """Verify that initLang in index.html detects navigator.language for fallback."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "navigator.language" in html or "navigator.userLanguage" in html, \
        "initLang must inspect navigator.language for browser language auto-detection"


def test_media_print_stylesheet_exists():
    """Verify that @media print rules exist for interview guide PDF/print formatting."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "@media print" in html, "index.html must include @media print styles for print/PDF formatting"
    assert ".aptitude-interview-guide" in html or "#aptitude-interview-guide" in html


def test_keyboard_shortcuts_registered():
    """Verify that keyboard shortcut listeners (Alt+1, Alt+2, etc.) are registered in index.html."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "altKey" in html or "Alt+" in html, "index.html must contain keyboard shortcut logic"
    assert "targets[e.key]" in html or "key === '1'" in html or "code === 'Digit1'" in html or "e.key === '1'" in html, \
        "Keyboard shortcut for Alt+1..7 navigation must be present"


def test_interview_notes_field_exists():
    """Verify that an interview notes textarea is supported in the aptitude section."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "interview-notes" in html or "aptitude-interview-memo" in html, \
        "Interview notes memo field must exist in index.html"
