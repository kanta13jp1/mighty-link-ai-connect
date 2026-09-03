"""Sync sales email records from local SQLite data/mighty.db to production Supabase PostgreSQL (SUPABASE_DB_URL)."""

from __future__ import annotations

import os
import json
import re
import sqlite3
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qsl, unquote, urlsplit

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ConnectionFactory = Callable[[str], Any]

_SAFE_FAILURE_MESSAGE = (
    "[-] Supabase PostgreSQL sync failed. Database error details are "
    "intentionally suppressed."
)
_SUPABASE_POOLER_HOST_RE = re.compile(
    r"^[a-z0-9-]+\.pooler\.supabase\.com$", re.IGNORECASE
)
_CANONICAL_PASSWORD_RE = re.compile(r"(?:[A-Za-z0-9._~-]|%[0-9A-Fa-f]{2})+")


def _invalid_database_url() -> ValueError:
    return ValueError(
        "SUPABASE_DB_URL is invalid. Rotate the database password and copy a "
        "fresh Supavisor connection string with percent-encoded credentials."
    )


def validate_database_url(db_url: str) -> None:
    """Validate a canonical Supavisor URL without exposing credential parts."""
    try:
        parsed = urlsplit(db_url)
        port = parsed.port
        query = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
    except (TypeError, ValueError) as error:
        raise _invalid_database_url() from error

    if parsed.scheme.lower() not in {"postgres", "postgresql"}:
        raise _invalid_database_url()
    if parsed.fragment or parsed.path != "/postgres" or port not in {5432, 6543}:
        raise _invalid_database_url()

    raw_password = parsed.password
    if (
        not parsed.username
        or raw_password is None
        or not unquote(raw_password)
        or _CANONICAL_PASSWORD_RE.fullmatch(raw_password) is None
    ):
        raise _invalid_database_url()

    username = unquote(parsed.username)
    host = (parsed.hostname or "").lower()
    if _SUPABASE_POOLER_HOST_RE.fullmatch(host) is None:
        raise _invalid_database_url()
    if re.fullmatch(r"postgres\.[a-z0-9]+", username) is None:
        raise _invalid_database_url()
    if query != [("sslmode", "require")]:
        raise _invalid_database_url()

def load_env_file():
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                # Explicit process/job environment variables are authoritative.
                # The monitor materializes mailbox settings into .env; allowing
                # that file to replace SUPABASE_DB_URL can select a stale secret.
                os.environ.setdefault(k.strip(), v.strip().strip("\"'"))

def sync_tables(
    *,
    db_url: str | None = None,
    connection_factory: ConnectionFactory | None = None,
    sqlite_path: Path | None = None,
) -> None:
    load_env_file()
    db_url = (db_url or os.environ.get("SUPABASE_DB_URL") or "").strip()
    if not db_url:
        raise _invalid_database_url()

    # Validate before touching either database. Driver errors may echo parsed
    # credential fragments that GitHub's exact-value secret mask cannot hide.
    validate_database_url(db_url)
    connection_factory = connection_factory or psycopg2.connect

    sqlite_path = sqlite_path or PROJECT_ROOT / "data" / "mighty.db"
    if not sqlite_path.exists():
        raise RuntimeError("Local SQLite database is unavailable.")

    print("[*] Connecting to local SQLite database...")
    sq_conn = sqlite3.connect(sqlite_path)
    sq_conn.row_factory = sqlite3.Row
    sq_cur = sq_conn.cursor()

    print("[*] Connecting to Supabase PostgreSQL database...")
    pg_conn = connection_factory(db_url)
    pg_cur = pg_conn.cursor(cursor_factory=RealDictCursor)

    # 1. Sync sales_email_messages
    sq_cur.execute("SELECT * FROM sales_email_messages;")
    sq_messages = [dict(r) for r in sq_cur.fetchall()]
    print(f"[*] Found {len(sq_messages)} messages in local SQLite.")

    # Get existing dedupe_keys from Supabase PostgreSQL
    pg_cur.execute("SELECT dedupe_key, id FROM sales_email_messages;")
    pg_existing = {r["dedupe_key"]: r["id"] for r in pg_cur.fetchall()}
    print(f"[*] Found {len(pg_existing)} existing messages in Supabase PostgreSQL.")

    msg_id_map = {}  # sq_id -> pg_id
    inserted_msg_count = 0

    for msg in sq_messages:
        sq_id = msg["id"]
        key = msg["dedupe_key"]
        if key in pg_existing:
            msg_id_map[sq_id] = pg_existing[key]
            # Update status if parsed
            if msg["ingest_status"] == "parsed":
                pg_cur.execute(
                    "UPDATE sales_email_messages SET ingest_status = 'parsed' WHERE id = %s;",
                    (pg_existing[key],)
                )
            continue

        try:
            pg_cur.execute("""
                INSERT INTO sales_email_messages (
                    message_id_hash, dedupe_key, sender_hash, sender_domain,
                    normalized_subject, received_at, body_hash, body_excerpt,
                    source_path, source_type, raw_storage_policy, ingest_status, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                msg["message_id_hash"], msg["dedupe_key"], msg["sender_hash"], msg["sender_domain"],
                msg["normalized_subject"], msg["received_at"], msg["body_hash"], msg["body_excerpt"],
                msg["source_path"], msg["source_type"], msg["raw_storage_policy"], msg["ingest_status"],
                msg["metadata"]
            ))
            new_pg_id = pg_cur.fetchone()["id"]
            msg_id_map[sq_id] = new_pg_id
            pg_existing[key] = new_pg_id
            inserted_msg_count += 1
        except Exception as dup_err:
            pg_conn.rollback()
            pg_cur.execute("SELECT id FROM sales_email_messages WHERE dedupe_key = %s;", (key,))
            existing_row = pg_cur.fetchone()
            if existing_row:
                msg_id_map[sq_id] = existing_row["id"]
                pg_existing[key] = existing_row["id"]

    print(f"[+] Inserted {inserted_msg_count} new sales_email_messages into Supabase PostgreSQL.")

    # Reset sequences to prevent duplicate pkey errors
    try:
        pg_cur.execute("SELECT setval(pg_get_serial_sequence('sales_email_messages', 'id'), COALESCE((SELECT max(id) FROM sales_email_messages), 1));")
        pg_cur.execute("SELECT setval(pg_get_serial_sequence('project_requirements', 'id'), COALESCE((SELECT max(id) FROM project_requirements), 1));")
        pg_cur.execute("SELECT setval(pg_get_serial_sequence('talent_profiles_from_email', 'id'), COALESCE((SELECT max(id) FROM talent_profiles_from_email), 1));")
    except Exception as error:
        raise RuntimeError("Supabase sequence reset failed.") from error
    sq_cur.execute("SELECT * FROM project_requirements;")
    sq_projects = [dict(r) for r in sq_cur.fetchall()]
    pg_cur.execute("SELECT message_id FROM project_requirements;")
    pg_existing_proj_msg_ids = {r["message_id"] for r in pg_cur.fetchall()}

    inserted_proj_count = 0
    for proj in sq_projects:
        sq_msg_id = proj["message_id"]
        pg_msg_id = msg_id_map.get(sq_msg_id)
        if not pg_msg_id or pg_msg_id in pg_existing_proj_msg_ids:
            continue

        req_skills = proj["required_skills"]
        if isinstance(req_skills, str):
            try:
                req_skills = json.loads(req_skills)
            except json.JSONDecodeError as err:
                print(f"[WARN] Failed to parse required_skills for msg {sq_msg_id}: {err}")
                req_skills = []

        nice_skills = proj["nice_to_have_skills"]
        if isinstance(nice_skills, str):
            try:
                nice_skills = json.loads(nice_skills)
            except json.JSONDecodeError as err:
                print(f"[WARN] Failed to parse nice_to_have_skills for msg {sq_msg_id}: {err}")
                nice_skills = []

        categories = proj["skill_categories"]
        if isinstance(categories, str):
            try:
                categories = json.loads(categories)
            except json.JSONDecodeError as err:
                print(f"[WARN] Failed to parse skill_categories for msg {sq_msg_id}: {err}")
                categories = {}

        pg_cur.execute("""
            INSERT INTO project_requirements (
                message_id, title, client_or_partner, summary, required_skills,
                nice_to_have_skills, skill_categories, rate_min, rate_max, rate_unit,
                location, remote_type, start_date_text, duration_text, commercial_flow,
                restrictions, evidence_excerpt, review_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            pg_msg_id, proj["title"], proj["client_or_partner"], proj["summary"],
            json.dumps(req_skills, ensure_ascii=False),
            json.dumps(nice_skills, ensure_ascii=False),
            json.dumps(categories, ensure_ascii=False),
            proj["rate_min"], proj["rate_max"], proj["rate_unit"],
            proj["location"], proj["remote_type"], proj["start_date_text"],
            proj["duration_text"], proj["commercial_flow"], proj["restrictions"],
            proj["evidence_excerpt"], proj["review_status"]
        ))
        inserted_proj_count += 1
        pg_existing_proj_msg_ids.add(pg_msg_id)

    print(f"[+] Inserted {inserted_proj_count} project_requirements into Supabase PostgreSQL.")

    # 3. Sync talent_profiles_from_email
    sq_cur.execute("SELECT * FROM talent_profiles_from_email;")
    sq_talents = [dict(r) for r in sq_cur.fetchall()]
    pg_cur.execute("SELECT message_id FROM talent_profiles_from_email;")
    pg_existing_tal_msg_ids = {r["message_id"] for r in pg_cur.fetchall()}

    inserted_tal_count = 0
    for tal in sq_talents:
        sq_msg_id = tal["message_id"]
        pg_msg_id = msg_id_map.get(sq_msg_id)
        if not pg_msg_id or pg_msg_id in pg_existing_tal_msg_ids:
            continue

        skills = tal["skills"]
        if isinstance(skills, str):
            try:
                skills = json.loads(skills)
            except json.JSONDecodeError as err:
                print(f"[WARN] Failed to parse talent skills for msg {sq_msg_id}: {err}")
                skills = []

        categories = tal["skill_categories"]
        if isinstance(categories, str):
            try:
                categories = json.loads(categories)
            except json.JSONDecodeError as err:
                print(f"[WARN] Failed to parse talent skill_categories for msg {sq_msg_id}: {err}")
                categories = {}

        pg_cur.execute("""
            INSERT INTO talent_profiles_from_email (
                message_id, anonymized_talent_key, summary, skills, skill_categories,
                experience_years, desired_rate_min, desired_rate_max, desired_location,
                remote_preference, availability_text, evidence_excerpt, review_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            pg_msg_id, tal["anonymized_talent_key"], tal["summary"],
            json.dumps(skills, ensure_ascii=False),
            json.dumps(categories, ensure_ascii=False),
            tal["experience_years"], tal["desired_rate_min"], tal["desired_rate_max"],
            tal["desired_location"], tal["remote_preference"], tal["availability_text"],
            tal["evidence_excerpt"], tal["review_status"]
        ))
        inserted_tal_count += 1
        pg_existing_tal_msg_ids.add(pg_msg_id)

    print(f"[+] Inserted {inserted_tal_count} talent_profiles_from_email into Supabase PostgreSQL.")

    pg_conn.commit()
    pg_conn.close()
    sq_conn.close()
    print("[+] Supabase PostgreSQL sync complete.")


def main() -> int:
    try:
        sync_tables()
    except Exception:
        # Never print database/driver exception text. Parsers and drivers can
        # transform a secret and thereby bypass GitHub's full-value masking.
        print(_SAFE_FAILURE_MESSAGE, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
