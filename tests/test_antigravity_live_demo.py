from __future__ import annotations

import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from run_antigravity_live_demo import collect_demo_kit_status


def _copy_workshop(tmp_path: Path) -> Path:
    source = PROJECT_ROOT / "docs" / "demo" / "antigravity_workshop"
    target = tmp_path / "docs" / "demo" / "antigravity_workshop"
    shutil.copytree(source, target)
    return target


def test_committed_antigravity_demo_kit_is_fail_closed_and_ready():
    result = collect_demo_kit_status(PROJECT_ROOT)

    assert result["passed"] is True
    assert all(check["passed"] for check in result["checks"])

    hypotheses = [check for check in result["checks"] if check["name"].startswith("H")]
    assert len(hypotheses) == 10
    assert {check["name"].split("_", 1)[0] for check in hypotheses} == {
        f"H{number}" for number in range(1, 11)
    }


def test_demo_kit_rejects_missing_synthetic_marker(tmp_path: Path):
    workshop = _copy_workshop(tmp_path)
    brief = workshop / "input" / "SITE_BRIEF.md"
    brief.write_text(brief.read_text(encoding="utf-8").replace("SYNTHETIC_DATA_ONLY", ""), encoding="utf-8")

    result = collect_demo_kit_status(tmp_path)
    failed = {check["name"] for check in result["checks"] if not check["passed"]}

    assert result["passed"] is False
    assert "H7_public_data_safety" in failed


def test_demo_kit_rejects_wrong_repository_and_missing_publish_approval(tmp_path: Path):
    workshop = _copy_workshop(tmp_path)
    prompt = workshop / "PROMPT_03_PUBLISH.txt"
    text = prompt.read_text(encoding="utf-8")
    prompt.write_text(
        text.replace("kanta13jp1/mighty-link-antigravity-live-demo", "kanta13jp1/mighty-link-ai-connect")
        .replace("正確に「公開して」と答えるまで", "確認を待たずに"),
        encoding="utf-8",
    )

    result = collect_demo_kit_status(tmp_path)
    failed = {check["name"] for check in result["checks"] if not check["passed"]}

    assert "H5_publish_isolation" in failed
    assert "H6_human_publish_gate" in failed


def test_demo_output_rejects_external_dependency_and_persistent_storage(tmp_path: Path):
    workshop = _copy_workshop(tmp_path)
    html = workshop / "output" / "index.html"
    javascript = workshop / "output" / "app.js"
    html.write_text(
        html.read_text(encoding="utf-8").replace(
            "</head>", '<script src="https://example.com/app.js"></script></head>'
        ),
        encoding="utf-8",
    )
    javascript.write_text(javascript.read_text(encoding="utf-8") + "\nlocalStorage.setItem('demo', '1');\n", encoding="utf-8")

    result = collect_demo_kit_status(tmp_path)
    failed = {check["name"] for check in result["checks"] if not check["passed"]}

    assert "H8_offline_fallback" in failed
