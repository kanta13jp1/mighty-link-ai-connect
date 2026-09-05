from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_codex_worktrees_are_ignored_and_not_tracked_as_gitlinks() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".codex-worktrees/" in gitignore.splitlines()

    result = subprocess.run(
        ["git", "ls-files", "--stage", ".codex-worktrees"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    tracked_gitlinks = [
        line for line in result.stdout.splitlines() if line.startswith("160000 ")
    ]
    assert tracked_gitlinks == []
