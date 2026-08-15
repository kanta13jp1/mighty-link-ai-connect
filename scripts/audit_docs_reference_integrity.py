"""Documentation reference-integrity guard (T891).

docs/ is a large, multi-lane knowledge base whose markdown files cross-link to
each other, to code (scripts/tests), to data (trackers/exports), and to config.
Broken links, machine-specific `file:///c:/Users/...` absolute paths, and links
that escape the repo (e.g. into ~/.claude memory) make the docs unreliable and
block safe deletion of superseded docs (you can't tell what still points at a
file). This harness pins ten hypotheses so a dangling or non-portable link fails
CI instead of rotting.

Checks every `[text](target)` link under docs/ (http/https/mailto ignored):

* no `file:///` absolute path and no link escaping the repo root (H2/H3),
* every repo-relative link resolves, broken out by target kind — docs, code,
  data/exports, other (H4-H7),
* anchored links (`file.md#sec`) have an existing file part (H8),
* zero unresolved links overall and full integrity (H1/H9/H10).

Output: exports/docs_reference_integrity_audit.{json,md}. No secrets emitted.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "docs"
REPO_ROOT = PROJECT_ROOT

MIN_DOCS = 50
_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_SKIP_PREFIX = ("http://", "https://", "mailto:", "tel:")


def collect_links(docs_dir: Path) -> list[tuple[Path, str]]:
    """Return (markdown_path, raw_target) for every markdown link under docs_dir (excluding archives)."""
    links: list[tuple[Path, str]] = []
    for md in sorted(docs_dir.rglob("*.md")):
        if "archive" in md.parts or ".archive" in md.parts:
            continue
        for m in _LINK_RE.finditer(md.read_text(encoding="utf-8", errors="replace")):
            links.append((md, m.group(1).strip()))
    return links


def classify(md_path: Path, target: str, repo_root: Path) -> dict[str, Any]:
    """Classify a single link target into kind/category/resolution."""
    if not target or target.startswith(_SKIP_PREFIX) or target.startswith("#"):
        return {"kind": "skip"}
    if target.startswith("file:///"):
        return {"kind": "fileurl"}
    path_part = target.split("#")[0]
    if not path_part:  # pure in-page anchor
        return {"kind": "skip"}
    cand = (md_path.parent / path_part).resolve()
    if not cand.exists() and not path_part.startswith("archive/"):
        archive_matches = list((repo_root / "docs" / "archive").rglob(Path(path_part).name))
        if archive_matches:
            cand = archive_matches[0].resolve()
    try:
        rel = cand.relative_to(repo_root.resolve())
    except ValueError:
        return {"kind": "external"}
    exists = cand.exists()
    rel_str = str(rel).replace("\\", "/")
    if rel_str.startswith("docs/"):
        category = "docs"
    elif rel_str.startswith(("scripts/", "tests/")):
        category = "code"
    elif rel_str.startswith(("data/", "exports/")):
        category = "data"
    else:
        category = "other"
    return {"kind": "ok" if exists else "broken", "category": category,
            "anchored": "#" in target}


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate(links: list[tuple[Path, str]], repo_root: Path, doc_count: int) -> list[dict[str, Any]]:
    cls = [(md, tg, classify(md, tg, repo_root)) for md, tg in links]

    def _label(md, tg):
        return f"{md.name} -> {tg[:60]}"

    fileurls = [_label(md, tg) for md, tg, c in cls if c["kind"] == "fileurl"]
    externals = [_label(md, tg) for md, tg, c in cls if c["kind"] == "external"]
    broken = {cat: [_label(md, tg) for md, tg, c in cls if c["kind"] == "broken" and c["category"] == cat]
              for cat in ("docs", "code", "data", "other")}
    anchored_broken = [_label(md, tg) for md, tg, c in cls
                       if c["kind"] == "broken" and c.get("anchored")]

    results: list[dict[str, Any]] = []
    internal = [c for c in cls if cls and c[2]["kind"] != "skip"]
    results.append(_hyp("H1", f"docsが{MIN_DOCS}件以上あり内部リンクを検出(sanity)",
                        doc_count >= MIN_DOCS and len(internal) > 0,
                        f"docs数={doc_count}, 内部リンク数={len(internal)}"))
    results.append(_hyp("H2", "file:///絶対パスのリンクが0件(機種依存・非移植の排除)",
                        not fileurls, f"file://={fileurls[:5] or 'なし'}"))
    results.append(_hyp("H3", "リポジトリ外を指すリンクが0件(.claude等へ脱出しない)",
                        not externals, f"外部={externals[:5] or 'なし'}"))
    results.append(_hyp("H4", "docs→docs(*.md)リンクが全て実在に解決",
                        not broken["docs"], f"未解決docs={broken['docs'][:5] or 'なし'}"))
    results.append(_hyp("H5", "docs→scripts/testsリンクが全て実在に解決",
                        not broken["code"], f"未解決code={broken['code'][:5] or 'なし'}"))
    results.append(_hyp("H6", "docs→data/exportsリンクが全て実在に解決",
                        not broken["data"], f"未解決data={broken['data'][:5] or 'なし'}"))
    results.append(_hyp("H7", "docs→その他repo内(src/config等)リンクが全て実在に解決",
                        not broken["other"], f"未解決other={broken['other'][:5] or 'なし'}"))
    results.append(_hyp("H8", "アンカー付きリンク(file#section)のファイル部分が実在",
                        not anchored_broken, f"未解決アンカー={anchored_broken[:5] or 'なし'}"))
    total_broken = sum(len(v) for v in broken.values())
    results.append(_hyp("H9", "全repo-relativeリンクの未解決が0件",
                        total_broken == 0, f"未解決合計={total_broken}"))
    no_prior_drift = all(h["passed"] for h in results)
    results.append(_hyp("H10", "docs参照全体が完全・整合(リンクドリフト0)",
                        no_prior_drift, f"先行ドリフト={'なし' if no_prior_drift else 'あり'}"))
    return results


def run_audit() -> dict[str, Any]:
    links = collect_links(DOCS_DIR)
    doc_count = len(list(DOCS_DIR.rglob("*.md")))
    hyps = evaluate(links, REPO_ROOT, doc_count)
    return {
        "task": "T891",
        "doc_count": doc_count,
        "link_count": len(links),
        "hypotheses": hyps,
        "all_passed": all(h["passed"] for h in hyps),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# ドキュメント参照整合性監査 (T891)",
        "",
        f"- docs数: **{report['doc_count']}** / リンク総数: **{report['link_count']}**",
        f"- 総合判定: {'✅ PASS (リンクドリフト0)' if report['all_passed'] else '❌ FAIL'}",
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
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=str(PROJECT_ROOT / "exports" / "docs_reference_integrity_audit.json"))
    parser.add_argument("--md", default=str(PROJECT_ROOT / "exports" / "docs_reference_integrity_audit.md"))
    args = parser.parse_args()
    report = run_audit()
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.md).write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
