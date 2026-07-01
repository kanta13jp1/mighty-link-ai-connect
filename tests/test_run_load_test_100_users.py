import scripts.run_load_test_100_users as load_probe


def test_percentile_uses_nearest_rank():
    values = [10.0, 20.0, 30.0, 40.0]

    assert load_probe.percentile(values, 50) == 20.0
    assert load_probe.percentile(values, 95) == 40.0


def test_summary_and_sla_pass_for_successful_metrics():
    metrics = [
        load_probe.RequestMetric("/api/health", "GET", 200, 10.0, 1, True),
        load_probe.RequestMetric("/api/parse", "POST", 200, 1000.0, 1, True),
        load_probe.RequestMetric("/api/match", "POST", 200, 1500.0, 1, True),
    ]

    summary = load_probe.summarize_metrics(metrics)
    sla = load_probe.evaluate_sla(summary)

    assert summary["total_requests"] == 3
    assert summary["total_errors"] == 0
    assert summary["by_endpoint"]["/api/match"]["p95_ms"] == 1500.0
    assert sla["overall_pass"] is True


def test_sla_fails_when_endpoint_has_error():
    metrics = [
        load_probe.RequestMetric("/api/health", "GET", 200, 10.0, 1, True),
        load_probe.RequestMetric("/api/parse", "POST", 500, 120.0, 1, False, "boom"),
    ]

    summary = load_probe.summarize_metrics(metrics)
    sla = load_probe.evaluate_sla(summary)

    assert summary["total_errors"] == 1
    assert sla["overall_pass"] is False
    assert sla["endpoint_results"]["/api/parse"]["error_free"] is False


def test_load_probe_configures_fast_deterministic_delays(tmp_path):
    app_module = load_probe.configure_test_app(tmp_path)

    assert app_module.DETERMINISTIC_PARSE_DELAY_SECONDS == load_probe.DEFAULT_PARSE_DELAY_SECONDS
    assert app_module.DETERMINISTIC_MATCH_DELAY_SECONDS == load_probe.DEFAULT_MATCH_DELAY_SECONDS
