"""WBS completion evidence aggregator for the GA closure judgment (T849_1).

T849 is the capstone "development-complete judgment / WBS full-completion
evidence / GA closure". The gate review is produced by
generate_production_go_no_go_review.py; this aggregator is the complementary
WBS-completion + evidence-index view:

* WBS completion stats (by status / phase / owner) and overdue detection,
* an evidence index mapping each Claude-Code takeover subtask to its on-disk
  artifact (so "全完了証跡化" is verifiable, not asserted),
* the remaining-for-GA breakdown tied to the non-PASS gates, classified into
  human-gated vs other-lane so the closure owner sees exactly what is left.

Ten hypotheses verify the aggregation is coherent. Output:
exports/wbs_completion_evidence.{json,md}. No secrets.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WBS = PROJECT_ROOT / "data" / "WBS.tsv"
CRITERIA = PROJECT_ROOT / "data" / "release_go_no_go_criteria.tsv"
ISSUES = PROJECT_ROOT / "data" / "issues_tracker.tsv"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "wbs_completion_evidence.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "wbs_completion_evidence.md"

# Claude Code takeover subtasks and the artifact that proves each one.
EVIDENCE_INDEX = {
    "T780": "exports/gemini_model_migration_eval.md",
    "T845_1": "exports/ga_acceptance_e2e_report.md",
    "T778_1": "exports/sla_view_verification.md",
    "T817_7_1": "exports/sales_email_hardening_audit.md",
    "T782": "exports/read_load_distribution_simulation.md",
    "T876_1": "docs/APTITUDE_MOTIVATION_DEMO_PRIVACY_DESIGN.md",
    "T877_1": "tests/test_theme_toggle.py",
    "T850_1": "exports/access_inventory_audit.md",
    "T866_1": "docs/archive/historical_reports/POSTMORTEM_2026-07-04_R114_MISSING_PROD_TABLES.md" if (PROJECT_ROOT / "docs/archive/historical_reports/POSTMORTEM_2026-07-04_R114_MISSING_PROD_TABLES.md").exists() else "docs/POSTMORTEM_2026-07-04_R114_MISSING_PROD_TABLES.md",
    "T875": "exports/custom_domain_dns_diagnostic.md",
}
NON_PASS_STATES = {"BLOCKED", "HUMAN_GATE", "WARNING"}
HUMAN_KEYWORDS = ("人間", "寛太梅澤")
DEFERRED_REVIEW_MARKER = "【再評価待ち:"
JST = ZoneInfo("Asia/Tokyo")


def jst_today() -> str:
    """Return the operational reporting date in the project's JST timezone."""
    return datetime.now(JST).date().isoformat()


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    lines = [ln for ln in path.read_text(encoding="utf-8").split("\n") if ln.strip()]
    # tolerate both \n and stripped \r
    lines = [ln.rstrip("\r") for ln in lines]
    header = lines[0].split("\t")
    rows = []
    for ln in lines[1:]:
        cells = ln.split("\t")
        cells += [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells)))
    return header, rows


def load_wbs() -> list[dict[str, str]]:
    _, rows = read_tsv(WBS)
    return rows


def load_criteria() -> list[dict[str, str]]:
    _, rows = read_tsv(CRITERIA)
    return rows


def load_issues() -> list[dict[str, str]]:
    _, rows = read_tsv(ISSUES)
    return rows


def _issue_wbs_tokens(issue: dict[str, str]) -> set[str]:
    """Related-WBS tokens of an issue row (header is '関連 WBS'; tolerate no space)."""
    raw = issue.get("関連 WBS") or issue.get("関連WBS") or ""
    return {t.strip() for t in raw.split(";") if t.strip()}


def open_issue_blockers(criterion: dict[str, str], issues: list[dict[str, str]]) -> list[str]:
    """OPEN issue IDs that contradict a gate whose related WBS are all complete.

    A gate is only safe to re-evaluate to PASS when nothing is outstanding
    against it. An issue blocks the gate when it is still `open` AND either its
    related-WBS set intersects the gate's related WBS, or it is named in the
    gate's own related_issue column. Without this, "all related tasks 完了" alone
    would recommend flipping a GA gate green while a real defect is unresolved
    (e.g. R132 empties the sales-email PoC data behind PUBLIC-11).
    """
    gate_tasks = {t.strip() for t in (criterion.get("related_wbs") or "").split(";") if t.strip()}
    gate_issues = {t.strip() for t in (criterion.get("related_issue") or "").split(";") if t.strip()}
    blockers = []
    for issue in issues:
        if (issue.get("状態") or "").strip().lower() != "open":
            continue
        iid = (issue.get("ID") or "").strip()
        if _issue_wbs_tokens(issue) & gate_tasks or (iid and iid in gate_issues):
            blockers.append(iid)
    return sorted(set(blockers))


def build_stats(wbs: list[dict[str, str]], today: str) -> dict[str, Any]:
    status_key = "ステータス"
    end_key = "終了予定日"
    owner_key = "担当"
    phase_key = "大フェーズ"
    total = len(wbs)
    done = sum(1 for r in wbs if r.get(status_key) == "完了")
    in_progress = sum(1 for r in wbs if r.get(status_key) == "実行中")
    not_started = sum(1 for r in wbs if r.get(status_key) == "未着手")
    overdue = [r["タスクID"] for r in wbs
               if r.get(status_key) != "完了" and r.get(end_key, "") and r.get(end_key) < today]
    by_phase: dict[str, dict[str, int]] = {}
    for r in wbs:
        p = r.get(phase_key, "?")
        d = by_phase.setdefault(p, {"total": 0, "done": 0})
        d["total"] += 1
        if r.get(status_key) == "完了":
            d["done"] += 1
    incomplete_by_owner: dict[str, int] = {}
    for r in wbs:
        if r.get(status_key) != "完了":
            incomplete_by_owner[r.get(owner_key, "?")] = incomplete_by_owner.get(r.get(owner_key, "?"), 0) + 1
    return {
        "total": total, "done": done, "in_progress": in_progress, "not_started": not_started,
        "completion_rate_pct": round(100.0 * done / total, 1) if total else 0.0,
        "overdue_incomplete": overdue,
        "by_phase": by_phase,
        "incomplete_by_owner": incomplete_by_owner,
    }


def classify_remaining(criteria: list[dict[str, str]], wbs: list[dict[str, str]],
                       issues: list[dict[str, str]] | None = None) -> dict[str, Any]:
    wbs_by_id = {r["タスクID"]: r for r in wbs}
    issues = issues if issues is not None else load_issues()
    remaining = []
    reevaluate = []
    deferred_reviews = []
    for c in criteria:
        state = (c.get("current_state") or "").strip().upper()
        if state not in NON_PASS_STATES:
            continue
        tasks = [t for t in (c.get("related_wbs") or "").split(";") if t]
        open_tasks = [t for t in tasks if t in wbs_by_id and wbs_by_id[t].get("ステータス") != "完了"]
        # classify by owner of the open tasks
        human = any(any(k in wbs_by_id[t].get("担当", "") for k in HUMAN_KEYWORDS) for t in open_tasks)
        blockers = open_issue_blockers(c, issues)
        # A non-PASS gate whose related tasks are ALL complete (and is not a pure
        # human sign-off gate) is a candidate to re-evaluate to PASS — but only
        # when no OPEN issue still contradicts it. Otherwise it is outstanding
        # work, not a bookkeeping lag, and recommending PASS would flip a GA gate
        # green over a live defect.
        gate_class = "human_or_mixed" if human else "lane"
        if not open_tasks and state != "HUMAN_GATE":
            if blockers:
                gate_class = "blocked_by_open_issue"
            elif DEFERRED_REVIEW_MARKER in (c.get("notes") or ""):
                # A formally deferred paid-launch gate is intentionally not
                # eligible for an immediate PASS flip merely because its old
                # WBS rows were closed as deferred. Keep it fail-closed until
                # the named review creates and completes replacement work.
                gate_class = "deferred_review"
                deferred_reviews.append(c.get("criterion_id"))
            else:
                gate_class = "reevaluate_candidate"
                reevaluate.append(c.get("criterion_id"))
        remaining.append({
            "gate": c.get("criterion_id"),
            "state": state,
            "open_tasks": open_tasks,
            "open_issues": blockers,
            "class": gate_class,
        })
    return {"non_pass_gates": remaining,
            "count": len(remaining),
            "reevaluate_candidates": reevaluate,
            "deferred_reviews": deferred_reviews}


def build_hypotheses(wbs, criteria, stats, remaining) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    wbs_ids = {r["タスクID"] for r in wbs}

    def record(hid, statement, check):
        try:
            passed, detail = check()
        except Exception as exc:
            passed, detail = False, f"例外: {type(exc).__name__}: {exc}"
        results.append({"id": hid, "hypothesis": statement, "passed": passed, "detail": detail})

    record("H1", "WBSが解析でき、ステータス内訳の合計が総数に一致する",
           lambda: (stats["done"] + stats["in_progress"] + stats["not_started"] == stats["total"],
                    f"完了{stats['done']}+実行中{stats['in_progress']}+未着手{stats['not_started']}={stats['total']}"))

    record("H2", "完了率が算出され、9割超である",
           lambda: (stats["completion_rate_pct"] > 90.0,
                    f"完了率={stats['completion_rate_pct']}%（{stats['done']}/{stats['total']}）"))

    record("H3", "期限超過の未完了タスクを検出できる（可視化対象）",
           lambda: (isinstance(stats["overdue_incomplete"], list),
                    f"期限超過(未完了)={stats['overdue_incomplete'] or 'なし'}"))

    def h4():
        missing = []
        for c in criteria:
            for t in (c.get("related_wbs") or "").split(";"):
                if t and t not in wbs_ids:
                    missing.append(f"{c.get('criterion_id')}:{t}")
        return not missing, f"ゲート参照WBSの欠落={missing or 'なし'}"

    record("H4", "全ゲートのrelated_wbsがWBSに実在する", h4)

    def h5():
        missing = [f"{k}->{v}" for k, v in EVIDENCE_INDEX.items() if not (PROJECT_ROOT / v).exists()]
        return not missing, f"証跡ファイル{len(EVIDENCE_INDEX)}件 / 欠落={missing or 'なし'}"

    record("H5", "Claude Code巻き取りサブタスクの証跡ファイルが全て実在する", h5)

    def h6():
        # every evidence-index subtask exists in the WBS and is 完了
        by_id = {r["タスクID"]: r for r in wbs}
        bad = [k for k in EVIDENCE_INDEX if k not in by_id or by_id[k].get("ステータス") != "完了"]
        return not bad, f"証跡サブタスクが未完了/不在={bad or 'なし'}"

    record("H6", "証跡インデックスの各サブタスクがWBSで完了済みである", h6)

    record("H7", "非PASSゲートを残作業として抽出できる",
           lambda: (remaining["count"] >= 1,
                    f"非PASSゲート={remaining['count']}件: {[g['gate'] for g in remaining['non_pass_gates']]}"))

    def h8():
        # every non-PASS gate is accounted for: has open tasks, is a HUMAN_GATE,
        # is blocked by an open issue, or is a re-evaluate candidate (all related
        # tasks complete AND nothing outstanding against it).
        unaccounted = [g["gate"] for g in remaining["non_pass_gates"]
                       if not g["open_tasks"] and g["state"] != "HUMAN_GATE"
                       and g["class"] not in {"reevaluate_candidate", "blocked_by_open_issue", "deferred_review"}]
        blocked = {g["gate"]: g["open_issues"] for g in remaining["non_pass_gates"]
                   if g["class"] == "blocked_by_open_issue"}
        return not unaccounted, (
            f"説明不能な非PASSゲート={unaccounted or 'なし'} / "
            f"再評価候補(関連全完了かつ未解決課題なし)={remaining['reevaluate_candidates'] or 'なし'} / "
            f"指定日まで延期再評価={remaining['deferred_reviews'] or 'なし'} / "
            f"未解決課題でPASS再判定不可={blocked or 'なし'}")

    record("H8", "各非PASSゲートが残タスク/HUMAN_GATE/未解決課題/再評価候補として説明できる", h8)

    def h9():
        classified = {g["class"] for g in remaining["non_pass_gates"]}
        return classified.issubset(
            {"human_or_mixed", "lane", "reevaluate_candidate", "blocked_by_open_issue", "deferred_review"}), \
            f"残作業の分類={sorted(classified)}"

    record("H9", "残作業が人間依存/レーン/再評価候補に分類できる", h9)

    def h10():
        # aggregation output is internally consistent: done count matches
        # completed rows recomputed
        done = sum(1 for r in wbs if r.get("ステータス") == "完了")
        return done == stats["done"], f"完了数再計算={done}(={stats['done']})"

    record("H10", "集約出力が内部整合している（完了数の再計算一致）", h10)

    return results


def build_report(today: str) -> dict[str, Any]:
    wbs = load_wbs()
    criteria = load_criteria()
    stats = build_stats(wbs, today)
    remaining = classify_remaining(criteria, wbs, load_issues())
    hypotheses = build_hypotheses(wbs, criteria, stats, remaining)
    passed = sum(1 for h in hypotheses if h["passed"])
    evidence = {k: {"artifact": v, "exists": (PROJECT_ROOT / v).exists()} for k, v in EVIDENCE_INDEX.items()}
    return {
        "report_id": "WBS_COMPLETION_EVIDENCE_T849_1",
        "checked_at": today,
        "status": "ok" if passed == len(hypotheses) else "attention",
        "hypotheses_total": len(hypotheses),
        "hypotheses_passed": passed,
        "hypotheses": hypotheses,
        "wbs_stats": stats,
        "evidence_index": evidence,
        "remaining_for_ga": remaining,
        "note": ("GAクローズ(T849本体)は非PASSゲートの解消後に人間が最終判定する。"
                 "本集約はWBS完了状況とClaude Code巻き取り証跡の索引であり、ゲート判定は"
                 "generate_production_go_no_go_review.pyが正本。"),
    }


def render_markdown(report: dict[str, Any]) -> str:
    s = report["wbs_stats"]
    lines = [
        "# WBS完了証跡集約 (T849_1)",
        "",
        f"- レポートID: `{report['report_id']}` / 実施日: {report['checked_at']}",
        f"- 判定: **{report['status']}** ({report['hypotheses_passed']}/{report['hypotheses_total']} 仮説PASS)",
        f"- WBS完了率: **{s['completion_rate_pct']}%**（完了{s['done']} / 実行中{s['in_progress']} / 未着手{s['not_started']} / 総数{s['total']}）",
        f"- 期限超過(未完了): {', '.join(s['overdue_incomplete']) or 'なし'}",
        "",
        f"> {report['note']}",
        "",
        "## Claude Code 巻き取り証跡インデックス",
        "",
        "| サブタスク | 証跡 | 実在 |",
        "| --- | --- | --- |",
    ]
    for k, v in report["evidence_index"].items():
        lines.append(f"| {k} | {v['artifact']} | {'OK' if v['exists'] else 'MISSING'} |")
    reeval = report["remaining_for_ga"].get("reevaluate_candidates") or []
    deferred = report["remaining_for_ga"].get("deferred_reviews") or []
    lines += ["", f"## 再評価候補ゲート（関連WBS全完了かつ未解決課題なし・PASS再判定推奨）: {', '.join(reeval) or 'なし'}",
              "", f"## 延期再評価ゲート（指定レビューまでPASS化しない）: {', '.join(deferred) or 'なし'}",
              "",
              "> 関連WBSが全完了でも、そのWBSを参照する未解決(open)課題が残るゲートは "
              "`blocked_by_open_issue` として再判定対象から除外する（実欠陥を抱えたままGAゲートを"
              "greenにしないため）。",
              "", "## 残作業（非PASSゲート）", "",
              "| ゲート | 状態 | 残WBS | 未解決課題 | 分類 |", "| --- | --- | --- | --- | --- |"]
    for g in report["remaining_for_ga"]["non_pass_gates"]:
        lines.append(
            f"| {g['gate']} | {g['state']} | {', '.join(g['open_tasks']) or '—'} | "
            f"{', '.join(g.get('open_issues') or []) or '—'} | {g['class']} |")
    lines += ["", "## 10仮説検証", "", "| # | 仮説 | 結果 | 根拠 |", "| --- | --- | --- | --- |"]
    for h in report["hypotheses"]:
        lines.append(f"| {h['id']} | {h['hypothesis']} | {'PASS' if h['passed'] else 'FAIL'} | {h['detail'].replace('|', '/')} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="WBS completion evidence aggregator (T849_1)")
    parser.add_argument("--today", default=jst_today())
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD)
    parser.add_argument("--fail-on-attention", action="store_true")
    args = parser.parse_args()

    report = build_report(args.today)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"[*] Wrote {args.json_out}")
    print(f"[*] Wrote {args.md_out}")
    print(f"[{'+' if report['status'] == 'ok' else '!'}] WBS completion evidence {report['status']}: "
          f"{report['hypotheses_passed']}/{report['hypotheses_total']} hypotheses; "
          f"completion={report['wbs_stats']['completion_rate_pct']}%")
    if args.fail_on_attention and report["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
