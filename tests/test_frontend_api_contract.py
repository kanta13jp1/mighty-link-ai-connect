"""T887 regression guard: the backend must keep returning the response fields the
frontend deep-reads, and the frontend must keep reading them.

This is the preventive capstone to T884/T885/T886, whose bugs all stemmed from a
frontend mishandling a backend response. Here we pin the *shape contract* itself:
if the backend renames/drops a field (e.g. `scores.skill`, `summary.work_hours`,
`attendance_import.summary.overtime_hours`) the dynamic checks go RED; if the
frontend stops reading a contracted field, the static checks go RED. Both mirrors
(index.html / src/index.html) are held to the same contract.

The heavy lifting (isolated TestClient probe + HTML cross-reference over 10
hypotheses) lives in scripts/audit_frontend_api_contract.py; this suite adds a
few direct assertions and pins the audit all-green.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import audit_frontend_api_contract as audit  # noqa: E402

INDEX_FILES = [PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html"]


# --------------------------------------------------------------------------- #
# has_path helper unit tests
# --------------------------------------------------------------------------- #
def test_has_path_traverses_dicts_and_first_list_element():
    obj = {"a": {"b": 1}, "qa": [{"question": "q"}]}
    assert audit.has_path(obj, "a.b")
    assert audit.has_path(obj, "qa.question")
    assert not audit.has_path(obj, "a.c")
    assert not audit.has_path(obj, "missing.x")


def test_has_path_empty_list_fails():
    assert not audit.has_path({"qa": []}, "qa.question")


# --------------------------------------------------------------------------- #
# Dynamic: the live backend responses satisfy the contract
# --------------------------------------------------------------------------- #
def test_backend_responses_satisfy_contract():
    resp = audit.probe_backend()
    checks = {
        "match": audit.MATCH_KEYS,
        "parse": audit.PARSE_KEYS,
        "punch": audit.PUNCH_KEYS,
        "approve": audit.APPROVE_KEYS,
    }
    for name, keys in checks.items():
        missing = [k for k in keys if not audit.has_path(resp.get(name, {}), k)]
        assert not missing, (name, missing)


# --------------------------------------------------------------------------- #
# Static: both HTML mirrors reference the contracted fields
# --------------------------------------------------------------------------- #
def test_both_html_mirrors_reference_contract_fields():
    all_refs = audit.MATCH_REFS + audit.PARSE_REFS + audit.PUNCH_REFS + audit.APPROVE_REFS
    for path in INDEX_FILES:
        text = path.read_text(encoding="utf-8", errors="replace")
        missing = [r for r in all_refs if r not in text]
        assert not missing, (path.name, missing)


# --------------------------------------------------------------------------- #
# Integration: the 10-hypothesis audit is all-green
# --------------------------------------------------------------------------- #
def test_audit_harness_all_hypotheses_pass():
    report = audit.evaluate()
    failing = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert report["all_passed"] is True, failing
    assert len(report["hypotheses"]) == 10
