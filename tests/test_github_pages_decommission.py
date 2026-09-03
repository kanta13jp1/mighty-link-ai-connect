import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import verify_github_pages_decommission as pages_guard


RETIRED_PAGES_URL = "https://kanta13jp1.github.io/mighty-link-ai-connect/"


def test_disabled_pages_site_passes_after_repository_access_is_confirmed():
    responses = iter([(200, {}), (404, {})])

    result = pages_guard.verify_pages_decommissioned(
        "kanta13jp1/mighty-link-ai-connect",
        token="test-token",
        requester=lambda _url, _token: next(responses),
    )

    assert result["repository_status"] == 200
    assert result["pages_status"] == 404
    assert result["decommissioned"] is True


def test_enabled_pages_site_fails_closed():
    responses = iter([(200, {}), (200, {"build_type": "legacy"})])

    with pytest.raises(pages_guard.PagesDecommissionError, match="still enabled"):
        pages_guard.verify_pages_decommissioned(
            "kanta13jp1/mighty-link-ai-connect",
            token="test-token",
            requester=lambda _url, _token: next(responses),
        )


def test_inaccessible_repository_is_not_mistaken_for_disabled_pages():
    with pytest.raises(pages_guard.PagesDecommissionError, match="repository access"):
        pages_guard.verify_pages_decommissioned(
            "kanta13jp1/mighty-link-ai-connect",
            token="test-token",
            requester=lambda _url, _token: (404, {}),
        )


def test_unexpected_pages_status_fails_closed():
    responses = iter([(200, {}), (403, {})])

    with pytest.raises(pages_guard.PagesDecommissionError, match="HTTP 403"):
        pages_guard.verify_pages_decommissioned(
            "kanta13jp1/mighty-link-ai-connect",
            token="test-token",
            requester=lambda _url, _token: next(responses),
        )


def test_active_operational_scripts_do_not_target_retired_pages_site():
    active_scripts = [
        "capture_demo_screenshots.py",
        "generate_branded_ceo_deck.py",
        "generate_ceo_presentation_deck.py",
        "generate_monthly_quality_report.py",
        "run_external_pentest_review.py",
        "run_ga_acceptance_e2e.py",
    ]

    for filename in active_scripts:
        content = (PROJECT_ROOT / "scripts" / filename).read_text(encoding="utf-8")
        assert RETIRED_PAGES_URL not in content, filename
