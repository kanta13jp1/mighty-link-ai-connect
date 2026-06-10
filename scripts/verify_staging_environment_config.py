#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Verify Firebase/Supabase staging separation without printing secrets.

The script supports WBS T788. It checks local Firebase config and environment
variable wiring for the staging lane before any preview deploy or database
migration is attempted.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PREVIEW_CHANNELS = {"live", "prod", "production", "main", "master", "default"}
PREVIEW_CHANNEL_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
TRUTHY = {"1", "true", "yes", "on"}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"__invalid_json__": True}
    return loaded if isinstance(loaded, dict) else {}


def env_value(env: Mapping[str, str], name: str) -> str:
    return str(env.get(name) or "").strip()


def is_truthy(value: str) -> bool:
    return value.strip().lower() in TRUTHY


def add_check(
    checks: list[dict[str, Any]],
    key: str,
    state: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> None:
    row: dict[str, Any] = {"key": key, "state": state, "message": message}
    if details:
        row["details"] = details
    checks.append(row)


def compare_secret_pair(
    checks: list[dict[str, Any]],
    key: str,
    staging_value: str,
    prod_value: str,
    *,
    missing_message: str,
    same_message: str,
    different_message: str,
) -> None:
    if staging_value and prod_value:
        if staging_value == prod_value:
            add_check(checks, key, "critical", same_message)
        else:
            add_check(checks, key, "ok", different_message)
        return

    missing: list[str] = []
    if not staging_value:
        missing.append("staging")
    if not prod_value:
        missing.append("prod")
    add_check(checks, key, "warning", missing_message, {"missing": missing})


def firebase_project_ids(
    firebaserc: dict[str, Any],
    env: Mapping[str, str],
) -> tuple[str, str]:
    projects = firebaserc.get("projects") if isinstance(firebaserc.get("projects"), dict) else {}
    default_project = str(projects.get("default") or "").strip()
    prod_project = (
        env_value(env, "FIREBASE_PROD_PROJECT_ID")
        or env_value(env, "FIREBASE_PROJECT_ID")
        or default_project
    )
    staging_project = env_value(env, "FIREBASE_STAGING_PROJECT_ID")
    return prod_project, staging_project


def validate_firebase_config(project_root: Path, env: Mapping[str, str], checks: list[dict[str, Any]]) -> None:
    firebase_json = load_json(project_root / "firebase.json")
    firebaserc = load_json(project_root / ".firebaserc")

    if firebase_json.get("__invalid_json__"):
        add_check(checks, "firebase.json", "critical", "firebase.json is invalid JSON")
        return
    if firebaserc.get("__invalid_json__"):
        add_check(checks, ".firebaserc", "critical", ".firebaserc is invalid JSON")
        return

    hosting = firebase_json.get("hosting")
    hosting_config = hosting[0] if isinstance(hosting, list) and hosting else hosting
    hosting_site = ""
    if isinstance(hosting_config, dict):
        hosting_site = str(hosting_config.get("site") or "").strip()
    if hosting_site:
        add_check(checks, "firebase.hosting.site", "ok", "Firebase Hosting site is explicitly configured")
    else:
        add_check(checks, "firebase.hosting.site", "warning", "Firebase Hosting site is not explicit")

    prod_project, staging_project = firebase_project_ids(firebaserc, env)
    if prod_project:
        add_check(checks, "firebase.prod_project", "ok", "Firebase production project is resolved")
    else:
        add_check(
            checks,
            "firebase.prod_project",
            "warning",
            "Firebase production project is not set in env or .firebaserc",
        )

    if staging_project and prod_project and staging_project == prod_project:
        add_check(
            checks,
            "firebase.staging_project",
            "critical",
            "FIREBASE_STAGING_PROJECT_ID must differ from the production Firebase project",
        )
    elif staging_project:
        add_check(checks, "firebase.staging_project", "ok", "Dedicated Firebase staging project is configured")
    else:
        add_check(
            checks,
            "firebase.staging_project",
            "warning",
            "No dedicated Firebase staging project is configured; Hosting preview channel only is assumed",
        )

    preview_channel = env_value(env, "FIREBASE_HOSTING_PREVIEW_CHANNEL") or "staging"
    if preview_channel in FORBIDDEN_PREVIEW_CHANNELS:
        add_check(
            checks,
            "firebase.preview_channel",
            "critical",
            "Preview channel name must not look like production or the live channel",
            {"channel": preview_channel},
        )
    elif not PREVIEW_CHANNEL_PATTERN.fullmatch(preview_channel):
        add_check(
            checks,
            "firebase.preview_channel",
            "critical",
            "Preview channel must be lowercase alphanumeric with optional hyphens",
            {"channel": preview_channel},
        )
    else:
        add_check(
            checks,
            "firebase.preview_channel",
            "ok",
            "Firebase Hosting preview channel name is safe",
            {"channel": preview_channel},
        )

    functions_enabled = is_truthy(env_value(env, "FIREBASE_FUNCTIONS_DEPLOY_ENABLED"))
    functions_allowlisted = is_truthy(env_value(env, "ALLOW_STAGING_FUNCTIONS_DEPLOY"))
    if functions_enabled and not functions_allowlisted:
        add_check(
            checks,
            "firebase.functions_deploy",
            "critical",
            "Functions deploy is enabled without ALLOW_STAGING_FUNCTIONS_DEPLOY=true",
        )
    elif functions_enabled:
        add_check(
            checks,
            "firebase.functions_deploy",
            "warning",
            "Functions deploy is explicitly enabled; confirm IAM and staging project separation before release",
        )
    else:
        add_check(checks, "firebase.functions_deploy", "ok", "Functions deploy remains disabled by default")


def validate_supabase_config(env: Mapping[str, str], checks: list[dict[str, Any]]) -> None:
    compare_secret_pair(
        checks,
        "supabase.url",
        env_value(env, "SUPABASE_STAGING_URL"),
        env_value(env, "SUPABASE_PROD_URL"),
        missing_message="Set SUPABASE_STAGING_URL and SUPABASE_PROD_URL before staging deploy",
        same_message="SUPABASE_STAGING_URL must not equal SUPABASE_PROD_URL",
        different_message="Supabase staging/prod URLs are separated",
    )
    compare_secret_pair(
        checks,
        "supabase.anon_key",
        env_value(env, "SUPABASE_STAGING_ANON_KEY"),
        env_value(env, "SUPABASE_PROD_ANON_KEY"),
        missing_message="Set staging/prod anon key fingerprints before browser integration checks",
        same_message="SUPABASE_STAGING_ANON_KEY must not equal SUPABASE_PROD_ANON_KEY",
        different_message="Supabase staging/prod anon keys differ",
    )
    compare_secret_pair(
        checks,
        "supabase.jwt_secret_fingerprint",
        env_value(env, "SUPABASE_STAGING_JWT_SECRET_FINGERPRINT"),
        env_value(env, "SUPABASE_PROD_JWT_SECRET_FINGERPRINT"),
        missing_message="Store non-secret JWT secret fingerprints for staging/prod comparison",
        same_message="Supabase JWT secret fingerprints must differ across staging/prod",
        different_message="Supabase JWT secret fingerprints are separated",
    )
    compare_secret_pair(
        checks,
        "supabase.service_role_key",
        env_value(env, "SUPABASE_STAGING_SERVICE_ROLE_KEY"),
        env_value(env, "SUPABASE_PROD_SERVICE_ROLE_KEY"),
        missing_message="Service role keys are not present locally; keep them in secret stores only",
        same_message="Supabase staging/prod service role keys must never be the same",
        different_message="Supabase staging/prod service role keys differ",
    )


def build_report(project_root: Path = PROJECT_ROOT, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    env = env or os.environ
    checks: list[dict[str, Any]] = []

    validate_firebase_config(project_root, env, checks)
    validate_supabase_config(env, checks)

    status = "ok"
    if any(check["state"] == "critical" for check in checks):
        status = "critical"
    elif any(check["state"] == "warning" for check in checks):
        status = "warning"

    return {
        "status": status,
        "checks": checks,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def print_console_report(report: dict[str, Any]) -> None:
    print(f"Staging environment config: {report['status']}")
    print("-" * 88)
    print("state      key                                      message")
    print("-" * 88)
    for check in report["checks"]:
        print(f"{check['state'][:9]:9} {check['key'][:40]:40} {check['message']}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--json", action="store_true", help="Print the full JSON report.")
    parser.add_argument("--output", type=Path, help="Write the JSON report to this path.")
    parser.add_argument("--fail-on-critical", action="store_true", help="Exit non-zero only on critical findings.")
    parser.add_argument("--fail-on-alert", action="store_true", help="Exit non-zero on warning or critical findings.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report = build_report(args.project_root)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_console_report(report)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.fail_on_critical and report["status"] == "critical":
        return 2
    if args.fail_on_alert and report["status"] in {"warning", "critical"}:
        return 2 if report["status"] == "critical" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
