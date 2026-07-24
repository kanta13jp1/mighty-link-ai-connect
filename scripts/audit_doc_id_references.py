"""Doc ID-reference integrity guard (T904).

docs/*.md reference WBS task IDs (T###[_n]), issue IDs (R##), and QA IDs
(QA-##) throughout their prose. When an ID is renumbered, removed, or mistyped
the reference dangles and the doc silently goes stale — e.g. the QA-135→QA-136
renumber left LEGAL_REVIEW_SIGNOFF_TRACKER.md pointing at a QA that no longer
existed. T891 checks Markdown *file* links; this harness adds *ID*-reference
integrity: every ID a doc names must resolve to a real tracker row, or be an
allowlisted known-historical/provisional reference, or CI fails.

Pins ten hypotheses:

* the three trackers load and are non-empty (H1),
* WBS references all resolve (or are allowlisted) — no dangling T### (H2),
* QA references all resolve (or are allowlisted) — no dangling QA-## (H3),
* issue references all resolve (or are allowlisted) — no dangling R## (H4),
* the allowlist entries are still *needed* (each is actually referenced) (H5),
* no allowlist entry masks an ID that now exists (stale allowlist) (H6),
* the scan covers a non-trivial number of docs (H7),
* the generated WBS.md and the trackers themselves are excluded (H8),
* the allowlist is documented with reasons in this module (H9),
* references and trackers are fully consistent overall (H10).

Output: exports/doc_id_references_audit.{json,md}. No secrets are emitted.
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
DATA = PROJECT_ROOT / "data"
WBS_TSV = DATA / "WBS.tsv"
ISSUES_TSV = DATA / "issues_tracker.tsv"
QA_TSV = DATA / "qa_tracker.tsv"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "doc_id_references_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "doc_id_references_audit.md"

# Docs excluded from the scan:
#   * WBS.md is generated from WBS.tsv (its IDs are the source, not references).
#   * UAT_TEST_SPECIFICATION.md documents these guards and deliberately embeds
#     example non-existent IDs (T999 / QA-999) in the guards' NG-check steps;
#     scanning it would flag the guards' own documentation. Excluding it also
#     keeps those example IDs OFF the allowlist, so the manual NG check (writing
#     T999 into some other doc) still fails as intended.
EXCLUDE_DOCS = frozenset({"WBS.md", "UAT_TEST_SPECIFICATION.md"})

_WBS_RE = re.compile(r"\bT\d{3}(?:_\d+)?\b")
_QA_RE = re.compile(r"\bQA-\d+\b")
_R_RE = re.compile(r"\bR\d{1,3}\b")

# Known-historical / provisional ID references that legitimately do not resolve
# to a current tracker row. Each entry documents WHY it is exempt.
ALLOWLIST: dict[str, str] = {
    # 6/2 CEO プレゼンの「決定したら作る」提案タスク表。実WBSは別IDで起票され、
    # 提案された各仮IDは作成されなかった歴史的記録（CEO_PRESENTATION_POST_DECISION_ROADMAP_2026-06-02.md）。
    "T720": "6/2決定前提案の仮タスクID（未起票の歴史的記録）",
    "T721": "6/2決定前提案の仮タスクID（未起票の歴史的記録）",
    "T722": "6/2決定前提案の仮タスクID（未起票の歴史的記録）",
    "T723": "6/2決定前提案の仮タスクID（未起票の歴史的記録）",
    "T724": "6/2決定前提案の仮タスクID（未起票の歴史的記録）",
    "T725": "6/2決定前提案の仮タスクID（未起票の歴史的記録）",
    "T726": "6/2決定前提案の仮タスクID（未起票の歴史的記録）",
    # 解決済み課題 R40「T774/T775 二重定義」の履歴記述内の言及（MONTHLY_REPORT_2026-06.md）。
    # T775 は重複として削除された側で、記述は正確な履歴。
    "T775": "解決済み課題R40（T774/T775二重定義）の履歴記述内の言及",
}


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _first_col_ids(path: Path, prefix_ok) -> set[str]:
    ids: set[str] = set()
    for line in read(path).splitlines()[1:]:
        cell = line.split("\t", 1)[0].strip()
        if cell and prefix_ok(cell):
            ids.add(cell)
    return ids


def valid_ids() -> tuple[set[str], set[str], set[str]]:
    """(wbs, issues, qa) ID sets from the source-of-truth trackers."""
    wbs = _first_col_ids(WBS_TSV, lambda c: re.fullmatch(r"T\d{3}(?:_\d+)?", c) is not None)
    issues = _first_col_ids(ISSUES_TSV, lambda c: re.fullmatch(r"R\d+", c) is not None)
    qa = _first_col_ids(QA_TSV, lambda c: c.startswith("QA-"))
    return wbs, issues, qa


def referenced_ids(text: str) -> set[str]:
    """All WBS/QA/issue IDs referenced in a doc's text."""
    return set(_WBS_RE.findall(text)) | set(_QA_RE.findall(text)) | set(_R_RE.findall(text))


def allowlist_ids() -> set[str]:
    return set(ALLOWLIST)


def dangling(referenced: set[str], valid: set[str], allowlist: set[str]) -> set[str]:
    """Referenced IDs that are neither valid nor allowlisted."""
    return set(referenced) - set(valid) - set(allowlist)


def _scan_docs() -> dict[str, set[str]]:
    """{doc_name: referenced_ids} for every scanned doc."""
    out: dict[str, set[str]] = {}
    for path in sorted(DOCS.glob("*.md")):
        if path.name in EXCLUDE_DOCS:
            continue
        out[path.name] = referenced_ids(read(path))
    return out


def _wbs_base(i: str) -> str:
    return i.split("_")[0]


def _resolves(i: str, valid_all: set[str]) -> bool:
    # a T###_n subtask resolves if either the exact id or its base T### exists,
    # or if i is a parent T### and any T###_n subtask exists in valid_all
    return i in valid_all or _wbs_base(i) in valid_all or any(v.startswith(i + "_") for v in valid_all)


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate() -> list[dict[str, Any]]:
    wbs, issues, qa = valid_ids()
    valid_all = wbs | issues | qa
    allow = allowlist_ids()
    scanned = _scan_docs()
    results: list[dict[str, Any]] = []

    results.append(_hyp("H1", "3トラッカー(WBS/課題/QA)が読み込め非空",
                        bool(wbs and issues and qa),
                        f"WBS={len(wbs)} 課題={len(issues)} QA={len(qa)}"))

    def dangle_family(regex: re.Pattern) -> dict[str, list[str]]:
        bad: dict[str, list[str]] = {}
        for name, refs in scanned.items():
            fam = {r for r in refs if regex.fullmatch(r)}
            d = sorted(r for r in fam if not _resolves(r, valid_all) and r not in allow)
            if d:
                bad[name] = d
        return bad

    dw = dangle_family(_WBS_RE)
    results.append(_hyp("H2", "docsのWBS参照が全て実在(リンク切れ0)",
                        not dw, f"WBSリンク切れ={dw or 'なし'}"))

    dq = dangle_family(_QA_RE)
    results.append(_hyp("H3", "docsのQA参照が全て実在(リンク切れ0)",
                        not dq, f"QAリンク切れ={dq or 'なし'}"))

    dr = dangle_family(_R_RE)
    results.append(_hyp("H4", "docsの課題(R)参照が全て実在(リンク切れ0)",
                        not dr, f"課題リンク切れ={dr or 'なし'}"))

    all_refs: set[str] = set()
    for refs in scanned.values():
        all_refs |= refs
    unused_allow = sorted(a for a in allow if a not in all_refs)
    results.append(_hyp("H5", "許可リストの各項目が実際に参照されている(不要項目0)",
                        not unused_allow, f"未参照の許可項目={unused_allow or 'なし'}"))

    now_exists = sorted(a for a in allow if _resolves(a, valid_all))
    results.append(_hyp("H6", "許可リストが実在IDを隠していない(stale許可0)",
                        not now_exists, f"実在化した許可項目={now_exists or 'なし'}"))

    results.append(_hyp("H7", "走査対象docsが十分ある(縮退検知)",
                        len(scanned) >= 50, f"走査docs={len(scanned)}"))

    results.append(_hyp("H8", "生成物WBS.mdと正本トラッカーを走査対象から除外",
                        "WBS.md" in EXCLUDE_DOCS and "WBS.md" not in scanned,
                        f"除外={sorted(EXCLUDE_DOCS)}"))

    documented = all(bool(reason) for reason in ALLOWLIST.values())
    results.append(_hyp("H9", "許可リストが理由付きで文書化されている",
                        documented and bool(ALLOWLIST), f"許可リスト={len(ALLOWLIST)}件(全件理由付き)"))

    prior_ok = all(r["passed"] for r in results if r["id"] in {"H1", "H2", "H3", "H4", "H6"})
    results.append(_hyp("H10", "ID参照と正本トラッカーが完全整合(陳腐化参照0)",
                        prior_ok, f"先行ドリフト={'なし' if prior_ok else 'あり'}"))

    return results


def _render_md(results: list[dict[str, Any]]) -> str:
    wbs, issues, qa = valid_ids()
    scanned = _scan_docs()
    ok = all(r["passed"] for r in results)
    lines = [
        "# ドキュメントID参照整合性監査 (T904)",
        "",
        f"- 正本: WBS **{len(wbs)}** / 課題 **{len(issues)}** / QA **{len(qa)}**",
        f"- 走査docs: **{len(scanned)}** / 許可リスト: **{len(ALLOWLIST)}件**",
        f"- 総合判定: {'✅ PASS (陳腐化参照0)' if ok else '❌ FAIL (リンク切れ参照あり)'}",
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
    lines.append("## 許可リスト（既知の歴史的・仮ID参照）")
    lines.append("")
    for i, reason in ALLOWLIST.items():
        lines.append(f"- `{i}`: {reason}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="docsのWBS/課題/QA ID参照整合ガード (T904)")
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
