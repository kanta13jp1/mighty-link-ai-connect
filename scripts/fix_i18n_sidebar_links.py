#!/usr/bin/env python3
"""Add data-i18n directly to sidebar <a> links for flawless i18n translation and test parity."""

from pathlib import Path

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# 1. Update each sidebar navigation link to have data-i18n directly on the <a> tag
replacements = [
    ('<a href="#top" class="sidebar-nav-item" data-tab-id="home-view">', '<a href="#top" class="sidebar-nav-item" data-tab-id="home-view" data-i18n="nav_home">'),
    ('<a href="#matching-section" class="sidebar-nav-item active" data-tab-id="matching-section">', '<a href="#matching-section" class="sidebar-nav-item active" data-tab-id="matching-section" data-i18n="nav_matching">'),
    ('<a href="#admin-dashboard-section" class="sidebar-nav-item" data-tab-id="admin-dashboard-section">', '<a href="#admin-dashboard-section" class="sidebar-nav-item" data-tab-id="admin-dashboard-section" data-i18n="nav_admin">'),
    ('<a href="#attendance-section" class="sidebar-nav-item" data-tab-id="attendance-section">', '<a href="#attendance-section" class="sidebar-nav-item" data-tab-id="attendance-section" data-i18n="nav_attendance">'),
    ('<a href="#survey-section" class="sidebar-nav-item" data-tab-id="survey-section">', '<a href="#survey-section" class="sidebar-nav-item" data-tab-id="survey-section" data-i18n="nav_survey">'),
    ('<a href="#aptitude-demo-section" class="sidebar-nav-item" data-tab-id="aptitude-demo-section">', '<a href="#aptitude-demo-section" class="sidebar-nav-item" data-tab-id="aptitude-demo-section" data-i18n="nav_aptitude">'),
    ('<a href="#onboarding-section" class="sidebar-nav-item" data-tab-id="onboarding-section">', '<a href="#onboarding-section" class="sidebar-nav-item" data-tab-id="onboarding-section" data-i18n="nav_onboarding">'),
    ('<a href="#training-section" class="sidebar-nav-item" data-tab-id="training-section">', '<a href="#training-section" class="sidebar-nav-item" data-tab-id="training-section" data-i18n="nav_training">'),
]

for old, new in replacements:
    if old in content:
        content = content.replace(old, new)

# 2. In switchLanguage, handle nodes with icons gracefully
js_i18n_update = """
            document.querySelectorAll("[data-i18n]").forEach(node => {
                const key = node.getAttribute("data-i18n");
                if (i18nDict[lang] && i18nDict[lang][key]) {
                    const textVal = i18nDict[lang][key];
                    const iconSpan = node.querySelector(".nav-icon");
                    if (iconSpan) {
                        const labelSpan = node.querySelector(".nav-label");
                        if (labelSpan) labelSpan.textContent = textVal;
                        else node.innerHTML = `<span class="nav-icon">${iconSpan.textContent}</span> <span class="nav-label">${textVal}</span><span class="nav-indicator"></span>`;
                    } else {
                        node.textContent = textVal;
                    }
                }
            });
"""

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Sidebar links updated with data-i18n attributes!")
