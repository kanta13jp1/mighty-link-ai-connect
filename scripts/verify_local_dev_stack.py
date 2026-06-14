#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Validate the Firebase Emulator + Supabase Local development stack.

This script supports WBS T760. It performs static checks that are safe to run
in CI without launching Docker or Firebase processes, and it can optionally
inspect the current shell environment before a developer starts the local stack.
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
from urllib.parse import urlparse

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback guard.
    tomllib = None  # type: ignore[assignment]


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FIREBASE_PORTS = {
    "auth": 9099,
    "functions": 5001,
    "hosting": 5000,
    "ui": 4000,
}
EXPECTED_SUPABASE_PORTS = {
    "api": 54321,
    "db": 54322,
    "studio": 54323,
}
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
SECRET_PATTERNS = [
    re.compile(r"xox[baprs]-[A-Za-z0-9-]+"),
    re.compile(r"hooks\.slack\.com/services/[A-Za-z0-9]+/[A-Za-z0-9]+/[A-Za-z0-9]+"),
    re.compile(r"sk_(?:live|test)_[A-Za-z0-9]+"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    re.compile(r"sb_secret_[A-Za-z0-9_-]+"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----"),
]


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def load_json(path: Path) -> tuple[dict[str, Any], str | None]:
    if not path.exists():
        return {}, "missing"
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, f"invalid JSON: {exc}"
    if not isinstance(loaded, dict):
        return {}, "root must be an object"
    return loaded, None


def load_toml(path: Path) -> tuple[dict[str, Any], str | None]:
    if tomllib is None:
        return {}, "Python 3.11+ tomllib is required"
    if not path.exists():
        return {}, "missing"
    try:
        loaded = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        return {}, f"invalid TOML: {exc}"
    if not isinstance(loaded, dict):
        return {}, "root must be a table"
    return loaded, None


def as_bool(value: Any) -> bool:
    return bool(value) if isinstance(value, bool) else str(value).strip().lower() in {"1", "true", "yes", "on"}


def validate_firebase(project_root: Path, checks: list[dict[str, Any]]) -> None:
    firebase_json, firebase_error = load_json(project_root / "firebase.json")
    firebaserc, firebaserc_error = load_json(project_root / ".firebaserc")

    if firebase_error:
        add_check(checks, "firebase.json", "critical", f"firebase.json is not usable: {firebase_error}")
        return
    add_check(checks, "firebase.json", "ok", "firebase.json is valid JSON")

    if firebaserc_error:
        add_check(checks, ".firebaserc", "warning", f".firebaserc is not usable: {firebaserc_error}")
    else:
        projects = firebaserc.get("projects") if isinstance(firebaserc.get("projects"), dict) else {}
        if str(projects.get("default") or "").strip():
            add_check(checks, ".firebaserc.default", "ok", "Default Firebase project is configured")
        else:
            add_check(checks, ".firebaserc.default", "warning", "Default Firebase project is not configured")

    hosting = firebase_json.get("hosting")
    hosting_config = hosting[0] if isinstance(hosting, list) and hosting else hosting
    if isinstance(hosting_config, dict) and hosting_config.get("site") and hosting_config.get("public"):
        add_check(checks, "firebase.hosting", "ok", "Hosting site and public directory are explicit")
    else:
        add_check(checks, "firebase.hosting", "critical", "Hosting site and public directory must be explicit")

    emulators = firebase_json.get("emulators")
    if not isinstance(emulators, dict):
        add_check(checks, "firebase.emulators", "critical", "firebase.json must define emulator ports")
        return

    for service, expected_port in EXPECTED_FIREBASE_PORTS.items():
        config = emulators.get(service)
        port = config.get("port") if isinstance(config, dict) else None
        if port == expected_port:
            add_check(
                checks,
                f"firebase.emulators.{service}",
                "ok",
                f"{service} emulator port is pinned",
                {"port": expected_port},
            )
        else:
            add_check(
                checks,
                f"firebase.emulators.{service}",
                "critical",
                f"{service} emulator port must be {expected_port}",
                {"actual": port, "expected": expected_port},
            )

    ui_config = emulators.get("ui")
    if isinstance(ui_config, dict) and as_bool(ui_config.get("enabled", True)):
        add_check(checks, "firebase.emulators.ui.enabled", "ok", "Emulator UI is enabled")
    else:
        add_check(checks, "firebase.emulators.ui.enabled", "warning", "Emulator UI should remain enabled locally")

    if as_bool(emulators.get("singleProjectMode", False)):
        add_check(checks, "firebase.emulators.singleProjectMode", "ok", "Single project mode is enabled")
    else:
        add_check(
            checks,
            "firebase.emulators.singleProjectMode",
            "warning",
            "Enable singleProjectMode to avoid cross-project local emulator mistakes",
        )


def nested(config: Mapping[str, Any], *keys: str) -> Any:
    current: Any = config
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def validate_supabase(project_root: Path, checks: list[dict[str, Any]]) -> None:
    config_path = project_root / "supabase" / "config.toml"
    config, error = load_toml(config_path)
    if error:
        add_check(checks, "supabase.config", "critical", f"supabase/config.toml is not usable: {error}")
        return
    add_check(checks, "supabase.config", "ok", "supabase/config.toml is valid TOML")

    project_id = str(config.get("project_id") or "").strip()
    if project_id and not any(word in project_id.lower() for word in ("prod", "production")):
        add_check(checks, "supabase.project_id", "ok", "Supabase local project_id is non-production")
    else:
        add_check(checks, "supabase.project_id", "critical", "Supabase local project_id must be explicit and non-production")

    for section, expected_port in EXPECTED_SUPABASE_PORTS.items():
        port = nested(config, section, "port")
        enabled = nested(config, section, "enabled")
        if port == expected_port:
            add_check(checks, f"supabase.{section}.port", "ok", f"{section} port is pinned", {"port": expected_port})
        else:
            add_check(
                checks,
                f"supabase.{section}.port",
                "critical",
                f"{section} port must be {expected_port}",
                {"actual": port, "expected": expected_port},
            )
        if section != "db" and enabled is False:
            add_check(checks, f"supabase.{section}.enabled", "critical", f"{section} service must be enabled")

    seed_enabled = nested(config, "db", "seed", "enabled")
    seed_paths = nested(config, "db", "seed", "sql_paths")
    if seed_enabled is True and isinstance(seed_paths, list) and "./seed.sql" in seed_paths:
        add_check(checks, "supabase.seed.config", "ok", "Supabase local seed is explicitly configured")
    else:
        add_check(checks, "supabase.seed.config", "critical", "db.seed.sql_paths must include ./seed.sql")

    seed_file = project_root / "supabase" / "seed.sql"
    if seed_file.exists():
        add_check(checks, "supabase.seed.file", "ok", "Supabase local seed file exists")
    else:
        add_check(checks, "supabase.seed.file", "critical", "supabase/seed.sql is missing")

    migrations_dir = project_root / "supabase" / "migrations"
    migration_count = len(list(migrations_dir.glob("*.sql"))) if migrations_dir.exists() else 0
    if migration_count:
        add_check(checks, "supabase.migrations", "ok", "Supabase migrations are present", {"count": migration_count})
    else:
        add_check(checks, "supabase.migrations", "critical", "Supabase migrations are missing")

    site_url = str(nested(config, "auth", "site_url") or "").strip()
    if site_url == "http://localhost:3000":
        add_check(checks, "supabase.auth.site_url", "ok", "Local auth site_url is localhost")
    else:
        add_check(checks, "supabase.auth.site_url", "warning", "Local auth site_url should be http://localhost:3000")


def validate_seed_safety(project_root: Path, checks: list[dict[str, Any]]) -> None:
    seed_file = project_root / "supabase" / "seed.sql"
    if not seed_file.exists():
        return
    seed_text = seed_file.read_text(encoding="utf-8")
    if "@ml-mightylink.com" in seed_text or "mightylink-app.com" in seed_text:
        add_check(checks, "supabase.seed.synthetic", "critical", "Seed data must not contain company or production-domain emails")
    elif "@example.test" in seed_text:
        add_check(checks, "supabase.seed.synthetic", "ok", "Seed data uses reserved synthetic example.test identities")
    else:
        add_check(checks, "supabase.seed.synthetic", "warning", "Seed data should use reserved synthetic example.test identities")


def secret_hits(path: Path) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    hits: list[str] = []
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            hits.append(pattern.pattern)
    return hits


def validate_secret_scan(project_root: Path, checks: list[dict[str, Any]]) -> None:
    files = [
        project_root / "firebase.json",
        project_root / ".firebaserc",
        project_root / "supabase" / "config.toml",
        project_root / "supabase" / "seed.sql",
    ]
    hit_files: list[str] = []
    for path in files:
        if secret_hits(path):
            hit_files.append(str(path.relative_to(project_root)))
    if hit_files:
        add_check(checks, "local_config.secret_scan", "critical", "Secret-like values found in local stack config", {"files": hit_files})
    else:
        add_check(checks, "local_config.secret_scan", "ok", "No secret-like values found in local stack config")


def redacted_url_details(value: str) -> dict[str, Any]:
    parsed = urlparse(value)
    return {
        "scheme": parsed.scheme or None,
        "hostname": parsed.hostname or None,
        "port": parsed.port,
        "path_present": bool(parsed.path and parsed.path != "/"),
    }


def is_local_supabase_db_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"postgres", "postgresql"} and parsed.hostname in LOCAL_HOSTS and parsed.port == 54322


def validate_current_env(env: Mapping[str, str], checks: list[dict[str, Any]]) -> None:
    db_url = str(env.get("SUPABASE_DB_URL") or "").strip()
    if not db_url:
        add_check(checks, "local_env.supabase_db_url", "ok", "SUPABASE_DB_URL is unset; local stack does not require production DB credentials")
    elif is_local_supabase_db_url(db_url):
        add_check(
            checks,
            "local_env.supabase_db_url",
            "ok",
            "SUPABASE_DB_URL points to local Supabase DB",
            redacted_url_details(db_url),
        )
    else:
        add_check(
            checks,
            "local_env.supabase_db_url",
            "critical",
            "Unset production SUPABASE_DB_URL before running local integration tests",
            redacted_url_details(db_url),
        )


def build_report(
    project_root: Path = PROJECT_ROOT,
    env: Mapping[str, str] | None = None,
    *,
    check_env: bool = False,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    checks: list[dict[str, Any]] = []

    validate_firebase(project_root, checks)
    validate_supabase(project_root, checks)
    validate_seed_safety(project_root, checks)
    validate_secret_scan(project_root, checks)
    if check_env:
        validate_current_env(env or os.environ, checks)

    status = "ok"
    if any(check["state"] == "critical" for check in checks):
        status = "critical"
    elif any(check["state"] == "warning" for check in checks):
        status = "warning"

    return {
        "status": status,
        "generated_at": utc_now(),
        "summary": {
            "ok": sum(1 for check in checks if check["state"] == "ok"),
            "warning": sum(1 for check in checks if check["state"] == "warning"),
            "critical": sum(1 for check in checks if check["state"] == "critical"),
        },
        "checks": checks,
    }


def print_console_report(report: dict[str, Any]) -> None:
    print(f"Local development stack: {report['status']}")
    print("-" * 96)
    print("state      key                                      message")
    print("-" * 96)
    for check in report["checks"]:
        print(f"{check['state'][:9]:9} {check['key'][:40]:40} {check['message']}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--check-env", action="store_true", help="Also validate the current shell environment.")
    parser.add_argument("--json", action="store_true", help="Print the full JSON report.")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "exports" / "local_dev_stack_report.json")
    parser.add_argument("--fail-on-critical", action="store_true", help="Exit non-zero only on critical findings.")
    parser.add_argument("--fail-on-alert", action="store_true", help="Exit non-zero on warning or critical findings.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report = build_report(args.project_root, check_env=args.check_env)

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
