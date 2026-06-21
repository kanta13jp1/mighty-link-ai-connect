#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Shared helpers for T808 monthly quality report delivery.

The module keeps the monthly delivery paths small and explicit:

- Google Sheets: upsert one row into the ``月次KPIサマリー`` tab.
- Notion: create a concise monthly report page from the generated Markdown.
- Slack: send a compact monthly report notification.

Secrets are read only from environment variables or local credential files and
are never written to generated artifacts.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TASK_ID = "T808"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path("data")
DOCS_DIR = Path("docs")
EXPORTS_DIR = Path("exports")
DEFAULT_SPREADSHEET_ID = "1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8"
EXPECTED_GOOGLE_ACCOUNT = "k-umezawa@ml-mightylink.com"
KPI_SHEET_NAME = "月次KPIサマリー"
NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_VERSION = "2022-06-28"
HTTP_TIMEOUT_SECONDS = 20

KPI_HEADERS = [
    "月",
    "稼働率(%)",
    "P95レスポンス(s)",
    "5xxエラー率(%)",
    "診断件数",
    "精度スコア(%)",
    "Gemini費用($)",
    "Firebase費用($)",
    "Supabase費用($)",
    "合計費用($)",
    "WBS完了率(%)",
    "テスト合格率(%)",
    "課題数",
    "セキュリティ検出数",
    "レポートファイル",
    "レポート種別",
    "最終同期日時",
]


class CredentialMissing(RuntimeError):
    """Raised when a live delivery path is requested without credentials."""


class DeliveryError(RuntimeError):
    """Raised when an external delivery API returns an error."""


@dataclass(frozen=True)
class DeliveryOutputs:
    kpi_json: Path
    notion_payload: Path
    notion_status: Path
    slack_payload: Path
    slack_status: Path


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today_from_arg(value: str | None) -> dt.date:
    return dt.date.fromisoformat(value) if value else dt.date.today()


def parse_month(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d{4})-(\d{2})", value.strip())
    if not match:
        raise ValueError("month must be YYYY-MM")
    year, month = int(match.group(1)), int(match.group(2))
    if month < 1 or month > 12:
        raise ValueError("month must be between 01 and 12")
    return year, month


def default_target_month(today: dt.date | None = None) -> str:
    """Return the last completed calendar month for scheduled delivery."""

    day = today or dt.date.today()
    first_this_month = day.replace(day=1)
    last_prev_month = first_this_month - dt.timedelta(days=1)
    return last_prev_month.strftime("%Y-%m")


def month_bounds(month: str) -> tuple[dt.date, dt.date]:
    year, mon = parse_month(month)
    first = dt.date(year, mon, 1)
    next_first = dt.date(year + 1, 1, 1) if mon == 12 else dt.date(year, mon + 1, 1)
    return first, next_first


def report_kind(month: str, today: dt.date) -> str:
    return "final" if today >= month_bounds(month)[1] else "interim"


def month_label(month: str) -> str:
    year, mon = parse_month(month)
    return f"{year}年{mon:02d}月"


def assert_child_path(root: Path, child: Path) -> None:
    root_resolved = root.resolve()
    child_resolved = child.resolve()
    if child_resolved == root_resolved or root_resolved not in child_resolved.parents:
        raise ValueError(f"Refusing to operate outside project root: {child}")


def resolve_project_path(root: Path, path: Path) -> Path:
    resolved = path if path.is_absolute() else root / path
    assert_child_path(root, resolved)
    return resolved


def display_path(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace(os.sep, "/")
    except ValueError:
        return str(path.resolve())


def read_tsv_dicts(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [dict(row) for row in reader if row and any((value or "").strip() for value in row.values())]


def parse_date(value: str) -> dt.date | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M"):
        try:
            return dt.datetime.strptime(value[:16] if " " in value else value[:10], fmt).date()
        except ValueError:
            continue
    return None


def in_month(value: str, month: str) -> bool:
    parsed = parse_date(value)
    return parsed is not None and parsed.strftime("%Y-%m") == month


def number_from_text(value: str) -> float | None:
    text = (value or "").strip().replace(",", "")
    if not text or text in {"-", "—", "未計測", "unknown"}:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else None


def format_metric(value: float | int | None, decimals: int = 1) -> str:
    if value is None:
        return "未計測"
    if isinstance(value, int) or float(value).is_integer():
        return str(int(value))
    return f"{float(value):.{decimals}f}"


def ensure_monthly_report(root: Path, month: str, today: dt.date, force: bool = False) -> Path:
    report_path = root / DOCS_DIR / f"MONTHLY_REPORT_{month}.md"
    if report_path.exists() and not force:
        return report_path

    scripts_dir = root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import generate_monthly_quality_report as monthly_report  # pylint: disable=import-error,import-outside-toplevel

    content = monthly_report.render(month, today)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8", newline="\n")
    return report_path


def wbs_summary(root: Path, month: str, today: dt.date) -> dict[str, Any]:
    rows = read_tsv_dicts(root / DATA_DIR / "WBS.tsv")
    done_rows = [row for row in rows if (row.get("ステータス") or "").strip() == "完了"]
    done_this_month = [row for row in done_rows if in_month(row.get("終了予定日", ""), month)]
    delayed = [
        row
        for row in rows
        if (row.get("ステータス") or "").strip() != "完了"
        and (due := parse_date(row.get("終了予定日", ""))) is not None
        and due < today
    ]
    return {
        "total": len(rows),
        "done_total": len(done_rows),
        "done_this_month": len(done_this_month),
        "completion_pct": round((100.0 * len(done_rows) / len(rows)) if rows else 0.0, 1),
        "delayed_count": len(delayed),
    }


def test_summary(root: Path) -> dict[str, Any]:
    rows = read_tsv_dicts(root / DATA_DIR / "test_results.tsv")
    statuses = [(row.get("ステータス") or "").strip().upper() for row in rows]
    passed = sum(1 for status in statuses if status == "PASS")
    return {
        "total": len(rows),
        "passed": passed,
        "pass_pct": round((100.0 * passed / len(rows)) if rows else 0.0, 1),
    }


def issue_summary(root: Path, month: str) -> dict[str, Any]:
    rows = read_tsv_dicts(root / DATA_DIR / "issues_tracker.tsv")
    month_rows = [
        row
        for row in rows
        if in_month(row.get("起票日", ""), month) or in_month(row.get("更新日", ""), month)
    ]
    open_rows = [row for row in month_rows if (row.get("状態") or "").strip() not in {"resolved", "wont_fix"}]
    return {"total": len(month_rows), "open": len(open_rows)}


def security_summary(root: Path, month: str) -> dict[str, Any]:
    rows = read_tsv_dicts(root / DATA_DIR / "security_log.tsv")
    month_rows = [row for row in rows if (row.get("検知日時") or "").startswith(month)]
    open_rows = [row for row in month_rows if (row.get("ステータス") or "").strip().upper() != "FIXED"]
    return {"total": len(month_rows), "open": len(open_rows)}


def usage_summary(root: Path, month: str) -> dict[str, Any]:
    providers: dict[str, dict[str, int]] = {}
    alerts: list[Any] = []
    audit_days = 0
    for path in sorted((root / "reports").glob("daily_usage_audit_*.json")):
        day = path.stem.replace("daily_usage_audit_", "")
        if not day.startswith(month):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        audit_days += 1
        for key, guard in (payload.get("guards") or {}).items():
            row = providers.setdefault(key, {"billable": 0, "blocked": 0, "tokens": 0})
            row["billable"] += int(guard.get("billable_calls") or 0)
            row["blocked"] += int(guard.get("blocked_calls") or 0)
            row["tokens"] += int(guard.get("reported_total_tokens") or 0)
        alerts.extend(payload.get("alerts") or [])
    return {"providers": providers, "alerts": alerts, "audit_days": audit_days}


def pilot_metrics(root: Path, month: str) -> dict[str, float | None]:
    rows = [
        row
        for row in read_tsv_dicts(root / DATA_DIR / "pilot_summary.tsv")
        if in_month(row.get("最終更新日時", ""), month)
    ]
    by_name = {(row.get("確認項目") or "").strip(): row for row in rows}
    diagnosis_count = number_from_text((by_name.get("テストマッチング回数") or {}).get("実績値", ""))
    accuracy_score = number_from_text((by_name.get("診断結果の適合精度") or {}).get("実績値", ""))
    api_cost = number_from_text((by_name.get("期間中累積APIコスト") or {}).get("実績値", ""))
    return {
        "diagnosis_count": diagnosis_count,
        "accuracy_score_pct": accuracy_score,
        "gemini_cost_usd": api_cost,
    }


def collect_monthly_summary(root: Path, month: str, today: dt.date, report_file: Path) -> dict[str, Any]:
    wbs = wbs_summary(root, month, today)
    tests = test_summary(root)
    issues = issue_summary(root, month)
    security = security_summary(root, month)
    usage = usage_summary(root, month)
    pilot = pilot_metrics(root, month)
    gemini_calls = sum(
        values["billable"] for key, values in usage["providers"].items() if key.startswith("gemini_api")
    )

    total_cost = None
    if pilot["gemini_cost_usd"] is not None:
        total_cost = float(pilot["gemini_cost_usd"])

    return {
        "task_id": TASK_ID,
        "month": month,
        "month_label": month_label(month),
        "generated_at": utc_now(),
        "report_kind": report_kind(month, today),
        "report_file": display_path(root, report_file),
        "wbs": wbs,
        "tests": tests,
        "issues": issues,
        "security": security,
        "usage": usage,
        "kpi": {
            "availability_pct": None,
            "p95_response_seconds": None,
            "error_5xx_pct": None,
            "diagnosis_count": pilot["diagnosis_count"],
            "accuracy_score_pct": pilot["accuracy_score_pct"],
            "gemini_cost_usd": pilot["gemini_cost_usd"],
            "firebase_cost_usd": None,
            "supabase_cost_usd": None,
            "total_cost_usd": total_cost,
            "gemini_billable_calls": gemini_calls,
        },
        "sources": {
            "report": display_path(root, report_file),
            "wbs": "data/WBS.tsv",
            "issues": "data/issues_tracker.tsv",
            "qa": "data/qa_tracker.tsv",
            "tests": "data/test_results.tsv",
            "security": "data/security_log.tsv",
            "pilot": "data/pilot_summary.tsv",
            "usage_audits": "reports/daily_usage_audit_*.json",
        },
        "notes": [
            "SLA availability, P95 response, 5xx error rate, Firebase cost, and Supabase cost remain '未計測' until T800/T807/T811 connect live telemetry and billing exports.",
            "Notification and API secrets are read from environment variables only and are not written to artifacts.",
        ],
    }


def kpi_row(summary: dict[str, Any]) -> list[str]:
    kpi = summary["kpi"]
    return [
        summary["month"],
        format_metric(kpi["availability_pct"], 2),
        format_metric(kpi["p95_response_seconds"], 2),
        format_metric(kpi["error_5xx_pct"], 2),
        format_metric(kpi["diagnosis_count"], 0),
        format_metric(kpi["accuracy_score_pct"], 1),
        format_metric(kpi["gemini_cost_usd"], 2),
        format_metric(kpi["firebase_cost_usd"], 2),
        format_metric(kpi["supabase_cost_usd"], 2),
        format_metric(kpi["total_cost_usd"], 2),
        format_metric(summary["wbs"]["completion_pct"], 1),
        format_metric(summary["tests"]["pass_pct"], 1),
        str(summary["issues"]["total"]),
        str(summary["security"]["total"]),
        summary["report_file"],
        summary["report_kind"],
        summary["generated_at"],
    ]


def merge_kpi_values(existing_values: list[list[str]], summary: dict[str, Any]) -> tuple[list[list[str]], int, str]:
    row = kpi_row(summary)
    values = [list(existing) for existing in existing_values if existing]
    if not values or values[0][: len(KPI_HEADERS)] != KPI_HEADERS:
        values = [KPI_HEADERS] + [value for value in values[1:] if value and value[0] != summary["month"]]

    month = summary["month"]
    for index, existing in enumerate(values[1:], start=1):
        if existing and existing[0] == month:
            values[index] = row
            return values, index + 1, "updated"
    values.append(row)
    return values, len(values), "appended"


def output_paths(root: Path, month: str) -> DeliveryOutputs:
    exports = root / EXPORTS_DIR
    return DeliveryOutputs(
        kpi_json=exports / f"monthly_quality_kpi_{month}.json",
        notion_payload=exports / f"monthly_quality_notion_payload_{month}.json",
        notion_status=exports / f"monthly_quality_notion_status_{month}.json",
        slack_payload=exports / f"monthly_quality_slack_payload_{month}.json",
        slack_status=exports / f"monthly_quality_slack_status_{month}.json",
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def google_credentials_configured(root: Path, allow_interactive_oauth: bool = False) -> bool:
    if os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"):
        return True
    if (root / "client_secret.json").exists() and (root / "authorized_user.json").exists():
        return True
    if (root / "credentials.json").exists():
        return True
    return allow_interactive_oauth and (root / "client_secret.json").exists()


def open_gspread_client(root: Path, allow_interactive_oauth: bool = False):
    src_dir = root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    try:
        import gspread  # pylint: disable=import-outside-toplevel
        from google.oauth2.service_account import Credentials  # pylint: disable=import-outside-toplevel
        from google_workspace_account import (  # pylint: disable=import-outside-toplevel
            assert_expected_google_account,
            credentials_from_gspread_client,
        )
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise CredentialMissing("gspread/google-auth are required for Sheets sync") from exc

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    service_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_json:
        credentials = Credentials.from_service_account_info(json.loads(service_json), scopes=scopes)
        return gspread.authorize(credentials)

    client_secret = root / "client_secret.json"
    authorized_user = root / "authorized_user.json"
    if client_secret.exists() and (authorized_user.exists() or allow_interactive_oauth):
        client = gspread.oauth(
            scopes=scopes,
            credentials_filename=str(client_secret),
            authorized_user_filename=str(authorized_user),
        )
        assert_expected_google_account(credentials_from_gspread_client(client), EXPECTED_GOOGLE_ACCOUNT)
        return client

    credentials_file = root / "credentials.json"
    if credentials_file.exists():
        credentials = Credentials.from_service_account_file(str(credentials_file), scopes=scopes)
        return gspread.authorize(credentials)

    raise CredentialMissing(
        "Google credentials are not configured. Set GOOGLE_SERVICE_ACCOUNT_JSON, credentials.json, "
        "or client_secret.json + authorized_user.json."
    )


def apply_kpi_sheet_style(spreadsheet: Any, worksheet: Any, row_count: int) -> None:
    sheet_id = worksheet.id
    requests = [
        {
            "updateSheetProperties": {
                "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91},
                        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat)",
            }
        },
        {
            "autoResizeDimensions": {
                "dimensions": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": len(KPI_HEADERS)}
            }
        },
    ]
    if row_count > 1:
        requests.append(
            {
                "setBasicFilter": {
                    "filter": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": row_count,
                            "startColumnIndex": 0,
                            "endColumnIndex": len(KPI_HEADERS),
                        }
                    }
                }
            }
        )
    spreadsheet.batch_update({"requests": requests})


def sync_summary_to_sheets(
    root: Path,
    spreadsheet_id: str,
    summary: dict[str, Any],
    allow_interactive_oauth: bool = False,
) -> dict[str, Any]:
    import gspread  # pylint: disable=import-outside-toplevel

    client = open_gspread_client(root, allow_interactive_oauth=allow_interactive_oauth)
    spreadsheet = client.open_by_key(spreadsheet_id)
    try:
        worksheet = spreadsheet.worksheet(KPI_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=KPI_SHEET_NAME, rows=120, cols=len(KPI_HEADERS))

    existing_values = worksheet.get_all_values()
    values, row_number, action = merge_kpi_values(existing_values, summary)
    worksheet.resize(rows=max(len(values) + 20, 60), cols=len(KPI_HEADERS))
    worksheet.update(values=values, range_name="A1", value_input_option="USER_ENTERED")
    apply_kpi_sheet_style(spreadsheet, worksheet, len(values))
    return {
        "status": "synced",
        "action": action,
        "spreadsheet_id": spreadsheet_id,
        "spreadsheet_url": getattr(spreadsheet, "url", ""),
        "worksheet": KPI_SHEET_NAME,
        "row_number": row_number,
        "synced_at": utc_now(),
    }


def text_object(content: str) -> dict[str, Any]:
    trimmed = content[:1900] + "..." if len(content) > 1900 else content
    return {"type": "text", "text": {"content": trimmed}}


def notion_rich_text(content: str) -> list[dict[str, Any]]:
    return [text_object(content)]


def build_notion_payload(summary: dict[str, Any], parent: dict[str, str], title_property: str = "Name") -> dict[str, Any]:
    title = f"Mighty Skill-Bridge 月次品質レポート {summary['month_label']}"
    kpi = summary["kpi"]
    wbs = summary["wbs"]
    tests = summary["tests"]
    issues = summary["issues"]
    blocks = [
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": notion_rich_text(title)}},
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": notion_rich_text(
                    f"{summary['report_kind']} report generated from {summary['report_file']} at {summary['generated_at']}."
                )
            },
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": notion_rich_text(
                    f"WBS完了率: {wbs['completion_pct']}% ({wbs['done_total']}/{wbs['total']})"
                )
            },
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": notion_rich_text(
                    f"テスト合格率: {tests['pass_pct']}% ({tests['passed']}/{tests['total']})"
                )
            },
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": notion_rich_text(
                    f"診断件数: {format_metric(kpi['diagnosis_count'], 0)} / 精度スコア: {format_metric(kpi['accuracy_score_pct'], 1)}%"
                )
            },
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": notion_rich_text(
                    f"当月課題: {issues['total']}件 (未解決 {issues['open']}件) / セキュリティ検出: {summary['security']['total']}件"
                )
            },
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": notion_rich_text(
                    "SLA稼働率、P95、5xx、Firebase/Supabase費用は未計測値を捏造せず、未計測として保持します。"
                )
            },
        },
    ]
    properties = (
        {"title": {"title": notion_rich_text(title)}}
        if "page_id" in parent
        else {title_property: {"title": notion_rich_text(title)}}
    )
    return {"parent": parent, "properties": properties, "children": blocks}


def notion_parent_from_env(env: dict[str, str] | None = None) -> dict[str, str] | None:
    source = env or os.environ
    if source.get("NOTION_DATA_SOURCE_ID"):
        return {"data_source_id": source["NOTION_DATA_SOURCE_ID"]}
    if source.get("NOTION_DATABASE_ID"):
        return {"database_id": source["NOTION_DATABASE_ID"]}
    if source.get("NOTION_PARENT_PAGE_ID"):
        return {"page_id": source["NOTION_PARENT_PAGE_ID"]}
    return None


def notion_credentials_configured(env: dict[str, str] | None = None) -> bool:
    source = env or os.environ
    return bool((source.get("NOTION_API_KEY") or source.get("NOTION_TOKEN")) and notion_parent_from_env(source))


def post_to_notion(payload: dict[str, Any], env: dict[str, str] | None = None) -> dict[str, Any]:
    source = env or os.environ
    token = source.get("NOTION_API_KEY") or source.get("NOTION_TOKEN")
    if not token:
        raise CredentialMissing("NOTION_API_KEY or NOTION_TOKEN is required")
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        NOTION_API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": source.get("NOTION_VERSION", NOTION_VERSION),
        },
        method="POST",
    )
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                response_body = response.read().decode("utf-8")
                data = json.loads(response_body) if response_body else {}
                return {
                    "status": "posted",
                    "url": data.get("url", ""),
                    "page_id": data.get("id", ""),
                    "posted_at": utc_now(),
                }
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt == 0:
                retry_after = min(int(exc.headers.get("Retry-After", "2") or 2), 10)
                time.sleep(retry_after)
                continue
            error_body = exc.read().decode("utf-8", errors="replace")
            raise DeliveryError(f"Notion API returned HTTP {exc.code}: {error_body[:500]}") from exc
        except urllib.error.URLError as exc:
            raise DeliveryError(f"Notion API request failed: {exc.reason}") from exc
    raise DeliveryError("Notion API request failed after retry")


def build_slack_payload(summary: dict[str, Any], notion_url: str = "") -> dict[str, Any]:
    kpi = summary["kpi"]
    wbs = summary["wbs"]
    tests = summary["tests"]
    cost_text = (
        f"${kpi['total_cost_usd']:.2f}" if kpi["total_cost_usd"] is not None else "未計測"
    )
    detail_links = f"Sheets: https://docs.google.com/spreadsheets/d/{DEFAULT_SPREADSHEET_ID}"
    if notion_url:
        detail_links += f" | Notion: {notion_url}"
    text = (
        f"[{summary['month_label']}] Mighty Skill-Bridge 月次品質レポート: "
        f"WBS {wbs['completion_pct']}%, tests {tests['pass_pct']}%, cost {cost_text}"
    )
    return {
        "text": text,
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"{summary['month_label']} 月次品質レポート"}},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*WBS完了率*\n{wbs['completion_pct']}% ({wbs['done_total']}/{wbs['total']})"},
                    {"type": "mrkdwn", "text": f"*テスト合格率*\n{tests['pass_pct']}% ({tests['passed']}/{tests['total']})"},
                    {"type": "mrkdwn", "text": f"*診断件数*\n{format_metric(kpi['diagnosis_count'], 0)}"},
                    {"type": "mrkdwn", "text": f"*精度スコア*\n{format_metric(kpi['accuracy_score_pct'], 1)}%"},
                    {"type": "mrkdwn", "text": f"*月間コスト*\n{cost_text}"},
                    {"type": "mrkdwn", "text": f"*未解決課題*\n{summary['issues']['open']}件"},
                ],
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": detail_links}},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"{summary['report_file']} / {summary['report_kind']} / {summary['generated_at']}",
                    }
                ],
            },
        ],
    }


def slack_configured(env: dict[str, str] | None = None) -> bool:
    source = env or os.environ
    return bool(source.get("SLACK_WEBHOOK_URL"))


def send_to_slack(payload: dict[str, Any], env: dict[str, str] | None = None) -> dict[str, Any]:
    source = env or os.environ
    webhook_url = source.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        raise CredentialMissing("SLACK_WEBHOOK_URL is required")
    request = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8", errors="replace")
            if response.status >= 300:
                raise DeliveryError(f"Slack webhook returned HTTP {response.status}: {body[:300]}")
            return {"status": "sent", "sent_at": utc_now(), "http_status": response.status}
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise DeliveryError(f"Slack webhook returned HTTP {exc.code}: {error_body[:300]}") from exc
    except urllib.error.URLError as exc:
        raise DeliveryError(f"Slack webhook request failed: {exc.reason}") from exc


def delivery_status(status: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"task_id": TASK_ID, "status": status, "message": message, "checked_at": utc_now(), **extra}
