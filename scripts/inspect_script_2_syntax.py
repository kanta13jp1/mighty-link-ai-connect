from pathlib import Path
import re

content = Path("index.html").read_text(encoding="utf-8")
scripts = re.findall(r'<script(?![^>]*src=)[^>]*>([\s\S]*?)</script>', content)

script_2 = scripts[2]
lines = script_2.split("\n")
print(f"Total lines in script 2: {len(lines)}")
for i in range(3750, min(len(lines), 3800)):
    print(f"{i+1}: {lines[i]}")
