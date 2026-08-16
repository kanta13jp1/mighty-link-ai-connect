#!/usr/bin/env python3
"""Implement World-Class UI/UX Level 100 Solutions for All Reported Issues.

1. Convert 'Training Guide' from Modal to Dedicated App Tab View (#training-section)
2. Completely remove duplicate 'Menu' column from Footer
3. Build Rich HTML Markdown Viewer for docs/DEVELOPMENT_KNOWLEDGE_FLOW.html
4. Fix Mermaid.js CDN and robust rendering in exports/sequence-diagrams/index.html
5. Fix 'Home Back' links to navigate smoothly within the same tab
"""

from pathlib import Path
import re

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# 1. Remove duplicate 'メニュー' column in footer
footer_menu_pattern = r'<div class="footer-column">\s*<h3>メニュー</h3>[\s\S]*?</div>'
content = re.sub(footer_menu_pattern, '', content)

# 2. Convert Training Guide link in sidebar from onclick="openTrainingModal(event)" to normal data-tab-id="training-section"
content = content.replace(
    '<a href="#training-modal" class="sidebar-nav-item" onclick="openTrainingModal(event)">',
    '<a href="#training-section" class="sidebar-nav-item" data-tab-id="training-section">'
)
content = content.replace(
    '<a href="#training-modal" onclick="openTrainingModal(event)" data-i18n="nav_training">研修ガイド</a>',
    '<a href="#training-section" data-tab-id="training-section" data-i18n="nav_training">研修ガイド</a>'
)

# 3. Create #training-section App Tab View right after #onboarding-section
training_section_html = """
        <!-- ==========================================================================
             Training Guide Tab View (T919 - Dedicated Seamless Full-Page App Tab)
             ========================================================================== -->
        <section id="training-section" class="app-tab-view internal-section" aria-label="社内役割別研修・オンボーディングガイド">
            <div class="step-kicker" data-i18n="nav_training">研修ガイド</div>
            <div class="comparison-container">
                <div class="comparison-controls">
                    <div>
                        <h2 data-i18n="training_modal_title">社内役割別研修・オンボーディングガイド</h2>
                        <span class="control-label" data-i18n="training_modal_subtitle">業務役割に応じたカリキュラムを選択し、機能解説・受講ポイント・操作手順を確認できます</span>
                    </div>
                </div>

                <div class="auth-modal-tabs" style="grid-template-columns: repeat(3, 1fr); margin-bottom: 20px; border-radius: 12px; background: rgba(0,0,0,0.3); padding: 4px;">
                    <button class="auth-tab-btn active" id="tab-course-tab-1" onclick="switchTrainingTab('course1')">① 全社員基礎</button>
                    <button class="auth-tab-btn" id="tab-course-tab-2" onclick="switchTrainingTab('course2')">② 営業・HR専門</button>
                    <button class="auth-tab-btn" id="tab-course-tab-3" onclick="switchTrainingTab('course3')">③ 管理者管理</button>
                </div>

                <!-- Course 1 Panel -->
                <div id="training-tab-course-1" class="training-course-content-panel">
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--line); border-radius: 14px; padding: 24px; margin-bottom: 20px;">
                        <h3 style="margin: 0 0 10px 0; color: var(--green); font-size: 1.15rem;">コース①: 全社員基礎研修（オンボーディング・勤怠・アンケート）</h3>
                        <p style="font-size: 0.9rem; color: var(--muted); margin-bottom: 16px; line-height: 1.6;">
                            管理者から発行されたアカウントで初期セットアップ（アクティベーション）を完了し、適性アンケートおよび勤怠打刻・CSV解析を正しく利用する手順を学びます。
                        </p>
                        <div style="display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px;">
                            <button type="button" onclick="switchAppTab('onboarding-section', true)" class="sample-btn" style="padding: 10px 16px; font-size: 13px;">⚙️ 初期セットアップへ移動</button>
                            <button type="button" onclick="switchAppTab('survey-section', true)" class="sample-btn" style="padding: 10px 16px; font-size: 13px;">📝 適性アンケートへ移動</button>
                            <button type="button" onclick="switchAppTab('attendance-section', true)" class="sample-btn" style="padding: 10px 16px; font-size: 13px;">⏱️ 勤怠管理へ移動</button>
                        </div>
                        <div style="font-size: 0.85rem; background: rgba(186,255,102,0.08); border: 1px solid rgba(186,255,102,0.2); padding: 12px 16px; border-radius: 8px; color: var(--green);">
                            📖 詳細マニュアル: <a href="docs/training/FOUNDATION_TRAINING_HANDBOOK.html" style="color: var(--green); text-decoration: underline; font-weight: bold;">全社員基礎研修ハンドブック (FOUNDATION_TRAINING_HANDBOOK.html)</a>
                        </div>
                    </div>
                </div>

                <!-- Course 2 Panel -->
                <div id="training-tab-course-2" class="training-course-content-panel" style="display: none;">
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--line); border-radius: 14px; padding: 24px; margin-bottom: 20px;">
                        <h3 style="margin: 0 0 10px 0; color: var(--blue); font-size: 1.15rem;">コース②: 営業・HR専門研修（AIフィット分析・メールマッチング・提案生成）</h3>
                        <p style="font-size: 0.9rem; color: var(--muted); margin-bottom: 16px; line-height: 1.6;">
                            Skill / Culture / Growth / Performing の4軸AI診断評価、BP営業メールの案件/人材双方向マッチング、および個人情報保護・人間による最終レビュー原則を修得します。
                        </p>
                        <div style="display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px;">
                            <button type="button" onclick="switchAppTab('matching-section', true)" class="sample-btn" style="padding: 10px 16px; font-size: 13px;">🤝 営業メールマッチングへ移動</button>
                            <button type="button" onclick="switchAppTab('aptitude-demo-section', true)" class="sample-btn" style="padding: 10px 16px; font-size: 13px;">📈 自己診断デモへ移動</button>
                        </div>
                        <div style="font-size: 0.85rem; background: rgba(0,210,255,0.08); border: 1px solid rgba(0,210,255,0.2); padding: 12px 16px; border-radius: 8px; color: var(--blue);">
                            📖 詳細マニュアル: <a href="docs/training/SALES_HR_TRAINING_HANDBOOK.html" style="color: var(--blue); text-decoration: underline; font-weight: bold;">営業・HR専門研修ハンドブック (SALES_HR_TRAINING_HANDBOOK.html)</a>
                        </div>
                    </div>
                </div>

                <!-- Course 3 Panel -->
                <div id="training-tab-course-3" class="training-course-content-panel" style="display: none;">
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--line); border-radius: 14px; padding: 24px; margin-bottom: 20px;">
                        <h3 style="margin: 0 0 10px 0; color: #ffd166; font-size: 1.15rem;">コース③: 管理者管理研修（統合ダッシュボード・仮名化監査・セキュリティ）</h3>
                        <p style="font-size: 0.9rem; color: var(--muted); margin-bottom: 16px; line-height: 1.6;">
                            統合管理者ダッシュボードでの全体監視、仮名化識別子（onb-digest）による監査ログ点検、Break-glass緊急対応および個人情報開示請求SLAの運用手順を修得します。
                        </p>
                        <div style="display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px;">
                            <button type="button" onclick="switchAppTab('admin-dashboard-section', true)" class="sample-btn" style="padding: 10px 16px; font-size: 13px;">🛡️ 管理者ダッシュボードへ移動</button>
                            <a href="admin" class="sample-btn" style="padding: 10px 16px; font-size: 13px; text-decoration: none;">⚙️ Admin (DB直通) を開く</a>
                        </div>
                        <div style="font-size: 0.85rem; background: rgba(255,209,102,0.08); border: 1px solid rgba(255,209,102,0.2); padding: 12px 16px; border-radius: 8px; color: #ffd166;">
                            📖 詳細マニュアル: <a href="docs/training/ADMIN_MANAGEMENT_TRAINING_HANDBOOK.html" style="color: #ffd166; text-decoration: underline; font-weight: bold;">管理者管理研修ハンドブック (ADMIN_MANAGEMENT_TRAINING_HANDBOOK.html)</a>
                        </div>
                    </div>
                </div>
            </div>
        </section>
"""

if '<section id="training-section"' not in content:
    content = content.replace(
        '</section>\n\n        <!-- ==========================================================================\n             従業員適性・状況アンケート',
        '</section>\n' + training_section_html + '\n        <!-- ==========================================================================\n             従業員適性・状況アンケート'
    )

# 4. Update Footer Links to open in same window and point to HTML versions
content = content.replace(
    '<a href="docs/DEVELOPMENT_KNOWLEDGE_FLOW.md" target="_blank" rel="noopener">Mighty Knowledge Flow</a>',
    '<a href="docs/DEVELOPMENT_KNOWLEDGE_FLOW.html">Mighty Knowledge Flow</a>'
)
content = content.replace(
    '<a href="exports/sequence-diagrams/index.html" target="_blank" rel="noopener">Mighty Architecture (シーケンス図)</a>',
    '<a href="exports/sequence-diagrams/index.html">Mighty Architecture (シーケンス図)</a>'
)

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Training section added as dedicated tab and footer links updated!")
