#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generate the T778 SLA measurement report from the Supabase KPI views.

Reads the views created by supabase/migrations/20260705000000_sla_measurement_views.sql
over a read-only connection and writes exports/sla_measurement_report.{json,md}.
Targets follow docs/SLA_KPI_DEFINITION_AND_MEASUREMENT.md (pilot tier).
The monthly quality pipeline (T764/T808) consumes these exports for Sheets delivery.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = PROJECT_ROOT / "exports" / "sla_measurement_report.json"
REPORT_MD = PROJECT_ROOT / "exports" / "sla_measurement_report.md"

TARGETS = {
    "availability_pct_pilot": 99.5,
    "p95_ms": 3000,
    "helpful_pct": 70.0,
}

VIEWS = [
    "kpi_monthly_availability",
    "kpi_daily_response_time",
    "kpi_weekly_diagnosis_accuracy",
    "kpi_daily_diagnoses",
    "kpi_weekly_active_users",
    "kpi_weekly_anonymous_sessions",
]


def fetch_view(cursor, view: str, limit: int = 30) -> list[dict]:
    if view not in VIEWS:
        raise ValueError(f"Unsupported SLA view: {view}")
    cursor.execute(f"SELECT * FROM public.{view} LIMIT %s", (limit,))  # nosec B608 -- view is restricted to VIEWS.
    columns = [d[0] for d in cursor.description]
    rows = []
    for record in cursor.fetchall():
        row = {}
        for key, value in zip(columns, record):
            row[key] = value.isoformat() if hasattr(value, "isoformat") else (
                float(value) if hasattr(value, "quantize") else value
            )
        rows.append(row)
    return rows


def evaluate(views: dict[str, list[dict]]) -> list[dict]:
    checks = []
    availability = views.get("kpi_monthly_availability") or []
    if availability:
        worst = min(float(r["availability_pct"]) for r in availability)
        checks.append({
            "metric": "availability_pct (worst target, all months)",
            "value": worst,
            "target": TARGETS["availability_pct_pilot"],
            "pass": worst >= TARGETS["availability_pct_pilot"],
        })
    else:
        checks.append({"metric": "availability_pct", "value": None,
                       "target": TARGETS["availability_pct_pilot"], "pass": None,
                       "note": "no uptime samples yet"})
    latency = views.get("kpi_daily_response_time") or []
    if latency:
        worst_p95 = max(float(r["p95_ms"]) for r in latency if r.get("p95_ms") is not None)
        checks.append({
            "metric": "p95_ms (worst day/target)",
            "value": worst_p95,
            "target": TARGETS["p95_ms"],
            "pass": worst_p95 <= TARGETS["p95_ms"],
        })
    else:
        checks.append({"metric": "p95_ms", "value": None, "target": TARGETS["p95_ms"],
                       "pass": None, "note": "no response samples yet"})
    accuracy = views.get("kpi_weekly_diagnosis_accuracy") or []
    rated = [r for r in accuracy if r.get("helpful_pct") is not None]
    if rated:
        latest = float(rated[0]["helpful_pct"])
        checks.append({
            "metric": "helpful_pct (latest week)",
            "value": latest,
            "target": TARGETS["helpful_pct"],
            "pass": latest >= TARGETS["helpful_pct"],
        })
    else:
        checks.append({"metric": "helpful_pct", "value": None,
                       "target": TARGETS["helpful_pct"], "pass": None,
                       "note": "no rated feedback yet"})
    return checks


def render_md(report: dict) -> str:
    lines = [
        "# SLA Measurement Report (T778)",
        "",
        f"- Generated: {report['generated_at_utc']}",
        f"- Status: {report['status']}",
        "",
        "## SLA/KPI checks",
        "",
        "| metric | value | target | pass |",
        "| --- | --- | --- | --- |",
    ]
    for c in report["checks"]:
        value = "-" if c["value"] is None else c["value"]
        passed = {True: "PASS", False: "FAIL", None: "NO DATA"}[c["pass"]]
        lines.append(f"| {c['metric']} | {value} | {c['target']} | {passed} |")
    lines += ["", "## View row counts", ""]
    for view, rows in report["views"].items():
        lines.append(f"- {view}: {len(rows)} row(s)")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    database_url = os.environ.get("SUPABASE_DB_URL", "").strip()
    if not database_url:
        print("[-] SUPABASE_DB_URL is not configured.")
        return 1
    import psycopg2

    conn = psycopg2.connect(database_url, connect_timeout=20)
    conn.set_session(readonly=True)
    cursor = conn.cursor()
    views = {view: fetch_view(cursor, view) for view in VIEWS}
    cursor.close()
    conn.close()

    checks = evaluate(views)
    failed = [c for c in checks if c["pass"] is False]
    no_data = [c for c in checks if c["pass"] is None]
    status = "fail" if failed else ("partial_no_data" if no_data else "pass")
    report = {
        "task_id": "T778",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "targets": TARGETS,
        "checks": checks,
        "views": views,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(f"[+] SLA measurement report {status}: {REPORT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
