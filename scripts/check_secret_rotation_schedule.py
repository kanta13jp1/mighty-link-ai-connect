#!/usr/bin/env python3
"""Check third-party secret rotation schedule metadata for T751.

This script intentionally reads only inventory metadata. It never needs raw
secret values and fails fast if a secret-looking value is accidentally added to
the inventory.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


TASK_ID = "T751"
DEFAULT_INVENTORY_PATH = Path("data") / "secret_rotation_inventory.tsv"
DEFAULT_REPORT_PATH = Path("exports") / "secret_rotation_report.json"

SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{16,}"),
    re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/_-]+"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}"),
)

REQUIRED_COLUMNS = {
    "secret_id",
    "provider",
    "secret_name",
    "environment",
    "storage_location",
    "rotation_owner",
    "rotation_interval_days",
    "rotation_anchor_date",
    "warning_days",
    "required",
    "verification_method",
    "notes",
}


@dataclass(frozen=True)
class SecretRotationItem:
    secret_id: str
    provider: str
    secret_name: str
    environment: str
    storage_location: str
    rotation_owner: str
    rotation_interval_days: int
    rotation_anchor_date: date
    warning_days: int
    required: bool
    verification_method: str
    notes: str


@dataclass(frozen=True)
class RotationResult:
    secret_id: str
    provider: str
    secret_name: str
    environment: str
    storage_location: str
    rotation_owner: str
    required: bool
    rotation_anchor_date: str
    next_rotation_due_date: str
    days_until_due: int
    status: str
    verification_method: str
    notes: str


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_date(raw: str) -> date:
    return datetime.strptime(raw.strip(), "%Y-%m-%d").date()


def parse_bool(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "y", "on", "必須", "yes"}


def assert_child_path(parent: Path, child: Path) -> None:
    parent_resolved = parent.resolve()
    child_resolved = child.resolve()
    if child_resolved == parent_resolved or parent_resolved not in child_resolved.parents:
        raise ValueError(f"Refusing to operate outside project root: {child}")


def resolve_project_path(root: Path, path: Path) -> Path:
    resolved = path if path.is_absolute() else root / path
    assert_child_path(root, resolved)
    return resolved


def looks_like_secret(value: str) -> bool:
    return any(pattern.search(value) for pattern in SECRET_PATTERNS)


def check_for_secret_material(rows: list[dict[str, str]]) -> list[str]:
    findings: list[str] = []
    for index, row in enumerate(rows, start=2):
        for key, value in row.items():
            if value and looks_like_secret(value):
                findings.append(f"row {index} column {key}")
    return findings


def read_inventory(path: Path) -> list[SecretRotationItem]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing secret rotation inventory columns: {sorted(missing)}")

        raw_rows = [row for row in reader if row.get("secret_id", "").strip()]
        leaks = check_for_secret_material(raw_rows)
        if leaks:
            raise ValueError(
                "Secret-like material found in metadata inventory: " + ", ".join(leaks)
            )

        seen: set[str] = set()
        items: list[SecretRotationItem] = []
        for row in raw_rows:
            secret_id = row["secret_id"].strip()
            if secret_id in seen:
                raise ValueError(f"Duplicate secret_id: {secret_id}")
            seen.add(secret_id)

            interval = int(row["rotation_interval_days"])
            warning_days = int(row["warning_days"])
            if interval < 1:
                raise ValueError(f"rotation_interval_days must be >= 1: {secret_id}")
            if warning_days < 0:
                raise ValueError(f"warning_days must be >= 0: {secret_id}")

            items.append(
                SecretRotationItem(
                    secret_id=secret_id,
                    provider=row["provider"].strip(),
                    secret_name=row["secret_name"].strip(),
                    environment=row["environment"].strip(),
                    storage_location=row["storage_location"].strip(),
                    rotation_owner=row["rotation_owner"].strip(),
                    rotation_interval_days=interval,
                    rotation_anchor_date=parse_date(row["rotation_anchor_date"]),
                    warning_days=warning_days,
                    required=parse_bool(row["required"]),
                    verification_method=row["verification_method"].strip(),
                    notes=row["notes"].strip(),
                )
            )
    if not items:
        raise ValueError(f"No secret rotation items found in {path}")
    return items


def evaluate_item(item: SecretRotationItem, as_of: date) -> RotationResult:
    due_date = item.rotation_anchor_date + timedelta(days=item.rotation_interval_days)
    days_until_due = (due_date - as_of).days
    if days_until_due < 0:
        status = "overdue_required" if item.required else "overdue_optional"
    elif days_until_due <= item.warning_days:
        status = "due_soon"
    else:
        status = "ok"

    return RotationResult(
        secret_id=item.secret_id,
        provider=item.provider,
        secret_name=item.secret_name,
        environment=item.environment,
        storage_location=item.storage_location,
        rotation_owner=item.rotation_owner,
        required=item.required,
        rotation_anchor_date=item.rotation_anchor_date.isoformat(),
        next_rotation_due_date=due_date.isoformat(),
        days_until_due=days_until_due,
        status=status,
        verification_method=item.verification_method,
        notes=item.notes,
    )


def summarize(results: list[RotationResult]) -> dict:
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    overdue_required = counts.get("overdue_required", 0)
    overdue_optional = counts.get("overdue_optional", 0)
    due_soon = counts.get("due_soon", 0)
    return {
        "total": len(results),
        "ok": counts.get("ok", 0),
        "due_soon": due_soon,
        "overdue_required": overdue_required,
        "overdue_optional": overdue_optional,
        "status": "failed" if overdue_required else "warning" if (overdue_optional or due_soon) else "ok",
    }


def build_report(results: list[RotationResult], *, inventory_path: Path, as_of: date) -> dict:
    return {
        "task_id": TASK_ID,
        "generated_at_utc": utc_timestamp(),
        "as_of_date": as_of.isoformat(),
        "inventory_path": str(inventory_path),
        "summary": summarize(results),
        "results": [asdict(result) for result in results],
        "policy": {
            "raw_secret_values_allowed": False,
            "required_overdue_exit_code": 1,
            "optional_overdue_exit_code": 0,
            "rotation_anchor_meaning": (
                "Date this secret entered the managed rotation calendar; "
                "provider-side replacement evidence is recorded in the runbook/issue at rotation time."
            ),
        },
    }


def write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check managed third-party secret rotation schedule metadata."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--inventory-path", type=Path, default=DEFAULT_INVENTORY_PATH)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--as-of", type=parse_date, default=date.today())
    parser.add_argument("--fail-on-overdue", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    inventory_path = resolve_project_path(root, args.inventory_path)
    report_path = resolve_project_path(root, args.report_path)

    try:
        items = read_inventory(inventory_path)
        results = [evaluate_item(item, args.as_of) for item in items]
        report = build_report(
            results=results,
            inventory_path=inventory_path.relative_to(root),
            as_of=args.as_of,
        )
        write_report(report_path, report)
    except Exception as exc:  # noqa: BLE001 - CLI should surface metadata validation failures.
        error_report = {
            "task_id": TASK_ID,
            "generated_at_utc": utc_timestamp(),
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
        }
        write_report(report_path, error_report)
        print(f"[-] T751 secret rotation check failed: {exc}", file=sys.stderr)
        return 2

    summary = report["summary"]
    print(
        "[+] T751 secret rotation check "
        f"{summary['status']}: ok={summary['ok']} "
        f"due_soon={summary['due_soon']} "
        f"overdue_required={summary['overdue_required']} "
        f"overdue_optional={summary['overdue_optional']}"
    )
    print(f"[*] Report: {report_path}")

    if args.fail_on_overdue and summary["overdue_required"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
