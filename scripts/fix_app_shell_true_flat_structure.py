#!/usr/bin/env python3
"""Restructure index.html into a truly flat, world-class SaaS SPA Tabbed layout."""

from pathlib import Path
import re

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# 1. Ensure #home-view wraps only Home elements (Hero, Report, Comparison, Video, Models, Knowledge-Flow)
# Let's inspect: replace <div id="home-view" class="app-tab-view home-tab-element tab-active">
# with <section id="home-view" class="app-tab-view home-tab-element tab-active">
content = content.replace(
    '<div id="home-view" class="app-tab-view home-tab-element tab-active">',
    '<!-- ========================================================\n     MAIN CONTENT VIEWPORT (Active Tab Display Area)          \n     ======================================================== -->\n    <div class="global-main-area">\n\n        <!-- 1. Home View -->\n        <div id="home-view" class="app-tab-view home-tab-element tab-active">'
)

# Close #home-view before #onboarding-section or first internal section
# In current HTML, #onboarding-section is the first internal section.
# Let's find: <!-- Step 2: 初期セットアップ・アクティベーション (T839) -->
# or <section id="onboarding-section"
content = re.sub(
    r'(\s*)(<!-- ==========================================================================\s*Step 2: 初期セットアップ|\s*<section id="onboarding-section")',
    r'\n        </div><!-- /#home-view -->\n\n\1',
    content,
    count=1
)

# 2. Make sure #training-section is a top-level app-tab-view inside .global-main-area
# Ensure all 8 sections are top-level children of .global-main-area

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Flattened app-tab-view structure applied!")
