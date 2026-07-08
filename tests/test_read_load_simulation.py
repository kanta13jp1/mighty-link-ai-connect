import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import simulate_read_load_distribution as sim


def test_erlang_c_matches_known_theory():
    # M/M/1: queueing probability equals utilization
    assert abs(sim.erlang_c(1, 0.6) - 0.6) < 1e-12
    # M/M/2 with 1 erlang offered: known closed form = 1/3
    assert abs(sim.erlang_c(2, 1.0) - 1.0 / 3.0) < 1e-12
    # Saturation clamps to 1
    assert sim.erlang_c(4, 4.0) == 1.0
    assert sim.erlang_c(4, 10.0) == 1.0


def test_queue_metrics_saturation_and_budget():
    saturated = sim.queue_metrics(arrival_per_s=2000.0, hold_ms=25.0, servers=4)
    assert saturated["saturated"] is True

    light = sim.queue_metrics(arrival_per_s=10.0, hold_ms=25.0, servers=4)
    assert light["saturated"] is False
    assert light["utilization"] < 0.1
    assert light["p95_wait_ms"] == 0.0  # queue probability below 5%


def test_instances_needed_monotonic_and_replica_effect():
    rps = 1441.0
    primary_only = sim.instances_needed(rps, sim.DB_HOLD_MS_BASELINE)
    offloaded = sim.instances_needed(rps * 0.51, sim.DB_HOLD_MS_BASELINE)
    assert primary_only > offloaded >= 1
    # More load never needs fewer instances
    assert sim.instances_needed(rps * 2, sim.DB_HOLD_MS_BASELINE) >= primary_only


def test_route_classification_matches_app_surface():
    routes = sim.classify_routes()
    assert routes["read_share"] > 0.5
    assert "/api/matches" in routes["primary_pinned_reads"]
    assert "/api/health" in routes["replica_safe_reads"]
    # writes never appear in read sets
    assert not set(routes["write_routes"]) & set(routes["read_routes"])


def test_safety_formula_within_supavisor_budget():
    used = sim.RECOMMENDED_MAX_INSTANCES * sim.POOL_MAX_PER_INSTANCE
    assert used <= sim.SUPAVISOR_CLIENT_CONN_BUDGET


def test_full_report_all_hypotheses_pass_without_fresh_load():
    report = sim.build_report("2026-07-08", fresh_load_result=None)
    # Without H10 the in-repo hypotheses must all hold
    failing = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert failing == [], f"unexpected failing hypotheses: {failing}"
    assert report["hypotheses_total"] == 9
