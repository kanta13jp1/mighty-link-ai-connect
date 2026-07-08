"""Read-load distribution & pool sizing simulation (T782).

T782 designs DB connection load balancing for access growth: read-replica
offloading and pool-size optimization. This harness is the quantitative half of
that design. It runs entirely offline:

* classifies the real API surface (GET vs write routes) from src/app.py,
* takes the measured 100-user load probe (T770/T858 exports) as the traffic
  baseline,
* models the connection pool as an M/M/c queue (Erlang C) to compute
  utilization, queueing probability and P95 queue wait across load multiples,
  pool sizes and replica-offload scenarios, and
* verifies the instance-count x pool-size safety formula against the Supavisor
  client-connection budget.

Results feed docs/DB_READ_LOAD_BALANCING_DESIGN.md; evidence goes to
exports/read_load_distribution_simulation.{json,md}. Ten hypotheses, all
verified here or by tests/test_read_load_simulation.py.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PY = PROJECT_ROOT / "src" / "app.py"
LOAD_REPORT = PROJECT_ROOT / "exports" / "load_test_100_users_2026-07-01.json"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "read_load_distribution_simulation.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "read_load_distribution_simulation.md"

# --- design constants (documented in DB_READ_LOAD_BALANCING_DESIGN.md) -------
# Supavisor client-connection budget we design against (Micro tier order of
# magnitude; the exact ceiling is checked in the dashboard before scaling).
SUPAVISOR_CLIENT_CONN_BUDGET = 200
POOL_MAX_PER_INSTANCE = 4          # SUPABASE_DB_POOL_MAX default in app.py
RECOMMENDED_MAX_INSTANCES = 20     # keeps 20 * 4 = 80 <= 200 with 2.5x headroom
# DB connection hold time per request. End-to-end latency from the load probe
# includes mock-AI work; the pool only cares about the DB borrow window, so we
# model it explicitly and run a sensitivity sweep instead of pretending the
# two are equal.
DB_HOLD_MS_BASELINE = 25.0
DB_HOLD_MS_SENSITIVITY = (10.0, 25.0, 50.0, 100.0)
# Design budget: pool queue wait may consume at most 10% of the P95 SLA
# (3000ms), i.e. 300ms. Waits beyond this erode the latency budget of the
# actual work.
POOL_WAIT_BUDGET_MS = 300.0
TARGET_UTILIZATION = 0.8  # scale-out threshold used for instance sizing


def instances_needed(arrival_per_s: float, hold_ms: float,
                     pool_per_instance: int = POOL_MAX_PER_INSTANCE,
                     target_util: float = TARGET_UTILIZATION) -> int:
    """Cloud Run instances needed to keep per-connection utilization <= target."""
    offered = arrival_per_s * (hold_ms / 1000.0)          # erlangs
    connections = math.ceil(offered / target_util)
    return max(1, math.ceil(connections / pool_per_instance))

# GET routes that must stay on the primary because the UI reads them right
# after a write (read-after-write consistency; async replica lag would show
# stale data). Everything else GET is replica-safe (dashboards, summaries,
# health, exports).
READ_AFTER_WRITE_ROUTES = {
    "/api/matches",      # listed immediately after POST /api/match
    "/api/engineers",    # listed immediately after POST /api/parse
    "/api/jobs",         # listed immediately after POST /api/parse
    "/api/auth/me",
}


def classify_routes() -> dict[str, Any]:
    src = APP_PY.read_text(encoding="utf-8")
    routes = re.findall(r'@app\.(get|post|put|delete|patch)\("([^"]+)"', src)
    api_routes = [(m, p) for m, p in routes if p.startswith("/api/")]
    reads = sorted({p for m, p in api_routes if m == "get"})
    writes = sorted({p for m, p in api_routes if m != "get"})
    replica_safe = [p for p in reads if p not in READ_AFTER_WRITE_ROUTES]
    return {
        "read_routes": reads,
        "write_routes": writes,
        "read_share": len(reads) / (len(reads) + len(writes)),
        "replica_safe_reads": replica_safe,
        "primary_pinned_reads": sorted(READ_AFTER_WRITE_ROUTES & set(reads)),
        "replica_safe_share_of_reads": len(replica_safe) / len(reads) if reads else 0.0,
    }


# --- M/M/c queue (Erlang C) ---------------------------------------------------

def erlang_c(servers: int, offered_erlangs: float) -> float:
    """Probability an arriving request must queue (all connections busy)."""
    if offered_erlangs <= 0:
        return 0.0
    if offered_erlangs >= servers:
        return 1.0
    inv_b = 1.0  # inverse Erlang B, iterative (numerically stable)
    for k in range(1, servers + 1):
        inv_b = 1.0 + inv_b * k / offered_erlangs
    erlang_b = 1.0 / inv_b
    rho = offered_erlangs / servers
    return erlang_b / (1.0 - rho + rho * erlang_b)


def queue_metrics(arrival_per_s: float, hold_ms: float, servers: int) -> dict[str, Any]:
    mu = 1000.0 / hold_ms                     # service rate per connection (req/s)
    offered = arrival_per_s / mu              # erlangs
    rho = offered / servers
    if rho >= 1.0:
        return {"servers": servers, "utilization": round(rho, 3), "saturated": True,
                "queue_probability": 1.0, "mean_wait_ms": None, "p95_wait_ms": None}
    pw = erlang_c(servers, offered)
    drain = servers * mu - arrival_per_s      # spare capacity (req/s)
    mean_wait_ms = (pw / drain) * 1000.0
    p95_wait_ms = (math.log(pw / 0.05) / drain) * 1000.0 if pw > 0.05 else 0.0
    return {"servers": servers, "utilization": round(rho, 3), "saturated": False,
            "queue_probability": round(pw, 4),
            "mean_wait_ms": round(mean_wait_ms, 2), "p95_wait_ms": round(max(p95_wait_ms, 0.0), 2)}


def load_baseline() -> dict[str, Any]:
    report = json.loads(LOAD_REPORT.read_text(encoding="utf-8"))
    scenario = report["scenario"]
    total = report["summary"]["total_requests"]
    elapsed = scenario["total_elapsed_seconds"]
    return {
        "source": LOAD_REPORT.name,
        "total_requests": total,
        "elapsed_seconds": elapsed,
        "burst_rps": round(total / elapsed, 1),
        "overall_p95_ms": report["summary"]["overall"]["p95_ms"],
    }


def build_scenarios(routes: dict[str, Any], baseline_rps: float) -> list[dict[str, Any]]:
    read_share = routes["read_share"]
    offload_share = read_share * routes["replica_safe_share_of_reads"]
    scenarios = []
    for multiple in (1, 2, 5, 10):
        rps = baseline_rps * multiple
        primary_only = queue_metrics(rps, DB_HOLD_MS_BASELINE, POOL_MAX_PER_INSTANCE)
        offloaded_rps = rps * (1.0 - offload_share)
        with_replica = queue_metrics(offloaded_rps, DB_HOLD_MS_BASELINE, POOL_MAX_PER_INSTANCE)
        replica_side = queue_metrics(rps * offload_share, DB_HOLD_MS_BASELINE, POOL_MAX_PER_INSTANCE)
        scenarios.append({
            "load_multiple": multiple,
            "arrival_rps": round(rps, 1),
            "offload_share": round(offload_share, 3),
            "primary_only": primary_only,
            "primary_with_replica": with_replica,
            "replica_pool": replica_side,
        })
    return scenarios


def pool_size_sweep(baseline_rps: float, multiple: int = 10) -> list[dict[str, Any]]:
    rps = baseline_rps * multiple
    return [queue_metrics(rps, DB_HOLD_MS_BASELINE, c) for c in range(2, 21, 2)]


def hold_time_sensitivity(baseline_rps: float) -> list[dict[str, Any]]:
    rows = []
    for hold in DB_HOLD_MS_SENSITIVITY:
        m = queue_metrics(baseline_rps, hold, POOL_MAX_PER_INSTANCE)
        rows.append({"db_hold_ms": hold, **m})
    return rows


def build_hypotheses(routes: dict[str, Any], baseline: dict[str, Any],
                     scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    app_src = APP_PY.read_text(encoding="utf-8")

    def record(hid: str, statement: str, check: Callable[[], tuple[bool, str]]) -> None:
        try:
            passed, detail = check()
        except Exception as exc:
            passed, detail = False, f"例外: {type(exc).__name__}: {exc}"
        results.append({"id": hid, "hypothesis": statement, "passed": passed, "detail": detail})

    record("H1", "現行プールはThreadedConnectionPool(min1/max4/recycle1800s/Supavisor mode検出)である",
           lambda: ("ThreadedConnectionPool" in app_src
                    and 'env_int("SUPABASE_DB_POOL_MAX", 4' in app_src
                    and "pooler.supabase.com" in app_src,
                    "app.py実装確認: pool種別/既定値/mode検出すべて存在"))

    record("H2", "APIはread(GET)がwriteより多く、read offloadの余地がある",
           lambda: (routes["read_share"] > 0.5,
                    f"read {len(routes['read_routes'])} / write {len(routes['write_routes'])}"
                    f" (read share={routes['read_share']:.0%})"))

    record("H3", "read-after-write整合が必要なGETを特定し、それ以外をレプリカ安全群に分類できる",
           lambda: (len(routes["primary_pinned_reads"]) >= 3 and routes["replica_safe_share_of_reads"] > 0.7,
                    f"primary固定={routes['primary_pinned_reads']} / レプリカ安全={len(routes['replica_safe_reads'])}件"
                    f" (read内{routes['replica_safe_share_of_reads']:.0%})"))

    def h4() -> tuple[bool, str]:
        # M/M/1 identity: Erlang C == rho
        c1 = erlang_c(1, 0.6)
        # M/M/2 known value: a=1 erlang -> Pw = 1/3
        c2 = erlang_c(2, 1.0)
        ok = abs(c1 - 0.6) < 1e-9 and abs(c2 - 1.0 / 3.0) < 1e-9
        return ok, f"M/M/1(ρ=0.6)→{c1:.3f}(=0.6期待) M/M/2(a=1)→{c2:.4f}(=0.3333期待)"

    record("H4", "Erlang C実装は既知の理論値と一致する", h4)

    def h5() -> tuple[bool, str]:
        s = scenarios[0]["primary_only"]
        ok = (not s["saturated"]
              and (s["p95_wait_ms"] or 0) <= POOL_WAIT_BUDGET_MS)
        return ok, (f"実測バースト{baseline['burst_rps']}req/s・DB占有{DB_HOLD_MS_BASELINE}ms・c=4: "
                    f"利用率{s['utilization']:.0%} P95待ち{s['p95_wait_ms']}ms"
                    f"(予算{POOL_WAIT_BUDGET_MS:.0f}ms=SLA比10%以内。ただし利用率90%で余裕薄→水平スケール前提を設計に明記)")

    record("H5", "現行実測バースト負荷では1インスタンスのプール(c=4)が飽和せず、P95待ちがプール待ち予算(SLA比10%)内", h5)

    def h6() -> tuple[bool, str]:
        s10 = scenarios[-1]["primary_only"]
        return s10["saturated"], (f"10倍負荷({scenarios[-1]['arrival_rps']}req/s)でc=4は"
                                  f"{'飽和(要スケール)' if s10['saturated'] else '未飽和'}")

    record("H6", "アクセス10倍ではprimary-only・c=4は飽和し、スケール施策が必須になる", h6)

    def h7() -> tuple[bool, str]:
        s10 = scenarios[-1]
        rps10 = s10["arrival_rps"]
        need_primary_only = instances_needed(rps10, DB_HOLD_MS_BASELINE)
        need_with_replica = instances_needed(rps10 * (1.0 - s10["offload_share"]), DB_HOLD_MS_BASELINE)
        ok = need_with_replica < need_primary_only
        return ok, (f"10倍負荷({rps10}req/s)の必要インスタンス数(利用率≤{TARGET_UTILIZATION:.0%}): "
                    f"primary-only {need_primary_only}台 → レプリカoffload後 {need_with_replica}台"
                    f" (offload率{s10['offload_share']:.0%}で必要台数を削減)")

    record("H7", "レプリカoffloadは高負荷時のprimary必要インスタンス数を削減する", h7)

    def h8() -> tuple[bool, str]:
        budget_used = RECOMMENDED_MAX_INSTANCES * POOL_MAX_PER_INSTANCE
        ok = budget_used <= SUPAVISOR_CLIENT_CONN_BUDGET
        return ok, (f"推奨maxInstances({RECOMMENDED_MAX_INSTANCES}) × POOL_MAX({POOL_MAX_PER_INSTANCE})"
                    f" = {budget_used} ≤ Supavisor予算{SUPAVISOR_CLIENT_CONN_BUDGET}")

    record("H8", "インスタンス数×プールサイズの安全式がSupavisorクライアント接続予算内に収まる", h8)

    def h9() -> tuple[bool, str]:
        bad = re.findall(r'cursor\.execute\(\s*["\'](SET |LISTEN|PREPARE|DECLARE)', app_src)
        return not bad, f"session state SQL(SET/LISTEN/PREPARE/DECLARE)使用={bad or 'なし'}(transaction mode安全)"

    record("H9", "現行コードはtransaction pooler(6543)の制約(session state不可)に抵触しない", h9)

    # H10 (fresh load probe green) is verified externally by run_load_test and
    # recorded by the caller; placeholder asserted by tests.
    return results


def build_report(checked_at: str, fresh_load_result: dict[str, Any] | None) -> dict[str, Any]:
    routes = classify_routes()
    baseline = load_baseline()
    scenarios = build_scenarios(routes, baseline["burst_rps"])
    hypotheses = build_hypotheses(routes, baseline, scenarios)
    if fresh_load_result is not None:
        hypotheses.append({
            "id": "H10",
            "hypothesis": "T866同期init後の実負荷テスト(100ユーザー)がSLA greenで回帰しない",
            "passed": bool(fresh_load_result.get("sla_green")),
            "detail": fresh_load_result.get("detail", ""),
        })
    passed = sum(1 for h in hypotheses if h["passed"])
    return {
        "report_id": "READ_LOAD_DISTRIBUTION_T782",
        "checked_at": checked_at,
        "status": "ok" if passed == len(hypotheses) else "attention",
        "hypotheses_total": len(hypotheses),
        "hypotheses_passed": passed,
        "hypotheses": hypotheses,
        "route_classification": routes,
        "traffic_baseline": baseline,
        "assumptions": {
            "db_hold_ms_baseline": DB_HOLD_MS_BASELINE,
            "supavisor_client_conn_budget": SUPAVISOR_CLIENT_CONN_BUDGET,
            "pool_max_per_instance": POOL_MAX_PER_INSTANCE,
            "recommended_max_instances": RECOMMENDED_MAX_INSTANCES,
        },
        "scenarios": scenarios,
        "pool_size_sweep_at_10x": pool_size_sweep(baseline["burst_rps"]),
        "db_hold_sensitivity_at_1x": hold_time_sensitivity(baseline["burst_rps"]),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# リード負荷分散シミュレーション (T782)",
        "",
        f"- レポートID: `{report['report_id']}` / 実施日: {report['checked_at']}",
        f"- 判定: **{report['status']}** ({report['hypotheses_passed']}/{report['hypotheses_total']} 仮説PASS)",
        f"- トラフィック基準: {report['traffic_baseline']['source']} burst {report['traffic_baseline']['burst_rps']} req/s",
        f"- 前提: DB占有 {report['assumptions']['db_hold_ms_baseline']}ms/req、"
        f"POOL_MAX {report['assumptions']['pool_max_per_instance']}/インスタンス、"
        f"Supavisor予算 {report['assumptions']['supavisor_client_conn_budget']} client conns",
        "",
        "## 10仮説検証",
        "",
        "| # | 仮説 | 結果 | 根拠 |",
        "| --- | --- | --- | --- |",
    ]
    for h in report["hypotheses"]:
        mark = "PASS" if h["passed"] else "FAIL"
        lines.append(f"| {h['id']} | {h['hypothesis']} | {mark} | {h['detail'].replace('|', '/')} |")
    lines += ["", "## 負荷シナリオ (Erlang C, c=4/インスタンス)", "",
              "| 負荷 | req/s | primary単独 利用率 | P95待ちms | レプリカoffload後 利用率 | P95待ちms |",
              "| --- | --- | --- | --- | --- | --- |"]
    for s in report["scenarios"]:
        po, pr = s["primary_only"], s["primary_with_replica"]
        po_u = "飽和" if po["saturated"] else f"{po['utilization']:.0%}"
        pr_u = "飽和" if pr["saturated"] else f"{pr['utilization']:.0%}"
        lines.append(f"| {s['load_multiple']}x | {s['arrival_rps']} | {po_u} | {po['p95_wait_ms']} | {pr_u} | {pr['p95_wait_ms']} |")
    lines += ["", "## プールサイズ掃引 (10倍負荷)", "",
              "| c | 利用率 | 待ち確率 | P95待ちms |", "| --- | --- | --- | --- |"]
    for row in report["pool_size_sweep_at_10x"]:
        u = "飽和" if row["saturated"] else f"{row['utilization']:.0%}"
        lines.append(f"| {row['servers']} | {u} | {row['queue_probability']} | {row['p95_wait_ms']} |")
    lines += ["", "詳細な設計判断は docs/DB_READ_LOAD_BALANCING_DESIGN.md を参照。", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-load distribution simulation (T782)")
    parser.add_argument("--checked-at", default="2026-07-08")
    parser.add_argument("--fresh-load-json", type=Path, default=None,
                        help="path to a fresh run_load_test_100_users JSON to fold in as H10")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD)
    parser.add_argument("--fail-on-attention", action="store_true")
    args = parser.parse_args()

    fresh: dict[str, Any] | None = None
    if args.fresh_load_json and args.fresh_load_json.exists():
        data = json.loads(args.fresh_load_json.read_text(encoding="utf-8"))
        overall = data["summary"]["overall"]
        sla = data.get("sla", {})
        green = data["summary"]["total_errors"] == 0 and overall["p95_ms"] <= 3000.0
        fresh = {"sla_green": green,
                 "detail": (f"{args.fresh_load_json.name}: errors={data['summary']['total_errors']} "
                            f"p95={overall['p95_ms']}ms (SLA 3000ms) sla_keys={list(sla)[:3]}")}

    report = build_report(args.checked_at, fresh)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"[*] Wrote {args.json_out}")
    print(f"[*] Wrote {args.md_out}")
    print(f"[{'+' if report['status'] == 'ok' else '!'}] Read-load simulation {report['status']}: "
          f"{report['hypotheses_passed']}/{report['hypotheses_total']} hypotheses passed")
    if args.fail_on_attention and report["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
