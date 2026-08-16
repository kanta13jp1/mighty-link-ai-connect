#!/usr/bin/env python3
"""Sync training tab button and panel IDs between HTML markup and switchTrainingTab JS."""

from pathlib import Path
import re

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# Update switchTrainingTab JS to handle both IDs
updated_js = """
        function switchTrainingTab(courseId) {
            const courses = ['course1', 'course2', 'course3'];
            courses.forEach((c, idx) => {
                const num = idx + 1;
                const btn1 = document.getElementById('training-tab-' + num);
                const btn2 = document.getElementById('tab-course-tab-' + num);
                const panel1 = document.getElementById('training-course-' + num);
                const panel2 = document.getElementById('training-tab-course-' + num);

                const isTarget = (c === courseId);
                [btn1, btn2].forEach(btn => {
                    if (btn) {
                        if (isTarget) btn.classList.add('active');
                        else btn.classList.remove('active');
                    }
                });
                [panel1, panel2].forEach(panel => {
                    if (panel) {
                        if (isTarget) {
                            panel.style.display = 'block';
                            panel.classList.add('active');
                        } else {
                            panel.style.display = 'none';
                            panel.classList.remove('active');
                        }
                    }
                });
            });
        }
"""

pattern = r'function switchTrainingTab\(courseId\) \{[\s\S]*?\}\s*\}'
content = re.sub(pattern, updated_js.strip(), content)

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Training tab switcher synced!")
