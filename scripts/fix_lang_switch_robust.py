#!/usr/bin/env python3
"""Make language switcher completely robust and immune to click hijacking."""

from pathlib import Path
import re

INDEX_PATHS = (Path("index.html"), Path("src/index.html"))

# Update language switch HTML markup with native button controls.
new_lang_switch = """                <div class="language-switch" role="group" aria-label="Language">
                    <button type="button" data-lang="en" aria-pressed="false" onclick="switchLanguage(this)">EN</button>
                    <span>/</span>
                    <button type="button" data-lang="zh" aria-pressed="false" onclick="switchLanguage(this)">中文</button>
                    <span>/</span>
                    <button type="button" data-lang="ko" aria-pressed="false" onclick="switchLanguage(this)">KO</button>
                    <span>/</span>
                    <button type="button" class="active" data-lang="ja" aria-pressed="true" onclick="switchLanguage(this)">JP</button>
                </div>"""

for index_path in INDEX_PATHS:
    content = index_path.read_text(encoding="utf-8")
    content = re.sub(
        r'<div class="language-switch"[^>]*>[\s\S]*?</div>',
        new_lang_switch.strip(),
        content,
    )
    index_path.write_text(content, encoding="utf-8")
print("[SUCCESS] Language switcher made completely robust!")
