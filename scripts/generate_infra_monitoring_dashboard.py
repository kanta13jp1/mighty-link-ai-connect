#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generate an infrastructure telemetry dashboard for T755.

The dashboard aggregates local resource signals and existing project reports
without requiring secrets. Live Supabase Metrics API scraping is optional and
uses environment variables only at runtime.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import shutil
import sys
import urllib.request
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from network_security import require_https_or_loopback_url


TASK_ID = "T755"
DEFAULT_REPORT_PATH = Path("exports") / "infra_monitoring_dashboard.json"
DEFAULT_MARKDOWN_PATH = Path("exports") / "infra_monitoring_dashboard.md"
DEFAULT_UPTIME_REPORT = Path("exports") / "uptime_monitor_report.json"
DEFAULT_PERFORMANCE_REPORT = Path("exports") / "supabase_performance_report.json"
DEFAULT_LOG_ROTATION_REPORT = Path("exports") / "log_rotation_report.json"
DEFAULT_EXTERNAL_USAGE_LOG = Path("data") / "external_api_usage.jsonl"
DEFAULT_TIMEOUT_SECONDS = 15

STATUS_ORDER = {"ok": 0, "unknown": 1, "warning": 2, "critical": 3}
SECRET_PATTERNS = (
    re.compile(r"hooks\.slack\.com/services/[A-Za-z0-9/_-]+"),
    re.compile(r"postgres(?:ql)?://[^\\s]+", re.IGNORECASE),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
)


@dataclass(frozen=True)
class TelemetryCheck:
    key: str
    category: str
    status: str
    value: str
    source: str
    recommendation: str


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def assert_child_path(parent: Path, child: Path) -> None:
    parent_resolved = parent.resolve()
    child_resolved = child.resolve()
    if child_resolved == parent_resolved or parent_resolved not in child_resolved.parents:
        raise ValueError(f"Refusing to operate outside project root: {child}")


def resolve_project_path(root: Path, path: Path) -> Path:
    resolved = path if path.is_absolute() else root / path
    assert_child_path(root, resolved)
    return resolved


def display_path(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"__invalid_json__": True}
    return loaded if isinstance(loaded, dict) else {}


def redact_secret_like_text(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("<redacted>", redacted)
    return redacted


def status_from_percent(value: float | None, warning: float, critical: float) -> str:
    if value is None:
        return "unknown"
    if value >= critical:
        return "critical"
    if value >= warning:
        return "warning"
    return "ok"


def local_host_resource_status(value: float | None, warning: float, critical: float) -> str:
    """Classify the current runner without turning CI/local pressure into prod incidents."""
    status = status_from_percent(value, warning, critical)
    if status == "critical" and os.environ.get("INFRA_HOST_RESOURCE_CRITICAL") != "1":
        return "warning"
    return status


def directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                continue
    return total


def bytes_to_mb(value: int | float | None) -> str:
    if value is None:
        return "unknown"
    return f"{float(value) / (1024 * 1024):.1f} MB"


def disk_usage_percent(path: Path) -> tuple[float, int, int]:
    usage = shutil.disk_usage(path)
    used_percent = round((usage.used / usage.total) * 100, 2) if usage.total else 0.0
    return used_percent, usage.free, usage.total


class MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def windows_memory_snapshot() -> tuple[float | None, int | None, int | None]:
    if os.name != "nt":
        return None, None, None
    status = MemoryStatusEx()
    status.dwLength = ctypes.sizeof(MemoryStatusEx)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):  # type: ignore[attr-defined]
        return None, None, None
    used_percent = float(status.dwMemoryLoad)
    return used_percent, int(status.ullAvailPhys), int(status.ullTotalPhys)


def proc_memory_snapshot() -> tuple[float | None, int | None, int | None]:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return None, None, None
    values: dict[str, int] = {}
    for line in meminfo.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            values[parts[0].rstrip(":")] = int(parts[1]) * 1024
    total = values.get("MemTotal")
    available = values.get("MemAvailable")
    if not total or available is None:
        return None, None, None
    used_percent = round(((total - available) / total) * 100, 2)
    return used_percent, available, total


def memory_snapshot() -> tuple[float | None, int | None, int | None]:
    return windows_memory_snapshot() if os.name == "nt" else proc_memory_snapshot()


def cpu_load_snapshot() -> tuple[float | None, int]:
    cpu_count = os.cpu_count() or 1
    if hasattr(os, "getloadavg"):
        load1 = os.getloadavg()[0]
        return round(load1 / cpu_count, 3), cpu_count
    return None, cpu_count


def collect_local_resource_checks(root: Path) -> list[TelemetryCheck]:
    checks: list[TelemetryCheck] = []

    disk_percent, disk_free, disk_total = disk_usage_percent(root)
    checks.append(
        TelemetryCheck(
            key="disk_usage",
            category="host",
            status=local_host_resource_status(disk_percent, 80.0, 90.0),
            value=f"{disk_percent:.2f}% used ({bytes_to_mb(disk_free)} free / {bytes_to_mb(disk_total)} total)",
            source="shutil.disk_usage(project root)",
            recommendation=(
                "Investigate generated artifacts, logs, and old archives if disk usage exceeds 80%; "
                "set INFRA_HOST_RESOURCE_CRITICAL=1 to fail local/CI runner saturation."
            ),
        )
    )

    memory_percent, memory_available, memory_total = memory_snapshot()
    checks.append(
        TelemetryCheck(
            key="memory_usage",
            category="host",
            status=local_host_resource_status(memory_percent, 85.0, 95.0),
            value=(
                f"{memory_percent:.2f}% used ({bytes_to_mb(memory_available)} available / {bytes_to_mb(memory_total)} total)"
                if memory_percent is not None
                else "not available on this runner"
            ),
            source="OS memory snapshot",
            recommendation=(
                "Use Google Cloud Monitoring / Cloud Run metrics for production memory saturation; "
                "set INFRA_HOST_RESOURCE_CRITICAL=1 to fail local/CI runner saturation."
            ),
        )
    )

    load_per_core, cpu_count = cpu_load_snapshot()
    raw_cpu_status = (
        "unknown"
        if load_per_core is None
        else "critical"
        if load_per_core >= 1.0
        else "warning"
        if load_per_core >= 0.75
        else "ok"
    )
    cpu_status = (
        "warning"
        if raw_cpu_status == "critical" and os.environ.get("INFRA_HOST_RESOURCE_CRITICAL") != "1"
        else raw_cpu_status
    )
    checks.append(
        TelemetryCheck(
            key="cpu_load",
            category="host",
            status=cpu_status,
            value=(
                f"1m load/core={load_per_core:.3f} across {cpu_count} core(s)"
                if load_per_core is not None
                else f"load average unavailable; cpu_count={cpu_count}"
            ),
            source="os.getloadavg",
            recommendation=(
                "Use Cloud Monitoring CPU utilization and Cloud Run concurrency for production CPU alerting; "
                "set INFRA_HOST_RESOURCE_CRITICAL=1 to fail local/CI runner saturation."
            ),
        )
    )

    data_size = directory_size(root / "data")
    exports_size = directory_size(root / "exports")
    checks.append(
        TelemetryCheck(
            key="repo_data_exports_size",
            category="host",
            status="warning" if data_size + exports_size > 250 * 1024 * 1024 else "ok",
            value=f"data={bytes_to_mb(data_size)}, exports={bytes_to_mb(exports_size)}",
            source="repository directory scan",
            recommendation="Keep generated artifacts bounded; large binary growth should move to Drive/GCS.",
        )
    )
    return checks


def collect_uptime_checks(report: dict[str, Any], source: str) -> list[TelemetryCheck]:
    if not report:
        return [
            TelemetryCheck(
                key="uptime_report",
                category="availability",
                status="warning",
                value="missing",
                source=source,
                recommendation="Run scripts/check_uptime_targets.py before generating the dashboard.",
            )
        ]
    if report.get("__invalid_json__"):
        return [
            TelemetryCheck(
                key="uptime_report",
                category="availability",
                status="critical",
                value="invalid JSON",
                source=source,
                recommendation="Regenerate the uptime report.",
            )
        ]

    summary = report.get("summary") or {}
    status = str(summary.get("status") or "unknown")
    mapped = "critical" if status == "failed" else "warning" if status == "warning" else "ok"
    checks = [
        TelemetryCheck(
            key="uptime_summary",
            category="availability",
            status=mapped,
            value=f"ok={summary.get('ok', 0)} warning={summary.get('warning', 0)} failed={summary.get('failed', 0)}",
            source=source,
            recommendation="Investigate failed targets; TLS warnings for mightylink-app.com remain expected until T740_3.",
        )
    ]
    elapsed_values = [
        float(result["elapsed_ms"])
        for result in report.get("results", [])
        if isinstance(result, dict) and result.get("elapsed_ms") is not None
    ]
    if elapsed_values:
        max_elapsed = max(elapsed_values)
        checks.append(
            TelemetryCheck(
                key="uptime_max_latency",
                category="availability",
                status="warning" if max_elapsed >= 3000 else "ok",
                value=f"{max_elapsed:.2f} ms",
                source=source,
                recommendation="Correlate high latency with Firebase Hosting and Cloud Run metrics.",
            )
        )
    return checks


def collect_performance_checks(report: dict[str, Any], source: str) -> list[TelemetryCheck]:
    if not report:
        return [
            TelemetryCheck(
                key="db_performance_report",
                category="database",
                status="warning",
                value="missing",
                source=source,
                recommendation="Run scripts/diagnose_supabase_performance.py --dry-run or --execute.",
            )
        ]
    if report.get("__invalid_json__"):
        return [
            TelemetryCheck(
                key="db_performance_report",
                category="database",
                status="critical",
                value="invalid JSON",
                source=source,
                recommendation="Regenerate the performance diagnostic report.",
            )
        ]

    report_status = str(report.get("status") or "unknown")
    dry_run = bool(report.get("dry_run"))
    if report_status.startswith("failed"):
        status = "critical"
    elif dry_run:
        status = "warning"
    else:
        status = "ok"
    checks = [
        TelemetryCheck(
            key="db_query_diagnostics",
            category="database",
            status=status,
            value=f"status={report_status}, dry_run={dry_run}, probes={len(report.get('probes') or [])}",
            source=source,
            recommendation="Use --execute with SUPABASE_DB_URL for live query telemetry before production DB changes.",
        )
    ]
    api_results = report.get("api_results") or []
    errored = [row for row in api_results if isinstance(row, dict) and row.get("status") == "error"]
    if api_results:
        checks.append(
            TelemetryCheck(
                key="api_probe_latency",
                category="application",
                status="critical" if errored else "ok",
                value=f"probes={len(api_results)}, errors={len(errored)}",
                source=source,
                recommendation="Investigate API probe errors alongside uptime monitor and Cloud Logging.",
            )
        )
    return checks


def collect_log_checks(report: dict[str, Any], source: str) -> list[TelemetryCheck]:
    if not report:
        return [
            TelemetryCheck(
                key="log_rotation_report",
                category="logs",
                status="warning",
                value="missing",
                source=source,
                recommendation="Run scripts/rotate_runtime_logs.py --dry-run.",
            )
        ]
    candidates = report.get("candidates") or []
    pruned = report.get("pruned_archives") or []
    status = "warning" if candidates or pruned else "ok"
    return [
        TelemetryCheck(
            key="log_rotation_backlog",
            category="logs",
            status=status,
            value=f"rotation_candidates={len(candidates)}, prune_candidates={len(pruned)}",
            source=source,
            recommendation="Run real log rotation if candidates remain after review.",
        )
    ]


def parse_external_usage(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"events": 0, "providers": {}, "outcomes": {}}
    providers: Counter[str] = Counter()
    outcomes: Counter[str] = Counter()
    billable = 0
    total = 0
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        total += 1
        providers[str(event.get("provider") or "unknown")] += 1
        outcomes[str(event.get("outcome") or "unknown")] += 1
        if event.get("billable"):
            billable += 1
    return {
        "events": total,
        "providers": dict(providers),
        "outcomes": dict(outcomes),
        "billable_events": billable,
    }


def collect_external_usage_checks(summary: dict[str, Any], source: str) -> list[TelemetryCheck]:
    events = int(summary.get("events") or 0)
    billable = int(summary.get("billable_events") or 0)
    blocked = int((summary.get("outcomes") or {}).get("blocked") or 0)
    status = "warning" if billable else "ok"
    return [
        TelemetryCheck(
            key="external_api_usage",
            category="cost",
            status=status,
            value=f"events={events}, billable={billable}, blocked={blocked}",
            source=source,
            recommendation="Compare billable usage with T757 cost dashboard and provider consoles.",
        )
    ]


def parse_prometheus_metrics(text: str) -> dict[str, Any]:
    categories: dict[str, set[str]] = defaultdict(set)
    samples = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r"^([a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{[^}]*\})?\s+[-+]?\d", stripped)
        if not match:
            continue
        samples += 1
        name = match.group(1)
        lowered = name.lower()
        if "cpu" in lowered:
            categories["cpu"].add(name)
        if "mem" in lowered or "memory" in lowered:
            categories["memory"].add(name)
        if "disk" in lowered or "io" in lowered:
            categories["disk_io"].add(name)
        if "conn" in lowered:
            categories["connections"].add(name)
        if "query" in lowered or "statement" in lowered:
            categories["queries"].add(name)
    return {
        "samples": samples,
        "categories": {key: sorted(value) for key, value in sorted(categories.items())},
    }


def fetch_prometheus_metrics(url: str, bearer_token: str | None, timeout_seconds: int) -> str:
    safe_url = require_https_or_loopback_url(url)
    headers = {"User-Agent": "Mighty-Link-Infra-Dashboard/1.0"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    request = urllib.request.Request(safe_url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # nosec B310 -- HTTPS or loopback-only HTTP is enforced.
        return response.read().decode("utf-8", errors="replace")


def collect_metrics_api_check(metrics_summary: dict[str, Any] | None, source: str) -> TelemetryCheck:
    if metrics_summary is None:
        return TelemetryCheck(
            key="supabase_metrics_api",
            category="database",
            status="warning",
            value="not configured",
            source=source,
            recommendation="Set SUPABASE_METRICS_URL and token secret in CI to scrape Prometheus-compatible Supabase metrics.",
        )
    samples = int(metrics_summary.get("samples") or 0)
    categories = metrics_summary.get("categories") or {}
    return TelemetryCheck(
        key="supabase_metrics_api",
        category="database",
        status="ok" if samples else "warning",
        value=f"samples={samples}, categories={','.join(categories.keys()) or 'none'}",
        source=source,
        recommendation="Feed these metrics into Prometheus/Grafana for long-term dashboards and alert rules.",
    )


def overall_status(checks: list[TelemetryCheck]) -> str:
    if not checks:
        return "unknown"
    return max((check.status for check in checks), key=lambda status: STATUS_ORDER.get(status, 1))


def summary_by_status(checks: list[TelemetryCheck]) -> dict[str, int]:
    counter = Counter(check.status for check in checks)
    return {status: int(counter.get(status, 0)) for status in ("ok", "unknown", "warning", "critical")}


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Infra Telemetry Dashboard",
        "",
        f"- Task: {report['task_id']}",
        f"- Generated: {report['generated_at_utc']}",
        f"- Overall status: {report['overall_status']}",
        "",
        "## Summary",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    for status, count in report["summary"].items():
        lines.append(f"| {status} | {count} |")

    lines.extend(
        [
            "",
            "## Checks",
            "",
            "| Category | Key | Status | Value | Recommendation |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for check in report["checks"]:
        value = str(check["value"]).replace("|", "\\|")
        recommendation = str(check["recommendation"]).replace("|", "\\|")
        lines.append(
            f"| {check['category']} | {check['key']} | {check['status']} | {value} | {recommendation} |"
        )

    lines.extend(
        [
            "",
            "## Sources",
            "",
        ]
    )
    for name, source in report["sources"].items():
        lines.append(f"- {name}: `{source}`")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This artifact contains no secret values. Runtime secrets are read only to connect to optional APIs.",
            "- Supabase Metrics API scraping is optional until the project token and endpoint are configured in GitHub secrets.",
            "- Custom domain TLS warning remains expected until T740_3 is complete.",
            "",
        ]
    )
    return "\n".join(lines)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact_secret_like_text(text), encoding="utf-8", newline="\n")


def build_dashboard(
    *,
    root: Path,
    uptime_report_path: Path,
    performance_report_path: Path,
    log_rotation_report_path: Path,
    external_usage_log_path: Path,
    metrics_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    sources = {
        "uptime": display_path(root, uptime_report_path),
        "database_performance": display_path(root, performance_report_path),
        "log_rotation": display_path(root, log_rotation_report_path),
        "external_api_usage": display_path(root, external_usage_log_path),
        "supabase_metrics_api": "SUPABASE_METRICS_URL" if metrics_summary is not None else "not configured",
    }

    checks: list[TelemetryCheck] = []
    checks.extend(collect_local_resource_checks(root))
    checks.extend(collect_uptime_checks(read_json(uptime_report_path), sources["uptime"]))
    checks.extend(collect_performance_checks(read_json(performance_report_path), sources["database_performance"]))
    checks.extend(collect_log_checks(read_json(log_rotation_report_path), sources["log_rotation"]))
    external_summary = parse_external_usage(external_usage_log_path)
    checks.extend(collect_external_usage_checks(external_summary, sources["external_api_usage"]))
    checks.append(collect_metrics_api_check(metrics_summary, sources["supabase_metrics_api"]))

    return {
        "task_id": TASK_ID,
        "generated_at_utc": utc_timestamp(),
        "overall_status": overall_status(checks),
        "summary": summary_by_status(checks),
        "sources": sources,
        "checks": [asdict(check) for check in checks],
        "external_api_usage_summary": external_summary,
        "supabase_metrics_summary": metrics_summary,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate T755 infra telemetry dashboard.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--markdown-path", type=Path, default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--uptime-report", type=Path, default=DEFAULT_UPTIME_REPORT)
    parser.add_argument("--performance-report", type=Path, default=DEFAULT_PERFORMANCE_REPORT)
    parser.add_argument("--log-rotation-report", type=Path, default=DEFAULT_LOG_ROTATION_REPORT)
    parser.add_argument("--external-usage-log", type=Path, default=DEFAULT_EXTERNAL_USAGE_LOG)
    parser.add_argument("--supabase-metrics-url", default=os.environ.get("SUPABASE_METRICS_URL", "").strip())
    parser.add_argument(
        "--supabase-metrics-token",
        default=os.environ.get("SUPABASE_METRICS_BEARER_TOKEN", "").strip(),
    )
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--fail-on-critical", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.timeout_seconds < 1:
        raise ValueError("timeout-seconds must be >= 1")

    root = args.root.resolve()
    report_path = resolve_project_path(root, args.report_path)
    markdown_path = resolve_project_path(root, args.markdown_path)
    uptime_report_path = resolve_project_path(root, args.uptime_report)
    performance_report_path = resolve_project_path(root, args.performance_report)
    log_rotation_report_path = resolve_project_path(root, args.log_rotation_report)
    external_usage_log_path = resolve_project_path(root, args.external_usage_log)

    metrics_summary = None
    if args.supabase_metrics_url:
        try:
            metrics_text = fetch_prometheus_metrics(
                args.supabase_metrics_url,
                args.supabase_metrics_token or None,
                args.timeout_seconds,
            )
            metrics_summary = parse_prometheus_metrics(metrics_text)
        except Exception as exc:  # noqa: BLE001 - dashboard should record optional scrape failures.
            metrics_summary = {
                "samples": 0,
                "categories": {},
                "error": redact_secret_like_text(f"{type(exc).__name__}: {exc}"),
            }

    report = build_dashboard(
        root=root,
        uptime_report_path=uptime_report_path,
        performance_report_path=performance_report_path,
        log_rotation_report_path=log_rotation_report_path,
        external_usage_log_path=external_usage_log_path,
        metrics_summary=metrics_summary,
    )

    write_text(report_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    write_text(markdown_path, render_markdown(report))
    print(
        f"[+] T755 infra dashboard {report['overall_status']}: "
        f"ok={report['summary']['ok']} warning={report['summary']['warning']} "
        f"critical={report['summary']['critical']}"
    )
    print(f"[*] JSON: {report_path}")
    print(f"[*] Markdown: {markdown_path}")
    if args.fail_on_critical and report["overall_status"] == "critical":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
