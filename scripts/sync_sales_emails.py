#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI script to sync sales emails over read-only IMAP and rebuild reports."""

from __future__ import annotations

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sales_email_imap import fetch_imap_emails
from sales_email_ingest import dedupe_key, normalize_subject, canonical_body, safe_excerpt, sender_domain, sha256_hex
from parse_sales_emails import DBAdapter, main as run_parser
from sales_email_extract import write_json_report, write_markdown_report
from sales_email_match import main as run_matcher


def check_duplicate_key(db: DBAdapter, key: str) -> bool:
    if db.use_supabase:
        try:
            res = db.sb_client.table("sales_email_messages").select("id").eq("dedupe_key", key).execute()
            return len(res.data) > 0 if res else False
        except Exception as e:
            print(f"[-] Supabase duplicate check error: {e}")
            return False
    else:
        try:
            cursor = db.sqlite_conn.cursor()
            cursor.execute("SELECT id FROM sales_email_messages WHERE dedupe_key = ?", (key,))
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"[-] SQLite duplicate check error: {e}")
            return False


def insert_sales_email_message(db: DBAdapter, payload: dict) -> int:
    if db.use_supabase:
        try:
            res = db.sb_client.table("sales_email_messages").insert(payload).execute()
            return res.data[0]["id"] if res and res.data else 0
        except Exception as e:
            print(f"[-] Supabase insert_message error: {e}")
            return 0
    else:
        try:
            cursor = db.sqlite_conn.cursor()
            keys = payload.keys()
            placeholders = ", ".join("?" for _ in keys)
            columns = ", ".join(keys)
            query = f"INSERT INTO sales_email_messages ({columns}) VALUES ({placeholders})"
            cursor.execute(query, list(payload.values()))
            db.sqlite_conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"[-] SQLite insert_message error: {e}")
            return 0


def sync_raw_email_list(db: DBAdapter, raw_emails: List[Any]) -> int:
    new_count = 0
    for email in raw_emails:
        key = dedupe_key(email)
        if check_duplicate_key(db, key):
            continue
        
        subj = normalize_subject(email.subject)
        body = canonical_body(email.body)
        body_exc = safe_excerpt(body, max_chars=240)
        
        original_received_at = None
        if email.received_at:
            try:
                from email.utils import parsedate_to_datetime
                parsed_dt = parsedate_to_datetime(email.received_at)
                original_received_at = parsed_dt.isoformat().replace("+00:00", "Z")
            except Exception:
                pass
        if not original_received_at:
            original_received_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        payload = {
            "message_id_hash": sha256_hex(email.message_id or f"mail-{key}"),
            "dedupe_key": key,
            "sender_hash": sha256_hex(email.sender),
            "sender_domain": sender_domain(email.sender),
            "normalized_subject": safe_excerpt(subj, max_chars=160),
            "received_at": original_received_at,
            "body_hash": sha256_hex(body),
            "body_excerpt": body_exc,
            "source_path": email.source_path,
            "source_type": "api",
            "raw_storage_policy": "hash_and_redacted_excerpt_only",
            "ingest_status": "new",
            "metadata": json.dumps({"sender_raw": email.sender}, ensure_ascii=False)
        }
        
        msg_id = insert_sales_email_message(db, payload)
        if msg_id:
            new_count += 1
            
    return new_count


def sync_imap_to_db(db: DBAdapter, max_messages: int | None = None) -> int:
    print(f"[*] Fetching emails via IMAP (max_messages={max_messages or 'default'})...")
    raw_emails = fetch_imap_emails(max_messages=max_messages)
    return sync_raw_email_list(db, raw_emails)


def rebuild_extraction_review_json(db: DBAdapter) -> None:
    print("[*] Rebuilding exports/sales_email_extraction_review.json from DB...")
    extractions = []
    
    if db.use_supabase:
        try:
            res_msg = db.sb_client.table("sales_email_messages").select("*").eq("ingest_status", "parsed").execute()
            messages = res_msg.data if res_msg else []
            
            res_proj = db.sb_client.table("project_requirements").select("*").execute()
            projects = {p["message_id"]: p for p in (res_proj.data if res_proj else [])}
            
            res_tal = db.sb_client.table("talent_profiles_from_email").select("*").execute()
            talents = {t["message_id"]: t for t in (res_tal.data if res_tal else [])}
        except Exception as e:
            print(f"[-] Supabase rebuild fetch error: {e}")
            return
    else:
        try:
            cursor = db.sqlite_conn.cursor()
            cursor.execute("SELECT * FROM sales_email_messages WHERE ingest_status = 'parsed'")
            messages = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM project_requirements")
            projects = {p["message_id"]: dict(p) for p in cursor.fetchall()}
            for pid, p in projects.items():
                for key in ["required_skills", "nice_to_have_skills", "skill_categories"]:
                    if isinstance(p.get(key), str):
                        p[key] = json.loads(p[key])
            
            cursor.execute("SELECT * FROM talent_profiles_from_email")
            talents = {t["message_id"]: dict(t) for t in cursor.fetchall()}
            for tid, t in talents.items():
                for key in ["skills", "skill_categories"]:
                    if isinstance(t.get(key), str):
                        t[key] = json.loads(t[key])
        except Exception as e:
            print(f"[-] SQLite rebuild fetch error: {e}")
            return

    project_count = 0
    talent_count = 0
    skill_tag_count = 0
    
    for msg in messages:
        msg_id = msg["id"]
        proj = projects.get(msg_id)
        tal = talents.get(msg_id)
        
        email_kind = "unknown"
        if proj:
            email_kind = "project"
            project_count += 1
            skill_tag_count += len(proj.get("required_skills", []))
            proj_data = {
                "title": proj["title"],
                "summary": proj["summary"],
                "required_skills": proj["required_skills"],
                "nice_to_have_skills": proj["nice_to_have_skills"],
                "skill_categories": proj.get("skill_categories", {}),
                "rate_min": proj["rate_min"],
                "rate_max": proj["rate_max"],
                "rate_unit": proj["rate_unit"],
                "location": proj["location"],
                "remote_type": proj["remote_type"],
                "start_date_text": proj["start_date_text"],
                "duration_text": proj["duration_text"],
                "commercial_flow": proj["commercial_flow"],
                "restrictions": proj["restrictions"],
                "evidence_excerpt": proj["evidence_excerpt"],
                "confidence": 1.0,
                "review_status": proj["review_status"]
            }
        else:
            proj_data = None
            
        if tal:
            email_kind = "talent"
            talent_count += 1
            skill_tag_count += len(tal.get("skills", []))
            tal_data = {
                "anonymized_talent_key": tal["anonymized_talent_key"],
                "summary": tal["summary"],
                "skills": tal["skills"],
                "skill_categories": tal.get("skill_categories", {}),
                "experience_years": tal["experience_years"],
                "desired_rate_min": tal["desired_rate_min"],
                "desired_rate_max": tal["desired_rate_max"],
                "desired_location": tal["desired_location"],
                "remote_preference": tal["remote_preference"],
                "availability_text": tal["availability_text"],
                "evidence_excerpt": tal["evidence_excerpt"],
                "confidence": 1.0,
                "review_status": tal["review_status"]
            }
        else:
            tal_data = None
            
        msg_received_at = "2026-06-18T00:00:00Z"
        if msg.get("received_at"):
            if isinstance(msg["received_at"], datetime):
                msg_received_at = msg["received_at"].isoformat().replace("+00:00", "Z")
            else:
                msg_received_at = str(msg["received_at"])
        elif msg.get("created_at"):
            if isinstance(msg["created_at"], datetime):
                msg_received_at = msg["created_at"].isoformat().replace("+00:00", "Z")
            else:
                msg_received_at = str(msg["created_at"])

        extractions.append({
            "source_path": msg["source_path"],
            "source_type": msg["source_type"],
            "dedupe_key": msg["dedupe_key"],
            "sender_domain": msg["sender_domain"],
            "normalized_subject": msg["normalized_subject"],
            "received_at": msg_received_at,
            "email_kind": email_kind,
            "model_name": "deterministic-sales-email-extractor-v1",
            "fallback_used": True,
            "project_requirement": proj_data,
            "talent_profile": tal_data
        })
        
    report = {
        "task_id": "T817_4",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "model_name": "deterministic-sales-email-extractor-v1",
        "fallback_used": True,
        "input_count": len(messages),
        "project_requirement_count": project_count,
        "talent_profile_count": talent_count,
        "skill_tag_count": skill_tag_count,
        "privacy_controls": [
            "raw_email_body_not_written",
            "email_phone_secret_patterns_redacted_from_evidence",
            "sender_hash_or_domain_only",
            "talent_identity_anonymized",
            "human_review_required_before_confirmed_status"
        ],
        "extractions": extractions
    }
    
    write_json_report(report, PROJECT_ROOT / "exports" / "sales_email_extraction_review.json")
    write_markdown_report(report, PROJECT_ROOT / "exports" / "sales_email_extraction_review.md")
    print("[+] exports/sales_email_extraction_review.json rebuilt successfully.")


def rebuild_match_review_json() -> None:
    print("[*] Rebuilding exports/sales_email_match_review.json...")
    try:
        input_path = str(PROJECT_ROOT / "exports" / "sales_email_extraction_review.json")
        output_json = str(PROJECT_ROOT / "exports" / "sales_email_match_review.json")
        run_matcher(["--input-report", input_path, "--json-report", output_json])
        print("[+] exports/sales_email_match_review.json rebuilt successfully.")
    except Exception as e:
        print(f"[-] Rebuild match review failed: {e}")


def sync_sales_emails_pipeline(max_messages: int | None = None, retry_errors: bool = False) -> Dict[str, Any]:
    sqlite_path = PROJECT_ROOT / "data" / "mighty.db"
    db = DBAdapter(sqlite_path)
    
    print(f"[*] Starting Sales Email Sync & Parse Pipeline (retry_errors={retry_errors}). Connection Mode: {'Supabase' if db.use_supabase else 'SQLite'}")
    
    # 1. Fetch via read-only IMAP. Shared mailboxes must never fall back to POP3.
    try:
        new_emails = sync_imap_to_db(db, max_messages=max_messages)
    except Exception:
        db.close()
        raise

    print(f"[+] Total new emails synced into DB: {new_emails}")
    
    # 2. AI Parse (if new emails exist, OR if there are any unparsed/retryable emails in the database)
    statuses = ["new", "deduped", "error"] if retry_errors else ["new", "deduped"]
    has_unparsed = False
    if db.use_supabase:
        try:
            res = db.sb_client.table("sales_email_messages").select("id").in_("ingest_status", statuses).limit(1).execute()
            has_unparsed = len(res.data) > 0 if res else False
        except Exception as e:
            print(f"[-] Supabase unparsed check failed: {e}")
    else:
        try:
            cursor = db.sqlite_conn.cursor()
            placeholders = ", ".join("?" for _ in statuses)
            cursor.execute(f"SELECT id FROM sales_email_messages WHERE ingest_status IN ({placeholders}) LIMIT 1", statuses)
            has_unparsed = cursor.fetchone() is not None
        except Exception as e:
            print(f"[-] SQLite unparsed check failed: {e}")

    if new_emails > 0 or has_unparsed:
        print(f"[*] Running AI parser on unparsed emails (new={new_emails}, has_unparsed={has_unparsed}, retry_errors={retry_errors})...")
        parser_args = ["--retry-errors", "--max-messages", "0"] if retry_errors else ["--max-messages", "0"]
        run_parser(parser_args)
    else:
        print("[*] No unparsed emails, skipping AI parser run.")
        
    # 3. Rebuild UI reports
    rebuild_extraction_review_json(db)
    rebuild_match_review_json()
    
    db.close()
    return {
        "status": "success",
        "new_emails_count": new_emails,
        "retry_errors": retry_errors
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sales Email Sync & Matching Pipeline (T910 1000-scale)")
    parser.add_argument("--max-messages", type=int, default=None, help="Maximum emails to fetch (default: env or 1000)")
    parser.add_argument("--retry-errors", action="store_true", default=False, help="Retry parsing messages with status 'error'")
    args = parser.parse_args()

    res = sync_sales_emails_pipeline(max_messages=args.max_messages, retry_errors=args.retry_errors)
    print(f"[+] Complete. Result: {res}")
