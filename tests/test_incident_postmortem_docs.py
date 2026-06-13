from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_t810_postmortem_docs_exist_and_link_r44():
    runbook = PROJECT_ROOT / "docs" / "INCIDENT_POSTMORTEM_RUNBOOK.md"
    r44 = PROJECT_ROOT / "docs" / "POSTMORTEM_2026-06-11_R44_PRODUCTION_API_502.md"

    assert runbook.exists()
    assert r44.exists()

    runbook_text = runbook.read_text(encoding="utf-8")
    r44_text = r44.read_text(encoding="utf-8")

    assert "R44" in runbook_text
    assert "POSTMORTEM_2026-06-11_R44_PRODUCTION_API_502.md" in runbook_text
    assert "ASGIMiddleware" in r44_text
    assert "gunicorn" in r44_text
    assert "再発防止アクション" in r44_text


def test_t810_issue_tracker_has_postmortem_followup():
    issues = (PROJECT_ROOT / "data" / "issues_tracker.tsv").read_text(encoding="utf-8")

    assert "R56" in issues
    assert "INCIDENT_POSTMORTEM_RUNBOOK.md" in issues
    assert "POSTMORTEM_2026-06-11_R44_PRODUCTION_API_502.md" in issues
