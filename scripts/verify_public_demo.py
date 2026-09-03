#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Guard the production UI source from accidental README fallback or UI removal.

The compatibility entry point remains at the repository root while FastAPI
serves src/index.html in production. Both are protected by repository tests.
"""

import argparse
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT_INDEX = PROJECT_ROOT / "index.html"

REQUIRED_MARKERS = [
    "Mighty Skill-Bridge",
    "エンジニア＆案件 AIフィットシミュレーター",
    "bridge-btn",
    "runAnalysis()",
    "knowledge-flow-demo",
    "generateKnowledgeFlowArtifacts",
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
        fail(f"{label} is missing production UI marker(s): {', '.join(missing)}")

    fallback_hits = [marker for marker in README_FALLBACK_MARKERS if marker in content]
    if fallback_hits:
        fail(f"{label} looks like README/Jekyll fallback content: {', '.join(fallback_hits)}")

    print(f"[+] {label} contains the required public demo UI markers.")


def fetch_url(url: str) -> str:
    separator = "&" if "?" in url else "?"
    cache_busted_url = f"{url}{separator}codex_guard={int(time.time())}"
    
    try:
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")
    except Exception:
        pass

    auth = None
    hostname = (urlparse(url).hostname or "").lower()
    if hostname in {"mightylink-app.com", "www.mightylink-app.com", "127.0.0.1", "localhost"}:
        user = os.environ.get("BASIC_AUTH_USERNAME")
        password = os.environ.get("BASIC_AUTH_PASSWORD")
        if not user or not password:
            fail("BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD are required for protected URL verification.")
        auth = (user, password)

    response = requests.get(
        cache_busted_url,
        headers={"User-Agent": "mighty-link-public-demo-guard/1.0"},
        auth=auth,
        timeout=30,
    )
    if response.status_code != 200:
        fail(f"Public URL returned HTTP {response.status_code}: {cache_busted_url}")
    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify public demo UI safety markers.")
    parser.add_argument(
        "--url",
        help="Optional production URL to verify after Firebase deployment.",
    )
    args = parser.parse_args()

    if not ROOT_INDEX.exists():
        fail("root index.html is missing; the production UI source mirror is incomplete.")

    verify_html(ROOT_INDEX.read_text(encoding="utf-8"), "root index.html")

    if args.url:
        verify_html(fetch_url(args.url), args.url)

    print("[+] Production UI guard passed.")


if __name__ == "__main__":
    main()
