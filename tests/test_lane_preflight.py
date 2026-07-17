"""T894 guard (written test-first): lane preflight aggregation.

The 16 domain guards each protect their own slice. This harness sits above them
and protects the property that *a lane cannot ship a red working tree*: every
scripts/audit_*.py is registered, every registered guard passes, has a CI path
(imported by some test) and emits evidence, the full pytest suite is green, and
AGENTS.md still documents the preflight command.

This suite pins the ten hypotheses the runner (scripts/run_lane_preflight.py)
verifies: a synthetic all-green baseline passes all ten, each injected defect
trips exactly its hypothesis, and the real repo is clean.

Note: evaluate() is pure and takes injected results, so this suite never shells
out to pytest (which would recurse).
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import run_lane_preflight as pre  # noqa: E402


def _ids(hyps):
    return {h["id"]: h for h in hyps}


def _good_registry():
    return {f"audit_g{i}.py": f"目的{i}" for i in range(1, 13)}


def _good_discovered():
    return set(_good_registry())


def _good_guard_results():
    return {name: {"exit_code": 0, "evidence": True} for name in _good_registry()}


def _good_pytest():
    return {"skipped": False, "failed": 0, "errors": 0, "collected": 458}


def _good_imports():
    return set(_good_registry())


def _good_exempt():
    return {"audit_ops_tool.py": "運用ツール: ローカル台帳依存のため対象外"}


def _good_discovered_with_exempt():
    return _good_discovered() | set(_good_exempt())


def _baseline(**overrides):
    kwargs = {
        "discovered": _good_discovered_with_exempt(),
        "registry": _good_registry(),
        "guard_results": _good_guard_results(),
        "pytest_result": _good_pytest(),
        "imported_guards": _good_imports(),
        "test_file_count": 74,
        "closeout_has_preflight": True,
        "exempt": _good_exempt(),
    }
    kwargs.update(overrides)
    return pre.evaluate(**kwargs)


def test_good_baseline_passes_all_ten():
    hyps = _baseline()
    assert len(hyps) == 10
    assert [h["id"] for h in hyps if not h["passed"]] == []


def test_h1_flags_too_few_guards():
    hyps = _ids(_baseline(discovered={"audit_g1.py"}, registry={"audit_g1.py": "x"},
                          guard_results={"audit_g1.py": {"exit_code": 0, "evidence": True}},
                          imported_guards={"audit_g1.py"}, exempt={}))
    assert hyps["H1"]["passed"] is False


def test_h1_flags_too_few_test_files():
    assert _ids(_baseline(test_file_count=3))["H1"]["passed"] is False


def test_h2_flags_unclassified_guard():
    """A new audit_*.py in neither partition must not be silently skipped."""
    discovered = _good_discovered_with_exempt() | {"audit_brand_new.py"}
    hyps = _ids(_baseline(discovered=discovered))
    assert hyps["H2"]["passed"] is False
    assert "audit_brand_new.py" in hyps["H2"]["detail"]


def test_h2_accepts_a_guard_classified_as_exempt():
    """Exempting is a valid decision; it must not read as unclassified."""
    discovered = _good_discovered_with_exempt() | {"audit_local_only.py"}
    exempt = dict(_good_exempt())
    exempt["audit_local_only.py"] = "運用ツール: 対象外"
    hyps = _ids(_baseline(discovered=discovered, exempt=exempt))
    assert hyps["H2"]["passed"] is True


def test_h3_flags_stale_registry_entry():
    registry = dict(_good_registry())
    registry["audit_deleted.py"] = "削除済み"
    hyps = _ids(_baseline(registry=registry))
    assert hyps["H3"]["passed"] is False
    assert "audit_deleted.py" in hyps["H3"]["detail"]


def test_h3_flags_stale_exempt_entry():
    exempt = dict(_good_exempt())
    exempt["audit_gone.py"] = "削除済み"
    hyps = _ids(_baseline(exempt=exempt))
    assert hyps["H3"]["passed"] is False
    assert "audit_gone.py" in hyps["H3"]["detail"]


def test_exempt_guards_are_not_required_to_pass_or_emit_evidence():
    """Exempt guards are never executed, so they must not gate the commit."""
    hyps = _ids(_baseline())
    assert hyps["H4"]["passed"] is True
    assert hyps["H7"]["passed"] is True
    assert hyps["H8"]["passed"] is True


def test_h4_flags_failing_guard():
    results = dict(_good_guard_results())
    results["audit_g2.py"] = {"exit_code": 1, "evidence": True}
    hyps = _ids(_baseline(guard_results=results))
    assert hyps["H4"]["passed"] is False
    assert "audit_g2.py" in hyps["H4"]["detail"]


def test_h5_flags_failing_tests():
    hyps = _ids(_baseline(pytest_result={"skipped": False, "failed": 3, "errors": 0,
                                         "collected": 458}))
    assert hyps["H5"]["passed"] is False
    assert "3" in hyps["H5"]["detail"]


def test_h5_flags_test_errors():
    hyps = _ids(_baseline(pytest_result={"skipped": False, "failed": 0, "errors": 2,
                                         "collected": 458}))
    assert hyps["H5"]["passed"] is False


def test_h5_and_h6_pass_but_are_marked_skipped_in_fast_mode():
    """Fast mode does not run pytest; H5/H6 must pass yet say so explicitly."""
    hyps = _ids(_baseline(pytest_result={"skipped": True, "failed": 0, "errors": 0,
                                         "collected": 0}))
    assert hyps["H5"]["passed"] is True
    assert hyps["H6"]["passed"] is True
    assert "高速モード" in hyps["H5"]["detail"]
    assert "高速モード" in hyps["H6"]["detail"]


def test_h6_flags_suite_shrinkage():
    hyps = _ids(_baseline(pytest_result={"skipped": False, "failed": 0, "errors": 0,
                                         "collected": 12}))
    assert hyps["H6"]["passed"] is False


def test_h7_flags_guard_without_ci_path():
    """A guard no test imports never runs in CI."""
    imported = set(_good_imports())
    imported.discard("audit_g5.py")
    hyps = _ids(_baseline(imported_guards=imported))
    assert hyps["H7"]["passed"] is False
    assert "audit_g5.py" in hyps["H7"]["detail"]


def test_h8_flags_missing_evidence():
    results = dict(_good_guard_results())
    results["audit_g3.py"] = {"exit_code": 0, "evidence": False}
    hyps = _ids(_baseline(guard_results=results))
    assert hyps["H8"]["passed"] is False
    assert "audit_g3.py" in hyps["H8"]["detail"]


def test_h9_flags_closeout_drift():
    hyps = _ids(_baseline(closeout_has_preflight=False))
    assert hyps["H9"]["passed"] is False


def test_h10_fails_when_any_prior_hypothesis_fails():
    hyps = _ids(_baseline(closeout_has_preflight=False))
    assert hyps["H10"]["passed"] is False


def test_h10_passes_only_on_clean_baseline():
    assert _ids(_baseline())["H10"]["passed"] is True


# --- discovery / binding against the real repository -------------------------

def test_discover_guards_finds_real_audit_scripts():
    found = pre.discover_guards()
    assert len(found) >= 10
    assert all(n.startswith("audit_") and n.endswith(".py") for n in found)
    assert "audit_uat_api_coverage.py" in found


def test_partition_matches_real_guards_exactly():
    """H2/H3 on the real repo: the partition and disk agree."""
    discovered = pre.discover_guards()
    classified = set(pre.GUARD_REGISTRY) | set(pre.EXEMPT_GUARDS)
    assert discovered - classified == set(), "未分類ガードあり"
    assert classified - discovered == set(), "stale分類あり"


def test_partition_is_disjoint():
    assert set(pre.GUARD_REGISTRY) & set(pre.EXEMPT_GUARDS) == set()


def test_every_classified_guard_has_a_purpose_or_reason_note():
    for mapping in (pre.GUARD_REGISTRY, pre.EXEMPT_GUARDS):
        assert all(str(v).strip() for v in mapping.values())


def test_declared_evidence_is_read_from_the_guard_not_guessed():
    """Artefact names do not track script names; guessing caused a false positive."""
    assert pre.declared_evidence("audit_issue_qa_blockers.py") == "issue_qa_blocker_audit.md"
    assert pre.declared_evidence("audit_uat_api_coverage.py") == "uat_api_coverage_audit.md"


def test_declared_evidence_is_none_for_a_guard_that_declares_no_export():
    assert pre.declared_evidence("audit_external_api_usage.py") is None


def test_every_preflight_guard_declares_an_evidence_artefact():
    missing = [g for g in pre.GUARD_REGISTRY if pre.declared_evidence(g) is None]
    assert missing == [], f"証跡未宣言: {missing}"


def test_imported_guards_detects_real_test_bindings():
    imported = pre.find_imported_guards()
    assert "audit_uat_api_coverage.py" in imported
    # naming convention differs across guards; import-based detection must cover both
    assert "audit_sales_email_hardening.py" in imported


def test_real_repo_has_no_guard_without_ci_path():
    missing = set(pre.GUARD_REGISTRY) - pre.find_imported_guards()
    assert missing == set(), f"CI実行経路なし: {sorted(missing)}"


def test_real_agents_md_documents_the_preflight():
    assert pre.closeout_documents_preflight() is True
    env = pre.utf8_subprocess_env({"PATH": "test-path", "PYTHONUTF8": "0"})
    assert env["PATH"] == "test-path"
    assert env["PYTHONUTF8"] == "1"
    assert env["PYTHONIOENCODING"] == "utf-8"


def test_render_markdown_contains_verdict_and_all_ten_rows():
    report = {
        "task": "T894",
        "mode": "full",
        "guard_count": 12,
        "test_file_count": 74,
        "hypotheses": _baseline(),
        "all_passed": True,
    }
    md = pre.render_markdown(report)
    assert "総合判定" in md
    for i in range(1, 11):
        assert f"| H{i} |" in md
