"""Sales-email AI matching hardening audit (T817_7_1).

T817_7 hardens the sales-email pipeline for production: PII minimization, audit
trail, retention/deletion, load, backup, and account permissions. The real-mail
part waits on T836 (mailbox connection approval), but every control that exists
in the repo — schema, pipeline code, docs, evidence exports — can be verified
offline with PoC data. This harness owns that half as 10 hypotheses.

Dimension map:
  個人情報最小化  H3 H4 H5 H6   監査ログ H10   保持/削除 H8
  負荷           H9            権限     H1 H2 H7
  バックアップ    scope note (full-DB pg_dump covers all 9 tables; permanent CI
                 fix is T870; interim 22-table local backup confirmed in T871)

Outputs: exports/sales_email_hardening_audit.{json,md}. Synthetic fixtures only —
no real mail, no secrets, no personal data.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SQL = PROJECT_ROOT / "supabase" / "migrations" / "20260618000000_sales_email_matching_schema.sql"
RETENTION_DOC = PROJECT_ROOT / "docs" / "DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "sales_email_hardening_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "sales_email_hardening_audit.md"

SALES_TABLES = [
    "sales_mailbox_sources",
    "sales_email_messages",
    "sales_email_entities",
    "project_requirements",
    "talent_profiles_from_email",
    "requirement_skill_tags",
    "email_parse_runs",
    "email_match_results",
    "email_match_feedback",
]

# Columns that would mean raw PII landed in the schema.
FORBIDDEN_COLUMN_PATTERNS = [
    r"\bsender_email\b",
    r"\brecipient",
    r"\bfull_body\b",
    r"\braw_body\b",
    r"\bbody_text\b",
    r"\bphone",
    r"\bcontact_email\b",
]

SALES_API_ROUTES = [
    "/api/sales-email/matches",
    "/api/sales-email/reviews",
    "/api/sales-email/reviews/summary",
]

REVIEW_AUDIT_EXPORTS = [
    "exports/sales_email_review_log.json",
    "exports/sales_email_review_log.md",
    "exports/sales_email_match_review.json",
]

PII_EVIDENCE_EXPORTS = [
    "exports/sales_email_ingest_review.md",
    "exports/sales_email_extraction_review.md",
    "exports/sales_email_match_review.md",
    "exports/sales_email_review_log.md",
]

RAW_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RAW_PHONE_RE = re.compile(r"0\d{1,4}-\d{1,4}-\d{3,4}")
ALLOWED_EMAIL_LITERALS = {"redacted"}  # "<email:redacted>" markers


def _sys_path():
    for p in (PROJECT_ROOT / "src", PROJECT_ROOT / "scripts"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))


def build_hypotheses() -> list[dict[str, Any]]:
    _sys_path()
    import sales_email_extract as extract_mod
    import sales_email_ingest as ingest_mod
    import parse_sales_emails as parse_cli

    schema_sql = SCHEMA_SQL.read_text(encoding="utf-8")
    retention_doc = RETENTION_DOC.read_text(encoding="utf-8")
    app_src = (PROJECT_ROOT / "src" / "app.py").read_text(encoding="utf-8")

    results: list[dict[str, Any]] = []

    def record(hid: str, statement: str, check: Callable[[], tuple[bool, str]]) -> None:
        try:
            passed, detail = check()
        except Exception as exc:
            passed, detail = False, f"例外: {type(exc).__name__}: {exc}"
        results.append({"id": hid, "hypothesis": statement, "passed": passed, "detail": detail})

    # H1: RLS enabled on all 9 tables.
    def h1() -> tuple[bool, str]:
        missing = [t for t in SALES_TABLES
                   if not re.search(rf"ALTER TABLE public\.{t} ENABLE ROW LEVEL SECURITY", schema_sql)]
        return not missing, f"RLS有効化 {len(SALES_TABLES) - len(missing)}/9" + (f" 欠落: {missing}" if missing else "")

    record("H1", "営業メール9テーブル全てにRLSが有効化されている", h1)

    # H2: anon/authenticated revoked on all 9 tables.
    def h2() -> tuple[bool, str]:
        missing = [t for t in SALES_TABLES
                   if not re.search(rf"REVOKE ALL ON TABLE public\.{t} FROM anon, authenticated", schema_sql)]
        return not missing, f"REVOKE {len(SALES_TABLES) - len(missing)}/9" + (f" 欠落: {missing}" if missing else "")

    record("H2", "9テーブル全てでanon/authenticatedの権限が剥奪されている", h2)

    # H3: schema has no raw-PII columns; body/subject stored as hash+capped excerpt.
    def h3() -> tuple[bool, str]:
        hits = [p for p in FORBIDDEN_COLUMN_PATTERNS if re.search(p, schema_sql, re.IGNORECASE)]
        has_hashes = all(c in schema_sql for c in ["sender_hash", "body_hash", "message_id_hash"])
        excerpt_capped = bool(re.search(r"body_excerpt.*char_length", schema_sql))
        ok = not hits and has_hashes and excerpt_capped
        return ok, f"禁止列={hits or 'なし'} hash列={has_hashes} excerpt長CHECK={excerpt_capped}"

    record("H3", "スキーマは生PII列を持たず、送信者/本文はhash+上限付きexcerptのみ保存する", h3)

    # H4: redaction utilities scrub email/phone/secret and cap excerpt length.
    def h4() -> tuple[bool, str]:
        dirty = "連絡は taro.yamada@example.co.jp / 090-1234-5678 まで。token=abcd1234secret"
        red = ingest_mod.redact_sensitive_text(dirty)
        exc = ingest_mod.safe_excerpt("あ" * 500)
        ok = ("taro.yamada" not in red and "090-1234-5678" not in red
              and "abcd1234secret" not in red and len(exc) <= 240)
        return ok, f"redact後PII残存なし={ok is True or red[:60]} excerpt長={len(exc)}(<=240)"

    record("H4", "redact/excerptユーティリティがメール・電話・secret実値を除去し240字上限を守る", h4)

    # H5: ingest end-to-end stores only hashes/redacted excerpts for a synthetic email.
    def h5() -> tuple[bool, str]:
        from dataclasses import asdict

        email = ingest_mod.RawSalesEmail(
            source_path="poc/t817-7-test.eml",
            source_type="eml",
            sender="Hanako Sato <hanako.sato@partner.example.jp>",
            subject="【案件】Java開発 連絡先: hanako.sato@partner.example.jp",
            body="単価80万。連絡は hanako.sato@partner.example.jp / 03-1234-5678 へ。",
            received_at="2026-07-08T09:00:00+09:00",
            message_id="<t817-7-test@example.com>",
        )
        sanitized = ingest_mod.sanitize_email(email, duplicate=False, duplicate_of="")
        blob = json.dumps(asdict(sanitized), ensure_ascii=False)
        no_pii = "hanako.sato" not in blob and "03-1234-5678" not in blob
        ok = no_pii and len(sanitized.sender_hash) == 64 and len(sanitized.body_hash) == 64
        return ok, f"生メール/電話の残存なし={no_pii} sender_hash/body_hash=sha256(64hex)"

    record("H5", "取込は合成メールのPII実値を保存せず、sha256ハッシュとredacted excerptのみ残す", h5)

    # H6: extraction anonymizes talent and redacts evidence.
    def h6() -> tuple[bool, str]:
        from dataclasses import asdict

        email = ingest_mod.RawSalesEmail(
            source_path="poc/t817-7-talent.eml",
            source_type="eml",
            sender="bp@partner.example.jp",
            subject="【要員】Java技術者のご紹介",
            body="30代Javaエンジニア、経験7年。希望単価60〜70万。連絡: taro@bp.example.jp",
            received_at="2026-07-08T09:05:00+09:00",
            message_id="<t817-7-talent@example.com>",
        )
        extraction = extract_mod.extract_email(email)
        blob = json.dumps(asdict(extraction), ensure_ascii=False)
        talent = extraction.talent_profile
        has_anon_key = bool(talent and talent.anonymized_talent_key)
        ok = "taro@bp.example.jp" not in blob and has_anon_key
        return ok, f"生連絡先残存なし={'taro@bp.example.jp' not in blob} anonymized_talent_key={talent.anonymized_talent_key if talent else 'なし'}"

    record("H6", "抽出は要員を匿名化キーで扱い、evidenceに生連絡先を残さない", h6)

    # H7: all sales-email API routes require authentication.
    def h7() -> tuple[bool, str]:
        missing = []
        for route in SALES_API_ROUTES:
            m = re.search(re.escape(f'"{route}"') + r"\)\s*\n(?:async )?def \w+\((.*?)\):", app_src, re.DOTALL)
            params = m.group(1) if m else ""
            if "verify_credentials" not in params:
                missing.append(route)
        return not missing, f"認証必須 {len(SALES_API_ROUTES) - len(missing)}/3" + (f" 欠落: {missing}" if missing else "")

    record("H7", "営業メールAPI全3ルートがBasic認証necessary（verify_credentials）である", h7)

    # H8: retention runbook covers all 9 tables with retention/deletion guidance.
    def h8() -> tuple[bool, str]:
        groups = [
            ("sales_mailbox_sources", ["sales_mailbox_sources"]),
            ("sales_email_messages", ["sales_email_messages"]),
            ("抽出4テーブル", ["sales_email_entities", "project_requirements",
                               "talent_profiles_from_email", "requirement_skill_tags"]),
            ("email_parse_runs", ["email_parse_runs"]),
            ("レビュー2テーブル", ["email_match_results", "email_match_feedback"]),
        ]
        missing = [name for name, tables in groups
                   if not all(t in retention_doc for t in tables)]
        has_days = bool(re.search(r"90日|180日", retention_doc))
        return not missing and has_days, f"runbook記載 {len(groups) - len(missing)}/5グループ 保持期間記載={has_days}"

    record("H8", "保持/削除runbookが9テーブル全ての保持期間と削除手順をカバーする", h8)

    # H9: load guard — parse CLI enforces a batch cap by default.
    def h9() -> tuple[bool, str]:
        default_cap = parse_cli.resolve_max_messages([])
        explicit = parse_cli.resolve_max_messages(["--max-messages", "10"])
        ok = default_cap == parse_cli.DEFAULT_MAX_MESSAGES and explicit == 10 and default_cap > 0
        return ok, f"既定cap={default_cap}(={parse_cli.DEFAULT_MAX_MESSAGES}期待) --max-messages指定={explicit}"

    record("H9", "負荷ガード: parse CLIは既定でバッチ上限を持ち、無制限のAPI呼び出しをしない", h9)

    # H10: review audit trail exists and evidence exports carry no raw PII.
    def h10() -> tuple[bool, str]:
        missing = [p for p in REVIEW_AUDIT_EXPORTS if not (PROJECT_ROOT / p).exists()]
        leaks: list[str] = []
        for rel in PII_EVIDENCE_EXPORTS:
            path = PROJECT_ROOT / rel
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for m in RAW_EMAIL_RE.finditer(text):
                if not any(marker in m.group(0) for marker in ALLOWED_EMAIL_LITERALS):
                    leaks.append(f"{rel}:{m.group(0)[:40]}")
                    break
            if RAW_PHONE_RE.search(text):
                leaks.append(f"{rel}:raw-phone")
        ok = not missing and not leaks
        return ok, f"監査証跡欠落={missing or 'なし'} 生PII検出={leaks or 'なし'}"

    record("H10", "レビュー監査証跡(exports)が存在し、証跡ファイルに生メール/電話が含まれない", h10)

    return results


def build_report(checked_at: str) -> dict[str, Any]:
    hypotheses = build_hypotheses()
    passed = sum(1 for h in hypotheses if h["passed"])
    return {
        "report_id": "SALES_EMAIL_HARDENING_T817_7_1",
        "checked_at": checked_at,
        "status": "ok" if passed == len(hypotheses) else "attention",
        "hypotheses_total": len(hypotheses),
        "hypotheses_passed": passed,
        "hypotheses": hypotheses,
        "scope_note": (
            "PoCデータ/スキーマ/コード/証跡のオフラインhardening監査。バックアップはfull-DB "
            "pg_dumpが9テーブルを包含（恒久CI化はT870、暫定22テーブルローカルバックアップはT871確認済み）。"
            "実メール接続後の実運用確認（実データの最小化スポット確認・実流量調整・アカウント権限実査）はT836受領後のT817_7本体工程。"
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 営業メールAIマッチング hardening監査ログ (T817_7_1)",
        "",
        f"- レポートID: `{report['report_id']}`",
        f"- 実施日: {report['checked_at']}",
        f"- 判定: **{report['status']}** ({report['hypotheses_passed']}/{report['hypotheses_total']} 仮説PASS)",
        f"- スコープ: {report['scope_note']}",
        "",
        "## 10仮説検証（hardening 6観点）",
        "",
        "| # | 仮説 | 結果 | 根拠 |",
        "| --- | --- | --- | --- |",
    ]
    for h in report["hypotheses"]:
        mark = "PASS" if h["passed"] else "FAIL"
        lines.append(f"| {h['id']} | {h['hypothesis']} | {mark} | {h['detail'].replace('|', '/')} |")
    lines += [
        "",
        "## 残作業（T817_7本体・T836実接続後）",
        "",
        "- 実メールボックス接続後の実データPII最小化スポット確認と、実流量でのバッチ上限・クォータ調整。",
        "- 実接続アカウントの権限実査（mailbox読み取り専用スコープ、service_role鍵の保管場所）。",
        "- 本番Supabase上の9テーブルへのパイプライン経由書き込み検証（T845残工程と同一の運用者工程）。",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Sales-email hardening audit (T817_7_1)")
    parser.add_argument("--checked-at", default="2026-07-08")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD)
    parser.add_argument("--fail-on-attention", action="store_true")
    args = parser.parse_args()

    report = build_report(args.checked_at)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"[*] Wrote {args.json_out}")
    print(f"[*] Wrote {args.md_out}")
    print(
        f"[{'+' if report['status'] == 'ok' else '!'}] Sales-email hardening audit {report['status']}: "
        f"{report['hypotheses_passed']}/{report['hypotheses_total']} hypotheses passed"
    )
    if args.fail_on_attention and report["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
