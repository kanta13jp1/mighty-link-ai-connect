"""Operations runbook catalog guard (T902).

The repo carries 46 operational runbooks (docs/*RUNBOOK*.md) — DR, incident
postmortem, rollback, backup/restore, secret rotation, cost dashboards, and so
on. Without an index an operator cannot find the right one mid-incident, and a
newly added runbook silently escapes discovery while a deleted one leaves a
stale reference. This harness pins a single catalog
(docs/OPERATIONS_RUNBOOK_CATALOG.md) to the on-disk runbook set: every runbook
must be cataloged (no orphan) and every catalog entry must resolve to a real
file (no dangling), or CI fails.

Pins ten hypotheses:

* the catalog exists (H1),
* every on-disk runbook is linked from the catalog — no orphan (H2),
* every runbook linked from the catalog exists on disk — no dangling (H3),
* the catalog groups runbooks under category headings (H4),
* the catalog is non-trivially sized relative to the corpus (H5),
* each catalog runbook entry carries a "when to open" trigger cue (H6),
* the catalog links are repo-relative (no file:/// or absolute paths) (H7),
* incident-response runbooks (DR / postmortem / rollback) are cataloged (H8),
* the catalog has no duplicate runbook links (H9),
* catalog and disk are fully in sync overall (H10).

Output: exports/runbook_catalog_audit.{json,md}. No secrets are emitted.
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
CATALOG = DOCS / "OPERATIONS_RUNBOOK_CATALOG.md"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "runbook_catalog_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "runbook_catalog_audit.md"

# Markdown link whose target is a *RUNBOOK*.md file (repo-relative).
_RUNBOOK_LINK_RE = re.compile(r"\]\(([^)]*?[A-Za-z0-9_]*RUNBOOK[A-Za-z0-9_]*\.md)\)")
# Any link target that points at a runbook filename, for absolute-path detection.
_ABS_LINK_RE = re.compile(r"\]\((file:///[^)]*RUNBOOK[^)]*|[A-Za-z]:[\\/][^)]*RUNBOOK[^)]*)\)")


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def runbook_files(docs_dir: Path = DOCS) -> set[str]:
    """Filenames of every operational runbook on disk (docs/*RUNBOOK*.md).

    The catalog itself matches the glob (…RUNBOOK_CATALOG.md) but is the index,
    not a runbook, so it is excluded.
    """
    return {p.name for p in docs_dir.glob("*RUNBOOK*.md") if p.name != CATALOG.name}


def cataloged_runbooks(catalog_text: str) -> set[str]:
    """Runbook filenames linked from the catalog (basename of each link target).

    The catalog's own filename is excluded — a self-link (e.g. a "back to index"
    reference) is the index pointing at itself, not a cataloged runbook.
    runbook_files() excludes the catalog too, so keeping this symmetric prevents
    a self-link from being read as a phantom dangling entry (H3/H5).
    """
    return set(cataloged_runbook_links(catalog_text))


def cataloged_runbook_links(catalog_text: str) -> list[str]:
    """Every runbook link basename incl. duplicates (for duplicate detection).

    Excludes self-links to the catalog itself (symmetric with runbook_files()).
    """
    return [
        name
        for m in _RUNBOOK_LINK_RE.finditer(catalog_text)
        if (name := Path(m.group(1)).name) != CATALOG.name
    ]


def orphan_runbooks(files: set[str], cataloged: set[str]) -> set[str]:
    """On disk but not in the catalog."""
    return set(files) - set(cataloged)


def dangling_entries(files: set[str], cataloged: set[str]) -> set[str]:
    """In the catalog but not on disk."""
    return set(cataloged) - set(files)


def catalog_categories(catalog_text: str) -> list[str]:
    """Section headings (## / ###) — the H1 title is excluded."""
    return [
        m.group(2).strip()
        for m in re.finditer(r"^(#{2,3})\s+(.+)$", catalog_text, re.M)
    ]


def _entry_lines(catalog_text: str) -> list[str]:
    """Catalog list lines that link a runbook."""
    return [ln for ln in catalog_text.splitlines() if _RUNBOOK_LINK_RE.search(ln)]


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate(docs_dir: Path = DOCS) -> list[dict[str, Any]]:
    catalog_text = read(CATALOG)
    files = runbook_files(docs_dir)
    cataloged = cataloged_runbooks(catalog_text)
    results: list[dict[str, Any]] = []

    results.append(_hyp("H1", "運用Runbookカタログが存在する",
                        bool(catalog_text), f"カタログ={'あり' if catalog_text else 'なし'}"))

    orphans = orphan_runbooks(files, cataloged)
    results.append(_hyp("H2", "全Runbookがカタログに掲載(孤児0)",
                        not orphans, f"孤児={sorted(orphans) or 'なし'}"))

    dangling = dangling_entries(files, cataloged)
    results.append(_hyp("H3", "カタログの全リンクが実在(切れリンク0)",
                        not dangling, f"切れリンク={sorted(dangling) or 'なし'}"))

    cats = catalog_categories(catalog_text)
    results.append(_hyp("H4", "カテゴリ見出しで整理されている(2件以上)",
                        len(cats) >= 2, f"カテゴリ数={len(cats)}"))

    results.append(_hyp("H5", "カタログ掲載数がディスクの運用Runbook数と一致",
                        len(cataloged) == len(files) and bool(files),
                        f"掲載={len(cataloged)} / ディスク={len(files)}"))

    entry_lines = _entry_lines(catalog_text)
    # A "trigger" cue: an em-dash separated 3rd field or a 'いつ/トリガー/場合/時' hint.
    trigger_re = re.compile(r"—.*—|いつ|トリガー|場合|とき|時に|障害|検知")
    without_trigger = [ln for ln in entry_lines if not trigger_re.search(ln)]
    results.append(_hyp("H6", "各エントリに『いつ開くか』のトリガー記載がある",
                        entry_lines and not without_trigger,
                        f"トリガー欠落={len(without_trigger)}件"))

    abs_links = _ABS_LINK_RE.findall(catalog_text)
    results.append(_hyp("H7", "リンクがリポジトリ相対(file:///・絶対パス無し)",
                        not abs_links, f"絶対パス={len(abs_links)}件"))

    ir = {"DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md",
          "INCIDENT_POSTMORTEM_RUNBOOK.md",
          "PRODUCTION_ROLLBACK_RUNBOOK.md"}
    ir_present = {f for f in ir if f in files}
    ir_missing = {f for f in ir_present if f not in cataloged}
    results.append(_hyp("H8", "インシデント対応Runbook(DR/ポストモーテム/ロールバック)を掲載",
                        not ir_missing, f"IR未掲載={sorted(ir_missing) or 'なし'}"))

    links = cataloged_runbook_links(catalog_text)
    dups = sorted({x for x in links if links.count(x) > 1})
    results.append(_hyp("H9", "カタログ内にRunbookリンクの重複が無い",
                        not dups, f"重複={dups or 'なし'}"))

    prior_ok = all(r["passed"] for r in results if r["id"] in {"H1", "H2", "H3", "H5"})
    results.append(_hyp("H10", "カタログとディスクが完全同期(索引ドリフト0)",
                        prior_ok, f"先行ドリフト={'なし' if prior_ok else 'あり'}"))

    return results


def _render_md(results: list[dict[str, Any]]) -> str:
    files = runbook_files()
    cataloged = cataloged_runbooks(read(CATALOG))
    ok = all(r["passed"] for r in results)
    lines = [
        "# 運用Runbookカタログ整合性監査 (T902)",
        "",
        f"- ディスク上の運用Runbook: **{len(files)}本**",
        f"- カタログ掲載: **{len(cataloged)}本**",
        f"- 総合判定: {'✅ PASS (索引ドリフト0)' if ok else '❌ FAIL (索引ドリフトあり)'}",
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
    parser = argparse.ArgumentParser(description="運用Runbookカタログ網羅整合ガード (T902)")
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
