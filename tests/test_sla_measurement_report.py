import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import verify_sla_measurement_views as verify


def _report_mod():
    return verify._load_report_module()


# ---- evaluate() SLA threshold logic ----

def test_evaluate_pass_when_all_metrics_meet_targets():
    mod = _report_mod()
    checks = mod.evaluate({
        "kpi_monthly_availability": [{"availability_pct": 99.9}, {"availability_pct": 99.6}],
        "kpi_daily_response_time": [{"p95_ms": 1500.0}, {"p95_ms": 2900.0}],
        "kpi_weekly_diagnosis_accuracy": [{"helpful_pct": 75.0}],
    })
    assert all(c["pass"] is True for c in checks)


def test_evaluate_flags_each_breach():
    mod = _report_mod()
    checks = mod.evaluate({
        "kpi_monthly_availability": [{"availability_pct": 98.0}],       # < 99.5
        "kpi_daily_response_time": [{"p95_ms": 3200.0}],                 # > 3000
        "kpi_weekly_diagnosis_accuracy": [{"helpful_pct": 65.0}],        # < 70
    })
    failed = {c["metric"].split()[0] for c in checks if c["pass"] is False}
    assert failed == {"availability_pct", "p95_ms", "helpful_pct"}


def test_evaluate_uses_worst_case_not_average():
    mod = _report_mod()
    # one bad month among good ones must fail availability (worst-case semantics)
    checks = mod.evaluate({
        "kpi_monthly_availability": [{"availability_pct": 99.99}, {"availability_pct": 99.0}],
        "kpi_daily_response_time": [{"p95_ms": 100.0}, {"p95_ms": 4000.0}],
    })
    by = {c["metric"].split()[0]: c for c in checks}
    assert by["availability_pct"]["pass"] is False
    assert by["p95_ms"]["pass"] is False


def test_evaluate_no_data_is_none_not_crash():
    mod = _report_mod()
    checks = mod.evaluate({})
    assert len(checks) == 3
    assert all(c["pass"] is None for c in checks)


# ---- schema-drift guard ----

def test_schema_parser_finds_expected_tables_and_columns():
    schema = verify.parse_schema_columns()
    assert "matches" in schema
    assert {"created_at", "user_id", "fit_score"}.issubset(schema["matches"])
    assert {"created_at", "rating"}.issubset(schema["feedback_events"])
    assert {"checked_at", "target_id", "status", "response_ms"}.issubset(schema["uptime_checks"])


def test_drift_guard_catches_missing_column():
    # Simulate a schema where matches lost fit_score; H1 must fail.
    schema = verify.parse_schema_columns()
    schema["matches"] = schema["matches"] - {"fit_score"}
    mod = _report_mod()
    hyps = verify.build_hypotheses(schema, mod)
    h1 = next(h for h in hyps if h["id"] == "H1")
    assert h1["passed"] is False
    assert "fit_score" in h1["detail"]


def test_all_hypotheses_pass_on_real_repo():
    report = verify.build_report("2026-07-08")
    failing = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert failing == [], f"unexpected failing hypotheses: {failing}"
    assert report["status"] == "ok"
