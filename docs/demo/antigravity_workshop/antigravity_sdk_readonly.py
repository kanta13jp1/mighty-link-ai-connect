#!/usr/bin/env python3
"""Run the Antigravity SDK as a read-only visual demo."""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import os
from pathlib import Path
import sys


WORKSPACE_FILES = ("index.html", "styles.css", "app.js", "SITE_BRIEF.md")
PROMPT_PATH = Path(__file__).with_name("PROMPT_11_SDK_READONLY.txt")


def preflight(workspace: Path) -> tuple[str, list[str]]:
    prompt = PROMPT_PATH.read_text(encoding="utf-8").strip()
    missing = [name for name in WORKSPACE_FILES if not (workspace / name).is_file()]
    return prompt, missing


async def run_agent(workspace: Path, prompt: str) -> None:
    from google.antigravity import Agent, LocalAgentConfig
    from google.antigravity.types import BuiltinTools, CapabilitiesConfig

    config = LocalAgentConfig(
        system_instructions=(
            "You are a read-only demo auditor. Stay inside the current workspace. "
            "Never create, edit, or delete files. Never run shell commands, access the "
            "network, or perform git writes. Do not reveal secrets or environment values."
        ),
        capabilities=CapabilitiesConfig(enabled_tools=BuiltinTools.read_only()),
    )

    print("SURFACE: ANTIGRAVITY SDK")
    print(f"WORKSPACE: {workspace}")
    print("MODE: READ ONLY")
    async with Agent(config) as agent:
        response = await agent.chat(prompt)
        async for token in response:
            print(token, end="", flush=True)
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    prompt, missing = preflight(workspace)
    if missing:
        print(f"STOP: required demo files are missing: {', '.join(missing)}")
        return 2

    sdk_installed = importlib.util.find_spec("google.antigravity") is not None
    if args.dry_run:
        print("SURFACE: ANTIGRAVITY SDK")
        print(f"WORKSPACE: {workspace}")
        print("MODE: READ ONLY")
        print(f"SDK_INSTALLED: {'YES' if sdk_installed else 'NO'}")
        print("PREFLIGHT: PASS")
        print("PROMPT_BEGIN")
        print(prompt)
        print("PROMPT_END")
        return 0

    if not sdk_installed:
        print("STOP: google-antigravity is not installed in this Python environment.")
        return 3
    if not os.environ.get("GEMINI_API_KEY"):
        print("STOP: GEMINI_API_KEY is not configured. Use the verified dry-run screen.")
        return 4

    asyncio.run(run_agent(workspace, prompt))
    return 0


if __name__ == "__main__":
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
