import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import run_ga_acceptance_e2e as ga


def test_current_local_date_uses_iso_today():
    assert ga.current_local_date() == ga.datetime.now().astimezone().date().isoformat()


def test_in_process_ga_flows_all_pass():
    # skip_network keeps the app-tier E2E deterministic (no external calls).
    report = ga.build_report("2026-07-08", timeout=5, skip_network=True)
    in_process = [h for h in report["hypotheses"] if h["id"] != "H10"]
    failing = [h["id"] for h in in_process if not h["passed"]]
    assert len(in_process) == 9
    assert failing == [], f"unexpected failing GA flows: {failing}"


def test_report_shape_and_scope_note():
    report = ga.build_report("2026-07-08", timeout=5, skip_network=True)
    assert report["report_id"] == "GA_ACCEPTANCE_E2E_T845_1"
    assert report["hypotheses_total"] == 10
    assert "T921" in report["scope_note"]
    assert "最終UATサインオフを代替しない" in report["scope_note"]
    assert report["external_evidence"]["executed"] is False


def test_consent_enforcement_hypothesis_present():
    report = ga.build_report("2026-07-08", timeout=5, skip_network=True)
    h4 = next(h for h in report["hypotheses"] if h["id"] == "H4")
    assert h4["passed"] is True
