#!/usr/bin/env python3
"""Restore saved language preference on page load."""

from pathlib import Path

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# In DOMContentLoaded, restore language preference
restore_code = """            // Restore saved language preference
            try {
                const savedLang = localStorage.getItem("msb_language_preference");
                if (savedLang && ['ja', 'en', 'zh', 'ko'].includes(savedLang)) {
                    switchLanguage(savedLang);
                }
            } catch (e) {}"""

content = content.replace(
    '// Initialize theme immediately to prevent flashing',
    restore_code + '\n\n            // Initialize theme immediately to prevent flashing'
)

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Language persistence on page load restored!")
