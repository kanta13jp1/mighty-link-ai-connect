"""Frontend<->backend API response-contract audit harness (T887): 10 hypotheses.

T884 (form errors), T885 (diagnosis), T886 (admin loaders) all fixed a UI that
mishandled a backend response. Their common root is response-shape *contract
drift*: the frontend deep-reads fields like `data.scores.skill`,
`data.summary.work_hours` or `data.attendance_import.summary.overtime_hours`, and
if the backend renames or drops one the UI silently shows blanks / `undefined` /
frozen sample values with no error.

This harness pins that contract from both sides at once:
  * dynamically (FastAPI TestClient on an isolated temp DB) it probes each key
    data-consuming endpoint and asserts the response really contains the fields
    the UI reads, and
  * statically it asserts index.html AND src/index.html actually reference those
    fields, so the contract stays honest with real usage.

A backend field rename now trips H1-H4; dropping a frontend usage trips H5-H7.
Output: exports/frontend_api_contract_audit.{json,md}. No secrets.
Run: `python scripts/audit_frontend_api_contract.py`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_FILES = [PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html"]
DEFAULT_JSON = PROJECT_ROOT / "exports" / "frontend_api_contract_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "frontend_api_contract_audit.md"

sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Contract: for each key flow, the backend response dot-paths the UI consumes and
# the exact `data.*` substrings that must appear in the HTML that reads them.
# response_keys use dot-paths; a list on the path is probed at element [0]
# (e.g. "qa.question" -> response["qa"][0]["question"]).
MATCH_KEYS = [
    "scores.skill", "scores.culture", "scores.growth", "scores.performing",
    "final_score", "summary", "qa.question", "qa.answer",
    "structured.matched_skills", "structured.missing_skills",
    "db_match_id", "roadmap_week1", "roadmap_week2", "roadmap_week3", "roadmap_week4",
]
PARSE_KEYS = [
    "import_id", "subject_pseudonym",
    "summary.work_hours", "summary.overtime_hours", "summary.holiday_work_days",
    "summary.midnight_hours", "summary.anomaly_count",
]
PUNCH_KEYS = ["subject_pseudonym", "punch_id", "status"]
APPROVE_KEYS = [
    "attendance_import.subject_pseudonym",
    "attendance_import.summary.overtime_hours",
    "attendance_import.status",
]

MATCH_REFS = ["data.scores.skill", "data.final_score", "data.summary",
              "data.structured.matched_skills", "data.roadmap_week1", "data.db_match_id"]
PARSE_REFS = ["data.import_id", "data.summary.work_hours", "data.summary.overtime_hours"]
PUNCH_REFS = ["data.subject_pseudonym"]
APPROVE_REFS = ["approved.subject_pseudonym", "approved.summary.overtime_hours"]


def has_path(obj: Any, dotted: str) -> bool:
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, list):
            if not cur:
                return False
            cur = cur[0]
        if not isinstance(cur, dict) or part not in cur:
            return False
        cur = cur[part]
    return True


def probe_backend() -> dict[str, Any]:
    """Spin an isolated TestClient and capture the four key responses."""
    import app  # noqa: E402
    from fastapi.testclient import TestClient  # noqa: E402

    saved = (app.DATA_DIR, app.AUDIT_DIR, getattr(app, "AUDIT_LOG_FILE", None))
    tmp = tempfile.mkdtemp()
    app.DATA_DIR = os.path.join(tmp, "data")
    app.AUDIT_DIR = os.path.join(tmp, "data", "audit")
    os.makedirs(app.AUDIT_DIR, exist_ok=True)
    if hasattr(app, "AUDIT_LOG_FILE"):
        app.AUDIT_LOG_FILE = os.path.join(app.AUDIT_DIR, "ai_audit.jsonl")
    consent = app.LEGAL_CONSENT_VERSION
    out: dict[str, Any] = {}
    try:
        with TestClient(app.app) as c:
            out["match"] = c.post("/api/match", json={
                "engineer_content": "氏名: X\nスキル: Python", "job_content": "案件: Y\n必須: Python",
                "legal_consent_accepted": True, "legal_consent_version": consent,
            }).json()
            out["punch"] = c.post("/api/attendance/punch", json={
                "employee_identifier": "emp-001", "event_type": "in", "consented": True,
            }).json()
            parse = c.post("/api/attendance/timesheet/parse",
                           data={"employee_identifier": "emp-001", "consented": "true",
                                 "consent_version": "MSB-ATTENDANCE-2026-06"},
                           files={"file": ("t.csv", b"date,work_hours\n2026-07-01,8\n2026-07-02,8\n", "text/csv")}).json()
            out["parse"] = parse
            out["approve"] = c.post("/api/attendance/timesheet/approve",
                                    json={"import_id": parse.get("import_id"), "decision": "approved"},
                                    auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD)).json()
    finally:
        app.DATA_DIR, app.AUDIT_DIR = saved[0], saved[1]
        if saved[2] is not None:
            app.AUDIT_LOG_FILE = saved[2]
    return out


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate() -> dict[str, Any]:
    resp = probe_backend()
    htmls = {p: p.read_text(encoding="utf-8", errors="replace") for p in INDEX_FILES}
    idx, src = INDEX_FILES[0], INDEX_FILES[1]

    def missing_keys(name: str, keys: list[str]) -> list[str]:
        r = resp.get(name, {})
        return [k for k in keys if not has_path(r, k)]

    def missing_refs(text: str, refs: list[str]) -> list[str]:
        return [r for r in refs if r not in text]

    results: list[dict[str, Any]] = []

    m = missing_keys("match", MATCH_KEYS)
    results.append(_hyp("H1", "/api/match応答が診断UIの読むフィールド(scores.*/final_score/summary/qa/structured/roadmap/db_match_id)を含む",
                        not m, f"欠落={m or 'なし'}"))

    m = missing_keys("parse", PARSE_KEYS)
    results.append(_hyp("H2", "/api/attendance/timesheet/parse応答がimport_id/summary.*を含む",
                        not m, f"欠落={m or 'なし'}"))

    m = missing_keys("punch", PUNCH_KEYS)
    results.append(_hyp("H3", "/api/attendance/punch応答がsubject_pseudonym/punch_id/statusを含む",
                        not m, f"欠落={m or 'なし'}"))

    m = missing_keys("approve", APPROVE_KEYS)
    results.append(_hyp("H4", "/api/attendance/timesheet/approve応答がattendance_import.summary.overtime_hours等を含む",
                        not m, f"欠落={m or 'なし'}"))

    mr = missing_refs(htmls[idx], MATCH_REFS)
    results.append(_hyp("H5", "index.htmlが診断応答フィールド(data.scores.skill/final_score/roadmap_week1等)を参照",
                        not mr, f"未参照={mr or 'なし'}"))

    mr = missing_refs(htmls[idx], PARSE_REFS + PUNCH_REFS + APPROVE_REFS)
    results.append(_hyp("H6", "index.htmlが勤怠応答フィールド(data.import_id/data.summary.work_hours/approved.summary.overtime_hours等)を参照",
                        not mr, f"未参照={mr or 'なし'}"))

    all_refs = MATCH_REFS + PARSE_REFS + PUNCH_REFS + APPROVE_REFS
    mr = missing_refs(htmls[src], all_refs)
    results.append(_hyp("H7", "src/index.htmlも同じ契約フィールドを参照(ミラー整合)",
                        not mr, f"未参照={mr or 'なし'}"))

    # H8: every frontend leaf ref is backed by a probed contract key (no UI read
    # without a verified backend guarantee).
    backed = set()
    for keys in (MATCH_KEYS, PARSE_KEYS, PUNCH_KEYS, APPROVE_KEYS):
        for k in keys:
            backed.add(k.split(".")[-1])
    leaf = lambda r: r.split(".")[-1]
    unbacked = [r for r in all_refs if leaf(r) not in backed]
    results.append(_hyp("H8", "フロント参照フィールドはすべてバックエンド検証済み契約キーに裏付けられている",
                        not unbacked, f"裏付けなし={unbacked or 'なし'}"))

    wbs = (PROJECT_ROOT / "data" / "WBS.tsv").read_text(encoding="utf-8", errors="replace")
    uat = (PROJECT_ROOT / "docs" / "UAT_TEST_SPECIFICATION.md").read_text(encoding="utf-8", errors="replace")
    import re
    wbs_ok = bool(re.search(r"(^|\n)T887\t", wbs))
    uat_ok = "TS-19" in uat and "T887" in uat
    results.append(_hyp("H9", "WBSにT887・UAT仕様書にTS-19(T887)が実在",
                        wbs_ok and uat_ok, f"WBS_T887={wbs_ok}, UAT_TS19={uat_ok}"))

    prior_ok = all(h["passed"] for h in results)
    results.append(_hyp("H10", "フロント⇔バックエンドAPI契約にドリフト0",
                        prior_ok, f"先行ドリフト={'なし' if prior_ok else 'あり'}"))

    return {
        "task": "T887",
        "endpoints": ["/api/match", "/api/attendance/timesheet/parse",
                      "/api/attendance/punch", "/api/attendance/timesheet/approve"],
        "hypotheses": results,
        "all_passed": all(h["passed"] for h in results),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# フロントエンド⇔バックエンド API応答契約 監査 (T887)",
        "",
        f"- 対象エンドポイント: {', '.join(report['endpoints'])}",
        f"- 総合判定: {'✅ PASS (ドリフト0)' if report['all_passed'] else '❌ FAIL'}",
        "",
        "## 10仮説の検証結果",
        "",
        "| 仮説 | 内容 | 判定 | 詳細 |",
        "| :--- | :--- | :---: | :--- |",
    ]
    for h in report["hypotheses"]:
        lines.append(f"| {h['id']} | {h['title']} | {'✅' if h['passed'] else '❌'} | {h['detail']} |")
    lines += [
        "",
        "> 動的(TestClient)でバックエンド実応答を、静的(HTML grep)でフロント参照を双方向照合。",
        "> バックエンドのフィールド改名/削除はH1-H4、フロント参照の欠落はH5-H7で検出する。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit frontend/backend API contract (T887, 10 hypotheses)")
    parser.add_argument("--json", default=str(DEFAULT_JSON))
    parser.add_argument("--md", default=str(DEFAULT_MD))
    args = parser.parse_args()

    report = evaluate()
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.md).write_text(render_markdown(report), encoding="utf-8")

    passed = sum(1 for h in report["hypotheses"] if h["passed"])
    print(f"[frontend-api-contract-audit] {passed}/{len(report['hypotheses'])} hypotheses passed "
          f"-> {'ALL PASS' if report['all_passed'] else 'FAIL'}")
    for h in report["hypotheses"]:
        print(f"  {'PASS' if h['passed'] else 'FAIL'} {h['id']}: {h['title']} ({h['detail']})")
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
