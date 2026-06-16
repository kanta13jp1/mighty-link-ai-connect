import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import verify_gemini_cli_migration as audit


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_clean_project_allows_historical_docs(tmp_path):
    write(tmp_path / "scripts" / "use_antigravity.ps1", "antigravity-ide.cmd chat \"hello\"\n")
    write(
        tmp_path / "docs" / "migration.md",
        "Gemini CLI から Antigravity CLI へ移行した履歴。Gemini Code Assist 個人向け停止も記録。\n",
    )
    write(tmp_path / "AGENTS.md", "Use Antigravity CLI for Google agent workflows.\n")

    report = audit.build_report(tmp_path, "2026-06-17")

    assert report["status"] == "ok"
    assert report["summary"]["active_blockers"] == 0
    assert report["summary"]["historical_references"] >= 2
    assert all(finding["state"] == "historical_reference" for finding in report["reference_findings"])


def test_active_firebase_gemini_cli_extension_is_critical(tmp_path):
    write(
        tmp_path / "scripts" / "setup_google_agent.ps1",
        "gemini extensions install https://github.com/firebase/agent-skills/\n",
    )

    report = audit.build_report(tmp_path, "2026-06-17")

    assert report["status"] == "critical"
    assert report["summary"]["active_blockers"] >= 1
    assert any(
        finding["pattern"] == "gemini_cli_firebase_extension"
        for finding in report["active_findings"]
    )


def test_active_code_assist_extension_recommendation_is_critical(tmp_path):
    write(
        tmp_path / ".vscode" / "extensions.json",
        json.dumps({"recommendations": ["google.geminicodeassist"]}),
    )

    report = audit.build_report(tmp_path, "2026-06-17")

    assert report["status"] == "critical"
    assert any(
        finding["pattern"] == "gemini_code_assist_extension"
        for finding in report["active_findings"]
    )


def test_report_files_are_written(tmp_path):
    write(tmp_path / "scripts" / "use_antigravity.ps1", "antigravity-ide.cmd chat \"hello\"\n")
    report = audit.build_report(tmp_path, "2026-06-17")
    output_dir = tmp_path / "exports"

    json_path = audit.write_json(report, output_dir)
    markdown_path = audit.write_markdown(report, output_dir)

    assert json_path.exists()
    assert markdown_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")
    assert payload["status"] == "ok"
    assert "Gemini CLI / Code Assist" in markdown
