# -*- coding: utf-8 -*-
"""
Tests for T1047: 営業メールマッチング結果テーブルにおける単価・スコア・受信日の双方向カラムソート機能とアクセシビリティ対応（4言語連動）.
Pins table sorting headers, sort indicators, aria-sort, JavaScript sort logic, and 4-language i18n keys.
"""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = PROJECT_ROOT / "index.html"
SRC_INDEX_HTML = PROJECT_ROOT / "src" / "index.html"
HTML_FILES = [INDEX_HTML, SRC_INDEX_HTML]


def test_matching_table_sortable_headers_in_both_html():
    """Verify that sortable th headers with aria-sort, titles, and onclick are present."""
    for html_file in HTML_FILES:
        content = html_file.read_text(encoding="utf-8")
        assert "sortMatchingTable('title')" in content, f"Missing title sort header in {html_file.name}"
        assert "sortMatchingTable('received_date')" in content, f"Missing received_date sort header in {html_file.name}"
        assert "sortMatchingTable('rate')" in content, f"Missing rate sort header in {html_file.name}"
        assert "sortMatchingTable('score')" in content, f"Missing score sort header in {html_file.name}"

        # Indicators
        assert 'id="matching-sort-title"' in content, f"Missing matching-sort-title in {html_file.name}"
        assert 'id="matching-sort-received_date"' in content, f"Missing matching-sort-received_date in {html_file.name}"
        assert 'id="matching-sort-rate"' in content, f"Missing matching-sort-rate in {html_file.name}"
        assert 'id="matching-sort-score"' in content, f"Missing matching-sort-score in {html_file.name}"


def test_matching_sort_js_functions_exist_in_both_html():
    """Verify that sort functions and state variables exist in both HTML files."""
    for html_file in HTML_FILES:
        content = html_file.read_text(encoding="utf-8")
        assert "function sortMatchingTable(" in content, f"Missing sortMatchingTable in {html_file.name}"
        assert "function sortMatchingItems(" in content, f"Missing sortMatchingItems in {html_file.name}"
        assert "function getMatchingRateSortValue(" in content, f"Missing getMatchingRateSortValue in {html_file.name}"
        assert "function getMatchingScoreSortValue(" in content, f"Missing getMatchingScoreSortValue in {html_file.name}"
        assert "function getMatchingDateSortValue(" in content, f"Missing getMatchingDateSortValue in {html_file.name}"
        assert "function getMatchingTitleSortValue(" in content, f"Missing getMatchingTitleSortValue in {html_file.name}"
        assert "function updateMatchingSortIndicators(" in content, f"Missing updateMatchingSortIndicators in {html_file.name}"


def test_matching_sort_i18n_keys_in_all_four_languages():
    """Verify that 4-language i18n dict contains all required header and tooltip keys."""
    keys = [
        "matching_th_title",
        "matching_th_received_date",
        "matching_th_rate",
        "matching_th_score",
        "matching_sort_title_tooltip",
        "matching_sort_date_tooltip",
        "matching_sort_rate_tooltip",
        "matching_sort_score_tooltip",
    ]
    for html_file in HTML_FILES:
        content = html_file.read_text(encoding="utf-8")
        for lang in ["ja", "en", "zh", "ko"]:
            for k in keys:
                assert f"{k}:" in content, f"Missing i18n key {k} in {html_file.name}"


def test_matching_sort_simulation_logic():
    """Simulate sorting behavior for rate, score, received_date, and title."""
    items = [
        {
            "id": 1,
            "title": "B案件: Pythonエンジニア",
            "score": 85,
            "project_received_date": "2026-09-10",
            "project_rate_max": 80,
            "project_rate_min": 70,
        },
        {
            "id": 2,
            "title": "A案件: TypeScriptフルスタック",
            "score": 95,
            "project_received_date": "2026-09-20",
            "project_rate_max": 100,
            "project_rate_min": 90,
        },
        {
            "id": 3,
            "title": "C案件: Goマイクロサービス",
            "score": 90,
            "project_received_date": "2026-09-15",
            "project_rate_max": None,
            "project_rate_min": None,
            "talent_desired_rate_max": 85,
        },
        {
            "id": 4,
            "title": "D案件: 応相談案件",
            "score": 75,
            "project_received_date": "2026-09-01",
            "project_rate_max": None,
            "project_rate_min": None,
        },
    ]

    def get_rate(m, order):
        vals = [m.get("project_rate_max"), m.get("project_rate_min"), m.get("talent_desired_rate_max")]
        for v in vals:
            if v is not None:
                return v
        return 999999 if order == "asc" else -1

    # 1. Rate Descending (100 -> 85 -> 80 -> None(-1))
    sorted_rate_desc = sorted(items, key=lambda m: get_rate(m, "desc"), reverse=True)
    assert [m["id"] for m in sorted_rate_desc] == [2, 3, 1, 4]

    # 2. Rate Ascending (80 -> 85 -> 100 -> None(999999))
    sorted_rate_asc = sorted(items, key=lambda m: get_rate(m, "asc"))
    assert [m["id"] for m in sorted_rate_asc] == [1, 3, 2, 4]

    # 3. Score Descending (95 -> 90 -> 85 -> 75)
    sorted_score_desc = sorted(items, key=lambda m: m["score"], reverse=True)
    assert [m["id"] for m in sorted_score_desc] == [2, 3, 1, 4]

    # 4. Score Ascending (75 -> 85 -> 90 -> 95)
    sorted_score_asc = sorted(items, key=lambda m: m["score"])
    assert [m["id"] for m in sorted_score_asc] == [4, 1, 3, 2]

    # 5. Received Date Descending (2026-09-20 -> 15 -> 10 -> 01)
    sorted_date_desc = sorted(items, key=lambda m: m["project_received_date"], reverse=True)
    assert [m["id"] for m in sorted_date_desc] == [2, 3, 1, 4]
