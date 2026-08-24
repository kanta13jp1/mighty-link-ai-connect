"""T920 regression guards for the public sales-email matching filters."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = [PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html"]


def html_sources() -> list[tuple[Path, str]]:
    return [(path, path.read_text(encoding="utf-8")) for path in HTML_FILES]


def test_filter_controls_exist_in_both_html_files():
    required_ids = {
        "matching-filter-keyword",
        "matching-filter-skill",
        "matching-filter-contract",
        "matching-filter-rate-min",
        "matching-filter-rate-max",
        "matching-filter-score",
        "matching-filter-received-from",
        "matching-filter-received-to",
        "matching-filter-count",
        "proposal-generation-modal",
    }

    for path, text in html_sources():
        for control_id in required_ids:
            assert f'id="{control_id}"' in text, f"{path} is missing {control_id}"
        assert "applyMatchingFilters()" in text
        assert "resetMatchingFilters()" in text
        assert "openProposalModal(" in text
        assert "copyProposalToClipboard()" in text
        assert "launchMailerWithProposal()" in text


def test_empty_filtered_results_do_not_fall_back_to_demo_rows():
    for path, text in html_sources():
        assert "const list = Array.isArray(dataList) ? dataList : matchingData;" in text, (
            f"{path} must preserve an explicit empty result list"
        )
        assert "const list = (dataList && dataList.length) ? dataList : matchingData;" not in text


def test_api_matches_are_enriched_with_project_filter_fields():
    required_fragments = {
        "project_required_skills:",
        "project_rate_min:",
        "project_rate_max:",
        "project_received_at:",
        "project_received_date:",
        "sender_domains:",
    }

    for path, text in html_sources():
        for fragment in required_fragments:
            assert fragment in text, f"{path} is missing API enrichment field {fragment}"


def test_skill_filter_uses_project_required_skills():
    for path, text in html_sources():
        assert "item.project_required_skills" in text, (
            f"{path} must filter against the project's required skills"
        )


def test_rate_filter_excludes_unknown_rates_and_checks_range_overlap():
    for path, text in html_sources():
        assert "function matchingRateOverlaps" in text
        assert "if (projectMin === null && projectMax === null) return false;" in text


def test_received_date_filter_refreshes_api_and_preserves_empty_results():
    required_fragments = {
        'params.set("received_from", receivedFrom)',
        'params.set("received_to", receivedTo)',
        "function matchingReceivedDateInRange",
        "function refreshSalesEmailMatchesForDateRange",
        "salesEmailMatchSourceReady ? salesEmailMatches : matchingData",
        'countElem.textContent = "受信日の期間を確認してください"',
        'document.getElementById("matching-filter-received-from").value = ""',
        'document.getElementById("matching-filter-received-to").value = ""',
    }

    for path, text in html_sources():
        for fragment in required_fragments:
            assert fragment in text, f"{path} is missing received-date behavior: {fragment}"
        assert 'colspan="7"' in text
        assert "<th>契約形態</th>" in text


def test_filter_toolbar_uses_scoped_responsive_styles():
    for path, text in html_sources():
        assert 'class="matching-filter-toolbar"' in text
        assert 'class="matching-date-range"' in text
        assert ".matching-filter-toolbar" in text
        assert ".matching-date-range" in text
        assert "@media (max-width: 700px)" in text
