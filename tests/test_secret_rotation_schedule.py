import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import check_secret_rotation_schedule as rotation


HEADER = (
    "secret_id\tprovider\tsecret_name\tenvironment\tstorage_location\t"
    "rotation_owner\trotation_interval_days\trotation_anchor_date\t"
    "warning_days\trequired\tverification_method\tnotes\n"
)


def write_inventory(path: Path, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(HEADER + "".join(rows), encoding="utf-8")


def test_read_inventory_and_evaluate_ok(tmp_path):
    inventory = tmp_path / "data" / "secret_rotation_inventory.tsv"
    write_inventory(
        inventory,
        [
            "SEC_TEST\tProvider\tTEST_SECRET\tproduction\tGitHub secret\tCodex\t365\t2026-06-14\t30\tyes\tconfirm in console\tmetadata only\n",
        ],
    )

    items = rotation.read_inventory(inventory)
    result = rotation.evaluate_item(items[0], rotation.parse_date("2026-06-14"))

    assert len(items) == 1
    assert result.status == "ok"
    assert result.next_rotation_due_date == "2027-06-14"
    assert result.days_until_due == 365


def test_due_soon_status_uses_warning_days(tmp_path):
    inventory = tmp_path / "data" / "secret_rotation_inventory.tsv"
    write_inventory(
        inventory,
        [
            "SEC_SOON\tProvider\tTEST_SECRET\tproduction\tGitHub secret\tCodex\t30\t2026-06-01\t10\tyes\tconfirm\tmetadata only\n",
        ],
    )

    item = rotation.read_inventory(inventory)[0]
    result = rotation.evaluate_item(item, rotation.parse_date("2026-06-25"))

    assert result.status == "due_soon"
    assert result.days_until_due == 6


def test_fail_on_overdue_required_returns_one(tmp_path):
    inventory = tmp_path / "data" / "secret_rotation_inventory.tsv"
    report = tmp_path / "exports" / "secret_rotation_report.json"
    write_inventory(
        inventory,
        [
            "SEC_OVERDUE\tProvider\tTEST_SECRET\tproduction\tGitHub secret\tCodex\t10\t2026-06-01\t3\tyes\tconfirm\tmetadata only\n",
        ],
    )

    exit_code = rotation.main(
        [
            "--root",
            str(tmp_path),
            "--inventory-path",
            "data/secret_rotation_inventory.tsv",
            "--report-path",
            "exports/secret_rotation_report.json",
            "--as-of",
            "2026-06-20",
            "--fail-on-overdue",
        ]
    )
    payload = json.loads(report.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert payload["summary"]["overdue_required"] == 1


def test_secret_like_material_is_rejected(tmp_path):
    inventory = tmp_path / "data" / "secret_rotation_inventory.tsv"
    report = tmp_path / "exports" / "secret_rotation_report.json"
    write_inventory(
        inventory,
        [
            "SEC_BAD\tProvider\tsk-thisShouldNotAppear1234567890\tproduction\tGitHub secret\tCodex\t365\t2026-06-14\t30\tyes\tconfirm\tmetadata only\n",
        ],
    )

    exit_code = rotation.main(
        [
            "--root",
            str(tmp_path),
            "--inventory-path",
            "data/secret_rotation_inventory.tsv",
            "--report-path",
            "exports/secret_rotation_report.json",
            "--as-of",
            "2026-06-14",
        ]
    )
    payload = json.loads(report.read_text(encoding="utf-8"))

    assert exit_code == 2
    assert payload["status"] == "failed"
    assert "Secret-like material" in payload["error"]


def test_project_inventory_has_no_secret_material():
    items = rotation.read_inventory(PROJECT_ROOT / "data" / "secret_rotation_inventory.tsv")
    results = [
        rotation.evaluate_item(item, rotation.parse_date("2026-06-14"))
        for item in items
    ]
    summary = rotation.summarize(results)

    assert len(items) >= 10
    assert summary["overdue_required"] == 0
    assert summary["status"] == "ok"
