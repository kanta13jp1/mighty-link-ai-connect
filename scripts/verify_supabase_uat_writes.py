"""Fail-closed Supabase production UAT write verification (T845/T921).

Offline mode verifies that every UAT table is defined by a migration. Live mode
must be explicitly enabled with ``--execute`` and a ``SUPABASE_DB_URL``. It
inserts synthetic, non-PII rows into all UAT tables, reads them back inside one
transaction, rolls the transaction back, and verifies that no probe rows remain.
No live failure is downgraded to PASS or WARN.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = PROJECT_ROOT / "supabase" / "migrations"
EXPORTS_DIR = PROJECT_ROOT / "exports"

LIVE_UAT_TABLES = (
    "employee_assessment_responses",
    "attendance_punch_events",
    "attendance_timesheet_imports",
    "usage_analytics_events",
    "sales_mailbox_sources",
    "sales_email_messages",
    "sales_email_entities",
    "project_requirements",
    "talent_profiles_from_email",
    "requirement_skill_tags",
    "email_parse_runs",
    "email_match_results",
    "email_match_feedback",
    "feedback_events",
    "support_requests",
)

ConnectionFactory = Callable[[str], Any]


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _base_result(mode: str) -> dict[str, Any]:
    result = {
        "report_id": "SUPABASE_UAT_WRITES_T845_T921",
        "generated_at": _timestamp(),
        "status": "FAIL",
        "mode": mode,
        "has_db_connection": False,
        "live_write_verified": False,
        "transaction_rolled_back": False,
        "cleanup_verified": False,
        "persisted_probe_records": None,
        "checked_tables": list(LIVE_UAT_TABLES),
        "table_status": {
            table: {"verified": False, "mode": mode}
            for table in LIVE_UAT_TABLES
        },
        "summary": "",
    }
    github_run_id = os.getenv("GITHUB_RUN_ID", "").strip()
    if github_run_id:
        server_url = os.getenv("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
        repository = os.getenv("GITHUB_REPOSITORY", "").strip()
        result["github_actions"] = {
            "run_id": github_run_id,
            "commit_sha": os.getenv("GITHUB_SHA", "").strip(),
            "run_url": (
                f"{server_url}/{repository}/actions/runs/{github_run_id}"
                if repository
                else ""
            ),
        }
    return result


def _redact_error(error: BaseException, db_url: str | None = None) -> str:
    message = str(error)
    if db_url:
        message = message.replace(db_url, "[REDACTED_DATABASE_URL]")
    message = re.sub(
        r"(?i)\bpostgres(?:ql)?://[^\s@]+@",
        "postgresql://***@",
        message,
    )
    message = re.sub(r"(?i)\b(password\s*=\s*)[^\s]+", r"\1***", message)
    return message[:500]


def _offline_schema_contract() -> dict[str, Any]:
    result = _base_result("offline_schema_contract")
    migration_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in sorted(MIGRATIONS_DIR.glob("*.sql"))
    )

    missing: list[str] = []
    for table in LIVE_UAT_TABLES:
        pattern = rf"CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+(?:public\.)?{re.escape(table)}\s*\("
        verified = re.search(pattern, migration_text, flags=re.IGNORECASE) is not None
        result["table_status"][table] = {
            "verified": verified,
            "mode": "migration_contract",
        }
        if not verified:
            missing.append(table)

    if missing:
        result["summary"] = (
            "Offline schema contract failed; missing migration definitions: "
            + ", ".join(missing)
        )
        return result

    result["status"] = "PASS"
    result["summary"] = (
        f"Offline schema contract passed for {len(LIVE_UAT_TABLES)} UAT tables. "
        "This does not claim a live database write."
    )
    return result


def _probe_id_base(run_token: str) -> int:
    digest = hashlib.sha256(run_token.encode("utf-8")).hexdigest()
    return -(int(digest[:12], 16) + 10_000)


def _insert_and_read(
    cursor: Any,
    result: dict[str, Any],
    table: str,
    sql: str,
    params: tuple[Any, ...],
) -> int:
    cursor.execute(sql, params)
    row = cursor.fetchone()
    if not row:
        raise RuntimeError(f"{table}: INSERT did not return an id")
    row_id = int(row[0])
    cursor.execute(f"SELECT 1 FROM public.{table} WHERE id = %s", (row_id,))
    if cursor.fetchone() != (1,):
        raise RuntimeError(f"{table}: inserted row could not be read back")
    result["table_status"][table] = {
        "verified": True,
        "mode": "transactional_insert_readback",
        "synthetic": True,
    }
    return row_id


def _run_transactional_inserts(
    cursor: Any,
    result: dict[str, Any],
    run_token: str,
) -> None:
    id_base = _probe_id_base(run_token)
    ids = {
        table: id_base - offset
        for offset, table in enumerate(LIVE_UAT_TABLES, start=1)
    }
    metadata = json.dumps(
        {"uat_run_id": run_token, "synthetic": True, "persist": False},
        separators=(",", ":"),
    )
    digest = hashlib.sha256(run_token.encode("utf-8")).hexdigest()
    sender_digest = hashlib.sha256(f"{run_token}:sender".encode("utf-8")).hexdigest()
    body_digest = hashlib.sha256(f"{run_token}:body".encode("utf-8")).hexdigest()

    assessment_id = _insert_and_read(
        cursor,
        result,
        "employee_assessment_responses",
        """
        INSERT INTO public.employee_assessment_responses
            (id, subject_pseudonym, department_bucket, motivation_level,
             culture_level, growth_support_excerpt, consent_version, status,
             source, session_id, metadata)
        VALUES (%s, %s, %s, 3, 3, %s, %s, 'pending_review', %s, %s, %s::jsonb)
        RETURNING id
        """,
        (
            ids["employee_assessment_responses"],
            f"uat-{run_token}",
            "UAT",
            "Synthetic transactional write probe",
            "uat-t921",
            "uat_transaction_probe",
            run_token,
            metadata,
        ),
    )
    if assessment_id != ids["employee_assessment_responses"]:
        raise RuntimeError("employee_assessment_responses: unexpected id")

    _insert_and_read(
        cursor,
        result,
        "attendance_punch_events",
        """
        INSERT INTO public.attendance_punch_events
            (id, subject_pseudonym, event_type, source, session_id, metadata)
        VALUES (%s, %s, 'clock_in', %s, %s, %s::jsonb)
        RETURNING id
        """,
        (
            ids["attendance_punch_events"],
            f"uat-{run_token}",
            "uat_transaction_probe",
            run_token,
            metadata,
        ),
    )
    _insert_and_read(
        cursor,
        result,
        "attendance_timesheet_imports",
        """
        INSERT INTO public.attendance_timesheet_imports
            (id, subject_pseudonym, file_digest, file_extension, work_minutes,
             overtime_minutes, holiday_work_days, midnight_minutes,
             anomaly_count, status, consent_version, source, session_id, metadata)
        VALUES (%s, %s, %s, 'csv', 480, 0, 0, 0, 0, 'pending_approval',
                'uat-t921', %s, %s, %s::jsonb)
        RETURNING id
        """,
        (
            ids["attendance_timesheet_imports"],
            f"uat-{run_token}",
            digest,
            "uat_transaction_probe",
            run_token,
            metadata,
        ),
    )
    _insert_and_read(
        cursor,
        result,
        "usage_analytics_events",
        """
        INSERT INTO public.usage_analytics_events
            (id, event_name, event_surface, page_path, session_pseudonym,
             user_agent_family, metadata)
        VALUES (%s, 'form_success', 'internal_console', '/uat-transaction-probe',
                %s, 'synthetic', %s::jsonb)
        RETURNING id
        """,
        (ids["usage_analytics_events"], run_token, metadata),
    )

    mailbox_id = _insert_and_read(
        cursor,
        result,
        "sales_mailbox_sources",
        """
        INSERT INTO public.sales_mailbox_sources
            (id, source_key, display_name, source_type, retention_days, metadata)
        VALUES (%s, %s, 'Synthetic UAT source', 'api', 1, %s::jsonb)
        RETURNING id
        """,
        (ids["sales_mailbox_sources"], f"uat-{run_token}", metadata),
    )
    message_id = _insert_and_read(
        cursor,
        result,
        "sales_email_messages",
        """
        INSERT INTO public.sales_email_messages
            (id, mailbox_source_id, message_id_hash, dedupe_key, sender_hash,
             sender_domain, normalized_subject, body_hash, body_excerpt,
             source_type, ingest_status, metadata)
        VALUES (%s, %s, %s, %s, %s, 'example.invalid', %s, %s, %s, 'api',
                'parsed', %s::jsonb)
        RETURNING id
        """,
        (
            ids["sales_email_messages"],
            mailbox_id,
            digest,
            digest,
            sender_digest,
            "Synthetic UAT project",
            body_digest,
            "Synthetic content only",
            metadata,
        ),
    )
    _insert_and_read(
        cursor,
        result,
        "sales_email_entities",
        """
        INSERT INTO public.sales_email_entities
            (id, message_id, entity_type, label, normalized_label, confidence,
             metadata)
        VALUES (%s, %s, 'skill', 'Python', 'python', 1.0, %s::jsonb)
        RETURNING id
        """,
        (ids["sales_email_entities"], message_id, metadata),
    )
    requirement_id = _insert_and_read(
        cursor,
        result,
        "project_requirements",
        """
        INSERT INTO public.project_requirements
            (id, message_id, title, summary, required_skills, review_status,
             metadata)
        VALUES (%s, %s, %s, 'Synthetic UAT requirement', '["Python"]'::jsonb,
                'pending', %s::jsonb)
        RETURNING id
        """,
        (
            ids["project_requirements"],
            message_id,
            f"Synthetic UAT requirement {run_token}",
            metadata,
        ),
    )
    talent_id = _insert_and_read(
        cursor,
        result,
        "talent_profiles_from_email",
        """
        INSERT INTO public.talent_profiles_from_email
            (id, message_id, anonymized_talent_key, summary, skills,
             review_status, metadata)
        VALUES (%s, %s, %s, 'Synthetic UAT talent', '["Python"]'::jsonb,
                'pending', %s::jsonb)
        RETURNING id
        """,
        (
            ids["talent_profiles_from_email"],
            message_id,
            f"uat-{run_token}",
            metadata,
        ),
    )
    _insert_and_read(
        cursor,
        result,
        "requirement_skill_tags",
        """
        INSERT INTO public.requirement_skill_tags
            (id, project_requirement_id, talent_profile_id, skill_name,
             skill_category, importance, confidence, metadata)
        VALUES (%s, %s, %s, 'Python', 'backend', 'required', 1.0, %s::jsonb)
        RETURNING id
        """,
        (
            ids["requirement_skill_tags"],
            requirement_id,
            talent_id,
            metadata,
        ),
    )
    _insert_and_read(
        cursor,
        result,
        "email_parse_runs",
        """
        INSERT INTO public.email_parse_runs
            (id, mailbox_source_id, status, input_count, unique_count,
             duplicate_count, parsed_entity_count, model_name, fallback_used,
             metadata, completed_at)
        VALUES (%s, %s, 'succeeded', 1, 1, 0, 1, 'synthetic-uat', TRUE,
                %s::jsonb, now())
        RETURNING id
        """,
        (ids["email_parse_runs"], mailbox_id, metadata),
    )
    match_id = _insert_and_read(
        cursor,
        result,
        "email_match_results",
        """
        INSERT INTO public.email_match_results
            (id, project_requirement_id, talent_profile_id, direction,
             match_score, matched_skills, missing_skills, mismatch_reasons,
             evidence_summary, review_status, metadata)
        VALUES (%s, %s, %s, 'project_to_talent', 100.0, '["Python"]'::jsonb,
                '[]'::jsonb, '[]'::jsonb, 'Synthetic UAT match', 'pending',
                %s::jsonb)
        RETURNING id
        """,
        (
            ids["email_match_results"],
            requirement_id,
            talent_id,
            metadata,
        ),
    )
    _insert_and_read(
        cursor,
        result,
        "email_match_feedback",
        """
        INSERT INTO public.email_match_feedback
            (id, match_result_id, reviewer_id, feedback_status,
             corrected_score, corrected_notes, metadata)
        VALUES (%s, %s, %s, 'accepted', 100.0, 'Synthetic UAT review',
                %s::jsonb)
        RETURNING id
        """,
        (
            ids["email_match_feedback"],
            match_id,
            f"uat-{run_token}",
            metadata,
        ),
    )
    _insert_and_read(
        cursor,
        result,
        "feedback_events",
        """
        INSERT INTO public.feedback_events
            (id, rating, nps_score, comment, source, session_id, metadata)
        VALUES (%s, 'helpful', 10, 'Synthetic UAT feedback', %s, %s,
                %s::jsonb)
        RETURNING id
        """,
        (
            ids["feedback_events"],
            "uat_transaction_probe",
            run_token,
            metadata,
        ),
    )
    _insert_and_read(
        cursor,
        result,
        "support_requests",
        """
        INSERT INTO public.support_requests
            (id, category, priority, contact_email, subject, message, status,
             source, session_id, metadata)
        VALUES (%s, 'technical', 'normal', 'uat@example.invalid',
                'Synthetic UAT probe', 'Synthetic transactional write probe.',
                'new', %s, %s, %s::jsonb)
        RETURNING id
        """,
        (
            ids["support_requests"],
            "uat_transaction_probe",
            run_token,
            metadata,
        ),
    )


def _count_persisted_probes(cursor: Any, run_token: str) -> int:
    terms = [
        f"(SELECT count(*) FROM public.{table} "
        "WHERE metadata ->> 'uat_run_id' = %s)"
        for table in LIVE_UAT_TABLES
    ]
    cursor.execute("SELECT (" + " + ".join(terms) + ")", (run_token,) * len(terms))
    row = cursor.fetchone()
    return int(row[0]) if row else -1


def _default_connection_factory(db_url: str) -> Any:
    import psycopg2

    return psycopg2.connect(
        db_url,
        application_name="mighty-link-uat-write-verifier",
        connect_timeout=15,
        sslmode="require",
    )


def verify_uat_db_writes(
    db_url: str | None = None,
    *,
    execute: bool = False,
    connection_factory: ConnectionFactory | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Validate the offline contract or execute the live rollback-only probe."""
    if not execute:
        return _offline_schema_contract()

    result = _base_result("live_transactional_write")
    url = (db_url or os.getenv("SUPABASE_DB_URL") or "").strip()
    if not url:
        result["summary"] = (
            "SUPABASE_DB_URL is required for --execute; live verification "
            "fails closed when the secret is absent."
        )
        return result

    run_token = re.sub(r"[^a-zA-Z0-9_-]", "-", run_id or uuid.uuid4().hex)[:48]
    result["run_id"] = run_token
    factory = connection_factory or _default_connection_factory
    connection = None
    cursor = None
    try:
        connection = factory(url)
        result["has_db_connection"] = True
        cursor = connection.cursor()
        cursor.execute("SET LOCAL statement_timeout = '30s'")
        cursor.execute("SET LOCAL lock_timeout = '5s'")
        cursor.execute("SHOW server_version_num")
        version_row = cursor.fetchone()
        version_num = str(version_row[0]) if version_row else ""
        result["postgres_version_num"] = version_num
        if not version_num.startswith("17"):
            raise RuntimeError(
                f"unexpected PostgreSQL major version {version_num or 'unknown'}; expected 17"
            )

        _run_transactional_inserts(cursor, result, run_token)
        connection.rollback()
        result["transaction_rolled_back"] = True

        cursor.close()
        cursor = connection.cursor()
        persisted = _count_persisted_probes(cursor, run_token)
        result["persisted_probe_records"] = persisted
        connection.rollback()
        if persisted != 0:
            raise RuntimeError(
                f"rollback cleanup verification found {persisted} persisted probe records"
            )

        result["cleanup_verified"] = True
        result["live_write_verified"] = True
        result["status"] = "PASS"
        result["summary"] = (
            f"Live transactional INSERT/readback passed for "
            f"{len(LIVE_UAT_TABLES)} tables; ROLLBACK completed and 0 probe "
            "records persisted."
        )
    except Exception as error:
        if connection is not None:
            try:
                connection.rollback()
            except Exception:
                pass
        result["status"] = "FAIL"
        result["live_write_verified"] = False
        result["summary"] = "Live write verification failed: " + _redact_error(error, url)
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
    return result


def _write_report(result: dict[str, Any], prefix: str) -> tuple[Path, Path]:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = EXPORTS_DIR / f"{prefix}.json"
    md_path = EXPORTS_DIR / f"{prefix}.md"
    json_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Supabase UAT DB Write Verification (T845/T921)",
        "",
        f"- Status: **{result['status']}**",
        f"- Mode: `{result['mode']}`",
        f"- Live write verified: **{result['live_write_verified']}**",
        f"- Transaction rolled back: **{result['transaction_rolled_back']}**",
        f"- Cleanup verified: **{result['cleanup_verified']}**",
        f"- Persisted probe records: `{result['persisted_probe_records']}`",
        f"- Summary: {result['summary']}",
    ]
    actions_context = result.get("github_actions")
    if actions_context:
        lines.extend(
            [
                f"- GitHub Actions run: `{actions_context['run_id']}`",
                f"- Commit: `{actions_context['commit_sha']}`",
                f"- Run URL: {actions_context['run_url']}",
            ]
        )
    lines.extend(["", "## Tables", ""])
    for table, info in result["table_status"].items():
        verdict = "PASS" if info["verified"] else "FAIL"
        lines.append(f"- `{table}`: **{verdict}** (`{info['mode']}`)")
    lines.extend(
        [
            "",
            "All live probe values are synthetic. Live mode never commits probe rows.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify Supabase UAT writes (T845/T921)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run live transactional INSERT/readback/ROLLBACK verification",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON")
    args = parser.parse_args(argv)

    result = verify_uat_db_writes(execute=args.execute)
    prefix = "supabase_uat_writes_live" if args.execute else "supabase_uat_writes_audit"
    _write_report(result, prefix)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"[*] UAT DB write verification: {result['status']} - {result['summary']}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
