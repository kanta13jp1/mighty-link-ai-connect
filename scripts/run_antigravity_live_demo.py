#!/usr/bin/env python3
"""Fail closed unless the dedicated Antigravity workshop kit is demo-ready."""

from __future__ import annotations

import csv
import io
from pathlib import Path
import sys


if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_DIR = PROJECT_ROOT / "docs" / "demo" / "antigravity_workshop"
INPUT_DIR = WORKSHOP_DIR / "input"
SYNTHETIC_MARKER = "SYNTHETIC_DATA_ONLY"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def collect_demo_kit_status(project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    workshop_dir = project_root / "docs" / "demo" / "antigravity_workshop"
    required_files = {
        "main_prompt": workshop_dir / "MAIN_PROMPT.txt",
        "backup_prompts": workshop_dir / "BACKUP_PROMPTS.txt",
        "customer_memo": workshop_dir / "input" / "customer_interview_memo.md",
        "expenses": workshop_dir / "input" / "expenses.csv",
        "sample_wbs": workshop_dir / "input" / "sample_wbs.tsv",
        "output_readme": workshop_dir / "output" / "README.md",
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
    raise SystemExit(verify_demo_data())
