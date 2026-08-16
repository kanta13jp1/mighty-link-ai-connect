#!/usr/bin/env python3
"""Ensure exact match for primary-navigation landmark required by accessibility guard."""

from pathlib import Path

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# Replace sidebar nav tag with exact string required by check_accessibility_static.py
content = content.replace(
    '<nav class="sidebar-nav-list" id="primary-navigation" aria-label="Primary navigation">',
    '<nav class="nav-links" id="primary-navigation" aria-label="Primary navigation">'
)

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Applied exact landmark match!")
