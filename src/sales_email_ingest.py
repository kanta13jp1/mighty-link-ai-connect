"""Safe sales email intake and duplicate review helpers.

This module implements the T817_2 local PoC. It parses exported `.eml`,
`.txt`, and `.csv` sales emails, creates deterministic duplicate keys, and
emits review artifacts that avoid raw bodies and credentials.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from pathlib import Path
from typing import Iterable, Sequence


SUPPORTED_EXTENSIONS = {".eml", ".txt", ".csv"}
DEFAULT_JSON_REPORT = Path("exports") / "sales_email_ingest_review.json"
DEFAULT_MARKDOWN_REPORT = Path("exports") / "sales_email_ingest_review.md"
SUBJECT_PREFIX_RE = re.compile(r"^\s*(?:re|fw|fwd|返信|転送)\s*[:：]\s*", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(
    r"(?<!\d)(?:\+81[-\s]?)?0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4}(?!\d)"
)
SECRET_LIKE_RE = re.compile(
    r"(?:Bearer\s+[A-Za-z0-9._=-]{8,}|"
    r"(?:api[_-]?key|token|password|secret)\s*[:=]\s*[A-Za-z0-9._=-]{6,})",
    re.IGNORECASE,
)
HTML_TAG_RE = re.compile(r"<[^>]+>")
CSV_ALIASES = {
    "sender": {
        "from",
        "sender",
        "mail_from",
        "\u5dee\u51fa\u4eba",
        "\u9001\u4fe1\u8005",
    },
    "subject": {"subject", "title", "\u4ef6\u540d", "\u30bf\u30a4\u30c8\u30eb"},
    "body": {"body", "text", "content", "message", "\u672c\u6587", "\u30e1\u30c3\u30bb\u30fc\u30b8"},
    "received_at": {
        "date",
        "received_at",
        "timestamp",
        "\u53d7\u4fe1\u65e5\u6642",
        "\u65e5\u6642",
    },
    "message_id": {"message_id", "message-id", "id", "\u30e1\u30c3\u30bb\u30fc\u30b8id"},
}


@dataclass(frozen=True)
class RawSalesEmail:
    source_path: str
    source_type: str
    sender: str
    subject: str
    body: str
    received_at: str = ""
    message_id: str = ""


@dataclass(frozen=True)
class SanitizedSalesEmail:
    source_path: str
    source_type: str
    duplicate: bool
    duplicate_of: str
    dedupe_key: str
    sender_hash: str
    sender_domain: str
    message_id_hash: str
    normalized_subject: str
    body_hash: str
    received_at: str
    body_excerpt: str


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def collapse_whitespace(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value or "").strip()


def normalize_subject(subject: str) -> str:
    value = collapse_whitespace(subject)
    while SUBJECT_PREFIX_RE.match(value):
        value = SUBJECT_PREFIX_RE.sub("", value, count=1)
    return value


def canonical_body(body: str) -> str:
    lines: list[str] = []
    for raw_line in (body or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            continue
        if line.startswith(("-----Original Message-----", "----- Forwarded message -----")):
            break
        if line in {"--", "----"}:
            break
        lines.append(line)
    return collapse_whitespace(" ".join(lines))


def redact_sensitive_text(value: str) -> str:
    redacted = EMAIL_RE.sub("<email:redacted>", value or "")
    redacted = PHONE_RE.sub("<phone:redacted>", redacted)
    redacted = SECRET_LIKE_RE.sub("<secret:redacted>", redacted)
    return redacted


def safe_excerpt(value: str, max_chars: int = 240) -> str:
    redacted = collapse_whitespace(redact_sensitive_text(value))
    if len(redacted) <= max_chars:
        return redacted
    return redacted[: max_chars - 3].rstrip() + "..."


def sender_domain(sender: str) -> str:
    _, addr = parseaddr(sender or "")
    if "@" not in addr:
        return ""
    return addr.rsplit("@", 1)[-1].lower()


def dedupe_key(email: RawSalesEmail) -> str:
    parts = [
        parseaddr(email.sender or "")[1].lower() or collapse_whitespace(email.sender).lower(),
        normalize_subject(email.subject).lower(),
        sha256_hex(canonical_body(email.body)),
    ]
    return sha256_hex("\n".join(parts))


def strip_html_to_text(value: str) -> str:
    return collapse_whitespace(html.unescape(HTML_TAG_RE.sub(" ", value or "")))


def _message_body(message) -> str:
    plain_parts: list[str] = []
    html_parts: list[str] = []
    for part in message.walk() if message.is_multipart() else [message]:
        disposition = (part.get_content_disposition() or "").lower()
        if disposition == "attachment":
            continue
        content_type = part.get_content_type()
        try:
            content = part.get_content()
        except (LookupError, UnicodeDecodeError):
            payload = part.get_payload(decode=True) or b""
            content = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        if content_type == "text/plain":
            plain_parts.append(str(content))
        elif content_type == "text/html":
            html_parts.append(strip_html_to_text(str(content)))
    return "\n".join(plain_parts or html_parts)


def parse_eml(path: Path) -> list[RawSalesEmail]:
    message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    return [
        RawSalesEmail(
            source_path=path.as_posix(),
            source_type="eml",
            sender=str(message.get("From", "")),
            subject=str(message.get("Subject", path.stem)),
            received_at=str(message.get("Date", "")),
            message_id=str(message.get("Message-ID", "")),
            body=_message_body(message),
        )
    ]


def parse_txt(path: Path) -> list[RawSalesEmail]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    header_text, separator, body = text.partition("\n\n")
    headers: dict[str, str] = {}
    if separator:
        for line in header_text.splitlines():
            key, sep, value = line.partition(":")
            if sep and key.strip().lower() in {"from", "subject", "date", "message-id", "message_id"}:
                headers[key.strip().lower()] = value.strip()
            else:
                body = text
                headers = {}
                break
    else:
        body = text
    return [
        RawSalesEmail(
            source_path=path.as_posix(),
            source_type="txt",
            sender=headers.get("from", ""),
            subject=headers.get("subject", path.stem),
            received_at=headers.get("date", ""),
            message_id=headers.get("message-id", headers.get("message_id", "")),
            body=body,
        )
    ]


def _normalized_csv_row(row: dict[str, str]) -> dict[str, str]:
    normalized = {collapse_whitespace(key).lower(): value for key, value in row.items() if key is not None}
    output: dict[str, str] = {}
    for canonical_name, aliases in CSV_ALIASES.items():
        for alias in aliases:
            if alias.lower() in normalized:
                output[canonical_name] = normalized[alias.lower()]
                break
    return output


def parse_csv_file(path: Path) -> list[RawSalesEmail]:
    emails: list[RawSalesEmail] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader, start=2):
            normalized = _normalized_csv_row(row)
            if not any(normalized.get(field) for field in ("sender", "subject", "body")):
                continue
            emails.append(
                RawSalesEmail(
                    source_path=f"{path.as_posix()}#row{index}",
                    source_type="csv",
                    sender=normalized.get("sender", ""),
                    subject=normalized.get("subject", f"{path.stem} row {index}"),
                    received_at=normalized.get("received_at", ""),
                    message_id=normalized.get("message_id", ""),
                    body=normalized.get("body", ""),
                )
            )
    return emails


def discover_input_files(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(
                child
                for child in sorted(path.rglob("*"))
                if child.is_file() and child.suffix.lower() in SUPPORTED_EXTENSIONS
            )
        elif path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)
        else:
            raise FileNotFoundError(f"Unsupported or missing input path: {path}")
    return sorted(files)


def parse_input_file(path: Path) -> list[RawSalesEmail]:
    suffix = path.suffix.lower()
    if suffix == ".eml":
        return parse_eml(path)
    if suffix == ".txt":
        return parse_txt(path)
    if suffix == ".csv":
        return parse_csv_file(path)
    raise ValueError(f"Unsupported input extension: {path}")


def load_sales_emails(paths: Sequence[Path]) -> list[RawSalesEmail]:
    emails: list[RawSalesEmail] = []
    for path in discover_input_files(paths):
        emails.extend(parse_input_file(path))
    return emails


def sanitize_email(email: RawSalesEmail, duplicate: bool, duplicate_of: str) -> SanitizedSalesEmail:
    normalized_subject = safe_excerpt(normalize_subject(email.subject), max_chars=160)
    body = canonical_body(email.body)
    message_id = collapse_whitespace(email.message_id)
    return SanitizedSalesEmail(
        source_path=email.source_path,
        source_type=email.source_type,
        duplicate=duplicate,
        duplicate_of=duplicate_of,
        dedupe_key=dedupe_key(email),
        sender_hash=sha256_hex(parseaddr(email.sender or "")[1].lower() or email.sender.lower()),
        sender_domain=sender_domain(email.sender),
        message_id_hash=sha256_hex(message_id) if message_id else "",
        normalized_subject=normalized_subject,
        body_hash=sha256_hex(body),
        received_at=safe_excerpt(email.received_at, max_chars=80),
        body_excerpt=safe_excerpt(body, max_chars=240),
    )


def build_ingest_report(emails: Sequence[RawSalesEmail]) -> dict[str, object]:
    seen: dict[str, str] = {}
    sanitized: list[SanitizedSalesEmail] = []
    for email in emails:
        key = dedupe_key(email)
        duplicate_of = seen.get(key, "")
        if not duplicate_of:
            seen[key] = email.source_path
        sanitized.append(sanitize_email(email, duplicate=bool(duplicate_of), duplicate_of=duplicate_of))

    duplicate_groups: dict[str, list[str]] = {}
    for item in sanitized:
        if item.duplicate:
            duplicate_groups.setdefault(item.dedupe_key, [item.duplicate_of]).append(item.source_path)

    return {
        "task_id": "T817_2",
        "generated_at": utc_timestamp(),
        "input_count": len(emails),
        "unique_count": len(seen),
        "duplicate_count": len(emails) - len(seen),
        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
        "privacy_controls": [
            "raw_email_body_not_written",
            "sender_hash_used_for_identity",
            "email_phone_secret_patterns_redacted_from_excerpts",
            "dedupe_uses_sender_subject_body_hash",
        ],
        "duplicate_groups": duplicate_groups,
        "messages": [asdict(item) for item in sanitized],
    }


def write_json_report(report: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_markdown_report(report: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    messages = report.get("messages", [])
    lines = [
        "# Sales Email Intake PoC Review\n",
        "\n",
        f"- Task: {report.get('task_id')}\n",
        f"- Generated at: {report.get('generated_at')}\n",
        f"- Input messages: {report.get('input_count')}\n",
        f"- Unique messages: {report.get('unique_count')}\n",
        f"- Duplicate messages: {report.get('duplicate_count')}\n",
        "- Privacy: raw bodies and credentials are not written; excerpts are redacted.\n",
        "\n",
        "| # | Source | Type | Duplicate | Sender domain | Subject | Body hash | Excerpt |\n",
        "| --- | --- | --- | --- | --- | --- | --- | --- |\n",
    ]
    for index, item in enumerate(messages, start=1):
        if not isinstance(item, dict):
            continue
        duplicate = "yes" if item.get("duplicate") else "no"
        lines.append(
            "| {index} | `{source}` | {source_type} | {duplicate} | {domain} | {subject} | `{body_hash}` | {excerpt} |\n".format(
                index=index,
                source=str(item.get("source_path", "")).replace("|", "\\|"),
                source_type=str(item.get("source_type", "")).replace("|", "\\|"),
                duplicate=duplicate,
                domain=str(item.get("sender_domain", "")).replace("|", "\\|"),
                subject=str(item.get("normalized_subject", "")).replace("|", "\\|"),
                body_hash=str(item.get("body_hash", ""))[:12],
                excerpt=str(item.get("body_excerpt", "")).replace("|", "\\|"),
            )
        )
    path.write_text("".join(lines), encoding="utf-8", newline="\n")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safely ingest exported sales emails for T817_2.")
    parser.add_argument(
        "--input",
        action="append",
        required=False,
        help="Input file or directory. Supported: .eml, .txt, .csv. Repeatable.",
    )
    parser.add_argument(
        "--pop3",
        action="store_true",
        help="Fetch emails from configured POP3 server.",
    )
    parser.add_argument("--json-report", default=str(DEFAULT_JSON_REPORT))
    parser.add_argument("--markdown-report", default=str(DEFAULT_MARKDOWN_REPORT))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    
    if not args.input and not args.pop3:
        parser.error("At least one of --input or --pop3 must be specified.")

    emails: list[RawSalesEmail] = []

    if args.input:
        input_paths = [Path(value) for value in args.input]
        emails.extend(load_sales_emails(input_paths))

    if args.pop3:
        # Import inside function to avoid circular imports with sales_email_pop3
        from sales_email_pop3 import fetch_pop3_emails
        emails.extend(fetch_pop3_emails())

    report = build_ingest_report(emails)
    write_json_report(report, Path(args.json_report))
    write_markdown_report(report, Path(args.markdown_report))
    print(
        "Parsed {input_count} messages, {unique_count} unique, {duplicate_count} duplicates".format(
            input_count=report["input_count"],
            unique_count=report["unique_count"],
            duplicate_count=report["duplicate_count"],
        )
    )
    print(f"Wrote {args.json_report} and {args.markdown_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

