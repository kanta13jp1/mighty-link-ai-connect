"""Test suite for verifying i18n coverage and dictionary completeness in index.html (T768)."""

from __future__ import annotations

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = PROJECT_ROOT / "index.html"


def parse_i18n_dict(html_content: str) -> dict[str, dict[str, str]]:
    """Extract and parse the inline JS i18nDict object from index.html."""
    match = re.search(r"const\s+i18nDict\s*=\s*(\{[\s\S]*?\});\s*(?:function|let|const|var|\()", html_content)
    assert match, "i18nDict JS object must exist in index.html"
    dict_str = match.group(1)
    
    # Convert JS object syntax to valid JSON format for parsing
    # 1. Quote unquoted property keys
    json_str = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)\s*:', r'\1"\2":', dict_str)
    # 2. Remove trailing commas
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse i18nDict JSON: {e}\nRaw snippet:\n{json_str[:300]}") from e


def test_i18n_dict_exists_and_has_four_languages():
    """Verify that i18nDict defines all required 4 languages (ja, en, zh, ko)."""
    assert INDEX_HTML.exists(), "index.html must exist"
    html = INDEX_HTML.read_text(encoding="utf-8")
    d = parse_i18n_dict(html)
    
    required_langs = {"ja", "en", "zh", "ko"}
    assert required_langs.issubset(set(d.keys())), f"i18nDict must include all 4 languages: {required_langs}"


def test_i18n_dict_key_symmetry():
    """Verify that all keys present in the Japanese dictionary exist in en, zh, and ko."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    d = parse_i18n_dict(html)
    
    ja_keys = set(d.get("ja", {}).keys())
    assert len(ja_keys) >= 40, f"Expected comprehensive i18n keys (at least 40), but found {len(ja_keys)}"
    
    for lang in ["en", "zh", "ko"]:
        lang_keys = set(d.get(lang, {}).keys())
        missing_keys = ja_keys - lang_keys
        assert not missing_keys, f"Language '{lang}' is missing i18n keys present in 'ja': {missing_keys}"


def test_html_data_i18n_attributes_defined_in_dict():
    """Verify that every data-i18n, data-i18n-placeholder, etc. in HTML is in i18nDict."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    d = parse_i18n_dict(html)
    ja_keys = set(d.get("ja", {}).keys())
    
    attr_patterns = [
        r'data-i18n="([^"]+)"',
        r'data-i18n-placeholder="([^"]+)"',
        r'data-i18n-html="([^"]+)"',
        r'data-i18n-aria-label="([^"]+)"',
    ]
    
    used_keys = set()
    for pat in attr_patterns:
        matches = re.findall(pat, html)
        used_keys.update(matches)
        
    assert used_keys, "HTML must contain data-i18n attributes"
    missing_in_dict = used_keys - ja_keys
    assert not missing_in_dict, f"HTML references data-i18n keys that are not defined in i18nDict: {missing_in_dict}"


def test_i18n_section_coverage():
    """Verify that key sections of the application have dedicated i18n keys."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    d = parse_i18n_dict(html)
    ja_keys = set(d.get("ja", {}).keys())
    
    expected_prefixes = [
        "nav_",        # Navigation
        "hero_",       # Hero section
        "onboard_",    # Onboarding
        "survey_",     # Aptitude survey
        "aptitude_",   # Aptitude demo
        "attendance_", # Attendance management
        "matching_",   # Sales email matching
        "admin_",      # Admin dashboard
        "auth_",       # Authentication
    ]
    
    for prefix in expected_prefixes:
        matching_keys = [k for k in ja_keys if k.startswith(prefix)]
        assert len(matching_keys) > 0, f"Expected i18n keys with prefix '{prefix}', but none were found"
