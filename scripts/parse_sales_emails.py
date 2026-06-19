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
from sales_email_parser import SalesEmailParser  # noqa: E402

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

    def get_unparsed_messages(self) -> List[Dict[str, Any]]:
        """Get sales email messages with status 'new' or 'deduped'."""
        if self.use_supabase:
            try:
                res = self.sb_client.table("sales_email_messages").select("*").in_("ingest_status", ["new", "deduped"]).execute()
                return res.data if res else []
            except Exception as e:
                print(f"[-] Supabase get_unparsed_messages error: {e}")
                return []
        else:
            try:
                cursor = self.sqlite_conn.cursor()
                cursor.execute(
                    "SELECT * FROM sales_email_messages WHERE ingest_status IN ('new', 'deduped')"
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

                keys = db_payload.keys()
                placeholders = ", ".join("?" for _ in keys)
                columns = ", ".join(keys)
                query = f"INSERT INTO project_requirements ({columns}) VALUES ({placeholders})"
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

                keys = db_payload.keys()
                placeholders = ", ".join("?" for _ in keys)
                columns = ", ".join(keys)
                query = f"INSERT INTO talent_profiles_from_email ({columns}) VALUES ({placeholders})"
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

                keys = db_payload.keys()
                placeholders = ", ".join("?" for _ in keys)
                columns = ", ".join(keys)
                query = f"INSERT INTO requirement_skill_tags ({columns}) VALUES ({placeholders})"
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

                keys = db_payload.keys()
                placeholders = ", ".join("?" for _ in keys)
                columns = ", ".join(keys)
                query = f"INSERT INTO sales_email_entities ({columns}) VALUES ({placeholders})"
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

                keys = db_payload.keys()
                placeholders = ", ".join("?" for _ in keys)
                columns = ", ".join(keys)
                query = f"INSERT INTO email_parse_runs ({columns}) VALUES ({placeholders})"
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

                sets = ", ".join(f"{key} = ?" for key in db_payload.keys())
                query = f"UPDATE email_parse_runs SET {sets} WHERE id = ?"
                params = list(db_payload.values()) + [run_id]
                cursor.execute(query, params)
                self.sqlite_conn.commit()
            except Exception as e:
                print(f"[-] SQLite update_parse_run error: {e}")


def main() -> int:
    sqlite_path = PROJECT_ROOT / "data" / "mighty.db"
    db = DBAdapter(sqlite_path)

    print(f"[*] Starting AI matching parser. Connection Mode: {'Supabase (service_role)' if db.use_supabase else 'SQLite Fallback'}")

    messages = db.get_unparsed_messages()
    if not messages:
        print("[+] No new unparsed emails found. Exiting.")
        db.close()
        return 0

    print(f"[*] Found {len(messages)} unparsed messages.")

    # Initialize parse run execution log
    run_id = db.insert_parse_run({
        "status": "running",
        "input_count": len(messages),
        "started_at": get_now_iso(),
        "model_name": "gemini-2.5-flash" if os.getenv("GEMINI_API_KEY") else "deterministic_fallback",
        "fallback_used": not bool(os.getenv("GEMINI_API_KEY"))
    })

    parser = SalesEmailParser()
    success_count = 0
    entity_count = 0

    for msg in messages:
        msg_id = msg.get("id")
        subject = msg.get("normalized_subject") or ""
        body = msg.get("body_excerpt") or ""

        print(f"  [*] Parsing message ID {msg_id}: '{subject[:30]}...'")

        try:
            result = parser.parse(subject, body)
            category = result.category

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
                    "evidence_excerpt": result.evidence_excerpt,
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
                
                # Tag project title itself
                db.insert_entity({
                    "message_id": msg_id,
                    "entity_type": "project",
                    "label": result.project.title,
                    "normalized_label": result.project.title.lower(),
                    "confidence": result.confidence,
                    "evidence_excerpt": result.evidence_excerpt
                })

            elif category == "talent" and result.talent:
                # Insert Talent Profile
                talent_payload = {
                    "message_id": msg_id,
                    "anonymized_talent_key": result.talent.anonymized_talent_key,
                    "summary": result.talent.summary,
                    "skills": result.talent.skills,
                    "experience_years": result.talent.experience_years,
                    "desired_rate_min": result.talent.desired_rate_min,
                    "desired_rate_max": result.talent.desired_rate_max,
                    "desired_location": result.talent.desired_location,
                    "remote_preference": result.talent.remote_preference,
                    "availability_text": result.talent.availability_text,
                    "evidence_excerpt": result.evidence_excerpt,
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
