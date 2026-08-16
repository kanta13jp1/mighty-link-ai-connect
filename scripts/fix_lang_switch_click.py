#!/usr/bin/env python3
"""Ensure language switcher links execute switchLanguage cleanly without hash jump interference."""

from pathlib import Path
import re

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# 1. Update language switcher links
old_lang_switch = """                <div class="language-switch" aria-label="Language">
                    <a href="#top" data-lang="en" onclick="switchLanguage(this)">EN</a>
                    <span>/</span>
                    <a href="#top" data-lang="zh" onclick="switchLanguage(this)">中文</a>
                    <span>/</span>
                    <a href="#top" data-lang="ko" onclick="switchLanguage(this)">KO</a>
                    <span>/</span>
                    <a href="#top" class="active" data-lang="ja" onclick="switchLanguage(this)">JP</a>
                </div>"""

new_lang_switch = """                <div class="language-switch" aria-label="Language">
                    <a href="#top" data-lang="en" onclick="switchLanguage(this); return false;">EN</a>
                    <span>/</span>
                    <a href="#top" data-lang="zh" onclick="switchLanguage(this); return false;">中文</a>
                    <span>/</span>
                    <a href="#top" data-lang="ko" onclick="switchLanguage(this); return false;">KO</a>
                    <span>/</span>
                    <a href="#top" class="active" data-lang="ja" onclick="switchLanguage(this); return false;">JP</a>
                </div>"""

content = content.replace(old_lang_switch, new_lang_switch)
content = content.replace(old_lang_switch.replace("\n", "\r\n"), new_lang_switch.replace("\n", "\r\n"))

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Language switcher links updated!")
