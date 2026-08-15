#!/usr/bin/env python3
"""Completely fix navigation redundancy, sidebar clipping, and tab rendering opacity issues."""

from pathlib import Path
import re

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# 1. CSS Fix:
# - Ensure .app-tab-view.tab-active and all its children are instantly 100% visible (overriding fade-in-on-scroll opacity: 0)
# - Fix sidebar top clipping (top: 84px, proper padding, crisp borders)
# - Clean up topbar (no duplicate nav links)
css_overrides = """
        /* ======================================================== */
        /* WORLD-CLASS UI/UX: STRICT VISIBILITY & ZERO CLIPPING     */
        /* ======================================================== */
        /* 1. Eliminate Duplicate Topbar Nav */
        .topbar .nav-links {
            display: none !important;
        }

        /* 2. Fix Sidebar Top Clipping */
        .global-app-sidebar {
            position: sticky !important;
            top: 84px !important;
            height: calc(100vh - 104px) !important;
            overflow-y: auto !important;
            margin-top: 0 !important;
            background: rgba(9, 13, 22, 0.95) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            box-shadow: 0 12px 36px rgba(0, 0, 0, 0.5) !important;
        }

        /* 3. Ensure Active Tab & its Contents are NEVER Hidden by Scroll Observers */
        .app-tab-view.tab-active {
            display: block !important;
            opacity: 1 !important;
            visibility: visible !important;
            transform: none !important;
        }

        .app-tab-view.tab-active .fade-in-on-scroll,
        .app-tab-view.tab-active .internal-section {
            opacity: 1 !important;
            visibility: visible !important;
            transform: none !important;
        }
"""

if "/* WORLD-CLASS UI/UX: STRICT VISIBILITY & ZERO CLIPPING" not in content:
    content = content.replace("</style>", css_overrides + "\n    </style>")

# 2. In switchAppTab, forcibly trigger is-visible on all sub-elements
js_switch_fix = """
            // Ensure all child elements inside active tab are fully visible
            const activeView = document.getElementById(targetId === 'home-view' ? 'home-view' : targetId);
            if (activeView) {
                activeView.querySelectorAll('.fade-in-on-scroll').forEach(el => {
                    el.classList.add('is-visible');
                    el.style.opacity = '1';
                    el.style.transform = 'none';
                });
            }
"""

content = content.replace(
    "currentActiveTabId = targetId;",
    "currentActiveTabId = targetId;\n" + js_switch_fix
)

# 3. Clean up Footer Navigation Redundancy
old_footer_menu = """                    <div class="footer-col">
                        <h4>メニュー</h4>
                        <div class="footer-links">
                            <a href="#top">ホーム</a>
                            <a href="#onboarding-section">初期セットアップ</a>
                            <a href="#survey-section">適性アンケート</a>
                            <a href="#aptitude-demo-section">自己診断デモ</a>
                            <a href="#attendance-section">勤怠管理</a>
                            <a href="#matching-section">営業メールマッチング</a>
                            <a href="#admin-dashboard-section">管理者ダッシュボード</a>
                        </div>
                    </div>"""

new_footer_menu = """                    <div class="footer-col">
                        <h4>製品・機能</h4>
                        <div class="footer-links">
                            <a href="#matching-section" onclick="switchAppTab('matching-section', true)">営業AIマッチング</a>
                            <a href="#attendance-section" onclick="switchAppTab('attendance-section', true)">勤怠・36協定解析</a>
                            <a href="#survey-section" onclick="switchAppTab('survey-section', true)">適性・状況診断</a>
                            <a href="#admin-dashboard-section" onclick="switchAppTab('admin-dashboard-section', true)">統合管理コンソール</a>
                        </div>
                    </div>"""

content = content.replace(old_footer_menu, new_footer_menu)
content = content.replace(old_footer_menu.replace("\n", "\r\n"), new_footer_menu.replace("\n", "\r\n"))

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Applied strict visibility, sidebar top alignment, and removed nav redundancies!")
