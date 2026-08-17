#!/usr/bin/env python3
"""Surgically fix all syntax errors and broken references in index.html."""

from pathlib import Path
import re

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# 1. Fix line 9316 JS Syntax Error in switchTrainingTab
broken_switch_training = """        function switchTrainingTab(courseId) {
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
        } else {
                    if (btn) btn.classList.remove('active');
                    if (panel) { panel.style.display = 'none'; panel.classList.remove('active'); }
                }
            });
        }"""

clean_switch_training = """        function switchTrainingTab(courseId) {
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
        }"""

if broken_switch_training in content:
    content = content.replace(broken_switch_training, clean_switch_training)
    print("[1] JS Syntax Error in switchTrainingTab fixed!")
else:
    # Try CRLF
    content = content.replace(broken_switch_training.replace("\n", "\r\n"), clean_switch_training.replace("\n", "\r\n"))
    print("[1] JS Syntax Error in switchTrainingTab fixed (CRLF)!")

# 2. Fix Docs icon link in footer (do not open raw markdown in new tab)
content = content.replace(
    '<a href="docs/DEVELOPMENT_KNOWLEDGE_FLOW.md" target="_blank" rel="noopener" class="footer-social-icon" aria-label="Docs" title="Documentation">',
    '<a href="docs/DEVELOPMENT_KNOWLEDGE_FLOW.html" class="footer-social-icon" aria-label="Docs" title="Documentation">'
)

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] All syntax errors and docs icon fixed!")
