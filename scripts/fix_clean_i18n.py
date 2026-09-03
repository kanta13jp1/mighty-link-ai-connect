#!/usr/bin/env python3
"""Clean up i18n structure in index.html for 100% test reliability."""

from pathlib import Path
import re

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# 1. Clean up sidebar links: data-i18n only on the label span
clean_sidebar_nav = """            <nav class="nav-links" id="primary-navigation" aria-label="Primary navigation">
                <!-- 1. Home / Fit Simulator -->
                <a href="#top" class="sidebar-nav-item" data-tab-id="home-view">
                    <span style="font-size: 15px;">🏠</span>
                    <span data-i18n="nav_home">ホーム</span>
                    <span class="nav-indicator"></span>
                </a>

                <!-- 2. Sales Email Matching -->
                <a href="#matching-section" class="sidebar-nav-item active" data-tab-id="matching-section">
                    <span style="font-size: 15px;">🤝</span>
                    <span data-i18n="nav_matching">営業メールマッチング</span>
                    <span class="nav-indicator"></span>
                </a>

                <!-- 3. Admin Dashboard -->
                <a href="#admin-dashboard-section" class="sidebar-nav-item" data-tab-id="admin-dashboard-section">
                    <span style="font-size: 15px;">🛡️</span>
                    <span data-i18n="nav_admin">管理者ダッシュボード</span>
                    <span class="nav-indicator"></span>
                </a>

                <!-- 4. Timesheet / Attendance -->
                <a href="#attendance-section" class="sidebar-nav-item" data-tab-id="attendance-section">
                    <span style="font-size: 15px;">⏱️</span>
                    <span data-i18n="nav_attendance">勤怠管理</span>
                    <span class="nav-indicator"></span>
                </a>

                <!-- 5. Survey / Assessment -->
                <a href="#survey-section" class="sidebar-nav-item" data-tab-id="survey-section">
                    <span style="font-size: 15px;">📊</span>
                    <span data-i18n="nav_survey">適性アンケート</span>
                    <span class="nav-indicator"></span>
                </a>

                <!-- 6. Aptitude Demo -->
                <a href="#aptitude-demo-section" class="sidebar-nav-item" data-tab-id="aptitude-demo-section">
                    <span style="font-size: 15px;">📈</span>
                    <span data-i18n="nav_aptitude">自己診断デモ</span>
                    <span class="nav-indicator"></span>
                </a>

                <!-- 7. Onboarding / Setup -->
                <a href="#onboarding-section" class="sidebar-nav-item" data-tab-id="onboarding-section">
                    <span style="font-size: 15px;">⚙️</span>
                    <span data-i18n="nav_onboarding">初期セットアップ</span>
                    <span class="nav-indicator"></span>
                </a>

                <!-- 8. Training Guide -->
                <a href="#training-section" class="sidebar-nav-item" data-tab-id="training-section">
                    <span style="font-size: 15px;">📖</span>
                    <span data-i18n="nav_training">研修ガイド</span>
                    <span class="nav-indicator"></span>
                </a>
            </nav>"""

pattern = r'<nav class="nav-links" id="primary-navigation" aria-label="Primary navigation">[\s\S]*?</nav>'
content = re.sub(pattern, clean_sidebar_nav, content)

# 2. Clean switchLanguage function
clean_switch_lang_js = """
        function switchLanguage(el) {
            const lang = typeof el === "string" ? el : el.getAttribute("data-lang");
            if (!lang) return;

            document.querySelectorAll(".language-switch button").forEach(button => {
                const selected = button.getAttribute("data-lang") === lang;
                button.classList.toggle("active", selected);
                button.setAttribute("aria-pressed", String(selected));
            });

            document.documentElement.lang = lang === "ja" ? "ja" : lang;
            try { localStorage.setItem("msb_language_preference", lang); } catch (e) {}

            document.querySelectorAll("[data-i18n]").forEach(node => {
                const key = node.getAttribute("data-i18n");
                if (i18nDict[lang] && i18nDict[lang][key]) {
                    node.textContent = i18nDict[lang][key];
                }
            });

            document.querySelectorAll("[data-i18n-html]").forEach(node => {
                const key = node.getAttribute("data-i18n-html");
                if (i18nDict[lang] && i18nDict[lang][key]) {
                    node.innerHTML = i18nDict[lang][key];
                }
            });

            document.querySelectorAll("[data-i18n-placeholder]").forEach(node => {
                const key = node.getAttribute("data-i18n-placeholder");
                if (i18nDict[lang] && i18nDict[lang][key]) {
                    node.setAttribute("placeholder", i18nDict[lang][key]);
                }
            });
        }
"""

pattern_lang = r'function switchLanguage\(el\) \{[\s\S]*?\}\s*\}\s*\}'
content = re.sub(pattern_lang, clean_switch_lang_js.strip(), content)

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Clean i18n applied!")
