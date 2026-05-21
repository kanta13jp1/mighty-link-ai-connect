#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Guard the public GitHub Pages demo from accidental README fallback or UI removal.

The CEO-facing URL is served from the repository root, so root index.html must
remain present even though FastAPI also serves src/index.html locally.
"""

import argparse
import sys
import time
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT_INDEX = PROJECT_ROOT / "index.html"

REQUIRED_MARKERS = [
    "Mighty Skill-Bridge",
    "エンジニア＆案件 AIフィットシミュレーター",
    "bridge-btn",
    "runAnalysis()",
    "sampleEngineer",
    "radarChart",
]

README_FALLBACK_MARKERS = [
    "## Quick Start",
    "docs/SETUP_GUIDE.md",
]


def fail(message: str) -> None:
    print(f"[-] {message}")
    sys.exit(1)


def verify_html(content: str, label: str) -> None:
    missing = [marker for marker in REQUIRED_MARKERS if marker not in content]
    if missing:
        fail(f"{label} is missing public demo marker(s): {', '.join(missing)}")

    fallback_hits = [marker for marker in README_FALLBACK_MARKERS if marker in content]
    if fallback_hits:
        fail(f"{label} looks like README/Jekyll fallback content: {', '.join(fallback_hits)}")

    print(f"[+] {label} contains the required public demo UI markers.")


def fetch_url(url: str) -> str:
    separator = "&" if "?" in url else "?"
    cache_busted_url = f"{url}{separator}codex_guard={int(time.time())}"
    request = urllib.request.Request(
        cache_busted_url,
        headers={"User-Agent": "mighty-link-public-demo-guard/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        status = getattr(response, "status", 200)
        if status != 200:
            fail(f"Public URL returned HTTP {status}: {cache_busted_url}")
        return response.read().decode("utf-8", errors="replace")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify public demo UI safety markers.")
    parser.add_argument(
        "--url",
        help="Optional public URL to verify after GitHub Pages deployment.",
    )
    args = parser.parse_args()

    if not ROOT_INDEX.exists():
        fail("root index.html is missing. GitHub Pages will fall back to README.")

    verify_html(ROOT_INDEX.read_text(encoding="utf-8"), "root index.html")

    if args.url:
        verify_html(fetch_url(args.url), args.url)

    print("[+] Public demo guard passed.")


if __name__ == "__main__":
    main()
