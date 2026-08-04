"""Tests for UI Japanese Help & FAQ Guide integration (T926)."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = PROJECT_ROOT / "index.html"
SRC_INDEX_HTML = PROJECT_ROOT / "src" / "index.html"


def test_help_modal_elements_exist_in_html() -> None:
    """Verify that Japanese help modal elements exist in both index.html and src/index.html."""
    for html_file in [INDEX_HTML, SRC_INDEX_HTML]:
        assert html_file.is_file(), f"Missing file: {html_file}"
        content = html_file.read_text(encoding="utf-8")
        
        # Check help modal trigger and modal ID
        assert 'id="matching-help-modal"' in content, f"Missing matching-help-modal in {html_file.name}"
        assert 'onclick="openMatchingHelpModal()"' in content, f"Missing help trigger in {html_file.name}"
        
        # Check polite Japanese explanation text
        assert "営業メールAIマッチング進捗の使い方" in content, f"Missing help title in {html_file.name}"
        assert "適合度（マッチングスコア）" in content, f"Missing score explanation in {html_file.name}"
        assert "管理者統合ダッシュボード" in content, f"Missing admin dashboard reference in {html_file.name}"


def test_help_modal_closing_and_accessibility() -> None:
    """Verify closing button and accessibility labels in Japanese help modal."""
    for html_file in [INDEX_HTML, SRC_INDEX_HTML]:
        content = html_file.read_text(encoding="utf-8")
        assert 'onclick="closeMatchingHelpModal()"' in content
        assert 'aria-label="閉じる"' in content or 'aria-label="営業メールマッチングの使い方を表示"' in content
