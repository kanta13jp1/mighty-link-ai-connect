#!/usr/bin/env python3
"""Sync document.documentElement.lang immediately in head script."""

from pathlib import Path

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

head_sync_script = """    <!-- Synchronous Language & Security Guard -->
    <script>
        (function() {
            try {
                var savedLang = localStorage.getItem('msb_language_preference');
                if (savedLang && ['ja', 'en', 'zh', 'ko'].indexOf(savedLang) !== -1) {
                    document.documentElement.lang = savedLang;
                }
            } catch(e) {}
        })();
    </script>"""

content = content.replace(
    '<!-- Synchronous Security Lockout Script (Pre-render Auth Guard) -->',
    head_sync_script + '\n    <!-- Synchronous Security Lockout Script (Pre-render Auth Guard) -->'
)

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Head language sync script added!")
