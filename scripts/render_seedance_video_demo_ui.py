#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Render the public/static and FastAPI demo HTML.

This script ensures that the root index.html and src/index.html remain in perfect sync.
"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT_INDEX = PROJECT_ROOT / "index.html"
SRC_INDEX = PROJECT_ROOT / "src" / "index.html"


def main() -> None:
    if not ROOT_INDEX.exists():
        print(f"[-] Error: {ROOT_INDEX} not found.")
        return
    
    # Read the master index.html
    html_content = ROOT_INDEX.read_text(encoding="utf-8")
    
    # Write to both locations to ensure exact alignment and clean line endings
    ROOT_INDEX.write_text(html_content, encoding="utf-8", newline="\n")
    SRC_INDEX.write_text(html_content, encoding="utf-8", newline="\n")
    
    print(f"[+] Successfully synchronized and rendered:")
    print(f"  - {ROOT_INDEX}")
    print(f"  - {SRC_INDEX}")


if __name__ == "__main__":
    main()
