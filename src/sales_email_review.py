"""Human review helpers for sales email AI matching (T817_6).

This module stores only sanitized match metadata. It never reads raw email
bodies and redacts contact/secret-like text from reviewer notes before writing
review artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


DEFAULT_MATCH_REPORT = Path("exports") / "sales_email_match_review.json"
DEFAULT_JSON_REPORT = Path("exports") / "sales_email_review_log.json"
DEFAULT_MARKDOWN_REPORT = Path("exports") / "sales_email_review_log.md"
REVIEW_MODEL_NAME = "human-sales-email-review-loop-v1"
VALID_FEEDBACK_STATUSES = {"accepted", "rejected", "needs_review", "corrected"}
REQUIRED_REVIEW_PRIVACY_CONTROLS = [
    "raw_email_body_not_loaded",
    "review_notes_redacted",
    "talent_identity_anonymized",
    "human_decision_logged",
]

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
SECRET_RE = re.compile(
    r"(Bearer\s+[A-Za-z0-9._=-]+|(?:api[_-]?key|token|secret|password)\s*[:=]\s*[A-Za-z0-9._=-]+)",
    re.IGNORECASE,
)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def as_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def redact_sensitive_text(value: Any) -> str:
    text = " ".join(str(value or "").split())
    text = EMAIL_RE.sub("<email:redacted>", text)
    text = PHONE_RE.sub("<phone:redacted>", text)
    text = SECRET_RE.sub("<secret:redacted>", text)
    return text


def compact_plain_text(value: Any, limit: int = 1000) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def compact_review_text(value: Any, limit: int = 1000) -> str:
    text = redact_sensitive_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {compact_review_text(key, 80): sanitize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    if isinstance(value, str):
        return compact_review_text(value, 500)
    return value


def sanitize_review_entry(entry: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(entry)
    for key in ["reviewer_id", "project_title", "talent_label", "reviewer_notes", "next_action"]:
        if key in sanitized:
            sanitized[key] = compact_review_text(sanitized.get(key), 1000)
    for key in ["project_key", "talent_key", "match_key", "review_id", "generated_at", "feedback_status"]:
        if key in sanitized:
            sanitized[key] = compact_plain_text(sanitized.get(key), 160)
    if "mismatch_reasons" in sanitized:
        sanitized["mismatch_reasons"] = [
            compact_review_text(item, 240) for item in as_list(sanitized.get("mismatch_reasons"))
        ]
    if "corrected_fields" in sanitized:
        sanitized["corrected_fields"] = sanitize_value(sanitized.get("corrected_fields") or {})
    return sanitized


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Report not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Report must be a JSON object: {path}")
    return payload


def match_key(match_row: dict[str, Any]) -> str:
    explicit = str(match_row.get("match_key") or "").strip()
    if explicit:
        return explicit
    base = "|".join(
        [
            str(match_row.get("project_key") or ""),
            str(match_row.get("talent_key") or ""),
            str(match_row.get("score") or ""),
            ",".join(as_list(match_row.get("matched_skills"))),
            ",".join(as_list(match_row.get("missing_skills"))),
        ]
    )
    return "match_" + stable_digest(base)[:20]


def project_by_key(report: dict[str, Any], project_key: str) -> dict[str, Any]:
    for project in report.get("projects", []):
        if isinstance(project, dict) and str(project.get("project_key") or "") == project_key:
            return project
    return {}


def talent_by_key(report: dict[str, Any], talent_key: str) -> dict[str, Any]:
    for talent in report.get("talents", []):
        if isinstance(talent, dict) and str(talent.get("talent_key") or "") == talent_key:
            return talent
    return {}


def find_match(
    report: dict[str, Any],
    *,
    wanted_match_key: str = "",
    project_key: str = "",
    talent_key: str = "",
) -> dict[str, Any]:
    candidates = [row for row in report.get("matches", []) if isinstance(row, dict)]
    for row in candidates:
        if wanted_match_key and match_key(row) != wanted_match_key:
            continue
        if project_key and str(row.get("project_key") or "") != project_key:
            continue
        if talent_key and str(row.get("talent_key") or "") != talent_key:
            continue
        return row
    if not wanted_match_key and not project_key and not talent_key and candidates:
        return candidates[0]
    raise ValueError("No sales email match found for the requested review target")


def build_review_entry(
    match_row: dict[str, Any],
    *,
    feedback_status: str,
    reviewer_id: str = "",
    corrected_score: float | int | None = None,
    corrected_notes: str = "",
    corrected_fields: dict[str, Any] | None = None,
    next_action: str = "",
) -> dict[str, Any]:
    status = compact_review_text(feedback_status, 32).lower()
    if status not in VALID_FEEDBACK_STATUSES:
        raise ValueError("feedback_status must be accepted, rejected, needs_review, or corrected")
    if corrected_score is not None:
        corrected_score = max(0.0, min(float(corrected_score), 100.0))

    key = match_key(match_row)
    timestamp = utc_timestamp()
    return {
        "task_id": "T817_6",
        "review_id": "review_" + stable_digest(f"{key}:{status}:{timestamp}")[:20],
        "generated_at": timestamp,
        "model_name": REVIEW_MODEL_NAME,
        "match_key": key,
        "feedback_status": status,
        "reviewer_id": compact_review_text(reviewer_id, 120),
        "project_key": compact_review_text(match_row.get("project_key"), 80),
        "project_title": compact_review_text(match_row.get("project_title"), 160),
        "talent_key": compact_review_text(match_row.get("talent_key"), 120),
        "talent_label": compact_review_text(match_row.get("talent_label"), 120),
        "original_score": match_row.get("score"),
        "corrected_score": corrected_score,
        "matched_skills": as_list(match_row.get("matched_skills")),
        "missing_skills": as_list(match_row.get("missing_skills")),
        "mismatch_reasons": [compact_review_text(item, 240) for item in as_list(match_row.get("mismatch_reasons"))],
        "reviewer_notes": compact_review_text(corrected_notes, 1000),
        "corrected_fields": sanitize_value(corrected_fields or {}),
        "next_action": compact_review_text(next_action, 240),
        "privacy_controls": REQUIRED_REVIEW_PRIVACY_CONTROLS,
    }


def load_review_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "task_id": "T817_6",
            "generated_at": utc_timestamp(),
            "model_name": REVIEW_MODEL_NAME,
            "privacy_controls": REQUIRED_REVIEW_PRIVACY_CONTROLS,
            "review_count": 0,
            "status_counts": {},
            "reviews": [],
        }
    return load_json(path)


def build_review_report(reviews: Sequence[dict[str, Any]]) -> dict[str, Any]:
    sanitized_reviews = [sanitize_review_entry(row) for row in reviews if isinstance(row, dict)]
    counter = Counter(str(row.get("feedback_status") or "unknown") for row in sanitized_reviews)
    return {
        "task_id": "T817_6",
        "generated_at": utc_timestamp(),
        "model_name": REVIEW_MODEL_NAME,
        "privacy_controls": REQUIRED_REVIEW_PRIVACY_CONTROLS,
        "review_count": len(sanitized_reviews),
        "status_counts": dict(sorted(counter.items())),
        "improvement_loop": {
            "accepted": counter.get("accepted", 0),
            "rejected": counter.get("rejected", 0),
            "corrected": counter.get("corrected", 0),
            "needs_review": counter.get("needs_review", 0),
            "ready_for_model_prompt_review": counter.get("corrected", 0) + counter.get("rejected", 0),
        },
        "reviews": sanitized_reviews,
    }


def upsert_review_entry(report: dict[str, Any], entry: dict[str, Any], replace: bool = False) -> dict[str, Any]:
    reviews = [row for row in report.get("reviews", []) if isinstance(row, dict)]
    if replace:
        reviews = [row for row in reviews if row.get("match_key") != entry.get("match_key")]
    reviews.append(entry)
    return build_review_report(reviews)


def write_json_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_markdown_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Sales Email Human Review Log\n",
        "\n",
        f"- Task: {report.get('task_id')}\n",
        f"- Generated at: {report.get('generated_at')}\n",
        f"- Reviews: {report.get('review_count')}\n",
        f"- Status counts: {json.dumps(report.get('status_counts', {}), ensure_ascii=False)}\n",
        "- Privacy: reviewer notes are redacted; raw email bodies are not loaded.\n",
        "\n",
        "| # | Match | Project | Talent | Status | Original | Corrected | Notes | Next action |\n",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n",
    ]
    for index, row in enumerate(report.get("reviews", []), start=1):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {index} | {match_key} | {project} | {talent} | {status} | {original} | {corrected} | {notes} | {next_action} |\n".format(
                index=index,
                match_key=str(row.get("match_key", "")).replace("|", "\\|"),
                project=str(row.get("project_title", "")).replace("|", "\\|"),
                talent=str(row.get("talent_label", "")).replace("|", "\\|"),
                status=str(row.get("feedback_status", "")).replace("|", "\\|"),
                original=row.get("original_score", ""),
                corrected="" if row.get("corrected_score") is None else row.get("corrected_score"),
                notes=str(row.get("reviewer_notes", "")).replace("|", "\\|"),
                next_action=str(row.get("next_action", "")).replace("|", "\\|"),
            )
        )
    path.write_text("".join(lines), encoding="utf-8", newline="\n")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append a sanitized human review entry for T817_6.")
    parser.add_argument("--match-report", default=str(DEFAULT_MATCH_REPORT))
    parser.add_argument("--json-report", default=str(DEFAULT_JSON_REPORT))
    parser.add_argument("--markdown-report", default=str(DEFAULT_MARKDOWN_REPORT))
    parser.add_argument("--match-key", default="")
    parser.add_argument("--project-key", default="")
    parser.add_argument("--talent-key", default="")
    parser.add_argument("--feedback-status", choices=sorted(VALID_FEEDBACK_STATUSES), default="needs_review")
    parser.add_argument("--reviewer-id", default="codex-session")
    parser.add_argument("--corrected-score", type=float)
    parser.add_argument("--notes", default="")
    parser.add_argument("--next-action", default="")
    parser.add_argument("--replace", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    match_report = load_json(Path(args.match_report))
    row = find_match(
        match_report,
        wanted_match_key=args.match_key,
        project_key=args.project_key,
        talent_key=args.talent_key,
    )
    entry = build_review_entry(
        row,
        feedback_status=args.feedback_status,
        reviewer_id=args.reviewer_id,
        corrected_score=args.corrected_score,
        corrected_notes=args.notes,
        next_action=args.next_action,
    )
    current = load_review_report(Path(args.json_report))
    report = upsert_review_entry(current, entry, replace=args.replace)
    write_json_report(report, Path(args.json_report))
    write_markdown_report(report, Path(args.markdown_report))
    print(f"Recorded {entry['feedback_status']} review for {entry['match_key']}")
    print(f"Wrote {args.json_report} and {args.markdown_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
