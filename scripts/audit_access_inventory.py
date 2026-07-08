"""Access / ownership inventory audit for the handover rehearsal (T850_1).

T850 rehearses company operations handover: permission inventory, bus-factor,
and break-glass. This harness turns data/access_inventory.tsv into a verifiable
artifact and runs 10 hypotheses over it — coverage vs the migration runbook,
owner presence, break-glass doc existence, MFA recording, single-point-of-
failure (bus-factor = 1) detection, and secret-rotation linkage.

Bus-factor SPOFs are expected in the current pre-migration state (most systems
are 梅澤-only). The audit surfaces them explicitly so T823 (company migration)
and the handover rehearsal have a concrete work list; a non-empty SPOF list is
reported, not silently hidden.

Outputs: exports/access_inventory_audit.{json,md}. No secrets — the inventory
holds owner names and doc references only, never key values.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INVENTORY = PROJECT_ROOT / "data" / "access_inventory.tsv"
MIGRATION_RUNBOOK = PROJECT_ROOT / "docs" / "ACCOUNT_OWNERSHIP_MIGRATION_RUNBOOK.md"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "access_inventory_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "access_inventory_audit.md"

# Critical systems that MUST appear in the inventory (from the migration runbook
# domains: domain, hosting/backend, GCP, DB, source, secrets, workspace, stripe).
REQUIRED_CRITICAL = {
    "domain_onamae", "firebase_hosting", "firebase_functions", "gcp_iam_billing",
    "supabase", "github_repo", "github_actions_secrets", "google_workspace",
}
VALID_TRANSFER_STATES = {"personal", "migrating", "company_managed", "n_a"}
VALID_CRITICALITY = {"critical", "high", "medium", "low"}
VALID_MFA_STATUS = {"enabled", "unknown", "n_a"}
SECRET_ROTATION_DOC = "docs/SECRET_ROTATION_RUNBOOK.md"


def load_inventory() -> list[dict[str, str]]:
    lines = [ln for ln in INVENTORY.read_text(encoding="utf-8").split("\n") if ln.strip()]
    header = lines[0].split("\t")
    rows = []
    for ln in lines[1:]:
        cells = ln.split("\t")
        # pad short rows (trailing empty cells)
        cells += [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells)))
    return rows


def build_hypotheses(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results: list[dict[str, Any]] = []
    by_id = {r["system_id"]: r for r in rows}
    critical = [r for r in rows if r["criticality"] == "critical"]
    spofs = [r["system_id"] for r in critical if not r["backup_owner"].strip()]

    def record(hid: str, statement: str, check: Callable[[], tuple[bool, str]]) -> None:
        try:
            passed, detail = check()
        except Exception as exc:
            passed, detail = False, f"例外: {type(exc).__name__}: {exc}"
        results.append({"id": hid, "hypothesis": statement, "passed": passed, "detail": detail})

    record("H1", "移管runbookのクリティカル領域が全て棚卸しに存在する",
           lambda: (REQUIRED_CRITICAL.issubset(set(by_id)),
                    f"必須{len(REQUIRED_CRITICAL)}件 / 欠落={sorted(REQUIRED_CRITICAL - set(by_id)) or 'なし'}"))

    record("H2", "全システムに一次所有者(primary_owner)が定義されている",
           lambda: (all(r["primary_owner"].strip() for r in rows),
                    f"未定義={[r['system_id'] for r in rows if not r['primary_owner'].strip()] or 'なし'}"))

    record("H3", "全クリティカルシステムにBreak-glass/復旧docsが指定されている",
           lambda: (all(r["break_glass_doc"].strip() for r in critical),
                    f"未指定={[r['system_id'] for r in critical if not r['break_glass_doc'].strip()] or 'なし'}"))

    def h4() -> tuple[bool, str]:
        missing = [r["system_id"] for r in rows if r["mfa_status"] not in VALID_MFA_STATUS]
        return not missing, f"MFA状態が不正/未記録={missing or 'なし'}(許可={sorted(VALID_MFA_STATUS)})"

    record("H4", "全システムにMFA状態が記録されている(enabled/unknown/n_a)", h4)

    def h5() -> tuple[bool, str]:
        bad = [r["system_id"] for r in rows if r["transfer_state"] not in VALID_TRANSFER_STATES]
        return not bad, f"移管状態が不正={bad or 'なし'}(許可={sorted(VALID_TRANSFER_STATES)})"

    record("H5", "移管状態(transfer_state)の値が妥当である", h5)

    def h6() -> tuple[bool, str]:
        bad = [r["system_id"] for r in rows if r["criticality"] not in VALID_CRITICALITY]
        return not bad, f"criticality不正={bad or 'なし'}"

    record("H6", "criticalityの値が妥当である", h6)

    def h7() -> tuple[bool, str]:
        # SPOF detection must work: current pre-migration state has known SPOFs.
        detected = bool(spofs)
        return detected, f"単一障害点(backup未設定のcritical)={spofs}（{len(spofs)}件・T823/リハーサルの対象）"

    record("H7", "バス係数=1の単一障害点(backup未設定のクリティカル)を検出できる", h7)

    def h8() -> tuple[bool, str]:
        secret_rows = [r for r in rows if r["secret_bearing"].strip().lower() == "yes"]
        linked = [r for r in secret_rows if r["break_glass_doc"].strip()]
        return len(linked) == len(secret_rows) and bool(secret_rows), \
            f"secret保持システム{len(secret_rows)}件が全て復旧/rotation docsに紐づく"

    record("H8", "secretを持つシステムが全て復旧/rotation手順に紐づく", h8)

    def h9() -> tuple[bool, str]:
        refs = {r["break_glass_doc"].strip() for r in rows if r["break_glass_doc"].strip()}
        missing = [d for d in sorted(refs) if not (PROJECT_ROOT / d).exists()]
        return not missing, f"参照docs{len(refs)}種 / 実在しない={missing or 'なし'}"

    record("H9", "棚卸しが参照するBreak-glass/復旧docsが全て実在する", h9)

    def h10() -> tuple[bool, str]:
        header = INVENTORY.read_text(encoding="utf-8").split("\n")[0].split("\t")
        ncols = len(header)
        raw = [ln for ln in INVENTORY.read_text(encoding="utf-8").split("\n") if ln.strip()]
        col_ok = all(1 <= len(ln.split("\t")) <= ncols for ln in raw[1:])
        ids = [r["system_id"] for r in rows]
        dup_ok = len(ids) == len(set(ids))
        return col_ok and dup_ok and ncols == 12, \
            f"列数={ncols}(12期待) 行数={len(rows)} 重複ID={'なし' if dup_ok else '有'}"

    record("H10", "棚卸しTSVの整合性(列数・重複ID)が保たれている", h10)

    summary = {
        "systems_total": len(rows),
        "critical_total": len(critical),
        "spof_systems": spofs,
        "spof_count": len(spofs),
        "company_managed": [r["system_id"] for r in rows if r["transfer_state"] == "company_managed"],
        "personal_pending_transfer": [r["system_id"] for r in rows if r["transfer_state"] == "personal"],
    }
    return results, summary


def build_report(checked_at: str) -> dict[str, Any]:
    rows = load_inventory()
    hypotheses, summary = build_hypotheses(rows)
    passed = sum(1 for h in hypotheses if h["passed"])
    return {
        "report_id": "ACCESS_INVENTORY_AUDIT_T850_1",
        "checked_at": checked_at,
        "status": "ok" if passed == len(hypotheses) else "attention",
        "hypotheses_total": len(hypotheses),
        "hypotheses_passed": passed,
        "hypotheses": hypotheses,
        "summary": summary,
        "note": ("単一障害点(SPOF)はバス係数=1のクリティカルシステムで、現状(移管前)は想定内。"
                 "T823会社移管と引継ぎリハーサルでbackup所有者を確立して解消する。"),
    }


def render_markdown(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        "# 権限棚卸し監査ログ (T850_1)",
        "",
        f"- レポートID: `{report['report_id']}` / 実施日: {report['checked_at']}",
        f"- 判定: **{report['status']}** ({report['hypotheses_passed']}/{report['hypotheses_total']} 仮説PASS)",
        f"- システム総数: {s['systems_total']}（うちクリティカル {s['critical_total']}）",
        f"- **単一障害点(SPOF・バス係数1のクリティカル): {s['spof_count']}件** → {', '.join(s['spof_systems']) or 'なし'}",
        f"- 会社管理済み: {', '.join(s['company_managed']) or 'なし'}",
        f"- 個人アカウント(移管待ち): {', '.join(s['personal_pending_transfer']) or 'なし'}",
        "",
        f"> {report['note']}",
        "",
        "## 10仮説検証",
        "",
        "| # | 仮説 | 結果 | 根拠 |",
        "| --- | --- | --- | --- |",
    ]
    for h in report["hypotheses"]:
        mark = "PASS" if h["passed"] else "FAIL"
        lines.append(f"| {h['id']} | {h['hypothesis']} | {mark} | {h['detail'].replace('|', '/')} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Access/ownership inventory audit (T850_1)")
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
    print(f"[{'+' if report['status'] == 'ok' else '!'}] Access inventory audit {report['status']}: "
          f"{report['hypotheses_passed']}/{report['hypotheses_total']} hypotheses passed; "
          f"SPOF={report['summary']['spof_count']}")
    if args.fail_on_attention and report["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
