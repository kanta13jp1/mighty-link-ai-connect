#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Create a custom-domain DNS/RDAP diagnostic packet for T855."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOMAIN = "mightylink-app.com"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "custom_domain_dns_diagnostic.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "custom_domain_dns_diagnostic.md"
DNS_SERVERS = ("8.8.8.8", "1.1.1.1")
QUERY_TYPES = ("NS", "SOA", "A", "AAAA", "TXT")


def utc_timestamp() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_rdap(domain: str, timeout_seconds: int) -> tuple[dict[str, Any] | None, str | None]:
    url = f"https://rdap.org/domain/{domain}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mighty-Link-DNS-Diagnostic/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
        return json.loads(body), None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def run_nslookup(domain: str, query_type: str, server: str, timeout_seconds: int) -> dict[str, Any]:
    command = ["nslookup", f"-type={query_type}", domain, server]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            # Windows nslookup emits locale-encoded output (e.g. CP932 on Japanese
            # Windows); decoding must never crash the diagnostic (R118).
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        stdout = (completed.stdout or "").strip()
        stderr = (completed.stderr or "").strip()
        output = "\n".join(part for part in [stdout, stderr] if part)
        return {
            "server": server,
            "query_type": query_type,
            "returncode": completed.returncode,
            "output": output,
            "nxdomain": is_nxdomain(output),
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "server": server,
            "query_type": query_type,
            "returncode": None,
            "output": "",
            "error": f"{type(exc).__name__}: {exc}",
            "nxdomain": False,
        }


def is_nxdomain(output: str) -> bool:
    lowered = output.lower()
    return "non-existent domain" in lowered or "nxdomain" in lowered


def analyze(rdap: dict[str, Any] | None, dns_results: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = [str(status).lower() for status in (rdap or {}).get("status", [])]
    nameservers = [item.get("ldhName", "") for item in (rdap or {}).get("nameservers", []) if item.get("ldhName")]
    has_client_hold = "client hold" in statuses or "clienthold" in statuses
    ns_queries = [row for row in dns_results if row.get("query_type") == "NS"]
    all_ns_nxdomain = bool(ns_queries) and all(row.get("nxdomain") for row in ns_queries)
    blockers: list[str] = []
    recommendations: list[str] = []

    if has_client_hold:
        blockers.append("rdap_client_hold")
        recommendations.append(
            "Ask the onamae.com domain owner to confirm why the domain is on client hold "
            "and complete any required verification, payment, abuse, or registrant-data action."
        )
    if all_ns_nxdomain:
        blockers.append("public_dns_nxdomain")
        recommendations.append(
            "Verify authoritative DNS delegation and publish the Firebase Hosting required records "
            "on the DNS zone that is actually authoritative after the hold is cleared."
        )
    if nameservers:
        recommendations.append(
            "Compare the RDAP nameservers with the DNS provider where records are being edited."
        )
    if not recommendations:
        recommendations.append(
            "Compare Firebase Hosting custom-domain guidance with public DNS results, then rerun strict HTTPS uptime checks."
        )

    return {
        "status": "blocked" if blockers else "ready_for_uptime_recheck",
        "blockers": blockers,
        "rdap_statuses": statuses,
        "rdap_nameservers": nameservers,
        "recommendations": recommendations,
    }


def build_report(domain: str, timeout_seconds: int) -> dict[str, Any]:
    rdap, rdap_error = fetch_rdap(domain, timeout_seconds)
    dns_results = [
        run_nslookup(domain, query_type, server, timeout_seconds)
        for server in DNS_SERVERS
        for query_type in QUERY_TYPES
    ]
    analysis = analyze(rdap, dns_results)
    return {
        "task_id": "T856",
        "parent_task_id": "T855",
        "domain": domain,
        "generated_at_utc": utc_timestamp(),
        "rdap_error": rdap_error,
        "rdap": rdap,
        "dns_results": dns_results,
        "analysis": analysis,
        "official_docs": [
            "https://firebase.google.com/docs/hosting/custom-domain",
            "https://help.onamae.com/answer/14353",
            "https://icann.org/epp",
        ],
    }


def write_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    analysis = report["analysis"]
    rdap = report.get("rdap") or {}
    events = rdap.get("events", [])
    lines = [
        "# Custom Domain DNS Diagnostic",
        "",
        f"- Generated: {report['generated_at_utc']}",
        f"- Domain: `{report['domain']}`",
        f"- Status: `{analysis['status']}`",
        f"- Blockers: {', '.join(analysis['blockers']) if analysis['blockers'] else 'none'}",
        "",
        "## RDAP",
        "",
        f"- Statuses: {', '.join(analysis['rdap_statuses']) if analysis['rdap_statuses'] else 'unknown'}",
        f"- Nameservers: {', '.join(analysis['rdap_nameservers']) if analysis['rdap_nameservers'] else 'unknown'}",
    ]
    if events:
        lines.extend(["", "## RDAP Events", ""])
        for event in events:
            lines.append(f"- {event.get('eventAction', '')}: {event.get('eventDate', '')}")
    lines.extend(["", "## DNS Summary", ""])
    for row in report["dns_results"]:
        result = "NXDOMAIN" if row.get("nxdomain") else f"returncode={row.get('returncode')}"
        lines.append(f"- {row['server']} {row['query_type']}: {result}")
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in analysis["recommendations"])
    lines.extend(
        [
            "",
            "## Official Docs",
            "",
            "- Firebase Hosting custom domain: https://firebase.google.com/docs/hosting/custom-domain",
            "- onamae.com DNS record setup: https://help.onamae.com/answer/14353",
            "- ICANN EPP status codes: https://icann.org/epp",
        ]
    )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", default=DEFAULT_DOMAIN)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--fail-on-blocked", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report = build_report(args.domain, args.timeout_seconds)
    write_json(report, args.json_output)
    write_markdown(report, args.md_output)
    status = report["analysis"]["status"]
    blockers = ",".join(report["analysis"]["blockers"]) or "none"
    print(f"Custom domain DNS diagnostic: {status} (blockers={blockers})")
    if args.fail_on_blocked and status == "blocked":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
