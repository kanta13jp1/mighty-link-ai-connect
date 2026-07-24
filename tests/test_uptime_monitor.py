import io
import json
import ssl
import sys
import urllib.error
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import check_uptime_targets as uptime


def make_target(**overrides):
    values = {
        "target_id": "demo",
        "name": "Demo",
        "url": "https://example.com/",
        "expected_status": 200,
        "timeout_seconds": 5,
        "allow_tls_error": False,
        "severity": "P1",
        "owner": "Codex",
        "notes": "test",
    }
    values.update(overrides)
    return uptime.UptimeTarget(**values)


def test_read_targets_from_tsv(tmp_path):
    tsv = tmp_path / "uptime_targets.tsv"
    tsv.write_text(
        "\t".join(
            [
                "target_id",
                "name",
                "url",
                "expected_status",
                "timeout_seconds",
                "allow_tls_error",
                "severity",
                "owner",
                "notes",
            ]
        )
        + "\n"
        + "demo\tDemo\thttps://example.com/\t200\t5\tfalse\tP1\tCodex\tpublic demo\n",
        encoding="utf-8",
    )

    targets = uptime.read_targets(tsv)

    assert len(targets) == 1
    assert targets[0].target_id == "demo"
    assert targets[0].allow_tls_error is False


def test_check_target_ok_with_expected_status():
    def fetcher(url, timeout_seconds, *, context=None):
        return uptime.FetchResult(status_code=200, final_url=url, elapsed_ms=123.4)

    result = uptime.check_target(make_target(), fetcher=fetcher)

    assert result.status == "ok"
    assert result.http_status == 200
    assert result.tls_verification == "strict"


def test_fetch_url_returns_http_error_status(monkeypatch):
    error = urllib.error.HTTPError(
        "https://example.com/",
        401,
        "Unauthorized",
        {},
        io.BytesIO(b""),
    )

    def raise_http_error(*args, **kwargs):
        raise error

    monkeypatch.setattr(uptime.urllib.request, "urlopen", raise_http_error)

    result = uptime.fetch_url("https://example.com/", 5)

    assert result.status_code == 401
    assert result.final_url == "https://example.com/"


def test_check_target_fails_on_unexpected_status():
    def fetcher(url, timeout_seconds, *, context=None):
        return uptime.FetchResult(status_code=503, final_url=url, elapsed_ms=50.0)

    result = uptime.check_target(make_target(), fetcher=fetcher)

    assert result.status == "failed"
    assert result.http_status == 503
    assert "expected HTTP 200" in result.error


def test_tls_error_can_fallback_to_warning():
    calls = []

    def fetcher(url, timeout_seconds, *, context=None):
        calls.append(context)
        if context is None:
            raise urllib.error.URLError(
                ssl.SSLCertVerificationError("hostname mismatch")
            )
        return uptime.FetchResult(status_code=200, final_url=url, elapsed_ms=80.0)

    result = uptime.check_target(
        make_target(allow_tls_error=True),
        fetcher=fetcher,
    )

    assert result.status == "warning"
    assert result.http_status == 200
    assert result.tls_verification == "fallback_unverified"
    assert len(calls) == 2


def test_main_writes_report_and_returns_zero_for_warning(tmp_path, monkeypatch):
    targets = tmp_path / "data" / "uptime_targets.tsv"
    targets.parent.mkdir(parents=True)
    targets.write_text(
        "target_id\tname\turl\texpected_status\ttimeout_seconds\tallow_tls_error\tseverity\towner\tnotes\n"
        "demo\tDemo\thttps://example.com/\t200\t5\tfalse\tP1\tCodex\ttest\n",
        encoding="utf-8",
    )
    report_path = tmp_path / "exports" / "uptime.json"

    monkeypatch.setattr(
        uptime,
        "check_target",
        lambda target: uptime.TargetResult(
            target_id=target.target_id,
            name=target.name,
            url=target.url,
            expected_status=target.expected_status,
            severity=target.severity,
            owner=target.owner,
            status="warning",
            http_status=200,
            elapsed_ms=10.0,
            final_url=target.url,
            tls_verification="fallback_unverified",
            error="certificate pending",
            notes=target.notes,
        ),
    )

    exit_code = uptime.main(
        [
            "--root",
            str(tmp_path),
            "--targets-path",
            "data/uptime_targets.tsv",
            "--report-path",
            "exports/uptime.json",
        ],
        env={},
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert report["task_id"] == "T743"
    assert report["summary"]["warning"] == 1
    assert "SLACK_WEBHOOK_URL" not in report_path.read_text(encoding="utf-8")


def test_slack_payload_omits_secret_url():
    report = {
        "summary": {"status": "failed", "ok": 0, "warning": 0, "failed": 1},
        "results": [
            {
                "target_id": "demo",
                "status": "failed",
                "url": "https://example.com/",
                "error": "HTTP 503",
            }
        ],
    }

    payload = uptime.slack_payload(report)

    assert "T743 uptime monitor: FAILED" in payload["text"]
    assert "hooks.slack.com" not in payload["text"]


def test_production_targets_cover_auth_gate_and_health():
    targets = uptime.read_targets(PROJECT_ROOT / "data" / "uptime_targets.tsv")
    expected_by_url = {target.url: target.expected_status for target in targets}

    assert expected_by_url["https://mightylink-app.com/"] == 401
    assert expected_by_url["https://mightylink-app.com/api/health"] == 200
    assert expected_by_url["https://mighty-link-ai-connect-13d22.web.app/"] == 401
