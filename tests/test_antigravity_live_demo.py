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


def _failed_hypotheses(project_root: Path) -> set[str]:
    result = collect_demo_kit_status(project_root)
    return {check["name"] for check in result["checks"] if not check["passed"]}


def test_committed_antigravity_demo_kit_is_fail_closed_and_ready():
    result = collect_demo_kit_status(PROJECT_ROOT)

    assert result["passed"] is True
    assert all(check["passed"] for check in result["checks"])

    hypotheses = [check for check in result["checks"] if check["name"].startswith("H")]
    assert len(hypotheses) == 10
    assert {check["name"].split("_", 1)[0] for check in hypotheses} == {
        f"H{number}" for number in range(1, 11)
    }


def test_demo_kit_rejects_missing_synthetic_marker_and_wrong_repository(tmp_path: Path):
    workshop = _copy_workshop(tmp_path)
    brief = workshop / "input" / "SITE_BRIEF.md"
    publish = workshop / "PROMPT_06_PUBLISH.txt"
    brief.write_text(brief.read_text(encoding="utf-8").replace("SYNTHETIC_DATA_ONLY", ""), encoding="utf-8")
    publish.write_text(
        publish.read_text(encoding="utf-8").replace(
            "kanta13jp1/mighty-link-antigravity-live-demo", "kanta13jp1/mighty-link-ai-connect"
        ),
        encoding="utf-8",
    )

    assert "H9_publish_safety" in _failed_hypotheses(tmp_path)


def test_demo_kit_rejects_global_or_unverified_skill_install(tmp_path: Path):
    workshop = _copy_workshop(tmp_path)
    prompt = workshop / "PROMPT_02_INSTALL_SKILL.txt"
    text = prompt.read_text(encoding="utf-8")
    prompt.write_text(
        text.replace("--agent antigravity --copy -y", "-g -y").replace(
            ".agents/skills/frontend-design/SKILL.md", "Skill名"
        ),
        encoding="utf-8",
    )

    assert "H4_project_scoped_install" in _failed_hypotheses(tmp_path)


def test_demo_kit_rejects_kiro_feature_names_assigned_to_antigravity(tmp_path: Path):
    workshop = _copy_workshop(tmp_path)
    concepts = workshop / "DEMO_CONCEPTS.md"
    text = concepts.read_text(encoding="utf-8")
    concepts.write_text(
        text.replace("Kiroの正式機能名です", "Antigravityの正式機能名です", 1).replace(
            "Kiroの正式機能です", "Antigravityの正式機能です", 1
        ),
        encoding="utf-8",
    )

    assert "H7_product_feature_accuracy" in _failed_hypotheses(tmp_path)


def test_demo_kit_rejects_mcp_write_and_skill_directory_publish(tmp_path: Path):
    workshop = _copy_workshop(tmp_path)
    mcp = workshop / "PROMPT_05_MCP_CHECK.txt"
    publish = workshop / "PROMPT_06_PUBLISH.txt"
    mcp.write_text(mcp.read_text(encoding="utf-8").replace("読み取り専用", "読み書き可能"), encoding="utf-8")
    publish.write_text(
        publish.read_text(encoding="utf-8").replace(
            "`.agents/skills/`は公開対象へaddしないでください。", "`.agents/skills/`もaddしてください。"
        ),
        encoding="utf-8",
    )

    failed = _failed_hypotheses(tmp_path)
    assert "H8_mcp_read_only" in failed
    assert "H9_publish_safety" in failed


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

    assert "H10_offline_accessible_recovery" in _failed_hypotheses(tmp_path)
