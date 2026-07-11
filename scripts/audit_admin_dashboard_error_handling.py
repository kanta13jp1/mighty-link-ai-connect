"""Admin dashboard error-handling audit harness (T886): 10 hypotheses.

loadOperationsDashboard() and downloadOperationsDashboardCsv() hit Basic-Auth
gated admin APIs but, before T886, showed a generic "Real data unavailable" /
"CSV export unavailable" on any non-OK response. The #1 real cause — wrong or
missing admin credentials (HTTP 401) — was indistinguishable from a server
outage, so an operator could not tell they just needed to re-enter credentials
(same error-swallowing family as T884 forms and T885 diagnosis).

This harness verifies, statically against both HTML mirrors and src/app.py, that
each admin loader now reads the server detail, distinguishes 404 (silent static
demo) from a real backend error, and surfaces the auth reason (401 -> admin auth
required) — while the static GitHub Pages mirror keeps its demo fallback so the
CEO-shared demo is unchanged.

Output: exports/admin_dashboard_error_handling_audit.{json,md}. No secrets.
Run: `python scripts/audit_admin_dashboard_error_handling.py`.
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
DEFAULT_JSON = PROJECT_ROOT / "exports" / "admin_dashboard_error_handling_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "admin_dashboard_error_handling_audit.md"

HANDLERS = ["loadOperationsDashboard", "downloadOperationsDashboardCsv"]


def handler_block(text: str, fn_name: str) -> str:
    marker = f"function {fn_name}("
    if marker not in text:
        return ""
    start = text.index(marker)
    rest = text[start + len(marker):]
    m = re.search(r"\n {8}(?:async )?function ", rest)
    end = start + len(marker) + (m.start() if m else 5000)
    return text[start:end]


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate() -> dict[str, Any]:
    texts = {p: p.read_text(encoding="utf-8", errors="replace") for p in INDEX_FILES}
    blocks = {p: {fn: handler_block(t, fn) for fn in HANDLERS} for p, t in texts.items()}
    app_text = APP_PY.read_text(encoding="utf-8", errors="replace") if APP_PY.exists() else ""
    idx, src = INDEX_FILES[0], INDEX_FILES[1]

    def reads_detail(b: str) -> bool:
        return "serverDetail" in b or ".detail" in b

    results: list[dict[str, Any]] = []

    miss = [fn for fn in HANDLERS if not reads_detail(blocks[idx][fn])]
    results.append(_hyp("H1", "index.html: 両管理者ローダーがサーバーdetailを読む",
                        not miss, f"未読取={miss or 'なし'}"))

    miss = [fn for fn in HANDLERS if not reads_detail(blocks[src][fn])]
    results.append(_hyp("H2", "src/index.html: 両管理者ローダーがサーバーdetailを読む",
                        not miss, f"未読取={miss or 'なし'}"))

    miss = [f"{p.name}:{fn}" for p in INDEX_FILES for fn in HANDLERS if "!== 404" not in blocks[p][fn]]
    results.append(_hyp("H3", "両ファイル: 404(静的デモ)と実バックエンドエラーを区別",
                        not miss, f"未区別={miss or 'なし'}"))

    miss = [f"{p.name}:{fn}" for p in INDEX_FILES for fn in HANDLERS if "認証" not in blocks[p][fn]]
    results.append(_hyp("H4", "両ファイル: 401時に管理者認証が必要と明示",
                        not miss, f"未明示={miss or 'なし'}"))

    miss = [f"{p.name}:{fn}" for p in INDEX_FILES for fn in HANDLERS if "STATIC_DEMO" not in blocks[p][fn]]
    results.append(_hyp("H5", "両ファイル: 静的デモ(404)フォールバックを保持(CEOデモ不変)",
                        not miss, f"欠落={miss or 'なし'}"))

    remain = [f"{p.name}:{fn}" for p in INDEX_FILES for fn in HANDLERS if "endpoint unavailable" in blocks[p][fn]]
    results.append(_hyp("H6", "旧握りつぶし表現(...endpoint unavailable のみthrow)が除去済み",
                        not remain, f"残存={remain or 'なし'}"))

    drift = [fn for fn in HANDLERS if blocks[idx][fn] != blocks[src][fn]]
    results.append(_hyp("H7", "index.html と src/index.html の両ローダーがバイト等価",
                        not drift, f"ドリフト={drift or 'なし'}"))

    wbs_text = WBS_PATH.read_text(encoding="utf-8", errors="replace") if WBS_PATH.exists() else ""
    uat_text = UAT_SPEC.read_text(encoding="utf-8", errors="replace") if UAT_SPEC.exists() else ""
    wbs_ok = bool(re.search(r"(^|\n)T886\t", wbs_text))
    uat_ok = "TS-18" in uat_text and "T886" in uat_text
    results.append(_hyp("H8", "WBSにT886・UAT仕様書にTS-18(T886)が実在",
                        wbs_ok and uat_ok, f"WBS_T886={wbs_ok}, UAT_TS18={uat_ok}"))

    route_ok = ('@app.get("/api/admin/operations-dashboard")' in app_text
                and '@app.get("/api/admin/operations-dashboard/report.csv"' in app_text)
    auth_ok = app_text.count("Depends(verify_credentials)") >= 1 and "operations-dashboard" in app_text
    results.append(_hyp("H9", "src/app.py: 管理者ダッシュボードAPIが実在しBasic認証(401)必須",
                        route_ok and auth_ok, f"route={route_ok}, auth={auth_ok}"))

    prior_ok = all(h["passed"] for h in results)
    results.append(_hyp("H10", "管理者ローダーのエラー握りつぶし解消が完全(ドリフト0)",
                        prior_ok, f"先行ドリフト={'なし' if prior_ok else 'あり'}"))

    return {
        "task": "T886",
        "handlers": HANDLERS,
        "index_files": [str(p.relative_to(PROJECT_ROOT)) for p in INDEX_FILES],
        "hypotheses": results,
        "all_passed": all(h["passed"] for h in results),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 管理者ダッシュボード読込エラー透明化 監査 (T886)",
        "",
        f"- 対象ローダー: {', '.join(report['handlers'])}",
        f"- 対象ファイル: {', '.join(report['index_files'])}",
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
        "> 401(資格情報ミス=運用者の最頻問題)を汎用文言で隠さず日本語で明示。",
        "> 静的GitHub Pagesデモ(当API 404)は従来の静的デモ表示にフォールバック(CEO共有デモ不変)。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit admin dashboard error handling (T886, 10 hypotheses)")
    parser.add_argument("--json", default=str(DEFAULT_JSON))
    parser.add_argument("--md", default=str(DEFAULT_MD))
    args = parser.parse_args()

    report = evaluate()
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.md).write_text(render_markdown(report), encoding="utf-8")

    passed = sum(1 for h in report["hypotheses"] if h["passed"])
    print(f"[admin-dashboard-audit] {passed}/{len(report['hypotheses'])} hypotheses passed "
          f"-> {'ALL PASS' if report['all_passed'] else 'FAIL'}")
    for h in report["hypotheses"]:
        print(f"  {'PASS' if h['passed'] else 'FAIL'} {h['id']}: {h['title']} ({h['detail']})")
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
