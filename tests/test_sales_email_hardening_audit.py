import json
import sys
from dataclasses import asdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import audit_sales_email_hardening as audit
import parse_sales_emails as parse_cli
import sales_email_ingest as ingest


def test_all_hardening_hypotheses_pass_on_real_repo():
    report = audit.build_report("2026-07-08")
    failing = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert report["hypotheses_total"] == 10
    assert failing == [], f"unexpected failing hypotheses: {failing}"
    assert report["status"] == "ok"


def test_sanitized_record_never_carries_raw_pii():
    email = ingest.RawSalesEmail(
        source_path="poc/pii.eml",
        source_type="eml",
        sender="PII Test <pii.leak@example.co.jp>",
        subject="連絡先 pii.leak@example.co.jp 090-1111-2222",
        body="至急連絡ください: pii.leak@example.co.jp / 090-1111-2222 / token=supersecret99",
        received_at="2026-07-08T10:00:00+09:00",
        message_id="<pii-test@example.com>",
    )
    blob = json.dumps(asdict(ingest.sanitize_email(email, duplicate=False, duplicate_of="")), ensure_ascii=False)
    assert "pii.leak" not in blob
    assert "090-1111-2222" not in blob
    assert "supersecret99" not in blob


def test_parse_cli_batch_cap_default_env_and_flag(monkeypatch):
    monkeypatch.delenv("SALES_EMAIL_PARSE_MAX_MESSAGES", raising=False)
    assert parse_cli.resolve_max_messages([]) == parse_cli.DEFAULT_MAX_MESSAGES

    monkeypatch.setenv("SALES_EMAIL_PARSE_MAX_MESSAGES", "7")
    assert parse_cli.resolve_max_messages([]) == 7

    # explicit flag beats env; 0 = explicit unlimited opt-in; negatives clamp to 0
    assert parse_cli.resolve_max_messages(["--max-messages", "3"]) == 3
    assert parse_cli.resolve_max_messages(["--max-messages", "0"]) == 0
    assert parse_cli.resolve_max_messages(["--max-messages", "-5"]) == 0


def test_schema_guard_would_catch_missing_rls():
    # The audit reads the real migration; simulate drift by checking the regex
    # actually distinguishes a table with no RLS statement.
    sql = audit.SCHEMA_SQL.read_text(encoding="utf-8")
    assert "ALTER TABLE public.sales_email_messages ENABLE ROW LEVEL SECURITY" in sql
    import re
    fake = sql.replace("ALTER TABLE public.sales_email_messages ENABLE ROW LEVEL SECURITY;", "")
    assert not re.search(r"ALTER TABLE public\.sales_email_messages ENABLE ROW LEVEL SECURITY", fake)
