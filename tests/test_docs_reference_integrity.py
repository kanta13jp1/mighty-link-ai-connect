"""T891 guard (written test-first): documentation reference integrity.

Every markdown link under docs/ must be a portable, repo-relative reference that
resolves — no `file:///` absolute paths, no links escaping the repo, no dangling
targets. This suite pins the ten hypotheses the audit
(scripts/audit_docs_reference_integrity.py) verifies: classify() labels each link
kind correctly, a synthetic all-resolving link set passes all ten, each injected
defect trips exactly its hypothesis, and the real docs/ tree is clean.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_docs_reference_integrity as audit  # noqa: E402


def _repo(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "data").mkdir()
    md = tmp_path / "docs" / "a.md"
    md.write_text("placeholder", encoding="utf-8")
    (tmp_path / "docs" / "b.md").write_text("y", encoding="utf-8")
    (tmp_path / "scripts" / "s.py").write_text("", encoding="utf-8")
    (tmp_path / "data" / "d.tsv").write_text("", encoding="utf-8")
    (tmp_path / "root.txt").write_text("", encoding="utf-8")
    return md


# --------------------------------------------------------------------------- #
# classify()
# --------------------------------------------------------------------------- #
def test_classify_http_is_skipped(tmp_path):
    md = _repo(tmp_path)
    assert audit.classify(md, "https://example.com", tmp_path)["kind"] == "skip"


def test_classify_resolving_doc_is_ok(tmp_path):
    md = _repo(tmp_path)
    c = audit.classify(md, "b.md", tmp_path)
    assert c["kind"] == "ok" and c["category"] == "docs"


def test_classify_code_and_data_categories(tmp_path):
    md = _repo(tmp_path)
    assert audit.classify(md, "../scripts/s.py", tmp_path)["category"] == "code"
    assert audit.classify(md, "../data/d.tsv", tmp_path)["category"] == "data"
    assert audit.classify(md, "../root.txt", tmp_path)["category"] == "other"


def test_classify_missing_is_broken(tmp_path):
    md = _repo(tmp_path)
    assert audit.classify(md, "missing.md", tmp_path)["kind"] == "broken"


def test_classify_fileurl_and_external(tmp_path):
    md = _repo(tmp_path)
    assert audit.classify(md, "file:///c:/x/y.md", tmp_path)["kind"] == "fileurl"
    assert audit.classify(md, "../../outside.md", tmp_path)["kind"] == "external"


# --------------------------------------------------------------------------- #
# evaluate(): synthetic good baseline + per-hypothesis defect injection
# --------------------------------------------------------------------------- #
def _good(md):
    return [(md, "b.md"), (md, "../scripts/s.py"), (md, "../data/d.tsv"), (md, "b.md#sec")]


def _ids(hyps):
    return {h["id"]: h for h in hyps}


def test_good_baseline_passes_all_ten(tmp_path):
    md = _repo(tmp_path)
    hyps = audit.evaluate(_good(md), tmp_path, doc_count=60)
    assert len(hyps) == 10
    assert [h["id"] for h in hyps if not h["passed"]] == []


def test_h1_flags_too_few_docs(tmp_path):
    md = _repo(tmp_path)
    assert _ids(audit.evaluate(_good(md), tmp_path, doc_count=10))["H1"]["passed"] is False


def test_h2_flags_fileurl(tmp_path):
    md = _repo(tmp_path)
    links = _good(md) + [(md, "file:///c:/x/y.md")]
    assert _ids(audit.evaluate(links, tmp_path, 60))["H2"]["passed"] is False


def test_h3_flags_external(tmp_path):
    md = _repo(tmp_path)
    links = _good(md) + [(md, "../../outside.md")]
    assert _ids(audit.evaluate(links, tmp_path, 60))["H3"]["passed"] is False


def test_h4_flags_broken_doc_link(tmp_path):
    md = _repo(tmp_path)
    links = _good(md) + [(md, "missing.md")]
    assert _ids(audit.evaluate(links, tmp_path, 60))["H4"]["passed"] is False


def test_h5_flags_broken_code_link(tmp_path):
    md = _repo(tmp_path)
    links = _good(md) + [(md, "../scripts/missing.py")]
    assert _ids(audit.evaluate(links, tmp_path, 60))["H5"]["passed"] is False


def test_h6_flags_broken_data_link(tmp_path):
    md = _repo(tmp_path)
    links = _good(md) + [(md, "../data/missing.tsv")]
    assert _ids(audit.evaluate(links, tmp_path, 60))["H6"]["passed"] is False


def test_h7_flags_broken_other_link(tmp_path):
    md = _repo(tmp_path)
    links = _good(md) + [(md, "../nope.bin")]
    assert _ids(audit.evaluate(links, tmp_path, 60))["H7"]["passed"] is False


def test_h8_flags_broken_anchored_link(tmp_path):
    md = _repo(tmp_path)
    links = _good(md) + [(md, "missing.md#section")]
    hyps = _ids(audit.evaluate(links, tmp_path, 60))
    assert hyps["H8"]["passed"] is False


def test_h9_and_h10_flag_any_broken(tmp_path):
    md = _repo(tmp_path)
    links = _good(md) + [(md, "missing.md")]
    hyps = _ids(audit.evaluate(links, tmp_path, 60))
    assert hyps["H9"]["passed"] is False
    assert hyps["H10"]["passed"] is False


# --------------------------------------------------------------------------- #
# Integration: the real docs/ tree
# --------------------------------------------------------------------------- #
def test_real_docs_reference_integrity_is_clean():
    report = audit.run_audit()
    failing = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert report["all_passed"] is True, failing
