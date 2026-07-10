"""Form error-handling audit harness (T884): 10 hypotheses, all verified.

T872 (timesheet) and T883 (survey) fixed a recurring defect — a form handler that
read `!response.ok` but discarded the server's 400/401 `detail`, so validation
errors surfaced as a misleading "接続できませんでした / 送信失敗" (connection
failed). A T882-driven audit found the same defect in five more data-mutation
handlers. This harness verifies, statically against both HTML mirrors and
src/app.py, that every one of those handlers now surfaces the real server reason
while keeping a genuine connection-failure fallback (so the static GitHub Pages
demo, where these APIs 404 / are unreachable, still degrades gracefully).

Output: exports/form_error_handling_audit.{json,md}. No secrets are read or
written. Run: `python scripts/audit_form_error_handling.py`.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_FILES = [PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html"]
APP_PY = PROJECT_ROOT / "src" / "app.py"
WBS_PATH = PROJECT_ROOT / "data" / "WBS.tsv"
UAT_SPEC = PROJECT_ROOT / "docs" / "UAT_TEST_SPECIFICATION.md"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "form_error_handling_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "form_error_handling_audit.md"

# Each data-mutation form handler: its JS function name, the API it posts to, and
# the specific backend 400/401 detail strings the UI must now be able to surface.
HANDLERS: dict[str, dict[str, Any]] = {
    "submitFeedback": {
        "api": "/api/feedback",
        "backend_details": [
            "nps_score must be between 0 and 10",
            "rating must be helpful or not_helpful",
        ],
    },
    "submitSupportRequest": {
        "api": "/api/support/request",
        "backend_details": [
            "message must be at least 10 characters",
            "valid contact_email is required",
        ],
    },
    "punchCard": {
        "api": "/api/attendance/punch",
        "backend_details": [
            "consent is required before storing attendance data",
            "employee_identifier must be at least 3 characters",
            "event_type must be one of",
        ],
    },
    "approveAttendanceData": {
        "api": "/api/attendance/timesheet/approve",
        "backend_details": [
            "decision must be approved or rejected",
            "import_id must be positive",
        ],
    },
    "downloadUserDataExport": {
        "api": "/api/user-data/export",
        "backend_details": [
            "Firebase ID token is required for user data export",
        ],
    },
}

# The pre-fix swallowing markers that must no longer remain in any handler block.
OLD_SWALLOW_MARKERS = ["endpoint unavailable"]


def handler_block(text: str, fn_name: str) -> str:
    marker = f"function {fn_name}("
    if marker not in text:
        return ""
    start = text.index(marker)
    rest = text[start + len(marker):]
    m = re.search(r"\n {8}(?:async )?function ", rest)
    end = start + len(marker) + (m.start() if m else 6000)
    return text[start:end]


def load_app_routes() -> set[str]:
    if not APP_PY.exists():
        return set()
    text = APP_PY.read_text(encoding="utf-8", errors="replace")
    return set(re.findall(r"@app\.(?:get|post|put|delete|patch)\(\"([^\"]+)\"", text))


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate() -> dict[str, Any]:
    texts = {p: p.read_text(encoding="utf-8", errors="replace") for p in INDEX_FILES}
    blocks = {
        p: {fn: handler_block(txt, fn) for fn in HANDLERS}
        for p, txt in texts.items()
    }
    app_text = APP_PY.read_text(encoding="utf-8", errors="replace") if APP_PY.exists() else ""
    routes = load_app_routes()

    results: list[dict[str, Any]] = []
    idx, src = INDEX_FILES[0], INDEX_FILES[1]

    def reads_detail(block: str) -> bool:
        return "serverDetail" in block or ".detail" in block

    # H1: index.html — every handler reads the server detail.
    miss = [fn for fn in HANDLERS if not reads_detail(blocks[idx][fn])]
    results.append(_hyp("H1", "index.html: 全5ハンドラがサーバーdetailを読む",
                        not miss, f"未読取={miss or 'なし'}"))

    # H2: src/index.html mirror — every handler reads the server detail.
    miss = [fn for fn in HANDLERS if not reads_detail(blocks[src][fn])]
    results.append(_hyp("H2", "src/index.html: 全5ハンドラがサーバーdetailを読む",
                        not miss, f"未読取={miss or 'なし'}"))

    # H3: both files — every handler surfaces the reason (サーバー応答 branch).
    miss = [
        f"{p.name}:{fn}"
        for p in INDEX_FILES for fn in HANDLERS
        if "サーバー応答" not in blocks[p][fn]
    ]
    results.append(_hyp("H3", "両ファイル: 全ハンドラに『サーバー応答』理由表示ブランチがある",
                        not miss, f"欠落={miss or 'なし'}"))

    # H4: both files — every handler keeps a real connection-failure fallback (接続).
    miss = [
        f"{p.name}:{fn}"
        for p in INDEX_FILES for fn in HANDLERS
        if "接続" not in blocks[p][fn]
    ]
    results.append(_hyp("H4", "両ファイル: 全ハンドラが接続失敗フォールバックを保持(graceful degradation)",
                        not miss, f"欠落={miss or 'なし'}"))

    # H5: the old swallowing markers ("endpoint unavailable") are gone from handlers.
    remain = [
        f"{p.name}:{fn}"
        for p in INDEX_FILES for fn in HANDLERS
        for mk in OLD_SWALLOW_MARKERS
        if mk in blocks[p][fn]
    ]
    results.append(_hyp("H5", "旧握りつぶし表現(...endpoint unavailable のみthrow)が全ハンドラから除去済み",
                        not remain, f"残存={remain or 'なし'}"))

    # H6: the backend really returns the specific 400/401 details the UI surfaces.
    missing_backend = [
        f"{fn}:{d}"
        for fn, meta in HANDLERS.items()
        for d in meta["backend_details"]
        if d not in app_text
    ]
    results.append(_hyp("H6", "src/app.pyが各エンドポイントの具体的400/401 detailを実装",
                        not missing_backend, f"未実装={missing_backend or 'なし'}"))

    # H7: the 5 handler blocks are byte-identical between the two mirrors.
    drift = [fn for fn in HANDLERS if blocks[idx][fn] != blocks[src][fn]]
    results.append(_hyp("H7", "index.html と src/index.html の5ハンドラがバイト等価(ミラードリフト0)",
                        not drift, f"ドリフト={drift or 'なし'}"))

    # H8: the WBS task and the human UAT case both exist.
    wbs_text = WBS_PATH.read_text(encoding="utf-8", errors="replace") if WBS_PATH.exists() else ""
    uat_text = UAT_SPEC.read_text(encoding="utf-8", errors="replace") if UAT_SPEC.exists() else ""
    wbs_ok = bool(re.search(r"(^|\n)T884\t", wbs_text))
    uat_ok = "TS-16" in uat_text and "T884" in uat_text
    results.append(_hyp("H8", "WBSにT884・UAT仕様書にTS-16(T884)が実在",
                        wbs_ok and uat_ok, f"WBS_T884={wbs_ok}, UAT_TS16={uat_ok}"))

    # H9: every form's API path is a real route in src/app.py.
    bad_api = [meta["api"] for meta in HANDLERS.values() if meta["api"] not in routes]
    results.append(_hyp("H9", "5フォームのAPIパスが全てsrc/app.pyに実在",
                        not bad_api, f"不在={bad_api or 'なし'}"))

    # H10: no prior drift.
    prior_ok = all(h["passed"] for h in results)
    results.append(_hyp("H10", "全ハンドラのエラー握りつぶし解消が完全(ドリフト0)",
                        prior_ok, f"先行ドリフト={'なし' if prior_ok else 'あり'}"))

    return {
        "task": "T884",
        "handlers": list(HANDLERS),
        "index_files": [str(p.relative_to(PROJECT_ROOT)) for p in INDEX_FILES],
        "hypotheses": results,
        "all_passed": all(h["passed"] for h in results),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# フォーム エラー握りつぶし解消 監査 (T884)",
        "",
        f"- 対象ハンドラ: {', '.join(report['handlers'])}",
        f"- 対象ファイル: {', '.join(report['index_files'])}",
        f"- 総合判定: {'✅ PASS (ドリフト0)' if report['all_passed'] else '❌ FAIL'}",
        "",
        "## 10仮説の検証結果",
        "",
        "| 仮説 | 内容 | 判定 | 詳細 |",
        "| :--- | :--- | :---: | :--- |",
    ]
    for h in report["hypotheses"]:
        mark = "✅" if h["passed"] else "❌"
        lines.append(f"| {h['id']} | {h['title']} | {mark} | {h['detail']} |")
    lines.append("")
    lines.append("> T872/T883 と同種の 400/401 detail 握りつぶしを全データ更新フォームへ横展開解消。")
    lines.append("> 真の接続断（静的デモ）は従来の接続エラー文言に戻り、サーバー応答時のみ実理由を表示する。")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit form error-handling (T884, 10 hypotheses)")
    parser.add_argument("--json", default=str(DEFAULT_JSON))
    parser.add_argument("--md", default=str(DEFAULT_MD))
    args = parser.parse_args()

    report = evaluate()
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.md).write_text(render_markdown(report), encoding="utf-8")

    passed = sum(1 for h in report["hypotheses"] if h["passed"])
    print(f"[form-error-audit] {passed}/{len(report['hypotheses'])} hypotheses passed "
          f"-> {'ALL PASS' if report['all_passed'] else 'FAIL'}")
    for h in report["hypotheses"]:
        print(f"  {'PASS' if h['passed'] else 'FAIL'} {h['id']}: {h['title']} ({h['detail']})")
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
