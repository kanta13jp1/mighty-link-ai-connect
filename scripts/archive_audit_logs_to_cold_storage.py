#!/usr/bin/env python3
"""Build cold-storage archives for operational and audit logs.

This implements WBS T773. By default it creates a local manifest and zip
package only. Uploading to GCS requires an explicit ``--upload`` flag and a
``gs://`` URI so a session cannot accidentally publish sensitive evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "T773"
DEFAULT_OUTPUT_DIR = Path("exports") / "cold_storage"
DEFAULT_PATTERNS = (
    "data/audit/*.jsonl",
    "data/log_archive/**/*.gz",
    "data/security_log.tsv",
    "data/deploy_log.tsv",
    "data/external_api_usage.jsonl",
    "exports/log_rotation_report.json",
    "exports/issue_qa_blocker_audit.*",
    "exports/production_go_no_go_review.*",
    "exports/uptime_monitor_report.json",
    "exports/custom_domain_dns_diagnostic.*",
    "exports/firebase_hosting_headers_review.*",
    "exports/external_pentest_review*.json",
    "exports/external_pentest_review*.md",
    "exports/secret_rotation_report.json",
    "exports/infra_monitoring_dashboard.*",
    "exports/monthly_quality_*.json",
    "exports/weekly_cost_*.json",
)
SECRET_FILE_NAMES = {
    "authorized_user.json",
    "client_secret.json",
    "credentials.json",
    "service-account.json",
    "service_account.json",
    ".env",
    ".env.local",
    "CLAUDE.local.md",
}
SECRET_PATH_PARTS = {
    ".claude/settings.local.json",
    ".claude\\settings.local.json",
}
SECRET_VALUE_PATTERNS = (
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    re.compile(r"sk_(?:live|test)_[0-9A-Za-z]{16,}"),
    re.compile(r"ghp_[0-9A-Za-z]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[0-9A-Za-z_\-./+=]{24,}"),
)
MAX_TEXT_SCAN_BYTES = 512 * 1024


@dataclass(frozen=True)
class ArchiveSource:
    path: str
    category: str
    size_bytes: int
    sha256: str
    modified_utc: str
    retention_days: int
    storage_class_after_30_days: str
    storage_class_after_365_days: str


@dataclass(frozen=True)
class ExcludedPath:
    path: str
    reason: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def assert_child_path(parent: Path, child: Path) -> None:
    parent_resolved = parent.resolve()
    child_resolved = child.resolve()
    if child_resolved == parent_resolved or parent_resolved not in child_resolved.parents:
        raise ValueError(f"Refusing to operate outside managed path: {child}")


def is_child_path(parent: Path, child: Path) -> bool:
    parent_resolved = parent.resolve()
    child_resolved = child.resolve()
    return child_resolved == parent_resolved or parent_resolved in child_resolved.parents


def relative_posix(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_source(relative_path: str) -> str:
    if relative_path.startswith("data/audit/"):
        return "local_audit_jsonl"
    if relative_path.startswith("data/log_archive/"):
        return "rotated_local_log_archive"
    if relative_path.startswith("data/"):
        return "project_control_log"
    if "pentest" in relative_path or "security" in relative_path or "secret_rotation" in relative_path:
        return "security_evidence"
    if "uptime" in relative_path or "domain" in relative_path:
        return "operations_evidence"
    return "release_or_quality_evidence"


def should_exclude(root: Path, path: Path) -> str | None:
    relative = relative_posix(root, path)
    if path.name in SECRET_FILE_NAMES:
        return "secret filename is never archived"
    if relative in SECRET_PATH_PARTS:
        return "local Claude settings are never archived"
    if ".git/" in relative or relative.startswith(".git/"):
        return "git internals are never archived"
    if path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
        return "database snapshots are out of scope for T773 log archives"
    return None


def scan_for_secret_like_values(path: Path) -> list[str]:
    if path.stat().st_size > MAX_TEXT_SCAN_BYTES:
        return []
    if path.suffix.lower() not in {".json", ".jsonl", ".md", ".tsv", ".txt", ".log", ".csv", ".yml", ".yaml"}:
        return []
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    warnings: list[str] = []
    for pattern in SECRET_VALUE_PATTERNS:
        if pattern.search(content):
            warnings.append(pattern.pattern)
    return warnings


def collect_sources(
    root: Path,
    patterns: tuple[str, ...] = DEFAULT_PATTERNS,
) -> tuple[list[Path], list[ExcludedPath], list[dict[str, str]]]:
    root = root.resolve()
    sources: dict[str, Path] = {}
    excluded: dict[str, ExcludedPath] = {}
    warnings: list[dict[str, str]] = []

    for pattern in patterns:
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            resolved = path.resolve()
            if not is_child_path(root, resolved):
                continue
            relative = relative_posix(root, resolved)
            reason = should_exclude(root, resolved)
            if reason:
                excluded[relative] = ExcludedPath(path=relative, reason=reason)
                continue
            scan_hits = scan_for_secret_like_values(resolved)
            if scan_hits:
                warnings.append(
                    {
                        "path": relative,
                        "reason": "secret-like value pattern detected; review before GCS upload",
                        "patterns": ", ".join(scan_hits),
                    }
                )
            sources[relative] = resolved

    return [sources[key] for key in sorted(sources)], [excluded[key] for key in sorted(excluded)], warnings


def build_lifecycle_policy(prefix: str = "mighty-link/log-archives/") -> dict:
    return {
        "lifecycle": {
            "rule": [
                {
                    "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
                    "condition": {"age": 30, "matchesPrefix": [prefix]},
                },
                {
                    "action": {"type": "SetStorageClass", "storageClass": "ARCHIVE"},
                    "condition": {"age": 365, "matchesPrefix": [prefix]},
                },
                {
                    "action": {"type": "Delete"},
                    "condition": {"age": 2555, "matchesPrefix": [prefix]},
                },
            ]
        }
    }


def build_manifest(
    *,
    root: Path,
    archive_date: str,
    sources: list[Path],
    excluded: list[ExcludedPath],
    secret_scan_warnings: list[dict[str, str]],
    gcs_uri: str | None,
    upload_requested: bool,
    archive_path: Path | None,
) -> dict:
    source_rows: list[ArchiveSource] = []
    for source in sources:
        stat = source.stat()
        relative = relative_posix(root, source)
        modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        source_rows.append(
            ArchiveSource(
                path=relative,
                category=classify_source(relative),
                size_bytes=stat.st_size,
                sha256=sha256_file(source),
                modified_utc=modified,
                retention_days=2555,
                storage_class_after_30_days="COLDLINE",
                storage_class_after_365_days="ARCHIVE",
            )
        )

    gcs_prefix = "<company-bucket>/mighty-link/log-archives/"
    if gcs_uri:
        gcs_prefix = gcs_uri.rstrip("/") + "/"

    return {
        "task_id": TASK_ID,
        "generated_at_utc": utc_now().isoformat(),
        "archive_date": archive_date,
        "root": ".",
        "sources": [asdict(row) for row in source_rows],
        "excluded": [asdict(row) for row in excluded],
        "secret_scan_warnings": secret_scan_warnings,
        "archive_path": relative_posix(root, archive_path) if archive_path else None,
        "gcs": {
            "uri": gcs_uri,
            "upload_requested": upload_requested,
            "upload_performed": False,
            "target_storage_classes": ["COLDLINE", "ARCHIVE"],
            "retention_days": 2555,
            "lifecycle_policy_file": "gcs_lifecycle_policy_template.json",
            "setup_commands": [
                "gcloud storage buckets create gs://<company-bucket> --location=asia-northeast1 --uniform-bucket-level-access",
                "gcloud storage buckets update gs://<company-bucket> --lifecycle-file=exports/cold_storage/gcs_lifecycle_policy_template.json",
                f"python scripts/archive_audit_logs_to_cold_storage.py --gcs-uri {gcs_prefix} --upload",
            ],
        },
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_zip_archive(root: Path, archive_path: Path, sources: list[Path], manifest_path: Path) -> None:
    assert_child_path(root, archive_path)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(manifest_path, arcname="manifest.json")
        for source in sources:
            zf.write(source, arcname=relative_posix(root, source))


def validate_gcs_uri(gcs_uri: str | None) -> None:
    if gcs_uri and not gcs_uri.startswith("gs://"):
        raise ValueError("gcs-uri must start with gs://")


def upload_archive(archive_path: Path, gcs_uri: str, secret_scan_warnings: list[dict[str, str]]) -> str:
    if secret_scan_warnings:
        raise ValueError("Refusing GCS upload while secret-like scan warnings exist")
    destination = gcs_uri.rstrip("/") + "/" + archive_path.name
    subprocess.run(["gcloud", "storage", "cp", str(archive_path), destination], check=True)
    return destination


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a cold-storage manifest and optional GCS archive for audit logs."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project root.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--archive-date", default=datetime.now().date().isoformat())
    parser.add_argument("--pattern", action="append", default=None)
    parser.add_argument("--manifest-only", action="store_true")
    parser.add_argument("--gcs-uri", default=None)
    parser.add_argument("--upload", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    assert_child_path(root, output_dir)
    validate_gcs_uri(args.gcs_uri)
    if args.upload and not args.gcs_uri:
        raise ValueError("--upload requires --gcs-uri gs://...")

    patterns = tuple(args.pattern or DEFAULT_PATTERNS)
    sources, excluded, warnings = collect_sources(root=root, patterns=patterns)
    archive_name = f"mighty-link-log-archive-{args.archive_date}.zip"
    archive_path = None if args.manifest_only else output_dir / archive_name
    manifest_path = output_dir / f"cold_storage_manifest_{args.archive_date}.json"
    lifecycle_path = output_dir / "gcs_lifecycle_policy_template.json"

    manifest = build_manifest(
        root=root,
        archive_date=args.archive_date,
        sources=sources,
        excluded=excluded,
        secret_scan_warnings=warnings,
        gcs_uri=args.gcs_uri,
        upload_requested=args.upload,
        archive_path=archive_path,
    )
    write_json(manifest_path, manifest)
    write_json(lifecycle_path, build_lifecycle_policy())

    uploaded_to = None
    if archive_path:
        create_zip_archive(root=root, archive_path=archive_path, sources=sources, manifest_path=manifest_path)
    if args.upload and archive_path:
        uploaded_to = upload_archive(archive_path, args.gcs_uri, warnings)
        manifest["gcs"]["upload_performed"] = True
        manifest["gcs"]["uploaded_to"] = uploaded_to
        write_json(manifest_path, manifest)

    print(
        f"[+] {TASK_ID} cold-storage manifest wrote {len(sources)} source(s); "
        f"excluded {len(excluded)} path(s); warnings {len(warnings)}. Manifest: {manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
