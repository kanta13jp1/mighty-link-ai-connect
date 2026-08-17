import re
import pathlib

p = pathlib.Path(r'c:\Users\kanta\GitHub\mighty-link-ai-connect\.codex\tmp\canva-template-redesign-20260816\mighty_skill_bridge_canva_official_template_2026.html')
txt = p.read_text(encoding='utf-8')
matches = re.findall(r'<section class="slide[^"]*"[^>]*data-label="([^"]*)"', txt)
print(f"Total slides: {len(matches)}")
for idx, label in enumerate(matches):
    print(f"{idx+1:02d}: {label}")
