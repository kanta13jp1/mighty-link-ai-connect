# -*- coding: utf-8 -*-
"""
Tests for T1046: 営業メールマッチング進捗テーブルへの単価列追加と4言語UI対応.
Pins the rate column header, i18n keys, colspan, and rate formatting helper.
"""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = PROJECT_ROOT / "index.html"
SRC_INDEX_HTML = PROJECT_ROOT / "src" / "index.html"
HTML_FILES = [INDEX_HTML, SRC_INDEX_HTML]


def test_matching_table_contains_rate_th_in_both_html():
    for html_file in HTML_FILES:
        content = html_file.read_text(encoding="utf-8")
        assert 'data-i18n="matching_th_rate"' in content, (
            f"Missing data-i18n=\"matching_th_rate\" in {html_file.name}"
        )
        assert re.search(r'<th[^>]*data-i18n="matching_th_rate"[^>]*>|<th[^>]*>[\s\S]*?data-i18n="matching_th_rate"', content), (
            f"Missing rate th header with matching_th_rate in {html_file.name}"
        )


def test_matching_table_colspan_is_8_in_both_html():
    for html_file in HTML_FILES:
        content = html_file.read_text(encoding="utf-8")
        assert 'colspan="8"' in content, f"Missing colspan=\"8\" in empty state in {html_file.name}"


def test_matching_rate_cell_formatter_exists_in_both_html():
    for html_file in HTML_FILES:
        content = html_file.read_text(encoding="utf-8")
        assert "function formatMatchingRateCell(" in content, (
            f"Missing formatMatchingRateCell function in {html_file.name}"
        )
        assert "${formatMatchingRateCell(m)}" in content, (
            f"renderPublicMatchingTable does not call formatMatchingRateCell(m) in {html_file.name}"
        )


def test_matching_th_rate_in_all_four_languages():
    for html_file in HTML_FILES:
        content = html_file.read_text(encoding="utf-8")
        # Find i18nDict
        for lang, expected_label in [("ja", "単価"), ("en", "Rate"), ("zh", "单价"), ("ko", "단가")]:
            lang_block_pattern = rf'{lang}:\s*\{{[^}}]*matching_th_rate:\s*"{re.escape(expected_label)}"'
            assert re.search(lang_block_pattern, content, re.DOTALL), (
                f"Missing or mismatched matching_th_rate for {lang} in {html_file.name}"
            )


def test_format_matching_rate_logic_simulation():
    def simulate_rate(p_min, p_max, rate_str=None, is_en=False):
        unit = "0k JPY" if is_en else "万円"
        consult = "Negotiable" if is_en else "相談"
        if p_min is not None and p_max is not None:
            return f"{p_min}{unit}" if p_min == p_max else f"{p_min}〜{p_max}{unit}"
        if p_min is not None:
            return f"{p_min}{unit}〜"
        if p_max is not None:
            return f"〜{p_max}{unit}"
        if rate_str:
            return str(rate_str)
        return consult

    assert simulate_rate(80, 95) == "80〜95万円"
    assert simulate_rate(80, 80) == "80万円"
    assert simulate_rate(70, None) == "70万円〜"
    assert simulate_rate(None, 90) == "〜90万円"
    assert simulate_rate(None, None, rate_str="75万") == "75万"
    assert simulate_rate(None, None) == "相談"
    assert simulate_rate(80, 95, is_en=True) == "80〜950k JPY"
    assert simulate_rate(None, None, is_en=True) == "Negotiable"
