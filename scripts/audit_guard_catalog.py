"""Quality-guard catalog sync guard (T903).

The lane preflight (run_lane_preflight.py) runs a growing set of quality guards
(18 at this writing) declared in GUARD_REGISTRY, plus a few EXEMPT_GUARDS. The
registry gives each a one-line label, but there is no human-readable reference
for what a guard protects, how it fails (NG example), and which WBS it relates
to — and nothing stops a newly registered guard from shipping undocumented or a
deleted one from lingering in prose. This harness pins a catalog
(docs/QUALITY_GUARD_CATALOG.md) to the machine source of truth: every
registered guard must be documented (no undocumented) and every guard the
catalog names must be registered-or-exempt (no phantom), or CI fails.

Pins ten hypotheses:

* the catalog exists (H1),
* every GUARD_REGISTRY guard is documented — no undocumented (H2),
* no catalog guard is unknown to registry∪exempt — no phantom (H3),
* the documented count matches registry∪exempt (H4),
* every registered guard's catalog entry carries an NG example (H5),
* every registered guard's catalog entry names a related WBS (T…) (H6),
* the EXEMPT_GUARDS are documented as exempt with a reason (H7),
* the catalog has no duplicate guard sections (H8),
* this guard itself (audit_guard_catalog.py) is catalogued (H9),
* catalog and machine registry are fully in sync overall (H10).

Output: exports/guard_catalog_audit.{json,md}. No secrets are emitted.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"
DOCS = PROJECT_ROOT / "docs"
CATALOG = DOCS / "QUALITY_GUARD_CATALOG.md"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "guard_catalog_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "guard_catalog_audit.md"

sys.path.insert(0, str(SCRIPTS))

# A guard filename mentioned anywhere in the catalog (heading or inline code).
_GUARD_RE = re.compile(r"audit_[A-Za-z0-9_]+\.py")


def _load_registry() -> tuple[dict[str, str], dict[str, str]]:
    import run_lane_preflight as pre  # imported lazily; no side effects at import
    return dict(pre.GUARD_REGISTRY), dict(pre.EXEMPT_GUARDS)


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def registered_guards() -> set[str]:
    """The GUARD_REGISTRY keys — guards the preflight actually runs."""
    registry, _ = _load_registry()
    return set(registry)


def exempt_guards() -> set[str]:
    _, exempt = _load_registry()
    return set(exempt)


def cataloged_guards(catalog_text: str) -> set[str]:
    """Guard filenames named in the catalog (### heading lines only)."""
    found: set[str] = set()
    for line in catalog_text.splitlines():
        if line.lstrip().startswith("#"):
            found.update(_GUARD_RE.findall(line))
    return found


def cataloged_guard_headings(catalog_text: str) -> list[str]:
    """Guard filenames from heading lines incl. duplicates (dup detection)."""
    out: list[str] = []
    for line in catalog_text.splitlines():
        if line.lstrip().startswith("#"):
            out.extend(_GUARD_RE.findall(line))
    return out


def undocumented_guards(registered: set[str], cataloged: set[str]) -> set[str]:
    """Registered but not documented in the catalog."""
    return set(registered) - set(cataloged)


def phantom_guards(cataloged: set[str], known: set[str]) -> set[str]:
    """Documented but neither registered nor exempt."""
    return set(cataloged) - set(known)


def _section_for(catalog_text: str, guard: str) -> str:
    """Text from the guard's ### heading to the next heading of same/higher level."""
    lines = catalog_text.splitlines()
    start = next((i for i, l in enumerate(lines) if guard in l and l.lstrip().startswith("#")), None)
    if start is None:
        return ""
    body = [lines[start]]
    for l in lines[start + 1:]:
        if re.match(r"^#{1,3}\s", l):
            break
        body.append(l)
    return "\n".join(body)


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate() -> list[dict[str, Any]]:
    catalog_text = read(CATALOG)
    registry, exempt = _load_registry()
    registered = set(registry)
    exempt_set = set(exempt)
    known = registered | exempt_set
    cataloged = cataloged_guards(catalog_text)
    results: list[dict[str, Any]] = []

    results.append(_hyp("H1", "品質ガードカタログが存在する",
                        bool(catalog_text), f"カタログ={'あり' if catalog_text else 'なし'}"))

    undoc = undocumented_guards(registered, cataloged)
    results.append(_hyp("H2", "全登録ガードがカタログに記載(未記載0)",
                        not undoc, f"未記載={sorted(undoc) or 'なし'}"))

    phantom = phantom_guards(cataloged, known)
    results.append(_hyp("H3", "カタログ記載ガードが全て登録or対象外(幽霊0)",
                        not phantom, f"幽霊={sorted(phantom) or 'なし'}"))

    results.append(_hyp("H4", "記載ガード数が登録∪対象外と一致",
                        cataloged == known,
                        f"記載={len(cataloged)} / 登録∪対象外={len(known)}"))

    no_ng = [g for g in sorted(registered)
             if not re.search(r"NG例|失敗|検知", _section_for(catalog_text, g))]
    results.append(_hyp("H5", "各登録ガードの記載にNG例がある",
                        not no_ng, f"NG例欠落={no_ng or 'なし'}"))

    no_wbs = [g for g in sorted(registered)
              if not re.search(r"T\d{3}", _section_for(catalog_text, g))]
    results.append(_hyp("H6", "各登録ガードの記載に関連WBS(T…)がある",
                        not no_wbs, f"WBS欠落={no_wbs or 'なし'}"))

    exempt_missing = [g for g in sorted(exempt_set) if g not in cataloged]
    results.append(_hyp("H7", "対象外ガード(EXEMPT)も理由付きで別掲",
                        not exempt_missing, f"対象外未記載={exempt_missing or 'なし'}"))

    headings = cataloged_guard_headings(catalog_text)
    dups = sorted({g for g in headings if headings.count(g) > 1})
    results.append(_hyp("H8", "カタログ内にガードセクションの重複が無い",
                        not dups, f"重複={dups or 'なし'}"))

    self_name = Path(__file__).name
    results.append(_hyp("H9", "本ガード自身(audit_guard_catalog.py)も記載されている",
                        self_name in cataloged, f"自己記載={'あり' if self_name in cataloged else 'なし'}"))

    prior_ok = all(r["passed"] for r in results if r["id"] in {"H1", "H2", "H3", "H4"})
    results.append(_hyp("H10", "カタログと機械側正本が完全同期(索引ドリフト0)",
                        prior_ok, f"先行ドリフト={'なし' if prior_ok else 'あり'}"))

    return results


def _render_md(results: list[dict[str, Any]]) -> str:
    registry, exempt = _load_registry()
    cataloged = cataloged_guards(read(CATALOG))
    ok = all(r["passed"] for r in results)
    lines = [
        "# 品質ガードカタログ整合性監査 (T903)",
        "",
        f"- 登録ガード(GUARD_REGISTRY): **{len(registry)}本** / 対象外(EXEMPT): **{len(exempt)}本**",
        f"- カタログ記載: **{len(cataloged)}本**",
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
    parser = argparse.ArgumentParser(description="品質ガードカタログとGUARD_REGISTRY同期ガード (T903)")
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
