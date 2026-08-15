"""AI Interview Scheduling & Calendar Integration Module (T968)."""

import urllib.parse
from typing import Any, Dict, List, Optional

def generate_interview_candidate_slots(
    base_date: str = "2026-09-01",
    slots: Optional[List[str]] = None
) -> List[str]:
    """Generate structured candidate interview time slots."""
    if slots:
        return slots
    return [
        f"{base_date} 10:00〜11:00 (オンライン / Google Meet)",
        f"{base_date} 14:00〜15:00 (オンライン / Google Meet)",
        f"{base_date} 16:30〜17:30 (オンライン / Google Meet)"
    ]

def build_google_calendar_url(
    title: str,
    start_iso: str,
    end_iso: str,
    description: str,
    location: str = "Google Meet (オンライン)"
) -> str:
    """Build a one-click Google Calendar event creation URL."""
    # format: YYYYMMDDTHHMMSSZ
    clean_start = start_iso.replace("-", "").replace(":", "").replace(" ", "T")
    clean_end = end_iso.replace("-", "").replace(":", "").replace(" ", "T")
    dates_param = f"{clean_start}/{clean_end}"

    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": dates_param,
        "details": description,
        "location": location
    }
    return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"

def create_interview_schedule_package(
    job_title: str,
    client_name: str,
    engineer_name: str,
    proposed_date: str = "2026-09-02",
    start_time: str = "14:00",
    end_time: str = "15:00"
) -> Dict[str, Any]:
    """Create a complete interview scheduling package with slots and calendar URL."""
    slots = generate_interview_candidate_slots(proposed_date)
    start_iso = f"{proposed_date} {start_time}:00"
    end_iso = f"{proposed_date} {end_time}:00"
    
    title = f"【面談】{job_title}（{engineer_name}様 / {client_name}様）"
    description = f"案件: {job_title}\n候補エンジニア: {engineer_name}様\nクライアント: {client_name}様\n\n※ MightyLink AI Connect にて自動調整"
    calendar_url = build_google_calendar_url(title, start_iso, end_iso, description)

    return {
        "status": "success",
        "job_title": job_title,
        "engineer_name": engineer_name,
        "client_name": client_name,
        "candidate_slots": slots,
        "selected_slot": f"{proposed_date} {start_time}〜{end_time}",
        "google_calendar_url": calendar_url
    }
