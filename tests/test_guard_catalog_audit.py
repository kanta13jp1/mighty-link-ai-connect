"""T903 test spec (written test-first): quality-guard catalog sync guard.

UAT TS-33 (docs/UAT_TEST_SPECIFICATION.md): the lane preflight now runs 18
quality guards, but there is no human-readable index of what each guard
protects, how it fails (NG example), and which WBS it relates to; and nothing
stops a newly registered guard from shipping undocumented. This suite pins the
guard's pure functions: the machine source of truth (GUARD_REGISTRY /
EXEMPT_GUARDS in run_lane_preflight) is read, the guards documented in the
catalog are parsed, and the two set differences — undocumented (registered but
not in catalog) and phantom (in catalog but neither registered nor exempt) —
are computed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import audit_guard_catalog as guard  # noqa: E402

SAMPLE_CATALOG = """# 品質ガードカタログ

## 法務・課金
### audit_legal_disclosures.py
- 守る対象: 法定開示の網羅
- NG例: 特商法の解約記載が消えると失敗
- 関連WBS: T900

### audit_pricing_consistency.py
- 守る対象: 料金ドリフト
- NG例: Standard価格が食い違うと失敗
- 関連WBS: T901

## 対象外(EXEMPT)
### audit_external_api_usage.py
- 対象外理由: ローカル台帳ツールのため
"""


def test_registered_guards_reads_machine_source_of_truth():
    reg = guard.registered_guards()
    assert isinstance(reg, set)
    assert "audit_legal_disclosures.py" in reg
    assert "audit_pricing_consistency.py" in reg
    assert len(reg) >= 15


def test_cataloged_guards_parses_headings():
    got = guard.cataloged_guards(SAMPLE_CATALOG)
    assert got == {
        "audit_legal_disclosures.py",
        "audit_pricing_consistency.py",
        "audit_external_api_usage.py",
    }


def test_undocumented_are_registered_but_absent_from_catalog():
    registered = {"a.py", "b.py", "c.py"}
    cataloged = {"a.py"}
    assert guard.undocumented_guards(registered, cataloged) == {"b.py", "c.py"}


def test_phantom_are_cataloged_but_neither_registered_nor_exempt():
    cataloged = {"a.py", "ghost.py"}
    known = {"a.py"}  # registry ∪ exempt
    assert guard.phantom_guards(cataloged, known) == {"ghost.py"}


def test_no_drift_when_catalog_matches_known_set():
    known = {"a.py", "b.py"}
    cataloged = {"a.py", "b.py"}
    assert guard.undocumented_guards(known, cataloged) == set()
    assert guard.phantom_guards(cataloged, known) == set()


def test_evaluate_passes_on_the_real_repo():
    results = guard.evaluate()
    assert isinstance(results, list) and len(results) == 10
    failed = [r["id"] for r in results if not r["passed"]]
    assert not failed, f"guard-catalog hypotheses failing on real repo: {failed}"
