from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP = ROOT / "docs" / "demo" / "antigravity_workshop"


def read(name: str) -> str:
    return (WORKSHOP / name).read_text(encoding="utf-8")


def test_test_spec_prompt_precedes_site_implementation_and_requires_red() -> None:
    prompt = read("PROMPT_03_TEST_SPEC.txt")

    assert "TEST_SPEC.md" in prompt
    assert "tests/test_site_contract.py" in prompt
    assert "index.html、styles.css、app.js、画像、設定を作成・変更しません" in prompt
    assert "1件以上FAILするRED" in prompt
    assert "すべてPASSした場合は想定外として停止" in prompt


def test_build_and_skill_prompts_cannot_weaken_tests() -> None:
    build = read("PROMPT_03_BUILD.txt")
    apply_skill = read("PROMPT_04_APPLY_SKILL.txt")

    assert "T01-T05がPASS" in build
    assert "T06-T08がFAIL" in build
    assert "テストは変更せず" in build
    assert "T01-T08がすべてPASS" in apply_skill
    assert "テストを削除、skip、弱体化してPASSさせない" in apply_skill


def test_run_of_show_places_test_spec_before_build() -> None:
    readme = read("README.md")
    test_spec_position = readme.index("Antigravity 2.0でテスト仕様作成")
    build_position = readme.index("Antigravity 2.0で初版作成")

    assert test_spec_position < build_position
    assert "RED -> 部分PASS -> GREEN" in readme


def test_backup_output_contract_suite_is_green() -> None:
    output = WORKSHOP / "output"
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=output,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "Ran 11 tests" in completed.stderr
