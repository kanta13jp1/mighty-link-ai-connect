#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mighty Skill-Bridge: API & Web Server Component
Author: Antigravity 2.0 (AI Agent)

This FastAPI application provides:
1. Static hosting for index.html.
2. Dynamic Multimodal AI parsing of resumes & jobs (Gemini 1.5/2.5 Flash).
3. 4-Dimension AI Fit Evaluation.
4. Auto-syncing of matching results to Google Sheets (Mighty Match Logs) with visual decoration.
5. Quota-safe deterministic fallbacks when GEMINI_API_KEY is not configured, ensuring robust demo delivery.
"""

import os
import sys
import datetime
import json
import io
import re
import hashlib
import uuid
import requests
import subprocess
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Tuple


def env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default
    return max(minimum, min(value, maximum))


def env_flag(name: str, default: bool = False) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


# Set console encoding to UTF-8 to prevent encoding errors on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Try loading optional libraries for Sheets & Gemini
try:
    import gspread
    from google.oauth2.service_account import Credentials as ServiceCredentials
    from google.oauth2.credentials import Credentials as UserCredentials
    import google.auth.transport.requests
    from google_workspace_account import (
        GoogleWorkspaceAccountError,
        assert_expected_google_account,
        credentials_from_gspread_client,
    )
    SHEETS_LIB_AVAILABLE = True
except ImportError:
    SHEETS_LIB_AVAILABLE = False

try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_LIB_AVAILABLE = True
except ImportError:
    genai = None
    genai_types = None
    GEMINI_LIB_AVAILABLE = False

# Initialize FastAPI App
app = FastAPI(title="Mighty Skill-Bridge API Server")

# Dynamic Path Resolution (ensures app.py works robustly inside src/)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is src/
PROJECT_ROOT = os.path.dirname(ROOT_DIR)             # Project root
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
EXPORTS_DIR = os.path.join(PROJECT_ROOT, "exports")
AUDIT_DIR = os.path.join(DATA_DIR, "audit")
AUDIT_LOG_FILE = os.path.join(AUDIT_DIR, "ai_audit.jsonl")
EXTERNAL_API_USAGE_LOG_FILE = os.path.join(DATA_DIR, "external_api_usage.jsonl")
KNOWLEDGE_FLOW_DIR = os.path.join(EXPORTS_DIR, "knowledge_flow")
KNOWLEDGE_FLOW_MANIFEST = os.path.join(KNOWLEDGE_FLOW_DIR, "manifest.json")
KNOWLEDGE_FLOW_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "generate_knowledge_flow_demo.py")
FAVICON_FILE = os.path.join(PROJECT_ROOT, "favicon.ico")
CHROME_DEVTOOLS_WORKSPACE_PATH = "/.well-known/appspecific/com.chrome.devtools.json"
SEEDANCE_DEMO_DIR = os.path.join(EXPORTS_DIR, "seedance_demo")
SEEDANCE_DEMO_VIDEO = os.path.join(SEEDANCE_DEMO_DIR, "mighty_skill_bridge_seedance_demo.mp4")
SEEDANCE_DEMO_MANIFEST = os.path.join(SEEDANCE_DEMO_DIR, "manifest.json")
SEEDANCE_MODEL = os.environ.get("SEEDANCE_MODEL", "seedance-1-0-pro")
SEEDANCE_API_URL = os.environ.get("SEEDANCE_API_URL", "").strip()
SEEDANCE_RESULT_API_URL_TEMPLATE = os.environ.get("SEEDANCE_RESULT_API_URL_TEMPLATE", "").strip()
SEEDANCE_PAYLOAD_STYLE = os.environ.get("SEEDANCE_PAYLOAD_STYLE", "content_task").strip().lower()
SEEDANCE_POLL_TIMEOUT_SECONDS = env_int("SEEDANCE_POLL_TIMEOUT_SECONDS", 30, 0, 600)
SEEDANCE_POLL_INTERVAL_SECONDS = env_int("SEEDANCE_POLL_INTERVAL_SECONDS", 5, 1, 60)
SEEDANCE_API_ENABLED = env_flag("SEEDANCE_API_ENABLED", False)
SEEDANCE_DAILY_GENERATION_LIMIT = env_int("SEEDANCE_DAILY_GENERATION_LIMIT", 1, 0, 1000)
SEEDANCE_DAILY_REPORTED_TOKEN_LIMIT = env_int("SEEDANCE_DAILY_REPORTED_TOKEN_LIMIT", 0, 0, 1_000_000_000)
SEEDANCE_API_KEY = (
    os.environ.get("SEEDANCE_API_KEY")
    or os.environ.get("ARK_API_KEY")
    or os.environ.get("BYTEPLUS_API_KEY")
)

CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, "credentials.json")
CLIENT_SECRET_FILE = os.path.join(PROJECT_ROOT, "client_secret.json")
AUTHORIZED_USER_FILE = os.path.join(PROJECT_ROOT, "authorized_user.json")
SPREADSHEET_ID = "1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8"
USER_EMAIL = "k-umezawa@ml-mightylink.com"
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_DAILY_CALL_LIMIT = env_int("GEMINI_DAILY_CALL_LIMIT", 20, 0, 10000)
GEMINI_DAILY_REPORTED_TOKEN_LIMIT = env_int("GEMINI_DAILY_REPORTED_TOKEN_LIMIT", 100000, 0, 1_000_000_000)

os.makedirs(EXPORTS_DIR, exist_ok=True)
app.mount("/exports", StaticFiles(directory=EXPORTS_DIR), name="exports")


def deterministic_uuid4(seed: str) -> str:
    digest = bytearray(hashlib.sha256(seed.encode("utf-8")).digest()[:16])
    digest[6] = (digest[6] & 0x0F) | 0x40
    digest[8] = (digest[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(digest)))


DEVTOOLS_WORKSPACE_UUID = deterministic_uuid4(os.path.normcase(os.path.abspath(PROJECT_ROOT)))


# Mighty-Link Color Palette (Normalized for Sheets API)
COLORS = {
    "header_bg": {"red": 26/255, "green": 115/255, "blue": 232/255},   # #1A73E8 (Mighty Blue)
    "header_text": {"red": 1.0, "green": 1.0, "blue": 1.0},            # White
    "accent_green": {"red": 52/255, "green": 168/255, "blue": 83/255},  # #34A853 (Mighty Green)
    "row_even": {"red": 248/255, "green": 250/255, "blue": 252/255},    # Slate 50
    "border_gray": {"red": 226/255, "green": 232/255, "blue": 240/255}  # Slate 200
}

SKILL_TAXONOMY = {
    "backend": [
        "python", "fastapi", "django", "flask", "node.js", "node", "express",
        "rest api", "api", "graphql", "java", "spring", "go", "golang"
    ],
    "frontend": [
        "javascript", "typescript", "react", "react.js", "next.js", "vue",
        "html", "css", "tailwind", "chart.js", "ui", "ux"
    ],
    "ai": [
        "gemini", "openai", "llm", "rag", "prompt", "vertex ai", "生成ai",
        "ai", "マルチモーダル", "エージェント", "自律"
    ],
    "google_workspace": [
        "google sheets", "sheets api", "google drive", "drive api",
        "google calendar", "calendar api", "gspread", "oauth", "docs api",
        "workspace", "スプレッドシート", "カレンダー"
    ],
    "cloud": [
        "google cloud", "gcp", "aws", "azure", "cloud run", "docker",
        "github actions", "ci/cd", "vertex ai"
    ],
    "database": [
        "postgresql", "sqlite", "mysql", "sql", "pinecone", "vector db",
        "redis", "bigquery"
    ],
    "delivery": [
        "agile", "scrum", "アジャイル", "スクラム", "要件定義", "設計",
        "顧客折衝", "リード", "レビュー", "テスト", "運用"
    ],
}

ROLE_PATTERNS = [
    r"シニア[^\n、。]*",
    r"リード[^\n、。]*",
    r"フルスタック[^\n、。]*",
    r"ソリューションアーキテクト",
    r"バックエンド[^\n、。]*",
    r"フロントエンド[^\n、。]*",
    r"AI[^\n、。]*エンジニア",
]

SAMPLE_ENGINEER_TEXT = (
    "【氏名】佐藤 賢太 (さとう けんた)\n"
    "【職種】シニアAIソリューションアーキテクト / フルスタックエンジニア\n"
    "【概要】IT業界経験8年。クラウドネイティブなWebアプリケーション開発、"
    "Python、JavaScript(TypeScript)、FastAPI、React、Google Cloud API、"
    "OpenAI、Gemini、gspread を用いた自律エージェント開発をリード。\n"
    "【主要スキル】Python, JavaScript, TypeScript, FastAPI, Django, React.js, Next.js, "
    "Vertex AI, Gemini API, gspread, SQL\n"
    "【インフラ/データベース】AWS, Google Cloud, PostgreSQL, Pinecone (Vector DB)\n"
    "【キャリア志向】生成AIを活用したプロダクト開発でビジネス価値を創造すること。"
)

SAMPLE_JOB_TEXT = (
    "【案件名】大手ITソリューション企業：LLM自律エージェント＆データ連携基盤開発\n"
    "【業務内容】生成AI(Gemini, GPT)を活用した業務プロセスの自動化・自律化エージェントの実装、"
    "Google API (Sheets API, Docs API) と連携した文書作成自動同期システムの構築、"
    "FastAPI / React.js を用いたWebアプリケーションの設計・開発。\n"
    "【必須スキル】Python/TypeScript実務開発、REST API(FastAPI等)設計構築、React.js実装実績。\n"
    "【歓迎スキル】Gemini/OpenAI API等のLLM連携実績、Google Cloud API (gspread, Drive API) 等のOAuth認証による連携実績。"
)


@dataclass
class ParsedProfile:
    doc_type: str
    title: str
    role: str
    summary: str
    experience_years: int = 0
    skills_by_category: Dict[str, List[str]] = field(default_factory=dict)
    all_skills: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    raw_excerpt: str = ""


def clamp(value: float, min_value: int = 50, max_value: int = 100) -> int:
    return max(min_value, min(max_value, round(value)))


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def now_utc_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def stable_digest(value: str) -> str:
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()[:16]


def safe_excerpt(value: str, limit: int = 220) -> str:
    normalized = normalize_text(value)
    return normalized[:limit]


def ensure_audit_dir():
    os.makedirs(AUDIT_DIR, exist_ok=True)


def write_audit_event(event_type: str, payload: dict) -> dict:
    """Append a privacy-conscious local audit event for later AI tuning."""
    ensure_audit_dir()
    timestamp = now_utc_iso()
    event = {
        "event_id": stable_digest(f"{event_type}:{timestamp}:{json.dumps(payload, ensure_ascii=False, sort_keys=True)}"),
        "timestamp_utc": timestamp,
        "event_type": event_type,
        "payload": payload,
    }
    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def read_recent_audit_events(limit: int = 20) -> List[dict]:
    if not os.path.exists(AUDIT_LOG_FILE):
        return []
    limit = max(1, min(limit, 100))
    with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    events = []
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(events))


def today_key() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d")


def utc_now_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def read_external_api_events(limit: Optional[int] = None) -> List[dict]:
    if not os.path.exists(EXTERNAL_API_USAGE_LOG_FILE):
        return []
    with open(EXTERNAL_API_USAGE_LOG_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    if limit:
        lines = lines[-max(1, min(limit, 1000)):]
    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def append_external_api_event(event: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    safe_event = {
        "timestamp": utc_now_iso(),
        "day": today_key(),
        "provider": event.get("provider", "unknown"),
        "operation": event.get("operation", "unknown"),
        "billable": bool(event.get("billable", False)),
        "outcome": event.get("outcome", "unknown"),
        "model": event.get("model"),
        "task_id": event.get("task_id"),
        "http_status": event.get("http_status"),
        "reported_total_tokens": event.get("reported_total_tokens"),
        "reported_input_tokens": event.get("reported_input_tokens"),
        "reported_output_tokens": event.get("reported_output_tokens"),
        "token_source": event.get("token_source", "provider_not_reported"),
        "reason": event.get("reason"),
        "prompt_digest": event.get("prompt_digest"),
    }
    with open(EXTERNAL_API_USAGE_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(safe_event, ensure_ascii=False) + "\n")


def find_token_usage(value) -> dict:
    """Extract provider-reported usage tokens from common API response shapes."""
    usage = {
        "reported_total_tokens": None,
        "reported_input_tokens": None,
        "reported_output_tokens": None,
        "token_source": "provider_not_reported",
    }
    if value is None:
        return usage
    if not isinstance(value, (dict, list)):
        value = {
            "total_token_count": getattr(value, "total_token_count", None),
            "prompt_token_count": getattr(value, "prompt_token_count", None),
            "candidates_token_count": getattr(value, "candidates_token_count", None),
            "total_tokens": getattr(value, "total_tokens", None),
            "input_tokens": getattr(value, "input_tokens", None),
            "output_tokens": getattr(value, "output_tokens", None),
        }
    if isinstance(value, list):
        for item in value:
            found = find_token_usage(item)
            if found["reported_total_tokens"] is not None:
                return found
        return usage
    if isinstance(value, dict):
        candidates = []
        for key in ("usage", "usage_metadata", "token_usage", "billing", "data", "result"):
            if isinstance(value.get(key), dict):
                candidates.append(value[key])
        candidates.append(value)
        for candidate in candidates:
            total = (
                candidate.get("total_tokens")
                or candidate.get("total_token_count")
                or candidate.get("tokens")
                or candidate.get("total")
            )
            input_tokens = (
                candidate.get("input_tokens")
                or candidate.get("prompt_tokens")
                or candidate.get("prompt_token_count")
            )
            output_tokens = (
                candidate.get("output_tokens")
                or candidate.get("completion_tokens")
                or candidate.get("candidates_token_count")
            )
            if total is None and (input_tokens is not None or output_tokens is not None):
                total = int(input_tokens or 0) + int(output_tokens or 0)
            if total is not None:
                return {
                    "reported_total_tokens": int(total),
                    "reported_input_tokens": int(input_tokens) if input_tokens is not None else None,
                    "reported_output_tokens": int(output_tokens) if output_tokens is not None else None,
                    "token_source": "provider_response",
                }
        for item in value.values():
            found = find_token_usage(item)
            if found["reported_total_tokens"] is not None:
                return found
    return usage


def external_api_daily_stats(provider: str, operation: Optional[str] = None) -> dict:
    events = [
        event for event in read_external_api_events()
        if event.get("day") == today_key()
        and event.get("provider") == provider
        and (operation is None or event.get("operation") == operation)
    ]
    billable_events = [event for event in events if event.get("billable")]
    return {
        "events": len(events),
        "billable_calls": len(billable_events),
        "blocked_calls": sum(1 for event in events if event.get("outcome") == "blocked"),
        "reported_total_tokens": sum(int(event.get("reported_total_tokens") or 0) for event in events),
    }


def check_external_api_circuit(provider: str, operation: str, call_limit: int, token_limit: int = 0) -> Tuple[bool, str, dict]:
    stats = external_api_daily_stats(provider, operation)
    if call_limit <= 0:
        return False, f"{provider}:{operation} is disabled by daily call limit 0.", stats
    if stats["billable_calls"] >= call_limit:
        return False, f"{provider}:{operation} daily call limit reached ({stats['billable_calls']}/{call_limit}).", stats
    if token_limit > 0 and stats["reported_total_tokens"] >= token_limit:
        return False, f"{provider}:{operation} daily reported token limit reached ({stats['reported_total_tokens']}/{token_limit}).", stats
    return True, "allowed", stats


def build_external_api_usage_summary() -> dict:
    events = read_external_api_events()
    today = today_key()
    providers = {}
    for provider in ("seedance_api", "gemini_api"):
        provider_events = [event for event in events if event.get("provider") == provider]
        today_events = [event for event in provider_events if event.get("day") == today]
        providers[provider] = {
            "total_events": len(provider_events),
            "today_events": len(today_events),
            "today_billable_calls": sum(1 for event in today_events if event.get("billable")),
            "today_blocked_calls": sum(1 for event in today_events if event.get("outcome") == "blocked"),
            "today_reported_total_tokens": sum(int(event.get("reported_total_tokens") or 0) for event in today_events),
        }
    seedance_create_stats = external_api_daily_stats("seedance_api", "generation_create")
    gemini_parse_stats = external_api_daily_stats("gemini_api", "parse")
    gemini_match_stats = external_api_daily_stats("gemini_api", "match")
    return {
        "status": "success",
        "day": today,
        "usage_log": os.path.relpath(EXTERNAL_API_USAGE_LOG_FILE, PROJECT_ROOT),
        "providers": providers,
        "circuit_breakers": {
            "seedance_generation_create": {
                "enabled": SEEDANCE_API_ENABLED,
                "configured": SEEDANCE_CONFIGURED,
                "daily_call_limit": SEEDANCE_DAILY_GENERATION_LIMIT,
                "today_billable_calls": seedance_create_stats["billable_calls"],
                "today_reported_total_tokens": seedance_create_stats["reported_total_tokens"],
                "daily_reported_token_limit": SEEDANCE_DAILY_REPORTED_TOKEN_LIMIT or None,
                "state": "open" if (
                    not SEEDANCE_API_ENABLED
                    or seedance_create_stats["billable_calls"] >= SEEDANCE_DAILY_GENERATION_LIMIT
                    or (
                        SEEDANCE_DAILY_REPORTED_TOKEN_LIMIT > 0
                        and seedance_create_stats["reported_total_tokens"] >= SEEDANCE_DAILY_REPORTED_TOKEN_LIMIT
                    )
                ) else "closed",
            },
            "gemini_parse": {
                "enabled": GEMINI_READY,
                "daily_call_limit": GEMINI_DAILY_CALL_LIMIT,
                "today_billable_calls": gemini_parse_stats["billable_calls"],
                "today_reported_total_tokens": gemini_parse_stats["reported_total_tokens"],
            },
            "gemini_match": {
                "enabled": GEMINI_READY,
                "daily_call_limit": GEMINI_DAILY_CALL_LIMIT,
                "today_billable_calls": gemini_match_stats["billable_calls"],
                "today_reported_total_tokens": gemini_match_stats["reported_total_tokens"],
            },
        },
        "seedance_saved_default": read_seedance_manifest(),
        "recent_events": list(reversed(read_external_api_events(limit=100))),
        "usage_note": "Provider-reported token usage is shown when the API response includes it. Seedance video responses may not include tokens; use BytePlus Console > ModelArk > Usage as the spend source of truth.",
    }


def seedance_demo_video_url() -> Optional[str]:
    if os.path.exists(SEEDANCE_DEMO_VIDEO):
        return "/exports/seedance_demo/mighty_skill_bridge_seedance_demo.mp4"
    return None


def read_seedance_manifest() -> Optional[dict]:
    if not os.path.exists(SEEDANCE_DEMO_MANIFEST):
        return None
    with open(SEEDANCE_DEMO_MANIFEST, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def find_video_url(value):
    """Return the first plausible video URL from nested Seedance-like payloads."""
    if isinstance(value, str):
        lowered = value.lower()
        if lowered.startswith(("http://", "https://", "/exports/")) and any(
            marker in lowered for marker in (".mp4", ".webm", ".mov", "video", "output")
        ):
            return value
        return None
    if isinstance(value, list):
        for item in value:
            found = find_video_url(item)
            if found:
                return found
        return None
    if isinstance(value, dict):
        preferred_keys = (
            "video_url",
            "url",
            "output_url",
            "download_url",
            "content_url",
            "video",
            "videos",
            "output",
            "data",
            "result",
            "results",
            "assets",
        )
        for key in preferred_keys:
            if key in value:
                found = find_video_url(value[key])
                if found:
                    return found
        for item in value.values():
            found = find_video_url(item)
            if found:
                return found
    return None


def find_task_id(value) -> Optional[str]:
    if isinstance(value, dict):
        for key in ("task_id", "id", "request_id", "job_id"):
            if key in value and value[key]:
                return str(value[key])
        for item in value.values():
            found = find_task_id(item)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = find_task_id(item)
            if found:
                return found
    return None


def find_task_status(value) -> Optional[str]:
    if isinstance(value, dict):
        for key in ("status", "task_status", "TaskStatus", "state", "State", "phase"):
            if key in value and value[key] is not None and not isinstance(value[key], (dict, list)):
                return str(value[key])
        for item in value.values():
            found = find_task_status(item)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = find_task_status(item)
            if found:
                return found
    return None


def seedance_fallback_response(reason: str, prompt: str, task_id: Optional[str] = None) -> dict:
    video_url = seedance_demo_video_url()
    return {
        "status": "success",
        "mode": "fallback",
        "provider": "local_seedance_demo_asset",
        "model": SEEDANCE_MODEL,
        "video_url": video_url,
        "task_id": task_id,
        "fallback_reason": reason,
        "manifest": read_seedance_manifest(),
        "prompt_digest": stable_digest(prompt),
    }


def seedance_pending_response(reason: str, prompt: str, task_id: str, raw_status: Optional[str] = None) -> dict:
    return {
        "status": "success",
        "mode": "pending",
        "provider": "seedance_api",
        "model": SEEDANCE_MODEL,
        "video_url": seedance_demo_video_url(),
        "task_id": task_id,
        "task_status": raw_status or "running",
        "fallback_reason": reason,
        "manifest": read_seedance_manifest(),
        "prompt_digest": stable_digest(prompt),
    }


def summarize_seedance_http_error(response: requests.Response) -> str:
    """Expose enough provider error detail for setup debugging without logging credentials."""
    try:
        error_payload = response.json()
    except ValueError:
        error_payload = response.text
    if isinstance(error_payload, (dict, list)):
        detail = json.dumps(error_payload, ensure_ascii=False)
    else:
        detail = str(error_payload)
    detail = detail.replace(SEEDANCE_API_KEY or "", "[redacted]")
    if len(detail) > 1200:
        detail = detail[:1200] + "...[truncated]"
    return f"{response.status_code} {response.reason}: {detail}"


def build_seedance_payload(prompt: str, req: "SeedanceVideoRequest") -> dict:
    """Build a ModelArk Seedance task payload.

    ModelArk's current Seedance task API expects text input under `content`.
    Keep a `prompt_legacy` escape hatch because BytePlus has multiple media endpoints.
    """
    if SEEDANCE_PAYLOAD_STYLE == "prompt_legacy":
        return {
            "model": SEEDANCE_MODEL,
            "prompt": prompt,
            "aspect_ratio": req.aspect_ratio,
            "duration": req.duration_seconds,
        }
    return {
        "model": SEEDANCE_MODEL,
        "content": [
            {
                "type": "text",
                "text": prompt,
            }
        ],
        "ratio": req.aspect_ratio,
        "duration": req.duration_seconds,
        "generate_audio": False,
    }


def poll_seedance_result(task_id: str, headers: dict) -> Tuple[Optional[str], Optional[dict], str]:
    if not SEEDANCE_RESULT_API_URL_TEMPLATE:
        return (
            None,
            None,
            "Seedance task was accepted, but SEEDANCE_RESULT_API_URL_TEMPLATE is not configured for result polling.",
        )
    if SEEDANCE_POLL_TIMEOUT_SECONDS <= 0:
        return None, None, "Seedance task was accepted, but result polling is disabled."

    result_url = SEEDANCE_RESULT_API_URL_TEMPLATE.format(task_id=task_id)
    deadline = time.monotonic() + SEEDANCE_POLL_TIMEOUT_SECONDS
    attempts = 0
    last_status = "unknown"
    last_payload = None

    while True:
        attempts += 1
        response = requests.get(result_url, headers=headers, timeout=45)
        if not response.ok:
            append_external_api_event({
                "provider": "seedance_api",
                "operation": "task_poll",
                "billable": False,
                "outcome": "http_error",
                "model": SEEDANCE_MODEL,
                "task_id": task_id,
                "http_status": response.status_code,
                "reason": summarize_seedance_http_error(response),
            })
            return (
                None,
                last_payload,
                f"Seedance result request failed: {summarize_seedance_http_error(response)}",
            )

        result_payload = response.json()
        last_payload = result_payload
        usage = find_token_usage(result_payload)
        video_url = find_video_url(result_payload)
        if video_url:
            append_external_api_event({
                "provider": "seedance_api",
                "operation": "task_poll",
                "billable": False,
                "outcome": "live",
                "model": SEEDANCE_MODEL,
                "task_id": task_id,
                "http_status": response.status_code,
                **usage,
            })
            return video_url, result_payload, ""

        last_status = find_task_status(result_payload) or last_status
        append_external_api_event({
            "provider": "seedance_api",
            "operation": "task_poll",
            "billable": False,
            "outcome": "pending",
            "model": SEEDANCE_MODEL,
            "task_id": task_id,
            "http_status": response.status_code,
            "reason": f"task_status={last_status}",
            **usage,
        })
        if time.monotonic() >= deadline:
            break
        time.sleep(SEEDANCE_POLL_INTERVAL_SECONDS)

    return (
        None,
        last_payload,
        f"Seedance task was accepted but no video URL was returned within {SEEDANCE_POLL_TIMEOUT_SECONDS}s. "
        f"task_status={last_status}; attempts={attempts}",
    )


def profile_audit_payload(profile: ParsedProfile, ai_mode: str, fallback_reason: str, source_text: str, file_name: Optional[str] = None) -> dict:
    return {
        "ai_mode": ai_mode,
        "fallback_reason": fallback_reason,
        "doc_type": profile.doc_type,
        "title": profile.title,
        "role": profile.role,
        "experience_years": profile.experience_years,
        "all_skills": profile.all_skills,
        "strengths": profile.strengths,
        "risk_flags": profile.risk_flags,
        "source_digest": stable_digest(source_text),
        "source_length": len(source_text or ""),
        "source_excerpt": safe_excerpt(source_text),
        "file_name": file_name,
    }


def match_audit_payload(match_data: dict) -> dict:
    structured = match_data.get("structured", {})
    candidate = structured.get("candidate", {})
    job = structured.get("job", {})
    return {
        "ai_mode": match_data.get("ai_mode"),
        "fallback_reason": match_data.get("fallback_reason"),
        "final_score": match_data.get("final_score"),
        "scores": match_data.get("scores", {}),
        "candidate_title": candidate.get("title"),
        "job_title": job.get("title"),
        "candidate_role": candidate.get("role"),
        "job_role": job.get("role"),
        "matched_skills": structured.get("matched_skills", []),
        "missing_skills": structured.get("missing_skills", []),
        "summary_excerpt": safe_excerpt(match_data.get("summary", "")),
    }


def decode_uploaded_text(file_bytes: bytes) -> str:
    if not file_bytes:
        return ""
    for encoding in ("utf-8", "cp932", "shift_jis"):
        try:
            decoded = file_bytes.decode(encoding)
            if decoded.strip():
                return decoded
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="ignore")


def extract_labeled_value(text: str, labels: List[str]) -> str:
    for label in labels:
        pattern = rf"【{re.escape(label)}】\s*([^\n]+)"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ""


def extract_experience_years(text: str) -> int:
    candidates = []
    patterns = [
        r"([0-9]{1,2})\s*年以上",
        r"([0-9]{1,2})\s*年",
        r"([0-9]{1,2})\s*(?:years?|yrs?)\b",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            candidates.append(int(match.group(1)))
    return max(candidates) if candidates else 0


def detect_skills(text: str) -> Tuple[Dict[str, List[str]], List[str]]:
    lower_text = text.lower()
    skills_by_category = {}
    all_skills: Set[str] = set()
    for category, keywords in SKILL_TAXONOMY.items():
        detected = []
        for keyword in keywords:
            if keyword_matches(keyword, lower_text):
                detected.append(keyword)
                all_skills.add(keyword)
        skills_by_category[category] = sorted(set(detected), key=str.lower)
    return skills_by_category, sorted(all_skills, key=str.lower)


def keyword_matches(keyword: str, lower_text: str) -> bool:
    key = keyword.lower()
    if re.fullmatch(r"[a-z0-9.+#/-]+", key):
        return re.search(rf"(?<![a-z0-9]){re.escape(key)}(?![a-z0-9])", lower_text) is not None
    return key in lower_text


def detect_role(text: str, doc_type: str) -> str:
    labeled = extract_labeled_value(text, ["職種", "役割", "ポジション", "案件名"])
    if labeled:
        return labeled
    for pattern in ROLE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return "AIソリューションエンジニア" if doc_type == "engineer" else "AI / Google Workspace 連携案件"


def detect_title(text: str, doc_type: str) -> str:
    labels = ["氏名", "名前"] if doc_type == "engineer" else ["案件名", "求人名", "タイトル"]
    labeled = extract_labeled_value(text, labels)
    if labeled:
        return labeled
    return "候補者プロフィール" if doc_type == "engineer" else "対象案件"


def build_profile(text: str, doc_type: str) -> ParsedProfile:
    source = text.strip() or (SAMPLE_ENGINEER_TEXT if doc_type == "engineer" else SAMPLE_JOB_TEXT)
    skills_by_category, all_skills = detect_skills(source)
    role = detect_role(source, doc_type)
    title = detect_title(source, doc_type)
    years = extract_experience_years(source)
    normalized = normalize_text(source)

    category_strengths = [
        category for category, skills in skills_by_category.items() if len(skills) >= 2
    ]
    strengths = []
    if years:
        strengths.append(f"実務経験 {years} 年相当")
    strengths.extend([f"{category} 領域の実装経験" for category in category_strengths[:4]])
    if not strengths and all_skills:
        strengths.append(f"{', '.join(all_skills[:3])} を中心とした技術経験")

    risk_flags = []
    if doc_type == "engineer" and "google_workspace" not in category_strengths:
        risk_flags.append("Google Workspace API 連携経験の深掘り確認")
    if doc_type == "engineer" and "ai" not in category_strengths:
        risk_flags.append("LLM / 生成AI 連携経験の具体性確認")
    if doc_type == "job" and not all_skills:
        risk_flags.append("必須スキル要件が未構造化")

    return ParsedProfile(
        doc_type=doc_type,
        title=title,
        role=role,
        summary=normalized[:260],
        experience_years=years,
        skills_by_category=skills_by_category,
        all_skills=all_skills,
        strengths=strengths[:5],
        risk_flags=risk_flags[:4],
        raw_excerpt=normalized[:600],
    )


def format_profile(profile: ParsedProfile) -> str:
    label = "氏名" if profile.doc_type == "engineer" else "案件名"
    skill_lines = []
    for category, skills in profile.skills_by_category.items():
        if skills:
            skill_lines.append(f"- {category}: {', '.join(skills)}")
    strengths = "\n".join(f"- {item}" for item in profile.strengths) or "- 入力内容から詳細確認が必要"
    risks = "\n".join(f"- {item}" for item in profile.risk_flags) or "- 重大な未確認リスクなし"
    return (
        f"【{label}】{profile.title}\n"
        f"【役割】{profile.role}\n"
        f"【経験年数】{profile.experience_years or '未記載'}\n"
        f"【抽出スキル】\n{chr(10).join(skill_lines) if skill_lines else '- 未抽出'}\n"
        f"【強み】\n{strengths}\n"
        f"【確認ポイント】\n{risks}\n"
        f"【要約】{profile.summary}"
    )


def overlap_ratio(candidate_skills: List[str], job_skills: List[str]) -> float:
    if not job_skills:
        return 0.55
    candidate_set = {item.lower() for item in candidate_skills}
    job_set = {item.lower() for item in job_skills}
    return len(candidate_set & job_set) / max(len(job_set), 1)


def category_overlap(candidate: ParsedProfile, job: ParsedProfile, category: str) -> float:
    return overlap_ratio(
        candidate.skills_by_category.get(category, []),
        job.skills_by_category.get(category, []),
    )


def build_fallback_match(engineer_text: str, job_text: str, fallback_reason: str) -> dict:
    candidate = build_profile(engineer_text, "engineer")
    job = build_profile(job_text, "job")

    skill_ratio = overlap_ratio(candidate.all_skills, job.all_skills)
    ai_ratio = category_overlap(candidate, job, "ai")
    workspace_ratio = category_overlap(candidate, job, "google_workspace")
    backend_ratio = category_overlap(candidate, job, "backend")
    frontend_ratio = category_overlap(candidate, job, "frontend")
    delivery_ratio = category_overlap(candidate, job, "delivery")

    breadth_bonus = min(len(candidate.all_skills), 12) * 0.9
    skill_score = clamp(58 + (skill_ratio * 36) + breadth_bonus)
    culture_score = clamp(64 + (delivery_ratio * 22) + (8 if candidate.experience_years >= 5 else 0))
    growth_score = clamp(62 + (ai_ratio * 18) + (workspace_ratio * 12) + (backend_ratio * 5))
    performing_score = clamp(56 + (backend_ratio * 16) + (frontend_ratio * 10) + (workspace_ratio * 12) + min(candidate.experience_years, 10))
    final_score = clamp((skill_score * 0.36) + (culture_score * 0.18) + (growth_score * 0.24) + (performing_score * 0.22))

    matched_skills = sorted(
        {item for item in candidate.all_skills if item.lower() in {skill.lower() for skill in job.all_skills}},
        key=str.lower,
    )
    missing_skills = sorted(
        {item for item in job.all_skills if item.lower() not in {skill.lower() for skill in candidate.all_skills}},
        key=str.lower,
    )
    top_matches = ", ".join(matched_skills[:8]) or "要件に対する明示的な一致スキルは限定的"
    top_gaps = ", ".join(missing_skills[:6]) or "大きな未充足スキルは検出されていません"

    summary = (
        f"{candidate.title} と {job.title} の適合度は {final_score}% です。"
        f"主要一致スキルは {top_matches}。"
        f"特に backend / AI / Google Workspace 連携の重なりを中心に評価しました。"
        f"確認すべきギャップは {top_gaps}。"
        "Gemini live 復帰後は、この構造化プロファイルをそのままプロンプトへ渡すことで、"
        "より深い文脈評価に即時移行できます。"
    )

    qa = [
        {
            "question": f"{top_matches} を使った実装経験を、担当範囲・設計判断・成果指標に分けて説明してください。",
            "answer": "単なる利用経験ではなく、要件定義、API設計、認証、例外処理、運用時の監視までを一連の流れとして説明します。",
            "tip": "Google API や OAuth、バッチ更新、クォータ回避など、本プロジェクトで求められる実務上の判断を具体例に落とし込むと強いです。"
        },
        {
            "question": f"現時点で不足候補として見えている {top_gaps} を、着任後どの順番でキャッチアップしますか？",
            "answer": "初週で既存仕様と認証フローを把握し、2週目で小さな検証実装、3週目で本番相当のエラーハンドリングとログ設計へ広げる計画を示します。",
            "tip": "不足を隠さず、検証単位・成果物・レビュー方法まで言語化すると信頼感が増します。"
        },
        {
            "question": "生成AIを外部業務システムへ組み込む際、どのように品質と安全性を担保しますか？",
            "answer": "構造化入出力、fallback、監査ログ、権限分離、手動確認ポイントを設計に含め、AI応答をそのまま業務データへ反映しない方針を説明します。",
            "tip": "AI live と deterministic fallback の二層構造を説明できると、今回の開発方針とよく噛み合います。"
        }
    ]

    return {
        "final_score": final_score,
        "scores": {
            "skill": skill_score,
            "culture": culture_score,
            "growth": growth_score,
            "performing": performing_score,
        },
        "summary": summary,
        "qa": qa,
        "roadmap_week1": f"{job.role} の業務範囲、OAuth / Google API 認証、既存 FastAPI 構成を把握し、{top_gaps} の検証観点を洗い出す",
        "roadmap_week2": "構造化パーサー、スキル分類、4軸スコアリングの小さな改善を行い、Sheets への診断ログ保存までを通す",
        "roadmap_week3": "Gemini live 復帰を想定し、プロンプト入力に渡す structured_profile / gap_analysis / scoring_context を安定化する",
        "roadmap_week4": "Browser Agent による主要シナリオ確認、エラー時 fallback、監査ログ、共有手順を整備して社長報告用デモ品質まで高める",
        "ai_mode": "deterministic_fallback",
        "fallback_reason": fallback_reason,
        "structured": {
            "candidate": asdict(candidate),
            "job": asdict(job),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
        }
    }

# Dynamic Environment Diagnostics
API_KEY = os.environ.get("GEMINI_API_KEY")
AI_FORCE_MOCK = os.environ.get("AI_FORCE_MOCK", "").lower() in {"1", "true", "yes", "on"}
GEMINI_READY = API_KEY is not None and GEMINI_LIB_AVAILABLE and not AI_FORCE_MOCK
GEMINI_CLIENT = None

if GEMINI_READY:
    GEMINI_CLIENT = genai.Client(api_key=API_KEY)
    print(f"[+] Gemini API successfully configured via GEMINI_API_KEY using {GEMINI_MODEL}.")
elif AI_FORCE_MOCK:
    print("[!] AI_FORCE_MOCK enabled. Running in quota-safe mock fallback mode.")
elif not GEMINI_LIB_AVAILABLE:
    print("[!] google-genai is not installed. Running in deterministic fallback mode.")
else:
    print("[*] GEMINI_API_KEY not set. Running in deterministic fallback mode.")


def generate_gemini_content(contents, response_mime_type: Optional[str] = None):
    if GEMINI_CLIENT is None:
        raise RuntimeError("Gemini client is not configured.")
    config = None
    if response_mime_type:
        config = genai_types.GenerateContentConfig(response_mime_type=response_mime_type)
    return GEMINI_CLIENT.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=config,
    )


SEEDANCE_CONFIGURED = bool(SEEDANCE_API_KEY and SEEDANCE_API_URL)
SEEDANCE_READY = bool(SEEDANCE_API_ENABLED and SEEDANCE_CONFIGURED)
if SEEDANCE_READY:
    print("[+] Seedance API adapter enabled via environment variables.")
elif SEEDANCE_CONFIGURED:
    print("[*] Seedance API credentials detected, but external calls are disabled. Set SEEDANCE_API_ENABLED=1 to enable billing calls.")
else:
    print("[!] Seedance API credentials not set. Using local demo video fallback.")


class SeedanceVideoRequest(BaseModel):
    prompt: str
    aspect_ratio: str = "16:9"
    duration_seconds: int = 6

# Static Hosting route
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serves the project favicon for browser tabs and DevTools requests."""
    if not os.path.exists(FAVICON_FILE):
        raise HTTPException(status_code=404, detail="favicon.ico not found in project root.")
    return FileResponse(FAVICON_FILE, media_type="image/x-icon")


@app.get(CHROME_DEVTOOLS_WORKSPACE_PATH, include_in_schema=False)
async def chrome_devtools_workspace():
    """Lets Chrome DevTools connect this localhost app to the workspace without a 404."""
    return JSONResponse({
        "workspace": {
            "root": os.path.abspath(PROJECT_ROOT),
            "uuid": DEVTOOLS_WORKSPACE_UUID,
        }
    })


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serves the main frontend page index.html."""
    try:
        index_path = os.path.join(ROOT_DIR, "index.html")
        if not os.path.exists(index_path):
            raise FileNotFoundError()
        
        content = None
        # 1. Try reading as strict UTF-8
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()
            print("[+] Successfully loaded index.html in strict UTF-8.")
        except UnicodeDecodeError:
            # 2. Try reading as UTF-8, replacing illegal bytes instead of falling back to CP932
            # Since index.html is written in UTF-8, falling back to CP932 causes full text corruption.
            try:
                with open(index_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                print("[!] Loaded index.html in UTF-8 with errors='replace'.")
            except Exception as e:
                # 3. Last resort fallback to CP932
                print(f"[-] UTF-8 fallback failed: {e}. Trying CP932...")
                with open(index_path, "r", encoding="cp932", errors="ignore") as f:
                    content = f.read()
                    
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found in project workspace.")

# API Health Check Endpoint
@app.get("/api/health")
async def health_check():
    """Provides client-side dynamic connection check."""
    return {
        "status": "healthy",
        "sheets_live": SHEETS_LIB_AVAILABLE and (os.path.exists(CREDENTIALS_FILE) or os.path.exists(CLIENT_SECRET_FILE)),
        "gemini_live": GEMINI_READY,
        "ai_mode": "gemini_live" if GEMINI_READY else "deterministic_fallback",
        "ai_force_mock": AI_FORCE_MOCK,
        "seedance_live": SEEDANCE_READY,
        "seedance_api_enabled": SEEDANCE_API_ENABLED,
        "seedance_credentials_configured": SEEDANCE_CONFIGURED,
        "seedance_model": SEEDANCE_MODEL,
        "seedance_result_polling": bool(SEEDANCE_RESULT_API_URL_TEMPLATE),
        "seedance_poll_timeout_seconds": SEEDANCE_POLL_TIMEOUT_SECONDS,
        "seedance_demo_video": seedance_demo_video_url(),
    }


@app.get("/api/audit/recent")
async def recent_audit_events(limit: int = 20):
    """Returns recent local AI audit events without raw document bodies."""
    return {
        "status": "success",
        "audit_log": os.path.relpath(AUDIT_LOG_FILE, PROJECT_ROOT),
        "events": read_recent_audit_events(limit)
    }


ADMIN_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mighty Skill-Bridge API Guard</title>
    <link rel="icon" href="/favicon.ico" sizes="any">
    <style>
        :root { color-scheme: dark; --bg:#070807; --panel:#111312; --line:#2a2f2b; --text:#f3f5ef; --muted:#a6ada4; --ok:#9df56d; --warn:#ffd166; --bad:#ff7d7d; --blue:#8bdcff; }
        * { box-sizing: border-box; }
        body { margin:0; font-family: "Segoe UI", "Noto Sans JP", sans-serif; background: var(--bg); color: var(--text); }
        header { display:flex; justify-content:space-between; align-items:center; gap:16px; padding:18px 24px; border-bottom:1px solid var(--line); background:#050605; position:sticky; top:0; }
        main { max-width:1180px; margin:0 auto; padding:24px; display:grid; gap:18px; }
        h1 { margin:0; font-size:22px; }
        h2 { margin:0 0 12px; font-size:16px; color:var(--muted); font-weight:700; }
        .grid { display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap:14px; }
        .card { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; }
        .metric { font-size:32px; font-weight:800; line-height:1; }
        .label { color:var(--muted); font-size:13px; margin-top:8px; }
        .state { display:inline-flex; align-items:center; padding:5px 10px; border:1px solid var(--line); border-radius:999px; font-size:13px; color:var(--muted); }
        .closed { color:var(--ok); border-color:rgba(157,245,109,.35); }
        .open { color:var(--bad); border-color:rgba(255,125,125,.35); }
        table { width:100%; border-collapse:collapse; font-size:13px; }
        th, td { text-align:left; padding:9px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
        th { color:var(--muted); font-weight:600; }
        code { color:var(--blue); }
        a { color:var(--blue); text-decoration:none; }
        .muted { color:var(--muted); }
        .toolbar { display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
        button, .button { border:1px solid var(--line); border-radius:7px; padding:9px 12px; background:#191c1a; color:var(--text); cursor:pointer; font-weight:700; }
        button:hover, .button:hover { border-color:var(--blue); }
        @media (max-width: 860px) { .grid { grid-template-columns:1fr; } header { align-items:flex-start; flex-direction:column; } }
    </style>
</head>
<body>
    <header>
        <div>
            <h1>External API Guard</h1>
            <div class="muted">Mighty Skill-Bridge local billing safety dashboard</div>
        </div>
        <div class="toolbar">
            <a class="button" href="/">Demo</a>
            <a class="button" href="/api/admin/usage/export">Export JSONL</a>
            <button onclick="loadUsage()">Refresh</button>
        </div>
    </header>
    <main>
        <section class="grid" id="cards"></section>
        <section class="card">
            <h2>Circuit Breakers</h2>
            <div id="breakers"></div>
        </section>
        <section class="card">
            <h2>Saved Seedance Video</h2>
            <div id="saved-video" class="muted"></div>
        </section>
        <section class="card">
            <h2>Antigravity 2.0 Managed Agents Cost Simulator (T688 監視体制)</h2>
            <div class="muted" style="margin-bottom:12px;">Google Vertex AI Agent Builderの公式料金モデルに基づき、正式採用時の月額コストを動的にシミュレーションします。</div>
            <div style="display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:18px; margin-bottom:14px;">
                <div>
                    <label style="display:block; font-size:12px; color:var(--muted); margin-bottom:4px;">月間稼働時間 (Active vCPU Hours)</label>
                    <input type="number" id="sim-hours" value="20" style="width:100%; border:1px solid var(--line); border-radius:5px; padding:6px; background:#191c1a; color:var(--text);" oninput="updateSim()">
                </div>
                <div>
                    <label style="display:block; font-size:12px; color:var(--muted); margin-bottom:4px;">想定月間会話セッション数</label>
                    <input type="number" id="sim-sessions" value="10000" style="width:100%; border:1px solid var(--line); border-radius:5px; padding:6px; background:#191c1a; color:var(--text);" oninput="updateSim()">
                </div>
                <div>
                    <label style="display:block; font-size:12px; color:var(--muted); margin-bottom:4px;">想定RAGクエリ数 (Vertex AI Search)</label>
                    <input type="number" id="sim-queries" value="5000" style="width:100%; border:1px solid var(--line); border-radius:5px; padding:6px; background:#191c1a; color:var(--text);" oninput="updateSim()">
                </div>
                <div>
                    <label style="display:block; font-size:12px; color:var(--muted); margin-bottom:4px;">Gemini 入力/出力トークン量 (百万 tokens)</label>
                    <div style="display:flex; gap:6px;">
                        <input type="number" id="sim-input-tokens" value="10" style="width:50%; border:1px solid var(--line); border-radius:5px; padding:6px; background:#191c1a; color:var(--text);" oninput="updateSim()" placeholder="入力 (M)">
                        <input type="number" id="sim-output-tokens" value="2" style="width:50%; border:1px solid var(--line); border-radius:5px; padding:6px; background:#191c1a; color:var(--text);" oninput="updateSim()" placeholder="出力 (M)">
                    </div>
                </div>
            </div>
            <div style="display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap:12px; border-top:1px solid var(--line); padding-top:14px;">
                <div>
                    <div id="sim-total" class="metric" style="color:var(--blue); font-size:28px;">$0.00</div>
                    <div class="label">想定月額合計コスト (USD)</div>
                </div>
                <div>
                    <div id="sim-budget-status" class="state" style="margin-top:6px; font-weight:700;">-</div>
                    <div class="label">予算アラート監視状態 (しきい値 $100.00)</div>
                </div>
                <div>
                    <div style="font-size:13px; color:var(--muted);">
                        • vCPU: 2個 / メモリ: 8GB 固定<br>
                        • 予算監視サーキット: 有効 (GCP Billing Alert)<br>
                        • Express Mode 評価: 90日間 (課金制限)
                    </div>
                </div>
            </div>
            <div id="sim-breakdown" style="font-size:12px; margin-top:14px; color:var(--muted); background:#0c0d0c; border:1px solid var(--line); border-radius:5px; padding:10px; display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:8px;">
            </div>
        </section>
        <section class="card">
            <h2>Recent Events</h2>
            <div class="muted" style="margin-bottom:10px;">Prompts and API keys are not stored. Signed video URLs are not stored in this ledger.</div>
            <table>
                <thead><tr><th>Time</th><th>Provider</th><th>Operation</th><th>Outcome</th><th>Billable</th><th>Tokens</th><th>Task</th><th>Reason</th></tr></thead>
                <tbody id="events"></tbody>
            </table>
        </section>
        <section class="card muted" id="note"></section>
    </main>
    <script>
        const fmt = (value) => value === null || value === undefined ? "-" : value;
        function stateClass(value) { return value === "closed" ? "closed" : "open"; }
        async function loadUsage() {
            const response = await fetch("/api/admin/usage");
            const data = await response.json();
            const seedance = data.providers.seedance_api;
            const gemini = data.providers.gemini_api;
            document.getElementById("cards").innerHTML = `
                <div class="card"><div class="metric">${seedance.today_billable_calls}</div><div class="label">Seedance billable calls today</div></div>
                <div class="card"><div class="metric">${gemini.today_billable_calls}</div><div class="label">Gemini billable calls today</div></div>
                <div class="card"><div class="metric">${seedance.today_reported_total_tokens + gemini.today_reported_total_tokens}</div><div class="label">Provider-reported tokens today</div></div>
            `;
            const breakerRows = Object.entries(data.circuit_breakers).map(([name, breaker]) => `
                <tr>
                    <td><code>${name}</code></td>
                    <td><span class="state ${stateClass(breaker.state || (breaker.enabled ? "closed" : "open"))}">${breaker.state || (breaker.enabled ? "enabled" : "disabled")}</span></td>
                    <td>${fmt(breaker.today_billable_calls)} / ${fmt(breaker.daily_call_limit)}</td>
                    <td>${fmt(breaker.today_reported_total_tokens)} / ${fmt(breaker.daily_reported_token_limit)}</td>
                </tr>
            `).join("");
            document.getElementById("breakers").innerHTML = `<table><thead><tr><th>Name</th><th>State</th><th>Calls</th><th>Reported tokens</th></tr></thead><tbody>${breakerRows}</tbody></table>`;
            const saved = data.seedance_saved_default || {};
            document.getElementById("saved-video").innerHTML = `
                <div>Provider: <code>${fmt(saved.provider)}</code></div>
                <div>Model: <code>${fmt(saved.model)}</code></div>
                <div>Task: <code>${fmt(saved.task_id)}</code></div>
                <div>Video: <a href="/${fmt(saved.video)}" download>${fmt(saved.video)}</a></div>
                <div>Backup: <code>${fmt(saved.backup_video)}</code></div>
            `;
            document.getElementById("events").innerHTML = data.recent_events.map((event) => `
                <tr>
                    <td>${fmt(event.timestamp)}</td>
                    <td>${fmt(event.provider)}</td>
                    <td>${fmt(event.operation)}</td>
                    <td>${fmt(event.outcome)}</td>
                    <td>${event.billable ? "yes" : "no"}</td>
                    <td>${fmt(event.reported_total_tokens)}</td>
                    <td><code>${fmt(event.task_id)}</code></td>
                    <td>${fmt(event.reason)}</td>
                </tr>
            `).join("") || `<tr><td colspan="8" class="muted">No local usage events yet.</td></tr>`;
            document.getElementById("note").textContent = data.usage_note;
            updateSim();
        }
        async function updateSim() {
            const hours = document.getElementById("sim-hours").value || 0;
            const sessions = document.getElementById("sim-sessions").value || 0;
            const queries = document.getElementById("sim-queries").value || 0;
            const input = document.getElementById("sim-input-tokens").value || 0;
            const output = document.getElementById("sim-output-tokens").value || 0;
            
            const response = await fetch(`/api/admin/managed-agents/cost-simulation?hours=${hours}&sessions=${sessions}&queries=${queries}&input_tokens_million=${input}&output_tokens_million=${output}`);
            const data = await response.json();
            
            document.getElementById("sim-total").textContent = `$${data.total_cost.toFixed(2)}`;
            
            const statusEl = document.getElementById("sim-budget-status");
            statusEl.textContent = data.monitoring.budget_state.toUpperCase();
            statusEl.className = "state " + (data.monitoring.budget_state === "healthy" ? "closed" : "open");
            
            const bd = data.breakdown;
            document.getElementById("sim-breakdown").innerHTML = `
                <div>• vCPU コンピュート費: $${bd.vcpu_cost.toFixed(2)}</div>
                <div>• メモリ (8GB) リソース費: $${bd.memory_cost.toFixed(2)}</div>
                <div>• セッション履歴維持費 (1k): $${bd.session_cost.toFixed(2)}</div>
                <div>• RAG 検索 (Vertex AI Search) 費: $${bd.search_cost.toFixed(2)}</div>
                <div>• Gemini 入力トークン費: $${bd.gemini_input_cost.toFixed(2)}</div>
                <div>• Gemini 出力トークン費: $${bd.gemini_output_cost.toFixed(2)}</div>
            `;
        }
        loadUsage();
    </script>
</body>
</html>"""


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    """Local-only external API usage and circuit-breaker dashboard."""
    return HTMLResponse(content=ADMIN_DASHBOARD_HTML)


@app.get("/api/admin/usage")
async def admin_usage():
    return build_external_api_usage_summary()


@app.get("/admin/usage")
async def admin_usage_alias():
    """Human-friendly alias for users who type /admin/usage in the browser."""
    return build_external_api_usage_summary()


@app.get("/api/admin/usage/export", response_class=PlainTextResponse)
async def admin_usage_export():
    if not os.path.exists(EXTERNAL_API_USAGE_LOG_FILE):
        return PlainTextResponse("", media_type="application/jsonl")
    with open(EXTERNAL_API_USAGE_LOG_FILE, "r", encoding="utf-8") as f:
        return PlainTextResponse(f.read(), media_type="application/jsonl")


@app.get("/api/admin/managed-agents/cost-simulation")
async def managed_agents_cost_simulation(
    hours: float = 20.0,
    sessions: int = 10000,
    queries: int = 5000,
    input_tokens_million: float = 10.0,
    output_tokens_million: float = 2.0
):
    """
    Managed Agents (Vertex AI Agent Builder) cost estimation simulator.
    Provides detailed monthly costs based on standard Google Cloud billing dimensions.
    """
    VCPU_PRICE_PER_HOUR = 0.0864
    MEMORY_PRICE_PER_GB_HOUR = 0.0090
    SESSION_PRICE_PER_1K = 0.25
    SEARCH_PRICE_PER_1K = 4.00
    GEMINI_INPUT_PER_1M = 1.25
    GEMINI_OUTPUT_PER_1M = 3.75
    
    vcpu_hours = 2 * hours
    memory_gb_hours = 8 * hours
    
    vcpu_cost = vcpu_hours * VCPU_PRICE_PER_HOUR
    memory_cost = memory_gb_hours * MEMORY_PRICE_PER_GB_HOUR
    session_cost = (sessions / 1000) * SESSION_PRICE_PER_1K
    search_cost = (queries / 1000) * SEARCH_PRICE_PER_1K
    gemini_input_cost = input_tokens_million * GEMINI_INPUT_PER_1M
    gemini_output_cost = output_tokens_million * GEMINI_OUTPUT_PER_1M
    
    total_cost = vcpu_cost + memory_cost + session_cost + search_cost + gemini_input_cost + gemini_output_cost
    
    daily_budget = 5.00
    monthly_budget = 100.00
    
    budget_state = "healthy"
    if total_cost > monthly_budget:
        budget_state = "exceeded"
    elif total_cost > (monthly_budget * 0.8):
        budget_state = "warning"
        
    return {
        "status": "success",
        "parameters": {
            "monthly_hours": hours,
            "monthly_sessions": sessions,
            "monthly_queries": queries,
            "input_tokens_million": input_tokens_million,
            "output_tokens_million": output_tokens_million,
            "vcpu_count": 2,
            "memory_gb": 8
        },
        "breakdown": {
            "vcpu_cost": round(vcpu_cost, 2),
            "memory_cost": round(memory_cost, 2),
            "session_cost": round(session_cost, 2),
            "search_cost": round(search_cost, 2),
            "gemini_input_cost": round(gemini_input_cost, 2),
            "gemini_output_cost": round(gemini_output_cost, 2),
        },
        "total_cost": round(total_cost, 2),
        "currency": "USD",
        "monitoring": {
            "budget_state": budget_state,
            "daily_limit_usd": daily_budget,
            "monthly_limit_usd": monthly_budget,
            "gcp_billing_alerts_enabled": True
        }
    }


def read_knowledge_flow_manifest() -> Optional[dict]:
    if not os.path.exists(KNOWLEDGE_FLOW_MANIFEST):
        return None
    with open(KNOWLEDGE_FLOW_MANIFEST, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/knowledge-flow/status")
async def knowledge_flow_status():
    """Returns current generated NotebookLM/Slack/Notion/Obsidian demo artifacts."""
    manifest = read_knowledge_flow_manifest()
    return {
        "status": "ready" if manifest else "not_generated",
        "output_dir": os.path.relpath(KNOWLEDGE_FLOW_DIR, PROJECT_ROOT),
        "manifest": manifest,
    }


@app.post("/api/knowledge-flow/generate")
async def generate_knowledge_flow_artifacts():
    """Generates safe, CEO-facing knowledge-flow demo artifacts locally."""
    if not os.path.exists(KNOWLEDGE_FLOW_SCRIPT):
        raise HTTPException(status_code=404, detail="Knowledge flow generator script not found.")

    result = subprocess.run(
        [sys.executable, KNOWLEDGE_FLOW_SCRIPT],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Knowledge flow artifact generation failed.",
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
        )

    manifest = read_knowledge_flow_manifest()
    return {
        "status": "success",
        "message": "NotebookLM / Slack / Notion / Obsidian demo artifacts generated.",
        "stdout": result.stdout,
        "manifest": manifest,
    }


@app.post("/api/seedance/video-demo")
async def generate_seedance_video(req: SeedanceVideoRequest):
    """Create a Seedance video when credentials are set, otherwise return a safe local preview."""
    prompt = normalize_text(req.prompt)
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required.")

    if not seedance_demo_video_url():
        return {
            "status": "error",
            "mode": "missing_fallback_asset",
            "provider": "local_seedance_demo_asset",
            "message": "Run scripts/generate_seedance_demo_video.py before launching the demo.",
        }

    if not SEEDANCE_READY:
        reason = "Seedance API billing calls are disabled by default. Set SEEDANCE_API_ENABLED=1 before starting FastAPI to generate a new video."
        if not SEEDANCE_CONFIGURED:
            reason = "SEEDANCE_API_KEY and SEEDANCE_API_URL are not configured."
        append_external_api_event({
            "provider": "seedance_api",
            "operation": "generation_create",
            "billable": False,
            "outcome": "blocked",
            "model": SEEDANCE_MODEL,
            "reason": reason,
            "prompt_digest": stable_digest(prompt),
        })
        return seedance_fallback_response(
            reason,
            prompt,
        )

    allowed, circuit_reason, _stats = check_external_api_circuit(
        "seedance_api",
        "generation_create",
        SEEDANCE_DAILY_GENERATION_LIMIT,
        SEEDANCE_DAILY_REPORTED_TOKEN_LIMIT,
    )
    if not allowed:
        append_external_api_event({
            "provider": "seedance_api",
            "operation": "generation_create",
            "billable": False,
            "outcome": "blocked",
            "model": SEEDANCE_MODEL,
            "reason": circuit_reason,
            "prompt_digest": stable_digest(prompt),
        })
        return seedance_fallback_response(circuit_reason, prompt)

    headers = {
        "Authorization": f"Bearer {SEEDANCE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = build_seedance_payload(prompt, req)

    try:
        create_response = requests.post(
            SEEDANCE_API_URL,
            headers=headers,
            json=payload,
            timeout=45,
        )
        if not create_response.ok:
            append_external_api_event({
                "provider": "seedance_api",
                "operation": "generation_create",
                "billable": True,
                "outcome": "http_error",
                "model": SEEDANCE_MODEL,
                "http_status": create_response.status_code,
                "reason": summarize_seedance_http_error(create_response),
                "prompt_digest": stable_digest(prompt),
            })
            return seedance_fallback_response(
                f"Seedance API request failed: {summarize_seedance_http_error(create_response)}",
                prompt,
            )
        create_payload = create_response.json()
        usage = find_token_usage(create_payload)
        video_url = find_video_url(create_payload)
        task_id = find_task_id(create_payload)

        if video_url:
            append_external_api_event({
                "provider": "seedance_api",
                "operation": "generation_create",
                "billable": True,
                "outcome": "live",
                "model": SEEDANCE_MODEL,
                "task_id": task_id,
                "http_status": create_response.status_code,
                "prompt_digest": stable_digest(prompt),
                **usage,
            })
            return {
                "status": "success",
                "mode": "live",
                "provider": "seedance_api",
                "model": SEEDANCE_MODEL,
                "video_url": video_url,
                "task_id": task_id,
                "raw_status": create_payload.get("status") if isinstance(create_payload, dict) else None,
            }

        if task_id:
            append_external_api_event({
                "provider": "seedance_api",
                "operation": "generation_create",
                "billable": True,
                "outcome": "task_created",
                "model": SEEDANCE_MODEL,
                "task_id": task_id,
                "http_status": create_response.status_code,
                "prompt_digest": stable_digest(prompt),
                **usage,
            })
            video_url, result_payload, poll_reason = poll_seedance_result(task_id, headers)
            if video_url:
                return {
                    "status": "success",
                    "mode": "live",
                    "provider": "seedance_api",
                    "model": SEEDANCE_MODEL,
                    "video_url": video_url,
                    "task_id": task_id,
                    "raw_status": result_payload.get("status") if isinstance(result_payload, dict) else None,
                }
            return seedance_pending_response(
                poll_reason,
                prompt,
                task_id,
                find_task_status(result_payload),
            )

        return seedance_fallback_response(
            "Seedance task was accepted but no video URL was returned yet.",
            prompt,
            task_id,
        )
    except requests.RequestException as exc:
        append_external_api_event({
            "provider": "seedance_api",
            "operation": "generation_create",
            "billable": False,
            "outcome": "request_exception",
            "model": SEEDANCE_MODEL,
            "reason": str(exc),
            "prompt_digest": stable_digest(prompt),
        })
        return seedance_fallback_response(f"Seedance API request failed: {exc}", prompt)
    except ValueError as exc:
        return seedance_fallback_response(f"Seedance API returned non-JSON response: {exc}", prompt)


@app.get("/api/seedance/video-task/{task_id}")
async def get_seedance_video_task(task_id: str):
    """Check an existing Seedance task once so the browser can continue polling."""
    if not SEEDANCE_READY:
        reason = "Seedance API billing calls are disabled by default. Set SEEDANCE_API_ENABLED=1 before starting FastAPI to poll a remote task."
        if not SEEDANCE_CONFIGURED:
            reason = "SEEDANCE_API_KEY and SEEDANCE_API_URL are not configured."
        append_external_api_event({
            "provider": "seedance_api",
            "operation": "task_poll",
            "billable": False,
            "outcome": "blocked",
            "model": SEEDANCE_MODEL,
            "task_id": task_id,
            "reason": reason,
        })
        return seedance_fallback_response(
            reason,
            task_id,
            task_id,
        )
    if not SEEDANCE_RESULT_API_URL_TEMPLATE:
        return seedance_pending_response(
            "SEEDANCE_RESULT_API_URL_TEMPLATE is not configured for result polling.",
            task_id,
            task_id,
            "unknown",
        )

    headers = {
        "Authorization": f"Bearer {SEEDANCE_API_KEY}",
        "Content-Type": "application/json",
    }
    result_url = SEEDANCE_RESULT_API_URL_TEMPLATE.format(task_id=task_id)
    try:
        result_response = requests.get(result_url, headers=headers, timeout=45)
        if not result_response.ok:
            append_external_api_event({
                "provider": "seedance_api",
                "operation": "task_poll",
                "billable": False,
                "outcome": "http_error",
                "model": SEEDANCE_MODEL,
                "task_id": task_id,
                "http_status": result_response.status_code,
                "reason": summarize_seedance_http_error(result_response),
            })
            return seedance_fallback_response(
                f"Seedance result request failed: {summarize_seedance_http_error(result_response)}",
                task_id,
                task_id,
            )
        result_payload = result_response.json()
        usage = find_token_usage(result_payload)
        video_url = find_video_url(result_payload)
        task_status = find_task_status(result_payload)
        if video_url:
            append_external_api_event({
                "provider": "seedance_api",
                "operation": "task_poll",
                "billable": False,
                "outcome": "live",
                "model": SEEDANCE_MODEL,
                "task_id": task_id,
                "http_status": result_response.status_code,
                **usage,
            })
            return {
                "status": "success",
                "mode": "live",
                "provider": "seedance_api",
                "model": SEEDANCE_MODEL,
                "video_url": video_url,
                "task_id": task_id,
                "task_status": task_status,
            }
        append_external_api_event({
            "provider": "seedance_api",
            "operation": "task_poll",
            "billable": False,
            "outcome": "pending",
            "model": SEEDANCE_MODEL,
            "task_id": task_id,
            "http_status": result_response.status_code,
            "reason": f"task_status={task_status or 'unknown'}",
            **usage,
        })
        return seedance_pending_response(
            "Seedance task is still running.",
            task_id,
            task_id,
            task_status,
        )
    except requests.RequestException as exc:
        return seedance_fallback_response(f"Seedance result request failed: {exc}", task_id, task_id)
    except ValueError as exc:
        return seedance_fallback_response(f"Seedance result returned non-JSON response: {exc}", task_id, task_id)


# 1. API: Multi-modal Resume/Job Parser
@app.post("/api/parse")
async def parse_document(
    file: UploadFile = File(None),
    text: str = Form(None),
    doc_type: str = Form("engineer") # "engineer" or "job"
):
    """Parses text or binary files (PDF/Images) and structure them."""
    print(f"[*] API Parse Request received. Type: {doc_type}")
    
    file_bytes = None
    file_name = None
    file_type = None
    
    if file:
        file_bytes = await file.read()
        file_name = file.filename
        file_type = file.content_type
        print(f"  - File uploaded: {file_name} ({file_type}, {len(file_bytes)} bytes)")
    elif text:
        print(f"  - Direct text input received ({len(text)} characters)")
    else:
        raise HTTPException(status_code=400, detail="Either file or text must be provided.")

    source_text = text or decode_uploaded_text(file_bytes or b"")
    fallback_reason = "Gemini live mode is not configured."

    # --- Live Gemini Parsing Logic ---
    if GEMINI_READY:
        try:
            allowed, circuit_reason, _stats = check_external_api_circuit(
                "gemini_api",
                "parse",
                GEMINI_DAILY_CALL_LIMIT,
                GEMINI_DAILY_REPORTED_TOKEN_LIMIT,
            )
            if not allowed:
                append_external_api_event({
                    "provider": "gemini_api",
                    "operation": "parse",
                    "billable": False,
                    "outcome": "blocked",
                    "model": GEMINI_MODEL,
                    "reason": circuit_reason,
                    "prompt_digest": stable_digest(source_text),
                })
                raise RuntimeError(circuit_reason)
            local_profile = build_profile(source_text, doc_type)
            
            prompt = (
                f"You are a professional HR data extraction engine.\n"
                f"Parse the following {doc_type} document and extract a clean structured text summary in Japanese.\n"
                f"Focus on extracting: Name (if engineer), Job Title / Role Name, Core Skills, Cloud / Infra, Databases, and Career Goals.\n"
                f"Make sure to output clean Japanese, keeping important technical details.\n"
                f"Use this local deterministic pre-parse as hints, but correct it when the document says otherwise:\n"
                f"{json.dumps(asdict(local_profile), ensure_ascii=False)}"
            )
            
            response = None
            if file_bytes:
                # Multimodal API Input (PDF/Images)
                pdf_part = genai_types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=file_type or "application/octet-stream",
                )
                response = generate_gemini_content([pdf_part, prompt])
            else:
                response = generate_gemini_content(f"{prompt}\n\nDocument Content:\n{text}")
                
            parsed_text = response.text.strip()
            append_external_api_event({
                "provider": "gemini_api",
                "operation": "parse",
                "billable": True,
                "outcome": "success",
                "model": GEMINI_MODEL,
                "prompt_digest": stable_digest(source_text),
                **find_token_usage(getattr(response, "usage_metadata", None)),
            })
            print(f"[+] Gemini Parser Sync completed successfully.")
            audit_event = write_audit_event(
                "parse",
                profile_audit_payload(local_profile, "gemini_live", "", source_text, file_name)
            )
            return {
                "status": "success",
                "ai_mode": "gemini_live",
                "parsed_content": parsed_text,
                "structured_profile": asdict(local_profile),
                "audit_event_id": audit_event["event_id"]
            }
            
        except Exception as e:
            fallback_reason = str(e)
            if "daily" not in fallback_reason.lower():
                append_external_api_event({
                    "provider": "gemini_api",
                    "operation": "parse",
                    "billable": False,
                    "outcome": "exception",
                    "model": GEMINI_MODEL,
                    "reason": fallback_reason,
                    "prompt_digest": stable_digest(source_text),
                })
            print(f"[-] Gemini live parser failed: {e}. Falling back to deterministic parser.")
    elif AI_FORCE_MOCK:
        fallback_reason = "AI_FORCE_MOCK is enabled to avoid Gemini quota usage."

    # --- Quota-safe deterministic parser fallback ---
    import time
    time.sleep(1.0) # Simulating AI processing time

    profile = build_profile(source_text, doc_type)
    parsed_content = format_profile(profile)
    audit_event = write_audit_event(
        "parse",
        profile_audit_payload(profile, "deterministic_fallback", fallback_reason, source_text, file_name)
    )
        
    print(f"[+] Deterministic parser fallback completed successfully.")
    return {
        "status": "success",
        "ai_mode": "deterministic_fallback",
        "fallback_reason": fallback_reason,
        "parsed_content": parsed_content,
        "structured_profile": asdict(profile),
        "audit_event_id": audit_event["event_id"]
    }


class EvaluationRequest(BaseModel):
    engineer_content: str
    job_content: str

# 2. API: 4-Dimension AI Fit Evaluation
@app.post("/api/match")
async def evaluate_matching(req: EvaluationRequest):
    """Calculates multidimensional matching score and generate interview QA and roadmap."""
    print("[*] API Match Request received.")
    
    fallback_reason = "Gemini live mode is not configured."

    # --- Live Gemini Evaluation Logic ---
    if GEMINI_READY:
        try:
            allowed, circuit_reason, _stats = check_external_api_circuit(
                "gemini_api",
                "match",
                GEMINI_DAILY_CALL_LIMIT,
                GEMINI_DAILY_REPORTED_TOKEN_LIMIT,
            )
            if not allowed:
                append_external_api_event({
                    "provider": "gemini_api",
                    "operation": "match",
                    "billable": False,
                    "outcome": "blocked",
                    "model": GEMINI_MODEL,
                    "reason": circuit_reason,
                    "prompt_digest": stable_digest(req.engineer_content + req.job_content),
                })
                raise RuntimeError(circuit_reason)
            fallback_context = build_fallback_match(
                req.engineer_content,
                req.job_content,
                "local deterministic pre-score for Gemini prompt context"
            )
            
            prompt = (
                "You are the Mighty-Link AI engine. Evaluate the fit between the Candidate Resume and the Job Description.\n"
                "You MUST return the response strictly as a JSON object with the following fields:\n"
                "{\n"
                "  \"final_score\": <Integer from 50 to 100>,\n"
                "  \"scores\": {\n"
                "    \"skill\": <Integer 50-100>,\n"
                "    \"culture\": <Integer 50-100>,\n"
                "    \"growth\": <Integer 50-100>,\n"
                "    \"performing\": <Integer 50-100>\n"
                "  },\n"
                "  \"summary\": \"<Detailed multi-dimensional evaluation summary paragraph in Japanese>\",\n"
                "  \"qa\": [\n"
                "    {\n"
                "      \"question\": \"<Technical interview question tailored for this specific match in Japanese>\",\n"
                "      \"answer\": \"<Best practice guide for candidate answer in Japanese>\",\n"
                "      \"tip\": \"<Tips to enhance points in Japanese>\"\n"
                "    },\n"
                "    {\n"
                "      \"question\": \"<Another relevant interview question in Japanese>\",\n"
                "      \"answer\": \"<Answer guide in Japanese>\",\n"
                "      \"tip\": \"<Tips in Japanese>\"\n"
                "    }\n"
                "  ],\n"
                "  \"roadmap_week1\": \"<Detailed week 1 roadmap actions in Japanese>\",\n"
                "  \"roadmap_week2\": \"<Detailed week 2 roadmap actions in Japanese>\",\n"
                "  \"roadmap_week3\": \"<Detailed week 3 roadmap actions in Japanese>\",\n"
                "  \"roadmap_week4\": \"<Detailed week 4 roadmap actions in Japanese>\"\n"
                "}\n"
                "Do NOT include any markdown code blocks (like ```json) or explanation text outside the JSON.\n\n"
                "Use this deterministic local analysis as structured context. Correct it when the source text provides better evidence:\n"
                f"{json.dumps(fallback_context.get('structured', {}), ensure_ascii=False)}\n\n"
                f"Candidate Resume Data:\n{req.engineer_content}\n\n"
                f"Job Description Data:\n{req.job_content}"
            )
            
            response = generate_gemini_content(
                prompt,
                response_mime_type="application/json"
            )
            
            res_text = response.text.strip()
            # Clean possible raw markdown block if LLM fails strict config
            if res_text.startswith("```"):
                res_text = res_text.split("\n", 1)[1].rsplit("\n", 1)[0]
                if res_text.startswith("json"):
                    res_text = res_text.split("\n", 1)[1]
            
            match_data = json.loads(res_text.strip())
            match_data["ai_mode"] = "gemini_live"
            match_data.setdefault("structured", fallback_context.get("structured", {}))
            append_external_api_event({
                "provider": "gemini_api",
                "operation": "match",
                "billable": True,
                "outcome": "success",
                "model": GEMINI_MODEL,
                "prompt_digest": stable_digest(req.engineer_content + req.job_content),
                **find_token_usage(getattr(response, "usage_metadata", None)),
            })
            audit_event = write_audit_event("match", match_audit_payload(match_data))
            match_data["audit_event_id"] = audit_event["event_id"]
            print("[+] Gemini Evaluator completed successfully.")
            return match_data
            
        except Exception as e:
            fallback_reason = str(e)
            if "daily" not in fallback_reason.lower():
                append_external_api_event({
                    "provider": "gemini_api",
                    "operation": "match",
                    "billable": False,
                    "outcome": "exception",
                    "model": GEMINI_MODEL,
                    "reason": fallback_reason,
                    "prompt_digest": stable_digest(req.engineer_content + req.job_content),
                })
            print(f"[-] Gemini live evaluation failed: {e}. Falling back to deterministic evaluator.")
    elif AI_FORCE_MOCK:
        fallback_reason = "AI_FORCE_MOCK is enabled to avoid Gemini quota usage."

    # --- Quota-safe deterministic evaluator fallback ---
    import time
    time.sleep(1.5) # Simulating AI processing time

    fallback_response = build_fallback_match(req.engineer_content, req.job_content, fallback_reason)
    audit_event = write_audit_event("match", match_audit_payload(fallback_response))
    fallback_response["audit_event_id"] = audit_event["event_id"]
    print("[+] Deterministic evaluator fallback completed successfully.")
    return fallback_response


class SyncRequest(BaseModel):
    candidate_name: str
    job_name: str
    final_score: int
    skill_score: int
    culture_score: int
    growth_score: int
    performing_score: int
    summary: str

# 3. API: Google Sheets Synchronizer
@app.post("/api/sync")
async def sync_to_sheets(req: SyncRequest):
    """Appends matching evaluation records into Google Sheets with visual formatting."""
    print(f"[*] API Sheets Sync request: {req.candidate_name} <=> {req.job_name}")
    
    if not SHEETS_LIB_AVAILABLE:
        print("[-] gspread library is missing. Cannot perform Sheets Sync.")
        return {"status": "error", "message": "Google Sheets client library is not installed."}
        
    client = None
    auth_mode = None
    
    # 1. OAuth 2.0 Auth Check
    if os.path.exists(CLIENT_SECRET_FILE):
        try:
            client = gspread.oauth(
                credentials_filename=CLIENT_SECRET_FILE,
                authorized_user_filename=AUTHORIZED_USER_FILE
            )
            assert_expected_google_account(credentials_from_gspread_client(client), USER_EMAIL)
            auth_mode = "OAuth 2.0"
        except GoogleWorkspaceAccountError as e:
            print(f"[-] OAuth 2.0 Workspace account verification failed in API: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            print(f"[-] OAuth 2.0 authentication failed in API: {e}")

    # 2. Service Account Fallback
    if not client and os.path.exists(CREDENTIALS_FILE):
        try:
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = ServiceCredentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
            client = gspread.authorize(creds)
            auth_mode = "Service Account"
        except Exception as e:
            print(f"[-] Service Account authentication failed in API: {e}")
            
    if not client:
        print("[-] Authentication credentials not found for Google Sheets.")
        return {"status": "error", "message": "Credentials file not found."}
        
    try:
        # 3. Open Spreadsheet and sheet
        sh = client.open_by_key(SPREADSHEET_ID)
        
        # Check if tab exists, otherwise create it
        tab_name = "Mighty Match Logs"
        try:
            worksheet = sh.worksheet(tab_name)
            print(f"[+] Opened existing sheet: '{tab_name}'")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=tab_name, rows="100", cols="10")
            print(f"[+] Created new sheet: '{tab_name}'")
            
        # Get current data to check headers
        existing_values = worksheet.get_all_values()
        
        headers = ["診断日時", "候補者氏名", "案件・求人名", "総合マッチ度 (%)", "技術 (Skill)", "文化 (Culture)", "キャリア (Growth)", "即戦力 (Performing)", "分析レポート概要"]
        
        # 4. Prepare batch requests list to prevent 429
        requests_list = []
        row_index = 1
        
        if not existing_values:
            # Append headers
            worksheet.append_row(headers)
            existing_values = [headers]
            row_index = 2
        else:
            row_index = len(existing_values) + 1
            
        # Append data row
        jst = datetime.timezone(datetime.timedelta(hours=9))
        jst_now = datetime.datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
        data_row = [
            jst_now,
            req.candidate_name,
            req.job_name,
            req.final_score,
            req.skill_score,
            req.culture_score,
            req.growth_score,
            req.performing_score,
            req.summary
        ]
        worksheet.append_row(data_row)
        print(f"[+] Successfully appended matching record for {req.candidate_name} into row {row_index}")
        
        # 5. Apply Visual Formatting to Sheets (Mighty Blue Design) via batch update
        sheet_id = worksheet.id
        
        # Gridlines enable
        requests_list.append({
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridlinesVisible": True
                },
                "fields": "gridlinesVisible"
            }
        })
        
        # Format Header Row (Mighty Blue, Bold, White text, Centered)
        requests_list.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": len(headers)
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": COLORS["header_bg"],
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "textFormat": {
                            "foregroundColor": COLORS["header_text"],
                            "bold": True,
                            "fontSize": 11
                        }
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,textFormat)"
            }
        })
        
        # Format Data Row Just Inserted (Center align scores, gray background if even)
        is_even = row_index % 2 == 0
        cell_format = {
            "verticalAlignment": "MIDDLE",
            "textFormat": {"fontSize": 10}
        }
        if is_even:
            cell_format["backgroundColor"] = COLORS["row_even"]
            
        requests_list.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": row_index - 1,
                    "endRowIndex": row_index,
                    "startColumnIndex": 0,
                    "endColumnIndex": len(headers)
                },
                "cell": {
                    "userEnteredFormat": cell_format
                },
                "fields": "userEnteredFormat(backgroundColor,verticalAlignment,textFormat)"
            }
        })
        
        # Center align scores specifically (columns index 3 to 7: final_score, skill, culture, growth, performing)
        requests_list.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": row_index - 1,
                    "endRowIndex": row_index,
                    "startColumnIndex": 3,
                    "endColumnIndex": 8
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER",
                        "textFormat": {
                            "bold": True,
                            "foregroundColor": COLORS["accent_green"]
                        }
                    }
                },
                "fields": "userEnteredFormat(horizontalAlignment,textFormat)"
            }
        })
        
        # Auto-resize columns width
        requests_list.append({
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": len(headers)
                }
            }
        })
        
        # Set specific height for rows
        requests_list.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": 0,
                    "endIndex": 1
                },
                "properties": {
                    "pixelSize": 36
                },
                "fields": "pixelSize"
            }
        })
        requests_list.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": row_index - 1,
                    "endIndex": row_index
                },
                "properties": {
                    "pixelSize": 28
                },
                "fields": "pixelSize"
            }
        })
        
        # Execute Visual Formatting Batch Update
        sh.batch_update({"requests": requests_list})
        print(f"[+] Visual styles and formatting applied successfully to '{tab_name}'!")
        
        return {"status": "success", "message": f"Successfully synced matching record into Google Sheets via {auth_mode}."}
        
    except Exception as e:
        print(f"[-] Sheets synchronization failed: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        try:
            import asyncio
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except (AttributeError, RuntimeError):
            pass
    import uvicorn
    print("[*] Starting Mighty Skill-Bridge FastAPI local server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
