#!/usr/bin/env python3
"""Make language switcher completely robust and immune to click hijacking."""

from pathlib import Path
import re

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# 1. Update language switch HTML markup with direct javascript calls
old_lang_switch_patterns = [
    r'<div class="language-switch"[^>]*>[\s\S]*?</div>',
]

new_lang_switch = """                <div class="language-switch" aria-label="Language">
                    <a href="javascript:void(0)" data-lang="en" onclick="switchLanguage('en'); return false;">EN</a>
                    <span>/</span>
                    <a href="javascript:void(0)" data-lang="zh" onclick="switchLanguage('zh'); return false;">中文</a>
                    <span>/</span>
                    <a href="javascript:void(0)" data-lang="ko" onclick="switchLanguage('ko'); return false;">KO</a>
                    <span>/</span>
                    <a href="javascript:void(0)" class="active" data-lang="ja" onclick="switchLanguage('ja'); return false;">JP</a>
                </div>"""

content = re.sub(r'<div class="language-switch" aria-label="Language">[\s\S]*?</div>', new_lang_switch.strip(), content)

# 2. Also ensure switchLanguage attaches click event listeners via JavaScript
content = content.replace(
    'window.addEventListener(\'DOMContentLoaded\', () => {',
    """window.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('.language-switch a').forEach(a => {
                a.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const lang = a.getAttribute('data-lang');
                    if (lang) switchLanguage(lang);
                });
            });"""
)

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Language switcher made completely robust!")
