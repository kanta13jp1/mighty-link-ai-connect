#!/usr/bin/env python3
"""Fail closed when the repository's retired GitHub Pages site is enabled."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any


DEFAULT_API_URL = "https://api.github.com"


class PagesDecommissionError(RuntimeError):
    """Raised when the Pages retirement state cannot be proven."""


def github_get(url: str, token: str) -> tuple[int, dict[str, Any]]:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "mighty-link-pages-decommission-guard/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        return exc.code, {}


def verify_pages_decommissioned(
    repository: str,
    *,
    token: str,
    api_url: str = DEFAULT_API_URL,
    requester: Callable[[str, str], tuple[int, dict[str, Any]]] = github_get,
) -> dict[str, Any]:
    repository = repository.strip().strip("/")
    if repository.count("/") != 1:
        raise PagesDecommissionError("repository must use the OWNER/REPO format")
    if not token:
        raise PagesDecommissionError("GITHUB_TOKEN is required")

    repository_url = f"{api_url.rstrip('/')}/repos/{repository}"
    repository_status, _ = requester(repository_url, token)
    if repository_status != 200:
        raise PagesDecommissionError(
            f"repository access check returned HTTP {repository_status}; "
            "a Pages 404 would be ambiguous"
        )

    pages_status, pages_data = requester(f"{repository_url}/pages", token)
    if pages_status == 404:
        return {
            "repository": repository,
            "repository_status": repository_status,
            "pages_status": pages_status,
            "decommissioned": True,
        }
    if pages_status == 200:
        build_type = str(pages_data.get("build_type") or "unknown")
        raise PagesDecommissionError(
            f"GitHub Pages is still enabled (build_type={build_type})"
        )
    raise PagesDecommissionError(
        f"GitHub Pages state check returned unexpected HTTP {pages_status}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify that the repository GitHub Pages site remains deleted."
    )
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY", ""),
        help="GitHub repository in OWNER/REPO format.",
    )
    parser.add_argument(
        "--api-url",
        default=os.environ.get("GITHUB_API_URL", DEFAULT_API_URL),
    )
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    try:
        result = verify_pages_decommissioned(
            args.repository,
            token=token,
            api_url=args.api_url,
        )
    except PagesDecommissionError as exc:
        print(f"[-] GitHub Pages decommission guard failed: {exc}")
        return 1

    print(
        "[+] GitHub Pages remains decommissioned: "
        f"repository={result['repository']}, pages_status={result['pages_status']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
