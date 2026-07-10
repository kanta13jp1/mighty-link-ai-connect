"""Diagnosis fallback transparency audit harness (T885): 10 hypotheses.

runAnalysis() posts to /api/match and, before T885, silently rendered the
pre-seeded sample scores (95/88/92/82) as a genuine AI diagnosis on any non-OK
response — so a 429 (rate limit) or 500 on the live backend fabricated a
"perfect" fit with no indication. For a hiring/matching tool that is a real
trust defect (same family as the T872/T883/T884 error-swallowing fixes).

This harness verifies, statically against both HTML mirrors and src/app.py, that
the diagnosis flow now surfaces a "these are sample values" warning when the live
backend actually errors, while keeping the silent mock fallback for the static
GitHub Pages demo (every /api route 404s there — a sample diagnosis IS the
intended demo) and for true offline, so the CEO-shared demo is byte-unchanged.

Output: exports/diagnosis_fallback_transparency_audit.{json,md}. No secrets.
Run: `python scripts/audit_diagnosis_fallback_transparency.py`.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_FILES = [PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html"]
APP_PY = PROJECT_ROOT / "src" / "app.py"
WBS_PATH = PROJECT_ROOT / "data" / "WBS.tsv"
UAT_SPEC = PROJECT_ROOT / "docs" / "UAT_TEST_SPECIFICATION.md"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "diagnosis_fallback_transparency_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "diagnosis_fallback_transparency_audit.md"


def run_analysis_block(text: str) -> str:
    marker = "function runAnalysis("
    if marker not in text:
        return ""
    start = text.index(marker)
    rest = text[start + len(marker):]
    m = re.search(r"\n {8}(?:async )?function ", rest)
    end = start + len(marker) + (m.start() if m else 8000)
    return text[start:end]


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate() -> dict[str, Any]:
    texts = {p: p.read_text(encoding="utf-8", errors="replace") for p in INDEX_FILES}
    blocks = {p: run_analysis_block(t) for p, t in texts.items()}
    app_text = APP_PY.read_text(encoding="utf-8", errors="replace") if APP_PY.exists() else ""
    idx, src = INDEX_FILES[0], INDEX_FILES[1]

    def reads_detail(b: str) -> bool:
        return "serverDetail" in b or ".detail" in b

    results: list[dict[str, Any]] = []

    results.append(_hyp("H1", "index.html: runAnalysisが非OK時にサーバーdetailを読む",
                        reads_detail(blocks[idx]), "OK" if reads_detail(blocks[idx]) else "未読取"))
    results.append(_hyp("H2", "src/index.html: runAnalysisが非OK時にサーバーdetailを読む",
                        reads_detail(blocks[src]), "OK" if reads_detail(blocks[src]) else "未読取"))

    d404 = [p.name for p in INDEX_FILES if "!== 404" not in blocks[p]]
    results.append(_hyp("H3", "両ファイル: 404(静的デモ)と実バックエンドエラーを区別",
                        not d404, f"未区別={d404 or 'なし'}"))

    nolabel = [p.name for p in INDEX_FILES if "サンプル" not in blocks[p]]
    results.append(_hyp("H4", "両ファイル: 実エラー時にスコアを『サンプル』と明示",
                        not nolabel, f"未明示={nolabel or 'なし'}"))

    nomock = [p.name for p in INDEX_FILES if "Falling back to default mock" not in blocks[p]]
    results.append(_hyp("H5", "両ファイル: 静的デモ/オフラインの無言サンプルフォールバックを保持",
                        not nomock, f"欠落={nomock or 'なし'}"))

    # H6: notice helper defined + cleared at run start in both files.
    bad_reset = [
        p.name for p in INDEX_FILES
        if "function setDiagnosisFallbackNotice" not in texts[p]
        or 'setDiagnosisFallbackNotice("")' not in blocks[p]
    ]
    results.append(_hyp("H6", "両ファイル: バナーヘルパー定義＋実行開始時クリアがある",
                        not bad_reset, f"欠落={bad_reset or 'なし'}"))

    drift = blocks[idx] != blocks[src]
    results.append(_hyp("H7", "index.html と src/index.html の runAnalysis がバイト等価",
                        not drift, "ドリフトあり" if drift else "一致"))

    wbs_text = WBS_PATH.read_text(encoding="utf-8", errors="replace") if WBS_PATH.exists() else ""
    uat_text = UAT_SPEC.read_text(encoding="utf-8", errors="replace") if UAT_SPEC.exists() else ""
    wbs_ok = bool(re.search(r"(^|\n)T885\t", wbs_text))
    uat_ok = "TS-17" in uat_text and "T885" in uat_text
    results.append(_hyp("H8", "WBSにT885・UAT仕様書にTS-17(T885)が実在",
                        wbs_ok and uat_ok, f"WBS_T885={wbs_ok}, UAT_TS17={uat_ok}"))

    # H9: the backend really can error on /api/match (route + rate limit + consent 400).
    route_ok = '@app.post("/api/match")' in app_text
    rl_ok = '"/api/match"' in app_text and "RATE_LIMIT_EXPENSIVE_API_PATHS" in app_text
    consent_ok = "consent is required before running this API" in app_text
    results.append(_hyp("H9", "src/app.py: /api/matchが実在し429(expensive rate limit)/400(consent)を返しうる",
                        route_ok and rl_ok and consent_ok,
                        f"route={route_ok}, rate_limited={rl_ok}, consent400={consent_ok}"))

    prior_ok = all(h["passed"] for h in results)
    results.append(_hyp("H10", "診断フォールバック透明化が完全(ドリフト0)",
                        prior_ok, f"先行ドリフト={'なし' if prior_ok else 'あり'}"))

    return {
        "task": "T885",
        "index_files": [str(p.relative_to(PROJECT_ROOT)) for p in INDEX_FILES],
        "hypotheses": results,
        "all_passed": all(h["passed"] for h in results),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 診断フォールバック透明化 監査 (T885)",
        "",
        f"- 対象ファイル: {', '.join(report['index_files'])}",
        f"- 総合判定: {'✅ PASS (ドリフト0)' if report['all_passed'] else '❌ FAIL'}",
        "",
        "## 10仮説の検証結果",
        "",
        "| 仮説 | 内容 | 判定 | 詳細 |",
        "| :--- | :--- | :---: | :--- |",
    ]
    for h in report["hypotheses"]:
        lines.append(f"| {h['id']} | {h['title']} | {'✅' if h['passed'] else '❌'} | {h['detail']} |")
    lines += [
        "",
        "> 実バックエンドが 429/500 等のエラーを返した時のみサンプル値である旨を明示し、",
        "> 静的GitHub Pagesデモ(/api/match 404)・オフラインは従来の無言サンプル表示を維持する(デモ不変)。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit diagnosis fallback transparency (T885, 10 hypotheses)")
    parser.add_argument("--json", default=str(DEFAULT_JSON))
    parser.add_argument("--md", default=str(DEFAULT_MD))
    args = parser.parse_args()

    report = evaluate()
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.md).write_text(render_markdown(report), encoding="utf-8")

    passed = sum(1 for h in report["hypotheses"] if h["passed"])
    print(f"[diagnosis-fallback-audit] {passed}/{len(report['hypotheses'])} hypotheses passed "
          f"-> {'ALL PASS' if report['all_passed'] else 'FAIL'}")
    for h in report["hypotheses"]:
        print(f"  {'PASS' if h['passed'] else 'FAIL'} {h['id']}: {h['title']} ({h['detail']})")
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
