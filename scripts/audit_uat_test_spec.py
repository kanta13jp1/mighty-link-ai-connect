"""Human-executable UAT test-specification guard (T882).

docs/UAT_TEST_SPECIFICATION.md is a manual test specification (テスト仕様書): a
person follows each case step by step against production and marks OK/NG. T845's
human production sign-off needs it. This harness keeps the spec complete,
executable, and consistent with the real WBS tasks and API endpoints by parsing
each case and verifying ten hypotheses.

Every case must carry preconditions, >=2 numbered steps, an expected result,
and explicit OK *and* NG criteria so the pass/fail judgment is unambiguous.
Referenced WBS ids and API paths must really exist, and all GA feature domains
must be covered. Output: exports/uat_test_spec_audit.{json,md}. No secrets.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = PROJECT_ROOT / "docs" / "UAT_TEST_SPECIFICATION.md"
WBS_PATH = PROJECT_ROOT / "data" / "WBS.tsv"
APP_PY = PROJECT_ROOT / "src" / "app.py"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "uat_test_spec_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "uat_test_spec_audit.md"

MIN_CASES = 12
MIN_STEPS = 2

# Fields every case must carry and fill (テスト手順 is validated via step count).
REQUIRED_FIELDS = [
    "対象機能", "関連WBS", "前提条件", "期待結果", "OK判定", "NG判定", "実施結果",
]

# GA feature domains that must each be covered by at least one case.
REQUIRED_DOMAINS = [
    "適性", "勤怠", "営業メール", "管理者", "同意", "エクスポート",
    "削除", "サポート", "フィードバック", "ライトモード", "ヘルス", "レートリミット",
]

_CASE_RE = re.compile(r"^###\s+(TS-\d+)\s+(.*)$")
_FIELD_RE = re.compile(r"^\s*[-*]\s*\*\*(.+?)\*\*\s*[:：]\s*(.*)$")
_STEP_RE = re.compile(r"^\s*\d+\.\s+(.*)$")
_WBS_TOKEN_RE = re.compile(r"T\d+(?:_\d+)*")


def parse_spec(md_text: str) -> list[dict[str, Any]]:
    """Parse `### TS-xx <title>` cases with their labeled fields and numbered steps."""
    cases: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in md_text.splitlines():
        header = _CASE_RE.match(line)
        if header:
            current = {
                "id": header.group(1),
                "title": header.group(2).strip(),
                "fields": {},
                "steps": [],
            }
            cases.append(current)
            continue
        if current is None:
            continue
        field = _FIELD_RE.match(line)
        if field:
            current["fields"][field.group(1).strip()] = field.group(2).strip()
            continue
        step = _STEP_RE.match(line)
        if step:
            current["steps"].append(step.group(1).strip())
    return cases


def extract_api_path(text: str) -> str | None:
    """Return the first real API path (e.g. '/api/health') or None for UI-only cases."""
    m = re.search(r"(/[A-Za-z][\w/{}.\-]{2,})", text or "")
    return m.group(1) if m else None


def load_wbs_ids() -> set[str]:
    if not WBS_PATH.exists():
        return set()
    ids: set[str] = set()
    for line in WBS_PATH.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
        if line.strip():
            ids.add(line.split("\t")[0])
    return ids


def load_api_paths() -> set[str]:
    if not APP_PY.exists():
        return set()
    text = APP_PY.read_text(encoding="utf-8", errors="replace")
    return set(re.findall(r"@app\.(?:get|post|put|delete|patch)\(\"([^\"]+)\"", text))


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def missing_domains(cases: list[dict[str, Any]]) -> list[str]:
    blob = " ".join(c["title"] + " " + c["fields"].get("対象機能", "") for c in cases)
    return [kw for kw in REQUIRED_DOMAINS if kw not in blob]


def evaluate(
    cases: list[dict[str, Any]],
    wbs_ids: set[str],
    api_paths: set[str],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    results.append(_hyp(
        "H1", f"テストケースが{MIN_CASES}件以上",
        len(cases) >= MIN_CASES, f"件数={len(cases)}"))

    ids = [c["id"] for c in cases]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    fmt_ok = all(re.fullmatch(r"TS-\d+", i) for i in ids)
    results.append(_hyp(
        "H2", "テストIDが一意かつTS-連番形式",
        not dup and fmt_ok, f"重複={dup or 'なし'}, 形式OK={fmt_ok}"))

    missing_fields = {
        c["id"]: [f for f in REQUIRED_FIELDS if not c["fields"].get(f)]
        for c in cases
    }
    missing_fields = {k: v for k, v in missing_fields.items() if v}
    results.append(_hyp(
        "H3", "全ケースが必須フィールドを保有(空欄なし)",
        not missing_fields, f"欠落={missing_fields or 'なし'}"))

    few_steps = [c["id"] for c in cases if len(c["steps"]) < MIN_STEPS]
    results.append(_hyp(
        "H4", f"全ケースのテスト手順が{MIN_STEPS}ステップ以上(人間が追える具体性)",
        not few_steps, f"手順不足={few_steps or 'なし'}"))

    no_criteria = [
        c["id"] for c in cases
        if not c["fields"].get("OK判定") or not c["fields"].get("NG判定")
    ]
    results.append(_hyp(
        "H5", "全ケースにOK判定とNG判定を両方明記(合否判断可能)",
        not no_criteria, f"判定欠落={no_criteria or 'なし'}"))

    bad_wbs = {}
    for c in cases:
        toks = _WBS_TOKEN_RE.findall(c["fields"].get("関連WBS", ""))
        unknown = [t for t in toks if t not in wbs_ids]
        if not toks or unknown:
            bad_wbs[c["id"]] = unknown or "参照なし"
    results.append(_hyp(
        "H6", "全ケースの関連WBSが実在(data/WBS.tsv)",
        not bad_wbs, f"不正WBS={bad_wbs or 'なし'}"))

    bad_api = {}
    for c in cases:
        path = extract_api_path(c["fields"].get("関連API", ""))
        if path is not None and path not in api_paths:
            bad_api[c["id"]] = path
    results.append(_hyp(
        "H7", "API記載ケースの関連APIがsrc/app.pyに実在",
        not bad_api, f"不正API={bad_api or 'なし'}"))

    miss_dom = missing_domains(cases)
    results.append(_hyp(
        "H8", "GA主要ドメインを全て網羅",
        not miss_dom, f"未網羅={miss_dom or 'なし'}"))

    no_marker = [
        c["id"] for c in cases
        if "OK" not in c["fields"].get("実施結果", "")
        or "NG" not in c["fields"].get("実施結果", "")
    ]
    results.append(_hyp(
        "H9", "全ケースの実施結果欄にOK/NG記入マーカーがある",
        not no_marker, f"記入欄欠落={no_marker or 'なし'}"))

    no_prior_drift = all(h["passed"] for h in results)
    results.append(_hyp(
        "H10", "仕様書全体が完全・整合(ドリフト0)",
        no_prior_drift, f"先行ドリフト={'なし' if no_prior_drift else 'あり'}"))

    return results


def run_audit() -> dict[str, Any]:
    spec_text = SPEC_PATH.read_text(encoding="utf-8", errors="replace") if SPEC_PATH.exists() else ""
    cases = parse_spec(spec_text)
    wbs_ids = load_wbs_ids()
    api_paths = load_api_paths()
    hypotheses = evaluate(cases, wbs_ids, api_paths)
    return {
        "task": "T882",
        "spec_path": str(SPEC_PATH.relative_to(PROJECT_ROOT)),
        "case_count": len(cases),
        "case_ids": [c["id"] for c in cases],
        "missing_domains": missing_domains(cases),
        "hypotheses": hypotheses,
        "all_passed": all(h["passed"] for h in hypotheses),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# UATテスト仕様書 整合監査 (T882)",
        "",
        f"- 対象: `{report['spec_path']}`",
        f"- テストケース数: **{report['case_count']}**",
        f"- 未網羅ドメイン: {report['missing_domains'] or 'なし'}",
        f"- 総合判定: {'✅ PASS (ドリフト0)' if report['all_passed'] else '❌ FAIL'}",
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=str(DEFAULT_JSON))
    parser.add_argument("--md", default=str(DEFAULT_MD))
    args = parser.parse_args()

    report = run_audit()
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    Path(args.md).write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
