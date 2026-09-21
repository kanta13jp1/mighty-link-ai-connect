"""Contract tests for the secret-free GitHub-hosted full preflight gate (T997)."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "cloud-preflight.yml"


def _workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_candidate_push_manual_and_reusable_triggers_are_pinned():
    text = _workflow()
    assert '"codex/preflight/**"' in text
    assert '"codex/preflight-*"' in text
    assert '"codex/cloud-first-preflight-t997"' in text
    assert "  workflow_call:" in text
    assert "  pull_request:" not in text
    assert "workflow_dispatch:" in text


def test_workflow_is_read_only_and_has_no_secret_context():
    text = _workflow()
    assert "permissions:\n  contents: read" in text
    assert "secrets." not in text
    assert "id-token: write" not in text


def test_workflow_runs_the_exact_full_gate_on_github_hosted_python():
    text = _workflow()
    assert "runs-on: ubuntu-latest" in text
    assert "uses: actions/checkout@v7" in text
    assert "uses: actions/setup-python@v7" in text
    assert 'python-version: "3.12"' in text
    assert "cache: pip" in text
    assert "playwright install chromium" in text
    assert "run: python scripts/run_lane_preflight.py --full" in text


def test_diagnostics_are_uploaded_for_success_and_failure_with_short_retention():
    text = _workflow()
    assert "if: always()" in text
    assert "uses: actions/upload-artifact@v7" in text
    assert "name: cloud-preflight-${{ github.sha }}" in text
    assert "exports/lane_preflight_report.json" in text
    assert "exports/lane_preflight_report.md" in text
    assert "exports/lane_preflight_pytest.xml" in text
    assert "exports/lane_preflight_pytest.log" in text
    assert "retention-days: 7" in text


def test_pr_has_one_full_gate_and_deployment_depends_on_its_success():
    caller = (ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
    assert "  pull_request:" in caller
    assert "      - main" in caller and "      - master" in caller
    assert "uses: ./.github/workflows/cloud-preflight.yml" in caller
    assert "needs: test" in caller
    assert "run_phase4_tests.py" not in caller
    assert "python -m py_compile src/app.py" in _workflow()
    assert "python scripts/verify_public_demo.py" in _workflow()
    assert "data/test_results.tsv" in _workflow()
    assert "data/security_log.tsv" in _workflow()


def test_non_pr_runs_do_not_share_cancellation_or_pending_groups():
    text = _workflow()
    assert "github.event_name == 'pull_request' && github.ref || github.run_id" in text
    assert "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in text
