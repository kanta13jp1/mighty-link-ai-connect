#!/usr/bin/env python3
from pathlib import Path
import re

content = Path("index.html").read_text(encoding="utf-8")
scripts = re.findall(r'<script(?![^>]*src=)[^>]*>([\s\S]*?)</script>', content)

script_1 = scripts[1]
lines = script_1.split("\n")
for i in range(max(0, 840), min(len(lines), 865)):
    print(f"{i+1}: {lines[i]}")
