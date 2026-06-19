import csv
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import validate_release_versioning as release


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_valid_inputs(root: Path, *, version: str = "0.1.0-controlled-demo.1") -> dict[str, Path]:
    version_path = root / "VERSION"
    changelog_path = root / "CHANGELOG.md"
    runbook_path = root / "docs" / "RELEASE_VERSIONING_RUNBOOK.md"
    go_no_go_path = root / "exports" / "production_go_no_go_review.json"
    wbs_path = root / "data" / "WBS.tsv"

    write(version_path, version + "\n")
    write(
        changelog_path,
        f"""# Changelog

## [{version}] - 2026-06-19

- controlled_demo: GO
- public_paid_launch: NO_GO
""",
    )
    write(runbook_path, "# Release Runbook\n\nNo secrets here.\n")
    write(
        go_no_go_path,
        json.dumps(
            {
                "scopes": {
                    "controlled_demo": {"recommendation": "GO"},
                    "public_paid_launch": {"recommendation": "NO_GO"},
                }
            },
            ensure_ascii=False,
        ),
    )
    wbs_path.parent.mkdir(parents=True)
    with wbs_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["タスクID", "ステータス"])
        writer.writerow(["T806", "完了"])
    return {
        "version_path": version_path,
        "changelog_path": changelog_path,
        "runbook_path": runbook_path,
        "go_no_go_path": go_no_go_path,
        "wbs_path": wbs_path,
    }


def state_by_key(report: dict, key: str) -> str:
    return next(check["state"] for check in report["checks"] if check["key"] == key)


def test_controlled_demo_prerelease_is_valid(tmp_path):
    paths = write_valid_inputs(tmp_path)

    report = release.build_report(**paths, expected_version="0.1.0-controlled-demo.1")

    assert report["status"] == "ok"
    assert report["tag"] == "v0.1.0-controlled-demo.1"
    assert report["github_release_prerelease"] is True
    assert state_by_key(report, "go_no_go.boundary") == "ok"


def test_ga_release_is_critical_when_public_paid_launch_is_no_go(tmp_path):
    paths = write_valid_inputs(tmp_path, version="1.0.0")

    report = release.build_report(**paths, expected_version="1.0.0")

    assert report["status"] == "critical"
    assert state_by_key(report, "go_no_go.public_paid_launch") == "critical"


def test_secret_like_value_in_changelog_is_critical(tmp_path):
    paths = write_valid_inputs(tmp_path)
    paths["changelog_path"].write_text(
        "# Changelog\n\n## [0.1.0-controlled-demo.1] - 2026-06-19\n\n"
        "- controlled_demo: GO\n"
        "- public_paid_launch: NO_GO\n"
        "- token=secret-token-value\n",
        encoding="utf-8",
    )

    report = release.build_report(**paths)

    assert report["status"] == "critical"
    assert state_by_key(report, "release.secret_free") == "critical"


def test_write_report_outputs_json_and_markdown(tmp_path):
    paths = write_valid_inputs(tmp_path)
    report = release.build_report(**paths)
    json_path = tmp_path / "exports" / "release_versioning_review.json"
    md_path = tmp_path / "exports" / "release_versioning_review.md"

    release.write_report(report, json_path, md_path)

    assert json_path.exists()
    assert md_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")
    assert payload["status"] == "ok"
    assert "v0.1.0-controlled-demo.1" in markdown
