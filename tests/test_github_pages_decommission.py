import sys
from pathlib import Path
from unittest.mock import Mock

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import verify_github_pages_decommission as pages_guard


RETIRED_PAGES_URL = "https://kanta13jp1.github.io/mighty-link-ai-connect/"
REPOSITORY = "kanta13jp1/mighty-link-ai-connect"


def mock_connection(status=200, body=b"{}"):
    connection = Mock()
    connection.getresponse.return_value.status = status
    connection.getresponse.return_value.read.return_value = body
    return connection


@pytest.mark.parametrize("api_url", ["https://api.github.com", "https://api.github.com/"])
@pytest.mark.parametrize("repository", [REPOSITORY, "owner/pages", "owner/.github"])
def test_https_transport_confirms_repository_then_pages_404(monkeypatch, api_url, repository):
    connections = [mock_connection(), mock_connection(status=404)]
    factory = Mock(side_effect=connections)
    monkeypatch.setattr(pages_guard.http.client, "HTTPSConnection", factory)

    result = pages_guard.verify_pages_decommissioned(
        repository, token="test-token", api_url=api_url,
    )

    assert result == {
        "repository": repository,
        "repository_status": 200,
        "pages_status": 404,
        "decommissioned": True,
    }
    assert factory.call_count == 2
    for index, connection in enumerate(connections):
        assert factory.call_args_list[index].args == ("api.github.com",)
        assert factory.call_args_list[index].kwargs == {"timeout": 30}
        suffix = "/pages" if index else ""
        connection.request.assert_called_once_with(
            "GET", f"/repos/{repository}{suffix}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer test-token",
                "User-Agent": "mighty-link-pages-decommission-guard/1.0",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        connection.close.assert_called_once_with()
    connections[1].getresponse.return_value.read.assert_not_called()


@pytest.mark.parametrize("repository", [
    "", "owner", "owner/repo/extra", "/owner/repo", "owner/..", "owner/.",
    "../repo", "owner/%2e%2e", "owner/repo?query=1", "owner/repo#fragment",
    "owner@attacker.invalid/repo", "owner/repo\\..", "owner/repo\n",
])
def test_invalid_repository_is_rejected_before_requester(repository):
    requester = Mock()
    with pytest.raises(pages_guard.PagesDecommissionError):
        pages_guard.verify_pages_decommissioned(
            repository, token="test-token", requester=requester,
        )
    requester.assert_not_called()


@pytest.mark.parametrize("api_url", [
    "http://api.github.com", "file:///tmp", "ftp://api.github.com",
    "https://api.github.com.attacker.invalid", "https://api.github.com@attacker.invalid",
    "https://user@api.github.com", "https://api.github.com:8443",
    "https://api.github.com:443", "https://api.github.com/path",
    "https://api.github.com?query=1", "https://api.github.com#fragment",
])
def test_invalid_api_origin_is_rejected_before_requester(api_url):
    requester = Mock()
    with pytest.raises(pages_guard.PagesDecommissionError):
        pages_guard.verify_pages_decommissioned(
            REPOSITORY, token="test-token", api_url=api_url, requester=requester,
        )
    requester.assert_not_called()


@pytest.mark.parametrize("url", [
    "http://api.github.com/repos/owner/repo",
    "file:///repos/owner/repo", "ftp://api.github.com/repos/owner/repo",
    "https://api.github.com.attacker.invalid/repos/owner/repo",
    "https://api.github.com@attacker.invalid/repos/owner/repo",
    "https://user@api.github.com/repos/owner/repo",
    "https://api.github.com:8443/repos/owner/repo",
    "https://api.github.com:443/repos/owner/repo",
    "https://api.github.com/repos/owner/../pages",
    "https://api.github.com/repos/owner/%2e%2e/pages",
    "https://api.github.com/repos/owner/repo?token=private",
    "https://api.github.com/repos/owner/repo#fragment",
    "https://api.github.com/repos/owner/repo/contents",
    "https://api.github.com/repos/owner/repo/pages/extra",
    "https://api.github.com/repos/owner/repo\r\nInjected: value",
])
def test_raw_github_get_rejects_invalid_url_before_connection(monkeypatch, url):
    factory = Mock()
    monkeypatch.setattr(pages_guard.http.client, "HTTPSConnection", factory)

    with pytest.raises(pages_guard.PagesDecommissionError):
        pages_guard.github_get(url, "test-token")
    factory.assert_not_called()


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize("redirect_stage", ["repository", "pages"])
def test_redirects_fail_without_following_location(monkeypatch, status, redirect_stage):
    redirect = mock_connection(status=status)
    redirect.getresponse.return_value.getheader.return_value = "https://attacker.invalid"
    connections = [redirect] if redirect_stage == "repository" else [mock_connection(), redirect]
    factory = Mock(side_effect=connections)
    monkeypatch.setattr(pages_guard.http.client, "HTTPSConnection", factory)

    with pytest.raises(pages_guard.PagesDecommissionError, match=f"HTTP {status}"):
        pages_guard.verify_pages_decommissioned(REPOSITORY, token="test-token")

    assert factory.call_count == len(connections)
    for connection in connections:
        connection.request.assert_called_once()
        connection.close.assert_called_once_with()
    redirect.getresponse.return_value.getheader.assert_not_called()
    redirect.getresponse.return_value.read.assert_not_called()


@pytest.mark.parametrize("failure_stage", ["construct", "request", "response", "read", "close"])
def test_transport_errors_are_redacted_and_connections_close(monkeypatch, capsys, failure_stage):
    secret = "test-token-that-must-never-be-printed"
    failure = OSError(f"transport failed at https://untrusted.invalid/{secret}")
    connection = mock_connection()
    factory = Mock(return_value=connection)
    if failure_stage == "construct":
        factory.side_effect = failure
    elif failure_stage == "request":
        connection.request.side_effect = failure
    elif failure_stage == "response":
        connection.getresponse.side_effect = failure
    elif failure_stage == "read":
        connection.getresponse.return_value.read.side_effect = failure
    else:
        connection.close.side_effect = failure
    monkeypatch.setattr(pages_guard.http.client, "HTTPSConnection", factory)
    monkeypatch.setenv("GITHUB_TOKEN", secret)

    assert pages_guard.main(["--repository", REPOSITORY, "--api-url", pages_guard.DEFAULT_API_URL]) == 1
    output = capsys.readouterr()
    assert output.out.strip() == (
        "[-] GitHub Pages decommission guard failed: "
        "GitHub API request failed or returned an invalid response"
    )
    assert output.err == ""
    if failure_stage != "construct":
        connection.close.assert_called_once_with()


@pytest.mark.parametrize("body", [b"not-json: test-secret", b"\xfftest-secret", b"[]"])
def test_invalid_json_response_fails_with_sanitized_error(monkeypatch, body):
    connection = mock_connection(body=body)
    monkeypatch.setattr(pages_guard.http.client, "HTTPSConnection", Mock(return_value=connection))

    with pytest.raises(pages_guard.PagesDecommissionError) as error:
        pages_guard.github_get(f"https://api.github.com/repos/{REPOSITORY}", "test-token")
    assert str(error.value) == "GitHub API request failed or returned an invalid response"
    assert error.value.__suppress_context__ is True
    connection.close.assert_called_once_with()


def test_enabled_pages_error_does_not_print_response_fields(monkeypatch, capsys):
    connections = [mock_connection(), mock_connection(body=b'{"build_type":"private-response-value"}')]
    monkeypatch.setattr(pages_guard.http.client, "HTTPSConnection", Mock(side_effect=connections))
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    assert pages_guard.main(["--repository", REPOSITORY, "--api-url", pages_guard.DEFAULT_API_URL]) == 1
    output = capsys.readouterr()
    assert output.out.strip() == "[-] GitHub Pages decommission guard failed: GitHub Pages is still enabled"
    assert output.err == ""


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
