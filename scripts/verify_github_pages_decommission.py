#!/usr/bin/env python3
"""Fail closed when the repository's retired GitHub Pages site is enabled."""

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import sys
from collections.abc import Callable
from typing import Any


DEFAULT_API_URL = "https://api.github.com"
REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9._-]+")


class PagesDecommissionError(RuntimeError):
    """Raised when the Pages retirement state cannot be proven."""


def validate_repository(repository: str) -> str:
    if (
        not REPOSITORY_PATTERN.fullmatch(repository)
        or repository.split("/")[-1] in {".", ".."}
    ):
        raise PagesDecommissionError("repository must use the OWNER/REPO format")
    return repository


def github_request_path(url: str) -> str:
    """Accept only the two GitHub.com endpoints needed by this guard."""
    prefix = f"{DEFAULT_API_URL}/repos/"
    if not url.startswith(prefix):
        raise PagesDecommissionError("GitHub API URL must use the canonical HTTPS origin")
    repository = url[len(prefix):]
    suffix = "/pages" if repository.count("/") == 2 and repository.endswith("/pages") else ""
    if suffix:
        repository = repository[:-len(suffix)]
    return f"/repos/{validate_repository(repository)}{suffix}"


def github_get(url: str, token: str) -> tuple[int, dict[str, Any]]:
    path = github_request_path(url)
    if not token:
        raise PagesDecommissionError("GITHUB_TOKEN is required")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "mighty-link-pages-decommission-guard/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        # HTTPSConnection verifies TLS by default and does not follow redirects.
        connection = http.client.HTTPSConnection("api.github.com", timeout=30)
        try:
            connection.request("GET", path, headers=headers)
            response = connection.getresponse()
            if response.status != 200:
                return response.status, {}
            body = response.read().decode("utf-8")
            payload = json.loads(body) if body else {}
            if not isinstance(payload, dict):
                raise ValueError("unexpected JSON response type")
            return response.status, payload
        finally:
            connection.close()
    except (OSError, http.client.HTTPException, ValueError):
        raise PagesDecommissionError(
            "GitHub API request failed or returned an invalid response"
        ) from None


def verify_pages_decommissioned(
    repository: str,
    *,
    token: str,
    api_url: str = DEFAULT_API_URL,
    requester: Callable[[str, str], tuple[int, dict[str, Any]]] = github_get,
) -> dict[str, Any]:
    repository = validate_repository(repository)
    if api_url not in {DEFAULT_API_URL, f"{DEFAULT_API_URL}/"}:
        raise PagesDecommissionError("GitHub API URL must use the canonical HTTPS origin")
    if not token:
        raise PagesDecommissionError("GITHUB_TOKEN is required")

    repository_url = f"{api_url.rstrip('/')}/repos/{repository}"
    repository_status, _ = requester(repository_url, token)
    if repository_status != 200:
        raise PagesDecommissionError(
            f"repository access check returned HTTP {repository_status}; "
            "a Pages 404 would be ambiguous"
        )

    pages_status, _ = requester(f"{repository_url}/pages", token)
    if pages_status == 404:
        return {
            "repository": repository,
            "repository_status": repository_status,
            "pages_status": pages_status,
            "decommissioned": True,
        }
    if pages_status == 200:
        raise PagesDecommissionError("GitHub Pages is still enabled")
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
