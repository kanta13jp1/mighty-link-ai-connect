#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Validate release notes and semantic versioning evidence for T806."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "T806"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERSION = PROJECT_ROOT / "VERSION"
DEFAULT_CHANGELOG = PROJECT_ROOT / "CHANGELOG.md"
DEFAULT_RUNBOOK = PROJECT_ROOT / "docs" / "RELEASE_VERSIONING_RUNBOOK.md"
DEFAULT_GO_NO_GO = PROJECT_ROOT / "exports" / "production_go_no_go_review.json"
DEFAULT_WBS = PROJECT_ROOT / "data" / "WBS.tsv"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "release_versioning_review.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "release_versioning_review.md"

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
SECRET_PATTERNS = (
    re.compile(r"postgres(?:ql)?://[^\s`\"']+", re.IGNORECASE),
    re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/_-]+", re.IGNORECASE),
    re.compile(r"sb_(?:secret|publishable|service_role)_[A-Za-z0-9_-]+", re.IGNORECASE),
    re.compile(r"sk_(?:test|live)_[A-Za-z0-9]+", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----"),
    re.compile(r"(?:api[_-]?key|token|password|secret)=([A-Za-z0-9._=-]+)", re.IGNORECASE),
)


@dataclass(frozen=True)
class Check:
    key: str
    state: str
    message: str
    details: dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_wbs_status(wbs_path: Path, task_id: str) -> str:
    if not wbs_path.exists():
        return "missing"
    with wbs_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            if (row.get("タスクID") or "").strip() == task_id:
                return (row.get("ステータス") or "").strip() or "missing_status"
    return "missing"


def load_go_no_go(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def find_secret_like_text(paths: list[Path]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in paths:
        if not path.exists() or path.is_dir():
            continue
        text = read_text(path)
        for pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                findings.append(
                    {
                        "path": display_path(path),
                        "pattern": pattern.pattern,
                        "excerpt": "<redacted>",
                    }
                )
    return findings


def check_version(version: str, expected_version: str | None) -> Check:
    if not version:
        return Check("version.file", "critical", "VERSION file is empty or missing.", {})
    if expected_version and version != expected_version:
        return Check(
            "version.expected",
            "critical",
            "VERSION does not match the expected release version.",
            {"version": version, "expected_version": expected_version},
        )
    if not SEMVER_RE.match(version):
        return Check("version.semver", "critical", "VERSION is not valid SemVer 2.0.0.", {"version": version})
    prerelease = "-" in version
    return Check(
        "version.semver",
        "ok",
        "VERSION is valid SemVer.",
        {"version": version, "tag": f"v{version}", "prerelease": prerelease},
    )


def check_changelog(changelog: str, version: str) -> Check:
    heading = f"## [{version}]"
    if heading not in changelog:
        return Check(
            "changelog.section",
            "critical",
            "CHANGELOG.md does not contain the release version section.",
            {"expected_heading": heading},
        )
    required_terms = ["controlled_demo", "public_paid_launch", "NO_GO"]
    missing = [term for term in required_terms if term not in changelog]
    state = "critical" if missing else "ok"
    return Check(
        "changelog.section",
        state,
        "CHANGELOG.md contains the release section and release boundary." if not missing else "CHANGELOG.md is missing release boundary terms.",
        {"expected_heading": heading, "missing_terms": missing},
    )


def check_go_no_go_boundary(report: dict[str, Any], version: str) -> Check:
    scopes = report.get("scopes", {}) if isinstance(report, dict) else {}
    controlled = scopes.get("controlled_demo", {}).get("recommendation")
    paid = scopes.get("public_paid_launch", {}).get("recommendation")
    prerelease = "-" in version
    if controlled != "GO":
        return Check(
            "go_no_go.controlled_demo",
            "critical",
            "controlled_demo must be GO before issuing a controlled demo release.",
            {"controlled_demo": controlled},
        )
    if paid == "GO" and prerelease:
        return Check(
            "go_no_go.public_paid_launch",
            "warning",
            "public_paid_launch is GO but the version is still a prerelease.",
            {"public_paid_launch": paid, "version": version},
        )
    if paid != "GO" and not prerelease:
        return Check(
            "go_no_go.public_paid_launch",
            "critical",
            "A GA version cannot be issued while public_paid_launch is not GO.",
            {"public_paid_launch": paid, "version": version},
        )
    return Check(
        "go_no_go.boundary",
        "ok",
        "Release version boundary matches the current Go/No-Go state.",
        {"controlled_demo": controlled, "public_paid_launch": paid, "version": version},
    )


def build_report(
    *,
    version_path: Path = DEFAULT_VERSION,
    changelog_path: Path = DEFAULT_CHANGELOG,
    runbook_path: Path = DEFAULT_RUNBOOK,
    go_no_go_path: Path = DEFAULT_GO_NO_GO,
    wbs_path: Path = DEFAULT_WBS,
    expected_version: str | None = None,
) -> dict[str, Any]:
    version = read_text(version_path).strip()
    changelog = read_text(changelog_path)
    runbook_exists = runbook_path.exists()
    go_no_go = load_go_no_go(go_no_go_path)
    wbs_status = load_wbs_status(wbs_path, TASK_ID)

    checks = [
        check_version(version, expected_version),
        check_changelog(changelog, version),
        Check(
            "runbook.exists",
            "ok" if runbook_exists else "critical",
            "Release versioning runbook exists." if runbook_exists else "Release versioning runbook is missing.",
            {"path": display_path(runbook_path)},
        ),
        check_go_no_go_boundary(go_no_go, version),
        Check(
            "wbs.status",
            "ok" if wbs_status == "完了" else "warning",
            "WBS T806 is marked complete." if wbs_status == "完了" else "WBS T806 is not marked complete yet.",
            {"task_id": TASK_ID, "status": wbs_status},
        ),
    ]
    secret_findings = find_secret_like_text([version_path, changelog_path, runbook_path])
    checks.append(
        Check(
            "release.secret_free",
            "critical" if secret_findings else "ok",
            "Release artifacts contain no secret-like values." if not secret_findings else "Release artifacts contain secret-like values.",
            {"findings": secret_findings},
        )
    )

    counts: dict[str, int] = {}
    for check in checks:
        counts[check.state] = counts.get(check.state, 0) + 1
    status = "critical" if counts.get("critical") else "warning" if counts.get("warning") else "ok"
    return {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "status": status,
        "version": version,
        "tag": f"v{version}" if version else "",
        "github_release_prerelease": "-" in version if version else None,
        "checks": [asdict(check) for check in checks],
        "summary": {"counts": counts},
        "sources": {
            "version": display_path(version_path),
            "changelog": display_path(changelog_path),
            "runbook": display_path(runbook_path),
            "go_no_go": display_path(go_no_go_path),
            "wbs": display_path(wbs_path),
        },
    }


def write_report(report: dict[str, Any], json_path: Path = DEFAULT_JSON, md_path: Path = DEFAULT_MD) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rows = "\n".join(
        f"| {check['key']} | {check['state']} | {check['message']} |"
        for check in report["checks"]
    )
    release_kind = "Prerelease" if report.get("github_release_prerelease") else "GA"
    md = f"""# Release Versioning Review

Generated: {report['generated_at']}

| Field | Value |
| --- | --- |
| Task | {report['task_id']} |
| Status | {report['status']} |
| Version | `{report['version']}` |
| Tag | `{report['tag']}` |
| GitHub Release Kind | {release_kind} |

## Checks

| Check | State | Message |
| --- | --- | --- |
{rows}

## GitHub Release Notes

# {report['tag']} controlled demo prerelease

This is a controlled-demo prerelease for CEO/internal review.

## Scope

- controlled_demo: GO
- public_paid_launch: NO_GO

## Highlights

- Custom domain and Firebase-managed HTTPS baseline.
- Sales-email AI matching MVP foundations through human review.
- Company account migration preparation.
- Release governance, rollback, monitoring, and support operations.

## Boundary

This release is not a public paid launch.
"""
    md_path.write_text(md, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-version", default=None)
    parser.add_argument("--json-output", default=str(DEFAULT_JSON))
    parser.add_argument("--markdown-output", default=str(DEFAULT_MD))
    parser.add_argument("--fail-on-warning", action="store_true")
    args = parser.parse_args()

    report = build_report(expected_version=args.expected_version)
    write_report(report, Path(args.json_output), Path(args.markdown_output))
    print(f"[+] Release versioning review generated: {report['status']} ({report['tag']})")
    print(f"[*] JSON: {args.json_output}")
    print(f"[*] Markdown: {args.markdown_output}")
    if report["status"] == "critical" or (args.fail_on_warning and report["status"] == "warning"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
