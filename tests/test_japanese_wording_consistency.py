"""Tests for Japanese UI/UX Wording and Glossary Consistency Guard (T917)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest

from audit_japanese_wording_consistency import (
    FORBIDDEN_RAW_ERROR_STRINGS,
    REQUIRED_GLOSSARY_TERMS,
    STYLE_GUIDE_FILE,
    audit_japanese_wording,
    check_forbidden_raw_errors,
    check_glossary_presence,
    check_style_guide_exists,
    check_ui_files_exist,
    write_exports,
)


def test_style_guide_file_exists() -> None:
    """Verify that docs/JAPANESE_UI_UX_STYLE_GUIDE.md exists and is valid."""
    assert STYLE_GUIDE_FILE.is_file()
    result = check_style_guide_exists()
    assert result["status"] == "PASS"


def test_ui_files_exist() -> None:
    """Verify that both index.html and src/index.html exist."""
    result = check_ui_files_exist()
    assert result["status"] == "PASS"


def test_check_forbidden_raw_errors_clean() -> None:
    """Verify that forbidden raw error check works on clean content."""
    clean_html = "<div>保存が完了しました。入力内容をご確認ください。</div>"
    violations = check_forbidden_raw_errors(clean_html, "test.html")
    assert not violations


def test_check_forbidden_raw_errors_detects_forbidden() -> None:
    """Verify that forbidden raw error strings are detected."""
    bad_html = "<div>400 Bad Request</div>"
    violations = check_forbidden_raw_errors(bad_html, "test.html")
    assert len(violations) == 1
    assert "400 Bad Request" in violations[0]


def test_check_glossary_presence_detects_missing() -> None:
    """Verify missing glossary terms are identified."""
    incomplete_html = "<div>営業メールAIマッチング</div>"
    missing = check_glossary_presence(incomplete_html, "test.html")
    assert len(missing) == len(REQUIRED_GLOSSARY_TERMS) - 1


def test_full_japanese_wording_audit_passes() -> None:
    """Verify the full audit pipeline returns overall PASS."""
    res = audit_japanese_wording()
    assert res["overall_status"] == "PASS", f"Violations: {res.get('violations')}"
    assert res["hypotheses"]["H10_wording_consistency_score"]["score"] == 100


def test_write_exports_creates_valid_files(tmp_path: Path) -> None:
    """Verify write_exports generates readable JSON and MD files."""
    audit_data = audit_japanese_wording()
    json_p = tmp_path / "test_audit.json"
    md_p = tmp_path / "test_audit.md"

    write_exports(audit_data, json_p, md_p)

    assert json_p.is_file()
    assert md_p.is_file()

    parsed = json.loads(json_p.read_text(encoding="utf-8"))
    assert parsed["overall_status"] == "PASS"

    md_content = md_p.read_text(encoding="utf-8")
    assert "日本語表記・UI文言整合性監査レポート" in md_content
