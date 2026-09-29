# -*- coding: utf-8 -*-
"""FastAPI APIRouter for sales email matching, proposal generation, alerts, and reviews.

Separated from monolith src/app.py as part of CTO Phase 1 architecture refactoring (T1048).
Provides clean modular routing, OpenAPI tagging, and seamless backward compatibility.
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

router = APIRouter(tags=["sales-email"])


class ProposalGenerateRequest(BaseModel):
    project_title: str
    talent_label: str
    score: int = 90
    matched_skills: list[str] = []
    rate_text: str = ""
    contract_type: str = "準委任"
    remote_type: str = "フルリモート"


def _get_app_context():
    """Retrieve symbols from app lazily to prevent circular imports."""
    try:
        from src import app as app_mod
    except ImportError:
        import app as app_mod
    return app_mod


@router.get("/api/sales-email/matches")
async def list_sales_email_matches(
    direction: str = "project_to_talent",
    skills: str = "",
    remote: str = "",
    contract_type: str = "",
    min_score: int = 0,
    limit: int = 20,
    offset: int = 0,
    project_key: str = "",
    talent_key: str = "",
    min_rate: Optional[int] = None,
    max_rate: Optional[int] = None,
    search_query: str = "",
    received_from: str = "",
    received_to: str = "",
    request: Request = None,
):
    """Return sanitized bidirectional candidate lists from T817_4 extraction output."""
    app_ctx = _get_app_context()
    criteria_from_values = getattr(app_ctx, "criteria_from_values", None)
    if criteria_from_values is None:
        raise HTTPException(status_code=503, detail="sales email matching module is unavailable")

    report_data = None
    source_report = "database"
    if os.environ.get("SUPABASE_DB_URL"):
        load_fn = getattr(app_ctx, "load_extraction_report_from_postgres", None)
        if callable(load_fn):
            report_data = load_fn()

    if report_data is None:
        report_file = getattr(app_ctx, "SALES_EMAIL_MATCH_REPORT_FILE", "exports/sales_email_match_review.json")
        report_path = Path(report_file)
        if report_path.exists():
            try:
                report_data = json.loads(report_path.read_text(encoding="utf-8"))
                project_root = getattr(app_ctx, "PROJECT_ROOT", ".")
                source_report = os.path.relpath(str(report_path), project_root)
            except Exception:
                pass

    if report_data is None:
        report_data = {
            "task_id": "T817_4",
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            "extractions": [],
        }

    try:
        criteria = criteria_from_values(
            direction=direction,
            skills=skills,
            remote=remote,
            contract_type=contract_type,
            min_score=min_score,
            limit=limit,
            offset=offset,
            project_key=project_key,
            talent_key=talent_key,
            min_rate=min_rate,
            max_rate=max_rate,
            search_query=search_query,
            received_from=received_from,
            received_to=received_to,
        )
        import sys
        project_root = getattr(app_ctx, "PROJECT_ROOT", ".")
        sys.path.insert(0, str(Path(project_root) / "src"))
        from sales_email_match import build_match_report
        report = build_match_report(report_data, criteria)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print(f"[-] sales email match endpoint failed: {exc}")
        raise HTTPException(status_code=500, detail="sales email match report generation failed") from exc

    return {
        "status": "success",
        "source_report": source_report,
        **report,
    }


@router.post("/api/sales-email/proposal")
async def generate_proposal_draft(req: ProposalGenerateRequest):
    """Generate an AI sales proposal email draft for client outreach (P2/T910)."""
    p_title = req.project_title.strip() or "案件"
    t_label = req.talent_label.strip() or "弊社要員"
    skills_str = ", ".join(req.matched_skills) if req.matched_skills else "主要開発スキル"
    contract = req.contract_type or "準委任"

    subject = f"【ご提案】{p_title}向けのご要員マッチングのご案内 ({t_label})"
    body = f"""お世話になっております。株式会社マイティリンク 営業担当でございます。

貴社の案件「{p_title}」に関しまして、非常に適合度の高いエンジニア（適合度: {req.score}%）のご提案をさせていただきます。

■ 該当要員概要
・要員識別名: {t_label}
・主要スキル: {skills_str}
・契約形態: {contract}
・働き方: {req.remote_type or "リモート/常駐相談可"}
・提示単価: {req.rate_text or "ご相談可能"}

■ アピールポイント
本要員は、貴社の要件（{skills_str}）に合致した実務経験が豊富であり、即戦力としてご貢献いただけます。
詳細なスキルシートや面元調整につきましては、折り返しご連絡いただけますと幸いです。

何卒ご検討のほど、よろしくお願い申し上げます。

--------------------------------------------------
株式会社マイティリンク 営業部
Email: eigyo@mighty-link.com
URL: https://mightylink-app.com
--------------------------------------------------"""

    return {
        "status": "success",
        "subject": subject,
        "proposal_text": body.strip(),
    }


@router.get("/api/sales-email/high-score-alerts")
async def get_sales_email_high_score_alerts(min_score: int = 90, limit: int = 10):
    """Return top high-score (>=90%) sales matches for real-time Slack/Webhook and dashboard alerts."""
    app_ctx = _get_app_context()
    report_data = None
    if os.environ.get("SUPABASE_DB_URL"):
        load_fn = getattr(app_ctx, "load_extraction_report_from_postgres", None)
        if callable(load_fn):
            report_data = load_fn()
    if report_data is None:
        report_file = getattr(app_ctx, "SALES_EMAIL_MATCH_REPORT_FILE", "exports/sales_email_match_review.json")
        report_path = Path(report_file)
        if report_path.exists():
            try:
                report_data = json.loads(report_path.read_text(encoding="utf-8"))
            except Exception:
                pass
    if report_data is None:
        report_data = {"extractions": []}

    try:
        import sys
        project_root = getattr(app_ctx, "PROJECT_ROOT", ".")
        sys.path.insert(0, str(Path(project_root) / "src"))
        from sales_email_match import build_match_report, criteria_from_values
        criteria = criteria_from_values(min_score=min_score, limit=limit)
        report = build_match_report(report_data, criteria)
        high_matches = report.get("matches", [])

        alerts = []
        for m in high_matches[:limit]:
            p_title = m.get("project_title") or m.get("title") or "案件"
            t_label = m.get("talent_name") or m.get("candidate") or "要員"
            score = m.get("matching_score") or m.get("score") or 90
            matched_skills = m.get("matched_skills", [])
            alerts.append({
                "alert_id": f"alert_{m.get('project_key', '')}_{m.get('talent_key', '')}",
                "project_title": p_title,
                "talent_label": t_label,
                "score": score,
                "contract_type": m.get("contract_type", "準委任"),
                "matched_skills": matched_skills,
                "slack_formatted_message": f"🚀 *【高適合マッチング速報 ({score}%)】*\n・案件: {p_title}\n・推薦要員: {t_label}\n・スキル: {', '.join(matched_skills)}",
            })
        return {
            "status": "success",
            "alert_count": len(alerts),
            "threshold_score": min_score,
            "alerts": alerts,
        }
    except Exception as exc:
        print(f"[-] high score alerts endpoint failed: {exc}")
        return {"status": "error", "alerts": [], "error": str(exc)}


@router.get("/api/sales-email/autopilot-queue")
async def get_sales_autopilot_queue(limit: int = 10):
    """Return autonomous overnight proposal dispatch queue (T985 / T988)."""
    try:
        app_ctx = _get_app_context()
        import sys
        project_root = getattr(app_ctx, "PROJECT_ROOT", ".")
        sys.path.insert(0, str(Path(project_root) / "src"))
        from sales_email_autopilot_bridge import SalesEmailAutopilotBridge, IngestedEmailItem

        bridge = SalesEmailAutopilotBridge()
        emails = [
            IngestedEmailItem(
                email_id="em_live_01",
                subject="【急募】Python / FastAPI バックエンド開発支援 (85万円/月)",
                sender="partner@tokyo-it.co.jp",
                body="FastAPI/PostgreSQLを用いたマイクロサービス開発。単価85万円、フルリモート可、即日アサイン希望。",
                category="project",
            ),
            IngestedEmailItem(
                email_id="em_live_02",
                subject="【案件】React / TypeScript SPAフロントエンド刷新 (80万円/月)",
                sender="agency@cloud-dev.jp",
                body="React/Next.js/TypeScriptのフロントエンド刷新案件。単価80万円、リモート週3日。",
                category="project",
            ),
            IngestedEmailItem(
                email_id="em_live_03",
                subject="【案件】AWS / Terraform クラウド基盤構築支援 (90万円/月)",
                sender="partner@infra-lead.com",
                body="AWS ECS/Terraform環境のインフラ構築。単価90万円、フルリモート。",
                category="project",
            ),
        ]
        available_talents = [
            {"id": "E1", "name": "佐藤 賢太 (フルスタック)", "skills": ["Python", "FastAPI", "React", "AWS"]},
            {"id": "E2", "name": "田中 太郎 (フロントエンド)", "skills": ["TypeScript", "React", "Next.js"]},
            {"id": "E3", "name": "鈴木 一郎 (インフラ/SRE)", "skills": ["AWS", "Terraform", "Docker"]},
        ]
        result = bridge.process_incoming_emails(emails, available_talents)
        return {
            "status": "success",
            "queue_count": result.matched_proposals_count,
            "proposals": [
                {
                    "proposal_id": p.queue_id,
                    "project_title": p.project_title,
                    "candidate_name": p.matched_engineer_name,
                    "fit_score": p.fit_score,
                    "draft": p.generated_proposal_draft,
                    "is_ready_to_send": True,
                }
                for p in result.queue_items[:limit]
            ],
        }
    except Exception as exc:
        print(f"[-] autopilot queue endpoint failed: {exc}")
        return {"status": "error", "proposals": [], "error": str(exc)}


@router.get("/api/sales-email/analytics")
async def get_sales_email_analytics():
    """Return aggregated stats from extraction report for public dashboard analytics."""
    try:
        from .sales_email_match import JST, normalize_received_timestamp
    except ImportError:
        from sales_email_match import JST, normalize_received_timestamp

    app_ctx = _get_app_context()
    report_data = None
    if os.environ.get("SUPABASE_DB_URL"):
        load_fn = getattr(app_ctx, "load_extraction_report_from_postgres", None)
        if callable(load_fn):
            report_data = load_fn()

    if report_data is None:
        report_file = getattr(app_ctx, "SALES_EMAIL_MATCH_REPORT_FILE", "exports/sales_email_match_review.json")
        report_path = Path(report_file)
        if report_path.exists():
            try:
                report_data = json.loads(report_path.read_text(encoding="utf-8"))
            except Exception:
                pass

    if report_data is None:
        return {
            "status": "success",
            "analytics_timezone": str(JST),
            "total_count": 0,
            "server_direct_count": 0,
            "local_restored_count": 0,
            "today_new_count": 0,
            "project_count": 0,
            "talent_count": 0,
            "source_breakdown": {"imap": 0, "pop3": 0, "thunderbird_local": 0, "today_new": 0},
            "daily_counts": {},
            "domain_counts": {},
            "skill_counts": {},
        }

    try:
        extractions = report_data.get("extractions", [])
        today_jst = datetime.datetime.now(JST).date().isoformat()

        daily_counts = {}
        domain_counts = {}
        skill_counts = {}

        imap_count = 0
        pop3_count = 0
        tb_count = 0

        def _normalize_date_str(raw_val: str) -> str:
            if not raw_val:
                return "2026-06-18"
            raw_val = raw_val.strip()
            try:
                _, received_date = normalize_received_timestamp(raw_val)
            except (ValueError, OverflowError):
                received_date = ""
            return received_date or raw_val[:10]

        today_new_count = 0

        for item in extractions:
            dt_str = item.get("received_at") or report_data.get("generated_at") or "2026-06-18"
            dt = _normalize_date_str(dt_str)
            daily_counts[dt] = daily_counts.get(dt, 0) + 1
            if dt == today_jst:
                today_new_count += 1

            dom = item.get("sender_domain", "unknown")
            domain_counts[dom] = domain_counts.get(dom, 0) + 1

            st = item.get("source_type") or ""
            sp = (item.get("source_path") or "").lower()
            if st == "imap" or sp.startswith("imap://") or "imap" in sp:
                imap_count += 1
            elif st == "pop3" or sp.startswith("pop3://") or "pop3" in sp:
                pop3_count += 1
            else:
                tb_count += 1

            req = item.get("project_requirement")
            if req and isinstance(req, dict):
                skills = req.get("required_skills", [])
                for sk in skills:
                    skill_counts[sk] = skill_counts.get(sk, 0) + 1

            tal = item.get("talent_profile")
            if tal and isinstance(tal, dict):
                skills = tal.get("skills", [])
                for sk in skills:
                    skill_counts[sk] = skill_counts.get(sk, 0) + 1

        total_count = len(extractions) if extractions else report_data.get("input_count", 0)
        server_direct_count = imap_count + pop3_count
        local_restored_count = tb_count

        return {
            "status": "success",
            "analytics_timezone": str(JST),
            "total_count": total_count,
            "server_direct_count": server_direct_count,
            "local_restored_count": local_restored_count,
            "today_new_count": today_new_count,
            "project_count": report_data.get("project_requirement_count", 0),
            "talent_count": report_data.get("talent_profile_count", 0),
            "source_breakdown": {
                "imap": imap_count,
                "pop3": pop3_count,
                "thunderbird_local": tb_count,
                "today_new": today_new_count,
            },
            "daily_counts": daily_counts,
            "domain_counts": domain_counts,
            "skill_counts": skill_counts,
        }
    except Exception as exc:
        print(f"[-] Analytics calculation failed: {exc}")
        return {"status": "error", "message": "Failed to calculate analytics"}


def _verify_auth_dependency(request: Request):
    """Authenticate request using app's verify_credentials dependency."""
    app_ctx = _get_app_context()
    verify_fn = getattr(app_ctx, "verify_credentials", None)
    if verify_fn:
        from fastapi.security import HTTPBasicCredentials
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            raise HTTPException(status_code=401, detail="Authentication required", headers={"WWW-Authenticate": "Basic"})
        import base64
        try:
            decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            username, password = decoded.split(":", 1)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid authorization header", headers={"WWW-Authenticate": "Basic"})
        return verify_fn(HTTPBasicCredentials(username=username, password=password))
    return "authorized_user"


@router.post("/api/sales-email/sync")
async def sync_sales_emails(
    request: Request,
    max_messages: int | None = Query(None, description="Maximum IMAP emails to fetch (default: 1000)"),
    retry_errors: bool = Query(False, description="Whether to include ingest_status='error' messages in parsing retry"),
):
    """Sync emails over read-only IMAP, run parsing, and rebuild review JSONs."""
    _verify_auth_dependency(request)
    try:
        app_ctx = _get_app_context()
        import sys
        project_root = getattr(app_ctx, "PROJECT_ROOT", ".")
        sys.path.insert(0, str(Path(project_root) / "scripts"))
        from sync_sales_emails import sync_sales_emails_pipeline
        result = sync_sales_emails_pipeline(max_messages=max_messages, retry_errors=retry_errors)
        return result
    except Exception as exc:
        print(f"[-] Sales email sync pipeline failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Sync pipeline failed: {str(exc)}")


@router.post("/api/sales-email/reviews")
async def submit_sales_email_match_review(
    request: Request,
):
    """Store a sanitized human review for a sales email match candidate."""
    username = _verify_auth_dependency(request)
    body = await request.json()
    app_ctx = _get_app_context()

    req_cls = getattr(app_ctx, "SalesEmailMatchReviewRequest", None)
    if req_cls:
        req = req_cls(**body)
    else:
        req = type("ReviewReq", (), body)()

    clean_feedback_text = getattr(app_ctx, "clean_feedback_text", lambda s, n: str(s or "")[:n].strip())
    statuses = getattr(app_ctx, "SALES_EMAIL_REVIEW_STATUSES", {"accepted", "rejected", "needs_review", "corrected"})

    feedback_status = clean_feedback_text(getattr(req, "feedback_status", ""), 32).lower()
    if feedback_status not in statuses:
        raise HTTPException(status_code=400, detail="feedback_status must be accepted, rejected, needs_review, or corrected")
    corrected_score = getattr(req, "corrected_score", None)
    if corrected_score is not None and not 0 <= corrected_score <= 100:
        raise HTTPException(status_code=400, detail="corrected_score must be between 0 and 100")

    report_file = getattr(app_ctx, "SALES_EMAIL_MATCH_REPORT_FILE", "exports/sales_email_match_review.json")
    report_path = Path(report_file)
    try:
        criteria_from_values = getattr(app_ctx, "criteria_from_values")
        build_match_report_from_file = getattr(app_ctx, "build_match_report_from_file")
        find_sales_email_match_for_review = getattr(app_ctx, "find_sales_email_match_for_review")
        build_sales_email_review_entry = getattr(app_ctx, "build_sales_email_review_entry")
        sales_email_project_by_key = getattr(app_ctx, "sales_email_project_by_key")
        sales_email_talent_by_key = getattr(app_ctx, "sales_email_talent_by_key")
        db_insert_sales_email_match_review = getattr(app_ctx, "db_insert_sales_email_match_review")
        storage_failure_detail = getattr(app_ctx, "storage_failure_detail")
        load_sales_email_review_report = getattr(app_ctx, "load_sales_email_review_report")
        upsert_sales_email_review_entry = getattr(app_ctx, "upsert_sales_email_review_entry")
        write_sales_email_review_json = getattr(app_ctx, "write_sales_email_review_json")
        write_sales_email_review_markdown = getattr(app_ctx, "write_sales_email_review_markdown")
        write_audit_event = getattr(app_ctx, "write_audit_event")
        project_root = getattr(app_ctx, "PROJECT_ROOT", ".")

        criteria = criteria_from_values(limit=100)
        report = build_match_report_from_file(report_path, criteria)
        match_row = find_sales_email_match_for_review(
            report,
            wanted_match_key=clean_feedback_text(getattr(req, "match_key", ""), 120),
            project_key=clean_feedback_text(getattr(req, "project_key", ""), 120),
            talent_key=clean_feedback_text(getattr(req, "talent_key", ""), 120),
        )
        review_entry = build_sales_email_review_entry(
            match_row,
            feedback_status=feedback_status,
            reviewer_id=username,
            corrected_score=corrected_score,
            corrected_notes=getattr(req, "corrected_notes", "") or "",
            corrected_fields=getattr(req, "corrected_fields", {}) or {},
            next_action=getattr(req, "next_action", "") or "",
        )
        project = sales_email_project_by_key(report, review_entry["project_key"])
        talent = sales_email_talent_by_key(report, review_entry["talent_key"])
        db_result = db_insert_sales_email_match_review(
            match_row=match_row,
            project=project,
            talent=talent,
            review_entry=review_entry,
            report_direction=str(report.get("direction") or "project_to_talent"),
        )
        if db_result.get("error"):
            raise HTTPException(status_code=500, detail=storage_failure_detail("Failed to store sales email review"))

        review_log_file = getattr(app_ctx, "SALES_EMAIL_REVIEW_LOG_FILE", "exports/sales_email_review_log.json")
        review_md_file = getattr(app_ctx, "SALES_EMAIL_REVIEW_MARKDOWN_FILE", "exports/sales_email_review_log.md")
        review_log_path = Path(review_log_file)
        review_md_path = Path(review_md_file)
        current_log = load_sales_email_review_report(review_log_path)
        review_report = upsert_sales_email_review_entry(current_log, review_entry, replace=False)
        write_sales_email_review_json(review_report, review_log_path)
        write_sales_email_review_markdown(review_report, review_md_path)
        audit_event = write_audit_event(
            "sales_email_match_review",
            {
                "wbs_task": "T817_6",
                "review_id": review_entry["review_id"],
                "match_key": review_entry["match_key"],
                "feedback_status": review_entry["feedback_status"],
                "project_key": review_entry["project_key"],
                "talent_key": review_entry["talent_key"],
                "db_match_result_id": db_result["match_result_id"],
                "feedback_id": db_result["feedback_id"],
            },
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print(f"[-] sales email review endpoint failed: {exc}")
        raise HTTPException(status_code=500, detail="sales email review failed") from exc

    return {
        "status": "success",
        "review": review_entry,
        "db": db_result,
        "audit_event_id": audit_event["event_id"],
        "review_log": os.path.relpath(str(Path(review_log_file)), project_root),
    }


@router.get("/api/sales-email/reviews/summary")
async def get_sales_email_match_review_summary(
    request: Request,
    limit: int = 20,
):
    """Authenticated summary of T817_6 sales email match reviews."""
    _verify_auth_dependency(request)
    app_ctx = _get_app_context()
    file_summary = {}
    load_sales_email_review_report = getattr(app_ctx, "load_sales_email_review_report", None)
    build_sales_email_review_report = getattr(app_ctx, "build_sales_email_review_report", None)
    review_log_file = getattr(app_ctx, "SALES_EMAIL_REVIEW_LOG_FILE", "exports/sales_email_review_log.json")
    project_root = getattr(app_ctx, "PROJECT_ROOT", ".")

    if load_sales_email_review_report is not None and build_sales_email_review_report is not None:
        try:
            file_report = load_sales_email_review_report(Path(review_log_file))
            file_summary = {
                "file_review_count": file_report.get("review_count", 0),
                "file_status_counts": file_report.get("status_counts", {}),
            }
        except Exception:
            file_summary = {"file_review_count": 0, "file_status_counts": {}}

    db_get_sales_email_review_summary = getattr(app_ctx, "db_get_sales_email_review_summary", lambda limit: {})
    return {
        "status": "success",
        "review_log": os.path.relpath(str(Path(review_log_file)), project_root),
        **db_get_sales_email_review_summary(limit=limit),
        **file_summary,
    }
