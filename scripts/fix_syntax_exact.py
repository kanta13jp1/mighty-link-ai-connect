#!/usr/bin/env python3
"""Remove extraneous closing bracket at end of switchLanguage in index.html."""

from pathlib import Path

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

broken_block = """            document.querySelectorAll("[data-i18n-placeholder]").forEach(node => {
                const key = node.getAttribute("data-i18n-placeholder");
                if (i18nDict[lang] && i18nDict[lang][key]) {
                    node.setAttribute("placeholder", i18nDict[lang][key]);
                }
            });
        }
        });"""

clean_block = """            document.querySelectorAll("[data-i18n-placeholder]").forEach(node => {
                const key = node.getAttribute("data-i18n-placeholder");
                if (i18nDict[lang] && i18nDict[lang][key]) {
                    node.setAttribute("placeholder", i18nDict[lang][key]);
                }
            });
        }"""

if broken_block in content:
    content = content.replace(broken_block, clean_block)
    print("[+] Fixed LF")
elif broken_block.replace("\n", "\r\n") in content:
    content = content.replace(broken_block.replace("\n", "\r\n"), clean_block.replace("\n", "\r\n"))
    print("[+] Fixed CRLF")
else:
    print("[-] Broken block not found directly, trying regex")
    import re
    content = re.sub(
        r'(\s*document\.querySelectorAll\("\[data-i18n-placeholder\]"\)[\s\S]*?\}\s*\}\s*\);)(\s*\}\s*\}\s*\);)',
        clean_block,
        content
    )

INDEX_PATH.write_text(content, encoding="utf-8")
