import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_gemini_model_policy as audit


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_policy(root: Path) -> Path:
    policy = {
        "policy_id": "test-policy",
        "checked_at": "2026-07-01",
        "official_docs": {
            "models_url": "https://ai.google.dev/gemini-api/docs/models",
            "context_caching_url": "https://ai.google.dev/gemini-api/docs/caching",
            "models_last_updated_utc": "2026-06-30",
        },
        "production_default": "gemini-3.5-flash",
        "stable_production_models": ["gemini-3.5-flash", "gemini-2.5-flash"],
        "evaluation_only_models": ["gemini-3.1-pro"],
        "blocked_model_patterns": ["^gemini-.*-latest$", "^gemini-2\\.0-.*"],
        "active_scan_roots": ["src", "scripts"],
        "current_truth_paths": ["docs/current.md"],
        "current_truth_context_markers": ["現行", "既定", "current", "default"],
    }
    path = root / "data" / "gemini_model_policy.json"
    write(path, json.dumps(policy, ensure_ascii=False))
    return path


def test_policy_passes_for_stable_default(tmp_path):
    policy_path = write_policy(tmp_path)
    write(
        tmp_path / "src" / "app.py",
        'GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")\n',
    )
    write(tmp_path / "src" / "parser.py", 'model = "gemini-3.5-flash"\n')
    write(tmp_path / "docs" / "current.md", "現行既定モデルは `gemini-3.5-flash` です。\n")

    report = audit.build_report(tmp_path, policy_path, "2026-07-01")

    assert report["status"] == "ok"
    assert report["summary"]["production_default"] == "gemini-3.5-flash"
    assert report["summary"]["blockers"] == 0


def test_latest_alias_is_blocked_in_runtime(tmp_path):
    policy_path = write_policy(tmp_path)
    write(
        tmp_path / "src" / "app.py",
        'GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")\n',
    )
    write(tmp_path / "scripts" / "worker.py", 'model = "gemini-flash-latest"\n')
    write(tmp_path / "docs" / "current.md", "現行既定モデルは `gemini-3.5-flash` です。\n")

    report = audit.build_report(tmp_path, policy_path, "2026-07-01")

    assert report["status"] == "blocked"
    assert any("blocked_by_pattern" in finding["reason"] for finding in report["blockers"])


def test_scan_exclude_paths_skips_test_fixture_files(tmp_path):
    # A file that intentionally references blocked/shutdown models as fixtures
    # (e.g. the T780 migration harness) must not be flagged when excluded.
    policy = json.loads((write_policy(tmp_path)).read_text(encoding="utf-8"))
    policy["scan_exclude_paths"] = ["scripts/migration_harness.py"]
    policy_path = tmp_path / "data" / "gemini_model_policy.json"
    write(policy_path, json.dumps(policy, ensure_ascii=False))

    write(
        tmp_path / "src" / "app.py",
        'GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")\n',
    )
    write(tmp_path / "scripts" / "migration_harness.py", 'SHUTDOWN = ["gemini-2.0-flash"]\n')
    write(tmp_path / "docs" / "current.md", "現行既定モデルは `gemini-3.5-flash` です。\n")

    report = audit.build_report(tmp_path, policy_path, "2026-07-01")

    assert report["status"] == "ok"
    assert report["summary"]["blockers"] == 0

    # Without the exclusion the same file must be flagged as a blocker.
    policy.pop("scan_exclude_paths")
    write(policy_path, json.dumps(policy, ensure_ascii=False))
    report2 = audit.build_report(tmp_path, policy_path, "2026-07-01")
    assert report2["status"] == "blocked"


def test_current_truth_doc_cannot_mark_old_model_as_current(tmp_path):
    policy_path = write_policy(tmp_path)
    write(
        tmp_path / "src" / "app.py",
        'GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")\n',
    )
    write(tmp_path / "docs" / "current.md", "現行既定モデルは `gemini-2.5-flash` です。\n")

    report = audit.build_report(tmp_path, policy_path, "2026-07-01")

    assert report["status"] == "blocked"
    assert any("current_truth_model_mismatch" in finding["reason"] for finding in report["blockers"])


def test_report_files_are_written(tmp_path):
    policy_path = write_policy(tmp_path)
    write(
        tmp_path / "src" / "app.py",
        'GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")\n',
    )
    write(tmp_path / "docs" / "current.md", "現行既定モデルは `gemini-3.5-flash` です。\n")
    report = audit.build_report(tmp_path, policy_path, "2026-07-01")

    json_path = audit.write_json(report, tmp_path / "exports" / "audit.json")
    markdown_path = audit.write_markdown(report, tmp_path / "exports" / "audit.md")

    assert json_path.exists()
    assert markdown_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["status"] == "ok"
    assert "Gemini Model Policy Audit" in markdown_path.read_text(encoding="utf-8")
