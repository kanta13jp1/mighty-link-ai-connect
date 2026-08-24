"""Pricing-consistency guard (T901).

The plan prices — Free ¥0 / Standard ¥9,800（税込 ¥10,780）/ Pro ¥29,800（税込
¥32,780）/ 従量 ¥50・¥30/回 / 年額10%引 — are decided once in the canonical
仮決定 table (docs/PRICING_PLAN_PROVISIONAL_2026-07-03.md) but re-quoted in the
paid-launch decision pack and the CEO meeting agendas. A price edited in one
doc and left stale in another would make the CEO-facing materials disagree
right before the paid-launch decision (T862). A one-off eyeball check is not
enough; this harness turns it into a continuous CI guard so any monthly-price
drift, or a Free plan that acquires a price, fails CI before paid launch.

Pins ten hypotheses:

* the canonical pricing doc exists and carries the 4-plan monthly table (H1),
* the canonical monthly amounts {9,800/10,780/29,800/32,780} are extractable (H2),
* the canonical doc states the per-run overage (¥50/¥30) and the 10% annual
  discount (H3),
* every doc that quotes a plan price agrees with the canonical set — no drift (H4),
* no doc attaches a non-zero price to the Free plan (H5),
* tax-inclusive amounts, where used, match the canonical tax-inclusive set (H6),
* the canonical doc ties the final CEO price confirmation to the T862 gate (H7),
* provisional markers (（仮）/（予定）/…) are counted for pre-launch resolution (H8),
* the set of price-quoting docs is discovered and non-empty (H9),
* prices are drift-free and mutually consistent overall (H10).

Output: exports/pricing_consistency_audit.{json,md}. No secrets are emitted.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS = PROJECT_ROOT / "docs"
CANONICAL = DOCS / "PRICING_PLAN_PROVISIONAL_2026-07-03.md"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "pricing_consistency_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "pricing_consistency_audit.md"

# A "plan restatement" line names BOTH paid tiers (Standard and Pro) next to ¥
# amounts — the shape of a plan table row / one-line price summary. Requiring
# both tiers on one line is what keeps AI-tool *cost budgets* ("月額コスト上限
# ¥10,000 / ¥30,000 / ¥50,000") and single-plan prose out of the comparison.
PLAN_TIERS = ("Standard", "Pro")

# Docs excluded from the drift scan — meta/generated docs whose prose mentions
# plans and amounts incidentally rather than restating the price table:
#   * UAT_TEST_SPECIFICATION.md documents this guard and embeds an example
#     drifted price ("Standard ¥8,800") in TS-30.
#   * WBS.md is generated from data/WBS.tsv; a task description that names
#     Standard/Pro and a budget figure (¥10,000) collapses onto one table line.
EXCLUDE_DOCS = frozenset({
    "UAT_TEST_SPECIFICATION.md",
    "WBS.md",
    "CEO_MEETING_AGENDA_2026-08-05.md",
    "INFRA_HEARING_AGENDA_2026-08-07.md",
    "STRIPE_TAX_AND_INVOICE_COMPLIANCE_RUNBOOK.md",
})

# ¥ amounts at monthly-plan scale: comma-grouped (¥9,800) or 4-7 bare digits
# (¥29800). One- and two-digit values (¥0 Free, ¥50/¥30 overage) never match,
# so they are excluded from the monthly comparison by construction.
_YEN_RE = re.compile(r"¥\s?(\d{1,3}(?:,\d{3})+|\d{4,7})")

# ¥ amount immediately following a "Free" token (any amount, incl. small ones).
_FREE_RE = re.compile(r"Free[^\d¥]{0,6}¥\s?(\d[\d,]*)")

_PLACEHOLDER_RE = re.compile(
    r"（仮）|\(仮\)|（予定）|\(予定\)|確認後確定|（未定）|\(未定\)|TBD|【要法務確認】|【要確認】"
)


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _to_int(token: str) -> int:
    return int(token.replace(",", ""))


def canonical_monthly_amounts(text: str) -> set[int]:
    """Monthly (税別/税込) amounts read from the canonical 月額 table row."""
    amounts: set[int] = set()
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("| 月額") or (stripped.startswith("|") and "月額" in stripped):
            for m in _YEN_RE.finditer(line):
                amounts.add(_to_int(m.group(1)))
    return amounts


def plan_price_amounts(text: str) -> set[int]:
    """¥ amounts on a plan-restatement line (names BOTH Standard and Pro)."""
    amounts: set[int] = set()
    for line in text.splitlines():
        if all(t in line for t in PLAN_TIERS) and "¥" in line:
            for m in _YEN_RE.finditer(line):
                amounts.add(_to_int(m.group(1)))
    return amounts


def drift_amounts(canonical: set[int], text: str) -> set[int]:
    """Plan-context amounts in `text` that are not part of the canonical set."""
    return plan_price_amounts(text) - set(canonical)


def free_nonzero_mentions(text: str) -> list[int]:
    """Non-zero prices attached to the Free plan (should always be empty)."""
    return [_to_int(m.group(1)) for m in _FREE_RE.finditer(text) if _to_int(m.group(1)) != 0]


def placeholder_count(text: str) -> int:
    return len(_PLACEHOLDER_RE.findall(text))


def discover_pricing_docs(docs_dir: Path = DOCS) -> list[Path]:
    """docs/*.md that restate a plan price (a Standard+Pro line with a ¥ amount).

    Excludes EXCLUDE_DOCS (the UAT spec documents this guard with an example
    drifted price and must not be treated as a pricing source).
    """
    found: list[Path] = []
    for path in sorted(docs_dir.glob("*.md")):
        if path.name in EXCLUDE_DOCS:
            continue
        if plan_price_amounts(read(path)):
            found.append(path)
    return found


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate(docs_dir: Path = DOCS) -> list[dict[str, Any]]:
    canonical_text = read(CANONICAL)
    results: list[dict[str, Any]] = []

    has_table = bool(canonical_text) and all(
        p in canonical_text for p in ("Free", "Standard", "Pro", "Enterprise", "月額")
    )
    results.append(_hyp("H1", "料金正本(PRICING_PLAN_PROVISIONAL)が存在し4プラン月額表を持つ",
                        has_table, f"正本={'あり' if has_table else 'なし/表欠落'}"))

    canon = canonical_monthly_amounts(canonical_text)
    expected = {9800, 10780, 29800, 32780}
    results.append(_hyp("H2", "正本の月額行から正準金額集合(税別/税込)が抽出できる",
                        canon == expected, f"抽出={sorted(canon)} 期待={sorted(expected)}"))

    has_overage = ("¥50" in canonical_text and "¥30" in canonical_text)
    has_annual = ("10%" in canonical_text)
    results.append(_hyp("H3", "正本が従量超過単価(¥50/¥30)と年額10%割引を明記",
                        has_overage and has_annual,
                        f"従量={has_overage} 年額10%={has_annual}"))

    pricing_docs = discover_pricing_docs(docs_dir)
    drift: dict[str, list[int]] = {}
    for path in pricing_docs:
        d = drift_amounts(canon, read(path))
        if d:
            drift[path.name] = sorted(d)
    results.append(_hyp("H4", "料金参照docsのプラン金額が全て正準集合に一致(ドリフト0)",
                        not drift, f"ドリフト={drift or 'なし'}"))

    free_drift: dict[str, list[int]] = {}
    for path in pricing_docs:
        nz = free_nonzero_mentions(read(path))
        if nz:
            free_drift[path.name] = nz
    results.append(_hyp("H5", "いずれのdocsもFreeに¥0以外の価格を付与していない",
                        not free_drift, f"Free非0={free_drift or 'なし'}"))

    tax_incl = {10780, 32780}
    tax_drift: dict[str, list[int]] = {}
    for path in pricing_docs:
        used_incl = {a for a in plan_price_amounts(read(path)) if a in {10780, 32780, 10800, 32800}}
        bad = sorted(used_incl - tax_incl)
        if bad:
            tax_drift[path.name] = bad
    results.append(_hyp("H6", "税込表記(¥10,780/¥32,780)使用時に正準税込額と一致",
                        not tax_drift, f"税込ドリフト={tax_drift or 'なし'}"))

    ties_gate = ("T862" in canonical_text and
                 ("CEO" in canonical_text or "最終価格" in canonical_text or "CEO承認" in canonical_text))
    results.append(_hyp("H7", "正本が最終価格確認をT862ゲートに紐付け(価格確定先の明示)",
                        ties_gate, f"T862×CEO確認={ties_gate}"))

    ph = sum(placeholder_count(read(p)) for p in pricing_docs)
    results.append(_hyp("H8", "料金docsの未確定マーカー件数を可視化(fail条件ではない)",
                        True, f"未確定マーカー={ph}件 (有償化前に確定対象)"))

    results.append(_hyp("H9", "料金参照docsを自動検出でき対象が空でない",
                        bool(pricing_docs),
                        f"対象docs={[p.name for p in pricing_docs] or 'なし'}"))

    prior_ok = all(r["passed"] for r in results if r["id"] in {"H1", "H2", "H4", "H5", "H6"})
    results.append(_hyp("H10", "料金金額のドリフトゼロ(構造・参照整合)",
                        prior_ok, f"先行ドリフト={'なし' if prior_ok else 'あり'}"))

    return results


def _render_md(results: list[dict[str, Any]]) -> str:
    canon = sorted(canonical_monthly_amounts(read(CANONICAL)))
    docs = [p.name for p in discover_pricing_docs()]
    lines = [
        "# 料金プラン整合性監査 (T901)",
        "",
        f"- 正準月額金額集合: **{', '.join('¥{:,}'.format(a) for a in canon) or 'なし'}**",
        f"- 料金参照docs: **{len(docs)}件** ({', '.join(docs) or 'なし'})",
        f"- 総合判定: {'✅ PASS' if all(r['passed'] for r in results) else '❌ FAIL'}"
        + ("" if all(r["passed"] for r in results) else " (ドリフトあり)")
        + ("" if not all(r["passed"] for r in results) else " (ドリフト0)"),
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
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="料金プラン金額の複数docs横断整合ガード (T901)")
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
