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
    publish = workshop / "PROMPT_05_PUBLISH.txt"
    brief.write_text(brief.read_text(encoding="utf-8").replace("SYNTHETIC_DATA_ONLY", ""), encoding="utf-8")
    publish.write_text(
        publish.read_text(encoding="utf-8").replace(
            "kanta13jp1/mighty-link-antigravity-live-demo", "kanta13jp1/mighty-link-ai-connect"
        ),
        encoding="utf-8",
    )

    assert "H9_publish_safety" in _failed_hypotheses(tmp_path)


def test_demo_kit_rejects_skill_install_and_weak_quality_check(tmp_path: Path):
    workshop = _copy_workshop(tmp_path)
    prompt = workshop / "PROMPT_01_FIND_SKILLS.txt"
    text = prompt.read_text(encoding="utf-8")
    prompt.write_text(
        text.replace("公開元とGitHub stars", "名前")
        .replace("セキュリティ監査の有無", "説明")
        .replace("まだSkillのインストール", "すぐSkillのインストール"),
        encoding="utf-8",
    )

    assert "H3_skill_discovery_quality" in _failed_hypotheses(tmp_path)


def test_demo_kit_rejects_mcp_write_and_power_as_official_feature(tmp_path: Path):
    workshop = _copy_workshop(tmp_path)
    mcp = workshop / "PROMPT_04_MCP_CHECK.txt"
    concepts = workshop / "DEMO_CONCEPTS.md"
    mcp.write_text(mcp.read_text(encoding="utf-8").replace("読み取り専用", "読み書き可能"), encoding="utf-8")
    concepts.write_text(
        concepts.read_text(encoding="utf-8")
        .replace("公式機能名ではなく", "公式機能名であり")
        .replace("独立設定があるとは説明しない", "独立設定として説明する"),
        encoding="utf-8",
    )

    failed = _failed_hypotheses(tmp_path)
    assert "H7_mcp_read_only" in failed
    assert "H8_power_clarity" in failed


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
