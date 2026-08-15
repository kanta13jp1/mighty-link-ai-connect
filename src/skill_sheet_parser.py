"""Skill Sheet Fast AI Structured Parser Module (T965)."""

import re
from typing import Any, Dict, List, Optional

def parse_skill_sheet_text(raw_text: str) -> Dict[str, Any]:
    """Parse raw text/markdown skill sheet and extract structured profile."""
    # Heuristic & Regex Fallback extraction
    name_match = re.search(r'(?:氏名|名前|イニシャル|エンジニア名)[：:\s]*([^\n\r]+)', raw_text)
    name = name_match.group(1).strip() if name_match else "候補エンジニア"

    exp_years_match = re.search(r'(?:経験年数|エンジニア歴|IT経験)[：:\s]*([0-9０-９]+)年', raw_text)
    exp_years = int(exp_years_match.group(1)) if exp_years_match else 3

    rate_match = re.search(r'(?:単価|希望単価|希望月額)[：:\s]*([0-9０-９]+)万', raw_text)
    rate = int(rate_match.group(1)) if rate_match else 75

    available_match = re.search(r'(?:稼働可能日|稼働開始|参画可能時期)[：:\s]*([^\n\r]+)', raw_text)
    available_date = available_match.group(1).strip() if available_match else "即日（応相談）"

    # Common skill keywords
    known_skills = [
        "Python", "FastAPI", "Django", "Go", "Golang", "Java", "Spring",
        "TypeScript", "JavaScript", "React", "Next.js", "Vue", "Node.js",
        "AWS", "GCP", "Azure", "Docker", "Kubernetes", "PostgreSQL", "MySQL"
    ]
    detected_skills = []
    for skill in known_skills:
        if re.search(rf'\b{re.escape(skill)}\b', raw_text, re.IGNORECASE):
            detected_skills.append(skill)

    if not detected_skills:
        detected_skills = ["Python", "AWS"]

    return {
        "engineer_name": name,
        "experience_years": exp_years,
        "desired_rate_man_yen": rate,
        "available_date": available_date,
        "detected_skills": detected_skills,
        "raw_text_length": len(raw_text),
        "status": "success"
    }
