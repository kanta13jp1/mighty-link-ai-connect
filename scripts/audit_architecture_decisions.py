"""Architecture decision record (ADR) completeness guard (T912).

A handover team (T850) can read the code and see *what* the stack is, but not
*why*: why Firebase+Supabase rather than Render/Firestore, why a dedicated
mightylink-app.com on お名前.com rather than the company domain, why Gemini
Flash, why Stripe with live deferred, why three AI lanes. That rationale was
scattered across cost reports, incident notes and the issue tracker, and
HOSTING_AND_DATABASE_SELECTION.md covered only hosting/DB with barely any
record of rejected alternatives.

This harness keeps docs/ARCHITECTURE_DECISION_RECORDS.md complete: numbered
records, each with context / decision / **rejected alternatives** / consequences
/ status / evidence, the required decisions all covered, and evidence links that
resolve. A decision recorded without its alternatives is not a decision record,
so that case fails.

Pins ten hypotheses: the log exists (H1), ids are 1..N unique (H2), every ADR
carries the six elements (H3), alternatives are non-trivial (H4), required
decisions are covered (H5), statuses are allowed (H6), evidence links resolve
(H7), retired ADRs name a successor/reason (H8), no credentials or registration
facts (H9), overall completeness (H10).

Output: exports/architecture_decisions_audit.{json,md}. No secrets are emitted.
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
ADR_DOC = DOCS / "ARCHITECTURE_DECISION_RECORDS.md"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "architecture_decisions_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "architecture_decisions_audit.md"

ELEMENTS = ["背景", "決定", "代替案", "影響", "ステータス", "根拠"]
REQUIRED_DECISIONS = ["ホスティング", "ドメイン", "AIモデル", "課金", "レーン"]
ALLOWED_STATUS = ["採用済み", "見直し中", "廃止"]

_ADR_RE = re.compile(r"^##\s+(ADR-(\d{4}))\s*[:：]?\s*(.*)$", re.M)
_LINK_RE = re.compile(r"\]\(([A-Za-z0-9_./-]+\.md)\)")


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def adr_sections(text: str) -> dict[str, str]:
    """{ADR-NNNN: section body}."""
    out: dict[str, str] = {}
    matches = list(_ADR_RE.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[m.group(1)] = text[m.start():end]
    return out


def adr_ids(text: str) -> list[int]:
    return [int(m.group(2)) for m in _ADR_RE.finditer(text)]


def missing_elements(body: str) -> list[str]:
    return [e for e in ELEMENTS if e not in body]


def alternatives_text(body: str) -> str:
    m = re.search(r"代替案[^\n]*\n(.*?)(?=\n- \*\*|\n## |\Z)", body, re.S)
    return m.group(1).strip() if m else ""


def missing_required(text: str) -> list[str]:
    return [d for d in REQUIRED_DECISIONS if d not in text]


def dangling_links(text: str, docs_dir: Path = DOCS) -> list[str]:
    bad = []
    for m in _LINK_RE.finditer(text):
        if not (docs_dir / m.group(1)).exists():
            bad.append(m.group(1))
    return sorted(set(bad))


def _status_of(body: str) -> str:
    m = re.search(r"ステータス\*\*\s*[:：]?\s*([^\n|]+)", body)
    return m.group(1).strip().strip("*").strip() if m else ""


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate() -> list[dict[str, Any]]:
    text = read(ADR_DOC)
    sections = adr_sections(text)
    results: list[dict[str, Any]] = []

    results.append(_hyp("H1", "ADR記録が存在する",
                        bool(text) and bool(sections), f"ADR数={len(sections)}"))

    ids = adr_ids(text)
    seq_ok = bool(ids) and len(ids) == len(set(ids)) and ids == list(range(1, len(ids) + 1))
    results.append(_hyp("H2", "ADR番号が1..Nで一意(重複・欠番0)",
                        seq_ok, f"ids={ids}"))

    gaps = {a: missing_elements(b) for a, b in sections.items() if missing_elements(b)}
    results.append(_hyp("H3", "各ADRが6要素(背景/決定/代替案/影響/ステータス/根拠)を持つ",
                        not gaps, f"要素欠落={gaps or 'なし'}"))

    thin = [a for a, b in sections.items() if len(alternatives_text(b)) < 20]
    results.append(_hyp("H4", "各ADRに代替案と却下理由が実質的に記載",
                        not thin, f"代替案が空/希薄={thin or 'なし'}"))

    miss = missing_required(text)
    results.append(_hyp("H5", "必須の主要決定を網羅",
                        not miss, f"未記録={miss or 'なし'}"))

    bad_status = {a: _status_of(b) for a, b in sections.items()
                  if not any(s in _status_of(b) for s in ALLOWED_STATUS)}
    results.append(_hyp("H6", "ステータスが許容集合(採用済み/見直し中/廃止)",
                        not bad_status, f"不正ステータス={bad_status or 'なし'}"))

    dangling = dangling_links(text)
    results.append(_hyp("H7", "根拠docsリンクが実在(切れリンク0)",
                        not dangling, f"切れリンク={dangling or 'なし'}"))

    retired_bad = [a for a, b in sections.items()
                   if "廃止" in _status_of(b)
                   and not re.search(r"ADR-\d{4}|廃止理由", b.replace(a, "", 1))]
    results.append(_hyp("H8", "廃止ADRに後継ADRまたは廃止理由が併記",
                        not retired_bad, f"後継/理由なし={retired_bad or 'なし'}"))

    forbidden = [p for p in (r"sk_(?:live|test)_", r"AIza[0-9A-Za-z_-]{10,}", r"〒\d{3}-\d{4}")
                 if re.search(p, text)]
    results.append(_hyp("H9", "認証情報・登記情報が混入していない",
                        not forbidden, f"検出={forbidden or 'なし'}"))

    prior_ok = all(r["passed"] for r in results if r["id"] in {"H1", "H2", "H3", "H4", "H5", "H7"})
    results.append(_hyp("H10", "ADR記録が完全(意思決定の追跡可能性)",
                        prior_ok, f"先行ドリフト={'なし' if prior_ok else 'あり'}"))

    return results


def _render_md(results: list[dict[str, Any]]) -> str:
    text = read(ADR_DOC)
    sections = adr_sections(text)
    ok = all(r["passed"] for r in results)
    lines = [
        "# アーキテクチャ意思決定記録(ADR)監査 (T912)",
        "",
        f"- 記録済みADR: **{len(sections)}件** ({', '.join(sorted(sections)) or 'なし'})",
        f"- 総合判定: {'✅ PASS (追跡可能性あり)' if ok else '❌ FAIL (記録不備あり)'}",
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
    parser = argparse.ArgumentParser(description="ADR完全性ガード (T912)")
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
