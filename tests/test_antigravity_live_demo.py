from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from run_antigravity_live_demo import collect_demo_kit_status


def test_committed_antigravity_demo_kit_is_fail_closed_and_ready():
    result = collect_demo_kit_status(PROJECT_ROOT)

    assert result["passed"] is True
    assert all(check["passed"] for check in result["checks"])


def test_demo_kit_rejects_missing_synthetic_marker(tmp_path: Path):
    workshop = tmp_path / "docs" / "demo" / "antigravity_workshop"
    input_dir = workshop / "input"
    output_dir = workshop / "output"
    input_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)

    (workshop / "MAIN_PROMPT.txt").write_text(
        "docs/demo/antigravity_workshop/output/index.html\n"
        "出力先以外に書き込まない\nブラウザで開き\n3行で報告\n",
        encoding="utf-8",
    )
    (workshop / "BACKUP_PROMPTS.txt").write_text("backup", encoding="utf-8")
    (input_dir / "customer_interview_memo.md").write_text("no marker", encoding="utf-8")
    (input_dir / "expenses.csv").write_text(
        "SYNTHETIC_DATA_ONLY,demo\n伝票番号,発生日付,金額_JPY,承認ステータス\n1,2026-08-01,100,済\n",
        encoding="utf-8",
    )
    (input_dir / "sample_wbs.tsv").write_text(
        "SYNTHETIC_DATA_ONLY\tdemo\ntask_id\ttask_name\tstatus\tdue_date\tpriority\nT1\tDemo\t未着手\t2026-08-20\t高\n",
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text("output", encoding="utf-8")

    result = collect_demo_kit_status(tmp_path)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "customer_memo_synthetic_marker" in failed
