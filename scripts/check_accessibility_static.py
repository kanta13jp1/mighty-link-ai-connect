"""Static accessibility guard for the public demo HTML.

This check complements axe/Lighthouse-style runtime scans by verifying the
project-specific landmarks, labels, and ARIA state hooks that must stay in the
single-page public demo.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = PROJECT_ROOT / "index.html"


def _contains(pattern: str, html: str) -> bool:
    return re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL) is not None


def check_index_html(path: Path = INDEX_HTML) -> dict[str, object]:
    path = path.resolve()
    html = path.read_text(encoding="utf-8")
    checks: list[tuple[str, bool, str]] = [
        (
            "localized_matching_filter_contract_label",
            '<label for="matching-filter-contract" '
            'data-i18n="matching_filter_contract_label">契約形態</label>' in html
            and all(
                f'matching_filter_contract_label: "{label}"' in html
                for label in ["契約形態", "Contract type", "合同类型", "계약 형태"]
            ),
            "Matching filter contract label must follow the selected language.",
        ),
        (
            "localized_matching_filter_contract_options",
            all(
                f'<option value="{value}" data-i18n="{key}">' in html
                for value, key in [
                    ("", "matching_filter_contract_option_all"),
                    ("準委任", "matching_filter_contract_option_quasi_mandate"),
                    ("派遣", "matching_filter_contract_option_temporary_staffing"),
                    ("請負", "matching_filter_contract_option_contract_work"),
                    ("正社員/契約社員", "matching_filter_contract_option_employee"),
                ]
            )
            and all(
                f'{key}: "{label}"' in html
                for key, labels in {
                    "matching_filter_contract_option_all": ["すべて", "All", "全部", "전체"],
                    "matching_filter_contract_option_quasi_mandate": ["準委任", "Quasi-mandate", "准委托", "준위임"],
                    "matching_filter_contract_option_temporary_staffing": ["派遣", "Temporary staffing", "派遣", "파견"],
                    "matching_filter_contract_option_contract_work": ["請負", "Contract work", "承包", "도급"],
                    "matching_filter_contract_option_employee": ["正社員/契約社員", "Permanent/contract employee", "正式员工/合同员工", "정규직/계약직"],
                }.items()
                for label in labels
            ),
            "Matching filter contract options must follow the selected language without changing their values.",
        ),
        (
            "localized_matching_filter_score_label",
            '<label for="matching-filter-score" '
            'data-i18n="matching_filter_score_label">適合度</label>' in html
            and all(
                f'matching_filter_score_label: "{label}"' in html
                for label in ["適合度", "Match score", "匹配度", "적합도"]
            ),
            "Matching filter score label must follow the selected language.",
        ),
        (
            "localized_matching_filter_rate_labels",
            '<label for="matching-filter-rate-min" '
            'data-i18n="matching_filter_rate_min_label">単価下限</label>' in html
            and '<label for="matching-filter-rate-max" '
            'data-i18n="matching_filter_rate_max_label">単価上限</label>' in html
            and all(
                f'matching_filter_rate_min_label: "{min_label}"' in html
                and f'matching_filter_rate_max_label: "{max_label}"' in html
                for min_label, max_label in [
                    ("単価下限", "単価上限"),
                    ("Minimum rate", "Maximum rate"),
                    ("最低单价", "最高单价"),
                    ("최소 단가", "최대 단가"),
                ]
            ),
            "Matching filter rate labels must follow the selected language.",
        ),
        (
            "localized_matching_filter_skill_label",
            '<label for="matching-filter-skill" '
            'data-i18n="matching_filter_skill_label">必須スキル</label>' in html
            and all(
                f'matching_filter_skill_label: "{label}"' in html
                for label in ["必須スキル", "Required skill", "必备技能", "필수 기술"]
            ),
            "Matching filter skill label must follow the selected language.",
        ),
        (
            "localized_matching_filter_keyword_copy",
            '<label for="matching-filter-keyword" '
            'data-i18n="matching_filter_keyword_label">フリーワード</label>' in html
            and 'id="matching-filter-keyword" placeholder="案件名・要員・送信元など" '
            'data-i18n-placeholder="matching_filter_keyword_placeholder"' in html
            and all(
                f'matching_filter_keyword_label: "{label}"' in html
                and f'matching_filter_keyword_placeholder: "{placeholder}"' in html
                for label, placeholder in [
                    ("フリーワード", "案件名・要員・送信元など"),
                    ("Keyword", "Project, talent, sender, etc."),
                    ("关键词", "项目、人才、发件人等"),
                    ("키워드", "프로젝트, 인재, 발신자 등"),
                ]
            ),
            "Matching filter keyword label and placeholder must follow the selected language.",
        ),
        (
            "localized_matching_filter_date_caption",
            '<label for="matching-filter-received-from" '
            'data-i18n="matching_filter_received_date_label">受信日</label>' in html
            and all(
                f'matching_filter_received_date_label: "{caption}"' in html
                for caption in ["受信日", "Received date", "接收日期", "수신일"]
            ),
            "Matching filter date caption must follow the selected language.",
        ),
        (
            "localized_matching_filter_date_input_names",
            'id="matching-filter-received-from" aria-label="受信日（開始）" '
            'data-i18n-aria-label="matching_filter_received_from_label"' in html
            and 'id="matching-filter-received-to" aria-label="受信日（終了）" '
            'data-i18n-aria-label="matching_filter_received_to_label"' in html
            and all(
                f'matching_filter_received_from_label: "{start_label}"' in html
                and f'matching_filter_received_to_label: "{end_label}"' in html
                for start_label, end_label in [
                    ("受信日（開始）", "受信日（終了）"),
                    ("Received date (start)", "Received date (end)"),
                    ("接收日期（开始）", "接收日期（结束）"),
                    ("수신일(시작)", "수신일(종료)"),
                ]
            ),
            "Matching filter date input names must follow the selected language.",
        ),
        (
            "localized_matching_filter_search_landmark",
            'class="matching-filter-toolbar" role="search" '
            'aria-label="営業メールAIマッチングの絞り込み" '
            'data-i18n-aria-label="matching_filter_search_label"' in html
            and all(
                f'matching_filter_search_label: "{label}"' in html
                for label in [
                    "営業メールAIマッチングの絞り込み",
                    "Sales email AI matching filters",
                    "销售邮件 AI 匹配筛选",
                    "영업 메일 AI 매칭 필터",
                ]
            ),
            "Matching filter search landmark name must follow the selected language.",
        ),
        (
            "localized_matching_filter_reset",
            'data-i18n-aria-label="matching_filter_reset_label"' in html
            and 'data-i18n-title="matching_filter_reset_label"' in html
            and 'document.querySelectorAll("[data-i18n-title]")' in html
            and all(
                f'matching_filter_reset_label: "{label}"' in html
                for label in [
                    "絞り込み条件をリセット",
                    "Reset filters",
                    "重置筛选条件",
                    "필터 조건 초기화",
                ]
            ),
            "Matching filter reset name and tooltip must follow the selected language.",
        ),
        (
            "localized_mobile_bottom_sheet_content",
            all(
                html.count(f'data-i18n="{key}"') == 1
                for key in [
                    "mobile_sheet_title",
                    "mobile_sheet_setup",
                    "mobile_sheet_self_assessment",
                    "mobile_sheet_admin",
                    "mobile_sheet_support",
                ]
            )
            and all(
                f'{key}: "{label}"' in html
                for key, labels in {
                    "mobile_sheet_title": ["メニュー & ツール", "Menu & Tools", "菜单与工具", "메뉴 & 도구"],
                    "mobile_sheet_setup": ["初期設定", "Setup", "初始设置", "초기 설정"],
                    "mobile_sheet_self_assessment": ["自己診断", "Self-assessment", "自我诊断", "자가 진단"],
                    "mobile_sheet_admin": ["管理者", "Admin", "管理", "관리자"],
                    "mobile_sheet_support": ["サポート", "Support", "支持", "지원"],
                }.items()
                for label in labels
            ),
            "Mobile bottom sheet content must follow the selected language.",
        ),
        (
            "localized_mobile_bottom_sheet_dialog_name",
            'role="dialog" aria-modal="true" aria-label="モバイル追加メニュー" '
            'data-i18n-aria-label="mobile_more_menu_dialog_label"' in html
            and all(
                f'mobile_more_menu_dialog_label: "{label}"' in html
                for label in ["モバイル追加メニュー", "More menu", "更多菜单", "추가 메뉴"]
            ),
            "Mobile bottom sheet dialog name must follow the selected language.",
        ),
        (
            "localized_mobile_bottom_sheet_close_button",
            'class="auth-modal-close" onclick="closeMobileBottomSheet()" '
            'style="position:static;" aria-label="閉じる" '
            'data-i18n-aria-label="shortcut_modal_close"' in html
            and all(
                f'shortcut_modal_close: "{label}"' in html
                for label in ["閉じる", "Close", "关闭", "닫기"]
            ),
            "Mobile bottom sheet close name must follow the selected language.",
        ),
        (
            "localized_shortcut_modal_close_button",
            'class="auth-modal-close" onclick="closeShortcutHelpModal()" '
            'aria-label="閉じる" data-i18n-aria-label="shortcut_modal_close"' in html
            and all(
                f'shortcut_modal_close: "{label}"' in html
                for label in ["閉じる", "Close", "关闭", "닫기"]
            ),
            "Shortcut help modal close name must follow the selected language.",
        ),
        (
            "localized_auth_modal_close_button",
            'class="auth-modal-close" onclick="closeAuthModal()" '
            'aria-label="認証ダイアログを閉じる" '
            'data-i18n-aria-label="auth_modal_close_label"' in html
            and all(
                f'auth_modal_close_label: "{label}"' in html
                for label in [
                    "認証ダイアログを閉じる",
                    "Close authentication dialog",
                    "关闭身份验证对话框",
                    "인증 대화상자 닫기",
                ]
            ),
            "Authentication modal close name must follow the selected language.",
        ),
        (
            "localized_brand_home_links",
            html.count('data-i18n-aria-label="brand_home_label"') == 2
            and 'aria-label="Mighty Skill-Bridge footer home"' not in html
            and all(
                f'brand_home_label: "{label}"' in html
                for label in [
                    "Mighty Skill-Bridge ホーム",
                    "Mighty Skill-Bridge home",
                    "Mighty Skill-Bridge 首页",
                    "Mighty Skill-Bridge 홈",
                ]
            ),
            "Header and footer brand home links must follow the selected language.",
        ),
        (
            "skip_link",
            '<a class="skip-link" href="#top" data-i18n="skip_to_main">' in html
            and '<main id="top" tabindex="-1">' in html,
            "Localized skip link must move keyboard users to the main content landmark.",
        ),
        (
            "primary_navigation_target",
            '<nav class="nav-links" id="primary-navigation" '
            'aria-label="メインナビゲーション" '
            'data-i18n-aria-label="primary_navigation_label">' in html
            and all(
                f'primary_navigation_label: "{label}"' in html
                for label in ["メインナビゲーション", "Primary navigation", "主导航", "주요 탐색"]
            ),
            "Primary navigation needs a localized aria label and stable id.",
        ),
        (
            "localized_workspace_navigation",
            '<aside class="global-app-sidebar" id="global-sidebar" '
            'aria-label="ワークスペースナビゲーション" '
            'data-i18n-aria-label="workspace_navigation_label">' in html
            and all(
                f'workspace_navigation_label: "{label}"' in html
                for label in [
                    "ワークスペースナビゲーション",
                    "Workspace navigation",
                    "工作区导航",
                    "워크스페이스 탐색",
                ]
            ),
            "Workspace navigation landmark name must follow the selected language.",
        ),
        (
            "localized_mobile_bottom_navigation",
            'class="mobile-bottom-nav" aria-label="モバイル主要ナビゲーション" '
            'data-i18n-aria-label="mobile_navigation_label">' in html
            and all(
                f'data-i18n="{key}"' in html
                for key in [
                    "mobile_nav_home",
                    "mobile_nav_survey",
                    "mobile_nav_attendance",
                    "mobile_nav_matching",
                    "mobile_nav_more",
                ]
            )
            and 'aria-label="その他のメニューを開く" '
            'data-i18n-aria-label="mobile_nav_more_menu_label">' in html
            and all(
                f'mobile_navigation_label: "{label}"' in html
                for label in [
                    "モバイル主要ナビゲーション",
                    "Mobile primary navigation",
                    "移动端主导航",
                    "모바일 주요 탐색",
                ]
            ),
            "Mobile bottom navigation labels must follow the selected language.",
        ),
        (
            "localized_theme_toggle",
            'id="theme-toggle" aria-label="ライトテーマに切り替え"' in html
            and 'id="theme-toggle-label">ライト</span>' in html
            and all(
                key in html
                for key in [
                    "theme_toggle_to_light",
                    "theme_toggle_to_dark",
                ]
            ),
            "Theme toggle name must follow the selected language and target theme.",
        ),
        (
            "localized_language_switch_group",
            '<div class="language-switch" role="group" aria-label="言語を選択" '
            'data-i18n-aria-label="language_switch_label">' in html
            and all(
                f'language_switch_label: "{label}"' in html
                for label in ["言語を選択", "Select language", "选择语言", "언어 선택"]
            )
            and 'document.querySelectorAll("[data-i18n-aria-label]")' in html,
            "Language switch group name must follow the selected language.",
        ),
        (
            "touch_target_css",
            ".nav-links a,\n        .language-switch button" in html
            and "min-height: 32px;" in html
            and "min-width: 32px;" in html,
            "Navigation links and language buttons must keep WCAG 2.2 AA touch target sizing.",
        ),
        (
            "keyboard_focus_css",
            "a:focus-visible," in html and "outline: 3px solid var(--blue);" in html,
            "Interactive elements need visible keyboard focus styling.",
        ),
        (
            "engineer_input_label",
            'for="engineer-input"' in html and 'aria-labelledby="engineer-input-heading"' in html,
            "Engineer input must have an explicit label and visible heading association.",
        ),
        (
            "job_input_label",
            'for="job-input"' in html and 'aria-labelledby="job-input-heading"' in html,
            "Job input must have an explicit label and visible heading association.",
        ),
        (
            "feedback_comment_label",
            '<label class="sr-only" for="feedback-comment">Feedback comment</label>' in html,
            "Feedback comment textarea must not rely on placeholder text as its label.",
        ),
        (
            "decorative_hero_video_hidden",
            'id="hero-video-bg"' in html and 'aria-hidden="true" tabindex="-1"' in html,
            "Decorative hero video should be removed from the accessibility tree.",
        ),
        (
            "story_video_named",
            'id="seedance-video"' in html and 'aria-label="AI-generated match story preview video"' in html,
            "Meaningful video preview requires an accessible name.",
        ),
        (
            "radar_canvas_named",
            'id="reportRadarChart" role="img"' in html and "4-axis fit radar chart" in html,
            "Canvas chart requires role=img, an accessible name, and fallback text.",
        ),
        (
            "progressbars_named",
            html.count('role="progressbar"') >= 4
            and all(
                label in html
                for label in [
                    'aria-label="Skill fit score"',
                    'aria-label="Culture fit score"',
                    'aria-label="Growth fit score"',
                    'aria-label="Performing fit score"',
                ]
            ),
            "All visual score bars must expose progressbar semantics.",
        ),
        (
            "tab_semantics",
            'role="tablist"' in html
            and html.count('role="tab"') >= 2
            and html.count('role="tabpanel"') >= 2
            and "aria-selected" in html,
            "Report tabs must expose tablist/tab/tabpanel semantics.",
        ),
        (
            "scroll_region_focusable",
            'class="table-responsive" tabindex="0"' in html
            and "Candidates comparison table" in html,
            "Horizontally scrollable comparison table must be keyboard focusable.",
        ),
        (
            "blank_targets_noopener",
            not _contains(r'target="_blank"(?![^>]*rel="[^"]*\bnoopener\b)', html),
            "Links opening a new tab must include rel=noopener.",
        ),
    ]

    failures = [
        {"id": check_id, "message": message}
        for check_id, passed, message in checks
        if not passed
    ]
    return {
        "source": str(path.relative_to(PROJECT_ROOT)),
        "status": "PASS" if not failures else "FAIL",
        "passed": len(checks) - len(failures),
        "total": len(checks),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    result = check_index_html()
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
