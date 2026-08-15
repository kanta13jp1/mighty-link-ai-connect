#!/usr/bin/env python3
"""Refactor index.html into a unified global SaaS sidebar shell layout."""

from pathlib import Path

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# 1. Add CSS for Global App Shell
css_insertion = """
        /* ======================================================== */
        /* UNIFIED GLOBAL SAAS APP SHELL LAYOUT                     */
        /* ======================================================== */
        .app-shell-container {
            display: grid;
            grid-template-columns: 260px minmax(0, 1fr);
            gap: 24px;
            max-width: 1680px;
            margin: 0 auto;
            padding: 16px 20px 60px;
            align-items: start;
        }

        .global-app-sidebar {
            background: rgba(9, 13, 22, 0.92);
            border: 1px solid rgba(24, 35, 56, 0.9);
            border-radius: 16px;
            padding: 20px 16px;
            backdrop-filter: blur(16px);
            position: sticky;
            top: 76px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            z-index: 40;
        }

        .global-app-sidebar .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .global-app-sidebar .sidebar-nav-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .global-app-sidebar .sidebar-nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            border-radius: 8px;
            color: var(--muted);
            font-size: 13px;
            font-weight: 600;
            text-decoration: none;
            border: 1px solid transparent;
            transition: all 0.2s ease;
            cursor: pointer;
        }

        .global-app-sidebar .sidebar-nav-item:hover {
            background: rgba(255, 255, 255, 0.05);
            color: #ffffff;
            transform: translateX(3px);
        }

        .global-app-sidebar .sidebar-nav-item.active {
            background: rgba(186, 255, 102, 0.12);
            border: 1px solid rgba(186, 255, 102, 0.4);
            color: #ffffff;
            font-weight: 700;
        }

        .global-app-sidebar .sidebar-nav-item.active .nav-indicator {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--green);
            margin-left: auto;
            box-shadow: 0 0 6px var(--green);
        }

        .global-main-area {
            min-width: 0;
            width: 100%;
        }

        @media (max-width: 1024px) {
            .app-shell-container {
                grid-template-columns: 1fr;
                padding: 12px 14px;
            }
            .global-app-sidebar {
                position: static;
                margin-bottom: 16px;
            }
        }
"""

if ".app-shell-container" not in content:
    content = content.replace("</style>", css_insertion + "\n    </style>")

# 2. Update Topbar: Remove duplicate nav-links text strip
old_nav_links = """        <nav class="nav-links" id="primary-navigation" aria-label="Primary navigation">
            <a href="#top" data-i18n="nav_home">ホーム</a>
            <a href="#onboarding-section" data-i18n="nav_onboarding">初期セットアップ</a>
            <a href="#training-modal" onclick="openTrainingModal(event)" data-i18n="nav_training">研修ガイド</a>
            <a href="#survey-section" data-i18n="nav_survey">適性アンケート</a>
            <a href="#aptitude-demo-section" data-i18n="nav_aptitude">自己診断デモ</a>
            <a href="#attendance-section" data-i18n="nav_attendance">勤怠管理</a>
            <a href="#matching-section" data-i18n="nav_matching">営業メールマッチング</a>
            <a href="#admin-dashboard-section" data-i18n="nav_admin">管理者ダッシュボード</a>
        </nav>"""

new_topbar_nav = """        <!-- Primary Navigation handled by Unified Global SaaS Sidebar -->
        <nav class="nav-links" id="primary-navigation" aria-label="Primary navigation" style="display:none;">
            <a href="#top" data-i18n="nav_home">ホーム</a>
            <a href="#onboarding-section" data-i18n="nav_onboarding">初期セットアップ</a>
            <a href="#survey-section" data-i18n="nav_survey">適性アンケート</a>
            <a href="#aptitude-demo-section" data-i18n="nav_aptitude">自己診断デモ</a>
            <a href="#attendance-section" data-i18n="nav_attendance">勤怠管理</a>
            <a href="#matching-section" data-i18n="nav_matching">営業メールマッチング</a>
            <a href="#admin-dashboard-section" data-i18n="nav_admin">管理者ダッシュボード</a>
        </nav>"""

if old_nav_links in content:
    content = content.replace(old_nav_links, new_topbar_nav)
else:
    # Try CRLF
    content = content.replace(old_nav_links.replace("\n", "\r\n"), new_topbar_nav.replace("\n", "\r\n"))

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] App Shell CSS and Topbar nav updated!")
