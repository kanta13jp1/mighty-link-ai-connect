#!/usr/bin/env python3
"""Execute switchLanguage immediately upon DOMContentLoaded and body attach."""

from pathlib import Path

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# Ensure switchLanguage is called immediately at the top of script
top_call = """        // Apply saved language immediately
        (function() {
            try {
                const saved = localStorage.getItem("msb_language_preference");
                if (saved && ['ja', 'en', 'zh', 'ko'].includes(saved)) {
                    document.documentElement.lang = saved;
                    if (typeof switchLanguage === 'function') switchLanguage(saved);
                }
            } catch(e) {}
        })();"""

content = content.replace(
    'window.addEventListener(\'DOMContentLoaded\', () => {',
    'window.addEventListener(\'DOMContentLoaded\', () => {\n' + top_call
)

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Instant language restore applied!")
