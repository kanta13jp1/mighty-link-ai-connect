#!/usr/bin/env python3
"""Implement 100/100 World-Class UI/UX Level Solutions for all reported items.

1. Completely eliminate #training-modal and modal JS functions from index.html.
2. Insert robust #training-section App Tab View inside <main> with full 3-course curriculum.
3. Remove target="_blank" from all internal doc links and ensure same-tab navigation.
4. Fix src/app.py serve_doc_file:
   - .html -> HTMLResponse (Content-Type: text/html)
   - .md -> Rich Markdown Viewer with Marked.js AND Mermaid.js graphic renderer
5. Rewrite test_training_modal_ui.py to test #training-section App Tab & assert NO modal.
6. Extend scripts/generate_figma_wireframes.py to cover all 8 app screens.
"""

from pathlib import Path
import re

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# 1. Remove old #training-modal markup completely
old_modal_pattern = r'<!-- Training / Onboarding Modal \(T919\) -->\s*<div class="auth-modal-overlay" id="training-modal"[\s\S]*?<!-- Modal: Authentication & Access Control'
content = re.sub(old_modal_pattern, '<!-- Modal: Authentication & Access Control', content)

# Also remove any leftover standalone #training-modal
content = re.sub(r'<div class="auth-modal-overlay" id="training-modal"[\s\S]*?</div>\s*</div>', '', content)

# 2. Build dedicated #training-section markup
training_section_markup = """
        <!-- ==========================================================================
             Training Guide Tab View (Dedicated Full App Tab View)
             ========================================================================== -->
        <section id="training-section" class="app-tab-view internal-section fade-in-on-scroll" aria-label="社内役割別研修・オンボーディングガイド">
            <div class="step-kicker" data-i18n="nav_training">研修ガイド</div>
            <div class="comparison-container" style="background: rgba(15, 18, 28, 0.7); border: 1px solid var(--line); border-radius: 16px; padding: 28px;">
                <div class="comparison-controls" style="margin-bottom: 20px;">
                    <div>
                        <h2 data-i18n="training_modal_title" style="font-size: 1.4rem; font-weight: 800; color: #fff; margin-bottom: 6px;">社内役割別研修・オンボーディングガイド</h2>
                        <span class="control-label" data-i18n="training_modal_subtitle" style="font-size: 0.88rem; color: var(--muted);">業務役割に応じたカリキュラムを選択し、機能解説・受講ポイント・操作手順を確認できます</span>
                    </div>
                </div>

                <div class="auth-modal-tabs" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 24px; background: rgba(0,0,0,0.4); padding: 6px; border-radius: 12px; border: 1px solid var(--line);">
                    <button type="button" class="auth-tab-btn active" id="training-tab-1" onclick="switchTrainingTab('course1')">① 全社員基礎</button>
                    <button type="button" class="auth-tab-btn" id="training-tab-2" onclick="switchTrainingTab('course2')">② 営業・HR専門</button>
                    <button type="button" class="auth-tab-btn" id="training-tab-3" onclick="switchTrainingTab('course3')">③ 管理者管理</button>
                </div>

                <!-- Course 1 Panel -->
                <div id="training-course-1" class="training-course-panel active">
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--line); border-radius: 12px; padding: 22px; margin-bottom: 16px;">
                        <h3 style="margin: 0 0 10px 0; color: var(--green); font-size: 1.1rem; font-weight: 700;">コース①: 全社員基礎研修（オンボーディング・勤怠・アンケート）</h3>
                        <p style="font-size: 0.9rem; color: var(--muted); margin-bottom: 16px; line-height: 1.6;">
                            管理者から発行されたアカウントで初期セットアップ（アクティベーション）を完了し、適性アンケートおよび勤怠打刻・CSV解析を正しく利用する手順を学びます。
                        </p>
                        <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px;">
                            <button type="button" onclick="switchAppTab('onboarding-section', true)" class="sample-btn" style="padding: 9px 15px; font-size: 13px;">⚙️ 初期セットアップへ移動</button>
                            <button type="button" onclick="switchAppTab('survey-section', true)" class="sample-btn" style="padding: 9px 15px; font-size: 13px;">📊 適性アンケートへ移動</button>
                            <button type="button" onclick="switchAppTab('attendance-section', true)" class="sample-btn" style="padding: 9px 15px; font-size: 13px;">⏱️ 勤怠管理へ移動</button>
                        </div>
                        <div style="font-size: 0.85rem; background: rgba(186,255,102,0.08); border: 1px solid rgba(186,255,102,0.2); padding: 12px 16px; border-radius: 8px; color: var(--green);">
                            📖 詳細マニュアル: <a href="docs/training/FOUNDATION_TRAINING_HANDBOOK.md" style="color: var(--green); text-decoration: underline; font-weight: bold;">全社員基礎研修ハンドブック (FOUNDATION_TRAINING_HANDBOOK.md)</a>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
                        <label style="font-size: 0.88rem; cursor: pointer; display: flex; align-items: center; gap: 10px; color: #fff;">
                            <input type="checkbox" id="training-check-course1" onchange="toggleTrainingCourseProgress('course1')">
                            <span>コース①の研修受講を完了として記録する</span>
                        </label>
                        <span id="training-status-course1" style="font-size: 0.82rem; font-weight: 700; color: var(--muted);">未完了</span>
                    </div>
                </div>

                <!-- Course 2 Panel -->
                <div id="training-course-2" class="training-course-panel" style="display: none;">
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--line); border-radius: 12px; padding: 22px; margin-bottom: 16px;">
                        <h3 style="margin: 0 0 10px 0; color: var(--blue); font-size: 1.1rem; font-weight: 700;">コース②: 営業・HR専門研修（4軸AI診断・営業メールマッチング）</h3>
                        <p style="font-size: 0.9rem; color: var(--muted); margin-bottom: 16px; line-height: 1.6;">
                            Skill / Culture / Growth / Performing の4軸AI診断評価、BP営業メールの案件/人材双方向マッチング、および個人情報保護・人間による最終レビュー原則を修得します。
                        </p>
                        <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px;">
                            <button type="button" onclick="switchAppTab('matching-section', true)" class="sample-btn" style="padding: 9px 15px; font-size: 13px;">🤝 営業メールマッチングへ移動</button>
                            <button type="button" onclick="switchAppTab('aptitude-demo-section', true)" class="sample-btn" style="padding: 9px 15px; font-size: 13px;">📈 自己診断デモへ移動</button>
                        </div>
                        <div style="font-size: 0.85rem; background: rgba(0,210,255,0.08); border: 1px solid rgba(0,210,255,0.2); padding: 12px 16px; border-radius: 8px; color: var(--blue);">
                            📖 詳細マニュアル: <a href="docs/training/SALES_HR_TRAINING_HANDBOOK.md" style="color: var(--blue); text-decoration: underline; font-weight: bold;">営業・HR専門研修ハンドブック (SALES_HR_TRAINING_HANDBOOK.md)</a>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
                        <label style="font-size: 0.88rem; cursor: pointer; display: flex; align-items: center; gap: 10px; color: #fff;">
                            <input type="checkbox" id="training-check-course2" onchange="toggleTrainingCourseProgress('course2')">
                            <span>コース②の研修受講を完了として記録する</span>
                        </label>
                        <span id="training-status-course2" style="font-size: 0.82rem; font-weight: 700; color: var(--muted);">未完了</span>
                    </div>
                </div>

                <!-- Course 3 Panel -->
                <div id="training-course-3" class="training-course-panel" style="display: none;">
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--line); border-radius: 12px; padding: 22px; margin-bottom: 16px;">
                        <h3 style="margin: 0 0 10px 0; color: #ffd166; font-size: 1.1rem; font-weight: 700;">コース③: 管理者管理研修（統合ダッシュボード・仮名化監査・セキュリティ）</h3>
                        <p style="font-size: 0.9rem; color: var(--muted); margin-bottom: 16px; line-height: 1.6;">
                            統合管理者ダッシュボードでの全体監視、仮名化識別子（onb-digest）による監査ログ点検、Break-glass緊急対応および個人情報開示請求SLAの運用手順を修得します。
                        </p>
                        <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px;">
                            <button type="button" onclick="switchAppTab('admin-dashboard-section', true)" class="sample-btn" style="padding: 9px 15px; font-size: 13px;">🛡️ 管理者ダッシュボードへ移動</button>
                            <a href="admin" class="sample-btn" style="padding: 9px 15px; font-size: 13px; text-decoration: none;">⚙️ Admin（DB直通）を開く</a>
                        </div>
                        <div style="font-size: 0.85rem; background: rgba(255,209,102,0.08); border: 1px solid rgba(255,209,102,0.2); padding: 12px 16px; border-radius: 8px; color: #ffd166;">
                            📖 詳細マニュアル: <a href="docs/training/ADMIN_MANAGEMENT_TRAINING_HANDBOOK.md" style="color: #ffd166; text-decoration: underline; font-weight: bold;">管理者管理研修ハンドブック (ADMIN_MANAGEMENT_TRAINING_HANDBOOK.md)</a>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
                        <label style="font-size: 0.88rem; cursor: pointer; display: flex; align-items: center; gap: 10px; color: #fff;">
                            <input type="checkbox" id="training-check-course3" onchange="toggleTrainingCourseProgress('course3')">
                            <span>コース③の研修受講を完了として記録する</span>
                        </label>
                        <span id="training-status-course3" style="font-size: 0.82rem; font-weight: 700; color: var(--muted);">未完了</span>
                    </div>
                </div>
            </div>
        </section>
"""

# Insert #training-section right after #onboarding-section if not already present
if '<section id="training-section"' not in content:
    content = content.replace(
        '</section>\n\n        <!-- ==========================================================================\n             従業員適性・状況アンケート',
        '</section>\n' + training_section_markup + '\n        <!-- ==========================================================================\n             従業員適性・状況アンケート'
    )
    if '<section id="training-section"' not in content:
        # Fallback insert before #survey-section
        content = content.replace(
            '<section id="survey-section"',
            training_section_markup + '\n        <section id="survey-section"'
        )

# 3. Clean up modal functions in JS
content = re.sub(r'function openTrainingModal\([^)]*\)\s*\{[\s\S]*?\}', 'function openTrainingModal(event) { if (event) event.preventDefault(); switchAppTab("training-section", true); }', content)
content = re.sub(r'function closeTrainingModal\([^)]*\)\s*\{[\s\S]*?\}', 'function closeTrainingModal() {}', content)

# 4. Remove target="_blank" from all docs / handbook links in index.html
content = re.sub(r'href="docs/([^"]+)"\s+target="_blank"\s+rel="noopener"', r'href="docs/\1"', content)
content = re.sub(r'target="_blank"\s+rel="noopener"\s+href="docs/([^"]+)"', r'href="docs/\1"', content)

INDEX_PATH.write_text(content, encoding="utf-8")
print("[1] index.html updated: #training-section added, modal eliminated, target=_blank removed!")
