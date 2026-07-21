"""Release-gate currency guard (T908).

data/release_go_no_go_criteria.tsv holds the 21 public-launch gates that decide
GO / NO_GO. Its current_state is maintained by hand, so it drifts from reality:
measured on 2026-07-20, PUBLIC-06 (T752), PUBLIC-11 (T817 series) and
PUBLIC-14 (T852) were still BLOCKED/WARNING although every related WBS task had
completed, and two had not been re-checked for 13 days. The verdict therefore
mixed genuine blockers with stale bookkeeping, and T849 (GA closure) could not
tell them apart.

This harness detects that drift in both directions:

* **stale** — a non-PASS gate whose related WBS are all 完了. The work is done,
  so the gate must be re-evaluated by its decision authority, or its notes must
  say why it stays non-PASS. Enforced via the 【再評価待ち: marker.
* **inverse drift** — a PASS gate with incomplete related WBS. This is the more
  dangerous direction (claiming readiness that isn't there) and is never
  tolerated.

**This guard is read-only with respect to the ledger.** It reports and forces
annotation; it never flips a gate to PASS, because decision_authority is a human
(開発責任者 / CEO / 会社管理者).

Pins ten hypotheses: ledger parses (H1), ids unique (H2), states valid (H3),
WBS refs resolve (H4), no inverse drift (H5), stale gates are annotated (H6),
owner+authority present (H7), non-PASS gates carry notes (H8), last_checked is
a date (H9), overall gate/WBS consistency (H10).

Output: exports/release_gate_currency_audit.{json,md}. No secrets are emitted.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CRITERIA = PROJECT_ROOT / "data" / "release_go_no_go_criteria.tsv"
WBS_TSV = PROJECT_ROOT / "data" / "WBS.tsv"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "release_gate_currency_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "release_gate_currency_audit.md"

ALLOWED_STATES = {"PASS", "WARNING", "BLOCKED", "HUMAN_GATE"}
DONE = "完了"

# Marker a stale gate's notes must carry so the drift is visible and routed to
# the decision authority instead of silently ageing.
REEVAL_MARKER = "【再評価待ち:"

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def read_gates(path: Path = CRITERIA) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_wbs_status(path: Path = WBS_TSV) -> dict[str, str]:
    """{task_id: status} from the WBS source of truth."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
        cols = line.split("\t")
        if len(cols) >= 8 and cols[0].strip():
            out[cols[0].strip()] = cols[7].strip()
    return out


def related_wbs_ids(gate: dict[str, str]) -> list[str]:
    return [x.strip() for x in str(gate.get("related_wbs", "")).split(";") if x.strip()]


def all_related_complete(gate: dict[str, str], wbs: dict[str, str]) -> bool:
    """True when the gate names WBS tasks and every one of them is 完了."""
    ids = related_wbs_ids(gate)
    return bool(ids) and all(wbs.get(i) == DONE for i in ids)


def stale_gates(gates: list[dict[str, str]], wbs: dict[str, str]) -> list[str]:
    """Non-PASS gates whose related work has all completed."""
    return [g["criterion_id"] for g in gates
            if str(g.get("current_state", "")).upper() != "PASS"
            and all_related_complete(g, wbs)]


def unannotated_stale(gates: list[dict[str, str]], wbs: dict[str, str]) -> list[str]:
    """Stale gates whose notes do not carry the re-evaluation marker."""
    stale = set(stale_gates(gates, wbs))
    return [g["criterion_id"] for g in gates
            if g["criterion_id"] in stale and REEVAL_MARKER not in str(g.get("notes", ""))]


def inverse_drift(gates: list[dict[str, str]], wbs: dict[str, str]) -> list[str]:
    """PASS gates that still have incomplete related WBS."""
    out = []
    for g in gates:
        if str(g.get("current_state", "")).upper() != "PASS":
            continue
        ids = related_wbs_ids(g)
        if any(wbs.get(i) != DONE for i in ids):
            out.append(g["criterion_id"])
    return out


def dangling_wbs_refs(gates: list[dict[str, str]], wbs: dict[str, str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for g in gates:
        bad = [i for i in related_wbs_ids(g) if i not in wbs]
        if bad:
            out[g["criterion_id"]] = bad
    return out


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate() -> list[dict[str, Any]]:
    gates = read_gates()
    wbs = read_wbs_status()
    results: list[dict[str, Any]] = []

    results.append(_hyp("H1", "ゲート台帳が読み込め非空",
                        bool(gates) and bool(wbs), f"ゲート={len(gates)} / WBS={len(wbs)}"))

    ids = [g.get("criterion_id", "") for g in gates]
    dups = sorted({i for i in ids if ids.count(i) > 1})
    results.append(_hyp("H2", "ゲートIDが一意", not dups, f"重複={dups or 'なし'}"))

    bad_state = sorted({str(g.get("current_state", "")) for g in gates
                        if str(g.get("current_state", "")).upper() not in ALLOWED_STATES})
    results.append(_hyp("H3", "状態値が許容集合(PASS/WARNING/BLOCKED/HUMAN_GATE)",
                        not bad_state, f"不正状態={bad_state or 'なし'}"))

    dangling = dangling_wbs_refs(gates, wbs)
    results.append(_hyp("H4", "related_wbsが実在WBSに解決(切れ参照0)",
                        not dangling, f"切れ参照={dangling or 'なし'}"))

    inv = inverse_drift(gates, wbs)
    results.append(_hyp("H5", "PASSゲートに未完了の関連WBSが無い(逆ドリフト0)",
                        not inv, f"逆ドリフト={inv or 'なし'}"))

    stale = stale_gates(gates, wbs)
    unann = unannotated_stale(gates, wbs)
    results.append(_hyp("H6", "陳腐化ゲート(非PASSだが関連WBS全完了)が再評価待ちとして注記済み",
                        not unann,
                        f"陳腐化={stale or 'なし'} / 未注記={unann or 'なし'}"))

    no_owner = [g["criterion_id"] for g in gates
                if not str(g.get("owner", "")).strip() or not str(g.get("decision_authority", "")).strip()]
    results.append(_hyp("H7", "全ゲートにowner・decision_authorityが記載",
                        not no_owner, f"欠落={no_owner or 'なし'}"))

    no_notes = [g["criterion_id"] for g in gates
                if str(g.get("current_state", "")).upper() != "PASS"
                and not str(g.get("notes", "")).strip()]
    results.append(_hyp("H8", "非PASSゲートにnotesが記載",
                        not no_notes, f"notes欠落={no_notes or 'なし'}"))

    bad_date = [g["criterion_id"] for g in gates
                if not _DATE_RE.match(str(g.get("last_checked", "")).strip())]
    results.append(_hyp("H9", "last_checkedがYYYY-MM-DD形式",
                        not bad_date, f"不正日付={bad_date or 'なし'}"))

    prior_ok = all(r["passed"] for r in results if r["id"] in {"H1", "H4", "H5", "H6"})
    results.append(_hyp("H10", "ゲート台帳とWBS実態が整合(ドリフト0)",
                        prior_ok, f"先行ドリフト={'なし' if prior_ok else 'あり'}"))

    return results


def _render_md(results: list[dict[str, Any]]) -> str:
    gates = read_gates()
    wbs = read_wbs_status()
    stale = stale_gates(gates, wbs)
    ok = all(r["passed"] for r in results)
    counts: dict[str, int] = {}
    for g in gates:
        counts[str(g.get("current_state", "?"))] = counts.get(str(g.get("current_state", "?")), 0) + 1
    lines = [
        "# リリース判定ゲート整合性監査 (T908)",
        "",
        f"- ゲート総数: **{len(gates)}** / 内訳: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())),
        f"- 陳腐化ゲート(非PASSだが関連WBS全完了): **{len(stale)}件** {stale or ''}",
        f"- 総合判定: {'✅ PASS (ドリフト0)' if ok else '❌ FAIL (ドリフトあり)'}",
        "",
        "> 本ガードは検知と可視化のみを行い、ゲートを自動的に PASS へ変更しない。",
        "> 状態変更は各ゲートの decision_authority（開発責任者 / CEO / 会社管理者）が行う。",
        "",
        "## 10仮説の検証結果",
        "",
        "| 仮説 | 内容 | 判定 | 詳細 |",
        "| :-- | :-- | :-- | :-- |",
    ]
    for r in results:
        mark = "✅" if r["passed"] else "❌"
        lines.append(f"| {r['id']} | {r['title']} | {mark} | {r['detail']} |")
    lines.append("")
    if stale:
        lines += ["## 再評価が必要なゲート", "",
                  "| ゲート | 状態 | 関連WBS(全完了) | decision_authority |",
                  "| :-- | :-- | :-- | :-- |"]
        for g in gates:
            if g["criterion_id"] in stale:
                lines.append(f"| {g['criterion_id']} | {g.get('current_state')} | "
                             f"{g.get('related_wbs')} | {g.get('decision_authority')} |")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="リリース判定ゲートとWBS実態の整合ガード (T908)")
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")

    results = evaluate()
    passed = all(r["passed"] for r in results)

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(
        json.dumps({"passed": passed, "hypotheses": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md = _render_md(results)
    args.md.write_text(md, encoding="utf-8")
    print(md)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
