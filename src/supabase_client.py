# -*- coding: utf-8 -*-
"""
Mighty Skill-Bridge: Supabase Client SDK Wrapper
Author: Antigravity 2.0 (AI Agent)

This module provides data access functions using the official Supabase Python Client SDK.
It reads SUPABASE_URL and SUPABASE_KEY (or SUPABASE_SERVICE_ROLE_KEY) from environment
variables to establish connection, with graceful fallbacks.
"""

import os
import json
from typing import Dict, List, Optional

try:
    from supabase import create_client, Client
    SUPABASE_SDK_AVAILABLE = True
except ImportError:
    SUPABASE_SDK_AVAILABLE = False
    Client = None

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    or os.environ.get("SUPABASE_KEY")
    or ""
).strip()

_client: Optional[Client] = None

def get_supabase_client() -> Optional[Client]:
    """Lazy initialization of the Supabase Client SDK instance."""
    global _client
    if not SUPABASE_SDK_AVAILABLE:
        return None
    if _client is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            _client = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("[+] Supabase Client SDK initialized successfully.")
        except Exception as e:
            print(f"[-] Failed to initialize Supabase Client SDK: {e}")
    return _client

def is_supabase_configured() -> bool:
    """Checks if Supabase SDK is available and environment credentials are set."""
    return SUPABASE_SDK_AVAILABLE and bool(SUPABASE_URL) and bool(SUPABASE_KEY)

# --- Data Access Helpers ---

def get_engineers() -> List[Dict]:
    """Fetch all engineers from Supabase 'engineers' table."""
    client = get_supabase_client()
    if not client:
        return []
    try:
        response = client.table("engineers").select("*").order("created_at", desc=True).execute()
        return response.data if response else []
    except Exception as e:
        print(f"[-] Supabase SDK error in get_engineers: {e}")
        return []

def get_engineer(engineer_id: int) -> Optional[Dict]:
    """Fetch an engineer by ID from Supabase 'engineers' table."""
    client = get_supabase_client()
    if not client:
        return None
    try:
        response = client.table("engineers").select("*").eq("id", engineer_id).execute()
        return response.data[0] if response and response.data else None
    except Exception as e:
        print(f"[-] Supabase SDK error in get_engineer: {e}")
        return None

def insert_engineer(name: str, resume_raw: str, parsed_skills: dict, career_goals: dict) -> int:
    """Inserts a new engineer and returns the generated ID."""
    client = get_supabase_client()
    if not client:
        return 0
    try:
        payload = {
            "name": name,
            "resume_raw": resume_raw,
            "parsed_skills": json.dumps(parsed_skills, ensure_ascii=False),
            "career_goals": json.dumps(career_goals, ensure_ascii=False),
        }
        response = client.table("engineers").insert(payload).execute()
        if response and response.data:
            return response.data[0].get("id", 0)
    except Exception as e:
        print(f"[-] Supabase SDK error in insert_engineer: {e}")
    return 0

def get_jobs() -> List[Dict]:
    """Fetch all jobs from Supabase 'jobs' table."""
    client = get_supabase_client()
    if not client:
        return []
    try:
        response = client.table("jobs").select("*").order("created_at", desc=True).execute()
        return response.data if response else []
    except Exception as e:
        print(f"[-] Supabase SDK error in get_jobs: {e}")
        return []

def get_job(job_id: int) -> Optional[Dict]:
    """Fetch a job by ID from Supabase 'jobs' table."""
    client = get_supabase_client()
    if not client:
        return None
    try:
        response = client.table("jobs").select("*").eq("id", job_id).execute()
        return response.data[0] if response and response.data else None
    except Exception as e:
        print(f"[-] Supabase SDK error in get_job: {e}")
        return None

def insert_job(title: str, company: str, job_description: str, parsed_requirements: dict, company_culture: dict) -> int:
    """Inserts a new job and returns the generated ID."""
    client = get_supabase_client()
    if not client:
        return 0
    try:
        payload = {
            "title": title,
            "company": company,
            "job_description": job_description,
            "parsed_requirements": json.dumps(parsed_requirements, ensure_ascii=False),
            "company_culture": json.dumps(company_culture, ensure_ascii=False),
        }
        response = client.table("jobs").insert(payload).execute()
        if response and response.data:
            return response.data[0].get("id", 0)
    except Exception as e:
        print(f"[-] Supabase SDK error in insert_job: {e}")
    return 0

def get_match_results() -> List[Dict]:
    """Fetch all match results from Supabase 'match_results' table."""
    client = get_supabase_client()
    if not client:
        return []
    try:
        response = client.table("match_results").select("*").order("analyzed_at", desc=True).execute()
        return response.data if response else []
    except Exception as e:
        print(f"[-] Supabase SDK error in get_match_results: {e}")
        return []

def insert_match_result(
    engineer_id: int,
    job_id: int,
    fit_ratio: float,
    score_skill: int,
    score_culture: int,
    score_growth: int,
    score_performing: int,
    match_summary: str,
    interview_questions: list
) -> int:
    """Inserts a new match result and returns the generated ID."""
    client = get_supabase_client()
    if not client:
        return 0
    try:
        payload = {
            "engineer_id": engineer_id,
            "job_id": job_id,
            "fit_ratio": fit_ratio,
            "score_skill": score_skill,
            "score_culture": score_culture,
            "score_growth": score_growth,
            "score_performing": score_performing,
            "match_summary": match_summary,
            "interview_questions": json.dumps(interview_questions, ensure_ascii=False),
        }
        response = client.table("match_results").insert(payload).execute()
        if response and response.data:
            return response.data[0].get("id", 0)
    except Exception as e:
        print(f"[-] Supabase SDK error in insert_match_result: {e}")
    return 0
