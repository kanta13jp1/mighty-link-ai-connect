"""UAT ⇄ API coverage traceability guard (T892).

audit_uat_test_spec.py (T882) checks the *forward* direction: every API a UAT
case names really exists. This harness adds the *reverse* direction that a
test-first project needs: every GA user-facing endpoint must have a
human-executable UAT case, and no new endpoint may ship unclassified.

Every FastAPI endpoint in src/app.py is partitioned into:
* REQUIRED_GA_ENDPOINTS — user-facing GA surface that MUST have a UAT case, and
* EXEMPT_ENDPOINTS — internal / debug / demo / gated endpoints, each with a
  documented reason, that intentionally need no UAT case.

Ten hypotheses keep the partition exhaustive and the required set fully covered,
so adding an endpoint without a coverage decision fails CI.

Output: exports/uat_api_coverage_audit.{json,md}. No secrets emitted.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PY = PROJECT_ROOT / "src" / "app.py"
SPEC = PROJECT_ROOT / "docs" / "UAT_TEST_SPECIFICATION.md"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "uat_api_coverage_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "uat_api_coverage_audit.md"

# GA user-facing endpoints that MUST be covered by a human-executable UAT case.
REQUIRED_GA_ENDPOINTS = {
    "/api/employee-assessment/responses",
    "/api/employee-assessment/responses/summary",
    "/api/attendance/punch",
    "/api/attendance/timesheet/parse",
    "/api/attendance/timesheet/approve",
    "/api/sales-email/matches",
    "/api/sales-email/reviews",
    "/api/sales-email/reviews/summary",
    "/api/sales-email/sync",
    "/api/sales-email/analytics",
    "/api/admin/operations-dashboard",
    "/api/match",
    "/api/parse",
    "/api/feedback",
    "/api/feedback/summary",
    "/api/support/request",
    "/api/support/summary",
    "/api/health",
    "/api/user-data/export",
    "/api/aptitude-demo/questions",
    "/api/aptitude-demo/evaluate",
    "/api/aptitude-demo/legend",
    # T752 オンボーディング/アクティベーション (TS-36, gate PUBLIC-06)
    "/api/onboarding/state",
    "/api/onboarding/progress",
    "/api/onboarding/activate",
}

# Internal / debug / demo / gated endpoints that need no UAT case (reason noted).
EXEMPT_ENDPOINTS = {
    "/api/admin/managed-agents/cost-simulation": "内部: 管理エージェント費用シミュレーション",
    "/api/admin/operations-dashboard/report.csv": "内部: TS-07で被覆済みダッシュボードのCSV下位形式",
    "/api/admin/usage": "内部: API利用量台帳(運用)",
    "/api/admin/usage/export": "内部: API利用量エクスポート(運用)",
    "/api/analytics/event": "内部: 匿名テレメトリのビーコン",
    "/api/attendance/summary": "内部: 認証必須の勤怠集計(TS-07ダッシュボード範囲)",
    "/api/audit/recent": "内部: 監査ログ取得(検証補助)",
    "/api/auth/me": "内部: 認証状態ヘルパー",
    "/api/billing/customer-portal/session": "gated: T862有償化判断前・live課金未有効",
    "/api/db-test": "内部: デバッグ用DB接続確認",
    "/api/engineers": "内部: 比較ボード用データ取得ヘルパー",
    "/api/favicon.ico": "内部: Favicon取得エイリアス",
    "/api/jobs": "内部: 比較ボード用データ取得ヘルパー",
    "/api/knowledge-flow/generate": "内部: ナレッジ連携デモ生成ツール",
    "/api/knowledge-flow/status": "内部: ナレッジ連携デモ状態",
    "/api/matches": "内部: 診断マッチ一覧の読取ヘルパー",
    "/api/ai/extract/structured": "内部: 構造化AIプロファイル抽出(T304開発支援・非直接GA導線)",
    "/api/extract-structured": "内部: 構造化AIプロファイル抽出エイリアス",
    "/api/seedance/video-demo": "非GA: Seedance動画デモ(T848で本番非採用に凍結)",
    "/api/seedance/video-task/{task_id}": "非GA: Seedance動画タスク(凍結)",
    "/api/sales-email/proposal": "内部: 営業提案メール生成ドラフト(TS-08マッチング詳細スコープ)",
    "/api/sync": "内部: サーバー内部同期",
}

# GA core domains that must each have at least one required, covered endpoint.
CORE_DOMAINS = {
    "診断/適性": ["/api/employee-assessment", "/api/aptitude-demo", "/api/match"],
    "勤怠": ["/api/attendance/punch", "/api/attendance/timesheet"],
    "営業メール": ["/api/sales-email/"],
    "管理者": ["/api/admin/operations-dashboard"],
    "サポート": ["/api/support/"],
    "フィードバック": ["/api/feedback"],
    "データエクスポート": ["/api/user-data/export"],
}


def load_endpoints(app_py: Path = APP_PY) -> set[str]:
    """Return the /api/ contract surface (page/static routes are out of scope)."""
    text = app_py.read_text(encoding="utf-8", errors="replace")
    return {p for p in re.findall(r'@app\.(?:get|post|put|delete|patch)\("([^"]+)"', text)
            if p.startswith("/api/")}


def load_uat_apis(spec: Path = SPEC) -> set[str]:
    if not spec.exists():
        return set()
    return set(re.findall(r"/api/[A-Za-z0-9/_{}-]+", spec.read_text(encoding="utf-8", errors="replace")))


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate(endpoints: set[str], uat_apis: set[str], uat_case_count: int) -> list[dict[str, Any]]:
    required = set(REQUIRED_GA_ENDPOINTS)
    exempt = set(EXEMPT_ENDPOINTS)
    results: list[dict[str, Any]] = []

    results.append(_hyp("H1", "エンドポイント30件以上かつUATケース20件以上(sanity)",
                        len(endpoints) >= 30 and uat_case_count >= 20,
                        f"endpoints={len(endpoints)}, UATケース={uat_case_count}"))

    bad_forward = sorted(a for a in uat_apis if a not in endpoints)
    results.append(_hyp("H2", "UAT参照APIが全てsrc/app.pyに実在(forward整合)",
                        not bad_forward, f"未実在={bad_forward[:5] or 'なし'}"))

    uncovered = sorted(e for e in required if e not in uat_apis)
    results.append(_hyp("H3", "全REQUIRED(GAユーザー向け)エンドポイントがUATで被覆(reverse)",
                        not uncovered, f"未被覆={uncovered or 'なし'}"))

    unclassified = sorted(e for e in endpoints if e not in required and e not in exempt)
    results.append(_hyp("H4", "全app.pyエンドポイントがREQUIRED∪EXEMPTに分類済み(未分類0)",
                        not unclassified, f"未分類={unclassified or 'なし'}"))

    overlap = sorted(required & exempt)
    results.append(_hyp("H5", "REQUIRED∩EXEMPT=∅(二重分類なし)",
                        not overlap, f"重複={overlap or 'なし'}"))

    stale_req = sorted(e for e in required if e not in endpoints)
    results.append(_hyp("H6", "全REQUIREDがapp.pyに実在(stale required無し)",
                        not stale_req, f"stale={stale_req or 'なし'}"))

    stale_ex = sorted(e for e in exempt if e not in endpoints)
    results.append(_hyp("H7", "全EXEMPTがapp.pyに実在(stale exempt無し)",
                        not stale_ex, f"stale={stale_ex or 'なし'}"))

    missing_dom = []
    for dom, prefixes in CORE_DOMAINS.items():
        covered = any(
            any(e.startswith(p) for p in prefixes) and e in uat_apis
            for e in required
        )
        if not covered:
            missing_dom.append(dom)
    results.append(_hyp("H8", "GA中核ドメインが各≥1の被覆エンドポイントを保有",
                        not missing_dom, f"未被覆ドメイン={missing_dom or 'なし'}"))

    covered_ct = sum(1 for e in required if e in uat_apis)
    ratio = covered_ct / len(required) if required else 1.0
    results.append(_hyp("H9", "REQUIREDカバレッジ率=100%",
                        ratio == 1.0, f"被覆={covered_ct}/{len(required)} ({ratio:.0%})"))

    no_prior_drift = all(h["passed"] for h in results)
    results.append(_hyp("H10", "UAT-API網羅が完全・整合(トレーサビリティドリフト0)",
                        no_prior_drift, f"先行ドリフト={'なし' if no_prior_drift else 'あり'}"))
    return results


def count_uat_cases(spec: Path = SPEC) -> int:
    if not spec.exists():
        return 0
    return len(re.findall(r"^###\s+TS-\d+", spec.read_text(encoding="utf-8", errors="replace"), re.M))


def run_audit() -> dict[str, Any]:
    endpoints = load_endpoints()
    uat_apis = load_uat_apis()
    case_count = count_uat_cases()
    hyps = evaluate(endpoints, uat_apis, case_count)
    return {
        "task": "T892",
        "endpoint_count": len(endpoints),
        "uat_case_count": case_count,
        "required_count": len(REQUIRED_GA_ENDPOINTS),
        "exempt_count": len(EXEMPT_ENDPOINTS),
        "hypotheses": hyps,
        "all_passed": all(h["passed"] for h in hyps),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# UAT-API網羅トレーサビリティ監査 (T892)",
        "",
        f"- エンドポイント数: **{report['endpoint_count']}** / UATケース: **{report['uat_case_count']}**",
        f"- REQUIRED(GA): **{report['required_count']}** / EXEMPT: **{report['exempt_count']}**",
        f"- 総合判定: {'✅ PASS (ドリフト0)' if report['all_passed'] else '❌ FAIL'}",
        "",
        "## 10仮説の検証結果",
        "",
        "| 仮説 | 内容 | 判定 | 詳細 |",
        "| :-- | :-- | :-- | :-- |",
    ]
    for h in report["hypotheses"]:
        mark = "✅" if h["passed"] else "❌"
        lines.append(f"| {h['id']} | {h['title']} | {mark} | {h['detail']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=str(DEFAULT_JSON))
    parser.add_argument("--md", default=str(DEFAULT_MD))
    args = parser.parse_args()
    report = run_audit()
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.md).write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
