"""T904 test spec (written test-first): doc ID-reference integrity guard.

UAT TS-34 (docs/UAT_TEST_SPECIFICATION.md): docs reference WBS/issue/QA IDs in
prose; when an ID is renumbered, removed, or mistyped the reference dangles and
the doc silently goes stale (this guard would have caught the QA-135→QA-136
renumber breakage in LEGAL_REVIEW_SIGNOFF_TRACKER.md). This suite pins the
guard's pure functions: valid IDs are read from the trackers, IDs referenced in
a doc are extracted, and the dangling set is the referenced IDs that are neither
valid nor allowlisted (known historical/provisional references).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import audit_doc_id_references as guard  # noqa: E402


def test_valid_ids_reads_trackers():
    wbs, issues, qa = guard.valid_ids()
    assert "T901" in wbs and "T904" not in ("",)  # WBS present and non-empty
    assert len(wbs) >= 100
    assert any(x.startswith("QA-") for x in qa)
    assert any(x.startswith("R") for x in issues)


def test_referenced_ids_extracts_all_three_families():
    text = "T901 を QA-138 で検証、課題 R143 参照。文中の Rev や T9 は無視。"
    got = guard.referenced_ids(text)
    assert "T901" in got
    assert "QA-138" in got
    assert "R143" in got
    assert "T9" not in got, "a 1-2 digit T-token is not a WBS id"


def test_referenced_ids_handles_subtask_suffix():
    assert "T862_1" in guard.referenced_ids("T862_1 の意思決定パッケージ")


def test_dangling_excludes_valid_and_allowlisted():
    referenced = {"T901", "T999", "QA-135"}
    valid = {"T901"}
    allowlist = {"QA-135"}
    assert guard.dangling(referenced, valid, allowlist) == {"T999"}


def test_dangling_empty_when_all_resolve():
    assert guard.dangling({"T901", "QA-138"}, {"T901", "QA-138"}, set()) == set()


def test_allowlist_ids_is_the_documented_exception_set():
    al = guard.allowlist_ids()
    assert isinstance(al, set)
    # the known historical/provisional references are covered
    assert "T720" in al and "T726" in al
    assert "T775" in al


def test_evaluate_passes_on_the_real_repo():
    results = guard.evaluate()
    assert isinstance(results, list) and len(results) == 10
    failed = [r["id"] for r in results if not r["passed"]]
    assert not failed, f"doc-id-reference hypotheses failing on real repo: {failed}"
