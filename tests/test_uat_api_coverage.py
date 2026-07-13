"""T892 guard (written test-first): UAT <-> API coverage traceability.

Every GA user-facing endpoint must have a human-executable UAT case, and every
src/app.py endpoint must be classified as REQUIRED or EXEMPT. This suite pins the
ten hypotheses the audit (scripts/audit_uat_api_coverage.py) verifies: a
synthetic fully-classified/fully-covered baseline passes all ten, each injected
defect trips exactly its hypothesis, and the real repo is clean.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_uat_api_coverage as audit  # noqa: E402


def _ids(hyps):
    return {h["id"]: h for h in hyps}


def _good_endpoints():
    return set(audit.REQUIRED_GA_ENDPOINTS) | set(audit.EXEMPT_ENDPOINTS)


def _good_uat():
    return set(audit.REQUIRED_GA_ENDPOINTS)


def test_load_endpoints_filters_to_api_surface():
    eps = audit.load_endpoints()
    assert all(e.startswith("/api/") for e in eps)
    assert len(eps) >= 30


def test_good_baseline_passes_all_ten():
    hyps = audit.evaluate(_good_endpoints(), _good_uat(), uat_case_count=22)
    assert len(hyps) == 10
    assert [h["id"] for h in hyps if not h["passed"]] == []


def test_h1_flags_too_few_cases():
    hyps = _ids(audit.evaluate(_good_endpoints(), _good_uat(), uat_case_count=5))
    assert hyps["H1"]["passed"] is False


def test_h2_flags_uat_api_not_in_app():
    uat = _good_uat() | {"/api/ghost-endpoint"}
    hyps = _ids(audit.evaluate(_good_endpoints(), uat, 22))
    assert hyps["H2"]["passed"] is False


def test_h3_flags_uncovered_required_endpoint():
    dropped = next(iter(audit.REQUIRED_GA_ENDPOINTS))
    uat = _good_uat() - {dropped}
    hyps = _ids(audit.evaluate(_good_endpoints(), uat, 22))
    assert hyps["H3"]["passed"] is False


def test_h4_flags_unclassified_endpoint():
    eps = _good_endpoints() | {"/api/brand-new-unclassified"}
    hyps = _ids(audit.evaluate(eps, _good_uat(), 22))
    assert hyps["H4"]["passed"] is False


def test_h5_flags_required_exempt_overlap(monkeypatch):
    overlap_member = next(iter(audit.EXEMPT_ENDPOINTS))  # an exempt endpoint
    req = set(audit.REQUIRED_GA_ENDPOINTS) | {overlap_member}
    monkeypatch.setattr(audit, "REQUIRED_GA_ENDPOINTS", req)
    eps = req | set(audit.EXEMPT_ENDPOINTS)
    hyps = _ids(audit.evaluate(eps, req, 22))
    assert hyps["H5"]["passed"] is False


def test_h6_flags_stale_required():
    dropped = next(iter(audit.REQUIRED_GA_ENDPOINTS))
    eps = _good_endpoints() - {dropped}  # a required endpoint no longer in app.py
    hyps = _ids(audit.evaluate(eps, _good_uat(), 22))
    assert hyps["H6"]["passed"] is False


def test_h7_flags_stale_exempt():
    dropped = next(iter(audit.EXEMPT_ENDPOINTS))
    eps = _good_endpoints() - {dropped}
    hyps = _ids(audit.evaluate(eps, _good_uat(), 22))
    assert hyps["H7"]["passed"] is False


def test_h8_flags_missing_core_domain():
    # drop every sales-email required endpoint from UAT coverage
    uat = {e for e in _good_uat() if not e.startswith("/api/sales-email/")}
    hyps = _ids(audit.evaluate(_good_endpoints(), uat, 22))
    assert hyps["H8"]["passed"] is False


def test_h9_and_h10_flag_partial_coverage():
    dropped = next(iter(audit.REQUIRED_GA_ENDPOINTS))
    uat = _good_uat() - {dropped}
    hyps = _ids(audit.evaluate(_good_endpoints(), uat, 22))
    assert hyps["H9"]["passed"] is False
    assert hyps["H10"]["passed"] is False


# --------------------------------------------------------------------------- #
# Integration: the real repository
# --------------------------------------------------------------------------- #
def test_real_uat_api_coverage_is_complete():
    report = audit.run_audit()
    failing = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert report["all_passed"] is True, failing
