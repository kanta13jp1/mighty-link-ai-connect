"""Fail-closed evidence audit for the 2026-08-24 paid-launch decision pack.

The decision pack must distinguish measured facts from targets, simulations,
and human approvals. A structurally valid document is not evidence that legal,
SLA, cost, sales-accuracy, or operational sign-off gates are complete.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import audit_legal_disclosures as legal
import audit_pricing_consistency as pricing


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "docs" / "PAID_LAUNCH_GO_NO_GO_DECISION_PACK_2026-08-24.md"
SALES = ROOT / "exports" / "sales_email_extraction_review.json"
MONTHLY_QUALITY = ROOT / "exports" / "monthly_quality_kpi_2026-06.json"
COST = ROOT / "exports" / "weekly_cost_dashboard.json"
SIGNOFF = ROOT / "docs" / "INFRA_HEARING_SIGN_OFF_PACK_2026-08-07.md"
DEFAULT_JSON = ROOT / "exports" / "paid_launch_evidence_audit.json"
DEFAULT_MD = ROOT / "exports" / "paid_launch_evidence_audit.md"


UNSUPPORTED_CLAIMS = (
    "適合率80%以上を維持・検証完了",
    "精度80%以上を実証",
    "成約時間 97% 削減の実測値",
    "1日1,000件スケール処理",
    "未確定マーカー0件",
    "弁護士最終確定のサインオフを確認",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _hyp(identifier: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": identifier, "title": title, "passed": bool(passed), "detail": detail}


def evidence_snapshot() -> dict[str, Any]:
    sales = read_json(SALES)
    monthly = read_json(MONTHLY_QUALITY)
    cost = read_json(COST)
    legal_report = legal.run_audit()
    pricing_results = pricing.evaluate()
    return {
        "sales": sales,
        "monthly": monthly,
        "cost": cost,
        "legal": legal_report,
        "pricing": pricing_results,
        "signoff_text": read_text(SIGNOFF),
    }


def evaluate(
    pack_text: str | None = None,
    snapshot: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    text = read_text(PACK) if pack_text is None else pack_text
    data = evidence_snapshot() if snapshot is None else snapshot
    sales = data.get("sales", {})
    monthly = data.get("monthly", {})
    cost = data.get("cost", {})
    legal_report = data.get("legal", {})
    pricing_results = data.get("pricing", [])
    signoff_text = str(data.get("signoff_text", ""))

    results: list[dict[str, Any]] = []
    results.append(_hyp("H1", "8/24経営判断パッケージが存在", bool(text), PACK.name))

    input_count = sales.get("input_count")
    model_name = str(sales.get("model_name", ""))
    fallback_used = sales.get("fallback_used")
    sales_ok = (
        input_count is not None
        and str(input_count) in text
        and model_name in text
        and str(fallback_used).lower() in text.lower()
        and "ラベル付き正解データ" in text
        and "未検証" in text
    )
    results.append(_hyp(
        "H2",
        "営業メール証拠の件数・モデル・fallback・精度限界を明記",
        sales_ok,
        f"input_count={input_count}, model={model_name or 'missing'}, fallback={fallback_used}",
    ))

    false_claims = [claim for claim in UNSUPPORTED_CLAIMS if claim in text]
    results.append(_hyp(
        "H3",
        "未立証の精度・削減率・法務完了を実績として断定しない",
        not false_claims,
        f"unsupported_claims={false_claims or 'なし'}",
    ))

    kpi = monthly.get("kpi", {})
    sla_unmeasured = all(
        kpi.get(key) is None
        for key in ("availability_pct", "p95_response_seconds", "error_5xx_pct")
    )
    sla_ok = sla_unmeasured and "月間SLA実績は未計測" in text and "99.9%は目標値" in text
    results.append(_hyp(
        "H4",
        "SLA目標と月間実績を分離し、未計測を明示",
        sla_ok,
        f"availability={kpi.get('availability_pct')}, p95={kpi.get('p95_response_seconds')}",
    ))

    actuals = cost.get("sources", {}).get("actuals")
    cost_status = cost.get("overall_status")
    cost_ok = (
        actuals == "not configured"
        and cost_status in ("unknown", "warning")
        and "実請求データ未接続" in text
        and ("overall_status=" in text)
    )
    results.append(_hyp(
        "H5",
        "実コスト未接続を黒字・固定費ゼロの実績へ読み替えない",
        cost_ok,
        f"actuals={actuals}, overall_status={cost_status}",
    ))

    placeholder_count = legal_report.get("placeholder_count")
    legal_ok = (
        isinstance(placeholder_count, int)
        and str(placeholder_count) in text
        and "法務・弁護士サインオフ未完了" in text
    )
    results.append(_hyp(
        "H6",
        "法定開示の構造PASSと未確定項目・人間承認を分離",
        legal_ok,
        f"placeholder_count={placeholder_count}",
    ))

    signoff_ok = "要人間確認" in signoff_text and "インフラ責任者のサインオフは未確認" in text
    results.append(_hyp(
        "H7",
        "インフラ提出パックを人間承認済み証跡として扱わない",
        signoff_ok,
        "human_signoff=unverified" if signoff_ok else "sign-off wording is not fail-closed",
    ))

    pricing_passed = bool(pricing_results) and all(result.get("passed") for result in pricing_results)
    pricing_h8 = next((result for result in pricing_results if result.get("id") == "H8"), {})
    pricing_ok = pricing_passed and "料金整合ガードはPASS" in text and "未確定マーカー3件" in text
    results.append(_hyp(
        "H8",
        "価格ドリフトPASSと価格関連の未確定事項を併記",
        pricing_ok,
        str(pricing_h8.get("detail", "missing")),
    ))

    stripe_ok = (
        "2026-08-19" in text
        and "Stripe Billing Meters" in text
        and "Metronomeへの移行必須ではない" in text
        and "R143" in text
    )
    results.append(_hyp(
        "H9",
        "現行Stripe公式Docsに基づく方式判断を記録",
        stripe_ok,
        "Billing Meters retained; reassess after Go before live activation",
    ))

    decision_ok = "現時点の推奨判定: NO-GO" in text and "Goへ変更できる条件" in text
    results.append(_hyp(
        "H10",
        "未完了の人間ゲートがある間はfail-closedでNO-GO",
        decision_ok,
        "decision=NO-GO until evidence gates close" if decision_ok else "decision boundary missing",
    ))
    return results


def run_audit() -> dict[str, Any]:
    results = evaluate()
    return {
        "task_id": "T988",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "passed": all(result["passed"] for result in results),
        "hypotheses": results,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 8/24有償化Go/No-Go 証拠整合監査 (T988)",
        "",
        f"- 総合判定: **{'PASS' if report['passed'] else 'FAIL'}**",
        f"- 生成日時: `{report['generated_at']}`",
        "",
        "| 仮説 | 検証内容 | 判定 | 根拠 |",
        "| --- | --- | --- | --- |",
    ]
    for result in report["hypotheses"]:
        verdict = "PASS" if result["passed"] else "FAIL"
        detail = str(result["detail"]).replace("|", "/")
        lines.append(f"| {result['id']} | {result['title']} | {verdict} | {detail} |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")

    report = run_audit()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.md.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
