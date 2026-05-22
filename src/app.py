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
import requests
import subprocess
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Tuple

# Set console encoding to UTF-8 to prevent encoding errors on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
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
    import google.generativeai as genai
    GEMINI_LIB_AVAILABLE = True
except ImportError:
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
KNOWLEDGE_FLOW_DIR = os.path.join(EXPORTS_DIR, "knowledge_flow")
KNOWLEDGE_FLOW_MANIFEST = os.path.join(KNOWLEDGE_FLOW_DIR, "manifest.json")
KNOWLEDGE_FLOW_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "generate_knowledge_flow_demo.py")
SEEDANCE_DEMO_DIR = os.path.join(EXPORTS_DIR, "seedance_demo")
SEEDANCE_DEMO_VIDEO = os.path.join(SEEDANCE_DEMO_DIR, "mighty_skill_bridge_seedance_demo.mp4")
SEEDANCE_DEMO_MANIFEST = os.path.join(SEEDANCE_DEMO_DIR, "manifest.json")
SEEDANCE_MODEL = os.environ.get("SEEDANCE_MODEL", "seedance-1-0-pro")
SEEDANCE_API_URL = os.environ.get("SEEDANCE_API_URL", "").strip()
SEEDANCE_RESULT_API_URL_TEMPLATE = os.environ.get("SEEDANCE_RESULT_API_URL_TEMPLATE", "").strip()
SEEDANCE_PAYLOAD_STYLE = os.environ.get("SEEDANCE_PAYLOAD_STYLE", "content_task").strip().lower()
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

os.makedirs(EXPORTS_DIR, exist_ok=True)
app.mount("/exports", StaticFiles(directory=EXPORTS_DIR), name="exports")

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


def seedance_demo_video_url() -> Optional[str]:
    if os.path.exists(SEEDANCE_DEMO_VIDEO):
        return "/exports/seedance_demo/mighty_skill_bridge_seedance_demo.mp4"
    return None


def read_seedance_manifest() -> Optional[dict]:
    if not os.path.exists(SEEDANCE_DEMO_MANIFEST):
        return None
    with open(SEEDANCE_DEMO_MANIFEST, "r", encoding="utf-8") as f:
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
    }


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

if GEMINI_READY:
    genai.configure(api_key=API_KEY)
    print("[+] Gemini API successfully configured via GEMINI_API_KEY.")
elif AI_FORCE_MOCK:
    print("[!] AI_FORCE_MOCK enabled. Running in quota-safe mock fallback mode.")
else:
    print("[!] Warning: GEMINI_API_KEY not set or library missing. Running in mock fallback mode.")

SEEDANCE_READY = bool(SEEDANCE_API_KEY and SEEDANCE_API_URL)
if SEEDANCE_READY:
    print("[+] Seedance API adapter configured via environment variables.")
else:
    print("[!] Seedance API credentials not set. Using local demo video fallback.")


class SeedanceVideoRequest(BaseModel):
    prompt: str
    aspect_ratio: str = "16:9"
    duration_seconds: int = 6

# Static Hosting route
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
        "seedance_model": SEEDANCE_MODEL,
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
        return seedance_fallback_response(
            "SEEDANCE_API_KEY and SEEDANCE_API_URL are not configured.",
            prompt,
        )

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
            return seedance_fallback_response(
                f"Seedance API request failed: {summarize_seedance_http_error(create_response)}",
                prompt,
            )
        create_payload = create_response.json()
        video_url = find_video_url(create_payload)
        task_id = find_task_id(create_payload)

        if video_url:
            return {
                "status": "success",
                "mode": "live",
                "provider": "seedance_api",
                "model": SEEDANCE_MODEL,
                "video_url": video_url,
                "task_id": task_id,
                "raw_status": create_payload.get("status") if isinstance(create_payload, dict) else None,
            }

        if task_id and SEEDANCE_RESULT_API_URL_TEMPLATE:
            result_url = SEEDANCE_RESULT_API_URL_TEMPLATE.format(task_id=task_id)
            result_response = requests.get(result_url, headers=headers, timeout=45)
            if not result_response.ok:
                return seedance_fallback_response(
                    f"Seedance result request failed: {summarize_seedance_http_error(result_response)}",
                    prompt,
                    task_id,
                )
            result_payload = result_response.json()
            video_url = find_video_url(result_payload)
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

        return seedance_fallback_response(
            "Seedance task was accepted but no video URL was returned yet.",
            prompt,
            task_id,
        )
    except requests.RequestException as exc:
        return seedance_fallback_response(f"Seedance API request failed: {exc}", prompt)
    except ValueError as exc:
        return seedance_fallback_response(f"Seedance API returned non-JSON response: {exc}", prompt)


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
            local_profile = build_profile(source_text, doc_type)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
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
                pdf_part = {
                    "mime_type": file_type,
                    "data": file_bytes
                }
                response = model.generate_content([prompt, pdf_part])
            else:
                response = model.generate_content(f"{prompt}\n\nDocument Content:\n{text}")
                
            parsed_text = response.text.strip()
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
            fallback_context = build_fallback_match(
                req.engineer_content,
                req.job_content,
                "local deterministic pre-score for Gemini prompt context"
            )
            model = genai.GenerativeModel("gemini-1.5-flash")
            
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
            
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
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
            audit_event = write_audit_event("match", match_audit_payload(match_data))
            match_data["audit_event_id"] = audit_event["event_id"]
            print("[+] Gemini Evaluator completed successfully.")
            return match_data
            
        except Exception as e:
            fallback_reason = str(e)
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
    import uvicorn
    print("[*] Starting Mighty Skill-Bridge FastAPI local server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
