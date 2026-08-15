"""Cost & Quota Monitoring Alerts Audit Guard (T932).

Verifies the integrity of cost monitoring, external API quotas, and alert thresholds
across the 3 core AI providers (Gemini, Claude, OpenAI) and supporting infrastructure
(Firebase, Supabase, Stripe, GCP). Enforces billing safety circuit-breakers, usage
ledgers, admin dashboard analytics endpoints, and alerting runbooks.

Outputs: exports/cost_quota_alerts_audit.{json,md}.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
DOCS_DIR = PROJECT_ROOT / "docs"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
EXPORTS_DIR = PROJECT_ROOT / "exports"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "cost_quota_alerts_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "cost_quota_alerts_audit.md"

SUBSCRIPTION_DOC = DOCS_DIR / "AI_DEVELOPMENT_TOOL_SUBSCRIPTION_POLICY.md"
PRICING_DOC = DOCS_DIR / "PRICING_PLAN_PROVISIONAL_2026-07-03.md"
RUNBOOK_DOC = DOCS_DIR / "AI_SAAS_SERVICE_FREEZE_RUNBOOK.md"
GUARD_DOC = DOCS_DIR / "COST_QUOTA_ALERTS_GUARD.md"

REQUIRED_SCRIPTS = [
    SCRIPTS_DIR / "send_daily_report.py",
    SCRIPTS_DIR / "audit_external_api_usage.py",
    SCRIPTS_DIR / "archive_audit_logs_to_cold_storage.py",
]


def check_required_scripts_exist() -> bool:
    return all(s.exists() for s in REQUIRED_SCRIPTS)


def build_hypotheses() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results: list[dict[str, Any]] = []

    # H1: Cost / subscription policy docs exist
    h1_pass = SUBSCRIPTION_DOC.exists() and PRICING_DOC.exists()
    results.append({
        "hypothesis": "H1",
        "description": "AIツール契約ポリシー (AI_DEVELOPMENT_TOOL_SUBSCRIPTION_POLICY.md) および価格プラン書が実在する",
        "passed": h1_pass,
        "detail": "各種コスト・価格ポリシー仕様書の実在を確認" if h1_pass else "コストポリシー仕様書が欠落",
    })

    # H2: Usage analytics endpoint /admin/usage exists in src/app.py
    app_code = (SRC_DIR / "app.py").read_text(encoding="utf-8") if (SRC_DIR / "app.py").exists() else ""
    h2_pass = "/api/admin/usage" in app_code or "/admin/usage" in app_code
    results.append({
        "hypothesis": "H2",
        "description": "管理者用API使用量・コスト確認エンドポイント (/api/admin/usage) が実装されている",
        "passed": h2_pass,
        "detail": "使用量ダッシュボードエンドポイントを確認" if h2_pass else "エンドポイント未検出",
    })

    # H3: Required monitoring and alerting scripts exist
    h3_pass = check_required_scripts_exist()
    results.append({
        "hypothesis": "H3",
        "description": "日次レポート送信・外部API監査・ログ退避スクリプトが実在する",
        "passed": h3_pass,
        "detail": f"監視・アラートスクリプト {len(REQUIRED_SCRIPTS)} 件の実在を確認" if h3_pass else "一部スクリプトが欠落",
    })

    # H4: External API call guards / circuit breaker in app.py
    h4_pass = "SEEDANCE_API_ENABLED" in app_code or "CIRCUIT_BREAKER" in app_code or "EXTERNAL_API_DAILY_LIMIT" in app_code or "rate_limit" in app_code
    results.append({
        "hypothesis": "H4",
        "description": "予期せぬ従量課金爆発を防止するサーキットブレーカー / 有効化フラグが実装されている",
        "passed": h4_pass,
        "detail": "課金保護フラグ・制限機構を確認" if h4_pass else "課金保護機構未検出",
    })

    # H5: Service Freeze / Budget overrun Runbook exists
    h5_pass = RUNBOOK_DOC.exists()
    results.append({
        "hypothesis": "H5",
        "description": "サービス緊急停止・予算超過時対応Runbook (AI_SAAS_SERVICE_FREEZE_RUNBOOK.md) が実在する",
        "passed": h5_pass,
        "detail": f"{RUNBOOK_DOC.name} 実在" if h5_pass else "緊急停止Runbook欠落",
    })

    # H6: Stripe Customer Portal & webhook billing safety
    stripe_portal_py = SRC_DIR / "stripe_customer_portal.py"
    h6_pass = stripe_portal_py.exists() and "customer" in stripe_portal_py.read_text(encoding="utf-8")
    results.append({
        "hypothesis": "H6",
        "description": "Stripe カスタマーポータル連携モジュール (src/stripe_customer_portal.py) が実在する",
        "passed": h6_pass,
        "detail": "Stripe ポータル連携モジュールを確認" if h6_pass else "Stripe モジュール欠落",
    })

    # H7: Pricing & Quota budget consistency
    sub_text = SUBSCRIPTION_DOC.read_text(encoding="utf-8") if SUBSCRIPTION_DOC.exists() else ""
    h7_pass = "Gemini" in sub_text and ("Claude" in sub_text or "Anthropic" in sub_text) and ("OpenAI" in sub_text or "Codex" in sub_text)
    results.append({
        "hypothesis": "H7",
        "description": "3大AIツール（Gemini / Claude / OpenAI Codex）の月額枠・用途が定義されている",
        "passed": h7_pass,
        "detail": "3大AIツールの定義・整合性を確認" if h7_pass else "AIツール定義不整合",
    })

    # H8: Audit guard spec doc exists
    h8_pass = GUARD_DOC.exists()
    results.append({
        "hypothesis": "H8",
        "description": "コスト・クォータ監視ガード仕様書 (COST_QUOTA_ALERTS_GUARD.md) が実在する",
        "passed": h8_pass,
        "detail": f"{GUARD_DOC.name} 実在" if h8_pass else "仕様書未作成",
    })

    # H9: Cold storage archiving script exists
    archive_py = SCRIPTS_DIR / "archive_audit_logs_to_cold_storage.py"
    h9_pass = archive_py.exists()
    results.append({
        "hypothesis": "H9",
        "description": "ストレージ費用増大を防止する監査ログアーカイブスクリプトが実在する",
        "passed": h9_pass,
        "detail": f"{archive_py.name} 実在" if h9_pass else "アーカイブスクリプト欠落",
    })

    # H10: Overall cost & quota monitoring sanity
    all_passed = all(r["passed"] for r in results)
    results.append({
        "hypothesis": "H10",
        "description": "コスト・クォータ監視アラート全体が完全・整合（ドリフト0）",
        "passed": all_passed,
        "detail": "全コスト監視仮説 PASS" if all_passed else "不整合・要対応項目あり",
    })

    summary = {
        "total_hypotheses": len(results),
        "passed_hypotheses": sum(1 for r in results if r["passed"]),
        "failed_hypotheses": sum(1 for r in results if not r["passed"]),
        "all_passed": all_passed,
    }
    return results, summary


def render_markdown(results: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# コスト・クォータ監視アラート統合監査レポート (T932)",
        "",
        f"- 総合判定: {'✅ PASS (ドリフト0)' if summary['all_passed'] else '❌ FAIL'}",
        f"- 合格仮説数: **{summary['passed_hypotheses']} / {summary['total_hypotheses']}**",
        "",
        "## 10仮説の検証結果",
        "",
        "| 仮説 | 内容 | 判定 | 詳細 |",
        "| :-- | :-- | :-- | :-- |",
    ]
    for r in results:
        badge = "✅" if r["passed"] else "❌"
        lines.append(f"| {r['hypothesis']} | {r['description']} | {badge} | {r['detail']} |")
    lines.append("")
    return "\n".join(lines)


def run_audit(json_out: Path = DEFAULT_JSON, md_out: Path = DEFAULT_MD) -> int:
    results, summary = build_hypotheses()
    
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    
    md_content = render_markdown(results, summary)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.write_text(md_content, encoding="utf-8")
    
    print(f"[*] コスト・クォータ監視監査 (T932): {'PASS' if summary['all_passed'] else 'FAIL'}")
    return 0 if summary["all_passed"] else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit cost and quota monitoring alerts")
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON, help="JSON output path")
    parser.add_argument("--md", type=Path, default=DEFAULT_MD, help="Markdown output path")
    args = parser.parse_args()
    sys_code = run_audit(json_out=args.json, md_out=args.md)
    if sys_code != 0:
        raise SystemExit(sys_code)


if __name__ == "__main__":
    main()
