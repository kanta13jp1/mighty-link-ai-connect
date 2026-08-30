#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI script to parse sales emails and register requirements/profiles (T817_4)."""

from __future__ import annotations

import os
import sys
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from supabase_client import get_supabase_client, is_supabase_configured  # noqa: E402
from sales_email_parser import SalesEmailParser, get_gemini_model_name  # noqa: E402


SQLITE_WRITE_COLUMNS = {
    "sales_email_messages": frozenset({"mailbox_source_id", "message_id_hash", "dedupe_key", "sender_hash", "sender_domain", "normalized_subject", "received_at", "body_hash", "body_excerpt", "source_path", "source_type", "raw_storage_policy", "ingest_status", "duplicate_of_id", "metadata"}),
    "project_requirements": frozenset({"message_id", "title", "client_or_partner", "summary", "required_skills", "nice_to_have_skills", "skill_categories", "rate_min", "rate_max", "rate_unit", "location", "remote_type", "start_date_text", "duration_text", "commercial_flow", "restrictions", "evidence_excerpt", "review_status", "metadata"}),
    "talent_profiles_from_email": frozenset({"message_id", "anonymized_talent_key", "summary", "skills", "skill_categories", "experience_years", "desired_rate_min", "desired_rate_max", "desired_location", "remote_preference", "availability_text", "evidence_excerpt", "review_status", "metadata"}),
    "requirement_skill_tags": frozenset({"project_requirement_id", "talent_profile_id", "skill_name", "skill_category", "importance", "confidence", "evidence_excerpt", "metadata"}),
    "sales_email_entities": frozenset({"message_id", "entity_type", "label", "normalized_label", "confidence", "evidence_excerpt", "metadata"}),
    "email_parse_runs": frozenset({"mailbox_source_id", "status", "input_count", "unique_count", "duplicate_count", "parsed_entity_count", "model_name", "fallback_used", "error_summary", "metadata", "started_at", "completed_at"}),
}


def _validated_sqlite_keys(table: str, payload: Dict[str, Any]) -> tuple[str, ...]:
    allowed = SQLITE_WRITE_COLUMNS.get(table)
    if allowed is None:
        raise ValueError(f"Unsupported SQLite write table: {table}")
    keys = tuple(payload)
    unexpected = sorted(set(keys) - allowed)
    if not keys or unexpected:
        raise ValueError(f"Invalid SQLite columns for {table}: {unexpected or 'empty payload'}")
    return keys


def get_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

class DBAdapter:
    """Helper to abstract Database operations for Supabase and SQLite."""
    def __init__(self, db_path: Path):
        self.use_supabase = is_supabase_configured()
        self.db_path = db_path
        self.sb_client = get_supabase_client() if self.use_supabase else None
        self.sqlite_conn = None
        if not self.use_supabase:
            self.sqlite_conn = sqlite3.connect(self.db_path)
            self.sqlite_conn.row_factory = sqlite3.Row

    def close(self):
        if self.sqlite_conn:
            self.sqlite_conn.close()

    def get_unparsed_messages(self, include_errors: bool = False) -> List[Dict[str, Any]]:
        """Get sales email messages with status 'new' or 'deduped', optionally including 'error'."""
        statuses = ["new", "deduped", "error"] if include_errors else ["new", "deduped"]
        if self.use_supabase:
            try:
                res = self.sb_client.table("sales_email_messages").select("*").in_("ingest_status", statuses).execute()
                return res.data if res else []
            except Exception as e:
                print(f"[-] Supabase get_unparsed_messages error: {e}")
                return []
        else:
            try:
                cursor = self.sqlite_conn.cursor()
                placeholders = ", ".join("?" for _ in statuses)
                cursor.execute(
                    f"SELECT * FROM sales_email_messages WHERE ingest_status IN ({placeholders})",  # nosec B608 -- only parameter placeholder count is dynamic.
                    statuses
                )
                return [dict(row) for row in cursor.fetchall()]
            except Exception as e:
                print(f"[-] SQLite get_unparsed_messages error: {e}")
                return []

    def update_message_status(self, msg_id: int, status: str) -> None:
        """Update message status to 'parsed' or 'error'."""
        if self.use_supabase:
            try:
                self.sb_client.table("sales_email_messages").update(
                    {"ingest_status": status, "updated_at": get_now_iso()}
                ).eq("id", msg_id).execute()
            except Exception as e:
                print(f"[-] Supabase update_message_status error: {e}")
        else:
            try:
                cursor = self.sqlite_conn.cursor()
                cursor.execute(
                    "UPDATE sales_email_messages SET ingest_status = ?, updated_at = ? WHERE id = ?",
                    (status, get_now_iso(), msg_id)
                )
                self.sqlite_conn.commit()
            except Exception as e:
                print(f"[-] SQLite update_message_status error: {e}")

    def insert_project_requirement(self, payload: Dict[str, Any]) -> int:
        """Insert project requirement and return its ID."""
        if self.use_supabase:
            try:
                res = self.sb_client.table("project_requirements").insert(payload).execute()
                return res.data[0]["id"] if res and res.data else 0
            except Exception as e:
                print(f"[-] Supabase insert_project_requirement error: {e}")
                return 0
        else:
            try:
                cursor = self.sqlite_conn.cursor()
                # Convert list/dict fields to JSON strings for SQLite
                db_payload = dict(payload)
                for key in ["required_skills", "nice_to_have_skills", "skill_categories", "metadata"]:
                    if key in db_payload and not isinstance(db_payload[key], str):
                        db_payload[key] = json.dumps(db_payload[key], ensure_ascii=False)

                keys = _validated_sqlite_keys("project_requirements", db_payload)
                placeholders = ", ".join("?" for _ in keys)
                columns = ", ".join(keys)
                query = f"INSERT INTO project_requirements ({columns}) VALUES ({placeholders})"  # nosec B608 -- columns are allowlisted.
                cursor.execute(query, list(db_payload.values()))
                self.sqlite_conn.commit()
                return cursor.lastrowid
            except Exception as e:
                print(f"[-] SQLite insert_project_requirement error: {e}")
                return 0

    def insert_talent_profile(self, payload: Dict[str, Any]) -> int:
        """Insert talent profile and return its ID."""
        if self.use_supabase:
            try:
                res = self.sb_client.table("talent_profiles_from_email").insert(payload).execute()
                return res.data[0]["id"] if res and res.data else 0
            except Exception as e:
                print(f"[-] Supabase insert_talent_profile error: {e}")
                return 0
        else:
            try:
                cursor = self.sqlite_conn.cursor()
                db_payload = dict(payload)
                for key in ["skills", "skill_categories", "metadata"]:
                    if key in db_payload and not isinstance(db_payload[key], str):
                        db_payload[key] = json.dumps(db_payload[key], ensure_ascii=False)

                keys = _validated_sqlite_keys("talent_profiles_from_email", db_payload)
                placeholders = ", ".join("?" for _ in keys)
                columns = ", ".join(keys)
                query = f"INSERT INTO talent_profiles_from_email ({columns}) VALUES ({placeholders})"  # nosec B608 -- columns are allowlisted.
                cursor.execute(query, list(db_payload.values()))
                self.sqlite_conn.commit()
                return cursor.lastrowid
            except Exception as e:
                print(f"[-] SQLite insert_talent_profile error: {e}")
                return 0

    def insert_skill_tag(self, payload: Dict[str, Any]) -> None:
        """Insert skill tag for project or talent."""
        if self.use_supabase:
            try:
                self.sb_client.table("requirement_skill_tags").insert(payload).execute()
            except Exception as e:
                print(f"[-] Supabase insert_skill_tag error: {e}")
        else:
            try:
                cursor = self.sqlite_conn.cursor()
                db_payload = dict(payload)
                if "metadata" in db_payload and not isinstance(db_payload["metadata"], str):
                    db_payload["metadata"] = json.dumps(db_payload["metadata"], ensure_ascii=False)

                keys = _validated_sqlite_keys("requirement_skill_tags", db_payload)
                placeholders = ", ".join("?" for _ in keys)
                columns = ", ".join(keys)
                query = f"INSERT INTO requirement_skill_tags ({columns}) VALUES ({placeholders})"  # nosec B608 -- columns are allowlisted.
                cursor.execute(query, list(db_payload.values()))
                self.sqlite_conn.commit()
            except Exception as e:
                print(f"[-] SQLite insert_skill_tag error: {e}")

    def insert_entity(self, payload: Dict[str, Any]) -> None:
        """Insert entity log for tracking extracted assets."""
        if self.use_supabase:
            try:
                self.sb_client.table("sales_email_entities").insert(payload).execute()
            except Exception as e:
                print(f"[-] Supabase insert_entity error: {e}")
        else:
            try:
                cursor = self.sqlite_conn.cursor()
                db_payload = dict(payload)
                if "metadata" in db_payload and not isinstance(db_payload["metadata"], str):
                    db_payload["metadata"] = json.dumps(db_payload["metadata"], ensure_ascii=False)

                keys = _validated_sqlite_keys("sales_email_entities", db_payload)
                placeholders = ", ".join("?" for _ in keys)
                columns = ", ".join(keys)
                query = f"INSERT INTO sales_email_entities ({columns}) VALUES ({placeholders})"  # nosec B608 -- columns are allowlisted.
                cursor.execute(query, list(db_payload.values()))
                self.sqlite_conn.commit()
            except Exception as e:
                print(f"[-] SQLite insert_entity error: {e}")

    def insert_parse_run(self, payload: Dict[str, Any]) -> int:
        """Insert start execution parse run log."""
        if self.use_supabase:
            try:
                res = self.sb_client.table("email_parse_runs").insert(payload).execute()
                return res.data[0]["id"] if res and res.data else 0
            except Exception as e:
                print(f"[-] Supabase insert_parse_run error: {e}")
                return 0
        else:
            try:
                cursor = self.sqlite_conn.cursor()
                db_payload = dict(payload)
                if "metadata" in db_payload and not isinstance(db_payload["metadata"], str):
                    db_payload["metadata"] = json.dumps(db_payload["metadata"], ensure_ascii=False)

                keys = _validated_sqlite_keys("email_parse_runs", db_payload)
                placeholders = ", ".join("?" for _ in keys)
                columns = ", ".join(keys)
                query = f"INSERT INTO email_parse_runs ({columns}) VALUES ({placeholders})"  # nosec B608 -- columns are allowlisted.
                cursor.execute(query, list(db_payload.values()))
                self.sqlite_conn.commit()
                return cursor.lastrowid
            except Exception as e:
                print(f"[-] SQLite insert_parse_run error: {e}")
                return 0

    def update_parse_run(self, run_id: int, payload: Dict[str, Any]) -> None:
        """Update parse run completion stats."""
        if self.use_supabase:
            try:
                self.sb_client.table("email_parse_runs").update(payload).eq("id", run_id).execute()
            except Exception as e:
                print(f"[-] Supabase update_parse_run error: {e}")
        else:
            try:
                cursor = self.sqlite_conn.cursor()
                db_payload = dict(payload)
                if "metadata" in db_payload and not isinstance(db_payload["metadata"], str):
                    db_payload["metadata"] = json.dumps(db_payload["metadata"], ensure_ascii=False)

                update_keys = _validated_sqlite_keys("email_parse_runs", db_payload)
                sets = ", ".join(f"{key} = ?" for key in update_keys)
                query = f"UPDATE email_parse_runs SET {sets} WHERE id = ?"  # nosec B608 -- columns are allowlisted.
                params = list(db_payload.values()) + [run_id]
                cursor.execute(query, params)
                self.sqlite_conn.commit()
            except Exception as e:
                print(f"[-] SQLite update_parse_run error: {e}")


DEFAULT_MAX_MESSAGES = 50


def resolve_parse_args(argv: list[str] | None = None) -> tuple[int, bool]:
    """Resolve max_messages and retry_errors flag from argv/env with CLI overrides (T817_4 / T910).

    Priority: --max-messages arg > SALES_EMAIL_PARSE_MAX_MESSAGES env > default 50.
    0 means unlimited (explicit operator opt-in only).
    """
    import argparse

    env_default = os.environ.get("SALES_EMAIL_PARSE_MAX_MESSAGES", "").strip()
    default = int(env_default) if env_default.isdigit() else DEFAULT_MAX_MESSAGES
    parser = argparse.ArgumentParser(description="Parse unparsed sales emails (T817_4)")
    parser.add_argument("--max-messages", type=int, default=default,
                        help=f"max messages per run (0=unlimited, default {DEFAULT_MAX_MESSAGES})")
    parser.add_argument("--retry-errors", action="store_true", default=False,
                        help="Include messages with ingest_status='error' for parsing retry")
    # parse_known_args so programmatic callers (tests import and call main()
    # directly, leaving pytest args in sys.argv) never crash on foreign args.
    args, _unknown = parser.parse_known_args(argv)
    return max(0, args.max_messages), args.retry_errors


def resolve_max_messages(argv: list[str] | None = None) -> int:
    max_msgs, _ = resolve_parse_args(argv)
    return max_msgs


def main(argv: list[str] | None = None, retry_errors: bool | None = None) -> int:
    max_messages, cli_retry_errors = resolve_parse_args(argv)
    do_retry_errors = retry_errors if retry_errors is not None else cli_retry_errors
    sqlite_path = PROJECT_ROOT / "data" / "mighty.db"
    db = DBAdapter(sqlite_path)

    print(f"[*] Starting AI matching parser (retry_errors={do_retry_errors}). Connection Mode: {'Supabase (service_role)' if db.use_supabase else 'SQLite Fallback'}")

    messages = db.get_unparsed_messages(include_errors=do_retry_errors)
    if not messages:
        print("[+] No new unparsed emails found. Exiting.")
        db.close()
        return 0

    if max_messages and len(messages) > max_messages:
        print(f"[!] {len(messages)} unparsed messages exceed the batch cap; processing first {max_messages} (rerun for the rest).")
        messages = messages[:max_messages]

    print(f"[*] Found {len(messages)} unparsed messages.")

    # Initialize parse run execution log
    run_id = db.insert_parse_run({
        "status": "running",
        "input_count": len(messages),
        "started_at": get_now_iso(),
        "model_name": get_gemini_model_name() if os.getenv("GEMINI_API_KEY") else "deterministic_fallback",
        "fallback_used": not bool(os.getenv("GEMINI_API_KEY"))
    })

    parser = SalesEmailParser()
    success_count = 0
    entity_count = 0

    for msg in messages:
        msg_id = msg.get("id")
        subject = msg.get("normalized_subject") or ""
        body = msg.get("body_excerpt") or ""

        out_enc = sys.stdout.encoding or "utf-8"
        safe_subject = subject[:30].encode(out_enc, errors="replace").decode(out_enc, errors="replace")
        print(f"  [*] Parsing message ID {msg_id}: '{safe_subject}...'")

        try:
            result = parser.parse(subject, body)
            category = result.category

            full_evidence = (body.strip() if body else result.evidence_excerpt) or result.evidence_excerpt

            if category == "project" and result.project:
                # Insert Project Requirements
                proj_payload = {
                    "message_id": msg_id,
                    "title": result.project.title,
                    "client_or_partner": result.project.client_or_partner,
                    "summary": result.project.summary,
                    "required_skills": result.project.required_skills,
                    "nice_to_have_skills": result.project.nice_to_have_skills,
                    "rate_min": result.project.rate_min,
                    "rate_max": result.project.rate_max,
                    "rate_unit": result.project.rate_unit,
                    "location": result.project.location,
                    "remote_type": result.project.remote_type,
                    "start_date_text": result.project.start_date_text,
                    "duration_text": result.project.duration_text,
                    "commercial_flow": result.project.commercial_flow,
                    "restrictions": result.project.restrictions,
                    "evidence_excerpt": full_evidence,
                    "review_status": "pending",
                }
                proj_id = db.insert_project_requirement(proj_payload)
                entity_count += 1

                # Insert Skill Tags
                for skill in result.project.required_skills:
                    db.insert_skill_tag({
                        "project_requirement_id": proj_id,
                        "skill_name": skill,
                        "importance": "required",
                        "confidence": result.confidence,
                        "evidence_excerpt": full_evidence
                    })
                    db.insert_entity({
                        "message_id": msg_id,
                        "entity_type": "skill",
                        "label": skill,
                        "normalized_label": skill.lower(),
                        "confidence": result.confidence,
                        "evidence_excerpt": full_evidence
                    })
                
                # Tag project title itself
                db.insert_entity({
                    "message_id": msg_id,
                    "entity_type": "project",
                    "label": result.project.title,
                    "normalized_label": result.project.title.lower(),
                    "confidence": result.confidence,
                    "evidence_excerpt": full_evidence
                })

            elif category == "talent" and result.talent:
                # Insert Talent Profile
                raw_talent_key = result.talent.anonymized_talent_key or "匿名技術者"
                unique_talent_key = f"{raw_talent_key}-ID{msg_id}"
                talent_payload = {
                    "message_id": msg_id,
                    "anonymized_talent_key": unique_talent_key,
                    "summary": result.talent.summary,
                    "skills": result.talent.skills,
                    "experience_years": result.talent.experience_years,
                    "desired_rate_min": result.talent.desired_rate_min,
                    "desired_rate_max": result.talent.desired_rate_max,
                    "desired_location": result.talent.desired_location,
                    "remote_preference": result.talent.remote_preference,
                    "availability_text": result.talent.availability_text,
                    "evidence_excerpt": full_evidence,
                    "review_status": "pending",
                }
                talent_id = db.insert_talent_profile(talent_payload)
                entity_count += 1

                # Insert Skill Tags
                for skill in result.talent.skills:
                    db.insert_skill_tag({
                        "talent_profile_id": talent_id,
                        "skill_name": skill,
                        "importance": "experience",
                        "confidence": result.confidence,
                        "evidence_excerpt": result.evidence_excerpt
                    })
                    db.insert_entity({
                        "message_id": msg_id,
                        "entity_type": "skill",
                        "label": skill,
                        "normalized_label": skill.lower(),
                        "confidence": result.confidence,
                        "evidence_excerpt": result.evidence_excerpt
                    })

                db.insert_entity({
                    "message_id": msg_id,
                    "entity_type": "talent",
                    "label": result.talent.anonymized_talent_key,
                    "normalized_label": result.talent.anonymized_talent_key.lower(),
                    "confidence": result.confidence,
                    "evidence_excerpt": result.evidence_excerpt
                })

            db.update_message_status(msg_id, "parsed")
            success_count += 1

        except Exception as e:
            print(f"  [!] Failed to parse message {msg_id}: {e}")
            db.update_message_status(msg_id, "error")

    # Update Parse Run Status
    status = "succeeded" if success_count == len(messages) else ("partial" if success_count > 0 else "failed")
    db.update_parse_run(run_id, {
        "status": status,
        "unique_count": success_count,
        "parsed_entity_count": entity_count,
        "completed_at": get_now_iso()
    })

    print(f"[+] Parse batch complete. Status: {status}, Parsed: {success_count}/{len(messages)}, Entities Added: {entity_count}")
    db.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
