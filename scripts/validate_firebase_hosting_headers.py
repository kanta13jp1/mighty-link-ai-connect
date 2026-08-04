#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Validate Firebase Hosting security headers for T835.

This is a static guard for firebase.json. It does not replace the external
pentest review, but it catches configuration drift before deploys and provides
redacted evidence for WBS/Sheets/GitHub.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "T835"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIREBASE_JSON = Path("firebase.json")
DEFAULT_JSON_REPORT = Path("exports") / "firebase_hosting_headers_review.json"
DEFAULT_MARKDOWN_REPORT = Path("exports") / "firebase_hosting_headers_review.md"

REQUIRED_CSP_TOKENS = {
    "default-src": ["'self'"],
    "base-uri": ["'self'"],
    "object-src": ["'none'"],
    "frame-ancestors": ["'none'"],
    "form-action": ["'self'"],
    "script-src": ["'self'", "https://cdn.jsdelivr.net"],
    "style-src": ["'self'", "https://fonts.googleapis.com"],
    "font-src": ["'self'", "https://fonts.gstatic.com"],
    "img-src": ["'self'", "data:"],
    "media-src": ["'self'"],
    "connect-src": ["'self'", "https://cdn.jsdelivr.net"],
    "worker-src": ["'self'"],
    "frame-src": ["'self'"],
    "upgrade-insecure-requests": [],
}

PERMISSIONS_POLICY_REQUIRED = [
    "camera=()",
    "microphone=()",
    "geolocation=()",
    "payment=()",
]


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
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object JSON in {path}")
    return payload


def hosting_blocks(config: dict[str, Any]) -> list[dict[str, Any]]:
    hosting = config.get("hosting")
    if isinstance(hosting, dict):
        return [hosting]
    if isinstance(hosting, list) and all(isinstance(item, dict) for item in hosting):
        return list(hosting)
    return []


def source_covers_all(source: str) -> bool:
    return source.strip() in {"**", "/**", "**/*", "/**/*"}


def collect_global_headers(config: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    headers: dict[str, str] = {}
    sources: list[str] = []
    for block in hosting_blocks(config):
        for rule in block.get("headers") or []:
            if not isinstance(rule, dict):
                continue
            source = str(rule.get("source") or "")
            if not source_covers_all(source):
                continue
            sources.append(source)
            for header in rule.get("headers") or []:
                if not isinstance(header, dict):
                    continue
                key = str(header.get("key") or "").strip().lower()
                value = str(header.get("value") or "").strip()
                if key and value:
                    headers[key] = value
    return headers, sources


def parse_csp(value: str) -> dict[str, list[str]]:
    directives: dict[str, list[str]] = {}
    for part in value.split(";"):
        part = part.strip()
        if not part:
            continue
        pieces = part.split()
        directives[pieces[0].lower()] = pieces[1:]
    return directives


def hsts_max_age(value: str) -> int | None:
    match = re.search(r"(?:^|;)\s*max-age=(\d+)", value, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def review_headers(config: dict[str, Any]) -> dict[str, Any]:
    headers, sources = collect_global_headers(config)
    findings: list[dict[str, str]] = []

    if not sources:
        findings.append(
            {
                "severity": "HIGH",
                "check": "firebase_hosting_global_headers",
                "summary": "No Firebase Hosting headers rule covers every public route.",
                "recommendation": "Add hosting.headers with source \"**\" in firebase.json.",
            }
        )

    csp = headers.get("content-security-policy")
    if not csp:
        findings.append(
            {
                "severity": "HIGH",
                "check": "content-security-policy",
                "summary": "Content-Security-Policy is missing.",
                "recommendation": "Add CSP with default-src, script-src, object-src, and frame-ancestors.",
            }
        )
    else:
        directives = parse_csp(csp)
        for directive, expected_tokens in REQUIRED_CSP_TOKENS.items():
            actual_tokens = directives.get(directive)
            if actual_tokens is None:
                findings.append(
                    {
                        "severity": "HIGH",
                        "check": f"csp.{directive}",
                        "summary": f"CSP directive {directive} is missing.",
                        "recommendation": f"Add {directive} to Content-Security-Policy.",
                    }
                )
                continue
            missing = [token for token in expected_tokens if token not in actual_tokens]
            if missing:
                findings.append(
                    {
                        "severity": "MED",
                        "check": f"csp.{directive}",
                        "summary": f"CSP directive {directive} is missing expected tokens: {', '.join(missing)}.",
                        "recommendation": f"Update {directive} to include the expected allowlist.",
                    }
                )

    if headers.get("x-content-type-options", "").lower() != "nosniff":
        findings.append(
            {
                "severity": "HIGH",
                "check": "x-content-type-options",
                "summary": "X-Content-Type-Options must be nosniff.",
                "recommendation": "Set X-Content-Type-Options: nosniff.",
            }
        )

    referrer = headers.get("referrer-policy", "").lower()
    if referrer not in {"strict-origin-when-cross-origin", "same-origin", "no-referrer"}:
        findings.append(
            {
                "severity": "MED",
                "check": "referrer-policy",
                "summary": "Referrer-Policy is missing or too permissive.",
                "recommendation": "Set Referrer-Policy to strict-origin-when-cross-origin or stricter.",
            }
        )

    permissions = headers.get("permissions-policy", "")
    for token in PERMISSIONS_POLICY_REQUIRED:
        if token not in permissions.replace(" ", ""):
            findings.append(
                {
                    "severity": "MED",
                    "check": "permissions-policy",
                    "summary": f"Permissions-Policy is missing {token}.",
                    "recommendation": "Deny unused browser features by default.",
                }
            )

    xfo = headers.get("x-frame-options", "").upper()
    csp_directives = parse_csp(headers.get("content-security-policy", ""))
    has_frame_ancestors_none = "'none'" in csp_directives.get("frame-ancestors", [])
    if xfo not in {"DENY", "SAMEORIGIN"} and not has_frame_ancestors_none:
        findings.append(
            {
                "severity": "MED",
                "check": "frame-protection",
                "summary": "Neither X-Frame-Options nor CSP frame-ancestors blocks framing.",
                "recommendation": "Set X-Frame-Options: DENY and CSP frame-ancestors 'none'.",
            }
        )

    hsts = headers.get("strict-transport-security", "")
    max_age = hsts_max_age(hsts)
    if max_age is None or max_age < 31_536_000:
        findings.append(
            {
                "severity": "MED",
                "check": "strict-transport-security",
                "summary": "Strict-Transport-Security is missing or max-age is below one year.",
                "recommendation": "Set Strict-Transport-Security: max-age=31536000 or stronger on HTTPS hosting.",
            }
        )

    return {
        "task_id": TASK_ID,
        "generated_at": utc_timestamp(),
        "status": "fail" if findings else "pass",
        "reviewed_sources": sources,
        "headers": headers,
        "findings": findings,
        "notes": [
            "Firebase Hosting production URL is the public paid launch target.",
            "GitHub Pages is a static CEO demo mirror and cannot set arbitrary response headers from repository files.",
            "Current inline scripts/styles require unsafe-inline; migrate to CSP nonce/hash when the frontend bundle is refactored.",
        ],
    }


def render_markdown(report: dict[str, Any], config_path: str) -> str:
    reviewed_sources = ", ".join(f"`{source}`" for source in report["reviewed_sources"]) or "none"
    lines = [
        "# Firebase Hosting Security Headers Review (T835)",
        "",
        f"- Generated at (UTC): {report['generated_at']}",
        f"- Firebase config: `{config_path}`",
        f"- Status: **{report['status'].upper()}**",
        f"- Reviewed source rules: {reviewed_sources}",
        "",
        "## Headers",
        "",
        "| Header | Value |",
        "| :--- | :--- |",
    ]
    for key, value in sorted(report["headers"].items()):
        escaped_value = value.replace("|", "\\|")
        lines.append(f"| `{key}` | `{escaped_value}` |")

    lines.extend(["", "## Findings", ""])
    if not report["findings"]:
        lines.append("- No blocking findings.")
    else:
        for finding in report["findings"]:
            lines.append(
                f"- {finding['severity']} `{finding['check']}`: {finding['summary']} "
                f"Recommendation: {finding['recommendation']}"
            )

    lines.extend(["", "## Notes", ""])
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--firebase-json", type=Path, default=DEFAULT_FIREBASE_JSON)
    parser.add_argument("--json-report", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--markdown-report", type=Path, default=DEFAULT_MARKDOWN_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = args.root.resolve()
    firebase_json = resolve_project_path(root, args.firebase_json)
    json_report = resolve_project_path(root, args.json_report)
    markdown_report = resolve_project_path(root, args.markdown_report)

    try:
        config = load_json(firebase_json)
        report = review_headers(config)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[-] T835 Firebase Hosting header review failed: {exc}", file=sys.stderr)
        return 2

    write_json(json_report, report)
    write_text(markdown_report, render_markdown(report, display_path(root, firebase_json)))
    print(f"[+] T835 Firebase Hosting header review: {report['status']}")
    print(f"[*] JSON: {display_path(root, json_report)}")
    print(f"[*] Markdown: {display_path(root, markdown_report)}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
