#!/usr/bin/env python3
"""Restore #primary-navigation accessibility and i18n attributes while integrating global sidebar."""

from pathlib import Path

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# 1. Restore #primary-navigation in topbar without style="display:none;"
topbar_nav_restored = """        <nav class="nav-links" id="primary-navigation" aria-label="Primary navigation">
            <a href="#top" class="active" data-i18n="nav_home">ホーム</a>
            <a href="#onboarding-section" data-i18n="nav_onboarding">初期セットアップ</a>
            <a href="#training-modal" onclick="openTrainingModal(event)" data-i18n="nav_training">研修ガイド</a>
            <a href="#survey-section" data-i18n="nav_survey">適性アンケート</a>
            <a href="#aptitude-demo-section" data-i18n="nav_aptitude">自己診断デモ</a>
            <a href="#attendance-section" data-i18n="nav_attendance">勤怠管理</a>
            <a href="#matching-section" data-i18n="nav_matching">営業メールマッチング</a>
            <a href="#admin-dashboard-section" data-i18n="nav_admin">管理者ダッシュボード</a>
        </nav>"""

# Replace any hidden #primary-navigation
content = content.replace(
    '        <!-- Primary Navigation handled by Unified Global SaaS Sidebar -->\n        <nav class="nav-links" id="primary-navigation" aria-label="Primary navigation" style="display:none;">\n            <a href="#top" data-i18n="nav_home">ホーム</a>\n            <a href="#onboarding-section" data-i18n="nav_onboarding">初期セットアップ</a>\n            <a href="#survey-section" data-i18n="nav_survey">適性アンケート</a>\n            <a href="#aptitude-demo-section" data-i18n="nav_aptitude">自己診断デモ</a>\n            <a href="#attendance-section" data-i18n="nav_attendance">勤怠管理</a>\n            <a href="#matching-section" data-i18n="nav_matching">営業メールマッチング</a>\n            <a href="#admin-dashboard-section" data-i18n="nav_admin">管理者ダッシュボード</a>\n        </nav>',
    topbar_nav_restored
)

# 2. Add data-i18n tags to Global Sidebar links as well
content = content.replace('<span>ホーム (AIシミュレーター)</span>', '<span data-i18n="nav_home">ホーム</span>')
content = content.replace('<span>初期セットアップ</span>', '<span data-i18n="nav_onboarding">初期セットアップ</span>')
content = content.replace('<span>研修・ガイド</span>', '<span data-i18n="nav_training">研修ガイド</span>')
content = content.replace('<span>適性・状況アンケート</span>', '<span data-i18n="nav_survey">適性アンケート</span>')
content = content.replace('<span>自己診断デモ</span>', '<span data-i18n="nav_aptitude">自己診断デモ</span>')
content = content.replace('<span>勤務表・残業解析</span>', '<span data-i18n="nav_attendance">勤怠管理</span>')
content = content.replace('<span>営業メールAIマッチング</span>', '<span data-i18n="nav_matching">営業メールマッチング</span>')
content = content.replace('<span>管理者統合ダッシュボード</span>', '<span data-i18n="nav_admin">管理者ダッシュボード</span>')

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Primary navigation and i18n attributes successfully restored!")
