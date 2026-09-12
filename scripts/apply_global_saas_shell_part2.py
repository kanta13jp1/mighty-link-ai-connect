#!/usr/bin/env python3
"""Wrap main area with global sidebar and clean up admin section inner sidebar."""

from pathlib import Path
import re

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

global_sidebar_html = """
    <div class="app-shell-container">
        <!-- ======================================================== -->
        <!-- UNIFIED GLOBAL SAAS SIDEBAR (Figma Untitled UI Parity)   -->
        <!-- ======================================================== -->
        <aside class="global-app-sidebar" id="global-sidebar" aria-label="ワークスペースナビゲーション" data-i18n-aria-label="workspace_navigation_label">
            <div class="sidebar-brand">
                <div style="width: 36px; height: 36px; border-radius: 10px; background: #162a15; border: 1.2px solid #baff66; display: flex; align-items: center; justify-content: center; font-size: 16px;">🛡️</div>
                <div>
                    <div style="font-size: 13px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px;">MIGHTY LINK</div>
                    <div style="font-size: 10px; font-weight: 700; color: var(--green);">AI CONNECT PRO</div>
                </div>
            </div>

            <div style="font-size: 10px; font-weight: 800; color: var(--muted); letter-spacing: 1px; margin-bottom: 10px; padding-left: 8px;">WORKSPACE APPS</div>

            <nav class="sidebar-nav-list">
                <!-- 1. Home / Fit Simulator -->
                <a href="#top" class="sidebar-nav-item" data-tab-id="home-view">
                    <span style="font-size: 15px;">🏠</span>
                    <span>ホーム (AIシミュレーター)</span>
                    <span class="nav-indicator"></span>
                </a>

                <!-- 2. Sales Email Matching -->
                <a href="#matching-section" class="sidebar-nav-item active" data-tab-id="matching-section">
                    <span style="font-size: 15px;">🤝</span>
                    <span>営業メールAIマッチング</span>
                    <span class="nav-indicator"></span>
                </a>

                <!-- 3. Admin Dashboard -->
                <a href="#admin-dashboard-section" class="sidebar-nav-item" data-tab-id="admin-dashboard-section">
                    <span style="font-size: 15px;">🛡️</span>
                    <span>管理者統合ダッシュボード</span>
                    <span class="nav-indicator"></span>
                </a>

                <!-- 4. Timesheet / Attendance -->
                <a href="#attendance-section" class="sidebar-nav-item" data-tab-id="attendance-section">
                    <span style="font-size: 15px;">⏱️</span>
                    <span>勤務表・残業解析</span>
                    <span class="nav-indicator"></span>
                </a>

                <!-- 5. Survey / Assessment -->
                <a href="#survey-section" class="sidebar-nav-item" data-tab-id="survey-section">
                    <span style="font-size: 15px;">📊</span>
                    <span>適性・状況アンケート</span>
                    <span class="nav-indicator"></span>
                </a>

                <!-- 6. Aptitude Demo -->
                <a href="#aptitude-demo-section" class="sidebar-nav-item" data-tab-id="aptitude-demo-section">
                    <span style="font-size: 15px;">📈</span>
                    <span>自己診断デモ</span>
                    <span class="nav-indicator"></span>
                </a>

                <!-- 7. Onboarding / Setup -->
                <a href="#onboarding-section" class="sidebar-nav-item" data-tab-id="onboarding-section">
                    <span style="font-size: 15px;">⚙️</span>
                    <span>初期セットアップ</span>
                    <span class="nav-indicator"></span>
                </a>

                <!-- 8. Training Guide -->
                <a href="#training-modal" class="sidebar-nav-item" onclick="openTrainingModal(event)">
                    <span style="font-size: 15px;">📖</span>
                    <span>研修・ガイド</span>
                </a>
            </nav>

            <!-- Bottom User Profile Card -->
            <div style="margin-top: 28px; padding: 12px; border-radius: 12px; background: rgba(13, 20, 36, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); display: flex; align-items: center; gap: 10px;">
                <div style="width: 32px; height: 32px; border-radius: 50%; background: #162e12; border: 1.2px solid #baff66; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 800; color: #baff66;">佐</div>
                <div style="flex: 1; min-width: 0;">
                    <div style="font-size: 12px; font-weight: 700; color: #ffffff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">佐藤 賢太</div>
                    <div style="font-size: 10px; color: var(--green);">最高統括管理者</div>
                </div>
                <span style="width: 8px; height: 8px; border-radius: 50%; background: var(--green); box-shadow: 0 0 6px var(--green);"></span>
            </div>
        </aside>

        <!-- ======================================================== -->
        <!-- MAIN CONTENT VIEWPORT (Active Tab Display Area)          -->
        <!-- ======================================================== -->
        <div class="global-main-area">
"""

# Insert global sidebar right after <main id="top" tabindex="-1">
if '<main id="top" tabindex="-1">' in content:
    content = content.replace('<main id="top" tabindex="-1">', '<main id="top" tabindex="-1">\n' + global_sidebar_html)
    # Close global-main-area and app-shell-container before </main>
    content = content.replace('</main>', '        </div> <!-- end .global-main-area -->\n    </div> <!-- end .app-shell-container -->\n</main>')
    print("[1] Global sidebar and main wrapper inserted!")

# Remove inner sidebar from #admin-dashboard-section
admin_sidebar_pattern = r'<!-- Enterprise SaaS 2-Column Container \(Figma Layout Parity\) -->[\s\S]*?<aside class="admin-sidebar-nav"[\s\S]*?</aside>[\s\S]*?<div class="admin-main-content"[^>]*>'
replacement_admin = '<!-- Admin Main Content -->'
content = re.sub(admin_sidebar_pattern, replacement_admin, content)
print("[2] Admin section inner sidebar removed!")

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Global SaaS App Shell fully applied!")
