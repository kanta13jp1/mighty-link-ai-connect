#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Interactive NotebookLM login helper for the Workspace account.

The upstream `notebooklm login` command can fail on Windows when Google redirects
from accounts.google.com to the account chooser while Playwright is still waiting
for the original navigation. This helper uses the same NotebookLM storage paths
but saves the browser state immediately after the user confirms that the
NotebookLM home page is visible.
"""

from __future__ import annotations

import sys
from pathlib import Path

from notebooklm.paths import get_browser_profile_dir, get_storage_path
from playwright.sync_api import sync_playwright


NOTEBOOKLM_URL = "https://notebooklm.google.com/"
NOTEBOOKLM_HOST = "notebooklm.google.com"
EXPECTED_ACCOUNT = "k-umezawa@ml-mightylink.com"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    storage_path = Path(get_storage_path())
    browser_profile = Path(get_browser_profile_dir())
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    browser_profile.mkdir(parents=True, exist_ok=True)

    print("Starting NotebookLM login helper.")
    print(f"Browser profile: {browser_profile}")
    print(f"Storage path: {storage_path}")
    print()
    print(f"In the browser, select: {EXPECTED_ACCOUNT}")
    print("After the NotebookLM home page is visible, return here and press Enter.")
    print()

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(browser_profile),
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--password-store=basic",
            ],
            ignore_default_args=["--enable-automation"],
        )

        page = context.pages[0] if context.pages else context.new_page()
        page.goto(NOTEBOOKLM_URL, wait_until="domcontentloaded", timeout=60000)

        input("[Press Enter after the NotebookLM home page is visible] ")

        current_url = page.url
        if NOTEBOOKLM_HOST not in current_url:
            print(f"Warning: current URL is not NotebookLM: {current_url}")
            answer = input("Save the current authentication state anyway? [y/N] ").strip().lower()
            if answer not in {"y", "yes"}:
                context.close()
                print("Exited without saving authentication state.")
                sys.exit(1)

        context.storage_state(path=str(storage_path))
        try:
            storage_path.chmod(0o600)
        except OSError:
            pass
        context.close()

    print()
    print(f"NotebookLM authentication saved: {storage_path}")
    print("Next, run: python scripts/sync_docs_to_notebooklm.py")


if __name__ == "__main__":
    main()
