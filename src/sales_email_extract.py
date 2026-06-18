"""Deterministic sales email requirement extraction pipeline for T817_4.

The module turns safely parsed sales emails into DB-ready project, talent, and
skill-tag records. It intentionally avoids storing raw email bodies or
credentials in generated review artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from sales_email_ingest import (
    RawSalesEmail,
    canonical_body,
    collapse_whitespace,
    dedupe_key,
    load_sales_emails,
    normalize_subject,
    safe_excerpt,
    sender_domain,
    sha256_hex,
    utc_timestamp,
)


DEFAULT_JSON_REPORT = Path("exports") / "sales_email_extraction_review.json"
DEFAULT_MARKDOWN_REPORT = Path("exports") / "sales_email_extraction_review.md"
DETERMINISTIC_MODEL_NAME = "deterministic-sales-email-extractor-v1"


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    category: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class SkillTag:
    skill_name: str
    skill_category: str
    importance: str
    confidence: float
    evidence_excerpt: str


@dataclass(frozen=True)
class ProjectRequirement:
    title: str
    summary: str
    required_skills: list[str]
    nice_to_have_skills: list[str]
    skill_categories: dict[str, list[str]]
    rate_min: int | None
    rate_max: int | None
    rate_unit: str
    location: str
    remote_type: str
    start_date_text: str
    duration_text: str
    commercial_flow: str
    restrictions: str
    evidence_excerpt: str
    confidence: float
    review_status: str = "pending"


@dataclass(frozen=True)
class TalentProfile:
    anonymized_talent_key: str
    summary: str
    skills: list[str]
    skill_categories: dict[str, list[str]]
    experience_years: float | None
    desired_rate_min: int | None
    desired_rate_max: int | None
    desired_location: str
    remote_preference: str
    availability_text: str
    evidence_excerpt: str
    confidence: float
    review_status: str = "pending"


@dataclass(frozen=True)
class EmailExtraction:
    source_path: str
    source_type: str
    dedupe_key: str
    sender_domain: str
    normalized_subject: str
    email_kind: str
    model_name: str
    fallback_used: bool
    project_requirement: ProjectRequirement | None
    talent_profile: TalentProfile | None
    skill_tags: list[SkillTag]


SKILLS: tuple[SkillDefinition, ...] = (
    SkillDefinition("Java", "language", ("java",)),
    SkillDefinition("Python", "language", ("python",)),
    SkillDefinition("JavaScript", "language", ("javascript", "js")),
    SkillDefinition("TypeScript", "language", ("typescript", "ts")),
    SkillDefinition("PHP", "language", ("php",)),
    SkillDefinition("Ruby", "language", ("ruby",)),
    SkillDefinition("Go", "language", ("golang", "go言語")),
    SkillDefinition("C#", "language", ("c#", "csharp")),
    SkillDefinition("Kotlin", "language", ("kotlin",)),
    SkillDefinition("Swift", "language", ("swift",)),
    SkillDefinition("COBOL", "language", ("cobol",)),
    SkillDefinition("SQL", "database", ("sql",)),
    SkillDefinition("Oracle", "database", ("oracle",)),
    SkillDefinition("PostgreSQL", "database", ("postgresql", "postgres")),
    SkillDefinition("MySQL", "database", ("mysql",)),
    SkillDefinition("SQL Server", "database", ("sql server", "mssql")),
    SkillDefinition("MongoDB", "database", ("mongodb",)),
    SkillDefinition("Redis", "database", ("redis",)),
    SkillDefinition("AWS", "cloud", ("aws", "amazon web services")),
    SkillDefinition("Azure", "cloud", ("azure",)),
    SkillDefinition("GCP", "cloud", ("gcp", "google cloud")),
    SkillDefinition("Firebase", "cloud", ("firebase",)),
    SkillDefinition("Supabase", "cloud", ("supabase",)),
    SkillDefinition("React", "framework", ("react",)),
    SkillDefinition("Vue", "framework", ("vue", "vue.js")),
    SkillDefinition("Angular", "framework", ("angular",)),
    SkillDefinition("Spring", "framework", ("spring", "spring boot")),
    SkillDefinition("FastAPI", "framework", ("fastapi",)),
    SkillDefinition("Django", "framework", ("django",)),
    SkillDefinition("Docker", "tool", ("docker",)),
    SkillDefinition("Kubernetes", "tool", ("kubernetes", "k8s")),
    SkillDefinition("Linux", "os", ("linux",)),
    SkillDefinition("GitHub Actions", "tool", ("github actions",)),
    SkillDefinition("PM", "role", ("pm", "プロジェクトマネージャ")),
    SkillDefinition("PL", "role", ("pl", "プロジェクトリーダ")),
    SkillDefinition("SE", "role", ("se", "システムエンジニア")),
    SkillDefinition("要件定義", "process", ("要件定義",)),
    SkillDefinition("基本設計", "process", ("基本設計",)),
    SkillDefinition("詳細設計", "process", ("詳細設計",)),
    SkillDefinition("テスト", "process", ("テスト", "試験")),
    SkillDefinition("運用保守", "process", ("運用保守", "保守運用")),
)

PROJECT_MARKERS = (
    "案件",
    "募集",
    "必須",
    "尚可",
    "勤務地",
    "単価",
    "精算",
    "リモート",
    "面談",
    "商流",
    "project",
    "required",
    "must",
    "rate",
    "start",
)
TALENT_MARKERS = (
    "要員提案",
    "要員情報",
    "人材",
    "経歴",
    "スキルシート",
    "稼働可能",
    "希望単価",
    "候補者",
    "engineer available",
    "available from",
    "candidate profile",
    "candidate available",
    "profile",
    "resume",
)
TALENT_REQUEST_MARKERS = ("要員募集", "人材募集", "候補者募集", "candidate wanted", "looking for talent")
NICE_MARKERS = ("尚可", "歓迎", "あれば尚可", "nice", "preferred")
REQUIRED_MARKERS = ("必須", "must", "required", "必要", "経験")
LOCATIONS = (
    "東京",
    "大阪",
    "名古屋",
    "福岡",
    "札幌",
    "横浜",
    "神奈川",
    "千葉",
    "埼玉",
    "品川",
    "渋谷",
    "新宿",
    "豊洲",
    "大手町",
)
REMOTE_RE = re.compile(r"(フルリモート|完全リモート|リモート可|在宅|リモート|remote|work from home)", re.IGNORECASE)
HYBRID_RE = re.compile(r"(リモート併用|一部リモート|ハイブリッド|hybrid|週\s*\d\s*日\s*出社)", re.IGNORECASE)
ONSITE_RE = re.compile(r"(常駐|出社必須|オンサイト|onsite|on-site)", re.IGNORECASE)
RATE_RANGE_RE = re.compile(r"(?:(?:単価|希望単価|月額)\s*[:：]?\s*)?(\d{2,3})\s*(?:万)?\s*[〜~\-ー－]\s*(\d{2,3})\s*万")
RATE_SINGLE_RE = re.compile(r"(?:(?:単価|希望単価|月額)\s*[:：]?\s*)?(\d{2,3})\s*万")
EXPERIENCE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:年以上|年経験|年)")
START_RE = re.compile(r"(即日|ASAP|\d{1,2}月(?:\d{1,2}日)?|20\d{2}[-/]\d{1,2}(?:[-/]\d{1,2})?)\s*(?:開始|参画|稼働)?", re.IGNORECASE)
DURATION_RE = re.compile(r"(長期|短期|\d+\s*(?:ヶ月|か月)|半年|1年)")


def split_segments(text: str) -> list[str]:
    prepared = re.sub(
        r"\s*(案件名|必須|尚可|歓迎|単価|希望単価|勤務地|稼働|商流|面談|制限|条件|スキル)\s*[:：]",
        r"\n\1:",
        text,
    )
    parts = re.split(r"[\n。!?！？;；]+", prepared)
    return [collapse_whitespace(part) for part in parts if collapse_whitespace(part)]


def contains_alias(text: str, alias: str) -> bool:
    haystack = text.lower()
    needle = alias.lower()
    if re.fullmatch(r"[a-z0-9+#.\s]+", needle):
        return re.search(rf"(?<![a-z0-9+#.]){re.escape(needle)}(?![a-z0-9+#.])", haystack) is not None
    return needle in haystack


def segment_importance(segment: str, default: str) -> str:
    lowered = segment.lower()
    if any(marker.lower() in lowered for marker in NICE_MARKERS):
        return "nice_to_have"
    if any(marker.lower() in lowered for marker in REQUIRED_MARKERS):
        return "required"
    return default


def extract_skill_tags(text: str, *, default_importance: str) -> list[SkillTag]:
    segments = split_segments(text)
    matches: dict[tuple[str, str], SkillTag] = {}
    for definition in SKILLS:
        for segment in segments:
            if not any(contains_alias(segment, alias) for alias in definition.aliases):
                continue
            importance = segment_importance(segment, default_importance)
            confidence = 0.86 if importance in {"required", "nice_to_have", "experience"} else 0.72
            key = (definition.name, importance)
            if key not in matches:
                matches[key] = SkillTag(
                    skill_name=definition.name,
                    skill_category=definition.category,
                    importance=importance,
                    confidence=confidence,
                    evidence_excerpt=safe_excerpt(segment, max_chars=180),
                )
            break
    return sorted(matches.values(), key=lambda item: (item.skill_category, item.skill_name, item.importance))


def grouped_skills(skill_tags: Iterable[SkillTag]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for tag in skill_tags:
        grouped.setdefault(tag.skill_category, [])
        if tag.skill_name not in grouped[tag.skill_category]:
            grouped[tag.skill_category].append(tag.skill_name)
    return {key: sorted(values) for key, values in sorted(grouped.items())}


def find_rate(text: str) -> tuple[int | None, int | None, str]:
    range_match = RATE_RANGE_RE.search(text)
    if range_match:
        low, high = sorted((int(range_match.group(1)), int(range_match.group(2))))
        return low, high, "万円/月"
    single_match = RATE_SINGLE_RE.search(text)
    if single_match:
        value = int(single_match.group(1))
        return value, value, "万円/月"
    return None, None, ""


def find_location(text: str) -> str:
    for location in LOCATIONS:
        if location in text:
            return location
    return ""


def find_remote_type(text: str) -> str:
    if HYBRID_RE.search(text):
        return "hybrid"
    if REMOTE_RE.search(text):
        return "remote"
    if ONSITE_RE.search(text):
        return "onsite"
    return "unknown"


def first_matching_segment(text: str, markers: Sequence[str]) -> str:
    for segment in split_segments(text):
        if any(marker.lower() in segment.lower() for marker in markers):
            return safe_excerpt(segment, max_chars=220)
    return ""


def find_start_date(text: str) -> str:
    match = START_RE.search(text)
    return safe_excerpt(match.group(0), max_chars=80) if match else ""


def find_duration(text: str) -> str:
    match = DURATION_RE.search(text)
    return safe_excerpt(match.group(0), max_chars=80) if match else ""


def find_experience_years(text: str) -> float | None:
    values = [float(match.group(1)) for match in EXPERIENCE_RE.finditer(text)]
    return max(values) if values else None


def classify_email(text: str) -> str:
    lowered = text.lower()
    if any(marker.lower() in lowered for marker in TALENT_REQUEST_MARKERS):
        return "talent_request"
    talent_score = sum(1 for marker in TALENT_MARKERS if marker.lower() in lowered)
    project_score = sum(1 for marker in PROJECT_MARKERS if marker.lower() in lowered)
    if talent_score > project_score and talent_score > 0:
        return "talent_proposal"
    if project_score > 0:
        return "project_intro"
    if talent_score > 0:
        return "talent_proposal"
    return "other"


def confidence_score(skill_count: int, *signals: object) -> float:
    score = 0.45 + min(skill_count, 5) * 0.06
    score += sum(0.05 for signal in signals if signal)
    return round(min(score, 0.95), 2)


def build_project_requirement(
    email: RawSalesEmail, text: str, skill_tags: list[SkillTag], *, email_kind: str
) -> ProjectRequirement | None:
    project_skill_tags = [tag for tag in skill_tags if tag.importance in {"required", "nice_to_have", "unknown"}]
    explicit_project_marker = any(marker.lower() in text.lower() for marker in PROJECT_MARKERS)
    if email_kind == "talent_proposal" and not explicit_project_marker:
        return None
    if not project_skill_tags and not explicit_project_marker:
        return None
    rate_min, rate_max, rate_unit = find_rate(text)
    required_skills = sorted({tag.skill_name for tag in project_skill_tags if tag.importance != "nice_to_have"})
    nice_to_have_skills = sorted({tag.skill_name for tag in project_skill_tags if tag.importance == "nice_to_have"})
    title = safe_excerpt(normalize_subject(email.subject) or "Untitled sales project", max_chars=140)
    location = find_location(text)
    remote_type = find_remote_type(text)
    start_date_text = find_start_date(text)
    duration_text = find_duration(text)
    commercial_flow = first_matching_segment(text, ("商流", "エンド", "元請", "一次", "二次"))
    restrictions = first_matching_segment(text, ("年齢", "国籍", "外国籍", "面談", "精算", "支払"))
    evidence = (
        first_matching_segment(text, ("必須", "尚可", "歓迎"))
        or first_matching_segment(text, tuple(required_skills + nice_to_have_skills))
        or safe_excerpt(text, 220)
    )
    return ProjectRequirement(
        title=title,
        summary=safe_excerpt(text, max_chars=300),
        required_skills=required_skills,
        nice_to_have_skills=nice_to_have_skills,
        skill_categories=grouped_skills(project_skill_tags),
        rate_min=rate_min,
        rate_max=rate_max,
        rate_unit=rate_unit,
        location=location,
        remote_type=remote_type,
        start_date_text=start_date_text,
        duration_text=duration_text,
        commercial_flow=commercial_flow,
        restrictions=restrictions,
        evidence_excerpt=evidence,
        confidence=confidence_score(len(project_skill_tags), rate_min, location, remote_type != "unknown", evidence),
    )


def build_talent_profile(email: RawSalesEmail, text: str, skill_tags: list[SkillTag]) -> TalentProfile | None:
    talent_marked = any(marker in text for marker in TALENT_MARKERS)
    if not talent_marked:
        return None
    talent_skill_tags = [
        SkillTag(
            skill_name=tag.skill_name,
            skill_category=tag.skill_category,
            importance="experience" if tag.importance == "unknown" else tag.importance,
            confidence=tag.confidence,
            evidence_excerpt=tag.evidence_excerpt,
        )
        for tag in skill_tags
    ]
    rate_min, rate_max, _ = find_rate(text)
    availability_text = first_matching_segment(text, ("稼働", "参画", "開始", "即日", "ASAP"))
    evidence = first_matching_segment(text, tuple(tag.skill_name for tag in talent_skill_tags)) or safe_excerpt(text, 220)
    return TalentProfile(
        anonymized_talent_key="talent_" + sha256_hex(dedupe_key(email) + ":talent")[:16],
        summary=safe_excerpt(text, max_chars=300),
        skills=sorted({tag.skill_name for tag in talent_skill_tags}),
        skill_categories=grouped_skills(talent_skill_tags),
        experience_years=find_experience_years(text),
        desired_rate_min=rate_min,
        desired_rate_max=rate_max,
        desired_location=find_location(text),
        remote_preference=find_remote_type(text),
        availability_text=availability_text,
        evidence_excerpt=evidence,
        confidence=confidence_score(len(talent_skill_tags), rate_min, availability_text, evidence),
    )


def extract_email(email: RawSalesEmail) -> EmailExtraction:
    body = canonical_body(email.body)
    text = collapse_whitespace(" ".join([normalize_subject(email.subject), body]))
    email_kind = classify_email(text)
    default_importance = "experience" if email_kind == "talent_proposal" else "unknown"
    skill_tags = extract_skill_tags(text, default_importance=default_importance)
    project_requirement = build_project_requirement(email, text, skill_tags, email_kind=email_kind)
    talent_profile = build_talent_profile(email, text, skill_tags)
    return EmailExtraction(
        source_path=email.source_path,
        source_type=email.source_type,
        dedupe_key=dedupe_key(email),
        sender_domain=sender_domain(email.sender),
        normalized_subject=safe_excerpt(normalize_subject(email.subject), max_chars=160),
        email_kind=email_kind,
        model_name=DETERMINISTIC_MODEL_NAME,
        fallback_used=True,
        project_requirement=project_requirement,
        talent_profile=talent_profile,
        skill_tags=skill_tags,
    )


def build_extraction_report(emails: Sequence[RawSalesEmail]) -> dict[str, object]:
    extractions = [extract_email(email) for email in emails]
    project_count = sum(1 for item in extractions if item.project_requirement is not None)
    talent_count = sum(1 for item in extractions if item.talent_profile is not None)
    skill_tag_count = sum(len(item.skill_tags) for item in extractions)
    return {
        "task_id": "T817_4",
        "generated_at": utc_timestamp(),
        "model_name": DETERMINISTIC_MODEL_NAME,
        "fallback_used": True,
        "input_count": len(emails),
        "project_requirement_count": project_count,
        "talent_profile_count": talent_count,
        "skill_tag_count": skill_tag_count,
        "privacy_controls": [
            "raw_email_body_not_written",
            "email_phone_secret_patterns_redacted_from_evidence",
            "sender_hash_or_domain_only",
            "talent_identity_anonymized",
            "human_review_required_before_confirmed_status",
        ],
        "extractions": [asdict(item) for item in extractions],
    }


def write_json_report(report: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_markdown_report(report: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Sales Email Extraction Review\n",
        "\n",
        f"- Task: {report.get('task_id')}\n",
        f"- Generated at: {report.get('generated_at')}\n",
        f"- Model: {report.get('model_name')}\n",
        f"- Fallback used: {report.get('fallback_used')}\n",
        f"- Input messages: {report.get('input_count')}\n",
        f"- Project requirements: {report.get('project_requirement_count')}\n",
        f"- Talent profiles: {report.get('talent_profile_count')}\n",
        f"- Skill tags: {report.get('skill_tag_count')}\n",
        "- Privacy: raw bodies and credentials are not written; evidence is redacted.\n",
        "\n",
        "| # | Source | Kind | Subject | Required skills | Nice skills | Talent skills | Rate | Remote | Evidence |\n",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n",
    ]
    for index, item in enumerate(report.get("extractions", []), start=1):
        if not isinstance(item, dict):
            continue
        project = item.get("project_requirement") or {}
        talent = item.get("talent_profile") or {}
        required = ", ".join(project.get("required_skills") or [])
        nice = ", ".join(project.get("nice_to_have_skills") or [])
        talent_skills = ", ".join(talent.get("skills") or [])
        rate_min = project.get("rate_min") or talent.get("desired_rate_min") or ""
        rate_max = project.get("rate_max") or talent.get("desired_rate_max") or ""
        rate = f"{rate_min}-{rate_max}万円/月" if rate_min and rate_max else ""
        remote = project.get("remote_type") or talent.get("remote_preference") or ""
        evidence = project.get("evidence_excerpt") or talent.get("evidence_excerpt") or ""
        lines.append(
            "| {index} | `{source}` | {kind} | {subject} | {required} | {nice} | {talent_skills} | {rate} | {remote} | {evidence} |\n".format(
                index=index,
                source=str(item.get("source_path", "")).replace("|", "\\|"),
                kind=str(item.get("email_kind", "")).replace("|", "\\|"),
                subject=str(item.get("normalized_subject", "")).replace("|", "\\|"),
                required=required.replace("|", "\\|"),
                nice=nice.replace("|", "\\|"),
                talent_skills=talent_skills.replace("|", "\\|"),
                rate=rate,
                remote=str(remote).replace("|", "\\|"),
                evidence=str(evidence).replace("|", "\\|"),
            )
        )
    path.write_text("".join(lines), encoding="utf-8", newline="\n")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract structured sales email matching records for T817_4.")
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        help="Input file or directory. Supported: .eml, .txt, .csv. Repeatable.",
    )
    parser.add_argument("--json-report", default=str(DEFAULT_JSON_REPORT))
    parser.add_argument("--markdown-report", default=str(DEFAULT_MARKDOWN_REPORT))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    emails = load_sales_emails([Path(value) for value in args.input])
    report = build_extraction_report(emails)
    write_json_report(report, Path(args.json_report))
    write_markdown_report(report, Path(args.markdown_report))
    print(
        "Extracted {project_count} project requirements, {talent_count} talent profiles, {skill_count} skill tags".format(
            project_count=report["project_requirement_count"],
            talent_count=report["talent_profile_count"],
            skill_count=report["skill_tag_count"],
        )
    )
    print(f"Wrote {args.json_report} and {args.markdown_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
