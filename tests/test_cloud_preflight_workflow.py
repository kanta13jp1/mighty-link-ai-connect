"""Contract tests for the secret-free GitHub-hosted full preflight gate (T997)."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "cloud-preflight.yml"


def _workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_candidate_push_pr_and_manual_triggers_are_pinned():
    text = _workflow()
    assert '"codex/preflight/**"' in text
    assert '"codex/preflight-*"' in text
    assert '"codex/cloud-first-preflight-t997"' in text
    assert "pull_request:" in text
    assert "      - main" in text
    assert "      - master" in text
    assert "workflow_dispatch:" in text


def test_workflow_is_read_only_and_has_no_secret_context():
    text = _workflow()
    assert "permissions:\n  contents: read" in text
    assert "secrets." not in text
    assert "id-token: write" not in text


def test_workflow_runs_the_exact_full_gate_on_github_hosted_python():
    text = _workflow()
    assert "runs-on: ubuntu-latest" in text
    assert "uses: actions/checkout@v6" in text
    assert "uses: actions/setup-python@v6" in text
    assert 'python-version: "3.12"' in text
    assert "cache: pip" in text
    assert "playwright install chromium" in text
    assert "run: python scripts/run_lane_preflight.py --full" in text


def test_diagnostics_are_uploaded_for_success_and_failure_with_short_retention():
    text = _workflow()
    assert "if: always()" in text
    assert "uses: actions/upload-artifact@v6" in text
    assert "name: cloud-preflight-${{ github.sha }}" in text
    assert "exports/lane_preflight_report.json" in text
    assert "exports/lane_preflight_report.md" in text
    assert "exports/lane_preflight_pytest.xml" in text
    assert "exports/lane_preflight_pytest.log" in text
    assert "retention-days: 7" in text
