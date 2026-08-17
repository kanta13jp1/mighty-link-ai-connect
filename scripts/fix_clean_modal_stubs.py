#!/usr/bin/env python3
"""Remove extra closing braces after openTrainingModal and closeTrainingModal."""

from pathlib import Path

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

broken = """        function openTrainingModal(event) { if (event) event.preventDefault(); switchAppTab("training-section", true); }
        }

        function closeTrainingModal() {}
        }"""

clean = """        function openTrainingModal(event) { if (event) event.preventDefault(); switchAppTab("training-section", true); }

        function closeTrainingModal() {}"""

if broken in content:
    content = content.replace(broken, clean)
    print("[+] Fixed LF")
elif broken.replace("\n", "\r\n") in content:
    content = content.replace(broken.replace("\n", "\r\n"), clean.replace("\n", "\r\n"))
    print("[+] Fixed CRLF")
else:
    print("[-] Exact match failed, trying regex")
    import re
    content = re.sub(
        r'function openTrainingModal[^\n]*\n\s*\}\s*\n\s*function closeTrainingModal[^\n]*\n\s*\}',
        clean,
        content
    )

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Extra closing braces removed!")
