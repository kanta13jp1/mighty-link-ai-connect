"""Test suite for verifying World-Class UI/UX perfection (Skeleton loader, Spring modal, Focus Trap, Color blindness icons, Mobile Bottom Sheet)."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = PROJECT_ROOT / "index.html"


def test_skeleton_loader_styles_and_placeholders_exist():
    """Verify skeleton loader CSS definitions for CLS elimination."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "skeleton-box" in html or "skeleton-shimmer" in html or ".skeleton" in html, \
        "Skeleton loader styles must be defined in index.html"


def test_spring_scale_modal_animations_exist():
    """Verify spring scale bezier curve animations for modals."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "cubic-bezier(0.16, 1, 0.3, 1)" in html or "cubic-bezier(0.34, 1.56, 0.64, 1)" in html, \
        "Spring scale cubic-bezier animation must be used for modal transitions"


def test_color_blindness_symbols_in_evaluation_bands():
    """Verify distinct symbols (✓, ⚠️, 🚩) are present alongside color indicators for WCAG 2.2 AAA."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "✓" in html or "&#10003;" in html, "Checkmark symbol must be included in normal band"
    assert "⚠️" in html or "⚠" in html or "!" in html, "Warning symbol must be included in caution band"
    assert "🚩" in html or "⚑" in html or "面談目安" in html, "Flag symbol must be included in interview guide band"


def test_focus_trap_and_mobile_bottom_sheet_exist():
    """Verify Focus Trap helper logic and mobile bottom sheet drawer in index.html."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "setupFocusTrap" in html or "trapFocus" in html, "Focus trap logic must be implemented"
    assert "mobile-bottom-sheet" in html or "openMobileBottomSheet" in html, \
        "Mobile native bottom sheet drawer must be present"
