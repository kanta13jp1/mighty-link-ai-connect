#!/usr/bin/env python3
"""Send commands or wireframe SVGs directly into Figma canvas via the Bridge Server."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

from network_security import require_loopback_http_url

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENDPOINT = "http://localhost:9099/push"


def send_svg_file(svg_path: Path, name: str = "MightyLink_Live_Wireframe") -> bool:
    if not svg_path.exists():
        print(f"[-] SVG file not found: {svg_path}")
        return False

    svg_text = svg_path.read_text(encoding="utf-8")
    payload = {
        "action": "create_svg_node",
        "name": name,
        "svg": svg_text
    }
    return send_payload(payload)


def send_payload(payload: dict) -> bool:
    endpoint = require_loopback_http_url(DEFAULT_ENDPOINT)
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310 -- endpoint is restricted to loopback HTTP.
            data = json.loads(resp.read().decode())
            print(f"[SUCCESS] Command sent to Figma: {data}")
            return True
    except urllib.error.HTTPError as e:
        print(f"[-] Bridge HTTP Error ({e.code}): {e.read().decode()}")
        return False
    except urllib.error.URLError as e:
        print(f"[-] Could not connect to Bridge Server on {DEFAULT_ENDPOINT}. Is scripts/figma_bridge_server.py running? ({e})")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Send commands directly into Figma canvas.")
    parser.add_argument("--svg", help="Path to SVG file to render on Figma canvas")
    parser.add_argument("--notify", help="Show toast notification in Figma")
    parser.add_argument("--color", help="Update selected layers fill color (hex, e.g. #baff66)")
    args = parser.parse_args()

    if args.svg:
        path = Path(args.svg)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        success = send_svg_file(path, name=path.stem)
        return 0 if success else 1

    if args.notify:
        success = send_payload({"action": "notify", "message": args.notify})
        return 0 if success else 1

    if args.color:
        success = send_payload({"action": "update_selection_color", "hex": args.color})
        return 0 if success else 1

    print("[*] No action specified. Usage: python scripts/send_to_figma.py --svg path/to/file.svg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
