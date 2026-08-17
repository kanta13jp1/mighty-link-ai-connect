#!/usr/bin/env python3
"""Find exact line of JS syntax error in index.html using Node.js."""

import subprocess
from pathlib import Path
import re

content = Path("index.html").read_text(encoding="utf-8")

# Extract all <script> contents (ignoring type="module" or external src)
scripts = re.findall(r'<script(?![^>]*src=)[^>]*>([\s\S]*?)</script>', content)

for idx, script in enumerate(scripts):
    temp_file = Path(f"temp_script_{idx}.js")
    temp_file.write_text(script, encoding="utf-8")
    res = subprocess.run(["node", "--check", str(temp_file)], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[-] Syntax Error in script block {idx}:")
        print(res.stderr)
    else:
        print(f"[+] Script block {idx} is valid JS!")
    if temp_file.exists():
        temp_file.unlink()
