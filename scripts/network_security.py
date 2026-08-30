"""Network destination validation shared by security-sensitive operator scripts."""

from __future__ import annotations

import ipaddress
from collections.abc import Collection
from urllib.parse import urlsplit


def _validated_parts(url: str):
    normalized = (url or "").strip()
    if not normalized or any(ord(char) < 32 for char in normalized):
        raise ValueError("URL must be non-empty and contain no control characters")
    parts = urlsplit(normalized)
    if not parts.hostname or parts.username is not None or parts.password is not None:
        raise ValueError("URL must include a host and must not embed credentials")
    return normalized, parts


def require_https_url(url: str, *, allowed_hosts: Collection[str] | None = None) -> str:
    """Return a validated HTTPS URL, optionally restricted to exact hosts."""
    normalized, parts = _validated_parts(url)
    if parts.scheme.lower() != "https":
        raise ValueError("Only HTTPS URLs are allowed")
    if allowed_hosts is not None:
        allowed = {host.lower() for host in allowed_hosts}
        if parts.hostname.lower() not in allowed:
            raise ValueError(f"URL host is not allowed: {parts.hostname}")
    return normalized


def _is_loopback(hostname: str) -> bool:
    if hostname.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


def require_https_or_loopback_url(url: str) -> str:
    """Allow HTTPS, or plain HTTP only for an explicit loopback destination."""
    normalized, parts = _validated_parts(url)
    scheme = parts.scheme.lower()
    if scheme == "https":
        return normalized
    if scheme == "http" and _is_loopback(parts.hostname):
        return normalized
    raise ValueError("URL must use HTTPS; HTTP is allowed only for loopback hosts")


def require_loopback_http_url(url: str) -> str:
    """Return a validated local bridge URL that cannot address a remote host."""
    normalized, parts = _validated_parts(url)
    if parts.scheme.lower() != "http" or not _is_loopback(parts.hostname):
        raise ValueError("Local bridge URL must use HTTP on a loopback host")
    return normalized