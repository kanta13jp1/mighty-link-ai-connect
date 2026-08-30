"""Regression contracts for dependencies required by targeted pytest workflows."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = (
    ROOT / ".github" / "workflows" / "db-migration-validate.yml",
    ROOT / ".github" / "workflows" / "local-dev-stack-validate.yml",
)


def test_targeted_pytest_workflows_install_shared_conftest_dependencies():
    for workflow in WORKFLOWS:
        text = workflow.read_text(encoding="utf-8")
        assert "python -m pip install httpx pytest" in text, workflow