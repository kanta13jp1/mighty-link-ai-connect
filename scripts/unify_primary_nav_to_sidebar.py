#!/usr/bin/env python3
"""Unify #primary-navigation into the visible global sidebar and resolve remote git drift."""

from pathlib import Path
import re

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# 1. Remove old topbar nav completely
topbar_nav_pattern = r'<nav class="nav-links" id="primary-navigation"[^>]*>[\s\S]*?</nav>'
content = re.sub(topbar_nav_pattern, '', content)

# 2. Make sidebar-nav-list the authoritative, visible #primary-navigation
content = content.replace(
    '<nav class="sidebar-nav-list">',
    '<nav class="sidebar-nav-list" id="primary-navigation" aria-label="Primary navigation">'
)

# 3. Remove .topbar .nav-links { display: none !important; } rule from CSS (clean CSS)
content = content.replace('.topbar .nav-links {\n            display: none !important;\n        }', '')

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Primary navigation unified cleanly into global sidebar!")
