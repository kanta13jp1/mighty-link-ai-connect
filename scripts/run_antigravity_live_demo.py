#!/usr/bin/env python3
"""Fail closed unless the dedicated Antigravity workshop kit is demo-ready."""

from __future__ import annotations

import csv
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_DIR = PROJECT_ROOT / "docs" / "demo" / "antigravity_workshop"
INPUT_DIR = WORKSHOP_DIR / "input"
SYNTHETIC_MARKER = "SYNTHETIC_DATA_ONLY"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class _DemoHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []
        self.section_ids: list[str] = []
        self.section_attrs: list[dict[str, str]] = []
        self.heading_counts = {"h1": 0, "h2": 0}
        self.progressbars: list[dict[str, str]] = []
        self.external_refs: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name: value or "" for name, value in attrs}
        self.tags.append(tag)
        if tag == "section":
            self.section_ids.append(values.get("id", ""))
            self.section_attrs.append(values)
        if tag in self.heading_counts:
            self.heading_counts[tag] += 1
        if values.get("role") == "progressbar":
            self.progressbars.append(values)
        for name in ("href", "src"):
            value = values.get(name, "")
            if value.startswith(("http://", "https://", "//")):
                self.external_refs.append(value)

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.text_parts.append(text)


def _demo_hypothesis_checks(output_html: Path, customer_memo: Path) -> list[dict[str, object]]:
    raw = _read_text(output_html)
    memo = _read_text(customer_memo)
    parser = _DemoHTMLParser()
    parser.feed(raw)
    visible_text = " ".join(parser.text_parts)

    source_facts = [
        "サンプルテック株式会社",
        "ITサービス",
        "従業員120名",
        "営業提案の初稿作成に時間がかかる。",
        "案件情報が担当者ごとのメモに分散している。",
        "提案後の次アクションが曖昧になりやすい。",
        "既存メモから提案骨子を自動で整理する。",
        "出力形式を共通化し、レビュー時間を短縮する。",
        "82 / 100",
        "76 / 100",
        "68 / 100",
        "合成データで提案画面を試作する。",
        "営業責任者が出力項目をレビューする。",
        "実データ利用前に情報管理ルールを確認する。",
    ]
    missing_facts = [fact for fact in source_facts if fact not in visible_text]
    invented_claims = [claim for claim in ("高適合", "ROI", "削減率", "導入決定") if claim in visible_text]
    h1 = not missing_facts and not invented_claims and "SYNTHETIC_DATA_ONLY" in memo

    decision_markers = ("提案判断サマリー", "営業責任者レビュー待ち", "社外送付不可")
    h2 = all(marker in visible_text for marker in decision_markers)

    expected_sections = ["customer-pain-points", "proposal-summary", "fit-score", "next-actions"]
    h3 = parser.section_ids == expected_sections

    upper_html = raw.upper()
    h4 = "#00A5E3" in upper_html and "#EF7E00" in upper_html

    progress_values = {bar.get("aria-valuenow") for bar in parser.progressbars}
    h5 = (
        len(parser.progressbars) == 3
        and progress_values == {"68", "76", "82"}
        and "ヒアリングメモ記載の参考値" in visible_text
        and "確認優先" in visible_text
    )

    human_review_markers = (
        "営業責任者レビュー待ち",
        "最終判断と顧客送付は必ず人が行います。",
        "営業責任者が出力項目をレビューする。",
    )
    h6 = all(marker in visible_text for marker in human_review_markers)

    forbidden_tags = {"script", "form", "input", "iframe"}
    h7 = (
        "SYNTHETIC_DATA_ONLY" in raw
        and not parser.external_refs
        and not forbidden_tags.intersection(parser.tags)
    )

    compact_css = re.sub(r"\s+", " ", raw)
    h8 = all(
        marker in compact_css
        for marker in (
            "grid-template-columns: repeat(12, minmax(0, 1fr))",
            "grid-template-rows: minmax(0, 1fr) minmax(0, 1fr)",
            "min-height: calc(100vh - 32px)",
        )
    )

    h9 = all(
        marker in compact_css
        for marker in (
            'name="viewport"',
            "@media (max-width: 720px)",
            "grid-column: 1 / -1",
            "overflow-wrap: anywhere",
            "min-width: 0",
        )
    )

    progress_aria_ok = all(
        bar.get("aria-labelledby")
        and bar.get("aria-valuemin") == "0"
        and bar.get("aria-valuemax") == "100"
        and bar.get("aria-valuenow")
        for bar in parser.progressbars
    )
    sections_labelled = all(section.get("aria-labelledby") for section in parser.section_attrs)
    h10 = (
        {"header", "main", "footer"}.issubset(parser.tags)
        and parser.heading_counts == {"h1": 1, "h2": 4}
        and sections_labelled
        and progress_aria_ok
    )

    hypotheses = [
        ("H1_source_fidelity", h1, f"missing={missing_facts or 'none'}; invented={invented_claims or 'none'}"),
        ("H2_decision_clarity", h2, "company, review status, and send restriction are visible"),
        ("H3_information_order", h3, f"sections={parser.section_ids}"),
        ("H4_brand_fidelity", h4, "official #00A5E3 and #EF7E00 are present"),
        ("H5_score_explainability", h5, f"progress_values={sorted(progress_values)}"),
        ("H6_human_review", h6, "review owner and human final decision are explicit"),
        ("H7_demo_safety", h7, f"external_refs={len(parser.external_refs)}; forbidden_tags={sorted(forbidden_tags.intersection(parser.tags))}"),
        ("H8_desktop_first_view", h8, "12-column, two-row viewport layout is declared"),
        ("H9_mobile_resilience", h9, "single-column breakpoint and overflow protections are declared"),
        ("H10_accessibility", h10, f"headings={parser.heading_counts}; progressbars={len(parser.progressbars)}"),
    ]
    return [
        {"name": name, "path": output_html, "passed": passed, "detail": detail}
        for name, passed, detail in hypotheses
    ]


def collect_demo_kit_status(project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    workshop_dir = project_root / "docs" / "demo" / "antigravity_workshop"
    required_files = {
        "main_prompt": workshop_dir / "MAIN_PROMPT.txt",
        "backup_prompts": workshop_dir / "BACKUP_PROMPTS.txt",
        "customer_memo": workshop_dir / "input" / "customer_interview_memo.md",
        "expenses": workshop_dir / "input" / "expenses.csv",
        "sample_wbs": workshop_dir / "input" / "sample_wbs.tsv",
        "output_readme": workshop_dir / "output" / "README.md",
        "output_html": workshop_dir / "output" / "index.html",
    }

    checks: list[dict[str, object]] = []
    for name, path in required_files.items():
        exists = path.is_file() and path.stat().st_size > 0
        checks.append({"name": name, "path": path, "passed": exists, "detail": "present" if exists else "missing"})

    if not all(check["passed"] for check in checks):
        return {"passed": False, "checks": checks}

    for name in ("customer_memo", "expenses", "sample_wbs"):
        path = required_files[name]
        has_marker = SYNTHETIC_MARKER in _read_text(path)
        checks.append(
            {
                "name": f"{name}_synthetic_marker",
                "path": path,
                "passed": has_marker,
                "detail": "synthetic marker present" if has_marker else "synthetic marker missing",
            }
        )

    main_prompt = _read_text(required_files["main_prompt"])
    prompt_requirements = {
        "scoped_output": "docs/demo/antigravity_workshop/output/index.html",
        "no_unscoped_writes": "出力先以外に書き込まない",
        "browser_verification": "ブラウザで開き",
        "source_fidelity": "数値・判定・効果を追加しない",
        "human_review": "営業責任者レビュー待ち",
        "desktop_viewport": "1440x900",
        "mobile_viewport": "390x844",
        "three_line_report": "3行で報告",
    }
    for name, expected in prompt_requirements.items():
        present = expected in main_prompt
        checks.append(
            {
                "name": f"main_prompt_{name}",
                "path": required_files["main_prompt"],
                "passed": present,
                "detail": f"contains {expected!r}" if present else f"missing {expected!r}",
            }
        )

    expense_lines = _read_text(required_files["expenses"]).splitlines()[1:]
    expense_rows = list(csv.DictReader(expense_lines))
    expense_columns = {"伝票番号", "発生日付", "金額_JPY", "承認ステータス"}
    expense_ok = bool(expense_rows) and expense_columns.issubset(expense_rows[0])
    checks.append(
        {
            "name": "expenses_schema",
            "path": required_files["expenses"],
            "passed": expense_ok,
            "detail": f"rows={len(expense_rows)}",
        }
    )

    wbs_lines = _read_text(required_files["sample_wbs"]).splitlines()[1:]
    wbs_rows = list(csv.DictReader(wbs_lines, delimiter="\t"))
    wbs_columns = {"task_id", "task_name", "status", "due_date", "priority"}
    wbs_ok = bool(wbs_rows) and wbs_columns.issubset(wbs_rows[0])
    checks.append(
        {
            "name": "sample_wbs_schema",
            "path": required_files["sample_wbs"],
            "passed": wbs_ok,
            "detail": f"rows={len(wbs_rows)}",
        }
    )

    checks.extend(_demo_hypothesis_checks(required_files["output_html"], required_files["customer_memo"]))

    return {"passed": all(check["passed"] for check in checks), "checks": checks}


def verify_demo_data(project_root: Path = PROJECT_ROOT) -> int:
    result = collect_demo_kit_status(project_root)
    print("Google Antigravity 8/26 ライブデモキット検証")
    print("=" * 56)
    for check in result["checks"]:
        status = "OK" if check["passed"] else "FAIL"
        path = Path(check["path"])
        try:
            display_path = path.relative_to(project_root)
        except ValueError:
            display_path = path
        print(f"[{status}] {check['name']}: {display_path} ({check['detail']})")
    print("\n[PASS] デモキットは合成データ・限定出力・確認手順を満たしています。" if result["passed"] else "\n[FAIL] デモキットの不足を修正してください。")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(verify_demo_data())
