#!/usr/bin/env python3
"""Check public uptime targets and optionally send Slack alerts for T743."""

from __future__ import annotations

import argparse
import csv
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "T743"
DEFAULT_TARGETS_PATH = Path("data") / "uptime_targets.tsv"
DEFAULT_REPORT_PATH = Path("exports") / "uptime_monitor_report.json"
DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_SLACK_TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class UptimeTarget:
    target_id: str
    name: str
    url: str
    expected_status: int
    timeout_seconds: int
    allow_tls_error: bool
    severity: str
    owner: str
    notes: str


@dataclass(frozen=True)
class FetchResult:
    status_code: int
    final_url: str
    elapsed_ms: float


@dataclass(frozen=True)
class TargetResult:
    target_id: str
    name: str
    url: str
    expected_status: int
    severity: str
    owner: str
    status: str
    http_status: int | None
    elapsed_ms: float | None
    final_url: str | None
    tls_verification: str
    error: str | None
    notes: str


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def assert_child_path(parent: Path, child: Path) -> None:
    parent_resolved = parent.resolve()
    child_resolved = child.resolve()
    if child_resolved == parent_resolved or parent_resolved not in child_resolved.parents:
        raise ValueError(f"Refusing to operate outside project root: {child}")


def resolve_project_path(root: Path, path: Path) -> Path:
    resolved = path if path.is_absolute() else root / path
    assert_child_path(root, resolved)
    return resolved


def parse_bool(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def read_targets(path: Path) -> list[UptimeTarget]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        required = {
            "target_id",
            "name",
            "url",
            "expected_status",
            "timeout_seconds",
            "allow_tls_error",
            "severity",
            "owner",
            "notes",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing uptime target columns: {sorted(missing)}")

        targets: list[UptimeTarget] = []
        for row in reader:
            if not row.get("target_id", "").strip():
                continue
            timeout = int(row.get("timeout_seconds") or DEFAULT_TIMEOUT_SECONDS)
            if timeout < 1:
                raise ValueError(f"timeout_seconds must be >= 1: {row['target_id']}")
            targets.append(
                UptimeTarget(
                    target_id=row["target_id"].strip(),
                    name=row["name"].strip(),
                    url=row["url"].strip(),
                    expected_status=int(row["expected_status"]),
                    timeout_seconds=timeout,
                    allow_tls_error=parse_bool(row["allow_tls_error"]),
                    severity=row["severity"].strip(),
                    owner=row["owner"].strip(),
                    notes=row["notes"].strip(),
                )
            )
    if not targets:
        raise ValueError(f"No uptime targets found in {path}")
    return targets


def fetch_url(
    url: str,
    timeout_seconds: int,
    *,
    context: ssl.SSLContext | None = None,
) -> FetchResult:
    started = time.perf_counter()
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mighty-Link-Uptime-Monitor/1.0"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds, context=context) as response:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return FetchResult(
            status_code=int(response.status),
            final_url=str(response.geturl()),
            elapsed_ms=elapsed_ms,
        )


def error_message(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


def is_tls_error(exc: BaseException) -> bool:
    if isinstance(exc, ssl.SSLError):
        return True
    if isinstance(exc, urllib.error.URLError) and isinstance(exc.reason, ssl.SSLError):
        return True
    return "CERTIFICATE_VERIFY_FAILED" in str(exc)


def check_target(
    target: UptimeTarget,
    *,
    fetcher=fetch_url,
) -> TargetResult:
    try:
        result = fetcher(target.url, target.timeout_seconds, context=None)
        ok = result.status_code == target.expected_status
        return TargetResult(
            target_id=target.target_id,
            name=target.name,
            url=target.url,
            expected_status=target.expected_status,
            severity=target.severity,
            owner=target.owner,
            status="ok" if ok else "failed",
            http_status=result.status_code,
            elapsed_ms=result.elapsed_ms,
            final_url=result.final_url,
            tls_verification="strict",
            error=None if ok else f"expected HTTP {target.expected_status}",
            notes=target.notes,
        )
    except Exception as exc:  # noqa: BLE001 - monitoring must record all failures.
        if target.allow_tls_error and is_tls_error(exc):
            try:
                fallback = fetcher(
                    target.url,
                    target.timeout_seconds,
                    context=ssl._create_unverified_context(),
                )
                fallback_ok = fallback.status_code == target.expected_status
                return TargetResult(
                    target_id=target.target_id,
                    name=target.name,
                    url=target.url,
                    expected_status=target.expected_status,
                    severity=target.severity,
                    owner=target.owner,
                    status="warning" if fallback_ok else "failed",
                    http_status=fallback.status_code,
                    elapsed_ms=fallback.elapsed_ms,
                    final_url=fallback.final_url,
                    tls_verification="fallback_unverified",
                    error=error_message(exc),
                    notes=target.notes,
                )
            except Exception as fallback_exc:  # noqa: BLE001
                return TargetResult(
                    target_id=target.target_id,
                    name=target.name,
                    url=target.url,
                    expected_status=target.expected_status,
                    severity=target.severity,
                    owner=target.owner,
                    status="failed",
                    http_status=None,
                    elapsed_ms=None,
                    final_url=None,
                    tls_verification="fallback_unverified",
                    error=f"{error_message(exc)}; fallback={error_message(fallback_exc)}",
                    notes=target.notes,
                )

        return TargetResult(
            target_id=target.target_id,
            name=target.name,
            url=target.url,
            expected_status=target.expected_status,
            severity=target.severity,
            owner=target.owner,
            status="failed",
            http_status=None,
            elapsed_ms=None,
            final_url=None,
            tls_verification="strict",
            error=error_message(exc),
            notes=target.notes,
        )


def summarize(results: list[TargetResult]) -> dict:
    failed = [result for result in results if result.status == "failed"]
    warnings = [result for result in results if result.status == "warning"]
    return {
        "total": len(results),
        "ok": len([result for result in results if result.status == "ok"]),
        "warning": len(warnings),
        "failed": len(failed),
        "status": "failed" if failed else "warning" if warnings else "ok",
    }


def build_report(results: list[TargetResult], targets_path: Path) -> dict:
    summary = summarize(results)
    return {
        "task_id": TASK_ID,
        "generated_at_utc": utc_timestamp(),
        "targets_path": str(targets_path),
        "summary": summary,
        "results": [asdict(result) for result in results],
    }


def write_report(report_path: Path, report: dict) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def slack_payload(report: dict) -> dict:
    summary = report["summary"]
    problem_results = [
        result
        for result in report["results"]
        if result["status"] in {"failed", "warning"}
    ]
    lines = [
        f"T743 uptime monitor: {summary['status'].upper()}",
        f"ok={summary['ok']} warning={summary['warning']} failed={summary['failed']}",
    ]
    for result in problem_results[:8]:
        lines.append(
            f"- {result['target_id']} {result['status']}: {result['url']} ({result.get('error')})"
        )
    return {"text": "\n".join(lines)}


def send_slack_alert(webhook_url: str, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=DEFAULT_SLACK_TIMEOUT_SECONDS) as response:
        if response.status >= 300:
            raise RuntimeError(f"Slack webhook returned HTTP {response.status}")


def record_results_to_db(results: list[TargetResult], env: dict[str, str]) -> int:
    """Insert uptime samples into public.uptime_checks for the T778 SLA views.

    Soft-fails with a warning so monitoring never breaks on DB issues.
    """
    database_url = env.get("SUPABASE_DB_URL", "").strip()
    if not database_url:
        print("[*] uptime DB recording skipped: SUPABASE_DB_URL is not configured.")
        return 0
    try:
        import psycopg2
    except ImportError:
        print("[*] uptime DB recording skipped: psycopg2 is not installed.")
        return 0
    status_map = {"ok": "UP", "warning": "WARNING", "failed": "DOWN"}
    try:
        conn = psycopg2.connect(database_url, connect_timeout=15)
        cursor = conn.cursor()
        inserted = 0
        for result in results:
            cursor.execute(
                """
                INSERT INTO public.uptime_checks
                    (target_id, url, status, http_status, response_ms, source)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (
                    result.target_id,
                    result.url,
                    status_map.get(result.status, "DOWN"),
                    result.http_status,
                    int(result.elapsed_ms) if result.elapsed_ms is not None else None,
                    "check_uptime_targets",
                ),
            )
            inserted += 1
        conn.commit()
        cursor.close()
        conn.close()
        print(f"[+] Recorded {inserted} uptime sample(s) into uptime_checks.")
        return inserted
    except Exception as exc:  # noqa: BLE001 - monitoring must not break on DB errors
        print(f"[-] uptime DB recording failed (non-fatal): {exc}")
        return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check public uptime targets.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--targets-path", type=Path, default=DEFAULT_TARGETS_PATH)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--fail-on-warning", action="store_true")
    parser.add_argument("--notify-on-warning", action="store_true")
    parser.add_argument("--notify-on-failure", action="store_true")
    parser.add_argument(
        "--record-db",
        action="store_true",
        help="Record samples into Supabase uptime_checks for the T778 SLA views.",
    )
    parser.add_argument(
        "--slack-webhook-url",
        default=None,
        help="Slack incoming webhook URL. Prefer SLACK_WEBHOOK_URL in CI.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, env: dict[str, str] | None = None) -> int:
    args = parse_args(argv)
    env = env if env is not None else os.environ
    root = args.root.resolve()
    targets_path = resolve_project_path(root, args.targets_path)
    report_path = resolve_project_path(root, args.report_path)

    targets = read_targets(targets_path)
    results = [check_target(target) for target in targets]
    report = build_report(
        results=results,
        targets_path=targets_path.relative_to(root),
    )
    write_report(report_path, report)

    summary = report["summary"]
    print(
        "[+] T743 uptime check "
        f"{summary['status']}: ok={summary['ok']} "
        f"warning={summary['warning']} failed={summary['failed']}"
    )
    print(f"[*] Report: {report_path}")

    if args.record_db:
        record_results_to_db(results, dict(env))

    should_notify = (
        (summary["failed"] and args.notify_on_failure)
        or (summary["warning"] and args.notify_on_warning)
    )
    webhook_url = args.slack_webhook_url or env.get("SLACK_WEBHOOK_URL")
    if should_notify and webhook_url:
        send_slack_alert(webhook_url, slack_payload(report))
        print("[+] Slack alert sent.")
    elif should_notify:
        print("[*] Slack alert skipped: SLACK_WEBHOOK_URL is not configured.")

    if summary["failed"]:
        return 1
    if summary["warning"] and args.fail_on_warning:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
